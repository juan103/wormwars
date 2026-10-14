"""The evolutionary E4-D's decision rule (design v2.1 §6, Astra): the one-sided 95% t bounds of the runs' mean gain,
read against the margin δ in five states, with the one-sided sign-flip p beside."""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats

from wormwars.e4 import evo_stats as ES


def test_the_bounds_are_one_sided_t():
    d = np.array([0.30, 0.42, 0.38, 0.25, 0.40])
    r = ES.reading(d, delta=0.15, grid=False)
    q = stats.t.ppf(0.95, 4)
    se = d.std(ddof=1) / math.sqrt(5)
    assert r["lb"] == pytest.approx(d.mean() - q * se)
    assert r["ub"] == pytest.approx(d.mean() + q * se)
    assert r["state"] == "practically relevant transfer found"


@pytest.mark.parametrize("d, state", [
    ([0.39, 0.40, 0.38, 0.41], "practically relevant transfer found"),
    ([0.06, 0.07, 0.05, 0.06], "weak transfer found"),
    ([0.05, 0.30, 0.10, 0.25], "transfer detected; its practical size unresolved"),
    ([0.01, -0.01, 0.0, 0.02, -0.02, 0.0], "practical gain excluded; transfer not detected"),
    ([-0.1, 0.4, 0.0, 0.3], "inconclusive"),
])
def test_the_five_states(d, state):
    assert ES.reading(d, delta=0.15, grid=False)["state"] == state


def test_the_states_vectorised_match_the_single_reading():
    rng = np.random.default_rng(3)
    D = np.clip(rng.normal(0.15, 0.2, size=(400, 6)), -0.5, 0.5)
    v = ES.states(D, delta=0.15)
    assert [ES.STATES[i] for i in v] == [ES.reading(d, delta=0.15, grid=False)["state"] for d in D]


def test_identical_gains_have_zero_width():
    r = ES.reading([0.2, 0.2, 0.2], delta=0.15, grid=False)
    assert r["lb"] == pytest.approx(0.2) and r["ub"] == pytest.approx(0.2)
    assert r["state"] == "practically relevant transfer found"


def test_not_evaluable():
    assert ES.reading([0.3, 0.3], delta=0.15, evaluable=False, grid=False)["state"] == "not evaluable"


def test_the_sign_flip_is_one_sided_with_smallest_p_one_over_2_to_the_r():
    assert ES.sign_flip_one_sided([0.1, 0.2, 0.3, 0.4]) == pytest.approx(1 / 16)
    assert ES.sign_flip_one_sided([-0.1, -0.2, -0.3, -0.4]) == pytest.approx(1.0)
    # by enumeration: patterns whose mean reaches the observed mean
    d = np.array([0.3, -0.1, 0.2])
    pats = [np.array(s) for s in np.array(np.meshgrid(*[[1, -1]] * 3)).T.reshape(-1, 3)]
    want = np.mean([(p * d).mean() >= d.mean() - 1e-12 for p in pats])
    assert ES.sign_flip_one_sided(d) == pytest.approx(want)


def test_the_registered_constants():
    assert ES.DELTA == 0.15 and ES.ALPHA == 0.05 and ES.TRIALS == 128
    assert ES.STATES == ("practically relevant transfer found", "weak transfer found",
                         "transfer detected; its practical size unresolved",
                         "practical gain excluded; transfer not detected", "inconclusive")


@pytest.mark.parametrize("lo, hi, want", [
    (0.15, 0.30, 2), (0.1500001, 0.30, 0), (0.15, 0.15, 2),          # LB = δ is not "practically relevant"
    (0.0, 0.10, 3), (1e-9, 0.10, 1), (0.05, 0.15, 2), (0.05, 0.1499999, 1),  # UB = δ is not "weak"
    (0.0, 0.15, 4), (-0.1, 0.1499999, 3), (-0.1, 0.30, 4),
])
def test_the_edges_are_strict(lo, hi, want):
    assert ES.state_of(lo, hi) == want


@pytest.mark.parametrize("d", [[0.3, float("nan"), 0.2], [0.3, float("inf")], [0.6, 0.2], [0.3, 0.2 + 1 / 1000]])
def test_malformed_gains_are_refused(d):
    with pytest.raises(ValueError):
        ES.reading(d)


def test_the_count_is_enforced():
    with pytest.raises(ValueError):
        ES.reading([0.25, 0.375], n_expected=3)
    assert ES.reading([0.25, 0.375, 0.3125], n_expected=3)["n"] == 3


def test_the_exact_sign_flip_matches_enumeration_with_zeros_and_ties():
    rng = np.random.default_rng(5)
    for _ in range(60):
        R = int(rng.integers(1, 13))
        k = rng.integers(-6, 7, size=R)  # gains on the 1/128 grid, many zeros and ties
        d = k / 128
        pats = np.array(np.meshgrid(*[[1, -1]] * R)).T.reshape(-1, R)
        want = np.mean((pats * k).sum(1) >= k.sum())
        assert ES.sign_flip_one_sided(d) == pytest.approx(want)


def test_the_sign_flip_at_r_32_is_fast_and_exact():
    import time
    d = np.r_[np.full(31, 48 / 128), -1 / 128]
    t = time.perf_counter()
    p = ES.sign_flip_one_sided(d)
    assert time.perf_counter() - t < 5
    assert p == pytest.approx(2 / 2 ** 32)  # no flip, or only the negative run's
