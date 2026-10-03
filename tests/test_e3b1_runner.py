"""E3b-1's runner (scripts/e3b1.py): its registered rules, checked without running a formal stage
(experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md §12, tests 2, 4, 5, 7, 8 and 11-20)."""

from __future__ import annotations

import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def m():
    s = importlib.util.spec_from_file_location("e3b1_under_test", ROOT / "scripts" / "e3b1.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


TIMING = {"training": {**{a: {"t_gen": 60.0, "t_ckpt": 10.0} for a in ("ta", "tf", "n", "r")},
                       "n4": {"t_gen": 40.0, "t_ckpt": 10.0}},
          "validation_32": 100.0, "eval_plain": 120.0, "eval_donor": 130.0, "eval_single": 10.0, "probes": 5.0}


# ------------------------------------------------------------------ test 2: "none" equals deposit-off

def test_none_equals_deposit_off_with_mutated_genomes(m):
    from wormwars.brain import Brain, Genome
    from wormwars.e3 import maze_world as MW
    from wormwars.e3 import tuning as T
    cfg = m.cfg_for("none")
    cfg.world.max_ticks = 150
    cx = m.context(cfg)
    start = cx["seed"].genome
    pop = Genome.cat([start] * 3)
    sc = T.scales(cx["seed"].ext)
    pop = pop.mutate(cfg.mutation, generator=torch.Generator().manual_seed(5), scales=sc)
    assert not torch.equal(pop.w[1], start.w[0])  # mutated, not only the seed
    off = m.cfg_for("shared")
    off.world.max_ticks = 150
    off.world.maze_trail_d0 = 0.0
    ids = np.array([9900, 9901])
    out = []
    for c, acc in ((cfg, "none"), (off, "shared")):
        strain_of = torch.as_tensor(np.repeat(np.arange(3), 2)).view(-1, 1)
        w = MW.MazeWorld(c, cx["seed"].iface, Brain(pop), strain_of, run_seed=m.seed(), world_ids=np.tile(ids, 3),
                         access=acc)
        w.run(150)
        out.append((w.pos.clone(), w.heading.clone(), w.task_events()))
    assert torch.equal(out[0][0], out[1][0]) and torch.equal(out[0][1], out[1][1])
    for k in ("visit_tick", "visits", "entries", "first_b_tick", "occluded_ticks"):
        assert np.array_equal(out[0][2][k], out[1][2][k]), k
    assert int(out[0][2]["visits"].sum()) >= 0


# ------------------------------------------------------------------ test 4: the failure rules

def test_the_attempt_rules(m):
    assert m.next_attempt([]) == {"attempt": 1, "exclude": []}
    assert m.next_attempt([{"outcome": "crash or kill"}]) == {"attempt": 2, "exclude": []}
    assert m.next_attempt([{"outcome": "non-finite", "runs": [3]}]) == {"attempt": 2, "exclude": []}
    nf = [{"outcome": "non-finite", "runs": [3]}, {"outcome": "non-finite", "runs": [5]}]
    assert m.next_attempt(nf) == {"attempt": 3, "exclude": [3, 5]}
    assert "final" in m.next_attempt([{"outcome": "non-finite", "runs": [3]}, {"outcome": "crash or kill"}])
    assert "final" in m.next_attempt([{"outcome": "crash or kill"}, {"outcome": "crash or kill"}])
    assert "final" in m.next_attempt(nf + [{"outcome": "non-finite", "runs": [1]}])  # at most three


class FakeBatch:
    """run_batch(runs) for `train_attempts`: a script of outcomes, one per call."""

    def __init__(self, script):
        self.script, self.calls = list(script), []

    def __call__(self, runs):
        self.calls.append(list(runs))
        what = self.script.pop(0)
        if what == "ok":
            return [f"population of run {r}, attempt {len(self.calls)}" for r in runs]
        if what == "crash":
            raise RuntimeError("a crash")
        err = FloatingPointError(f"non-finite in run {what}")
        err.runs = [what]
        raise err


def test_attempt_3_excludes_the_named_runs_and_no_stopped_population_is_used(m):
    saved = []
    fake = FakeBatch([3, 5, "ok"])
    res = m.train_attempts([], list(range(8)), fake, lambda e: saved.append(json.loads(json.dumps(e))))
    assert fake.calls == [list(range(8)), list(range(8)), [0, 1, 2, 4, 6, 7]]
    assert res["failed"] == [3, 5] and res["runs"] == [0, 1, 2, 4, 6, 7]
    assert res["records"] == [f"population of run {r}, attempt 3" for r in res["runs"]]
    assert [e["outcome"] for e in res["entries"]] == ["non-finite", "non-finite", "completed"]
    assert res["entries"][0]["runs"] == [3]  # the record names the run before the abort
    assert saved[0][-1]["outcome"] is None  # each attempt is written before it runs


def test_a_crash_propagates_with_its_attempt_recorded_and_a_second_stop_is_final(m):
    entries = []
    with pytest.raises(RuntimeError):
        m.train_attempts(entries, list(range(4)), FakeBatch(["crash"]), lambda e: None)
    assert entries[-1]["outcome"] is None and not m.attempts_final(entries)  # a rerun follows
    with pytest.raises(RuntimeError):
        m.train_attempts(entries, list(range(4)), FakeBatch(["crash"]), lambda e: None)
    assert entries[0]["outcome"] == "crash or kill" and m.attempts_final(entries)
    nf_then_crash = []
    with pytest.raises(RuntimeError):
        m.train_attempts(nf_then_crash, list(range(4)), FakeBatch([2, "crash"]), lambda e: None)
    assert m.attempts_final(nf_then_crash)


def test_three_non_finite_attempts_end_the_stage_with_every_run_failed(m):
    res = m.train_attempts([], list(range(4)), FakeBatch([1, 1, 2]), lambda e: None)
    assert res["final"] and res["records"] is None and res["failed"] == [0, 1, 2, 3]


def test_every_in_stage_attempt_is_admitted_like_its_stage(m):
    asked = []

    def admit(k):
        asked.append(k)
        return k < 2

    res = m.train_attempts([], list(range(4)), FakeBatch([1, "ok"]), lambda e: None, admit=admit)
    assert asked == [2]  # attempt 1 was admitted with its stage
    assert res["final"] and res["not_admitted"] and res["records"] is None and res["failed"] == [0, 1, 2, 3]
    assert res["entries"][-1] == {"attempt": 2, "outcome": "not admitted"}
    assert m.attempts_final(res["entries"])


def test_a_refused_rerun_settles_the_stage(m, tmp_path, monkeypatch):
    monkeypatch.setattr(m.E, "EXP", tmp_path)
    monkeypatch.setattr(m, "EXP", tmp_path)
    (tmp_path / "train-tf.json").write_text(json.dumps({"outcome": m.E.OUTCOMES["stopped"]}), encoding="utf-8")
    assert m.stage_state("train-tf") == "awaiting-rerun"
    (tmp_path / "train-tf-refused.json").write_text("{}", encoding="utf-8")
    assert m.stage_state("train-tf") == "refused"


def test_the_hours_spent_include_the_running_stage(m, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(m.E, "clock", lambda: SimpleNamespace(spent_hours=lambda: 2.0))
    monkeypatch.setattr(m.time, "perf_counter", lambda: 3600.0 * 5)
    assert m.spent_hours(3600.0 * 4) == pytest.approx(3.0)
    assert m.spent_hours() == pytest.approx(2.0)


def test_evaluate_resumes_at_the_first_incomplete_chunk_and_keeps_completed_ones(m, tmp_path):
    calls = []

    def play(names):
        calls.append(list(names))
        if names == ["c"]:
            raise RuntimeError("stopped")
        return {"visits": np.full((len(names), 3), len(calls), dtype=float)}

    paths = [tmp_path / "eval-b1-shared-c00.npz", tmp_path / "eval-b1-shared-c01.npz"]
    m.run_chunk(paths[0], ["a", "b"], play)
    with pytest.raises(RuntimeError):
        m.run_chunk(paths[1], ["c"], play)
    assert paths[0].exists() and not paths[1].exists()
    m.run_chunk(paths[0], ["a", "b"], play)  # completed: not replayed
    assert calls == [["a", "b"], ["c"]]
    with np.load(paths[0], allow_pickle=False) as z:
        assert (z["visits"] == 1).all()
    with pytest.raises(SystemExit, match="organisms"):
        m.run_chunk(paths[0], ["a", "x"], play)  # a completed chunk must hold the planned organisms


# ------------------------------------------------------------------ test 5: the champion rule

def test_the_champion_is_the_best_of_all_32_ties_to_the_lower_index(m):
    means = np.zeros(32)
    means[[7, 19]] = 3.0
    assert m.champion_index(means) == 7
    assert m.champion_index(np.arange(32.0)) == 31


def test_champions_are_validated_with_the_arms_access(m):
    assert m.arm_cfg("n").world.maze_trail_access == "none"
    for arm in ("ta", "tf", "r"):
        assert m.arm_cfg(arm).world.maze_trail_access == "shared"
    seen = {}

    def fake(cfg, iface, genome, ids, world_seed, device, **kw):
        seen["access"], seen["n"], seen["ids"] = cfg.world.maze_trail_access, genome.n_strains, np.asarray(ids)
        s = np.zeros((genome.n_strains, len(ids)))
        s[4] = 2.0
        s[9] = 2.0
        from types import SimpleNamespace
        return SimpleNamespace(score=s)

    from wormwars.brain import Genome
    cx = m.context(m.arm_cfg("n"))
    pop = Genome.cat([cx["seed"].genome] * 32)
    k, means = m.validate_read_point(pop, "n", "cpu", rollout_fn=fake)
    assert k == 4 and seen["access"] == "none" and seen["n"] == 32
    assert np.array_equal(seen["ids"], m.ids("validation"))


# ------------------------------------------------------------------ test 7: the maze blocks

def test_the_blocks_are_disjoint_from_each_other_and_from_e3b0s(m):
    blocks = {k: set(range(*m.REGISTERED["ids"][k])) for k in ("validation", "learning", "calibration", "test")}
    assert [len(b) for b in blocks.values()] == [128, 128, 256, 256]
    e3b0 = set(range(0, 256)) | set(range(1000, 1256)) | set(range(2000, 2256)) | set(range(9000, 10_000))
    names = list(blocks)
    for i, a in enumerate(names):
        assert not blocks[a] & e3b0
        for b in names[i + 1:]:
            assert not blocks[a] & blocks[b]
    t = m.REGISTERED["train"]
    assert t["base"] == 10_000_000 and t["base"] + t["span"] == 20_000_000
    assert all(max(b) < t["base"] for b in blocks.values())
    B0 = json.loads((ROOT / "experiments" / "E3-ab-organism" / "E3b-0" / "stage-b3.json").read_text())
    assert m.seed() == 1_180_000 == B0["registered"]["maze_seed"]


# ------------------------------------------------------------------ test 8: the test block

def test_the_test_block_is_refused_outside_the_evaluation_stage(m):
    with pytest.raises(SystemExit, match="test block"):
        m.ids("test")
    with m.test_block_open():
        assert len(m.ids("test")) == 256
    with pytest.raises(SystemExit, match="test block"):
        m.ids("test")


# ------------------------------------------------------------------ test 11: the readings' needs

def _blocks(m, *, drop=(), n_mazes=256, seed_visits=5.0, gain=(0.3, 0.2), empty_nose=()):
    rng = np.random.default_rng(0)

    def org(v, fb=900.0, legs=2.5, nose=True):
        d = {"visits": np.full(n_mazes, v) + rng.normal(0, 0.01, n_mazes), "legs": np.full(n_mazes, legs),
             "later_first_b": np.full(n_mazes, fb), "later_leg_rate": np.full(n_mazes, 1.0)}
        if nose:
            d["nose_qualified"] = np.full(n_mazes, 0 if nose == "empty" else 100)
            d["nose_above_1.0"] = np.full(n_mazes, 0 if nose == "empty" else 2)
        return d

    champs = [{"arm": a, "run": i, "read": "final"} for a in ("ta", "tf") for i in range(8)]
    champs += [{"arm": "tf", "run": i, "read": "snap124"} for i in range(8)]
    names = ["seed"] + [f"{c['arm']}:{c['run']}:final" for c in champs if c["read"] == "final"]
    g = {"ta": gain[0], "tf": gain[1]}
    blocks = {"b1-shared": {}, "b2-none": {}, "b3-own": {}, "b4-shared": {}, "b5-peers": {}, "b6-shared": {},
              "b6-none": {}}
    for n in names:
        v = seed_visits if n == "seed" else seed_visits * (1 + g[n[:2]] + 0.01 * int(n.split(":")[1]))
        blocks["b1-shared"][n] = org(v, nose="empty" if n in empty_nose else True)
        blocks["b2-none"][n] = org(v * 0.8, nose=False)
        blocks["b3-own"][n] = org(v, fb=1000.0, nose=False)
        blocks["b5-peers"][n] = org(v, nose=False)
    for i in range(8):
        blocks["b4-shared"][f"tf:{i}:snap124"] = org(seed_visits * (1.1 + 0.01 * i))
    blocks["b6-shared"]["w2_alone"] = org(seed_visits - 1.0)
    blocks["b6-shared"]["follower"] = org(seed_visits + 3.0)
    for k in drop:
        blocks.pop(k)
    return blocks, champs


def test_a_missing_block_5_or_6_leaves_the_registered_readings_read(m):
    blocks, champs = _blocks(m, drop=("b5-peers", "b6-shared", "b6-none"))
    r = m.compute_readings(blocks, champs, m.default_plan(), n_mazes=256)
    for k in ("G", "S-gen", "S-trail", "S-peer"):
        assert r[k]["label"] not in ("not read",), k
    assert r["G"]["multiple_of_seed_minus_w2"] is None and r["G"]["multiple_of_follower_minus_seed"] is None


def test_the_registered_readings_on_synthetic_blocks(m):
    blocks, champs = _blocks(m)
    r = m.compute_readings(blocks, champs, m.default_plan(), n_mazes=256)
    assert r["G"]["label"] == "better" and r["G"]["estimate"] == pytest.approx(0.285, abs=0.01)
    assert r["G"]["multiple_of_seed_minus_w2"] == pytest.approx(r["G"]["delta_visits"] / 1.0, rel=1e-2)
    assert r["S-trail"]["estimate"] == pytest.approx(0.2 * 0.285, abs=0.01)  # e = 0.2 × (T − seed) / seed
    assert r["S-peer"]["estimate"] == pytest.approx(-0.1, abs=1e-6)  # (900 − 1000) / the seed's own 1000
    assert r["S-gen"]["n"] == 8


def test_a_run_short_of_the_full_test_block_is_not_read(m):
    blocks, champs = _blocks(m)
    for i in range(5):
        blocks["b1-shared"][f"ta:{i}:final"]["visits"] = blocks["b1-shared"][f"ta:{i}:final"]["visits"][:200]
    r = m.compute_readings(blocks, champs, m.default_plan(), n_mazes=256)
    assert r["G"]["label"] == "not read" and r["G"]["n_a"] == 3


def test_the_wording_carries_cut_3s_250_generations(m):
    plan = m.default_plan()
    assert m.final_index(plan, "tf") == 299 and "300 generations" in m.wording(plan)
    plan["G"]["tf"] = 250
    assert m.final_index(plan, "tf") == 249 and "250 generations" in m.wording(plan)
    blocks, champs = _blocks(m)
    assert "250 generations" in m.compute_readings(blocks, champs, plan, n_mazes=256)["wording"]


# ------------------------------------------------------------------ test 12: the replay coefficient

def test_the_replay_coefficient_is_per_organism_and_not_read_at_zero_donor_exposure(m):
    assert m.replay_coefficient(0.6, 0.3) == pytest.approx(2.0)
    assert m.replay_coefficient(0.6, 0.0) is None


def test_the_donors_differ_in_a_or_b_from_episode_1000(m):
    from wormwars.e3 import maze as M
    from wormwars.e3 import maze_runs as MR
    ids = np.arange(5000, 5016)
    eps, exc = MR.replay_donors(ids, m.seed(), 5)
    assert not exc and (eps >= 1000).all()
    for mid, ep in zip(ids, eps):
        _, p0 = M.maze_for(run_seed=m.seed(), maze_id=int(mid), episode=0, c=5)
        _, p1 = M.maze_for(run_seed=m.seed(), maze_id=int(mid), episode=int(ep), c=5)
        assert (p1.a, p1.b) != (p0.a, p0.b)
        for e in range(1000, int(ep)):
            _, pe = M.maze_for(run_seed=m.seed(), maze_id=int(mid), episode=e, c=5)
            assert (pe.a, pe.b) == (p0.a, p0.b)


# ------------------------------------------------------------------ test 13: admission and the cuts

def test_the_cuts_apply_in_order_until_the_plan_fits(m):
    big = json.loads(json.dumps(TIMING))
    plan = m.apply_cuts(big, spent=0.0)
    assert plan["fits"] and plan["cuts"] == []
    # hand-computed fit limits on t_gen (s): 93.5 uncut, 99.9 after cut 1, 125.0 after cut 2, 138.7 after cut 3
    for scale, want in ((1.6, ["n to runs 0-3"]), (1.8, ["n to runs 0-3", "r dropped"]),
                        (2.2, ["n to runs 0-3", "r dropped", "tf to 250 generations"])):
        t = json.loads(json.dumps(TIMING))
        for a in t["training"].values():
            a["t_gen"] *= scale
        p = m.apply_cuts(t, spent=0.0)
        assert p["cuts"] == want and p["fits"], (scale, p["planned_total"])
    t = json.loads(json.dumps(TIMING))
    for a in t["training"].values():
        a["t_gen"] *= 2.5
    assert not m.apply_cuts(t, spent=0.0)["fits"]


def test_the_cuts_change_the_plan_as_registered(m):
    t = json.loads(json.dumps(TIMING))
    for a in t["training"].values():
        a["t_gen"] *= 2.2
    p = m.apply_cuts(t, spent=0.0)
    assert p["runs"] == {"ta": 8, "tf": 8, "n": 4, "r": 0} and p["G"]["tf"] == 250
    assert p["projected_hours"]["train-n"] == pytest.approx((125 * t["training"]["n4"]["t_gen"] + 6 * 10.0) / 3600)


def test_a_training_projection_counts_its_checkpoints(m):
    assert m.n_checkpoints(125, 25) == 6  # 0, 25, 50, 75, 100, 124
    assert m.n_checkpoints(300, 25) == 13  # 0 … 275, 299
    assert m.n_checkpoints(250, 25) == 11
    p = m.projections(TIMING, m.default_plan())
    assert p["train-ta"] == pytest.approx((125 * 60 + 6 * 10) / 3600)


def test_admission(m):
    proj = {"train-ta": 4.0, "train-tf": 5.0, "train-n": 3.0, "train-r": 1.0, "champions": 1.0, "evaluate": 1.0,
            "g-e": 0.3}
    assert m.admit_training("train-ta", 15.0, proj)  # 15 + 5 + 2 = 22
    assert not m.admit_training("train-ta", 15.01, proj)
    assert m.admit_champions(22.0, proj) and not m.admit_champions(22.01, proj)
    assert m.admit_evaluate(23.0, proj) and not m.admit_evaluate(23.01, proj)


def test_a_refused_training_stage_stops_every_later_one(m):
    st = {"train-ta": "completed", "train-tf": "refused", "train-n": "absent", "train-r": "absent"}
    with pytest.raises(SystemExit, match="refused: no later training stage starts"):
        m.check_order("train-n", st.get)
    m.check_order("train-tf", st.get)  # its own state is the frame's business
    with pytest.raises(SystemExit, match="settled"):
        m.check_order("train-tf", {"train-ta": "awaiting-rerun"}.get)


def test_projections_after_failures_count_only_completed_runs(m):
    full = m.projections(TIMING, m.default_plan())
    fewer = m.projections(TIMING, m.default_plan(), done={"ta": 8, "tf": 4, "n": 6, "r": 0})
    assert fewer["champions"] < full["champions"] and fewer["evaluate"] < full["evaluate"]
    assert full["champions"] == pytest.approx((8 + 16 + 6 + 2) * 100.0 / 3600)


# ------------------------------------------------------------------ test 14: the fixed inputs

def test_a_changed_fixed_input_is_refused(m, monkeypatch):
    m.check_inputs()
    bad = dict(m.FIXED)
    k = next(iter(bad))
    bad[k] = "0" * 64
    monkeypatch.setattr(m, "FIXED", bad)
    with pytest.raises(SystemExit, match="has changed"):
        m.check_inputs()


# ------------------------------------------------------------------ test 15: g-e

def test_g_e_fails_when_one_generations_hash_differs(m):
    want = [[f"{r}-{g}" for g in range(26)] for r in range(4)]
    assert m.ge_verdict(want, want, [128, 8, 1])["all_match"]
    got = json.loads(json.dumps(want))
    got[2][17] = "sabotaged"
    v = m.ge_verdict(got, want, [128, 8, 1])
    assert not v["all_match"] and v["matching_generations_per_run"] == [26, 26, 25, 26]


def test_g_e_requires_every_leg(m):
    assert m.ge_passed({"passed": True}, {"all_match": True}, {"identical": True})
    assert not m.ge_passed({"passed": True}, {"all_match": True}, {"identical": False})
    assert not m.ge_passed({"passed": False}, {"all_match": True}, {"identical": True})
    assert not m.ge_passed({"passed": True}, {"all_match": False}, {"identical": True})
    assert not m.ge_passed({"passed": True}, {"skipped": "smoke"}, {"identical": True}, smoke=False)
    assert m.ge_passed({"passed": True}, {"skipped": "smoke"}, {"identical": True}, smoke=True)


# ------------------------------------------------------------------ test 16: the probes' thresholds

def test_the_levels_are_e3b0s_at_full_precision(m):
    rep = json.loads((ROOT / "experiments" / "E3-ab-organism" / "E3b-0" / "report.json").read_text())
    assert m.levels() == rep["component_tests"]["levels"]
    assert m.levels()[2] == 0.039810717055349776


def test_the_thresholds_apply_by_level(m):
    ok = {"A@0.35": 30.0, "A@0.8912509381337459": 10.5 / 0.8912509381337459 + 1e-9, "A@1.0": 10.5, "A@1.8197008586099825": 0.0}
    assert m.active_passes(ok)
    assert not m.active_passes({**ok, "A@0.35": 29.99})
    assert not m.active_passes({**ok, "A@1.0": 10.49})
    assert m.active_passes({**ok, "A@0.001": 30.0, "A@1.8197008586099825": -5.0})  # above 1.0: reported only
    assert m.active_passes({"A@0.8912509381337459": 12.0, "A@0.35": 31.0})  # K_D 12 < 30 is fine above 0.35


def test_e3b0s_seed_passes_at_its_levels(m):
    cfg = m.cfg_for("shared")
    cx = m.context(cfg)
    res = m.probe_organism(cx["seed"].genome, cx, cfg)
    assert res["structure"] == "bistable" and res["active_passed"] and res["one_nose_passed"]


# ------------------------------------------------------------------ test 17: the nose recorder

def test_the_recorder_runs_for_every_organism_under_shared_trails_in_blocks_1_4_and_6(m):
    champs = [{"arm": a, "run": i, "read": "final"} for a, n in (("ta", 8), ("tf", 8), ("n", 6), ("r", 2)) for i in range(n)]
    champs += [{"arm": "tf", "run": i, "read": "snap124"} for i in range(8)]
    plan = m.eval_plan(champs, coefs=None)
    shared = [c for c in plan if c["cond"] == "shared" and c["block"] in (1, 4, 6)]
    assert shared and all(c["recorder"] for c in shared)
    covered = {n for c in shared for n in c["names"]}
    assert {"seed", "w2_alone", "follower", "degraded", "tf:3:snap124", "n:5:final", "r:1:final"} <= covered
    assert not any(c["recorder"] for c in plan if c["cond"] != "shared" or c["block"] not in (1, 4, 6))


def test_an_empty_nose_count_is_not_read(m):
    blocks, champs = _blocks(m, empty_nose=("ta:0:final",))
    r = m.compute_readings(blocks, champs, m.default_plan(), n_mazes=256)
    assert r["nose_share_above_1"]["ta:0:final"] is None
    assert r["nose_share_above_1"]["ta:1:final"] == pytest.approx(0.02)


def test_the_plans_order_and_chunks(m):
    champs = [{"arm": a, "run": i, "read": "final"} for a, n in (("tf", 8), ("ta", 8)) for i in reversed(range(n))]
    plan = m.eval_plan(champs, coefs=None)
    b1 = [c for c in plan if c["block"] == 1]
    assert [len(c["names"]) for c in b1] == [16, 1]
    assert b1[0]["names"][:3] == ["seed", "ta:0:final", "ta:1:final"] and b1[1]["names"] == ["tf:7:final"]
    assert [c["block"] for c in plan] == sorted(c["block"] for c in plan)


# ------------------------------------------------------------------ test 18: champions and evaluate

def test_evaluate_requires_a_completed_champions(m):
    with pytest.raises(SystemExit, match="champions"):
        m.require_champions_state("absent")
    with pytest.raises(SystemExit, match="champions"):
        m.require_champions_state("awaiting-rerun")
    with pytest.raises(SystemExit, match="champions"):
        m.require_champions_state("final-stopped")
    m.require_champions_state("completed")


# ------------------------------------------------------------------ test 19: the replay pre-pass

def test_the_replay_pre_pass_has_two_legs(m):
    legs = []

    def play(names, cond, maze_ids, coefs):
        legs.append((cond, list(names), np.asarray(maze_ids).copy(), coefs))
        exp = {"shared": {"a": 0.6, "b": 0.6}, "replay": {"a": 0.3, "b": 0.0}}[cond]
        return {"exposure_mean": np.array([[exp[n]] * len(maze_ids) for n in names])}

    coefs = m.replay_prepass(["a", "b"], play, maze_ids=np.arange(5000, 5004))
    assert [l[0] for l in legs] == ["shared", "replay"]
    assert legs[1][3] == {"a": 1.0, "b": 1.0}
    assert coefs == {"a": pytest.approx(2.0), "b": None}


def test_the_pre_pass_projection(m):
    t = dict(TIMING)
    k = 17  # the seed and 16 T champions
    want = math.ceil(k / 16) * t["eval_plain"] + math.ceil(k / 8) * t["eval_donor"]
    assert m.prepass_seconds(t, k) == pytest.approx(want)


# ------------------------------------------------------------------ test 20: a smoke of every stage

@pytest.mark.slow
def test_a_smoke_of_every_stage(m):
    for stage in m.STAGES:
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "e3b1.py"), stage, "--smoke", "--device", "cpu"],
                           cwd=ROOT, capture_output=True, text=True, timeout=3600)
        assert r.returncode == 0, (stage, r.stdout[-2000:], r.stderr[-4000:])
    out = ROOT / "runs" / "e3b1-smoke"
    ev = json.loads((out / "evaluate.json").read_text(encoding="utf-8"))
    assert ev["outcome"] == "completed" and "G" in ev["readings"]


# ------------------------------------------------------------------ the code review's findings (D188)

def test_kill_reconciliation_has_its_tail(m):
    assert m.REGISTERED["rerun_kill_tail_seconds"] == 900  # E2's frame charges it beyond a kill's last write


def test_training_and_evaluation_write_durable_progress(m, tmp_path, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(m.E, "EXP", tmp_path)
    monkeypatch.setattr(m, "EXP", tmp_path)
    recs = [SimpleNamespace(spec=SimpleNamespace(run=i), checkpoints=[{"generation": 25}]) for i in range(2)]
    m.training_progress("train-ta")(recs, 25)
    doc = json.loads(m.E.partial_path("train-ta").read_text(encoding="utf-8"))
    assert doc["generation"] == 25 and doc["runs_in_batch"] == [0, 1]
    m.note_progress("evaluate", "eval-b1-shared-c00.npz")
    m.note_progress("evaluate", "eval-b1-shared-c01.npz")
    doc = json.loads(m.E.partial_path("evaluate").read_text(encoding="utf-8"))
    assert doc["completed_chunks"] == ["eval-b1-shared-c00.npz", "eval-b1-shared-c01.npz"]


def test_an_exhausted_stage_is_settled_on_its_rerun_without_a_batch(m):
    fake = FakeBatch([])
    res = m.train_attempts([{"attempt": 1, "outcome": "non-finite", "runs": [2]}, {"attempt": 2, "outcome": None}],
                           list(range(4)), fake, lambda e: None)
    assert res["final"] and fake.calls == [] and res["entries"][1]["outcome"] == "crash or kill"


def test_in_stage_admission_charges_the_running_time(m, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(m.E, "clock", lambda: SimpleNamespace(spent_hours=lambda: 15.0))
    monkeypatch.setattr(m.time, "perf_counter", lambda: 3600.0)
    proj = {"train-ta": 4.0, "champions": 1.0, "evaluate": 1.0}
    assert m.stage_admit("train-ta", proj, t_start=3600.0)(2)  # 15 + 0 + 5 + 2 = 22
    assert not m.stage_admit("train-ta", proj, t_start=0.0)(2)  # one hour of this process already spent


def test_an_in_stage_refusal_is_durable_and_stops_later_training(m, tmp_path, monkeypatch):
    monkeypatch.setattr(m.E, "EXP", tmp_path)
    monkeypatch.setattr(m, "EXP", tmp_path)
    m.refuse("train-tf", {"attempt": 2})
    assert m.stage_state("train-tf") == "refused"
    with pytest.raises(SystemExit, match="refused: no later training stage starts"):
        m.check_order("train-n", {"train-ta": "completed", "train-tf": m.stage_state("train-tf")}.get)


def test_runs_stopped_by_the_cap_are_not_run_and_others_failed(m):
    from wormwars import registration as reg
    assert m.unmade_label(reg.CapReached("cap")) == "not_run_runs"
    assert m.unmade_label(RuntimeError("crash")) == "failed_runs"


def test_earlier_training_records_must_be_published(m):
    seen = []
    m.check_order("train-n", {"train-ta": "completed", "train-tf": "skipped"}.get, require=seen.append)
    assert seen == ["train-ta", "train-tf"]


def test_training_admission_counts_completed_runs_after_failures(m):
    plan = m.default_plan()
    full = m.admission_projection(TIMING, plan, {"ta": [0, 1, 2, 3, 4, 5, 6, 7]}, "train-tf")
    fewer = m.admission_projection(TIMING, plan, {"ta": [0, 1]}, "train-tf")
    assert fewer["champions"] < full["champions"] and fewer["train-tf"] == full["train-tf"]


def test_each_reading_checks_its_own_denominator(m):
    blocks, champs = _blocks(m, seed_visits=0.0)
    blocks["b1-shared"]["seed"]["visits"] = np.zeros(256)  # exactly 0: _blocks adds noise
    r = m.compute_readings(blocks, champs, m.default_plan(), n_mazes=256)
    assert r["G"]["label"] == "not read" and r["S-trail"]["label"] == "not read" and r["S-gen"]["label"] == "not read"
    assert r["S-peer"]["label"] == "read" and r["S-peer"]["estimate"] == pytest.approx(-0.1, abs=1e-6)


def test_the_secondary_readings_carry_their_direction_and_holm(m):
    blocks, champs = _blocks(m)
    r = m.compute_readings(blocks, champs, m.default_plan(), n_mazes=256)
    sp = r["S-peer"]
    assert sp["label"] == "read" and sp["alternative"] == "less" and "lower_bound_95" not in sp
    assert sp["upper_bound_95"] == pytest.approx(sp["estimate"])  # zero spread: the point estimate
    assert sp["holm_rejected"] == r["holm"]["S-peer"]["rejected"]
    st = r["S-trail"]
    assert st["alternative"] == "greater" and st["holm_rejected"]
    assert st["conclusion"] == "increased trail dependence"


def test_s_trails_four_means_use_the_same_pairs_and_weights(m):
    blocks, champs = _blocks(m)
    for i in range(3):  # three T-A runs without their "none" condition
        blocks["b2-none"].pop(f"ta:{i}:final")
    r = m.compute_readings(blocks, champs, m.default_plan(), n_mazes=256)
    st, fm = r["S-trail"], r["S-trail"]["four_means"]
    assert fm["pairs"] == {"ta": 5, "tf": 8}
    lhs = fm["t_shared"] - fm["seed_shared"]
    rhs = (fm["t_none"] - fm["seed_none"]) + st["estimate"] * fm["seed_shared"]
    assert lhs == pytest.approx(rhs)


def test_readings_after_a_final_champions_stop_are_not_read(m):
    r = m.readings_from({"outcome": m.E.OUTCOMES["stopped"], "final": True}, {"plan": m.default_plan()}, {})
    assert all(r[k]["label"] == "not read" for k in ("G", "S-gen", "S-trail", "S-peer"))


def test_validation_is_one_chunk_of_32_by_128(m):
    seen = {}

    def fake(cfg, iface, genome, ids, world_seed, device, **kw):
        from types import SimpleNamespace
        seen["chunk_worlds"] = kw.get("chunk_worlds")
        return SimpleNamespace(score=np.zeros((genome.n_strains, len(ids))))

    from wormwars.brain import Genome
    cx = m.context(m.arm_cfg("ta"))
    m.validate_read_point(Genome.cat([cx["seed"].genome] * 32), "ta", "cpu", rollout_fn=fake)
    assert seen["chunk_worlds"] == 32 * 128


def test_the_route_overlap_matches_play_replay(m):
    from wormwars.e3 import maze_organisms as MO
    from wormwars.e3 import maze_runs as MR
    ids = np.array([5000, 5001, 5002])
    eps, _ = MR.replay_donors(ids, m.seed(), 5)
    cfg = m.cfg_for("shared")
    cx = m.context(cfg)
    rep = MR.play_replay(cfg, cx["seed"].iface, lambda: MO.brain(cx["seed"]), ids, m.seed(), donor_episodes=eps,
                         coef=1.0, ticks=1)
    assert np.allclose(m.route_overlap(ids, eps), rep["route_overlap"])


def test_each_chunks_composition_is_recorded(m):
    champs = [{"arm": a, "run": i, "read": "final"} for a in ("ta", "tf") for i in range(8)]
    comp = m.chunk_compositions(m.eval_plan(champs, coefs=None), n_mazes=256)
    b1 = [c for c in comp if c["chunk"].startswith("eval-b1-shared")]
    assert [c["composition"] for c in b1] == [[16, 256, 8], [1, 256, 8]]
    rep = [c for c in comp if c["chunk"].startswith("eval-b5-replay")]
    assert [c["composition"] for c in rep] == [[16, 256, 8], [16, 256, 8], [2, 256, 8]]  # with their donors


def test_distinct_organisms_in_one_chunk_play_as_their_own(m, monkeypatch):
    from wormwars.brain import Genome
    from wormwars.e3 import tuning as T
    monkeypatch.setitem(m.REGISTERED, "H", 150)
    cfg = m.cfg_for("shared")
    cx = m.context(cfg)
    mut = Genome.cat([cx["seed"].genome]).mutate(cfg.mutation, generator=torch.Generator().manual_seed(9),
                                                  scales={k: v * 8 for k, v in T.scales(cx["seed"].ext).items()})
    real = m.org_genome
    monkeypatch.setattr(m, "org_genome", lambda n, c, f: mut if n == "mut" else real(n, c, f))
    mazes = np.array([9900, 9901, 9902])
    both = m.play_names(["seed", "mut"], "shared", mazes, cx, "cpu")
    alone = {n: m.play_names([n], "shared", mazes, cx, "cpu") for n in ("seed", "mut")}
    for i, n in enumerate(("seed", "mut")):
        assert np.array_equal(both["visits"][i], alone[n]["visits"][0]) and np.array_equal(both["legs"][i], alone[n]["legs"][0])
    assert not np.array_equal(both["exposure_mean"][0], both["exposure_mean"][1])
