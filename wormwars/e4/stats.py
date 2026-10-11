"""E4's statistics (docs/E4/E4-DESIGN.md v3 §2).

- `sign_flip`: the exact paired sign-flip test, two-sided, by enumeration of the 2^R sign patterns in chunks (E3c's
  permutation code materialised every permutation). Exact under the null that each run's difference is symmetric
  about 0; its label is distributional.
- `t_interval`: the t-based paired interval at 1 − α, model-based.
- `margins`: E3c's dual margin defined for E4, in visits per wey: 0.10 of a reference mean and 0.5 visits; (the
  smaller, the larger).
- `p1_state`: positive / negative (the exact test at α and the interval beyond the larger margin in that
  direction), equivalent (the interval strictly inside the smaller), inconclusive, or not evaluable. The
  difference is intact − intervention, so "positive" is "cutting hurts".
- `p2_label`: X+ − X0. "beyond" (rejected, the interval beyond the larger margin), "no relevant difference" (the
  interval strictly inside the smaller), "unclear", or "not evaluable".
- `joint`: the interpretation. Each contrast keeps its own reading; one qualification is keyed on P1-info (with P2,
  confirmatory; design v3 §2), P1-cut qualifying it. Rows D* are the design's, rows C* proposed (see `joint`).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

ALPHA = 0.025  # P1-info and P2, each two-sided
MARGIN_REL = 0.10
MARGIN_VISITS = 0.5
P1_STATES = ("positive", "negative", "equivalent", "inconclusive", "not evaluable")
P2_LABELS = ("beyond, X+ higher", "beyond, X0 higher", "no relevant difference", "unclear", "not evaluable")


def sign_flip(d, *, chunk: int = 1 << 16) -> float:
    """Two-sided exact p: the share of the 2^R sign patterns whose |mean| reaches the observed |mean|."""
    d = np.asarray(d, dtype=np.float64)
    R = len(d)
    obs = abs(d.mean()) - 1e-12
    bits = np.arange(R, dtype=np.int64)
    hits = 0
    for lo in range(0, 1 << R, chunk):
        k = np.arange(lo, min(lo + chunk, 1 << R), dtype=np.int64)
        signs = 1.0 - 2.0 * ((k[:, None] >> bits) & 1)
        hits += int((np.abs(signs @ d) / R >= obs).sum())
    return hits / float(1 << R)


def t_interval(d, *, alpha: float = ALPHA) -> tuple[float, float]:
    d = np.asarray(d, dtype=np.float64)
    m, se = float(d.mean()), float(d.std(ddof=1) / math.sqrt(len(d)))
    q = float(stats.t.ppf(1 - alpha / 2, len(d) - 1))
    return m - q * se, m + q * se


def margins(ref_mean: float, rel: float = MARGIN_REL, visits: float = MARGIN_VISITS) -> tuple[float, float]:
    if not (math.isfinite(ref_mean) and ref_mean > 0):
        raise ValueError(f"the reference mean must be finite and positive, not {ref_mean}")
    a, b = rel * ref_mean, visits
    return min(a, b), max(a, b)


def _read(d, alpha, m_lo, m_hi):
    d = np.asarray(d, dtype=np.float64)
    p = sign_flip(d)
    lo, hi = t_interval(d, alpha=alpha)
    out = {"n": len(d), "mean": float(d.mean()), "p": p, "lo": lo, "hi": hi, "alpha": alpha, "m_lo": m_lo,
           "m_hi": m_hi, "exact_label": "the per-run differences are not sign-symmetric (exact)" if p <= alpha else
           "sign symmetry not rejected (exact)", "interval_label": "approximate (model-based)"}
    up, down = p <= alpha and lo > m_hi, p <= alpha and hi < -m_hi
    inside = lo > -m_lo and hi < m_lo
    return out, up, down, inside


def p1_state(d, *, m_lo: float, m_hi: float, alpha: float = ALPHA, evaluable: bool = True) -> dict:
    if not evaluable:
        return {"state": "not evaluable"}
    out, up, down, inside = _read(d, alpha, m_lo, m_hi)
    out["state"] = "positive" if up else "negative" if down else "equivalent" if inside else "inconclusive"
    return out


def p2_label(d, *, m_lo: float, m_hi: float, alpha: float = ALPHA, evaluable: bool = True) -> dict:
    if not evaluable:
        return {"label": "not evaluable"}
    out, up, down, inside = _read(d, alpha, m_lo, m_hi)
    out["label"] = ("beyond, X+ higher" if up else "beyond, X0 higher" if down else
                    "no relevant difference" if inside else "unclear")
    return out


P1_INFO_READINGS = {
    "positive": "the time-varying signal crossing the module boundary is used, beyond a validation-estimated constant "
                "replacement",
    "negative": "replacing the cross-link signal by its validation mean improves performance",
    "equivalent": "no practically relevant dependence on the time-varying signal beyond its mean",
    "inconclusive": "P1-info is unresolved",
    "not evaluable": "P1-info is not evaluable",
}
P1_CUT_READINGS = {
    "positive": "cutting the cross-links hurts",
    "negative": "cutting the cross-links helps",
    "equivalent": "no practically relevant acute dependence on the cross-links",
    "inconclusive": "P1-cut is unresolved",
    "not evaluable": "P1-cut is not evaluable",
}
P2_READINGS = {
    "beyond, X+ higher": "the option of cross-links raises performance",
    "beyond, X0 higher": "the option of cross-links lowers performance",
    "no relevant difference": "no relevant difference between the arms",
    "unclear": "the training contrast is unclear",
    "not evaluable": "the training contrast is not evaluable (an arm not competent)",
}
VOIDED = " (E4-D's positive control failed: not read as evidence of absence)"

READINGS = {
    "D1": "evolved organisms use the time-varying signal crossing the boundary; the directional read decides "
          "\"the other module's information\"",
    "D2": "they depend on the cross-links, and a constant replacement suffices: the dependence is tonic",
    "D2u": "they depend on the cross-links; the mechanism is unresolved",
    "D3": "the evolved cross-links cost performance on the test block: a maladaptive or overfitted use, not transfer",
    "D4": "a benefit of the larger architecture without acute dependence; the mechanism is unresolved",
    "D5": "no practically relevant benefit detected by the registered interventions",
    "D6": "no acute dependence detected; the training contrast is unresolved",
    "D7": "the acute readings are unresolved at this budget",
    "D8": "no acute dependence detected in X+; the training comparison is not evaluable",
    "C0": "the time-varying signal crossing the boundary is used (P1-info, confirmatory); dependence on the links as a "
          "whole is not established, since P1-cut is not positive",
    "C1": "cutting hurts, and this constant replacement improves performance; no mechanism is resolved",
    "C2": "they depend on the cross-links; whether through the time-varying signal is not evaluable",
    "C3": "no practically relevant benefit detected, but E4-D's positive control failed, so the null is not read",
    "C4": "the option of cross-links costs in training, without acute dependence",
    "C5": "P1 is not evaluable; P2 is read alone",
    "C6": "no acute dependence detected by cutting; this constant replacement improves performance, with no "
          "mechanism resolved",
    "C7": "no acute dependence detected by cutting; P1-info is unresolved",
    "C8": "P1-cut is unresolved; P1-info is read beside it",
}


def _qualification(cut: str, info: str, p2: str, control_working: bool) -> str:
    if cut == "negative":
        return "D3"
    if info == "positive":
        return "D1" if cut == "positive" else "C0"
    if cut == "positive":
        return {"equivalent": "D2", "inconclusive": "D2u", "negative": "C1", "not evaluable": "C2"}[info]
    if cut == "equivalent" and info == "equivalent":
        return {"beyond, X+ higher": "D4", "beyond, X0 higher": "C4", "unclear": "D6", "not evaluable": "D8",
                "no relevant difference": "D5" if control_working else "C3"}[p2]
    if cut == "equivalent":
        return "C6" if info == "negative" else "C7"
    if cut == "inconclusive":
        return "D7" if info == "inconclusive" else "C8"
    return "C5"


def joint(cut: str, info: str, p2: str, *, control_working: bool) -> dict:
    """The three contrasts' own readings, then one qualification keyed on the confirmatory P1-info, with P1-cut as
    its qualifier and P2 entering only where both acute readings are equivalent. Rows D* are design v3's (D2 split by
    whether P1-info is equivalent or inconclusive, after both reviewers); rows C* are proposed for the
    pre-registration. A failed E4-D control voids only the null readings."""
    if cut not in P1_STATES or info not in P1_STATES or p2 not in P2_LABELS:
        raise ValueError((cut, info, p2))
    readings = {"p1_info": P1_INFO_READINGS[info], "p1_cut": P1_CUT_READINGS[cut], "p2": P2_READINGS[p2]}
    if not control_working:
        for k, state in (("p1_info", info), ("p1_cut", cut), ("p2", p2)):
            if state in ("equivalent", "no relevant difference"):
                readings[k] += VOIDED
    row = _qualification(cut, info, p2, control_working)
    return {"row": row, "qualification": READINGS[row], "readings": readings, "proposed": row.startswith("C")}
