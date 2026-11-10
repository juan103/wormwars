"""E5-1's O1 rules and its bootstrap (docs/E5/E5-1-DESIGN.md §5)."""

import numpy as np
import pytest

from wormwars.e5 import stats as S

D = 0.25


@pytest.mark.parametrize("d, lo, hi, want", [
    (0.40, 0.10, 0.70, "N2 ahead, estimate at least δ"),
    (0.25, 0.01, 0.49, "N2 ahead, estimate at least δ"),
    (0.18, 0.10, 0.24, "N2 ahead, estimate below δ"),  # Astra's case: a detected, small advantage
    (-0.40, -0.70, -0.10, "SH-route ahead, estimate at least δ"),
    (-0.18, -0.24, -0.10, "SH-route ahead, estimate below δ"),
    (0.02, -0.20, 0.20, "no difference of δ either way"),
    (0.10, -0.05, 0.30, "inconclusive"),
    (-0.10, -0.30, 0.05, "inconclusive"),
    (0.00, -0.25, 0.10, "inconclusive"),  # a bound on −δ itself is not inside
])
def test_label(d, lo, hi, want):
    assert S.label(d, lo, hi, D) == want


def test_label_refuses_a_bad_interval():
    with pytest.raises(ValueError):
        S.label(0.0, 0.1, -0.1, D)


def test_delta_is_n2_runs_against_graph_means():
    n2 = np.array([3.0, 3.2, 2.8, 3.0])
    runs = np.array([[2.0, 2.4], [3.0, 3.0], [2.5, 2.7]])  # graph × run
    d, lo, hi = S.delta_interval(n2, runs, n_boot=2000, seed=0)
    assert d == pytest.approx(3.0 - np.mean([2.2, 3.0, 2.6]))
    assert lo < d < hi


def test_bootstrap_resamples_graph_means_not_runs():
    """Within-graph spread with identical graph means gives no null-side width (single level, Astra)."""
    n2 = np.full(8, 3.0)
    runs = np.array([[1.0, 5.0], [2.0, 4.0], [0.0, 6.0], [3.0, 3.0]])  # every graph mean is 3.0
    d, lo, hi = S.delta_interval(n2, runs, n_boot=2000, seed=0)
    assert (d, lo, hi) == (0.0, 0.0, 0.0)


def test_bootstrap_is_seeded():
    rng = np.random.default_rng(5)
    n2, runs = rng.normal(3, 0.3, 16), rng.normal(2.8, 0.3, (16, 2))
    assert S.delta_interval(n2, runs, seed=1) == S.delta_interval(n2, runs, seed=1)
