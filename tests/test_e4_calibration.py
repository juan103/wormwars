"""E4's calibration rules (D255, after both reviewers read the diagnostics): the module-bias factor and the
cross-link load bound, on children, paired."""

from __future__ import annotations

import pytest

from wormwars.e4 import calibration as CB


@pytest.mark.parametrize("children, want, rule", [
    ({0.05: 3.50, 0.02: 3.95, 0.01: 4.00, 0.005: 4.02, 0.0: 4.03}, 0.02, "the largest meeting both"),
    ({0.05: 3.90, 0.02: 3.95, 0.01: 4.00, 0.005: 4.02, 0.0: 4.03}, 0.05, "the largest meeting both"),
    ({0.05: 3.50, 0.02: 3.70, 0.01: 3.75, 0.005: 3.76, 0.0: 4.03}, 0.0, "none meets both: biases frozen, flagged"),
])
def test_the_bias_factor(children, want, rule):
    """E-G unmutated 4.03; frozen-bias children are `children[0.0]`."""
    got = CB.bias_factor(children, eg=4.03)
    assert got["factor"] == want and got["rule"] == rule


def test_the_bias_factor_needs_both_conditions():
    # 95% of E-G is 3.83: 0.05 passes it, but it is 0.3 below the frozen-bias children (4.20)
    assert CB.bias_factor({0.05: 3.90, 0.02: 4.00, 0.01: 4.10, 0.005: 4.15, 0.0: 4.20}, eg=4.03)["factor"] == 0.02


def test_the_confirmation():
    assert CB.confirmed(children=3.85, eg=4.03) and not CB.confirmed(children=3.80, eg=4.03)


@pytest.mark.parametrize("xplus, ok", [(3.80, True), (3.79, True), (3.70, False)])
def test_the_cross_link_bound(xplus, ok):
    """X0's children 3.98: the bound is min(0.25, 0.05 × 3.98) = 0.199."""
    assert CB.cross_load_ok(xplus, x0=3.98) is ok
