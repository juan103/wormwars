"""E3d: a maze that wall-following cannot solve (docs/E3/E3d-DESIGN.md v2.2, bound at 65b77fb; Amendment 1;
D221-D226). Exploratory: it validates a task and trains nothing.

    python scripts/e3d.py project --device cuda      # the cost of the plan, and the reductions if needed
    python scripts/e3d.py g-e --device cuda          # rule 7: E3c's legs and the full-rollout leg
    python scripts/e3d.py calibrate --device cuda    # k_r = 0, 2, 4 on ids 30 000-30 127; the smallest qualifying
    python scripts/e3d.py confirm --device cuda      # the chosen k_r on ids 30 200-30 455; the 6 × 6 tree reference
    python scripts/e3d.py report                     # the gate, the verdict, the predictions, the bootstrap
    add --smoke for toy sizes in runs/e3d-smoke (never results)

The stages write their records to `experiments/E3-ab-organism/E3d/` and are run once each (E2's frame). The
formal stages refuse unless the design (with its amendments) is the bound text and the engine is unchanged since
the binding commit. The ceiling is 3 GPU-hours (`runs/e3d/compute`).
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import graft as G  # noqa: E402
from wormwars.brain import Brain, BrainSpec  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e3 import assembly as AS  # noqa: E402
from wormwars.e3 import attribution as AT  # noqa: E402
from wormwars.e3 import e3d_controls as DC  # noqa: E402
from wormwars.e3 import e3d_gate as GT  # noqa: E402
from wormwars.e3 import e3d_records as RC  # noqa: E402
from wormwars.e3 import islands as IS  # noqa: E402
from wormwars.e3 import maze as MZ  # noqa: E402
from wormwars.e3 import maze_controls as MC  # noqa: E402
from wormwars.e3 import maze_organisms as MO  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e3 import organism as O  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.e4s import comparator as C  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


E = _load("e2_for_e3d", "e2.py")  # E2's stage frame, configured for E3d's own folders
X = _load("e3c_for_e3d", "e3c.py")  # E3c's organisms, references and champions (read only)

EXP = ROOT / "experiments" / "E3-ab-organism" / "E3d"
REFERENCES = EXP  # the committed full-rollout references, read from here in smoke runs too
OUT = ROOT / "runs" / "e3d"
DESIGN = "docs/E3/E3d-DESIGN.md"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", DESIGN]
SMOKE = False
STAGES = ["project", "g-e", "calibrate", "confirm", "report"]
TIMING_TICKS, TIMING_MAZES = 200, 128  # the projection times the formal compositions over 200 ticks
REQUIRES = {"project": [], "g-e": ["project"], "calibrate": ["project", "g-e"], "confirm": ["project", "g-e", "calibrate"],
            "report": ["project", "calibrate"]}

REGISTERED = {
    "design": DESIGN,  # §8: the design with Amendment 1, bound at the code commit (D226); the engine frozen there
    "binding_commit": "202666e91c1b0bf1c78e96831e7e3fdd92c9a84a",
    "design_sha256": "37ee0c39868f074446cca43fd0242ce8bf72e9f90127fdafbade60394e4b4147",
    "maze_seed": 1_190_000, "c": 6, "H": 2400, "colony": 8, "spawns": 4,
    "trail": {"mu": 0.01, "lam": 0.02, "delta": 0.05, "d0": 1.142},
    "k_r": [0, 2, 4], "feasible_floor": 0.5,
    "blocks": {"calibration": [30_000, 30_128], "confirmation": [30_200, 30_456], "tree_reference": [30_200, 30_328],
               "tangent": [30_200, 30_264]},  # §3's tangent-start diagnostic: the confirmation's first 64 mazes
    "turn_grid": [-0.8, -0.4, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 1.95],
    "walk_grid": {"persistence": [0.25, 0.5, 0.8], "rate": [0.5, 1.0, 2.0], "speed": 1.0, "seed": 0},
    "reductions": [{"walk_grid": {"persistence": [0.5], "rate": [0.5, 1.0, 2.0], "speed": 1.0, "seed": 0}},
                   {"turn_grid": [-0.8, 0.0, 0.4, 0.8, 1.2, 1.4, 1.95]},
                   {"blocks.tree_reference": [30_200, 30_264]}],
    "thresholds": dict(GT.THRESHOLDS),
    "bootstrap": {"resamples": 2000, "seed": 20_261_011},
    "e3c_champions": {"record": "experiments/E3-ab-organism/E3c/champions.json",
                      "sha256": "52c3c92ad1f0ef25596a900ead835e4bee3c3673618d6dfd86b8a6214ebfafe3"},
    "arms": ["s_mod", "s_dense", "p_sel", "p_joint"],
    "cap_gpu_hours": 3.0,
    "ge_allowance_hours": 0.25,  # g-e runs after project; its cost is reserved in the admission (both reviewers)
}


def configure() -> None:
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, OUT, GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E3d: not completed (the run stopped)",
                  "cap": "E3d: not completed (the cap was reached)"}
    E.RECORD.update({s: s for s in STAGES})
    E.WHAT.update({s: f"E3d's {s}" for s in STAGES})
    E.task_config = lambda: cfg_for("islands", 0, "shared")


def cfg_for(family: str, k_r: int, access: str):
    R = REGISTERED
    return MW.maze_config(X.base_config(), c=R["c"], horizon=R["H"], colony=R["colony"], access=access,
                          spawns=R["spawns"], family=family, k_r=k_r if family == "islands" else 0, **R["trail"])


configure()


# ------------------------------------------------------------------------------------------- the binding (§8)

def design_sha256() -> str:
    return hashlib.sha256((ROOT / DESIGN).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def engine_changes() -> list:
    out = E.reg.git("diff", "--name-status", REGISTERED["binding_commit"], "HEAD", "--", "wormwars", "configs",
                    "requirements.txt", root=ROOT)
    return [line for line in out.splitlines() if line.strip()]


BINDING_VALUE = re.compile(r'("(?:binding_commit|design_sha256)": )"[^"]*"')


def _normalise(text: str) -> str:
    """The runner's text with only the two binding values blanked (Astra: whole lines must not be exempt)."""
    return BINDING_VALUE.sub(r'"<bound>"', text)


def script_changes() -> list:
    """The scripts changed since the binding commit, beyond this runner's two binding lines (both reviewers):
    any other script, or any other line of this one."""
    b = REGISTERED["binding_commit"]
    names = [n for n in E.reg.git("diff", "--name-only", b, "HEAD", "--", "scripts", root=ROOT).splitlines() if n.strip()]
    bad = [n for n in names if n != "scripts/e3d.py"]
    if "scripts/e3d.py" in names:
        if _normalise(E.reg.git("show", f"{b}:scripts/e3d.py", root=ROOT)) != _normalise(E.reg.git("show", "HEAD:scripts/e3d.py", root=ROOT)):
            bad.append("scripts/e3d.py")
    return bad


def require_bound(args) -> None:
    """The formal stages run only on the bound design, the engine of the binding commit and its scripts."""
    if not E.formal(args):
        return
    if not REGISTERED["binding_commit"] or not REGISTERED["design_sha256"]:
        raise SystemExit("E3d's design is not bound in this runner (§8): refusing")
    if design_sha256() != REGISTERED["design_sha256"]:
        raise SystemExit("the design differs from the bound text (with its amendments): refusing")
    ch = engine_changes()
    if ch:
        raise SystemExit(f"the engine changed since the binding commit: {ch[:5]}")
    sc = script_changes()
    if sc:
        raise SystemExit(f"scripts changed since the binding commit: {sc[:5]}")


def check_champions_record() -> dict:
    rel = REGISTERED["e3c_champions"]["record"]
    h = hashlib.sha256((ROOT / rel).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if not SMOKE and h != REGISTERED["e3c_champions"]["sha256"]:
        raise SystemExit(f"{rel} has changed (sha256 {h}): refusing")
    return {rel: h}


def requires(stage: str):
    def req(args, prov):
        require_bound(args)
        got = {s: E.require_earlier(args, prov, s) for s in REQUIRES[stage]}
        if stage == "report" and E.record_path("confirm").exists():
            got["confirm"] = E.require_earlier(args, prov, "confirm")
        if "project" in got and not got["project"]["admitted"]:
            raise SystemExit("the projection exceeds 3 GPU-hours after every reduction: nothing is played (§7)")
        if "g-e" in got and not got["g-e"].get("passed"):
            raise SystemExit("g-e did not pass: nothing is played, and the owner is asked")
        if stage == "confirm" and got["calibrate"]["choice"]["k_r"] is None and not SMOKE:
            raise SystemExit("calibration chose no k_r ('E3d: failed at calibration'): nothing to confirm (§4)")
        return got
    return req


# ------------------------------------------------------------------------------------------- the conditions (§3)

def ids_of(block: str) -> np.ndarray:
    return np.arange(*REGISTERED["blocks"][block])


def w2_turn(con, bcfg, r: float):
    """E3c's W2-turn reference at resting turn r; |r| < 2 is the bound (`carrier_turn`'s atanh(r/2))."""
    if not abs(r) < 2:
        raise ValueError(f"the resting turn {r} is outside |r| < 2")
    return X.w2_turn(con, bcfg, r)


def carrier_variant(con, bcfg, variant: str):
    """The carrier with E3b-0's variant (W2+M40, W2+M80), built as E3c builds W2 alone."""
    carrier = O.carrier_only()
    ext = G.graft_connectome(con, carrier)
    sd = MO.Seed("carrier", carrier, ext, C.carrier_genome(ext, carrier, bcfg, forward=1.0, turn=0.2))
    return MO.maze_organism(con, sd, variant, bcfg)


def specs(block: str, champions: dict) -> list:
    """Every condition of a block (§3's table and "who plays where"), in play order."""
    R = REGISTERED
    out = [{"name": "wall_left", "role": "blind", "kind": "wall", "hand": "left"},
           {"name": "wall_right", "role": "blind", "kind": "wall", "hand": "right"},
           {"name": "w2", "role": "blind", "kind": "w2"}]
    out += [{"name": f"w2_turn_{r:g}", "role": "blind", "kind": "w2_turn", "r": r} for r in R["turn_grid"]]
    out += [{"name": f"w2_{v[3:].lower()}", "role": "blind", "kind": "carrier", "variant": v} for v in ("W2+M40", "W2+M80")]
    wg = R["walk_grid"]
    out += [{"name": f"walk_p{p:g}_r{q:g}", "role": "blind", "kind": "walk", "persistence": p, "rate": q}
            for p in wg["persistence"] for q in wg["rate"]]
    out += [{"name": "seed_noses", "role": "blind", "kind": "seed", "noses": False}]
    out += [{"name": f"{a}_noses", "role": "blind", "kind": "arm", "arm": a, "noses": False} for a in champions]
    out += [{"name": "oracle", "role": "navigator", "kind": "oracle"},
            {"name": "follower_shared", "role": "navigator", "kind": "follower", "access": "shared"},
            {"name": "follower_none", "role": "navigator", "kind": "follower", "access": "none"},
            {"name": "seed", "role": "organism", "kind": "seed", "noses": True}]
    if block != "calibration":
        out += [{"name": f"{a}_intact", "role": "organism", "kind": "arm", "arm": a, "noses": True} for a in champions]
    return out


def build(spec: dict, cfg, con, l1, cx, champions: dict, dev):
    """(iface, brain, n_strains, access) for a condition."""
    access = spec.get("access", "shared")
    k = spec["kind"]
    plain = load_interface(con)
    if k == "wall":
        return plain, DC.wall_follower(plain, cfg, spec["hand"], device=dev), 1, access
    if k == "walk":
        wg = REGISTERED["walk_grid"]
        pol = MC.ReflexWalk(speed=wg["speed"], rate=spec["rate"], persistence=spec["persistence"], seed=wg["seed"])
        return plain, MC.WorldScripted(plain, cfg, pol, device=dev), 1, access
    if k == "oracle":
        return plain, MC.oracle(plain, cfg, device=dev), 1, access
    if k == "follower":
        return plain, MC.follower(plain, cfg, device=dev), 1, access
    if k in ("w2", "w2_turn", "carrier", "seed"):
        org = {"w2": lambda: X.w2_alone(con, cfg.brain), "w2_turn": lambda: w2_turn(con, cfg.brain, spec["r"]),
               "carrier": lambda: carrier_variant(con, cfg.brain, spec["variant"]), "seed": lambda: cx["seed"]}[k]()
        iface = org.iface if spec.get("noses", True) else AT.without_scent(org.iface)
        return iface, MO.brain(org, dev), 1, access
    if k == "arm":
        org = X._org(spec["arm"], cx)
        g = X.load_champions(spec["arm"], champions[spec["arm"]], BrainSpec.from_connectome(org.ext), cfg.brain)
        iface = org.iface if spec["noses"] else AT.without_scent(org.iface)
        return iface, Brain(X._on(g, dev)), g.n_strains, access
    raise ValueError(f"unknown condition kind {k}")


def available_champions() -> dict:
    """E3c's champions (the record's runs), if every genome file is present (they stay local)."""
    rec = json.loads((ROOT / REGISTERED["e3c_champions"]["record"]).read_text(encoding="utf-8"))
    out = {}
    for arm in REGISTERED["arms"]:
        runs_ = (rec.get("arms") or {}).get(arm, {}).get("runs", [])
        if runs_ and all(X.champion_file(arm, r["run"]).exists() for r in runs_):
            out[arm] = runs_
    if not SMOKE and set(out) != set(REGISTERED["arms"]):
        raise SystemExit(f"E3c's champion genomes are missing for {sorted(set(REGISTERED['arms']) - set(out))}")
    return out


# ------------------------------------------------------------------------------------------- playing and recording

class PathRecorder:
    """Each wey's head after every tick (the world calls `record` after the tick count advances), index t the
    position after tick t, the tick a visit is stamped with."""

    def __init__(self, n_worlds: int, n_weys: int, ticks: int):
        self.paths = np.zeros((n_worlds, n_weys, ticks, 2), dtype=np.float32)
        self.t = 0

    def record(self, world) -> None:
        self.paths[:, :, self.t] = world.pos[:, 0].detach().to("cpu", torch.float32).numpy()
        self.t += 1


def maze_info(family: str, k_r: int, ids) -> dict:
    """Per maze: the placement, the redraw index, the goals' entrances, the spawn candidates, the scent-reach
    flags and the maze-ness measures; and the contact tables, kept in memory for every condition."""
    R = REGISTERED
    rows, tables = [], {}
    for mid in ids:
        mid = int(mid)
        if family == "islands":
            mz, pl, im = IS.maze_for(run_seed=R["maze_seed"], maze_id=mid, episode=0, c=R["c"], k_r=k_r, n_spawns=R["spawns"])
            k, n_cand = im.k, len(IS.spawn_candidates(mz, pl.a, pl.b))
        else:
            mz, pl = MZ.maze_for(run_seed=R["maze_seed"], maze_id=mid, episode=0, c=R["c"], n_spawns=R["spawns"])
            d = mz.tree_distance()  # E3b-1's spawn candidates: dead ends 2 or more cells from both goals
            n_cand = sum(1 for s_ in mz.dead_ends() if s_ not in (pl.a, pl.b) and d[s_][pl.a] >= 2 and d[s_][pl.b] >= 2)
            k = MZ.walls_for(run_seed=R["maze_seed"], maze_id=mid, c=R["c"])[1]
        m = RC.maze_measures(mz, pl)
        rows.append({"id": mid, "redraw": int(k), "a": list(pl.a), "b": list(pl.b), "spawns": [list(s) for s in pl.spawns],
                     "spawn_candidates": n_cand, "scent_reach": [RC.scent_reach(mz, pl.a), RC.scent_reach(mz, pl.b)],
                     **{kk: (list(v) if isinstance(v, tuple) else v) for kk, v in m.items()}})
        tables[mid] = RC.contact_tables(mz.wall, pl.a, pl.b)
    return {"mazes": rows, "first_draw_feasible_share": float(np.mean([r["redraw"] == 0 for r in rows])),
            "_tables": tables}


CLASS_CODE = {"none": 0, **{k: i + 1 for i, k in enumerate(RC.CLASSES)}}


def summarise(ev, paths, mazes, placements, ids, S: int, tables: dict, H: int, c: int) -> tuple[list, dict]:
    """Per strain, per maze: throughput, discovery, coverage, occupancy and contact (§6); and the arrays kept
    per wey and per visit (Astra): the head cell each tick, the visit ledger, raw entries, the first component
    acquired, and each visit's remembered and outside classes."""
    n = len(ids)
    vt = ev["visit_tick"]
    th = RC.throughput(vt, H)
    ent = np.stack([RC.entries(paths[w], placements[w].a, placements[w].b) for w in range(S * n)])
    disc = RC.discovery(ent, H)
    cov = np.stack([RC.coverage(paths[w], c) for w in range(S * n)]).mean(-1)
    occ = np.stack([RC.occupancy(paths[w], placements[w].a, placements[w].b) for w in range(S * n)]).mean(-1)
    con = {"share": {k: [] for k in RC.CLASSES}, "switches": [], "first_class": [], "switches_by_pair": [], "at_visit": [],
           "first_label": []}
    step = 256
    for lo in range(0, S * n, step):
        sl = range(lo, min(lo + step, S * n))
        got = RC.contact_batch(paths[lo:lo + step], [mazes[w].wall for w in sl],
                               [(placements[w].a, placements[w].b) for w in sl], vt[lo:lo + step],
                               tables=[tables[int(ids[w % n])] for w in sl])
        for k in RC.CLASSES:
            con["share"][k].append(got["share"][k])
        con["switches"].append(got["switches"])
        con["first_label"].append(got["first_label"])
        for key in ("first_class", "switches_by_pair", "at_visit"):
            con[key] += got[key]
    share = {k: np.concatenate(v) for k, v in con["share"].items()}
    switches = np.concatenate(con["switches"])
    r6 = lambda x: np.round(np.asarray(x, dtype=np.float64), 6).tolist()  # noqa: E731
    nan = lambda x: [None if (v != v) else v for v in r6(x)]  # noqa: E731
    out = []
    for s in range(S):
        sl = slice(s * n, (s + 1) * n)
        fc, pairs, at = {}, {}, {}
        for w in range(s * n, (s + 1) * n):
            for x in con["first_class"][w]:
                fc[x] = fc.get(x, 0) + 1
            for x in con["switches_by_pair"][w]:
                for (a, b), v in x.items():
                    pairs[f"{a}->{b}"] = pairs.get(f"{a}->{b}", 0) + v
            for recs in con["at_visit"][w]:
                for (now, before) in recs:
                    at[f"{now}|{before}"] = at.get(f"{now}|{before}", 0) + 1
        out.append({"visits": r6(th["visits"][sl].mean(-1)), "legs": r6(th["legs"][sl].mean(-1)),
                    "visited_share": r6((th["visits"][sl] > 0).mean(-1)), "round_trip_share": r6(th["round_trip"][sl].mean(-1)),
                    "later_leg_rate": r6(th["later_leg_rate"][sl]), "no_first_visit_share": r6(th["no_first_visit_share"][sl]),
                    "arrived_a": r6(disc["arrived_a"][sl]), "arrived_b": r6(disc["arrived_b"][sl]),
                    "first_entry_median_a": nan(disc["censored_median_a"][sl]),
                    "first_entry_median_b": nan(disc["censored_median_b"][sl]),
                    "coverage": r6(cov[sl]), "occupancy": r6(occ[sl]),
                    **{f"contact_{k}": r6(share[k][sl].mean(-1)) for k in RC.CLASSES},
                    "switch_rate": r6(switches[sl].mean(-1) / H * 1000.0),
                    "first_class": fc, "switches_by_pair": pairs, "at_visit": at})
    visits_rows = [(w, b, v, int(vt[w, b, v]), CLASS_CODE[now], CLASS_CODE[before])
                   for w in range(S * n) for b, recs in enumerate(con["at_visit"][w]) for v, (now, before) in enumerate(recs)]
    used = int((vt >= 0).sum(-1).max()) if vt.size else 0
    arrays = {"cells": np.floor(paths).astype(np.int8), "visit_tick": vt[..., :max(used, 1)].astype(np.int32),
              "entries": ent.astype(np.int32), "first_label": np.concatenate(con["first_label"]).astype(np.int16),
              "first_class": np.array([[CLASS_CODE[x] for x in row] for row in con["first_class"]], dtype=np.int8),
              "visits_contact": np.array(visits_rows, dtype=np.int32).reshape(-1, 6),
              "world_ids": np.tile(np.asarray(ids), S), "strain_of_world": np.repeat(np.arange(S), n),
              "class_codes": np.array(list(CLASS_CODE))}
    return out, arrays


def save_records(path: Path, arrays: dict) -> dict:
    """The condition's per-wey and per-visit arrays, saved locally (bulky; not committed), hashed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "sha256": E.sha256_bytes(path)}


def play(spec, cfg, con, l1, cx, champions, info, ids, dev, tangent: bool = False, save_as: Path | None = None) -> dict:
    iface, brain, S, access = build(spec, cfg, con, l1, cx, champions, dev)
    n, H, B = len(ids), int(cfg.world.max_ticks), int(cfg.world.weys_per_swarm)
    strain_of = torch.as_tensor(np.repeat(np.arange(S), n), device=dev).view(-1, 1)
    t0 = time.perf_counter()
    w = MW.MazeWorld(cfg, iface, brain, strain_of, run_seed=REGISTERED["maze_seed"], world_ids=np.tile(ids, S),
                     device=dev, access=access)
    moved = DC.tangent_start(w) if tangent else None
    rec = PathRecorder(S * n, B, H)
    w.recorder = rec
    w.run()
    ev = w.task_events()
    play_s = time.perf_counter() - t0
    strains, arrays = summarise(ev, rec.paths, w.mazes, w.placements, ids, S, info["_tables"], H, REGISTERED["c"])
    kept = save_records(save_as, arrays) if save_as is not None else None
    return {"records_file": kept, "role": spec["role"], "spec": {k: v for k, v in spec.items() if k not in ("role",)},
            "composition": [S, n, B], "play_seconds": play_s, "seconds": time.perf_counter() - t0,
            "runs": [r["run"] for r in champions.get(spec.get("arm"), [])] if spec["kind"] == "arm" else None,
            **({"tangent_moved_share": float(moved.mean())} if tangent else {}), "strains": strains}


def play_block(ctx, stage: str, block: str, family: str, k_r: int, champions: dict, state: dict, key: str,
               tangent: bool = False) -> dict:
    """Every condition of a block, the partial record written after each (§7). With `tangent`, the blind family
    only, from §3's tangent start (reported only)."""
    dev = ctx.args.device
    cfg_s = cfg_for(family, k_r, "shared")
    con, l1 = load_connectome(), A.load_l1()
    cx = AS.context(con, l1, cfg_s.brain)
    ids = ids_of(block)
    info = maze_info(family, k_r, ids)
    res = {"block": block, "family": family, "k_r": k_r if family == "islands" else None, "ids": [int(i) for i in ids],
           "mazes": info["mazes"], "first_draw_feasible_share": info["first_draw_feasible_share"], "conditions": {}}
    state[key] = res
    for spec in specs(block, champions):
        if tangent and spec["role"] != "blind":
            continue
        ctx.cap.check()
        cfg = cfg_for(family, k_r, spec.get("access", "shared"))
        with acct.category("final" if not tangent else "probe"):
            res["conditions"][spec["name"]] = play(spec, cfg, con, l1, cx, champions, info, ids, dev, tangent=tangent,
                                                   save_as=OUT / "records" / f"{stage}-{key}-{spec['name']}.npz")
        E.write_atomic(E.partial_path(stage), {"stage": stage, "partial": True, **state})
    return res


# ------------------------------------------------------------------------------------------- the stages

def projection(seconds: dict, champions: dict, reserved_hours: float = 0.0) -> dict:
    """The plan's cost from measured seconds per world (one colony, H ticks): scripted and neural single
    controllers (timed at 128 worlds), champion arms (timed at 8 × 128 worlds) and the records, scaled linearly
    in worlds; after each reduction in turn until it fits the ceiling."""
    import copy
    R = copy.deepcopy(REGISTERED)
    steps = [None] + R["reductions"]
    tried = []
    for k, red in enumerate(steps):
        if red:
            for key, v in red.items():
                if key.startswith("blocks."):
                    R["blocks"][key.split(".", 1)[1]] = v
                else:
                    R[key] = v
        saved = dict(REGISTERED)
        REGISTERED.update({kk: R[kk] for kk in ("turn_grid", "walk_grid", "blocks")})
        try:
            total = 0.0
            n_runs = {a: len(v) for a, v in champions.items()}
            for block, reps in (("calibration", len(R["k_r"])), ("confirmation", 1), ("tree_reference", 1), ("tangent", 1)):
                n = len(ids_of(block))
                for sp in specs(block, champions):
                    if block == "tangent" and sp["role"] != "blind":
                        continue
                    kind = ("arm" if sp["kind"] == "arm" else
                            "scripted" if sp["kind"] in ("wall", "walk", "oracle", "follower") else "neural")
                    S = n_runs.get(sp.get("arm"), 1) if sp["kind"] == "arm" else 1
                    total += reps * S * n * (seconds[kind] + seconds["records"])
        finally:
            REGISTERED.clear()
            REGISTERED.update(saved)
        tried.append({"after_reductions": k, "hours": total / 3600, "reserved_hours": reserved_hours})
        if total / 3600 + reserved_hours <= R["cap_gpu_hours"]:
            return {"admitted": True, "reductions": k, "plan": {kk: R[kk] for kk in ("turn_grid", "walk_grid", "blocks")},
                    "tried": tried}
    return {"admitted": False, "reductions": len(steps) - 1, "plan": None, "tried": tried}


def reserved_hours(clock, now: float | None = None) -> float:
    """The hours the admission reserves (both reviewers): earlier attempts, this stage's own elapsed time, and
    g-e's allowance."""
    now = time.perf_counter() if now is None else now
    return clock.spent_hours() + (now - clock.t_start) / 3600 + REGISTERED["ge_allowance_hours"]


def cmd_project(args):
    def body(ctx):
        dev = ctx.args.device
        champions = available_champions()
        out = {"champions_record": check_champions_record(), "champions": {a: [r["run"] for r in v] for a, v in champions.items()}}
        con, l1 = load_connectome(), A.load_l1()
        H, H_t = REGISTERED["H"], min(TIMING_TICKS, REGISTERED["H"])
        cfg = cfg_for("islands", 0, "shared")
        cfg.world.max_ticks = H_t  # timed over H_t ticks, scaled to H
        cx = AS.context(con, l1, cfg.brain)
        n_t = min(TIMING_MAZES, len(ids_of("calibration")))
        ids = np.arange(40_100, 40_100 + n_t)  # timing mazes, outside every E3d block
        info = maze_info("islands", 0, ids)
        arm = next(iter(champions), None)
        timed = [("scripted", {"name": "t", "role": "blind", "kind": "wall", "hand": "left"}),
                 ("neural", {"name": "t", "role": "organism", "kind": "seed", "noses": True})]
        if arm:
            timed.append(("arm", {"name": "t", "role": "blind", "kind": "arm", "arm": arm, "noses": False}))
        secs, rec_s, rec_w = {}, 0.0, 0
        with acct.category("calibration"):
            for kind, spec in timed:  # saving the records is timed too, then the timing files are removed
                tmp = OUT / "records" / f"project-timing-{kind}.npz"
                r = play(spec, cfg, con, l1, cx, champions, info, ids, dev, save_as=tmp)
                tmp.unlink(missing_ok=True)
                worlds = r["composition"][0] * r["composition"][1]
                secs[kind] = r["play_seconds"] / worlds * H / H_t
                rec_s, rec_w = rec_s + r["seconds"] - r["play_seconds"], rec_w + worlds
        secs.setdefault("arm", secs["neural"])
        secs["records"] = rec_s / rec_w * H / H_t
        out["seconds_per_world"] = secs
        out["timing"] = {"ticks": H_t, "mazes": n_t, "arm": arm}
        reserve = reserved_hours(ctx.cap)
        out["reserved_hours"] = {"total": reserve, "spent_before_this_stage": ctx.cap.spent_hours(),
                                 "g-e_allowance": REGISTERED["ge_allowance_hours"]}
        out.update(projection(secs, champions, reserved_hours=reserve))
        out["first_draw_feasible_share_calibration"] = {}
        for k_r in REGISTERED["k_r"]:
            ks = [IS.islands_for(run_seed=REGISTERED["maze_seed"], maze_id=int(m), c=REGISTERED["c"], k_r=k_r).k
                  for m in ids_of("calibration")]
            out["first_draw_feasible_share_calibration"][str(k_r)] = float(np.mean([k == 0 for k in ks]))
        return out

    return E.run_stage(args, "project", requires("project"), body)


def cmd_ge(args):
    def body(ctx):
        out = {}
        B1 = _load("e3b1_for_e3d_ge", "e3b1.py")
        B1.SMOKE = SMOKE
        ref = json.loads((ROOT / B1.EQ_REFERENCE).read_text(encoding="utf-8"))
        with acct.category("calibration"):
            out["cpu"] = B1.EQ.compare(ref, B1.EQ.run(ROOT, ROOT / "data" / "cache" / "cook2019_herm.npz"))
            out["snapshot_hook"] = B1.hook_leg(ctx.cap)
            out["mazes"] = B1.maze_leg()
            out["gpu"] = {"skipped": "smoke"} if SMOKE else B1.gpu_leg(ctx.args.device, ctx.cap)
            legs = {"cpu": "cpu"} if SMOKE else {"cpu": "cpu", "cuda": ctx.args.device}
            out["full_rollout"] = {name: rollout_leg(name, dev) for name, dev in legs.items()}
        out["passed"] = bool(B1.ge_passed(out["cpu"], out["gpu"], out["snapshot_hook"], out["mazes"], smoke=SMOKE)
                             and all(v.get("identical") for v in out["full_rollout"].values()))
        return out

    return E.run_stage(args, "g-e", requires("g-e"), body)


def rollout_leg(name: str, dev: str, run=subprocess.run) -> dict:
    """The full-rollout leg against the committed reference. Passes only on a fresh comparison written by a
    subprocess that exits 0 and reports identical (Astra: a stale record must not pass). The compare runs as a
    subprocess outside the accounting, so its rollouts are uncounted (rule 8; Fable)."""
    refp = REFERENCES / f"equivalence-reference-{name}.json"
    if not refp.exists():
        return {"identical": False, "missing_reference": str(refp.relative_to(ROOT))}
    rec = OUT / f"equivalence-{name}.json"
    rec.unlink(missing_ok=True)
    r = run([sys.executable, str(ROOT / "scripts" / "e3d_equivalence.py"), "--compare", "--reference", str(refp),
             "--device", dev, "--out", str(rec)], capture_output=True, text=True)
    got = json.loads(rec.read_text(encoding="utf-8")) if rec.exists() else {"identical": False, "missing_record": True}
    return {**got, "identical": bool(r.returncode == 0 and got.get("identical") is True), "returncode": r.returncode,
            "reference_sha256": E.sha256_bytes(refp), "stderr_tail": (r.stderr or "")[-2000:] if r.returncode else "",
            "accounting": ("the compare's wall time counts in g-e's seconds; its worlds, ticks and neural updates are "
                           "uncounted (a subprocess outside wormwars.accounting; rule 8)")}


def stage_records(stage: str) -> list:
    """A stage's record files, so a rerun archives attempt 1's with its record (Fable)."""
    return sorted((OUT / "records").glob(f"{stage}-*.npz"))


def apply_plan(project: dict) -> None:
    """The projection's plan (after any reductions) for the formal blocks."""
    plan = project.get("plan") or {}
    for key in ("turn_grid", "walk_grid", "blocks"):
        if key in plan:
            REGISTERED[key] = plan[key]


def cmd_calibrate(args):
    def body(ctx):
        apply_plan(ctx.earlier["project"])
        champions = available_champions()
        state = {"champions_record": check_champions_record(), "blocks": {}}
        gates, feasible = {}, {}
        for k_r in REGISTERED["k_r"]:
            b = play_block(ctx, "calibrate", "calibration", "islands", k_r, champions, state["blocks"], str(k_r))
            gates[k_r] = GT.gate(b, REGISTERED["thresholds"])
            feasible[k_r] = b["first_draw_feasible_share"]
            b["gate"] = gates[k_r]
        state["choice"] = GT.choose_k(gates, feasible, REGISTERED["feasible_floor"])
        return state

    return E.run_stage(args, "calibrate", requires("calibrate"), body, local_files=stage_records("calibrate"))


def cmd_confirm(args):
    def body(ctx):
        apply_plan(ctx.earlier["project"])
        champions = available_champions()
        chosen = ctx.earlier["calibrate"]["choice"]["k_r"]
        k_r = int(REGISTERED["k_r"][0] if chosen is None else chosen)  # None only in a smoke run
        state = {"champions_record": check_champions_record(), "k_r": k_r, "blocks": {},
                 **({"smoke_k_r": "calibration chose none; the smoke plays the first k_r"} if chosen is None else {})}
        b = play_block(ctx, "confirm", "confirmation", "islands", k_r, champions, state["blocks"], "confirmation")
        b["gate"] = GT.gate(b, REGISTERED["thresholds"])
        play_block(ctx, "confirm", "tree_reference", "tree", 0, champions, state["blocks"], "tree_reference")
        play_block(ctx, "confirm", "tangent", "islands", k_r, champions, state["blocks"], "tangent", tangent=True)
        return state

    return E.run_stage(args, "confirm", requires("confirm"), body, local_files=stage_records("confirm"))


def report_from(earlier: dict) -> dict:
    cal, conf = earlier["calibrate"], earlier.get("confirm")
    out = {"calibration": {k: {"gate": b["gate"], "first_draw_feasible_share": b["first_draw_feasible_share"]}
                           for k, b in cal["blocks"].items()}, "choice": cal["choice"]}
    if cal["choice"]["k_r"] is None and not (conf or {}).get("smoke_k_r"):
        out["verdict"] = cal["choice"]["verdict"]
        return out
    if conf is None:
        out["verdict"] = "E3d: not completed (no confirmation record)"
        return out
    isl, tree = conf["blocks"]["confirmation"], conf["blocks"]["tree_reference"]
    g = GT.gate(isl, REGISTERED["thresholds"])
    out.update({"verdict": g["verdict"], "gate": g, "failed": g["failed"],
                "bootstrap": GT.bootstrap(isl, REGISTERED["bootstrap"]["resamples"], REGISTERED["bootstrap"]["seed"]),
                "tree_reference_gate_quantities": GT.quantities(tree),
                "maze_summary": {b: maze_summary(conf["blocks"][b]) for b in ("confirmation", "tree_reference")},
                "scent_reach_split": scent_split(isl),
                "tangent_blind_means": ({m: float(np.mean(v)) for m, v in GT.blind_members(conf["blocks"]["tangent"]).items()}
                                        if "tangent" in conf["blocks"] else None),
                "predictions": GT.predictions(isl, tree),
                "round_trip_share_blind": {m: float(np.mean(st["round_trip_share"]))
                                           for name, c in isl["conditions"].items() if c["role"] == "blind"
                                           for m, st in ((name if len(c["strains"]) == 1 else f"{name}#{s}", st)
                                                         for s, st in enumerate(c["strains"]))}})
    return out


def maze_summary(block: dict) -> dict:
    """The accepted mazes' means: open share, junctions, dead ends, the A-B detour, line of sight, the goals'
    entrances, spawn candidates, the share redrawn, the share of goals the scent-reach flag marks."""
    rows = block["mazes"]
    f = lambda k: float(np.mean([r[k] for r in rows]))  # noqa: E731
    return {**{k: f(k) for k in ("open_share", "junctions", "dead_ends", "detour", "line_of_sight_share", "spawn_candidates")},
            "entrances": float(np.mean([e for r in rows for e in r["entrances"]])),
            "redrawn_share": float(np.mean([r["redraw"] > 0 for r in rows])),
            "scent_reach_share": float(np.mean([x for r in rows for x in r["scent_reach"]]))}


def scent_split(block: dict) -> dict:
    """§2: per goal (Astra), the share of the shared follower's and the seed's weys whose head reached that goal,
    on goals whose scent reaches the perimeter track and on the others; A and B separately and pooled. Beside it,
    the whole-maze split (visits and no-first-visit shares on mazes with both goals flagged and the others)."""
    flags = np.array([r["scent_reach"] for r in block["mazes"]], dtype=bool)  # [mazes, (A, B)]
    both = flags.all(-1)
    out = {"goals_flagged": int(flags.sum()), "goals_other": int((~flags).sum()),
           "mazes_both_flagged": int(both.sum()), "mazes_other": int((~both).sum()), "per_goal": {}}
    for name in ("follower_shared", "seed"):
        st = block["conditions"][name]["strains"][0]
        arr = np.stack([np.asarray(st["arrived_a"]), np.asarray(st["arrived_b"])], axis=-1)
        grp = lambda m: float(arr[m].mean()) if m.any() else None  # noqa: E731
        out["per_goal"][name] = {"arrived_flagged": grp(flags), "arrived_other": grp(~flags),
                                 **{f"arrived_{g}_{lab}": (float(arr[:, k][m[:, k]].mean()) if m[:, k].any() else None)
                                    for k, g in enumerate("ab") for lab, m in (("flagged", flags), ("other", ~flags))}}
    for name in ("follower_shared", "seed"):
        st = block["conditions"][name]["strains"][0]
        v, z = np.asarray(st["visits"]), np.asarray(st["no_first_visit_share"])
        out[name] = {grp: ({"visits": float(v[m].mean()), "no_first_visit_share": float(z[m].mean())} if m.any() else None)
                     for grp, m in (("both_flagged", both), ("other", ~both))}
    return out


def cmd_report(args):
    def body(ctx):
        return report_from(ctx.earlier)

    return E.run_stage(args, "report", requires("report"), body)


# ------------------------------------------------------------------------------------------- smoke and main

def use_smoke(args) -> None:
    global EXP, OUT, SMOKE
    EXP = OUT = ROOT / "runs" / "e3d-smoke"
    SMOKE = True
    R = REGISTERED
    R["H"] = 60
    R["blocks"] = {"calibration": [8000, 8002], "confirmation": [8002, 8004], "tree_reference": [8002, 8004],
                   "tangent": [8002, 8003]}
    R["turn_grid"] = [0.4, 1.95]
    R["walk_grid"] = {"persistence": [0.5], "rate": [1.0], "speed": 1.0, "seed": 0}
    R["bootstrap"] = {"resamples": 50, "seed": 20_261_011}
    configure()
    stage = args.command
    for s in STAGES[STAGES.index(stage):]:
        files = [E.record_path(s), E.marker_path(s), E.partial_path(s)]
        files += [E.rerun_note(E.record_path(s))] + [E.attempt1(f) for f in list(files)]
        for f in files:
            if EXP in f.parents:
                f.unlink(missing_ok=True)


COMMANDS = {"project": cmd_project, "g-e": cmd_ge, "calibrate": cmd_calibrate, "confirm": cmd_confirm, "report": cmd_report}


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=list(COMMANDS))
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--guarded", action="store_true")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--reason")
    args = ap.parse_args()
    if args.smoke:
        use_smoke(args)
    if args.command == "report":
        REGISTERED["cap_gpu_hours"] = float("inf")
    COMMANDS[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    if any(a == "--out" or a.startswith("--out=") for a in sys.argv[1:]):
        raise SystemExit("--out is not accepted: E3d writes only to its own folders")
    smoke = "--smoke" in sys.argv
    out_dir = ROOT / "runs" / ("e3d-smoke" if smoke else "e3d")
    try:
        run_script(main, out_default=str(out_dir), default="measure", name="e3d")
    finally:
        agg = out_dir / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
