"""03mc's runner (`scripts/p4mc.py`) and report (`wormwars/exp03/mc_report.py`), on the CPU without drawing a graph.

The runner was written before these tests (D289); each test here was also run against a sabotaged copy of the
behaviour it checks, and failed there."""

from __future__ import annotations

import importlib.util
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
        units = [{"id": "a"}, {"id": "b"}]
        doc = {"attempts": [{"provenance": {}}], "inputs": {"x": "1"}, "plan": units}
        r.check_resume(doc, {}, {"x": "1"}, units)
        with pytest.raises(SystemExit):
            r.check_resume(doc, {}, {"x": "2"}, units)
        with pytest.raises(SystemExit):
            r.check_resume(doc, {}, {"x": "1"}, units[::-1])
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

def synthetic(n2_gap_change, n2_share, k=6, perms=4, batches=2, seed=1):
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
            a.update(pre_final=a["final"], pre_steady=a["steady"])
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
    return {"units": units, "plan": plan, "attempts": [], "smoke": True}, names, arrays


REG = None


def registered(r):
    reg_ = dict(r.REGISTERED)
    reg_["factorial_permutations"] = 2
    reg_["null_deletion_graphs_per_ensemble"] = 2
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
    res = {"p": 0.03, "per_ensemble": {"SH": {"r": 1, "n": 128}}}
    w = mc_report.wording("A", res, holm, replicated=True)
    assert w.startswith("met α = 0.05 alone, but not its Holm threshold")
    holm = {"A": {"passed": True, "alone_at_alpha": True}}
    assert "narrows" in mc_report.wording("A", res, holm, replicated=True)
    assert "narrows" not in mc_report.wording("A", res, holm, replicated=False)  # only if the lead replicates
