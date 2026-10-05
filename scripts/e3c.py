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
from wormwars.e3 import e3c_formal as FO  # noqa: E402
from wormwars.e3 import e3c_stats as ES  # noqa: E402
from wormwars.evo.genomes import genome_hash, load_population, save_population  # noqa: E402


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
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", DESIGN, *FIXED,
           "experiments/E3-ab-organism/E3c/PREREGISTRATION.md"]
SMOKE = False

STAGES = ["pilot", "replay", "project", "g-e", "train-smod", "train-sdense", "train-psel", "champions", "evaluate", "report"]
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
    "formal": {"binding_commit": "69d7cd5ec9a0c77e094af903e754a3c881626394", "G": FO.G, "W": FO.W,
               "blocks": {k: list(v) for k, v in FO.BLOCKS.items()}, "train": dict(FO.TRAIN),
               "bench_train": dict(FO.BENCH_TRAIN), "turn_grid": list(FO.TURN_GRID), "cap_total_gpu_hours": 30.0,
               "pinned": {"experiments/E4s-stereo-module/E4s-0/module.json":
                          "9613cd155a20ed2cfb891c1bd10fed16814f24a04f912a1940524f2378e877d4",
                          "experiments/E3-ab-organism/E3c/pilot.json":
                          "6f6402ebecdf34633a77f8e4df97f8cf9a1e86316179116a63a668286d9ee41e",
                          "experiments/E3-ab-organism/E3b-1/train-tf.json":
                          "68f485107eefb9609d192b50b7e227c50732e6c1159cd656d2118d05ba05f01b",
                          "experiments/E3-ab-organism/E3b-1/maze-reference.json":
                          "11b726a05ef5e0ff5b6d6a01d4eb59abc51a48b516c785cf35151fc9e0e6358d"},
               "amended_engine_files": [], "bootstrap_resamples": 10_000,
               "registered_text_sha256": "553f253d260b80638d9ef72d4654f2ef78372e960ea31d62d04345098d8c3397",
               "bootstrap_seeds": {"contrast": 20_261_007, "seed_loss": 20_261_008},
               "smoke_runs": {"s": 2, "p_sel": 1}},
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


def play_recorded(cfg, iface, brain, n_strains: int, ids, dev, access: str = "shared", keep_paths: bool = False) -> dict:
    """Every strain on every maze at episode 0 under shared trails (play_batch's layout), with each wey's cell
    recorded: the visits, and per wey the coverage of the c × c cells and the tour match."""
    from wormwars.e3 import maze_world as MW_
    ids = np.asarray(ids)
    S, n = n_strains, len(ids)
    strain_of = torch.as_tensor(np.repeat(np.arange(S), n), device=dev).view(-1, 1)
    w = MW_.MazeWorld(cfg, iface, brain, strain_of, run_seed=seed(), world_ids=np.tile(ids, S), device=dev,
                      access=access)
    c = REGISTERED["c"]
    rec = CellRecorder(c)
    w.recorder = rec
    w.run()
    ev = w.task_events()
    ev = {k: (v.reshape(S, n, *v.shape[1:]) if isinstance(v, np.ndarray) and v.shape[:1] == (S * n,) else v)
          for k, v in ev.items()}
    allout = outcomes(ev, int(cfg.world.max_ticks))
    visits = allout["visits"]  # [S, n]
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
        out.append({**{f"{m}_per_maze": np.round(allout[m][s], 6).tolist()
                       for m in ("legs", "later_leg_rate", "unvisited_share", "round_trip_share")},
                    **{m: float(allout[m][s].mean()) for m in ("legs", "later_leg_rate", "unvisited_share", "round_trip_share")},
                    "sample_paths": [path(s * n + m, j) for m in range(min(4, n)) for j in range(2)],
                    "tour_match_best_lag": _nan_to_none(float(np.nanmean(tb[sl])) if np.isfinite(tb[sl]).any()
                                                        else float("nan")),"visits": float(visits[s].mean()), "visits_per_maze": np.round(visits[s], 6).tolist(),
                    "coverage": float(cov[sl].mean()), "coverage_per_maze": np.round(cov[sl].mean(axis=1), 6).tolist(),
                    "tour_match": _nan_to_none(float(np.nanmean(t)) if np.isfinite(t).any() else float("nan")),
                    "tour_match_per_maze": [_nan_to_none(float(np.nanmean(r)) if np.isfinite(r).any() else float("nan"))
                                            for r in t]})
    res = {"strains": out}
    if keep_paths:  # every wey's moves and their ticks, flattened with offsets: [worlds, weys] → a slice
        cells_l, ticks_l, offs = [], [], np.zeros(cells.shape[:2] + (2,), dtype=np.int64)
        pos = 0
        for i in range(cells.shape[0]):
            for j in range(cells.shape[1]):
                q = cells[i, j]
                keep = np.concatenate([[True], q[1:] != q[:-1]])
                mv, tk = q[keep].astype(np.int16), np.flatnonzero(keep).astype(np.int32)
                offs[i, j] = (pos, pos + len(mv))
                pos += len(mv)
                cells_l.append(mv)
                ticks_l.append(tk)
        res["paths"] = {"cells": np.concatenate(cells_l), "ticks": np.concatenate(ticks_l), "offsets": offs,
                        "world_ids": np.tile(np.asarray(ids), S), "strain_of_world": np.repeat(np.arange(S), n)}
    return res


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


# ============================================================================== the formal stages (PREREGISTRATION.md, bound at 69d7cd5; Amendment 1)

FORMAL_STAGES = ["project", "g-e", "train-smod", "train-sdense", "train-psel", "champions", "evaluate", "report"]
STAGE_ARM = {"train-smod": "s_mod", "train-sdense": "s_dense", "train-psel": "p_sel"}
ARM_STAGE = {v: k for k, v in STAGE_ARM.items()}
# (prerequisites that must be completed, prerequisites that may also be final-stopped or cap-stopped: Amendment 1)
REQUIRES = {"project": ([], []), "g-e": (["project"], []),
            "train-smod": (["project", "g-e"], []), "train-sdense": (["project", "g-e"], ["train-smod"]),
            "train-psel": (["project", "g-e"], ["train-sdense"]),
            "champions": (["project", "g-e"], ["train-smod", "train-sdense", "train-psel"]),
            "evaluate": (["project"], ["champions"]),
            "report": (["project"], ["train-smod", "train-sdense", "train-psel", "champions", "evaluate"])}
PREREG = "experiments/E3-ab-organism/E3c/PREREGISTRATION.md"
E3B1_DIR = ROOT / "experiments" / "E3-ab-organism" / "E3b-1"
E3B1_GENOMES = ROOT / "runs" / "e3b1" / "genomes"


def formal_ids(block: str) -> np.ndarray:
    return np.arange(*REGISTERED["formal"]["blocks"][block])


def formal_plan_from(project: dict) -> dict:
    return project["admission"]["plan"]


def formal_runs(plan: dict) -> dict:
    if SMOKE:
        n = {"s_mod": REGISTERED["formal"]["smoke_runs"]["s"], "s_dense": REGISTERED["formal"]["smoke_runs"]["s"],
             "p_sel": REGISTERED["formal"]["smoke_runs"]["p_sel"]}
        return {arm: [{"arm": arm, "run": r, "seed": FO.RUN_SEED_BASE + r} for r in list(FO.ARM_RUNS[arm])[:n[arm]]]
                for arm in FO.ARM_RUNS}
    return FO.runs(plan)


def formal_gens() -> list:
    G = REGISTERED["formal"]["G"]
    return [g for g in FO.checkpoint_generations() if g < G - 1] + [G - 1]


def engine_diff() -> list:
    """The name-status diff from the binding commit under the engine paths (§12)."""
    out = E.reg.git("diff", "--name-status", REGISTERED["formal"]["binding_commit"], "HEAD", "--", "wormwars",
                    "configs", "requirements.txt", root=ROOT)
    return [tuple(line.split("\t", 1)) for line in out.splitlines() if line.strip()]


def registered_text_sha() -> str:
    """The pre-registration's registered text, everything before §14's amendments (CRLF → LF)."""
    t = (ROOT / PREREG).read_bytes().replace(b"\r\n", b"\n")
    i = t.find(b"## 14. Amendments")
    return hashlib.sha256(t[:i] if i >= 0 else t).hexdigest()


def _provenance_with_freeze(orig):
    def prov(guarded, root=None):
        p = orig(guarded, root)
        try:
            fr = FO.engine_freeze(engine_diff(), set(REGISTERED["formal"]["amended_engine_files"]))
        except Exception as e:  # noqa: BLE001 (recorded, then refused by the stage's requirement)
            fr = {"changed": [["error", f"{type(e).__name__}: {e}"]], "passes": False}
        return {**p, "binding_commit": REGISTERED["formal"]["binding_commit"], "engine_freeze": fr,
                "registered_text_sha256": registered_text_sha()}
    return prov


def require_engine(args, prov) -> None:
    fr = prov.get("engine_freeze") or {"passes": False, "changed": [["missing", "no engine-freeze record"]]}
    if E.formal(args) and not fr["passes"]:
        raise SystemExit(f"the engine changed since the binding commit (§12): {fr['changed'][:5]}")
    if E.formal(args) and prov.get("registered_text_sha256") != REGISTERED["formal"]["registered_text_sha256"]:
        raise SystemExit("the pre-registration's registered text (before §14) differs from the bound text")


def check_pinned() -> dict:
    got = {}
    for rel, want in REGISTERED["formal"]["pinned"].items():
        h = hashlib.sha256((ROOT / rel).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if h != want:
            raise SystemExit(f"{rel} has changed (sha256 {h}): refusing to run (§2)")
        got[rel] = h
    return got


def require_record(args, prov, stage: str, stopped_ok: bool) -> dict:
    """An earlier stage's record: completed; or, when `stopped_ok` (Amendment 1), also final-stopped (its rerun
    used) or stopped by the cap, which can never be rerun. A stopped record is read through its salvage."""
    try:
        return E.require_earlier(args, prov, stage, final_ok=stopped_ok)
    except SystemExit:
        path = E.record_path(stage)
        if not (stopped_ok and path.exists()):
            raise
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("outcome") != E.OUTCOMES["cap"]:
            raise
        if E.formal(args):
            if not args.smoke:
                E.require_committed(path)
            E.reg.require_same_code(rec["provenance_at_start"]["git_commit"], GUARDED)
            E.reg.require_same_env(rec["provenance_at_start"], prov)
        return rec


def formal_requires(stage: str):
    must, may = REQUIRES[stage]

    def req(args, prov):
        require_engine(args, prov)
        got = {s: E.require_earlier(args, prov, s) for s in must}
        for s in may:
            if stage == "report" and not E.record_path(s).exists() and not E.marker_path(s).exists():
                got[s] = None  # never started, e.g. after the cap was reached (Amendment 1)
            else:
                got[s] = require_record(args, prov, s, stopped_ok=True)
        if "project" in got and stage != "g-e" and not got["project"]["admission"]["admitted"]:
            raise SystemExit("project's projection did not fit even after every cut: E3c does not start (§10)")
        if "g-e" in got and not got["g-e"].get("passed"):
            raise SystemExit("g-e did not pass: no training stage starts, and the owner is asked (§5)")
        return got
    return req


def _sync(dev):
    if str(dev).startswith("cuda"):
        torch.cuda.synchronize()


def _timed(fn, dev) -> float:
    _sync(dev)
    t0 = time.perf_counter()
    fn()
    _sync(dev)
    return time.perf_counter() - t0


def _formal_cfg():
    return cfg_for("shared", REGISTERED["formal"]["W"])


def _org(arm, cx):
    return cx["dense"] if arm == "s_dense" else cx["seed"]


def _on(g, dev):
    return g if str(dev) == "cpu" else EV.moved(g, dev)


class Progress:
    """A stage's durable progress: written at once on demand and at least once a minute; also the salvage."""

    def __init__(self, ctx, state: dict):
        self.ctx, self.state, self.last = ctx, state, 0.0
        ctx.salvage = lambda: dict(self.state)

    def write(self, force=False):
        if force or time.monotonic() - self.last >= 60:
            E.write_atomic(E.partial_path(self.ctx.doc["stage"]), {"stage": self.ctx.doc["stage"], **self.state})
            self.last = time.monotonic()

    def check(self):
        self.ctx.cap.check()
        self.write()


# ---------------------------------------------------------------------------------------------- project

def bench_train_ids(n_runs: int) -> list:
    bt = REGISTERED["formal"]["bench_train"]
    return [int(x) for k in range(n_runs) for g in range(3)
            for x in EV.train_ids(1_390_000 + k, g, REGISTERED["formal"]["W"], bt["base"], bt["span"])]


def cmd_project(args):
    def body(ctx):
        inputs = check_pinned()
        dev = ctx.args.device
        cfg = _formal_cfg()
        con, l1 = load_connectome(), A.load_l1()
        cx = AS.context(con, l1, cfg.brain)
        bench = formal_ids("benchmark")
        b128 = bench[: len(bench) // 2]
        pop = cfg.evo.population
        n_s, n_s_cut, n_p, n_p_cut = (2, 1, 1, 1) if SMOKE else (8, 6, 4, 2)
        ctx.doc["mazes"] = preflight(list(formal_ids("validation")) + list(formal_ids("learning"))
                                     + list(formal_ids("test")) + list(bench) + bench_train_ids(n_s))
        t = {}
        prog = Progress(ctx, {"timings_seconds": t})

        def gen_seconds(arm, n_runs):
            org = _org(arm, cx)
            specs = [EV.RunSpec(900 + k, 1_390_000 + k, 0.0) for k in range(n_runs)]
            sc = AS.arm_scales(arm, cx)
            draws = {s.run: AS.draw(arm, cx, np.random.default_rng([s.run_seed, 0xE3C]), pop) for s in specs}
            bt = REGISTERED["formal"]["bench_train"]
            recs = EV.evolve_batch(cfg, org.iface, BrainSpec.from_connectome(org.ext), specs, generations=3,
                                   checkpoint_every=10 ** 6, validation_ids=bench[:1], world_seed=seed(),
                                   id_base=bt["base"], id_span=bt["span"], device=dev, check=prog.check,
                                   category=acct.category, initial=lambda r: draws[r.run], mutation_scales=lambda r: sc)
            return float(recs[0].log[1]["batch_seconds"])  # generation 1: no checkpoint

        with acct.category("calibration"):
            for key, arm, n in (("train_s", "s_dense", n_s), ("train_s_cut", "s_dense", n_s_cut),
                                ("train_psel", "p_sel", n_p), ("train_psel_cut", "p_sel", n_p_cut)):
                t[key] = gen_seconds(arm, n)
                prog.write(force=True)
            g = AS.draw("s_dense", cx, np.random.default_rng(7), 32)
            org = cx["dense"]
            for r in (8, 6, 4, 2):
                prog.check()
                gg = g.select(list(range(r)))
                t[f"checkpoint_{r}"] = _timed(lambda: MR.play_batch(cfg, org.iface, Brain(_on(gg, dev)), np.arange(r), b128,
                                                                   seed(), dev, access="shared"), dev)
            prog.check()
            t["champion_chunk"] = _timed(lambda: MR.play_batch(cfg, org.iface, Brain(_on(g, dev)), np.arange(32), b128,
                                                               seed(), dev, access="shared"), dev)
            g8 = g.select(list(range(8)))
            prog.check()
            t["eval_chunk"] = _timed(lambda: play_recorded(cfg, org.iface, Brain(_on(g8, dev)), 8, bench, dev), dev)
            prog.check()
            t["eval_single"] = _timed(lambda: play_recorded(cfg, cx["seed"].iface, MO.brain(cx["seed"], dev), 1, bench, dev), dev)
        # earlier attempts plus this stage's own time so far (CapClock.spent_hours counts only the former)
        spent = ctx.cap.spent_hours() + (time.perf_counter() - ctx.cap.t_start) / 3600
        remaining = REGISTERED["formal"]["cap_total_gpu_hours"] - spent
        adm = FO.admit(t, remaining)
        prog.state.update({"fixed_inputs": inputs, "spent_hours_at_decision": spent, "admission": adm})
        return {"fixed_inputs": inputs, "timings_seconds": t, "spent_hours_at_decision": spent,
                "projection_hours": {str(k): FO.projection_hours(t, FO.plan_after_cuts(k)) for k in range(4)},
                "admission": adm,
                "compositions": {"train_s": [8 * pop, 8, 8], "train_s_cut": [6 * pop, 8, 8], "train_psel": [4 * pop, 8, 8],
                                 "train_psel_cut": [2 * pop, 8, 8], "checkpoint": "[R, 128, 8]",
                                 "champion": [32, 128, 8], "evaluation": "[R, 256, 8]"}}

    return E.run_stage(args, "project", formal_requires("project"), body)


# ---------------------------------------------------------------------------------------------- g-e

def cmd_ge(args):
    def body(ctx):
        inputs = check_pinned()
        prog = Progress(ctx, {"fixed_inputs": inputs})
        B1 = _load("e3b1_for_e3c_ge", "e3b1.py")
        B1.SMOKE = SMOKE
        ref = json.loads((ROOT / B1.EQ_REFERENCE).read_text(encoding="utf-8"))
        with acct.category("calibration"):
            new = B1.EQ.run(ROOT, Path(ROOT / "data" / "cache" / "cook2019_herm.npz"))
            hook = B1.hook_leg(ctx.cap)
            mazes = B1.maze_leg()
        cpu = B1.EQ.compare(ref, new)
        prog.state.update(cpu=cpu, snapshot_hook=hook, mazes=mazes)
        prog.write(force=True)
        with acct.category("calibration"):
            gpu = {"skipped": "smoke"} if SMOKE else B1.gpu_leg(ctx.args.device, ctx.cap)
        prog.state.update({"passed": B1.ge_passed(cpu, gpu, hook, mazes, smoke=SMOKE), "gpu": gpu,
                           "note": "E3b-1's three legs at E3c's formal commit (§5); P-joint trained at f881308"})
        return dict(prog.state)

    return E.run_stage(args, "g-e", formal_requires("g-e"), body)


# ---------------------------------------------------------------------------------------------- training (one stage per arm)

def formal_genome_file(arm: str, run: int, kind: str) -> Path:
    return OUT / "genomes" / f"formal-{arm}-run{run:02d}-{kind}.npz"


def check_consistency(inloop: dict, post: dict) -> dict:
    """The in-loop checkpoints (generations 0 and the last) against the post-hoc plays: the candidate hashes and the
    per-maze vectors must be equal; a mismatch refuses (both reviewers)."""
    out = {}
    for g, c in inloop.items():
        p = post.get(g)
        same = p is not None and c["sha256"] == p["sha256"] and list(c["validation_counts"]) == list(p["validation_counts"])
        out[str(g)] = bool(same)
        if not same:
            raise RuntimeError(f"generation {g}: the post-hoc checkpoint differs from the in-loop one (hash or per-maze)")
    return out


def _prior_training(stage: str, arm: str) -> dict | None:
    """Amendment 1: on a rerun, the stopped attempt's training of this arm, when all its runs completed every
    generation and their saved populations are on disk; else None."""
    for f in (E.attempt1(E.record_path(stage)), E.attempt1(E.partial_path(stage))):
        if f.exists():
            prev = json.loads(f.read_text(encoding="utf-8"))
            tr = (prev.get("arms") or {}).get(arm, {}).get("training")
            if tr and tr.get("complete"):
                return tr
    return None


def train_arm(ctx, arm: str, plan: dict) -> dict:
    stage = ctx.doc["stage"]
    dev = ctx.args.device
    cfg = _formal_cfg()
    H = int(cfg.world.max_ticks)
    con, l1 = load_connectome(), A.load_l1()
    cx = AS.context(con, l1, cfg.brain)
    org = _org(arm, cx)
    spec = BrainSpec.from_connectome(org.ext)
    learn = formal_ids("learning")
    gens = formal_gens()
    pop = cfg.evo.population
    G = REGISTERED["formal"]["G"]
    tr = REGISTERED["formal"]["train"]
    rs = formal_runs(plan)[arm]
    ctx.doc["mazes"] = preflight(list(learn) + [int(x) for r in rs for g in range(G)
                                                  for x in EV.train_ids(r["seed"], g, REGISTERED["formal"]["W"],
                                                                        tr["base"], tr["span"])])
    sc = AS.arm_scales(arm, cx)
    draws = {r["run"]: AS.draw(arm, cx, np.random.default_rng([r["seed"], 0xE3C]), pop) for r in rs}
    entry = {"composition": [len(rs) * pop, REGISTERED["formal"]["W"], REGISTERED["colony"]],
             "checkpoint_composition": [len(rs), len(learn), REGISTERED["colony"]], "training": None, "runs": []}
    prog = Progress(ctx, {"arms": {arm: entry}, "checkpoint_generations": gens})
    live = []

    def on_checkpoint(records, g):
        live[:] = records
        entry["in_progress"] = [{"run": x.spec.run, "generations": len(x.log)} for x in records]
        prog.write(force=True)

    prior = _prior_training(stage, arm) if ctx.doc.get("attempt") == 2 else None
    inloop = {}
    if prior is not None:  # Amendment 1: reuse the completed, hash-verified training of the stopped attempt
        try:
            finals, cands, logs = {}, {}, {}
            for r in prior["runs"]:
                i = r["run"]
                for kind in ("final", "candidates"):
                    f = next(x for x in r["genome_files"] if x["kind"] == kind)
                    src = E.attempt1(ROOT / f["path"]) if E.attempt1(ROOT / f["path"]).exists() else ROOT / f["path"]
                    g, _ = load_population(src, spec, cfg.brain)
                    if [genome_hash(g, k) for k in range(g.n_strains)] != f["sha256"]:
                        raise ValueError(f"{src.name} differs from its recorded hashes")
                    (finals if kind == "final" else cands)[i] = g
                logs[i] = r["log"]
                inloop[i] = {int(k): v for k, v in r["inloop_checkpoints"].items()}  # checked again below (both)
            entry["training_reused_from_attempt_1"] = True
        except (ValueError, KeyError, OSError, StopIteration) as e:  # Amendment 1, point 3: train again
            entry["reuse_refused"] = f"{type(e).__name__}: {e}"
            prior = None
            inloop = {}
    if prior is None:
        recs = EV.evolve_batch(cfg, org.iface, spec, [EV.RunSpec(r["run"], r["seed"], 0.0) for r in rs], generations=G,
                               checkpoint_every=10 ** 6, validation_ids=learn, world_seed=seed(), id_base=tr["base"],
                               id_span=tr["span"], device=dev, check=prog.check, category=acct.category,
                               initial=lambda r: draws[r.run], mutation_scales=lambda r: sc,
                               on_checkpoint=on_checkpoint, snapshot_at=tuple(gens))
        finals, cands, logs = {}, {}, {}
        for rec in recs:
            i = rec.spec.run
            for g in (rec.final, *rec.snapshots.values()):
                assert_frozen(draws[i], g, sc)
            picks = []
            for g in gens:
                snap = rec.final if g == G - 1 else rec.snapshots[g]
                k = FO.index_of_hash([genome_hash(snap, j) for j in range(snap.n_strains)], rec.log[g]["best_sha256"])
                picks.append(snap.select([k]))
            finals[i], cands[i], logs[i] = rec.final, Genome.cat(picks), rec.log
            inloop[i] = {c["generation"]: {"sha256": c["sha256"], "validation_counts": c["validation_counts"]}
                         for c in rec.checkpoints}
    # saved at once, before any further play (both reviewers)
    runs_out = []
    for r in rs:
        i = r["run"]
        files = []
        for kind, gg, meta in (("final", finals[i], {"generation": G - 1}), ("candidates", cands[i], {"generations": gens})):
            p = save_population(formal_genome_file(arm, i, kind), gg, cfg=cfg, run=i, stage=stage, **meta)
            files.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "kind": kind,
                          "sha256": [genome_hash(gg, k) for k in range(gg.n_strains)]})
        runs_out.append({"run": i, "seed": r["seed"], "generations": len(logs[i]), "completed": len(logs[i]) == G,
                         "log": logs[i], "genome_files": files, "learning_curve": [],
                         "inloop_checkpoints": {str(g): v for g, v in inloop[i].items()}})
    entry["training"] = {"complete": all(x["completed"] for x in runs_out), "runs": runs_out}
    entry["runs"] = runs_out
    live.clear()
    prog.write(force=True)
    # the checkpoints, played from the saved candidates (§5): each generation's best by training fitness
    with acct.category("holdout"):
        for j, g in enumerate(gens):
            prog.check()
            cat = Genome.cat([cands[r["run"]].select([j]) for r in rs])
            ev = MR.play_batch(cfg, org.iface, Brain(_on(cat, dev)), np.arange(len(rs)), learn, seed(), dev, access="shared")
            vis = outcomes(ev, H)["visits"]
            for k, ro in enumerate(runs_out):
                ro["learning_curve"].append({"generation": g, "validation_mean": float(vis[k].mean()),
                                             "validation_counts": FO_counts(vis[k]),
                                             "sha256": logs[ro["run"]][g]["best_sha256"]})
            prog.write(force=True)
    for ro in runs_out:  # always checked, a reused training included (both reviewers; Amendment 1's annotation)
        post = {c["generation"]: c for c in ro["learning_curve"]}
        ro["checkpoint_consistency"] = check_consistency(inloop[ro["run"]], post)
    prog.write(force=True)
    return {"arms": {arm: entry}, "checkpoint_generations": gens}


def FO_counts(v) -> list:
    """Per-maze visits as `evolve_batch` records them (`_counts`), so the in-loop and post-hoc vectors compare."""
    return EV._counts(np.asarray(v))


def cmd_train(stage: str):
    arm = STAGE_ARM[stage]

    def cmd(args):
        def body(ctx):
            inputs = check_pinned()
            plan = formal_plan_from(ctx.earlier["project"])
            return {"fixed_inputs": inputs, "plan": plan, **train_arm(ctx, arm, plan)}

        files = [formal_genome_file(arm, r["run"], k) for r in formal_runs(FO.PLAN_FULL)[arm] for k in ("final", "candidates")]
        return E.run_stage(args, stage, formal_requires(stage), body, local_files=files)
    return cmd


# ---------------------------------------------------------------------------------------------- champions

def pjoint_populations(cx, cfg, kind: str) -> dict:
    """P-joint's 8 populations at index 299 ("final") or 124 ("snap124"), checked against `train-tf.json`'s recorded
    hashes; a mismatch refuses (§2)."""
    rec = json.loads((E3B1_DIR / "train-tf.json").read_text(encoding="utf-8"))
    out = {}
    for r in rec["runs"]:
        i = int(r["run"])
        g, _ = load_population(E3B1_GENOMES / f"tf-run{i:02d}-{kind}.npz", cx["spec"], cfg.brain)
        want = r["final_sha256"] if kind == "final" else r["snapshot_sha256"]["124"]
        if [genome_hash(g, k) for k in range(g.n_strains)] != want:
            raise SystemExit(f"P-joint's run {i} {kind} population differs from train-tf.json: the stage refuses (§2)")
        out[i] = {"genome": g, "log": r["log"]}
    return out


def grafted_by_name(genome: Genome, ext, k: int) -> dict:
    g = genome.select([k])
    n0 = int(ext.meta["worm_neurons"])
    return {"edges": {f"{a}->{b}": float(w) for (a, b), w in MO.named_edges(g, ext).items()},
            "neurons": {ext.names[j]: {"tau": float(g.tau[0, j]), "bias": float(g.bias[0, j])} for j in range(n0, ext.n)},
            "sha256": genome_hash(g, 0)}


def champions_file(arm: str) -> Path:
    return OUT / "genomes" / f"formal-{arm}-champions.npz"


def trained_runs(rec: dict, arm: str) -> list:
    """The runs of a training record (completed or stopped) whose training completed every generation."""
    entry = (rec.get("arms") or {}).get(arm) or {}
    return [r for r in entry.get("runs", []) if r.get("completed")]


def cmd_champions(args):
    def body(ctx):
        inputs = check_pinned()
        dev = ctx.args.device
        cfg = _formal_cfg()
        H = int(cfg.world.max_ticks)
        con, l1 = load_connectome(), A.load_l1()
        cx = {**AS.context(con, l1, cfg.brain)}
        cx["spec"] = BrainSpec.from_connectome(cx["seed"].ext)
        val, learn = formal_ids("validation"), formal_ids("learning")
        pj_final = pjoint_populations(cx, cfg, "final")
        pj_124 = pjoint_populations(cx, cfg, "snap124")
        arms, published = {}, {}
        prog = Progress(ctx, {"arms": arms})

        def play(genomes, org, ids_):
            return outcomes(MR.play_batch(cfg, org.iface, Brain(_on(genomes, dev)), np.arange(genomes.n_strains), ids_,
                                          seed(), dev, access="shared"), H)["visits"]

        with acct.category("final"):
            for arm in ("s_mod", "s_dense", "p_sel", "p_joint"):
                org = _org(arm, cx)
                spec = BrainSpec.from_connectome(org.ext)
                if arm == "p_joint":
                    pops = {i: v["genome"] for i, v in pj_final.items()}
                else:
                    pops = {}
                    for r in trained_runs(ctx.earlier[ARM_STAGE[arm]], arm):
                        f = next(x for x in r["genome_files"] if x["kind"] == "final")
                        g, _ = load_population(ROOT / f["path"], spec, cfg.brain)
                        if [genome_hash(g, k) for k in range(g.n_strains)] != f["sha256"]:
                            raise SystemExit(f"{f['path']} differs from its recorded hashes")
                        pops[r["run"]] = g
                per_run, champs = [], []
                arms[arm] = {"runs": per_run}
                for i, g in sorted(pops.items()):
                    prog.check()
                    means = play(g, org, val).mean(axis=1)
                    k = FO.champion_index(means)
                    champs.append(g.select([k]))
                    per_run.append({"run": i, "validation_means": np.round(means, 6).tolist(), "champion_index": k,
                                    "champion_sha256": genome_hash(g, k)})
                    published[f"{arm}-run{i:02d}"] = grafted_by_name(g, org.ext, k)
                    save_population(champions_file(arm), Genome.cat(champs), cfg=cfg, stage="champions", arm=arm,
                                    runs=[x["run"] for x in per_run])  # the champions so far, saved with each chunk
                    prog.write(force=True)
            grid = REGISTERED["formal"]["turn_grid"]
            orgs = [w2_turn(con, cfg.brain, r) for r in grid]
            prog.check()
            tv = play(Genome.cat([o.genome for o in orgs]), orgs[0], val).mean(axis=1)
            chosen = FO.choose_turn(grid, tv)
            prog.state["w2_turn"] = {"grid": grid, "block": "validation", "ids": [int(x) for x in val],
                                     "validation_means": np.round(tv, 6).tolist(), "chosen": chosen}
            pj_curve = {}
            for gen, pops in ((124, pj_124), (299, pj_final)):
                picks, shas = [], {}
                for i, v in sorted(pops.items()):
                    entry = v["log"][gen]
                    if entry["generation"] != gen:
                        raise SystemExit(f"P-joint run {i}'s log entry {gen} is generation {entry['generation']}")
                    k = FO.index_of_hash([genome_hash(v["genome"], j) for j in range(v["genome"].n_strains)],
                                         entry["best_sha256"])
                    picks.append(v["genome"].select([k]))
                    shas[i] = entry["best_sha256"]
                prog.check()
                vis = play(Genome.cat(picks), cx["seed"], learn)
                pj_curve[str(gen)] = {str(i): {"validation_mean": float(vis[k].mean()), "sha256": shas[i],
                                               "validation_counts": np.round(vis[k], 6).tolist()}
                                      for k, i in enumerate(sorted(pops))}
            prog.state["p_joint_learning_curve"] = pj_curve
            refs = {}
            for name, org in (("w2_alone", w2_alone(con, cfg.brain)), ("seed", cx["seed"])):
                prog.check()
                ev = MR.play(cfg, org.iface, lambda org=org: MO.brain(org, dev), learn, seed(), dev, access="shared")
                ev1 = {k: (v[None] if isinstance(v, np.ndarray) and v.shape[:1] == (len(learn),) else v) for k, v in ev.items()}
                refs[name] = float(outcomes(ev1, H)["visits"].mean())
            prog.state["learning_curve_references"] = refs
        pub = EXP / "champions-grafted.json"
        E.write_atomic(pub, {"note": "every champion's grafted parameters by name (§6; D200)", "champions": published})
        prog.state.update({"fixed_inputs": inputs, "published": str(pub.relative_to(ROOT)).replace("\\", "/"),
                           "compositions": {"validation": "[32, 128, 8] per run",
                                            "w2_turn": [len(grid), len(val), REGISTERED["colony"]],
                                            "p_joint_points": [len(pj_final), len(learn), REGISTERED["colony"]]}})
        return dict(prog.state)

    files = [champions_file(a) for a in ("s_mod", "s_dense", "p_sel", "p_joint")]
    return E.run_stage(args, "champions", formal_requires("champions"), body, local_files=files)


# ---------------------------------------------------------------------------------------------- evaluate

def ab_distances(ids_) -> list:
    out = []
    for mid in ids_:
        mz, pl = MZ.maze_for(run_seed=seed(), maze_id=int(mid), episode=0, c=REGISTERED["c"], n_spawns=REGISTERED["spawns"])
        out.append(float(mz.free_distance(pl.a)[2 + 4 * pl.b[0], 2 + 4 * pl.b[1]]))
    return out


def r_shared(con, l1, bcfg):
    module = O.b_shared(l1)
    ext = G.graft_connectome(con, module)
    genome = C.carrier_genome(ext, module, bcfg, forward=MO.CARRIER_FORWARD, turn=MO.REST_TURN["W0"])
    return MO.maze_organism(con, MO.Seed("R-shared", module, ext, genome), "W2", bcfg)


def paths_file(name: str, cond: str) -> Path:
    return OUT / "paths" / f"formal-{name}-{cond}.npz"


def save_paths(name: str, cond: str, paths: dict) -> dict:
    """Every wey's cell path (moves and their ticks) in one condition, saved locally (Amendment 1), hashed."""
    p = paths_file(name, cond)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(p, **paths)
    return {"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "worlds_weys": list(paths["offsets"].shape[:2])}  # [worlds, weys], as paths_ok checks (Astra, D213)


def cmd_evaluate(args):
    def body(ctx):
        inputs = check_pinned()
        dev = ctx.args.device
        cfg = _formal_cfg()
        con, l1 = load_connectome(), A.load_l1()
        cx = AS.context(con, l1, cfg.brain)
        test = formal_ids("test")
        ch = ctx.earlier["champions"]
        plan = formal_plan_from(ctx.earlier["project"])
        out = {"fixed_inputs": inputs, "arms": {}, "references": {}, "ab_distance": ab_distances(test),
               "test_ids": [int(x) for x in test], "trails_off_run": plan["trails_off"],
               "compositions": {"champions": "[runs, 256, 8]", "references": [1, len(test), REGISTERED["colony"]]}}
        prog = Progress(ctx, out)
        prog.write(force=True)
        with acct.category("final"):
            refs = {"seed": cx["seed"], "w2_alone": w2_alone(con, cfg.brain), "r_shared": r_shared(con, l1, cfg.brain)}
            if "w2_turn" in ch:
                refs["w2_turn"] = w2_turn(con, cfg.brain, ch["w2_turn"]["chosen"])
            else:
                out["w2_turn_unavailable"] = "the champions record has no W2-turn choice"
            for name, org in refs.items():  # the references first: every reading needs P-fixed and W2 alone
                res = {"paths_files": {}}
                out["references"][name] = res
                conds = [("intact", lambda i: i, "shared")] + ([("noses_removed", AT.without_scent, "shared")] if name == "seed" else [])
                if plan["trails_off"] and name in ("seed", "w2_alone"):
                    conds.append(("trails_off", lambda i: i, "none"))
                for cond, f, access in conds:
                    prog.check()
                    got = play_recorded(cfg, f(org.iface), MO.brain(org, dev), 1, test, dev, access=access,
                                        keep_paths=cond != "trails_off")
                    res[cond] = got["strains"][0]
                    if "paths" in got:
                        res["paths_files"][cond] = save_paths(name, cond, got["paths"])
                    prog.write(force=True)
            for arm in ("s_mod", "s_dense", "p_sel", "p_joint"):
                runs_ = [r for r in (ch.get("arms") or {}).get(arm, {}).get("runs", [])]
                if not runs_:
                    out["arms"][arm] = {"runs": [], "unavailable": "no champions"}
                    continue
                org = _org(arm, cx)
                g, _ = load_population(champions_file(arm), BrainSpec.from_connectome(org.ext), cfg.brain)
                if [genome_hash(g, k) for k in range(g.n_strains)] != [r["champion_sha256"] for r in runs_]:
                    raise SystemExit(f"{arm}'s champions differ from the champions record")
                res = {"runs": [r["run"] for r in runs_], "paths_files": {}}
                out["arms"][arm] = res
                conds = [("intact", lambda i: i, "shared"), ("noses_removed", AT.without_scent, "shared")]
                if plan["trails_off"]:
                    conds.append(("trails_off", lambda i: i, "none"))
                for cond, f, access in conds:
                    prog.check()
                    got = play_recorded(cfg, f(org.iface), Brain(_on(g, dev)), g.n_strains, test, dev, access=access,
                                        keep_paths=cond != "trails_off")
                    res[cond] = got["strains"]
                    if "paths" in got:
                        res["paths_files"][cond] = save_paths(arm, cond, got["paths"])
                    prog.write(force=True)
                with acct.category("probe"):
                    turns = generation0_offsets(g, org, cfg, ref=resting_turn(cx["seed"], cfg))
                res["turn_offset"], res["K_D_A_at_q0"] = turns["turn_offset"], turns["K_D_A_at_q0"]
                prog.write(force=True)
        return dict(out)

    return E.run_stage(args, "evaluate", formal_requires("evaluate"), body)


# ---------------------------------------------------------------------------------------------- report

def _visits(entry) -> np.ndarray:
    return np.asarray(entry["visits_per_maze"], dtype=np.float64)


def _complete(entry, n: int) -> bool:
    return isinstance(entry, dict) and len(entry.get("visits_per_maze", [])) == n


def paths_ok(manifest, n_worlds: int) -> bool:
    """A path file exists, has its recorded sha256 and its registered dimensions (Astra, D212)."""
    if not manifest:
        return False
    f = ROOT / manifest["path"]
    if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest() != manifest["sha256"]:
        return False
    return list(manifest.get("worlds_weys", [])) == [n_worlds, REGISTERED["colony"]]


def contrast_readings(d: dict, run_visits: dict, avail: dict, seed_mean: float, w2: float) -> dict:
    """The primary contrasts as `e3c_stats.readings` computes them, with a contrast that cannot be read (too few
    runs) entering the family as unread: p = 1 in Holm, its interval level unchanged, nothing fictitious (both,
    D212). With both available it is `e3c_stats.readings` itself."""
    from scipy import stats as st
    if avail["Q1"] and avail["Q2"]:
        return ES.readings(d=d, seed_mean=seed_mean, run_visits=run_visits, w2_alone=w2)
    m_lo, m_hi = ES.margins(seed_mean)
    arms = {"Q1": ("s_mod", "s_dense"), "Q2": ("p_joint", "s_mod")}
    q1_floor = (avail["Q1"] and max(float(np.mean(run_visits["s_mod"])), float(np.mean(run_visits["s_dense"])))
                <= w2 + ES.FLOOR_MARGIN)
    pairs = {q: ((d[arms[q][0]], d[arms[q][1]]) if avail[q] and not (q == "Q1" and q1_floor) else None) for q in arms}
    res = ES.contrasts(pairs)
    out = {"margins": {"m_lo": m_lo, "m_hi": m_hi}, "seed_mean": seed_mean}
    for q, r in res.items():
        a, b = ES.NAMES[q]
        if pairs[q] is None:
            lab = "not read: both at the floor" if (q == "Q1" and q1_floor) else "not read: too few runs"
            out[q] = {**r, "label": lab, "exact": {"p": None, "label": lab}}
            continue
        x, y = pairs[q]
        p_exact = ES.permutation_p(x, y)
        rej = p_exact <= ES.ALPHA / 2
        side = a if np.mean(x) > np.mean(y) else b
        fails = {arm: ES.failed(run_visits[arm], w2) for arm in arms[q]}
        ok = {arm: np.asarray(dd)[np.asarray(run_visits[arm], dtype=np.float64) > w2 + ES.FLOOR_MARGIN]
              for arm, dd in zip(arms[q], (x, y))}
        lab = ES.label(r["estimate"], r["lo"], r["hi"], r["rejected"], m_lo=m_lo, m_hi=m_hi, a=a, b=b)
        out[q] = {**r, "label": f"approximate (model-based): {lab}", "label_unqualified": lab,
                  "exact": {"p": p_exact, "level": ES.ALPHA / 2, "rejected": rej,
                            "label": (f"distributions differ (exact test); observed mean higher for {side}" if rej
                                      else "no difference detected (exact)")},
                  "failed_runs": fails, "failed_runs_present": any(fails.values()),
                  "decomposition": ES.decomposition(ok[arms[q][0]], ok[arms[q][1]]),
                  "estimate_visits": r["estimate"] * seed_mean,
                  "mann_whitney_p": float(st.mannwhitneyu(x, y, alternative="two-sided").pvalue)}
    out["note"] = "an arm below 6 eligible runs: its contrasts are not read and enter Holm with p = 1 (§5, Amendment 1)"
    return out


def report_readings(ev: dict, ch: dict, trained: dict, project: dict, n_test: int | None = None, paths_check=None) -> dict:
    """§7's readings from the records only (one function; tested on synthetic records), with §5's eligibility:
    the registered maze count, the path files, and every unavailable input an explicit outcome."""
    from scipy import stats as st
    paths_check = paths_check or paths_ok
    n = n_test if n_test is not None else len(ev.get("test_ids") or [])
    refs = ev.get("references") or {}
    seed_entry = (refs.get("seed") or {}).get("intact")
    seed_pm = _visits(seed_entry) if _complete(seed_entry, n) else None
    seed_mean = float(seed_pm.mean()) if seed_pm is not None else float("nan")
    seed_ok = math.isfinite(seed_mean) and seed_mean > 0
    w2_entry = (refs.get("w2_alone") or {}).get("intact")
    w2 = float(_visits(w2_entry).mean()) if _complete(w2_entry, n) else float("nan")
    gens = trained.get("checkpoint_generations") or formal_gens()
    out = {"seed_mean": seed_mean, "w2_alone": w2, "n_test": n, "eligibility": {}}
    arms = {}
    for arm in ("s_mod", "s_dense", "p_sel", "p_joint"):
        a = (ev.get("arms") or {}).get(arm) or {}
        done = ({r["run"] for r in trained.get(arm, [])} if arm != "p_joint" else set(a.get("runs", [])))
        n_runs = len(a.get("runs", []))
        pf = a.get("paths_files") or {}
        paths_good = {c: paths_check(pf.get(c), n_runs * n) for c in ("intact", "noses_removed")}

        def at(key, k):
            xs = a.get(key) or []
            return xs[k] if k < len(xs) else None

        rows = []
        for k, run in enumerate(a.get("runs", [])):
            intact, removed = at("intact", k), at("noses_removed", k)
            rows.append({"run": run, "eligible": run in done and _complete(intact, n), "intact": intact,
                         "noses_removed": removed if _complete(removed, n) else None,
                         "paths_ok": paths_good["intact"] and paths_good["noses_removed"],
                         "turn_offset": at("turn_offset", k), "K_D": at("K_D_A_at_q0", k), "trails_off": at("trails_off", k)})
        arms[arm] = [r for r in rows if r["eligible"]]
        out["eligibility"][arm] = {"evaluated": len(rows), "eligible": len(arms[arm]),
                                   "excluded": [r["run"] for r in rows if not r["eligible"]], "paths_ok": paths_good}
    run_pm = {arm: (np.array([_visits(r["intact"]) for r in rows]) if rows else np.zeros((0, n))) for arm, rows in arms.items()}
    run_visits = {arm: (v.mean(axis=1) if len(v) else np.zeros(0)) for arm, v in run_pm.items()}
    # the primary contrasts
    if not seed_ok:
        lab = "not read: P-fixed's mean is not positive" if seed_pm is not None else "not read: P-fixed's play is unavailable"
        prim = {q: {"read": False, "label": lab, "exact": {"p": None, "label": lab}} for q in ("Q1", "Q2")}
    elif not math.isfinite(w2):
        prim = {q: {"read": False, "label": "not read: W2 alone's play is unavailable",
                    "exact": {"p": None, "label": "not read: W2 alone's play is unavailable"}} for q in ("Q1", "Q2")}
    else:
        d = {arm: (run_visits[arm] - seed_mean) / seed_mean for arm in arms}
        enough = {arm: len(arms[arm]) >= 6 for arm in ("s_mod", "s_dense", "p_joint")}
        avail = {"Q1": enough["s_mod"] and enough["s_dense"], "Q2": enough["p_joint"] and enough["s_mod"]}
        prim = contrast_readings({k: d[k] for k in ("s_mod", "s_dense", "p_joint")},
                                 {k: run_visits[k] for k in ("s_mod", "s_dense", "p_joint")}, avail, seed_mean, w2)
        for q, (a, b) in (("Q1", ("s_mod", "s_dense")), ("Q2", ("p_joint", "s_mod"))):
            if prim.get(q, {}).get("read"):
                fa, fb = ES.failed(run_visits[a], w2), ES.failed(run_visits[b], w2)
                prim[q]["failed_fisher_p"] = float(st.fisher_exact([[fa, len(run_visits[a]) - fa],
                                                                    [fb, len(run_visits[b]) - fb]])[1])
    out["primary"] = prim
    # the maze-paired bootstrap, each contrast on its own (P-fixed's mean and every d recomputed on each resample)
    out["bootstrap"] = {}
    for q, (a, b) in (("Q1", ("s_mod", "s_dense")), ("Q2", ("p_joint", "s_mod"))):
        if not (seed_ok and prim.get(q, {}).get("read")):
            out["bootstrap"][q] = "not computed: the contrast is not read"
            continue
        rng = np.random.default_rng(REGISTERED["formal"]["bootstrap_seeds"]["contrast"])  # the registered seed, fresh per contrast
        vals = []
        for _ in range(REGISTERED["formal"]["bootstrap_resamples"]):
            idx = rng.integers(0, n, n)
            sm = seed_pm[idx].mean()
            vals.append(((run_pm[a][:, idx].mean(axis=1) - sm) / sm).mean() - ((run_pm[b][:, idx].mean(axis=1) - sm) / sm).mean())
        out["bootstrap"][q] = {"lo": float(np.percentile(vals, 2.5)), "hi": float(np.percentile(vals, 97.5))}
    # the cost curve (§7.2); a run whose curve lacks a registered checkpoint is undefined there
    lcr = (ch or {}).get("learning_curve_references") or {}
    cost = {}
    if "w2_alone" in lcr and "seed" in lcr:
        lc_w2, lc_seed = lcr["w2_alone"], lcr["seed"]
        for arm in ("s_mod", "s_dense", "p_sel"):
            per, undefined = [], []
            for r in trained.get(arm, []):
                curve = {c["generation"]: c["validation_mean"] for c in r.get("learning_curve", [])}
                if any(g not in curve for g in gens):
                    undefined.append(r["run"])
                    continue
                row = {"run": r["run"]}
                for name, thr in (("w2_plus_1", lc_w2 + 1.0), ("seed", lc_seed)):
                    hit = [g for g in gens if curve[g] > thr]
                    row[name] = hit[0] if hit else float("inf")
                per.append(row)
            cost[arm] = {"runs": [{k: (None if v == float("inf") else v) for k, v in x.items()} for x in per],
                         "undefined_runs": undefined,
                         **{f"{t}_reached": sum(x[t] != float("inf") for x in per) for t in ("w2_plus_1", "seed")},
                         **{f"{t}_median": ES.censored_median([x[t] for x in per]) for t in ("w2_plus_1", "seed")}}
        fisher = {}
        for t in ("w2_plus_1", "seed"):
            a, b = cost["s_mod"], cost["s_dense"]
            na, nb = len(a["runs"]), len(b["runs"])
            fisher[t] = float(st.fisher_exact([[a[f"{t}_reached"], na - a[f"{t}_reached"]],
                                               [b[f"{t}_reached"], nb - b[f"{t}_reached"]]])[1]) if na and nb else None
        order = sorted(fisher, key=lambda t: 1.0 if fisher[t] is None else fisher[t])
        run_, adj = 0.0, {}
        for i, t in enumerate(order):
            run_ = max(run_, min(1.0, (len(order) - i) * (1.0 if fisher[t] is None else fisher[t])))
            adj[t] = run_
        thresholds = {"w2_plus_1": lc_w2 + 1.0, "seed": lc_seed}
    else:
        fisher, adj, thresholds = "not computed: the learning-curve references are unavailable", None, None
    curves = {arm: {str(r["run"]): [[c["generation"], c["validation_mean"]] for c in r.get("learning_curve", [])]
                    for r in trained.get(arm, [])} for arm in ("s_mod", "s_dense", "p_sel")}
    curves["p_joint"] = {g: {i: v["validation_mean"] for i, v in pts.items()}
                         for g, pts in ((ch or {}).get("p_joint_learning_curve") or {}).items()}
    out["cost_curve"] = {"arms": cost, "fisher_s_mod_vs_s_dense": fisher, "fisher_holm": adj, "thresholds": thresholds,
                         "learning_curves": curves,
                         "checkpoint_consistency": {arm: {str(r["run"]): r.get("checkpoint_consistency") for r in trained.get(arm, [])}
                                                    for arm in ("s_mod", "s_dense", "p_sel")}}
    # §7.3: nose dependence and the coverage hypothesis; a champion without its paths or noses-removed play is
    # undefined there, never dropped
    m_lo_visits = (ES.margins(seed_mean)[0] * seed_mean) if seed_ok else None

    def coverer(entry, retained):
        tm, c = entry.get("tour_match"), entry.get("coverage")
        if retained is None or tm is None or c is None:
            return None
        return bool(retained >= 0.9 and c >= 0.95 and tm >= 0.5)

    def loss_reading(L):
        if len(L) < 2:
            return {"loss_mean": float(L.mean()) if len(L) else None, "loss_ci95": "not computed: fewer than 2",
                    "no_material_loss": None}
        sd = L.std(ddof=1)
        ci = st.t.interval(0.95, len(L) - 1, loc=L.mean(), scale=sd / np.sqrt(len(L))) if sd > 0 else (L.mean(), L.mean())
        return {"loss_mean": float(L.mean()), "loss_ci95": [float(ci[0]), float(ci[1])],
                "no_material_loss": bool(m_lo_visits is not None and ci[1] < m_lo_visits)}

    nose, cover_lists = {}, {}
    for arm in ("s_mod", "s_dense", "p_sel", "p_joint"):
        rows = []
        for r in arms[arm]:
            va = float(_visits(r["intact"]).mean())
            if r["noses_removed"] is None or not r["paths_ok"]:
                rows.append({"run": r["run"], "intact": va, "noses_removed": None, "retained": None, "class": "undefined",
                             "coverage": None, "tour_match": None, "coverer": None, "loss": None, "maze_differences": None,
                             "why_undefined": "no complete noses-removed play" if r["noses_removed"] is None else "paths missing or altered"})
                continue
            vb = float(_visits(r["noses_removed"]).mean())
            ret = None if va <= 0 else vb / va
            rows.append({"run": r["run"], "intact": va, "noses_removed": vb, "retained": ret, "class": ES.nose_class(ret),
                         "coverage": r["intact"].get("coverage"), "tour_match": r["intact"].get("tour_match"),
                         "tour_match_best_lag": r["intact"].get("tour_match_best_lag"), "coverer": coverer(r["intact"], ret),
                         "loss": float((_visits(r["intact"]) - _visits(r["noses_removed"])).mean()),
                         "maze_differences": np.round(_visits(r["intact"]) - _visits(r["noses_removed"]), 6).tolist()})
        L = np.array([x["loss"] for x in rows if x["loss"] is not None])
        nose[arm] = {"champions": rows, "classes": {c: sum(x["class"] == c for x in rows)
                                                     for c in ("nose-independent", "partial", "nose-dependent", "undefined")},
                     "coverers": sum(x["coverer"] is True for x in rows), "coverers_undefined": sum(x["coverer"] is None for x in rows),
                     **loss_reading(L)}
        cover_lists[arm] = [x["coverer"] for x in rows]
    sref = refs.get("seed") or {}
    sp = sref.get("paths_files") or {}
    if seed_ok and _complete(sref.get("noses_removed"), n) and paths_check(sp.get("intact"), n) and paths_check(sp.get("noses_removed"), n):
        sa, sb = seed_pm, _visits(sref["noses_removed"])
        rng2 = np.random.default_rng(REGISTERED["formal"]["bootstrap_seeds"]["seed_loss"])
        lb = [float((sa[i] - sb[i]).mean()) for i in (rng2.integers(0, n, n) for _ in range(REGISTERED["formal"]["bootstrap_resamples"]))]
        ret = float(sb.mean() / sa.mean())
        ci = [float(np.percentile(lb, 2.5)), float(np.percentile(lb, 97.5))]
        nose["p_fixed"] = {"retained": ret, "class": ES.nose_class(ret), "coverer": coverer(sref["intact"], ret),
                           "loss_mean": float((sa - sb).mean()), "loss_ci95_bootstrap": ci,
                           "no_material_loss": bool(m_lo_visits is not None and ci[1] < m_lo_visits),
                           "maze_differences": np.round(sa - sb, 6).tolist()}
    else:
        nose["p_fixed"] = {"retained": None, "class": "undefined", "coverer": None}
    dep = {}
    for s_arm in ("s_mod", "s_dense"):
        x = [r["retained"] for r in nose["p_joint"]["champions"] if r["retained"] is not None]
        y = [r["retained"] for r in nose[s_arm]["champions"] if r["retained"] is not None]
        dep[s_arm] = ES.welch(x, y, level=0.95) if len(x) > 1 and len(y) > 1 else "not computed: fewer than 2"
    out["nose"] = nose
    out["coverage_hypothesis"] = ES.coverage_rule({k: cover_lists[k] for k in ("s_mod", "s_dense", "p_joint")})
    out["nose_dependence_p_joint_minus_s"] = dep
    qual = {arm: {"nose_classes": nose[arm]["classes"], "coverers": nose[arm]["coverers"], "eligible": len(arms[arm])}
            for arm in ("s_mod", "s_dense", "p_joint")}
    for q, pair in (("Q1", ("s_mod", "s_dense")), ("Q2", ("p_joint", "s_mod"))):
        if isinstance(prim.get(q), dict):
            prim[q]["qualifier"] = {a: qual[a] for a in pair}
    # descriptives (§7.4)
    out["references"] = {k: {c: {"visits": float(_visits(v[c]).mean()), "coverage": v[c].get("coverage"),
                                 "tour_match": v[c].get("tour_match")} for c in v if isinstance(v[c], dict) and "visits_per_maze" in v[c]}
                         for k, v in refs.items()}
    pj_mean = float(run_visits["p_joint"].mean()) if len(run_visits["p_joint"]) else None
    out["p_sel"] = {"above_floor": int(sum(run_visits["p_sel"] > w2 + 1.0)) if math.isfinite(w2) else None,
                    "eligible": len(arms["p_sel"]),
                    "runs": [{"run": r["run"], "visits": float(v), "minus_p_fixed": (float(v) - seed_mean) if seed_ok else None,
                              "minus_p_joint_mean": (float(v) - pj_mean) if pj_mean is not None else None}
                             for r, v in zip(arms["p_sel"], run_visits["p_sel"])]}
    abd = ev.get("ab_distance")
    out["per_champion"] = {arm: [{"run": r["run"],
                                  "spearman_with_seed": (float(st.spearmanr(_visits(r["intact"]), seed_pm).correlation)
                                                         if seed_pm is not None else None),
                                  "spearman_with_ab_distance": (float(st.spearmanr(_visits(r["intact"]), abd).correlation)
                                                                if abd and len(abd) == n else None),
                                  "turn_offset": r["turn_offset"], "K_D_A_at_q0": r["K_D"],
                                  **{k: r["intact"].get(k) for k in ("legs", "later_leg_rate", "unvisited_share", "round_trip_share")},
                                  "trails_off_visits": float(_visits(r["trails_off"]).mean()) if _complete(r["trails_off"], n) else None}
                                 for r in arms[arm]] for arm in arms}
    return out


def report_from(earlier: dict) -> dict:
    """The report from whatever records exist (Amendment 1): a stage that never ran, or whose record lacks what a
    reading needs, gives that reading an explicit "not read"."""
    trained = {arm: trained_runs(earlier[ARM_STAGE[arm]], arm) if earlier.get(ARM_STAGE[arm]) else []
               for arm in ARM_STAGE}
    trained["checkpoint_generations"] = formal_gens()
    inputs = {s: (earlier[s].get("outcome") if earlier.get(s) else "never started")
              for s in REQUIRES["report"][0] + REQUIRES["report"][1]}
    if not earlier.get("evaluate"):
        lab = "not read: evaluate did not run"
        return {"readings": {"primary": {q: {"read": False, "label": lab, "exact": {"p": None, "label": lab}} for q in ("Q1", "Q2")},
                             "cost_curve": {"learning_curves": {arm: {str(r["run"]): [[c["generation"], c["validation_mean"]]
                                                                                     for c in r.get("learning_curve", [])]
                                                                     for r in trained[arm]} for arm in ARM_STAGE}}},
                "inputs": inputs}
    return {"readings": report_readings(earlier["evaluate"], earlier.get("champions") or {}, trained, earlier["project"],
                                        n_test=len(formal_ids("test"))), "inputs": inputs}


def cmd_report(args):
    def body(ctx):
        return report_from(ctx.earlier)

    return E.run_stage(args, "report", formal_requires("report"), body)


def use_smoke(args) -> None:
    global EXP, OUT, SMOKE
    EXP = OUT = ROOT / "runs" / "e3c-smoke"
    SMOKE = True
    R = REGISTERED
    R["H"] = 120
    R["ga"].update(population=4, elites=1, truncation=2)
    R["pilot"].update(runs_per_arm=1, G=3, W=2, checkpoint_every=2, train_base=9_100_000, train_span=1000)
    R["formal"].update(G=12, W=2, blocks={"validation": [8000, 8002], "learning": [8002, 8004], "test": [8004, 8008],
                                         "benchmark": [8008, 8012]},
                       train={"base": 9_200_000, "span": 1000}, bench_train={"base": 9_300_000, "span": 1000},
                       bootstrap_resamples=200)
    configure()
    stage = getattr(args, "command", "pilot") if args is not None else "pilot"
    files = [E.record_path(stage), E.marker_path(stage), E.partial_path(stage)]
    files += [E.rerun_note(E.record_path(stage))] + [E.attempt1(f) for f in list(files)]
    if stage in STAGE_ARM:
        g = [formal_genome_file(STAGE_ARM[stage], r["run"], k) for r in formal_runs(FO.PLAN_FULL)[STAGE_ARM[stage]]
             for k in ("final", "candidates")]
        files += g + [E.attempt1(f) for f in g]
    for f in files:
        if EXP in f.parents:
            f.unlink(missing_ok=True)


COMMANDS = {"pilot": cmd_pilot, "replay": cmd_replay, "project": cmd_project, "g-e": cmd_ge,
            "train-smod": cmd_train("train-smod"), "train-sdense": cmd_train("train-sdense"),
            "train-psel": cmd_train("train-psel"),
            "champions": cmd_champions, "evaluate": cmd_evaluate, "report": cmd_report}


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
    if args.command in FORMAL_STAGES:
        REGISTERED["cap_gpu_hours"] = (float("inf") if args.command == "report"
                                       else REGISTERED["formal"]["cap_total_gpu_hours"])
        E.reg.provenance = _provenance_with_freeze(E.reg.provenance)
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
