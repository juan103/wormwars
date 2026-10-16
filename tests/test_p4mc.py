"""03mc's runner (`scripts/p4mc.py`) and report (`wormwars/exp03/mc_report.py`), on the CPU without drawing a graph.

The runner was written before these tests (D289); each test here was also run against a sabotaged copy of the
behaviour it checks, and failed there."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def r():
    spec = importlib.util.spec_from_file_location("p4mc_test", ROOT / "scripts" / "p4mc.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.use_smoke(False)
    return mod


@pytest.fixture(scope="module")
def con():
    from wormwars.connectome import load_connectome
    return load_connectome()


def fake_names(k=128):
    from wormwars.exp03 import mc
    return {e: [f"{e}-{9_000_000 + 10_000 * j + i}" for i in range(k)] for j, e in enumerate(mc.ENSEMBLES)}


def test_the_plan_is_in_the_registered_order_and_size(r, con):
    names = fake_names()
    u = r.plan(con, names)
    ids = [x["id"] for x in u]
    assert len(ids) == len(set(ids))
    assert ids[:2] == ["N2/long", "N2/gaps"]
    first_qb, first_graph = ids.index("qb/0/intact"), ids.index(f"graph/{names['SH-route'][0]}/long")
    assert all(i.startswith("perm/") for i in ids[2:first_qb]) and len(ids[2:first_qb]) == 256
    assert ids[first_qb + 1] == "qb/0/empty"
    assert sum(i.startswith("qb/") for i in ids) == 32 * 4 + 1
    # the ensembles interleave in the registered order, so a stop leaves them balanced
    g = [i for i in ids if i.startswith("graph/") and i.endswith("/long")]
    assert [x.split("/")[1].rsplit("-", 1)[0] for x in g[:5]] == list(r.ORDER)
    assert len(g) == 640 and sum(i.startswith("graph/") for i in ids) == 1280
    # the primary units are exactly N2's batch 0, the permutations, Q-B's batches and the ensembles, and every one
    # comes before every secondary
    assert all(x["primary"] == (x["id"].split("/")[0] in ("N2", "perm", "qb", "graph")) for x in u)
    last_primary = max(k for k, x in enumerate(u) if x["primary"])
    assert all(not x["primary"] for x in u[last_primary + 1:]) and all(x["primary"] for x in u[:last_primary + 1])
    assert sum(i.startswith("pair/") for i in ids) == 93
    assert sum(i.startswith("fact/") for i in ids) == 32 * 3
    assert sum(i.startswith("null/") for i in ids) == 5 * 32 * 3
    assert "pair/RIA" not in ids and "pair/RMDD" not in ids


def test_the_controls_are_in_the_screen(r, con):
    screen = r.screen_pairs(con)
    assert len(screen) == 95
    for ks in r.REGISTERED["controls"].values():
        assert set(ks) <= set(screen)


def test_the_deletions_are_the_named_pairs(r, con):
    names = list(con.names)
    assert sorted(names[i] for i in r.deletion_lists(con, "RIA")) == ["RIAL", "RIAR"]
    assert sorted(names[i] for i in r.deletion_lists(con, "both")) == ["AIYL", "AIYR", "RIAL", "RIAR"]
    assert r.deletion_lists(con, "empty") == [] and r.deletion_lists(con, None) == []


def test_the_prereg_may_only_grow(r):
    r.prereg_append_only(b"bound text\n", b"bound text\n\n## Amendment 1\n")
    r.prereg_append_only(b"bound text\r\n", b"bound text\n")  # line endings normalised
    with pytest.raises(SystemExit):
        r.prereg_append_only(b"bound text\n", b"bound texts\n")


def test_a_resume_refuses_a_changed_input_or_plan(r):
    r.use_smoke(True)  # the code and environment comparison is formal-only; the rest is tested here
    try:
        units = [{"id": "a", "seed_name": "N2"}, {"id": "b", "seed_name": "N2"}]
        base = lambda: {"attempts": [{"provenance": {}, "outcome": "stopped: cap"}], "inputs": {"x": "1"},  # noqa: E731
                        "plan": [dict(u) for u in units], "units": {}, "registered": r.REGISTERED, "smoke": True}
        r.check_resume(base(), {}, {"x": "1"}, units, verify_arrays=False)
        with pytest.raises(SystemExit):
            r.check_resume(base(), {}, {"x": "2"}, units, verify_arrays=False)
        with pytest.raises(SystemExit):
            r.check_resume(base(), {}, {"x": "1"}, units[::-1], verify_arrays=False)
        changed = [dict(units[0], seed_name="N2#1"), units[1]]  # Astra: the same ids, another genome stream
        with pytest.raises(SystemExit):
            r.check_resume(base(), {}, {"x": "1"}, changed, verify_arrays=False)
        d = base()
        d["registered"] = {**r.REGISTERED, "follow": 200}
        with pytest.raises(SystemExit):
            r.check_resume(d, {}, {"x": "1"}, units, verify_arrays=False)
        d = base()
        d["smoke"] = False
        with pytest.raises(SystemExit):
            r.check_resume(d, {}, {"x": "1"}, units, verify_arrays=False)
    finally:
        r.use_smoke(False)


def test_the_empty_deletion_stop_survives_a_resume(r):
    """Fable, Astra (prereg review): the stopped unit was recorded, so a rerun skipped it and went on."""
    r.use_smoke(True)
    try:
        units = [{"id": "qb/0/intact"}, {"id": "qb/0/empty"}]
        doc = {"attempts": [{"provenance": {}, "outcome": r.TERMINAL}], "inputs": {}, "plan": units,
               "registered": r.REGISTERED, "smoke": True,
               "units": {"qb/0/intact": {"numerator": 0.1, "denominator": 0.2},
                         "qb/0/empty": {"numerator": 0.1, "denominator": 0.3}}}
        with pytest.raises(SystemExit, match="empty deletion"):
            r.check_resume(doc, {}, {}, units, verify_arrays=False)
        lost = {**doc, "units": {"qb/0/intact": doc["units"]["qb/0/intact"]}}  # the outcome alone refuses
        with pytest.raises(SystemExit, match="empty deletion"):
            r.check_resume(lost, {}, {}, units, verify_arrays=False)
        doc["attempts"][0]["outcome"] = "stopped: cap"  # even if the outcome were lost, the records refuse
        with pytest.raises(SystemExit, match="empty deletion"):
            r.check_resume(doc, {}, {}, units, verify_arrays=False)
    finally:
        r.use_smoke(False)


def test_the_empty_deletion_must_reproduce_exactly(r):
    it = {"numerator": 0.1, "denominator": 0.2}
    assert r.empty_reproduces({"numerator": 0.1, "denominator": 0.2}, it)
    assert not r.empty_reproduces({"numerator": 0.1, "denominator": 0.2 + 1e-12}, it)


def fake_h(n=64, ticks=(0, 5, 10, 20, 30, 40, 50, 100, 300), scale=1.0, seed=0):
    rng = np.random.default_rng(seed)
    final = rng.normal(0, 0.1, n) * scale
    steady = rng.normal(0, 0.2, n) * scale
    decay = np.exp(-np.asarray(ticks)[:, None] / 40.0)
    return {"raw_turn": {"final": final, "steady_contrast": steady, "after": final},
            "pre_turn": {"final": 2 * final, "steady_contrast": 2 * steady}, "ticks": list(ticks),
            "diff": decay * final[None, :], "end_state_range": np.full(n, 1e-5), "hold_state_range": np.full(n, 1e-5),
            "slope_hold": np.full(n, 0.5), "slope_ramp": np.full(n, 0.6)}


def test_summaries_hold_shares_to_validity(r):
    rec, arr = r.summarise({"id": "x", "kind": "long"}, fake_h())
    assert rec["valid"] and rec["share"]["30"] == pytest.approx(np.exp(-30 / 40), rel=1e-6)
    assert arr["diff"].shape == (9, 64)
    bad, _ = r.summarise({"id": "y", "kind": "long"}, fake_h(scale=1e-6))  # a denominator below the floor
    assert not bad["valid"] and bad["share"]["30"] is None


# ----------------------------------------------------------------------------- the report, on synthetic records

def synthetic(n2_gap_change, n2_share, k=6, perms=4, batches=2, seed=1, controls=False):
    """A complete synthetic measurement set: N2 and k graphs per ensemble, permutations, Q-B batches."""
    from wormwars.exp03 import mc
    rng = np.random.default_rng(seed)
    units, arrays, plan = {}, {}, []
    n = 400

    def put(uid, final, steady, long=False, share=None, gap=None):
        f, s = np.abs(final), np.abs(steady)
        rec = {"id": uid, "numerator": float(f.mean()), "denominator": float(s.mean()),
               "P4": float(f.mean() / s.mean()), "valid": True}
        a = {"final": final.astype(np.float32), "steady": steady.astype(np.float32)}
        if long:
            ticks = [0, 5, 10, 20, 30, 40, 50, 100, 300]
            rec.update(pre_numerator=rec["numerator"], pre_denominator=rec["denominator"], pre_P4=rec["P4"], pre_valid=True,
                       ticks=ticks, mean_abs_difference=[float(f.mean() * share ** (t / 30)) for t in ticks],
                       share={"30": share, "10": share ** (1 / 3), "50": share ** (5 / 3), "100": share ** (10 / 3),
                              "300": share ** 10},
                       eligible=n, remaining=1, settled=n, settled_and_remaining=1, slope_hold=0.5, slope_ramp=0.6)
            a.update(pre_final=a["final"], pre_steady=a["steady"],
                     diff=np.stack([final * share ** (t / 30) for t in ticks]).astype(np.float32))
        units[uid], arrays[uid] = rec, a
        plan.append({"id": uid})

    def brain(p4, scale=1.0):
        s = np.abs(rng.normal(0.1, 0.03, n)) * scale
        return p4 * s * np.abs(rng.normal(1, 0.05, n)), s

    f, s = brain(0.93, 4)
    put("N2/long", f, s, long=True, share=n2_share)
    put("N2/gaps", *brain(0.93 + n2_gap_change, 4))
    names = {e: [f"{e}-{i}" for i in range(k)] for e in mc.ENSEMBLES}
    for e in mc.ENSEMBLES:
        for g in names[e]:
            put(f"graph/{g}/long", *brain(0.82), long=True, share=0.3)
            put(f"graph/{g}/gaps", *brain(0.82 + 0.08))
    for sd in range(perms):
        put(f"perm/{1000 + sd}", *brain(0.88, 1.0))
    for b in range(batches):
        fi, si = brain(0.93, 4)
        put(f"qb/{b}/intact", fi, si)
        for cond, keep in (("RIA", 0.4), ("AIY", 0.5), ("both", 0.25)):
            put(f"qb/{b}/{cond}", fi * keep, si * keep)
            if b == 0 and cond == "both" and controls:
                for e in names:  # null-graph deletions for the first 5 graphs: skewed cuts (0, 0, 0, 0, 0.9)
                    for j, g in enumerate(names[e][:5]):
                        ul = units[f"graph/{g}/long"]
                        al = arrays[f"graph/{g}/long"]
                        for c in ("RIA", "AIY", "both"):
                            keep = 0.1 if j == 4 else 1.0
                            put(f"null/{g}/{c}", al["final"].astype(float) * keep, al["steady"].astype(float) * keep)
                for k_ in ("AIB", "AVJ", "RIM", "AVH", "AWB", "RIF", "RIP", "RIV"):
                    put(f"pair/{k_}", fi * 0.9, si * 0.9)
    return {"units": units, "plan": plan, "attempts": [], "smoke": True}, names, arrays


REG = None


def registered(r):
    reg_ = dict(r.REGISTERED)
    reg_["factorial_permutations"] = 2
    reg_["null_deletion_graphs_per_ensemble"] = 5
    reg_["bootstrap"] = {**reg_["bootstrap"], "resamples": 200}
    return reg_


def test_the_report_passes_a_clean_synthetic_effect(r):
    from wormwars.exp03 import mc_report
    doc, names, arrays = synthetic(n2_gap_change=0.0, n2_share=0.5)
    rep = mc_report.build(doc, names, arrays.__getitem__, registered(r), {"graphs": 6, "permutations": 4}, effect_boot=50)
    assert rep["Q-A"]["p"] == pytest.approx(1 / 7) and rep["Q-D"]["p"] == pytest.approx(1 / 7)
    assert rep["Q-C"]["p"] == pytest.approx(1 / 5)
    assert rep["Q-B"]["complete"] and rep["Q-B"]["p"] < 1e-6  # exact scalings: cuts 0.6 and 0.5, P4 unchanged
    assert rep["counts"]["completed_units"] == len(doc["units"])


def test_the_report_withholds_a_question_with_too_few_graphs_and_keeps_four_in_holm(r):
    from wormwars.exp03 import mc_report
    doc, names, arrays = synthetic(n2_gap_change=0.0, n2_share=0.5)
    for g in names["SH"][:3]:
        del doc["units"][f"graph/{g}/gaps"]
    rep = mc_report.build(doc, names, arrays.__getitem__, registered(r), {"graphs": 6, "permutations": 4}, effect_boot=50)
    assert rep["Q-A"]["p"] is None and rep["holm"]["A"]["missing"] and rep["holm"]["A"]["p"] == 1.0
    assert rep["headline"]["Q-A"]["wording"].startswith("withheld")
    assert len(rep["holm"]) == 4


def test_the_holm_stop_wording(r):
    from wormwars.exp03 import mc_report
    holm = {"A": {"passed": False, "alone_at_alpha": True}}
    lead = {"SH": {"lead_intact": 0.1, "lead_gaps_off": 0.04, "change": -0.06}}
    res = {"p": 0.03, "per_ensemble": {"SH": {"r": 1, "n": 128}}, "lead": lead}
    w = mc_report.wording("A", res, holm, replicated=True)
    assert w.startswith("met α = 0.05 alone, but not its Holm threshold")
    holm = {"A": {"passed": True, "alone_at_alpha": True}}
    assert "narrows" in mc_report.wording("A", res, holm, replicated=True)
    assert "narrow" not in mc_report.wording("A", res, holm, replicated=False)  # only if the lead replicates
    # Fable (prereg review): a pass does not imply the lead over the median narrowed; computed, never asserted
    res["lead"] = {**lead, "SH-route": {"lead_intact": 0.1, "lead_gaps_off": 0.12, "change": 0.02}}
    w = mc_report.wording("A", res, holm, replicated=True)
    assert "did not narrow in every ensemble" in w and "narrows without" not in w


def test_the_lead_change_is_computed_from_the_ensemble_medians(r):
    from wormwars.exp03 import mc_report
    doc, names, arrays = synthetic(n2_gap_change=0.0, n2_share=0.5)
    lead = mc_report.lead_change(doc["units"], names)
    u = doc["units"]
    med = float(np.median([u[f"graph/{g}/long"]["P4"] for g in names["SH"]]))
    assert lead["SH"]["lead_intact"] == pytest.approx(u["N2/long"]["P4"] - med)
    # with gaps off the nulls rise by 0.08 and N2 by 0, so the lead narrows in every ensemble
    assert all(v["change"] < 0 for v in lead.values())


def test_exp03_refuses_03mc_commands_except_a_tokened_build_and_the_rebuild(tmp_path):
    """Fable, Astra (prereg review): `exp03.py build --instance 03mc` drew the formal graphs with no guard. The rule
    is tested as a function: a test that ran the real build would draw them if the guard failed."""
    spec = importlib.util.spec_from_file_location("exp03_guard_test", ROOT / "scripts" / "exp03.py")
    x = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(x)
    bound = tmp_path / "bound.json"
    bound.write_text('{"commit": "abc1234def"}')
    ok = lambda *a: x.instance_command_allowed(*a, bound_path=bound)  # noqa: E731
    assert ok("03", "run", {}) and ok("03r", "report", {})
    assert not ok("03mc", "build", {})
    assert not ok("03mc", "build", {"P4MC_BUILD_TOKEN": "something else"})
    assert ok("03mc", "build", {"P4MC_BUILD_TOKEN": "abc1234def"})
    assert ok("03mc", "rebuild-graphs", {})  # regenerating from the committed record draws nothing new
    for c in ("pilot", "variance", "power", "run", "report"):
        assert not ok("03mc", c, {"P4MC_BUILD_TOKEN": "abc1234def"})
    assert ok("03mc-smoke", "build", {}) and not ok("03mc-smoke", "run", {})
    bound.unlink()
    assert not ok("03mc", "build", {"P4MC_BUILD_TOKEN": "abc1234def"})  # no binding, no formal build


def test_the_prereg_chain_protects_every_committed_amendment(r):
    """Astra (prereg review): a later amendment could be edited while the bound text and the code commit's text
    still survived."""
    v0 = b"bound\n"
    v1 = b"bound\n\n## Amendment 1\ntext\n"
    v2 = v1 + b"\n## Amendment 2\nmore\n"
    r.check_prereg_chain([v0, v1, v2], v2)
    r.check_prereg_chain([v0, v1, v2], v2 + b"\n## Amendment 3\n")
    with pytest.raises(SystemExit):
        r.check_prereg_chain([v0, v1, v2], v1 + b"\n## Amendment 2\nedited\n")  # amendment 2 changed
    with pytest.raises(SystemExit):
        r.check_prereg_chain([v0, v1, v2], v0 + b"\n## Amendment 2\nmore\n")  # amendment 1 removed


def test_a_moved_code_commit_must_be_named_by_an_amendment(r):
    r.check_code_commit_named(b"anything", {"commit": "aaaaaaa1", "code_commit": "aaaaaaa1"})
    r.check_code_commit_named(b"... formal code at `bbbbbbb2` ...", {"commit": "aaaaaaa1", "code_commit": "bbbbbbb2cc"})
    with pytest.raises(SystemExit):
        r.check_code_commit_named(b"no name here", {"commit": "aaaaaaa1", "code_commit": "bbbbbbb2cc"})


def test_without_bound_json_nothing_formal_starts(r, tmp_path, monkeypatch):
    monkeypatch.setattr(r, "EXP_FORMAL", tmp_path)
    with pytest.raises(SystemExit, match="not bound"):
        r.bound()
    (tmp_path / "bound.json").write_text('{"commit": "abc"}')
    assert r.bound() == {"commit": "abc", "code_commit": "abc"}


def test_the_run_needs_the_build_under_this_binding_with_unchanged_records(r, tmp_path, monkeypatch):
    monkeypatch.setattr(r, "exp_dir", lambda: tmp_path)
    for f in r.BUILD_RECORDS[1:]:
        (tmp_path / f).write_text("{}\n")
    sha = r.records_sha(r.BUILD_RECORDS[1:])
    (tmp_path / "build.json").write_text(json.dumps({"outcome": "completed", "bound_commit": "abc", "records_sha256": sha}))
    r.require_build("abc")
    with pytest.raises(SystemExit, match="another binding"):
        r.require_build("def")
    (tmp_path / "ensembles.json").write_text('{"changed": 1}\n')
    with pytest.raises(SystemExit, match="changed"):
        r.require_build("abc")


def test_a_forged_or_stale_check_does_not_admit_the_run(r, tmp_path, monkeypatch):
    """Astra (prereg review): `{"passed": true}` alone admitted the run."""
    monkeypatch.setattr(r, "EXP_FORMAL", tmp_path)
    monkeypatch.setattr(r, "out_dir", lambda: tmp_path)
    (tmp_path / "prerun-check.json").write_text('{"passed": true}')
    (tmp_path / "prerun-repeat.json").write_text('{"passed": true}')
    with pytest.raises(SystemExit, match="does not admit"):
        r.require_check("abc")
    good = {"passed": True, "set": "check", "device": "cuda", "genomes": 2048,
            "reference_sha256": dict(r.EQ.REFERENCE_SHA256), "stamp": {"dirty": False, "git_commit": "c1"}}
    rep = {"passed": True, "device": "cuda", "genomes": 2048, "provenance": {"git_commit": "c1", "dirty": False}}
    for bad in ({"device": "cpu"}, {"set": "panel"}, {"genomes": 8}, {"stamp": {"dirty": True, "git_commit": "c1"}}):
        (tmp_path / "prerun-check.json").write_text(json.dumps({**good, **bad}))
        (tmp_path / "prerun-repeat.json").write_text(json.dumps(rep))
        with pytest.raises(SystemExit, match="does not admit"):
            r.require_check("abc")
    (tmp_path / "prerun-check.json").write_text(json.dumps(good))
    (tmp_path / "prerun-repeat.json").write_text(json.dumps({**rep, "passed": False}))
    with pytest.raises(SystemExit, match="repeat"):
        r.require_check("abc")
    (tmp_path / "prerun-repeat.json").write_text(json.dumps(rep))
    seen = []
    monkeypatch.setattr(r.reg, "require_same_code", lambda c, paths: seen.append(c))
    with pytest.raises(SystemExit, match="start marker"):
        r.require_check("abc")
    assert "c1" in seen and "abc" in seen  # the check's code and the code commit, both against HEAD
    (tmp_path / "markers").mkdir()
    (tmp_path / "markers" / "check-started.json").write_text("{}")
    r.require_check("abc")
    # Astra (review of draft 2): the environment, the measurement inputs and a clean repeat record are compared too
    env = {"python": "3.13.1", "numpy": "2", "torch": "2.12", "cuda": "13.0", "gpu": "RTX 5080", "connectome_cache_sha256": "h"}
    (tmp_path / "prerun-check.json").write_text(json.dumps({**good, "stamp": {**good["stamp"], **env}}))
    (tmp_path / "prerun-repeat.json").write_text(json.dumps({**rep, "provenance": {**rep["provenance"], **env},
                                                             "inputs": {"pilot": "1"}}))
    r.require_check("abc", env, {"pilot": "1"})
    with pytest.raises(SystemExit, match="environment"):
        r.require_check("abc", {**env, "torch": "2.13"}, {"pilot": "1"})
    with pytest.raises(SystemExit, match="inputs"):
        r.require_check("abc", env, {"pilot": "2"})
    (tmp_path / "prerun-repeat.json").write_text(json.dumps({**rep, "provenance": {**rep["provenance"], **env, "dirty": True},
                                                             "inputs": {"pilot": "1"}}))
    with pytest.raises(SystemExit, match="uncommitted"):
        r.require_check("abc", env, {"pilot": "1"})


def test_the_report_validates_the_measurements_and_every_array(r, tmp_path, monkeypatch):
    """Astra (review of draft 2): the report checked arrays only when a statistic loaded them (25 smoke units never),
    and never checked the measurements' settings, plan or inputs."""
    r.use_smoke(True)
    try:
        monkeypatch.setattr(r, "out_dir", lambda: tmp_path)
        units = [{"id": "qb/0/intact"}, {"id": "perm/9000"}]
        recs = {}
        for u in units:
            recs[u["id"]] = {"arrays_sha256": r.save_arrays(r.array_path(u["id"]), {"final": np.ones(2, np.float32)})}
        doc = {"attempts": [], "smoke": True, "registered": r.REGISTERED, "plan": units, "inputs": {"x": "1"},
               "units": recs}
        r.validate_measurements(doc, None, units, {"x": "1"})
        with pytest.raises(SystemExit, match="plan"):
            r.validate_measurements(doc, None, units[:1], {"x": "1"})
        with pytest.raises(SystemExit, match="inputs"):
            r.validate_measurements(doc, None, units, {"x": "2"})
        with pytest.raises(SystemExit, match="settings"):
            r.validate_measurements({**doc, "registered": {}}, None, units, {"x": "1"})
        r.array_path("perm/9000").write_bytes(b"changed")  # a unit no statistic may load
        with pytest.raises(SystemExit, match="does not hash"):
            r.validate_measurements(doc, None, units, {"x": "1"})
    finally:
        r.use_smoke(False)


def test_one_run_at_a_time(r, tmp_path):
    lock = tmp_path / "run.lock"
    with r.RunLock(lock):
        assert lock.exists()
        with pytest.raises(SystemExit, match="another run"):
            with r.RunLock(lock):
                pass
    assert not lock.exists()


def test_arrays_load_only_with_their_recorded_hash(r, tmp_path, monkeypatch):
    monkeypatch.setattr(r, "out_dir", lambda: tmp_path)
    sha = r.save_arrays(r.array_path("qb/0/intact"), {"final": np.ones(3, np.float32)})
    load = r.array_loader({"qb/0/intact": {"arrays_sha256": sha}})
    assert load("qb/0/intact")["final"].sum() == 3
    load_bad = r.array_loader({"qb/0/intact": {"arrays_sha256": "0" * 64}})
    with pytest.raises(SystemExit, match="does not hash"):
        load_bad("qb/0/intact")


def test_genome_intervals_resample_the_genome_axis():
    """A curve is [ticks, genomes]: the first version took the tick count as the genome count (found by the smoke run;
    silent when genomes outnumber ticks)."""
    from wormwars.exp03 import mc_report
    d = np.vstack([np.arange(1000.0), np.arange(1000.0)])
    ci = mc_report.genome_ci([d], lambda x: float(x.shape[-1] + x[0].mean() * 0), seed=0, resamples=20)
    assert ci == [1000.0, 1000.0]
    ci = mc_report.genome_ci([d], lambda x: float(x[1].mean()), seed=0, resamples=200)
    assert 470 < ci[0] < 499.5 < ci[1] < 530  # the mean of 0..999 is 499.5


def test_the_null_deletion_interval_is_of_the_median():
    """Astra, Fable (review of draft 2): §7 promises each ensemble's median with an interval; the first version
    bootstrapped the mean. 31 zeros and a one: the median's interval is [0, 0]."""
    from wormwars.exp03 import mc_report
    v = [0.0] * 31 + [1.0]
    assert mc_report._boot_ci(v, seed=0, resamples=2000, stat="median") == [0.0, 0.0]
    assert mc_report._boot_ci(v, seed=0, resamples=2000)[1] > 0  # the mean's interval is not


def test_withheld_questions_still_report_their_counts_and_estimates(r):
    """Astra (review of draft 2): an invalid N2, an incomplete Q-B or too few permutations dropped the counts and the
    available estimates."""
    from wormwars.exp03 import mc_report
    doc, names, arrays = synthetic(n2_gap_change=0.0, n2_share=0.5)
    del doc["units"]["perm/1003"]
    del doc["units"]["qb/1/AIY"]
    rep = mc_report.build(doc, names, arrays.__getitem__, registered(r), {"graphs": 6, "permutations": 4}, effect_boot=20)
    assert rep["Q-C"]["p"] is None and rep["Q-C"]["measured"] == 3 and rep["Q-C"]["n2_response"] > 0
    assert rep["Q-C"]["n2_response_interval_95"] is not None
    assert rep["Q-B"]["p"] is None
    assert rep["Q-B"]["per_deletion"]["AIY"]["batches_planned"] == 2 and rep["Q-B"]["per_deletion"]["AIY"]["batches_measured"] == 1
    doc["units"]["N2/long"] = {**doc["units"]["N2/long"], "valid": False, "P4": None}
    rep = mc_report.build(doc, names, arrays.__getitem__, registered(r), {"graphs": 6, "permutations": 4}, effect_boot=20)
    assert rep["replication"]["overall"] == "withheld" and rep["replication"]["counts"]["SH"]["valid"] == 6


def test_the_controls_path_runs(r):
    """Fable (review of draft 2): the controls' code had never run; the synthetic set now has the eight control pairs."""
    from wormwars.exp03 import mc_report
    doc, names, arrays = synthetic(n2_gap_change=0.0, n2_share=0.5, controls=True)
    rep = mc_report.build(doc, names, arrays.__getitem__, registered(r), {"graphs": 6, "permutations": 4}, effect_boot=20)
    c = rep["secondary_tests"]["degree-matched controls"]
    assert c["RIA"]["complete"] and c["AIY"]["complete"]
    assert c["RIA"]["passed"] and c["AIY"]["passed"]  # RIA keeps 0.4 and AIY 0.5 of the response; controls keep 0.9
    assert rep["descriptive"]["pair screen, batch 0"]["rank_by_cut"] == {"RIA": 1, "AIY": 2}
    nd = rep["descriptive"]["null-graph deletions"]["RIA"]["SH"]
    want = mc_report._boot_ci(list(nd["cuts"].values()), seed=r.REGISTERED["bootstrap"]["graphs_seed"], resamples=200,
                              stat="median")
    assert nd["graphs"] == 5 and nd["median_cut_95"] == want
    assert nd["median_cut_95"] != mc_report._boot_ci(list(nd["cuts"].values()), seed=r.REGISTERED["bootstrap"]["graphs_seed"],
                                                     resamples=200)  # the case separates the median from the mean  # the median's interval, not the mean's


def test_a_report_never_replaces_an_existing_file(r, tmp_path):
    first = r.reserve_report_path(tmp_path)
    first.write_text("{}")
    second = r.reserve_report_path(tmp_path)
    third = r.reserve_report_path(tmp_path)
    assert len({first, second, third}) == 3 and first.name == "report.json"


def test_the_measurement_inputs_are_pinned_to_the_binding(r, monkeypatch):
    """Astra (review of draft 3): a committed change to the stimulus bank or the remaps after binding was admitted;
    they are now compared against the code commit like the code."""
    seen = []
    monkeypatch.setattr(r, "SMOKE", False)
    monkeypatch.setattr(r, "bound", lambda: {"commit": "aaaaaaa", "code_commit": "aaaaaaa"})
    monkeypatch.setattr(r.subprocess, "run", lambda *a, **k: r.subprocess.CompletedProcess(a, 0))
    monkeypatch.setattr(r, "prereg_versions", lambda c: [b"x\n"])
    monkeypatch.setattr(r, "check_prereg_chain", lambda v, n: None)
    monkeypatch.setattr(r.reg, "require_same_code", lambda c, paths: seen.append(list(paths)))
    monkeypatch.setattr(r.reg, "require_pins", lambda p: None)
    monkeypatch.setattr(r.reg, "require_pushed", lambda p: None)
    r.guards(type("A", (), {"device": "cpu"})(), {}, "build")
    assert any(set(r.MEASUREMENT_INPUTS) <= set(p) for p in seen)


def test_an_incomplete_qb_still_reports_its_available_paired_batches(r):
    """Astra (review of draft 3): a missing batch suppressed the deletion's estimate; the confirmatory question stays
    withheld, and a descriptive estimate from the complete pairs is reported, labelled."""
    from wormwars.exp03 import mc_report
    doc, names, arrays = synthetic(n2_gap_change=0.0, n2_share=0.5)
    del doc["units"]["qb/1/AIY"]
    rep = mc_report.build(doc, names, arrays.__getitem__, registered(r), {"graphs": 6, "permutations": 4}, effect_boot=20)
    aiy = rep["Q-B"]["per_deletion"]["AIY"]
    assert rep["Q-B"]["p"] is None and not aiy["complete"]
    assert aiy["intact_batches_measured"] == 2 and aiy["paired_batches"] == 1
    d = aiy["descriptive_available_batches"]
    assert d["genomes"] == 400 and d["cut"] == pytest.approx(0.5)


def test_qb_failure_names_parts_against_the_holm_threshold(r):
    """Fable (review of draft 3): a part between its Holm threshold and 0.05 was not named."""
    from wormwars.exp03 import mc_report
    bt = {"cut": 0.5, "cut_q05_q95": [0.45, 0.55], "dP4": 0.01, "dP4_q05_q95": [-0.001, 0.021]}
    res = {"p": 0.03, "per_deletion": {"RIA": {"tests": {"p_cut": 1e-6, "p_eq": 0.03}, "bootstrap": bt},
                                       "AIY": {"tests": {"p_cut": 1e-6, "p_eq": 1e-4}, "bootstrap": bt}}}
    holm = {"B": {"passed": False, "alone_at_alpha": True, "threshold": 0.0125}}
    w = mc_report.wording("B", res, holm, replicated=True)
    assert "RIA's change in P4 was not shown to be within 0.02" in w and "AIY" not in w


def test_the_report_refuses_units_outside_the_plan(r, tmp_path, monkeypatch):
    r.use_smoke(True)
    try:
        monkeypatch.setattr(r, "out_dir", lambda: tmp_path)
        units = [{"id": "qb/0/intact"}]
        recs = {u: {"arrays_sha256": r.save_arrays(r.array_path(u), {"final": np.ones(2, np.float32)})}
                for u in ("qb/0/intact", "pair/XYZ")}
        doc = {"attempts": [], "smoke": True, "registered": r.REGISTERED, "plan": units, "inputs": {}, "units": recs}
        with pytest.raises(SystemExit, match="not in the plan"):
            r.validate_measurements(doc, None, units, {})
    finally:
        r.use_smoke(False)
