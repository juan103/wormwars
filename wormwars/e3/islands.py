"""E3d's island-goal mazes (docs/E3/E3d-DESIGN.md v2.2 §2).

On E3b-1's Wilson tree (drawn from `maze.walls_for`'s own streams, [run seed, id, 0x3A11] at redraw k = 0 and
[run seed, id, 0x3A11, k] after), with a second stream [run seed, id, 0x15A7, k] for the rest:
1. A and B: a pair proposed uniformly among the interior cells' pairs whose rings share no corner post
   (Chebyshev distance ≥ 2), swapped with probability ½ as `maze.place` does;
2. the islands: every closed segment leaving one of a goal's four corner posts outward is opened, so the
   goal's remaining sides and posts are free-standing, and the goal sits in an open 3 × 3 roundabout;
3. k_r further openings: the first k_r of one random order of the remaining closed segments, the goals' own
   sides excluded, so the openings at k_r = 2 are a subset of those at k_r = 4 at a shared redraw index;
4. every opening appended to `Maze.edges`.

The checks on the final maze: A and B island-safe (no wall cell of the perimeter component, 4-connected, in
either goal's closed 5 × 5 block); no wall component touching both goal blocks; the graph distance in
[⌈c/2⌉ + 1, 2c]; a spawn candidate (a cell whose closed block holds no island wall cell, at graph distance ≥ 2
from both goals). A failing maze is redrawn at k + 1, at most `maze.REDRAW_MAX` times.

The spawns are drawn per episode from [run seed, id, episode, 0x9ACE], E3b-1's episode stream.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import ndimage

from . import maze as M

Cell = M.Cell
GOAL_STREAM = 0x15A7


@dataclass(frozen=True)
class IslandMaze:
    maze: M.Maze
    a: Cell
    b: Cell
    k: int  # the redraw index
    carved: tuple  # the segments opened around the goals
    extra: tuple  # the k_r further openings, in order


def segments(c: int) -> list:
    """Every internal wall segment, as the pair of maze cells it separates."""
    return [((i, j), (k, l)) for i in range(c) for j in range(c) for (k, l) in ((i + 1, j), (i, j + 1))
            if k < c and l < c]


def components(wall: np.ndarray) -> tuple[np.ndarray, set]:
    """The wall cells' 4-connected component labels (0 for free cells) and the perimeter labels: every
    component touching the grid's border."""
    lab, _ = ndimage.label(wall)
    edge = np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    return lab, set(int(x) for x in np.unique(edge)) - {0}


def block_labels(lab: np.ndarray, cell: Cell) -> set:
    """The component labels in a maze cell's closed 5 × 5 block (its open block, sides and corner posts)."""
    i, j = cell
    return set(int(x) for x in np.unique(lab[4 * i:4 * i + 5, 4 * j:4 * j + 5])) - {0}


def island_safe(wall: np.ndarray, cell: Cell) -> bool:
    lab, border = components(wall)
    return not (block_labels(lab, cell) & border)


def _segment_posts(seg) -> set:
    """The two corner posts (post (p, q) sits at grid row 4p, column 4q) at the ends of a segment's wall."""
    u, v = sorted(seg)
    if u[0] != v[0]:  # vertical neighbours: the wall row 4 · v[0]
        return {(v[0], u[1]), (v[0], u[1] + 1)}
    return {(u[0], v[1]), (u[0] + 1, v[1])}


def carve_island(wall: np.ndarray, edges: list, goal: Cell, c: int) -> list:
    """Open every closed segment that leaves one of `goal`'s four corner posts and is not one of the goal's
    own sides; append each to `edges`, in `segments` order. Returns the opened segments."""
    gi, gj = goal
    posts = {(gi, gj), (gi, gj + 1), (gi + 1, gj), (gi + 1, gj + 1)}
    open_ = {frozenset(e) for e in edges}
    out = []
    for s in segments(c):
        if frozenset(s) in open_ or goal in s or not (_segment_posts(s) & posts):
            continue
        M._carve(wall, *s)
        edges.append(s)
        out.append(s)
    return out


def spawn_candidates(mz: M.Maze, a: Cell, b: Cell) -> list:
    """The cells whose closed block holds no island wall cell, at graph distance ≥ 2 from A and B, sorted."""
    lab, border = components(mz.wall)
    d = mz.tree_distance()
    return sorted(s for s in np.ndindex(mz.c, mz.c)
                  if block_labels(lab, s) <= border and d[s][a] >= 2 and d[s][b] >= 2)


def _goal_pairs(c: int) -> list:
    interior = [(i, j) for i in range(1, c - 1) for j in range(1, c - 1)]
    return [(a, b) for x, a in enumerate(interior) for b in interior[x + 1:]
            if max(abs(a[0] - b[0]), abs(a[1] - b[1])) >= 2]


def _draw(run_seed: int, maze_id: int, c: int, k_r: int, k: int) -> IslandMaze | None:
    tree_key = [run_seed, maze_id, 0x3A11] if k == 0 else [run_seed, maze_id, 0x3A11, k]
    mz = M.generate(np.random.default_rng(tree_key), c)
    rng = np.random.default_rng([run_seed, maze_id, GOAL_STREAM, k])
    pairs = _goal_pairs(c)
    if not pairs:
        return None
    a, b = pairs[int(rng.integers(len(pairs)))]
    if rng.random() < 0.5:
        a, b = b, a
    wall, edges = mz.wall.copy(), list(mz.edges)
    carved = carve_island(wall, edges, a, c) + carve_island(wall, edges, b, c)
    open_ = {frozenset(e) for e in edges}
    pool = [s for s in segments(c) if frozenset(s) not in open_ and a not in s and b not in s]
    order = [pool[i] for i in rng.permutation(len(pool))]
    extra = order[:k_r]
    if len(extra) < k_r:
        return None
    for s in extra:
        M._carve(wall, *s)
        edges.append(s)
    out = M.Maze(c, wall, edges)
    if failed_check(out, a, b) is not None:
        return None
    return IslandMaze(out, a, b, k, tuple(carved), tuple(extra))


def failed_check(mz: M.Maze, a: Cell, b: Cell) -> str | None:
    """The first check the final maze fails, or None: "island" (a perimeter wall cell in a goal's closed
    block), "shared" (one wall component in both goal blocks), "distance", "spawn"."""
    lab, border = components(mz.wall)
    la, lb = block_labels(lab, a), block_labels(lab, b)
    if (la | lb) & border:
        return "island"
    if la & lb:
        return "shared"
    if not (math.ceil(mz.c / 2) + 1 <= mz.tree_distance()[a].get(b, math.inf) <= 2 * mz.c):
        return "distance"
    if not spawn_candidates(mz, a, b):
        return "spawn"
    return None


def islands_for(*, run_seed: int, maze_id: int, c: int, k_r: int) -> IslandMaze:
    """The island maze of (run seed, maze id) at k_r: the first draw k = 0, 1, … that passes the checks."""
    for k in range(M.REDRAW_MAX + 1):
        im = _draw(run_seed, maze_id, c, k_r, k)
        if im is not None:
            return im
    raise ValueError(f"maze {maze_id} (c={c}, k_r={k_r}) has no feasible island maze within {M.REDRAW_MAX} redraws")


def maze_for(*, run_seed: int, maze_id: int, episode: int, c: int, k_r: int,
             n_spawns: int = 4) -> tuple[M.Maze, M.Placement, IslandMaze]:
    """The walls and goals from (run seed, maze id) only; up to `n_spawns` spawns from the episode stream."""
    im = islands_for(run_seed=run_seed, maze_id=maze_id, c=c, k_r=k_r)
    cands = spawn_candidates(im.maze, im.a, im.b)
    order = np.random.default_rng([run_seed, maze_id, episode, 0x9ACE]).permutation(len(cands))
    return im.maze, M.Placement(im.a, im.b, tuple(cands[k] for k in order[:n_spawns])), im
