"""E2's batched loops for random sampling and OpenAI-ES, beside 04a's `evolve_batch` (docs/E2/DESIGN.md).

They mirror `evolve_batch`: several independent runs in lockstep, each with its own random streams
and its own schedule of training worlds (`train_ids(run seed, generation)`), sharing only the
simulator call; the same checkpoint schedule (generation 0, every `checkpoint_every` generations and
the last), scored on the validation worlds by raw count; the champion is the first checkpoint with the
highest validation mean. Every training and validation score must be finite, or the batch stops.
Fitness is the unshaped count, averaged over the run's worlds.

**Generation 0 is every method's start, and it is paired across methods:** a run seed's generation-0
population is `initial_population(run seed)`, the GA's own, on the GA's generation-0 worlds.

**Random sampling** draws a fresh population each generation from the run's initialisation stream
(so its generation 0 is the GA's), and at each checkpoint nominates the best genome by training score
since the previous checkpoint (ties to the earliest).

**OpenAI-ES:** generation 0 is the start screen; its best genome (ties to the earliest) becomes the
mean. Each later generation asks `population / 2` antithetic pairs from the run's noise stream,
decodes and scores them, and updates the mean; the mean is projected into the genome's bounds only
after a real update (a flat generation changes nothing, `OpenAIES.tell`). A checkpoint validates the
genome the mean decodes to, after that generation's update. The loop returns each run's state, from
which `es_batch(resume=...)` continues the same run (the descriptive extension).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import torch

from ..brain import BrainSpec, Genome
from ..e04a.evolve import RunRecord, RunSpec, _Null, _stack_ids, init_seed, initial_population, moved, train_ids
from ..evo.genomes import genome_hash
from ..evo.rollout import rollout
from .optimizers import BestSinceCheckpoint, OpenAIES, decode, encode, project

NOISE_STREAM = 0xE5  # the ES's noise generator: (run seed, this key)
CLIP_TOLERANCE = 1e-3  # an ES coordinate counts as clipped if decoding moved it by more than this


@dataclass
class ESRecord(RunRecord):
    start: dict = field(default_factory=dict)  # the start screen's best: index, score, sha256
    flat_generations: int = 0  # generations with no update, cumulative across a resume
    first_non_flat: int | None = None  # the first generation with a real update


def _check_runs(runs, settings=None):
    """Every run has its own number and seed; the ES pilot may repeat a seed across settings (paired:
    the same start screen, worlds and noise), never within one."""
    keys = [r.run_seed for r in runs] if settings is None else [(r.run_seed, *s) for r, s in zip(runs, settings)]
    if len({r.run for r in runs}) != len(runs) or len(set(keys)) != len(runs):
        raise ValueError("every run in a batch needs its own run number, and its own seed (or setting, in the pilot)")
    if any(r.shaping != 0.0 for r in runs):
        raise ValueError("E2's methods are unshaped (c = 0)")


def _train(cfg, iface, genomes, ids, P, world_seed, device, rollout_fn, check, category, g):
    """[strains, worlds] counts for every run's strains, each on its own run's worlds."""
    check()
    with category("selection"):
        res = rollout_fn(cfg, iface, Genome.cat(genomes), _stack_ids(ids, P), world_seed, device,
                         chunk_worlds=len(genomes) * P * ids[0].size)
    if not np.isfinite(res.score).all():
        raise FloatingPointError(f"generation {g}: non-finite training count")
    return np.asarray(res.score, dtype=np.float64)


def _validate(cfg, iface, cands, records, validation_ids, world_seed, device, rollout_fn, check, category, g,
              training_scores):
    check()
    with category("holdout"):  # the checkpoints, as `evolve` counts them
        v = rollout_fn(cfg, iface, Genome.cat(cands), validation_ids, world_seed, device,
                       chunk_worlds=len(cands) * len(validation_ids))
    if not np.isfinite(v.score).all():
        raise FloatingPointError(f"generation {g}: non-finite validation count")
    for i, rec in enumerate(records):
        rec.checkpoints.append({"generation": g, "validation_mean": float(v.score[i].mean()),
                                "validation_counts": np.asarray(v.score[i]).astype(int).tolist(),
                                "training_score": training_scores[i], "sha256": genome_hash(cands[i], 0)})
        rec.candidates.append(moved(cands[i].clone(), "cpu"))


def _log(rec, g, fit, genome, extra=None):
    best = int(np.argmax(fit))
    rec.log.append({"generation": g, "best_fitness": float(fit[best]), "mean_fitness": float(fit.mean()),
                    "zero_share": float((fit == 0).mean()), "best_sha256": genome_hash(genome, best),
                    **(extra or {})})
    return best


def _is_checkpoint(g, every, generations):
    return g % every == 0 or g == generations - 1


def random_batch(cfg, iface, spec: BrainSpec, runs: list[RunSpec], *, generations: int, checkpoint_every: int,
                 validation_ids: np.ndarray, world_seed: int, id_base: int, id_span: int, device="cpu",
                 rollout_fn=rollout, check=None, category=None, on_checkpoint=None) -> list[RunRecord]:
    """Random sampling for every run in `runs`, generations 0 .. generations - 1, in lockstep."""
    _check_runs(runs)
    P, W = cfg.evo.population, cfg.evo.worlds_per_strain
    check = check or (lambda: None)
    category = category or (lambda name: _Null())
    validation_ids = np.asarray(validation_ids, dtype=np.int64)
    gens = [torch.Generator().manual_seed(init_seed(r.run_seed)) for r in runs]  # on the CPU, then moved
    best = [BestSinceCheckpoint() for _ in runs]
    records = [RunRecord(r) for r in runs]

    for g in range(generations):
        t_gen = time.perf_counter()
        pops = [moved(Genome.random(spec, cfg.brain, P, generator=gens[i]), device) for i in range(len(runs))]
        ids = [train_ids(r.run_seed, g, W, id_base, id_span) for r in runs]
        count = _train(cfg, iface, pops, ids, P, world_seed, device, rollout_fn, check, category, g)
        for i, rec in enumerate(records):
            c_i = count[i * P:(i + 1) * P]
            fit = c_i.mean(axis=1)
            b = _log(rec, g, fit, pops[i])
            best[i].offer(fit[b:b + 1], [(float(fit[b]), pops[i].select([b]))])
            if g == 0:
                rec.generation0 = {"train_ids": ids[i].tolist(), "counts": c_i.astype(int).tolist()}

        if _is_checkpoint(g, checkpoint_every, generations):
            taken = [b.take() for b in best]
            _validate(cfg, iface, [t[1] for t in taken], records, validation_ids, world_seed, device, rollout_fn,
                      check, category, g, [t[0] for t in taken])
            if on_checkpoint is not None:
                on_checkpoint(records, g)
        for rec in records:
            rec.log[-1]["batch_seconds"] = time.perf_counter() - t_gen
    return records


def _noise_rng(run_seed: int) -> np.random.Generator:
    return np.random.default_rng([int(run_seed), NOISE_STREAM])


def es_batch(cfg, iface, spec: BrainSpec, runs: list[RunSpec], *, generations: int, sigma, lr,
             checkpoint_every: int, validation_ids: np.ndarray, world_seed: int, id_base: int, id_span: int,
             device="cpu", rollout_fn=rollout, check=None, category=None, on_checkpoint=None,
             resume: list[dict] | None = None) -> tuple[list[ESRecord], list[dict]]:
    """OpenAI-ES for every run in `runs`, in lockstep, up to generation `generations - 1`.

    Without `resume`, generation 0 is the start screen. With `resume` (the states a previous call
    returned, one per run, in order), each run continues from its saved generation; the records then
    hold only the new generations. `sigma` and `lr` are one value or one per run (the pilot). Returns
    the records and each run's state after the last generation."""
    R = len(runs)
    sigmas = [float(x) for x in (sigma if np.ndim(sigma) else [sigma] * R)]
    lrs = [float(x) for x in (lr if np.ndim(lr) else [lr] * R)]
    if len(sigmas) != R or len(lrs) != R:
        raise ValueError("one σ and one learning rate per run")
    _check_runs(runs, list(zip(sigmas, lrs)))
    P, W = cfg.evo.population, cfg.evo.worlds_per_strain
    if P % 2:
        raise ValueError("the ES needs an even population (antithetic pairs)")
    check = check or (lambda: None)
    category = category or (lambda name: _Null())
    validation_ids = np.asarray(validation_ids, dtype=np.int64)
    records = [ESRecord(r) for r in runs]
    screens = [initial_population(spec, cfg.brain, r.run_seed, P, device) for r in runs]

    if resume is None:
        g0 = 0
        ids = [train_ids(r.run_seed, 0, W, id_base, id_span) for r in runs]
        t_gen = time.perf_counter()
        count = _train(cfg, iface, screens, ids, P, world_seed, device, rollout_fn, check, category, 0)
        templates, ess = [], []
        for i, rec in enumerate(records):
            c_i = count[i * P:(i + 1) * P]
            fit = c_i.mean(axis=1)
            b = _log(rec, 0, fit, screens[i], {"flat": None, "clip_share": None})
            rec.start = {"index": b, "score": float(fit[b]), "sha256": genome_hash(screens[i], b)}
            rec.generation0 = {"train_ids": ids[i].tolist(), "counts": c_i.astype(int).tolist()}
            templates.append(screens[i].select([b]))
            mean = encode(templates[i])[0].detach().cpu().numpy().astype(np.float64)
            ess.append(OpenAIES(mean, sigma=sigmas[i], lr=lrs[i], pairs=P // 2, generator=_noise_rng(runs[i].run_seed)))
            rec.start["mean"] = mean.copy()
        _es_checkpoint(cfg, iface, ess, templates, records, validation_ids, world_seed, device, rollout_fn, check,
                       category, 0, generations, checkpoint_every, on_checkpoint,
                       [r.start["score"] for r in records])
        for rec in records:
            rec.log[-1]["batch_seconds"] = time.perf_counter() - t_gen
    else:
        if len(resume) != R or any(s["run_seed"] != r.run_seed for s, r in zip(resume, runs)):
            raise ValueError("the resumed states must match the runs, in order")
        g0 = {s["generation"] for s in resume}
        if len(g0) != 1:
            raise ValueError("every resumed run must be at the same generation")
        g0 = g0.pop()
        templates, ess = [], []
        for i, (rec, s) in enumerate(zip(records, resume)):
            templates.append(screens[i].select([s["start"]["index"]]))
            es = OpenAIES(s["mean"], sigma=s["sigma"], lr=s["lr"], pairs=P // 2, generator=np.random.default_rng())
            es.rng.bit_generator.state = s["rng_state"]
            es.m, es.v, es.t, es.flat_generations = s["m"].copy(), s["v"].copy(), int(s["t"]), int(s["flat_generations"])
            if (es.sigma, es.lr) != (sigmas[i], lrs[i]):
                raise ValueError("a resumed run keeps its σ and learning rate")
            ess.append(es)
            rec.start, rec.first_non_flat = dict(s["start"]), s["first_non_flat"]

    for g in range(g0 + 1, generations):
        t_gen = time.perf_counter()
        asked = [es.ask() for es in ess]
        cands, clips = [], []
        for i in range(R):
            zt = torch.as_tensor(asked[i], dtype=templates[i].w.dtype, device=templates[i].device)
            c = decode(zt, templates[i])
            clips.append(float(((encode(c) - zt).abs() > CLIP_TOLERANCE).float().mean()))
            cands.append(c)
        ids = [train_ids(r.run_seed, g, W, id_base, id_span) for r in runs]
        count = _train(cfg, iface, cands, ids, P, world_seed, device, rollout_fn, check, category, g)
        for i, (rec, es) in enumerate(zip(records, ess)):
            fit = count[i * P:(i + 1) * P].mean(axis=1)
            t_before = es.t
            es.tell(fit)
            updated = es.t > t_before
            if updated:
                es.mean = project(torch.as_tensor(es.mean, dtype=templates[i].w.dtype, device=templates[i].device),
                                  templates[i]).detach().cpu().numpy().astype(np.float64)
                if rec.first_non_flat is None:
                    rec.first_non_flat = g
            _log(rec, g, fit, cands[i], {"flat": not updated, "clip_share": clips[i]})
        _es_checkpoint(cfg, iface, ess, templates, records, validation_ids, world_seed, device, rollout_fn, check,
                       category, g, generations, checkpoint_every, on_checkpoint, [None] * R)
        for rec in records:
            rec.log[-1]["batch_seconds"] = time.perf_counter() - t_gen

    states = []
    for i, (rec, es) in enumerate(zip(records, ess)):
        rec.flat_generations = es.flat_generations
        rec.final = moved(_mean_genome(es, templates[i]), "cpu")
        states.append({"run_seed": runs[i].run_seed, "generation": generations - 1, "sigma": es.sigma, "lr": es.lr,
                       "mean": es.mean.copy(), "m": es.m.copy(), "v": es.v.copy(), "t": es.t,
                       "flat_generations": es.flat_generations, "rng_state": es.rng.bit_generator.state,
                       "start": dict(rec.start), "start_mean": rec.start["mean"].copy(),
                       "first_non_flat": rec.first_non_flat})
    return records, states


def _mean_genome(es: OpenAIES, template: Genome) -> Genome:
    return decode(torch.as_tensor(es.mean[None], dtype=template.w.dtype, device=template.device), template)


def _es_checkpoint(cfg, iface, ess, templates, records, validation_ids, world_seed, device, rollout_fn, check,
                   category, g, generations, every, on_checkpoint, training_scores):
    if not _is_checkpoint(g, every, generations):
        return
    cands = [_mean_genome(es, t) for es, t in zip(ess, templates)]
    _validate(cfg, iface, cands, records, validation_ids, world_seed, device, rollout_fn, check, category, g,
              training_scores)
    if on_checkpoint is not None:
        on_checkpoint(records, g)
