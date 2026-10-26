"""M4e (docs/memory/M4E-PLAN.md): the blocks, the paired genomes, the second pass and the readings."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m4"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))


@pytest.fixture(scope="module")
def M(tmp_path_factory):
    os.environ["MEMORY_M4E_SMOKE"] = "1"
    os.environ["MEMORY_M4E_OUT"] = str(tmp_path_factory.mktemp("m4e"))
    os.environ["MEMORY_M4E_SMOKE_N"] = "8"
    import m4e
    if not m4e.SMOKE:  # imported earlier without the smoke settings (a sabotage run imports it with them, patched)
        m4e = importlib.reload(m4e)
    yield m4e
    for k in ("MEMORY_M4E_SMOKE", "MEMORY_M4E_OUT", "MEMORY_M4E_SMOKE_N"):
        os.environ.pop(k, None)


@pytest.fixture(scope="module")
def R():
    import m4e_read
    return m4e_read


@pytest.fixture(scope="module")
def host(M):
    con, _ = M.m4d.build_host("SH", 2019100)
    return con


@pytest.fixture(scope="module")
def drawn(M, host):
    hb = M.host_block(host)
    blocks, info = M.draw_blocks(0, 0, hb)
    return hb, blocks, info


# ---------------------------------------------------------------------------------------------------------- the blocks
def test_every_block_follows_the_plan(M, drawn):
    hb, blocks, info = drawn
    M.check_blocks(blocks, info, hb)
    off = ~np.eye(30, dtype=bool)
    assert info["E_h"] == int((hb[off] > 0).sum()) and np.isclose(info["S_h"], hb[off].sum())
    for a, total in (("U_LL", info["S_h"]), ("U_LH", M.N2_S), ("U_HL", info["S_h"]), ("U_HH", M.N2_S),
                     ("U_HX", 2 * M.N2_S), ("W", M.N2_S), ("K", M.N2_S)):
        assert np.isclose(blocks[a][off].sum(), total, rtol=1e-5), a
        assert np.array_equal(np.diag(blocks[a]), np.diag(hb)), a  # the host's autapses
    assert np.array_equal(blocks["T"], M.m4d.n2_block())
    lo = {tuple(x) for x in np.argwhere(off & (blocks["U_LL"] > 0))}
    hi = {tuple(x) for x in np.argwhere(off & (blocks["U_HH"] > 0))}
    assert lo < hi and len(hi) == 260  # nested supports


def test_the_block_check_catches_each_rule(M, drawn):
    hb, blocks, info = drawn
    off = ~np.eye(30, dtype=bool)
    for a, change in (("U_HH", lambda B: B.__setitem__(tuple(np.argwhere(off & (B > 0))[0]), 1.0)),  # unequal
                      ("W", lambda B: B.__setitem__((0, 0), B[0, 0] + 1)),  # the diagonal
                      ("K", lambda B: B.__setitem__(tuple(np.argwhere(off & (B > 0))[0]), 0.0)),  # a degree
                      ("T", lambda B: B.__setitem__((1, 2), B[1, 2] + 1))):
        bad = {k: v.copy() for k, v in blocks.items()}
        change(bad[a])
        with pytest.raises(SystemExit):
            M.check_blocks(bad, info, hb)


def test_the_reciprocal_matching_records_a_miss(M):
    Bn = M.m4d.n2_block()
    out, rec = M.match_recip(Bn, 1000, np.random.default_rng(0))  # unreachable
    assert not rec["matched"] and rec["achieved"] == M.m4d.block_stats(out)["reciprocal"]
    assert M.m4d.block_stats(out)["in_degree"] == M.m4d.block_stats(Bn)["in_degree"]


def test_a_clamped_magnitude_stops(M, host):
    g, _ = M.m4d.host_genomes(host, 2, 1)
    k = M.m4d.core_idx()
    chem = host.chem.copy()
    chem[k[0], k[1]] = 1e5
    with pytest.raises(SystemExit):
        M.check_clamp(g, M.c.S.masks(chem, host.gap.copy(), "huge"))


def test_the_paired_genome_keeps_the_outside_and_the_sham_is_exact(M, host, drawn):
    _, blocks, _ = drawn
    g, _ = M.m4d.host_genomes(host, 4, 5)
    signs = M.m4d.sign_matrix(g, 4, 6)
    M.m4d.sham_check(g, host, signs)
    con = M.arm_graph(host, "U_HH", blocks)
    M.m4d.check_outside(host, con)
    ga = M.m4d.paired_genome(g, con, signs)
    assert torch.equal(ga.tau, g.tau) and torch.equal(ga.bias, g.bias)


# ------------------------------------------------------------------------------------------------------ the second pass
def test_the_hold_continued_from_tick_2000_equals_a_longer_probe(M, host):
    g, cfg = M.m4d.host_genomes(host, 3, 11)
    long = M.P.probe_states(g, cfg, ticks=2060)
    short = M.P.probe_states(g, cfg)
    cont = M.continue_hold(g, cfg, short["end"], 60, tail=40)
    assert torch.equal(cont["end"], long["end"])
    assert np.array_equal(cont["tail"], long["tail"][:, -40:])
    # from tick 20, where the states still move (fading genomes stall in float32 well before tick 2000; the M2 pilot)
    early = M.P.probe_states(g, cfg, ticks=20)
    later = M.P.probe_states(g, cfg, ticks=80)
    cont = M.continue_hold(g, cfg, early["end"], 60, tail=40)
    assert torch.equal(cont["end"], later["end"]) and not torch.equal(early["end"], later["end"])
    assert np.array_equal(cont["tail"], later["dense"][:, -40:])


def test_the_oscillation_rerun_follows_the_requested_horizon(M, monkeypatch):
    calls = {}

    def fake_follow(g, cfg, initial, substeps=None, dtype=None, ticks=None, record=True, hook=None):
        calls["ticks"] = ticks
        n = 0
        for _ in range(ticks * substeps):
            n += 1
            hook(torch.zeros(1, 2, 3))
        return None

    monkeypatch.setattr(M.P, "follow_from", fake_follow)
    monkeypatch.setattr(M.P.K, "returns", lambda sub, maxlag: (calls.__setitem__("samples", len(sub)), None)[1])
    with pytest.raises(Exception):  # stops after the recurrence part; only the recording is under test
        M.P.oscillation_check(None, None, torch.zeros(3), np.zeros((200, 3)), None, None, 0, initial=torch.zeros(1, 2, 3),
                              eval_substeps=4, follow_ticks=500, tail_from=301)
    assert calls["ticks"] == 500 and calls["samples"] == 200 * 4


def test_the_rerun_from_the_pre_tail_state_records_the_same_substeps(M, host):
    """The oscillation check's rerun from the state TAIL ticks before the end records exactly the substeps a rerun from
    tick 2000 records over the same final ticks (here 40 of a 60-tick continuation, while the states still move)."""
    g, cfg = M.m4d.host_genomes(host, 1, 13)
    end = M.P.probe_states(g, cfg, ticks=20)["end"].to(torch.float32)
    cont = M.continue_hold(g, cfg, end, 60, tail=40)
    a, b = [], []
    n = {"a": 0}

    def hook_a(v):
        n["a"] += 1
        if n["a"] > 20 * 32:
            a.append(v.clone())

    M.P.follow_from(g, cfg, end, substeps=32, ticks=60, record=False, hook=hook_a)
    M.P.follow_from(g, cfg, cont["pre_tail"], substeps=32, ticks=40, record=False, hook=lambda v: b.append(v.clone()))
    assert len(a) == len(b) == 40 * 32 and all(torch.equal(x, y) for x, y in zip(a, b))
    assert not torch.equal(a[0], a[-1])


def test_the_default_horizon_is_the_frozen_one(M):
    import inspect
    for f in (M.P.full_classify, M.P.oscillation_check):
        p = inspect.signature(f).parameters
        assert p["follow_ticks"].default == M.P.FOLLOW == 2000 and p["tail_from"].default == M.P.TAIL_FROM == 1801


def test_merged_classes_and_the_audit(M):
    rec = {"class": [2, 0, 4, 2, 2], "audit": [3, 4], "second": {"ids": [1, 2, 3, 4], "class": [2, 0, 2, 2]}}
    assert M.merged_classes(rec) == [2, 2, 0, 2, 2]
    assert not M.audit_failed(rec)
    rec["second"]["class"] = [2, 0, 2, 1]  # an audited fading genome became separate states
    assert M.audit_failed(rec)


def test_the_audit_ids_are_fixed(M):
    a = M.audit_ids(3, 1, "K", 512)
    assert a == M.audit_ids(3, 1, "K", 512) and len(set(a)) == M.AUDIT_PER_PANEL == 40
    assert a != M.audit_ids(3, 1, "W", 512)


# ---------------------------------------------------------------------------------------------------------- readings
def test_the_two_fields_at_their_boundaries(R):
    assert R.direction((1e-9, 1)) == "raises" and R.direction((-1, -1e-9)) == "lowers"
    assert R.direction((0, 1)) == "direction unresolved"
    assert R.size((0.0011, 0.0035), 0.0) == ["at least 0.001", "no effect of 0.004 or more" + R.LIMIT]
    assert R.size((0.001, 0.0035), 0.0) == ["no effect of 0.004 or more" + R.LIMIT]
    assert R.size((-0.004, 0.0), 0.0) == ["size unresolved"]  # strictly inside
    assert R.size((-0.002, 0.002), 0.01) == [R.SINGLE_HOST]  # the guard
    assert R.size((-0.002, 0.002), 0.0, exclusions_ok=False) == ["size unresolved"]  # the coverage's response
    assert R.size((-0.0035, -0.0011), 0.0)[0] == "at least 0.001"


def test_the_envelope_decides_when_the_unresolved_could(R):
    h = 10
    sep = {"U_HH": [3] * h, "U_HL": [1] * h}
    unres = {"U_HH": [0] * h, "U_HL": [4] * h}  # counted against U_HH, every host's difference turns negative
    idx = np.random.default_rng(0).integers(0, h, (R.B, h))
    c = R.contrast(sep, unres, 1024, idx, "U_HH", "U_HL")
    assert c["direction_before_bounds"] == "raises" and c["envelope_direction"] == "direction unresolved"
    assert c["direction"] == R.BY_UNRESOLVED
    sep = {"U_HH": [8] * h, "U_HL": [1] * h}
    unres = {"U_HH": [0] * h, "U_HL": [0] * h}
    c = R.contrast(sep, unres, 1024, idx, "U_HH", "U_HL")
    assert c["direction"] == "raises"


def test_the_reader_refuses_fewer_than_ten_hosts(R):
    counts = {"sep": {a: [1] * 9 for a in ("I", "U_LL", "U_LH", "U_HL", "U_HH")},
              "unres": {a: [0] * 9 for a in ("I", "U_LL", "U_LH", "U_HL", "U_HH")}}
    with pytest.raises(SystemExit):
        R.read(counts, 1024, True)


def test_the_poisson_slope_recovers_a_known_dose(R):
    x = np.log([1.0, 2.0, 4.0, 8.0])
    n = 10_000_000
    counts = np.round(n * np.exp(-6 + 1.5 * x))
    a, b = R.poisson_slope(counts, n, x)
    assert abs(b - 1.5) < 1e-3 and abs(a + 6) < 1e-3
    assert R.poisson_slope([0, 0, 0], 100, [0.0, 1.0, 2.0]) is None
    # switches in one arm only: the MLE does not exist (Fable, Astra, round 1: the smoke host's own pattern)
    assert R.poisson_slope([0, 0, 0, 5], 1024, np.log([1.0, 2.0, 4.0, 8.0])) is None
    assert R.poisson_slope([0, 1, 0, 0], 1024, np.log([3.0, 50.0, 1.0, 26.0])) is None
    # one switching arm at an interior dose has a finite slope (Astra, round 2, on the smoke host's S2 values)
    res = R.poisson_slope([0, 0, 0, 5], 1024, np.log([2.7816, 69.6586, 1.05915, 26.5239]))
    assert res is not None
    a, b = res
    assert abs(b - 0.464609) < 1e-3 and abs(a + 7.98953) < 1e-2


def test_the_dose_model_leaves_out_a_host_without_a_slope(R):
    h = 3
    sep = {"I": [0] * h, "U_LL": [0, 1, 2], "U_LH": [1, 3, 4], "U_HL": [0, 1, 1], "U_HH": [0, 2, 3], "W": [1, 2, 2],
           "K": [0, 1, 2]}
    s2 = {a: [v] * h for a, v in (("U_LL", 2.0), ("U_LH", 40.0), ("U_HL", 1.0), ("U_HH", 26.0), ("W", 71.0),
                                  ("K", 71.0))}
    out = R.dose_model(sep, 1024, s2, ["U_LL", "U_LH", "U_HL", "U_HH"], ["W", "K"])
    assert out["hosts_without_a_slope"] == [0] and len(out["slopes"]) == 2
    assert out["hosts_where_the_arm_lies_outside_the_U_range"] == {"W": 2, "K": 2}
    assert all(np.isfinite(out["slopes"]))


def test_the_coverage_simulation_reads_no_effect_as_no_effect(R):
    rng = np.random.default_rng(1)
    res = R.simulate(np.array([0.002, 0.005, 0.0]), "fixed", 0.0, rng, screens=40)
    assert res["at_least_bench"] <= 0.1 and 0.0 <= res["coverage"] <= 1.0


def test_a_record_must_carry_the_planned_second_pass(M):
    r = {"host": 0, "name": "SH-x"}
    n = M.N_DRAW
    audit = M.audit_ids(0, 0, "U_HH")
    cls = [2] * n
    cls[1] = 0  # a separate-states genome must be in the second pass
    want = sorted(set([1] + audit))
    rec = {"host": 0, "name": "SH-x", "draw": 0, "arm": "U_HH", "genome_seed": M.GENOME_SEED, "n": n,
           "arm_sha256": "h", "genomes": list(range(n)), "class": cls, "audit": audit,
           **{k: [0.0] * n for k in ("reason", "a", "root_distance", "readout_difference", "write_sq", "write_core")},
           "second": {"ids": want, "class": [2] * len(want),
                      **{k: [0.0] * len(want) for k in ("reason", "root_distance", "readout_difference")}}}
    M.validate(rec, r, 0, "U_HH", "h")
    short = [i for i in want if i != 1]
    rec["second"] = {"ids": short, "class": [2] * len(short),
                     **{k: [0.0] * len(short) for k in ("reason", "root_distance", "readout_difference")}}
    with pytest.raises(SystemExit):
        M.validate(rec, r, 0, "U_HH", "h")


def test_the_reader_checks_before_it_reads(M, R, monkeypatch):
    class Checked(Exception):
        pass

    def verify():
        raise Checked

    monkeypatch.setattr(M, "verify_run", verify)
    with pytest.raises(Checked):
        R.main()


def test_a_batched_continuation_replays_one_genome_exactly(M, host):
    """Production continues up to 128 genomes in a batch and reruns one genome from its pre-tail state: the batched
    continuation equals one genome's own, and its rerun records the same substeps (Fable, Astra, round 1)."""
    g, cfg = M.m4d.host_genomes(host, 128, 17)  # the production chunk (Fable, round 2)
    end = M.P.probe_states(g, cfg, ticks=20)["end"]
    batch = M.continue_hold(g, cfg, end, 60, tail=40)
    for k_ in (1, 77):
        one = M.continue_hold(g.select([k_]), cfg, end[k_:k_ + 1], 60, tail=40)
        assert torch.equal(batch["end"][k_:k_ + 1], one["end"])
        assert np.array_equal(batch["tail"][k_:k_ + 1], one["tail"])
        assert torch.equal(batch["pre_tail"][k_:k_ + 1], one["pre_tail"])
    mid = M.continue_hold(g.select(list(range(48))), cfg, end[:48], 60, tail=40)  # a typical second-pass batch (Fable)
    assert torch.equal(mid["end"], batch["end"][:48]) and torch.equal(mid["pre_tail"], batch["pre_tail"][:48])
    a, b = [], []
    n = {"a": 0}

    def hook_a(v):
        n["a"] += 1
        if n["a"] > 20 * 32:
            a.append(v.clone())

    M.P.follow_from(g.select([1]), cfg, end[1:2].to(torch.float32), substeps=32, ticks=60, record=False, hook=hook_a)
    M.P.follow_from(g.select([1]), cfg, batch["pre_tail"][1:2], substeps=32, ticks=40, record=False,
                    hook=lambda v: b.append(v.clone()))
    assert len(a) == len(b) == 40 * 32 and all(torch.equal(x, y) for x, y in zip(a, b))


def test_a_second_pass_code_outside_the_classes_is_refused(M):
    r = {"host": 0, "name": "SH-x"}
    n = M.N_DRAW
    audit = M.audit_ids(0, 0, "U_HH")
    rec = {"host": 0, "name": "SH-x", "draw": 0, "arm": "U_HH", "genome_seed": M.GENOME_SEED, "n": n,
           "arm_sha256": "h", "genomes": list(range(n)), "class": [2] * n, "audit": audit,
           **{k: [0.0] * n for k in ("reason", "a", "root_distance", "readout_difference", "write_sq", "write_core")},
           "second": {"ids": audit, **{k: [0.0] * len(audit) for k in ("reason", "root_distance",
                                                                      "readout_difference")},
                      "class": [2] * len(audit)}}
    M.validate(rec, r, 0, "U_HH", "h")
    rec["second"]["class"][0] = -1
    with pytest.raises(SystemExit):
        M.validate(rec, r, 0, "U_HH", "h")
    rec["second"]["class"][0] = 2
    rec["second"]["reason"] = rec["second"]["reason"][1:]
    with pytest.raises(SystemExit):
        M.validate(rec, r, 0, "U_HH", "h")


def test_a_host_seed_jump_must_be_recorded(M):
    h, kind, s0 = M.host_list()[0]
    rec = {"host": h, "ensemble": kind, "seed": s0, "name": f"{kind}-{s0}", "content_sha256": "a", "skipped": []}
    M.check_host_list([rec])
    jumped = {**rec, "seed": s0 + 50, "name": f"{kind}-{s0 + 50}"}
    with pytest.raises(SystemExit):
        M.check_host_list([jumped])


def test_a_failed_audit_puts_every_panel_back_on_its_first_pass(M, R, monkeypatch, tmp_path):
    """The global fallback through the reader's counting (Astra, round 1)."""
    import json
    n = M.N_DRAW
    r = {"host": 0, "name": "SH-x"}
    arms = ("I", "U_HH")
    files = {}
    for a in arms:
        audit = M.audit_ids(0, 0, a)
        cls = [2] * n
        cls[0] = 4  # unresolved in the first pass, separate states in the second
        ids = sorted(set([0] + audit))
        second = [0 if i == 0 else 2 for i in ids]
        if a == "U_HH":
            second[ids.index(audit[-1])] = 1  # an audited fading genome turned separate states
        rec = {"class": cls, "audit": audit, "valid": True,
               "second": {"ids": ids, "class": second, "reason": [""] * len(ids)}}
        f = tmp_path / f"{a}.json"
        f.write_text(json.dumps(rec))
        files[a] = f
    monkeypatch.setattr(M, "panel_file", lambda rr, d, a: files[a])
    monkeypatch.setattr(M, "validate", lambda *x: None)
    verified = [{"rec": r, "draw": 0, "arms": {a: (None, "h") for a in arms}}]
    counts = R.load_counts(verified, arms)
    assert not counts["use_second"] and counts["audit_failed"]
    assert counts["sep"]["I"] == [0] and counts["unres"]["I"] == [1]  # the first pass, for every panel
    assert R.classes(counts, ("SH-x", 0, "I"))[0] == 4  # and the tables take the same choice (Astra, round 2)


def test_a_size_field_holding_on_both_intervals_stands(R):
    h = 10
    idx = np.random.default_rng(0).integers(0, h, (R.B, h))
    sep = {"U_HH": [3] * h, "U_HL": [1] * h}  # 0.00195 in every host: at least 0.001 and inside 0.004
    unres = {"U_HH": [1] * h, "U_HL": [0] * h}  # for U_HH: 0.0029, still at least 0.001; the exclusion still holds
    c = R.contrast(sep, unres, 1024, idx, "U_HH", "U_HL")
    assert "at least 0.001" in c["size"]
    unres = {"U_HH": [3] * h, "U_HL": [0] * h}  # for U_HH: 0.0059, the exclusion fails on the envelope
    c = R.contrast(sep, unres, 1024, idx, "U_HH", "U_HL")
    assert c["size"] == ["at least 0.001"]


def test_a_fresh_skipped_seed_stops_the_hosts(M, host, monkeypatch):
    """check_skips regenerates every recorded skip: one that is fresh should have been used (Astra, round 1; its test,
    Fable, round 2)."""
    rec = {"name": "SH-9", "ensemble": "SH", "content_sha256": "c", "skipped": [{"seed": 1, "why": "used"}]}
    monkeypatch.setattr(M.m4d, "build_host", lambda kind, seed: (host, None))
    monkeypatch.setattr(M.m4d, "fresh", lambda n, d, u: False)
    M.check_skips([rec], (set(), set()))
    monkeypatch.setattr(M.m4d, "fresh", lambda n, d, u: True)
    with pytest.raises(SystemExit):
        M.check_skips([rec], (set(), set()))
