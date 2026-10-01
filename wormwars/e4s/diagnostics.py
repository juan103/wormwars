"""E4s-0's analysis pieces (docs/E4s/E4s-0-PLAN.md v2).

- `sweep_class`: the residual sweep's classes, from per-k 95% intervals of the paired difference
  from k = 0. "Improves at k" and "is harmed at k" need their bound at k and at the next larger k
  (adjacency, against multiplicity); the last k is only ever a neighbour.
- `g0_bests`: each population's generation-0 best, as `evolve_batch` picks it (unshaped fitness, the
  mean count; ties to the lowest index).
- `module_scales`: mutation scales that move the module's parameters (its neurons' τ and bias, every
  edge with a module neuron at either end) and pin the worm's.
- `motor_stats`: per-strain means over an episode of the world's forward and turn commands, and of the
  share of saturated turn neurons.
- `settle`: the convergence rule for an open-loop response measured against its control.
"""

from __future__ import annotations

import contextlib

import numpy as np
import torch

from ..brain import BrainSpec
from ..world import World

CLASSES = ("rises early", "rises late", "dips first", "harmed", "no detected benefit on the tested grid")


def sweep_class(ks, lo, hi, early_k: float = 1.0) -> dict:
    """`ks` ascending, k = 0 excluded; `lo`, `hi` the 95% bounds of the difference from k = 0."""
    ks, lo, hi = list(ks), np.asarray(lo, float), np.asarray(hi, float)
    if not (len(ks) == len(lo) == len(hi)) or ks != sorted(ks):
        raise ValueError("ks must be ascending, with one bound pair each")
    n = len(ks)
    improves = [bool(lo[i] > 0 and lo[i + 1] > 0) for i in range(n - 1)]
    harmed = [bool(hi[i] < 0 and hi[i + 1] < 0) for i in range(n - 1)]
    first = next((i for i, x in enumerate(improves) if x), None)
    if first is not None:
        before = any(harmed[:first])
        cls = "dips first" if before else ("rises early" if ks[first] <= early_k else "rises late")
        later = any(harmed[first + 1:])
    else:
        cls = "harmed" if any(harmed) else "no detected benefit on the tested grid"
        later = False
    return {"class": cls, "k_star": None if first is None else ks[first], "harmed_at_larger_k": later,
            "improves_at": [k for k, x in zip(ks, improves) if x], "harmed_at": [k for k, x in zip(ks, harmed) if x]}


def g0_bests(score: np.ndarray, population: int) -> np.ndarray:
    """[populations x population, worlds] counts -> each population's best strain (index within it)."""
    score = np.asarray(score, dtype=np.float64)
    if score.shape[0] % population:
        raise ValueError(f"{score.shape[0]} strains do not split into populations of {population}")
    return np.argmax(score.mean(axis=1).reshape(-1, population), axis=1)


def module_scales(ext, factor: float) -> dict:
    spec = BrainSpec.from_connectome(ext)
    n0 = int(ext.meta["worm_neurons"])
    f = float(factor)
    mod = lambda i, j: ((i >= n0) | (j >= n0)).to(torch.float32) * f  # noqa: E731
    node = (torch.arange(spec.n) >= n0).to(torch.float32) * f
    return {"w": mod(spec.chem_i, spec.chem_j).cpu(), "g": mod(spec.gap_i, spec.gap_j).cpu(),
            "tau": node.clone(), "bias": node.clone()}


class _Stats:
    def __init__(self):
        self.worlds = []  # per World instance, in creation order: lists of per-tick tensors

    def per_strain(self, n_strains: int, n_worlds: int, skip_ticks: int = 0) -> dict:
        out = {}
        for key in ("forward", "turn", "saturated_share"):
            parts = [torch.stack(w[key][skip_ticks:]).mean(0).reshape(-1) for w in self.worlds]
            out[key] = torch.cat(parts).cpu().numpy().reshape(n_strains, n_worlds)
        return out


@contextlib.contextmanager
def motor_stats():
    """Records, for every world played inside the block, the forward and turn commands and the share
    of saturated turn neurons (|tanh| > 0.99) at every tick. One swarm, one wey per world (Task N);
    worlds are strain-major, as `rollout` lays them out."""
    inner = World._read_motors
    stats = _Stats()

    def read(self, v_world):
        fwd, turn, pump = inner(self, v_world)
        if not hasattr(self, "_e4s_stats_index"):
            self._e4s_stats_index = len(stats.worlds)
            stats.worlds.append({"forward": [], "turn": [], "saturated_share": []})
        rec = stats.worlds[self._e4s_stats_index]
        idx = torch.cat([self._m_turn_p, self._m_turn_m])
        sat = (torch.tanh(v_world[..., idx]).abs() > 0.99).to(torch.float32).mean(-1)
        rec["forward"].append(fwd.detach().reshape(-1).float())
        rec["turn"].append(turn.detach().reshape(-1).float())
        rec["saturated_share"].append(sat.detach().reshape(-1))
        return fwd, turn, pump

    World._read_motors = read
    try:
        yield stats
    finally:
        World._read_motors = inner


def settle(trace, expected_sign: int | None = None, window: int = 20, tol: float = 0.01,
           negligible: float = 1e-4, frac: float = 0.9) -> dict:
    """`trace`: the change from the control, tick by tick after the input changed."""
    x = np.asarray(trace, dtype=np.float64)
    last, prev = x[-window:].mean(), x[-2 * window:-window].mean()
    out = {"final": float(last), "settled": bool(abs(last - prev) < tol * abs(last)) if last != 0 else True,
           "t90": None, "flag": None}
    if abs(last) < negligible:
        out.update(flag="negligible", settled=True)
        return out
    if expected_sign is not None and np.sign(last) != expected_sign:
        out["flag"] = "wrong sign"
    reached = np.flatnonzero(np.abs(x) >= frac * abs(last))
    out["t90"] = int(reached[0]) if reached.size else None
    if not out["settled"] and out["flag"] is None:
        out["flag"] = "not settled"
    return out
