"""E4's statistics (docs/E4/E4-DESIGN.md v3 §2): the exact paired sign-flip test by enumeration, the t-based paired
interval, P1's states, P2's labels, and the joint interpretation table (complete over every state)."""

from __future__ import annotations

import itertools

import numpy as np
import pytest
from scipy import stats

from wormwars.e4 import stats as S


def _brute(d):
    d = np.asarray(d, dtype=np.float64)
    obs = abs(d.mean())
    null = [abs((np.array(s) * d).mean()) for s in itertools.product((1.0, -1.0), repeat=len(d))]
    return float(np.mean(np.array(null) >= obs - 1e-12))


def test_sign_flip_smallest_p_is_two_over_two_to_the_r():
    assert S.sign_flip(np.ones(7)) == pytest.approx(2 / 128)
    assert S.sign_flip(np.ones(8)) == pytest.approx(0.0078125)  # Astra's zero-mean asymmetric case: all +1


def test_sign_flip_matches_brute_force():
    rng = np.random.default_rng(3)
    for n in (5, 6, 9):
        d = rng.normal(0.3, 1.0, n)
        assert S.sign_flip(d) == pytest.approx(_brute(d))


def test_sign_flip_enumerates_in_chunks():
    d = np.random.default_rng(4).normal(0.2, 1.0, 12)
    assert S.sign_flip(d, chunk=64) == pytest.approx(S.sign_flip(d))


def test_sign_flip_of_zeros_is_one():
    assert S.sign_flip(np.zeros(7)) == 1.0


def test_t_interval():
    d = np.array([0.5, 1.2, -0.3, 0.8, 1.1, 0.4, 0.9])
    lo, hi = S.t_interval(d, alpha=0.025)
    q = stats.t.ppf(1 - 0.025 / 2, 6)
    se = d.std(ddof=1) / np.sqrt(7)
    assert lo == pytest.approx(d.mean() - q * se) and hi == pytest.approx(d.mean() + q * se)
    assert S.t_interval(np.full(7, 0.4), alpha=0.025) == (pytest.approx(0.4), pytest.approx(0.4))


def test_margins_are_ten_percent_and_half_a_visit():
    assert S.margins(6.0) == (pytest.approx(0.5), pytest.approx(0.6))
    assert S.margins(4.0) == (pytest.approx(0.4), pytest.approx(0.5))


@pytest.mark.parametrize("d, want", [
    (np.full(8, 2.0) + np.linspace(-0.1, 0.1, 8), "positive"),
    (-(np.full(8, 2.0) + np.linspace(-0.1, 0.1, 8)), "negative"),
    (np.linspace(-0.05, 0.05, 8), "equivalent"),
    (np.array([3.0, -2.0, 1.0, -1.5, 2.5, -0.5, 0.2, 1.0]), "inconclusive"),
])
def test_p1_states(d, want):
    assert S.p1_state(d, m_lo=0.5, m_hi=0.6)["state"] == want


def test_p1_positive_needs_the_interval_beyond_the_larger_margin():
    d = np.full(8, 0.55) + np.linspace(-0.01, 0.01, 8)  # exact p 2/256, but the interval is not beyond 0.6
    r = S.p1_state(d, m_lo=0.5, m_hi=0.6)
    assert r["p"] <= 0.025 and r["state"] == "inconclusive"


def test_p1_not_evaluable():
    assert S.p1_state(np.ones(8), m_lo=0.5, m_hi=0.6, evaluable=False)["state"] == "not evaluable"


@pytest.mark.parametrize("d, want", [
    (np.full(8, 2.0) + np.linspace(-0.1, 0.1, 8), "beyond, X+ higher"),
    (-(np.full(8, 2.0) + np.linspace(-0.1, 0.1, 8)), "beyond, X0 higher"),
    (np.linspace(-0.05, 0.05, 8), "no relevant difference"),
    (np.array([3.0, -2.0, 1.0, -1.5, 2.5, -0.5, 0.2, 1.0]), "unclear"),
])
def test_p2_labels(d, want):
    assert S.p2_label(d, m_lo=0.5, m_hi=0.6)["label"] == want


def test_the_joint_table_covers_every_state():
    for cut, info, p2, ctl in itertools.product(S.P1_STATES, S.P1_STATES, S.P2_LABELS, (True, False)):
        r = S.joint(cut, info, p2, control_working=ctl)
        assert r["row"] in S.READINGS and set(r["readings"]) == {"p1_info", "p1_cut", "p2"}, (cut, info, p2, ctl)


@pytest.mark.parametrize("cut, info, p2, ctl, row", [
    ("positive", "positive", "unclear", True, "D1"),
    ("positive", "positive", "unclear", False, "D1"),  # a failed control voids only the null row
    ("positive", "equivalent", "beyond, X+ higher", True, "D2"),
    ("positive", "inconclusive", "not evaluable", False, "D2u"),  # "tonic" only when P1-info is equivalent
    ("positive", "negative", "unclear", True, "C1"),
    ("positive", "not evaluable", "unclear", True, "C2"),
    ("negative", "positive", "unclear", True, "D3"),
    ("negative", "equivalent", "not evaluable", True, "D3"),
    ("equivalent", "equivalent", "beyond, X+ higher", True, "D4"),
    ("equivalent", "equivalent", "beyond, X0 higher", True, "C4"),
    ("equivalent", "equivalent", "no relevant difference", True, "D5"),
    ("equivalent", "equivalent", "no relevant difference", False, "C3"),
    ("equivalent", "equivalent", "unclear", True, "D6"),
    ("equivalent", "equivalent", "not evaluable", True, "D8"),
    ("equivalent", "positive", "not evaluable", True, "C0"),  # Astra: an evaluable P1-info positive survives
    ("inconclusive", "positive", "unclear", True, "C0"),
    ("not evaluable", "positive", "unclear", True, "C0"),
    ("equivalent", "negative", "unclear", True, "C6"),
    ("equivalent", "inconclusive", "unclear", True, "C7"),
    ("inconclusive", "inconclusive", "beyond, X+ higher", True, "D7"),
    ("inconclusive", "equivalent", "unclear", True, "C8"),
    ("not evaluable", "not evaluable", "beyond, X+ higher", True, "C5"),
])
def test_the_rows(cut, info, p2, ctl, row):
    assert S.joint(cut, info, p2, control_working=ctl)["row"] == row


def test_p2_evidence_is_kept_beside_an_unresolved_acute_reading():
    """Astra: (inconclusive, inconclusive, beyond X+) is not globally "unresolved"; P2's own reading stands."""
    r = S.joint("inconclusive", "inconclusive", "beyond, X+ higher", control_working=True)
    assert r["readings"]["p2"] == S.P2_READINGS["beyond, X+ higher"]


def test_a_failed_control_annotates_the_null_readings():
    r = S.joint("equivalent", "equivalent", "no relevant difference", control_working=False)
    assert "E4-D" in r["readings"]["p2"] and "E4-D" in r["readings"]["p1_info"]
    r = S.joint("positive", "positive", "beyond, X+ higher", control_working=False)
    assert "E4-D" not in r["readings"]["p2"] and "E4-D" not in r["readings"]["p1_info"]


def test_rows_beyond_the_design_are_marked_proposed():
    assert S.joint("positive", "negative", "unclear", control_working=True)["proposed"]
    assert not S.joint("positive", "positive", "unclear", control_working=True)["proposed"]
