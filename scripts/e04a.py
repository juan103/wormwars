"""04a: the evolved N2 navigation primitive (experiments/04a-navigation-primitive/PREREGISTRATION.md).

    python scripts/e04a.py project            # the budget projection, on smoke ids; writes projection.json
    python scripts/e04a.py train --batch A    # runs 0-7; needs the committed projection, within its limit
    python scripts/e04a.py train --batch B    # runs 8-15; needs batch A committed, the same code and environment
    python scripts/e04a.py evaluate           # once, on the hold-out; needs both training records committed
    python scripts/e04a.py train --batch A --smoke   # tiny sizes, ids 0-9 999, runs/e04a-smoke/
    python scripts/e04a.py train --batch A --rerun --reason "..."   # once, after a crash or interrupt

Every number the pre-registration fixes is in `REGISTERED`, and every rule is applied mechanically.
Task N and the controls are E1's, imported from `scripts/e1.py` unchanged; the guards are the shared
ones in `wormwars/registration.py`.

The experiment folder holds records only (JSON, and the hold-out's event tables). Genome files stay
local under `runs/e04a/`: generation 0 is drawn with weights proportional to the connectome's, which
this project does not redistribute (D028). The records carry every genome's hash.
"""

from __future__ import annotations

import argparse
import calendar
import dataclasses
import hashlib
import importlib
import importlib.util
import itertools
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import torch
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e1.task import HOLDOUT_04A_IDS  # noqa: E402
from wormwars.evo.genomes import genome_hash, load_population, save_genome, save_population  # noqa: E402
from wormwars.evo.rollout import rollout_brain  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402
from wormwars.world import arena_side  # noqa: E402

rollout_mod = importlib.import_module("wormwars.evo.rollout")  # the module: `wormwars.evo.rollout` is also a function

_spec = importlib.util.spec_from_file_location("e1_frozen", ROOT / "scripts" / "e1.py")
E1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E1)  # Task N's config, the controls and the secondary measures, unchanged

EXP = ROOT / "experiments" / "04a-navigation-primitive"
OUT = ROOT / "runs" / "e04a"
PREREG = "experiments/04a-navigation-primitive/PREREGISTRATION.md"
E1_FREEZE = ROOT / "experiments" / "E1-navigation" / "freeze.json"
E1_GATE = ROOT / "experiments" / "E1-navigation" / "gate.json"
E1_INPUTS = ["experiments/E1-navigation/freeze.json", "experiments/E1-navigation/gate.json"]
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PREREG, *E1_INPUTS]
SMOKE_IDS = np.arange(10_000)  # outside every E1 and 04a range
SMOKE = False

REGISTERED = {
    "world_seed": 1_100_001,  # E1's run seed: with the world id it generates each world and its targets
    "sigma": 6.0,  # E1's frozen σ
    "cap_gpu_hours": 6.0,  # every stage together, T0's accounting across attempts
    "evolution": {"population": 32, "elites": 3, "truncation": 8, "worlds_per_strain": 8, "generations": 1000,
                  "islands": 1, "mutation": {"w_sigma": 0.08, "g_sigma": 0.04, "tau_sigma": 0.15,
                                             "bias_sigma": 0.05, "p_mutate": 1.0}},
    # moved from 1 104 000 after the development pilot and projection used those seeds (review v2, D105)
    "runs": {"seed_base": 1_105_000, "shaping": 0.5, "shaped": list(range(12)), "unshaped": [12, 13, 14, 15],
             "batches": {"A": list(range(8)), "B": list(range(8, 16))}},
    # moved from 997 000 000 after the first smoke run drew 24 ids from that range (review v1, D104)
    "train_ids": {"base": 999_000_000, "span": 1_000_000},
    "validation": {"first": 998_000_000, "worlds": 256, "every": 25},
    "holdout": {"offset": 1000, "worlds": 1024},
    "rules": {
        "reliability": {"min_arrivals": 2, "required_share": 0.80},
        "baselines": ["constant", "random-walk", "wall-follower", "K"],
        "baseline_margin": 0.5,
        "cue": {"probe": "mirrored", "contrast": "0.5 x real - mirrored, per world", "required_lower_bound": 0.0},
        "cue_helps": {"probe": "constant", "contrast": "real - constant probe, per world", "margin": 0.5},
        "generation0_margin": 0.5,
        "interval": {"method": "paired percentile bootstrap over worlds, one-sided 95% lower bound",
                     "resamples": 10_000, "seed": 0},
    },
    "outcome": {"arm": "shaped", "required_passing_runs": 6,
                "interval": "exact (Clopper-Pearson) one-sided 95% lower bound on the passing share, reported"},
    "references": ["S-const", "S-const k<=32", "M-avg", "oracle"],
    # the projection's own seeds, never the formal ones; its training plan is derived from "evolution"
    "projection": {"generations_timed": 6, "seed_base": 1_109_000, "max_training_hours": 4.5},
    "rerun": ("once per stage, from scratch with the same seeds, after a crash, an interrupt or a kill, with the "
              "reason written first; never after the cap. The projection may also be rerun after an over-limit "
              "result, once an amendment in AMENDMENTS.md (not guarded) reduces the generations so that training "
              "fits the limit at that projection's own rates"),
    "rerun_kill_tail_seconds": 900,  # charged beyond a killed attempt's last file write (D107)
}
SMOKE_SEED_BASE = 1_108_000  # smoke runs' own seeds
OUTCOMES = {"passed": "04a: passed", "some": "04a: some runs passed ({k} of {n})", "none": "04a: not passed",
            "cap": "04a: not completed (the registered cap was reached)",
            "stopped": "04a: not completed (the run stopped)"}


# ----------------------------------------------------------------------------- paths and guards

def train_path(batch: str) -> Path:
    return EXP / f"train-{batch}.json"


def genomes_path(run: int) -> Path:
    return OUT / "genomes" / f"run{run:02d}-candidates.npz"


def clock() -> reg.CapClock:
    """The cap clock, after rebuilding the accounting's total from every attempt record, so a stage
    never starts on a stale or missing total (Fable, review v5)."""
    if (OUT / "compute").exists():
        acct.write_aggregate(OUT / "compute", OUT / "compute.json")
    return reg.CapClock(REGISTERED["cap_gpu_hours"], OUT / "compute.json")


def formal(args) -> bool:
    return not args.smoke or args.guarded


def preflight(device: str):
    con = load_connectome()
    iface = load_interface(con)
    if float(torch.ones(4, device=device).sum().item()) != 4.0:
        raise SystemExit(f"the device {device} failed a trivial operation")
    return con, iface


def config_sha256(cfg) -> str:
    return hashlib.sha256(json.dumps(cfg.to_dict(), sort_keys=True).encode()).hexdigest()


def e1_input_hashes() -> dict:
    return {p: reg.file_sha256(ROOT / p) for p in E1_INPUTS}


def task_config():
    """E1's Task N, exactly: built by E1's own function, checked against E1's gate record."""
    cfg = E1.config(REGISTERED["sigma"])
    want = json.loads(E1_GATE.read_text(encoding="utf-8"))["resolved_config"]
    if hashlib.sha256(json.dumps(want, sort_keys=True).encode()).hexdigest() != config_sha256(cfg):
        raise SystemExit("Task N's resolved configuration differs from E1's gate: refusing to run")
    if SMOKE:
        cfg.world.max_ticks = 40
    e, m = cfg.evo, REGISTERED["evolution"]
    e.population, e.elites, e.truncation = m["population"], m["elites"], m["truncation"]
    e.worlds_per_strain, e.generations, e.islands = m["worlds_per_strain"], m["generations"], m["islands"]
    for k, v in m["mutation"].items():
        setattr(cfg.mutation, k, v)
    return cfg


def run_specs(batch: str, seed_base: int | None = None) -> list[EV.RunSpec]:
    r = REGISTERED["runs"]
    base = r["seed_base"] if seed_base is None else seed_base
    return [EV.RunSpec(run=i, run_seed=base + i, shaping=r["shaping"] if i in r["shaped"] else 0.0)
            for i in r["batches"][batch]]


def training_plan() -> dict:
    """What the projection projects, derived from the registered evolution: both batches' generations
    and checkpoints."""
    g, every = REGISTERED["evolution"]["generations"], REGISTERED["validation"]["every"]
    per_run = len({x for x in range(g) if x % every == 0} | {g - 1})
    return {"generations": 2 * g, "checkpoints": 2 * per_run}


def validation_ids() -> np.ndarray:
    v = REGISTERED["validation"]
    return SMOKE_IDS[5000:5000 + v["worlds"]] if SMOKE else np.arange(v["first"], v["first"] + v["worlds"])


def holdout_ids() -> np.ndarray:
    h = REGISTERED["holdout"]
    return SMOKE_IDS[6000:6000 + h["worlds"]] if SMOKE else HOLDOUT_04A_IDS[h["offset"]:h["offset"] + h["worlds"]]


def projection_ids() -> tuple[np.ndarray, int, int]:
    """The projection always runs on smoke ids: training 0-4 999, validation from 5 000."""
    return SMOKE_IDS[5000:5000 + REGISTERED["validation"]["worlds"]], 0, 5000


def id_record(ids) -> dict:
    ids = np.asarray(ids)
    return {"first": int(ids[0]), "last": int(ids[-1]), "count": int(len(ids))}


def require_committed(path: Path, root: Path | None = None) -> None:
    """Tracked, unchanged, and (with the HEAD check in `require_formal`) pushed."""
    root = root or ROOT
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], cwd=root,
                             capture_output=True).returncode == 0
    if not tracked or reg.git("status", "--porcelain", "--", str(path), root=root):
        raise SystemExit(f"{Path(path).name} must be committed, unchanged and pushed first")


def load_record(path: Path, what: str) -> dict:
    if not path.exists():
        raise SystemExit(f"{what} has not run")
    return json.loads(path.read_text(encoding="utf-8"))


def require_earlier(args, prov: dict, path: Path, what: str, need: str = "completed") -> dict:
    """An earlier stage: completed, committed (formal), the same code and environment (guarded)."""
    rec = load_record(path, what)
    if rec.get("outcome") != need:
        raise SystemExit(f"{what} did not complete")
    if formal(args):
        if not args.smoke:
            require_committed(path)
        reg.require_same_code(rec["provenance_at_start"]["git_commit"], GUARDED)
        reg.require_same_env(rec["provenance_at_start"], prov)
    return rec


def write_atomic(path: Path, doc) -> None:
    reg.write_json(path, doc, atomic=True)


def attempt1(f: Path) -> Path:
    return f.with_name(f.stem.replace(".tmp", "") + "-attempt1" + f.suffix)


def rerun_plan(stage: str, files: list[Path], reason: str | None, over_limit_ok: bool = False) -> dict:
    """The registered rerun, checked but not yet applied: once per stage, after a crash, an interrupt or
    a kill (never the cap), with a reason. `files[0]` is the record and `files[1]` the start marker. A
    kill leaves a marker and no record; its compute is reconciled into the accounting first
    (`reconcile_kill`), so the cap check that follows includes it. With `over_limit_ok` (the
    projection), a completed projection over its limit may be rerun only once an amendment has
    reduced the registered generations so that, at the archived projection's own rates, training
    fits the limit (D107, D108). A killed attempt is charged before any refusal, so even a final,
    refused one is counted."""
    if not reason or not reason.strip():
        raise SystemExit("a rerun needs --reason, written before it runs")
    record, marker = files[0], files[1]
    reconciled = reconcile_kill(stage, files) if (marker.exists() and not record.exists()) else None
    if any(attempt1(f).exists() for f in files[:2]):
        raise SystemExit(f"{stage} has been rerun once already")
    if record.exists():
        rec = json.loads(record.read_text(encoding="utf-8"))
        over = over_limit_ok and rec.get("outcome") == "completed" and rec.get("within_limit") is False
        if rec.get("outcome") != OUTCOMES["stopped"] and not over:
            raise SystemExit(f"only a stage stopped by a crash, an interrupt or a kill is rerun, not: {rec.get('outcome')}")
        if over and not amended_plan_fits(rec):
            raise SystemExit("an over-limit projection is rerun only after an amendment reduces the generations "
                             "enough to fit the limit at the projection's own rates")
        how = "over its limit" if over else "stopped"
    elif marker.exists():
        how = "killed: a start marker and no record"
    else:
        raise SystemExit(f"{stage} has not run: nothing to rerun")
    return {"stage": stage, "files": files, "reason": reason.strip(), "how": how, "reconciled": reconciled}


def amended_plan_fits(rec: dict) -> bool:
    """For an over-limit projection's rerun: fewer registered generations than it projected, and
    training within the limit at its own measured rates (Fable, review v4)."""
    plan = training_plan()
    if not plan["generations"] < rec.get("plan", {}).get("generations", 0):
        return False
    hours = (plan["generations"] * rec["median_seconds_per_generation"]
             + plan["checkpoints"] * rec["seconds_per_checkpoint"]) / 3600
    return hours <= REGISTERED["projection"]["max_training_hours"]


def reconcile_kill(stage: str, files: list[Path]) -> dict:
    """A kill skips the accounting's cleanup (`finally`), so the attempt's time is missing from
    compute.json. It is charged here, once: from the marker's start to the attempt's last file
    write, plus the registered tail for the unrecorded end. The record is written atomically, under
    a name the aggregate does not read until it is complete; an existing record is reused with its
    stored charge; and the aggregate is rebuilt every time, so a kill between the two writes cannot
    leave a stale total for the cap check (Astra, review v4)."""
    marker = files[1]
    started = json.loads(marker.read_text(encoding="utf-8"))["started_utc"]
    t_start = calendar.timegm(time.strptime(started, "%Y-%m-%dT%H:%M:%SZ"))
    last = max(f.stat().st_mtime for f in files if f.exists())
    tail = float(REGISTERED["rerun_kill_tail_seconds"])
    seconds = max(0.0, last - t_start) + tail
    compute = OUT / "compute"
    name = f"killed-{marker.stem}-{started.replace(':', '')}.json"
    doc = {"status": "killed (reconciled)", "stage": stage, "marker": marker.name, "started_utc": started,
           "last_write_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(last)), "tail_seconds": tail,
           "categories": {"killed attempt": {**{f: 0 for f in acct.COUNT_FIELDS}, "seconds": seconds}},
           "note": "counts unknown; seconds estimated from the marker and the last file write (D107)"}
    compute.mkdir(parents=True, exist_ok=True)
    path = compute / name
    if path.exists():  # once, however often the rerun is refused and retried: reuse the stored charge
        seconds = float(json.loads(path.read_text(encoding="utf-8"))["categories"]["killed attempt"]["seconds"])
    else:
        tmp = path.with_name(path.name + ".partial")  # not *.json, so the aggregate never reads it half-written
        reg.write_json(tmp, doc)
        os.replace(tmp, path)
    acct.write_aggregate(compute, OUT / "compute.json")
    return {"file": name, "seconds": seconds}


def apply_rerun(plan: dict | None) -> dict | None:
    """After every other check has passed: keep the stopped attempt's files beside, renamed
    `-attempt1`, and write the reason and the mapping to `<record>-rerun.json`."""
    if plan is None:
        return None
    moved = {}
    for f in plan["files"]:
        if f.exists():
            os.replace(f, attempt1(f))
            moved[f.name] = attempt1(f).name
    record = plan["files"][0]
    note = {"stage": plan["stage"], "how_the_first_attempt_ended": plan["how"], "reason": plan["reason"],
            "reconciled_compute": plan["reconciled"], "archived": moved,
            "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    reg.write_json(record.with_name(record.stem + "-rerun.json"), note)
    return note


def _device_genome(g: Genome, device) -> Genome:
    return EV.moved(g, device)


# ----------------------------------------------------------------------------- records

def run_record(rec: EV.RunRecord) -> dict:
    out = {"spec": asdict(rec.spec), "log": rec.log, "checkpoints": rec.checkpoints, "generation0": rec.generation0,
           "generations_completed": len(rec.log)}
    if rec.checkpoints:
        ci = rec.champion_index()
        out["champion"] = {"checkpoint": ci, **{k: v for k, v in rec.checkpoints[ci].items() if k != "validation_counts"}}
        out["generation0_baseline"] = {"checkpoint": 0, **{k: v for k, v in rec.checkpoints[0].items()
                                                           if k != "validation_counts"}}
    if rec.final is not None:
        out["final_population_sha256"] = [genome_hash(rec.final, i) for i in range(rec.final.n_strains)]
    return out


def save_genomes(records: list[EV.RunRecord], cfg, folder: Path | None = None) -> None:
    """Each run's checkpoint candidates, local, written to a temporary file and moved into place."""
    for rec in records:
        if not rec.candidates:
            continue
        path = genomes_path(rec.spec.run) if folder is None else Path(folder) / f"run{rec.spec.run:02d}-candidates.npz"
        tmp = path.with_name(path.stem + ".tmp.npz")
        save_population(tmp, Genome.cat(rec.candidates), cfg=cfg, run=rec.spec.run, run_seed=rec.spec.run_seed,
                        shaping=rec.spec.shaping, checkpoint_generations=[c["generation"] for c in rec.checkpoints])
        os.replace(tmp, path)


# ----------------------------------------------------------------------------- the projection

def projection_verdict(secs: list[float]) -> dict:
    """The median time of the timed generations after the first (which includes warm-up and the
    first checkpoint) sets the per-generation time; the last generation's excess over it is one
    checkpoint's cost. Training is projected for both batches, checkpoints included."""
    P, plan = REGISTERED["projection"], training_plan()
    per_gen = float(np.median(secs[1:-1])) if len(secs) > 2 else float(secs[-1])
    per_checkpoint = max(0.0, float(secs[-1]) - per_gen)
    hours = (plan["generations"] * per_gen + plan["checkpoints"] * per_checkpoint) / 3600
    return {"plan": plan, "median_seconds_per_generation": per_gen, "seconds_per_checkpoint": per_checkpoint,
            "projected_training_hours": hours, "limit_hours": P["max_training_hours"],
            "within_limit": hours <= P["max_training_hours"]}


def cmd_project(args):
    """Before the formal stages (PREREGISTRATION.md §8): batch A's shape at full size, on smoke ids,
    timed per generation, once. Batch A refuses to start without a completed projection within its
    limit, on the same code and environment."""
    prov = reg.provenance(GUARDED)
    if formal(args):
        reg.require_formal(args.device, prov)
    path = EXP / "projection.json"
    scratch = [OUT / "projection-genomes" / f"run{r.run:02d}-candidates.npz"
               for r in run_specs("A", REGISTERED["projection"]["seed_base"])]
    plan = rerun_plan("the projection", [path, EXP / "project-started.json", *scratch], args.reason,
                      over_limit_ok=True) if args.rerun else None
    if plan is None and path.exists():
        raise SystemExit(f"{path.name} exists: the projection runs once")
    cap = clock()
    try:
        cap.check()
    except reg.CapReached as e:
        raise SystemExit(f"the projection did not start: {e}") from None
    con, iface = preflight(args.device)
    spec = BrainSpec.from_connectome(con)
    cfg = task_config()
    rerun = apply_rerun(plan)
    marker = reg.start_marker(EXP, "project", prov)
    n = REGISTERED["projection"]["generations_timed"]
    val, base, span = projection_ids()
    doc = {"registered": REGISTERED["projection"], "provenance_at_start": prov, "device": args.device,
           "resolved_config_sha256": config_sha256(cfg), "e1_inputs_sha256": e1_input_hashes(),
           "start_marker": marker.name, "generations_timed": n, "rerun": rerun,
           "seeds": [r.run_seed for r in run_specs("A", REGISTERED["projection"]["seed_base"])],
           "ids": {"training": [base, base + span - 1], "validation": id_record(val)}}
    t0 = time.perf_counter()
    try:
        with acct.category("measure"):
            # the checkpoint writes are timed too, as in training (local scratch files, kept, and
            # archived with the projection on a rerun)
            recs = EV.evolve_batch(cfg, iface, spec, run_specs("A", REGISTERED["projection"]["seed_base"]),
                                   generations=n, checkpoint_every=n - 1, validation_ids=val,
                                   world_seed=REGISTERED["world_seed"], id_base=base, id_span=span,
                                   device=args.device, rollout_fn=rollout_mod.rollout, check=cap.check,
                                   on_checkpoint=lambda rs, g: save_genomes(rs, cfg, OUT / "projection-genomes"))
        secs = [x["batch_seconds"] for x in recs[0].log]
        doc.update(outcome="completed", batch_seconds=secs, **projection_verdict(secs),
                   seconds=time.perf_counter() - t0)
        cap.check()
    except reg.CapReached as e:
        doc.update(outcome=OUTCOMES["cap"], error=str(e), seconds=time.perf_counter() - t0)
        write_atomic(path, doc)
        raise SystemExit(doc["outcome"]) from None
    except BaseException as e:  # noqa: BLE001
        doc.update(outcome=OUTCOMES["stopped"], error=f"{type(e).__name__}: {e}", seconds=time.perf_counter() - t0)
        write_atomic(path, doc)
        raise
    write_atomic(path, doc)
    print(f"{doc['median_seconds_per_generation']:.3f} s per generation; training projected at "
          f"{doc['projected_training_hours']:.2f} h (limit {doc['limit_hours']} h): "
          f"{'within' if doc['within_limit'] else 'OVER: the formal stages do not start'}")


def require_projection(args, prov) -> dict:
    p = require_earlier(args, prov, EXP / "projection.json", "the projection")
    if not p.get("within_limit"):
        raise SystemExit("the projection is over its limit: reduce the generations by a dated amendment first")
    return p


# ----------------------------------------------------------------------------- training

def cmd_train(args):
    batch = args.batch
    prov = reg.provenance(GUARDED)
    if formal(args):
        reg.require_formal(args.device, prov)
    path, partial_path = train_path(batch), EXP / f"train-{batch}-partial.json"
    local = [genomes_path(r.run) for r in run_specs(batch)] + [OUT / f"run{r.run:02d}-final.npz"
                                                                for r in run_specs(batch)]
    plan = rerun_plan(f"batch {batch}", [path, EXP / f"train-{batch}-started.json", partial_path, *local],
                      args.reason) if args.rerun else None
    if plan is None and path.exists():
        raise SystemExit(f"{path.name} exists: batch {batch} runs once")
    if batch == "A":
        require_projection(args, prov)
    else:
        require_earlier(args, prov, train_path("A"), "batch A")
    cap = clock()
    try:
        cap.check()
    except reg.CapReached as e:
        raise SystemExit(f"batch {batch} did not start: {e}") from None
    con, iface = preflight(args.device)
    spec = BrainSpec.from_connectome(con)
    cfg = task_config()
    rerun = apply_rerun(plan)
    marker = reg.start_marker(EXP, f"train-{batch}", prov)
    t0 = time.perf_counter()
    runs = run_specs(batch)
    val = validation_ids()
    ti = REGISTERED["train_ids"]
    result = {"batch": batch, "registered": REGISTERED, "provenance_at_start": prov, "device": args.device,
              "resolved_config": cfg.to_dict(), "resolved_config_sha256": config_sha256(cfg),
              "e1_inputs_sha256": e1_input_hashes(), "runs": [asdict(r) for r in runs],
              "training_ids": [ti["base"], ti["base"] + ti["span"] - 1], "validation_worlds": id_record(val),
              "composition": {"training": [len(runs) * cfg.evo.population, cfg.evo.worlds_per_strain, 1],
                              "validation": [len(runs), len(val), 1]},
              "genome_files": "local, runs/e04a/genomes/ (not published; D028)", "start_marker": marker.name,
              "rerun": rerun}
    records: list = []

    def partial(recs, g):
        records[:] = recs
        save_genomes(recs, cfg)
        write_atomic(partial_path, {**result, "generation": g, "records": [run_record(r) for r in recs]})

    try:
        recs = EV.evolve_batch(
            cfg, iface, spec, runs, generations=cfg.evo.generations, checkpoint_every=REGISTERED["validation"]["every"],
            validation_ids=val, world_seed=REGISTERED["world_seed"], id_base=ti["base"], id_span=ti["span"],
            device=args.device, rollout_fn=rollout_mod.rollout, check=cap.check, category=acct.category,
            on_checkpoint=partial)
        records[:] = recs
        save_genomes(recs, cfg)
        for r in recs:  # the final populations stay local, for any continuation
            save_population(OUT / f"run{r.spec.run:02d}-final.npz", r.final, cfg=cfg, run=r.spec.run,
                            run_seed=r.spec.run_seed, shaping=r.spec.shaping, generations=cfg.evo.generations)
        summary = {"outcome": "completed", "records": [run_record(r) for r in recs],
                   "seconds": time.perf_counter() - t0}
        cap.check()  # the final budget decision, before the record is written
    except reg.CapReached as e:
        _train_not_completed(path, result, records, cfg, str(e), t0, "cap")
    except BaseException as e:  # noqa: BLE001  (recorded as not completed, then re-raised)
        _train_not_completed(path, result, records, cfg, f"{type(e).__name__}: {e}", t0, "stopped", reraise=e)
    result.update(summary)
    write_atomic(path, result)
    partial_path.unlink(missing_ok=True)
    for r in result["records"]:
        print(f"run {r['spec']['run']:2d} c={r['spec']['shaping']}: champion g{r['champion']['generation']} "
              f"validation {r['champion']['validation_mean']:.3f}")


def _train_not_completed(path, result, records, cfg, error, t0, reason, reraise=None):
    """The record first, so it survives even if saving genomes is what failed; then one attempt to
    save the last checkpoint's genomes, whose own failure is added to the record."""
    result.update(outcome=OUTCOMES[reason], error=error, records=[run_record(r) for r in records],
                  seconds=time.perf_counter() - t0)
    write_atomic(path, result)
    try:
        save_genomes(records, cfg)
    except Exception as e:  # noqa: BLE001
        result["genome_save_error"] = f"{type(e).__name__}: {e} (the files from the previous checkpoint remain)"
        write_atomic(path, result)
    if reraise is not None:
        raise reraise
    raise SystemExit(result["outcome"])


# ----------------------------------------------------------------------------- the evaluation

def gain_curve_params(tuned: dict) -> dict[float, dict]:
    """For each k of E1's S-const grid, the first maximum over speed and turn among E1's tuned means."""
    t = tuned["S-const"]
    keys, grid, means = t["keys"], t["grid"], np.asarray(t["means"])
    combos = list(itertools.product(*[grid[k] for k in keys]))
    if len(combos) != len(means):
        raise SystemExit("E1's S-const grid and means disagree")
    out = {}
    for kval in grid["k"]:
        idx = [i for i, c in enumerate(combos) if c[keys.index("k")] == kval]
        best = idx[int(np.argmax(means[idx]))]
        out[float(kval)] = dict(zip(keys, (float(x) for x in combos[best])))
    return out


def equivalent_k(mean: float, curve: dict[float, float]):
    """The performance-equivalent k: linear in log k inside the first pair of neighbouring grid points
    (in increasing k) with mean(lower k) <= `mean` <= mean(higher k). "< k_min" below the first
    point's mean; "> k_max" above every point's mean. ("not bracketed" is a guard only: a curve that
    starts at or below `mean` and reaches above it crosses it upward between some neighbours.)"""
    ks = sorted(curve)
    if mean < curve[ks[0]]:
        return f"< {ks[0]:g}"
    for a, b in zip(ks, ks[1:]):
        lo, hi = curve[a], curve[b]
        if lo <= mean <= hi:
            if hi == lo:
                return float(a)
            f = (mean - lo) / (hi - lo)
            return float(np.exp(np.log(a) + f * (np.log(b) - np.log(a))))
    if mean > max(curve.values()):
        return f"> {ks[-1]:g}"
    return "not bracketed"


def run_rules(counts: dict, run: int) -> dict:
    G = REGISTERED["rules"]
    B = G["interval"]
    lb = lambda d: reg.lower_bound(d, B["resamples"], B["seed"])  # noqa: E731
    tag = f"run{run:02d}"
    real = counts[f"{tag} champion"]
    n_ok = int((real >= G["reliability"]["min_arrivals"]).sum())
    rules = {"reliability": {"episodes_with_at_least_2": n_ok, "episodes": int(real.size), "share": n_ok / real.size,
                             "required_share": G["reliability"]["required_share"],
                             "passed": n_ok / real.size >= G["reliability"]["required_share"]},
             "baselines": {}}
    for b in G["baselines"]:
        d = real - counts[b]
        v = lb(d)
        rules["baselines"][b] = {"mean_difference": float(d.mean()), "lower_95": v, "margin": G["baseline_margin"],
                                 "passed": v > G["baseline_margin"]}
    contrast = 0.5 * real - counts[f"{tag} mirrored"]
    v = lb(contrast)
    rules["cue"] = {"mean": float(contrast.mean()), "lower_95": v, "required": G["cue"]["required_lower_bound"],
                    "passed": v >= G["cue"]["required_lower_bound"]}
    d = real - counts[f"{tag} constant"]
    v = lb(d)
    rules["cue_helps"] = {"mean_difference": float(d.mean()), "lower_95": v, "margin": G["cue_helps"]["margin"],
                          "passed": v > G["cue_helps"]["margin"]}
    d = real - counts[f"{tag} generation 0"]
    v = lb(d)
    rules["generation0"] = {"mean_difference": float(d.mean()), "lower_95": v, "margin": G["generation0_margin"],
                            "passed": v > G["generation0_margin"]}
    checks = {"reliability": rules["reliability"]["passed"],
              **{f"beats {b}": x["passed"] for b, x in rules["baselines"].items()},
              "fails with the mirrored cue": rules["cue"]["passed"],
              "beats its own constant probe": rules["cue_helps"]["passed"],
              "beats generation 0": rules["generation0"]["passed"]}
    rules["passed"] = all(checks.values())
    rules["failed"] = [k for k, ok in checks.items() if not ok]
    return rules


def share_lower_bound(k: int, n: int) -> float:
    """Exact (Clopper-Pearson) one-sided 95% lower bound on a binomial share."""
    return 0.0 if k == 0 else float(beta.ppf(0.05, k, n - k + 1))


def outcome_of(per_run: dict) -> str:
    shaped = REGISTERED["runs"]["shaped"]
    k = sum(per_run[r]["passed"] for r in shaped)
    if k >= REGISTERED["outcome"]["required_passing_runs"]:
        return OUTCOMES["passed"]
    return OUTCOMES["some"].format(k=k, n=len(shaped)) if k else OUTCOMES["none"]


def decoy_capture(events: dict, side: int) -> dict:
    """For each world's unfinished leg: the head's final distance to the decoy point (side-1-x,
    side-1-y) and to the true target."""
    fh = events["final_head"][0]  # [worlds, 2]
    reach, act = events["reach_tick"][0], events["activation_tick"][0]
    cur = np.array([np.flatnonzero((act[w] >= 0) & (reach[w] < 0))[0] for w in range(act.shape[0])])
    tx = events["target_x"][0][np.arange(len(cur)), cur]
    ty = events["target_y"][0][np.arange(len(cur)), cur]
    d_true = np.hypot(fh[:, 0] - tx, fh[:, 1] - ty)
    d_decoy = np.hypot(fh[:, 0] - (side - 1 - tx), fh[:, 1] - (side - 1 - ty))
    return {"median_distance_to_decoy": float(np.median(d_decoy)), "median_distance_to_target": float(np.median(d_true)),
            "share_closer_to_decoy": float((d_decoy < d_true).mean())}


def load_candidates(run: int, spec, cfg) -> Genome:
    g, _ = load_population(genomes_path(run), spec, cfg.brain)
    return g


def check_genomes(records: dict, spec, cfg) -> dict:
    """The champions and baselines, from the local files, checked against the committed hashes;
    and each generation-0 baseline found in its run's regenerated initial population."""
    genomes = {}
    want = dataclasses.asdict(cfg.brain)
    for run, r in records.items():
        cands = load_candidates(run, spec, cfg)
        if dataclasses.asdict(cands.cfg) != want:  # a file's metadata can override padding (Astra, review v2)
            diff = {k: (want[k], v) for k, v in dataclasses.asdict(cands.cfg).items() if want.get(k) != v}
            raise SystemExit(f"run {run}'s genome file loads with another brain configuration: {diff}")
        for label, key in (("champion", "champion"), ("generation 0", "generation0_baseline")):
            g = cands.select([r[key]["checkpoint"]])
            if genome_hash(g, 0) != r[key]["sha256"]:
                raise SystemExit(f"run {run}'s {label} does not match its committed hash")
            genomes[(run, label)] = g
        init = EV.initial_population(spec, cfg.brain, r["spec"]["run_seed"], cfg.evo.population, "cpu")
        if r["generation0_baseline"]["sha256"] not in {genome_hash(init, i) for i in range(init.n_strains)}:
            raise SystemExit(f"run {run}'s generation-0 baseline is not in its regenerated initial population")
    return genomes


def cmd_evaluate(args):
    prov = reg.provenance(GUARDED)
    if formal(args):
        reg.require_formal(args.device, prov)
    result_path, events_path = EXP / "evaluation.json", EXP / "evaluation_events.npz"
    partial = EXP / "evaluation_partial.npz"
    plan = rerun_plan("the evaluation", [result_path, EXP / "evaluate-started.json", events_path, partial],
                      args.reason) if args.rerun else None
    if plan is None and result_path.exists():
        raise SystemExit(f"{result_path.name} exists: the hold-out worlds are used once")
    trains = {b: require_earlier(args, prov, train_path(b), f"batch {b}") for b in ("A", "B")}
    if trains["A"]["e1_inputs_sha256"] != e1_input_hashes():
        raise SystemExit("E1's freeze or gate record differs from what batch A recorded")
    cap = clock()
    try:
        cap.check()
    except reg.CapReached as e:
        raise SystemExit(f"the evaluation did not start: {e}") from None
    con, iface = preflight(args.device)
    spec = BrainSpec.from_connectome(con)
    cfg = task_config()
    records = {r["spec"]["run"]: r for b in ("A", "B") for r in trains[b]["records"]}
    genomes = check_genomes(records, spec, cfg)  # before any hold-out world is used
    tuned = json.loads(E1_FREEZE.read_text(encoding="utf-8"))["tuned"]
    curve = gain_curve_params(tuned)
    rerun = apply_rerun(plan)
    marker = reg.start_marker(EXP, "evaluate", prov)
    t0 = time.perf_counter()
    ids = holdout_ids()
    ws = REGISTERED["world_seed"]

    def neural(g, probe="real"):
        c = cfg.copy()
        c.world.food_probe = probe
        cap.check()
        with acct.category("final"):
            r = rollout_mod.rollout(c, iface, _device_genome(g, args.device), ids, ws, args.device,
                                    chunk_worlds=len(ids))
        return r.score[0], _events(r)

    def scripted(name, params, probe="real"):
        c = cfg.copy()
        c.world.food_probe = probe
        if name == "oracle":
            brain = E1.C.OracleBrain(iface, 302, c.world.forward_gain, c.world.turn_gain, device=args.device, **params)
        else:
            brain = E1.C.scripted(iface, E1.MAKERS[name](**params), c, device=args.device)
        cap.check()
        with acct.category("final"):
            r = rollout_brain(c, iface, brain, ids, ws, args.device)
        return r.score[0], _events(r)

    arms = []
    for run in sorted(records):
        tag = f"run{run:02d}"
        arms += [(f"{tag} champion", "neural", (run, "champion"), "real"),
                 (f"{tag} mirrored", "neural", (run, "champion"), "mirrored"),
                 (f"{tag} constant", "neural", (run, "champion"), "constant"),
                 (f"{tag} generation 0", "neural", (run, "generation 0"), "real")]
    for name in REGISTERED["rules"]["baselines"]:
        arms.append((name, "scripted", (name, tuned[name]["params"]), "real"))
    for name in REGISTERED["references"]:
        base = "S-const" if name == "S-const k<=32" else name
        arms.append((name, "scripted", (base, tuned[name]["params"]), "real"))
    for kval, params in curve.items():
        arms.append((f"gain k={kval:g}", "scripted", ("S-const", params), "real"))

    counts, events = {}, {}
    result = {"registered": REGISTERED, "provenance_at_start": prov, "device": args.device,
              "resolved_config_sha256": config_sha256(cfg), "e1_inputs_sha256": e1_input_hashes(),
              "worlds": id_record(ids), "start_marker": marker.name, "rerun": rerun,
              "training_records": {b: train_path(b).name for b in trains},
              "composition": {"neural arms": [1, len(ids), 1], "scripted arms": [1, len(ids), 1]}}
    try:
        for label, kind, what, probe in arms:
            counts[label], events[label] = neural(genomes[what], probe) if kind == "neural" else scripted(*what, probe)
            _checkpoint(partial, counts, events, ids)
        analysis = analyse(counts, events, records, curve, cfg)
        cap.check()  # the final budget decision, before the verdict is written
    except reg.CapReached as e:
        _eval_not_completed(result_path, events_path, result, counts, events, ids, str(e), t0, "cap")
    except BaseException as e:  # noqa: BLE001
        _eval_not_completed(result_path, events_path, result, counts, events, ids, f"{type(e).__name__}: {e}", t0,
                            "stopped", reraise=e)
    # the gating record first; the non-gating extras after it, so a failure there cannot void it
    result.update(analysis, seconds=time.perf_counter() - t0)
    write_atomic(result_path, result)
    _save_events(events_path, events, ids)
    partial.unlink(missing_ok=True)
    print(result["outcome"], f"(shaped share lower bound {result['passing_share_lower_95']:.2f})")
    for r, v in result["rules"].items():
        print(f"run {r}: {'pass' if v['passed'] else 'fail'} {v['failed']}  "
              f"mean {result['means'][f'run{int(r):02d} champion']:.2f}")
    extras(records, genomes, events, cfg, spec, iface, args.device, cap, result)


def analyse(counts, events, records, curve, cfg) -> dict:
    per_run = {run: run_rules(counts, run) for run in sorted(records)}
    shaped, unshaped = REGISTERED["runs"]["shaped"], REGISTERED["runs"]["unshaped"]
    k = sum(per_run[r]["passed"] for r in shaped)
    oracle = float(counts["oracle"].mean())
    curve_means = {kk: float(counts[f"gain k={kk:g}"].mean()) for kk in curve}
    return {
        "outcome": outcome_of(per_run),
        "passing_runs": {"shaped": [r for r in shaped if per_run[r]["passed"]],
                         "unshaped": [r for r in unshaped if per_run[r]["passed"]]},
        "passing_share": k / len(shaped), "passing_share_lower_95": share_lower_bound(k, len(shaped)),
        "rules": {str(r): v for r, v in per_run.items()},
        "means": {kk: float(v.mean()) for kk, v in counts.items()},
        "fraction_of_oracle": {kk: (float(v.mean()) / oracle if oracle > 0 else None) for kk, v in counts.items()},
        "gain_curve": {f"{kk:g}": {"params": curve[kk], "mean": m} for kk, m in curve_means.items()},
        "equivalent_k": {str(r): equivalent_k(float(counts[f"run{r:02d} champion"].mean()), curve_means)
                         for r in sorted(records)},
        "secondary": {kk: E1.secondary(events[kk], cfg.world.max_ticks) for kk in counts},
        "per_world_counts": {kk: v.astype(int).tolist() for kk, v in counts.items()},
        "events_file": "evaluation_events.npz"}


def extras(records, genomes, events, cfg, spec, iface, device, cap, result) -> None:
    """Reported, not gating: the decoy capture, a replay check per champion, and the modules. Written
    to their own file; an error here is recorded there and leaves the verdict untouched."""
    doc, path = {"errors": {}, "decoy_capture": {}, "replay": {}}, EXP / "evaluation-extras.json"
    side = arena_side(cfg, 1)
    for r in sorted(records):
        try:
            doc["decoy_capture"][str(r)] = decoy_capture(events[f"run{r:02d} mirrored"], side)
        except Exception as e:  # noqa: BLE001
            doc["errors"][f"decoy {r}"] = f"{type(e).__name__}: {e}"
    for r in sorted(records):
        try:
            doc["replay"][str(r)] = replay_check(records, r, spec, cfg, iface, device, cap)
        except (reg.CapReached, Exception) as e:  # noqa: BLE001
            doc["errors"][f"replay {r}"] = f"{type(e).__name__}: {e}"
    try:
        doc["modules"] = save_modules(records, genomes, cfg, result)
        champ = {r: result["means"][f"run{r:02d} champion"] for r in result["passing_runs"]["shaped"]}
        doc["module_for_E3"] = max(champ, key=champ.get) if champ else None
    except Exception as e:  # noqa: BLE001
        doc["errors"]["modules"] = f"{type(e).__name__}: {e}"
    write_atomic(path, doc)


def _events(r) -> dict:
    ev = dict(r.events)
    ev["final_head"] = r.final_head
    return ev


def _checkpoint(path: Path, counts, events, ids) -> None:
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, world_ids=ids, **{f"{k}|count": v for k, v in counts.items()},
                        **{f"{label}|{k}": v[0] for label, ev in events.items() for k, v in ev.items()})
    os.replace(tmp, path)


def _save_events(path: Path, events, ids) -> None:
    np.savez_compressed(path, world_ids=ids,
                        **{f"{label}|{k}": v[0] for label, ev in events.items() for k, v in ev.items()})


def _eval_not_completed(result_path, events_path, result, counts, events, ids, error, t0, reason, reraise=None):
    result.update(outcome=OUTCOMES[reason], error=error, arms_completed=list(counts),
                  per_world_counts={k: v.astype(int).tolist() for k, v in counts.items()},
                  seconds=time.perf_counter() - t0)
    write_atomic(result_path, result)
    _save_events(events_path, events, ids)
    if reraise is not None:
        raise reraise
    raise SystemExit(result["outcome"])


def replay_check(records: dict, run: int, spec, cfg, iface, device, cap) -> dict:
    """Reload from disk the checkpoint batch that produced the run's champion (every run of its batch
    at that checkpoint) and replay it in the same composition on the validation worlds. Reported,
    not claimed exact."""
    batch = next(b for b, runs in REGISTERED["runs"]["batches"].items() if run in runs)
    ci = records[run]["champion"]["checkpoint"]
    mates = REGISTERED["runs"]["batches"][batch]
    g = Genome.cat([load_candidates(m, spec, cfg).select([ci]) for m in mates])
    val = validation_ids()
    cap.check()
    with acct.category("probe"):  # the replay check
        r = rollout_mod.rollout(cfg, iface, _device_genome(g, device), val, REGISTERED["world_seed"], device,
                                chunk_worlds=len(mates) * len(val))
    got = r.score[mates.index(run)].astype(int)
    want = np.asarray(records[run]["checkpoints"][ci]["validation_counts"], dtype=int)
    return {"worlds": int(len(val)), "identical_worlds": int((got == want).sum()),
            "recorded_mean": float(want.mean()), "replayed_mean": float(got.mean())}


def save_modules(records, genomes, cfg, result) -> dict:
    """Each champion as a module, local (runs/e04a/modules/): the genome, the world settings, the
    interface and the evidence. Their hashes go in the record."""
    out = {}
    for run in records:
        path = OUT / "modules" / f"run{run:02d}-champion.npz"
        save_genome(path, genomes[(run, "champion")], cfg=cfg, run=run,
                    input_mapping="goal cue, left and right, at AWA, AWC and ASE (configs/interface.yaml)",
                    interface="configs/interface.yaml", task="E1 Task N, sigma 6",
                    evidence={"holdout_mean": result["means"][f"run{run:02d} champion"],
                              "passed": result["rules"][str(run)]["passed"],
                              "failed": result["rules"][str(run)]["failed"]})
        out[str(run)] = {"file": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                         "genome_sha256": genome_hash(genomes[(run, "champion")], 0)}
    return out


# ----------------------------------------------------------------------------- smoke

def use_smoke(args, folder: Path | None = None) -> None:
    """Tiny sizes, ids 0-9 999 (outside every E1 and 04a range) for every stage, and a scratch folder.
    Never results. Only files inside that folder are removed."""
    global EXP, OUT, SMOKE
    EXP = OUT = Path(folder) if folder is not None else ROOT / "runs" / "e04a-smoke"
    SMOKE = True
    R = REGISTERED
    R["train_ids"] = {"base": 0, "span": 5000}
    R["runs"]["seed_base"] = SMOKE_SEED_BASE
    R["evolution"].update(generations=3, population=4, elites=1, truncation=2, worlds_per_strain=2)
    R["runs"]["batches"] = {"A": [0, 1], "B": [12, 13]}
    R["runs"]["shaped"], R["runs"]["unshaped"] = [0, 1], [12, 13]
    R["validation"].update(worlds=4, every=2)
    R["holdout"].update(worlds=16)
    R["projection"].update(generations_timed=3)
    R["rules"]["interval"]["resamples"] = 200
    R["outcome"]["required_passing_runs"] = 1
    later = {"project": ["project", "train-A", "train-B", "evaluate"], "train": [f"train-{args.batch}"]
             + (["train-B", "evaluate"] if args.batch == "A" else ["evaluate"]), "evaluate": ["evaluate"]}
    for stage in later[args.command]:
        name = {"project": "projection", "evaluate": "evaluation"}.get(stage, stage)
        for f in (EXP / f"{name}.json", EXP / f"{stage}-started.json", EXP / f"{name}-partial.json",
                  EXP / "evaluation_events.npz", EXP / "evaluation-extras.json"):
            if stage != "evaluate" and f.name.startswith("evaluation"):
                continue
            f.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=["project", "train", "evaluate"])
    ap.add_argument("--batch", choices=["A", "B"])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true", help="tiny sizes, ids outside E1 and 04a, scratch folder")
    ap.add_argument("--guarded", action="store_true", help="with --smoke: keep the formal guards")
    ap.add_argument("--rerun", action="store_true", help="once, after a crash, an interrupt or a kill (never the cap)")
    ap.add_argument("--reason", help="with --rerun: why the first attempt stopped, recorded before the rerun")
    args = ap.parse_args()
    if args.command == "train" and not args.batch:
        ap.error("train needs --batch A or B")
    if args.smoke:
        use_smoke(args)
    {"train": cmd_train, "evaluate": cmd_evaluate, "project": cmd_project}[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    out = ROOT / "runs" / ("e04a-smoke" if smoke else "e04a")
    try:
        run_script(main, out_default=str(out), default="measure", name="e04a")
    finally:
        agg = out / "compute.json"
        if agg.exists() and not smoke:
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
