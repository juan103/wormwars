"""E3d's records (docs/E3/E3d-DESIGN.md v2.2 §6): observers computed from head paths and the world's events.
They never touch a rollout.

A path is [weys, ticks, 2] head positions (x, y) in grid cells; index t is the position after tick t, the tick
a visit is stamped with (`MazeWorld._post_move` runs before the tick count increments). Maze cell (i, j)'s open
block is grid rows 1 + 4i .. 3 + 4i and columns 1 + 4j .. 3 + 4j; its closed block rows 4i .. 4i + 4.

- **throughput:** visits, legs (visits − 1, at least 0), round trips (legs ≥ 2), `maze_measures`' later-leg
  rate and the share of weys with no first visit;
- **discovery:** the first tick the head enters each goal's open block, whatever the goal order; nonarrivals
  censored, and E3c's censored median (a median touching a censored wey is "not reached", nan here);
- **coverage** and **goal-block occupancy**;
- **physical component contact:** the raster's 4-connected wall components, classed perimeter > ring_a >
  ring_b > other (a goal ring: not perimeter, with a cell in that goal's closed block); each tick, the
  components with a wall cell in the head cell's 3 × 3 neighbourhood; the remembered component (unchanged
  without contact; kept if contacted, otherwise the one with most cells in the neighbourhood, ties to the
  smallest label); switches after the first acquisition, in total and by class pair; at each visit, the
  remembered class and the class of the last remembered component not in the visited goal's ring;
- **per maze:** open share, junctions, dead ends, the A-B detour, the goals' entrances, line of sight from
  the spawns to the goals, and the scent-reach flag;
- **the bootstrap** of B_max, the maximum over blind members recomputed in each resample of mazes.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np

from . import islands as I
from . import maze as M
from . import maze_measures as MM
from .e3c_stats import censored_median

CLASSES = ("perimeter", "ring_a", "ring_b", "other")


def _cell_ix(paths):
    return np.floor(paths[..., 0]).astype(np.int64), np.floor(paths[..., 1]).astype(np.int64)


def _in_open_block(paths, cell):
    ix, iy = _cell_ix(paths)
    i, j = cell
    return (ix >= 1 + 4 * j) & (ix < 4 + 4 * j) & (iy >= 1 + 4 * i) & (iy < 4 + 4 * i)


def _in_closed_block(paths, cell):
    ix, iy = _cell_ix(paths)
    i, j = cell
    return (ix >= 4 * j) & (ix <= 4 * j + 4) & (iy >= 4 * i) & (iy <= 4 * i + 4)


# --- throughput and discovery ----------------------------------------------------------------------------

def throughput(visit_tick: np.ndarray, horizon: int) -> dict:
    """`visit_tick` [colonies, weys, legs], −1 padded. Per wey: visits, legs, round trips; per colony: the
    later-leg rate and the share of weys with no first visit (`maze_measures.later_leg_rate`)."""
    visits = (visit_tick >= 0).sum(-1)
    legs = MM.legs(visit_tick)
    rate, none = MM.later_leg_rate(visit_tick, horizon)
    return {"visits": visits, "legs": legs, "round_trip": legs >= 2, "later_leg_rate": rate,
            "no_first_visit_share": none}


def entries(paths: np.ndarray, a, b) -> np.ndarray:
    """[weys, (A, B)]: the first tick each wey's head is in each goal's open block, −1 if never."""
    out = np.full((paths.shape[0], 2), -1, dtype=np.int64)
    for k, g in enumerate((a, b)):
        inside = _in_open_block(paths, g)
        hit = inside.any(-1)
        out[hit, k] = inside[hit].argmax(-1)
    return out


def discovery(ent: np.ndarray, horizon: int) -> dict:
    """`ent` [colonies, weys, (A, B)] from `entries`. Per colony: the share arriving at each goal and E3c's
    censored median of the first-entry tick (nan where it touches a censored wey)."""
    out = {}
    for k, g in enumerate("ab"):
        e = ent[..., k]
        out[f"arrived_{g}"] = (e >= 0).mean(-1)
        med = []
        for row in e:
            m = censored_median(np.where(row >= 0, row, np.inf))
            med.append(m if isinstance(m, float) else math.nan)
        out[f"censored_median_{g}"] = np.array(med)
    return out


def coverage(paths: np.ndarray, c: int) -> np.ndarray:
    """[weys]: the share of the c × c maze cells whose open block the head entered."""
    ix, iy = _cell_ix(paths)
    inb = (ix % 4 != 0) & (iy % 4 != 0) & (ix > 0) & (iy > 0) & (ix < 4 * c) & (iy < 4 * c)
    out = []
    for w in range(paths.shape[0]):
        cells = {((y - 1) // 4, (x - 1) // 4) for x, y in zip(ix[w][inb[w]], iy[w][inb[w]])}
        out.append(len(cells) / (c * c))
    return np.array(out)


def occupancy(paths: np.ndarray, a, b) -> np.ndarray:
    """[weys]: the share of ticks the head is in either goal's closed 5 × 5 block (a flag, not contact)."""
    return (_in_closed_block(paths, a) | _in_closed_block(paths, b)).mean(-1)


# --- physical component contact --------------------------------------------------------------------------

def component_classes(wall: np.ndarray, a, b) -> tuple[np.ndarray, dict]:
    """The labels and each label's class: perimeter (touches the border), else ring_a / ring_b (a cell in
    that goal's closed block), else other."""
    lab, border = I.components(wall)
    la, lb = I.block_labels(lab, a), I.block_labels(lab, b)
    cls = {}
    for v in set(int(x) for x in np.unique(lab)) - {0}:
        cls[v] = "perimeter" if v in border else "ring_a" if v in la else "ring_b" if v in lb else "other"
    return lab, cls


def contact(paths: np.ndarray, wall: np.ndarray, a, b, visit_tick: np.ndarray) -> dict:
    """Physical contact for each wey of one colony. `visit_tick` [weys, legs] (visits alternate A, B, ...)."""
    lab, cls = component_classes(wall, a, b)
    H, W = lab.shape
    n_w, T = paths.shape[:2]
    ix, iy = _cell_ix(paths)
    share = {k: np.zeros(n_w) for k in CLASSES}
    remembered = np.zeros((n_w, T), dtype=np.int64)
    first_class, switches, pairs, at_visit = [], np.zeros(n_w, dtype=np.int64), [], []
    for w in range(n_w):
        mem, first, outside_a, outside_b, by_pair = 0, "none", 0, 0, {}
        last_outside = {0: 0, 1: 0}  # per goal: the last remembered component not in that goal's ring
        counts = {k: 0 for k in CLASSES}
        for t in range(T):
            x, y = int(ix[w, t]), int(iy[w, t])
            win = lab[max(y - 1, 0):min(y + 2, H), max(x - 1, 0):min(x + 2, W)]
            vals, n = np.unique(win[win > 0], return_counts=True)
            for v in vals:
                counts[cls[int(v)]] += 1
            if len(vals):
                if mem not in vals:
                    best = sorted(zip(-n, vals))[0][1]
                    if mem and int(best) != mem:
                        switches[w] += 1
                        key = (cls[mem], cls[int(best)])
                        by_pair[key] = by_pair.get(key, 0) + 1
                    mem = int(best)
                    if first == "none":
                        first = cls[mem]
            remembered[w, t] = mem
            if mem:
                if cls[mem] != "ring_a":
                    last_outside[0] = mem
                if cls[mem] != "ring_b":
                    last_outside[1] = mem
        for k in CLASSES:
            share[k][w] = counts[k] / T  # ticks with contact of that class (a tick may count in two)
        recs = []
        for v, t in enumerate(visit_tick[w]):
            if t < 0:
                break
            g = v % 2
            # the remembered component at the visit; and the last one outside the visited goal's ring
            mem_t = int(remembered[w, t])
            outside = 0
            for s in range(t, -1, -1):
                m = int(remembered[w, s])
                if m and cls[m] != ("ring_a" if g == 0 else "ring_b"):
                    outside = m
                    break
            recs.append((cls[mem_t] if mem_t else "none", cls[outside] if outside else "none"))
        first_class.append(first)
        pairs.append(by_pair)
        at_visit.append(recs)
    return {"share": share, "remembered": remembered, "first_class": first_class, "switches": switches,
            "switches_by_pair": pairs, "at_visit": at_visit}


# --- per maze -------------------------------------------------------------------------------------------

def _line_free(wall, p, q, step=0.05) -> bool:
    n = max(int(math.ceil(math.hypot(q[0] - p[0], q[1] - p[1]) / step)), 1)
    for k in range(n + 1):
        x = p[0] + (q[0] - p[0]) * k / n
        y = p[1] + (q[1] - p[1]) * k / n
        if wall[int(math.floor(y)), int(math.floor(x))]:
            return False
    return True


def maze_measures(mz: M.Maze, pl: M.Placement) -> dict:
    nb = mz.neighbours()
    deg = {k: len(v) for k, v in nb.items()}
    n_internal = 2 * mz.c * (mz.c - 1)
    d = mz.tree_distance()[pl.a][pl.b]
    manhattan = abs(pl.a[0] - pl.b[0]) + abs(pl.a[1] - pl.b[1])
    pairs = [(s, g) for s in pl.spawns for g in (pl.a, pl.b)]
    los = [_line_free(mz.wall, M.cell_centre(s), M.cell_centre(g)) for s, g in pairs]
    return {"open_share": len({frozenset(e) for e in mz.edges}) / n_internal,
            "junctions": sum(v >= 3 for v in deg.values()), "dead_ends": sum(v == 1 for v in deg.values()),
            "detour": d / manhattan, "entrances": (deg[pl.a], deg[pl.b]),
            "line_of_sight_share": float(np.mean(los)) if los else math.nan}


def scent_reach(mz: M.Maze, goal, reach: int = 8) -> bool:
    """Whether a free cell 8-adjacent to a perimeter wall cell lies within free-path distance `reach` of the
    goal's centre (a grid-field proxy for the scripted follower's threshold, design §2)."""
    lab, border = I.components(mz.wall)
    per = np.isin(lab, list(border)) if border else np.zeros_like(mz.wall)
    near = np.zeros_like(per)
    H, W = per.shape
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            sh = np.zeros_like(per)
            sh[max(dy, 0):H + min(dy, 0), max(dx, 0):W + min(dx, 0)] = per[max(-dy, 0):H + min(-dy, 0),
                                                                         max(-dx, 0):W + min(-dx, 0)]
            near |= sh
    track = near & ~mz.wall
    dist = mz.free_distance(goal)
    return bool((track & (dist <= reach)).any())


# --- the bootstrap ---------------------------------------------------------------------------------------

def bootstrap_bmax(blind: dict, resamples: int, seed: int) -> dict:
    """`blind` {member: [mazes] per-maze scores, paired}. B_max's point estimate and its resampled values,
    the maximum over members recomputed inside each resample of mazes."""
    names = sorted(blind)
    X = np.stack([np.asarray(blind[k], dtype=np.float64) for k in names])  # [members, mazes]
    n = X.shape[1]
    idx = np.random.default_rng(seed).integers(0, n, size=(resamples, n))
    draws = X[:, idx].mean(-1).max(0)  # [resamples]
    return {"point": float(X.mean(1).max()), "argmax": names[int(X.mean(1).argmax())], "draws": draws,
            "interval": (float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975)))}


def _tables(wall, a, b):
    """Per head cell: the contacted components as a bitmask, the best new component (most cells in the
    neighbourhood, ties to the smallest label), and which classes are contacted; and each label's class."""
    lab, cls = component_classes(wall, a, b)
    n_lab = int(lab.max())
    if n_lab > 62:
        raise ValueError(f"{n_lab} wall components: the bitmask holds 62")
    H, W = lab.shape
    mask = np.zeros((H, W), dtype=np.int64)
    best = np.zeros((H, W), dtype=np.int64)
    has = np.zeros((H, W, len(CLASSES)), dtype=bool)
    for y in range(H):
        for x in range(W):
            win = lab[max(y - 1, 0):min(y + 2, H), max(x - 1, 0):min(x + 2, W)]
            vals, n = np.unique(win[win > 0], return_counts=True)
            if len(vals):
                for v in vals:
                    mask[y, x] |= np.int64(1) << np.int64(v)
                    has[y, x, CLASSES.index(cls[int(v)])] = True
                best[y, x] = int(sorted(zip(-n, vals))[0][1])
    cls_of = np.full(n_lab + 1, -1, dtype=np.int64)  # class index per label; −1 for none (label 0)
    for v, c in cls.items():
        cls_of[v] = CLASSES.index(c)
    return mask, best, has, cls_of


def contact_tables(wall, a, b):
    """The per-maze lookup tables `contact_batch` uses; computed once per maze and reused across conditions."""
    return _tables(wall, a, b)


def contact_batch(paths: np.ndarray, walls: list, goals: list, visit_tick: np.ndarray, tables: list | None = None) -> dict:
    """`contact`, vectorised over colonies and weys: `paths` [colonies, weys, ticks, 2], one wall raster and
    one (A, B) per colony, `visit_tick` [colonies, weys, legs]; `tables` optionally `contact_tables` per colony.
    Equal to `contact` per colony (a test)."""
    n_c, n_w, T = paths.shape[:3]
    tabs = tables if tables is not None else [_tables(w, a, b) for w, (a, b) in zip(walls, goals)]
    H, W = walls[0].shape
    ix = np.clip(np.floor(paths[..., 0]).astype(np.int64), 0, W - 1)
    iy = np.clip(np.floor(paths[..., 1]).astype(np.int64), 0, H - 1)
    mask = np.stack([t[0] for t in tabs])[np.arange(n_c)[:, None, None], iy, ix]  # [c, w, T]
    best = np.stack([t[1] for t in tabs])[np.arange(n_c)[:, None, None], iy, ix]
    has = np.stack([t[2] for t in tabs])[np.arange(n_c)[:, None, None], iy, ix]  # [c, w, T, classes]
    width = max(len(t[3]) for t in tabs)
    cls_of = np.full((n_c, width), -1, dtype=np.int64)
    for k, t in enumerate(tabs):
        cls_of[k, :len(t[3])] = t[3]
    ci = np.arange(n_c)[:, None]
    mem = np.zeros((n_c, n_w), dtype=np.int64)
    first = np.full((n_c, n_w), -1, dtype=np.int64)
    switches = np.zeros((n_c, n_w), dtype=np.int64)
    pair = np.zeros((n_c, n_w, len(CLASSES), len(CLASSES)), dtype=np.int64)
    remembered = np.zeros((n_c, n_w, T), dtype=np.int64)
    out_a = np.zeros((n_c, n_w, T), dtype=np.int64)  # the last remembered component not in A's ring
    out_b = np.zeros((n_c, n_w, T), dtype=np.int64)
    la = np.zeros((n_c, n_w), dtype=np.int64)
    lb = np.zeros((n_c, n_w), dtype=np.int64)
    RA, RB = CLASSES.index("ring_a"), CLASSES.index("ring_b")
    for t in range(T):
        m = mask[..., t]
        keep = ((m >> mem) & 1).astype(bool) & (mem > 0)
        new = (m != 0) & ~keep
        changed = new & (mem > 0) & (best[..., t] != mem)
        switches += changed
        cw, ww = np.nonzero(changed)
        np.add.at(pair, (cw, ww, cls_of[cw, mem[cw, ww]], cls_of[cw, best[cw, ww, t]]), 1)
        mem = np.where(new, best[..., t], mem)
        first = np.where((first < 0) & (mem > 0), mem, first)
        remembered[..., t] = mem
        c_mem = cls_of[ci, mem]
        la = np.where((mem > 0) & (c_mem != RA), mem, la)
        lb = np.where((mem > 0) & (c_mem != RB), mem, lb)
        out_a[..., t], out_b[..., t] = la, lb
    share = {k: has[..., i].mean(-1) for i, k in enumerate(CLASSES)}
    name = lambda k, v: CLASSES[cls_of[k, v]] if v > 0 else "none"
    first_class = [[name(k, int(first[k, w])) for w in range(n_w)] for k in range(n_c)]
    by_pair = [[{(CLASSES[i], CLASSES[j]): int(pair[k, w, i, j]) for i in range(len(CLASSES))
                 for j in range(len(CLASSES)) if pair[k, w, i, j]} for w in range(n_w)] for k in range(n_c)]
    at_visit = []
    for k in range(n_c):
        rows = []
        for w in range(n_w):
            recs = []
            for v, t in enumerate(visit_tick[k, w]):
                if t < 0:
                    break
                o = out_a[k, w, t] if v % 2 == 0 else out_b[k, w, t]
                recs.append((name(k, int(remembered[k, w, t])), name(k, int(o))))
            rows.append(recs)
        at_visit.append(rows)
    return {"share": share, "remembered": remembered, "first_class": first_class, "switches": switches,
            "switches_by_pair": by_pair, "at_visit": at_visit}
