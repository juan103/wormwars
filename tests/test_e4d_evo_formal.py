"""The evolutionary E4-D's formal helpers (`wormwars/e4/evo_formal.py`), against the bound pre-registration
(`experiments/E4-two-minds/E4-D-evo/PREREGISTRATION.md`, D274): runs and seeds (§3), blocks and the pre-flight (§4),
the registered assertions, the dependencies and the reports (§5, §7)."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.e4 import evo_formal as FM
from wormwars.e4 import evo_stats as ES


def test_runs_and_seeds():
    for arm, first, n in (("L", 0, 32), ("F", 100, 4), ("S", 200, 32)):
        rs = FM.runs(arm)
        assert [r["run"] for r in rs] == list(range(first, first + n))
        assert [r["seed"] for r in rs] == [1_440_000 + first + k for k in range(n)]
        assert all(r["arm"] == arm for r in rs)


def test_blocks_follow_the_registration():
    v, t = FM.blocks("L", 0)
    assert v[0] == 55_000 and v[-1] == 55_063 and t[0] == 55_064 and t[-1] == 55_127
    v, t = FM.blocks("L", 31)
    assert v[0] == 55_000 + 128 * 31 and t[-1] == 55_000 + 128 * 31 + 127
    v, t = FM.blocks("F", 103)
    assert v[0] == 60_000 + 128 * 3 and t[0] == 60_064 + 128 * 3
    v, t = FM.blocks("S", 231)
    assert v[0] == 61_000 + 128 * 31 and t[-1] == 61_000 + 128 * 31 + 127
    assert list(FM.CHECK_IDS) == list(range(54_000, 54_064))
    assert list(FM.CHECKPOINT_IDS) == list(range(54_100, 54_108))
    with pytest.raises(ValueError):
        FM.blocks("L", 32)


def test_the_blocks_are_disjoint_from_each_other_and_from_the_pilot():
    named = FM.all_blocks()
    ids = np.concatenate(list(named.values()))
    assert len(ids) == len(np.unique(ids))
    assert len(named) == 2 + 2 * (32 + 4 + 32)
    for lo, hi in FM.PILOT_RANGES:
        assert not np.any((ids >= lo) & (ids < hi))


def test_the_preflight_records_replacements_and_refuses_collisions():
    named = {"a": np.array([10, 11, 12]), "b": np.array([20, 21])}
    out = FM.preflight(named, resolve=lambda ids: np.where(ids == 11, 13, ids))
    assert out["replacements"] == {"a": [[11, 13]]}
    with pytest.raises(FM.IntegrityError):
        FM.preflight(named, resolve=lambda ids: np.where(ids == 12, 20, ids))  # lands in another block
    with pytest.raises(FM.IntegrityError):
        FM.preflight({"a": np.array([53_000])}, resolve=lambda ids: ids)  # a pilot id


def test_training_ids_must_stay_in_range():
    FM.check_ids(np.array([[100_000_000, 109_999_999]]))
    FM.check_ids(np.array([FM.CHECKPOINT_IDS]))
    for bad in (110_000_000, 99_999_999, 55_000):
        with pytest.raises(FM.IntegrityError):
            FM.check_ids(np.array([[100_000_001, bad]]))


def test_per_maze_balance():
    rf = np.array([[[1, 0], [0, 0]]])
    df = np.array([[[0, 1], [0, 0]]])
    FM.assert_balanced(rf, df, "ok")
    with pytest.raises(FM.IntegrityError):
        FM.assert_balanced(np.array([[[1, 0], [1, 0]]]), np.array([[[0, 1], [0, 0]]]), "one maze unbalanced")
    with pytest.raises(FM.IntegrityError):
        FM.assert_balanced(np.array([[[1, 1]]]), np.array([[[0, 0]]]), "same totals would not do")


def test_the_conditions_map_to_the_sources():
    assert FM.CONDITIONS == {"intact": "real", "reversed": "decoy", "removed": "none", "fixed": "fixed0"}
    assert set(FM.BALANCED) == {"removed", "fixed", "cut", "eg"}


def test_integrity_errors_are_recognised():
    assert FM.is_integrity("IntegrityError: x")
    assert FM.is_integrity("FloatingPointError: a fitness is not finite")
    assert FM.is_integrity("RuntimeError: integrity: link-free strains [3] distinguish the assignments")
    assert not FM.is_integrity("RuntimeError: CUDA error: an illegal memory access")
    assert not FM.is_integrity("KeyboardInterrupt: ")


def test_a_rerun_needs_an_infrastructure_reason():
    FM.check_rerun_reason("infrastructure: the driver reset")
    for bad in (None, "", "  ", "the numbers looked odd"):
        with pytest.raises(SystemExit):
            FM.check_rerun_reason(bad)


def test_the_dependencies():
    D = FM.DEPENDS
    assert D["check"] == ()
    assert D["train-l"] == ("check",) and D["evaluate-l"] == ("train-l",) and D["report-l"] == ("evaluate-l",)
    assert D["train-f"] == ("report-l",) and D["evaluate-f"] == ("train-f",) and D["report-f"] == ("evaluate-f",)
    assert D["train-s"] == ("report-l",) and D["evaluate-s"] == ("train-s",) and D["report-s"] == ("evaluate-s",)
    assert not any(s.endswith("-f") for s in D["train-s"] + D["evaluate-s"] + D["report-s"])  # F never blocks S
    assert FM.GROUP == {"check": "l", "train-l": "l", "evaluate-l": "l", "report-l": "l", "train-f": "f",
                        "evaluate-f": "f", "report-f": "f", "train-s": "s", "evaluate-s": "s", "report-s": "s"}
    assert FM.CAPS == {"l": 8.0, "f": 1.5, "s": 6.0}


def test_s_is_triggered_only_by_the_two_states():
    assert FM.s_triggered({"state": ES.STATES[3]}) and FM.s_triggered({"state": ES.STATES[4]})
    for st in (*ES.STATES[:3], "not evaluable", "not completed"):
        assert not FM.s_triggered({"state": st})


def _run(gain_k, eg_k=63):
    return {"test": {"intact": {"real_first": 64 + gain_k, "decoy_first": 64 - gain_k - 2, "neither": 2},
                     "eg": {"real_first": eg_k, "decoy_first": eg_k, "neither": 128 - 2 * eg_k}}}


def test_the_report_goes_through_the_registered_rule_and_refuses_a_reduced_arm():
    per_run = [_run(48) for _ in range(31)] + [_run(-1)]
    rep = FM.report("L", per_run)
    want = ES.reading([48 / 128] * 31 + [-1 / 128], n_expected=32)
    assert rep["reading"]["state"] == want["state"] and rep["reading"]["lb"] == pytest.approx(want["lb"])
    assert rep["gains"][0] == 48 / 128 and rep["minus_eg"][0] == (64 + 48 - 63) / 128
    with pytest.raises(ValueError):
        FM.report("L", per_run[:31])
    assert FM.report("F", [_run(40)] * 4)["reading"]["n"] == 4


def test_s_against_its_start():
    per_run = [{**_run(40), "start": {"real_first": 64 + 10, "decoy_first": 50, "neither": 4}} for _ in range(32)]
    rep = FM.improvement_report(per_run)
    assert rep["differences"][0] == (40 - 10) / 128
    assert rep["reading"]["state"] == ES.IMPROVEMENT_STATES[0]
    with pytest.raises(ValueError):
        FM.improvement_report(per_run[:31])
