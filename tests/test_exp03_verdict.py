"""Experiment 03's verdict (design v3, D051): exact one-sided rank tests, the maximum over
ensembles then Holm across signals, and a joint bootstrap with shared world indices."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.exp03 import verdict as V


def test_rank_p_is_exact_and_one_sided():
    ens = np.arange(128, dtype=float)          # 0 .. 127
    assert V.rank_p(200.0, ens, "above") == pytest.approx(1 / 129)
    assert V.rank_p(-1.0, ens, "above") == pytest.approx(129 / 129)
    assert V.rank_p(-1.0, ens, "below") == pytest.approx(1 / 129)
    assert V.rank_p(63.5, ens, "above") == pytest.approx((64 + 1) / 129)


def test_intersection_then_holm_takes_the_worst_ensemble_first():
    p = {"P1": {"A": 0.001, "B": 0.03}, "P2": {"A": 0.004, "B": 0.004}, "P3": {"A": 0.5, "B": 0.001}}
    out = V.iut_holm(p)
    assert out["P1"]["p_max"] == 0.03 and out["P3"]["p_max"] == 0.5
    # Holm on [0.03, 0.004, 0.5]: sorted 0.004*3=0.012, 0.03*2=0.06, 0.5*1 -> monotone
    assert out["P2"]["p_holm"] == pytest.approx(0.012)
    assert out["P1"]["p_holm"] == pytest.approx(0.06)
    assert out["P3"]["p_holm"] == pytest.approx(0.5)


def test_verdicts_are_mutually_exclusive():
    m = {"effect": 0.1, "equivalence": 0.1}
    assert V.classify(0.01, (0.15, 0.30), m, "above") == "distinctive"
    assert V.classify(0.01, (-0.30, -0.15), m, "above") == "reversed"
    assert V.classify(0.20, (-0.05, 0.05), m, "above") == "compatible"
    assert V.classify(0.01, (0.05, 0.30), m, "above") == "inconclusive"
    assert V.classify(0.20, (0.15, 0.30), m, "above") == "inconclusive"  # interval beyond, test not significant


def test_joint_bootstrap_shares_world_indices_across_graphs():
    """Graphs that differ only by a world effect shared across graphs must give a tight
    difference, which a world-independent bootstrap would not."""
    rng = np.random.default_rng(0)
    world_effect = rng.normal(0, 1.0, 16)
    def graph(offset):
        return offset + world_effect[None, :] + rng.normal(0, 0.01, (32, 16))
    n2 = graph(0.5)
    ens = [graph(0.0) for _ in range(20)]
    lo, hi = V.effect_interval(n2, ens, lambda x: x.mean(), n_boot=400, seed=1)
    assert 0.45 < lo < 0.5 < hi < 0.55
