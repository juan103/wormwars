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

from .. import accounting as acct
from ..brain import BrainSpec, Genome
from ..config import Config
from ..interface import Interface
from .genomes import genome_hash, nickname, save_population, strain_id
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
    best_sha256: str = ""  # the full hash of the logged best genome (T0, D067)


@dataclass
class RunResult:
    graph: str
    run: int
    run_seed: int
    log: list = field(default_factory=list)
    champion: Genome | None = None
    champion_id: str = ""
    gpu_seconds: float = 0.0
    evaluations: int = 0  # selection strain-worlds only, as before; see `compute` for everything
    snapshots: dict = field(default_factory=dict)  # generation -> best-of-generation strain
    compute: dict = field(default_factory=dict)  # per category, from the ledger (T0, D068)

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

    return Genome.cat([genome.select(list(elites)), children])


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
    checkpoint_ids: np.ndarray | None = None,
    snapshots: tuple = (),
) -> RunResult:
    """One independent evolutionary run. This is the unit of statistical analysis."""
    e = cfg.evo
    if e.generations < 1:
        raise ValueError("evolve needs at least one generation")
    if e.islands > 1:  # supported island settings, checked before anything runs (T0 item 5, D073)
        sizes = np.bincount(np.arange(e.population) % e.islands, minlength=e.islands)
        if sizes.min() == 0:
            raise ValueError(f"{e.islands} islands for {e.population} strains leaves an island empty")
        if e.migrate_every < 1:
            raise ValueError("migrate_every must be at least 1 with islands")
        if not 0 <= e.migrants <= sizes.min() // 2:
            raise ValueError(f"migrants={e.migrants} exceeds half the smallest island ({sizes.min()} strains): "
                             "an island would overwrite its own best strains with immigrants")
    gen_t = torch.Generator(device=device).manual_seed(run_seed)
    genome = Genome.random(spec, cfg.brain, e.population, generator=gen_t, device=device)
    pool = SeedPool(cfg, run_seed)
    result = RunResult(graph=spec.label, run=run, run_seed=run_seed)
    t_start = time.perf_counter()
    ledger_before = acct.LEDGER.snapshot()

    island_of = np.arange(e.population) % e.islands if e.islands > 1 else np.zeros(e.population, int)

    for g in range(e.generations):
        t0 = time.perf_counter()
        ids = pool.train_ids(g)
        with acct.category("selection"):
            res = evaluate_on(cfg, iface, genome, ids, run_seed, device, combat_stage)
        fit = res.per_strain()
        result.evaluations += fit.size * len(ids)
        if g in snapshots:
            result.snapshots[g] = genome.select([int(np.argmax(fit))])

        hb = hm = None
        if g % holdout_every == 0 or g == e.generations - 1 or g in snapshots:
            best_i = int(np.argmax(fit))
            suite = pool.holdout if checkpoint_ids is None else np.asarray(checkpoint_ids)
            # one evaluation, counted once: a snapshot generation's check is the snapshot
            with acct.category("snapshot" if g in snapshots else "holdout"):
                hres = evaluate_on(
                    cfg, iface, genome.select([best_i]), suite, run_seed, device, combat_stage
                )
            hb = float(hres.per_strain()[0])
            hm = hb

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
            best_sha256=genome_hash(genome, best_i),
        )
        result.log.append(entry)
        if verbose and (g % log_every == 0 or g == e.generations - 1):
            hold = f" holdout {hb:6.3f}" if hb is not None else ""
            print(
                f"  [{spec.label} run{run:02d}] g{g:04d} best {entry.best:6.3f} "
                f"mean {entry.mean:6.3f}{hold}  {entry.elapsed_s:5.2f}s  {entry.best_nickname}"
            )

        if g < e.generations - 1:
            # migration after logging, so the log describes the evaluated generation; the
            # migrants carry their own fitness into breeding (D064)
            if e.islands > 1 and g > 0 and g % e.migrate_every == 0:
                genome, fit = _migrate(genome, fit, island_of, e, gen_t)
            genome = _breed_islands(genome, fit, island_of, cfg, gen_t)

    # The champion is the final generation's logged best, from the evaluation already made. The
    # first version re-evaluated the population on the same worlds, which cost an uncounted
    # evaluation and under default CUDA could pick a different strain than the log names (D066).
    best_per_generation = np.array([g.best for g in result.log])
    best_i = int(np.argmax(fit))
    result.champion = genome.select([best_i])
    result.champion_id = strain_id(spec.label, run, e.generations - 1, 1)
    result.gpu_seconds = time.perf_counter() - t_start
    result.compute = acct.LEDGER.since(ledger_before)

    if out_dir is not None:
        out = Path(out_dir)
        save_population(
            out / f"{spec.label}-run{run:02d}-final.npz",
            genome,
            cfg=cfg,
            run=run,
            run_seed=run_seed,
            generations=e.generations,
            fitness=[float(x) for x in fit],  # per strain, index-aligned with the genomes
            best_per_generation=[float(x) for x in best_per_generation],
        )
        (out / f"{spec.label}-run{run:02d}-log.json").write_text(
            json.dumps([asdict(x) for x in result.log], indent=2), encoding="utf-8"
        )
    return result


def _breed_islands(genome, fit, island_of, cfg, gen_t) -> Genome:
    """Each island breeds from its own members only, with `max(1, elites // islands)` elites and
    `max(2, truncation // islands)` parents per island. That rule changes the *total* selection
    pressure with the island count: with elites=3, two islands keep 2 elites in total and four
    keep 4, and elites=0 still keeps one per island. Compare an island arm with a one-island arm
    only with this in mind (Fable, D065; documented in D073)."""
    if cfg.evo.islands <= 1:
        return breed(genome, fit, cfg, gen_t)
    # each island's children are written back into that island's own slots, so `island_of`
    # stays true from generation to generation. The first version concatenated the islands in
    # blocks while `island_of` stayed interleaved, mixing islands from the second generation (D064).
    out = genome
    for isl in range(cfg.evo.islands):
        idx = np.flatnonzero(island_of == isl)
        sub_cfg = cfg.copy()
        sub = genome.select(list(idx))
        sub_cfg.evo.population = len(idx)
        sub_cfg.evo.elites = max(1, cfg.evo.elites // cfg.evo.islands)
        sub_cfg.evo.truncation = max(2, cfg.evo.truncation // cfg.evo.islands)
        out = out.assign(idx, breed(sub, fit[idx], sub_cfg, gen_t))
    return out


def _migrate(genome, fit, island_of, e, gen_t):
    """Send each island's best to the next island, replacing its worst. Within a run only.
    Returns the new population and its fitness: every migrant keeps all of its parameters,
    its Dale sign vector included, and its own fitness (D064)."""
    out = genome
    new_fit = np.array(fit, dtype=float, copy=True)
    for isl in range(e.islands):
        src = np.flatnonzero(island_of == isl)
        dst = np.flatnonzero(island_of == (isl + 1) % e.islands)
        best = src[np.argsort(-fit[src])[: e.migrants]]
        worst = dst[np.argsort(fit[dst])[: e.migrants]]
        out = out.assign(worst, genome.select(list(best)))  # read from the original: synchronous
        new_fit[worst] = fit[best]
    return out, new_fit
