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

def test_the_start_rule_on_a_hand_grid():
    """A corridor fork: the start must be where the two downhill sets part within 4 steps."""
    wall = np.ones((7, 9), dtype=bool)
    wall[3, 1:8] = False  # a horizontal corridor
    d0 = np.full(wall.shape, np.inf)
    d1 = np.full(wall.shape, np.inf)
    for x in range(1, 8):
        d0[3, x], d1[3, x] = x - 1, 7 - x  # candidate 0 at the left end, candidate 1 at the right
    got = TL.start_cell(wall, d0, d1)
    assert got == (3, 4)  # the midpoint: |d0 − d1| = 0, both downhill sets disjoint at once, min distance 3


def test_no_qualifying_cell_gives_none():
    wall = np.ones((5, 5), dtype=bool)
    wall[2, 1:4] = False
    d0 = np.full(wall.shape, np.inf)
    d1 = np.full(wall.shape, np.inf)
    d0[2, 1:4] = [0, 1, 2]
    d1[2, 1:4] = [0, 1, 2]  # both candidates to the left: the downhill sets never part
    assert TL.start_cell(wall, d0, d1) is None


def test_the_start_qualifies_on_island_mazes():
    for mid in IDS:
        mz, pl, _ = IS.maze_for(run_seed=SEED, maze_id=int(mid), episode=0, c=6, k_r=0, n_spawns=4)
        c0, c1 = sorted((tuple(pl.a), tuple(pl.b)))
        d0, d1 = mz.free_distance(c0), mz.free_distance(c1)
        s = TL.start_cell(mz.wall, d0, d1)
        if s is None:
            continue
        assert abs(d0[s] - d1[s]) <= 4 and min(d0[s], d1[s]) > 2


# ------------------------------------------------------------------------------------------- the world (§1)

def test_the_assignment_changes_neither_walls_start_nor_heading(setup):
    cfg, cx = setup
    w0, w1 = _world(cfg, cx, IDS, [0, 0, 0]), _world(cfg, cx, IDS, [1, 1, 1])
    assert torch.equal(w0.fields, w1.fields) and torch.equal(w0.pos, w1.pos) and torch.equal(w0.heading, w1.heading)


def test_one_wey_no_trails(setup):
    cfg, cx = setup
    w = _world(cfg, cx, IDS, [0, 1, 0])
    assert w.n_weys == 1 and set(w.access) == {"none"}


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
    cfg, cx = setup
    w = _world(cfg, cx, IDS, [0, 1, 0])
    w.run(cfg.world.max_ticks)
    out = w.trial_events()
    assert out["first_tick"].shape == (len(IDS), 1)
    assert np.all((out["first_tick"] < 0) | (out["first_tick"] < cfg.world.max_ticks))
    assert set(np.unique(out["first_candidate"])) <= {-1, 0, 1}


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
    cfg, cx = setup
    w = _world(cfg, cx, [IDS[0], IDS[0], IDS[1], IDS[1]], [0, 1, 0, 1])
    pos, v = _trace(w, 150, cx["org"].gate["q"])
    keep = _non_a(cx)
    vv = v[..., keep].reshape(v.shape[0], 4, -1)  # [ticks, worlds, non-A neurons]
    assert torch.equal(pos[:, 0], pos[:, 1]) and torch.equal(pos[:, 2], pos[:, 3])
    assert torch.equal(vv[:, 0], vv[:, 1]) and torch.equal(vv[:, 2], vv[:, 3])
    assert not torch.equal(v[..., ~keep].reshape(v.shape[0], 4, -1)[:, 0], v[..., ~keep].reshape(v.shape[0], 4, -1)[:, 1])


@pytest.mark.parametrize("sabotage", ["cue_into_b", "ungated", "relay"])
def test_the_invariance_check_can_fail(setup, sabotage):
    cfg, cx = setup
    ids, assign = [IDS[0], IDS[0]], [0, 1]
    if sabotage == "cue_into_b":
        w = _world(cfg, cx, ids, assign, b_source="real")
    elif sabotage == "ungated":
        w = _world(cfg, cx, ids, assign, gated=False)
    else:
        w = _world(cfg, cx, ids, assign, relay_leak=True)
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
