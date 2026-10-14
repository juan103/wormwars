"""The evolutionary E4-D's formal stages (`scripts/e4d_evo_formal.py`) against the bound pre-registration's §10 and
Amendment 1 (D276): the dependencies and refusals, provenance (append-only amendments, the formal commit, reruns),
integrity failures never rerun, the replay comparison and the timing refusal, the registered assertions sabotaged
through the stage code, the champion's inputs, the cue conditions at a multi-strain composition, S₀, the pinned files,
and the smokes' isolation."""

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
IDS = np.array([52_100, 52_101, 52_102])  # outside every pilot, formal, spent and smoke block


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


CHECK = {"timing": {"seconds_per_generation": 60.0}, "eg_sha256": "e"}


def test_a_stage_refuses_without_its_predecessors(S):
    with pytest.raises(SystemExit, match="check has not completed"):
        S.requires("train-l")(None, {})
    _write(S, "check", CHECK)
    assert "check" in S.requires("train-l")(None, {})
    with pytest.raises(SystemExit, match="train-l has not completed"):
        S.requires("evaluate-l")(None, {})


def test_a_stopped_predecessor_does_not_count(S):
    _write(S, "check", CHECK)
    S.E.record_path("check").write_text(json.dumps({"outcome": "E4-D evo formal: not completed (the run stopped)"}),
                                        encoding="utf-8")
    with pytest.raises(SystemExit):
        S.requires("train-l")(None, {})


def test_train_l_recomputes_the_timing_against_its_clock(S, monkeypatch):
    _write(S, "check", {**CHECK, "timing": {"seconds_per_generation": 300.0}})  # 10 h projected
    with pytest.raises(SystemExit, match="timing projection"):
        S.requires("train-l")(None, {})
    _write(S, "check", CHECK)  # 2 h projected: passes against an unused cap
    S.requires("train-l")(None, {})
    monkeypatch.setattr(S.E, "clock", lambda: SimpleNamespace(spent_hours=lambda: 6.0))  # a failed attempt spent 6 h
    with pytest.raises(SystemExit, match="timing projection"):  # 2 h against 0.8 × 2 h
        S.requires("train-l")(None, {})


def test_the_timing_rule_exactly(S):
    t = S.timing_ok(60.0, 0.5, 8.0)
    assert t["projected_hours"] == pytest.approx(2.0) and t["allowance_hours"] == pytest.approx(6.0)
    assert S.timing_ok(180.0, 0.5, 8.0)["within_cap"]  # exactly the allowance passes
    assert not S.timing_ok(180.01, 0.5, 8.0)["within_cap"]


@pytest.mark.parametrize("state, ok", [(ES.STATES[0], False), (ES.STATES[1], False), (ES.STATES[2], False),
                                       (ES.STATES[3], True), (ES.STATES[4], True)])
def test_s_needs_a_triggering_l_and_not_f(S, state, ok):
    _write(S, "check", CHECK)
    _write(S, "report-l", {"reading": {"state": state}})
    if ok:
        got = S.requires("train-s")(None, {})
        assert not any(k.endswith("-f") for k in got)  # nothing of F's is required
    else:
        with pytest.raises(SystemExit, match="not triggered"):
            S.requires("train-s")(None, {})


def test_f_failing_does_not_block_s(S):
    _write(S, "check", CHECK)
    _write(S, "report-l", {"reading": {"state": ES.STATES[3]}})
    S.E.record_path("train-f").write_text(json.dumps({"outcome": S.E.OUTCOMES["integrity"]}), encoding="utf-8")
    assert "report-l" in S.requires("train-s")(None, {})


def _formal(S, monkeypatch):
    monkeypatch.setattr(S, "SMOKE", False)
    monkeypatch.setattr(S, "check_provenance", lambda *a: None)
    monkeypatch.setattr(S.reg, "require_same_code", lambda *a, **k: None)


def test_a_changed_environment_is_refused(S, monkeypatch):
    _formal(S, monkeypatch)
    _write(S, "check", {**CHECK, "provenance_at_start": {"git_commit": "x", "torch": "2.12.0"}})
    S.requires("train-l")(None, {"torch": "2.12.0"})
    with pytest.raises(SystemExit, match="environment"):
        S.requires("train-l")(None, {"torch": "2.13.0"})


def test_a_changed_registration_is_refused(S, monkeypatch):
    _formal(S, monkeypatch)
    monkeypatch.setattr(S.reg, "require_same_env", lambda *a, **k: None)
    _write(S, "check", CHECK)
    S.REGISTERED["G"] = 101
    with pytest.raises(SystemExit, match="registration differs"):
        S.requires("train-l")(None, {})


def test_check_needs_the_local_populations_on_the_tested_machine(S, monkeypatch):
    _formal(S, monkeypatch)
    monkeypatch.setattr(S, "local_gen010", lambda *a, **k: None)
    with pytest.raises(SystemExit, match="generation-10"):
        S.requires("check")(None, {})


def test_amendments_are_appended_and_edits_refused(S):
    bound = b"# Title\r\n\r\nline one\r\nline two\r\n"
    S.prereg_append_only(bound, b"# Title\n\nline one\nline two\n\n## Amendment 1\n\nnew\n")
    S.prereg_append_only(bound, bound)
    with pytest.raises(SystemExit, match="changed"):
        S.prereg_append_only(bound, b"# Title\n\nline one\nline 2\n\n## Amendment 1\n")


def test_the_formal_commit_is_read_from_the_amendment(S):
    with pytest.raises(SystemExit, match="formal code's commit"):
        S.formal_commit("no amendment yet")
    assert S.formal_commit("a\n**The formal code's commit:** `abc1234`\nb\n**The formal code's commit:** `def5678`") \
        == "def5678"


def test_a_rerun_is_held_to_its_first_attempts_code_and_environment(S, monkeypatch):
    refs = {}
    _provenance_stubs(S, monkeypatch, refs)
    seen = []
    monkeypatch.setattr(S.reg, "require_same_code", lambda c, g, **k: seen.append(c))
    marker = S.E.marker_path("train-l")
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"provenance": {"git_commit": "first", "torch": "2.12.0"}}), encoding="utf-8")
    S.check_provenance(SimpleNamespace(rerun=True), {"torch": "2.12.0"}, "train-l")
    assert "first" in seen and "first" in refs
    with pytest.raises(SystemExit, match="environment"):
        S.check_provenance(SimpleNamespace(rerun=True), {"torch": "2.13.0"}, "train-l")


def test_an_integrity_failure_is_not_evaluable_and_never_rerun(S):
    path = S.E.record_path("train-l")
    path.parent.mkdir(parents=True, exist_ok=True)
    ctx = SimpleNamespace(salvage=lambda: {}, after_fail=lambda: None)
    for err in ("IntegrityError: run 3 unbalanced", "FloatingPointError: generation 4: non-finite",
                "RuntimeError: integrity: link-free strains [1] distinguish the assignments"):
        S.E._not_completed(path, {}, ctx, "stopped", err, 0.0)
        rec = json.loads(path.read_text(encoding="utf-8"))
        assert rec["outcome"] == S.E.OUTCOMES["integrity"] and rec["final"] is True
        marker = S.E.marker_path("train-l")
        marker.write_text(json.dumps({"stage": "train-l", "attempt": 1, "started_utc": "2026-10-14T00:00:00Z"}),
                          encoding="utf-8")
        with pytest.raises(SystemExit, match="only a stage stopped"):
            S.E.rerun_plan("train-l", [path, marker], "infrastructure: the driver")
    S.E._not_completed(path, {}, ctx, "stopped", "RuntimeError: CUDA error: an illegal memory access", 0.0)
    assert json.loads(path.read_text(encoding="utf-8"))["outcome"] == S.E.OUTCOMES["stopped"]


def test_a_rerun_keeps_the_first_attempts_training_files(S):
    files = S.train_files("L")
    assert files[0].name == "L-selections.npz" and files[1].name == "L-parents.npz"
    assert len(files) == 2 + 32 * (len(set(range(0, 100, 10)) | {99}) + 1)


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


def test_the_local_populations_are_hashed_from_their_arrays(S, trial):
    _, cx = trial
    loc = S.local_gen010(cx["org"].genome.spec, cx["org"].genome.cfg)
    if loc is None:
        pytest.skip("the pilot's local populations are not on this machine")
    runs = [r["run"] for r in S.PILOT_RUNS]
    assert S.population_digest([S.population_digest(loc[r]) for r in runs]) == S.PILOT_DIGEST
    meta = json.loads(str(np.load(S.gen010_files()[runs[0]], allow_pickle=False)["meta"]))["genome_sha256s"]
    assert loc[runs[0]] == meta  # the arrays agree with the recorded hashes


def test_the_pinned_files_hash_as_registered(S, monkeypatch):
    monkeypatch.setattr(S, "SMOKE", False)
    S.check_pinned()
    monkeypatch.setitem(S.PINNED, "docs/E4/E4-D-DESIGN.md", "0" * 64)
    with pytest.raises(SystemExit, match="does not hash"):
        S.check_pinned()


def test_smokes_are_isolated_from_the_formal_layout(S, monkeypatch):
    formal_seed = FM.MAZE_SEED
    formal = np.concatenate(list(FM.all_blocks().values()))
    for name in ("MAZES", "TRIALS", "POP", "MAZE_SEED", "SEED_BASE", "CHECK_IDS", "CHECKPOINT_IDS", "TRAIN", "TIMING"):
        monkeypatch.setattr(FM, name, getattr(FM, name))
    monkeypatch.setattr(FM, "BASES", dict(FM.BASES))
    monkeypatch.setattr(FM, "N_RUNS", dict(FM.N_RUNS))
    S.use_smoke()
    assert FM.MAZE_SEED != formal_seed and FM.SEED_BASE != 1_440_000
    smoke = np.concatenate(list(FM.all_blocks().values()))
    assert not np.isin(smoke, formal).any()
    for lo, hi in FM.SPENT:
        assert not np.any((smoke >= lo) & (smoke < hi))
    assert FM.TRAIN[0] >= 200_000_000


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
    assert S.same_genome(s0, want)
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
    a = ET.trial_rollout(cx)(cfg, org.iface, batch, IDS, FM.MAZE_SEED, "cpu")
    b = ET.trial_rollout(cx, a_source="decoy")(cfg, org.iface, batch, IDS, FM.MAZE_SEED, "cpu")
    assert np.array_equal(b.real_first_maze, a.decoy_first_maze[:, :, ::-1])
    assert np.array_equal(b.decoy_first_maze, a.real_first_maze[:, :, ::-1])


def _ctx():
    return SimpleNamespace(cap=SimpleNamespace(check=lambda: None), args=SimpleNamespace(device="cpu"))


def test_the_evaluation_path_plays_every_condition(trial, S):
    cfg, cx = trial
    eg = cx["org"].genome.select([0])
    ctl = TL.control_genome(eg, cx, "comparator", 3.0)
    saved = []
    out = S.evaluate_conditions(_ctx(), cx, cfg, ctl, IDS[:2], arm="L", start=eg,
                                persist=lambda n, r: saved.append(n))
    assert set(out) == {"intact", "reversed", "removed", "fixed", "cut", "eg", "start"} == set(saved)
    for c in ("removed", "fixed", "cut", "eg"):
        assert out[c]["real_first"] == out[c]["decoy_first"]
        assert np.asarray(out[c]["per_maze"]["neither"]).shape == (2, 2)


def test_an_unbalanced_condition_raises_after_it_is_saved(trial, S, monkeypatch):
    """Astra (D276): the assertion itself, sabotaged through the stage code, not a balance the control has anyway."""
    cfg, cx = trial
    eg = cx["org"].genome.select([0])
    ctl = TL.control_genome(eg, cx, "comparator", 3.0)
    real = S.play

    def unbalanced(ctx, cx_, cfg_, g, ids, *, a_source="real", **kw):
        res = real(ctx, cx_, cfg_, g, ids, a_source=a_source, **kw)
        if a_source == "fixed0":
            res.real_first_maze = res.real_first_maze.copy()
            res.decoy_first_maze = res.decoy_first_maze.copy()
            res.real_first_maze[0, 0] = [1, 1]
            res.decoy_first_maze[0, 0] = [0, 0]
        return res

    monkeypatch.setattr(S, "play", unbalanced)
    saved = []
    with pytest.raises(FM.IntegrityError, match="fixed"):
        S.evaluate_conditions(_ctx(), cx, cfg, ctl, IDS[:2], arm="L", persist=lambda n, r: saved.append(n))
    assert saved[-1] == "fixed"  # saved before the assertion
    monkeypatch.setattr(FM, "assert_balanced", lambda *a: None)  # with the assertion disabled, nothing is raised
    S.evaluate_conditions(_ctx(), cx, cfg, ctl, IDS[:2], arm="L")


def test_a_cut_champion_that_is_not_eg_raises(trial, S):
    cfg, cx = trial
    eg = cx["org"].genome.select([0])
    ctl = TL.control_genome(eg, cx, "comparator", 3.0)
    with pytest.raises(FM.IntegrityError, match="not E-G"):  # an F-like change outside the slots, read as L
        S.evaluate_conditions(_ctx(), cx, cfg, ctl.with_params(bias=ctl.bias + 0.01), IDS[:1], arm="L")


def test_the_frozen_set_and_the_lineage_checks(trial, S):
    _, cx = trial
    eg = cx["org"].genome.select([0])
    start = Genome.cat([eg, eg])
    sc = S.scales_of(cx, "L")
    S.check_frozen(start, Genome.cat([TL.control_genome(eg, cx, "comparator", 1.0), eg]), sc, "slots move")
    with pytest.raises(FM.IntegrityError, match="frozen"):
        S.check_frozen(start, Genome.cat([eg.with_params(bias=eg.bias + 0.01), eg]), sc, "a bias moved")
    rec = SimpleNamespace(final=start, spec=SimpleNamespace(run=0))
    S.check_lineage([rec], [{"final": start}])
    with pytest.raises(FM.IntegrityError, match="lineage"):
        S.check_lineage([rec], [{"final": Genome.cat([eg.with_params(bias=eg.bias + 0.01), eg])}])


def test_the_champion_uses_the_last_selection(trial, S):
    _, cx = trial
    eg = cx["org"].genome.select([0])
    final = Genome.cat([eg, eg, eg])
    slots = AR.slot_indices(cx)
    val = np.array([[1.0, 0.5], [1.0, 0.5], [0.0, 0.0]])  # 0 and 1 tie on validation
    sel = np.zeros((2, 3, 4))
    sel[0, 0], sel[-1, 1] = 1.0, 1.0  # the first selection favours 0, the last favours 1
    assert S.champion_of(final, val, sel, slots) == 1


def test_a_final_population_that_differs_from_the_training_record_raises(trial, S):
    cfg, cx = trial
    eg = cx["org"].genome.select([0])
    pop = Genome.cat([eg, TL.control_genome(eg, cx, "comparator", 1.0)])
    path = S.pop_path("L", 0, "final")
    path.parent.mkdir(parents=True, exist_ok=True)
    S.save_population(path, pop, cfg=cfg, run=0)
    from wormwars.evo.genomes import genome_hash
    want = [genome_hash(pop, i) for i in range(2)]
    got = S.load_final("L", 0, want, cx["org"].genome.spec, cx["org"].genome.cfg, "cpu")
    assert S.same_genome(got, pop)
    with pytest.raises(FM.IntegrityError, match="differs from the training record"):
        S.load_final("L", 0, want[::-1], cx["org"].genome.spec, cx["org"].genome.cfg, "cpu")


def test_an_edited_amendment_is_refused(S):
    """Astra (D277): the text at every reference commit (the bound one, the formal commit, earlier stages' and the first
    attempt's) must survive as a prefix, so an earlier amendment cannot be rewritten either."""
    bound = b"# T\n\nbound\n"
    formal = bound + b"\n## Amendment 1\n\nids 64 000\n"
    S.check_prereg(formal + b"\nmore\n", {"c3fe432": bound, "fb30301": formal})
    with pytest.raises(SystemExit, match="fb30301"):
        S.check_prereg(bound + b"\n## Amendment 1\n\nids 65 000\n", {"c3fe432": bound, "fb30301": formal})


def _provenance_stubs(S, monkeypatch, refs):
    monkeypatch.setattr(S, "SMOKE", False)
    monkeypatch.setattr(S, "check_pinned", lambda: None)
    monkeypatch.setattr(S.E, "require_committed", lambda p: None)
    monkeypatch.setattr(S, "formal_commit", lambda t: "f")
    monkeypatch.setattr(S, "prereg_at", lambda c: refs.setdefault(c, b""))
    monkeypatch.setattr(S.reg, "require_same_code", lambda c, g, **k: None)


def test_an_interrupted_rerun_setup_is_held_to_the_archived_marker(S, monkeypatch):
    """Astra (D277): after the frame has archived the first marker as -attempt1, the comparison reads it."""
    refs = {}
    _provenance_stubs(S, monkeypatch, refs)
    marker = S.E.marker_path("check")
    marker.parent.mkdir(parents=True, exist_ok=True)
    S.E.attempt1(marker).write_text(json.dumps({"provenance": {"git_commit": "first", "torch": "2.12.0"}}),
                                    encoding="utf-8")
    S.check_provenance(SimpleNamespace(rerun=True), {"torch": "2.12.0"}, "check")
    assert {"first", "f", "c3fe432"} <= set(refs)  # the first attempt's, the formal and the bound texts
    with pytest.raises(SystemExit, match="environment"):
        S.check_provenance(SimpleNamespace(rerun=True), {"torch": "2.13.0"}, "check")


def test_a_rerun_without_any_first_marker_is_refused(S, monkeypatch):
    _provenance_stubs(S, monkeypatch, {})
    with pytest.raises(SystemExit, match="first attempt"):
        S.check_provenance(SimpleNamespace(rerun=True), {}, "check")
    S.check_provenance(SimpleNamespace(rerun=False), {}, "check")  # a first attempt needs none
