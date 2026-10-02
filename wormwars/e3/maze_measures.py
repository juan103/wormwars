"""E3b-0's measures (docs/E3/E3b-0-PLAN.md §3b, §3c). The colony is the unit; a colony summary is a mean
over its weys. Inputs are `MazeWorld.task_events` arrays: `visit_tick` [colonies, weys, legs] (−1 padded)
and `first_b_tick` [colonies, weys] (−1: none).

- **Legs:** a leg is a confirmed visit after the previous one, so a wey's legs are its visits − 1.
- **The later-leg rate:** legs per 1 000 ticks after each wey's first visit (the ticks from it to the
  horizon), averaged over the weys that made one; the share of weys that did not is reported apart, and a
  colony in which none did scores 0.
- **The first-B time of later discoverers:** the colony's first-B times, nonarrivals at the horizon,
  sorted; the mean of order statistics 2 to 8 (the earliest dropped, whoever it is).
- **The first discovery of A:** the colony's earliest first visit (the horizon if none).
- **Route cells (geometric):** the open cells of the maze cells on the tree path from A to B and of the
  gaps between them (the A-B route found by breadth-first search on the tree).
- **The gradient share:** the share of route cells (at path distance ≥ 1 from the source) whose closer
  route neighbours (4-adjacent, one step nearer by free distance) hold more on average.
- **The route-permuted trail:** the route cells' values permuted at random; every other cell unchanged.
- **`world_ci`:** the paired percentile bootstrap over mazes of mean(a − b), two-sided 95% (E2d's rule,
  10 000 resamples, seed 0).
"""

from __future__ import annotations

from collections import deque

import numpy as np

from . import maze as M

RESAMPLES, CI_SEED = 10_000, 0


def legs(visit_tick: np.ndarray) -> np.ndarray:
    """[colonies, weys]: each wey's legs."""
    return np.maximum((visit_tick >= 0).sum(-1) - 1, 0)


def colony_mean(x: np.ndarray) -> np.ndarray:
    return np.asarray(x, dtype=np.float64).mean(axis=-1)


def later_leg_rate(visit_tick: np.ndarray, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    """([colonies] the mean later-leg rate per 1 000 ticks over weys with a first visit, 0 if none;
    [colonies] the share of weys with no first visit)."""
    first = visit_tick[..., 0]
    seen = first >= 0
    span = np.where(seen, horizon - first, 1).astype(np.float64)
    rate = np.where(seen, legs(visit_tick) / span * 1000.0, 0.0)
    n = seen.sum(-1)
    mean = np.where(n > 0, rate.sum(-1) / np.maximum(n, 1), 0.0)
    return mean, 1.0 - n / seen.shape[-1]


def later_first_b(first_b_tick: np.ndarray, horizon: int) -> np.ndarray:
    """[colonies]: the mean of order statistics 2-8 of the first-B times, nonarrivals at the horizon."""
    t = np.where(first_b_tick >= 0, first_b_tick, horizon).astype(np.float64)
    t = np.sort(t, axis=-1)
    return t[..., 1:8].mean(axis=-1)


def first_discovery(visit_tick: np.ndarray, horizon: int) -> np.ndarray:
    first = visit_tick[..., 0]
    return np.where(first >= 0, first, horizon).min(axis=-1)


def tree_path(mz: M.Maze, a, b) -> list:
    nb = mz.neighbours()
    prev = {a: None}
    q = deque([a])
    while q:
        u = q.popleft()
        for v in nb[u]:
            if v not in prev:
                prev[v] = u
                q.append(v)
    path = [b]
    while path[-1] != a:
        path.append(prev[path[-1]])
    return path[::-1]


def route_cells(mz: M.Maze, a, b) -> np.ndarray:
    """[side, side] bool: the open cells on the A-B route."""
    out = np.zeros_like(mz.wall)
    path = tree_path(mz, a, b)
    for i, j in path:
        out[1 + 4 * i:4 + 4 * i, 1 + 4 * j:4 + 4 * j] = True
    for (i, j), (k, l) in zip(path, path[1:]):
        if k != i:
            out[4 + 4 * min(i, k), 1 + 4 * j:4 + 4 * j] = True
        else:
            out[1 + 4 * i:4 + 4 * i, 4 + 4 * min(j, l)] = True
    return out & ~mz.wall


def gradient_share(field: np.ndarray, mz: M.Maze, source, route: np.ndarray) -> float:
    d = mz.free_distance(source)
    n = field.shape[0]
    rising, counted = 0, 0
    for y, x in zip(*np.nonzero(route)):
        if not np.isfinite(d[y, x]) or d[y, x] < 1:
            continue
        closer = [field[yy, xx] for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1))
                  if 0 <= yy < n and 0 <= xx < n and route[yy, xx] and d[yy, xx] == d[y, x] - 1]
        if closer:
            counted += 1
            rising += float(np.mean(closer)) > float(field[y, x])
    return rising / counted if counted else float("nan")


def route_permuted(field: np.ndarray, route: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    out = np.array(field, copy=True)
    vals = out[route]
    out[route] = vals[rng.permutation(len(vals))]
    return out


def world_ci(a, b, resamples: int = RESAMPLES, seed: int = CI_SEED) -> dict:
    d = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    rng = np.random.default_rng(seed)
    m = d[rng.integers(0, len(d), size=(resamples, len(d)))].mean(axis=1)
    return {"mean": float(d.mean()), "lo95": float(np.percentile(m, 2.5)), "hi95": float(np.percentile(m, 97.5)),
            "n": int(len(d))}
