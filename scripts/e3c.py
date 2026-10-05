"""E3c: the assembly comparison (docs/E3/E3c-DESIGN.md v2.1; D198-D200). This runner holds the exploratory pilot (§5).

    python scripts/e3c.py pilot             # the pilot, on the GPU (about 2.5 GPU-hours)
    add --smoke for toy sizes in runs/e3c-smoke (never results)

**The pilot:**
- **The runs:** S-mod, S-dense and P-sel, 3 runs each.
- **The schedule:** factor 1.0, 100 generations × 8 mazes per genome.
- **The checkpoints:** every 25 generations, on a pilot learning-curve block of 128 mazes.
- **The references:** W2 alone and the seed (P-fixed), on the same block.
- **The decision branch:** "mazes" if either S arm is off the floor (a checkpoint above W2 alone + 1 visit per
  wey), "open arena" if neither is, and "inconclusive" if the pilot did not complete.

The pilot's compute counts toward E3c's ceiling of 30 GPU-hours (`runs/e3c/compute`).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import graft as G  # noqa: E402
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e3 import assembly as AS  # noqa: E402
from wormwars.e3 import maze as MZ  # noqa: E402
from wormwars.e3 import maze_measures as MM  # noqa: E402
from wormwars.e3 import maze_organisms as MO  # noqa: E402
from wormwars.e3 import maze_runs as MR  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e3 import organism as O  # noqa: E402
from wormwars.e3 import probe as P  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.e4s import comparator as C  # noqa: E402
from wormwars.e3 import attribution as AT  # noqa: E402
from wormwars.evo.genomes import genome_hash, save_population  # noqa: E402


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


E = _load("e2_for_e3c", "e2.py")  # E2's stage frame, configured for E3c's own folders

EXP = ROOT / "experiments" / "E3-ab-organism" / "E3c"
OUT = ROOT / "runs" / "e3c"
DESIGN = "docs/E3/E3c-DESIGN.md"
FIXED = {"experiments/E4s-stereo-module/E4s-0/module.json": "9613cd155a20ed2cfb891c1bd10fed16814f24a04f912a1940524f2378e877d4"}
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", DESIGN, *FIXED]
SMOKE = False

STAGES = ["pilot", "replay"]
REGISTERED = {
    "maze_seed": 1_180_000, "c": 5, "H": 2400, "colony": 8, "spawns": 4,
    "trail": {"mu": 0.01, "lam": 0.02, "delta": 0.05, "d0": 1.142},
    "ga": {"population": 32, "elites": 3, "truncation": 8,
           "mutation": {"w_sigma": 0.08, "tau_sigma": 0.15, "bias_sigma": 0.05, "p_mutate": 1.0}, "factor": AS.FACTOR},
    "pilot": {"runs_per_arm": 3, "G": 100, "W": 8, "checkpoint_every": 25, "learning": [7600, 7728],
              "train_base": 30_000_000, "train_span": 10_000_000, "run_seed_base": 1_200_000, "margin": 1.0},
    "smoke_ids": [8000, 8100],
    "replay": {"pilot_sha256": "6f6402ebecdf34633a77f8e4df97f8cf9a1e86316179116a63a668286d9ee41e",
               "engine_paths": ["wormwars", "configs", "requirements.txt"],
               "cap_total_gpu_hours": 5.0,  # E3c's running total: the pilot's 2.85 + about 1.5 + margin (D205)
               "turn_sweep": [-0.8, -0.4, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4]},
    "cap_gpu_hours": 4.5,  # the pilot's stop: about 2.8 h projected, and a rerun must fit; it counts toward E3c's 30
    "rerun_kill_tail_seconds": 900,
}
ARM_OFFSET = {"s_mod": 0, "s_dense": 10, "p_sel": 20}


def configure() -> None:
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, OUT, GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E3c: not completed (the run stopped)",
                  "cap": "E3c: not completed (the cap was reached)"}
    E.RECORD.update({s: s for s in STAGES})
    E.WHAT.update({s: f"E3c's {s}" for s in STAGES})


configure()


def check_inputs() -> dict:
    got = {}
    for rel, want in FIXED.items():
        h = hashlib.sha256((ROOT / rel).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if h != want:
            raise SystemExit(f"{rel} has changed (sha256 {h}): refusing to run")
        got[rel] = h
    return got


def base_config():
    cfg = E.E1.config(6.0)
    want = json.loads(E.E1_GATE.read_text(encoding="utf-8"))["resolved_config"]
    if hashlib.sha256(json.dumps(want, sort_keys=True).encode()).hexdigest() != E.config_sha256(cfg):
        raise SystemExit("Task N's resolved configuration differs from E1's gate: refusing to run")
    return cfg


def cfg_for(access: str, W: int):
    R = REGISTERED
    cfg = MW.maze_config(base_config(), c=R["c"], horizon=R["H"], colony=R["colony"], access=access,
                         spawns=R["spawns"], **R["trail"])
    g = R["ga"]
    cfg.evo.population, cfg.evo.elites, cfg.evo.truncation = g["population"], g["elites"], g["truncation"]
    cfg.evo.worlds_per_strain = int(W)
    for k, v in g["mutation"].items():
        setattr(cfg.mutation, k, v)
    return cfg


E.task_config = lambda: cfg_for("shared", REGISTERED["pilot"]["W"])


def seed() -> int:
    return REGISTERED["maze_seed"]


def learning_ids() -> np.ndarray:
    return np.arange(*REGISTERED["smoke_ids"])[:4] if SMOKE else np.arange(*REGISTERED["pilot"]["learning"])


def pilot_runs() -> list:
    P_ = REGISTERED["pilot"]
    return [{"arm": arm, "run": ARM_OFFSET[arm] + k, "seed": P_["run_seed_base"] + ARM_OFFSET[arm] + k}
            for arm in AS.TRAINED for k in range(P_["runs_per_arm"])]


def off_floor(checkpoints: list, w2: float, margin: float | None = None) -> bool:
    """§5: a checkpoint's generation-best strictly above W2 alone + the margin (1 visit per wey)."""
    margin = REGISTERED["pilot"]["margin"] if margin is None else margin
    return any(c["validation_mean"] > w2 + margin for c in checkpoints)


def decision(off: dict, complete: bool) -> str:
    """§5's branches, fixed before the pilot."""
    if not complete:
        return "inconclusive"
    return "mazes" if (off.get("s_mod") or off.get("s_dense")) else "open arena"


def w2_alone(con, bcfg):
    """W2 alone on the carrier (the carrier with W2 and no seed module), built as E3b-0 built it."""
    carrier = O.carrier_only()
    ext = G.graft_connectome(con, carrier)
    sd = MO.Seed("carrier", carrier, ext, C.carrier_genome(ext, carrier, bcfg, forward=1.0, turn=0.2))
    return MO.maze_organism(con, sd, "W2", bcfg)


def preflight(ids_list: list) -> dict:
    redrawn = []
    for mid in sorted(set(int(x) for x in ids_list)):
        _, k = MZ.walls_for(run_seed=seed(), maze_id=mid, c=REGISTERED["c"])
        MZ.maze_for(run_seed=seed(), maze_id=mid, episode=0, c=REGISTERED["c"], n_spawns=REGISTERED["spawns"])
        if k:
            redrawn.append({"id": mid, "k": int(k)})
    return {"checked": len(set(int(x) for x in ids_list)), "redrawn": redrawn}


def outcomes(ev: dict, H: int) -> dict:
    vt = ev["visit_tick"]
    S, n = vt.shape[:2]
    f = lambda x: np.asarray(x).reshape(S * n, *np.asarray(x).shape[2:])  # noqa: E731
    legs = MM.legs(f(vt))
    rate, unvisited = MM.later_leg_rate(f(vt), H)
    out = {"visits": MM.colony_mean(f(ev["visits"])), "legs": MM.colony_mean(legs), "later_leg_rate": rate,
           "unvisited_share": unvisited, "round_trip_share": (legs >= 2).mean(axis=-1)}
    return {k: np.asarray(v, dtype=np.float64).reshape(S, n) for k, v in out.items()}


def resting_turn(org, cfg) -> float:
    """An organism's turn command with the noses level (m = 0.05) and q free from 0, after 60 ticks (E3a's probe)."""
    pc = P.ProbeContext(org.ext, org.iface, cfg)
    return float(pc.turn(P._free_run(org.genome, pc, pc.latch_state(org.genome, 0.0), 60, None, 0)[-1])[0])


def generation0_offsets(genome: Genome, org, cfg, ref: float) -> dict:
    """E3a's generation-0 log (scripts/e3a.py `generation0_offsets`), per strain: the turn offset from `ref` at level
    noses, and A's K_D with q held at 0. The draws are mirror-symmetric, so the offsets should be 0 (a check)."""
    pc = P.ProbeContext(org.ext, org.iface, cfg)
    st = pc.latch_state(genome, 0.0)
    u = P._free_run(genome, pc, st, 60, None, 0)[-1]
    return {"turn_offset": (pc.turn(u) - ref).tolist(), "K_D_A_at_q0": P.k_d(genome, pc, "A", 0.05, st).tolist()}


def assert_frozen(start: Genome, final: Genome, scales: dict) -> None:
    """Every parameter the arm's mask freezes (scale 0) is the draw's, bitwise, in every strain of `final`."""
    got, ref = final.params(), start.params()
    for k, sc in scales.items():
        if ref.get(k) is None:
            continue
        frozen = sc.reshape(-1) == 0
        want = ref[k][0, frozen]
        assert torch.equal(ref[k][:, frozen], want.expand(ref[k].shape[0], -1)), f"{k}: the draws differ where frozen"
        assert torch.equal(got[k][:, frozen], want.expand(got[k].shape[0], -1)), f"{k}: a frozen parameter moved"


def _per_maze(out: dict, k: int) -> dict:
    return {m: np.round(v[k], 6).tolist() for m, v in out.items()}


def run_summary(r: dict, rec) -> dict:
    """A run's training record: every checkpoint's per-maze counts, the generation logs and timings, and the
    generation-0 per-strain means (the distributions the power analysis needs)."""
    g0 = np.asarray(rec.generation0.get("counts", []), dtype=np.float64)
    return {"arm": r["arm"], "run": r["run"], "seed": r["seed"],
            "learning_curve": [{k: c[k] for k in ("generation", "validation_mean", "validation_counts", "sha256")}
                               for c in rec.checkpoints],
            "best_fitness": [g["best_fitness"] for g in rec.log], "mean_fitness": [g["mean_fitness"] for g in rec.log],
            "best_sha256": [g["best_sha256"] for g in rec.log],
            "batch_seconds": [g.get("batch_seconds") for g in rec.log],
            "generation0": {"mean_visits": np.round(g0.mean(axis=1), 6).tolist() if g0.size else [],
                            "train_ids": rec.generation0.get("train_ids")}}


def cmd_pilot(args):
    def body(ctx):
        inputs = check_inputs()
        dev = ctx.args.device
        P_ = REGISTERED["pilot"]
        cfg = cfg_for("shared", P_["W"])
        con, l1 = load_connectome(), A.load_l1()
        cx = AS.context(con, l1, cfg.brain)
        learn = learning_ids()
        runs = pilot_runs()
        by_run = {r["run"]: r for r in runs}
        pop = cfg.evo.population
        G_ = P_["G"]
        train = [int(x) for r in runs for g in range(G_)
                 for x in EV.train_ids(r["seed"], g, P_["W"], P_["train_base"], P_["train_span"])]
        ctx.doc["mazes"] = preflight(list(learn) + train)
        draws = {r["run"]: AS.draw(r["arm"], cx, np.random.default_rng([r["seed"], 0xE3C]), pop) for r in runs}
        scales = {arm: AS.arm_scales(arm, cx) for arm in AS.TRAINED}
        recs, live, last_write = {}, [], [0.0]

        def progress() -> dict:
            return {"decision": "inconclusive",
                    "completed_runs": [run_summary(by_run[k], recs[k]) for k in sorted(recs)],
                    "runs_in_progress": [run_summary(by_run[x.spec.run], x) for x in live if x.spec.run not in recs]}

        def write_partial(force=False):
            # at least once a minute, so a kill is charged to its last minute (E2's reconciliation)
            if force or time.monotonic() - last_write[0] >= 60:
                E.write_atomic(E.partial_path("pilot"), {"stage": "pilot", **progress()})
                last_write[0] = time.monotonic()

        def check():
            ctx.cap.check()
            write_partial()

        def on_checkpoint(records, g):
            live[:] = records
            write_partial(force=True)

        ctx.salvage = progress
        for arms, org in ((("s_mod", "p_sel"), cx["seed"]), (("s_dense",), cx["dense"])):
            group = [r for r in runs if r["arm"] in arms]
            specs = [EV.RunSpec(r["run"], r["seed"], 0.0) for r in group]
            out = EV.evolve_batch(cfg, org.iface, BrainSpec.from_connectome(org.ext), specs, generations=G_,
                                  checkpoint_every=P_["checkpoint_every"], validation_ids=learn, world_seed=seed(),
                                  id_base=P_["train_base"], id_span=P_["train_span"], device=dev, check=check,
                                  category=acct.category, initial=lambda r: draws[r.run],
                                  mutation_scales=lambda r: scales[by_run[r.run]["arm"]], on_checkpoint=on_checkpoint)
            for rec in out:
                arm = by_run[rec.spec.run]["arm"]
                for g in (rec.final, *rec.candidates):
                    assert_frozen(draws[rec.spec.run], g, scales[arm])
                recs[rec.spec.run] = rec
            live.clear()
            write_partial(force=True)
        # the references on the pilot's block
        refs = {}
        with acct.category("holdout"):
            for name, org in (("w2_alone", w2_alone(con, cfg.brain)), ("seed", cx["seed"])):
                ctx.cap.check()
                ev = MR.play(cfg, org.iface, lambda org=org: MO.brain(org, dev), learn, seed(), dev, access="shared")
                ev1 = {k: (v[None] if isinstance(v, np.ndarray) and v.shape[:1] == (len(learn),) else v) for k, v in ev.items()}
                o = outcomes(ev1, int(cfg.world.max_ticks))
                refs[name] = {**{k: float(v.mean()) for k, v in o.items()}, "per_maze": _per_maze(o, 0)}
        w2 = refs["w2_alone"]["visits"]
        ref_turn = resting_turn(cx["seed"], cfg)
        arms = {}
        for arm in AS.TRAINED:
            rs = [r for r in runs if r["arm"] == arm]
            org = cx["dense"] if arm == "s_dense" else cx["seed"]
            # each run's last generation-best, on the pilot's block: legs and the other outcomes
            last = Genome.cat([recs[r["run"]].candidates[-1] for r in rs])
            ctx.cap.check()
            with acct.category("holdout"):
                ev = MR.play_batch(cfg, org.iface, Brain(last if str(dev) == "cpu" else EV.moved(last, dev)),
                                   np.arange(len(rs)), learn, seed(), dev, access="shared")
            final = outcomes(ev, int(cfg.world.max_ticks))
            per_run = []
            for k, r in enumerate(rs):
                rec = recs[r["run"]]
                s = run_summary(r, rec)
                with acct.category("probe"):
                    s["generation0"].update(generation0_offsets(draws[r["run"]], org, cfg, ref=ref_turn))
                g0 = np.asarray(s["generation0"]["mean_visits"])
                s["generation0"]["share_above_w2"] = float((g0 > w2).mean())
                s["final_generation_best"] = {**{m: float(final[m][k].mean()) for m in final},
                                              "per_maze": _per_maze(final, k)}
                s["off_floor"] = off_floor(rec.checkpoints, w2)
                s["frozen_checked"] = True
                per_run.append(s)
            arms[arm] = {"runs": per_run, "off_floor": any(x["off_floor"] for x in per_run),
                         "generation0_max_abs_offset": max(float(np.abs(x["generation0"]["turn_offset"]).max())
                                                           for x in per_run)}
        off = {arm: arms[arm]["off_floor"] for arm in AS.TRAINED}
        return {"fixed_inputs": inputs, "references": refs, "arms": arms, "off_floor": off,
                "decision": decision(off, complete=True), "completed_runs": None, "runs_in_progress": None,
                "criterion": f"a checkpoint's generation-best above W2 alone ({w2:.3f}) + {P_['margin']} visit per wey",
                "composition": {"training_e": [6 * pop, P_["W"], REGISTERED["colony"]],
                                "training_dense": [3 * pop, P_["W"], REGISTERED["colony"]]},
                "note": "exploratory (§5); only the mutation factor may change after it"}

    return E.run_stage(args, "pilot", lambda a, prov: {}, body)


# ============================================================================== the replay and probe (D205)

def compare_hashes(got: list, want: list) -> dict:
    """Every generation's best-genome hash, run by run, against the pilot's record."""
    per = [sum(a == b for a, b in zip(x, y)) for x, y in zip(got, want)]
    return {"all_match": got == want, "matching_generations_per_run": per}


def cell_index(xy: np.ndarray, c: int) -> np.ndarray:
    """The maze cell (row × c + column) of grid positions [..., 2] in cell units: cell (col, row) owns its 3 × 3
    open block from 1 + 4 col and the corridor after it."""
    col = np.clip(np.floor((xy[..., 0] - 1) / 4), 0, c - 1).astype(np.int64)
    row = np.clip(np.floor((xy[..., 1] - 1) / 4), 0, c - 1).astype(np.int64)
    return row * c + col


def _moves(cells: np.ndarray) -> np.ndarray:
    """A wey's directed cell-to-cell moves (from, to), encoded as from × 1000 + to, repeats of a cell removed."""
    seq = np.asarray(cells, dtype=np.int64)
    if len(seq) == 0:
        return seq
    seq = seq[np.concatenate([[True], seq[1:] != seq[:-1]])]
    return seq[:-1] * 1000 + seq[1:]


def tour_match(cells: np.ndarray, period: int) -> float:
    """The share of a wey's directed moves that repeat the move `period` moves earlier. A circuit of a tree
    (a wall-follower's) repeats every 2 × (cells − 1) moves and scores 1; NaN unless the wey made more than
    `period` moves (Astra: cells alone can match where no move does)."""
    mv = _moves(cells)
    if len(mv) <= period:
        return float("nan")
    return float(np.mean(mv[period:] == mv[:-period]))


def tour_match_best_lag(cells: np.ndarray, lags=range(44, 53)) -> float:
    """Exploratory companion (Fable): the best tour match over nearby lags, less sensitive to one deviation."""
    vals = [tour_match(cells, k) for k in lags]
    vals = [v for v in vals if v == v]
    return max(vals) if vals else float("nan")


class CellRecorder:
    """Each wey's maze cell at every tick (the world calls `record` after each step)."""

    def __init__(self, c: int):
        self.c, self.ticks = c, []

    def record(self, world) -> None:
        self.ticks.append(world.pos[:, 0].detach().to("cpu", torch.float64).numpy().copy())


def _nan_to_none(x):
    return None if isinstance(x, float) and x != x else x


def play_recorded(cfg, iface, brain, n_strains: int, ids, dev) -> dict:
    """Every strain on every maze at episode 0 under shared trails (play_batch's layout), with each wey's cell
    recorded: the visits, and per wey the coverage of the c × c cells and the tour match."""
    from wormwars.e3 import maze_world as MW_
    ids = np.asarray(ids)
    S, n = n_strains, len(ids)
    strain_of = torch.as_tensor(np.repeat(np.arange(S), n), device=dev).view(-1, 1)
    w = MW_.MazeWorld(cfg, iface, brain, strain_of, run_seed=seed(), world_ids=np.tile(ids, S), device=dev,
                      access="shared")
    c = REGISTERED["c"]
    rec = CellRecorder(c)
    w.recorder = rec
    w.run()
    ev = w.task_events()
    ev = {k: (v.reshape(S, n, *v.shape[1:]) if isinstance(v, np.ndarray) and v.shape[:1] == (S * n,) else v)
          for k, v in ev.items()}
    visits = outcomes(ev, int(cfg.world.max_ticks))["visits"]  # [S, n]
    cells = np.stack(rec.ticks, axis=0)  # [ticks, worlds, weys, 2]
    cells = cell_index(cells, c).transpose(1, 2, 0)  # [worlds, weys, ticks]
    cov = np.array([[len(np.unique(cells[i, j])) / (c * c) for j in range(cells.shape[1])] for i in range(cells.shape[0])])
    period = 2 * (c * c - 1)
    tm = np.array([[tour_match(cells[i, j], period) for j in range(cells.shape[1])] for i in range(cells.shape[0])])
    tb = np.array([[tour_match_best_lag(cells[i, j]) for j in range(cells.shape[1])] for i in range(cells.shape[0])])

    def path(i, j):
        q = cells[i, j]
        keep = np.concatenate([[True], q[1:] != q[:-1]])
        return {"maze": int(ids[i % n]), "wey": j, "cells": q[keep].tolist(), "ticks": np.flatnonzero(keep).tolist()}

    out = []
    for s in range(S):
        sl = slice(s * n, (s + 1) * n)
        t = tm[sl]
        out.append({"sample_paths": [path(s * n + m, j) for m in range(min(4, n)) for j in range(2)],
                    "tour_match_best_lag": _nan_to_none(float(np.nanmean(tb[sl])) if np.isfinite(tb[sl]).any()
                                                        else float("nan")),"visits": float(visits[s].mean()), "visits_per_maze": np.round(visits[s], 6).tolist(),
                    "coverage": float(cov[sl].mean()), "coverage_per_maze": np.round(cov[sl].mean(axis=1), 6).tolist(),
                    "tour_match": _nan_to_none(float(np.nanmean(t)) if np.isfinite(t).any() else float("nan")),
                    "tour_match_per_maze": [_nan_to_none(float(np.nanmean(r)) if np.isfinite(r).any() else float("nan"))
                                            for r in t]})
    return {"strains": out}


def w2_turn(con, bcfg, rest: float):
    """W2 alone with the carrier's turn bias set for resting turn `rest` (W2's own is MO.REST_TURN["W2"])."""
    org = w2_alone(con, bcfg)
    k = 2 * math.tanh(math.atanh(rest / 2) - MO.resting_reflex_push("W2"))
    b_t = math.atanh(k / 2)
    bias = org.genome.bias.clone()
    for name in C.TURN_DORSAL:
        bias[:, org.ext.index(name)] = b_t
    for name in C.TURN_VENTRAL:
        bias[:, org.ext.index(name)] = -b_t
    return MO.Organism(f"W2+turn{rest:g}", org.module, org.ext, org.iface, org.genome.with_params(bias=bias))


def consequence(probes: dict, champions: list) -> str:
    """D205's outcomes, fixed before the replay: "coverage" if every champion keeps ≥ 0.9 of its visits with the
    noses removed and covers ≥ 0.95 of its maze with a tour match ≥ 0.5; "scent-dependent" if every champion
    keeps ≤ 0.5; "mixed" otherwise."""
    ps = [probes[k] for k in champions]
    if all(p["retained_fraction"] is not None and p["retained_fraction"] >= 0.9 and p["intact"]["coverage"] >= 0.95
           and (p["intact"]["tour_match"] or 0) >= 0.5 for p in ps):
        return "coverage"
    if all(p["retained_fraction"] is not None and p["retained_fraction"] <= 0.5 for p in ps):
        return "scent-dependent"
    return "mixed"


def require_pilot(args, prov) -> dict:
    """The pilot's record, made on earlier scripts (both reviewers; E3b-0's pattern, D178): completed, committed,
    the pinned file, the same environment, and the engine paths unchanged since its commit. `scripts` may
    differ: the replay's own code lives there."""
    path = E.record_path("pilot")
    if not path.exists():
        raise SystemExit("the pilot has not run")
    raw = path.read_bytes()
    if E.formal(args) and not args.smoke:
        E.require_committed(path)
        if hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() != REGISTERED["replay"]["pilot_sha256"]:
            raise SystemExit("pilot.json differs from the pinned record: not the pilot the replay reproduces")
    rec = json.loads(raw.decode("utf-8"))
    if rec.get("outcome") != "completed":
        raise SystemExit("the pilot did not complete")
    if E.formal(args) and not args.smoke:
        E.reg.require_same_code(rec["provenance_at_start"]["git_commit"], REGISTERED["replay"]["engine_paths"])
        E.reg.require_same_env(rec["provenance_at_start"], prov)
    return rec


def genome_file(run: int, kind: str) -> Path:
    return OUT / "genomes" / f"s_dense-run{run:02d}-{kind}.npz"


def cmd_replay(args):
    REGISTERED["cap_gpu_hours"] = REGISTERED["replay"]["cap_total_gpu_hours"]
    s_dense = [r["run"] for r in pilot_runs() if r["arm"] == "s_dense"]

    def body(ctx):
        inputs = check_inputs()
        pilot = ctx.earlier["pilot"]
        dev = ctx.args.device
        P_ = REGISTERED["pilot"]
        cfg = cfg_for("shared", P_["W"])
        con, l1 = load_connectome(), A.load_l1()
        cx = AS.context(con, l1, cfg.brain)
        learn = learning_ids()
        runs = [r for r in pilot_runs() if r["arm"] == "s_dense"]
        pop = cfg.evo.population
        draws = {r["run"]: AS.draw("s_dense", cx, np.random.default_rng([r["seed"], 0xE3C]), pop) for r in runs}
        sc = AS.arm_scales("s_dense", cx)
        org = cx["dense"]
        if ctx.doc["resolved_config_sha256"] != pilot["resolved_config_sha256"]:
            raise SystemExit("the task configuration differs from the pilot's: not a replay")
        want = {r["run"]: r["best_sha256"] for r in pilot["arms"]["s_dense"]["runs"]}
        live, files, probes, last_write = [], [], {}, [0.0]

        def progress() -> dict:
            got = {str(x.spec.run): [g["best_sha256"] for g in x.log] for x in live}
            return {"replay": {"best_sha256": got, "hashes_so_far": compare_hashes(
                        [got[str(x.spec.run)] for x in live], [want[x.spec.run][:len(x.log)] for x in live]),
                        "genome_files": files}, "probes": probes}

        def write_partial(force=False):
            if force or time.monotonic() - last_write[0] >= 60:
                E.write_atomic(E.partial_path("replay"), {"stage": "replay", **progress()})
                last_write[0] = time.monotonic()

        def check():
            ctx.cap.check()
            write_partial()

        def on_checkpoint(records, g):
            live[:] = records
            write_partial(force=True)

        ctx.salvage = progress
        # the pilot's S-dense batch, unchanged: same draws, masks, ids, schedule and composition
        recs = EV.evolve_batch(cfg, org.iface, BrainSpec.from_connectome(org.ext),
                               [EV.RunSpec(r["run"], r["seed"], 0.0) for r in runs], generations=P_["G"],
                               checkpoint_every=P_["checkpoint_every"], validation_ids=learn, world_seed=seed(),
                               id_base=P_["train_base"], id_span=P_["train_span"], device=dev, check=check,
                               category=acct.category, initial=lambda r: draws[r.run], mutation_scales=lambda r: sc,
                               on_checkpoint=on_checkpoint)
        live[:] = recs
        best = {str(rec.spec.run): [g["best_sha256"] for g in rec.log] for rec in recs}
        hashes = compare_hashes([best[str(rec.spec.run)] for rec in recs], [want[rec.spec.run] for rec in recs])
        for rec in recs:
            for g in (rec.final, *rec.candidates):
                assert_frozen(draws[rec.spec.run], g, sc)
        for rec in recs:
            i = rec.spec.run
            for kind, g, meta in (("final", rec.final, {"generation": P_["G"] - 1}),
                                  ("candidates", Genome.cat(rec.candidates),
                                   {"generations": [c["generation"] for c in rec.checkpoints]})):
                p = save_population(genome_file(i, kind), g, cfg=cfg, run=i, stage="replay", **meta)
                files.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "run": i, "kind": kind,
                              "sha256": [genome_hash(g, k) for k in range(g.n_strains)]})
        # the probes, on the pilot block: intact and with the noses removed
        champs = Genome.cat([rec.candidates[-1] for rec in recs])
        names = [f"s_dense_{rec.spec.run}" for rec in recs]
        w2 = w2_alone(con, cfg.brain)
        write_partial(force=True)
        with acct.category("probe"):
            for cond, f in (("intact", lambda i: i), ("noses_removed", AT.without_scent)):
                ctx.cap.check()
                got = play_recorded(cfg, f(org.iface), Brain(champs if str(dev) == "cpu" else EV.moved(champs, dev)),
                                    len(names), learn, dev)
                for k, nm in enumerate(names):
                    probes.setdefault(nm, {})[cond] = got["strains"][k]
                for nm, o in (("seed", cx["seed"]), ("w2_alone", w2)):
                    ctx.cap.check()
                    got = play_recorded(cfg, f(o.iface), MO.brain(o, dev), 1, learn, dev)
                    probes.setdefault(nm, {})[cond] = got["strains"][0]
        for nm in ("seed", "w2_alone", *names):
            a, b = probes[nm]["intact"]["visits"], probes[nm]["noses_removed"]["visits"]
            probes[nm]["retained_fraction"] = None if a <= 0 else b / a
        pilot_final = {f"s_dense_{r['run']}": r["final_generation_best"]["per_maze"]["visits"]
                       for r in pilot["arms"]["s_dense"]["runs"]}
        checks = {nm: probes[nm]["intact"]["visits_per_maze"] == pilot_final[nm] for nm in names}
        checks["w2_alone"] = probes["w2_alone"]["intact"]["visits_per_maze"] == pilot["references"]["w2_alone"]["per_maze"]["visits"]
        checks["seed"] = probes["seed"]["intact"]["visits_per_maze"] == pilot["references"]["seed"]["per_maze"]["visits"]
        # W2 with a constant turn bias: a scent-free reference (Fable's), swept over resting turns
        rests = REGISTERED["replay"]["turn_sweep"]
        orgs = [w2_turn(con, cfg.brain, r) for r in rests]
        gs = Genome.cat([o.genome for o in orgs])
        with acct.category("probe"):
            ctx.cap.check()
            got = play_recorded(cfg, orgs[0].iface, Brain(gs if str(dev) == "cpu" else EV.moved(gs, dev)), len(rests),
                                learn, dev)
        sweep = [{"resting_turn": r, **{k: v for k, v in s.items() if not k.endswith("per_maze")}}
                 for r, s in zip(rests, got["strains"])]
        ref = resting_turn(cx["seed"], cfg)
        turns = generation0_offsets(champs, org, cfg, ref=ref)
        return {"fixed_inputs": inputs,
                "replay": {"runs": [rec.spec.run for rec in recs], "hashes": hashes, "best_sha256": best,
                           "description": "replay" if hashes["all_match"] else
                           "exploratory retraining (the hashes differ from the pilot's; D205)",
                           "genome_files": files,
                           "composition": [len(recs) * pop, P_["W"], REGISTERED["colony"]]},
                "probes": probes, "intact_matches_pilot": checks, "turn_sweep": sweep,
                "champion_turn_offsets": turns["turn_offset"], "champion_K_D_A_at_q0": turns["K_D_A_at_q0"],
                "consequence": consequence(probes, names),
                "pilot_commit": pilot["provenance_at_start"]["git_commit"],
                "definitions": {"coverage": "intact; each wey's share of the 25 cells, averaged over weys and mazes",
                                "tour_match": "intact; directed moves at lag 48, averaged over weys with more than "
                                              "48 moves", "noses_removed": "the four A/B nose channels at gain 0; "
                                              "the relays' source-occupancy inputs and W2's collision stay on"},
                "note": "exploratory (D205): the pilot's S-dense batch replayed, and its champions probed"}

    return E.run_stage(args, "replay", lambda a, prov: {"pilot": require_pilot(a, prov)}, body,
                       local_files=[genome_file(r, k) for r in s_dense for k in ("final", "candidates")])


def use_smoke(args) -> None:
    global EXP, OUT, SMOKE
    EXP = OUT = ROOT / "runs" / "e3c-smoke"
    SMOKE = True
    R = REGISTERED
    R["H"] = 120
    R["ga"].update(population=4, elites=1, truncation=2)
    R["pilot"].update(runs_per_arm=1, G=3, W=2, checkpoint_every=2, train_base=9_100_000, train_span=1000)
    configure()
    stage = getattr(args, "command", "pilot") if args is not None else "pilot"
    for f in (E.record_path(stage), E.marker_path(stage), E.partial_path(stage)):
        if EXP in f.parents:
            f.unlink(missing_ok=True)


COMMANDS = {"pilot": cmd_pilot, "replay": cmd_replay}


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
    COMMANDS[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    if any(a == "--out" or a.startswith("--out=") for a in sys.argv[1:]):
        raise SystemExit("--out is not accepted: E3c writes only to its own folders (D195)")
    smoke = "--smoke" in sys.argv
    out_dir = ROOT / "runs" / ("e3c-smoke" if smoke else "e3c")
    try:
        run_script(main, out_default=str(out_dir), default="measure", name="e3c")
    finally:
        agg = out_dir / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
