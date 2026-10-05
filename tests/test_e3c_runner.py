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


# ------------------------------------------------------------------ the replay and probe (D205; the owner's choice)

def test_the_tour_match_compares_directed_moves():
    """Astra's counterexample: on the tree 1-0-5, 24 round trips to 1 then 24 to 5 share cells at lag 48 but no
    directed move; exactly `period` moves leave nothing to compare."""
    mod = _fresh("e3c_tour_directed")
    seq = np.array([0, 1] * 24 + [0, 5] * 24 + [0])
    assert mod.tour_match(seq, period=48) == 0.0
    assert np.isnan(mod.tour_match(np.array([0, 1] * 24 + [0]), period=48))  # 48 moves
    assert mod.tour_match(np.array([0, 1] * 25 + [0]), period=48) == 1.0  # 50 moves, 2 compared
    assert mod.tour_match_best_lag(seq, lags=range(44, 53)) <= 1.0


def test_the_tour_match_finds_a_repeated_circuit():
    mod = _fresh("e3c_tour")
    tour = np.array([0, 1, 2, 1, 3, 1, 0, 4])  # an Euler tour of a 5-cell tree: 2 x 4 edges = 8 transitions
    walk = np.repeat(np.tile(tour, 6), 7)  # each cell held for 7 ticks, the circuit repeated
    assert mod.tour_match(walk, period=8) == pytest.approx(1.0)
    rng = np.random.default_rng(0)
    assert mod.tour_match(np.repeat(rng.integers(0, 5, 60), 3), period=8) < 0.5
    assert np.isnan(mod.tour_match(np.array([0, 0, 1]), period=8))


def test_cells_come_from_head_positions():
    mod = _fresh("e3c_cells")
    # cell (col, row) owns its 3 x 3 open block at 1 + 4 col and the corridor after it
    xy = np.array([[1.5, 1.5], [5.2, 1.5], [4.5, 9.9], [20.9, 20.9]])
    assert mod.cell_index(xy, c=5).tolist() == [0, 1, 10, 24]


def test_hash_comparison(m):
    want = [["a", "b", "c"], ["d", "e", "f"]]
    assert m.compare_hashes(want, want) == {"all_match": True, "matching_generations_per_run": [3, 3]}
    got = [["a", "b", "x"], ["d", "e", "f"]]
    assert m.compare_hashes(got, want) == {"all_match": False, "matching_generations_per_run": [2, 3]}


def test_w2_with_its_own_resting_turn_is_w2_alone(m):
    import torch
    from wormwars.connectome import load_connectome
    from wormwars.e3 import maze_organisms as MO
    cfg = m.cfg_for("shared", 8)
    con = load_connectome()
    a = m.w2_alone(con, cfg.brain)
    b = m.w2_turn(con, cfg.brain, MO.REST_TURN["W2"])
    assert torch.equal(a.genome.bias, b.genome.bias) and torch.equal(a.genome.w, b.genome.w)
    c = m.w2_turn(con, cfg.brain, 0.8)
    assert not torch.equal(a.genome.bias, c.genome.bias)


@pytest.mark.slow
def test_a_smoke_of_the_replay_reproduces_the_pilot_on_the_cpu(m):
    for stage in ("pilot", "replay"):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "e3c.py"), stage, "--smoke", "--device", "cpu"],
                           cwd=ROOT, capture_output=True, text=True, timeout=3600)
        assert r.returncode == 0, (stage, r.stdout[-2000:], r.stderr[-4000:])
    rec = json.loads((ROOT / "runs" / "e3c-smoke" / "replay.json").read_text(encoding="utf-8"))
    assert rec["outcome"] == "completed" and rec["replay"]["hashes"]["all_match"] is True  # CPU repeats exactly
    for f in rec["replay"]["genome_files"]:
        assert (ROOT / f["path"]).exists()
    probes = rec["probes"]
    for name in ("seed", "w2_alone", *[f"s_dense_{r}" for r in rec["replay"]["runs"]]):
        p = probes[name]
        assert set(p) >= {"intact", "noses_removed", "retained_fraction"}
        assert set(p["intact"]) >= {"visits_per_maze", "coverage", "tour_match"}
    assert len(rec["turn_sweep"]) >= 3 and rec["consequence"] in ("coverage", "scent-dependent", "mixed")
    assert rec["replay"]["description"] == "replay" and set(rec["replay"]["best_sha256"]) == {str(r) for r in rec["replay"]["runs"]}
    for r in rec["replay"]["runs"]:  # every champion keeps identifiable paths (both reviewers)
        paths = probes[f"s_dense_{r}"]["intact"]["sample_paths"]
        assert paths and {"maze", "wey", "cells", "ticks"} <= set(paths[0])


def test_the_outcome_rule_has_its_three_branches(m):
    def probe(r, cov=1.0, tm=0.9):
        return {"retained_fraction": r, "intact": {"coverage": cov, "tour_match": tm}}
    names = ["a", "b", "c"]
    assert m.consequence({k: probe(0.95) for k in names}, names) == "coverage"
    assert m.consequence({k: probe(0.9, 0.95, 0.5) for k in names}, names) == "coverage"  # inclusive bounds
    assert m.consequence({k: probe(0.3) for k in names}, names) == "scent-dependent"
    assert m.consequence({k: probe(0.5) for k in names}, names) == "scent-dependent"
    assert m.consequence({"a": probe(0.95), "b": probe(0.95), "c": probe(0.95, tm=0.4)}, names) == "mixed"
    assert m.consequence({"a": probe(0.95), "b": probe(0.95), "c": probe(0.95, tm=None)}, names) == "mixed"
    assert m.consequence({"a": probe(0.95), "b": probe(0.3), "c": probe(0.95)}, names) == "mixed"
    assert m.consequence({"a": probe(None), "b": probe(0.3), "c": probe(0.3)}, names) == "mixed"


def test_the_replay_accepts_the_pilot_made_on_earlier_scripts(monkeypatch, tmp_path):
    """Both reviewers: the general rule requires every guarded path unchanged since the pilot, and the replay's
    own code is a change. The replay's loader checks the record (committed, pinned, same environment) and the
    engine paths only; `scripts` is exempt, nothing else."""
    mod = _fresh("e3c_loader")
    rec = {"outcome": "completed", "provenance_at_start": {"git_commit": "abc"}}
    body = json.dumps(rec).encode()
    (tmp_path / "pilot.json").write_bytes(body)
    monkeypatch.setattr(mod.E, "EXP", tmp_path)
    import hashlib
    monkeypatch.setitem(mod.REGISTERED["replay"], "pilot_sha256", hashlib.sha256(body).hexdigest())
    seen = {}
    monkeypatch.setattr(mod.E, "require_committed", lambda path: seen.setdefault("committed", path))
    monkeypatch.setattr(mod.E.reg, "require_same_env", lambda a, b: seen.setdefault("env", True))

    def same_code(commit, paths):
        if "scripts" in paths:
            raise SystemExit("the scripts changed")
        seen["code"] = (commit, list(paths))

    monkeypatch.setattr(mod.E.reg, "require_same_code", same_code)
    args = type("A", (), {"smoke": False, "guarded": False})()
    got = mod.require_pilot(args, {"git_commit": "def"})
    assert got["outcome"] == "completed" and seen["code"][0] == "abc" and "wormwars" in seen["code"][1]
    assert "committed" in seen and seen["env"]
    monkeypatch.setitem(mod.REGISTERED["replay"], "pilot_sha256", "0" * 64)
    with pytest.raises(SystemExit):
        mod.require_pilot(args, {"git_commit": "def"})
