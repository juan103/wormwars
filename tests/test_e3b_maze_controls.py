"""E3b-0's scripted controls (docs/E3/E3b-0-PLAN.md §3a).

- The path oracle: the tree path's maze-cell centres as waypoints, at full speed, turning at most the
  world's 0.30 rad per tick (privileged, as E1's oracle).
- The scripted trail follower: its goal channel's bilateral reading (trail + scent, as sensed); if
  max(L, R) ≥ 0.005 it steers by 32 (L − R) plus W1's reflex, otherwise it explores as W2; forward 1.
- The blind baselines: the random walk (E1's tuned) with W1's reflex; W2 alone.
The scripted reflexes are W1's and W2's steady-state turn commands on the carrier (D176).
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import Brain
from wormwars.connectome import load_connectome
from wormwars.e3 import maze as M
from wormwars.e3 import maze_controls as MC
from wormwars.e3 import maze_organisms as MO
from wormwars.e3 import maze_world as MW
from wormwars.e3.task import shuttle_config
from wormwars.e4s import arms as A
from wormwars.e4s import comparator as C
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def iface(con):
    return load_interface(con)


def _cfg(**kw):
    base = dict(c=5, horizon=600, colony=1, mu=0.01, lam=0.03, delta=0.15, d0=0.571)
    base.update(kw)
    return MW.maze_config(**base)


def _world(iface, cfg, brain, ids, **kw):
    strain_of = torch.zeros(len(ids), 1, dtype=torch.long)
    return MW.MazeWorld(cfg, iface, brain, strain_of, run_seed=11, world_ids=np.asarray(ids), **kw)


# ------------------------------------------------------------------ the scripted reflexes

@pytest.mark.parametrize("variant", ["W1", "W2"])
def test_the_scripted_reflexes_match_the_neural_ones_at_steady_state(con, variant):
    cfg = shuttle_config()
    org = MO.maze_organism(con, MO.seed("E", A.load_l1(), cfg.brain, con=con), variant, cfg.brain)
    # the scripted W1 term is the reflex alone: compare it with W1 on a carrier without a turn bias
    genome = (C.carrier_genome(org.ext, org.module, cfg.brain, forward=1.0, turn=0.0) if variant == "W1"
              else org.genome)
    brain = Brain(genome)
    for cl, cr in ((0.0, 0.0), (2.0, 0.0), (0.0, 2.0), (0.7, 0.3), (1.2, 1.9), (0.1, 0.0), (0.0, 0.15)):
        cur = torch.zeros(1, 1, org.ext.n)
        cur[..., org.ext.index("E3B_WL")], cur[..., org.ext.index("E3B_WR")] = cl, cr
        v = brain.initial_state(1)
        for _ in range(80):
            v = brain.step(v, cur)
        _, turn = C.motor_commands(v, org.iface, cfg)
        c_l, c_r = torch.tensor([cl]), torch.tensor([cr])
        if variant == "W1":
            want = MC.w1_reflex(c_l, c_r, cfg).clamp(-1, 1)
        else:
            want = MC.w2_turn(c_l, c_r, cfg).clamp(-1, 1)
        assert float(turn) == pytest.approx(float(want), abs=3e-3)


# ------------------------------------------------------------------ the trail follower's policy

def test_the_follower_steers_on_its_goal_channel_and_explores_as_w2_below_threshold():
    cfg = shuttle_config()
    pol = MC.TrailFollower()
    z = torch.zeros(3)
    sig = {"goal_left": torch.tensor([0.2, 0.004, 0.0]), "goal_right": torch.tensor([0.1, 0.0, 0.004]),
           "collision_front_left": z, "collision_front_right": z}
    fwd, turn = pol(sig, cfg)
    assert torch.equal(fwd, torch.ones(3))
    assert float(turn[0]) == pytest.approx(min(1.0, 32 * 0.1), abs=1e-6)  # steering, the reflex at rest is 0
    w2 = float(MC.w2_turn(z[:1], z[:1], cfg))
    assert float(turn[1]) == pytest.approx(w2, abs=1e-6) and float(turn[2]) == pytest.approx(w2, abs=1e-6)
    assert w2 == pytest.approx(0.4, abs=1e-6)


# ------------------------------------------------------------------ the oracle

def test_the_oracle_shuttles_along_the_tree_path(iface):
    cfg = _cfg()
    brain = MC.oracle(iface, cfg)
    ids = np.arange(12)
    world = _world(iface, cfg, brain, ids, access="none")
    world.run()
    ev = world.task_events()
    assert (ev["visits"] >= 4).all()  # 600 ticks: the A-B route is at most 2c = 10 maze cells
    for w in range(len(ids)):
        mz, pl = world.mazes[w], world.placements[w]
        d = mz.free_distance(pl.a)[2 + 4 * pl.b[0], 2 + 4 * pl.b[1]]
        legs = np.diff(ev["visit_tick"][w, 0][ev["visit_tick"][w, 0] >= 0])
        assert np.median(legs) <= 1.6 * d / 0.35 + 10  # close to the shortest free path at full speed


# ------------------------------------------------------------------ the sabotage check (plan §3c)

def test_own_and_none_are_identical_for_the_follower_until_each_weys_first_b_visit(iface):
    cfg = _cfg(colony=8, horizon=1500)
    ids = np.arange(6)
    traces = {}
    for mode in ("own", "none"):
        brain = MC.follower(iface, cfg)
        world = _world(iface, cfg, brain, ids, access=mode)
        pos = []
        for _ in range(cfg.world.max_ticks):
            world.tick()
            pos.append(world.pos[:, 0].clone())
        traces[mode] = (torch.stack(pos, dim=2), world.task_events())  # [worlds, weys, ticks, 2]
    (p_own, ev), (p_none, _) = traces["own"], traces["none"]
    fb = ev["first_b_tick"]
    assert (fb >= 0).sum() >= 4  # enough weys reach B for the check to mean something
    T = p_own.shape[2]
    for w in range(len(ids)):
        for b in range(8):
            upto = T if fb[w, b] < 0 else fb[w, b] + 1
            assert torch.equal(p_own[w, b, :upto], p_none[w, b, :upto])
    assert not torch.equal(p_own, p_none)  # after a B visit the own trail matters


def test_the_blind_baselines_run(iface):
    cfg = _cfg(colony=4, horizon=300)
    for brain in (MC.reflex_walk(iface, cfg), MC.w2_alone(iface, cfg)):
        world = _world(iface, cfg, brain, np.arange(4))
        world.run()
        assert world.task_events()["visits"].shape == (4, 4)
