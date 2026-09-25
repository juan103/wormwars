"""Running populations through worlds and scoring them.

Two rules hold everywhere in here:

- **Common random numbers.** Within one evaluation, every strain plays the *same* world ids. A
  world's map and spawn depend only on (run_seed, world_id), so comparisons between strains are
  paired rather than noisy.
- **Chunking is invisible.** Splitting a rollout to fit memory must not change any score, because a
  world is generated from its id and simulated independently of its batch-mates.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from ..brain import Brain, Genome
from ..config import Config
from ..interface import Interface
from ..world import World


@dataclass
class RolloutResult:
    """Per (strain, world) outcomes. Axis order is [strains, worlds]."""

    score: np.ndarray  # the fitness actually selected on
    energy: np.ndarray  # surviving swarm energy
    alive: np.ndarray  # surviving weys
    eaten: np.ndarray  # food removed from the map by this swarm
    ticks: int
    ledger_error: float
    pellet_eaten: np.ndarray | None = None  # corpse pellets eaten, [strains, worlds]
    food_start: np.ndarray | None = None  # plant food on the map at tick 0, [strains, worlds]

    def per_strain(self) -> np.ndarray:
        return self.score.mean(axis=1)


def foraging_score(world: World, swarm: int = 0) -> torch.Tensor:
    """Surviving energy as a fraction of what the swarm started with.

    1.0 means the swarm ended with exactly the energy it began with; 0.0 means it is all dead.
    Comparable across swarm sizes, which matters once headcounts vary.
    """
    start = world.cfg.world.start_energy * world.n_weys
    return world.swarm_energy()[:, swarm] / start


def _play(cfg, iface, brain, world_ids, run_seed, device, combat_stage=0, ticks=None, recorder=None):
    """Every strain of `brain` on every world id. `brain` is a Brain or anything World accepts."""
    n_sub, n_ids = brain.n_strains, len(world_ids)
    strain_of = torch.arange(n_sub, device=device).repeat_interleave(n_ids).reshape(-1, 1)
    ids = np.tile(world_ids, n_sub)
    world = World(
        cfg, iface, brain, strain_of, run_seed=run_seed, world_ids=ids,
        device=device, combat_stage=combat_stage,
    )
    if recorder is not None:
        recorder.attach(world)
    food0 = world.fields[:, world.ch.FOOD].sum(dim=(1, 2)).clone()
    world.run(ticks)
    food1 = world.fields[:, world.ch.FOOD].sum(dim=(1, 2))
    shape = (n_sub, n_ids)
    return {
        "score": foraging_score(world).reshape(shape).cpu().numpy(),
        "energy": world.swarm_energy()[:, 0].reshape(shape).cpu().numpy(),
        "alive": world.n_alive()[:, 0].reshape(shape).cpu().numpy(),
        "eaten": (food0 - food1).reshape(shape).cpu().numpy(),
        "pellet": world.pellet_eaten.reshape(shape).cpu().numpy(),
        "food0": food0.reshape(shape).cpu().numpy(),
        "err": world.energy_ledger_error().abs().max().item(),
        "ticks": world.tick_count,
    }


def rollout_brain(cfg, iface, brain, world_ids, run_seed, device="cpu", ticks=None) -> RolloutResult:
    """Like `rollout`, for an already-built brain (for example a scripted controller)."""
    world_ids = np.asarray(world_ids, dtype=np.int64)
    r = _play(cfg, iface, brain, world_ids, run_seed, device, ticks=ticks)
    return RolloutResult(r["score"], r["energy"], r["alive"], r["eaten"], r["ticks"], r["err"],
                         pellet_eaten=r["pellet"], food_start=r["food0"])


def rollout(
    cfg: Config,
    iface: Interface,
    genome: Genome,
    world_ids: np.ndarray,
    run_seed: int,
    device="cpu",
    combat_stage: int = 0,
    chunk_worlds: int | None = None,
    ticks: int | None = None,
    recorder=None,
    brain_hook=None,
) -> RolloutResult:
    """Play every strain on every world id, single swarm.

    Returns scores shaped [strains, len(world_ids)].
    """
    world_ids = np.asarray(world_ids, dtype=np.int64)
    n_ids = len(world_ids)
    S = genome.n_strains
    chunk_worlds = chunk_worlds or cfg.evo.chunk_worlds
    strains_per_chunk = max(1, chunk_worlds // max(n_ids, 1))

    scores, energies, alives, eatens, pellets = [], [], [], [], []
    worst_err = 0.0
    used_ticks = 0

    for lo in range(0, S, strains_per_chunk):
        hi = min(lo + strains_per_chunk, S)
        sub = genome.select(list(range(lo, hi)))
        brain = Brain(sub)
        if brain_hook is not None:
            # lets callers modify the brain per chunk (e.g. apply a different ablation per strain)
            brain_hook(brain, lo, hi)
        r = _play(cfg, iface, brain, world_ids, run_seed, device, combat_stage, ticks,
                  recorder if lo == 0 else None)
        scores.append(r["score"])
        energies.append(r["energy"])
        alives.append(r["alive"])
        eatens.append(r["eaten"])
        pellets.append(r["pellet"])
        worst_err = max(worst_err, r["err"])
        used_ticks = r["ticks"]

    return RolloutResult(
        score=np.concatenate(scores),
        energy=np.concatenate(energies),
        alive=np.concatenate(alives),
        eaten=np.concatenate(eatens),
        ticks=used_ticks,
        ledger_error=worst_err,
        pellet_eaten=np.concatenate(pellets),
    )


class SeedPool:
    """Training and held-out world ids for one run, derived from the run seed.

    The two pools are disjoint ranges, so a held-out world can never have been selected on. Which
    training ids a generation uses is itself derived from (run_seed, generation), so a run is
    reproducible without storing the schedule.
    """

    def __init__(self, cfg: Config, run_seed: int):
        self.cfg, self.run_seed = cfg, run_seed
        e = cfg.evo
        self.holdout = np.arange(e.holdout_seed_base, e.holdout_seed_base + e.holdout_worlds)

    def train_ids(self, generation: int, n: int | None = None) -> np.ndarray:
        e = self.cfg.evo
        n = n or e.worlds_per_strain
        rng = np.random.default_rng([self.run_seed, generation, 0xC0FFEE])
        return e.train_seed_base + rng.integers(0, e.train_seed_span, size=n)
