"""E3a's runner (scripts/e3a.py; PREREGISTRATION §5, §7, §9; tests 15-17 and 22).

- the world ranges, disjoint from each other and from every earlier range;
- the stage plan, the seeds and the frame;
- the reductions and admission on synthetic projections;
- the champion rule's tie-break;
- the stage dependencies.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name, file):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def mod():
    return _load("e3a_under_test", "e3a.py")


def test_the_world_ranges_are_disjoint_from_each_other_and_every_earlier_range(mod):
    from wormwars.e1 import task as T
    from wormwars.exp02 import grid as GRID
    m0 = _load("e4s0_ranges_for_e3a", "e4s0.py")
    m1 = _load("e4s1_ranges_for_e3a", "e4s1.py")
    earlier = [(0, 10_000), (900_000_000, 901_000_000), (950_000_000, 951_000_000), (960_000_000, 961_000_000),
               (970_000_000, 971_000_000), (980_000_000, 981_000_000), (990_000_000, 991_000_000),
               (992_700_000, 993_000_000), (993_000_000, 995_000_000), (995_000_000, 996_000_000),
               (996_000_000, 1_000_000_000)]
    earlier += [(int(r[0]), int(r[-1]) + 1) for r in (T.PILOT_IDS, T.TUNING_IDS, T.GATE_IDS, T.HOLDOUT_04A_IDS,
                                                       GRID.CHECKPOINT_IDS, GRID.GATE_IDS, GRID.PROBE_IDS)]
    earlier += list(m0.formal_ranges().values()) + list(m1.formal_ranges().values())
    mine = list(mod.formal_ranges().values())
    s = sorted(mine)
    for (a0, a1), (b0, b1) in zip(s, s[1:]):
        assert a1 <= b0, (a0, a1, b0, b1)
    for m0_, m1_ in mine:
        for e0, e1 in earlier:
            assert m1_ <= e0 or e1 <= m0_, ((m0_, m1_), (e0, e1))


def test_the_plan_seeds_and_frame(mod):
    assert mod.STAGES == ["project", "g-e", "g0", "g1", "calibrate-e", "census", "train-1", "train-2", "champions-2",
                          "train-3", "train-4", "champions-3", "calibrate", "evaluate"]
    assert mod.BATCHES == ["ga", "rs", "stage3", "btask"]
    assert mod.run_seed("ga", 3) == mod.run_seed("rs", 3) == 1_170_003
    assert mod.run_seed("stage3", 3) == 1_176_003 and mod.run_seed("btask", 3) == 1_177_003
    R = mod.REGISTERED
    assert R["cap_gpu_hours"] == 30.0 and R["admit_hours"] == 28.0 and R["reserve_factor"] == 1.25
    assert R["generations"] == {"ga": 300, "rs": 300, "stage3": 500, "btask": 800}
    assert R["ga"]["population"] == 32 and R["ga"]["worlds_per_strain"] == 16 and R["checkpoint_every"] == 25
    assert mod.E.task_config is mod.task_config  # the frame builds the shuttle's configuration
    cfg = mod.task_config()
    assert cfg.world.task == "shuttle" and cfg.world.max_ticks == 600 and cfg.evo.worlds_per_strain == 16


def _hours(scale=1.0):
    return {"fixed": 2.0 * scale, "ga": 1.7 * scale, "rs": 1.7 * scale, "stage3": 2.8 * scale,
            "btask_per_generation": 4.5 * scale / 800, "evaluation_per_champion": 0.05 * scale}


def test_no_reduction_when_the_plan_fits(mod):
    p = mod.reductions(_hours(), 0.0)
    assert p["steps"] == [] and p["fits"] and p["btask_generations"] == 800 and p["stage3_runs"] == 8


def test_the_reductions_apply_in_order(mod):
    p = mod.reductions(_hours(1.8), 0.0)  # 1.25 x 14.3 x 1.8 = 32.2 h: over the cap
    assert p["steps"][:1] == ["B-task, to 300 generations"] and p["fits"]
    p = mod.reductions(_hours(100.0), 0.0)
    assert p["steps"] == ["B-task, to 300 generations", "B-task, dropped", "Stage 3, to runs 0-3", "Stage 3, dropped",
                          "random sampling, to runs 0-3"]
    assert not p["fits"] and p["rs_runs"] == 4 and p["stage3_runs"] == 0 and p["btask_generations"] == 0


def test_the_champion_rule_breaks_ties_low(mod):
    assert mod.champion_of(np.array([1.0, 3.0, 3.0, 2.0])) == 1
    assert mod.champion_of(np.array([0.0])) == 0


def test_admission_counts_the_batch_and_the_reserved_evaluation(mod):
    p = {"btask_generations": 800, "stage3_runs": 8, "rs_runs": 8}
    h = _hours()
    assert mod.batch_hours("btask", p, h) == pytest.approx(4.5)
    assert mod.batch_hours("rs", {**p, "rs_runs": 4}, h) == pytest.approx(0.85)
    assert mod.remaining_eval_hours(1, p, h) == pytest.approx(0.05 * 32 + 1.0)


def test_stage_three_needs_the_frozen_stage_two_champions(mod, tmp_path, monkeypatch):
    """A batch refuses to start before its dependencies (test 16): train-3 without champions-2."""
    monkeypatch.setattr(mod.E, "EXP", tmp_path)
    monkeypatch.setattr(mod.E, "OUT", tmp_path)
    assert mod.batch_state("train-1") == "absent"
    with pytest.raises(SystemExit):
        mod.E.require_earlier(type("A", (), {"smoke": True, "guarded": False})(), {}, "champions-2")
