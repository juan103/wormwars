"""E4's cross-link scale rule (docs/E4/E4-DESIGN.md v3 §1): the reach of a neutral slot along simulated champion
lineages, the mutation-load bound, and the choice among the candidates."""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats

from wormwars.e4 import scale_rule as SR


def test_reach_without_clipping_matches_the_normal_tail():
    p = SR.reach(counts=[100], sigma=0.08, factor=1.0, w_max=100.0, n_sim=200_000, seed=1)
    want = 2 * stats.norm.sf(1.0 / (0.08 * math.sqrt(100)))
    assert p == pytest.approx(want, abs=0.005)


def test_reach_weights_each_lineage_equally():
    a = SR.reach(counts=[10], sigma=0.08, factor=1.0, w_max=3.0, n_sim=100_000, seed=2)
    b = SR.reach(counts=[400], sigma=0.08, factor=1.0, w_max=3.0, n_sim=100_000, seed=2)
    both = SR.reach(counts=[10, 400], sigma=0.08, factor=1.0, w_max=3.0, n_sim=100_000, seed=2)
    assert both == pytest.approx((a + b) / 2, abs=0.01)


def test_clipping_holds_the_walk_inside_w_max():
    w = SR.walk(count=500, sigma=0.08, factor=1.0, w_max=0.5, n_sim=1000, rng=np.random.default_rng(3))
    assert np.abs(w).max() <= 0.5


def test_zero_mutations_never_reach():
    assert SR.reach(counts=[0], sigma=0.08, factor=1.0, w_max=3.0, n_sim=1000, seed=4) == 0.0


def test_the_load_bound():
    assert SR.load_ok(x_plus_mean=5.80, x0_mean=6.0)
    assert not SR.load_ok(x_plus_mean=5.70, x0_mean=6.0)
    assert not SR.load_ok(x_plus_mean=6.30, x0_mean=6.0)


def test_the_candidates_reach_four():
    assert SR.CANDIDATES == (0.25, 0.5, 1.0, 2.0, 4.0)


C = SR.CANDIDATES
ALL = {f: True for f in C}


@pytest.mark.parametrize("reach, load, want, rule", [
    (dict(zip(C, (0.0, 0.1, 0.6, 0.9, 1.0))), ALL, 1.0, "reach and load"),
    (dict(zip(C, (0.0, 0.1, 0.6, 0.9, 1.0))), {**ALL, 1.0: False}, 2.0, "reach and load"),
    (dict(zip(C, (0.0, 0.0, 0.1, 0.3, 0.4))), ALL, 4.0, "reach-deficient: the largest factor meeting the load bound"),
    (dict(zip(C, (0.0, 0.0, 0.1, 0.3, 0.4))), {**ALL, 2.0: False, 4.0: False}, 1.0,
     "reach-deficient: the largest factor meeting the load bound"),
    (dict(zip(C, (0.0, 0.0, 0.1, 0.3, 0.4))), {f: False for f in C}, None, "no candidate meets the load bound"),
])
def test_the_choice(reach, load, want, rule):
    got = SR.choose(reach, load)
    assert got["factor"] == want and got["rule"] == rule


def test_lineage_counts_scale_to_the_formal_horizon():
    """The pilot measures the mutated share of a lineage at its G; the formal count is that share × the formal G."""
    assert SR.formal_counts([30, 50], g_pilot=100, g_formal=300) == [90, 150]


def test_the_largest_load_passing_factor():
    assert SR.largest_load_passing({0.25: True, 0.5: True, 1.0: True, 2.0: False, 4.0: True}) == 4.0
    assert SR.largest_load_passing({f: False for f in C}) is None
