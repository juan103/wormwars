"""E4's calibration rules (D255; both reviewers of the diagnostics, D254), fixed before stage A is played.

- `bias_factor`: the module biases' mutation factor (weights and τ stay at 0.25). Candidates 0.05, 0.02, 0.01 and
  0.005: the largest whose children keep at least 95% of unmutated E-G's mean (Astra) **and** are within 0.25 visits of
  the frozen-bias children (Fable), paired on the same mazes and seeds. If none meets both, the biases are frozen
  (factor 0), flagged.
- `confirmed`: the chosen setting's children keep at least 95% of E-G on a second fresh block; if not, the choice is
  reconsidered explicitly, never by searching further blocks.
- `cross_load_ok`: X+'s children within min(0.25 visits, 5% of X0's children's mean) of X0's children (Astra's
  stricter form of Fable's 0.25).
"""

from __future__ import annotations

BIAS_CANDIDATES = (0.05, 0.02, 0.01, 0.005)
RETAIN = 0.95
NEAR_FROZEN = 0.25
CROSS_ABS, CROSS_REL = 0.25, 0.05


def bias_factor(children: dict, *, eg: float) -> dict:
    """`children`: {factor: children's mean}, with 0.0 the frozen-bias children; `eg`: unmutated E-G's mean."""
    frozen = children[0.0]
    ok = [f for f in BIAS_CANDIDATES if children[f] >= RETAIN * eg and frozen - children[f] <= NEAR_FROZEN]
    if ok:
        return {"factor": max(ok), "rule": "the largest meeting both", "children": children, "eg": eg}
    return {"factor": 0.0, "rule": "none meets both: biases frozen, flagged", "children": children, "eg": eg}


def confirmed(*, children: float, eg: float) -> bool:
    return children >= RETAIN * eg


def cross_load_ok(xplus: float, *, x0: float) -> bool:
    return x0 - xplus <= min(CROSS_ABS, CROSS_REL * x0) + 1e-12
