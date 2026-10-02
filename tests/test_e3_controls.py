"""E3a's controls on the shuttle (PREREGISTRATION §4): S-oracle steers at the current goal; S-shuttle is
E1's S-const on the goal's bilateral scent; L1-switch is L1 with its noses on the goal's scent.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars import graft as G
from wormwars.brain import Brain
from wormwars.connectome import load_connectome
from wormwars.e1 import controllers as C1
from wormwars.e3 import controls as K
from wormwars.e3 import organism as O
from wormwars.e3.task import shuttle_config
from wormwars.e4s import comparator as C
from wormwars.e4s.arms import load_l1
from wormwars.evo.rollout import rollout_brain
from wormwars.world import World


@pytest.fixture(scope="module")
def ctx():
    con, l1, cfg = load_connectome(), load_l1(), shuttle_config(horizon=600)
    sw = O.l1_switch(l1)
    ext = G.graft_connectome(con, sw)
    return {"con": con, "l1": l1, "cfg": cfg, "sw": sw, "ext": ext, "iface": G.graft_interface(ext, sw)}


def test_the_worlds_current_target_is_the_shuttles_goal(ctx):
    brain = C1.scripted(ctx["iface"], C1.ConstantMotion(0.0, 0.0), ctx["cfg"], n=ctx["ext"].n)
    world = World(ctx["cfg"], ctx["iface"], brain, torch.zeros(2, 1, dtype=torch.long), run_seed=7, world_ids=np.arange(2))
    assert torch.equal(world.current_target(), world.shuttle_sources[:, 0])
    world.shuttle_goal[1] = 1
    assert torch.equal(world.current_target()[1], world.shuttle_sources[1, 1])


def test_the_oracle_shuttles(ctx):
    brain = K.oracle(ctx["iface"], ctx["cfg"], ctx["ext"].n)
    r = rollout_brain(ctx["cfg"], ctx["iface"], brain, np.arange(16), run_seed=7)
    assert r.score.mean() >= 5


def test_s_shuttle_reads_the_goals_scent(ctx):
    brain = K.s_shuttle(ctx["iface"], ctx["cfg"], ctx["ext"].n, k=8192.0, speed=1.0, turn=0.0)
    names = list(ctx["iface"].signal_names)
    assert brain.left == int(ctx["iface"].sensor_neuron[names.index("goal_left")])
    assert brain.right == int(ctx["iface"].sensor_neuron[names.index("goal_right")])
    r = rollout_brain(ctx["cfg"], ctx["iface"], brain, np.arange(16), run_seed=7)
    assert r.score.mean() >= 3


def test_l1_switch_shuttles_on_the_carrier(ctx):
    g = C.carrier_genome(ctx["ext"], ctx["sw"], ctx["cfg"].brain, forward=1.0, turn=0.2)
    r = rollout_brain(ctx["cfg"], ctx["iface"], Brain(g), np.arange(16), run_seed=7)
    assert r.score.mean() >= 2
