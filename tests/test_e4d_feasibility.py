"""E4-D's feasibility rules (docs/E4/E4-D-DESIGN.md v2.1 §2, §4): the trial readout, σ_D's choice, the control's
selection, the maze-level bootstrap bound and the success verdict."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.e4 import feasibility as F


def _ev(fc, assign):
    """first_candidate and assign per trial, as `TrialWorld.trial_events` gives them (one wey)."""
    fc, assign = np.asarray(fc).reshape(-1, 1), np.asarray(assign)
    return {"first_candidate": fc, "assign": assign}


def test_the_readout():
    r = F.readout(_ev([0, 1, -1, 1], [0, 0, 1, 1]))
    assert r["real_first_all"] == pytest.approx(2 / 4) and r["entries"] == 3
    assert r["real_first_entries"] == pytest.approx(2 / 3) and r["neither"] == 1


def test_the_readout_with_no_entries_is_undefined():
    r = F.readout(_ev([-1, -1], [0, 1]))
    assert r["real_first_entries"] is None and r["entry_rate"] == 0.0


@pytest.mark.parametrize("scout, want", [
    ({3: (0.6, 0.9), 6: (0.8, 0.8), 9: (0.9, 0.9), 12: (0.95, 0.95)}, 6),
    ({3: (0.6, 0.9), 6: (0.8, 0.7), 9: (0.9, 0.9), 12: (0.95, 0.95)}, 9),
    ({3: (0.6, 0.9), 6: (0.7, 0.8), 9: (0.7, 0.9), 12: (0.7, 0.95)}, None),
])
def test_sigma_is_the_smallest_meeting_both(scout, want):
    """(the oracle's real-first share over all trials, X0's entry rate) per σ."""
    assert F.choose_sigma({s: {"oracle_real_first_all": a, "x0_entry_rate": b} for s, (a, b) in scout.items()}) == want


def test_the_control_selection_and_its_ties():
    res = {("nose", 2.0): 0.8, ("comparator", 3.0): 0.8, ("comparator", 1.0): 0.6, ("nose", 0.5): 0.2}
    assert F.choose_control(res) == ("nose", 2.0)  # the smaller w first
    res[("comparator", 2.0)] = 0.8
    assert F.choose_control(res) == ("comparator", 2.0)  # then comparator-origin


def test_the_bootstrap_bound():
    per_maze = np.array([1.0] * 50 + [0.5] * 14)
    lo = F.maze_bound(per_maze, seed=20_261_013, resamples=4000)
    normal = per_maze.mean() - 1.645 * per_maze.std() / np.sqrt(len(per_maze))
    assert abs(lo - normal) < 0.01 and lo < per_maze.mean()
    assert F.maze_bound(np.full(64, 0.5), seed=1, resamples=500) == pytest.approx(0.5)


def test_per_maze_means_pair_the_two_assignments():
    ev = _ev([0, 0, 1, 0], [0, 1, 0, 1])  # trials ordered maze-major: maze 0 (assign 0, 1), maze 1 (0, 1)
    assert F.per_maze(ev, n_mazes=2).tolist() == [0.5, 0.0]


OK = {"control": {"real_first_all": 0.8}, "control_bound": 0.7, "x0_invariant": True, "reversal_ok": True,
      "fixed_cue_invariant": True, "removal_identical": True, "latch_held": True, "oracle_real_first_all": 0.9}


def test_the_verdict():
    v = F.verdict(OK)
    assert v["passed"] and v["reading"].startswith("passed")
    for k, bad in (("control", {"real_first_all": 0.74}), ("control_bound", 0.5)):
        assert not F.verdict({**OK, k: bad})["passed"], k


@pytest.mark.parametrize("check", ["x0_invariant", "reversal_ok", "fixed_cue_invariant", "removal_identical", "latch_held"])
def test_a_failed_integrity_check_voids_the_result(check):
    """Both reviewers: a failed exactness, mapping or latch check is not a slots result."""
    v = F.verdict({**OK, check: False})
    assert not v["passed"] and v["reading"].startswith("void")


def test_a_performance_failure_is_read_with_the_oracle():
    weak = {**OK, "control": {"real_first_all": 0.6}}
    assert "did not carry" in F.verdict(weak)["reading"]
    assert "infeasible" in F.verdict({**weak, "oracle_real_first_all": 0.6})["reading"]


def test_reversal_is_a_mapping_check():
    normal = _ev([0, 1, 1, -1], [0, 0, 1, 1])
    reversed_ = _ev([0, 1, 1, -1], [1, 1, 0, 0])  # the same choices with the labels exchanged
    assert F.reversal_ok(normal, reversed_)
    assert not F.reversal_ok(normal, _ev([0, 0, 1, -1], [1, 1, 0, 0]))
