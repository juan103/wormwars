"""Several independent evolutionary runs in lockstep, as one batch (04a, D103).

Each run keeps everything of its own: its genomes, its initialisation and mutation random streams,
its schedule of training worlds and its shaping coefficient. The runs share only the simulator
call: in each generation every run's strains play in one rollout, each strain on its own run's
worlds. That is the throughput E1 measured for 04a's shape (32 strains x 8 worlds x 1 wey, with 8
runs batched), and it is the only thing batching changes. Floating-point results are exact only
within one batch composition (docs/REPRODUCIBILITY.md), and no exact replay is claimed.

The selection step is `wormwars.evo.evolve.breed`, 02's truncation selection with elitism and
Gaussian mutation, applied to each run separately with that run's generator.

**Fitness** is count + c x progress per world, averaged over the run's worlds, where count is the
number of targets reached and progress the fraction of the unfinished leg's starting distance closed
by the end, clipped to [0, 1] (`World.final_progress`). With c < 1 the bonus is always worth less
than one arrival. c = 0 is the unshaped arm. Every validation, hold-out and gate score is the raw
count.

**Checkpoints:** at generation 0, every `checkpoint_every` generations and at the last, each run's
best strain of that generation (by its own fitness) is scored on the validation worlds, raw count.
The run's champion is the first checkpoint with the highest validation mean (ties go to the
earliest); its generation-0 baseline is the generation-0 checkpoint. Validation worlds select the
champion but never breed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import torch

from ..brain import BrainSpec, Genome
from ..evo.evolve import breed
from ..evo.genomes import genome_hash
from ..evo.rollout import rollout

TRAIN_STREAM = 0xC0FFEE  # the same key as `SeedPool.train_ids`, with the run seed and generation


@dataclass(frozen=True)
class RunSpec:
    run: int
    run_seed: int
    shaping: float  # c, in [0, 1)

    def __post_init__(self):
        if not 0.0 <= self.shaping < 1.0:
            raise ValueError(f"shaping must be in [0, 1) so the bonus stays below one arrival, got {self.shaping}")


def fitness(count: np.ndarray, progress: np.ndarray, c: float) -> np.ndarray:
    """[strains]: the mean over worlds of count + c x progress."""
    if not 0.0 <= c < 1.0:
        raise ValueError(f"shaping must be in [0, 1), got {c}")
    progress = np.asarray(progress, dtype=np.float64)
    if progress.min(initial=0.0) < 0.0 or progress.max(initial=0.0) > 1.0:
        raise ValueError("progress must lie in [0, 1]")
    return (np.asarray(count, dtype=np.float64) + c * progress).mean(axis=1)


def train_ids(run_seed: int, generation: int, n: int, base: int, span: int) -> np.ndarray:
    """The run's training worlds for one generation: a function of (run seed, generation) only."""
    rng = np.random.default_rng([int(run_seed), int(generation), TRAIN_STREAM])
    return base + rng.integers(0, span, size=n)


def init_seed(run_seed: int) -> int:
    return 2 * int(run_seed)


def breed_seed(run_seed: int) -> int:
    return 2 * int(run_seed) + 1


def initial_population(spec: BrainSpec, bcfg, run_seed: int, population: int, device) -> Genome:
    """Drawn on the CPU from the run's own generator, then moved, so it does not depend on the device."""
    g = Genome.random(spec, bcfg, population, generator=torch.Generator().manual_seed(init_seed(run_seed)))
    return moved(g, device)


def moved(genome: Genome, device) -> Genome:
    """A copy of `genome` on `device`, every parameter included."""
    return genome.with_params(spec=genome.spec.to(device),
                              **{k: v.to(device) for k, v in genome.params().items() if v is not None})


@dataclass
class RunRecord:
    spec: RunSpec
    log: list = field(default_factory=list)  # one dict per generation
    checkpoints: list = field(default_factory=list)  # one dict per checkpoint
    candidates: list = field(default_factory=list)  # one single-strain Genome per checkpoint (CPU)
    generation0: dict = field(default_factory=dict)  # per-genome, per-world counts and progress
    final: Genome | None = None  # the last generation's population (CPU)

    def champion_index(self) -> int:
        """The first checkpoint with the highest validation mean."""
        return int(np.argmax([c["validation_mean"] for c in self.checkpoints]))


def _stack_ids(per_run: list[np.ndarray], population: int) -> np.ndarray:
    """[runs x population, worlds]: each strain plays its own run's worlds."""
    return np.concatenate([np.tile(ids, (population, 1)) for ids in per_run])


def evolve_batch(cfg, iface, spec: BrainSpec, runs: list[RunSpec], *, generations: int, checkpoint_every: int,
                 validation_ids: np.ndarray, world_seed: int, id_base: int, id_span: int, device="cpu",
                 rollout_fn=rollout, check=None, category=None, on_checkpoint=None, initial=None,
                 mutation_scales=None) -> list[RunRecord]:
    """Evolve every run in `runs` for `generations` generations, in lockstep.

    `check()` is called before every rollout (the cap); `category(name)` returns a context manager
    for the compute accounting; `on_checkpoint(records, generation)` is called after every
    checkpoint, so a caller can write partial records.

    E4s's hooks, both optional, and the defaults are unchanged: `initial(run_spec)` returns a run's
    generation-0 population (`population` strains) in place of `initial_population`;
    `mutation_scales(run_spec)` returns that run's per-parameter factors on the mutation sigmas
    (`Genome.mutate`), or None."""
    if len({r.run for r in runs}) != len(runs) or len({r.run_seed for r in runs}) != len(runs):
        raise ValueError("every run in a batch needs its own run number and run seed")
    P, W = cfg.evo.population, cfg.evo.worlds_per_strain
    check = check or (lambda: None)
    category = category or (lambda name: _Null())
    validation_ids = np.asarray(validation_ids, dtype=np.int64)
    if initial is None:
        pops = [initial_population(spec, cfg.brain, r.run_seed, P, device) for r in runs]
    else:
        pops = [moved(initial(r), device) for r in runs]
        if any(p.n_strains != P for p in pops):
            raise ValueError(f"an initial population must hold {P} strains (the population)")
    scales = [None if mutation_scales is None else mutation_scales(r) for r in runs]
    gens = [torch.Generator(device=device).manual_seed(breed_seed(r.run_seed)) for r in runs]
    records = [RunRecord(r) for r in runs]
    R = len(runs)

    for g in range(generations):
        t_gen = time.perf_counter()
        ids = [train_ids(r.run_seed, g, W, id_base, id_span) for r in runs]
        check()
        with category("selection"):
            res = rollout_fn(cfg, iface, Genome.cat(pops), _stack_ids(ids, P), world_seed, device,
                             chunk_worlds=R * P * W)
        count, progress = res.score, res.progress
        if not (np.isfinite(count).all() and np.isfinite(progress).all()):
            raise FloatingPointError(f"generation {g}: non-finite count or progress")
        fits = []
        for i, rec in enumerate(records):
            c_i, p_i = count[i * P:(i + 1) * P], progress[i * P:(i + 1) * P]
            fit = fitness(c_i, p_i, rec.spec.shaping)
            fits.append(fit)
            best = int(np.argmax(fit))
            per_strain_count = c_i.mean(axis=1)
            rec.log.append({"generation": g, "best_fitness": float(fit[best]), "mean_fitness": float(fit.mean()),
                            "best_count": float(per_strain_count[best]), "max_count": float(per_strain_count.max()),
                            "mean_count": float(per_strain_count.mean()),
                            "zero_share": float((per_strain_count == 0).mean()),
                            "best_sha256": genome_hash(pops[i], best)})
            if g == 0:
                rec.generation0 = {"train_ids": ids[i].tolist(), "counts": c_i.astype(int).tolist(),
                                   "progress": p_i.round(6).tolist()}

        if g % checkpoint_every == 0 or g == generations - 1:
            cands = [pops[i].select([int(np.argmax(fits[i]))]) for i in range(R)]
            check()
            with category("holdout"):  # the checkpoints, as `evolve` counts them
                v = rollout_fn(cfg, iface, Genome.cat(cands), validation_ids, world_seed, device,
                               chunk_worlds=R * len(validation_ids))
            if not np.isfinite(v.score).all():
                raise FloatingPointError(f"generation {g}: non-finite validation count")
            for i, rec in enumerate(records):
                rec.checkpoints.append({"generation": g, "validation_mean": float(v.score[i].mean()),
                                        "validation_counts": v.score[i].astype(int).tolist(),
                                        "sha256": genome_hash(cands[i], 0)})
                rec.candidates.append(moved(cands[i].clone(), "cpu"))
            if on_checkpoint is not None:
                on_checkpoint(records, g)

        if g < generations - 1:
            pops = [breed(pops[i], fits[i], cfg, gens[i], scales[i]) for i in range(R)]
        for rec in records:  # wall seconds for the whole batch's generation, checkpoint included
            rec.log[-1]["batch_seconds"] = time.perf_counter() - t_gen
    for i, rec in enumerate(records):
        rec.final = moved(pops[i], "cpu")
    return records


class _Null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
