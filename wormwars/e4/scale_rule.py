"""E4's cross-link scale rule (docs/E4/E4-DESIGN.md v3 §1), decided before the formal run.

- **The candidates:** the factors 0.25, 0.5, 1.0, 2.0 and 4.0 on the weight sigma (2 and 4 added after both
  reviewers of the code: at w_sigma 0.08 the first three cannot reach).
- **The reach:** the probability that a single neutral slot ends at |w| ≥ 1, along simulated champion lineages: a
  Gaussian walk from 0 with one step per mutation on the lineage, clipped at ±w_max after every step as
  `Genome.clamp_` does. The counts are the pilot's lineages (`lineage.mutations`) scaled to the formal horizon,
  share × G_formal (`formal_counts`), each lineage weighted equally.
- **The load bound:** the pilot's generation-1 X+ mean fitness under common random numbers within 0.25 visits per
  wey of X0's.
- **The choice:** the smallest candidate with reach ≥ 0.5 that meets the load bound; if none, the largest meeting the
  load bound, labelled reach-deficient (both reviewers: the smallest would make the slots barely move); if none
  meets the load bound, no factor.
"""

from __future__ import annotations

import numpy as np

CANDIDATES = (0.25, 0.5, 1.0, 2.0, 4.0)
THRESHOLD = 1.0
MIN_REACH = 0.5
LOAD_BOUND = 0.25


def walk(count: int, sigma: float, factor: float, w_max: float, n_sim: int, rng) -> np.ndarray:
    w = np.zeros(n_sim)
    for _ in range(int(count)):
        w = np.clip(w + rng.normal(0.0, sigma * factor, n_sim), -w_max, w_max)
    return w


def reach(counts, sigma: float, factor: float, w_max: float, *, n_sim: int = 20_000, seed: int = 0) -> float:
    rng = np.random.default_rng(seed)
    return float(np.mean([np.mean(np.abs(walk(c, sigma, factor, w_max, n_sim, rng)) >= THRESHOLD) for c in counts]))


def load_ok(x_plus_mean: float, x0_mean: float, bound: float = LOAD_BOUND) -> bool:
    return abs(float(x_plus_mean) - float(x0_mean)) <= bound


def formal_counts(counts, *, g_pilot: int, g_formal: int) -> list:
    return [int(round(c * g_formal / g_pilot)) for c in counts]


def largest_load_passing(load_by_factor: dict, candidates=CANDIDATES):
    ok = [f for f in sorted(candidates) if load_by_factor[f]]
    return ok[-1] if ok else None


def choose(reach_by_factor: dict, load_by_factor: dict, candidates=CANDIDATES) -> dict:
    ok = [f for f in sorted(candidates) if load_by_factor[f]]
    both = [f for f in ok if reach_by_factor[f] >= MIN_REACH]
    base = {"reach": reach_by_factor, "load_ok": load_by_factor}
    if both:
        return {"factor": both[0], "rule": "reach and load", **base}
    if ok:
        return {"factor": ok[-1], "rule": "reach-deficient: the largest factor meeting the load bound", **base}
    return {"factor": None, "rule": "no candidate meets the load bound", **base}
