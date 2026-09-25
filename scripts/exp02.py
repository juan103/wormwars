"""Experiment 02, the screening fraction. See experiments/02-screening/DESIGN.md.

    py -3.13 scripts/exp02.py remaps        # choose R1, R2, MS by the fixed rule -> remaps.json
    py -3.13 scripts/exp02.py calibrate     # in-world gains per graph variant   -> calibration.json
    py -3.13 scripts/exp02.py diagnostics   # tune and score scripted controllers -> diagnostics.json
    py -3.13 scripts/exp02.py pilot         # timed end-to-end runs on SH101 (discarded) -> pilot.json
    py -3.13 scripts/exp02.py run           # the grid, in balanced resumable batches
    py -3.13 scripts/exp02.py probes        # evaluation-only probes on every champion -> probes.json
    py -3.13 scripts/exp02.py report        # estimates and tripwires -> analysis.json
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
from wormwars.exp02 import analysis as An
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
        cal = calib.calibrate_in_world(graph, cfg, iface, grid.TARGET_DRIVE,
                                       n_strains=grid.CALIBRATION_STRAINS, device=args.device)
        check = cfg.copy()
        check.world.forward_gain, check.world.turn_gain = cal.forward_gain, cal.turn_gain
        val = calib.achieved_drive(graph, check, iface, n_strains=grid.CALIBRATION_STRAINS, seed=1,
                                   device=args.device)
        out[name] = {**cal.as_dict(), "validation_seed1": val.as_dict(),
                     "seconds": time.perf_counter() - t0}
        print(f"{name:8} gains {cal.forward_gain:.3f}/{cal.turn_gain:.3f} in {cal.iterations} it; "
              f"validation |fwd| {val.forward:.3f} |turn| {val.turn:.3f}")
    _json(grid.EXP02_DIR / "calibration.json", out)


K_GRID = {"slow": [0.0, 0.25, 0.5, 0.75, 1.0], "fast": [0.5, 0.75, 1.0],
          "threshold": [0.0003, 0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0], "turn": [0.0, 0.1, 0.2, 0.4, 0.7]}
FALL_GRID = {"fall_turn": [0.4, 0.7, 1.0], "fall_threshold": [0.0, 0.001, 0.003]}
K_STEREO = [8.0, 32.0, 128.0, 512.0, 2048.0, 8192.0]
# values at a grid edge that are physical bounds, not choices: the edge rule ignores these
PHYSICAL = {"fast": {1.0}, "slow": {0.0, 1.0}, "turn": {0.0}, "fall_turn": {1.0}, "fall_threshold": {0.0}}
JITTER_RADII = [1.0, 2.0, 3.0]
HOLD_TICKS = [4, 8, 16]


def _near(v, vals):
    i = vals.index(v)
    return vals[max(0, i - 1): i + 2]


def _edges(params, grid_):
    out = []
    for k, v in params.items():
        vals = sorted(grid_[k])
        if len(vals) > 1 and v in (vals[0], vals[-1]) and v not in PHYSICAL.get(k, set()):
            out.append(f"{k}={v}")
    return out


def _tune_family(cfg, iface, task, device):
    """Nested families: K (memoryless) always; M (K + memory) for mono, S (K + stereo) otherwise.
    M and S are tuned around K's optimum and fall back to K exactly if they do not beat it, so
    the family on top of K can never score below it on the tuning worlds."""
    tn = lambda make, g: scripted.tune_batched(make, g, cfg, iface, grid.TUNING_IDS, grid.TUNING_SEED, device)  # noqa: E731
    kp, ks = tn(lambda **p: scripted.LevelKinesis(**p), K_GRID)
    local = {k: _near(kp[k], K_GRID[k]) for k in K_GRID}
    out = {"K": {"params": kp, "tuning_score": ks, "edges": _edges(kp, K_GRID)}}
    if task == "T1":
        mp, ms = tn(lambda **p: scripted.MemoryKinesis(**p), dict(local, **FALL_GRID))
        if ms < ks:
            mp, ms = dict(kp, fall_turn=kp["turn"], fall_threshold=0.0), ks
        out["M"] = {"params": mp, "tuning_score": ms,
                    "edges": _edges({k: mp[k] for k in FALL_GRID}, FALL_GRID)}
    else:
        sp, ss = tn(lambda **p: scripted.StereoKinesis(**p), dict(local, k=K_STEREO))
        if ss < ks:
            sp, ss = dict(kp, k=0.0), ks
        out["S"] = {"params": sp, "tuning_score": ss, "edges": _edges({"k": sp["k"]}, {"k": K_STEREO})}
    return out


def _policy(name, params):
    return {"K": scripted.LevelKinesis, "M": scripted.MemoryKinesis, "S": scripted.StereoKinesis}[name](**params)


def _val(cfg, iface, pol, ids, seed, device):
    b = scripted.ScriptedBrain(iface, 302, pol, cfg.world.forward_gain, cfg.world.turn_gain, device=device)
    r = scripted.rollout_brain(cfg, iface, b, ids, seed, device)
    return r.score[0], r.eaten[0] / np.maximum(r.food_start[0], 1e-9)


def _share(best, base, straight, n=20000):
    rng = np.random.default_rng(0)
    idx = rng.integers(0, len(best), (n, len(best)))
    s = (best - base)[idx].mean(1) / (best - straight)[idx].mean(1)
    return {"estimate": float((best - base).mean() / (best - straight).mean()),
            "lo": float(np.quantile(s, 0.025)), "hi": float(np.quantile(s, 0.975))}


def _paired(a, b, n=20000):
    d = np.asarray(a) - np.asarray(b)
    rng = np.random.default_rng(0)
    m = d[rng.integers(0, len(d), (n, len(d)))].mean(1)
    return {"estimate": float(d.mean()), "lo": float(np.quantile(m, 0.025)), "hi": float(np.quantile(m, 0.975))}


def _history_probe_validation(cfg, iface, fam, device):
    """Which history ablation is valid: the memoryless controller must be unchanged within its
    interval, and the memory controller must fall toward it. Returns every candidate's numbers."""
    K, M = _policy("K", fam["K"]["params"]), _policy("M", fam["M"]["params"])
    base_k, _ = _val(cfg, iface, K, grid.GATE_IDS, grid.GATE_SEED, device)
    base_m, _ = _val(cfg, iface, M, grid.GATE_IDS, grid.GATE_SEED, device)
    out = []
    for kind, values, field in (("jitter", JITTER_RADII, "food_probe_radius"), ("hold", HOLD_TICKS, "food_probe_hold")):
        for v in values:
            c = cfg.copy()
            c.world.food_probe = kind
            setattr(c.world, field, v)
            k, _ = _val(c, iface, K, grid.GATE_IDS, grid.GATE_SEED, device)
            m, _ = _val(c, iface, M, grid.GATE_IDS, grid.GATE_SEED, device)
            k_change = _paired(k, base_k)
            memory_left = _paired(m, k)       # what memory still adds under the ablation
            memory_before = _paired(base_m, base_k)
            valid = (k_change["lo"] <= 0 <= k_change["hi"]) and memory_left["hi"] < memory_before["lo"]
            out.append({"kind": kind, "value": v, "K_change": k_change, "memory_gain_under_probe": memory_left,
                        "memory_gain_without": memory_before, "valid": bool(valid)})
    return out


def cmd_diagnostics(args, con, iface):
    fg, tg = _gains("N2")
    seeds = _unit_seeds()
    out = {}
    for task in ("T0", "T1", "A"):
        t0 = time.perf_counter()
        cfg = grid.task_config(Config(), task)
        cfg.world.forward_gain, cfg.world.turn_gain = fg, tg
        fam = _tune_family(cfg, iface, task, args.device)
        pols = {"stationary": scripted.Stationary(), "straight": scripted.Straight()}
        pols.update({name: _policy(name, v["params"]) for name, v in fam.items()})
        # the gate, on validation worlds disjoint from tuning and from every run's held-out worlds
        val = {n: _val(cfg, iface, p, grid.GATE_IDS, grid.GATE_SEED, args.device) for n, p in pols.items()}
        top = "M" if task == "T1" else "S"
        gate = {
            "share": _share(val[top][0], val["K"][0], val["straight"][0]),
            "median_eaten_best": float(np.median(val[top][1])),
            "means": {n: float(v[0].mean()) for n, v in val.items()},
            "edges": sum((v["edges"] for v in fam.values()), []),
        }
        per_seed = {}
        for seed in seeds:
            ids = SeedPool(cfg, seed).holdout
            per_seed[str(seed)] = {n: scripted.score_policy(cfg, iface, p, ids, seed, args.device).tolist()
                                   for n, p in pols.items()}
        out[task] = {"tuned": fam, "gate": gate, "per_seed_holdout": per_seed,
                     "seconds": time.perf_counter() - t0}
        if task == "T1":
            out[task]["history_probe"] = _history_probe_validation(cfg, iface, fam, args.device)
        print(task, "share", {k: round(v, 3) for k, v in gate["share"].items()},
              "eaten", round(gate["median_eaten_best"], 2), "edges", gate["edges"] or "-",
              f"{out[task]['seconds']:.0f}s", flush=True)
    t0 = grid.task_config(Config(), "T0")
    t0.world.forward_gain, t0.world.turn_gain = fg, tg
    s_on_t0 = out["T0"]["gate"]["means"]["S"]
    out["stereo_vs_memory"] = {"S_on_T0": s_on_t0, "M_on_T1": out["T1"]["gate"]["means"]["M"]}
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
                                   n_strains=grid.CALIBRATION_STRAINS, device=args.device)
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


def cmd_report(args, con, iface):
    recs = An.normalise(grid.read_records(OUT / "records.jsonl"), _load(grid.EXP02_DIR / "diagnostics.json"))
    diag = _load(grid.EXP02_DIR / "diagnostics.json")
    prb = _load(OUT / "probes.json")
    cal = _load(grid.EXP02_DIR / "calibration.json")
    main_recs = [r for r in recs if r["task"] in ("T0", "T1")]
    out = {}
    for tag in ("norm_g00", "norm_g39"):
        n2, sh = An.units(main_recs, tag)
        out[tag] = {
            "I_T0": An.paired_bootstrap(n2, sh, lambda a, s: An.interaction(a, s, "T0")),
            "I_T1": An.paired_bootstrap(n2, sh, lambda a, s: An.interaction(a, s, "T1")),
            "I_T1_minus_I_T0": An.paired_bootstrap(n2, sh, An.task_contrast),
            "advantage": {f"{t}-{m}": An.paired_bootstrap(n2, sh, lambda a, s, c=(t, m): An.advantage(a, s, c))
                          for t, m in grid.MAIN},
            "variance_T0": An.variance_components(sh, "T0"),
            "variance_T1": An.variance_components(sh, "T1"),
            "loo_T1": An.leave_one_graph_out(n2, sh, "T1"),
        }
    n2, sh = An.units(recs, "norm_g39")
    matched_adv = lambda a, s: float(np.mean([An.advantage(a, s, ("T1", m)) for m in An.MATCHED]))  # noqa: E731
    sh_matched = lambda s: float(np.mean([An._sh_mean(s, ("T1", m)) for m in An.MATCHED]))  # noqa: E731
    summary = {
        "temporal": An.temporal_check(prb["champions"]),
        "memory_vs_memoryless": An.memory_vs_memoryless(diag),
        "anchor": An.paired_bootstrap(n2, sh, lambda a, s: An.advantage(a, s, ("A", "M0"))),
        "sign_01b": An.sign_of_01b(Path("runs/exp01b-direction-corrected/records.json")),
        "drive": An.drive_check(recs, cal, grid.TARGET_DRIVE),
        "integrator": An.integrator_interactions(recs, prb["champions"]),
        "late_cells": An.late_cells(recs),
        "ms_vs_matched": An.paired_bootstrap(n2, sh, lambda a, s: An.advantage(a, s, ("T1", "MS")) - matched_adv(a, s)),
        "r1_minus_r2": An.paired_bootstrap(n2, sh, lambda a, s: An.advantage(a, s, ("T1", "R1")) - An.advantage(a, s, ("T1", "R2"))),
        "sh_mapping": An.paired_bootstrap(n2, sh, lambda a, s: An._sh_mean(s, ("T1", "M0")) - sh_matched(s)),
        "valence_no_gap_max": max(v["max_abs_score_diff"] for v in prb["valence"] if not v["gaps"]),
        "strength": An.strength_contrast(recs, "norm_g39"),
        "pellet_share_g39": float(np.mean([r["pellet_share_g39"] for r in recs])),
        "max_ledger_error": max(r["ledger_error"] for r in recs),
    }
    out["summary"] = summary
    out["tripwires"] = An.tripwires(summary)
    _json(OUT / "analysis.json", out)
    for tw in out["tripwires"]:
        print(f"{'FIRED' if tw['fired'] else 'ok   '}  {tw['name']}")
    for tag in ("norm_g00", "norm_g39"):
        for k in ("I_T0", "I_T1", "I_T1_minus_I_T0"):
            b = out[tag][k]
            print(f"{tag} {k:16} {b['estimate']:+.4f} [{b['lo']:+.4f}, {b['hi']:+.4f}]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["remaps", "calibrate", "diagnostics", "pilot", "run", "probes", "report"])
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--max-hours", type=float, default=10.0)
    args = ap.parse_args()
    con = load_connectome()
    iface = load_interface(con)
    {"remaps": cmd_remaps, "calibrate": cmd_calibrate, "diagnostics": cmd_diagnostics,
     "pilot": cmd_pilot, "run": cmd_run, "probes": cmd_probes, "report": cmd_report}[args.command](args, con, iface)


if __name__ == "__main__":
    main()
