"""E3c's power simulation (scripts/e3c_power.py): centred on the true arm means (Astra, D207), and checked against
the registered readings (a sabotaged label must be caught)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def P():
    s = importlib.util.spec_from_file_location("e3c_power_under_test", ROOT / "scripts" / "e3c_power.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


@pytest.mark.parametrize("p", [0.0, 0.125, 0.25])
def test_a_mixture_has_the_requested_mean(P, p):
    x = P.mixture(np.random.default_rng(0), 4000, 8, 5.6, 0.06, p, 2.3, 0.3)
    assert x.mean() == pytest.approx(5.6, abs=0.03)


def test_scenario_contrasts_are_the_true_differences(P):
    rng = np.random.default_rng(1)
    res, (smod, sdense, pj, _) = P.simulate(rng, n_s=8, sd_s=0.06, p_mod=0.25, p_dense=0.125, f=(2.3, 0.3),
                                            d1=0.5, d2=-1.0, pj_sd_mult=1.0, shape="normal", seed_mean=5.0,
                                            trials=20000)
    assert smod.mean() - sdense.mean() == pytest.approx(0.5, abs=0.05)
    assert pj.mean() - smod.mean() == pytest.approx(-1.0, abs=0.05)


def test_the_registered_check_catches_a_changed_label(P):
    rng = np.random.default_rng(2)
    res, draws = P.simulate(rng, n_s=8, sd_s=0.06, p_mod=0.0, p_dense=0.0, f=(2.3, 0.3), d1=0.0, d2=0.0,
                            pj_sd_mult=1.0, shape="normal", seed_mean=5.0, trials=50)
    assert P.check_against_registered(res, draws, 5.0, 50, np.random.default_rng(3)) == 50
    res["Q2"]["label"][7] = "approximate (model-based): engineered initialization and tuning better, beyond the margin"
    with pytest.raises(AssertionError):
        P.check_against_registered(res, draws, 5.0, 50, np.random.default_rng(3))


def test_the_false_assertion_counter(P):
    """Astra (D208): every false label assertion counts, the margin ones included."""
    m_lo, m_hi = 0.08, 0.10

    def fa(lab, t):
        return P.false_assertion(P.APPROX + lab, t, m_lo, m_hi)

    assert fa("modular better, beyond the margin", 0.0) and fa("dense better, margin unresolved", 0.2)
    assert fa("modular better, beyond the margin", 0.09)  # true inside m_hi: "beyond" is false
    assert not fa("modular better, beyond the margin", 0.2)
    assert fa("modular better, within the margin", 0.09) and not fa("modular better, within the margin", 0.05)
    assert fa("no relevant difference", 0.08) and not fa("no relevant difference", 0.05)
    assert not fa("unclear", 0.3) and not fa("modular better, margin unresolved", 0.09)
    assert not P.false_assertion("not read: both at the floor", 0.3, m_lo, m_hi)


def test_the_vectorized_permutation_test_matches_the_registered_one(P):
    from wormwars.e3 import e3c_stats as S
    rng = np.random.default_rng(4)
    x, y = rng.normal(0.3, 0.1, (5, 8)), rng.normal(0.25, 0.1, (5, 6))
    got = P.vpermutation_p(x, y)
    for i in range(5):
        assert got[i] == pytest.approx(S.permutation_p(x[i], y[i]))


def test_every_scenario_stores_its_analytic_means(P):
    sc = {"p_mod": 0.25, "f": (2.3, 0.3), "d1": 0.5, "d2": -1.0}
    m = P.arm_means(sc)
    assert m["s_mod"] == pytest.approx(6.7 * 0.75 + 2.3 * 0.25)
    assert m["s_mod"] - m["s_dense"] == pytest.approx(0.5) and m["p_joint"] - m["s_mod"] == pytest.approx(-1.0)
