"""The evolutionary E4-D's trial rollout (docs/E4/E4-D-EVO-DESIGN.md v2.1 §3), a `rollout_fn` for `evolve_batch`.

- Every strain plays each of its mazes (shared, or one row per strain) under both assignments, maze-major, in one
  `TrialWorld` batch; `score` [strains, mazes] is the real-first share over the maze's two trials, so a strain's mean
  over mazes is its real-first count over all 2W trials (the fitness); `progress` is zero.
- **The integrity check,** every call: a strain whose 32 slots are all zero has equal real-first and decoy-first counts
  (D265, Fable); otherwise the call raises.
- **Qualifying ids:** a maze without a qualifying start (design v2.3 §2) is replaced by the next id that has one,
  deterministically and independently of the assignment (scouting found none without; the mapping is a guard).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import torch

from ..e3 import islands as IS
from . import arms as AR
from . import trial as TL
from .train import gated_brain


@lru_cache(maxsize=200_000)
def qualifies(mid: int, seed: int, c: int = 6) -> bool:
    mz, pl, _ = IS.maze_for(run_seed=int(seed), maze_id=int(mid), episode=0, c=c, k_r=0, n_spawns=4)
    c0, c1 = sorted((tuple(pl.a), tuple(pl.b)))
    return TL.start_cell(mz.wall, TL.block_distance(mz, c0), TL.block_distance(mz, c1)) is not None


def qualifying(ids, seed: int) -> np.ndarray:
    """Each id, or the next qualifying id not already used in its row (rows of a 2-D array map independently), so
    rejected ids never collapse onto a neighbour (Astra)."""
    arr = np.asarray(ids)
    rows = arr.reshape(-1, arr.shape[-1]) if arr.ndim else arr.reshape(1, 1)
    out = np.empty_like(rows, dtype=np.int64)
    for r, row in enumerate(rows):
        used = set()
        for k, mid in enumerate(row):
            m = int(mid)
            while m in used or not qualifies(m, int(seed)):
                m += 1
            used.add(m)
            out[r, k] = m
    return out.reshape(arr.shape)


def distinguishes(real_first: np.ndarray, decoy_first: np.ndarray) -> np.ndarray:
    """[strains]: whether any maze's two trials ([strains, mazes, 2]) give unequal real-first and decoy-first counts.
    A strain blind to the assignment enters the same candidate under both, so it never does (D265; per maze, Fable)."""
    return (np.asarray(real_first).sum(axis=2) != np.asarray(decoy_first).sum(axis=2)).any(axis=1)


@dataclass
class TrialResult:
    score: np.ndarray  # [strains, mazes]: the real-first share over the maze's two assignments
    progress: np.ndarray  # zeros
    real_first: np.ndarray  # [strains]: counts over all trials
    decoy_first: np.ndarray
    neither: np.ndarray


def trial_rollout(cx, *, a_source: str = "real", b_source: str = "sum", check: bool = True):
    """A `rollout_fn`: (cfg, iface, genome, world_ids, run_seed, device, **ignored) → `TrialResult`. `cfg` is a trial
    configuration (`trial.trial_config`). `b_source="real"` is the oracle's mapping, which distinguishes the
    assignments without links by design, so the oracle is played with `check=False`; every other use keeps the check."""
    org = cx["org"]
    slots = AR.slot_indices(cx)

    def fn(cfg, iface, genome, world_ids, run_seed, device="cpu", **_):
        S = genome.n_strains
        ids = np.asarray(world_ids)
        ids = np.broadcast_to(ids, (S, ids.shape[-1])) if ids.ndim == 1 else ids
        ids = qualifying(ids, run_seed)
        W = ids.shape[1]
        strain_of = torch.as_tensor(np.repeat(np.arange(S), 2 * W), device=device).view(-1, 1)
        w = TL.TrialWorld(cfg, iface, gated_brain(genome, org.gate, device), strain_of, run_seed=run_seed,
                          world_ids=np.repeat(ids.reshape(-1), 2), assign=np.tile([0, 1], S * W),
                          q_index=org.gate["q"], device=device, a_source=a_source, b_source=b_source)
        w.run(cfg.world.max_ticks)
        ev = w.trial_events()
        rf = ev["real_first"][:, 0].reshape(S, W, 2)
        df = ev["decoy_first"][:, 0].reshape(S, W, 2)
        res = TrialResult(score=rf.mean(axis=2).astype(np.float64), progress=np.zeros((S, W)),
                          real_first=rf.sum(axis=(1, 2)), decoy_first=df.sum(axis=(1, 2)),
                          neither=2 * W - rf.sum(axis=(1, 2)) - df.sum(axis=(1, 2)))
        free = (genome.w[:, slots.to(genome.w.device)] == 0).all(dim=1).cpu().numpy()
        bad = np.flatnonzero(free & distinguishes(rf, df))
        if check and len(bad):
            raise RuntimeError(f"integrity: link-free strains {bad.tolist()} distinguish the assignments")
        return res

    return fn


def champion(validation: np.ndarray, final_fitness: np.ndarray, link_norm: np.ndarray) -> int:
    """The final population's champion (design v2.1 §5): the highest validation share; ties to the higher
    final-generation fitness, then the smaller cross-link norm, then the lowest index."""
    v, f, n = (np.asarray(x, dtype=np.float64) for x in (validation, final_fitness, link_norm))
    order = np.lexsort((np.arange(len(v)), n, -f, -v))
    return int(order[0])
