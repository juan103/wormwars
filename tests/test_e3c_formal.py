"""E3c's formal plan (PREREGISTRATION.md, bound at 69d7cd5; §3-§6, §10, §12): the runs and the cuts, the
checkpoint schedule, the blocks, the champion and W2-turn rules, P-joint's candidates by logged hash, the
projection and admission, and the engine freeze."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.e3 import e3c_formal as F

EARLIER = ((0, 256), (1000, 1256), (2000, 2256), (4000, 4128), (4500, 4628), (5000, 5256), (6000, 6256),
           (7000, 7256), (7300, 7556), (7600, 7728), (8000, 8100), (9000, 10000))


def test_the_runs_and_the_cuts():
    full = F.runs(F.PLAN_FULL)
    assert [r["run"] for r in full["s_mod"]] == list(range(8))
    assert [r["run"] for r in full["s_dense"]] == list(range(10, 18))
    assert [r["run"] for r in full["p_sel"]] == [20, 21, 22, 23]
    assert all(r["seed"] == 1_300_000 + r["run"] for arm in full.values() for r in arm)
    cut3 = F.runs(F.plan_after_cuts(3))
    assert [r["run"] for r in cut3["s_mod"]] == list(range(6)) and [r["run"] for r in cut3["s_dense"]] == list(range(10, 16))
    assert [r["run"] for r in cut3["p_sel"]] == [20, 21]
    assert F.plan_after_cuts(1) == {"trails_off": False, "p_sel_runs": 4, "s_runs": 8}
    assert F.plan_after_cuts(2) == {"trails_off": False, "p_sel_runs": 2, "s_runs": 8}


def test_the_compositions():
    assert F.training_composition("s_mod", F.PLAN_FULL) == [256, 8, 8]
    assert F.training_composition("p_sel", F.PLAN_FULL) == [128, 8, 8]
    assert F.training_composition("s_dense", F.plan_after_cuts(3)) == [192, 8, 8]
    assert F.training_composition("p_sel", F.plan_after_cuts(3)) == [64, 8, 8]


def test_the_checkpoint_schedule():
    g = F.checkpoint_generations()
    assert g == [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 299]
    assert len(g) == 21


def test_the_blocks_are_disjoint_from_each_other_and_every_earlier_block():
    blocks = [F.BLOCKS[k] for k in ("validation", "learning", "test", "benchmark")]
    sets = [set(range(*b)) for b in blocks]
    assert [len(s) for s in sets] == [128, 128, 256, 256]
    for i, a in enumerate(sets):
        for b in sets[i + 1:]:
            assert not a & b
        for lo, hi in EARLIER:
            assert not a & set(range(lo, hi))
    assert F.TRAIN["base"] == 40_000_000 and F.TRAIN["span"] == 10_000_000
    assert F.BENCH_TRAIN["base"] >= 50_000_000


def test_the_champion_rule_ties_to_the_lower_index():
    assert F.champion_index([1.0, 3.0, 3.0, 2.0]) == 1
    assert F.champion_index([5.0]) == 0


def test_the_w2_turn_choice_and_its_ties():
    grid = F.TURN_GRID
    means = [1.0] * len(grid)
    means[grid.index(1.2)] = 5.6
    means[grid.index(1.4)] = 5.6  # tie: the smaller |turn| wins
    assert F.choose_turn(grid, means) == 1.2
    means = [0.0] * len(grid)
    means[grid.index(-0.4)] = 2.0
    means[grid.index(0.4)] = 2.0  # equal |turn|: the earlier grid position
    assert F.choose_turn(grid, means) == -0.4


def test_p_joints_candidate_is_found_by_its_logged_hash():
    hashes = ["a", "b", "c"]
    assert F.index_of_hash(hashes, "b") == 1
    with pytest.raises(ValueError):
        F.index_of_hash(hashes, "z")


def test_the_projection_and_the_admission_rule():
    t = {"train_s": 74.0, "train_s_cut": 58.0, "train_psel": 43.0, "train_psel_cut": 25.0, "checkpoint_8": 30.0,
         "checkpoint_6": 24.0, "checkpoint_4": 18.0, "checkpoint_2": 12.0, "champion_chunk": 30.0,
         "eval_chunk": 60.0, "eval_single": 20.0}
    full = F.projection_hours(t, F.PLAN_FULL)
    assert full == pytest.approx(F.projection_hours(t, F.plan_after_cuts(0)))
    assert F.projection_hours(t, F.plan_after_cuts(3)) < F.projection_hours(t, F.plan_after_cuts(2)) \
        < F.projection_hours(t, F.plan_after_cuts(1)) < full
    assert F.admit(t, remaining_hours=full + 0.01)["cuts"] == 0
    a = F.admit(t, remaining_hours=F.projection_hours(t, F.plan_after_cuts(2)) + 0.01)
    assert a["cuts"] == 2 and a["admitted"]
    r = F.admit(t, remaining_hours=0.1)
    assert r["admitted"] is False and r["cuts"] == 3


def test_the_engine_freeze():
    ok = [("A", "wormwars/e3/e3c_formal.py"), ("M", "scripts/e3c.py"), ("M", "tests/test_e3c_formal.py")]
    assert F.engine_freeze(ok) == {"changed": [], "passes": True}
    bad = ok + [("M", "wormwars/e04a/evolve.py"), ("D", "configs/x.yaml"), ("M", "requirements.txt")]
    got = F.engine_freeze(bad)
    assert got["passes"] is False and got["changed"] == [["M", "wormwars/e04a/evolve.py"], ["D", "configs/x.yaml"],
                                                          ["M", "requirements.txt"]]
    assert F.engine_freeze(bad[:4], amended={"wormwars/e04a/evolve.py"})["passes"] is True
    assert F.engine_freeze([("M", "wormwars/e3/e3c_stats.py")])["passes"] is False  # bound with the text


def test_the_projection_counts_23_checkpoint_plays_per_batch():
    """Astra (D211): the 21 post-hoc plays plus evolve_batch's in-loop plays at generations 0 and 299."""
    t = {k: 0.0 for k in ("train_s", "train_s_cut", "train_psel", "train_psel_cut", "checkpoint_6", "checkpoint_4",
                          "checkpoint_2", "champion_chunk", "eval_chunk", "eval_single")}
    t["checkpoint_8"] = 3600.0
    plan = {"trails_off": False, "p_sel_runs": 4, "s_runs": 8}
    # 23 plays per S batch, two S batches, plus P-joint's two learning points in champions
    assert F.projection_hours(t, plan) == pytest.approx(23 * 2 + 2 + F.GE_HOURS)
