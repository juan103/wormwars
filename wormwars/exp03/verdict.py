"""Experiment 03's verdict (design v3, D051).

- One-sided exact rank test of N2 against each ensemble: p = (r + 1)/(n + 1).
- For a claim against every ensemble (intersection-union): p_j = max over ensembles, then Holm
  across the primary signals.
- Effect size with its uncertainty: a 90% interval of N2 minus the ensemble mean from a joint
  bootstrap. World indices are resampled once and shared by every graph, genomes within each
  graph, and ensemble graphs with replacement.
- Verdicts are mutually exclusive: distinctive, reversed, consistent, inconclusive.
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


def classify(p_holm: float, p_holm_opposite: float, interval: tuple, margins: dict, direction: str,
             n2_interval: tuple, ensemble) -> str:
    """Mutually exclusive verdicts for one signal against one ensemble (design v3.2, D053).
    `interval`: the 90% interval of N2 minus the ensemble mean. `n2_interval`: N2's own 90%
    measurement interval. `ensemble`: the ensemble's graph values.
    - distinctive: significant in the expected direction and the interval beyond the margin;
    - reversed: the same in the opposite direction, with its own rank test (v3's code declared
      it from the interval alone);
    - consistent: N2's interval lies inside the ensemble's central 90%. That is consistency with
      the ensemble's distribution, not closeness to its mean (both reviewers);
    - inconclusive: otherwise."""
    lo, hi = interval
    s_ = 1.0 if direction == "above" else -1.0
    lo_s, hi_s = sorted((s_ * lo, s_ * hi))
    if p_holm <= ALPHA and lo_s > margins["effect"]:
        return "distinctive"
    if p_holm_opposite <= ALPHA and hi_s < -margins["effect"]:
        return "reversed"
    q05, q95 = np.quantile(np.asarray(ensemble, dtype=float), [0.05, 0.95])
    if q05 <= n2_interval[0] and n2_interval[1] <= q95:
        return "consistent"
    return "inconclusive"


def _as2d(d):
    """Per-genome signals have no world axis: treat them as [genomes, 1]."""
    if isinstance(d, dict):
        return {k: (v[:, None] if np.ndim(v) == 1 else v) for k, v in d.items()}
    return d[:, None] if np.ndim(d) == 1 else d


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
    n2 = _as2d(n2)
    ensemble = [_as2d(e) for e in ensemble]
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
