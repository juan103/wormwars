"""E2d's runner (`scripts/e2d.py`) through its stage commands, with fake rollouts and smoke sizes. The
sources (E2's and 04a's smoke records and genome files) are generated in a scratch folder by E2's and
04a's own runners, with the same fakes. Checked: the stage order, the controls' replay as a gate, the
pairing, the admission rule for first attempts and reruns, the hard stop, the hash checks, Part B's
checks and de-duplication, and the hold-out pass with a missing arm. The formal guards are off, as
in E2's command tests."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(f"{name}_script_{id(object())}", ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Fakes:
    """count = 3 for a genome whose mean bias is positive, else 0, under every probe (a non-stereo
    plateau by construction). Records every id."""

    def __init__(self):
        self.calls = []

    def rollout(self, cfg, iface, genome, ids, world_seed, device, chunk_worlds=None, **kw):
        ids = np.asarray(ids)
        self.calls.append((cfg.world.food_probe, genome.n_strains, ids.shape, ids.copy()))
        good = (genome.bias.mean(dim=1).cpu().numpy() > 0).astype(np.float32)
        count = np.repeat(good[:, None], ids.shape[-1], axis=1) * 3.0
        return SimpleNamespace(score=count, progress=np.zeros(count.shape, np.float32),
                               events={}, final_head=np.zeros(count.shape + (2,), np.float32))

    def rollout_brain(self, cfg, iface, brain, ids, world_seed, device, ticks=None):
        n = len(ids)
        self.calls.append((cfg.world.food_probe, 1, (n,), np.asarray(ids).copy()))
        return SimpleNamespace(score=np.zeros((1, n), np.float32), events={}, final_head=np.zeros((1, n, 2), np.float32))


def fake_scripted(cfg, iface, maker, params, world_ids, probe, device, cap):
    """S-const steers by the difference (4 real, 0 otherwise); M-avg reads the mean (2 always)."""
    n = len(world_ids)
    if maker == "S-const":
        return np.full(n, 4.0 if probe == "real" else 0.0)
    return np.full(n, 2.0)


def _args(command, arm=None, rerun=False, reason=None):
    return SimpleNamespace(command=command, arm=arm, stage=None, method=None, device="cpu", smoke=True,
                           guarded=False, rerun=rerun, reason=reason)


@pytest.fixture(scope="module")
def sources(tmp_path_factory):
    """E2's and 04a's smoke chains, run once, with fakes, into a scratch folder."""
    base = tmp_path_factory.mktemp("sources")
    fakes = Fakes()
    e2 = _load("e2")
    e2.use_smoke(SimpleNamespace(command="project", stage=None, method=None), folder=base / "e2")
    e2.rollout_mod.rollout, orig = fakes.rollout, e2.rollout_mod.rollout
    e2.rollout_brain = fakes.rollout_brain
    try:
        for c, kw in [("project", {}), ("pilot", {"stage": 1}), ("pilot", {"stage": 2}), ("train", {"method": "ga"}),
                      ("train", {"method": "random"}), ("train", {"method": "es"}), ("extend", {}), ("evaluate", {})]:
            a = SimpleNamespace(command=c, stage=kw.get("stage"), method=kw.get("method"), device="cpu", smoke=True,
                                guarded=False, rerun=False, reason=None)
            {"project": e2.cmd_project, "pilot": e2.cmd_pilot, "train": e2.cmd_train, "extend": e2.cmd_extend,
             "evaluate": e2.cmd_evaluate}[c](a)
        e04a = _load("e04a")
        e04a.use_smoke(SimpleNamespace(command="project", batch=None), folder=base / "e04a")
        e04a.rollout_brain = fakes.rollout_brain
        for c, b in (("project", None), ("train", "A"), ("train", "B")):
            a = SimpleNamespace(command=c, batch=b, device="cpu", smoke=True, guarded=False, rerun=False, reason=None)
            {"project": e04a.cmd_project, "train": e04a.cmd_train}[c](a)
    finally:
        e2.rollout_mod.rollout = orig
    return base


@pytest.fixture
def m(sources, tmp_path, monkeypatch):
    mod = _load("e2d")
    mod.use_smoke(SimpleNamespace(command="project"), folder=tmp_path / "e2d", e2_folder=sources / "e2",
                  e04a_folder=sources / "e04a")
    fakes = Fakes()
    monkeypatch.setattr(mod.rollout_mod, "rollout", fakes.rollout)
    monkeypatch.setattr(mod, "rollout_brain", fakes.rollout_brain)
    monkeypatch.setattr(mod, "scripted", fake_scripted)
    mod._fakes = fakes
    return mod


CHAIN = [("project",), ("probe",), ("siblings",), ("replay",), ("arm", "c1"), ("arm", "c2"), ("arm", "c4"),
         ("arm", "c3"), ("evaluate",)]


def _run(m, command, arm=None, **kw):
    fn = {"project": m.cmd_project, "probe": m.cmd_probe, "siblings": m.cmd_siblings, "replay": m.cmd_replay,
          "arm": m.cmd_arm, "evaluate": m.cmd_evaluate}[command]
    return fn(_args(command, arm, **kw))


def _upto(m, n):
    for c in CHAIN[:n]:
        _run(m, *c)


def _rec(m, stage):
    return json.loads(m.E.record_path(stage).read_text())


def test_the_whole_chain_runs_and_reads(m):
    _upto(m, len(CHAIN))
    b = _rec(m, "probe")
    assert b["checks"]["passed"] and b["non_stereo_plateau"] in (True, False)
    assert _rec(m, "replay")["passed"]
    ev = _rec(m, "evaluate")
    assert set(ev["arms"]) == {"c1", "c2", "c4", "c3"}
    assert all("reading" in v for v in ev["arms"].values())
    assert "interaction" in ev["contrasts"]
    for x in ("c1", "c2", "c4", "c3"):
        assert _rec(m, f"arm-{x}")["pairing"]["passed"]


def test_every_smoke_id_is_below_10_000(m):
    _upto(m, len(CHAIN))
    seen = np.concatenate([c[3].ravel() for c in m._fakes.calls])
    assert seen.max() < 10_000


@pytest.mark.parametrize("k", range(1, len(CHAIN)))
def test_each_stage_needs_the_one_before(m, k):
    _upto(m, k - 1)
    with pytest.raises(SystemExit, match="has not run"):
        _run(m, *CHAIN[k])


def test_a_replay_that_does_not_match_e2_blocks_part_c(m, sources):
    _upto(m, 3)
    path = sources / "e2" / "train-ga.json"
    keep = path.read_text()
    rec = json.loads(keep)
    rec["records"][0]["checkpoints"][1]["sha256"] = "0" * 64
    path.write_text(json.dumps(rec))
    try:
        _run(m, "replay")
    finally:
        path.write_text(keep)
    r = _rec(m, "replay")
    assert not r["passed"] and r["diagnosis"].startswith("drift")
    with pytest.raises(SystemExit, match="Part C does not start"):
        _run(m, "arm", "c1")


def test_a_first_attempt_that_does_not_fit_is_skipped_and_the_pass_runs_without_it(m, monkeypatch):
    _upto(m, 4)
    monkeypatch.setattr(m.reg.CapClock, "spent_hours", lambda self: m.REGISTERED["cap_gpu_hours"] - 0.1)
    with pytest.raises(SystemExit, match="skipped"):
        _run(m, "arm", "c1")
    monkeypatch.setattr(m.reg.CapClock, "spent_hours", lambda self: 0.0)
    for x in ("c2", "c4", "c3"):
        _run(m, "arm", x)
    _run(m, "evaluate")
    ev = _rec(m, "evaluate")
    assert ev["arms"]["c1"]["reading"].startswith("not drawn")
    assert ev["contrasts"]["interaction"].startswith("not drawn")


def test_a_rerun_that_does_not_fit_is_final_and_not_completed(m, monkeypatch):
    _upto(m, 4)
    real = m.E.train_batch

    def boom(*a, **k):
        raise RuntimeError("crash")
    m.E.train_batch = boom
    with pytest.raises(RuntimeError):
        _run(m, "arm", "c1")
    m.E.train_batch = real
    monkeypatch.setattr(m.reg.CapClock, "spent_hours", lambda self: m.REGISTERED["cap_gpu_hours"] - 0.1)
    with pytest.raises(SystemExit, match="not admitted"):
        _run(m, "arm", "c1", rerun=True, reason="crashed")
    rec = _rec(m, "arm-c1")
    assert rec["final"] and rec["rerun_refused"]
    monkeypatch.setattr(m.reg.CapClock, "spent_hours", lambda self: 0.0)
    _run(m, "arm", "c2")  # the next arm is not blocked


def test_training_runs_under_the_hard_stop(m, monkeypatch):
    _upto(m, 4)
    monkeypatch.setattr(m, "training_clock", lambda: m.reg.CapClock(0.0, m.OUT / "compute.json"))
    with pytest.raises(SystemExit, match="cap"):
        _run(m, "arm", "c1")
    assert _rec(m, "arm-c1")["outcome"] == m.E.OUTCOMES["cap"]


def test_part_b_evaluates_a_shared_genome_once_and_draws_no_reading_if_a_check_fails(m, monkeypatch):
    _upto(m, 1)

    def broken(cfg, iface, maker, params, world_ids, probe, device, cap):
        return np.full(len(world_ids), 2.0)  # S-const no longer loses under mean and swapped
    monkeypatch.setattr(m, "scripted", broken)
    m._fakes.calls.clear()  # the projection's timing rollouts are not Part B's
    _run(m, "probe")
    b = _rec(m, "probe")
    assert not b["checks"]["passed"] and b["non_stereo_plateau"].startswith("not drawn")
    shas = b["champion_sha256"]
    distinct = len(set(shas.values()))
    neural_calls = [c for c in m._fakes.calls if c[2] == (16,)]
    assert len(neural_calls) == distinct * 3


def test_the_evaluation_refuses_a_champion_that_does_not_match_its_hash(m):
    _upto(m, 8)
    rec = _rec(m, "arm-c2")
    rec["records"][0]["champion"]["sha256"] = "0" * 64
    m.E.record_path("arm-c2").write_text(json.dumps(rec))
    with pytest.raises(SystemExit, match="does not match its committed hash"):
        _run(m, "evaluate")


def test_matched_checkpoints_are_chosen_among_the_matched_generations(m):
    rec = {"checkpoints": [{"generation": g, "validation_mean": v, "sha256": str(g)}
                           for g, v in ((0, 1.0), (25, 3.0), (100, 2.0), (125, 9.0), (200, 2.0))]}
    c = m.matched(rec, [0, 100, 200])
    assert (c["generation"], c["checkpoint"]) == (100, 2)  # the first best among 0, 100 and 200


def test_the_registered_arms_ids_and_seeds():
    mod = _load("e2d")
    R = mod.REGISTERED
    assert R["arms"]["c1"] == {"method": "ga", "worlds": 32, "mutation_scale": 1.0, "generations": 250}
    assert R["arms"]["c2"] == {"method": "ga", "worlds": 8, "mutation_scale": 0.5, "generations": 1000}
    assert R["arms"]["c4"] == {"method": "ga", "worlds": 32, "mutation_scale": 0.5, "generations": 250}
    assert R["arms"]["c3"] == {"method": "es", "worlds": 8, "sigma": 0.25, "lr": 0.15, "generations": 623}
    assert R["matched_generations"] == [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 999]
    assert (R["cap_gpu_hours"], R["training_cap_hours"], R["reserve_hours"]) == (7.0, 6.5, 0.5)
    spans = [(v["first"], v["first"] + v["worlds"]) for v in R["ids"].values()]
    earlier = [(0, 10_000), (900_000_000, 901_000_000), (950_000_000, 951_000_000), (980_000_000, 981_000_000),
               (990_000_000, 991_000_000), (993_000_000, 1_000_000_000)]
    allspans = sorted(spans + earlier)
    for (a0, a1), (b0, b1) in zip(allspans, allspans[1:]):
        assert a1 <= b0
    assert R["ga"] == _load("e2").REGISTERED["ga"]  # E2's GA, unchanged


def test_a_32_world_draw_begins_with_the_8_world_draw():
    from wormwars.e04a.evolve import train_ids
    for r in range(8):
        for g in (0, 1, 249, 999):
            assert (train_ids(1_120_000 + r, g, 32, 995_300_000, 500_000)[:8]
                    == train_ids(1_120_000 + r, g, 8, 995_300_000, 500_000)).all()


# ------------------------------------------------------------------ code review (D133)

def test_a_capped_arm_is_final_and_the_pass_still_runs(m, monkeypatch):
    """Review (both): the hard stop's "cap reached" must not block the later arms or the pass."""
    _upto(m, 4)
    real = m.training_clock
    monkeypatch.setattr(m, "training_clock", lambda: m.reg.CapClock(0.0, m.OUT / "compute.json"))
    with pytest.raises(SystemExit, match="cap"):
        _run(m, "arm", "c1")
    monkeypatch.setattr(m, "training_clock", real)
    for x in ("c2", "c4", "c3"):
        _run(m, "arm", x)
    _run(m, "evaluate")
    ev = _rec(m, "evaluate")
    assert ev["arms"]["c1"]["reading"] == "not drawn (the arm did not complete)"
    assert ev["contrasts"]["interaction"].startswith("not drawn")


def test_an_arm_stopped_after_a_checkpoint_gets_no_reading(m, monkeypatch):
    """Review (both): a stopped arm keeps champions from its last checkpoint; they must not be read."""
    _upto(m, 5)
    orig = m.E.write_atomic

    def boom(path, doc, **kw):
        orig(path, doc, **kw)
        if path == m.E.partial_path("arm-c2") and doc.get("records"):
            raise RuntimeError("after the checkpoint")
    m.E.write_atomic = boom
    with pytest.raises(RuntimeError):
        _run(m, "arm", "c2")
    m.E.write_atomic = orig
    monkeypatch.setattr(m.reg.CapClock, "spent_hours", lambda self: m.REGISTERED["cap_gpu_hours"] - 0.1)
    with pytest.raises(SystemExit, match="not admitted"):
        _run(m, "arm", "c2", rerun=True, reason="stopped")
    monkeypatch.setattr(m.reg.CapClock, "spent_hours", lambda self: 0.0)
    for x in ("c4", "c3"):
        _run(m, "arm", x)
    _run(m, "evaluate")
    ev = _rec(m, "evaluate")
    assert ev["arms"]["c2"]["reading"] == "not drawn (the arm did not complete)"
    assert ev["contrasts"]["interaction"].startswith("not drawn")


def test_failed_part_b_checks_suppress_set_readings_and_leave_part_c_on_scores(m, monkeypatch):
    _upto(m, 1)
    monkeypatch.setattr(m, "scripted", lambda cfg, iface, maker, params, ids, probe, device, cap: np.full(len(ids), 2.0))
    _run(m, "probe")
    b = _rec(m, "probe")
    assert all(s["reading"].startswith("not drawn") for s in b["sets"].values() if s["read"])
    for c in CHAIN[2:]:
        _run(m, *c)
    ev = _rec(m, "evaluate")
    assert all(v["plateau_rule"] == "scores only (a Part B check failed)" for v in ev["arms"].values())


def test_an_arm_record_carries_the_arms_own_configuration(m):
    _upto(m, 6)
    c2, c1 = _rec(m, "arm-c2"), _rec(m, "arm-c1")
    assert c2["resolved_config"]["mutation"]["w_sigma"] == pytest.approx(0.04)
    assert c1["resolved_config"]["evo"]["worlds_per_strain"] == m.REGISTERED["arms"]["c1"]["worlds"]
    assert c1["resolved_config"]["evo"]["generations"] == m.REGISTERED["arms"]["c1"]["generations"]
    assert c1["resolved_config_sha256"] != c1["base_config_sha256"]


def test_a_failed_pairing_check_blocks_the_paired_readings(m, monkeypatch):
    _upto(m, 4)
    real = m.pairing_check
    monkeypatch.setattr(m, "pairing_check", lambda *a, **k: {**real(*a, **k), "passed": False})
    for x in ("c1", "c2", "c4", "c3"):
        _run(m, "arm", x)
    _run(m, "evaluate")
    ev = _rec(m, "evaluate")
    assert all(v["reading"].startswith("not drawn (the pairing") for v in ev["arms"].values())


def test_the_pairing_check_uses_the_ids_actually_played_at_the_last_generation(m):
    _upto(m, 5)
    rec = _rec(m, "arm-c1")
    last = rec["pairing"]["last_generation_ids"]
    assert len(last) == len(m.e2_runs()) and all(len(x) == m.REGISTERED["arms"]["c1"]["worlds"] for x in last)


def test_the_projection_counts_what_is_already_spent(m, monkeypatch):
    monkeypatch.setattr(m.reg.CapClock, "spent_hours", lambda self: 6.2)
    _run(m, "project")
    p = _rec(m, "project")
    assert p["spent_hours"] >= 6.2 and p["projected_total_hours"] > 6.2 >= p["projected_hours"]
    assert p["within_limit"] is False  # the rest alone would fit; the total does not


def test_the_probes_act_on_task_ns_sensors():
    """`mean` and `swapped` change what a stereo steerer does on Task N (a real rollout, CPU)."""
    mod = _load("e2d")
    from wormwars.connectome import load_connectome
    from wormwars.interface import load_interface
    iface = load_interface(load_connectome())
    cfg = mod.E.task_config()
    cfg.world.max_ticks = 60
    world = np.arange(8)
    res = {}
    for p in ("real", "mean", "swapped"):
        res[p] = mod.scripted(cfg, iface, "S-const", {"k": 64.0, "speed": 1.0, "turn": -0.2}, world, p, "cpu",
                              SimpleNamespace(check=lambda: None))
    assert res["real"].mean() > res["mean"].mean() and res["real"].mean() > res["swapped"].mean()


def test_a_missing_04a_record_is_an_error_outside_smoke(m, tmp_path):
    m.SMOKE = False
    m.E04A_EXP = tmp_path / "nowhere"
    with pytest.raises(SystemExit, match="04a"):
        m.e04a_champions(None, None)


# ------------------------------------------------------------------ confirmation review (D134)

def _as_recs(m, arm):
    """The arm's committed records as the objects `pairing_check` reads."""
    from wormwars.e04a.evolve import RunSpec
    return [SimpleNamespace(spec=RunSpec(**r["spec"]), checkpoints=r["checkpoints"], generation0=r["generation0"])
            for r in _rec(m, f"arm-{arm}")["records"]]


def _played(m, arm):
    P = m.REGISTERED["ga"]["population"]
    rows = _rec(m, f"arm-{arm}")["pairing"]["last_generation_ids"]
    return np.repeat(np.asarray(rows), P, axis=0)  # every strain of a run plays its run's worlds


def test_the_pairing_check_fails_on_each_kind_of_mismatch(m):
    """Fable: seen failing on its own inputs, not only through its consequence."""
    _upto(m, 6)
    train, _ = m.e2_ids()
    recs, played = _as_recs(m, "c1"), _played(m, "c1")
    assert m.pairing_check("c1", recs, train, played)["passed"]
    bad = played.copy()
    bad[m.REGISTERED["ga"]["population"] + 1, 0] += 1  # a later strain of run 1 plays another world
    assert not m.pairing_check("c1", recs, train, bad)["passed"]
    from wormwars.e04a.evolve import RunSpec
    renamed = [SimpleNamespace(spec=RunSpec(99, recs[0].spec.run_seed, 0.0), checkpoints=recs[0].checkpoints,
                               generation0=recs[0].generation0)] + recs[1:]
    r = m.pairing_check("c1", renamed, train, played)  # only the roster differs
    assert r["per_run"] == m.pairing_check("c1", recs, train, played)["per_run"] and not r["passed"]
    recs2, played2 = _as_recs(m, "c2"), _played(m, "c2")
    assert m.pairing_check("c2", recs2, train, played2)["passed"]
    recs2[0].checkpoints = [{**recs2[0].checkpoints[0], "sha256": "0" * 64}] + recs2[0].checkpoints[1:]
    assert not m.pairing_check("c2", recs2, train, played2)["passed"]  # generation 0


def _analyse_c_inputs(m, b_ok):
    runs, W = range(8), 16
    real, zero = [2] * W, [0] * W
    b = {"checks": {"passed": b_ok}, "per_world_counts": {}}
    for r in runs:
        for lab in ("e2 ga", "e2 es"):
            for p in ("real", "mean", "swapped"):
                b["per_world_counts"][f"{lab} run{r:02d} {p}"] = real
    counts = {}
    for r in runs:
        for lab in ("ga'", "c1", "c2", "c4", "c3", "c2'"):
            counts[f"{lab} run{r:02d} real"] = np.array(real)
            counts[f"{lab} run{r:02d} mean"] = np.array(zero)  # loses under the probes: "uses"
            counts[f"{lab} run{r:02d} swapped"] = np.array(zero)
    arms = {x: {"outcome": "completed", "pairing": {"passed": True}} for x in ("c1", "c2", "c4", "c3")}
    return counts, b, arms


@pytest.mark.parametrize("b_ok,leaves", [(True, True), (False, False)])
def test_part_bs_check_failure_changes_the_plateau_rule_by_behaviour(m, b_ok, leaves):
    """Fable: champions that use the difference but score 2 (< 2.5) leave the plateau only while Part
    B's checks pass; on scores alone they do not."""
    counts, b, arms = _analyse_c_inputs(m, b_ok)
    out = m.analyse_c(counts, b, arms)
    assert all(v["leaves_plateau"] is leaves for v in out["arms"].values())


def test_c0_records_its_seeds(m):
    _upto(m, 3)
    seeds = _rec(m, "siblings")["seeds"]
    C = m.REGISTERED["c0"]
    for r in range(len(m.e2_runs())):
        assert seeds[f"ga run{r:02d}"] == C["seed_ga"] + 10 * r and seeds[f"es run{r:02d}"] == C["seed_es"] + 10 * r
