"""03a's arms on the simulator (experiments/03a-self-consistency/DESIGN.md v7.1 §3, §4, §6).

**NIP brains are evolved pinned on the intact mask:** generation 0 is the run's ordinary initial population with every
weight and conductance on an edge touching X set to zero, and those edges' mutation scales are zero (`Genome.mutate`'s
scales, E4s), so they stay exactly zero through every mutation (tested). A brain with X's edges at zero is X deleted
(tests/test_e03a_reinsert.py), so this is evolution with X deleted; pinning instead of a separate mask lets the NIP
brains of several targets share one lockstep batch with the selector and MIP brains, and keeps every arm's initial
magnitudes on one normalisation (`Genome.random` scales by the mean anatomical weight of the mask's edges).

**Scoring** is always the raw count of targets reached, on worlds shared by everything compared.
"""

from __future__ import annotations

import numpy as np
import torch

from ..brain import BrainSpec, Genome
from ..deletion import delete_neurons
from ..e04a import evolve as EV
from ..evo.rollout import rollout
from .reinsert import Reinsertion, XState


def x_edges(spec: BrainSpec, x: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Boolean masks over the chemical edges and the gap junctions that touch X."""
    return (spec.chem_i == x) | (spec.chem_j == x), (spec.gap_i == x) | (spec.gap_j == x)


def nip_scales(spec: BrainSpec, x: int) -> dict:
    """Mutation scales that pin X's edges: 0 on them, 1 everywhere else (τ and bias unscaled; X is isolated)."""
    c, g = x_edges(spec, x)
    return {"w": (~c).to(torch.float32).cpu(), "g": (~g).to(torch.float32).cpu()}


def nip_initial(spec: BrainSpec, bcfg, run_seed: int, population: int, x: int) -> Genome:
    """The run's ordinary generation 0 (`e04a.evolve.initial_population`'s draw, on the CPU) with X's edges at zero."""
    g = EV.initial_population(spec, bcfg, run_seed, population, "cpu")
    c, gg = x_edges(g.spec, x)
    w, cond = g.w.clone(), g.g.clone()
    w[:, c.cpu()] = 0.0
    cond[:, gg.cpu()] = 0.0
    return g.with_params(w=w, g=cond)


def hooks(spec: BrainSpec, bcfg, population: int, target_of: dict):
    """`initial` and `mutation_scales` for `evolve_batch`: runs in `target_of` (run number -> X) are NIP brains,
    every other run is an intact brain (selector or MIP), unchanged."""
    def initial(r):
        x = target_of.get(r.run)
        if x is None:
            return EV.initial_population(spec, bcfg, r.run_seed, population, "cpu")
        return nip_initial(spec, bcfg, r.run_seed, population, x)

    def scales(r):
        x = target_of.get(r.run)
        return None if x is None else nip_scales(spec, x)

    return initial, scales


def play(cfg, iface, genome: Genome, world_ids, world_seed: int, device, chunk_worlds: int | None = None,
         rollout_fn=rollout):
    """The full rollout result (counts, final head positions, the target event table), the genome moved to `device`."""
    ids = np.asarray(world_ids, dtype=np.int64)
    return rollout_fn(cfg, iface, EV.moved(genome, device), ids, world_seed, device,
                      chunk_worlds=chunk_worlds or genome.n_strains * ids.shape[-1])


def same_episodes(a, b) -> bool:
    """Two rollout results agree on counts, final head positions and every target event, exactly (Astra: equal counts
    alone can hide different trajectories)."""
    def eq(x, y):  # NaN marks an unfinished leg in the event table, and NaN equals NaN here
        x, y = np.asarray(x), np.asarray(y)
        return x.shape == y.shape and np.array_equal(x, y, equal_nan=x.dtype.kind == "f" and y.dtype.kind == "f")

    if not eq(a.score, b.score):
        return False
    if (a.final_head is None) != (b.final_head is None) or (a.final_head is not None and not eq(a.final_head, b.final_head)):
        return False
    ea, eb = a.events or {}, b.events or {}
    return set(ea) == set(eb) and all(eq(ea[k], eb[k]) for k in ea)


def counts(cfg, iface, genome: Genome, world_ids, world_seed: int, device, chunk_worlds: int | None = None,
           rollout_fn=rollout) -> np.ndarray:
    """[strains, worlds] raw counts."""
    r = play(cfg, iface, genome, world_ids, world_seed, device, chunk_worlds, rollout_fn)
    out = np.asarray(r.score, dtype=np.float64)
    if not np.isfinite(out).all():
        raise FloatingPointError("a non-finite count")
    return out


def score_states(cfg, iface, reins: Reinsertion, states: XState, world_ids, world_seed: int, device,
                 chunk_worlds: int | None = None, rollout_fn=rollout) -> np.ndarray:
    """[states, worlds]: each state of X's wiring, reinserted into the reinsertion's background."""
    return counts(cfg, iface, reins.genome(states), world_ids, world_seed, device, chunk_worlds, rollout_fn)


def deletion_scan(cfg, iface, brain: Genome, neurons: list, world_ids, world_seed: int, device,
                  chunk_worlds: int | None = None, rollout_fn=rollout) -> tuple[np.ndarray, np.ndarray]:
    """One brain intact and with each neuron deleted (D044), on the same worlds: ([worlds], [neurons, worlds])."""
    if brain.n_strains != 1:
        raise ValueError("one brain")
    batch = delete_neurons(brain.select([0] * (len(neurons) + 1)), [[]] + [[int(k)] for k in neurons])
    out = counts(cfg, iface, batch, world_ids, world_seed, device, chunk_worlds, rollout_fn)
    return out[0], out[1:]
