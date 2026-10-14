"""The evolutionary E4-D's decision rule (docs/E4/E4-D-EVO-DESIGN.md v2.1 §6, Astra; δ the owner's, D266).

- `reading`: one arm's per-run gains (each champion's real-first share on its own test block, minus 0.5). The mean
  gain's one-sided 95% t bounds LB and UB, read against δ in five states (`state_of`, strict edges); the one-sided
  sign-flip p beside, labelled distributional. Malformed gains are refused (non-finite, outside [−0.5, 0.5], off the
  1/128 grid of a 128-trial block, or a count other than the registered one; both reviewers, D272).
- `states`: the same states for many simulated arms at once (the power analysis), as indices into `STATES`.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

ALPHA = 0.05  # each bound one-sided
DELTA = 0.15  # the owner's margin (D266)
TRIALS = 128  # a test block: 64 mazes × 2 assignments
STATES = ("practically relevant transfer found", "weak transfer found",
          "transfer detected; its practical size unresolved", "practical gain excluded; transfer not detected",
          "inconclusive")


def _state_index(lo, hi, delta):
    lo, hi = np.asarray(lo), np.asarray(hi)
    return np.select([lo > delta, (lo > 0) & (hi < delta), lo > 0, hi < delta], [0, 1, 2, 3], default=4)


def state_of(lo: float, hi: float, delta: float = DELTA) -> int:
    """The state's index in `STATES` for bounds LB = lo and UB = hi: LB > δ; 0 < LB and UB < δ; LB > 0; UB < δ;
    otherwise. Every edge is strict."""
    return int(_state_index(lo, hi, delta))


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


def _on_grid(d, trials: int) -> bool:
    k = np.asarray(d, dtype=np.float64) * trials
    return bool(np.all(np.abs(k - np.round(k)) < 1e-9))


def sign_flip_one_sided(d, *, trials: int = TRIALS, chunk: int = 1 << 16) -> float:
    """The share of the 2^R sign patterns whose mean reaches the observed mean (smallest 1/2^R); exact under sign
    symmetry about 0, so its label is distributional (Fable, Astra).

    On the 1/`trials` grid (every registered gain) it is counted exactly in integers: a pattern flipping the set S
    reaches the observed sum iff Σ_S k_i ≤ 0, so the count is the number of subsets with a non-positive sum (a
    subset-sum count; R = 32 in milliseconds). Off the grid it is enumerated, for R ≤ 20 only."""
    d = np.asarray(d, dtype=np.float64)
    R = len(d)
    if _on_grid(d, trials):
        k = np.round(d * trials).astype(np.int64)
        off = int(np.abs(k).sum())
        counts = np.zeros(2 * off + 1, dtype=object)
        counts[off] = 1
        for ki in k:
            nxt = counts.copy()
            if ki > 0:
                nxt[ki:] += counts[:-ki]
            elif ki < 0:
                nxt[:ki] += counts[-ki:]
            else:
                nxt += counts
            counts = nxt
        return float(sum(counts[:off + 1])) / float(1 << R)
    if R > 20:
        raise ValueError("off the grid, the sign-flip is enumerated only for R <= 20")
    obs = d.mean() - 1e-12
    bits = np.arange(R, dtype=np.int64)
    hits = 0
    for lo in range(0, 1 << R, chunk):
        k = np.arange(lo, min(lo + chunk, 1 << R), dtype=np.int64)
        signs = 1.0 - 2.0 * ((k[:, None] >> bits) & 1)
        hits += int(((signs @ d) / R >= obs).sum())
    return hits / float(1 << R)


def reading(d, *, delta: float = DELTA, alpha: float = ALPHA, evaluable: bool = True, n_expected: int | None = None,
            grid: bool = True, trials: int = TRIALS) -> dict:
    """`grid=False` only for tests of the rule on arbitrary numbers; every registered reading keeps the grid."""
    if not evaluable:
        return {"state": "not evaluable"}
    d = np.asarray(d, dtype=np.float64)
    if d.ndim != 1 or len(d) < 2:
        raise ValueError("the gains must be one value per run, at least two")
    if n_expected is not None and len(d) != n_expected:
        raise ValueError(f"{len(d)} gains, not the registered {n_expected}")
    if not np.all(np.isfinite(d)) or np.any(np.abs(d) > 0.5):
        raise ValueError("a gain is not finite or lies outside [-0.5, 0.5]")
    if grid and not _on_grid(d, trials):
        raise ValueError(f"a gain is not a whole number of trials out of {trials}, minus 0.5")
    m, lo, hi = bounds(d, alpha=alpha)
    return {"n": len(d), "mean": float(m), "lb": float(lo), "ub": float(hi), "alpha_one_sided": alpha, "delta": delta,
            "state": STATES[state_of(lo, hi, delta)], "interval_label": "approximate (model-based)",
            "sign_flip_p_one_sided": sign_flip_one_sided(d, trials=trials),
            "sign_flip_label": "distributional (sign symmetry)"}
