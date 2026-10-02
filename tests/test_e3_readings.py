"""E3a's registered readings on synthetic inputs (PREREGISTRATION §5, §8; tests 14 and 18): the
straight-run reference, G0 and G1, S2-a, S2-b, S2-c and the descriptive comparisons, every outcome
reached.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from wormwars.e3 import readings as R
from wormwars.e4s.readings import boot_means


def world_ci(a, b):
    d = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    m = boot_means(d, 10_000, 0)
    return {"mean": float(d.mean()), "lo95": float(np.percentile(m, 2.5)), "hi95": float(np.percentile(m, 97.5))}


def classify(c1, c2):
    if c1["lo95"] > 0.5 and c2["lo95"] > 0.5:
        return "uses"
    inside = lambda c: c["lo95"] > -0.25 and c["hi95"] < 0.25  # noqa: E731
    return "no material benefit" if inside(c1) and inside(c2) else "unclear"


def test_the_straight_run_reference():
    spawn, a, b = np.array([[0.0, 0.0]]), np.array([[11.5, 0.0]]), np.array([[11.5, 10.0]])
    t1 = (11.5 - 1.5) / 0.35
    t_leg = (10.0 - 3.0) / 0.35 + math.pi / 0.30
    assert R.straight_run_reference(spawn, a, b)[0] == 1 + math.floor((600 - t1) / t_leg)
    far = np.array([[300.0, 0.0]])
    assert R.straight_run_reference(spawn, far, b)[0] == 0


def _g0_inputs(blind_mean=0.5, blind_top=1.0):
    rng = np.random.default_rng(0)
    n = 1024
    return {"oracle": np.full(n, 12.0), "reference": np.full(n, 15), "s_8192": np.full(n, 9.0),
            "s_32": np.full(n, 7.0), "l1_switch": 6.0 + rng.normal(0, 0.5, n),
            "blind": {"constant": np.where(np.arange(n) < 900, blind_mean, blind_top),
                      "random-walk": np.zeros(n), "circle": np.zeros(n)}}


def test_g0_passes_and_fails_on_each_condition():
    assert R.g0(**_g0_inputs(), world_ci=world_ci)["passed"]
    bad = _g0_inputs(); bad["oracle"] = np.full(1024, 8.0)  # noqa: E702
    assert not R.g0(**bad, world_ci=world_ci)["oracle"]["passed"]
    bad = _g0_inputs(); bad["s_8192"] = np.full(1024, 5.0)  # noqa: E702
    assert not R.g0(**bad, world_ci=world_ci)["s_shuttle"]["passed"]
    bad = _g0_inputs(); bad["l1_switch"] = np.full(1024, 3.0)  # noqa: E702
    assert not R.g0(**bad, world_ci=world_ci)["l1_switch"]["passed"]
    assert not R.g0(**_g0_inputs(blind_mean=2.0), world_ci=world_ci)["blind"]["passed"]
    # the 90th-percentile world alone can fail it
    r = R.g0(**_g0_inputs(blind_mean=0.0, blind_top=4.0), world_ci=world_ci)
    assert not r["blind"]["passed"] and r["blind"]["constant"]["mean_ok"]


def test_g1_needs_every_part():
    n = 1024
    rng = np.random.default_rng(1)
    e, l1 = 5.5 + rng.normal(0, 0.5, n), np.full(n, 6.0)
    ok = R.g1(e=e, l1_switch=l1, no_latch=np.full(n, 2.0), one_module=np.full(n, 1.0), component=True,
              assays={"clamp": True, "settable": True, "hold": True, "reset": True}, world_ci=world_ci, classify=classify)
    assert ok["passed"]
    worse = R.g1(e=e, l1_switch=l1, no_latch=e - 0.1, one_module=np.full(n, 1.0), component=True,
                 assays={"clamp": True, "settable": True, "hold": True, "reset": True}, world_ci=world_ci, classify=classify)
    assert not worse["passed"] and not worse["controls"]["passed"]
    assert not R.g1(e=e, l1_switch=l1, no_latch=np.full(n, 2.0), one_module=np.full(n, 1.0), component=True,
                    assays={"clamp": True, "settable": True, "hold": True, "reset": False}, world_ci=world_ci,
                    classify=classify)["passed"]


@pytest.mark.parametrize("flags,want", [
    ([True] * 8, "evolution found a working selector in 8 of 8 runs"),
    ([True] * 7 + [False], "evolution found a working selector in 7 of 8 runs"),
    ([True] * 3 + [False] * 5, "evolution found a working selector in 3 of 8 runs, not reliably"),
    ([False] * 8, "no working selector was found in 300 generations at 02's sigmas, with untied mutation at 1×, "
                  "from this initial distribution"),
    ([True] * 2 + [None] * 2 + [False] * 4, "evolution found a working selector in 2 of 6 read runs, not reliably"),
])
def test_s2a(flags, want):
    assert R.s2a(flags)["wording"] == want


def test_s2b_reaches_every_outcome():
    w = [True] + [False] * 7
    assert R.s2b(np.full(8, 1.0), w, [False] * 8)["label"] == "evolution better"
    assert R.s2b(np.full(8, -1.0), w, [False] * 8)["label"] == "random sampling better"
    assert R.s2b(np.array([0.1, -0.1] * 4), w, w)["label"] == "as good"
    assert R.s2b(np.array([2.0, -2.0, 1.5, -1.0, 0.5, 2.5, -1.5, 0.0]), w, w)["label"] == "unclear"
    assert R.s2b(np.full(8, 1.0), [False] * 8, [False] * 8)["label"] == "neither found a working selector"
    four = R.s2b(np.full(4, 1.0), w[:4], [False] * 4)
    assert four["descriptive"] and four["label"] == "evolution better"


def test_s2c_wording_and_interval():
    zero = R.s2c(0, 1024)
    assert zero["hi"] == pytest.approx(1 - 0.025 ** (1 / 1024), rel=1e-6)
    assert zero["wording"].startswith("none of 1024 draws passed the screen and the full check")
    assert not R.s2c(9, 1024, ga_distribution=True)["generation_zero"]
    assert R.s2c(10, 1024, ga_distribution=True)["generation_zero"]
    capped = R.s2c(64, 1024, unchecked=7)
    assert capped["wording"].startswith("at least 64")


def test_the_descriptive_comparison_has_no_working_branch():
    assert R.compare(np.full(8, 1.0))["label"] == "better"
    assert R.compare(np.full(8, -1.0))["label"] == "worse"
    assert R.compare(np.array([0.1, -0.1] * 4))["label"] == "as good"


def test_s2b_rule_one_reads_every_champion_not_only_the_pairs():
    """A working GA champion in an unpaired run (random sampling reduced to 4) is not 'neither'."""
    r = R.s2b(np.full(4, 0.0), [False] * 4, [False] * 4, ga_all=[False] * 7 + [True], rs_all=[False] * 4)
    assert r["label"] != "neither found a working selector"
    assert "against a blind search over the whole range" in r["wording"]


def test_s2a_zero_with_unread_runs_says_so():
    r = R.s2a([False] * 6 + [None] * 2)
    assert r["wording"].startswith("no working selector was found") and "(0 of 6 read)" in r["wording"]


def test_a_capped_census_reports_no_ordinary_interval():
    r = R.s2c(64, 1024, unchecked=7)
    assert r["lo"] is None and r["hi"] is None


def test_stage_three_has_the_neither_branch():
    assert R.compare(np.full(8, 1.0), a_working=[False] * 8, b_working=[False] * 8)["label"] == \
        "neither found a working selector"
    assert R.compare(np.full(8, 1.0), a_working=[True] + [False] * 7, b_working=[False] * 8)["label"] == "better"
