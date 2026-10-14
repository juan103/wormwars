"""The evolutionary E4-D's formal stages (`scripts/e4d_evo_formal.py`) against the bound pre-registration's §10: the
dependencies and refusals, integrity failures never rerun, the replay comparison and the timing refusal (with
sabotages), the cue conditions at a multi-strain composition, S₀, and the pinned files."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from wormwars.brain import Genome
from wormwars.connectome import load_connectome
from wormwars.e4 import arms as AR
from wormwars.e4 import evo_formal as FM
from wormwars.e4 import evo_stats as ES
from wormwars.e4 import evo_trial as ET
from wormwars.e4 import trial as TL
from wormwars.e4s import arms as A

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def S(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("e4d_evo_formal_under_test", ROOT / "scripts" / "e4d_evo_formal.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    monkeypatch.setattr(m, "EXP", tmp_path / "records")
    monkeypatch.setattr(m, "SMOKE", True)
    monkeypatch.setattr(m, "SMOKE_ROOT", tmp_path / "out")
    m.configure("train-l")
    return m


def _write(S, stage, doc):
    p = S.E.record_path(stage)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"outcome": "completed", "registered": S.REGISTERED,
                             "provenance_at_start": {"git_commit": "x"}, **doc}), encoding="utf-8")


def test_a_stage_refuses_without_its_predecessors(S):
    with pytest.raises(SystemExit, match="check has not completed"):
        S.requires("train-l")(None, {})
    _write(S, "check", {"timing": {"within_cap": True}})
    assert "check" in S.requires("train-l")(None, {})
    with pytest.raises(SystemExit, match="train-l has not completed"):
        S.requires("evaluate-l")(None, {})


def test_a_stopped_predecessor_does_not_count(S):
    _write(S, "check", {"timing": {"within_cap": True}})
    S.E.record_path("check").write_text(json.dumps({"outcome": "E4-D evo formal: not completed (the run stopped)"}),
                                        encoding="utf-8")
    with pytest.raises(SystemExit):
        S.requires("train-l")(None, {})


def test_train_l_refuses_on_the_timing_projection(S):
    _write(S, "check", {"timing": {"within_cap": False}})
    with pytest.raises(SystemExit, match="timing projection"):
        S.requires("train-l")(None, {})


@pytest.mark.parametrize("state, ok", [(ES.STATES[0], False), (ES.STATES[1], False), (ES.STATES[2], False),
                                       (ES.STATES[3], True), (ES.STATES[4], True)])
def test_s_needs_a_triggering_l_and_not_f(S, state, ok):
    _write(S, "check", {"timing": {"within_cap": True}})
    _write(S, "report-l", {"reading": {"state": state}})
    if ok:
        got = S.requires("train-s")(None, {})
        assert set(got) == {"report-l"}  # nothing of F's is required
    else:
        with pytest.raises(SystemExit, match="not triggered"):
            S.requires("train-s")(None, {})


def test_f_failing_does_not_block_s(S):
    _write(S, "check", {"timing": {"within_cap": True}})
    _write(S, "report-l", {"reading": {"state": ES.STATES[3]}})
    S.E.record_path("train-f").write_text(json.dumps({"outcome": S.E.OUTCOMES["integrity"]}), encoding="utf-8")
    assert "report-l" in S.requires("train-s")(None, {})


def test_a_changed_environment_is_refused(S, monkeypatch):
    monkeypatch.setattr(S, "SMOKE", False)
    monkeypatch.setattr(S, "check_pinned", lambda: None)
    monkeypatch.setattr(S.reg, "require_same_code", lambda *a, **k: None)
    _write(S, "check", {"timing": {"within_cap": True}, "provenance_at_start": {"git_commit": "x", "torch": "2.12.0"}})
    S.requires("train-l")(None, {"torch": "2.12.0"})
    with pytest.raises(SystemExit, match="environment"):
        S.requires("train-l")(None, {"torch": "2.13.0"})


def test_a_changed_registration_is_refused(S, monkeypatch):
    monkeypatch.setattr(S, "SMOKE", False)
    monkeypatch.setattr(S, "check_pinned", lambda: None)
    monkeypatch.setattr(S.reg, "require_same_code", lambda *a, **k: None)
    monkeypatch.setattr(S.reg, "require_same_env", lambda *a, **k: None)
    _write(S, "check", {"timing": {"within_cap": True}})
    S.REGISTERED["G"] = 101
    with pytest.raises(SystemExit, match="registration differs"):
        S.requires("train-l")(None, {})


def test_an_integrity_failure_is_not_evaluable_and_never_rerun(S, tmp_path):
    path = S.E.record_path("train-l")
    path.parent.mkdir(parents=True, exist_ok=True)
    ctx = SimpleNamespace(salvage=lambda: {}, after_fail=lambda: None)
    for err in ("IntegrityError: run 3 unbalanced", "FloatingPointError: generation 4: non-finite",
                "RuntimeError: integrity: link-free strains [1] distinguish the assignments"):
        doc = {}
        S.E._not_completed(path, doc, ctx, "stopped", err, 0.0)
        rec = json.loads(path.read_text(encoding="utf-8"))
        assert rec["outcome"] == S.E.OUTCOMES["integrity"] and rec["final"] is True
        marker = S.E.marker_path("train-l")
        marker.write_text(json.dumps({"stage": "train-l", "attempt": 1, "started_utc": "2026-10-14T00:00:00Z"}),
                          encoding="utf-8")
        with pytest.raises(SystemExit, match="only a stage stopped"):
            S.E.rerun_plan("train-l", [path, marker], "infrastructure: the driver")
    S.E._not_completed(path, {}, ctx, "stopped", "RuntimeError: CUDA error: an illegal memory access", 0.0)
    assert json.loads(path.read_text(encoding="utf-8"))["outcome"] == S.E.OUTCOMES["stopped"]


def test_the_owner_word_is_required_before_check_and_s(S, monkeypatch):
    monkeypatch.setattr(S, "SMOKE", False)
    for stage in ("check", "train-s"):
        with pytest.raises(SystemExit, match="owner-word"):
            S.owner_word(SimpleNamespace(owner_word=None), stage)
        assert S.owner_word(SimpleNamespace(owner_word=" yes, 2026-10-14 "), stage) == "yes, 2026-10-14"
    assert S.owner_word(SimpleNamespace(owner_word=None), "train-l") is None


def _screen(S, sha="c"):
    return {"L_logs": {str(r["run"]): {"checkpoints": [{"generation": 0, "sha256": "g0"},
                                                        {"generation": 10, "sha256": f"{sha}{r['run']}"}]}
                       for r in S.PILOT_RUNS}}


def test_the_replay_comparison_and_its_sabotages(S, monkeypatch):
    runs = [r["run"] for r in S.PILOT_RUNS]
    local = {r: [f"s{r}-{i}" for i in range(32)] for r in runs}
    digest = S.population_digest([S.population_digest(local[r]) for r in runs])
    monkeypatch.setitem(S.REGISTERED["replay"], "pilot_digest", digest)
    cks = {r: f"c{r}" for r in runs}
    out = S.compare_replay({r: list(v) for r, v in local.items()}, cks, _screen(S), local)
    assert out["populations"].startswith("equal")
    assert S.compare_replay(local, cks, _screen(S), None)["populations"] == "not compared"
    bad = {r: list(v) for r, v in local.items()}
    bad[runs[5]][7] = "perturbed"
    with pytest.raises(FM.IntegrityError, match="population differs"):
        S.compare_replay(bad, cks, _screen(S), local)
    with pytest.raises(FM.IntegrityError, match="checkpoint differs"):  # the wrong snapshot's hashes
        S.compare_replay(local, {r: "g0" for r in runs}, _screen(S), local)
    monkeypatch.setitem(S.REGISTERED["replay"], "pilot_digest", "0" * 64)
    with pytest.raises(FM.IntegrityError, match="registered digest"):
        S.compare_replay(local, cks, _screen(S), local)


def test_the_registered_digest_is_the_local_populations(S):
    loc = S.local_gen010()
    if loc is None:
        pytest.skip("the pilot's local populations are not on this machine")
    runs = [r["run"] for r in S.PILOT_RUNS]
    assert S.population_digest([S.population_digest(loc[r]) for r in runs]) == S.PILOT_DIGEST


def test_the_timing_refusal(S):
    S.REGISTERED["G"] = 100
    assert S.timing_ok(60.0, 0.5, 8.0)["within_cap"]  # 2 h against 6 h
    assert not S.timing_ok(300.0, 0.5, 8.0)["within_cap"]  # 10 h, inflated


def test_the_pinned_files_hash_as_registered(S, monkeypatch):
    monkeypatch.setattr(S, "SMOKE", False)
    S.check_pinned()
    monkeypatch.setitem(S.PINNED, "docs/E4/E4-D-DESIGN.md", "0" * 64)
    with pytest.raises(SystemExit, match="does not hash"):
        S.check_pinned()


@pytest.fixture(scope="module")
def trial():
    cfg = TL.trial_config(sigma=6.0, horizon=300)
    cx = AR.context(load_connectome(), A.load_l1(), cfg.brain)
    return cfg, cx


def test_s0_is_the_seeded_wiring(trial, S):
    _, cx = trial
    eg = cx["org"].genome.select([0])
    s0 = S.s0_of(cx)
    want = TL.control_genome(eg, cx, "comparator", 0.5)
    assert all(torch.equal(getattr(s0, k), getattr(want, k)) for k in ("w", "bias", "tau", "g"))
    diff = torch.nonzero(s0.w[0] != eg.w[0]).flatten()
    slots = AR.slot_indices(cx)
    assert len(diff) == 2 and set(diff.tolist()) <= set(slots.tolist())
    assert all(torch.equal(getattr(s0, k), getattr(eg, k)) for k in ("bias", "tau", "g"))


def test_reversal_swaps_the_counts_exactly_per_maze(trial):
    """A reversed trial (maze, assignment a) gives A the inputs of the intact trial (maze, 1 − a), and B the same sum;
    so real-first under reversal is decoy-first intact on the other assignment, per maze, at a multi-strain batch."""
    cfg, cx = trial
    org = cx["org"]
    eg = org.genome.select([0])
    batch = Genome.cat([TL.control_genome(eg, cx, "comparator", 3.0), eg, TL.control_genome(eg, cx, "comparator", 1.0)])
    ids = np.array([54_000, 54_001, 54_002])
    a = ET.trial_rollout(cx)(cfg, org.iface, batch, ids, FM.MAZE_SEED, "cpu")
    b = ET.trial_rollout(cx, a_source="decoy")(cfg, org.iface, batch, ids, FM.MAZE_SEED, "cpu")
    assert np.array_equal(b.real_first_maze, a.decoy_first_maze[:, :, ::-1])
    assert np.array_equal(b.decoy_first_maze, a.real_first_maze[:, :, ::-1])


def test_the_evaluation_path_asserts_balance(trial, S):
    cfg, cx = trial
    eg = cx["org"].genome.select([0])
    ctl = TL.control_genome(eg, cx, "comparator", 3.0)
    ctx = SimpleNamespace(cap=SimpleNamespace(check=lambda: None), args=SimpleNamespace(device="cpu"))
    out = S.evaluate_conditions(ctx, cx, cfg, ctl, np.array([54_000, 54_001]), arm="L")
    assert set(out) == {"intact", "reversed", "removed", "fixed", "cut", "eg"}
    for c in ("removed", "fixed", "cut", "eg"):
        assert out[c]["real_first"] == out[c]["decoy_first"]
    with pytest.raises(FM.IntegrityError, match="not E-G"):  # an F-like change outside the slots, read as L
        S.evaluate_conditions(ctx, cx, cfg, ctl.with_params(bias=ctl.bias + 0.01), np.array([54_000]), arm="L")
