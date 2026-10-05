"""E3c's registered statistics (its pre-registration's §7).

- **The unit:** each run's d = (its champion's mean visits per wey on the test block − the seed's) / the seed's
  mean. The run is the independent unit.
- **The contrasts:** Q1 = S-mod − S-dense; Q2 = P-joint − S-mod. Each is a two-sided Welch test; Holm's
  step-down over the two at 5%.
- **The intervals:** each contrast's Welch interval at its Holm level, 1 − α / (m − rank). After the first
  contrast that is not rejected, the later ones keep that step's level. A contrast is then rejected exactly
  when its interval excludes 0.
- **The practical margin** (the owner's choice, 2026-10-05): two margins, combined so that both must agree:
  - 0.10 of the seed's mean (Fable);
  - 0.5 visits per wey (Astra), that is 0.5 / the seed's mean in d.

  "Beyond the margin" needs the interval to clear the larger. "No relevant difference" needs it inside the
  smaller.
- **Q1's floor guard:** Q1 is not read unless at least one S arm's mean test visits exceed W2 alone + 1.
- **Supplement:** a two-sided Mann-Whitney U test per contrast, unadjusted. It is never a label.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

ALPHA = 0.05
MARGIN_REL = 0.10
MARGIN_VISITS = 0.5
FLOOR_MARGIN = 1.0
NAMES = {"Q1": ("modular", "dense"), "Q2": ("engineered initialization", "from scratch")}


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
    """Holm's step-down over `pairs` ({name: (x, y)} or {name: None} when not read), with each contrast's
    interval at its Holm level."""
    names = list(pairs)
    m = len(names)
    base = {k: (welch(*v) if v is not None else None) for k, v in pairs.items()}
    order = sorted(names, key=lambda k: 1.0 if base[k] is None else base[k]["p"])
    out, still, level = {}, True, None
    for i, k in enumerate(order):
        if still:  # after the first failure, later contrasts keep the failed step's level, so that their
            level = 1 - alpha / (m - i)  # intervals (p at least as large) include 0, as their Holm result says
        if pairs[k] is None:
            out[k] = {"read": False, "rejected": False, "level": level}
            still = False
            continue
        w = welch(*pairs[k], level=level)
        rej = still and w["p"] <= 1 - level
        still = still and rej
        out[k] = {**w, "read": True, "rejected": bool(rej)}
    return out


def readings(*, d: dict, seed_mean: float, visits: dict, w2_alone: float, alpha: float = ALPHA) -> dict:
    """Q1 and Q2 from the runs' d (`d["s_mod"]`, `d["s_dense"]`, `d["p_joint"]`), with Q1's floor guard on the S
    arms' mean test visits."""
    q1_read = max(visits["s_mod"], visits["s_dense"]) > w2_alone + FLOOR_MARGIN
    pairs = {"Q1": (d["s_mod"], d["s_dense"]) if q1_read else None, "Q2": (d["p_joint"], d["s_mod"])}
    res = contrasts(pairs, alpha)
    m_lo, m_hi = margins(seed_mean)
    out = {"margins": {"m_lo": m_lo, "m_hi": m_hi}, "seed_mean": seed_mean}
    for q, r in res.items():
        a, b = NAMES[q]
        if not r["read"]:
            out[q] = {**r, "label": "not read: both at the floor"}
            continue
        x, y = pairs[q]
        mw = stats.mannwhitneyu(x, y, alternative="two-sided")
        out[q] = {**r, "label": label(r["estimate"], r["lo"], r["hi"], r["rejected"], m_lo=m_lo, m_hi=m_hi, a=a, b=b),
                  "estimate_visits": r["estimate"] * seed_mean, "mann_whitney_p": float(mw.pvalue)}
    return out
