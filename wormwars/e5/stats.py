"""E5-1's confirmatory reading, O1 (docs/E5/E5-1-DESIGN.md §5).

Δ is the mean over N2's runs minus the mean over SH-route's graph means (each the mean of its runs).
The registered interval (draft 3) is Welch's 90% t interval over N2's runs and the graph means: one
level, since the graph means already carry their within-graph noise (Astra, r1), with no resample count
or seed (Fable, r2). The 90% percentile bootstrap at the same single level is reported beside it.
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
    if not all(np.isfinite([d, lo, hi, delta])) or delta <= 0:
        raise ValueError("label needs finite d, bounds and a positive δ")
    if lo > hi:
        raise ValueError("the interval's lower bound is above its upper bound")
    if lo > 0:
        return LABELS[0] if d >= delta else LABELS[1]
    if hi < 0:
        return LABELS[2] if d <= -delta else LABELS[3]
    if -delta < lo and hi < delta:
        return LABELS[4]
    return LABELS[5]


def _scores(n2, runs) -> tuple[np.ndarray, np.ndarray]:
    n2 = np.asarray(n2, dtype=float)
    runs = np.asarray(runs, dtype=float)
    if n2.ndim != 1 or runs.ndim != 2 or len(n2) < 2 or runs.shape[0] < 2:
        raise ValueError("need N2's run scores [n >= 2] and SH-route's [graphs >= 2, runs]")
    if not (np.isfinite(n2).all() and np.isfinite(runs).all()):
        raise ValueError("scores must be finite")
    return n2, runs


def welch_many(n2: np.ndarray, graph_means: np.ndarray):
    """Δ and Welch's 90% bounds for each row: n2 [S, n], graph_means [S, g]."""
    from scipy import stats as sps
    n2, gm = np.atleast_2d(n2), np.atleast_2d(graph_means)
    n, g = n2.shape[1], gm.shape[1]
    v1, v2 = n2.var(1, ddof=1) / n, gm.var(1, ddof=1) / g
    se2 = v1 + v2
    with np.errstate(invalid="ignore", divide="ignore"):
        nu = np.where(se2 > 0, se2 ** 2 / (v1 ** 2 / (n - 1) + v2 ** 2 / (g - 1)), np.inf)
    h = sps.t.ppf(0.95, nu) * np.sqrt(se2)
    d = n2.mean(1) - gm.mean(1)
    return d, d - h, d + h


def welch_interval(n2, runs) -> tuple[float, float, float]:
    """O1's registered interval: N2's run scores [n] and SH-route's [graph, run]."""
    n2, runs = _scores(n2, runs)
    d, lo, hi = welch_many(n2, runs.mean(1))
    return float(d[0]), float(lo[0]), float(hi[0])


def latent_graph_sd(runs) -> float:
    """SH-route's between-graph SD: the variance of the graph means less the within-graph sampling variance
    (the mean within-graph variance over the runs per graph), truncated at 0."""
    runs = np.asarray(runs, dtype=float)
    within = runs.var(1, ddof=1).mean() / runs.shape[1]
    return float(np.sqrt(max(runs.mean(1).var(ddof=1) - within, 0.0)))


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
    """The percentile bootstrap, reported beside Welch: N2's run scores [n] and SH-route's [graph, run]."""
    n2, runs = _scores(n2, runs)
    gm = runs.mean(1)
    d, lo, hi = intervals(n2, gm, n_boot, np.random.default_rng(seed))
    return float(d[0]), float(lo[0]), float(hi[0])
