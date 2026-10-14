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


def test_blocks_follow_amendment_1():
    v, t = FM.blocks("L", 0)
    assert v[0] == 65_000 and v[-1] == 65_063 and t[0] == 65_064 and t[-1] == 65_127
    v, t = FM.blocks("L", 31)
    assert v[0] == 65_000 + 128 * 31 and t[-1] == 65_000 + 128 * 31 + 127 == 69_095
    v, t = FM.blocks("F", 103)
    assert v[0] == 69_200 + 128 * 3 and t[-1] == 69_711
    v, t = FM.blocks("S", 231)
    assert v[0] == 70_000 + 128 * 31 and t[-1] == 74_095
    assert list(FM.CHECK_IDS) == list(range(64_000, 64_064))
    assert list(FM.CHECKPOINT_IDS) == list(range(64_100, 64_108))
    assert FM.TRAIN == (120_000_000, 130_000_000) and FM.TIMING == (130_000_000, 140_000_000)
    with pytest.raises(ValueError):
        FM.blocks("L", 32)


def test_the_blocks_are_disjoint_from_each_other_and_from_the_pilot():
    named = FM.all_blocks()
    ids = np.concatenate(list(named.values()))
    assert len(ids) == len(np.unique(ids))
    assert len(named) == 2 + 2 * (32 + 4 + 32)
    for lo, hi in FM.PILOT_RANGES + FM.SPENT:
        assert not np.any((ids >= lo) & (ids < hi))
    for lo, hi in FM.SPENT:  # the training and timing ranges too
        for a, b in (FM.TRAIN, FM.TIMING):
            assert hi <= a or lo >= b


def test_the_preflight_records_replacements_and_refuses_collisions():
    named = {"a": np.array([10, 11, 12]), "b": np.array([20, 21])}
    out = FM.preflight(named, resolve=lambda ids: np.where(ids == 11, 13, ids))
    assert out["replacements"] == {"a": [[11, 13]]}
    with pytest.raises(FM.IntegrityError):
        FM.preflight(named, resolve=lambda ids: np.where(ids == 12, 20, ids))  # lands in another block
    with pytest.raises(FM.IntegrityError):
        FM.preflight({"a": np.array([53_000])}, resolve=lambda ids: ids)  # a pilot id
    with pytest.raises(FM.IntegrityError):
        FM.preflight({"a": np.array([55_001])}, resolve=lambda ids: ids)  # spent by a smoke before Amendment 1


def test_training_ids_must_stay_in_range():
    FM.check_ids(np.array([[120_000_000, 129_999_999]]))
    FM.check_ids(np.array([FM.CHECKPOINT_IDS]))
    for bad in (130_000_000, 119_999_999, 100_000_000, 65_000):
        with pytest.raises(FM.IntegrityError):
            FM.check_ids(np.array([[120_000_001, bad]]))


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


def _cond(rf, df):
    """Counts and per-maze arrays consistent with them: rf real-first, df decoy-first, the rest neither."""
    flat = np.array([1] * rf + [2] * df + [0] * (128 - rf - df)).reshape(64, 2)
    pm = {"real_first": (flat == 1).astype(int).tolist(), "decoy_first": (flat == 2).astype(int).tolist(),
          "neither": (flat == 0).astype(int).tolist()}
    return {"real_first": rf, "decoy_first": df, "neither": 128 - rf - df, "per_maze": pm}


def _run(gain_k, eg_k=63, r=None, start=None):
    test = {"intact": _cond(64 + gain_k, 64 - gain_k - 2), "eg": _cond(eg_k, eg_k)}
    for c in ("reversed", "removed", "fixed", "cut"):
        test[c] = _cond(60, 60)
    out = {**(r or {}), "validation_shares": [0.5] * 32, "test": test}
    if start is not None:
        out["start"] = _cond(*start)
    return out


def _arm(arm, gains, **kw):
    return [_run(g, r=r, **kw) for g, r in zip(gains, FM.runs(arm))]


def test_the_report_goes_through_the_registered_rule_and_refuses_a_reduced_arm():
    per_run = _arm("L", [48] * 31 + [-1])
    rep = FM.report("L", per_run)
    want = ES.reading([48 / 128] * 31 + [-1 / 128], n_expected=32)
    assert rep["reading"]["state"] == want["state"] and rep["reading"]["lb"] == pytest.approx(want["lb"])
    assert rep["gains"][0] == 48 / 128 and rep["minus_eg"][0] == (64 + 48 - 63) / 128
    with pytest.raises(FM.IntegrityError):
        FM.report("L", per_run[:31])
    assert FM.report("F", _arm("F", [40] * 4))["reading"]["n"] == 4


def test_an_incomplete_or_duplicated_arm_is_refused():
    """Astra (D276): 32 copies of one run, or a run missing a condition or its per-maze counts, never reach the rule."""
    good = _arm("L", [40] * 32)
    with pytest.raises(FM.IntegrityError, match="runs are"):
        FM.report("L", [good[0]] * 32)
    for sabotage in (lambda r: r["test"].pop("fixed"), lambda r: r["test"]["cut"].pop("per_maze"),
                     lambda r: r["validation_shares"].pop(), lambda r: r["test"]["eg"].update(neither=3)):
        bad = [json_copy(x) for x in good]
        sabotage(bad[7])
        with pytest.raises(FM.IntegrityError):
            FM.report("L", bad)


def json_copy(x):
    import json
    return json.loads(json.dumps(x))


def test_the_descriptives():
    sc = np.zeros((2, 4, 3))
    sc[0] = [[1, 1, 1], [1, 1, 1], [0, 0, 0], [0.5, 0.5, 0.5]]  # two tied at 1
    sc[1] = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1]]  # three tied at 1/3
    assert FM.tie_shares(sc) == [0.5, 0.75]
    source = np.array([[0, 1, 0, 0], [0, 2, 3, 3]])
    child = np.array([[False, False, True, True], [False, True, True, True]])
    assert FM.turnover(source, child) == [2 / 3]  # breeding 1 draws on 0, 2, 3; breeding 0 made 2 and 3 as children
    assert FM.lineage_mutations(source, child, 2) == 2  # strain 2, a child of 3, itself a child of 0
    assert FM.lineage_mutations(source, child, 0) == 0


def test_s_against_its_start():
    per_run = _arm("S", [40] * 32, start=(74, 50))
    rep = FM.improvement_report(per_run)
    assert rep["differences"][0] == (40 - 10) / 128
    assert rep["reading"]["state"] == ES.IMPROVEMENT_STATES[0]
    with pytest.raises(FM.IntegrityError):
        FM.improvement_report(per_run[:31])
