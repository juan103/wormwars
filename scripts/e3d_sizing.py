"""E3d's sizing (design v2; both reviewers of v1, D222): the share of mazes with a full feasible placement, and how
varied the placements are, for each construction, maze size and A-B distance bound. CPU only; no reading depends
on it.

    python scripts/e3d_sizing.py      # writes docs/E3/e3d-sizing.json

**A full feasible placement:**
- A and B on island-safe cells, with no wall component touching both goal blocks;
- their graph distance in [lo, 2c];
- at least one spawn cell whose 5 × 5 block holds no island wall cell, at least 2 maze cells from A and B.

**The constructions:**
- **random k:** k closed internal segments of the Wilson tree opened at random;
- **carved islands:** A and B drawn among interior cells; every closed wall segment leading away from their four
  corner posts opened, so each goal's ring is free-standing; then k_r further random openings.

Seed 20 261 010, 400 mazes per setting.
"""

from __future__ import annotations

import json
import math
import sys
from collections import deque
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.e3 import maze as MZ  # noqa: E402

N_MAZES, SEED = 400, 20_261_010


def segments(c):
    return [((i, j), (k, l)) for i in range(c) for j in range(c) for (k, l) in ((i + 1, j), (i, j + 1)) if k < c and l < c]


def graph_dist(edges, c, a):
    nb = {(i, j): [] for i in range(c) for j in range(c)}
    for u, v in edges:
        nb[u].append(v)
        nb[v].append(u)
    d = {a: 0}
    q = deque([a])
    while q:
        u = q.popleft()
        for v in nb[u]:
            if v not in d:
                d[v] = d[u] + 1
                q.append(v)
    return d


def components(wall):
    lab, _ = ndimage.label(wall)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    return lab, border


def block_labels(lab, cell):
    i, j = cell
    return set(np.unique(lab[4 * i:4 * i + 5, 4 * j:4 * j + 5])) - {0}


def placements(wall, edges, c, lo):
    lab, border = components(wall)
    cells = [(i, j) for i in range(c) for j in range(c)]
    safe = [x for x in cells if not (block_labels(lab, x) & border)]
    spawnable = [x for x in cells if block_labels(lab, x) <= border]
    out = []
    for ai, a in enumerate(safe):
        da = graph_dist(edges, c, a)
        for b in safe[ai + 1:]:
            if block_labels(lab, a) & block_labels(lab, b):
                continue  # one wall component touches both goals (Astra)
            if not (lo <= da[b] <= 2 * c):
                continue
            db = graph_dist(edges, c, b)
            if any(da[s] >= 2 and db[s] >= 2 for s in spawnable):
                out.append((a, b))
    return out


def random_k(rng, c, k, lo):
    mz = MZ.generate(rng, c)
    wall, edges = mz.wall.copy(), list(mz.edges)
    open_ = {frozenset(e) for e in edges}
    closed = [s for s in segments(c) if frozenset(s) not in open_]
    for idx in rng.choice(len(closed), size=min(k, len(closed)), replace=False):
        MZ._carve(wall, *closed[idx])
        edges.append(closed[idx])
    return wall, edges, placements(wall, edges, c, lo)


def carved(rng, c, k_r, lo):
    mz = MZ.generate(rng, c)
    wall, edges = mz.wall.copy(), list(mz.edges)
    interior = [(i, j) for i in range(1, c - 1) for j in range(1, c - 1)]
    pairs = [(a, b) for x, a in enumerate(interior) for b in interior[x + 1:]
             if max(abs(a[0] - b[0]), abs(a[1] - b[1])) >= 2]  # distinct rings: no shared post
    a, b = pairs[int(rng.integers(len(pairs)))]
    open_ = {frozenset(e) for e in edges}
    for g in (a, b):  # open every closed segment that leaves one of the goal's four corner posts outward
        gi, gj = g
        for (pi, pj) in ((gi, gj), (gi, gj + 1), (gi + 1, gj), (gi + 1, gj + 1)):  # post at grid (4pi, 4pj)
            for s in segments(c):
                (u, v) = s
                if frozenset(s) in open_ or g in s:
                    continue
                # the segment's wall line touches post (pi, pj)?
                if u[0] != v[0]:  # vertical neighbours: horizontal wall row 4*(min row + 1), columns 4u1..4u1+4
                    row, col = max(u[0], v[0]), u[1]
                    touches = row == pi and col in (pj - 1, pj)
                else:
                    row, col = u[0], max(u[1], v[1])
                    touches = col == pj and row in (pi - 1, pi)
                if touches:
                    MZ._carve(wall, *s)
                    edges.append(s)
                    open_.add(frozenset(s))
    closed = [s for s in segments(c) if frozenset(s) not in open_]
    for idx in rng.choice(len(closed), size=min(k_r, len(closed)), replace=False):
        MZ._carve(wall, *closed[idx])
        edges.append(closed[idx])
        open_.add(frozenset(closed[idx]))
    ok = [p for p in placements(wall, edges, c, lo) if set(p) == {a, b}]
    # an infeasible draw: does it fail only the distance's lower bound? (no random draws consumed)
    lower_only = not ok and any(set(p) == {a, b} for p in placements(wall, edges, c, 1))
    return wall, edges, ok, lower_only


def summarise(rows, c, n_internal):
    feasible = [r for r in rows if r["placements"]]
    pos = {}
    for r in feasible:  # each feasible maze draws one placement uniformly: weight 1/len per placement
        for p in r["placements"]:
            pos[p] = pos.get(p, 0) + 1 / len(r["placements"])
    w = np.array(sorted(pos.values(), reverse=True)) / max(len(feasible), 1)
    return {"feasible_share": len(feasible) / len(rows), "distinct_placements": len(pos),
            "effective_placements": float(np.exp(-(w * np.log(w)).sum())) if len(w) else 0.0,
            "top2_share": float(w[:2].sum()) if len(w) else 0.0,
            "mean_placements_per_feasible_maze": float(np.mean([len(r["placements"]) for r in feasible])) if feasible else 0.0,
            "open_fraction_of_internal_segments": float(np.mean([r["open"] for r in rows])) / n_internal}


def main():
    rng = np.random.default_rng(SEED)
    out = []
    for c in (5, 6):
        n_internal = len(segments(c))
        for lo_name, lo in (("ceil(c/2)+1", math.ceil(c / 2) + 1), ("3", 3)):
            for kind, ks in (("random", (6, 8, 10)), ("carved", (0, 2, 4))):
                for k in ks:
                    rows = []
                    for _ in range(N_MAZES):
                        lower_only = False
                        if kind == "random":
                            wall, edges, pl = random_k(rng, c, k, lo)
                        else:
                            wall, edges, pl, lower_only = carved(rng, c, k, lo)
                        rows.append({"placements": pl, "open": len({frozenset(e) for e in edges}), "lower_only": lower_only})
                    s = summarise(rows, c, n_internal)
                    if kind == "carved":
                        s["infeasible"] = sum(not r["placements"] for r in rows)
                        s["infeasible_by_lower_bound_only"] = sum(r["lower_only"] for r in rows)
                    out.append({"c": c, "lo": lo_name, "lo_value": lo, "construction": kind, "k": k, **s})
                    print(f"c={c} lo={lo} {kind:6s} k={k:2d}: feasible {s['feasible_share']:.2f}, distinct placements "
                          f"{s['distinct_placements']:3d} (effective {s['effective_placements']:5.1f}, top 2 {s['top2_share']:.2f}), open {s['open_fraction_of_internal_segments']:.2f}", flush=True)
    path = ROOT / "docs" / "E3" / "e3d-sizing.json"
    path.write_text(json.dumps({"n_mazes": N_MAZES, "seed": SEED, "settings": out}, indent=1), encoding="utf-8", newline="\n")
    print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
