"""Truncation selection with elitism, Gaussian mutation, optional islands.

Deliberately plain. The experiment compares wiring, so the search algorithm is held fixed and
identical across N2, SH and RD: same population size, same mutation settings, same evaluation
budget, same initialisation distribution.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import torch

from ..brain import BrainSpec, Genome
from ..config import Config
from ..interface import Interface
from .genomes import nickname, save_population, strain_id
from .rollout import RolloutResult, SeedPool, rollout


@dataclass
class GenerationLog:
    generation: int
    best: float
    mean: float
    median: float
    holdout_best: float | None
    holdout_mean: float | None
    elapsed_s: float
    evaluations: int
    ledger_error: float
    best_nickname: str


@dataclass
class RunResult:
    graph: str
    run: int
    run_seed: int
    log: list = field(default_factory=list)
    champion: Genome | None = None
    champion_id: str = ""
    gpu_seconds: float = 0.0
    evaluations: int = 0

    def history(self) -> dict[str, np.ndarray]:
        return {
            k: np.array([getattr(g, k) for g in self.log])
            for k in ("generation", "best", "mean", "median", "holdout_best", "holdout_mean")
        }


def evaluate_on(cfg, iface, genome, ids, run_seed, device, combat_stage=0) -> RolloutResult:
    return rollout(
        cfg, iface, genome, ids, run_seed=run_seed, device=device, combat_stage=combat_stage
    )


def breed(
    genome: Genome,
    fitness: np.ndarray,
    cfg: Config,
    generator: torch.Generator,
) -> Genome:
    """Truncation selection + elitism + Gaussian mutation, bounds re-clamped inside `mutate`."""
    e = cfg.evo
    order = np.argsort(-fitness)  # best first
    elites = order[: e.elites]
    parents = order[: min(e.truncation, len(order))]

    n_children = e.population - len(elites)
    pick = parents[
        torch.randint(
            len(parents), (n_children,), generator=generator, device=genome.device
        ).cpu().numpy()
    ]
    children = genome.select(list(pick))
    children.mutate(cfg.mutation, generator=generator)

    keep = genome.select(list(elites))
    return Genome(
        genome.spec,
        genome.cfg,
        torch.cat([keep.w, children.w]),
        torch.cat([keep.g, children.g]),
        torch.cat([keep.tau, children.tau]),
        torch.cat([keep.bias, children.bias]),
        None
        if genome.dale_sign is None
        else torch.cat([keep.dale_sign, children.dale_sign]),
    )


def evolve(
    cfg: Config,
    iface: Interface,
    spec: BrainSpec,
    run: int,
    run_seed: int,
    device="cpu",
    combat_stage: int = 0,
    log_every: int = 1,
    holdout_every: int = 5,
    out_dir: str | Path | None = None,
    verbose: bool = True,
) -> RunResult:
    """One independent evolutionary run. This is the unit of statistical analysis."""
    e = cfg.evo
    gen_t = torch.Generator(device=device).manual_seed(run_seed)
    genome = Genome.random(spec, cfg.brain, e.population, generator=gen_t, device=device)
    pool = SeedPool(cfg, run_seed)
    result = RunResult(graph=spec.label, run=run, run_seed=run_seed)
    t_start = time.perf_counter()

    island_of = np.arange(e.population) % e.islands if e.islands > 1 else np.zeros(e.population, int)

    for g in range(e.generations):
        t0 = time.perf_counter()
        ids = pool.train_ids(g)
        res = evaluate_on(cfg, iface, genome, ids, run_seed, device, combat_stage)
        fit = res.per_strain()
        result.evaluations += fit.size * len(ids)

        hb = hm = None
        if g % holdout_every == 0 or g == e.generations - 1:
            best_i = int(np.argmax(fit))
            hres = evaluate_on(
                cfg, iface, genome.select([best_i]), pool.holdout, run_seed, device, combat_stage
            )
            hb = float(hres.per_strain()[0])
            hm = hb

        if e.islands > 1 and g > 0 and g % e.migrate_every == 0:
            genome, island_of = _migrate(genome, fit, island_of, e, gen_t)

        best_i = int(np.argmax(fit))
        entry = GenerationLog(
            generation=g,
            best=float(fit.max()),
            mean=float(fit.mean()),
            median=float(np.median(fit)),
            holdout_best=hb,
            holdout_mean=hm,
            elapsed_s=time.perf_counter() - t0,
            evaluations=fit.size * len(ids),
            ledger_error=res.ledger_error,
            best_nickname=nickname(genome, best_i),
        )
        result.log.append(entry)
        if verbose and (g % log_every == 0 or g == e.generations - 1):
            hold = f" holdout {hb:6.3f}" if hb is not None else ""
            print(
                f"  [{spec.label} run{run:02d}] g{g:04d} best {entry.best:6.3f} "
                f"mean {entry.mean:6.3f}{hold}  {entry.elapsed_s:5.2f}s  {entry.best_nickname}"
            )

        if g < e.generations - 1:
            genome = _breed_islands(genome, fit, island_of, cfg, gen_t)

    fit_final = np.array([g.best for g in result.log])
    best_i = int(np.argmax(evaluate_on(cfg, iface, genome, pool.train_ids(e.generations - 1),
                                       run_seed, device, combat_stage).per_strain()))
    result.champion = genome.select([best_i])
    result.champion_id = strain_id(spec.label, run, e.generations - 1, 1)
    result.gpu_seconds = time.perf_counter() - t_start

    if out_dir is not None:
        out = Path(out_dir)
        save_population(
            out / f"{spec.label}-run{run:02d}-final.npz",
            genome,
            cfg=cfg,
            run=run,
            run_seed=run_seed,
            generations=e.generations,
            fitness=[float(x) for x in fit_final],
        )
        (out / f"{spec.label}-run{run:02d}-log.json").write_text(
            json.dumps([asdict(x) for x in result.log], indent=2), encoding="utf-8"
        )
    return result


def _breed_islands(genome, fit, island_of, cfg, gen_t) -> Genome:
    if cfg.evo.islands <= 1:
        return breed(genome, fit, cfg, gen_t)
    parts = []
    for isl in range(cfg.evo.islands):
        idx = np.flatnonzero(island_of == isl)
        sub_cfg = cfg.copy()
        sub = genome.select(list(idx))
        sub_cfg.evo.population = len(idx)
        sub_cfg.evo.elites = max(1, cfg.evo.elites // cfg.evo.islands)
        sub_cfg.evo.truncation = max(2, cfg.evo.truncation // cfg.evo.islands)
        parts.append(breed(sub, fit[idx], sub_cfg, gen_t))
    return Genome(
        genome.spec,
        genome.cfg,
        torch.cat([p.w for p in parts]),
        torch.cat([p.g for p in parts]),
        torch.cat([p.tau for p in parts]),
        torch.cat([p.bias for p in parts]),
        None if genome.dale_sign is None else torch.cat([p.dale_sign for p in parts]),
    )


def _migrate(genome, fit, island_of, e, gen_t):
    """Send each island's best to the next island, replacing its worst. Within a run only."""
    w = genome.w.clone()
    g_ = genome.g.clone()
    tau = genome.tau.clone()
    b = genome.bias.clone()
    for isl in range(e.islands):
        src = np.flatnonzero(island_of == isl)
        dst = np.flatnonzero(island_of == (isl + 1) % e.islands)
        best = src[np.argsort(-fit[src])[: e.migrants]]
        worst = dst[np.argsort(fit[dst])[: e.migrants]]
        w[worst], g_[worst], tau[worst], b[worst] = (
            genome.w[best],
            genome.g[best],
            genome.tau[best],
            genome.bias[best],
        )
    return (
        Genome(genome.spec, genome.cfg, w, g_, tau, b, genome.dale_sign),
        island_of,
    )
