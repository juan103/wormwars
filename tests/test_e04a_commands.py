"""04a's runner (`scripts/e04a.py`) through its stage commands, with fake rollouts, smoke sizes and a
scratch folder: the order of stages and the projection gate, the once-only refusals and the rerun
rule, the hash checks before any hold-out world is touched, not-completed records, the verdict
written before the extras, and the registered rules as functions.

These command tests run with the formal guards off (`smoke=True, guarded=False`). The guards
themselves are tested as functions here and in `test_registration.py`; their wiring runs in the
guarded smoke run on the binding commit."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("e04a_script", ROOT / "scripts" / "e04a.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _events(n_strains, n_worlds, count):
    """A minimal event table consistent with `count` targets reached per world."""
    T = 12
    act = np.full((n_strains, n_worlds, T), -1)
    reach = np.full((n_strains, n_worlds, T), -1)
    for s in range(n_strains):
        for w in range(n_worlds):
            c = int(count[s, w])
            act[s, w, :c + 1] = np.arange(c + 1) * 10
            reach[s, w, :c] = np.arange(c) * 10 + 9
    z = np.zeros((n_strains, n_worlds, T))
    return {"activation_tick": act, "reach_tick": reach, "path_length": z + 5.0, "target_x": z + 5.0,
            "target_y": z + 6.0, "start_x": z + 1.0, "start_y": z + 1.0, "end_x": z + 5.0, "end_y": z + 6.0}


class Fakes:
    """count = 3 for a genome whose mean bias is positive, else 0; 0 under the mirrored and constant
    probes; scripted arms reach 0 except the oracle (4). Every id passed in is recorded."""

    def __init__(self):
        self.calls, self.crash_at = [], None

    def rollout(self, cfg, iface, genome, ids, world_seed, device, chunk_worlds=None, **kw):
        ids = np.asarray(ids)
        n_w = ids.shape[-1]
        self.calls.append(("neural", cfg.world.food_probe, genome.n_strains, ids.shape, ids.copy()))
        if self.crash_at is not None and len(self.calls) == self.crash_at:
            raise RuntimeError("boom")
        good = (genome.bias.mean(dim=1).cpu().numpy() > 0).astype(np.float32)
        real = cfg.world.food_probe == "real"
        count = np.repeat(good[:, None], n_w, axis=1) * (3.0 if real else 0.0)
        return SimpleNamespace(score=count, progress=np.full(count.shape, 0.5, np.float32),
                               events=_events(genome.n_strains, n_w, count),
                               final_head=np.full((genome.n_strains, n_w, 2), 3.0, np.float32))

    def rollout_brain(self, cfg, iface, brain, ids, world_seed, device, ticks=None):
        n_w = len(ids)
        self.calls.append(("scripted", cfg.world.food_probe, 1, (n_w,), np.asarray(ids).copy()))
        v = 4.0 if type(brain).__name__ == "OracleBrain" else 0.0
        count = np.full((1, n_w), v, np.float32)
        return SimpleNamespace(score=count, events=_events(1, n_w, count),
                               final_head=np.full((1, n_w, 2), 3.0, np.float32))


@pytest.fixture
def m(tmp_path, monkeypatch):
    mod = _load()
    mod.use_smoke(SimpleNamespace(command="project", batch=None), folder=tmp_path)  # nothing outside tmp_path
    fakes = Fakes()
    monkeypatch.setattr(mod.rollout_mod, "rollout", fakes.rollout)
    monkeypatch.setattr(mod, "rollout_brain", fakes.rollout_brain)
    mod._fakes = fakes
    return mod


def _args(command, batch=None, rerun=False, reason=None):
    return SimpleNamespace(command=command, batch=batch, device="cpu", smoke=True, guarded=False, rerun=rerun,
                           reason=reason)


def _all(m):
    m.cmd_project(_args("project"))
    m.cmd_train(_args("train", "A"))
    m.cmd_train(_args("train", "B"))
    m.cmd_evaluate(_args("evaluate"))


def test_smoke_cleanup_touches_only_its_own_folder(tmp_path, monkeypatch):
    mod = _load()
    removed = []
    orig = Path.unlink

    def spy(self, missing_ok=False):
        removed.append(self)
        return orig(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", spy)
    for c, b in (("project", None), ("train", "A"), ("train", "B"), ("evaluate", None)):
        mod.use_smoke(SimpleNamespace(command=c, batch=b), folder=tmp_path)
    assert removed and all(tmp_path in p.parents for p in removed)


def test_the_stages_run_in_order_and_the_evaluation_applies_the_rules(m):
    _all(m)
    a = json.loads(m.train_path("A").read_text())
    assert a["outcome"] == "completed" and [r["spec"]["run"] for r in a["records"]] == [0, 1]
    assert all("champion" in r and "generation0_baseline" in r for r in a["records"])
    ev = json.loads((m.EXP / "evaluation.json").read_text())
    assert ev["outcome"].startswith("04a:") and set(ev["rules"]) == {"0", "1", "12", "13"}
    for r in ev["rules"].values():
        assert set(r) >= {"reliability", "baselines", "cue", "cue_helps", "generation0", "passed", "failed"}
    assert 0.0 <= ev["passing_share_lower_95"] <= ev["passing_share"]
    assert (m.EXP / "evaluation_events.npz").exists() and not (m.EXP / "evaluation_partial.npz").exists()
    extras = json.loads((m.EXP / "evaluation-extras.json").read_text())
    assert set(extras["replay"]) == {"0", "1", "12", "13"} and not extras["errors"]
    assert (m.OUT / "modules" / "run00-champion.npz").exists()


def test_every_smoke_id_is_outside_the_registered_ranges(m):
    _all(m)
    seen = np.concatenate([c[4].ravel() for c in m._fakes.calls])
    assert seen.max() < 10_000


def test_the_hold_out_uses_one_strain_on_all_its_worlds(m):
    m.cmd_project(_args("project"))
    m.cmd_train(_args("train", "A"))
    m.cmd_train(_args("train", "B"))
    m._fakes.calls.clear()
    m.cmd_evaluate(_args("evaluate"))
    hold = [c for c in m._fakes.calls if c[0] == "neural" and c[3] == (16,)]
    assert len(hold) == 4 * 4 and all(c[2] == 1 for c in hold)


def test_batch_a_needs_the_projection_within_its_limit(m):
    with pytest.raises(SystemExit, match="the projection has not run"):
        m.cmd_train(_args("train", "A"))
    m.cmd_project(_args("project"))
    p = json.loads((m.EXP / "projection.json").read_text())
    assert p["outcome"] == "completed" and p["within_limit"]
    p["within_limit"] = False
    (m.EXP / "projection.json").write_text(json.dumps(p))
    with pytest.raises(SystemExit, match="over its limit"):
        m.cmd_train(_args("train", "A"))
    assert not (m.EXP / "train-A-started.json").exists()


def test_the_projection_runs_once(m):
    m.cmd_project(_args("project"))
    with pytest.raises(SystemExit, match="runs once"):
        m.cmd_project(_args("project"))


def test_the_projection_verdict_counts_generations_and_checkpoints():
    mod = _load()
    assert mod.training_plan() == {"generations": 2000, "checkpoints": 82}  # derived from the registered evolution
    v = mod.projection_verdict([9.0, 4.0, 5.0, 4.0, 4.0, 7.0])
    assert v["median_seconds_per_generation"] == 4.0 and v["seconds_per_checkpoint"] == 3.0
    assert v["projected_training_hours"] == pytest.approx((2000 * 4 + 82 * 3) / 3600) and v["within_limit"]
    assert not mod.projection_verdict([9.0, 9.0, 9.0, 9.0])["within_limit"]
    mod.REGISTERED["evolution"]["generations"] = 500
    assert mod.training_plan() == {"generations": 1000, "checkpoints": 42}


def test_a_batch_runs_once(m):
    m.cmd_project(_args("project"))
    m.cmd_train(_args("train", "A"))
    with pytest.raises(SystemExit, match="runs once"):
        m.cmd_train(_args("train", "A"))


def test_batch_b_needs_a_completed_batch_a(m):
    with pytest.raises(SystemExit, match="batch A has not run"):
        m.cmd_train(_args("train", "B"))
    m.train_path("A").write_text(json.dumps({"outcome": "04a: not completed (the run stopped)"}))
    with pytest.raises(SystemExit, match="did not complete"):
        m.cmd_train(_args("train", "B"))


def test_the_evaluation_needs_both_batches(m):
    m.cmd_project(_args("project"))
    m.cmd_train(_args("train", "A"))
    with pytest.raises(SystemExit, match="batch B has not run"):
        m.cmd_evaluate(_args("evaluate"))


def _trained(m):
    m.cmd_project(_args("project"))
    m.cmd_train(_args("train", "A"))
    m.cmd_train(_args("train", "B"))


def test_the_evaluation_refuses_a_champion_that_does_not_match_its_hash(m):
    _trained(m)
    a = json.loads(m.train_path("A").read_text())
    a["records"][0]["champion"]["sha256"] = "0" * 64
    m.train_path("A").write_text(json.dumps(a))
    with pytest.raises(SystemExit, match="does not match its committed hash"):
        m.cmd_evaluate(_args("evaluate"))
    assert not (m.EXP / "evaluate-started.json").exists()  # refused before the hold-out is touched


def test_the_evaluation_refuses_a_baseline_missing_from_its_regenerated_population(m, monkeypatch):
    _trained(m)
    real = m.EV.initial_population
    monkeypatch.setattr(m.EV, "initial_population", lambda spec, b, seed, n, dev: real(spec, b, seed + 7, n, dev))
    with pytest.raises(SystemExit, match="regenerated initial population"):
        m.cmd_evaluate(_args("evaluate"))
    assert not (m.EXP / "evaluate-started.json").exists()


def test_the_evaluation_refuses_changed_e1_inputs(m, monkeypatch):
    _trained(m)
    monkeypatch.setattr(m, "e1_input_hashes", lambda: {"experiments/E1-navigation/freeze.json": "x"})
    with pytest.raises(SystemExit, match="E1's freeze or gate"):
        m.cmd_evaluate(_args("evaluate"))


def test_the_evaluation_runs_once(m):
    _all(m)
    with pytest.raises(SystemExit, match="used once"):
        m.cmd_evaluate(_args("evaluate"))


def test_a_cap_hit_in_training_is_not_completed_and_keeps_the_checkpoints(m, monkeypatch):
    m.cmd_project(_args("project"))
    calls = {"n": 0}

    def check(self):
        calls["n"] += 1
        if calls["n"] > 4:
            raise m.reg.CapReached("cap")

    monkeypatch.setattr(m.reg.CapClock, "check", check)
    with pytest.raises(SystemExit, match="not completed"):
        m.cmd_train(_args("train", "A"))
    a = json.loads(m.train_path("A").read_text())
    assert a["outcome"] == m.OUTCOMES["cap"] and a["records"][0]["checkpoints"]
    assert m.genomes_path(0).exists()
    with pytest.raises(SystemExit, match="only a stage stopped by a crash"):  # no rerun after the cap
        m.cmd_train(_args("train", "A", rerun=True, reason="x"))


def test_a_crash_before_the_first_checkpoint_is_not_completed(m):
    m.cmd_project(_args("project"))
    m._fakes.crash_at = len(m._fakes.calls) + 1
    with pytest.raises(RuntimeError, match="boom"):
        m.cmd_train(_args("train", "A"))
    a = json.loads(m.train_path("A").read_text())
    assert a["outcome"] == m.OUTCOMES["stopped"] and a["records"] == []


def _hashes(path):
    d = np.load(path, allow_pickle=False)
    return json.loads(str(d["meta"]))["genome_sha256s"]


def test_a_stopped_batch_is_rerun_once_with_the_attempt_and_its_genomes_kept(m):
    m.cmd_project(_args("project"))
    m._fakes.crash_at = len(m._fakes.calls) + 3  # after the first checkpoint
    with pytest.raises(RuntimeError):
        m.cmd_train(_args("train", "A"))
    before = _hashes(m.genomes_path(0))
    with pytest.raises(SystemExit, match="needs --reason"):
        m.cmd_train(_args("train", "A", rerun=True))
    m._fakes.crash_at = len(m._fakes.calls) + 3  # the rerun stops too
    with pytest.raises(RuntimeError):
        m.cmd_train(_args("train", "A", rerun=True, reason="test: a crash"))
    kept = json.loads((m.EXP / "train-A-attempt1.json").read_text())
    assert kept["outcome"] == m.OUTCOMES["stopped"] and (m.EXP / "train-A-started-attempt1.json").exists()
    assert _hashes(m.genomes_path(0).with_name("run00-candidates-attempt1.npz")) == before
    note = json.loads((m.EXP / "train-A-rerun.json").read_text())
    assert note["reason"] == "test: a crash" and note["how_the_first_attempt_ended"] == "stopped"
    with pytest.raises(SystemExit, match="rerun once already"):  # a second stop is not rerun
        m.cmd_train(_args("train", "A", rerun=True, reason="again"))


def _killed_batch_a(m, hours_ago=2.0, last_write_hours_ago=1.0):
    """What a hard kill of batch A leaves: a marker, a partial record, no result, no accounting."""
    import os
    import time
    m.cmd_project(_args("project"))
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - hours_ago * 3600))
    (m.EXP / "train-A-started.json").write_text(json.dumps({"stage": "train-A", "started_utc": started}))
    partial = m.EXP / "train-A-partial.json"
    partial.write_text("{}")
    t = time.time() - last_write_hours_ago * 3600
    for f in (partial, m.EXP / "train-A-started.json"):
        os.utime(f, (t, t))


def _spent(m):
    return json.loads((m.OUT / "compute.json").read_text())["totals"]["seconds_timed"]


def test_a_killed_attempts_time_is_charged_once_before_the_rerun(m):
    _killed_batch_a(m)
    m.cmd_train(_args("train", "A", rerun=True, reason="test: killed"))
    note = json.loads((m.EXP / "train-A-rerun.json").read_text())
    assert note["how_the_first_attempt_ended"].startswith("killed")
    charged = note["reconciled_compute"]["seconds"]
    assert charged == pytest.approx(3600 + 900, abs=5)  # start to the last write, plus the tail
    assert _spent(m) >= charged


def test_a_killed_attempt_that_exhausts_the_cap_is_not_rerun_and_keeps_its_rerun(m):
    _killed_batch_a(m, hours_ago=3.0, last_write_hours_ago=0.5)  # 2.5 h, plus the tail
    m.REGISTERED["cap_gpu_hours"] = 2.0
    with pytest.raises(SystemExit, match="did not start"):
        m.cmd_train(_args("train", "A", rerun=True, reason="test: killed"))
    assert (m.EXP / "train-A-started.json").exists() and not (m.EXP / "train-A-started-attempt1.json").exists()
    before = _spent(m)
    with pytest.raises(SystemExit, match="did not start"):  # retried: charged once, not twice
        m.cmd_train(_args("train", "A", rerun=True, reason="test: killed"))
    assert _spent(m) == before


def test_a_killed_stage_with_a_marker_and_no_record_can_be_rerun(m):
    m.cmd_project(_args("project"))
    m.reg.start_marker(m.EXP, "train-A", {"stage": "killed"})  # what a hard kill leaves
    with pytest.raises(SystemExit, match="started before"):
        m.cmd_train(_args("train", "A"))
    m.cmd_train(_args("train", "A", rerun=True, reason="test: killed"))
    assert json.loads(m.train_path("A").read_text())["outcome"] == "completed"
    note = json.loads((m.EXP / "train-A-rerun.json").read_text())
    assert note["how_the_first_attempt_ended"].startswith("killed")


def test_an_over_limit_projection_is_rerun_only_with_fewer_generations(m):
    m.cmd_project(_args("project"))
    with pytest.raises(SystemExit, match="only a stage stopped"):  # completed within its limit
        m.cmd_project(_args("project", rerun=True, reason="x"))
    p = json.loads((m.EXP / "projection.json").read_text())
    p["within_limit"] = False
    (m.EXP / "projection.json").write_text(json.dumps(p))
    with pytest.raises(SystemExit, match="reduces the generations"):  # unchanged: not rerun until it passes
        m.cmd_project(_args("project", rerun=True, reason="over the limit"))
    assert not (m.EXP / "projection-attempt1.json").exists()
    m.REGISTERED["evolution"]["generations"] -= 1  # the amendment
    m.cmd_project(_args("project", rerun=True, reason="test: over the limit, generations amended"))
    assert json.loads((m.EXP / "projection.json").read_text())["within_limit"]
    assert (m.EXP / "projection-attempt1.json").exists()


def test_a_stopped_projection_is_rerun_once(m):
    m._fakes.crash_at = 1
    with pytest.raises(RuntimeError):
        m.cmd_project(_args("project"))
    m._fakes.crash_at = None
    m.cmd_project(_args("project", rerun=True, reason="test: a crash"))
    assert json.loads((m.EXP / "projection.json").read_text())["outcome"] == "completed"
    assert json.loads((m.EXP / "projection-attempt1.json").read_text())["outcome"] == m.OUTCOMES["stopped"]


def test_a_stopped_evaluation_is_rerun_once(m):
    _trained(m)
    m._fakes.crash_at = len(m._fakes.calls) + 2
    with pytest.raises(RuntimeError):
        m.cmd_evaluate(_args("evaluate"))
    m._fakes.crash_at = None
    m.cmd_evaluate(_args("evaluate", rerun=True, reason="test: a crash"))
    assert json.loads((m.EXP / "evaluation.json").read_text())["outcome"].startswith("04a: ")
    assert json.loads((m.EXP / "evaluation-attempt1.json").read_text())["outcome"] == m.OUTCOMES["stopped"]
    assert json.loads((m.EXP / "evaluation-rerun.json").read_text())["reason"] == "test: a crash"


def test_a_failing_genome_save_still_leaves_a_stopped_record(m, monkeypatch):
    m.cmd_project(_args("project"))

    def broken(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(m, "save_genomes", broken)
    with pytest.raises(OSError, match="disk full"):
        m.cmd_train(_args("train", "A"))
    a = json.loads(m.train_path("A").read_text())
    assert a["outcome"] == m.OUTCOMES["stopped"] and "disk full" in a["genome_save_error"]


def test_a_cap_already_spent_does_not_start_a_stage(m, monkeypatch):
    monkeypatch.setattr(m.reg.CapClock, "check", lambda self: (_ for _ in ()).throw(m.reg.CapReached("spent")))
    with pytest.raises(SystemExit, match="did not start"):
        m.cmd_project(_args("project"))
    assert not (m.EXP / "project-started.json").exists()


def test_a_crash_in_the_evaluation_is_not_completed_and_keeps_the_arms(m):
    _trained(m)
    m._fakes.crash_at = len(m._fakes.calls) + 2
    with pytest.raises(RuntimeError, match="boom"):
        m.cmd_evaluate(_args("evaluate"))
    ev = json.loads((m.EXP / "evaluation.json").read_text())
    assert ev["outcome"] == m.OUTCOMES["stopped"] and ev["arms_completed"] == ["run00 champion"]


def test_the_cap_after_the_analysis_is_not_a_verdict(m, monkeypatch):
    _trained(m)
    real = m.analyse

    def analyse_then_cap(*a, **k):
        out = real(*a, **k)
        monkeypatch.setattr(m.reg.CapClock, "check", lambda self: (_ for _ in ()).throw(m.reg.CapReached("cap")))
        return out

    monkeypatch.setattr(m, "analyse", analyse_then_cap)
    with pytest.raises(SystemExit, match="not completed"):
        m.cmd_evaluate(_args("evaluate"))
    ev = json.loads((m.EXP / "evaluation.json").read_text())
    assert ev["outcome"] == m.OUTCOMES["cap"] and "rules" not in ev
    assert not (m.EXP / "evaluation-extras.json").exists()


def test_the_decoy_measure_failing_is_recorded_in_the_extras(m, monkeypatch):
    _trained(m)
    monkeypatch.setattr(m, "decoy_capture", lambda *a: (_ for _ in ()).throw(IndexError("no unfinished leg")))
    m.cmd_evaluate(_args("evaluate"))
    extras = json.loads((m.EXP / "evaluation-extras.json").read_text())
    assert "no unfinished leg" in extras["errors"]["decoy 0"] and extras["replay"]


def test_a_genome_file_that_loads_with_another_brain_configuration_is_refused(m):
    _trained(m)
    path = m.genomes_path(0)
    d = dict(np.load(path, allow_pickle=False))
    meta = json.loads(str(d["meta"]))
    meta["brain_config"]["pad_single_strain"] = not meta["brain_config"]["pad_single_strain"]
    d["meta"] = np.array(json.dumps(meta))
    np.savez_compressed(path, **d)  # every parameter, and so every hash, unchanged
    with pytest.raises(SystemExit, match="another brain configuration"):
        m.cmd_evaluate(_args("evaluate"))
    assert not (m.EXP / "evaluate-started.json").exists()


def test_a_stopped_projection_does_not_open_batch_a(m):
    (m.EXP / "projection.json").write_text(json.dumps({"outcome": m.OUTCOMES["stopped"], "within_limit": True}))
    with pytest.raises(SystemExit, match="did not complete"):
        m.cmd_train(_args("train", "A"))


def test_guarded_stages_compare_code_and_environment_with_the_earlier_stage(m, monkeypatch):
    m.cmd_project(_args("project"))
    seen = []
    monkeypatch.setattr(m.reg, "require_same_code", lambda commit, guarded: seen.append(("code", commit)))
    monkeypatch.setattr(m.reg, "require_same_env", lambda was, now: seen.append(("env", was["git_commit"])))
    args = SimpleNamespace(smoke=True, guarded=True)
    m.require_earlier(args, {"git_commit": "now"}, m.EXP / "projection.json", "the projection")
    commit = json.loads((m.EXP / "projection.json").read_text())["provenance_at_start"]["git_commit"]
    assert seen == [("code", commit), ("env", commit)]


def test_formal_seeds_are_disjoint_from_the_development_and_projection_seeds():
    mod = _load()
    formal = {r.run_seed for b in ("A", "B") for r in mod.run_specs(b)}
    pilot_and_v1 = set(range(1_104_000, 1_104_016))  # v1's formal seeds, used by the pilot and projection
    projection = {r.run_seed for r in mod.run_specs("A", mod.REGISTERED["projection"]["seed_base"])}
    smoke = {mod.SMOKE_SEED_BASE + i for i in range(16)}
    assert not formal & (pilot_and_v1 | projection | smoke)
    assert not projection & pilot_and_v1


def test_the_verdict_is_written_before_the_extras(m, monkeypatch):
    _trained(m)
    monkeypatch.setattr(m, "replay_check", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("replay broke")))
    m.cmd_evaluate(_args("evaluate"))
    ev = json.loads((m.EXP / "evaluation.json").read_text())
    assert ev["outcome"].startswith("04a:") and "rules" in ev
    extras = json.loads((m.EXP / "evaluation-extras.json").read_text())
    assert "replay broke" in extras["errors"]["replay 0"]


def test_task_n_must_equal_e1s_gate_configuration(m, tmp_path):
    gate = json.loads(m.E1_GATE.read_text(encoding="utf-8"))
    gate["resolved_config"]["world"]["target_sigma"] = 3.0
    fake = tmp_path / "gate.json"
    fake.write_text(json.dumps(gate))
    m.E1_GATE = fake
    with pytest.raises(SystemExit, match="differs from E1"):
        m.task_config()


def test_the_real_task_config_matches_e1():
    mod = _load()
    cfg = mod.task_config()
    assert cfg.world.target_sigma == 6.0 and cfg.world.max_ticks == 300
    assert cfg.evo.population == 32 and cfg.evo.worlds_per_strain == 8 and cfg.evo.generations == 1000


def test_e1s_inputs_are_guarded_files():
    mod = _load()
    assert set(mod.E1_INPUTS) <= set(mod.GUARDED)
    assert set(mod.e1_input_hashes()) == set(mod.E1_INPUTS)


def test_runs_are_seeded_by_run_number_and_the_arms_are_as_registered():
    mod = _load()
    a, b = mod.run_specs("A"), mod.run_specs("B")
    assert [r.run for r in a + b] == list(range(16))
    assert [r.run_seed for r in a + b] == [1_105_000 + i for i in range(16)]
    assert [r.shaping for r in a + b] == [0.5] * 12 + [0.0] * 4


def test_the_registered_id_ranges_are_disjoint_from_e1_each_other_and_the_smoke_exposure():
    mod = _load()
    from wormwars.e1.task import GATE_IDS, PILOT_IDS, TUNING_IDS
    hold, val, t = mod.holdout_ids(), mod.validation_ids(), mod.REGISTERED["train_ids"]
    assert hold[0] == 996_301_000 and len(hold) == 1024 and len(val) == 256
    for r in (PILOT_IDS, TUNING_IDS, GATE_IDS):
        assert hold.min() > r.max() or hold.max() < r.min()
        assert val.min() > r.max() and t["base"] > r.max()
    assert val.max() < t["base"] and hold.max() < val.min()
    exposed = json.loads((ROOT / "experiments" / "04a-navigation-primitive" / "development-records"
                          / "smoke-training-exposure.json").read_text())["distinct_ids"]
    assert all(not (t["base"] <= i < t["base"] + t["span"]) for i in exposed)


def test_the_gain_curve_takes_the_first_maximum_at_each_k():
    mod = _load()
    tuned = {"S-const": {"keys": ["k", "speed", "turn"], "grid": {"k": [1, 2], "speed": [0.5, 1.0], "turn": [0.0, 0.1]},
                         "means": [1, 3, 3, 2, 5, 4, 4, 5]}}
    c = mod.gain_curve_params(tuned)
    assert c[1.0] == {"k": 1.0, "speed": 0.5, "turn": 0.1}
    assert c[2.0] == {"k": 2.0, "speed": 0.5, "turn": 0.0}


def test_the_gain_curve_parameters_from_e1s_freeze_include_the_navigator():
    mod = _load()
    tuned = json.loads(mod.E1_FREEZE.read_text(encoding="utf-8"))["tuned"]
    c = mod.gain_curve_params(tuned)
    assert sorted(c) == [1, 2, 4, 8, 16, 32, 64, 256, 1024, 8192]
    assert c[8192.0] == tuned["S-const"]["params"]


def test_the_equivalent_k_interpolates_in_log_k():
    mod = _load()
    curve = {1.0: 1.0, 4.0: 3.0, 16.0: 5.0}
    assert mod.equivalent_k(2.0, curve) == pytest.approx(2.0)
    assert mod.equivalent_k(0.5, curve) == "< 1"
    assert mod.equivalent_k(6.0, curve) == "> 16"
    assert mod.equivalent_k(5.0, curve) == pytest.approx(16.0)
    assert mod.equivalent_k(5.5, {1.0: 1.0, 4.0: 6.0, 16.0: 5.0}) == pytest.approx(np.exp(np.log(4) * 0.9))
    assert mod.equivalent_k(5.0, {1.0: 1.0, 4.0: 6.0, 16.0: 2.0, 64.0: 4.0}) == pytest.approx(
        np.exp(np.log(1) + 0.8 * (np.log(4) - np.log(1))))
    assert mod.equivalent_k(5.5, {1.0: 6.0, 4.0: 2.0, 16.0: 5.0}) == "< 1"  # below the first point


def _counts(real, mirrored, gen0, constant=0.0, base=0.0, n=400):
    r = np.random.default_rng(0)
    c = {"run00 champion": np.clip(r.normal(real, 1, n), 0, None).round(),
         "run00 mirrored": np.clip(r.normal(mirrored, 1, n), 0, None).round(),
         "run00 constant": np.clip(r.normal(constant, 0.5, n), 0, None).round(),
         "run00 generation 0": np.clip(r.normal(gen0, 0.3, n), 0, None).round()}
    for b in ("constant", "random-walk", "wall-follower", "K"):
        c[b] = np.clip(r.normal(base, 0.3, n), 0, None).round()
    return c


def test_a_run_passes_only_with_every_rule():
    mod = _load()
    ok = mod.run_rules(_counts(6, 0.2, 0.1), 0)
    assert ok["passed"] and ok["failed"] == []
    no_cue = mod.run_rules(_counts(6, 5.5, 0.1), 0)
    assert not no_cue["passed"] and no_cue["failed"] == ["fails with the mirrored cue"]
    blind = mod.run_rules(_counts(3, 0.0, 0.1, constant=3.0), 0)  # Astra's case: mirror harms, real no better than blind
    assert blind["failed"] == ["beats its own constant probe"]
    weak = mod.run_rules(_counts(0.6, 0.0, 0.3), 0)
    assert "reliability" in weak["failed"] and "beats generation 0" in weak["failed"]


def test_the_outcome_counts_shaped_runs_only_and_the_share_bound_is_exact():
    mod = _load()
    per = {r: {"passed": r in (0, 1, 2, 3, 4, 12, 13, 14, 15)} for r in range(16)}
    assert mod.outcome_of(per) == "04a: some runs passed (5 of 12)"
    per[5]["passed"] = True
    assert mod.outcome_of(per) == "04a: passed"
    assert mod.outcome_of({r: {"passed": r >= 12} for r in range(16)}) == "04a: not passed"
    assert mod.share_lower_bound(6, 12) == pytest.approx(0.2453, abs=1e-3)
    assert mod.share_lower_bound(10, 12) > 0.5 > mod.share_lower_bound(9, 12)
    assert mod.share_lower_bound(0, 12) == 0.0


def test_the_decoy_capture_measures_the_unfinished_leg():
    mod = _load()
    ev = {k: v[:1] for k, v in _events(1, 2, np.array([[0, 1]])).items()}
    ev["final_head"] = np.array([[[18.0, 17.0], [5.0, 6.0]]])  # world 0 at the decoy (23-5, 23-6); world 1 at the target
    assert mod.decoy_capture(ev, 24)["share_closer_to_decoy"] == 0.5


def test_require_committed_refuses_untracked_and_modified_files(tmp_path):
    mod = _load()

    def g(*a):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)

    g("init", "-q")
    g("config", "user.email", "t@example.invalid")
    g("config", "user.name", "t")
    f = tmp_path / "train-A.json"
    f.write_text("{}\n")
    with pytest.raises(SystemExit, match="must be committed"):
        mod.require_committed(f, root=tmp_path)
    g("add", ".")
    g("commit", "-qm", "record")
    mod.require_committed(f, root=tmp_path)
    f.write_text('{"changed": 1}\n')
    with pytest.raises(SystemExit, match="must be committed"):
        mod.require_committed(f, root=tmp_path)
