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
