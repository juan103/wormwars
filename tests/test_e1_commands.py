"""E1's stage commands end to end, with a fake rollout and ids outside E1's ranges (D097-D099).

Through `cmd_gate` and `cmd_pilot` themselves: the gate completed, the cap reached during the arms or
after the analysis, a crash in the arms or in the analysis, an interrupt, a stage that does not start
because the cap is spent, the once-only refusals, the committed-freeze check, and the pilot's refusal
to run over a freeze. As functions, in this file: the atomic checkpoint, the same-code check in a
real git repository, and the pin refusals. Both reviewers asked for tests through the commands, not
only their helpers."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


def _module(tmp_path):
    spec = importlib.util.spec_from_file_location("e1_cmd", ROOT / "scripts" / "e1.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.EXP = tmp_path
    m.FREEZE, m.GATE_RESULT = tmp_path / "freeze.json", tmp_path / "gate.json"
    m.GATE_EVENTS, m.GATE_PARTIAL = tmp_path / "gate_events.npz", tmp_path / "gate_partial.npz"
    m.OUT = tmp_path / "out"
    m.PILOT_IDS = m.TUNING_IDS = m.GATE_IDS = m.SMOKE_IDS  # never E1's worlds, even faked (Fable, D098)
    m.provenance = lambda: {"git_commit": "abc", "branch": "roadmap", "dirty": False}
    return m


def _freeze(m):
    R = m.REGISTERED
    n_legs = R["sigma_rule"]["pilot_worlds"] * R["sigma_rule"]["legs_per_world"]
    cov = [{"sigma": s, "share_above_floor": v, "leg_starts": n_legs}
           for s, v in zip(R["sigma_rule"]["candidates"], (0.0, 0.0, 0.3, 0.88))]
    tuned = {}
    for name in (*m.CONTROLS, "S-const k<=32"):
        base = "S-const" if name == "S-const k<=32" else name
        grid = m.grid_for(base, 0.3, R["tuning"]["s_small_gain_max_k"] if name == "S-const k<=32" else None)
        keys, combos = m.combos_of(grid)
        means = [float((i * 7) % 11) / 10 for i in range(len(combos))]
        i = int(np.argmax(means))
        tuned[name] = {"keys": keys, "grid": grid, "means": means, "winner_index": i,
                       "params": dict(zip(keys, [float(x) for x in combos[i]])), "tuned_mean": means[i]}
    tuned["oracle"] = {"params": dict(R["oracle"]), "tuned_mean": 5.0}
    doc = {"registered": R, "coverage": cov, "sigma": 6.0, "sigma_flagged": True,
           "own_body": {"own_body_max_current": 0.3, "samples": 100}, "tuned": tuned,
           "navigator": m.navigator_of(tuned), "provenance_at_start": {"git_commit": "abc"}}
    m.write_json(m.FREEZE, json.loads(json.dumps(doc)))


class FakeRollout:
    """Counts of 3 on every world, and a full event table; optionally raises on the n-th call."""

    def __init__(self, fail_on=None):
        self.calls, self.fail_on = 0, fail_on

    def __call__(self, cfg, iface, brain, ids, seed, device):
        self.calls += 1
        if self.fail_on == self.calls:
            raise RuntimeError("injected failure")
        n = len(ids)
        z = np.zeros((1, n, 3))
        ev = {"activation_tick": np.tile([0, 11, 21], (1, n, 1)), "reach_tick": np.tile([10, 20, -1], (1, n, 1)),
              "path_length": z + 5.0, "target_x": z + 5.0, "target_y": z + 5.0, "start_x": z + 1.0,
              "start_y": z + 1.0, "end_x": z + 4.0, "end_y": z + 5.0}
        return types.SimpleNamespace(score=np.full((1, n), 3.0, dtype=np.float32), events=ev)


def _args(smoke=True):
    return argparse.Namespace(device="cpu", smoke=smoke, guarded=False)


def _read(m):
    return json.loads(m.GATE_RESULT.read_text(encoding="utf-8"))


def test_a_completed_gate_writes_the_outcome_then_the_events(tmp_path, monkeypatch):
    m = _module(tmp_path)
    _freeze(m)
    monkeypatch.setattr(m, "rollout_brain", FakeRollout())
    m.cmd_gate(_args())
    doc = _read(m)
    assert doc["outcome"].startswith("E1 positive control: ") and "not completed" not in doc["outcome"]
    assert m.GATE_EVENTS.exists() and not m.GATE_PARTIAL.exists()
    assert (tmp_path / "gate-started.json").exists()


def test_a_crash_keeps_every_completed_arm(tmp_path, monkeypatch):
    m = _module(tmp_path)
    _freeze(m)
    monkeypatch.setattr(m, "rollout_brain", FakeRollout(fail_on=3))
    with pytest.raises(RuntimeError):
        m.cmd_gate(_args())
    doc = _read(m)
    assert doc["outcome"] == "E1 positive control: not completed (the run stopped)"
    assert doc["arms_completed"] == ["navigator", "navigator mirrored"]
    assert len(doc["per_world_counts"]["navigator"]) == m.REGISTERED["gate"]["worlds"]
    with np.load(m.GATE_EVENTS, allow_pickle=False) as z:
        assert "navigator mirrored|reach_tick" in z.files
    with np.load(m.GATE_PARTIAL, allow_pickle=False) as z:  # the per-arm checkpoint survives too
        assert "navigator|count" in z.files


def test_the_cap_reached_during_the_arms_keeps_the_completed_ones(tmp_path, monkeypatch):
    m = _module(tmp_path)
    _freeze(m)
    monkeypatch.setattr(m, "rollout_brain", FakeRollout())
    calls = {"n": 0}

    def cap():
        calls["n"] += 1
        if calls["n"] == 4:  # the start check, then arms 1 and 2 pass; arm 3 does not start
            raise m.CapReached("cap")
    monkeypatch.setattr(m, "check_cap", lambda *a: cap())
    with pytest.raises(SystemExit):
        m.cmd_gate(_args())
    doc = _read(m)
    assert doc["outcome"] == "E1 positive control: not completed (the registered cap was reached)"
    assert doc["arms_completed"] == ["navigator", "navigator mirrored"]


def test_the_cap_reached_during_the_analysis_is_not_a_pass(tmp_path, monkeypatch):
    """Astra's mocked clock (D096): crossing the cap after the arms must not end as "passed"."""
    m = _module(tmp_path)
    _freeze(m)
    monkeypatch.setattr(m, "rollout_brain", FakeRollout())
    state = {"analysed": False}
    real_rules = m.gate_rules

    def rules(counts):
        state["analysed"] = True
        return real_rules(counts)

    def cap(*a):
        if state["analysed"]:
            raise m.CapReached("cap")
    monkeypatch.setattr(m, "gate_rules", rules)
    monkeypatch.setattr(m, "check_cap", cap)
    with pytest.raises(SystemExit):
        m.cmd_gate(_args())
    doc = _read(m)
    assert doc["outcome"] == "E1 positive control: not completed (the registered cap was reached)"
    assert "navigator" in doc["per_world_counts"]
    assert "rules" not in doc and "failed_rules" not in doc  # never a rule's result (Fable, D099)


def test_a_gate_with_a_result_or_a_marker_does_not_run_again(tmp_path, monkeypatch):
    m = _module(tmp_path)
    _freeze(m)
    fake = FakeRollout()
    monkeypatch.setattr(m, "rollout_brain", fake)
    (tmp_path / "gate-started.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        m.cmd_gate(_args())
    assert fake.calls == 0
    (tmp_path / "gate-started.json").unlink()
    m.GATE_RESULT.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        m.cmd_gate(_args())
    assert fake.calls == 0


def test_the_formal_gate_needs_a_committed_freeze(tmp_path, monkeypatch):
    m = _module(tmp_path)
    _freeze(m)
    fake = FakeRollout()
    monkeypatch.setattr(m, "rollout_brain", fake)
    monkeypatch.setattr(m, "require_formal", lambda *a: None)
    monkeypatch.setattr(m.subprocess, "run", lambda cmd, *a, **k: subprocess.CompletedProcess(cmd, 1))
    with pytest.raises(SystemExit):
        m.cmd_gate(_args(smoke=False))
    assert fake.calls == 0 and not (tmp_path / "gate-started.json").exists()


def test_the_pilot_does_not_run_over_a_freeze(tmp_path):
    m = _module(tmp_path)
    _freeze(m)
    with pytest.raises(SystemExit):
        m.cmd_pilot(_args())
    assert not (tmp_path / "pilot-started.json").exists()


def test_the_pins_are_read_from_requirements_and_enforced(tmp_path):
    m = _module(tmp_path)
    pins = m.pinned()
    assert pins["python"] == "3.13" and pins["torch"].startswith("2.12.0") and "numpy" in pins
    good = {"python": "3.13.3", "torch": pins["torch"], "numpy": pins["numpy"]}
    m.require_pins(good)
    for k, v in (("python", "3.12.1"), ("torch", "2.11.0"), ("numpy", "1.0.0")):
        with pytest.raises(SystemExit):
            m.require_pins({**good, k: v})



def test_a_crash_in_the_analysis_is_not_completed_and_keeps_the_arms(tmp_path, monkeypatch):
    """Astra's injection (D098): an error in gate_rules after every arm has run."""
    m = _module(tmp_path)
    _freeze(m)
    monkeypatch.setattr(m, "rollout_brain", FakeRollout())

    def boom(counts):
        raise RuntimeError("analysis failed")
    monkeypatch.setattr(m, "gate_rules", boom)
    with pytest.raises(RuntimeError):
        m.cmd_gate(_args())
    doc = _read(m)
    assert doc["outcome"] == "E1 positive control: not completed (the run stopped)"
    assert "rules" not in doc and "navigator" in doc["per_world_counts"]


def test_an_interrupt_is_not_completed_and_keeps_the_arms(tmp_path, monkeypatch):
    m = _module(tmp_path)
    _freeze(m)
    fake = FakeRollout()

    def interrupting(*a):
        if fake.calls == 2:
            raise KeyboardInterrupt
        return fake(*a)
    monkeypatch.setattr(m, "rollout_brain", interrupting)
    with pytest.raises(KeyboardInterrupt):
        m.cmd_gate(_args())
    doc = _read(m)
    assert doc["outcome"] == "E1 positive control: not completed (the run stopped)"
    assert doc["arms_completed"] == ["navigator", "navigator mirrored"]


@pytest.mark.parametrize("stage", ["pilot", "gate"])
def test_a_cap_spent_before_a_stage_starts_spends_nothing(tmp_path, monkeypatch, stage):
    m = _module(tmp_path)
    if stage == "gate":
        _freeze(m)
    fake = FakeRollout()
    monkeypatch.setattr(m, "rollout_brain", fake)

    def spent(*a):
        raise m.CapReached("cap")
    monkeypatch.setattr(m, "check_cap", spent)
    with pytest.raises(SystemExit, match="did not start"):
        (m.cmd_gate if stage == "gate" else m.cmd_pilot)(_args())
    assert fake.calls == 0 and not (tmp_path / f"{stage}-started.json").exists()


def test_a_failed_checkpoint_write_leaves_the_previous_checkpoint(tmp_path, monkeypatch):
    m = _module(tmp_path)
    ids = np.array([1, 2])
    m.checkpoint({"a": np.array([3.0, 4.0])}, {}, ids)

    def dies(path, *a, **k):  # a kill mid-write: a truncated file where it was writing, then death
        Path(path).write_bytes(b"PK truncated")
        raise OSError("killed during the write")
    monkeypatch.setattr(m.np, "savez_compressed", dies)
    with pytest.raises(OSError):
        m.checkpoint({"a": np.array([3.0, 4.0]), "b": np.array([5.0, 6.0])}, {}, ids)
    with np.load(m.GATE_PARTIAL, allow_pickle=False) as z:
        assert list(z["a|count"]) == [3.0, 4.0] and "b|count" not in z.files


def _git(repo, *a):
    return subprocess.check_output(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", *a],
                                   cwd=repo, text=True).strip()


def test_the_same_code_check_accepts_output_only_commits_and_refuses_code(tmp_path):
    """A real repository (Astra, D098): a commit changing only the freeze passes; one changing a
    guarded file does not."""
    repo = tmp_path / "repo"
    (repo / "wormwars").mkdir(parents=True)
    (repo / "experiments" / "E1-navigation").mkdir(parents=True)
    (repo / "wormwars" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (repo / "experiments" / "E1-navigation" / "PREREGISTRATION.md").write_text("v1\n", encoding="utf-8")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "pilot")
    pilot = _git(repo, "rev-parse", "HEAD")
    (repo / "experiments" / "E1-navigation" / "freeze.json").write_text("{}\n", encoding="utf-8")
    (repo / "experiments" / "E1-navigation" / "pilot-started.json").write_text("{}\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "freeze")
    m = _module(tmp_path / "exp")
    m.ROOT = repo
    freeze = {"provenance_at_start": {"git_commit": pilot}}
    m.require_same_code_as_pilot(freeze)  # outputs only: accepted
    (repo / "wormwars" / "a.py").write_text("x = 2\n", encoding="utf-8")
    _git(repo, "commit", "-q", "-am", "code")
    with pytest.raises(SystemExit):
        m.require_same_code_as_pilot(freeze)
