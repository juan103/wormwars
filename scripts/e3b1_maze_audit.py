"""E3b-1's maze audit (Amendment 1, D190-D191): feasibility, redraws and a bitwise equivalence reference for the
maze generator, on every maze E3b-0 and E3b-1 use.

    python scripts/e3b1_maze_audit.py --write experiments/E3-ab-organism/E3b-1/maze-reference.json   # at 171fcc5
    python scripts/e3b1_maze_audit.py --compare experiments/E3-ab-organism/E3b-1/maze-reference.json \\
        --redraws experiments/E3-ab-organism/E3b-1/maze-redraws.json                                     # after

The corpus:
- E3b-0's three blocks and E3b-1's four, at maze run seed 1 180 000;
- every registered training id set (each arm, run and generation);
- the `project` stage's ids at the projection seed 1 190 900.

Per maze it hashes the walls, the tree edges and the episode-0 placement. On the calibration and test blocks it
also hashes the replay donors' episodes and placements, and reports any donor search that exhausted. One short
CPU maze-world trace of the seed plays on mazes outside every registered block (`TRACE_IDS`).

With `--compare`, every maze that was feasible before must hash identically, and the trace must be identical
(tolerance: bitwise). The redraws, with their accepted k, are written as the predicted list the stage records
are checked against. `g-e` runs the same comparison (`compare`). CPU only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.e04a.evolve import train_ids  # noqa: E402
from wormwars.e3 import maze as M  # noqa: E402

SEED, PSEED, C, SPAWNS = 1_180_000, 1_190_900, 5, 4
TRACE_IDS = (9900, 9901, 9902)  # outside every registered block of E3b-0 and E3b-1 (D191)
ARMS = {"ta": (1_190_000, 8, 125, 16), "tf": (1_190_100, 8, 300, 8), "n": (1_190_200, 6, 125, 16),
        "r": (1_190_300, 2, 125, 16)}
PROJECT = {"ta": (8, 16), "tf": (8, 8), "n": (6, 16), "n4": (4, 16), "r": (2, 16)}  # runs, W, as `project` times them


def corpus() -> dict:
    """{set name: (run seed, [ids], donors wanted)}."""
    out = {"e3b0-selection": (SEED, range(0, 256), False), "e3b0-report": (SEED, range(1000, 1256), False),
           "e3b0-fresh": (SEED, range(2000, 2256), False), "validation": (SEED, range(4000, 4128), False),
           "learning": (SEED, range(4500, 4628), False), "calibration": (SEED, range(5000, 5256), True),
           "test": (SEED, range(6000, 6256), True)}
    for arm, (base, runs, G, W) in ARMS.items():
        ids = [int(x) for i in range(runs) for g in range(G) for x in train_ids(base + i, g, W, 10_000_000, 10_000_000)]
        out[f"train-{arm}"] = (SEED, ids, False)
    pids = list(range(9500, 9756))  # the projection's validation and evaluation ids
    for j, (key, (runs, W)) in enumerate(PROJECT.items()):
        for k in range(runs):
            for g in range(2):
                pids += [int(x) for x in train_ids(PSEED + 100 * j + k, g, W, 9_000_000, 100_000)]
    out["project"] = (PSEED, pids, False)
    return out


def walls_k(seed: int, mid: int):
    """The maze and its accepted redraw index (None before Amendment 1 for an infeasible maze)."""
    if hasattr(M, "walls_for"):
        return M.walls_for(run_seed=seed, maze_id=mid, c=C)
    mz = M.generate(np.random.default_rng([seed, mid, 0x3A11]), C)
    return mz, (0 if M.eligible_pairs(mz) else None)


def maze_hash(seed: int, mid: int, donors: bool):
    """(hash, k, donor exceptions) for one maze; (None, None, []) if infeasible before Amendment 1."""
    mz, k = walls_k(seed, mid)
    if k is None:
        return None, None, []
    h = hashlib.sha256(np.ascontiguousarray(mz.wall, dtype=np.uint8).tobytes())
    h.update(repr(sorted(mz.edges)).encode())
    _, p = M.maze_for(run_seed=seed, maze_id=mid, episode=0, c=C, n_spawns=SPAWNS)
    h.update(repr((p.a, p.b, p.spawns)).encode())
    exc = []
    if donors:
        from wormwars.e3 import maze_runs as MR
        eps, exc = MR.replay_donors(np.array([mid]), seed, C)
        _, pd = M.maze_for(run_seed=seed, maze_id=mid, episode=int(eps[0]), c=C, n_spawns=SPAWNS)
        h.update(repr((int(eps[0]), exc, pd.a, pd.b, pd.spawns)).encode())
    return h.hexdigest(), k, list(exc)


def trace() -> str:
    """A 300-tick CPU maze-world trace of the seed E + W2 on `TRACE_IDS`: positions and events, hashed."""
    import importlib.util

    import torch
    from wormwars.brain import Brain
    from wormwars.connectome import load_connectome
    from wormwars.e3 import maze_world as MW
    from wormwars.e3 import tuning as T
    from wormwars.e4s import arms as A
    s = importlib.util.spec_from_file_location("e3b1_for_audit", ROOT / "scripts" / "e3b1.py")
    run = importlib.util.module_from_spec(s)
    s.loader.exec_module(run)
    cfg = run.cfg_for("shared")
    org = T.start_organism("seed", load_connectome(), A.load_l1(), cfg.brain)
    ids = np.array(TRACE_IDS)
    w = MW.MazeWorld(cfg, org.iface, Brain(org.genome), torch.zeros(len(ids), 1, dtype=torch.long), run_seed=SEED,
                     world_ids=ids, access="shared")
    w.run(300)
    h = hashlib.sha256(w.pos.cpu().numpy().tobytes())
    for k, v in sorted(w.task_events().items()):
        h.update(k.encode())
        h.update(np.ascontiguousarray(v).tobytes())
    return h.hexdigest()


def audit(sets=None, with_trace: bool = True) -> dict:
    out_sets, redraws = {}, []
    for name, (seed, ids, donors) in corpus().items():
        if sets is not None and name not in sets:
            continue
        digest, per_id, infeasible, exceptions = hashlib.sha256(), {}, [], []
        for mid in ids:
            h, k, exc = maze_hash(seed, int(mid), donors)
            if h is None:
                infeasible.append(int(mid))
                continue
            exceptions += exc
            if k:
                redraws.append({"set": name, "seed": seed, "id": int(mid), "k": int(k)})
            digest.update(f"{mid}:{h};".encode())
            if len(ids) <= 256:
                per_id[str(mid)] = h
        out_sets[name] = {"seed": seed, "n": len(ids), "infeasible": infeasible,
                          "digest_of_feasible": digest.hexdigest(), "per_id": per_id,
                          **({"donor_exceptions": exceptions} if donors else {})}
    return {"sets": out_sets, "redraws": redraws, "trace_ids": list(TRACE_IDS),
            "trace_sha256": trace() if with_trace else None}


def compare(ref: dict, sets=None, with_trace: bool = True) -> dict:
    """The current generator against `ref`: every maze feasible in `ref` hashes identically, the trace is
    identical, and no infeasible maze is left."""
    new = audit(sets, with_trace)
    diffs = []
    for name, r in ref["sets"].items():
        if sets is not None and name not in sets:
            continue
        for mid, h in r["per_id"].items():
            if new["sets"][name]["per_id"].get(mid) != h:
                diffs.append([name, mid])
        seed, ids, donors = corpus()[name]
        d = hashlib.sha256()
        for mid in ids:
            if int(mid) in r["infeasible"]:
                continue
            h, _, _ = maze_hash(seed, int(mid), donors)
            d.update(f"{mid}:{h};".encode())
        if d.hexdigest() != r["digest_of_feasible"]:
            diffs.append([name, "digest"])
    same_trace = (not with_trace) or new["trace_sha256"] == ref["trace_sha256"]
    left = {k: v["infeasible"] for k, v in new["sets"].items() if v["infeasible"]}
    exhausted = {k: v["donor_exceptions"] for k, v in new["sets"].items() if v.get("donor_exceptions")}
    return {"identical_feasible": not diffs, "differences": diffs[:20], "trace_identical": same_trace,
            "trace_ids": list(TRACE_IDS), "infeasible_after": left, "donor_exceptions": exhausted,
            "redraws": new["redraws"], "passed": not diffs and same_trace and not left and not exhausted}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write")
    ap.add_argument("--compare")
    ap.add_argument("--redraws")
    a = ap.parse_args()
    if a.write:
        out = audit()
        Path(a.write).write_text(json.dumps({"note": "the maze generator before Amendment 1 (171fcc5)", **out},
                                            indent=1, sort_keys=True), encoding="utf-8", newline="\n")
        print({k: v["infeasible"][:5] for k, v in out["sets"].items() if v["infeasible"]})
    if a.compare:
        result = compare(json.loads(Path(a.compare).read_text(encoding="utf-8")))
        if a.redraws:
            Path(a.redraws).write_text(json.dumps(result, indent=1), encoding="utf-8", newline="\n")
        print({k: v for k, v in result.items() if k != "redraws"}, len(result["redraws"]), "redraws")
        if not result["passed"]:
            raise SystemExit("the maze audit failed")


if __name__ == "__main__":
    main()
