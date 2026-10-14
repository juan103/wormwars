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
    r = ES.reading(d, delta=0.15)
    q = stats.t.ppf(0.95, 4)
    se = d.std(ddof=1) / math.sqrt(5)
    assert r["lo"] == pytest.approx(d.mean() - q * se)
    assert r["hi"] == pytest.approx(d.mean() + q * se)
    assert r["state"] == "practically relevant transfer found"


@pytest.mark.parametrize("d, state", [
    ([0.39, 0.40, 0.38, 0.41], "practically relevant transfer found"),
    ([0.06, 0.07, 0.05, 0.06], "weak transfer found"),
    ([0.05, 0.30, 0.10, 0.25], "transfer detected; its practical size unresolved"),
    ([0.01, -0.01, 0.0, 0.02, -0.02, 0.0], "practical gain excluded; transfer not detected"),
    ([-0.1, 0.4, 0.0, 0.3], "inconclusive"),
])
def test_the_five_states(d, state):
    assert ES.reading(d, delta=0.15)["state"] == state


def test_the_states_vectorised_match_the_single_reading():
    rng = np.random.default_rng(3)
    D = rng.normal(0.15, 0.2, size=(400, 6))
    v = ES.states(D, delta=0.15)
    assert [ES.STATES[i] for i in v] == [ES.reading(d, delta=0.15)["state"] for d in D]


def test_identical_gains_have_zero_width():
    r = ES.reading([0.2, 0.2, 0.2], delta=0.15)
    assert r["lo"] == pytest.approx(0.2) and r["hi"] == pytest.approx(0.2)
    assert r["state"] == "practically relevant transfer found"


def test_not_evaluable():
    assert ES.reading([0.3, 0.3], delta=0.15, evaluable=False)["state"] == "not evaluable"


def test_the_sign_flip_is_one_sided_with_smallest_p_one_over_2_to_the_r():
    assert ES.sign_flip_one_sided([0.1, 0.2, 0.3, 0.4]) == pytest.approx(1 / 16)
    assert ES.sign_flip_one_sided([-0.1, -0.2, -0.3, -0.4]) == pytest.approx(1.0)
    # by enumeration: patterns whose mean reaches the observed mean
    d = np.array([0.3, -0.1, 0.2])
    pats = [np.array(s) for s in np.array(np.meshgrid(*[[1, -1]] * 3)).T.reshape(-1, 3)]
    want = np.mean([(p * d).mean() >= d.mean() - 1e-12 for p in pats])
    assert ES.sign_flip_one_sided(d) == pytest.approx(want)
