"""03h's registered statistics (experiments/03h-history-use/DESIGN.md §6)."""

from __future__ import annotations

import numpy as np
from scipy.stats import rankdata

_TOL = 1e-12


def partial_spearman(h, f, s) -> tuple[float, bool]:
    """The partial Spearman correlation of h with f given s: the Pearson correlation of the residuals after regressing
    the ranks of h and of f (average ranks for ties) on the ranks of s, with an intercept. A degenerate case (constant
    h or f, or a residual with no variance) gives (0.0, True), flagged; otherwise (rho, False)."""
    h, f, s = (np.asarray(x, dtype=np.float64).ravel() for x in (h, f, s))
    if not (len(h) == len(f) == len(s)) or len(h) < 3:
        raise ValueError("h, f and s need the same length, at least 3")
    if not (np.isfinite(h).all() and np.isfinite(f).all() and np.isfinite(s).all()):
        raise ValueError("h, f and s must be finite (Astra)")
    rh, rf, rs = rankdata(h), rankdata(f), rankdata(s)
    X = np.column_stack([np.ones_like(rs), rs])

    def resid(y):
        return y - X @ np.linalg.lstsq(X, y, rcond=None)[0]

    eh, ef = resid(rh), resid(rf)
    sh, sf = float(np.sqrt((eh ** 2).sum())), float(np.sqrt((ef ** 2).sum()))
    if sh <= _TOL * len(h) or sf <= _TOL * len(h):
        return 0.0, True
    return float((eh @ ef) / (sh * sf)), False
