"""E4-D's single-choice trial (docs/E4/E4-D-DESIGN.md v2.1 §1-§3, §6): the start-cell rule, the channel mapping,
the silent relays and the start cue off, the latch held in mode B, first-entry latching, and X0's exact invariance to
the assignment, with its sabotages."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import Brain
from wormwars.connectome import load_connectome
from wormwars.e3 import islands as IS
from wormwars.e4 import arms as AR
from wormwars.e4 import trial as TL
from wormwars.e4.train import gated_brain
from wormwars.e4s import arms as A

SEED, IDS = 1_410_000, np.array([50_000, 50_001, 50_002])


@pytest.fixture(scope="module")
def setup():
    cfg = TL.trial_config(sigma=9.0, horizon=200)
    cx = AR.context(load_connectome(), A.load_l1(), cfg.brain)
    return cfg, cx


def _world(cfg, cx, ids, assign, genome=None, gated=True, **kw):
    org = cx["org"]
    g = org.genome.select([0]) if genome is None else genome
    brain = gated_brain(g, org.gate) if gated else Brain(g)
    return TL.TrialWorld(cfg, org.iface, brain, torch.zeros(len(ids), 1, dtype=torch.long), run_seed=SEED,
                         world_ids=np.asarray(ids), assign=np.asarray(assign), q_index=org.gate["q"], **kw)


# ------------------------------------------------------------------------------------------- the start cell (§2)

def _corridor(n_free=7, extra_common=0):
    """A horizontal corridor; candidate 0 at the left end, candidate 1 at the right."""
    wall = np.ones((7, n_free + 2), dtype=bool)
    wall[3, 1:n_free + 1] = False
    d0 = np.full(wall.shape, np.inf)
    d1 = np.full(wall.shape, np.inf)
    for x in range(1, n_free + 1):
        d0[3, x], d1[3, x] = x - 1, n_free - x
    return wall, d0, d1


def test_the_start_rule_on_a_hand_grid():
    """A corridor: the start is the midpoint, where |d0 − d1| = 0 and the downhill sets part at once."""
    wall, d0, d1 = _corridor()
    assert TL.start_cell(wall, d0, d1) == (3, 4)


def test_the_start_must_lie_outside_both_blocks():
    wall, d0, d1 = _corridor(n_free=3)  # the midpoint has d0 = d1 = 1 > 0: allowed; a block cell (d = 0) never
    s = TL.start_cell(wall, d0, d1)
    assert s is not None and d0[s] > 0 and d1[s] > 0


def test_the_separation_walk_allows_four_common_steps_not_five():
    """A shared stem of k cells below a fork: qualifies at k = 4, not at k = 5."""
    def fork(k):
        H, W = 4 + k + 2, 9
        wall = np.ones((H, W), dtype=bool)
        wall[1, 1:8] = False          # the fork's bar: candidate 0 at (1, 1), candidate 1 at (1, 7)
        wall[2:2 + k, 4] = False  # a stem of k cells down from (1, 4): k common steps back to the fork
        d0 = np.full(wall.shape, np.inf)
        d1 = np.full(wall.shape, np.inf)
        for x in range(1, 8):
            d0[1, x], d1[1, x] = x - 1, 7 - x
        for i in range(1, k + 1):
            d0[1 + i, 4], d1[1 + i, 4] = 3 + i, 3 + i
        return wall, d0, d1, (1 + k, 4)
    for k, ok in ((3, True), (4, True), (5, False)):
        wall, d0, d1, bottom = fork(k)
        assert TL._separates(d0, d1, *bottom) is ok, k


def test_no_qualifying_cell_gives_none():
    wall = np.ones((5, 5), dtype=bool)
    wall[2, 1:4] = False
    d0 = np.full(wall.shape, np.inf)
    d1 = np.full(wall.shape, np.inf)
    d0[2, 1:4] = [0, 1, 2]
    d1[2, 1:4] = [0, 1, 2]  # both candidates to the left: the downhill sets never part
    assert TL.start_cell(wall, d0, d1) is None


def test_block_distance_is_zero_on_the_block_and_grows_off_it():
    mz, pl, _ = IS.maze_for(run_seed=SEED, maze_id=int(IDS[0]), episode=0, c=6, k_r=0, n_spawns=4)
    d = TL.block_distance(mz, tuple(pl.a))
    y0, x0 = 1 + 4 * pl.a[0], 1 + 4 * pl.a[1]
    assert np.all(d[y0:y0 + 3, x0:x0 + 3][~mz.wall[y0:y0 + 3, x0:x0 + 3]] == 0)
    assert np.all(d <= mz.free_distance(tuple(pl.a)))  # never farther than from the centre


def test_the_start_qualifies_on_island_mazes():
    found = 0
    for mid in IDS:
        mz, pl, _ = IS.maze_for(run_seed=SEED, maze_id=int(mid), episode=0, c=6, k_r=0, n_spawns=4)
        c0, c1 = sorted((tuple(pl.a), tuple(pl.b)))
        d0, d1 = TL.block_distance(mz, c0), TL.block_distance(mz, c1)
        s = TL.start_cell(mz.wall, d0, d1)
        if s is None:
            continue
        found += 1
        assert abs(d0[s] - d1[s]) <= 4 and min(d0[s], d1[s]) > 0
    assert found >= 1


# ------------------------------------------------------------------------------------------- the world (§1)

def test_the_assignment_changes_neither_walls_start_nor_heading(setup):
    cfg, cx = setup
    w0, w1 = _world(cfg, cx, IDS, [0, 0, 0]), _world(cfg, cx, IDS, [1, 1, 1])
    assert torch.equal(w0.fields, w1.fields) and torch.equal(w0.pos, w1.pos) and torch.equal(w0.heading, w1.heading)


def test_one_wey_no_trails_no_crowding(setup):
    cfg, cx = setup
    w = _world(cfg, cx, IDS, [0, 1, 0])
    assert w.n_weys == 1 and set(w.access) == {"none"}
    assert cfg.world.crowd_resist == 0.0 and cfg.world.crowd_push == 0.0


def _currents(w):
    """The current each world's brain receives on the next tick ([worlds, N]; one wey)."""
    seen = []
    step = w.brains[0].step
    w.brains[0].step = lambda v, cur, substeps=None: (seen.append(cur.clone()), step(v, cur, substeps))[1]
    w.tick()
    w.brains[0].step = step
    return seen[0].reshape(w.n_worlds, -1)


def test_the_assignment_reaches_only_as_noses(setup):
    """§1's enumeration: under both assignments, from identical states, the injected currents differ only at E3_A_NL
    and E3_A_NR (Fable, Astra)."""
    cfg, cx = setup
    ext = cx["org"].ext
    w = _world(cfg, cx, [IDS[0], IDS[0], IDS[1], IDS[1]], [0, 1, 0, 1])
    cur = _currents(w)
    diff = torch.nonzero((cur[0] != cur[1]) | (cur[2] != cur[3])).view(-1).tolist()
    assert set(diff) <= {ext.index("E3_A_NL"), ext.index("E3_A_NR")} and diff


@pytest.mark.parametrize("a_source, b_source", [("decoy", "sum"), ("fixed0", "sum"), ("none", "sum"), ("real", "real")])
def test_the_channel_variants(setup, a_source, b_source):
    cfg, cx = setup
    w = _world(cfg, cx, [IDS[0], IDS[0]], [0, 1], a_source=a_source, b_source=b_source)
    sig = w.trial_signals()
    c = sig["cand"]  # [W, 1, B, 2, (L, R)]
    real = torch.stack([c[0, ..., 0, :], c[1, ..., 1, :]])
    decoy = torch.stack([c[0, ..., 1, :], c[1, ..., 0, :]])
    a = torch.stack((sig["a_left"], sig["a_right"]), -1)
    b = torch.stack((sig["b_left"], sig["b_right"]), -1)
    want_a = {"decoy": decoy, "fixed0": torch.stack([c[0, ..., 0, :], c[1, ..., 0, :]]),
              "none": torch.zeros_like(real)}[a_source] if a_source != "real" else real
    want_b = real if b_source == "real" else c[..., 0, :] + c[..., 1, :]
    assert torch.equal(a, want_a) and torch.equal(b, want_b)


def test_the_channels(setup):
    """B reads the sum of both candidates; A reads the real one; the relays and the start cue are silent."""
    cfg, cx = setup
    w = _world(cfg, cx, [IDS[0], IDS[0]], [0, 1])
    sig = w.trial_signals()
    c0, c1 = sig["cand"][..., 0, :], sig["cand"][..., 1, :]  # [worlds, 1, weys, (L, R)]
    assert torch.equal(sig["b_left"], c0[..., 0] + c1[..., 0]) and torch.equal(sig["b_right"], c0[..., 1] + c1[..., 1])
    assert torch.equal(sig["a_left"][0], c0[0, ..., 0]) and torch.equal(sig["a_left"][1], c1[1, ..., 0])
    assert torch.all(sig["at_a"] == 0) and torch.all(sig["at_b"] == 0)
    assert torch.equal(sig["b_left"][0], sig["b_left"][1])  # B's input is the same under both assignments


def test_the_inherited_start_cue_would_open_the_gate(setup):
    """The sabotage of the cue rule: in a plain MazeWorld at_b is held at 1 for the first ticks."""
    cfg, cx = setup
    w = _world(cfg, cx, IDS[:1], [0], keep_start_cue=True)
    assert torch.all(w.trial_signals()["at_b"] == 1)


def test_the_latch_holds_mode_b(setup):
    cfg, cx = setup
    org = cx["org"]
    w = _world(cfg, cx, IDS, [0, 1, 0])
    assert torch.all(w.v[0][..., org.gate["q"]] == -1.0)
    qs = []
    w.brains[0].substep_hook = lambda v: qs.append(v[..., org.gate["q"]].clone())
    w.run(120)
    assert torch.all(torch.stack(qs) < 0)


def test_with_the_start_cue_on_q_turns_positive(setup):
    """Rule 9: the latch check can fail."""
    cfg, cx = setup
    org = cx["org"]
    w = _world(cfg, cx, IDS[:1], [0], keep_start_cue=True)
    qs = []
    w.brains[0].substep_hook = lambda v: qs.append(float(v[..., org.gate["q"]].max()))
    w.run(5)
    assert max(qs) > 0


# ------------------------------------------------------------------------------------------- first entries (§1)

def test_first_entry_latching():
    cand = torch.full((2, 1), -1, dtype=torch.long)
    tick = torch.full((2, 1), -1, dtype=torch.long)
    TL.latch_first(cand, tick, torch.tensor([[[False, True]], [[False, False]]]), 7)
    TL.latch_first(cand, tick, torch.tensor([[[True, False]], [[True, False]]]), 9)
    assert cand.tolist() == [[1], [0]] and tick.tolist() == [[7], [9]]


def test_an_entry_on_the_last_tick_counts(setup):
    """Find a trial's first entry tick t; with the horizon t + 1 it is recorded, with the horizon t it is not."""
    cfg, cx = setup
    long = TL.trial_config(sigma=9.0, horizon=600)
    w = _world(long, cx, IDS, [0, 1, 0])
    w.run(600)
    ev = w.trial_events()
    k = int(np.flatnonzero(ev["first_tick"][:, 0] >= 0)[0])  # a trial that entered
    t = int(ev["first_tick"][k, 0])
    for horizon, want in ((t + 1, t), (t, -1)):
        w = _world(TL.trial_config(sigma=9.0, horizon=horizon), cx, [IDS[k]], [[0, 1, 0][k]])
        w.run(horizon)
        assert int(w.trial_events()["first_tick"][0, 0]) == want, horizon


# ------------------------------------------------------------------------------------------- X0's invariance (§3)

def _trace(w, ticks, q):
    pos, states = [], []
    w.brains[0].substep_hook = None
    for _ in range(ticks):
        w.tick()
        pos.append(w.pos.clone())
        v = w.v[0].clone()
        states.append(v)
    return torch.stack(pos), torch.stack(states)


def _non_a(cx):
    ext = cx["org"].ext
    a = [ext.index(n) for n in ("E3_A_NL", "E3_A_NR", "E3_A_CL", "E3_A_CR")]
    keep = torch.ones(ext.n, dtype=torch.bool)
    keep[a] = False
    return keep


def test_x0_is_invariant_to_the_assignment(setup):
    """Traced to the horizon, through at least one entry (Fable: the post-entry path must be traced too)."""
    cfg, cx = setup
    long = TL.trial_config(sigma=9.0, horizon=600)
    w = _world(long, cx, [IDS[0], IDS[0], IDS[1], IDS[1]], [0, 1, 0, 1])
    pos, v = _trace(w, 600, cx["org"].gate["q"])
    assert (w.trial_events()["first_tick"] >= 0).any()
    keep = _non_a(cx)
    vv = v[..., keep].reshape(v.shape[0], 4, -1)  # [ticks, worlds, non-A neurons]
    assert torch.equal(pos[:, 0], pos[:, 1]) and torch.equal(pos[:, 2], pos[:, 3])
    assert torch.equal(vv[:, 0], vv[:, 1]) and torch.equal(vv[:, 2], vv[:, 3])
    assert not torch.equal(v[..., ~keep].reshape(v.shape[0], 4, -1)[:, 0], v[..., ~keep].reshape(v.shape[0], 4, -1)[:, 1])


@pytest.mark.parametrize("sabotage", ["cue_into_b", "ungated", "relay", "a_link"])
def test_the_invariance_check_can_fail(setup, sabotage):
    cfg, cx = setup
    ids, assign = [IDS[0], IDS[0]], [0, 1]
    if sabotage == "cue_into_b":
        w = _world(cfg, cx, ids, assign, b_source="real")
    elif sabotage == "ungated":
        w = _world(cfg, cx, ids, assign, gated=False)
    elif sabotage == "relay":
        w = _world(cfg, cx, ids, assign, relay_leak=True)
    else:  # one nonzero slot: the smallest control (Fable)
        w = _world(cfg, cx, ids, assign, genome=TL.control_genome(cx["org"].genome.select([0]), cx, "nose", 0.05))
    pos, v = _trace(w, 150, cx["org"].gate["q"])
    keep = _non_a(cx)
    vv = v[..., keep].reshape(v.shape[0], 2, -1)
    assert not (torch.equal(pos[:, 0], pos[:, 1]) and torch.equal(vv[:, 0], vv[:, 1]))


# ------------------------------------------------------------------------------------------- the control (§4)

def test_the_control_wirings(setup):
    _, cx = setup
    org = cx["org"]
    spec, ext = org.genome.spec, org.ext

    def w_of(g, pre, post):
        k = int(((spec.chem_i == ext.index(pre)) & (spec.chem_j == ext.index(post))).nonzero()[0, 0])
        return float(g.w[0, k])

    g = TL.control_genome(org.genome.select([0]), cx, "comparator", 2.0)
    assert w_of(g, "E3_A_CL", "E3_B_CL") == 2.0 and w_of(g, "E3_A_CR", "E3_B_CR") == 2.0
    assert w_of(g, "E3_A_NL", "E3_B_CL") == 0.0
    g = TL.control_genome(org.genome.select([0]), cx, "nose", 3.0)
    assert (w_of(g, "E3_A_NL", "E3_B_CL"), w_of(g, "E3_A_NL", "E3_B_CR"),
            w_of(g, "E3_A_NR", "E3_B_CR"), w_of(g, "E3_A_NR", "E3_B_CL")) == (3.0, -3.0, 3.0, -3.0)
    slots = AR.slot_indices(cx)
    assert int((g.w[0, slots] != 0).sum()) == 4
