"""M5's pilot (docs/memory/M5-PILOT-PLAN.md): the Rr blocks, the replay, the audit sample, the horizon rule and the
report's arithmetic."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m5"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m4"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))


@pytest.fixture(scope="module")
def MP(tmp_path_factory):
    os.environ["MEMORY_M5P_OUT"] = str(tmp_path_factory.mktemp("m5p"))
    import m5_pilot
    yield m5_pilot
    os.environ.pop("MEMORY_M5P_OUT", None)


@pytest.fixture(scope="module")
def RP(MP):
    import m5_pilot_read
    return m5_pilot_read


@pytest.fixture(scope="module")
def rr(MP):
    return MP.rr_blocks(0)


@pytest.fixture(scope="module")
def host(MP):
    con, _ = MP.m4d.build_host("SH", 2019100)
    return con


# ------------------------------------------------------------------------------------------------------------- Rr
def test_rr_blocks_follow_the_plan(MP, rr):
    B1, B2, chain = rr
    MP.check_rr(B1)
    MP.check_rr(B2)
    Bn = MP.m4d.n2_block()
    off = ~np.eye(30, dtype=bool)
    assert np.allclose(B1[off].reshape(30, 29).sum(1), Bn[off].reshape(30, 29).sum(1))  # out-strengths
    assert chain["first"]["accepted"] == chain["continued"]["accepted"] == 20 * 260
    assert not np.array_equal(B1, Bn) and not np.array_equal(B2, B1)


def test_the_rr_check_catches_each_rule(MP, rr):
    B1 = rr[0]
    off = ~np.eye(30, dtype=bool)
    e = [tuple(x) for x in np.argwhere(off & (B1 > 0))]
    z = [tuple(x) for x in np.argwhere(off & (B1 == 0))]

    def moved(B):  # one edge moved to an empty place: degrees change
        B = B.copy()
        B[z[0]], B[e[0]] = B[e[0]], 0
        return B

    def reweighed(B):  # one magnitude changed: a source's outgoing collection changes
        B = B.copy()
        B[e[0]] += 1
        return B

    def diagonal(B):
        B = B.copy()
        B[0, 0] += 1
        return B

    for bad in (moved(B1), reweighed(B1), diagonal(B1)):
        with pytest.raises(SystemExit):
            MP.check_rr(bad)


def test_the_rr_check_catches_a_lost_reciprocal_pair(MP):
    """A swap that keeps every degree and outgoing magnitude but changes the reciprocal-pair count is refused."""
    Bn = MP.m4d.n2_block()
    rng = np.random.default_rng(5)
    B, _ = MP.m4d.rewire(Bn, rng, keep_recip=False)  # degrees and magnitudes kept, reciprocity free
    if MP.m4d.block_stats(B)["reciprocal"] == MP.N_RECIP:
        pytest.skip("this draw kept 75 pairs by chance")
    with pytest.raises(SystemExit):
        MP.check_rr(B)


def test_the_chain_is_continued_not_restarted(MP, rr):
    B1, B2, _ = rr
    rng = np.random.default_rng(MP.SEED_RR + 0)
    a, _ = MP.m4d.rewire(MP.m4d.n2_block(), rng, keep_recip=True)
    b, _ = MP.m4d.rewire(a, rng, keep_recip=True)
    assert np.array_equal(a, B1) and np.array_equal(b, B2)
    restarted, _ = MP.m4d.rewire(B1, np.random.default_rng(MP.SEED_RR + 0), keep_recip=True)
    assert not np.array_equal(restarted, B2)


def test_the_similarity_splits_reciprocal_edges(MP):
    Bn = MP.m4d.n2_block()
    s = MP.similarity(Bn, Bn)
    assert s["shared_edges"] == 260 and s["n2_reciprocal_edges"] == 150 and s["n2_nonreciprocal_edges"] == 110
    assert s["shared_reciprocal_edges"] == 150 and s["shared_nonreciprocal_edges"] == 110
    assert s["same_magnitude_edges"] == 260 and np.isclose(s["min_weight_overlap"], 1.0)
    off = ~np.eye(30, dtype=bool)
    rec = off & (Bn > 0) & (Bn.T > 0)
    i, j = np.argwhere(rec)[0]
    B = Bn.copy()
    B[i, j] = 0  # one reciprocal edge dropped
    s = MP.similarity(B, Bn)
    assert s["shared_reciprocal_edges"] == 149 and s["shared_nonreciprocal_edges"] == 110


def test_the_seed_families_do_not_meet_m4e(MP):
    m4e = MP.m4e
    shift = getattr(m4e, "_SHIFT", 0)
    m4e_fams = [range(20261301, 20261500), range(20261511, 20261531), range(20261541, 20261544),
                range(20261601, 20261601 + 100 * 19 + 9)]
    pilot = [range(MP.SEED_RR, MP.SEED_RR + 20), range(MP.SEED_RR_AUDIT, MP.SEED_RR_AUDIT + 20),
             range(MP.SEED_BIG_AUDIT, MP.SEED_BIG_AUDIT + 3)]
    import m5_pilot_read
    pilot.append(range(m5_pilot_read.SEED_READ, m5_pilot_read.SEED_READ + 1))
    seen = set()
    for r in pilot:
        assert not seen & set(r)
        seen |= set(r)
    for r in m4e_fams:
        assert not seen & set(r)
    assert shift in (0, 900_000)


# ------------------------------------------------------------------------------------------------------- the replay
def test_a_first_pass_does_not_depend_on_its_batch(MP, host):
    """The full 2000-tick first pass of a T-arm panel in its production chunk of 128 equals the replay's batches of 2
    and 3, state, tail and read-out (Astra, round 3); the replay never runs a batch of one (Fable, round 3)."""
    g_host, cfg = MP.m4d.host_genomes(host, 128, 23)
    signs = MP.m4d.sign_matrix(g_host, 128, 24)
    con = MP.m4e.arm_graph(host, "T", {"T": MP.m4d.n2_block()})
    g = MP.m4d.paired_genome(g_host, con, signs)
    full = MP.P.probe_states(g, cfg)
    for ids in ([3, 99], [0, 40, 127]):
        part = MP.P.probe_states(g.select(ids), cfg)
        assert torch.equal(part["end"], full["end"][ids])
        assert np.array_equal(part["tail"], full["tail"][ids]) and np.array_equal(part["y"], full["y"][ids])


def test_extend_classifies_as_the_second_pass(MP, host, monkeypatch):
    """extend gives the second pass's classes and calls the classifier as m4e.second_pass does: from the pre-tail
    state, following the recorded tail only (fading genomes alone cannot show a wrong horizon, so the call is
    compared too)."""
    g, cfg = MP.m4d.host_genomes(host, 3, 29)
    gs, run, r1, run_ids = MP.replay(g, cfg, [0, 2])
    end, y = run["end"], run["y"][:, :301]
    assert run_ids == [0, 2] and len(r1) == 2
    calls = []
    real = MP.P.full_classify

    def spy(*a, **k):
        calls.append(({x: v for x, v in k.items() if x != "initial"}, k.get("initial")))
        return real(*a, **k)

    monkeypatch.setattr(MP.P, "full_classify", spy)
    _, r22 = MP.extend(gs, cfg, end, y, MP.m4e.EXTRA)
    recs = MP.m4e.second_pass(g, cfg, [0, 2], end, y)
    assert MP.fields(r22, MP.SECOND_FIELDS) == MP.fields(recs, MP.SECOND_FIELDS)
    (ka, ia), (kb, ib) = calls
    assert ka == kb and ia is not None and torch.equal(ia, ib)


def test_the_replay_stops_on_a_different_output(MP):
    """Class, reason and write amplitude exactly; the root search's two fields within 1e-9 relative (the smoke's
    3e-13 passes); exact=True (the composition check) bit for bit."""
    a = {"class": 4, "reason": "x", "a": 0.5, "root_distance": 1.952984554547665, "readout_difference": 0.10977950278985057}
    MP.check_replay("same", [a, a], [dict(a), dict(a)])
    near = {**a, "root_distance": 1.9529845545473936, "readout_difference": 0.10977950278976745}  # the smoke's pair
    assert 0 < MP.check_replay("composition", [near], [a]) < 1e-12
    with pytest.raises(SystemExit):
        MP.check_replay("exact", [near], [a], exact=True)
    for got, want in (([a], [{**a, "class": 2}]), ([a], [{**a, "a": float(np.nextafter(0.5, 1))}]),
                      ([a], [{**a, "root_distance": a["root_distance"] * (1 + 1e-6)}]),
                      ([a], [{**a, "reason": "y"}]), ([a], [a, a])):
        with pytest.raises(SystemExit):
            MP.check_replay("differs", got, want)


def test_a_batch_of_one_gets_a_discarded_companion(MP, host):
    g, cfg = MP.m4d.host_genomes(host, 4, 31)
    gs, run, r1, run_ids = MP.replay(g, cfg, [2])
    assert run_ids == [2, 0] and len(r1) == 1 and gs.n_strains == 2
    _, _, r2, _ = MP.replay(g, cfg, [2, 0])
    assert MP.fields(r1, MP.FIRST_FIELDS) == MP.fields(r2[:1], MP.FIRST_FIELDS)


def test_the_state_check_compares_the_hold_with_the_chunk(MP, host):
    g, cfg = MP.m4d.host_genomes(host, 8, 37)
    _, run, _, _ = MP.replay(g, cfg, [1, 6])
    assert MP.state_check(g, cfg, [1, 6], run) == [[0, 7]]
    bad = {**run, "end": run["end"].clone()}
    bad["end"][1, 0, 0] += 1e-6
    with pytest.raises(SystemExit):
        MP.state_check(g, cfg, [1, 6], bad)


def _stage_file(MP, ids):
    a = {"class": 4, "reason": "x", "a": 0.5, "root_distance": 1.9, "readout_difference": 0.1}
    s = {"class": 4, "reason": "y", "root_distance": 1.8, "readout_difference": 0.2}
    rec = {"class": [4] * 8, "reason": ["x"] * 8, "a": [0.5] * 8, "root_distance": [1.9] * 8,
           "readout_difference": [0.1] * 8, "second": {"ids": list(range(8)), "class": [4] * 8, "reason": ["y"] * 8,
                                                       "root_distance": [1.8] * 8, "readout_difference": [0.2] * 8}}
    out = {"host": "SH-1", "draw": 0, "arm": "T", "ids": ids, "recorded_2000": [a] * len(ids),
           "recorded_22000": [s] * len(ids), "replayed_2000": [a] * len(ids), "replayed_22000": [s] * len(ids),
           "class_100000": [2] * len(ids), "reason_100000": [""] * len(ids), "fallbacks": []}
    return rec, out


def test_a_stage_file_is_checked_against_its_source(MP):
    """Identity, the stored copy of the record and the replay's agreement, before a resume skips or the reader reads
    the file (Astra, round 4)."""
    rec, out = _stage_file(MP, [2, 5])
    expect = ("SH-1", 0, "T")
    MP.check_out(out, [2, 5], MP.LONGER_COLS, "ok", expect, rec)
    bad_cases = [{**out, "draw": 1},
                 {**out, "recorded_2000": [{**out["recorded_2000"][0], "class": 2}, out["recorded_2000"][1]]},
                 {**out, "replayed_2000": [{**out["replayed_2000"][0], "class": 2}, out["replayed_2000"][1]]},
                 {**out, "replayed_22000": [out["replayed_22000"][0], {**out["replayed_22000"][1], "reason": "z"}]}]
    for bad in bad_cases:
        with pytest.raises(SystemExit):
            MP.check_out(bad, [2, 5], MP.LONGER_COLS, "bad", expect, rec)
    covered = {**bad_cases[2], "fallbacks": [{"genome": 2, "pass": "first", "panel_rerun_exact": True}]}
    MP.check_out(covered, [2, 5], MP.LONGER_COLS, "covered", expect, rec)


def test_the_failure_remedy_continues_only_on_an_exact_panel_rerun(MP, monkeypatch):
    want = [{"class": 4, "reason": "x", "a": 0.5, "root_distance": 1.9, "readout_difference": 0.1}]
    flipped = [{**want[0], "reason": "y"}]  # a branch flip in the classifier, the state identical
    rec = {"class": [4], "reason": ["x"], "a": [0.5], "root_distance": [1.9], "readout_difference": [0.1],
           "second": {"ids": []}}
    monkeypatch.setattr(MP, "panel_rerun", lambda v, arm, cache: rec)
    fb = []
    MP.checked("t", flipped, want, None, "T", [0], "first", {}, fb)
    assert fb and fb[0]["genome"] == 0 and fb[0]["panel_rerun_exact"] is True
    monkeypatch.setattr(MP, "panel_rerun", lambda v, arm, cache: {**rec, "reason": ["z"]})
    with pytest.raises(SystemExit):
        MP.checked("t", flipped, want, None, "T", [0], "first", {}, [])
    assert MP.fallback_holds(want, want) and not MP.fallback_holds(flipped, want)


def test_the_composition_file_must_be_the_plans_passed_check(MP, monkeypatch):
    monkeypatch.setattr(MP.m4e, "N_DRAW", 512)
    verified = [{"rec": {"name": "SH-1"}, "draw": 0}, {"rec": {"name": "SH-1"}, "draw": 1}]
    m = lambda u: {"class": [2] * 512, "second": {"ids": [], "class": []}, "_u": u}  # noqa: E731
    recs = {a: [m([]), m([300])] for a in MP.PILOT_ARMS}
    monkeypatch.setattr(MP, "longer_targets", lambda rec: rec["_u"])
    good = {a: {"panel": "SH-1 d1", "genome": 300, "chunk": [256, 383], "exact": True, "states_equal": True}
            for a in MP.PILOT_ARMS}
    MP.check_composition_file(good, verified, recs)
    for bad in ({}, {**good, "T": {**good["T"], "exact": False}}, {**good, "K": {**good["K"], "genome": 301}},
                {**good, "Rr": {**good["Rr"], "states_equal": None}}):
        with pytest.raises(SystemExit):
            MP.check_composition_file(bad, verified, recs)


def test_the_output_folder_cannot_be_m4e_or_m4d(MP):
    for old in ("memory-m4e", "memory-m4d"):
        with pytest.raises(SystemExit):
            MP.check_out_dir(ROOT / "runs" / old)
    MP.check_out_dir(ROOT / "runs" / "memory-m5-pilot")


def test_incomplete_records_are_refused(MP):
    with pytest.raises(SystemExit):  # three ids, no 100,000-tick classes (Astra, round 3)
        MP.check_out({"ids": [1, 2, 3], **{k: [] for k in MP.LONGER_COLS}}, [1, 2, 3], MP.LONGER_COLS, "x")
    with pytest.raises(SystemExit):
        MP.check_out({"ids": [1, 2], **{k: [0, 0] for k in MP.LONGER_COLS}}, [1, 2, 3], MP.LONGER_COLS, "x")
    with pytest.raises(SystemExit):
        MP.check_out({"ids": [1], **{k: [9] for k in MP.AUDIT_COLS}}, [1], MP.AUDIT_COLS, "x")
    MP.check_out({"ids": [1], **{k: [2] for k in MP.AUDIT_COLS}}, [1], MP.AUDIT_COLS, "x")


def test_an_rr_record_without_its_second_pass_is_refused(MP, monkeypatch):
    n = 8
    monkeypatch.setattr(MP.m4e, "N_DRAW", n)
    r = {"host": 0, "name": "SH-0"}
    audit = MP.rr_audit_ids(0, n)
    cls = [2] * n
    rec = {"host": 0, "name": "SH-0", "draw": 0, "arm": "Rr", "genome_seed": MP.m4e.GENOME_SEED, "n": n,
           "arm_sha256": "x", "genomes": list(range(n)), **{k: [0] * n for k in ("reason", "a", "root_distance",
                                                                                "readout_difference", "write_sq",
                                                                                "write_core")},
           "class": cls, "audit": audit,
           "second": {"ids": audit, **{k: [2] * len(audit) for k in MP.SECOND_FIELDS}}}
    MP.validate_rr(rec, r, 0, "x")
    for bad in ({**rec, "second": {**rec["second"], "class": []}}, {**rec, "genomes": list(range(n - 1))}):
        with pytest.raises(SystemExit):
            MP.validate_rr(bad, r, 0, "x")


# -------------------------------------------------------------------------------------------------------- the audit
def _recs():
    rng = np.random.default_rng(3)
    out = []
    for _ in range(4):
        cls = rng.choice([0, 2, 2, 2, 2, 3, 4], 60).tolist()
        audit = sorted(rng.choice(60, 8, replace=False).tolist())
        second = [i for i, x in enumerate(cls) if x != 2 or i in audit]
        out.append({"class": cls, "audit": audit, "second": {"ids": second}})
    return out


def test_the_audit_sample_is_unaudited_fading_and_fixed(MP):
    recs = _recs()
    s = MP.audit_sample(recs, "T", n=50)
    assert len(s) == len(set(s)) == 50
    for p, i in s:
        assert recs[p]["class"][i] == MP.FADING and i not in recs[p]["audit"] and i not in recs[p]["second"]["ids"]
    assert s == MP.audit_sample(recs, "T", n=50)  # its seed fixes it
    assert s != MP.audit_sample(recs, "K", n=50)  # each arm its own generator
    pool = MP.audit_pool(recs)
    assert len(MP.audit_sample(recs, "T", n=10 ** 6)) == len(pool)  # never more than the population


# ------------------------------------------------------------------------------------------------------- the report
def test_the_horizon_rule_at_its_boundary(RP):
    assert RP.horizon_rule(0.5) == "continue to 100,000 ticks"
    assert RP.horizon_rule(0.4999) == "keep 22,000 ticks"


def test_clopper_pearson_upper_bounds(RP):
    assert np.isclose(RP.cp_upper(0, 3000), 1 - 0.05 ** (1 / 3000), rtol=1e-6)
    assert np.isclose(RP.cp_upper(0, 1500), 0.001995, atol=1e-6)
    assert np.isclose(RP.cp_upper(2, 56), 0.1086, atol=5e-4)
    assert RP.cp_upper(5, 5) == 1.0 and RP.cp_upper(0, 0) == 1.0


def test_the_paired_genome_part_is_zero_for_identical_outcomes(RP):
    """Identical paired outcomes give zero genome variance (Astra, round 3); independent binomials would not."""
    d = np.zeros((10, 2))
    v = RP.variance_split(d, 0.005, 0.005, 1024, p11=0.005)
    assert v["genome"] == 0 and RP.variance_split(d, 0.005, 0.005, 1024)["genome"] > 0


def test_the_horizon_rule_waits_for_a_complete_stage(RP):
    rows = {("h", 0, a): {"ids": [1, 2], "class_100000": [2, 2], "recorded_22000": [{"reason": "r"}] * 2,
                          "reason_100000": ["", ""]} for a in ("T", "K", "Rr")}
    assert RP.longer_report(rows, [])["horizon_rule"] == "continue to 100,000 ticks"
    assert RP.longer_report(rows, ["x.json"])["horizon_rule"] == "not applied: incomplete"
    rows[("h", 0, "T")]["class_100000"] = [4, 4]
    rows[("h", 0, "K")]["class_100000"] = [4, 4]
    assert RP.longer_report(rows, [])["horizon_rule"] == "keep 22,000 ticks"


def test_the_variance_split_recovers_known_components(RP):
    rng = np.random.default_rng(11)
    H, D, n, pa, pb = 4000, 2, 1024, 0.006, 0.004
    host = rng.normal(0, np.sqrt(1.5e-5), H)
    draw = rng.normal(0, np.sqrt(5e-6), (H, D))
    sa = rng.binomial(n, pa, (H, D)) / n
    sb = rng.binomial(n, pb, (H, D)) / n
    d = host[:, None] + draw + sa - sb
    v = RP.variance_split(d, pa, pb, n)
    assert np.isclose(v["genome"], (pa * (1 - pa) + pb * (1 - pb)) / n)
    assert abs(v["host"] - 1.5e-5) < 2.5e-6 and abs(v["draw"] - 5e-6) < 2e-6


def test_the_reader_reproduces_m4es_t_minus_k(MP, RP):
    """End to end on M4e's committed records (Fable, round 4): the reader's contrast gives M4e's published T − K mean
    and host spread, and the independent split Astra's decomposition (0.5085 / 0.0773 / 0.4142, within the genome
    part's pooling)."""
    import json
    hosts = json.load(open(ROOT / "runs" / "memory-m4e" / "hosts.json"))["hosts"]
    panels = {}
    for h in hosts:
        for d in (0, 1):
            for a in ("T", "K"):
                f = ROOT / "runs" / "memory-m4e" / "arms" / f"{h['name']}__d{d}__{a}.json"
                panels[(h["host"], d, a)] = MP.m4e.merged_classes(json.load(open(f)))
    c = RP.contrast(panels, "T", "K", 512, [h["host"] for h in hosts])
    assert c["mean"] == 0.001953125 and np.isclose(c["variance"]["sd_of_host_contrasts"], 0.005466, atol=1e-6)
    s = c["variance_independent"]["shares_of_host_contrast_variance"]
    assert abs(s["host"] - 0.5085) < 0.01 and abs(s["draw"] - 0.0773) < 0.01 and abs(s["genome"] - 0.4142) < 0.01
    pa, pb = c["rates"]  # no genome confirmed in both: the paired part exceeds the independent one by 2 pa pb / n
    assert c["confirmed_in_both"] == 0
    assert np.isclose(c["variance"]["genome"], c["variance_independent"]["genome"] + 2 * pa * pb / 512, rtol=1e-12)
