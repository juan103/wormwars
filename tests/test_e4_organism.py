"""E4's organism E-G on the maze (docs/E4/E4-DESIGN.md v3 §1): E-G + W2 with its output gate attached, and the
slotted organism's exactness (the 32 cross-link slots at 0 change nothing)."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars import graft as G
from wormwars.connectome import load_connectome
from wormwars.e3 import maze_organisms as MO
from wormwars.e3 import maze_world as MW
from wormwars.e3 import organism as O
from wormwars.e4 import organism as E4O
from wormwars.e4s import arms as A
from wormwars.e4s import comparator as C


@pytest.fixture(scope="module")
def parts():
    con, l1 = load_connectome(), A.load_l1()
    cfg = MW.maze_config(c=6, horizon=300, colony=8, mu=0.01, lam=0.02, delta=0.05, d0=1.142, family="islands", k_r=0)
    return con, l1, cfg


def _play(org, cfg, ids=(42_100, 42_101)):
    w = MW.MazeWorld(cfg, org.iface, MO.brain(org, "cpu"), torch.zeros(len(ids), 1, dtype=torch.long),
                     run_seed=1_193_000, world_ids=np.asarray(ids), access="shared")
    pos = []
    for _ in range(cfg.world.max_ticks):
        w.tick()
        pos.append(w.pos[:, 0].clone())
    return torch.stack(pos), w.task_events()["visits"]


def test_eg_carries_its_gate_and_its_brain_applies_it(parts):
    con, l1, cfg = parts
    org = E4O.eg(con, l1, cfg.brain)
    assert org.gate is not None and len(org.gate["a"]) == len(org.gate["b"]) == 16
    assert MO.brain(org, "cpu").output_gate is not None
    seed = MO.maze_organism(con, MO.seed("E", l1, cfg.brain, con=con), "W2", cfg.brain)
    assert seed.gate is None and MO.brain(seed, "cpu").output_gate is None


def test_the_slots_at_zero_change_nothing(parts):
    """E-G with its 32 slots at 0 plays exactly as E-G built without the slots (the same gate)."""
    con, l1, cfg = parts
    slotted = E4O.eg(con, l1, cfg.brain)
    bare = E4O.eg(con, l1, cfg.brain, slots=False)
    a, va = _play(slotted, cfg)
    b, vb = _play(bare, cfg)
    assert torch.equal(a, b) and np.array_equal(va, vb)
