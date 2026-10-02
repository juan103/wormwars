"""E3b-0's measures (docs/E3/E3b-0-PLAN.md §3b, §3c): legs, the later-leg rate, the first-B time of later
discoverers, the first discovery of A, route cells, the gradient share, the route-permuted trail and the
paired interval over mazes."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.e3 import maze as M
from wormwars.e3 import maze_measures as MM


def _ticks(rows, legs=8):
    out = np.full((1, len(rows), legs), -1, dtype=np.int64)
    for b, r in enumerate(rows):
        out[0, b, :len(r)] = r
    return out


def test_legs_are_visits_after_the_first():
    vt = _ticks([[10, 50, 90], [30], []])
    assert MM.legs(vt).tolist() == [[2, 0, 0]]
    assert MM.colony_mean(MM.legs(vt)).tolist() == [pytest.approx(2 / 3)]


def test_the_later_leg_rate_counts_only_the_time_after_each_weys_first_visit():
    vt = _ticks([[0, 100, 200], [500, 1000], []])
    rate, unvisited = MM.later_leg_rate(vt, horizon=1000)
    # wey 0: 2 legs in 1000 ticks; wey 1: 1 leg in 500 ticks; wey 2: no first visit, counted apart
    assert rate.tolist() == [pytest.approx((2.0 + 2.0) / 2)]
    assert unvisited.tolist() == [pytest.approx(1 / 3)]
    none, share = MM.later_leg_rate(_ticks([[], []]), horizon=1000)
    assert none.tolist() == [0.0] and share.tolist() == [1.0]  # a colony with no first visit scores 0


def test_the_first_b_time_of_later_discoverers_drops_the_earliest_and_caps_at_the_horizon():
    fb = np.array([[5, 40, -1, 30, 20, -1, 60, 10]])  # -1: never reached B
    got = MM.later_first_b(fb, horizon=100)
    want = np.mean(sorted([5, 40, 100, 30, 20, 100, 60, 10])[1:8])
    assert got.tolist() == [pytest.approx(want)]
    assert MM.later_first_b(np.full((1, 8), -1), horizon=100).tolist() == [100.0]


def test_the_first_discovery_of_a_is_the_colonys_earliest_first_visit():
    vt = _ticks([[70, 90], [30], []])
    assert MM.first_discovery(vt, horizon=500).tolist() == [30]
    assert MM.first_discovery(_ticks([[], []]), horizon=500).tolist() == [500]


def test_route_cells_are_the_blocks_and_gaps_on_the_tree_path():
    mz, pl = M.maze_for(run_seed=3, maze_id=5, episode=0, c=6)
    route = MM.route_cells(mz, pl.a, pl.b)
    path = MM.tree_path(mz, pl.a, pl.b)
    assert path[0] == pl.a and path[-1] == pl.b
    assert route.sum() == 9 * len(path) + 3 * (len(path) - 1)
    assert not (route & mz.wall).any()
    dist = mz.free_distance(pl.a)
    assert np.isfinite(dist[route]).all()


def test_the_gradient_share_reads_a_slope_toward_the_source():
    mz, pl = M.maze_for(run_seed=3, maze_id=5, episode=0, c=6)
    route = MM.route_cells(mz, pl.a, pl.b)
    d = mz.free_distance(pl.a)
    slope = np.where(route, np.exp(-0.1 * np.where(np.isfinite(d), d, 0)), 0.0)
    assert MM.gradient_share(slope, mz, pl.a, route) == 1.0
    flat = np.where(route, 1.0, 0.0)
    assert MM.gradient_share(flat, mz, pl.a, route) == 0.0
    away = np.where(route, 1 - np.exp(-0.1 * np.where(np.isfinite(d), d, 0)), 0.0)
    assert MM.gradient_share(away, mz, pl.a, route) == 0.0


def test_the_route_permutation_keeps_the_values_and_breaks_the_slope():
    mz, pl = M.maze_for(run_seed=3, maze_id=5, episode=0, c=6)
    route = MM.route_cells(mz, pl.a, pl.b)
    d = mz.free_distance(pl.a)
    field = np.where(route, np.exp(-0.1 * np.where(np.isfinite(d), d, 0)), 0.0)
    field[~route & ~mz.wall] = 0.01  # off-route values stay where they are
    perm = MM.route_permuted(field, route, np.random.default_rng(0))
    assert np.array_equal(np.sort(perm[route]), np.sort(field[route]))
    assert np.array_equal(perm[~route], field[~route])
    assert MM.gradient_share(perm, mz, pl.a, route) < 0.7


def test_the_paired_interval_over_mazes():
    rng = np.random.default_rng(1)
    a = rng.normal(1.0, 0.5, 256)
    b = a - 0.3 + rng.normal(0, 0.05, 256)
    ci = MM.world_ci(a, b)
    assert ci["mean"] == pytest.approx(0.3, abs=0.02) and ci["lo95"] > 0.25 and ci["hi95"] < 0.35
    same = MM.world_ci(a, a)
    assert same["lo95"] == same["hi95"] == 0.0
