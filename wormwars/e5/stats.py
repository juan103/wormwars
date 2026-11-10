"""E5-1's confirmatory reading, O1 (docs/E5/E5-1-DESIGN.md §5).

Δ is the mean over N2's runs minus the mean over SH-route's graph means (each the mean of its runs).
The interval is a 90% percentile bootstrap over N2's runs and over the graph means, independently: a
single level, since resampling runs inside each drawn graph counts within-graph noise twice (Astra, r1).
Inference is conditional on the frozen test suite.

The labels are symmetric (Fable, r1) and keep a detected but small difference apart (Astra, r1).
"""

from __future__ import annotations

import numpy as np

LABELS = (
    "N2 ahead, estimate at least δ",
    "N2 ahead, estimate below δ",
    "SH-route ahead, estimate at least δ",
    "SH-route ahead, estimate below δ",
    "no difference of δ either way",
    "inconclusive",
)


def label(d: float, lo: float, hi: float, delta: float) -> str:
    """The rules, in order: an interval above 0, below 0, inside (−δ, δ), or none of these."""
    if lo > hi:
        raise ValueError("the interval's lower bound is above its upper bound")
    if lo > 0:
        return LABELS[0] if d >= delta else LABELS[1]
    if hi < 0:
        return LABELS[2] if d <= -delta else LABELS[3]
    if -delta < lo and hi < delta:
        return LABELS[4]
    return LABELS[5]


def intervals(n2: np.ndarray, graph_means: np.ndarray, n_boot: int, rng: np.random.Generator):
    """Δ and its 90% percentile bounds for each row: n2 [S, n], graph_means [S, g]."""
    n2, gm = np.atleast_2d(n2), np.atleast_2d(graph_means)
    s, n = n2.shape
    g = gm.shape[1]
    d = n2.mean(1) - gm.mean(1)
    i = rng.integers(0, n, (s, n_boot, n))
    j = rng.integers(0, g, (s, n_boot, g))
    rows = np.arange(s)[:, None, None]
    boot = n2[rows, i].mean(2) - gm[rows, j].mean(2)
    lo, hi = np.percentile(boot, [5, 95], axis=1)
    return d, lo, hi


def delta_interval(n2, runs, n_boot: int = 10_000, seed: int = 0) -> tuple[float, float, float]:
    """O1 for one experiment: N2's run scores [n] and SH-route's [graph, run]."""
    gm = np.asarray(runs, dtype=float).mean(1)
    d, lo, hi = intervals(np.asarray(n2, dtype=float), gm, n_boot, np.random.default_rng(seed))
    return float(d[0]), float(lo[0]), float(hi[0])
