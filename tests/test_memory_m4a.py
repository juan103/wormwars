"""M4a (scripts/memory_m4, docs/memory/M4A-PLAN.md): the cut and its window, the matched controls' search, the match
tick, Part 2's outcomes and the readings' boundaries."""
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m4"))


def test_the_readings_boundaries():
    import m4a_read
    m4a_read.test_rules()


def test_the_matching_search():
    """Smallest matching k; bisection between grid values that bracket m*; every grid value evaluated without assuming
    monotonicity; 'unmatched' (k = 0) when nothing matches or m* is not finite."""
    import m4a
    kmax = 1000
    calls = []

    def evalm(k):  # m(k) = k / kmax, except a bump at k = 1000 back to 0
        k = np.asarray(k)
        calls.append(k.copy())
        return np.where(k >= kmax, 0.0, k / kmax)

    mstar = np.array([0.5, 0.0123, 2.0, np.nan, 0.3])
    best, cand = m4a.match(evalm, kmax, mstar)
    grid = m4a.grid(kmax)
    assert all(any(k == g for k, _ in cand[0]) for g in grid)  # every grid value evaluated
    assert 0 < best[0] and abs(best[0] / kmax - 0.5) <= 0.2 * 0.5  # within tolerance
    assert best[0] not in grid.tolist() or best[0] == min(k for k, m in cand[0] if abs(m - 0.5) <= 0.1)
    assert best[0] == min(k for k, m in cand[0] if abs(m - 0.5) <= 0.1)  # the smallest match among candidates
    assert best[2] == 0 and best[3] == 0  # out of range, and not finite: unmatched
    assert 0 < best[4] < 300  # bisection reaches below the grid value that first matched
    # m* = 0.0123 is small: the absolute tolerance 0.01 applies
    assert abs(best[1] / kmax - 0.0123) <= 0.01


def test_the_match_uses_the_windows_third_tick_only():
    """No quantity after the window's third tick chooses a control: three_ticks steps exactly three times."""
    import m4a

    class Count:
        n = 0

        def step(self, v, cur):
            Count.n += 1
            return v

    m4a.three_ticks(Count(), torch.zeros(1), None)
    assert Count.n == 3 and m4a.MATCH_TICK == 3


def test_masks_and_the_cut():
    """prefix_mask takes each strain's own first k edges; cut() zeroes exactly those and leaves the genome unchanged."""
    import m4a
    import common as c
    g, cfg = c.S.genomes(c.S.CON, 3, 7600)
    order = np.stack([np.random.default_rng(i).permutation(g.w.shape[1]) for i in range(3)])
    m = m4a.prefix_mask(g, order, [0, 2, 5])
    assert m[0].sum() == 0 and set(np.where(m[1])[0]) == set(order[1, :2]) and set(np.where(m[2])[0]) == set(order[2, :5])
    w0 = g.w.clone()
    gc = m4a.cut(g, m)
    assert torch.equal(g.w, w0)  # the original is untouched, so the intact brain is restored after the window
    assert (gc.w[torch.as_tensor(m)] == 0).all() and torch.equal(gc.w[torch.as_tensor(~m)], w0[torch.as_tensor(~m)])


def test_the_window_switches_brains_and_back():
    """follow_arm uses the cut brain inside the window only: a run cut for ticks 2 to 3 equals stepping by hand, and
    a cut of no edges equals the intact run bitwise."""
    import m4a
    import common as c
    from wormwars.brain import Brain
    g, cfg = c.S.genomes(c.S.CON, 2, 7600)
    brain, v0, food = c.ramp(g, cfg)
    cidx = m4a.core()
    internal, _ = m4a.edge_sets(g.spec, cidx)
    bc = Brain(m4a.cut(g, m4a.common_mask(g, internal)))
    rec, _ = m4a.follow_arm(brain, bc, cfg, v0, food, (2, 3), 6, cidx)
    cur = c.at(cfg, g.spec.n, 2, [food, food])
    v = v0
    for t in range(1, 7):
        v = (bc if 2 <= t <= 3 else brain).step(v, cur)
    assert np.allclose(rec["nv"][:, 6], m4a.norms(v, cidx)[0], rtol=0, atol=0)
    b0 = Brain(m4a.cut(g, np.zeros(tuple(g.w.shape), bool)))
    r0, _ = m4a.follow_arm(brain, b0, cfg, v0, food, (1, 6), 6, cidx)
    ri, _ = m4a.follow_arm(brain, brain, cfg, v0, food, None, 6, cidx)
    assert np.array_equal(r0["nv"], ri["nv"]) and np.array_equal(r0["dy"], ri["dy"])


def test_part_2_outcomes():
    import m4a
    a, b = np.zeros(4), np.ones(4)
    stored = np.stack([a, b])
    assert m4a.assign(stored, np.stack([a, b]), ["reached"] * 2) == "both kept"
    assert m4a.assign(stored, np.stack([b, a]), ["reached"] * 2) == "swapped"
    assert m4a.assign(stored, np.stack([a, a + 1e-9]), ["reached"] * 2) == "erased"
    assert m4a.assign(stored, np.stack([a, a + 0.5]), ["reached"] * 2) == "other root"  # a third root (Fable)
    assert m4a.assign(stored, np.stack([a, b]), ["reached", "not approaching"]) == "not reached"


def test_part_2s_gate_holds_on_a_restart(tmp_path, monkeypatch):
    """Astra, round 3: a saved Part 2 record whose intact arm lost a root must stop the run again on restart."""
    import json
    import pytest
    import m4a
    monkeypatch.setattr(m4a, "OUT", tmp_path)
    rec = {"panel": "N2__7600", "genomes": [3, 5], "arms": {"intact": ["both kept", "erased"]}}
    json.dump(rec, open(tmp_path / "part2__N2__7600.json", "w"))
    with pytest.raises(SystemExit):
        m4a.run_part2_graph("N2__7600", "N2", 7600)


def test_cutting_every_edge_equals_zero_weights():
    """The plan's check: an all-true mask equals a genome with w = 0, bitwise, through the window."""
    import m4a
    import common as c
    from wormwars.brain import Brain
    g, cfg = c.S.genomes(c.S.CON, 2, 7600)
    brain, v0, food = c.ramp(g, cfg)
    cidx = m4a.core()
    b_all = Brain(m4a.cut(g, np.ones(tuple(g.w.shape), bool)))
    b_zero = Brain(g.with_params(w=torch.zeros_like(g.w)))
    r1, _ = m4a.follow_arm(brain, b_all, cfg, v0, food, (1, 4), 8, cidx)
    r2, _ = m4a.follow_arm(brain, b_zero, cfg, v0, food, (1, 4), 8, cidx)
    assert np.array_equal(r1["nv"], r2["nv"]) and np.array_equal(r1["dy"], r2["dy"])


def test_the_random_cuts_follow_c3s_endpoint_degrees():
    """Fable, round 2: each draw has as many external edges as C3 has internal ones, without repeats, all external,
    with C3's per-bin counts of summed endpoint degree wherever the bin has enough external edges."""
    import m4a
    import common as c
    g, cfg = c.S.genomes(c.S.CON, 1, 7600)
    internal, external = m4a.edge_sets(g.spec, m4a.core())
    draws = m4a.stratified_draws(g.spec, internal, external, 4, 1)
    di, de = m4a.endpoint_degree(g.spec, internal), m4a.endpoint_degree(g.spec, external)
    q = np.quantile(di, np.linspace(0, 1, m4a.BINS + 1))
    q[0], q[-1] = -np.inf, np.inf
    b = lambda d: np.clip(np.searchsorted(q, d, side="right") - 1, 0, m4a.BINS - 1)  # noqa: E731
    for e in draws:
        assert len(e) == len(internal) == len(set(e.tolist())) and set(e.tolist()) <= set(external.tolist())
        got = np.bincount(b(m4a.endpoint_degree(g.spec, e)), minlength=m4a.BINS)
        want = np.bincount(b(di), minlength=m4a.BINS)
        avail = np.bincount(b(de), minlength=m4a.BINS)
        assert all(got[k] >= min(want[k], avail[k]) for k in range(m4a.BINS))
    assert not np.array_equal(np.sort(draws[0]), np.sort(draws[1]))


def test_weight_stratified_draws_follow_c3s_weights():
    """The weight family: C3's per-bin counts of anatomical weight wherever the bin has enough external edges."""
    import m4a
    import common as c
    g, cfg = c.S.genomes(c.S.CON, 1, 7600)
    internal, external = m4a.edge_sets(g.spec, m4a.core())
    key = g.spec.chem_anat.numpy()
    q = np.quantile(key[internal], np.linspace(0, 1, m4a.BINS + 1))
    q[0], q[-1] = -np.inf, np.inf
    b = lambda d: np.clip(np.searchsorted(q, d, side="right") - 1, 0, m4a.BINS - 1)  # noqa: E731
    for e in m4a.stratified_draws(g.spec, internal, external, 3, 2, key=key):
        got, want = np.bincount(b(key[e]), minlength=m4a.BINS), np.bincount(b(key[internal]), minlength=m4a.BINS)
        avail = np.bincount(b(key[external]), minlength=m4a.BINS)
        assert len(e) == len(internal) and all(got[k] >= min(want[k], avail[k]) for k in range(m4a.BINS))


def test_m4b_reading_and_contrast():
    import m4b_read
    m4b_read.test_rules()


def test_m4b_own_location_sets():
    """M4b: the top-difference neurons are the k largest |v1 - v2|; the own set's edges lie inside them, the controls'
    outside, as many as the own set's, without repeats."""
    import m4a
    import m4b
    import common as c
    roots = np.zeros((2, 302))
    roots[0, [5, 7, 9]] = [3.0, 2.0, 1.0]
    assert m4b.top_difference(roots, 2).tolist() == [5, 7]
    g, cfg = c.S.genomes(c.S.CON, 1, 7600)
    nodes = np.arange(40, 70)
    inside, outside = m4b.set_edges(g.spec, nodes)
    i, j = g.spec.chem_i.numpy(), g.spec.chem_j.numpy()
    assert np.isin(i[inside], nodes).all() and np.isin(j[inside], nodes).all() and (i[inside] != j[inside]).all()
    assert (~np.isin(i[outside], nodes)).all() and (~np.isin(j[outside], nodes)).all()
    for e in m4a.stratified_draws(g.spec, inside, outside, 3, 1, key=g.spec.chem_anat.numpy()):
        assert len(e) == len(inside) == len(set(e.tolist())) and set(e.tolist()) <= set(outside.tolist())
    out = m4b.out_edges(g.spec, nodes)  # Fable, round 2: presynaptic inside, postsynaptic outside, no autapses
    assert len(out) and np.isin(i[out], nodes).all() and (~np.isin(j[out], nodes)).all() and (i[out] != j[out]).all()
    k = min(len(inside), len(out))
    for e in m4a.stratified_draws(g.spec, inside[:k], out, 3, 1, key=g.spec.chem_anat.numpy()):
        assert len(e) == k == len(set(e.tolist())) and set(e.tolist()) <= set(out.tolist())


def test_m4b_rejects_invalid_records():
    """Astra, round 1: a saved panel with other genome ids (a smoke), an incomplete arm or a failed intact arm stops the
    run and the reading."""
    import pytest
    import m4b
    arms = {a: ["both kept", "erased"] for a in m4b.expected_arms("selected")}
    arms["intact"] = ["both kept"] * 2
    good = {"panel": "X", "role": "selected", "genomes": [1, 2], "info": [{"genome": 1}, {"genome": 2}], "arms": arms}
    m4b.validate(good, [1, 2], "X", "selected")
    with pytest.raises(SystemExit):
        m4b.validate(good, [1, 2, 3])  # truncated, as a smoke record would be
    with pytest.raises(SystemExit):
        m4b.validate({**good, "arms": {**arms, "own": ["erased"]}}, [1, 2])  # an incomplete arm
    with pytest.raises(SystemExit):
        m4b.validate({**good, "arms": {k: v for k, v in arms.items() if k != "out3"}}, [1, 2])  # a missing arm
    with pytest.raises(SystemExit):
        m4b.validate({**good, "arms": {**arms, "intact": ["both kept", "erased"]}}, [1, 2])  # failed intact
    with pytest.raises(SystemExit):
        m4b.validate(good, [1, 2], "Y")  # another panel's record
    with pytest.raises(SystemExit):
        m4b.validate({**good, "info": [{"genome": 2}, {"genome": 1}]}, [1, 2])  # info not aligned


def test_m4b_n2_records_are_checked_against_m4a(tmp_path):
    """Astra, round 2: an N2 record whose C3 outcomes differ from M4a's Part 2 is rejected, whatever flag it carries."""
    import json
    import pytest
    import m4b
    real = json.load(open(m4b.ROOT / "runs" / "memory-m4a" / "part2__N2__7600.json"))
    ids = real["genomes"]
    arms = {a: ["both kept"] * len(ids) for a in m4b.expected_arms("N2")}
    arms["intact"], arms["C3"] = real["arms"]["intact"], real["arms"]["C3"]
    rec = {"panel": "N2__7600", "role": "N2", "genomes": ids, "info": [{"genome": i} for i in ids], "arms": arms,
           "matches_m4a_part2": True}
    m4b.validate(rec, ids, "N2__7600", "N2")
    changed = list(real["arms"]["C3"])
    changed[0] = "both kept" if changed[0] != "both kept" else "erased"
    with pytest.raises(SystemExit):
        m4b.validate({**rec, "arms": {**arms, "C3": changed}}, ids, "N2__7600", "N2")


def test_m4c_reading_and_bootstrap():
    import m4c_read
    m4c_read.test_rules()


def test_m4c_matched_draws():
    """M4c: a matched draw has the target's count, from the pool, without repeats, its summed weight within the
    tolerance and each weight near one of the target's; a weight fill is from the pool, without repeats, within the
    tolerance."""
    import m4c
    rng = np.random.default_rng(3)
    key = np.concatenate([rng.integers(1, 60, 400), rng.integers(1, 5, 2000)]).astype(float)
    target = np.arange(30)
    pool = np.arange(30, len(key))
    for _ in range(5):
        e, r = m4c.matched_draw(target, pool, key, rng)
        assert e is not None and len(e) == len(target) == len(set(e.tolist())) and set(e.tolist()) <= set(pool.tolist())
        assert abs(key[e].sum() / key[target].sum() - 1) <= m4c.TOL + 1e-12 and abs(r - key[e].sum() / key[target].sum()) < 1e-9
        tw, ew = np.sort(key[target]), np.sort(key[e])
        assert (np.abs(ew - tw) <= np.maximum(1.0, m4c.NEAR * tw) + 1e-9).mean() >= 0.9
        f, r = m4c.weight_fill(float(key[target].sum()), pool, key, rng)
        assert len(f) == len(set(f.tolist())) and set(f.tolist()) <= set(pool.tolist())
        assert abs(key[f].sum() / key[target].sum() - 1) <= m4c.TOL + 1e-12


def test_m4c_sets_follow_the_plan():
    """M4c: the sides are M4b's dissection arms (26 and 29 edges, weight 560 and 503); no control holds an edge of
    either RIA (checked here independently of the code's own rule); the sets pass check_sets, and a set breaking a
    rule does not."""
    import copy
    import pytest
    import m4a
    import m4c
    c = m4a.c
    spec = m4c.n2_spec()
    sets = m4c.build_sets(spec)
    m4c.check_sets(sets, spec)
    key = spec.chem_anat.numpy()
    i, j = spec.chem_i.numpy(), spec.chem_j.numpy()
    ria = {c.NAMES.index("RIAL"), c.NAMES.index("RIAR")}
    for side, n, w in (("RIAR", 26, 560.0), ("RIAL", 29, 503.0)):
        s = sets["sides"][side]
        assert len(s["edges"]) == n and abs(key[s["edges"]].sum() - w) < 1e-6
        assert all(len(e) == n for e in s["C"])
        assert len({tuple(sorted(e)) for e in s["C"]}) > 1 and 0 < s["C_acceptance"] < 1  # Fable, round 2
        for e in s["X"] + s["W"] + s["C"] + [s["heaviest"]] + [x["edges"] for x in s["stars"].values()]:
            assert not any(i[k] in ria or j[k] in ria for k in e)
    bad = copy.deepcopy(sets)
    bad["sides"]["RIAR"]["X"][0][0] = sets["sides"]["RIAR"]["edges"][0]  # an RIA edge in a control
    with pytest.raises(SystemExit):
        m4c.check_sets(bad, spec)
    bad = copy.deepcopy(sets)
    bad["sides"]["RIAL"]["W"][3] = bad["sides"]["RIAL"]["W"][3][:-10]  # lighter than the tolerance
    with pytest.raises(SystemExit):
        m4c.check_sets(bad, spec)
    bad = copy.deepcopy(sets)
    bad["sides"]["RIAR"]["X"][5] = bad["sides"]["RIAR"]["W"][5][:26]  # inside C3, not exterior
    with pytest.raises(SystemExit):
        m4c.check_sets(bad, spec)
    bad = copy.deepcopy(sets)
    bad["sides"]["RIAR"]["C"][2] = bad["sides"]["RIAR"]["W"][2]  # more edges than the side
    with pytest.raises(SystemExit):
        m4c.check_sets(bad, spec)


def test_m4c_rejects_invalid_records():
    """M4c: a saved panel with other genome ids, a missing, incomplete or unexpected arm, a failed intact arm or
    another panel's name stops the run and the reading."""
    import pytest
    import m4c
    side = {"edges": [1], "X": [[2]] * m4c.N_SETS, "W": [[3]] * m4c.N_SETS, "C": [[6]] * m4c.N_SETS, "heaviest": [4],
            "stars": {}}
    sets = {"sides": {"RIAR": side, "RIAL": side}, "descriptive": {"RIA both": [1]},
            "dissection": {"C3": [5], "C3:RIAR": [1], "C3:RIAL": [1]}}
    arms = {a: ["both kept", "erased"] for a in m4c.arm_edges(sets)}
    arms["intact"] = ["both kept"] * 2
    good = {"panel": "N2__1", "genomes": [1, 2], "arms": arms}
    m4c.validate(good, [1, 2], sets, "N2__1")
    for rec, ids, name in ((good, [1, 2, 3], None), (good, [1, 2], "N2__2"),
                           ({**good, "arms": {**arms, "RIAR": ["erased"]}}, [1, 2], None),
                           ({**good, "arms": {k: v for k, v in arms.items() if k != "RIAL:W7"}}, [1, 2], None),
                           ({**good, "arms": {**arms, "other": ["erased"] * 2}}, [1, 2], None),
                           ({**good, "arms": {**arms, "intact": ["both kept", "erased"]}}, [1, 2], None),
                           ({**good, "arms": {**arms, "C3:RIAL": ["both kept", "both kept"]}}, [1, 2], None)):
        with pytest.raises(SystemExit):
            m4c.validate(rec, ids, sets, name)


def _fake_census(out, seed_, n_panel, classes, **over):
    import json
    (out / "census").mkdir(parents=True, exist_ok=True)
    rec = {"panel": f"N2__{seed_}", "graph": "N2", "seed": seed_, "role": "fresh", "valid": True,
           "all": {"a": [1.0] * n_panel}, "genomes": [{"genome": k, "class": c_} for k, c_ in enumerate(classes)]}
    rec.update(over)
    json.dump(rec, open(out / "census" / f"N2__{seed_}.json", "w"))
    np.savez(out / "census" / f"N2__{seed_}.npz", idx=np.arange(len(classes)), roots=np.zeros((len(classes), 2, 3)))


def test_m4c_census_records_and_the_extra_panels(tmp_path, monkeypatch):
    """M4c (Astra, Fable, round 1): a cached census record must be this fresh N2 panel's, of the panel size, with
    aligned arrays; an invalid panel gives no genomes; the four extra panels join only below MIN_GENOMES."""
    import pytest
    import m4c
    monkeypatch.setattr(m4c, "OUT", tmp_path)
    sep = ["separate states"] * 8 + ["fading"] * 2
    for s in m4c.SEEDS:
        _fake_census(tmp_path, s, m4c.N_PANEL, sep)
    assert m4c.switch_ids(m4c.SEEDS[0]) == list(range(8))
    assert m4c.panel_seeds() == m4c.SEEDS  # 64 genomes: no extra panels
    _fake_census(tmp_path, m4c.SEEDS[1], m4c.N_PANEL, sep, valid=False)
    assert m4c.switch_ids(m4c.SEEDS[1]) == []
    assert m4c.panel_seeds() == m4c.SEEDS + m4c.EXTRA_SEEDS  # 56 genomes: the extra panels join
    for over in ({"graph": "SH-1"}, {"seed": 1}, {"role": "N2"}, {"all": {"a": [1.0] * 5}}):
        _fake_census(tmp_path, m4c.SEEDS[2], m4c.N_PANEL, sep, **over)
        with pytest.raises(SystemExit):
            m4c.census_record(m4c.SEEDS[2])
    _fake_census(tmp_path, m4c.SEEDS[2], m4c.N_PANEL, sep)
    np.savez(tmp_path / "census" / f"N2__{m4c.SEEDS[2]}.npz", idx=np.arange(1, 11), roots=np.zeros((10, 2, 3)))
    with pytest.raises(SystemExit):
        m4c.census_record(m4c.SEEDS[2])  # arrays not aligned with the eligible genomes


def test_m4c_classify_patches_the_census_only_inside(tmp_path, monkeypatch):
    """M4c: C1 is skipped and the census writes to M4c's folder only during classify, and both are restored even when
    the panel fails."""
    import pytest
    import m4c
    census = m4c.census
    before = census.OUT, census.N_PANEL, census.c1
    seen = {}

    def boom(name, gname, seed, role, core, hubs):
        seen.update(out=census.OUT, c1=census.c1, role=role, gname=gname)
        raise RuntimeError("stop")
    monkeypatch.setattr(m4c, "OUT", tmp_path)
    monkeypatch.setattr(census, "run_panel", boom)
    with pytest.raises(RuntimeError):
        m4c.classify(7801)
    assert seen["out"] == tmp_path / "census" and seen["c1"] is not before[2] and seen["role"] == "fresh"
    assert seen["gname"] == "N2" and (census.OUT, census.N_PANEL, census.c1) == before


def test_m4c_rejects_a_changed_sets_file(tmp_path, monkeypatch):
    """M4c (Astra, round 1): a saved sets.json that differs from the code's rebuild stops the run and the reading."""
    import json
    import pytest
    import m4c
    monkeypatch.setattr(m4c, "OUT", tmp_path)
    monkeypatch.setattr(m4c, "n2_spec", lambda: None)
    monkeypatch.setattr(m4c, "build_sets", lambda spec: {"sides": {"RIAR": {"edges": [1, 2]}}})
    monkeypatch.setattr(m4c, "check_sets", lambda sets, spec: None)
    json.dump({"sides": {"RIAR": {"edges": [1, 3]}}}, open(tmp_path / "sets.json", "w"))
    with pytest.raises(SystemExit):
        m4c.load_sets()
    with pytest.raises(SystemExit):
        m4c.stage_sets()
    json.dump({"sides": {"RIAR": {"edges": [1, 2]}}}, open(tmp_path / "sets.json", "w"))
    assert m4c.load_sets() == {"sides": {"RIAR": {"edges": [1, 2]}}}
