"""Experiment 02, the screening fraction. See experiments/02-screening/DESIGN.md.

    py -3.13 scripts/exp02.py remaps        # choose R1, R2, MS by the fixed rule -> remaps.json
    py -3.13 scripts/exp02.py calibrate     # in-world gains per graph variant   -> calibration.json
    py -3.13 scripts/exp02.py diagnostics   # tune and score scripted controllers -> diagnostics.json
    py -3.13 scripts/exp02.py pilot         # timed end-to-end runs on SH101 (discarded) -> pilot.json
    py -3.13 scripts/exp02.py run           # the grid, in balanced resumable batches
    py -3.13 scripts/exp02.py probes        # evaluation-only probes on every champion -> probes.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wormwars import calibration as calib
from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import shuffled
from wormwars.evo import SeedPool, load_genome, rollout, save_genome
from wormwars.evo.bundle import write_bundle
from wormwars.evo.evolve import evolve
from wormwars.exp02 import grid, remaps, scripted
from wormwars.exp02 import probes as P
from wormwars.exp02.manifest import check_manifest, run_manifest
from wormwars.interface import load_interface

OUT = Path("runs/exp02-screening")
PILOT_GRAPH = 101  # SH101: a shuffle reserved for pilots, never used in the main runs


def _json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _gains(name):
    c = _load(grid.EXP02_DIR / "calibration.json")[name]
    return c["forward_gain"], c["turn_gain"]


# ----------------------------------------------------------------------------- frozen inputs

def cmd_remaps(args, con, iface):
    rec = remaps.remap_record(con, iface)
    _json(grid.EXP02_DIR / "remaps.json", rec)
    print(json.dumps(rec["sets"], indent=1))


def cmd_calibrate(args, con, iface):
    base = grid.task_config(Config(), "T0")
    out = {}
    for name in grid.GRAPH_VARIANTS:
        t0 = time.perf_counter()
        cfg = grid.brain_config_for_graph(base, name)
        graph = grid.graph_for(con, name)
        cal = calib.calibrate_in_world(graph, cfg, iface, grid.TARGET_DRIVE, device=args.device)
        check = cfg.copy()
        check.world.forward_gain, check.world.turn_gain = cal.forward_gain, cal.turn_gain
        val = calib.achieved_drive(graph, check, iface, seed=1, device=args.device)
        out[name] = {**cal.as_dict(), "validation_seed1": val.as_dict(),
                     "seconds": time.perf_counter() - t0}
        print(f"{name:8} gains {cal.forward_gain:.3f}/{cal.turn_gain:.3f} in {cal.iterations} it; "
              f"validation |fwd| {val.forward:.3f} |turn| {val.turn:.3f}")
    _json(grid.EXP02_DIR / "calibration.json", out)


POLICIES = {
    "stereo": {"stereo_proportional": (
        lambda k, speed: scripted.StereoProportional(k, speed),
        {"k": [0.5, 1, 2, 4, 8], "speed": [0.4, 0.6, 0.8, 1.0]})},
    "mono": {
        "level_kinesis": (
            lambda slow, fast, threshold, turn: scripted.LevelKinesis(slow, fast, threshold, turn),
            {"slow": [0.0, 0.2], "fast": [0.6, 1.0], "threshold": [0.02, 0.05, 0.1],
             "turn": [0.0, 0.3, 0.6]}),
        "one_step_memory": (
            lambda speed, turn, threshold: scripted.OneStepMemory(speed, turn, threshold),
            {"speed": [0.6, 0.8, 1.0], "turn": [0.5, 0.9], "threshold": [0.0, 0.005, 0.02]}),
    },
}


def _unit_seeds():
    return sorted({r.run_seed for b in grid.run_schedule() for r in b})


def cmd_diagnostics(args, con, iface):
    fg, tg = _gains("N2")
    seeds = _unit_seeds()
    out = {}
    for task in ("T0", "T1", "A"):
        t0 = time.perf_counter()
        cfg = grid.task_config(Config(), task)
        cfg.world.forward_gain, cfg.world.turn_gain = fg, tg
        pols = {"stationary": scripted.Stationary(), "straight": scripted.Straight()}
        tuned = {}
        for name, (make, space) in POLICIES["mono" if task == "T1" else "stereo"].items():
            best, s = scripted.tune(make, space, cfg, iface, grid.TUNING_IDS, grid.TUNING_SEED, args.device)
            tuned[name] = {"params": best, "tuning_score": s}
            pols[name] = make(**best)
        per_seed = {}
        for seed in seeds:
            ids = SeedPool(cfg, seed).holdout
            per_seed[str(seed)] = {n: scripted.score_policy(cfg, iface, p, ids, seed, args.device).tolist()
                                   for n, p in pols.items()}
        out[task] = {"tuned": tuned, "per_seed_holdout": per_seed, "seconds": time.perf_counter() - t0}
        print(task, {n: v["params"] for n, v in tuned.items()}, f"{out[task]['seconds']:.0f}s")
    _json(grid.EXP02_DIR / "diagnostics.json", out)


# ----------------------------------------------------------------------------- one run

def _execute(spec: grid.RunSpec, con, remap_sets, device, out: Path, graph=None, gains=None) -> dict:
    cfg = grid.brain_config_for_graph(grid.task_config(Config(), spec.cell.task), spec.graph)
    cfg.evo.generations = spec.generations
    cfg.world.forward_gain, cfg.world.turn_gain = gains or _gains(spec.graph)
    graph = graph if graph is not None else grid.graph_for(con, spec.graph)
    iface = grid.interface_for(con, spec.cell.mapping, remap_sets)
    bspec = BrainSpec.from_connectome(graph, device=device)
    manifest = run_manifest(cfg, iface, bspec)
    t0 = time.perf_counter()
    # the drive of this run's own generation-0 population (same seed as evolve's initialisation)
    drive = calib.achieved_drive(graph, cfg, iface, n_strains=cfg.evo.population, seed=spec.run_seed,
                                 device=device)
    res = evolve(cfg, iface, bspec, spec.run, spec.run_seed, device=device, holdout_every=10,
                 checkpoint_ids=grid.CHECKPOINT_IDS, snapshots=spec.snapshots, verbose=False)
    pool = SeedPool(cfg, spec.run_seed)
    rec = {"key": spec.key, "task": spec.cell.task, "mapping": spec.cell.mapping, "graph": spec.graph,
           "run": spec.run, "run_seed": spec.run_seed, "generations": spec.generations,
           "gen0_drive": drive.as_dict(),
           "checkpoints": [(x.generation, x.holdout_best) for x in res.log if x.holdout_best is not None],
           "ledger_error": max(x.ledger_error for x in res.log)}
    champs = {g: res.snapshots[g] for g in spec.snapshots}
    if spec.generations > 40:
        champs[spec.generations - 1] = res.champion
    for g, champ in champs.items():
        tag = f"g{g:02d}"
        held = rollout(cfg, iface, champ, pool.holdout, spec.run_seed, device)
        rec[f"holdout_{tag}"] = held.score[0].tolist()
        eaten, pellet = float(held.eaten.sum()), float(held.pellet_eaten.sum())
        rec[f"pellet_share_{tag}"] = pellet / max(eaten + pellet, 1e-9)
        save_genome(out / f"{spec.key}-{tag}.npz", champ, 0, cfg=cfg, run_seed=spec.run_seed,
                    snapshot_generation=g, **manifest)
    rec["wall_seconds"] = time.perf_counter() - t0
    return rec


def cmd_pilot(args, con, iface):
    remap_sets = _load(grid.EXP02_DIR / "remaps.json")["sets"]
    graph = shuffled(con, PILOT_GRAPH, f"SH{PILOT_GRAPH}")
    cal = calib.calibrate_in_world(graph, grid.task_config(Config(), "T0"), iface, grid.TARGET_DRIVE,
                                   device=args.device)
    gains = (cal.forward_gain, cal.turn_gain)
    out = OUT / "pilot"
    times, probe_times = {}, {}
    for task in ("T0", "T1"):
        spec = grid.RunSpec(grid.Cell(task, "M0"), f"SH{PILOT_GRAPH}", 0, 31_000, 40, (0, 39))
        rec = _execute(spec, con, remap_sets, args.device, out, graph=graph, gains=gains)
        times[task] = rec["wall_seconds"]
        cfg = grid.task_config(Config(), task)
        cfg.world.forward_gain, cfg.world.turn_gain = gains
        champ, _ = load_genome(out / f"{spec.key}-g39.npz", BrainSpec.from_connectome(graph, device=args.device),
                               None, device=args.device)
        tp = time.perf_counter()
        _champion_probes(cfg, iface, champ, 31_000, args.device, False)
        probe_times[task] = time.perf_counter() - tp
        print(f"{task}: {rec['wall_seconds']:.0f}s end to end, probes {probe_times[task]:.0f}s, "
              f"held-out g39 {np.mean(rec['holdout_g39']):.3f}")
    per_run = float(np.mean(list(times.values())))
    runs = [r for b in grid.run_schedule() for r in b]
    run_equivalents = sum(r.generations / 40 for r in runs)
    projected = per_run * run_equivalents / 3600
    probe_h = float(np.mean(list(probe_times.values()))) * len(runs) / 3600
    _json(grid.EXP02_DIR / "pilot.json", {"graph": f"SH{PILOT_GRAPH}", "seconds_per_run": times,
                                          "probe_seconds_per_champion": probe_times,
                                          "run_equivalents": run_equivalents,
                                          "projected_grid_hours": projected,
                                          "projected_champion_probe_hours": probe_h})
    print(f"projected grid time: {projected:.2f} h for {run_equivalents:.0f} run-equivalents; "
          f"champion probes {probe_h:.2f} h")


# ----------------------------------------------------------------------------- the grid

def cmd_run(args, con, iface):
    remap_sets = _load(grid.EXP02_DIR / "remaps.json")["sets"]
    OUT.mkdir(parents=True, exist_ok=True)
    records_path = OUT / "records.jsonl"
    done = grid.read_records(records_path)
    if not (OUT / "bundle.json").exists():
        write_bundle(OUT, grid.task_config(Config(), "T0"), con,
                     extra={"script": "exp02.py run", "remaps": remap_sets,
                            "calibration": _load(grid.EXP02_DIR / "calibration.json"),
                            "schedule": [[r.key for r in b] for b in grid.run_schedule()]})
    # per-batch cost, seeded from completed batches so a resumed run does not overrun the cap
    by_unit = defaultdict(float)
    for r in done:
        by_unit[(r["graph"], r["run"])] += r["wall_seconds"]
    per_batch = max(by_unit.values(), default=0.0)
    elapsed = sum(r["wall_seconds"] for r in done)
    budget = args.max_hours * 3600
    batches = grid.pending(grid.run_schedule(), {r["key"] for r in done})
    print(f"{len(done)} runs done, {len(batches)} batches pending, {elapsed / 3600:.2f} h used")
    for batch in batches:
        if per_batch and grid.select_batches(1, elapsed, per_batch, budget) == 0:
            print(f"stopping at a batch boundary: {elapsed / 3600:.2f} h used of {args.max_hours} h")
            break
        tb = time.perf_counter()
        for spec in batch:
            rec = _execute(spec, con, remap_sets, args.device, OUT)
            with records_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec) + "\n")
            print(f"  {spec.key:32} g39 {np.mean(rec['holdout_g39']):.3f}  {rec['wall_seconds']:.0f}s",
                  flush=True)
        took = time.perf_counter() - tb
        elapsed += took
        per_batch = max(per_batch, took)


def _champion_probes(cfg, iface, champ, seed, device, with_pheromone) -> dict:
    ids = grid.CHECKPOINT_IDS
    return {
        "channels": P.channel_dependence(cfg, iface, champ, ids, seed, device, with_pheromone),
        "integrator": P.integrator_rescore(cfg, iface, champ, ids, seed, device),
        "behaviour": P.behaviour(cfg, iface, champ, ids[:4], seed, device),
    }


def cmd_probes(args, con, iface):
    remap_sets = _load(grid.EXP02_DIR / "remaps.json")["sets"]
    recs = grid.read_records(OUT / "records.jsonl")
    ids = grid.CHECKPOINT_IDS[:8]
    t_start = time.perf_counter()
    out = {"valence": [], "gen0_strength": [], "input_response": {}, "champions": {}}
    cfg1 = grid.task_config(Config(), "T1")
    graphs = ["N2"] + [f"SH{k}" for k in range(1, grid.SH_GRAPHS + 1)]
    for name in ("N2", "SH1"):
        cfg = cfg1.copy()
        cfg.world.forward_gain, cfg.world.turn_gain = _gains(name)
        spec = BrainSpec.from_connectome(grid.graph_for(con, name), device=args.device)
        for gaps in (False, True):
            out["valence"].append({"graph": name, **P.valence_check(
                spec, cfg, con, iface, 128, ids, 7, args.device, gaps)})
    for name in graphs:
        spec = BrainSpec.from_connectome(grid.graph_for(con, name), device=args.device)
        for mapping in ("M0", "R1", "R2", "MS"):
            fam = grid.interface_for(con, mapping, remap_sets)
            for mode in ("anatomical", "uniform", "permuted"):
                cfg = cfg1.copy()
                cfg.brain.init_chem_magnitude = cfg.brain.init_gap_magnitude = mode
                cfg.world.forward_gain, cfg.world.turn_gain = _gains(name)
                out["gen0_strength"].append({"graph": name, "mapping": mapping, "mode": mode,
                                             "score": P.gen0_scores(spec, cfg, fam, 32, ids, 7, args.device)})
            out["input_response"][f"{name}-{mapping}"] = P.input_response(spec, cfg1, fam, 64, args.device)
    print(f"generation-0 probes: {time.perf_counter() - t_start:.0f}s")
    for r in recs:
        cfg = grid.brain_config_for_graph(grid.task_config(Config(), r["task"]), r["graph"])
        cfg.world.forward_gain, cfg.world.turn_gain = _gains(r["graph"])
        fam = grid.interface_for(con, r["mapping"], remap_sets)
        spec = BrainSpec.from_connectome(grid.graph_for(con, r["graph"]), device=args.device)
        champ, meta = load_genome(OUT / f"{r['key']}-g39.npz", spec, None, device=args.device)
        check_manifest(meta, cfg, fam, spec)
        out["champions"][r["key"]] = _champion_probes(cfg, fam, champ, r["run_seed"], args.device,
                                                      r["task"] == "A")
    out["seconds"] = time.perf_counter() - t_start
    _json(OUT / "probes.json", out)
    print(f"probes done in {out['seconds']:.0f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["remaps", "calibrate", "diagnostics", "pilot", "run", "probes"])
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--max-hours", type=float, default=10.0)
    args = ap.parse_args()
    con = load_connectome()
    iface = load_interface(con)
    {"remaps": cmd_remaps, "calibrate": cmd_calibrate, "diagnostics": cmd_diagnostics,
     "pilot": cmd_pilot, "run": cmd_run, "probes": cmd_probes}[args.command](args, con, iface)


if __name__ == "__main__":
    main()
