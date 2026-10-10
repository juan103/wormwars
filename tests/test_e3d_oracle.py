"""E3b-0's oracle on E3d's loop mazes (docs/E3/E3d-DESIGN.md v2.2 §3, §7): its waypoints are next hops of a
shortest graph path over `Maze.edges` (loops included), and it reaches both goals."""

from __future__ import annotations

from collections import deque

import numpy as np
import pytest
import torch

from wormwars.connectome import load_connectome
from wormwars.e3 import maze_controls as MC
from wormwars.e3 import maze_world as MW
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def iface():
    return load_interface(load_connectome())


def _cfg(horizon):
    return MW.maze_config(c=6, horizon=horizon, colony=1, mu=0.01, lam=0.02, delta=0.05, d0=1.142, family="islands", k_r=4)


def _bfs(nb, goal):
    d = {goal: 0}
    q = deque([goal])
    while q:
        u = q.popleft()
        for v in nb[u]:
            if v not in d:
                d[v] = d[u] + 1
                q.append(v)
    return d


def test_the_oracles_hops_follow_shortest_graph_paths_on_loop_mazes(iface):
    cfg = _cfg(10)
    ids = np.arange(41_000, 41_008)
    brain = MC.oracle(iface, cfg)
    w = MW.MazeWorld(cfg, iface, brain, torch.zeros(len(ids), 1, dtype=torch.long), run_seed=1_190_000, world_ids=ids,
                     access="none")
    hop = brain.hop.cpu().numpy()
    loops = 0
    for k, (mz, pl) in enumerate(zip(w.mazes, w.placements)):
        nb = mz.neighbours()
        loops += len({frozenset(e) for e in mz.edges}) > 35  # more edges than a 6 × 6 tree: there are loops
        for g, goal in enumerate((pl.a, pl.b)):
            d = _bfs(nb, goal)
            for v in d:
                if v == goal:
                    continue
                h = tuple(hop[k, g][v])
                assert h in nb[v] and d[h] == d[v] - 1
    assert loops == len(ids)


def test_the_oracle_shuttles_on_loop_mazes(iface):
    cfg = _cfg(1200)
    ids = np.arange(41_000, 41_008)
    w = MW.MazeWorld(cfg, iface, MC.oracle(iface, cfg), torch.zeros(len(ids), 1, dtype=torch.long), run_seed=1_190_000,
                     world_ids=ids, access="none")
    w.run()
    ev = w.task_events()
    assert (ev["visits"] >= 4).all()
