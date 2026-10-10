"""E3d's gate, the choice of k_r, the champions' predictions and the bootstrap (docs/E3/E3d-DESIGN.md v2.2 §4-5).

A block summary is {"conditions": {name: {"role": "blind" | "navigator" | "organism", "strains": [{"visits":
[per maze], "legs": [per maze], "visited_share": [per maze]}, ...]}}}: per maze, a colony's mean visits per wey,
its mean legs, and the share of its weys with a visit, mazes paired across conditions. The gate reads
"follower_shared", "oracle" and "seed"; every member of a "blind" condition (one per strain, named
"name#strain" when the condition has several) enters B_max.

| | criterion |
|---|---|
| G1a | B_max ≤ 0.25 × the shared follower |
| G1b | B_max ≤ 2.0 mean visits per wey |
| G2a | the shared follower ≥ ⅓ of the oracle |
| G2b | the shared follower ≥ 4.0 |
| G3a | the seed − B_max ≥ max(0.5, 0.10 × the seed) |
| G3b | the seed's median over mazes of the colony-mean legs ≥ 2 |

The precondition: the oracle ≥ the shared follower, and ≥ 95% of the oracle's weys make a visit.
"""

from __future__ import annotations

import numpy as np

THRESHOLDS = {"g1a": 0.25, "g1b": 2.0, "g2a": 1 / 3, "g2b": 4.0, "g3_abs": 0.5, "g3_rel": 0.10, "g3b": 2.0,
              "oracle_visit_share": 0.95}
CRITERIA = ("G1a", "G1b", "G2a", "G2b", "G3a", "G3b")
S_ARMS, P_ARM = ("s_mod", "s_dense"), "p_joint"


def _per_maze(block, name, key="visits", strain=0) -> np.ndarray:
    return np.asarray(block["conditions"][name]["strains"][strain][key], dtype=np.float64)


def blind_members(block) -> dict:
    """{member: per-maze visits} for every strain of every blind condition."""
    out = {}
    for name, c in block["conditions"].items():
        if c.get("role") != "blind":
            continue
        for s, st in enumerate(c["strains"]):
            out[name if len(c["strains"]) == 1 else f"{name}#{s}"] = np.asarray(st["visits"], dtype=np.float64)
    return out


def quantities(block, idx=None) -> dict:
    """The gate's quantities, on the mazes `idx` (all of them by default; a bootstrap resample otherwise)."""
    pick = (lambda x: x) if idx is None else (lambda x: x[idx])
    members = {k: float(pick(v).mean()) for k, v in blind_members(block).items()}
    arg = max(members, key=lambda k: (members[k], k)) if members else None
    return {"follower": float(pick(_per_maze(block, "follower_shared")).mean()),
            "oracle": float(pick(_per_maze(block, "oracle")).mean()),
            "oracle_visited_share": float(pick(_per_maze(block, "oracle", "visited_share")).mean()),
            "seed": float(pick(_per_maze(block, "seed")).mean()),
            "seed_median_legs": float(np.median(pick(_per_maze(block, "seed", "legs")))),
            "b_max": members[arg] if arg else 0.0, "b_max_member": arg, "blind_means": members}


def gate(block, th=THRESHOLDS) -> dict:
    q = quantities(block)
    F, O, S, B = q["follower"], q["oracle"], q["seed"], q["b_max"]
    crit = {"G1a": B <= th["g1a"] * F, "G1b": B <= th["g1b"], "G2a": F >= th["g2a"] * O, "G2b": F >= th["g2b"],
            "G3a": S - B >= max(th["g3_abs"], th["g3_rel"] * S), "G3b": q["seed_median_legs"] >= th["g3b"]}
    pre = O >= F and q["oracle_visited_share"] >= th["oracle_visit_share"]
    failed = [k for k in CRITERIA if not crit[k]]
    verdict = "E3d: not evaluable" if not pre else ("E3d: passed" if not failed else "E3d: failed")
    return {**q, "criteria": crit, "failed": failed, "precondition": bool(pre), "verdict": verdict}


def choose_k(gates: dict, feasible: dict, floor: float) -> dict:
    """The smallest k_r whose gate passes with the precondition met and whose first-draw feasible share is at
    least `floor`; otherwise "failed at calibration", with each k_r's failures."""
    failures = {}
    for k in sorted(gates):
        g = gates[k]
        why = list(g["failed"]) + ([] if g["precondition"] else ["precondition"]) + \
            ([] if feasible[k] >= floor else ["feasible share"])
        if not why:
            return {"k_r": k, "verdict": "chosen", "failures": failures}
        failures[k] = why
    return {"k_r": None, "verdict": "E3d: failed at calibration", "failures": failures}


def _arm_means(block, arm) -> np.ndarray:
    c = block["conditions"][f"{arm}_intact"]
    return np.array([np.mean(st["visits"]) for st in c["strains"]])


def predictions(islands, tree) -> dict:
    """§5's descriptive predictions: each S arm's mean intact visits on the islands at most 0.5 × its mean on
    the tree reference; P-joint's at least 0.5 ×. Per-champion ratios beside."""
    out = {}
    for arm in (*S_ARMS, P_ARM):
        if f"{arm}_intact" not in islands["conditions"] or f"{arm}_intact" not in tree["conditions"]:
            out[arm] = {"unavailable": True}
            continue
        i, t = _arm_means(islands, arm), _arm_means(tree, arm)
        ratio = float(i.mean() / t.mean()) if t.mean() > 0 else None  # reported; the inequality decides
        holds = i.mean() <= 0.5 * t.mean() if arm in S_ARMS else i.mean() >= 0.5 * t.mean()
        out[arm] = {"islands": float(i.mean()), "tree": float(t.mean()), "ratio": ratio, "holds": bool(holds),
                    "per_champion": [float(a / b) if b > 0 else None for a, b in zip(i, t)]}
    return out


def bootstrap(block, resamples: int, seed: int) -> dict:
    """95% intervals over resamples of the paired mazes, B_max recomputed as the maximum in each resample."""
    n = len(_per_maze(block, "follower_shared"))
    idx = np.random.default_rng(seed).integers(0, n, size=(resamples, n))
    keys = ("b_max", "follower", "oracle", "seed", "b_max_over_follower", "follower_over_oracle", "seed_minus_b_max",
            "seed_median_legs", "oracle_visited_share")

    def derived(q):
        return {"b_max": q["b_max"], "follower": q["follower"], "oracle": q["oracle"], "seed": q["seed"],
                "b_max_over_follower": q["b_max"] / q["follower"] if q["follower"] else float("nan"),
                "follower_over_oracle": q["follower"] / q["oracle"] if q["oracle"] else float("nan"),
                "seed_minus_b_max": q["seed"] - q["b_max"], "seed_median_legs": q["seed_median_legs"],
                "oracle_visited_share": q["oracle_visited_share"]}

    point = derived(quantities(block))
    draws = {k: [] for k in keys}
    for r in range(resamples):
        d = derived(quantities(block, idx[r]))
        for k in keys:
            draws[k].append(d[k])
    return {k: {"point": point[k], "interval": [float(np.nanquantile(draws[k], 0.025)),
                                                float(np.nanquantile(draws[k], 0.975))]} for k in keys}
