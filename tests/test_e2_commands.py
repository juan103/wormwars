"""E2's runner (`scripts/e2.py`) through its stage commands, with fake rollouts, smoke sizes and a
scratch folder: the order of stages and the projection gate, the once-only refusals and the rerun
rule, the pilot's pairing and selection, the extension's resume, the hash checks before any hold-out
world is touched, and the registered rules (the allowance, the decision, the floor) as functions.

As in 04a's command tests, the formal guards are off here (`smoke=True, guarded=False`); they are
the shared ones in `wormwars/registration.py`, tested in `test_registration.py`, and their wiring runs
in the guarded smoke run on the binding commit."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


def _load(name="e2"):
    spec = importlib.util.spec_from_file_location(f"{name}_script", ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Fakes:
    """count = 3 for a genome whose mean bias is positive, else 0; 0 under the mirrored and constant
    probes; scripted arms reach 0 except the oracle (4). Every id passed in is recorded."""

    def __init__(self):
        self.calls, self.crash_at = [], None

    def rollout(self, cfg, iface, genome, ids, world_seed, device, chunk_worlds=None, **kw):
        ids = np.asarray(ids)
        self.calls.append(("neural", cfg.world.food_probe, genome.n_strains, ids.shape, ids.copy()))
        if self.crash_at is not None and len(self.calls) == self.crash_at:
            raise RuntimeError("boom")
        good = (genome.bias.mean(dim=1).cpu().numpy() > 0).astype(np.float32)
        count = np.repeat(good[:, None], ids.shape[-1], axis=1) * (3.0 if cfg.world.food_probe == "real" else 0.0)
        return SimpleNamespace(score=count, progress=np.zeros(count.shape, np.float32))

    def rollout_brain(self, cfg, iface, brain, ids, world_seed, device, ticks=None):
        n_w = len(ids)
        self.calls.append(("scripted", cfg.world.food_probe, 1, (n_w,), np.asarray(ids).copy()))
        v = 4.0 if type(brain).__name__ == "OracleBrain" else 0.0
        return SimpleNamespace(score=np.full((1, n_w), v, np.float32))


@pytest.fixture
def m(tmp_path, monkeypatch):
    mod = _load()
    mod.use_smoke(SimpleNamespace(command="project", stage=None, method=None), folder=tmp_path)
    fakes = Fakes()
    monkeypatch.setattr(mod.rollout_mod, "rollout", fakes.rollout)
    monkeypatch.setattr(mod, "rollout_brain", fakes.rollout_brain)
    mod._fakes = fakes
    return mod


def _args(command, stage=None, method=None, rerun=False, reason=None):
    return SimpleNamespace(command=command, stage=stage, method=method, device="cpu", smoke=True, guarded=False,
                           rerun=rerun, reason=reason)


CHAIN = [("project", None, None), ("pilot", 1, None), ("pilot", 2, None), ("train", None, "ga"),
         ("train", None, "random"), ("train", None, "es"), ("extend", None, None), ("evaluate", None, None)]


def _run(m, command, stage=None, method=None, **kw):
    fn = {"project": m.cmd_project, "pilot": m.cmd_pilot, "train": m.cmd_train, "extend": m.cmd_extend,
          "evaluate": m.cmd_evaluate}[command]
    return fn(_args(command, stage, method, **kw))


def _upto(m, n):
    for c in CHAIN[:n]:
        _run(m, *c)


def _rec(m, name):
    return json.loads(m.record_path(name).read_text())


# ------------------------------------------------------------------ the whole chain

def test_the_stages_run_in_order_and_the_evaluation_decides(m):
    _upto(m, len(CHAIN))
    ev = _rec(m, "evaluate")
    assert ev["outcome"] in m.OUTCOMES.values() and ev["outcome"].startswith("E2:")
    assert set(ev["methods"]) == {"ga", "random", "es"} and ev["methods"]["ga"]["complete"]
    assert "floor" in ev and "extension" in ev
    for name in ("pilot-1", "pilot-2", "train-ga", "train-random", "train-es", "extend"):
        assert _rec(m, name)["outcome"] == "completed"


def test_every_smoke_id_is_outside_the_registered_ranges(m):
    _upto(m, len(CHAIN))
    seen = np.concatenate([c[4].ravel() for c in m._fakes.calls])
    assert seen.max() < 10_000


@pytest.mark.parametrize("k", range(1, len(CHAIN)))
def test_each_stage_needs_the_one_before(m, k):
    _upto(m, k - 1)  # everything up to, but not including, the stage just before k
    with pytest.raises(SystemExit, match="has not run"):
        _run(m, *CHAIN[k])
    assert not (m.EXP / f"{m.STAGES[k]}-started.json").exists()


@pytest.mark.parametrize("k", range(len(CHAIN)))
def test_each_stage_runs_once(m, k):
    _upto(m, k + 1)
    with pytest.raises(SystemExit, match="runs once"):
        _run(m, *CHAIN[k])


def test_a_stage_needs_a_completed_projection_within_its_limit(m):
    _run(m, "project")
    p = _rec(m, "project")
    assert p["outcome"] == "completed" and p["within_limit"]
    p["within_limit"] = False
    m.record_path("project").write_text(json.dumps(p))
    with pytest.raises(SystemExit, match="over its limit"):
        _run(m, "pilot", 1)


# ------------------------------------------------------------------ the pilot and the ES

def test_the_pilot_pairs_its_settings_on_shared_seeds_and_selects_at_the_last_checkpoint(m):
    _upto(m, 3)
    p1, p2 = _rec(m, "pilot-1"), _rec(m, "pilot-2")
    seeds = [r["spec"]["run_seed"] for r in p1["records"]]
    assert sorted(set(seeds)) == sorted(set(r["spec"]["run_seed"] for r in p2["records"]))
    assert {(r["sigma"], r["lr"]) for r in p1["records"]} == {(s, 0.3 * s) for s in m.REGISTERED["pilot"]["sigmas"]}
    s = p1["selected_sigma"]
    assert {r["sigma"] for r in p2["records"]} == {s}
    assert p2["selected"]["sigma"] == s and p2["selected"]["lr_multiple"] in m.REGISTERED["pilot"]["lr_multiples"]
    last = m.REGISTERED["pilot"]["generations"] - 1
    assert all(r["checkpoints"][-1]["generation"] == last for r in p1["records"] + p2["records"])


def test_the_formal_es_uses_the_selected_setting_and_saves_its_state(m):
    _upto(m, 6)
    sel = _rec(m, "pilot-2")["selected"]
    es = _rec(m, "train-es")
    assert all((r["sigma"], r["lr"]) == (sel["sigma"], sel["lr"]) for r in es["records"])
    assert all(r["generations_completed"] == m.REGISTERED["generations"]["es"] for r in es["records"])
    assert len(es["state_sha256"]) == 64


def test_the_extension_continues_the_formal_runs_and_takes_the_best_over_both(m):
    _upto(m, 7)
    es, ext = _rec(m, "train-es"), _rec(m, "extend")
    g = m.REGISTERED["generations"]
    for a, b, c in zip(es["records"], ext["records"], ext["champions_over_both"]):
        assert b["log"][0]["generation"] == g["es"] and b["log"][-1]["generation"] == g["extension"] - 1
        allv = [x["validation_mean"] for x in a["checkpoints"] + b["checkpoints"]]
        assert c["run"] == a["spec"]["run"] and c["validation_mean"] == max(allv)


def test_the_extension_refuses_a_changed_state_file(m):
    _upto(m, 6)
    m.state_path().write_bytes(m.state_path().read_bytes() + b"x")
    with pytest.raises(SystemExit, match="state"):
        _run(m, "extend")


# ------------------------------------------------------------------ the evaluation

def test_the_hold_out_uses_one_strain_on_all_its_worlds(m):
    _upto(m, 7)
    m._fakes.calls.clear()
    _run(m, "evaluate")
    n = len(m.holdout_ids())
    hold = [c for c in m._fakes.calls if c[0] == "neural" and c[3] == (n,)]
    runs = len(m.run_specs())
    assert len(hold) == 3 * runs * 3 + runs and all(c[2] == 1 for c in hold)
    probes = {c[1] for c in hold}
    assert probes == {"real", "mirrored", "constant"}


def test_the_evaluation_refuses_a_champion_that_does_not_match_its_hash(m):
    _upto(m, 7)
    rec = _rec(m, "train-random")
    rec["records"][0]["champion"]["sha256"] = "0" * 64
    m.record_path("train-random").write_text(json.dumps(rec))
    with pytest.raises(SystemExit, match="does not match its committed hash"):
        _run(m, "evaluate")
    assert not (m.EXP / "evaluate-started.json").exists()


# ------------------------------------------------------------------ not completed, reruns, the cap

def test_a_crash_leaves_a_stopped_record_and_the_next_stage_waits_for_its_rerun(m):
    _upto(m, 3)
    m._fakes.crash_at = len(m._fakes.calls) + 2
    with pytest.raises(RuntimeError):
        _run(m, "train", method="ga")
    assert _rec(m, "train-ga")["outcome"] == m.OUTCOMES["stopped"]
    with pytest.raises(SystemExit, match="rerun"):
        _run(m, "train", method="random")
    m._fakes.crash_at = len(m._fakes.calls) + 2  # the rerun stops too: the stage is final, not completed
    with pytest.raises(RuntimeError):
        _run(m, "train", method="ga", rerun=True, reason="test")
    m._fakes.crash_at = None
    with pytest.raises(SystemExit, match="rerun once already"):
        _run(m, "train", method="ga", rerun=True, reason="test")
    for c in CHAIN[4:]:
        _run(m, *c)
    ev = _rec(m, "evaluate")
    assert not ev["methods"]["ga"]["complete"] and ev["outcome"] == m.OUTCOMES["no decision"]


def test_a_stopped_rerun_that_completes_opens_the_next_stage(m):
    _upto(m, 3)
    m._fakes.crash_at = len(m._fakes.calls) + 2
    with pytest.raises(RuntimeError):
        _run(m, "train", method="ga")
    m._fakes.crash_at = None
    _run(m, "train", method="ga", rerun=True, reason="test")
    assert _rec(m, "train-ga")["outcome"] == "completed"
    assert (m.EXP / "train-ga-attempt1.json").exists()
    _run(m, "train", method="random")


def test_a_cap_already_spent_does_not_start_a_stage(m, monkeypatch):
    _run(m, "project")
    monkeypatch.setattr(m.reg.CapClock, "spent_hours", lambda self: 99.0)
    with pytest.raises(SystemExit, match="did not start"):
        _run(m, "pilot", 1)
    assert not (m.EXP / "pilot-1-started.json").exists()


def test_the_pilot_does_not_accept_a_stopped_stage(m):
    _upto(m, 1)
    m._fakes.crash_at = len(m._fakes.calls) + 2
    with pytest.raises(RuntimeError):
        _run(m, "pilot", 1)
    with pytest.raises(SystemExit):
        _run(m, "pilot", 2)


# ------------------------------------------------------------------ registered rules as functions

def test_the_allowance_matches_the_design():
    mod = _load()
    a = mod.allowance()
    assert a["ga"] == a["random"] == 2_131_968
    assert a["es"] == 2_131_712 and a["es"] <= a["ga"] and a["ga"] - a["es"] < 256 * 8
    assert a["es_parts"] == {"pilot": 802_560, "formal": 1_329_152}


def test_checkpoints_count_generation_0_every_25th_and_the_last():
    mod = _load()
    assert mod.n_checkpoints(0, 1000, 25) == 41
    assert mod.n_checkpoints(0, 623, 25) == 26
    assert mod.n_checkpoints(0, 200, 25) == 9
    assert mod.n_checkpoints(623, 1000, 25) == 16


def _totals(means, worlds=1024):
    return [int(round(x * worlds)) for x in means]


@pytest.mark.parametrize("es,ga,rnd,complete,outcome,floor", [
    ([3.0] * 8, [2.0] * 8, [0.5] * 8, {}, "replace", "clears"),
    ([2.4] * 8, [2.0] * 8, [0.5] * 8, {}, "keep", "clears"),  # below the 0.5 margin
    ([2.5] * 8, [2.0] * 8, [0.5] * 8, {}, "replace", "clears"),  # exactly 0.5: "at least"
    ([6.0] * 3 + [2.0] * 5, [2.0] * 8, [0.5] * 8, {}, "keep", "clears"),  # mean up by 1.5, only 3 of 8 above
    ([3.0] * 6 + [2.0] * 2, [2.0] * 4 + [2.1] * 4, [0.5] * 8, {}, "replace", "clears"),  # 6 of 8 above ~2.05
    ([3.0] * 5 + [2.0] * 3, [2.0] * 4 + [2.1] * 4, [0.0] * 8, {}, "keep", "clears"),  # 5 of 8 above it
    ([3.0] * 8, [2.0] * 8, [0.5] * 8, {"es": False}, "es incomplete", "clears"),
    ([3.0] * 8, [2.0] * 8, [0.5] * 8, {"ga": False}, "no decision", "not made"),
    ([3.0] * 8, [2.0] * 8, [1.5] * 8, {}, "replace", "diagnose"),  # within 0.5 of the GA
    ([3.0] * 8, [2.0] * 8, [2.5] * 8, {}, "replace", "diagnose"),  # above the GA
    ([3.0] * 8, [2.0] * 8, [0.5] * 8, {"random": False}, "replace", "not made"),
])
def test_the_decision_rule(es, ga, rnd, complete, outcome, floor):
    mod = _load()
    comp = {"ga": True, "random": True, "es": True, **complete}
    d = mod.decide({"es": _totals(es), "ga": _totals(ga), "random": _totals(rnd)}, comp, 1024)
    assert d["outcome"] == mod.OUTCOMES[outcome]
    assert d["floor"] == mod.FLOOR[floor]
    assert d["provisional"] == (floor == "not made" and outcome != "no decision")


def test_the_pilot_selection_breaks_ties_by_the_smaller_value():
    mod = _load()
    rows = [{"sigma": s, "lr_multiple": 0.3, "total": t} for s, t in ((0.5, 12), (1.0, 10), (2.0, 12))]
    assert mod.select_sigma(rows) == 0.5  # a tie between 0.5 and 2: the registered order is 1, 0.5, 2
    rows = [{"sigma": 1.0, "lr_multiple": r, "total": t} for r, t in ((0.1, 7), (0.3, 5), (1.0, 7))]
    assert mod.select_rate(rows, 1.0) == 0.1  # the registered order is 0.3, 0.1, 1


def test_the_ga_call_is_04as_evolve_batch_with_04as_settings():
    """E2's GA runs through 04a's `evolve_batch` with 04a's registered evolution: on the CPU, with a
    fake simulator, the same seeds give the same checkpoint and final-population hashes."""
    import torch  # noqa: F401
    from wormwars.brain import BrainSpec
    from wormwars.connectome import load_connectome
    from wormwars.e04a import evolve as EV
    from wormwars.evo.genomes import genome_hash

    e2, e04a = _load(), _load("e04a")
    spec = BrainSpec.from_connectome(load_connectome())

    def fake(cfg, iface, genome, ids, world_seed, device, chunk_worlds=None):
        b = genome.bias.mean(dim=1).cpu().numpy()
        s = np.repeat(np.floor(np.clip(10 * b + 1, 0, None))[:, None], np.asarray(ids).shape[-1], axis=1)
        s = s.astype(np.float32)
        return SimpleNamespace(score=s, progress=np.zeros_like(s))

    runs = [EV.RunSpec(0, 42, 0.0), EV.RunSpec(1, 43, 0.0)]
    kw = dict(generations=3, checkpoint_every=2, validation_ids=np.arange(4), world_seed=1, id_base=0, id_span=100)
    got, _ = e2.run_method("ga", e2.task_config(), None, spec, runs, rollout_fn=fake, **kw)
    want = EV.evolve_batch(e04a.task_config(), None, spec, runs, rollout_fn=fake, **kw)
    for a, b in zip(got, want):
        assert [c["sha256"] for c in a.checkpoints] == [c["sha256"] for c in b.checkpoints]
        assert [genome_hash(a.final, i) for i in range(32)] == [genome_hash(b.final, i) for i in range(32)]


def test_the_task_and_the_ga_are_04as():
    e2, e04a = _load(), _load("e04a")
    assert e2.config_sha256(e2.task_config()) == e04a.config_sha256(e04a.task_config())
    assert e2.REGISTERED["ga"] == e04a.REGISTERED["evolution"]


def test_the_registered_id_ranges_are_disjoint_from_earlier_ones_and_each_other():
    mod = _load()
    spans = mod.id_spans()
    earlier = [(0, 10_000), (900_000_000, 901_000_000), (950_000_000, 951_000_000), (980_000_000, 981_000_000),
               (990_000_000, 991_000_000), (993_000_000, 995_000_000), (996_000_000, 1_000_000_000)]
    allspans = sorted(list(spans.values()) + earlier)
    for (a0, a1), (b0, b1) in zip(allspans, allspans[1:]):
        assert a1 <= b0, (a0, a1, b0, b1)


def test_seeds_are_disjoint_across_formal_pilot_projection_and_smoke_and_from_04a():
    mod, e04a = _load(), _load("e04a")
    groups = {k: set(v) for k, v in mod.seed_groups().items()}
    names = sorted(groups)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            assert not groups[a] & groups[b], (a, b)
    used = set(range(1_104_000, 1_110_000))  # 04a's development, formal, smoke and projection seeds
    assert not set().union(*groups.values()) & used


# ------------------------------------------------------------------ review v1 (D120)

def _kill(m, stage, hours_ago=2.0, last_write_hours_ago=1.0, partial=True):
    """What a hard kill leaves: a marker, perhaps a partial record, no record, no accounting."""
    import os
    import time
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - hours_ago * 3600))
    marker = m.EXP / f"{stage}-started.json"
    marker.write_text(json.dumps({"stage": stage, "started_utc": started, "provenance": {"git_commit": "x"}}))
    files = [marker]
    if partial:
        m.partial_path(stage).write_text("{}")
        files.append(m.partial_path(stage))
    t = time.time() - last_write_hours_ago * 3600
    for f in files:
        os.utime(f, (t, t))


def test_a_killed_attempt_then_a_crashed_rerun_is_final(m):
    _upto(m, 3)
    _kill(m, "train-ga")
    m._fakes.crash_at = len(m._fakes.calls) + 2
    with pytest.raises(RuntimeError):
        _run(m, "train", method="ga", rerun=True, reason="killed")
    m._fakes.crash_at = None
    _run(m, "train", method="random")  # the GA's stage is final, not completed


def test_a_crash_then_a_killed_rerun_is_charged_recorded_as_final_and_opens_the_next_stage(m):
    _upto(m, 3)
    m._fakes.crash_at = len(m._fakes.calls) + 2
    with pytest.raises(RuntimeError):
        _run(m, "train", method="ga")
    m._fakes.crash_at = None
    plan = m.rerun_plan("train-ga", [m.record_path("train-ga"), m.EXP / "train-ga-started.json",
                                     m.partial_path("train-ga")], "crashed")
    m.apply_rerun(plan)  # the rerun starts ...
    _kill(m, "train-ga")  # ... and is killed
    with pytest.raises(SystemExit, match="killed"):
        _run(m, "train", method="random")
    with pytest.raises(SystemExit, match="recorded as final"):
        _run(m, "train", method="ga", rerun=True, reason="the rerun was killed")
    rec = _rec(m, "train-ga")
    assert rec["outcome"] == m.OUTCOMES["stopped"] and rec["final"] and rec["reconciled_compute"]["seconds"] > 3600
    _run(m, "train", method="random")


def test_a_killed_attempt_and_a_killed_rerun_are_final(m):
    _upto(m, 3)
    _kill(m, "train-ga")
    plan = m.rerun_plan("train-ga", [m.record_path("train-ga"), m.EXP / "train-ga-started.json",
                                     m.partial_path("train-ga")], "killed")
    m.apply_rerun(plan)
    _kill(m, "train-ga")
    with pytest.raises(SystemExit, match="recorded as final"):
        _run(m, "train", method="ga", rerun=True, reason="the rerun was killed")
    assert _rec(m, "train-ga")["final"]
    _run(m, "train", method="random")


def test_an_incomplete_es_is_not_reported_as_failing_the_criteria():
    mod = _load()
    d = mod.decide({"es": _totals([9.0] * 8), "ga": _totals([2.0] * 8), "random": _totals([0.0] * 8)},
                   {"ga": True, "random": True, "es": False}, 1024)
    assert d["outcome"] == mod.OUTCOMES["es incomplete"] and "did not complete" in d["outcome"]


def test_every_decision_outcome_names_unshaped_fitness():
    mod = _load()
    for k in ("replace", "keep", "es incomplete"):
        assert "unshaped" in mod.OUTCOMES[k]


@pytest.mark.parametrize("after", [False, True])
def test_a_stopped_extension_keeps_champions_over_what_completed(m, after):
    """In smoke the extension runs generations 3-4 with one checkpoint, at 4: stop at its first
    training call, or after that checkpoint (on the save that follows it)."""
    _upto(m, 6)
    if after:
        orig = m.save_genomes

        def boom(records, cfg, prefix):
            if prefix == "extension" and any(r.checkpoints for r in records):
                orig(records, cfg, prefix)
                raise RuntimeError("after the checkpoint")
            return orig(records, cfg, prefix)
        m.save_genomes = boom
    else:
        m._fakes.crash_at = len(m._fakes.calls) + 1
    with pytest.raises(RuntimeError):
        _run(m, "extend")
    ext = _rec(m, "extend")
    assert ext["outcome"] == m.OUTCOMES["stopped"]
    champs = ext["champions_over_both"]
    assert len(champs) == len(m.run_specs())
    if not after:
        assert all(c["source"] == "formal" for c in champs)


def test_the_extensions_champion_tie_goes_to_the_formal_checkpoint():
    mod = _load()
    formal = {"checkpoints": [{"generation": 0, "validation_mean": 1.0, "sha256": "a"},
                              {"generation": 2, "validation_mean": 2.0, "sha256": "b"}]}
    c = mod.champion_over_both(formal, [{"generation": 4, "validation_mean": 2.0, "sha256": "c"}])
    assert (c["source"], c["sha256"]) == ("formal", "b")
    c = mod.champion_over_both(formal, [{"generation": 4, "validation_mean": 2.5, "sha256": "c"}])
    assert (c["source"], c["checkpoint"]) == ("extension", 0)


def test_a_stopped_evaluation_keeps_its_completed_arms_in_a_partial_record(m):
    _upto(m, 7)
    m._fakes.crash_at = len(m._fakes.calls) + 5
    with pytest.raises(RuntimeError):
        _run(m, "evaluate")
    # the partial record is written after each arm, so a kill (no handler) would keep them too
    part = json.loads(m.partial_path("evaluate").read_text())
    assert len(part["arms_completed"]) == 4


def test_an_over_limit_projection_records_the_experiment_outcome(m, monkeypatch):
    monkeypatch.setitem(m.REGISTERED["projection"], "max_training_hours", 0.0)
    _run(m, "project")
    p = _rec(m, "project")
    assert not p["within_limit"] and p["experiment_outcome"] == m.OUTCOMES["over limit"]


def test_the_pilot_ties_go_to_the_middle_setting_and_an_all_tied_stage_is_uninformative():
    mod = _load()
    rows = [{"sigma": s, "lr_multiple": 0.3, "total": 0} for s in (0.5, 1.0, 2.0)]
    assert mod.select_sigma(rows) == 1.0 and mod.uninformative(rows)
    rows = [{"sigma": s, "lr_multiple": 0.3, "total": t} for s, t in ((0.5, 5), (1.0, 3), (2.0, 5))]
    assert mod.select_sigma(rows) == 0.5 and not mod.uninformative(rows)
    rows = [{"sigma": 1.0, "lr_multiple": r, "total": 4} for r in (0.1, 0.3, 1.0)]
    assert mod.select_rate(rows, 1.0) == 0.3


def test_the_registered_es_constants_are_the_ones_the_code_uses():
    import inspect

    from wormwars.e2.optimizers import SCALES, OpenAIES
    mod = _load()
    es = mod.REGISTERED["es"]
    assert es["pairs"] == mod.REGISTERED["ga"]["population"] // 2  # the loop asks population / 2 pairs
    p = inspect.signature(OpenAIES).parameters
    assert (p["beta1"].default, p["beta2"].default, p["eps"].default) == (es["beta1"], es["beta2"], es["eps"])
    assert es["encoding_scales"] == SCALES


def test_smoke_projections_have_their_own_seeds(m):
    _run(m, "project")
    base = _rec(m, "project")["seeds_base"]
    assert base == m.SMOKE_PROJECTION_SEED_BASE and base not in m.seed_groups()["projection"]


def test_the_es_state_hash_is_a_plain_sha256(m):
    import hashlib
    _upto(m, 6)
    assert _rec(m, "train-es")["state_sha256"] == hashlib.sha256(m.state_path().read_bytes()).hexdigest()


def test_the_evaluation_reports_pairing_and_per_run_differences(m):
    _upto(m, len(CHAIN))
    ev = _rec(m, "evaluate")
    assert ev["pairing"]["generation0_candidates_match"] is True
    assert set(ev["es_minus_ga_per_run"]) == {f"run{r:02d}" for r in range(len(m.run_specs()))}


def test_an_atomic_write_survives_a_transient_permission_error(tmp_path, monkeypatch):
    """Windows can refuse a replace for a moment while another process (an indexer, an antivirus)
    holds the file; the per-arm partial record makes that likely (seen in this suite)."""
    import os
    mod = _load()
    real, fails = os.replace, [2]

    def flaky(a, b):
        if fails[0]:
            fails[0] -= 1
            raise PermissionError(5, "Access is denied")
        return real(a, b)
    monkeypatch.setattr(os, "replace", flaky)
    mod.write_atomic(tmp_path / "x.json", {"a": 1})
    assert json.loads((tmp_path / "x.json").read_text()) == {"a": 1}
