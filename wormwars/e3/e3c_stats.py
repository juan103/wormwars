"""E3c's registered statistics (its pre-registration's §7; draft 4, D207-D209).

- **The unit:** each run's d = (its champion's mean visits per wey on the test block − P-fixed's) / P-fixed's
  mean. The run is the independent unit.
- **The contrasts:** Q1 = S-mod − S-dense; Q2 = P-joint − S-mod.
- **The confirmatory decision** (D208): an exact two-sided permutation test of the difference in mean d, over
  every split of the pooled runs, at 0.05 / 2 per contrast.
  - **Its null:** the two arms' runs are exchangeable (one distribution). Under that null its finite-sample
    type I error is at most 0.025, whatever the failure rates.
  - **What it does not claim:** a difference in means. For Q2 the null is expected to be false on spread alone
    (D209).
- **The margin labels** are approximate (model-based): fixed Welch intervals at 1 − 0.05 / 2 with the dual
  margin. They are calibrated only under the no-failure model of `power.json`. Holm's adjusted p-values are
  reported beside, never as labels.
- **The practical margin** (the owner's choice, 2026-10-05): two margins, combined so that both must agree:
  - 0.10 of P-fixed's mean (Fable);
  - 0.5 visits per wey (Astra), that is 0.5 / P-fixed's mean in d.

  "Beyond the margin" needs the interval to clear the larger, strictly. "No relevant difference" needs it
  strictly inside the smaller.
- **Q1's floor guard:** Q1 is not read unless at least one S arm's mean test visits exceed W2 alone + 1. When it
  is not read, it enters Holm with p = 1.
- **Failed runs** (D207, D208): a run whose champion's mean test visits are not above W2 alone + 1. They are
  counted per arm and reported with every label, with a decomposition (Welch among the runs that did not fail).
  They detect only failures below that line.
- **Supplement:** a two-sided Mann-Whitney U test per contrast, unadjusted, never a label.
- **The coverage classification** (descriptive; §7.3): by proportions, with nose classes kept apart from
  coverers.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

ALPHA = 0.05
LEVEL = 1 - ALPHA / 2
MARGIN_REL = 0.10
MARGIN_VISITS = 0.5
FLOOR_MARGIN = 1.0
NAMES = {"Q1": ("modular", "dense"), "Q2": ("engineered initialization and tuning", "from scratch")}
NOSE_INDEPENDENT, NOSE_DEPENDENT = 0.9, 0.5
COVER_HIGH, COVER_LOW = 0.75, 0.25


def welch(x, y, level: float = 0.95) -> dict:
    x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    vx, vy = x.var(ddof=1) / len(x), y.var(ddof=1) / len(y)
    se = float(np.sqrt(vx + vy))
    df = float((vx + vy) ** 2 / (vx ** 2 / (len(x) - 1) + vy ** 2 / (len(y) - 1))) if se > 0 else float("inf")
    est = float(x.mean() - y.mean())
    if se == 0:
        p = 1.0 if est == 0 else 0.0
        return {"estimate": est, "se": 0.0, "df": df, "p": p, "lo": est, "hi": est, "level": level}
    p = float(2 * stats.t.sf(abs(est / se), df))
    q = float(stats.t.ppf(1 - (1 - level) / 2, df))
    return {"estimate": est, "se": se, "df": df, "p": p, "lo": est - q * se, "hi": est + q * se, "level": level}


def margins(seed_mean: float, rel: float = MARGIN_REL, visits: float = MARGIN_VISITS) -> tuple[float, float]:
    """(the smaller, the larger) margin in d."""
    if not (math.isfinite(seed_mean) and seed_mean > 0):
        raise ValueError(f"P-fixed's mean must be finite and positive, not {seed_mean}")
    a, b = rel, visits / seed_mean
    return min(a, b), max(a, b)


def label(est: float, lo: float, hi: float, rejected: bool, *, m_lo: float, m_hi: float, a: str, b: str) -> str:
    if rejected:
        side, (l, h) = (a, (lo, hi)) if est > 0 else (b, (-hi, -lo))
        if l > m_hi:
            return f"{side} better, beyond the margin"
        if h < m_lo:
            return f"{side} better, within the margin"
        return f"{side} better, margin unresolved"
    if lo > -m_lo and hi < m_lo:
        return "no relevant difference"
    return "unclear"


def contrasts(pairs: dict, alpha: float = ALPHA) -> dict:
    """Each contrast's Welch interval at 1 − alpha / m; "rejected" when it excludes 0. Holm's adjusted p beside
    (a contrast not read enters with p = 1)."""
    m = len(pairs)
    level = 1 - alpha / m
    out = {}
    for k, v in pairs.items():
        if v is None:
            out[k] = {"read": False, "rejected": False, "level": level, "p": None}
            continue
        w = welch(*v, level=level)
        out[k] = {**w, "read": True, "rejected": bool(w["lo"] > 0 or w["hi"] < 0)}
    ps = {k: (1.0 if out[k]["p"] is None else out[k]["p"]) for k in out}
    running = 0.0
    for i, k in enumerate(sorted(ps, key=ps.get)):
        running = max(running, min(1.0, (m - i) * ps[k]))
        out[k]["p_holm"] = running
    return out


def permutation_p(x, y) -> float:
    """The exact two-sided permutation p-value of the difference in means, over every split of the pooled values
    into groups of len(x) and len(y)."""
    import itertools
    x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    pooled = np.concatenate([x, y])
    n, nx = len(pooled), len(x)
    idx = np.array(list(itertools.combinations(range(n), nx)))
    a = np.zeros((len(idx), n))
    a[np.arange(len(idx))[:, None], idx] = 1.0
    sx = a @ pooled
    diffs = sx / nx - (pooled.sum() - sx) / (n - nx)
    obs = x.mean() - y.mean()
    return float(np.mean(np.abs(diffs) >= abs(obs) - 1e-12))


def decomposition(x_ok, y_ok) -> dict:
    """Welch (two-sided 95%) among the runs that did not fail; not computed when an arm has fewer than 2."""
    counts = [len(x_ok), len(y_ok)]
    if min(counts) < 2:
        return {"successful_runs": counts, "welch": "not computed: fewer than 2"}
    return {"successful_runs": counts, "welch": welch(x_ok, y_ok, level=0.95)}


def failed(run_visits, w2_alone: float) -> int:
    return int(np.sum(np.asarray(run_visits, dtype=np.float64) <= w2_alone + FLOOR_MARGIN))


def readings(*, d: dict, seed_mean: float, run_visits: dict, w2_alone: float, alpha: float = ALPHA) -> dict:
    """Q1 and Q2 from the runs' d and their champions' mean test visits (`run_visits`, per arm), with Q1's floor
    guard and the failed-run rule."""
    if not (math.isfinite(seed_mean) and seed_mean > 0):
        lab = "not read: P-fixed's mean is not positive"
        return {"seed_mean": seed_mean, **{q: {"read": False, "label": lab, "exact": {"p": None, "label": lab}}
                                           for q in ("Q1", "Q2")}}
    m_lo, m_hi = margins(seed_mean)
    q1_read = max(float(np.mean(run_visits["s_mod"])), float(np.mean(run_visits["s_dense"]))) > w2_alone + FLOOR_MARGIN
    pairs = {"Q1": (d["s_mod"], d["s_dense"]) if q1_read else None, "Q2": (d["p_joint"], d["s_mod"])}
    arms = {"Q1": ("s_mod", "s_dense"), "Q2": ("p_joint", "s_mod")}
    res = contrasts(pairs, alpha)
    out = {"margins": {"m_lo": m_lo, "m_hi": m_hi}, "seed_mean": seed_mean}
    for q, r in res.items():
        a, b = NAMES[q]
        fails = {arm: failed(run_visits[arm], w2_alone) for arm in arms[q]}
        if not r["read"]:
            out[q] = {**r, "label": "not read: both at the floor", "failed_runs": fails,
                      "exact": {"p": None, "label": "not read"}}
            continue
        x, y = pairs[q]
        p_exact = permutation_p(x, y)
        side = a if np.mean(x) > np.mean(y) else b
        rej = p_exact <= alpha / len(pairs)
        exact = {"p": p_exact, "level": alpha / len(pairs), "rejected": rej,
                 "label": (f"distributions differ (exact test); observed mean higher for {side}" if rej
                           else "no difference detected (exact)")}
        ok = {arm: np.asarray(dd)[np.asarray(run_visits[arm], dtype=np.float64) > w2_alone + FLOOR_MARGIN]
              for arm, dd in zip(arms[q], (x, y))}
        mw = stats.mannwhitneyu(x, y, alternative="two-sided")
        lab = label(r["estimate"], r["lo"], r["hi"], r["rejected"], m_lo=m_lo, m_hi=m_hi, a=a, b=b)
        out[q] = {**r, "label": f"approximate (model-based): {lab}", "label_unqualified": lab, "exact": exact,
                  "failed_runs": fails, "failed_runs_present": any(fails.values()),
                  "decomposition": decomposition(ok[arms[q][0]], ok[arms[q][1]]),
                  "estimate_visits": r["estimate"] * seed_mean, "mann_whitney_p": float(mw.pvalue)}
    return out


def nose_class(r) -> str:
    if r is None or not math.isfinite(r):
        return "undefined"
    if r >= NOSE_INDEPENDENT:
        return "nose-independent"
    if r <= NOSE_DEPENDENT:
        return "nose-dependent"
    return "partial"


def coverage_rule(coverer: dict) -> dict:
    """`coverer[arm]`: per champion True, False or None (undefined).
    - **Shares** are over defined champions (None when an arm has none).
    - **The S-arm part,** from the S arms alone: "undefined" if any S champion is; "high" if both shares are
      ≥ 0.75; "low" if both are ≤ 0.25; else "mixed".
    - **The P-joint comparison:** whether P-joint's share is below both S arms'. None when any champion of the
      three arms is undefined (Astra, D209).
    - **The classification:** "mixed" whenever any champion is undefined; otherwise "not supported" if the S arms
      are low; "supported" if they are high and P-joint is lower than both; else "mixed"."""
    share, undefined = {}, {}
    for arm, xs in coverer.items():
        defined = [bool(x) for x in xs if x is not None]
        undefined[arm] = len(xs) - len(defined)
        share[arm] = sum(defined) / len(defined) if defined else None
    s = ("s_mod", "s_dense")
    if any(undefined[a] for a in s):
        s_part = "undefined"
    elif all(share[a] >= COVER_HIGH for a in s):
        s_part = "high"
    elif all(share[a] <= COVER_LOW for a in s):
        s_part = "low"
    else:
        s_part = "mixed"
    any_undefined = any(undefined.values())
    p_lower = None if any_undefined else all(share["p_joint"] < share[a] for a in s)
    if any_undefined:
        lab = "mixed"
    elif s_part == "low":
        lab = "not supported"
    elif s_part == "high" and p_lower:
        lab = "supported"
    else:
        lab = "mixed"
    return {"coverers": lab, "s_arms": s_part, "p_joint_lower_than_both": p_lower, "shares": share,
            "undefined": undefined}


def censored_median(gens) -> float | str:
    """The median generation to threshold, with censored runs as +inf; "not reached" when the median touches
    a censored run (fewer than half reach it, or exactly half)."""
    x = np.sort(np.asarray(gens, dtype=np.float64))
    n = len(x)
    if n == 0:
        return "no runs"
    mid = x[(n - 1) // 2: n // 2 + 1]
    if not np.all(np.isfinite(mid)):
        return "not reached"
    return float(mid.mean())
