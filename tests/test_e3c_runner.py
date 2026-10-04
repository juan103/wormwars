"""E3c's runner (scripts/e3c.py): the pilot's fixed rules (docs/E3/E3c-DESIGN.md v2.1 §5)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def m():
    s = importlib.util.spec_from_file_location("e3c_under_test", ROOT / "scripts" / "e3c.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


def test_the_pilot_blocks_are_disjoint_from_every_earlier_block(m):
    learn = set(range(*m.REGISTERED["pilot"]["learning"]))
    smoke = set(range(*m.REGISTERED["smoke_ids"]))
    assert len(learn) == 128
    earlier = set()
    for lo, hi in ((0, 256), (1000, 1256), (2000, 2256), (4000, 4128), (4500, 4628), (5000, 5256), (6000, 6256),
                   (7000, 7256), (7300, 7556), (9000, 9100), (9100, 9106), (9200, 9206), (9300, 9334), (9400, 9406),
                   (9500, 9756), (9800, 9900), (9900, 9903)):
        earlier |= set(range(lo, hi))
    assert not learn & earlier and not smoke & earlier and not learn & smoke
    base, span = m.REGISTERED["pilot"]["train_base"], m.REGISTERED["pilot"]["train_span"]
    assert base >= 20_000_000 and base + span <= 2**31  # above E3b-1's 10 000 000-19 999 999


def test_every_pilot_run_has_its_own_number_and_seed(m):
    runs = m.pilot_runs()
    assert len(runs) == 9 and {r["arm"] for r in runs} == {"s_mod", "s_dense", "p_sel"}
    assert len({r["run"] for r in runs}) == 9 and len({r["seed"] for r in runs}) == 9


def test_the_floor_criterion(m):
    w2 = 1.7
    assert m.off_floor([{"validation_mean": 1.0}, {"validation_mean": 2.71}], w2) is True
    assert m.off_floor([{"validation_mean": 2.70}], w2) is False  # strictly above W2 + 1
    assert m.decision({"s_mod": True, "s_dense": False}, complete=True) == "mazes"
    assert m.decision({"s_mod": False, "s_dense": False}, complete=True) == "open arena"
    assert m.decision({"s_mod": False, "s_dense": False}, complete=False) == "inconclusive"


@pytest.mark.slow
def test_a_smoke_of_the_pilot(m):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "e3c.py"), "pilot", "--smoke", "--device", "cpu"],
                       cwd=ROOT, capture_output=True, text=True, timeout=3600)
    assert r.returncode == 0, (r.stdout[-2000:], r.stderr[-4000:])
    rec = json.loads((ROOT / "runs" / "e3c-smoke" / "pilot.json").read_text(encoding="utf-8"))
    assert rec["outcome"] == "completed" and rec["decision"] in ("mazes", "open arena", "inconclusive")
    assert set(rec["arms"]) == {"s_mod", "s_dense", "p_sel"}
    n = len(range(*m.REGISTERED["smoke_ids"])[:4])
    for name in ("w2_alone", "seed"):
        assert len(rec["references"][name]["per_maze"]["visits"]) == n
    for arm in rec["arms"].values():
        for r in arm["runs"]:  # the distributions the power analysis needs (both reviewers)
            assert all(len(c["validation_counts"]) == n for c in r["learning_curve"])
            assert len(r["generation0"]["mean_visits"]) == 4 and len(r["generation0"]["K_D_A_at_q0"]) == 4
            assert len(r["batch_seconds"]) == 3 and len(r["final_generation_best"]["per_maze"]["visits"]) == n
            assert r["frozen_checked"] is True


def test_the_generation0_diagnostics_are_e3as(m):
    """Offsets from the seed's resting turn (q free from 0, 60 ticks), and A's K_D at q held at 0 (E3a's log)."""
    import numpy as np
    from wormwars.connectome import load_connectome
    from wormwars.e3 import assembly as AS
    from wormwars.e4s import arms as A
    cfg = m.cfg_for("shared", 8)
    cx = AS.context(load_connectome(), A.load_l1(), cfg.brain)
    seed = cx["seed"]
    d = m.generation0_offsets(seed.genome, seed, cfg, ref=m.resting_turn(seed, cfg))
    assert abs(d["turn_offset"][0]) < 1e-6 and d["K_D_A_at_q0"][0] > 1.0
    g = AS.draw("s_dense", cx, np.random.default_rng(3), 4)
    d = m.generation0_offsets(g, cx["dense"], cfg, ref=m.resting_turn(seed, cfg))
    assert len(d["turn_offset"]) == 4 and len(set(round(x, 6) for x in d["K_D_A_at_q0"])) == 4


# ------------------------------------------------------------------ the code check (both: "fix first")

def _fresh(name):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "e3c.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


def test_the_cap_leaves_room_for_the_benchmarked_runtime(m):
    assert m.REGISTERED["cap_gpu_hours"] >= 4.5  # Fable: about 2.8 h projected; a rerun must also fit


def test_the_frozen_check_catches_a_leak(m):
    import torch
    from wormwars.connectome import load_connectome
    from wormwars.e3 import assembly as AS
    from wormwars.e4s import arms as A
    cfg = m.cfg_for("shared", 8)
    cx = AS.context(load_connectome(), A.load_l1(), cfg.brain)
    for arm in AS.TRAINED:
        start = AS.draw(arm, cx, np.random.default_rng(1), 3)
        sc = AS.arm_scales(arm, cx)
        moved = start.clone().mutate(cfg.mutation, torch.Generator().manual_seed(2), scales=sc)
        m.assert_frozen(start, moved, sc)  # the mask's own mutations pass
        b = start.bias.clone()
        b[:, 0] += 1.0  # a worm neuron's bias: frozen in every arm
        with pytest.raises(AssertionError):
            m.assert_frozen(start, start.with_params(bias=b), sc)


@pytest.mark.slow
def test_a_failed_pilot_keeps_what_finished_and_is_inconclusive(monkeypatch):
    mod = _fresh("e3c_failing")
    mod.use_smoke(None)
    real, calls = mod.EV.evolve_batch, []

    def second_fails(*a, **k):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("injected: the second batch fails")
        return real(*a, **k)

    monkeypatch.setattr(mod.EV, "evolve_batch", second_fails)
    args = type("A", (), {"device": "cpu", "smoke": True, "guarded": False, "rerun": False, "reason": None})()
    with pytest.raises(RuntimeError):
        mod.cmd_pilot(args)
    rec = json.loads((ROOT / "runs" / "e3c-smoke" / "pilot.json").read_text(encoding="utf-8"))
    assert rec["outcome"] != "completed" and rec["decision"] == "inconclusive"
    assert {r["arm"] for r in rec["completed_runs"]} == {"s_mod", "p_sel"}
    assert all(r["learning_curve"] for r in rec["completed_runs"])
