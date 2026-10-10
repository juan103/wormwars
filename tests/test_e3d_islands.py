"""E3d's island-goal mazes (docs/E3/E3d-DESIGN.md v2.2 §2).

A Wilson tree from `walls_for`'s own streams; two interior goals whose rings share no post; every closed
segment leaving a goal's corner posts outward opened, so the goal's ring is free-standing; then the first k_r
of one random order of the remaining closed segments, the goals' own sides excluded. Checks: island-safety,
no shared component, the graph distance in [⌈c/2⌉ + 1, 2c], a spawn cell; redrawn by (seed, id, k), at most
64 times.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np
import pytest

from wormwars.e3 import islands as I
from wormwars.e3 import maze as M

SEED = 1_190_000


def _raster(c, edges):
    n = 4 * c + 1
    wall = np.ones((n, n), dtype=bool)
    for i in range(c):
        for j in range(c):
            wall[1 + 4 * i:4 + 4 * i, 1 + 4 * j:4 + 4 * j] = False
    for u, v in edges:
        M._carve(wall, u, v)
    return wall


def _ring_road(g):
    i, j = g
    ring = [(i - 1, j - 1), (i - 1, j), (i - 1, j + 1), (i, j + 1), (i + 1, j + 1), (i + 1, j), (i + 1, j - 1), (i, j - 1)]
    return [frozenset((ring[k], ring[(k + 1) % 8])) for k in range(8)]


def _posts(g):
    i, j = g
    return {(i, j), (i, j + 1), (i + 1, j), (i + 1, j + 1)}


def _segment_posts(s):
    (u, v) = sorted(s)
    if u[0] != v[0]:  # vertical neighbours: the wall row 4 * v[0], from post (v0, u1) to (v0, u1 + 1)
        return {(v[0], u[1]), (v[0], u[1] + 1)}
    return {(u[0], v[1]), (u[0] + 1, v[1])}


# --- the labelling and island-safety ---------------------------------------------------------------------

def test_every_wall_of_a_tree_is_in_the_perimeter_component():
    for mid in range(20):
        mz, _ = M.walls_for(run_seed=SEED, maze_id=mid, c=6)
        lab, border = I.components(mz.wall)
        assert set(np.unique(lab[mz.wall])) <= border


def test_a_tree_cell_is_never_island_safe_but_a_carved_goal_is():
    mz, _ = M.walls_for(run_seed=SEED, maze_id=3, c=6)
    assert not any(I.island_safe(mz.wall, (i, j)) for i in range(6) for j in range(6))
    wall, edges = mz.wall.copy(), list(mz.edges)
    I.carve_island(wall, edges, (2, 3), 6)
    assert I.island_safe(wall, (2, 3))


OUTWARD_33 = [((0, 0), (0, 1)), ((0, 0), (1, 0)), ((0, 1), (0, 2)), ((0, 2), (1, 2)),
              ((1, 0), (2, 0)), ((2, 0), (2, 1)), ((1, 2), (2, 2)), ((2, 1), (2, 2))]


def test_island_safety_on_a_hand_built_grid_with_a_sabotage():
    """c = 3, every segment closed: the centre is not island-safe. Open the eight segments leaving its posts
    outward and it is. Re-close any one of them (it reaches the outer wall) and it is not again."""
    assert not I.island_safe(_raster(3, []), (1, 1))
    assert I.island_safe(_raster(3, OUTWARD_33), (1, 1))
    for k in range(8):
        assert not I.island_safe(_raster(3, OUTWARD_33[:k] + OUTWARD_33[k + 1:]), (1, 1))


def test_carve_island_opens_exactly_the_outward_segments():
    wall, edges = _raster(3, []), []
    carved = I.carve_island(wall, edges, (1, 1), 3)
    assert {frozenset(s) for s in carved} == {frozenset(s) for s in OUTWARD_33}
    assert np.array_equal(wall, _raster(3, OUTWARD_33)) and len(edges) == 8


def test_the_checks_can_fail():
    """The island and shared-component checks cannot fail for carved goals, so they are sabotaged here: a tree
    fails "island"; with the outer frame removed, no component is perimeter, and the one remaining wall
    component touches both goal blocks ("shared")."""
    mz, _ = M.walls_for(run_seed=SEED, maze_id=3, c=6)
    assert I.failed_check(mz, (1, 1), (3, 4)) == "island"
    wall = _raster(6, [])
    wall[0, :] = wall[-1, :] = wall[:, 0] = wall[:, -1] = False
    assert I.failed_check(M.Maze(6, wall, []), (1, 1), (3, 4)) == "shared"


# --- the construction ------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    return {(mid, k_r): I.islands_for(run_seed=SEED, maze_id=mid, c=6, k_r=k_r)
            for mid in range(30_000, 30_040) for k_r in (0, 2, 4)}


def test_raster_and_edges_agree(built):
    for im in built.values():
        assert len({frozenset(e) for e in im.maze.edges}) == len(im.maze.edges)
        assert np.array_equal(_raster(6, im.maze.edges), im.maze.wall)


def test_the_tree_comes_from_walls_for_streams(built):
    for (mid, _), im in built.items():
        rng = np.random.default_rng([SEED, mid, 0x3A11] if im.k == 0 else [SEED, mid, 0x3A11, im.k])
        tree = M.generate(rng, 6)
        assert [tuple(e) for e in im.maze.edges[:len(tree.edges)]] == [tuple(e) for e in tree.edges]
        assert len(tree.edges) == 35


def test_goals_are_interior_with_separate_rings(built):
    for im in built.values():
        for g in (im.a, im.b):
            assert 1 <= g[0] <= 4 and 1 <= g[1] <= 4
        assert max(abs(im.a[0] - im.b[0]), abs(im.a[1] - im.b[1])) >= 2


def test_the_roundabout_is_open_around_each_goal(built):
    for im in built.values():
        open_ = {frozenset(e) for e in im.maze.edges}
        for g in (im.a, im.b):
            assert set(_ring_road(g)) <= open_


def test_carving_opens_only_segments_leaving_a_goal_post(built):
    for im in built.values():
        for s in im.carved:
            s = frozenset(s)
            assert im.a not in s and im.b not in s
            assert _segment_posts(s) & (_posts(im.a) | _posts(im.b))


def test_exactly_k_r_extra_openings_none_on_a_goal_side(built):
    for (_, k_r), im in built.items():
        assert len(im.extra) == k_r
        n_tree = 35
        assert len(im.maze.edges) == n_tree + len(im.carved) + k_r
        for s in im.extra:
            assert im.a not in s and im.b not in s


def test_extra_openings_are_nested_across_k_r_at_a_shared_redraw_index(built):
    shared = 0
    for mid in range(30_000, 30_040):
        ims = [built[(mid, k)] for k in (0, 2, 4)]
        for lo, hi in ((ims[0], ims[1]), (ims[1], ims[2])):
            if lo.k == hi.k:
                shared += 1
                assert (lo.a, lo.b) == (hi.a, hi.b)
                assert [frozenset(e) for e in lo.extra] == [frozenset(e) for e in hi.extra[:len(lo.extra)]]
    assert shared > 0


def test_every_cell_is_reachable(built):
    for im in built.values():
        nb = im.maze.neighbours()
        seen, q = {(0, 0)}, deque([(0, 0)])
        while q:
            u = q.popleft()
            for v in nb[u]:
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        assert len(seen) == 36


def test_the_checks_hold_on_the_final_maze(built):
    for im in built.values():
        assert I.island_safe(im.maze.wall, im.a) and I.island_safe(im.maze.wall, im.b)
        lab, _ = I.components(im.maze.wall)
        assert not (I.block_labels(lab, im.a) & I.block_labels(lab, im.b))
        d = im.maze.tree_distance()[im.a][im.b]  # BFS over the final edges, loops included
        assert math.ceil(6 / 2) + 1 <= d <= 12
        assert I.spawn_candidates(im.maze, im.a, im.b)


def test_both_goal_orders_occur(built):
    """A and B are swapped with probability 1/2: across 40 mazes both orders of the row index occur."""
    orders = {im.a < im.b for (_, k_r), im in built.items() if k_r == 0}
    assert orders == {True, False}


# --- the keying and the redraw ---------------------------------------------------------------------------

def test_deterministic_per_seed_id_and_k_r():
    a = I.islands_for(run_seed=SEED, maze_id=30_001, c=6, k_r=2)
    b = I.islands_for(run_seed=SEED, maze_id=30_001, c=6, k_r=2)
    assert (a.a, a.b, a.k) == (b.a, b.b, b.k) and np.array_equal(a.maze.wall, b.maze.wall)
    c = I.islands_for(run_seed=SEED + 1, maze_id=30_001, c=6, k_r=2)
    assert not np.array_equal(a.maze.wall, c.maze.wall)


def test_walls_and_goals_do_not_depend_on_the_episode():
    m0, p0, _ = I.maze_for(run_seed=SEED, maze_id=30_005, episode=0, c=6, k_r=2)
    m1, p1, _ = I.maze_for(run_seed=SEED, maze_id=30_005, episode=1, c=6, k_r=2)
    assert np.array_equal(m0.wall, m1.wall) and (p0.a, p0.b) == (p1.a, p1.b)


def test_redraws_beyond_the_limit_raise():
    """c = 3 has a single interior cell, so no pair exists and every redraw fails."""
    with pytest.raises(ValueError, match="redraws"):
        I.islands_for(run_seed=SEED, maze_id=0, c=3, k_r=0)


# --- the spawns ------------------------------------------------------------------------------------------

def test_spawns_have_no_island_wall_in_their_block_and_keep_their_distance():
    for mid in range(30_000, 30_030):
        mz, pl, _ = I.maze_for(run_seed=SEED, maze_id=mid, episode=0, c=6, k_r=2)
        lab, border = I.components(mz.wall)
        d = mz.tree_distance()
        assert 1 <= len(pl.spawns) <= 4
        for s in pl.spawns:
            assert I.block_labels(lab, s) <= border
            assert d[s][pl.a] >= 2 and d[s][pl.b] >= 2


def _rings_only(c, goals):
    """Every segment open except three sides of each goal (`goals`: (cell, the open side's neighbour)); the
    outer frame removed, so no wall is perimeter and every corner post stands alone."""
    closed = set()
    for (i, j), keep in goals:
        closed |= {frozenset(((i, j), n)) for n in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)) if n != keep}
    edges = [s for s in I.segments(c) if frozenset(s) not in closed]
    wall = _raster(c, edges)
    wall[0, :] = wall[-1, :] = wall[:, 0] = wall[:, -1] = False
    return M.Maze(c, wall, edges)


def test_the_distance_and_spawn_checks_fire():
    """(1, 1) open east and (1, 3) open west are 2 apart: "distance". (1, 1) and (3, 3), both open north, are 6
    apart, but every cell's block holds a free-standing post, so no cell can be a spawn: "spawn"."""
    assert I.failed_check(_rings_only(5, [((1, 1), (1, 2)), ((1, 3), (1, 2))]), (1, 1), (1, 3)) == "distance"
    assert I.failed_check(_rings_only(5, [((1, 1), (0, 1)), ((3, 3), (2, 3))]), (1, 1), (3, 3)) == "spawn"


def test_the_goal_stream_reproduces_exactly():
    """A, B, the swap and the k_r order come from [run seed, id, 0x15A7, k] in that order (design §2)."""
    for mid in range(30_000, 30_010):
        im = I.islands_for(run_seed=SEED, maze_id=mid, c=6, k_r=4)
        rng = np.random.default_rng([SEED, mid, 0x15A7, im.k])
        pairs = I._goal_pairs(6)
        a, b = pairs[int(rng.integers(len(pairs)))]
        if rng.random() < 0.5:
            a, b = b, a
        assert (im.a, im.b) == (a, b)
        tree = M.generate(np.random.default_rng([SEED, mid, 0x3A11] if im.k == 0 else [SEED, mid, 0x3A11, im.k]), 6)
        open_ = {frozenset(e) for e in tree.edges} | {frozenset(e) for e in im.carved}
        pool = [s for s in I.segments(6) if frozenset(s) not in open_ and a not in s and b not in s]
        order = [pool[i] for i in rng.permutation(len(pool))]
        assert [frozenset(e) for e in im.extra] == [frozenset(e) for e in order[:4]]
