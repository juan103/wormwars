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
from wormwars.evo.genomes import genome_hash  # noqa: E402


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

STAGES = ["pilot"]
REGISTERED = {
    "maze_seed": 1_180_000, "c": 5, "H": 2400, "colony": 8, "spawns": 4,
    "trail": {"mu": 0.01, "lam": 0.02, "delta": 0.05, "d0": 1.142},
    "ga": {"population": 32, "elites": 3, "truncation": 8,
           "mutation": {"w_sigma": 0.08, "tau_sigma": 0.15, "bias_sigma": 0.05, "p_mutate": 1.0}, "factor": AS.FACTOR},
    "pilot": {"runs_per_arm": 3, "G": 100, "W": 8, "checkpoint_every": 25, "learning": [7600, 7728],
              "train_base": 30_000_000, "train_span": 10_000_000, "run_seed_base": 1_200_000, "margin": 1.0},
    "smoke_ids": [8000, 8100],
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


def use_smoke(args) -> None:
    global EXP, OUT, SMOKE
    EXP = OUT = ROOT / "runs" / "e3c-smoke"
    SMOKE = True
    R = REGISTERED
    R["H"] = 120
    R["ga"].update(population=4, elites=1, truncation=2)
    R["pilot"].update(runs_per_arm=1, G=3, W=2, checkpoint_every=2, train_base=9_100_000, train_span=1000)
    configure()
    for f in (E.record_path("pilot"), E.marker_path("pilot"), E.partial_path("pilot")):
        if EXP in f.parents:
            f.unlink(missing_ok=True)


COMMANDS = {"pilot": cmd_pilot}


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
