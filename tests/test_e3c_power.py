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
    res["Q2"]["label"][7] = "engineered initialization and tuning better, beyond the margin"
    with pytest.raises(AssertionError):
        P.check_against_registered(res, draws, 5.0, 50, np.random.default_rng(3))
