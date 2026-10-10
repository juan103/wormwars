"""E3d's records (docs/E3/E3d-DESIGN.md v2.2 §6), observers computed from head paths and events.

Paths are [weys, ticks, 2] head positions (x, y), index t the position after tick t, which is the tick a visit
is stamped with (`MazeWorld._post_move` runs before the tick count increments).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from wormwars.e3 import e3d_records as R
from wormwars.e3 import islands as I
from wormwars.e3 import maze as M

OUTWARD_33 = [((0, 0), (0, 1)), ((0, 0), (1, 0)), ((0, 1), (0, 2)), ((0, 2), (1, 2)),
              ((1, 0), (2, 0)), ((2, 0), (2, 1)), ((1, 2), (2, 2)), ((2, 1), (2, 2))]


def _raster(c, edges):
    n = 4 * c + 1
    wall = np.ones((n, n), dtype=bool)
    for i in range(c):
        for j in range(c):
            wall[1 + 4 * i:4 + 4 * i, 1 + 4 * j:4 + 4 * j] = False
    for u, v in edges:
        M._carve(wall, u, v)
    return wall


def _cells(*xy):
    return np.array([[[x, y] for x, y in xy]], dtype=np.float64)  # one wey


# --- throughput and discovery ----------------------------------------------------------------------------

def test_legs_round_trips_and_later_leg_rate():
    vt = np.full((1, 3, 8), -1)
    vt[0, 0, :3] = [100, 400, 700]  # three visits: two legs, a round trip
    vt[0, 1, :1] = [50]  # one visit: no leg
    out = R.throughput(vt, horizon=1000)
    assert out["visits"].tolist() == [[3, 1, 0]]
    assert out["legs"].tolist() == [[2, 0, 0]]
    assert out["round_trip"].tolist() == [[True, False, False]]
    # the later-leg rate (maze_measures): legs per 1 000 ticks after the first visit, over weys with one
    assert out["later_leg_rate"][0] == pytest.approx((2 / 900 * 1000 + 0) / 2)
    assert out["no_first_visit_share"][0] == pytest.approx(1 / 3)


def test_raw_entries_whatever_the_goal_order_with_censoring():
    """A's block (cell (0, 0)) spans x, y in [1, 4); B's (cell (2, 2)) in [9, 12). The wey enters B at tick 1
    (before ever visiting A) and A at tick 3; the second wey never arrives (censored at H = 5)."""
    a, b = (0, 0), (2, 2)
    paths = np.array([[[6, 6], [10, 10], [6, 6], [2, 2], [2, 2]],
                      [[6, 6]] * 5], dtype=np.float64)
    e = R.entries(paths, a, b)
    assert e.tolist() == [[3, 1], [-1, -1]]
    s = R.discovery(e[None], horizon=5)
    assert s["arrived_a"][0] == pytest.approx(0.5) and s["arrived_b"][0] == pytest.approx(0.5)
    # E3c's censored median: censored weys count as +inf; a median touching one is "not reached" (nan)
    assert math.isnan(s["censored_median_a"][0])
    assert R.discovery(np.array([[[3, 1], [2, 4], [-1, -1]]]), horizon=5)["censored_median_a"][0] == 3


def test_coverage_counts_maze_cells_whose_open_block_the_head_entered():
    p = _cells((2.5, 2.5), (4.2, 2.5), (6.5, 2.5), (6.5, 6.5))  # (0,0), a wall column, (0,1), (1,1)
    assert R.coverage(p, c=3)[0] == pytest.approx(3 / 9)


def test_goal_block_occupancy_uses_the_closed_block():
    p = _cells((4.5, 4.5), (0.5, 0.5), (8.2, 8.2), (6.5, 6.5))  # (1,1)'s closed block is x, y in [4, 9)
    assert R.occupancy(p, (1, 1), (2, 2))[0] == pytest.approx(3 / 4)


# --- physical component contact --------------------------------------------------------------------------

def test_classes_on_a_carved_centre_and_on_a_tree():
    wall = _raster(3, OUTWARD_33)
    lab, cls = R.component_classes(wall, a=(1, 1), b=(0, 0))
    ring = {int(lab[4, 4]), int(lab[4, 8]), int(lab[8, 4]), int(lab[8, 8])}
    assert {cls[r] for r in ring} == {"ring_a"}
    assert cls[int(lab[0, 0])] == "perimeter"
    tree = M.walls_for(run_seed=1, maze_id=0, c=5)[0]
    lab_t, cls_t = R.component_classes(tree.wall, a=(1, 1), b=(3, 3))
    assert set(cls_t.values()) == {"perimeter"}


def test_a_centre_line_entry_records_no_contact():
    """Astra's case: the carved centre with its north side opened; a wey entering down the entrance's centre
    line never has a wall cell in its head's 3 × 3 neighbourhood, so it records no contact, yet visits."""
    wall = _raster(3, OUTWARD_33 + [((0, 1), (1, 1))])  # the goal's north side opened: an entrance
    path = _cells((6.5, 2.5), (6.5, 3.5), (6.5, 4.5), (6.5, 5.5), (6.5, 6.5))  # down the entrance's centre line
    rec = R.contact(path, wall, a=(1, 1), b=(0, 0), visit_tick=np.array([[4, -1]]))
    # x = 6.5 is column 6; the 3 × 3 neighbourhood (columns 5-7) never holds a wall cell on rows 1-7
    assert rec["share"]["perimeter"][0] == 0 and rec["share"]["ring_a"][0] == 0 and rec["share"]["other"][0] == 0
    assert rec["first_class"][0] == "none" and rec["switches"][0] == 0
    assert rec["at_visit"][0] == [("none", "none")]


def test_remembered_component_tie_rule_and_switches_by_class_pair():
    """Two pillars in an open 13 × 13 box: a 2-cell pillar P (left) and a 1-cell pillar Q (right), 3 columns
    apart. A head between them touching both keeps the one it remembers; with none remembered, the one with
    more cells in the neighbourhood."""
    wall = np.zeros((13, 13), dtype=bool)
    wall[0, :] = wall[-1, :] = wall[:, 0] = wall[:, -1] = True
    wall[5:7, 4] = True  # P: rows 5-6, column 4
    wall[6, 6] = True  # Q: row 6, column 6
    lab, _ = I.components(wall)
    P, Q = int(lab[5, 4]), int(lab[6, 6])
    # tick 0: at (5.5, 6.5) the head cell is (5, 6): neighbourhood columns 4-6, rows 5-7: P has 2 cells, Q 1
    # tick 1: no contact (centre); tick 2: (7.5, 6.5) touches Q only: a switch P → Q
    path = _cells((5.5, 6.5), (9.5, 9.5), (7.5, 6.5), (5.5, 6.5))  # tick 3 touches both: Q is kept
    rec = R.contact(path, wall, a=(2, 2), b=(0, 0), visit_tick=np.array([[-1]]))
    assert rec["remembered"][0].tolist() == [P, P, Q, Q]
    assert rec["switches"][0] == 1
    assert rec["switches_by_pair"][0] == {("other", "other"): 1}
    assert rec["first_class"][0] == "other"


def test_a_tree_has_only_perimeter_contacts_and_no_switches():
    mz, pl = M.maze_for(run_seed=3, maze_id=2, episode=0, c=5)
    rng = np.random.default_rng(0)
    path = np.cumsum(rng.normal(0, 0.3, (1, 400, 2)), axis=1) + np.array(M.cell_centre(pl.spawns[0]))
    path = np.clip(path, 0.1, 20.9)
    rec = R.contact(path, mz.wall, a=pl.a, b=pl.b, visit_tick=np.full((1, 4), -1))
    assert rec["share"]["ring_a"][0] == rec["share"]["ring_b"][0] == rec["share"]["other"][0] == 0
    assert rec["switches"][0] == 0


def test_the_component_before_a_visit_skips_the_visited_goals_ring():
    """A fragmented ring: the carved centre with its north and south sides opened leaves the ring in two pieces
    (west and east). A wey touches the perimeter, then the west piece, then visits A: at the visit the
    remembered class is ring_a, and the last component that is not A's ring is the perimeter."""
    wall = _raster(3, OUTWARD_33 + [((0, 1), (1, 1)), ((1, 1), (2, 1))])
    lab, cls = R.component_classes(wall, a=(1, 1), b=(0, 0))
    assert sum(v == "ring_a" for v in cls.values()) >= 2  # the ring is in pieces
    path = _cells((6.5, 1.5), (5.5, 3.5), (6.5, 5.5), (6.5, 6.5))
    # tick 0: head cell (6, 1): neighbourhood rows 0-2 hold the outer wall (perimeter)
    # tick 1: (5, 3): rows 2-4, columns 4-6: the post (4, 4) of A's ring → ring_a
    rec = R.contact(path, wall, a=(1, 1), b=(0, 0), visit_tick=np.array([[3, -1]]))
    assert rec["at_visit"][0] == [("ring_a", "perimeter")]


# --- per maze -------------------------------------------------------------------------------------------

def test_maze_measures_on_a_hand_built_maze():
    c = 3
    edges = [((0, 0), (0, 1)), ((0, 1), (0, 2)), ((0, 2), (1, 2)), ((1, 2), (2, 2)), ((2, 2), (2, 1)), ((2, 1), (2, 0)),
             ((2, 0), (1, 0)), ((1, 0), (1, 1))]  # a spiral: a path through all nine cells
    mz = M.Maze(c, _raster(c, edges), edges)
    pl = M.Placement((0, 0), (1, 1), ((0, 2),))
    m = R.maze_measures(mz, pl)
    assert m["open_share"] == pytest.approx(8 / 12)
    assert m["junctions"] == 0 and m["dead_ends"] == 2
    assert m["detour"] == pytest.approx(8 / 2)
    assert m["entrances"] == (1, 1)
    # spawn (0, 2) → A (0, 0): the straight line along row 0's centre is free; → B (1, 1) crosses a wall
    assert m["line_of_sight_share"] == pytest.approx(1 / 2)


def test_the_scent_reach_flag():
    """The perimeter track is every free cell 8-adjacent to a perimeter wall cell. On a tree every goal is
    flagged (its own block touches the outer walls' component). The carved centre of a 3 × 3 with its north
    side opened: from its centre cell (6, 6), the nearest track cell is 5 free steps away (up the entrance to
    row 1), so it is flagged at d ≤ 8 and not at d ≤ 4."""
    mz, pl = M.maze_for(run_seed=3, maze_id=2, episode=0, c=5)
    assert R.scent_reach(mz, pl.a) and R.scent_reach(mz, pl.b)
    edges = OUTWARD_33 + [((0, 1), (1, 1))]
    carved = M.Maze(3, _raster(3, edges), edges)
    assert R.scent_reach(carved, (1, 1))
    assert not R.scent_reach(carved, (1, 1), reach=4)


# --- the bootstrap ---------------------------------------------------------------------------------------

def test_the_bootstrap_recomputes_the_blind_maximum_in_each_resample():
    """Two blind members whose best flips across mazes: the resampled B_max is the maximum of the resampled
    means, so its interval sits above both members' own intervals' lower ends, never the argmax member's."""
    blind = {"x": np.array([3.0, 0.0, 3.0, 0.0]), "y": np.array([0.0, 2.0, 0.0, 2.0])}
    bs = R.bootstrap_bmax(blind, resamples=2000, seed=20_261_011)
    assert bs["point"] == pytest.approx(1.5)
    assert bs["draws"].shape == (2000,)
    assert (bs["draws"] >= 1.0 - 1e-12).all()  # max(mean x, mean y) ≥ 1 for any resample of these mazes


def test_the_batched_contact_equals_the_reference_on_island_mazes():
    """`contact_batch` (vectorised over colonies and weys, for the runner) equals `contact` (the readable
    reference) on random walks over carved mazes, visits included."""
    rng = np.random.default_rng(4)
    paths, walls, goals, vts = [], [], [], []
    for mid in range(30_000, 30_004):
        mz, pl, _ = I.maze_for(run_seed=1_190_000, maze_id=mid, episode=0, c=6, k_r=2)
        start = np.array(M.cell_centre(pl.a))
        p = start + np.cumsum(rng.normal(0, 0.6, (3, 300, 2)), axis=1)
        paths.append(np.clip(p, 0.01, 24.99))
        walls.append(mz.wall)
        goals.append((pl.a, pl.b))
        vt = np.full((3, 6), -1)
        vt[:, :3] = np.sort(rng.choice(300, size=(3, 3), replace=True), axis=1)
        vts.append(vt)
    batch = R.contact_batch(np.stack(paths), walls, goals, np.stack(vts))
    for k in range(4):
        ref = R.contact(paths[k], walls[k], *goals[k], vts[k])
        for cl in R.CLASSES:
            assert np.allclose(batch["share"][cl][k], ref["share"][cl])
        assert batch["first_class"][k] == ref["first_class"]
        assert batch["switches"][k].tolist() == ref["switches"].tolist()
        assert batch["switches_by_pair"][k] == ref["switches_by_pair"]
        assert batch["at_visit"][k] == ref["at_visit"]
