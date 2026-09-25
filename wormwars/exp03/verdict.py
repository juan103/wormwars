"""Experiment 03's verdict (design v3, D051).

- One-sided exact rank test of N2 against each ensemble: p = (r + 1)/(n + 1).
- For a claim against every ensemble (intersection-union): p_j = max over ensembles, then Holm
  across the primary signals.
- Effect size with its uncertainty: a 90% interval of N2 minus the ensemble mean from a joint
  bootstrap. World indices are resampled once and shared by every graph, genomes within each
  graph, and ensemble graphs with replacement.
- Verdicts are mutually exclusive: distinctive, reversed, compatible, inconclusive.
"""

from __future__ import annotations

import numpy as np

ALPHA = 0.05


def rank_p(x: float, ensemble, direction: str) -> float:
    ens = np.asarray(ensemble, dtype=float)
    if direction == "above":
        r = int((ens >= x).sum())
    elif direction == "below":
        r = int((ens <= x).sum())
    else:
        raise ValueError(direction)
    return (r + 1) / (len(ens) + 1)


def iut_holm(p: dict) -> dict:
    """{signal: {ensemble: p}} -> {signal: {"p_max": .., "p_holm": ..}}."""
    pmax = {j: max(v.values()) for j, v in p.items()}
    order = sorted(pmax, key=lambda j: pmax[j])
    k = len(order)
    out, running = {}, 0.0
    for i, j in enumerate(order):
        running = max(running, min(1.0, (k - i) * pmax[j]))
        out[j] = {"p_max": pmax[j], "p_holm": running}
    return out


def classify(p_holm: float, interval: tuple, margins: dict, direction: str) -> str:
    """`interval` is the 90% interval of N2 minus the ensemble mean."""
    lo, hi = interval
    s = 1.0 if direction == "above" else -1.0
    lo_s, hi_s = sorted((s * lo, s * hi))
    if p_holm <= ALPHA and lo_s > margins["effect"]:
        return "distinctive"
    if hi_s < -margins["effect"]:
        return "reversed"
    if -margins["equivalence"] < lo and hi < margins["equivalence"]:
        return "compatible"
    return "inconclusive"


def _take(d, gi, wi):
    if isinstance(d, dict):
        return {k: v[np.ix_(gi, wi)] for k, v in d.items()}
    return d[np.ix_(gi, wi)]


def _shape(d):
    return next(iter(d.values())).shape if isinstance(d, dict) else d.shape


def effect_interval(n2, ensemble: list, stat, n_boot: int = 2000, seed: int = 0, level: float = 0.90):
    """N2 and each ensemble graph are arrays [genomes, worlds], or dicts of such arrays. `stat`
    maps one graph's (resampled) data to a scalar. Returns the `level` interval of stat(N2)
    minus the mean of stat over the resampled ensemble."""
    rng = np.random.default_rng(seed)
    g_n2, w_all = _shape(n2)
    diffs = np.empty(n_boot)
    for b in range(n_boot):
        wi = rng.integers(0, w_all, w_all)  # shared by every graph: the worlds are shared
        a = stat(_take(n2, rng.integers(0, g_n2, g_n2), wi))
        picks = rng.integers(0, len(ensemble), len(ensemble))
        vals = []
        for p in picks:
            g = _shape(ensemble[p])[0]
            vals.append(stat(_take(ensemble[p], rng.integers(0, g, g), wi)))
        diffs[b] = a - float(np.mean(vals))
    q = (1 - level) / 2
    return float(np.quantile(diffs, q)), float(np.quantile(diffs, 1 - q))
