"""E3b-0's maze generator (docs/E3/E3b-0-PLAN.md §1a).

A random spanning tree on a c × c grid of maze cells, carved with 3-wide corridors and 1-cell walls, so
the side is 4c + 1. A and B sit at two distinct dead ends whose tree distance is in [⌈c/2⌉ + 1, 2c]; the
spawns at up to 4 other dead ends, each at least 2 maze cells from A and B.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np
import pytest

from wormwars.e3 import maze as M


def _connected(free: np.ndarray) -> bool:
    cells = list(zip(*np.nonzero(free)))
    seen, q = {cells[0]}, deque([cells[0]])
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (y + dy, x + dx)
            if 0 <= n[0] < free.shape[0] and 0 <= n[1] < free.shape[1] and free[n] and n not in seen:
                seen.add(n)
                q.append(n)
    return len(seen) == len(cells)


@pytest.mark.parametrize("c", [5, 6, 8])
def test_the_maze_is_a_carved_spanning_tree(c):
    mz = M.generate(np.random.default_rng(1), c)
    assert mz.wall.shape == (4 * c + 1, 4 * c + 1)
    assert mz.wall[0].all() and mz.wall[-1].all() and mz.wall[:, 0].all() and mz.wall[:, -1].all()
    assert len(mz.edges) == c * c - 1  # a tree
    assert _connected(~mz.wall)
    for i in range(c):  # every maze cell's 3 x 3 interior is open
        for j in range(c):
            assert not mz.wall[1 + 4 * i:4 + 4 * i, 1 + 4 * j:4 + 4 * j].any()
    # exactly the tree's passages are open between neighbouring cells, 3 wide
    open_between = 0
    for i in range(c):
        for j in range(c - 1):
            gap = mz.wall[1 + 4 * i:4 + 4 * i, 4 + 4 * j]
            assert gap.all() or not gap.any()
            open_between += not gap.any()
    for i in range(c - 1):
        for j in range(c):
            gap = mz.wall[4 + 4 * i, 1 + 4 * j:4 + 4 * j]
            assert gap.all() or not gap.any()
            open_between += not gap.any()
    assert open_between == c * c - 1


def test_the_maze_depends_only_on_its_generator():
    a = M.generate(np.random.default_rng(7), 6)
    b = M.generate(np.random.default_rng(7), 6)
    c = M.generate(np.random.default_rng(8), 6)
    assert np.array_equal(a.wall, b.wall) and not np.array_equal(a.wall, c.wall)


def test_dead_ends_and_tree_distances():
    mz = M.generate(np.random.default_rng(3), 6)
    deg = {k: 0 for k in np.ndindex(6, 6)}
    for u, v in mz.edges:
        deg[u] += 1
        deg[v] += 1
    assert set(mz.dead_ends()) == {k for k, d in deg.items() if d == 1}
    d = mz.tree_distance()
    some = mz.dead_ends()[0]
    assert d[some][some] == 0 and all(d[some][k] >= 1 for k in deg if k != some)


@pytest.mark.parametrize("c", [5, 6, 8])
def test_placements_meet_the_rule(c):
    for seed in range(30):
        mz, p = M.draw(np.random.default_rng(seed), np.random.default_rng(1000 + seed), c, n_spawns=4)
        d = mz.tree_distance()
        ends = set(mz.dead_ends())
        assert p.a in ends and p.b in ends and p.a != p.b
        assert math.ceil(c / 2) + 1 <= d[p.a][p.b] <= 2 * c
        assert 1 <= len(p.spawns) <= 4
        for s in p.spawns:
            assert s in ends and s not in (p.a, p.b)
            assert d[s][p.a] >= 2 and d[s][p.b] >= 2


def test_cell_centres_and_bfs_distance_on_free_cells():
    mz = M.generate(np.random.default_rng(2), 5)
    assert M.cell_centre((0, 0)) == (2.5, 2.5) and M.cell_centre((1, 2)) == (10.5, 6.5)
    dist = mz.free_distance((0, 0))
    y, x = 2, 2  # the centre grid cell of maze cell (0, 0)
    assert dist[y, x] == 0 and np.isinf(dist[mz.wall]).all()
    assert np.isfinite(dist[~mz.wall]).all()
