"""E3b's tree mazes (docs/E3/E3b-0-PLAN.md §1a).

A uniform random spanning tree (Wilson's algorithm) on a c × c grid of maze cells, carved with 3-wide
corridors and 1-cell walls: the grid is (4c + 1) × (4c + 1), `wall[y, x]` True for wall cells. Maze cell
(i, j) (row i, column j) owns the open block of rows 1 + 4i .. 3 + 4i and columns 1 + 4j .. 3 + 4j; a tree
edge opens the 3-wide gap in the wall between two neighbouring cells.

`maze_for` keys the walls by (run seed, maze id) and the placements by (run seed, maze id, episode), so a
placement never moves the walls. The placements are A and B at two distinct dead ends whose tree distance
is in [⌈c/2⌉ + 1, 2c], drawn only among pairs that leave a spawn candidate, and spawns at up to `n_spawns`
other dead ends, each at least 2 maze cells from A and from B. A maze with no eligible pair raises.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

import numpy as np

Cell = tuple[int, int]


@dataclass
class Maze:
    c: int
    wall: np.ndarray  # [4c + 1, 4c + 1] bool
    edges: list = field(default_factory=list)  # tree edges between maze cells

    def neighbours(self) -> dict:
        nb = {k: [] for k in np.ndindex(self.c, self.c)}
        for u, v in self.edges:
            nb[u].append(v)
            nb[v].append(u)
        return nb

    def dead_ends(self) -> list:
        return sorted(k for k, v in self.neighbours().items() if len(v) == 1)

    def tree_distance(self) -> dict:
        nb = self.neighbours()
        out = {}
        for s in nb:
            d = {s: 0}
            q = deque([s])
            while q:
                u = q.popleft()
                for v in nb[u]:
                    if v not in d:
                        d[v] = d[u] + 1
                        q.append(v)
            out[s] = d
        return out

    def free_distance(self, cell: Cell) -> np.ndarray:
        """Breadth-first-search distance over 4-connected free grid cells from the maze cell's centre
        grid cell; inf in walls and anywhere unreachable."""
        n = self.wall.shape[0]
        dist = np.full((n, n), np.inf)
        y0, x0 = 2 + 4 * cell[0], 2 + 4 * cell[1]
        dist[y0, x0] = 0
        q = deque([(y0, x0)])
        while q:
            y, x = q.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < n and 0 <= xx < n and not self.wall[yy, xx] and np.isinf(dist[yy, xx]):
                    dist[yy, xx] = dist[y, x] + 1
                    q.append((yy, xx))
        return dist


@dataclass(frozen=True)
class Placement:
    a: Cell
    b: Cell
    spawns: tuple


def cell_centre(cell: Cell) -> tuple[float, float]:
    """(x, y) world coordinates of a maze cell's centre."""
    i, j = cell
    return (2.5 + 4 * j, 2.5 + 4 * i)


def _carve(wall: np.ndarray, u: Cell, v: Cell) -> None:
    (i, j), (k, l) = u, v
    if k != i:  # vertical neighbours: the horizontal wall row between them
        wall[4 + 4 * min(i, k), 1 + 4 * j:4 + 4 * j] = False
    else:
        wall[1 + 4 * i:4 + 4 * i, 4 + 4 * min(j, l)] = False


def generate(rng: np.random.Generator, c: int) -> Maze:
    """A uniform spanning tree by Wilson's algorithm (loop-erased random walks), which branches far more
    than a depth-first search (both reviewers of E3b-0's plan v1)."""
    n = 4 * c + 1
    wall = np.ones((n, n), dtype=bool)
    for i in range(c):
        for j in range(c):
            wall[1 + 4 * i:4 + 4 * i, 1 + 4 * j:4 + 4 * j] = False
    cells = [(i, j) for i in range(c) for j in range(c)]
    in_tree = {cells[int(rng.integers(len(cells)))]}
    edges = []
    for start in cells:
        if start in in_tree:
            continue
        nxt = {}
        u = start
        while u not in in_tree:  # a random walk, remembering only the last exit from each cell
            opts = [(u[0] + di, u[1] + dj) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= u[0] + di < c and 0 <= u[1] + dj < c]
            nxt[u] = opts[int(rng.integers(len(opts)))]
            u = nxt[u]
        u = start
        while u not in in_tree:  # the loop-erased path, added to the tree
            v = nxt[u]
            edges.append((u, v))
            _carve(wall, u, v)
            in_tree.add(u)
            u = v
    return Maze(c, wall, edges)


def eligible_pairs(mz: Maze) -> list:
    """The (A, B) pairs of distinct dead ends with tree distance in [⌈c/2⌉ + 1, 2c] that leave at least
    one spawn candidate (a dead end at least 2 maze cells from both)."""
    c = mz.c
    ends = mz.dead_ends()
    d = mz.tree_distance()
    lo, hi = math.ceil(c / 2) + 1, 2 * c
    out = []
    for a in ends:
        for b in ends:
            if a < b and lo <= d[a][b] <= hi and any(s not in (a, b) and d[s][a] >= 2 and d[s][b] >= 2 for s in ends):
                out.append((a, b))
    return out


def place(rng: np.random.Generator, mz: Maze, n_spawns: int = 4) -> Placement | None:
    """A, B and the spawns, drawn only among eligible pairs; None if the maze has none."""
    d = mz.tree_distance()
    pairs = eligible_pairs(mz)
    if not pairs:
        return None
    a, b = pairs[int(rng.integers(len(pairs)))]
    if rng.random() < 0.5:
        a, b = b, a
    cands = [s for s in mz.dead_ends() if s not in (a, b) and d[s][a] >= 2 and d[s][b] >= 2]
    order = rng.permutation(len(cands))
    return Placement(a, b, tuple(cands[k] for k in order[:n_spawns]))


REDRAW_MAX = 64


def walls_for(*, run_seed: int, maze_id: int, c: int) -> tuple[Maze, int]:
    """The maze's walls and their redraw index k. k = 0 is the original stream [run seed, maze id, 0x3A11],
    unchanged. Walls with no eligible A/B pair are redrawn from [run seed, maze id, 0x3A11, k] for
    k = 1, 2, …, and the first walls with an eligible pair are accepted. The redraw is keyed by the id, never
    by the episode, and beyond REDRAW_MAX redraws it raises (E3b-1's Amendment 1, D190; before it, an
    infeasible maze raised)."""
    mz = generate(np.random.default_rng([run_seed, maze_id, 0x3A11]), c)
    k = 0
    while not eligible_pairs(mz):
        k += 1
        if k > REDRAW_MAX:
            raise ValueError(f"maze {maze_id} (c={c}) has no feasible walls within {REDRAW_MAX} redraws")
        mz = generate(np.random.default_rng([run_seed, maze_id, 0x3A11, k]), c)
    return mz, k


def maze_for(*, run_seed: int, maze_id: int, episode: int, c: int, n_spawns: int = 4) -> tuple[Maze, Placement]:
    """The walls from (run seed, maze id) only (`walls_for`: never redrawn by the episode), the placements from
    (run seed, maze id, episode) on those walls (plan §1a)."""
    mz, _ = walls_for(run_seed=run_seed, maze_id=maze_id, c=c)
    p = place(np.random.default_rng([run_seed, maze_id, episode, 0x9ACE]), mz, n_spawns)
    if p is None:  # unreachable: walls_for accepts only walls with an eligible pair
        raise ValueError(f"maze {maze_id} (c={c}) has no eligible placement")
    return mz, p
