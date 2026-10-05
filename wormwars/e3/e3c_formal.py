"""E3c's formal plan (its pre-registration, bound at 69d7cd5: §3-§6, §10, §12): the runs and the cuts, the
compositions, the checkpoint schedule, the blocks, the champion and W2-turn rules, P-joint's candidates by
logged hash, the projection and admission rule, and the engine freeze. Pure functions; the stages that use them
are in `scripts/e3c.py`."""

from __future__ import annotations

import numpy as np

BINDING_COMMIT = "69d7cd5"
RUN_SEED_BASE = 1_300_000
ARM_RUNS = {"s_mod": range(0, 8), "s_dense": range(10, 18), "p_sel": range(20, 24)}
G, W = 300, 8
BLOCKS = {"validation": (10_000, 10_128), "learning": (10_200, 10_328), "test": (10_400, 10_656),
          "benchmark": (10_700, 10_956)}
TRAIN = {"base": 40_000_000, "span": 10_000_000}
BENCH_TRAIN = {"base": 50_000_000, "span": 100_000}
TURN_GRID = [-0.8, -0.4, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4]
PLAN_FULL = {"trails_off": True, "p_sel_runs": 4, "s_runs": 8}
TRAIN_MARGIN = 1.25
GE_HOURS = 0.15  # E3b-1's g-e took 0.066 h (its record); a registered allowance in the projection
P_JOINT_RUNS = 8
ENGINE_PATHS = ("wormwars/", "configs/", "requirements.txt")


def plan_after_cuts(k: int) -> dict:
    """§10's cuts, in order: 1 trails off; 2 P-sel to runs 20-21; 3 the S arms to runs 0-5 and 10-15."""
    return {"trails_off": k < 1, "p_sel_runs": 4 if k < 2 else 2, "s_runs": 8 if k < 3 else 6}


def runs(plan: dict) -> dict:
    n = {"s_mod": plan["s_runs"], "s_dense": plan["s_runs"], "p_sel": plan["p_sel_runs"]}
    return {arm: [{"arm": arm, "run": r, "seed": RUN_SEED_BASE + r} for r in list(ARM_RUNS[arm])[:n[arm]]]
            for arm in ARM_RUNS}


def training_composition(arm: str, plan: dict, population: int = 32) -> list:
    return [len(runs(plan)[arm]) * population, W, 8]


def checkpoint_generations() -> list:
    return list(range(0, 51, 5)) + list(range(75, 276, 25)) + [G - 1]


def champion_index(means) -> int:
    """The best mean, ties to the lower index."""
    return int(np.argmax(np.asarray(means, dtype=np.float64)))


def choose_turn(grid, means) -> float:
    """The best mean visits, ties to the smaller |turn|, then to the earlier grid position."""
    order = sorted(range(len(grid)), key=lambda i: (-float(means[i]), abs(grid[i]), i))
    return grid[order[0]]


def index_of_hash(hashes, sha: str) -> int:
    for i, h in enumerate(hashes):
        if h == sha:
            return i
    raise ValueError(f"no genome with hash {sha[:12]} in the population")


def projection_hours(t: dict, plan: dict) -> float:
    """The formal total from `project`'s timings (seconds): training with × 1.25, the checkpoints, the champions,
    the evaluation and `g-e`'s allowance."""
    cut_s, cut_p = plan["s_runs"] < 8, plan["p_sel_runs"] < 4
    n_s, n_p = plan["s_runs"], plan["p_sel_runs"]
    train = TRAIN_MARGIN * G * (2 * t["train_s_cut" if cut_s else "train_s"] + t["train_psel_cut" if cut_p else "train_psel"])
    ck = len(checkpoint_generations()) + 2  # the 21 post-hoc plays and evolve_batch's two in-loop ones (Astra)
    checkpoints = ck * (2 * t["checkpoint_6" if cut_s else "checkpoint_8"] + t["checkpoint_2" if cut_p else "checkpoint_4"])
    n_runs = 2 * n_s + n_p + P_JOINT_RUNS
    champions = (n_runs + 1) * t["champion_chunk"] + 2 * t["checkpoint_8"] + 2 * t["eval_single"]
    arms = 4
    evaluation = 2 * arms * t["eval_chunk"] + 5 * t["eval_single"]
    if plan["trails_off"]:
        evaluation += arms * t["eval_chunk"] + 2 * t["eval_single"]
    return (train + checkpoints + champions + evaluation) / 3600 + GE_HOURS


def admit(t: dict, remaining_hours: float) -> dict:
    """§10: the cuts apply in order until the projection fits; if none fits, E3c does not start."""
    for k in range(4):
        h = projection_hours(t, plan_after_cuts(k))
        if h <= remaining_hours:
            return {"admitted": True, "cuts": k, "plan": plan_after_cuts(k), "projected_hours": h,
                    "remaining_hours": remaining_hours}
    return {"admitted": False, "cuts": 3, "plan": plan_after_cuts(3), "projected_hours": h,
            "remaining_hours": remaining_hours}


def engine_freeze(diff: list, amended: set | None = None) -> dict:
    """§12: the diff from the binding commit (git name-status entries) may add files under the engine paths but
    change none, unless an amendment names it."""
    amended = amended or set()
    changed = [[st, path] for st, path in diff
               if any(path == p or path.startswith(p) for p in ENGINE_PATHS) and not st.startswith("A")
               and path not in amended]
    return {"changed": changed, "passes": not changed}
