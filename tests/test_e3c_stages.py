"""E3c's formal stages (scripts/e3c.py; PREREGISTRATION.md §5, §12): the order, P-joint's hash check (sabotaged),
the report on synthetic records, the engine freeze in the start markers, and a CPU smoke of every stage."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
TF_GENOMES = ROOT / "runs" / "e3b1" / "genomes" / "tf-run00-final.npz"
FORMAL = ["project", "g-e", "train-smod", "train-sdense", "train-psel", "champions", "evaluate", "report"]


def _fresh(name):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "e3c.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


def _run(stage, *extra):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "e3c.py"), stage, "--smoke", "--device", "cpu", *extra],
                          cwd=ROOT, capture_output=True, text=True, timeout=3600)


def _ge_or_skip():
    """Run the smoke g-e. Off Windows its CPU leg is bitwise against a Windows reference (rule 6; D202), so it may
    not pass there: then the other legs must pass, and the test that needs it is skipped with the reason."""
    r = _run("g-e")
    assert r.returncode == 0, ("g-e", r.stderr[-3000:])
    ge = json.loads((ROOT / "runs" / "e3c-smoke" / "g-e.json").read_text(encoding="utf-8"))
    if not ge["passed"]:
        legs = {k: ge[k] for k in ("cpu", "snapshot_hook", "mazes")}
        assert sys.platform != "win32", legs
        assert ge["snapshot_hook"]["identical"] and ge["mazes"]["passed"] and not ge["cpu"]["passed"], legs
        pytest.skip("g-e's CPU leg is bitwise against a Windows reference (rule 6, D202); training needs g-e")


# ------------------------------------------------------------------ P-joint's hash check (§2, §12: sabotaged)

@pytest.mark.skipif(not TF_GENOMES.exists(), reason="needs E3b-1's T-F genomes, which stay local (D200)")
def test_p_joints_hash_check_refuses_one_changed_byte(tmp_path, monkeypatch):
    m = _fresh("e3c_pj")
    from wormwars.brain import BrainSpec
    from wormwars.connectome import load_connectome
    from wormwars.e3 import assembly as AS
    from wormwars.e4s import arms as A
    cfg = m._formal_cfg()
    cx = dict(AS.context(load_connectome(), A.load_l1(), cfg.brain))
    cx["spec"] = BrainSpec.from_connectome(cx["seed"].ext)
    assert len(m.pjoint_populations(cx, cfg, "final")) == 8  # the real record passes
    rec = json.loads((m.E3B1_DIR / "train-tf.json").read_text(encoding="utf-8"))
    h = rec["runs"][3]["final_sha256"][5]
    rec["runs"][3]["final_sha256"][5] = ("0" if h[0] != "0" else "1") + h[1:]  # one changed character
    (tmp_path / "train-tf.json").write_text(json.dumps(rec), encoding="utf-8")
    monkeypatch.setattr(m, "E3B1_DIR", tmp_path)
    with pytest.raises(SystemExit, match="refuses"):
        m.pjoint_populations(cx, cfg, "final")


# ------------------------------------------------------------------ the report on synthetic records (§7)

def _strain(per_maze, cov=1.0, tm=0.99):
    v = np.asarray(per_maze, dtype=float)
    return {"visits": float(v.mean()), "visits_per_maze": v.tolist(), "coverage": cov, "tour_match": tm,
            "tour_match_best_lag": tm, "legs": float(v.mean()) - 1, "later_leg_rate": 2.0, "unvisited_share": 0.0,
            "round_trip_share": 0.99}


GENS = [0, 5, 25, 299]


def _synthetic(levels: dict, seed_level=5.0, retained=1.0, n_maze=16, rng=None, spread=0.05):
    rng = rng or np.random.default_rng(0)
    arms = {}
    for arm, xs in levels.items():
        intact = [_strain(x + spread * rng.standard_normal(n_maze)) for x in xs]
        removed = [_strain(np.asarray(s["visits_per_maze"]) * retained) for s in intact]
        arms[arm] = {"runs": list(range(len(xs))), "intact": intact, "noses_removed": removed,
                     "turn_offset": [0.5] * len(xs), "K_D_A_at_q0": [0.0] * len(xs)}
    seed_pm = seed_level + 0.3 * rng.standard_normal(n_maze)
    ev = {"arms": arms, "ab_distance": list(rng.uniform(10, 40, n_maze)), "test_ids": list(range(n_maze)),
          "references": {"seed": {"intact": _strain(seed_pm, 0.8, 0.07), "noses_removed": _strain(seed_pm * 0.35, 0.8, 0.05)},
                         "w2_alone": {"intact": _strain(np.full(n_maze, 1.7) + 0.01 * rng.standard_normal(n_maze))},
                         "w2_turn": {"intact": _strain(np.full(n_maze, 5.7))}, "r_shared": {"intact": _strain(np.full(n_maze, 3.0))}}}
    ch = {"learning_curve_references": {"w2_alone": 1.7, "seed": seed_level}, "p_joint_learning_curve": {}}
    trained = {arm: [{"run": i, "completed": True, "learning_curve": [{"generation": g, "validation_mean": (x if g >= 25 else 1.6)}
                                                                      for g in GENS]} for i, x in enumerate(levels[arm])]
               for arm in ("s_mod", "s_dense", "p_sel")}
    trained["checkpoint_generations"] = GENS
    return ev, ch, trained


@pytest.fixture(scope="module")
def m():
    mod = _fresh("e3c_report")
    mod.REGISTERED["formal"]["bootstrap_resamples"] = 300
    return mod


BASE = {"s_mod": [6.7] * 8, "s_dense": [6.72] * 8, "p_sel": [2.3, 5.2, 2.3, 2.2], "p_joint": list(np.linspace(6.0, 8.0, 8))}
A_ = "approximate (model-based): "


def RR(mod, ev, ch, tr, paths=True):
    """The report on synthetic records; the path files are taken as present unless `paths` is False."""
    return mod.report_readings(ev, ch, tr, {}, paths_check=(lambda man, n: True) if paths else (lambda man, n: False))


def test_the_report_reads_coverers_and_no_relevant_difference(m):
    ev, ch, tr = _synthetic(BASE)
    r = RR(m, ev, ch, tr)
    assert r["primary"]["Q1"]["label"] == A_ + "no relevant difference"
    assert r["primary"]["Q1"]["qualifier"]["s_mod"]["coverers"] == 8  # the qualifier sits inside the reading
    assert r["coverage_hypothesis"]["s_arms"] == "high"
    assert r["nose"]["s_mod"]["classes"]["nose-independent"] == 8 and r["p_sel"]["above_floor"] == 1
    assert r["cost_curve"]["arms"]["s_mod"]["w2_plus_1_reached"] == 8
    assert r["cost_curve"]["arms"]["s_mod"]["w2_plus_1_median"] == 25.0
    assert r["nose"]["p_fixed"]["class"] == "nose-dependent" and "maze_differences" in r["nose"]["p_fixed"]


def test_the_report_reads_a_difference_both_ways(m):
    ev, ch, tr = _synthetic({"s_mod": [6.7] * 8, "s_dense": [5.2] * 8, "p_sel": [2.3] * 4, "p_joint": [6.7] * 8})
    r = RR(m, ev, ch, tr)
    assert r["primary"]["Q1"]["label"] == A_ + "modular better, beyond the margin"
    assert r["primary"]["Q1"]["exact"]["label"] == "distributions differ (exact test); observed mean higher for modular"
    ev, ch, tr = _synthetic({"s_mod": [5.2] * 8, "s_dense": [6.7] * 8, "p_sel": [2.3] * 4, "p_joint": [6.7] * 8})
    r = RR(m, ev, ch, tr)
    assert r["primary"]["Q1"]["label"] == A_ + "dense better, beyond the margin"
    assert r["primary"]["Q2"]["label"] == A_ + "engineered initialization and tuning better, beyond the margin"


def test_the_report_reads_within_unresolved_and_unclear(m):
    ev, ch, tr = _synthetic({"s_mod": [6.7] * 8, "s_dense": [6.5] * 8, "p_sel": [2.3] * 4, "p_joint": [6.7] * 8},
                            spread=0.01)
    assert RR(m, ev, ch, tr)["primary"]["Q1"]["label"] == A_ + "modular better, within the margin"
    ev, ch, tr = _synthetic({"s_mod": [6.7] * 8, "s_dense": [6.2] * 8, "p_sel": [2.3] * 4, "p_joint": [6.7] * 8},
                            spread=0.01)
    assert RR(m, ev, ch, tr)["primary"]["Q1"]["label"] == A_ + "modular better, margin unresolved"
    ev, ch, tr = _synthetic({"s_mod": [6.7] * 8, "s_dense": [6.7] * 8, "p_sel": [2.3] * 4,
                             "p_joint": [4.0, 9.0, 5.0, 8.5, 4.5, 9.5, 6.0, 7.5]})
    assert RR(m, ev, ch, tr)["primary"]["Q2"]["label"] == A_ + "unclear"


def test_the_report_counts_failed_runs_and_reads_the_floor(m):
    ev, ch, tr = _synthetic({"s_mod": [6.7] * 7 + [2.0], "s_dense": [6.7] * 8, "p_sel": [2.3] * 4, "p_joint": [6.7] * 8})
    r = RR(m, ev, ch, tr)
    assert r["primary"]["Q1"]["failed_runs"]["s_mod"] == 1 and r["primary"]["Q1"]["failed_runs_present"] is True
    assert r["primary"]["Q1"]["decomposition"]["successful_runs"] == [7, 8]
    ev, ch, tr = _synthetic({"s_mod": [2.0] * 8, "s_dense": [2.1] * 8, "p_sel": [2.0] * 4, "p_joint": [6.7] * 8})
    assert RR(m, ev, ch, tr)["primary"]["Q1"]["label"] == "not read: both at the floor"


def test_the_report_reads_nose_dependence(m):
    ev, ch, tr = _synthetic({"s_mod": [6.7] * 8, "s_dense": [6.7] * 8, "p_sel": [2.3] * 4, "p_joint": [7.0] * 8},
                            retained=0.3)
    r = RR(m, ev, ch, tr)
    assert r["nose"]["s_mod"]["classes"]["nose-dependent"] == 8 and r["coverage_hypothesis"]["coverers"] == "not supported"
    assert r["nose"]["p_fixed"]["retained"] == pytest.approx(0.35, abs=0.01)


# ------------------------------------------------------------------ eligibility (§5; both reviewers, D211)

def test_too_few_runs_are_not_read(m):
    ev, ch, tr = _synthetic({**BASE, "s_mod": [6.7] * 5})
    r = RR(m, ev, ch, tr)
    assert r["primary"]["Q1"]["label"] == "not read: too few runs" and r["primary"]["Q2"]["label"] == "not read: too few runs"
    ev, ch, tr = _synthetic({**BASE, "p_joint": [6.7] * 5})
    r = RR(m, ev, ch, tr)
    assert r["primary"]["Q2"]["label"] == "not read: too few runs" and r["primary"]["Q1"]["read"] is True


def test_an_incomplete_training_run_is_excluded(m):
    ev, ch, tr = _synthetic(BASE)
    tr["s_mod"] = [r for r in tr["s_mod"] if r["run"] != 3]  # run 3 did not complete its training
    r = RR(m, ev, ch, tr)
    assert r["eligibility"]["s_mod"]["excluded"] == [3] and r["primary"]["Q1"]["qualifier"]["s_mod"]["eligible"] == 7


def test_a_missing_checkpoint_curve_is_undefined_not_censored(m):
    ev, ch, tr = _synthetic(BASE)
    tr["s_dense"][2]["learning_curve"] = tr["s_dense"][2]["learning_curve"][:2]
    r = RR(m, ev, ch, tr)
    assert r["cost_curve"]["arms"]["s_dense"]["undefined_runs"] == [2] and len(r["cost_curve"]["arms"]["s_dense"]["runs"]) == 7


def test_a_missing_noses_removed_row_is_undefined_never_dropped(m):
    ev, ch, tr = _synthetic(BASE)
    ev["arms"]["s_mod"]["noses_removed"] = ev["arms"]["s_mod"]["noses_removed"][:7]
    r = RR(m, ev, ch, tr)
    assert len(r["nose"]["s_mod"]["champions"]) == 8 and r["nose"]["s_mod"]["classes"]["undefined"] == 1
    assert r["coverage_hypothesis"]["coverers"] == "mixed"
    del ev["arms"]["s_dense"]["noses_removed"]
    r = RR(m, ev, ch, tr)  # no crash
    assert r["nose"]["s_dense"]["classes"]["undefined"] == 8


def test_one_run_gives_no_loss_interval(m):
    ev, ch, tr = _synthetic({**BASE, "p_sel": [5.0]})
    r = RR(m, ev, ch, tr)
    assert r["nose"]["p_sel"]["loss_ci95"] == "not computed: fewer than 2" and r["nose"]["p_sel"]["no_material_loss"] is None


def test_an_unusable_p_fixed_mean_is_a_registered_outcome(m):
    for bad in (float("inf"), 0.0):
        ev, ch, tr = _synthetic(BASE)
        ev["references"]["seed"]["intact"]["visits_per_maze"] = [bad] * 16
        r = RR(m, ev, ch, tr)
        assert r["primary"]["Q1"]["label"] == "not read: P-fixed's mean is not positive"
        assert r["bootstrap"]["Q1"].startswith("not computed") and r["bootstrap"]["Q2"].startswith("not computed")


def test_the_report_tests_are_not_vacuous(m):
    """Sabotage (rule 9; these tests were written after the report): swapping the arms must change the reading."""
    ev, ch, tr = _synthetic({"s_mod": [6.7] * 8, "s_dense": [5.2] * 8, "p_sel": [2.3] * 4, "p_joint": [6.7] * 8})
    ev["arms"]["s_mod"], ev["arms"]["s_dense"] = ev["arms"]["s_dense"], ev["arms"]["s_mod"]
    assert RR(m, ev, ch, tr)["primary"]["Q1"]["label"] != A_ + "modular better, beyond the margin"


# ------------------------------------------------------------------ the consistency check and the freeze (sabotaged)

def test_the_checkpoint_consistency_refuses_a_mismatch(m):
    same = {0: {"sha256": "a", "validation_counts": [1.0, 2.0]}, 5: {"sha256": "b", "validation_counts": [3.0, 4.0]}}
    assert m.check_consistency(same, same) == {"0": True, "5": True}
    for bad in ({**same, 5: {"sha256": "x", "validation_counts": [3.0, 4.0]}},
                {**same, 5: {"sha256": "b", "validation_counts": [3.0, 4.5]}}, {0: same[0]}):
        with pytest.raises(RuntimeError):
            m.check_consistency(same, bad)


def test_a_formal_stage_refuses_a_changed_engine_or_registered_text(m):
    args = type("A", (), {"smoke": False, "guarded": False})()
    good = {"engine_freeze": {"passes": True, "changed": []},
            "registered_text_sha256": m.REGISTERED["formal"]["registered_text_sha256"]}
    m.require_engine(args, good)
    with pytest.raises(SystemExit, match="engine changed"):
        m.require_engine(args, {**good, "engine_freeze": {"passes": False, "changed": [["M", "wormwars/brain.py"]]}})
    with pytest.raises(SystemExit, match="registered text"):
        m.require_engine(args, {**good, "registered_text_sha256": "0" * 64})
    assert m.registered_text_sha() == m.REGISTERED["formal"]["registered_text_sha256"]  # the working tree's text


@pytest.mark.skipif(not TF_GENOMES.exists(), reason="needs E3b-1's T-F genomes, which stay local (D200)")
def test_p_joints_snapshot_hash_check_refuses_one_changed_byte(tmp_path, monkeypatch):
    m2 = _fresh("e3c_pj124")
    from wormwars.brain import BrainSpec
    from wormwars.connectome import load_connectome
    from wormwars.e3 import assembly as AS
    from wormwars.e4s import arms as A
    cfg = m2._formal_cfg()
    cx = dict(AS.context(load_connectome(), A.load_l1(), cfg.brain))
    cx["spec"] = BrainSpec.from_connectome(cx["seed"].ext)
    rec = json.loads((m2.E3B1_DIR / "train-tf.json").read_text(encoding="utf-8"))
    h = rec["runs"][6]["snapshot_sha256"]["124"][0]
    rec["runs"][6]["snapshot_sha256"]["124"][0] = ("0" if h[0] != "0" else "1") + h[1:]
    (tmp_path / "train-tf.json").write_text(json.dumps(rec), encoding="utf-8")
    monkeypatch.setattr(m2, "E3B1_DIR", tmp_path)
    with pytest.raises(SystemExit, match="refuses"):
        m2.pjoint_populations(cx, cfg, "snap124")


# ------------------------------------------------------------------ the order, the freeze, and the smoke

def test_a_stage_refuses_before_its_prerequisites():
    out = ROOT / "runs" / "e3c-smoke-order"
    r = subprocess.run([sys.executable, "-c", (
        "import sys, importlib.util; sys.argv=['e3c.py','champions','--smoke','--device','cpu'];"
        f"s=importlib.util.spec_from_file_location('m', r'{ROOT / 'scripts' / 'e3c.py'}');m=importlib.util.module_from_spec(s);"
        "s.loader.exec_module(m);"
        f"m.use_smoke(type('A',(),{{'command':'champions'}})());m.EXP=m.OUT=m.Path(r'{out}');m.configure();"
        "m.REGISTERED['cap_gpu_hours']=30.0;m.cmd_champions(type('A',(),{'device':'cpu','smoke':True,'guarded':False,"
        "'rerun':False,'reason':None})())")], cwd=ROOT, capture_output=True, text=True, timeout=600)
    shutil.rmtree(out, ignore_errors=True)
    assert r.returncode != 0 and "has not run" in (r.stderr + r.stdout)


@pytest.mark.slow
@pytest.mark.skipif(not TF_GENOMES.exists(), reason="needs E3b-1's T-F genomes, which stay local (D200)")
def test_a_smoke_of_every_formal_stage():
    for stage in FORMAL:
        if stage == "g-e":
            _ge_or_skip()
            continue
        r = _run(stage)
        assert r.returncode == 0, (stage, r.stdout[-2000:], r.stderr[-4000:])
    out = ROOT / "runs" / "e3c-smoke"
    marker = json.loads((out / "project-started.json").read_text(encoding="utf-8"))
    assert marker["provenance"]["engine_freeze"]["passes"] in (True, False)  # recorded in every formal marker
    assert marker["provenance"]["binding_commit"].startswith("69d7cd5")
    rep = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert rep["outcome"] == "completed" and {"Q1", "Q2"} <= set(rep["readings"]["primary"])
    ch = json.loads((out / "champions.json").read_text(encoding="utf-8"))
    assert set(ch["arms"]) == {"s_mod", "s_dense", "p_sel", "p_joint"} and len(ch["arms"]["p_joint"]["runs"]) == 8
    for st in ("train-smod", "train-sdense", "train-psel"):
        tr = json.loads((out / f"{st}.json").read_text(encoding="utf-8"))
        assert all(all(r["checkpoint_consistency"].values()) for a in tr["arms"].values() for r in a["runs"])
        assert all(len(r["learning_curve"]) == len(tr["checkpoint_generations"]) for a in tr["arms"].values() for r in a["runs"])
    # the engine paths E3c's freeze forbids changing: modified (not added) since the binding commit. E3d (D226) changed
    # wormwars/config.py and maze_world.py, so from then on the freeze must fail, and E3c's formal stages refuse
    import subprocess
    diff = subprocess.run(["git", "diff", "--name-status", "69d7cd5", "HEAD", "--", "wormwars", "configs", "requirements.txt"],
                          capture_output=True, text=True, cwd=ROOT).stdout.splitlines()
    modified = sorted(line.split("	", 1)[1] for line in diff if line.strip() and not line.startswith("A"))
    for st in FORMAL:  # every formal marker carries the engine freeze and the registered text's hash
        mk = json.loads((out / f"{st}-started.json").read_text(encoding="utf-8"))
        assert mk["provenance"]["engine_freeze"]["passes"] is (not modified)
        assert sorted(p for _, p in mk["provenance"]["engine_freeze"]["changed"]) == modified
        assert mk["provenance"]["registered_text_sha256"] == "553f253d260b80638d9ef72d4654f2ef78372e960ea31d62d04345098d8c3397"
    # W2-turn chosen on the validation block only; P-joint's points are the logged generation-bests (§12)
    assert ch["w2_turn"]["block"] == "validation" and ch["w2_turn"]["ids"] == list(range(8000, 8002))
    tf = json.loads((ROOT / "experiments" / "E3-ab-organism" / "E3b-1" / "train-tf.json").read_text(encoding="utf-8"))
    for gen in ("124", "299"):
        for r in tf["runs"]:
            assert ch["p_joint_learning_curve"][gen][str(r["run"])]["sha256"] == r["log"][int(gen)]["best_sha256"]
    ev = json.loads((out / "evaluate.json").read_text(encoding="utf-8"))
    for arm in ("s_mod", "p_joint"):  # every wey's path, in both conditions, saved and hashed
        for cond in ("intact", "noses_removed"):
            f = ev["arms"][arm]["paths_files"][cond]
            z = np.load(ROOT / f["path"], allow_pickle=False)
            assert list(z["offsets"].shape[:2]) == [len(ev["arms"][arm]["runs"]) * 4, 8]


@pytest.mark.slow
def test_a_stopped_training_keeps_its_populations_and_its_rerun_reuses_them(monkeypatch):
    """Both reviewers and Amendment 1: populations are saved before the checkpoint plays; a rerun of a stage whose
    training completed reuses them (hash-checked) and redoes only the plays."""
    r = _run("project")
    assert r.returncode == 0, ("project", r.stderr[-3000:])
    _ge_or_skip()
    m = _fresh("e3c_rerun")
    m.use_smoke(type("A", (), {"command": "train-smod"})())
    m.REGISTERED["cap_gpu_hours"] = 30.0
    real_play = m.MR.play_batch

    def boom(*a, **k):
        raise RuntimeError("injected: the checkpoint plays fail")

    monkeypatch.setattr(m.MR, "play_batch", boom)
    args = type("A", (), {"device": "cpu", "smoke": True, "guarded": False, "rerun": False, "reason": None})()
    with pytest.raises(RuntimeError, match="injected"):
        m.cmd_train("train-smod")(args)
    rec = json.loads(m.E.record_path("train-smod").read_text(encoding="utf-8"))
    assert rec["outcome"] != "completed" and rec["arms"]["s_mod"]["training"]["complete"] is True
    for r in rec["arms"]["s_mod"]["runs"]:
        assert all((ROOT / f["path"]).exists() for f in r["genome_files"])
    monkeypatch.setattr(m.MR, "play_batch", real_play)

    def no_training(*a, **k):
        raise AssertionError("the rerun retrained instead of reusing the saved populations")

    monkeypatch.setattr(m.EV, "evolve_batch", no_training)
    rerun = type("A", (), {"device": "cpu", "smoke": True, "guarded": False, "rerun": True, "reason": "test: plays failed"})()
    m.cmd_train("train-smod")(rerun)
    rec = json.loads(m.E.record_path("train-smod").read_text(encoding="utf-8"))
    entry = rec["arms"]["s_mod"]
    assert rec["outcome"] == "completed" and entry["training_reused_from_attempt_1"] is True
    assert all(len(r["learning_curve"]) == len(rec["checkpoint_generations"]) for r in entry["runs"])


@pytest.mark.parametrize("stage", ["train-smod", "train-psel", "report"])
def test_formal_stages_refuse_before_their_prerequisites(stage):
    out = ROOT / "runs" / f"e3c-smoke-order-{stage}"
    r = subprocess.run([sys.executable, "-c", (
        "import sys, importlib.util; "
        f"s=importlib.util.spec_from_file_location('m', r'{ROOT / 'scripts' / 'e3c.py'}');m=importlib.util.module_from_spec(s);"
        "s.loader.exec_module(m);"
        f"m.use_smoke(type('A',(),{{'command':'{stage}'}})());m.EXP=m.OUT=m.Path(r'{out}');m.configure();"
        "m.REGISTERED['cap_gpu_hours']=30.0;"
        f"m.COMMANDS['{stage}'](type('A',(),{{'device':'cpu','smoke':True,'guarded':False,'rerun':False,'reason':None}})())")],
        cwd=ROOT, capture_output=True, text=True, timeout=600)
    shutil.rmtree(out, ignore_errors=True)
    assert r.returncode != 0 and "has not run" in (r.stderr + r.stdout)



# ------------------------------------------------------------------ the recheck (both reviewers, D212)

def test_an_unread_contrast_enters_holm_with_p_1_and_nothing_fictitious(m):
    from wormwars.e3 import e3c_stats as S
    ev, ch, tr = _synthetic(BASE)
    full = RR(m, ev, ch, tr)["primary"]["Q2"]  # Q1 readable
    a = ev["arms"]["s_dense"]
    for key in ("runs", "intact", "noses_removed", "turn_offset", "K_D_A_at_q0"):
        a[key] = a[key][:5]  # the same data, S-dense cut to 5 runs
    tr["s_dense"] = tr["s_dense"][:5]
    r = RR(m, ev, ch, tr)
    q2 = r["primary"]["Q2"]
    assert r["primary"]["Q1"]["label"] == "not read: too few runs"
    assert q2["p_holm"] == pytest.approx(min(1.0, 2 * q2["p"]))  # Q1 enters Holm with p = 1 (Astra's 0.552)
    for k in ("estimate", "lo", "hi", "level"):
        assert q2[k] == pytest.approx(full[k])
    assert q2["exact"]["p"] == pytest.approx(full["exact"]["p"])


def test_truncated_vectors_are_ineligible(m):
    ev, ch, tr = _synthetic(BASE)
    for arm in ev["arms"].values():
        for x in arm["intact"]:
            x["visits_per_maze"] = x["visits_per_maze"][:15]
    r = RR(m, ev, ch, tr)
    assert r["eligibility"]["s_mod"]["eligible"] == 0 and r["primary"]["Q1"]["label"] == "not read: too few runs"


def test_missing_paths_make_section_7_3_undefined_but_keep_primary_eligibility(m):
    ev, ch, tr = _synthetic(BASE)
    r = RR(m, ev, ch, tr, paths=False)
    assert r["nose"]["s_mod"]["classes"]["undefined"] == 8 and r["coverage_hypothesis"]["coverers"] == "mixed"
    assert r["primary"]["Q1"]["read"] is True and r["nose"]["p_fixed"]["class"] == "undefined"


def test_missing_references_are_registered_outcomes(m):
    ev, ch, tr = _synthetic(BASE)
    del ev["references"]["seed"]
    assert RR(m, ev, ch, tr)["primary"]["Q1"]["label"] == "not read: P-fixed's play is unavailable"
    ev, ch, tr = _synthetic(BASE)
    del ev["references"]["w2_alone"]
    assert RR(m, ev, ch, tr)["primary"]["Q2"]["label"] == "not read: W2 alone's play is unavailable"
    ev, ch, tr = _synthetic(BASE)
    r = RR(m, ev, {}, tr)  # a champions record without its learning-curve references
    assert r["cost_curve"]["fisher_s_mod_vs_s_dense"].startswith("not computed")


def test_a_salvage_shaped_evaluate_record_is_reported(m):
    ev, ch, tr = _synthetic(BASE)
    salvage = {"arms": {"s_mod": ev["arms"]["s_mod"]}, "references": {"seed": {"intact": ev["references"]["seed"]["intact"]}},
               "test_ids": ev["test_ids"], "ab_distance": ev["ab_distance"]}
    r = RR(m, salvage, ch, tr)
    assert r["primary"]["Q1"]["label"].startswith("not read") and r["nose"]["p_fixed"]["class"] == "undefined"
    assert r["eligibility"]["s_dense"]["evaluated"] == 0


def test_a_report_with_no_evaluate_record(m):
    rep = m.report_from({"project": {"admission": {"plan": {}}}, "train-smod": None, "train-sdense": None,
                         "train-psel": None, "champions": None, "evaluate": None})
    assert rep["readings"]["primary"]["Q1"]["label"] == "not read: evaluate did not run"
    assert rep["inputs"]["evaluate"] == "never started"


def test_the_bootstrap_against_a_direct_computation(m):
    ev, ch, tr = _synthetic(BASE)
    r = RR(m, ev, ch, tr)
    seed_pm = np.asarray(ev["references"]["seed"]["intact"]["visits_per_maze"])
    pm = {a: np.array([x["visits_per_maze"] for x in ev["arms"][a]["intact"]]) for a in ("s_mod", "s_dense")}
    rng = np.random.default_rng(20_261_007)  # §7.1's registered seed
    vals = []
    for _ in range(m.REGISTERED["formal"]["bootstrap_resamples"]):
        idx = rng.integers(0, 16, 16)
        sm = seed_pm[idx].mean()
        vals.append(((pm["s_mod"][:, idx].mean(1) - sm) / sm).mean() - ((pm["s_dense"][:, idx].mean(1) - sm) / sm).mean())
    assert r["bootstrap"]["Q1"]["lo"] == pytest.approx(np.percentile(vals, 2.5))
    assert r["bootstrap"]["Q1"]["hi"] == pytest.approx(np.percentile(vals, 97.5))


@pytest.mark.slow
@pytest.mark.skipif(not TF_GENOMES.exists(), reason="needs E3b-1's T-F genomes, which stay local (D200)")
def test_interruptions_keep_completed_work_and_a_mismatch_stays_refused(monkeypatch):
    """Both reviewers (D212): a consistency mismatch refuses in attempt 1 and again in a rerun that reuses the
    training; champions and evaluate persist each completed chunk; a stage runs once; the training ids are
    pre-flighted."""
    r = _run("project")
    assert r.returncode == 0, ("project", r.stderr[-3000:])
    _ge_or_skip()
    once = _fresh("e3c_once")  # the smoke's own reset is skipped: a completed stage runs once
    once.use_smoke(type("A", (), {"command": "pilot"})())  # clears only the pilot smoke's records
    once.REGISTERED["cap_gpu_hours"] = 30.0
    with pytest.raises(SystemExit, match="runs once"):
        once.cmd_project(type("A", (), {"device": "cpu", "smoke": True, "guarded": False, "rerun": False, "reason": None})())
    m = _fresh("e3c_interrupt")
    m.use_smoke(type("A", (), {"command": "train-smod"})())
    m.REGISTERED["cap_gpu_hours"] = 30.0
    real = m.MR.play_batch

    def shifted(*a, **k):  # the post-hoc plays differ from the in-loop ones
        ev = real(*a, **k)
        ev["visits"] = ev["visits"] + 1
        return ev

    monkeypatch.setattr(m.MR, "play_batch", shifted)
    args = type("A", (), {"device": "cpu", "smoke": True, "guarded": False, "rerun": False, "reason": None})()
    with pytest.raises(RuntimeError, match="differs from the in-loop"):
        m.cmd_train("train-smod")(args)
    rerun = type("A", (), {"device": "cpu", "smoke": True, "guarded": False, "rerun": True, "reason": "test: mismatch"})()
    with pytest.raises(RuntimeError, match="differs from the in-loop"):
        m.cmd_train("train-smod")(rerun)  # the reused training is checked again: the mismatch stays refused
    rec = json.loads(m.E.record_path("train-smod").read_text(encoding="utf-8"))
    assert rec["arms"]["s_mod"]["training_reused_from_attempt_1"] is True
    monkeypatch.setattr(m.MR, "play_batch", real)
    for stage in ("train-smod", "train-sdense", "train-psel"):  # a clean slate, then clean training
        r = _run(stage)
        assert r.returncode == 0, (stage, r.stderr[-3000:])
    tr = json.loads((ROOT / "runs" / "e3c-smoke" / "train-smod.json").read_text(encoding="utf-8"))
    G, W = 12, 2
    learn = set(range(8002, 8004))
    ids_ = {int(x) for rr in tr["arms"]["s_mod"]["runs"] for g in range(G)
            for x in m.EV.train_ids(rr["seed"], g, W, 9_200_000, 1000)}
    assert tr["mazes"]["checked"] == len(learn | ids_)  # every training id pre-flighted
    # champions: a stop before the second validation chunk keeps the first
    m2 = _fresh("e3c_champ")
    m2.use_smoke(type("A", (), {"command": "champions"})())
    m2.REGISTERED["cap_gpu_hours"] = 30.0
    calls = {"n": 0}
    real2 = m2.MR.play_batch

    def second_fails(*a, **k):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("injected: the second validation chunk")
        return real2(*a, **k)

    monkeypatch.setattr(m2.MR, "play_batch", second_fails)
    with pytest.raises(RuntimeError, match="injected"):
        m2.cmd_champions(args)
    rec = json.loads(m2.E.record_path("champions").read_text(encoding="utf-8"))
    assert len(rec["arms"]["s_mod"]["runs"]) == 1 and m2.champion_file("s_mod", rec["arms"]["s_mod"]["runs"][0]["run"]).exists()


def test_the_real_path_validator(tmp_path, monkeypatch):
    """Astra (D213): the writer's recorded shape and the validator's check agree; altered or missing files fail."""
    m3 = _fresh("e3c_paths")
    monkeypatch.setattr(m3, "ROOT", tmp_path)
    monkeypatch.setattr(m3, "OUT", tmp_path / "out")
    paths = {"cells": np.arange(6, dtype=np.int16), "ticks": np.arange(6, dtype=np.int32),
             "offsets": np.zeros((3, 8, 2), dtype=np.int64), "world_ids": np.arange(3), "strain_of_world": np.zeros(3)}
    man = m3.save_paths("s_mod", "intact", paths)
    assert m3.paths_ok(man, 3) is True
    assert m3.paths_ok(man, 4) is False and m3.paths_ok(None, 3) is False
    m3.paths_file("s_mod", "intact").write_bytes(b"altered")
    assert m3.paths_ok(man, 3) is False



# ------------------------------------------------------------------ the second recheck (Astra, D214)

def test_a_report_without_evaluate_keeps_the_cost_curve(m):
    ev, ch, tr = _synthetic(BASE)
    earlier = {"project": {}, "evaluate": None, "champions": ch,
               "train-smod": {"arms": {"s_mod": {"runs": tr["s_mod"]}}},
               "train-sdense": {"arms": {"s_dense": {"runs": tr["s_dense"]}}},
               "train-psel": {"arms": {"p_sel": {"runs": tr["p_sel"]}}}}
    monkey = m.formal_gens
    m.formal_gens = lambda: GENS
    try:
        rep = m.report_from(earlier)
    finally:
        m.formal_gens = monkey
    r = rep["readings"]
    assert r["primary"]["Q1"]["label"] == "not read: evaluate did not run"
    assert r["cost_curve"]["arms"]["s_mod"]["w2_plus_1_reached"] == 8 and r["cost_curve"]["fisher_holm"] is not None


def test_an_atomic_save_keeps_the_earlier_file(tmp_path, monkeypatch):
    m4 = _fresh("e3c_atomic")
    target = tmp_path / "x.npz"
    target.write_bytes(b"earlier")

    def broken(path, genome, **kw):
        Path(path).write_bytes(b"partial")
        raise OSError("injected: the write was interrupted")

    monkeypatch.setattr(m4, "save_population", broken)
    with pytest.raises(OSError):
        m4.save_atomic(target, None)
    assert target.read_bytes() == b"earlier" and not (tmp_path / "x.tmp.npz").exists()


@pytest.mark.slow
@pytest.mark.skipif(not TF_GENOMES.exists(), reason="needs E3b-1's T-F genomes, which stay local (D200)")
def test_the_cap_and_the_last_chunks(monkeypatch):
    """Astra (D214): a stage refused at the cap before it starts leaves no record and no marker (the report reads it
    as never started); a cap reached at the frame's final check keeps the whole result as salvage; champions keeps
    P-joint's first learning point when the second play fails; a corrupt saved archive makes a rerun train again."""
    r = _run("project")
    assert r.returncode == 0, ("project", r.stderr[-3000:])
    _ge_or_skip()
    for stage in ("train-smod", "train-sdense", "train-psel"):
        r = _run(stage)
        assert r.returncode == 0, (stage, r.stderr[-3000:])
    args = type("A", (), {"device": "cpu", "smoke": True, "guarded": False, "rerun": False, "reason": None})()
    # the final cap check
    m = _fresh("e3c_cap_final")
    m.use_smoke(type("A", (), {"command": "champions"})())
    m.REGISTERED["cap_gpu_hours"] = 30.0
    flag = {"done": False}

    class Clock:
        def check(self):
            if flag["done"]:
                raise m.E.reg.CapReached("injected: the cap at the final check")

        def spent_hours(self):
            return 0.0

    real_write = m.E.write_atomic

    def write(path, doc):
        real_write(path, doc)
        if Path(path).name == "champions-grafted.json":
            flag["done"] = True

    monkeypatch.setattr(m.E, "clock", lambda: Clock())
    monkeypatch.setattr(m.E, "write_atomic", write)
    with pytest.raises(SystemExit):
        m.cmd_champions(args)
    rec = json.loads(m.E.record_path("champions").read_text(encoding="utf-8"))
    assert rec["outcome"] == m.E.OUTCOMES["cap"] and {"w2_turn", "learning_curve_references", "arms"} <= set(rec)
    assert len(rec["arms"]["p_joint"]["runs"]) == 8
    # P-joint's second learning point fails: the first is kept
    m2 = _fresh("e3c_pj_points")
    m2.use_smoke(type("A", (), {"command": "champions"})())
    m2.REGISTERED["cap_gpu_hours"] = 30.0
    n_val = sum(len(json.loads((ROOT / "runs" / "e3c-smoke" / f"{st}.json").read_text(encoding="utf-8"))["arms"][a]["runs"])
                for st, a in (("train-smod", "s_mod"), ("train-sdense", "s_dense"), ("train-psel", "p_sel"))) + 8
    calls = {"n": 0}
    real = m2.MR.play_batch

    def fail_at_299(*a, **k):
        calls["n"] += 1
        if calls["n"] == n_val + 2 + 1:  # the validation chunks, W2-turn, P-joint at 124, then at 299
            raise RuntimeError("injected: P-joint's 299 play")
        return real(*a, **k)

    monkeypatch.setattr(m2.MR, "play_batch", fail_at_299)
    with pytest.raises(RuntimeError, match="injected"):
        m2.cmd_champions(args)
    rec = json.loads(m2.E.record_path("champions").read_text(encoding="utf-8"))
    assert "124" in rec["p_joint_learning_curve"] and "299" not in rec["p_joint_learning_curve"] and "w2_turn" in rec
    monkeypatch.setattr(m2.MR, "play_batch", real)
    # a refusal at the cap before the stage starts (after a clean champions run, so only the cap can refuse)
    r = _run("champions")
    assert r.returncode == 0, r.stderr[-3000:]
    m3 = _fresh("e3c_cap_pre")
    m3.use_smoke(type("A", (), {"command": "evaluate"})())
    m3.REGISTERED["cap_gpu_hours"] = 0.0
    with pytest.raises(SystemExit, match="did not start"):
        m3.cmd_evaluate(args)
    assert not m3.E.record_path("evaluate").exists() and not m3.E.marker_path("evaluate").exists()
    # a corrupt saved archive: the rerun trains again (Amendment 1, point 3)
    m4 = _fresh("e3c_corrupt")
    m4.use_smoke(type("A", (), {"command": "train-smod"})())
    m4.REGISTERED["cap_gpu_hours"] = 30.0
    real4 = m4.MR.play_batch

    def boom(*a, **k):
        raise RuntimeError("injected: the checkpoint plays fail")

    monkeypatch.setattr(m4.MR, "play_batch", boom)
    with pytest.raises(RuntimeError, match="injected"):
        m4.cmd_train("train-smod")(args)
    monkeypatch.setattr(m4.MR, "play_batch", real4)
    rec = json.loads(m4.E.record_path("train-smod").read_text(encoding="utf-8"))
    f = ROOT / rec["arms"]["s_mod"]["runs"][0]["genome_files"][0]["path"]
    f.write_bytes(f.read_bytes()[:100])  # truncated: not a readable archive
    rerun = type("A", (), {"device": "cpu", "smoke": True, "guarded": False, "rerun": True, "reason": "test: corrupt"})()
    m4.cmd_train("train-smod")(rerun)
    rec = json.loads(m4.E.record_path("train-smod").read_text(encoding="utf-8"))
    entry = rec["arms"]["s_mod"]
    for f in (ROOT / "runs" / "e3c-smoke" / "genomes").glob("*-attempt1.npz"):
        f.unlink()  # the deliberately truncated archive must not outlive this test (other tests read every .npz)
    assert rec["outcome"] == "completed" and "reuse_refused" in entry and "training_reused_from_attempt_1" not in entry



# ------------------------------------------------------------------ the final recheck (D215)

@pytest.mark.slow
@pytest.mark.skipif(not TF_GENOMES.exists(), reason="needs E3b-1's T-F genomes, which stay local (D200)")
def test_a_failed_champion_save_leaves_a_consistent_record(monkeypatch):
    """Astra: a save that fails adds no record entry, so the record and the files agree and evaluate can load every
    listed champion; a file written just before a kill is merely unreferenced."""
    r = _run("project")
    assert r.returncode == 0, ("project", r.stderr[-3000:])
    _ge_or_skip()
    for stage in ("train-smod", "train-sdense", "train-psel"):
        r = _run(stage)
        assert r.returncode == 0, (stage, r.stderr[-3000:])
    m = _fresh("e3c_champ_save")
    m.use_smoke(type("A", (), {"command": "champions"})())
    m.REGISTERED["cap_gpu_hours"] = 30.0
    real, calls = m.save_atomic, {"n": 0}

    def second_fails(path, genome, **kw):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("injected: the second champion's save")
        return real(path, genome, **kw)

    monkeypatch.setattr(m, "save_atomic", second_fails)
    args = type("A", (), {"device": "cpu", "smoke": True, "guarded": False, "rerun": False, "reason": None})()
    with pytest.raises(OSError, match="injected"):
        m.cmd_champions(args)
    rec = json.loads(m.E.record_path("champions").read_text(encoding="utf-8"))
    listed = rec["arms"]["s_mod"]["runs"]
    assert len(listed) == 1  # the failed save added no entry
    from wormwars.brain import BrainSpec
    from wormwars.connectome import load_connectome
    from wormwars.e3 import assembly as AS
    from wormwars.e4s import arms as A
    cfg = m._formal_cfg()
    cx = AS.context(load_connectome(), A.load_l1(), cfg.brain)
    g = m.load_champions("s_mod", listed, BrainSpec.from_connectome(cx["seed"].ext), cfg.brain)
    assert g.n_strains == 1


def test_after_the_cap_a_crashed_or_killed_stage_is_read_as_final(tmp_path, monkeypatch):
    """Fable: once the cap is exhausted, a crashed stage (no rerun possible) is read from its stopped record, and a
    killed one from its partial record; before that, both still refuse."""
    m = _fresh("e3c_cap_final_read")
    m.use_smoke(type("A", (), {"command": "pilot"})())
    monkeypatch.setattr(m.E, "EXP", tmp_path)
    args = type("A", (), {"smoke": True, "guarded": False})()
    (tmp_path / "train-smod.json").write_text(json.dumps({"outcome": m.E.OUTCOMES["stopped"], "arms": {"s_mod": {}},
                                                         "provenance_at_start": {"git_commit": "x"}}), encoding="utf-8")
    (tmp_path / "train-psel-started.json").write_text(json.dumps({"provenance": {"git_commit": "x"}}), encoding="utf-8")
    (tmp_path / "train-psel-partial.json").write_text(json.dumps({"arms": {"p_sel": {"runs": []}}}), encoding="utf-8")
    monkeypatch.setattr(m, "cap_exhausted", lambda: False)
    for st in ("train-smod", "train-psel"):
        with pytest.raises(SystemExit):
            m.require_record(args, {}, st, stopped_ok=True)
    monkeypatch.setattr(m, "cap_exhausted", lambda: True)
    assert m.require_record(args, {}, "train-smod", stopped_ok=True)["arms"] == {"s_mod": {}}
    got = m.require_record(args, {}, "train-psel", stopped_ok=True)
    assert got["arms"] == {"p_sel": {"runs": []}} and got["outcome"].startswith("killed")



def test_a_killed_stage_read_after_the_cap_passes_the_usual_guards(tmp_path, monkeypatch):
    """Both reviewers (D216): the killed route checks the committed inputs, the code and the environment from the
    start marker's provenance; a killed rerun goes the frame's way; a kill before any partial gives an empty record."""
    m = _fresh("e3c_killed_guards")
    m.use_smoke(type("A", (), {"command": "pilot"})())
    monkeypatch.setattr(m.E, "EXP", tmp_path)
    monkeypatch.setattr(m, "cap_exhausted", lambda: True)
    (tmp_path / "train-psel-started.json").write_text(json.dumps({"provenance": {"git_commit": "abc"}}), encoding="utf-8")
    (tmp_path / "train-psel-partial.json").write_text(json.dumps({"arms": {"p_sel": {"runs": []}}}), encoding="utf-8")
    formal = type("A", (), {"smoke": False, "guarded": False})()
    seen = []
    monkeypatch.setattr(m.E, "require_committed", lambda p: seen.append(Path(p).name))
    monkeypatch.setattr(m.E.reg, "require_same_code", lambda c, g: seen.append(("code", c)))
    monkeypatch.setattr(m.E.reg, "require_same_env", lambda a, b: seen.append("env"))
    got = m.require_record(formal, {}, "train-psel", stopped_ok=True)
    assert got["outcome"].startswith("killed") and got["provenance_at_start"] == {"git_commit": "abc"}
    assert {"train-psel-started.json", "train-psel-partial.json"} <= set(x for x in seen if isinstance(x, str))
    assert ("code", "abc") in seen and "env" in seen

    def uncommitted(p):
        raise SystemExit(f"{Path(p).name} must be committed")

    monkeypatch.setattr(m.E, "require_committed", uncommitted)
    with pytest.raises(SystemExit, match="committed"):
        m.require_record(formal, {}, "train-psel", stopped_ok=True)
    monkeypatch.setattr(m.E, "require_committed", lambda p: None)

    def changed(c, g):
        raise SystemExit("code changed")

    monkeypatch.setattr(m.E.reg, "require_same_code", changed)
    with pytest.raises(SystemExit, match="code changed"):
        m.require_record(formal, {}, "train-psel", stopped_ok=True)
    monkeypatch.setattr(m.E.reg, "require_same_code", lambda c, g: None)
    monkeypatch.setattr(m.E, "rerun_state", lambda st: "used")  # a killed rerun: the frame's own route
    with pytest.raises(SystemExit):
        m.require_record(formal, {}, "train-psel", stopped_ok=True)
    monkeypatch.setattr(m.E, "rerun_state", lambda st: "setup")  # an interrupted rerun setup: the frame's route too
    with pytest.raises(SystemExit):
        m.require_record(formal, {}, "train-psel", stopped_ok=True)
    monkeypatch.setattr(m.E, "rerun_state", lambda st: "none")
    (tmp_path / "train-psel-partial.json").unlink()
    got = m.require_record(formal, {}, "train-psel", stopped_ok=True)
    assert got["outcome"].startswith("killed before") and "arms" not in got
