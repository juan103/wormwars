"""M4d (scripts/memory_m4/m4d.py, docs/memory/M4D-PLAN.md): the blocks, the paired genomes, the classification without
a floor, the hosts' freshness, record validation, and the reading with its host bootstrap and unresolved bounds."""
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m4"))
os.environ.setdefault("MEMORY_M4D_OUT", tempfile.mkdtemp(prefix="m4d-test-"))  # never the real run's folder
os.environ.setdefault("MEMORY_M4D_SMOKE", "1")


def _m4d():
    import m4d
    return m4d


def _host_and_genome(n=6):
    m4d = _m4d()
    host, _ = m4d.build_host("SH", 2019999, passes=1)
    g, cfg = m4d.host_genomes(host, n, 7998)
    return m4d, host, g, cfg


def test_the_readings_boundaries():
    import m4d_read
    m4d_read.test_rules()


def test_the_blocks_keep_what_the_plan_says():
    """Checked here independently of check_blocks: count, weights and autapses for every arm; degrees and out-strengths
    for R and Rr; 75 reciprocal pairs for Rr; N2's positions for P; N2's block for T."""
    m4d = _m4d()
    Bn = m4d.n2_block()
    off = ~np.eye(len(Bn), dtype=bool)
    blocks, info = m4d.draw_blocks(3)
    deg = lambda B: ((B * off > 0).sum(0).tolist(), (B * off > 0).sum(1).tolist())  # noqa: E731
    recip = lambda B: int(((B * off > 0) & (B * off > 0).T).sum() // 2)  # noqa: E731
    for arm, B in blocks.items():
        assert int((B * off > 0).sum()) == 260
        assert np.array_equal(np.sort(B[off & (B > 0)]), np.sort(Bn[off & (Bn > 0)]))
        assert np.array_equal(np.diag(B), np.diag(Bn)) and int((np.diag(Bn) > 0).sum()) == 8
    for arm in ("R", "Rr"):
        assert deg(blocks[arm]) == deg(Bn)
        assert np.allclose((blocks[arm] * off).sum(1), (Bn * off).sum(1))
        assert info[arm]["accepted"] == 20 * 260
        assert not np.array_equal(blocks[arm] > 0, Bn > 0)
    assert recip(blocks["Rr"]) == 75 and recip(Bn) == 75 and recip(blocks["R"]) != 75
    assert np.array_equal(blocks["P"] > 0, Bn > 0) and not np.array_equal(blocks["P"], Bn)
    assert np.array_equal(blocks["T"], Bn)
    assert deg(blocks["D"]) != deg(Bn)
    m4d.check_blocks(blocks)


def test_a_block_breaking_a_rule_is_rejected():
    m4d = _m4d()
    blocks, _ = m4d.draw_blocks(0)
    B = blocks["R"].copy()
    i, j = map(int, np.argwhere((B > 0) & ~np.eye(len(B), dtype=bool))[0])
    free = [(a, b) for a in range(len(B)) for b in range(len(B)) if a != b and B[a, b] == 0 and a != i][0]
    B[free], B[i, j] = B[i, j], 0  # moves an edge's source: out-degrees change
    with pytest.raises(SystemExit):
        m4d.check_blocks({**blocks, "R": B})


def test_the_arm_graph_changes_only_the_block():
    m4d = _m4d()
    host, _ = m4d.build_host("SH", 2019999, passes=1)
    blocks, _ = m4d.draw_blocks(0)
    k = m4d.core_idx()
    for arm in m4d.ARMS:
        con = m4d.arm_graph(host, arm, blocks)
        m4d.check_outside(host, con)
        if arm != "I":
            assert np.array_equal(con.chem[np.ix_(k, k)], blocks["T" if arm == "T+G" else arm])
        same_gap = np.array_equal(con.gap, host.gap)
        assert same_gap == (arm != "T+G")
    bad = host.chem.copy()
    bad[0, 1] += 1.0
    with pytest.raises(SystemExit):
        m4d.check_outside(host, m4d.c.S.masks(bad, host.gap, "bad"))


def test_the_paired_genomes():
    """Outside the block every parameter is the intact genome's; block magnitudes follow Genome.random's arithmetic;
    signs are the intact genome's at the host's block edges and shared across arms; the sham is exact."""
    m4d, host, g, cfg = _host_and_genome()
    n = g.n_strains
    signs = m4d.sign_matrix(g, n, 11)
    m4d.sham_check(g, host, signs)
    blocks, _ = m4d.draw_blocks(0)
    k = m4d.core_idx()
    pos = {int(x): a for a, x in enumerate(k)}
    inc = np.zeros(host.n, bool)
    inc[k] = True
    hs = g.spec
    hidx = {(int(a), int(b)): e for e, (a, b) in enumerate(zip(hs.chem_i.numpy(), hs.chem_j.numpy()))}
    mean = float(hs.chem_anat.mean())
    by_arm = {}
    for arm in ("T", "P", "R", "T+G"):
        ga = m4d.paired_genome(g, m4d.arm_graph(host, arm, blocks), signs)
        assert torch.equal(ga.tau, g.tau) and torch.equal(ga.bias, g.bias)
        ci, cj = ga.spec.chem_i.numpy(), ga.spec.chem_j.numpy()
        ws = {}
        for e, (a, b) in enumerate(zip(ci, cj)):
            a, b = int(a), int(b)
            if inc[a] and inc[b]:
                want = 0.2 * float(ga.spec.chem_anat[e]) / mean
                assert np.allclose(ga.w[:, e].abs().numpy(), want, rtol=1e-6)
                assert np.array_equal(np.sign(ga.w[:, e].numpy()), signs[:, pos[a], pos[b]])
                if (a, b) in hidx:  # the host's own block edge keeps the intact genome's sign
                    assert np.array_equal(np.sign(ga.w[:, e].numpy()), np.sign(g.w[:, hidx[(a, b)]].numpy()))
                ws[(a, b)] = np.sign(ga.w[:, e].numpy())
            else:
                assert torch.equal(ga.w[:, e], g.w[:, hidx[(a, b)]])
        by_arm[arm] = ws
        gi, gj = ga.spec.gap_i.numpy(), ga.spec.gap_j.numpy()
        hg = {(int(a), int(b)): e for e, (a, b) in enumerate(zip(hs.gap_i.numpy(), hs.gap_j.numpy()))}
        for e, (a, b) in enumerate(zip(gi, gj)):
            if not (inc[a] and inc[b]):
                assert torch.equal(ga.g[:, e], g.g[:, hg[(int(a), int(b))]])
    common = set(by_arm["T"]) & set(by_arm["R"])
    assert common and all(np.array_equal(by_arm["T"][e], by_arm["R"][e]) for e in common)
    assert set(by_arm["T"]) == set(by_arm["P"])
    host_edges = [e for e in hidx if inc[e[0]] and inc[e[1]]]
    assert any(e in by_arm["T"] for e in host_edges)


def test_the_sham_check_catches_a_redrawn_genome():
    from wormwars.brain import Genome
    m4d, host, g, cfg = _host_and_genome()
    other = Genome.random(g.spec, cfg.brain, g.n_strains, generator=torch.Generator().manual_seed(1), device="cpu")
    signs = m4d.sign_matrix(g, g.n_strains, 11)
    with pytest.raises(SystemExit):
        m4d.sham_check(other, host, signs)


def test_every_genome_is_classified_without_a_floor(monkeypatch):
    """With the eligibility floor raised above every genome's start difference, every genome is still classified."""
    m4d, host, g, cfg = _host_and_genome(4)
    monkeypatch.setattr(m4d.c, "START_FLOOR", 1e9)
    cols, val = m4d.classify_all(g, cfg)
    assert len(cols["class"]) == 4 and all(isinstance(x, int) for x in cols["class"])
    assert val["eligible"] == 0 and len(cols["write_core"]) == 4


def test_the_hosts_are_fresh():
    m4d = _m4d()
    names, hashes = m4d.used_graphs()
    assert "SH-2010000" in names and "SH-10000" in names and len(hashes) >= 2000
    assert not m4d.fresh("SH-2010000", "x", (names, hashes))
    assert not m4d.fresh("SH-2011000", next(iter(hashes)), (names, hashes))
    assert m4d.fresh("SH-2011000", "x", (names, hashes))
    assert all(f"{k}-{m4d.SEED_BASE[k] + 1000 + i}" not in names for k in m4d.ENSEMBLES for i in (0, 1))  # the run's


def test_a_used_graph_is_recognised_by_its_content():
    """A true positive (Fable, round 2): 03mc's SH-2010000, rebuilt by the sampler, hashes to a recorded content."""
    m4d = _m4d()
    con, _ = m4d.build_host("SH", 2010000)
    names, hashes = m4d.used_graphs()
    assert m4d.sha_content(con.chem, con.gap) in hashes
    assert not m4d.fresh("SH-2011000", m4d.sha_content(con.chem, con.gap), (names, hashes))


def test_the_host_list_is_checked(monkeypatch):
    m4d = _m4d()
    plan = [(h, k, s) for h, k in enumerate(("SH", "SH", "SH-route")) for s in [2011000 + h]]
    monkeypatch.setattr(m4d, "host_list", lambda: plan)
    monkeypatch.setattr(m4d, "HOSTS_PER", 2)
    good = [{"host": h, "ensemble": k, "seed": s, "name": f"{k}-{s}", "content_sha256": str(h)} for h, k, s in plan]
    m4d.check_host_list(good)
    dup = [dict(x) for x in good]
    dup[1].update(seed=2011000, name="SH-2011000")  # host 1 repeats host 0
    skip = [dict(x) for x in good]
    skip[2].update(seed=2011003, name="SH-route-2011003")  # off its seed sequence
    same = [dict(x) for x in good]
    same[2]["content_sha256"] = "0"
    for bad in (dup, skip, same, good[:2]):
        with pytest.raises(SystemExit):
            m4d.check_host_list(bad)


def test_records_are_validated():
    m4d = _m4d()
    r = {"host": 0, "name": "SH-2019000"}
    n = m4d.N_PANEL
    good = {"host": 0, "name": "SH-2019000", "arm": "T", "genome_seed": m4d.GENOME_SEED, "n": n, "arm_sha256": "abc",
            "genomes": list(range(n)), **{c_: [0] * n for c_ in ("class", "reason", "a", "root_distance",
                                                                 "readout_difference", "write_sq", "write_core")}}
    m4d.validate(good, r, "T", "abc")
    for bad in ({**good, "arm": "R"}, {**good, "genome_seed": 1}, {**good, "class": [0] * (n - 1)},
                {**good, "genomes": list(range(1, n + 1))}, {**good, "class": [9] * n}, {**good, "arm_sha256": "abd"}):
        with pytest.raises(SystemExit):
            m4d.validate(bad, r, "T", "abc")


def test_the_envelope_covers_one_host_assignments():
    """Astra's counterexample (round 2): T has 5 switches and 20 unresolved genomes in every host, I and R none. Both
    extreme assignments read positive, but assigning one host's unresolved genomes as switches lowers the widened
    interval below the margin; the envelope must see it, and the reading must not be called robust."""
    import m4d_read
    arms = ("I", "D", "R", "Rr", "P", "T", "T+G")
    sep = {a: [0] * 10 for a in arms}
    sep["T"] = [5] * 10
    unres = {a: [0] * 10 for a in arms}
    unres["T"] = [20] * 10
    out = m4d_read.read(sep, unres, 1024, True)
    assert out["reading_before_bounds"] == m4d_read.READINGS[0]
    one = [25] + [5] * 9
    idx = np.random.default_rng(m4d_read.SEED_BOOT).integers(0, 10, (m4d_read.B, 10))
    low = m4d_read.interval(np.array(one) / 1024, idx, True)[0]
    assert low < m4d_read.MARGIN and out["envelope"]["D_TI"][0] <= low + 1e-12
    assert not out["robust"] and out["reading"] == m4d_read.BY_UNRESOLVED


def test_the_coverage_simulation():
    """The widened interval covers at least as often as the bootstrap's; a zero shift is never read as positive."""
    import m4d_read
    rng = np.random.default_rng(3)
    rates = np.array([0.0] * 19 + [0.003] * 6 + [0.006] * 5)
    r = m4d_read.simulate(rates, "fixed", 0.004, rng, screens=40)
    assert r["coverage_widened"] >= r["coverage"] and 0 < r["coverage"] <= 1
    z = m4d_read.simulate(rates, "fixed", 0.0, rng, screens=40)
    assert z["lower_above_margin"] == 0
    s = m4d_read.shifts("sparse", 0.004, np.random.default_rng(1), 10000)
    assert abs(s.mean() - 0.004) < 0.0006 and set(np.unique(s)) <= {0.0, 0.04}
    e = m4d_read.shifts("ensemble", 0.004, np.random.default_rng(1))
    assert np.isclose(e.mean(), 0.004) and (e > 0).sum() == 4


def test_the_host_bootstrap():
    """The interval resamples hosts only: it equals the percentiles of host-resampled means of the host differences."""
    import m4d_read
    rng = np.random.default_rng(5)
    arms = ("I", "D", "R", "Rr", "P", "T", "T+G")
    sep = {a: rng.integers(0, 20, 10).tolist() for a in arms}
    unres = {a: [0] * 10 for a in arms}
    out = m4d_read.read(sep, unres, 1024, False, seed=7)
    idx = np.random.default_rng(7).integers(0, 10, (m4d_read.B, 10))
    d = (np.array(sep["T"]) - np.array(sep["R"])) / 1024
    m = d[idx].mean(1)
    assert np.allclose(out["D_TR"]["interval"], [np.percentile(m, 5), np.percentile(m, 95)])
    assert np.isclose(out["D_TR"]["D"], d.mean())
    w = m4d_read.read(sep, unres, 1024, True, seed=7)["D_TR"]["interval"]
    tl, th = m4d_read.t_interval(d)
    assert np.isclose(w[0], min(np.percentile(m, 5), tl)) and np.isclose(w[1], max(np.percentile(m, 95), th))


def test_the_unresolved_genomes_bound_the_reading():
    import m4d_read
    arms = ("I", "D", "R", "Rr", "P", "T", "T+G")
    base = {a: [2] * 10 for a in arms}
    sep = {**base, "T": [30] * 10}
    sep["I"] = [0, 1, 2, 0, 1, 2, 0, 1, 2, 1]
    sep["R"] = [1, 2, 0, 1, 2, 0, 1, 2, 0, 1]
    none = {a: [0] * 10 for a in arms}
    clean = m4d_read.read(sep, none, 1024, True)
    assert clean["reading"] == m4d_read.READINGS[0] and clean["robust"]
    many = {**none, "R": [40] * 10}  # if R's unresolved genomes were switches, T would not beat R
    out = m4d_read.read(sep, many, 1024, True)
    assert out["reading_before_bounds"] == m4d_read.READINGS[0] and not out["robust"]
    assert out["reading"].startswith("Unresolved (the unresolved genomes")


def test_the_companion_takes_only_the_block_and_core_parameters():
    m4d, host, g, cfg = _host_and_genome(3)
    from wormwars.brain import Genome
    sel = Genome.random(g.spec, cfg.brain, 3, generator=torch.Generator().manual_seed(2), device="cpu")
    out = m4d.with_selected(g, sel)
    k = m4d.core_idx()
    inc = np.zeros(host.n, bool)
    inc[k] = True
    ci, cj = g.spec.chem_i.numpy(), g.spec.chem_j.numpy()
    blk = inc[ci] & inc[cj]
    assert torch.equal(out.w[:, blk], sel.w[:, blk]) and torch.equal(out.w[:, ~blk], g.w[:, ~blk])
    assert torch.equal(out.tau[:, k], sel.tau[:, k]) and torch.equal(out.tau[:, ~inc], g.tau[:, ~inc])
    assert torch.equal(out.bias[:, k], sel.bias[:, k]) and torch.equal(out.g, g.g)


def test_the_reader_checks_before_it_reads(monkeypatch):
    """The reader's entry point calls verify_run before anything else (Astra, round 3)."""
    import m4d_read
    m4d = _m4d()

    def stop():
        raise RuntimeError("verify_run was called")
    monkeypatch.setattr(m4d, "verify_run", stop)
    with pytest.raises(RuntimeError, match="verify_run was called"):
        m4d_read.main()


def test_the_reader_validates_every_panel_against_its_arm_graph():
    import json
    import m4d_read
    m4d = _m4d()
    n = m4d.N_PANEL
    r = {"host": 0, "name": "SH-reader-test"}
    (m4d.OUT / "arms").mkdir(parents=True, exist_ok=True)
    cols = {c_: [0] * n for c_ in ("class", "reason", "a", "root_distance", "readout_difference", "write_sq", "write_core")}
    for a in m4d.ARMS:
        json.dump({"host": 0, "name": r["name"], "arm": a, "genome_seed": m4d.GENOME_SEED, "n": n,
                   "arm_sha256": "bad" if a == "P" else "ok", "genomes": list(range(n)), **cols},
                  open(m4d.panel_file(r, a), "w"))
    verified = [{"rec": r, "arms": {a: (None, "ok") for a in m4d.ARMS}}]
    with pytest.raises(SystemExit):
        m4d_read.load_counts(verified, m4d.ARMS, n)
    json.dump({**json.load(open(m4d.panel_file(r, "P"))), "arm_sha256": "ok"}, open(m4d.panel_file(r, "P"), "w"))
    sep, unres, _ = m4d_read.load_counts(verified, m4d.ARMS, n)
    assert sep["T"] == [n] and unres["T"] == [0]  # class 0 is separate states
    with pytest.raises(SystemExit):  # one host is never read
        m4d_read.read(sep, unres, n, True)


def test_the_paired_counts():
    import m4d_read
    rng = np.random.default_rng(4)
    pb, pt = np.full(400, 0.01), np.full(400, 0.02)
    for pairing in m4d_read.PAIRINGS:
        ct, cb = m4d_read.paired_counts(pb, pt, pairing, 1024, rng)
        assert abs(ct.mean() / 1024 - 0.02) < 0.002 and abs(cb.mean() / 1024 - 0.01) < 0.002
    ct, cb = m4d_read.paired_counts(pb, pt, "nested", 1024, rng)
    assert (ct >= cb).all()  # every comparator switch is also a T switch
    dis = m4d_read.paired_counts(pb, pt, "disjoint", 1024, rng)
    nes = m4d_read.paired_counts(pb, pt, "nested", 1024, rng)
    assert np.var(dis[0] - dis[1]) > np.var(nes[0] - nes[1])
    one = m4d_read.shifts("one host", 0.0012, np.random.default_rng(2))
    assert (one > 0).sum() == 1 and np.isclose(one.max(), 0.012)
