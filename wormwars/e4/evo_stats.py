"""The evolutionary E4-D's decision rule (docs/E4/E4-D-EVO-DESIGN.md v2.1 §6, Astra; δ the owner's, D266).

- `reading`: one arm's per-run gains (each champion's real-first share on its own test block, minus 0.5). The mean
  gain's one-sided 95% t bounds L and U, read against δ in five states; the one-sided sign-flip p beside, labelled
  distributional.
- `states`: the same states for many simulated arms at once (the power analysis), as indices into `STATES`.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

ALPHA = 0.05  # each bound one-sided
DELTA = 0.15  # the owner's margin (D266)
STATES = ("practically relevant transfer found", "weak transfer found",
          "transfer detected; its practical size unresolved", "practical gain excluded; transfer not detected",
          "inconclusive")


def _state_index(lo, hi, delta):
    lo, hi = np.asarray(lo), np.asarray(hi)
    return np.select([lo > delta, (lo > 0) & (hi < delta), lo > 0, hi < delta], [0, 1, 2, 3], default=4)


def bounds(D, *, alpha: float = ALPHA):
    """The one-sided 1 − α t bounds of the mean over the last axis."""
    D = np.asarray(D, dtype=np.float64)
    R = D.shape[-1]
    m = D.mean(-1)
    se = D.std(-1, ddof=1) / math.sqrt(R)
    q = float(stats.t.ppf(1 - alpha, R - 1))
    return m, m - q * se, m + q * se


def states(D, *, delta: float = DELTA, alpha: float = ALPHA) -> np.ndarray:
    _, lo, hi = bounds(D, alpha=alpha)
    return _state_index(lo, hi, delta)


def sign_flip_one_sided(d, *, chunk: int = 1 << 16) -> float:
    """The share of the 2^R sign patterns whose mean reaches the observed mean (smallest 1/2^R); exact under sign
    symmetry about 0, so its label is distributional (Fable, Astra)."""
    d = np.asarray(d, dtype=np.float64)
    R = len(d)
    obs = d.mean() - 1e-12
    bits = np.arange(R, dtype=np.int64)
    hits = 0
    for lo in range(0, 1 << R, chunk):
        k = np.arange(lo, min(lo + chunk, 1 << R), dtype=np.int64)
        signs = 1.0 - 2.0 * ((k[:, None] >> bits) & 1)
        hits += int(((signs @ d) / R >= obs).sum())
    return hits / float(1 << R)


def reading(d, *, delta: float = DELTA, alpha: float = ALPHA, evaluable: bool = True) -> dict:
    if not evaluable:
        return {"state": "not evaluable"}
    d = np.asarray(d, dtype=np.float64)
    m, lo, hi = bounds(d, alpha=alpha)
    return {"n": len(d), "mean": float(m), "lo": float(lo), "hi": float(hi), "alpha_one_sided": alpha, "delta": delta,
            "state": STATES[int(_state_index(lo, hi, delta))], "interval_label": "approximate (model-based)",
            "sign_flip_p_one_sided": sign_flip_one_sided(d), "sign_flip_label": "distributional (sign symmetry)"}
