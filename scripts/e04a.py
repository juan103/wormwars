"""04a: the evolved N2 navigation primitive (experiments/04a-navigation-primitive/PREREGISTRATION.md).

    python scripts/e04a.py train --batch A    # runs 0-7; writes train-A.json and the genomes
    python scripts/e04a.py train --batch B    # runs 8-15; needs batch A committed, the same code and environment
    python scripts/e04a.py evaluate           # once, on the hold-out; needs both training records committed
    python scripts/e04a.py train --batch A --smoke   # tiny sizes, ids 0-9 999, runs/e04a-smoke/

Every number the pre-registration fixes is in `REGISTERED`, and every rule is applied mechanically.
Task N and the controls are E1's, imported from `scripts/e1.py` unchanged; the guards are the shared
ones in `wormwars/registration.py`.
"""

from __future__ import annotations

import argparse
import hashlib
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e1.task import HOLDOUT_04A_IDS  # noqa: E402
rollout_mod = importlib.import_module("wormwars.evo.rollout")  # the module: `wormwars.evo.rollout` is also a function
from wormwars.evo.genomes import genome_hash, load_population, save_genome, save_population  # noqa: E402
from wormwars.evo.rollout import rollout_brain  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402
from wormwars.world import arena_side  # noqa: E402

_spec = importlib.util.spec_from_file_location("e1_frozen", ROOT / "scripts" / "e1.py")
E1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E1)  # Task N's config, the controls and the secondary measures, unchanged

EXP = ROOT / "experiments" / "04a-navigation-primitive"
OUT = ROOT / "runs" / "e04a"
PREREG = "experiments/04a-navigation-primitive/PREREGISTRATION.md"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PREREG]
E1_FREEZE = ROOT / "experiments" / "E1-navigation" / "freeze.json"
E1_GATE = ROOT / "experiments" / "E1-navigation" / "gate.json"
SMOKE_IDS = np.arange(10_000)  # outside every E1 and 04a range
SMOKE = False
GUARDED_SMOKE = False

REGISTERED = {
    "world_seed": 1_100_001,  # E1's run seed: with the world id it generates each world and its targets
    "sigma": 6.0,  # E1's frozen σ
    "cap_gpu_hours": 6.0,  # every stage together, T0's accounting across attempts
    "evolution": {"population": 32, "elites": 3, "truncation": 8, "worlds_per_strain": 8, "generations": 1000,
                  "islands": 1, "mutation": {"w_sigma": 0.08, "g_sigma": 0.04, "tau_sigma": 0.15,
                                             "bias_sigma": 0.05, "p_mutate": 1.0}},
    "runs": {"seed_base": 1_104_000, "shaping": 0.5, "shaped": list(range(12)), "unshaped": [12, 13, 14, 15],
             "batches": {"A": list(range(8)), "B": list(range(8, 16))}},
    "train_ids": {"base": 997_000_000, "span": 1_000_000},
    "validation": {"first": 998_000_000, "worlds": 64, "every": 25},
    "holdout": {"offset": 1000, "worlds": 1024},
    "rules": {
        "reliability": {"min_arrivals": 2, "required_share": 0.80},
        "baselines": ["constant", "random-walk", "wall-follower", "K"],
        "baseline_margin": 0.5,
        "cue": {"probe": "mirrored", "contrast": "0.5 x real - mirrored, per world", "required_lower_bound": 0.0},
        "generation0_margin": 0.5,
        "interval": {"method": "paired percentile bootstrap over worlds, one-sided 95% lower bound",
                     "resamples": 10_000, "seed": 0},
    },
    "outcome": {"arm": "shaped", "required_passing_runs": 6},
    "references": ["S-const", "S-const k<=32", "M-avg", "oracle"],
    "projection": {"generations": 2000, "max_training_hours": 4.5},
}
OUTCOMES = {"passed": "04a: passed", "some": "04a: some runs passed ({k} of {n})", "none": "04a: not passed",
            "cap": "04a: not completed (the registered cap was reached)",
            "stopped": "04a: not completed (the run stopped)"}


# ----------------------------------------------------------------------------- paths and guards

def train_path(batch: str) -> Path:
    return EXP / f"train-{batch}.json"


def genomes_path(run: int) -> Path:
    return EXP / "genomes" / f"run{run:02d}-candidates.npz"


def clock() -> reg.CapClock:
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


def run_specs(batch: str) -> list[EV.RunSpec]:
    r = REGISTERED["runs"]
    return [EV.RunSpec(run=i, run_seed=r["seed_base"] + i, shaping=r["shaping"] if i in r["shaped"] else 0.0)
            for i in r["batches"][batch]]


def validation_ids() -> np.ndarray:
    v = REGISTERED["validation"]
    return (SMOKE_IDS[5000:5000 + v["worlds"]] if SMOKE else np.arange(v["first"], v["first"] + v["worlds"]))


def holdout_ids() -> np.ndarray:
    h = REGISTERED["holdout"]
    base = SMOKE_IDS if SMOKE else HOLDOUT_04A_IDS
    return base[h["offset"]:h["offset"] + h["worlds"]]


def id_record(ids) -> dict:
    ids = np.asarray(ids)
    return {"first": int(ids[0]), "last": int(ids[-1]), "count": int(len(ids))}


def require_committed(path: Path) -> None:
    """Tracked, unchanged, and (with the HEAD check in `require_formal`) pushed."""
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], cwd=ROOT,
                             capture_output=True).returncode == 0
    if not tracked or reg.git("status", "--porcelain", "--", str(path)):
        raise SystemExit(f"{path.name} must be committed, unchanged and pushed first")


def _device_genome(g: Genome, device) -> Genome:
    return EV.moved(g, device)


# ----------------------------------------------------------------------------- records

def run_record(rec: EV.RunRecord) -> dict:
    out = {"spec": asdict(rec.spec), "log": rec.log, "checkpoints": rec.checkpoints, "generation0": rec.generation0,
           "generations_completed": len(rec.log)}
    if rec.checkpoints:
        ci = rec.champion_index()
        out["champion"] = {"checkpoint": ci, **rec.checkpoints[ci]}
        out["generation0_baseline"] = {"checkpoint": 0, **rec.checkpoints[0]}
    return out


def save_genomes(records: list[EV.RunRecord], cfg) -> None:
    """Each run's checkpoint candidates, written to a temporary file and moved into place."""
    for rec in records:
        if not rec.candidates:
            continue
        path = genomes_path(rec.spec.run)
        tmp = path.with_name(path.stem + ".tmp.npz")
        save_population(tmp, Genome.cat(rec.candidates), cfg=cfg, run=rec.spec.run, run_seed=rec.spec.run_seed,
                        shaping=rec.spec.shaping, checkpoint_generations=[c["generation"] for c in rec.checkpoints])
        os.replace(tmp, path)


def write_atomic(path: Path, doc) -> None:
    reg.write_json(path, doc, atomic=True)


# ----------------------------------------------------------------------------- training

def cmd_train(args):
    batch = args.batch
    prov = reg.provenance(GUARDED)
    if formal(args):
        reg.require_formal(args.device, prov)
    path = train_path(batch)
    if path.exists():
        raise SystemExit(f"{path.name} exists: batch {batch} runs once")
    if batch == "B":
        if not train_path("A").exists():
            raise SystemExit("batch B runs after batch A")
        a = json.loads(train_path("A").read_text(encoding="utf-8"))
        if a.get("outcome") != "completed":
            raise SystemExit("batch A did not complete")
        if formal(args):
            if not args.smoke:
                require_committed(train_path("A"))
            reg.require_same_code(a["provenance_at_start"]["git_commit"], GUARDED)
            reg.require_same_env(a["provenance_at_start"], prov)
    cap = clock()
    try:
        cap.check()
    except reg.CapReached as e:
        raise SystemExit(f"batch {batch} did not start: {e}") from None
    con, iface = preflight(args.device)
    spec = BrainSpec.from_connectome(con)
    cfg = task_config()
    marker = reg.start_marker(EXP, f"train-{batch}", prov)
    t0 = time.perf_counter()
    runs = run_specs(batch)
    val = validation_ids()
    result = {"batch": batch, "registered": REGISTERED, "provenance_at_start": prov, "device": args.device,
              "resolved_config": cfg.to_dict(), "resolved_config_sha256": config_sha256(cfg),
              "runs": [asdict(r) for r in runs], "validation_worlds": id_record(val),
              "composition": {"training": [len(runs) * cfg.evo.population, cfg.evo.worlds_per_strain, 1],
                              "validation": [len(runs), len(val), 1]},
              "start_marker": marker.name}
    records: list = []

    def partial(recs, g):
        records[:] = recs
        save_genomes(recs, cfg)
        write_atomic(EXP / f"train-{batch}-partial.json",
                     {**result, "generation": g, "records": [run_record(r) for r in recs]})

    try:
        recs = EV.evolve_batch(
            cfg, iface, spec, runs, generations=cfg.evo.generations, checkpoint_every=REGISTERED["validation"]["every"],
            validation_ids=val, world_seed=REGISTERED["world_seed"], id_base=REGISTERED["train_ids"]["base"],
            id_span=REGISTERED["train_ids"]["span"], device=args.device, rollout_fn=rollout_mod.rollout,
            check=cap.check, category=acct.category, on_checkpoint=partial)
        records[:] = recs
        save_genomes(recs, cfg)
        for r in recs:  # the final populations stay local (runs/), for any continuation
            save_population(OUT / f"run{r.spec.run:02d}-final.npz", r.final, cfg=cfg, run=r.spec.run,
                            run_seed=r.spec.run_seed, shaping=r.spec.shaping, generations=cfg.evo.generations)
        summary = {"outcome": "completed", "records": [run_record(r) for r in recs],
                   "genome_files": {r.spec.run: str(genomes_path(r.spec.run).relative_to(EXP)) for r in recs},
                   "seconds": time.perf_counter() - t0}
        cap.check()  # the final budget decision, before the record is written
    except reg.CapReached as e:
        _train_not_completed(path, result, records, cfg, str(e), t0, "cap")
    except BaseException as e:  # noqa: BLE001  (recorded as not completed, then re-raised)
        _train_not_completed(path, result, records, cfg, f"{type(e).__name__}: {e}", t0, "stopped", reraise=e)
    result.update(summary)
    write_atomic(path, result)
    (EXP / f"train-{batch}-partial.json").unlink(missing_ok=True)
    for r in result["records"]:
        print(f"run {r['spec']['run']:2d} c={r['spec']['shaping']}: champion g{r['champion']['generation']} "
              f"validation {r['champion']['validation_mean']:.3f}")


def _train_not_completed(path, result, records, cfg, error, t0, reason, reraise=None):
    save_genomes(records, cfg)
    result.update(outcome=OUTCOMES[reason], error=error, records=[run_record(r) for r in records],
                  seconds=time.perf_counter() - t0)
    write_atomic(path, result)
    if reraise is not None:
        raise reraise
    raise SystemExit(result["outcome"])


# ----------------------------------------------------------------------------- the projection

def cmd_project(args):
    """Before the formal stages (PREREGISTRATION.md §8): batch A's shape at full size, for a few
    generations on smoke ids (outside every E1 and 04a range), timed per generation. The training
    projection is the registered number of generations for both batches at the median time of the
    generations after the first, which includes warm-up and a checkpoint."""
    prov = reg.provenance(GUARDED)
    if formal(args):
        reg.require_formal(args.device, prov)
    con, iface = preflight(args.device)
    spec = BrainSpec.from_connectome(con)
    cfg = task_config()
    n = args.generations
    t0 = time.perf_counter()
    with acct.category("measure"):
        recs = EV.evolve_batch(cfg, iface, spec, run_specs("A"), generations=n, checkpoint_every=n,
                               validation_ids=SMOKE_IDS[5000:5000 + REGISTERED["validation"]["worlds"]],
                               world_seed=REGISTERED["world_seed"], id_base=0, id_span=5000, device=args.device,
                               rollout_fn=rollout_mod.rollout)
    secs = [x["batch_seconds"] for x in recs[0].log]
    per_gen = float(np.median(secs[1:])) if n > 1 else secs[0]
    P = REGISTERED["projection"]
    hours = P["generations"] * per_gen / 3600
    doc = {"provenance": prov, "device": args.device, "generations_timed": n, "batch_seconds": secs,
           "median_seconds_per_generation_after_the_first": per_gen,
           "projected_training_hours": hours, "limit_hours": P["max_training_hours"],
           "within_limit": hours <= P["max_training_hours"], "seconds": time.perf_counter() - t0,
           "ids": "training 0-4 999 and validation 5 000 onward (smoke ids, outside every E1 and 04a range)"}
    reg.write_json(EXP / "projection.json", doc)
    print(f"{per_gen:.3f} s per generation; training projected at {hours:.2f} h "
          f"(limit {P['max_training_hours']} h): {'within' if doc['within_limit'] else 'OVER'}")


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
    """The performance-equivalent k: linear in log k between the grid points whose means bracket
    `mean`, at the first crossing; "< k_min" below the first point and "> k_max" above the largest."""
    ks = sorted(curve)
    if mean < curve[ks[0]]:
        return f"< {ks[0]:g}"
    for a, b in zip(ks, ks[1:]):
        lo, hi = curve[a], curve[b]
        if lo <= mean <= hi and hi > lo:
            f = (mean - lo) / (hi - lo)
            return float(np.exp(np.log(a) + f * (np.log(b) - np.log(a))))
        if lo <= mean <= hi:
            return float(a)
    if mean > max(curve.values()):
        return f"> {ks[-1]:g}"
    return None  # a non-monotone curve with no bracketing pair: reported as such


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
    d = real - counts[f"{tag} generation 0"]
    v = lb(d)
    rules["generation0"] = {"mean_difference": float(d.mean()), "lower_95": v, "margin": G["generation0_margin"],
                            "passed": v > G["generation0_margin"]}
    checks = {"reliability": rules["reliability"]["passed"],
              **{f"beats {b}": x["passed"] for b, x in rules["baselines"].items()},
              "uses the cue": rules["cue"]["passed"], "beats generation 0": rules["generation0"]["passed"]}
    rules["passed"] = all(checks.values())
    rules["failed"] = [k for k, ok in checks.items() if not ok]
    return rules


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
    g, meta = load_population(genomes_path(run), spec, cfg.brain)
    return g


def cmd_evaluate(args):
    prov = reg.provenance(GUARDED)
    if formal(args):
        reg.require_formal(args.device, prov)
    result_path, events_path = EXP / "evaluation.json", EXP / "evaluation_events.npz"
    if result_path.exists():
        raise SystemExit(f"{result_path.name} exists: the hold-out worlds are used once")
    trains = {}
    for b in ("A", "B"):
        if not train_path(b).exists():
            raise SystemExit(f"batch {b} has not run")
        trains[b] = json.loads(train_path(b).read_text(encoding="utf-8"))
        if trains[b].get("outcome") != "completed":
            raise SystemExit(f"batch {b} did not complete")
        if not args.smoke:
            require_committed(train_path(b))
            for r in trains[b]["records"]:
                require_committed(genomes_path(r["spec"]["run"]))
    if formal(args):
        was = trains["A"]["provenance_at_start"]
        reg.require_same_code(was["git_commit"], GUARDED)
        reg.require_same_env(was, prov)
    cap = clock()
    try:
        cap.check()
    except reg.CapReached as e:
        raise SystemExit(f"the evaluation did not start: {e}") from None
    con, iface = preflight(args.device)
    spec = BrainSpec.from_connectome(con)
    cfg = task_config()
    records = {r["spec"]["run"]: r for b in ("A", "B") for r in trains[b]["records"]}
    # the champions and baselines are the committed ones, checked before any hold-out world is used
    genomes = {}
    for run, r in records.items():
        cands = load_candidates(run, spec, cfg)
        for label, key in (("champion", "champion"), ("generation 0", "generation0_baseline")):
            g = cands.select([r[key]["checkpoint"]])
            if genome_hash(g, 0) != r[key]["sha256"]:
                raise SystemExit(f"run {run}'s {label} does not match its committed hash")
            genomes[(run, label)] = g
    tuned = json.loads(E1_FREEZE.read_text(encoding="utf-8"))["tuned"]
    curve = gain_curve_params(tuned)
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
              "resolved_config_sha256": config_sha256(cfg), "worlds": id_record(ids), "start_marker": marker.name,
              "training_records": {b: str(train_path(b).name) for b in trains},
              "composition": {"neural arms": [1, len(ids), 1], "scripted arms": [1, len(ids), 1]}}
    partial = EXP / "evaluation_partial.npz"
    try:
        for label, kind, what, probe in arms:
            counts[label], events[label] = neural(genomes[what], probe) if kind == "neural" else scripted(*what, probe)
            _checkpoint(partial, counts, events, ids)
        per_run = {run: run_rules(counts, run) for run in sorted(records)}
        oracle = float(counts["oracle"].mean())
        curve_means = {k: float(counts[f"gain k={k:g}"].mean()) for k in curve}
        analysis = {
            "outcome": outcome_of(per_run),
            "passing_runs": {"shaped": [r for r in REGISTERED["runs"]["shaped"] if per_run[r]["passed"]],
                             "unshaped": [r for r in REGISTERED["runs"]["unshaped"] if per_run[r]["passed"]]},
            "rules": {str(r): v for r, v in per_run.items()},
            "means": {k: float(v.mean()) for k, v in counts.items()},
            "fraction_of_oracle": {k: (float(v.mean()) / oracle if oracle > 0 else None) for k, v in counts.items()},
            "gain_curve": {f"{k:g}": {"params": curve[k], "mean": m} for k, m in curve_means.items()},
            "equivalent_k": {str(r): equivalent_k(float(counts[f"run{r:02d} champion"].mean()), curve_means)
                             for r in sorted(records)},
            "secondary": {k: E1.secondary(events[k], cfg.world.max_ticks) for k in counts},
            "decoy_capture": {str(r): decoy_capture(events[f"run{r:02d} mirrored"], arena_side(cfg, 1))
                              for r in sorted(records)},
            "replay": {str(r): replay_check(records, r, spec, cfg, iface, args.device, cap) for r in sorted(records)},
            "per_world_counts": {k: v.astype(int).tolist() for k, v in counts.items()},
            "events_file": events_path.name}
        champ = {r: float(counts[f"run{r:02d} champion"].mean()) for r in per_run}
        passing = [r for r in analysis["passing_runs"]["shaped"]]
        analysis["module_for_E3"] = (max(passing, key=lambda r: champ[r]) if passing else None)
        save_modules(records, genomes, cfg, analysis)
        cap.check()
    except reg.CapReached as e:
        _eval_not_completed(result_path, events_path, result, counts, events, ids, str(e), t0, "cap")
    except BaseException as e:  # noqa: BLE001
        _eval_not_completed(result_path, events_path, result, counts, events, ids, f"{type(e).__name__}: {e}", t0,
                            "stopped", reraise=e)
    result.update(analysis, seconds=time.perf_counter() - t0)
    write_atomic(result_path, result)
    _save_events(events_path, events, ids)
    partial.unlink(missing_ok=True)
    print(result["outcome"])
    for r, v in result["rules"].items():
        print(f"run {r}: {'pass' if v['passed'] else 'fail'} {v['failed']}  mean {result['means'][f'run{int(r):02d} champion']:.2f}")


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
    at that generation) and replay it in the same composition on the validation worlds. Reported,
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


def save_modules(records, genomes, cfg, analysis) -> None:
    """Each champion as a module: the genome, the world settings, the interface and the evidence."""
    for run in records:
        save_genome(EXP / "modules" / f"run{run:02d}-champion.npz", genomes[(run, "champion")], cfg=cfg,
                    run=run, input_mapping="goal cue, left and right, at AWA, AWC and ASE (configs/interface.yaml)",
                    interface="configs/interface.yaml", task="E1 Task N, sigma 6",
                    evidence={"holdout_mean": analysis["means"][f"run{run:02d} champion"],
                              "passed": analysis["rules"][str(run)]["passed"],
                              "failed": analysis["rules"][str(run)]["failed"]})


# ----------------------------------------------------------------------------- smoke

def use_smoke(args) -> None:
    """Tiny sizes, ids 0-9 999 (outside every E1 and 04a range), and a scratch folder. Never results."""
    global EXP, OUT, SMOKE
    EXP = OUT = ROOT / "runs" / "e04a-smoke"
    if args.command == "project":  # the projection keeps the full sizes; only its folder changes
        return
    SMOKE = True
    R = REGISTERED
    R["evolution"].update(generations=3, population=4, elites=1, truncation=2, worlds_per_strain=2)
    R["runs"]["batches"] = {"A": [0, 1], "B": [12, 13]}
    R["runs"]["shaped"], R["runs"]["unshaped"] = [0, 1], [12, 13]
    R["validation"].update(worlds=4, every=2)
    R["holdout"].update(offset=0, worlds=16)
    R["rules"]["interval"]["resamples"] = 200
    R["outcome"]["required_passing_runs"] = 1
    stale = [EXP / "evaluation.json", EXP / "evaluation_events.npz", EXP / "evaluate-started.json"]
    if args.command == "train":
        stale += [train_path(args.batch), EXP / f"train-{args.batch}-started.json"]
        if args.batch == "A":
            stale += [train_path("B"), EXP / "train-B-started.json"]
    for f in stale:
        f.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=["train", "evaluate", "project"])
    ap.add_argument("--generations", type=int, default=6, help="project: generations to time")
    ap.add_argument("--batch", choices=["A", "B"])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true", help="tiny sizes, ids outside E1 and 04a, scratch folder")
    ap.add_argument("--guarded", action="store_true", help="with --smoke: keep the formal guards")
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
