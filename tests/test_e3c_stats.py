"""E3c's registered statistics (the pre-registration's §7): Welch with Holm, intervals at each contrast's Holm
level, and the dual practical margin (the owner's choice, 2026-10-05: 0.10 of the seed's mean and 0.5 visits per
wey, combined so that both must agree)."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from wormwars.e3 import e3c_stats as S


def test_welch_matches_scipy():
    rng = np.random.default_rng(1)
    x, y = rng.normal(0.4, 0.1, 8), rng.normal(0.3, 0.3, 8)
    w = S.welch(x, y, level=0.95)
    ref = stats.ttest_ind(x, y, equal_var=False)
    assert w["estimate"] == pytest.approx(x.mean() - y.mean())
    assert w["p"] == pytest.approx(ref.pvalue)
    ci = ref.confidence_interval(0.95)
    assert (w["lo"], w["hi"]) == (pytest.approx(ci.low), pytest.approx(ci.high))


def test_the_two_margins_in_units_of_the_seed():
    lo, hi = S.margins(seed_mean=5.0)  # 0.10 and 0.5 / 5.0 = 0.10
    assert lo == pytest.approx(0.10) and hi == pytest.approx(0.10)
    lo, hi = S.margins(seed_mean=4.0)  # 0.10 and 0.125
    assert (lo, hi) == (pytest.approx(0.10), pytest.approx(0.125))
    lo, hi = S.margins(seed_mean=6.25)  # 0.10 and 0.08
    assert (lo, hi) == (pytest.approx(0.08), pytest.approx(0.10))


@pytest.mark.parametrize("est,lo,hi,rejected,want", [
    (0.30, 0.15, 0.45, True, "A better, beyond the margin"),     # the interval clears the larger margin
    (0.12, 0.05, 0.19, True, "A better, margin unresolved"),      # straddles the margins
    (0.04, 0.01, 0.07, True, "A better, within the margin"),      # detectable, inside the smaller margin
    (-0.30, -0.45, -0.15, True, "B better, beyond the margin"),
    (0.01, -0.05, 0.07, False, "no relevant difference"),         # inside the smaller margin both ways
    (0.05, -0.05, 0.15, False, "unclear"),
])
def test_the_label_rule(est, lo, hi, rejected, want):
    got = S.label(est, lo, hi, rejected, m_lo=0.08, m_hi=0.10, a="A", b="B")
    assert got == want


def test_beyond_needs_the_larger_margin_and_negligible_the_smaller():
    # lo between the two margins: beyond the smaller only, so not "beyond"
    assert S.label(0.2, 0.09, 0.3, True, m_lo=0.08, m_hi=0.10, a="A", b="B") == "A better, margin unresolved"
    # hi between the two margins: inside the larger only, so not "no relevant difference"
    assert S.label(0.0, -0.05, 0.09, False, m_lo=0.08, m_hi=0.10, a="A", b="B") == "unclear"


def test_holm_levels_and_intervals_agree():
    """A contrast is rejected exactly when its interval at its Holm level excludes 0."""
    rng = np.random.default_rng(3)
    for _ in range(200):
        a, b, c = (rng.normal(m, 0.15, 8) for m in rng.uniform(0.2, 0.5, 3))
        r = S.contrasts({"Q1": (a, b), "Q2": (c, a)}, alpha=0.05)
        for q in ("Q1", "Q2"):
            excl = r[q]["lo"] > 0 or r[q]["hi"] < 0
            assert excl == r[q]["rejected"], (q, r[q])
        p = sorted(r[q]["p"] for q in r)
        first = min(r, key=lambda q: r[q]["p"])
        assert r[first]["level"] == pytest.approx(1 - 0.05 / 2)


def test_a_contrast_not_read_enters_holm_with_p_1():
    rng = np.random.default_rng(4)
    a, b = rng.normal(0.4, 0.05, 8), rng.normal(0.1, 0.05, 8)
    r = S.contrasts({"Q1": None, "Q2": (a, b)}, alpha=0.05)
    assert r["Q1"]["read"] is False and r["Q1"]["rejected"] is False
    assert r["Q2"]["rejected"] and r["Q2"]["level"] == pytest.approx(0.975)


def test_the_readings_end_to_end():
    rng = np.random.default_rng(5)
    seed = 5.0
    smod, sdense, pjoint = (rng.normal(m, s, 8) for m, s in ((0.36, 0.01), (0.37, 0.012), (0.38, 0.18)))
    out = S.readings(d={"s_mod": smod, "s_dense": sdense, "p_joint": pjoint}, seed_mean=seed,
                     visits={"s_mod": 6.8, "s_dense": 6.85}, w2_alone=1.7)
    assert out["Q1"]["label"] in ("no relevant difference", "modular better, within the margin",
                                  "dense better, within the margin")
    assert out["margins"] == {"m_lo": pytest.approx(0.10), "m_hi": pytest.approx(0.10)}
    assert "mann_whitney_p" in out["Q1"] and "mann_whitney_p" in out["Q2"]
    floor = S.readings(d={"s_mod": smod, "s_dense": sdense, "p_joint": pjoint}, seed_mean=seed,
                       visits={"s_mod": 2.0, "s_dense": 2.1}, w2_alone=1.7)
    assert floor["Q1"]["label"] == "not read: both at the floor" and floor["Q1"]["read"] is False
