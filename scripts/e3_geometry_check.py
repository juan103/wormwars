"""E3a's source geometry, checked against the real one-wey spawn (docs/E3/DESIGN.md, v2.1).

    python scripts/e3_geometry_check.py     # writes docs/E3/geometry-check.json (CPU, seconds)

The spawn follows `World` (world.py, the spawn block): a point at radius (W/2 - spawn_margin) * 0.82
from the centre at a uniform angle, plus a uniform jitter of +-spawn_spread * W / 2 on each axis.
Sources A and B are drawn uniformly in the centre box [1 + clearance, W - 1 - clearance]^2, as Task N's
targets are, and accepted when the rule below holds. For each sampled spawn, the acceptance rate of the
rule is estimated; the design needs every spawn's rate well above 1 / 10 000 (the rejection limit).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "E3" / "geometry-check.json"

W = 24.0
SPAWN_MARGIN, SPAWN_SPREAD = 3.0, 0.28   # config.py MapConfig defaults
CLEARANCE = 3.0                          # Task N's wall clearance: the box 4..20
SIGMA = 6.0
REACH = math.ceil(3 * SIGMA)             # target_field's support along either axis
RULE = {"ab_min": 8.0, "ab_max": 14.0, "spawn_min": 6.0, "spawn_axis_max_A": 16.0}


def spawns(rng, n):
    r = (W / 2 - SPAWN_MARGIN) * 0.82
    half = SPAWN_SPREAD * W / 2
    ang = rng.uniform(0, 2 * np.pi, n)
    x = W / 2 + np.cos(ang) * r + rng.uniform(-half, half, n)
    y = W / 2 + np.sin(ang) * r + rng.uniform(-half, half, n)
    return np.stack([x, y], 1)


def accept(s, a, b, rule):
    dab = np.hypot(*(a - b).T)
    da = np.hypot(*(a - s).T)
    db = np.hypot(*(b - s).T)
    axis_a = np.abs(a - s).max(1)
    return ((dab >= rule["ab_min"]) & (dab <= rule["ab_max"]) & (da >= rule["spawn_min"])
            & (db >= rule["spawn_min"]) & (axis_a <= rule["spawn_axis_max_A"]))


def check(rule, n_spawn=2000, n_draw=20000, seed=0):
    rng = np.random.default_rng(seed)
    lo, hi = 1 + CLEARANCE, W - 1 - CLEARANCE
    S = spawns(rng, n_spawn)
    rates = np.empty(n_spawn)
    acc_n = blind = beyond16 = 0
    for i, s in enumerate(S):
        a = rng.uniform(lo, hi, (n_draw, 2))
        b = rng.uniform(lo, hi, (n_draw, 2))
        ok = accept(s, a, b, rule)
        rates[i] = ok.mean()
        axis_a = np.abs(a - s).max(1)[ok]
        acc_n += int(ok.sum())
        blind += int((axis_a > REACH).sum())
        beyond16 += int((axis_a > 16).sum())
    axis_far = np.abs(np.stack([np.array([lo, lo]), np.array([hi, hi])])[None] - S[:, None]).max((1, 2))
    return {"rule": rule, "spawns": n_spawn, "draws_per_spawn": n_draw, "seed": seed,
            "acceptance_min": float(rates.min()), "acceptance_median": float(np.median(rates)),
            "spawns_with_zero_acceptance": int((rates == 0).sum()),
            "accepted_draws": acc_n, "accepted_with_A_beyond_field_reach": blind,
            "accepted_with_A_axis_beyond_16": beyond16,
            "max_axis_distance_spawn_to_box": float(axis_far.max()), "field_reach": REACH,
            "spawn_extent": [float(S.min()), float(S.max())]}


def main():
    doc = {"with_rule": check(RULE),
           "without_axis_limit": check({**RULE, "spawn_axis_max_A": 1e9})}
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, indent=1))


if __name__ == "__main__":
    main()
