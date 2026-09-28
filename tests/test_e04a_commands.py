"""04a's runner (`scripts/e04a.py`) through its stage commands, with fake rollouts, smoke sizes and a
scratch folder: the order of stages, the once-only refusals, the committed-hash check, not-completed
records, and the registered rules as functions."""

from __future__ import annotations

import importlib.util
import json
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
    """count = 3 for a genome whose mean bias is positive, else 0; the mirrored probe halves nothing
    (count 0); scripted arms reach 0 except the oracle (4). Deterministic in the genome."""

    def __init__(self, crash_on=None):
        self.crash_on, self.calls = crash_on, []

    def rollout(self, cfg, iface, genome, ids, world_seed, device, chunk_worlds=None, **kw):
        ids = np.asarray(ids)
        n_w = ids.shape[-1]
        self.calls.append(("neural", cfg.world.food_probe, genome.n_strains, ids.shape))
        if self.crash_on and self.crash_on == (cfg.world.food_probe, len(self.calls)):
            raise RuntimeError("boom")
        good = (genome.bias.mean(dim=1).cpu().numpy() > 0).astype(np.float32)
        count = np.repeat(good[:, None], n_w, axis=1) * (0.0 if cfg.world.food_probe == "mirrored" else 3.0)
        return SimpleNamespace(score=count, progress=np.full(count.shape, 0.5, np.float32),
                               events=_events(genome.n_strains, n_w, count),
                               final_head=np.full((genome.n_strains, n_w, 2), 3.0, np.float32))

    def rollout_brain(self, cfg, iface, brain, ids, world_seed, device, ticks=None):
        n_w = len(ids)
        v = 4.0 if type(brain).__name__ == "OracleBrain" else 0.0
        count = np.full((1, n_w), v, np.float32)
        return SimpleNamespace(score=count, events=_events(1, n_w, count),
                               final_head=np.full((1, n_w, 2), 3.0, np.float32))


@pytest.fixture
def m(tmp_path, monkeypatch):
    mod = _load()
    mod.use_smoke(SimpleNamespace(command="train", batch="A"))
    mod.EXP = mod.OUT = tmp_path
    fakes = Fakes()
    monkeypatch.setattr(mod.rollout_mod, "rollout", fakes.rollout)
    monkeypatch.setattr(mod, "rollout_brain", fakes.rollout_brain)
    mod._fakes = fakes
    return mod


def _args(command, batch=None):
    return SimpleNamespace(command=command, batch=batch, device="cpu", smoke=True, guarded=False)


def _train_both(m):
    m.cmd_train(_args("train", "A"))
    m.cmd_train(_args("train", "B"))


def test_the_stages_run_in_order_and_the_evaluation_applies_the_rules(m):
    _train_both(m)
    a = json.loads(m.train_path("A").read_text())
    assert a["outcome"] == "completed" and [r["spec"]["run"] for r in a["records"]] == [0, 1]
    assert all("champion" in r and "generation0_baseline" in r for r in a["records"])
    m.cmd_evaluate(_args("evaluate"))
    ev = json.loads((m.EXP / "evaluation.json").read_text())
    assert ev["outcome"].startswith("04a:")
    assert set(ev["rules"]) == {"0", "1", "12", "13"}
    assert (m.EXP / "evaluation_events.npz").exists() and not (m.EXP / "evaluation_partial.npz").exists()
    assert (m.EXP / "modules" / "run00-champion.npz").exists()
    for r in ev["rules"].values():
        assert set(r) >= {"reliability", "baselines", "cue", "generation0", "passed", "failed"}


def test_the_hold_out_uses_one_strain_on_all_its_worlds(m):
    _train_both(m)
    m._fakes.calls.clear()
    m.cmd_evaluate(_args("evaluate"))
    neural = [c for c in m._fakes.calls if c[0] == "neural" and c[3] == (16,)]
    assert neural and all(c[2] == 1 for c in neural)
    assert len(neural) == 4 * 4  # champion, mirrored, constant, generation 0 for each of 4 runs


def test_a_batch_runs_once(m):
    m.cmd_train(_args("train", "A"))
    with pytest.raises(SystemExit, match="runs once"):
        m.cmd_train(_args("train", "A"))


def test_batch_b_needs_a_completed_batch_a(m):
    with pytest.raises(SystemExit, match="after batch A"):
        m.cmd_train(_args("train", "B"))
    m.train_path("A").write_text(json.dumps({"outcome": "04a: not completed (the run stopped)"}))
    with pytest.raises(SystemExit, match="did not complete"):
        m.cmd_train(_args("train", "B"))


def test_the_evaluation_needs_both_batches(m):
    m.cmd_train(_args("train", "A"))
    with pytest.raises(SystemExit, match="batch B has not run"):
        m.cmd_evaluate(_args("evaluate"))


def test_the_evaluation_refuses_a_champion_that_does_not_match_its_hash(m):
    _train_both(m)
    a = json.loads(m.train_path("A").read_text())
    a["records"][0]["champion"]["sha256"] = "0" * 64
    m.train_path("A").write_text(json.dumps(a))
    with pytest.raises(SystemExit, match="does not match its committed hash"):
        m.cmd_evaluate(_args("evaluate"))
    assert not (m.EXP / "evaluate-started.json").exists()  # refused before the hold-out is touched


def test_the_evaluation_runs_once(m):
    _train_both(m)
    m.cmd_evaluate(_args("evaluate"))
    with pytest.raises(SystemExit, match="used once"):
        m.cmd_evaluate(_args("evaluate"))


def test_a_cap_hit_in_training_is_not_completed_and_keeps_the_checkpoints(m, monkeypatch):
    calls = {"n": 0}

    def check(self):
        calls["n"] += 1
        if calls["n"] > 4:
            raise m.reg.CapReached("cap")

    monkeypatch.setattr(m.reg.CapClock, "check", check)
    with pytest.raises(SystemExit, match="not completed"):
        m.cmd_train(_args("train", "A"))
    a = json.loads(m.train_path("A").read_text())
    assert a["outcome"] == m.OUTCOMES["cap"]
    assert a["records"] and a["records"][0]["checkpoints"]
    assert m.genomes_path(0).exists()


def test_a_cap_already_spent_does_not_start_a_stage(m, monkeypatch):
    monkeypatch.setattr(m.reg.CapClock, "check", lambda self: (_ for _ in ()).throw(m.reg.CapReached("spent")))
    with pytest.raises(SystemExit, match="did not start"):
        m.cmd_train(_args("train", "A"))
    assert not (m.EXP / "train-A-started.json").exists()


def test_a_crash_in_the_evaluation_is_not_completed_and_keeps_the_arms(m):
    _train_both(m)
    m._fakes.crash_on = ("mirrored", len(m._fakes.calls) + 2)
    with pytest.raises(RuntimeError, match="boom"):
        m.cmd_evaluate(_args("evaluate"))
    ev = json.loads((m.EXP / "evaluation.json").read_text())
    assert ev["outcome"] == m.OUTCOMES["stopped"] and ev["arms_completed"] == ["run00 champion"]


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


def test_runs_are_seeded_by_run_number_and_the_arms_are_as_registered():
    mod = _load()
    a, b = mod.run_specs("A"), mod.run_specs("B")
    assert [r.run for r in a + b] == list(range(16))
    assert [r.run_seed for r in a + b] == [1_104_000 + i for i in range(16)]
    assert [r.shaping for r in a + b] == [0.5] * 12 + [0.0] * 4


def test_the_registered_id_ranges_are_disjoint_from_e1_and_each_other():
    mod = _load()
    from wormwars.e1.task import GATE_IDS, PILOT_IDS, TUNING_IDS
    hold = mod.holdout_ids()
    val = mod.validation_ids()
    t = mod.REGISTERED["train_ids"]
    assert hold[0] == 996_301_000 and len(hold) == 1024
    for r in (PILOT_IDS, TUNING_IDS, GATE_IDS):
        assert not set(hold) & set(r[[0, -1]]) and (hold.min() > r.max() or hold.max() < r.min())
        assert val.min() > r.max() and t["base"] > r.max()
    assert t["base"] + t["span"] <= val.min()


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


def _counts(real, mirrored, gen0, base=0.0, n=400):
    r = np.random.default_rng(0)
    c = {"run00 champion": np.clip(r.normal(real, 1, n), 0, None).round(),
         "run00 mirrored": np.clip(r.normal(mirrored, 1, n), 0, None).round(),
         "run00 generation 0": np.clip(r.normal(gen0, 0.3, n), 0, None).round()}
    for b in ("constant", "random-walk", "wall-follower", "K"):
        c[b] = np.clip(r.normal(base, 0.3, n), 0, None).round()
    return c


def test_a_run_passes_only_with_all_four_rules():
    mod = _load()
    ok = mod.run_rules(_counts(6, 0.2, 0.1), 0)
    assert ok["passed"] and ok["failed"] == []
    no_cue = mod.run_rules(_counts(6, 5.5, 0.1), 0)
    assert not no_cue["passed"] and no_cue["failed"] == ["uses the cue"]
    weak = mod.run_rules(_counts(0.6, 0.0, 0.3), 0)
    assert "reliability" in weak["failed"] and "beats generation 0" in weak["failed"]


def test_the_outcome_counts_shaped_runs_only():
    mod = _load()
    per = {r: {"passed": r in (0, 1, 2, 3, 4, 12, 13, 14, 15)} for r in range(16)}
    assert mod.outcome_of(per) == "04a: some runs passed (5 of 12)"
    per[5]["passed"] = True
    assert mod.outcome_of(per) == "04a: passed"
    assert mod.outcome_of({r: {"passed": r >= 12} for r in range(16)}) == "04a: not passed"


def test_the_decoy_capture_measures_the_unfinished_leg():
    mod = _load()
    ev = {k: v[:1] for k, v in _events(1, 2, np.array([[0, 1]])).items()}
    ev["final_head"] = np.array([[[18.0, 17.0], [5.0, 6.0]]])  # world 0 at the decoy (23-5, 23-6); world 1 at the target
    out = mod.decoy_capture(ev, 24)
    assert out["share_closer_to_decoy"] == 0.5
