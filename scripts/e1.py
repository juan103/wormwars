"""E1's positive control (experiments/E1-navigation/PREREGISTRATION.md; docs/E1/DESIGN.md v2.1).

    python scripts/e1.py pilot [--device cuda]   # pilot + tuning; writes experiments/E1-navigation/freeze.json
    python scripts/e1.py gate  [--device cuda]   # once, on the gate worlds; needs the committed freeze

Every number the pre-registration fixes is in `REGISTERED` below. The pilot applies the registered
rules mechanically and writes the freeze; nothing in it is chosen by hand. The gate refuses to run
unless the freeze is committed and unchanged, records its sha256, and runs once: it refuses to
overwrite an existing gate result. Both stages record their code provenance at the start, refuse a
dirty tree, count compute with T0's accounting, and stop at the registered cap.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e1 import controllers as C  # noqa: E402
from wormwars.e1.task import GATE_IDS, PILOT_IDS, TUNING_IDS, task_n_config  # noqa: E402
from wormwars.evo import rollout  # noqa: E402
from wormwars.evo.rollout import rollout_brain  # noqa: E402
from wormwars.exp02.scripted import LevelKinesis  # noqa: E402
from wormwars.fields import sample_bilinear  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402
from wormwars.world import World  # noqa: E402

EXP = ROOT / "experiments" / "E1-navigation"
OUT = ROOT / "runs" / "e1"
FREEZE = EXP / "freeze.json"
GATE_RESULT = EXP / "gate.json"

REGISTERED = {
    "run_seed": 1_100_001,
    "cap_gpu_hours": 8.0,  # pilot, tuning and gate together, T0's accounting (synchronised wall clock)
    "task": {"amplitude": 1.0, "radius": 1.5, "separation": 8.0, "max_separation": 0.0, "horizon": 300,
             "wall_clearance": 3.0, "sense_scale_food": 0.35},
    "sigma_rule": {"candidates": [2.0, 3.0, 4.0, 6.0], "pilot_worlds": 256, "legs_per_world": 5,
                   "usable_floor_fraction_of_amplitude": 0.05, "required_share": 0.90,
                   "if_none": "the largest candidate, flagged"},
    "own_body": {"pilot_worlds": 64, "ticks": 100, "speed": 0.5, "turn": 0.2, "min_wall_distance": 3.0},
    "generation0": {"genomes": 256, "pilot_worlds": 64, "genome_seed": 11},
    "tuning": {
        "worlds": 256, "combos_per_chunk": 64,
        "grids": {
            "S-const": {"k": [1, 2, 4, 8, 16, 32, 64, 256, 1024, 8192], "speed": [0.4, 0.6, 0.8, 1.0],
                        "turn": [-0.2, -0.1, 0.0, 0.1, 0.2]},
            "M-avg": {"slow": [0.4, 0.7, 1.0], "fast": [0.4, 0.7, 1.0], "threshold": [0.0, 0.02, 0.05, 0.1],
                      "turn": [0.0, 0.1, 0.2], "fall_turn": [0.4, 0.7, 1.0], "fall_threshold": [0.0, 0.001, 0.005]},
            "K": {"slow": [0.2, 0.5, 0.8, 1.0], "fast": [0.2, 0.5, 0.8, 1.0], "threshold": [0.02, 0.05, 0.1, 0.2],
                  "turn": [0.05, 0.1, 0.2, 0.4]},
            "constant": {"speed": [0.2, 0.4, 0.6, 0.8, 1.0],
                         "turn": [round(-0.6 + 0.1 * i, 1) for i in range(13)]},
            "random-walk": {"speed": [0.4, 0.7, 1.0], "rate": [0.2, 0.4, 0.8, 1.0],
                            "persistence": [0.5, 0.8, 0.9, 0.95, 0.99]},
            "wall-follower": {"speed": [0.4, 0.7, 1.0], "seek_turn": [-0.1, -0.2, -0.4],
                              "avoid_turn": [0.4, 0.8, 1.0],
                              "threshold_above_own_body": [0.05, 0.1, 0.2, 0.4, 0.8, 1.6]},
        },
        "s_small_gain_max_k": 32,  # S-const is also tuned at k <= 32 and reported, non-gating
        "random_walk_seed": 0,
        "tie": "the first maximum in grid order; between navigators, S-const",
    },
    "oracle": {"k": 2.0, "speed": 1.0},
    "gate": {
        "worlds": 1024,
        "reliability": {"min_arrivals": 2, "required_share": 0.80},
        "baselines": ["constant", "random-walk", "wall-follower", "K"],
        "baseline_margin": 0.5,  # targets per episode, on the lower bound of the paired difference
        "cue": {"probe": "mirrored", "required_drop_fraction_of_real_mean": 0.5},
        "interval": {"method": "paired percentile bootstrap over worlds, one-sided 95% lower bound",
                     "resamples": 10_000, "seed": 0},
        "mode": "CUDA default mode; each controller is one strain on all gate worlds, in one rollout",
    },
}


# ----------------------------------------------------------------------------- plumbing

def provenance() -> dict:
    def git(*a):
        return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
    return {"git_commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain", "--", "wormwars", "scripts", "configs"))}


def spent_hours() -> float:
    path = OUT / "compute.json"
    if not path.exists():
        return 0.0
    return float(json.loads(path.read_text(encoding="utf-8"))["totals"]["seconds_timed"]) / 3600


def check_cap(t0: float) -> None:
    if spent_hours() + (time.perf_counter() - t0) / 3600 > REGISTERED["cap_gpu_hours"]:
        raise SystemExit(f"the registered cap of {REGISTERED['cap_gpu_hours']} GPU-hours is reached")


def config(sigma: float):
    t = REGISTERED["task"]
    c = task_n_config(sigma=sigma, amplitude=t["amplitude"], radius=t["radius"], separation=t["separation"],
                      max_separation=t["max_separation"], horizon=t["horizon"])
    c.world.target_wall_clearance = t["wall_clearance"]
    c.world.sense_scale_food = t["sense_scale_food"]
    return c


def _json(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1), encoding="utf-8")


# ----------------------------------------------------------------------------- pilot measures

def coverage(iface, spec, sigma: float, device) -> dict:
    """The σ rule's measure: for each leg start (the spawn, then each previous centre) the scent of
    the *next* target at that point, from the actual sampled field, as a fraction of the amplitude."""
    r = REGISTERED["sigma_rule"]
    cfg = config(sigma)
    ids = PILOT_IDS[: r["pilot_worlds"]]
    brain = C.scripted(iface, C.ConstantMotion(0.0, 0.0), cfg, device=device)
    w = World(cfg, iface, brain, torch.zeros(len(ids), 1, dtype=torch.long), run_seed=REGISTERED["run_seed"],
              world_ids=ids, device=device)
    starts = [w.pos[:, 0, 0]] + [w.target_centres[:, k] for k in range(r["legs_per_world"] - 1)]
    vals, sat = [], 0.0
    for k, p in enumerate(starts):
        w.target_index = torch.full((len(ids),), k, dtype=torch.long, device=w.device)
        f = w.target_field()
        v = sample_bilinear(f.unsqueeze(1).contiguous(), p.view(-1, 1, 2))[:, 0, 0]
        vals.append(v / cfg.world.target_amplitude)
    v = torch.stack(vals).flatten().cpu().numpy()
    peak_current = cfg.world.target_amplitude * cfg.world.sense_scale_food * max(iface.sensor_gain) * cfg.brain.input_gain
    return {"sigma": sigma, "leg_starts": int(v.size),
            "share_above_floor": float((v >= r["usable_floor_fraction_of_amplitude"]).mean()),
            "median": float(np.median(v)), "p10": float(np.quantile(v, 0.1)),
            "peak_input_current": float(peak_current), "input_max": float(cfg.brain.input_max),
            "clamp_saturated": bool(peak_current >= cfg.brain.input_max)}


def choose_sigma(rows: list[dict]) -> tuple[float, bool]:
    r = REGISTERED["sigma_rule"]
    for row in sorted(rows, key=lambda x: x["sigma"]):
        if row["share_above_floor"] >= r["required_share"]:
            return row["sigma"], False
    return max(r["candidates"]), True


def own_body_level(iface, spec, sigma, device) -> dict:
    """The largest collision current the wey's own body produces at the front and front-right
    sensors, measured while the head is at least `min_wall_distance` cells from the wall ring."""
    o = REGISTERED["own_body"]
    cfg = config(sigma)
    ids = PILOT_IDS[: o["pilot_worlds"]]
    brain = C.scripted(iface, C.ConstantMotion(o["speed"], o["turn"]), cfg, device=device)
    w = World(cfg, iface, brain, torch.zeros(len(ids), 1, dtype=torch.long), run_seed=REGISTERED["run_seed"],
              world_ids=ids, device=device)
    names = list(iface.signal_names)
    gain = {s: float(iface.sensor_gain[names.index(f"collision_{s}")]) * cfg.brain.input_gain
            for s in ("front", "front_right")}
    best = 0.0
    for _ in range(o["ticks"]):
        w.tick()
        head = w.pos[:, 0, 0]
        dist = torch.minimum(head - 1.0, (w.side - 1.0) - head).min(dim=-1).values
        far = dist >= o["min_wall_distance"]
        for s in gain:
            x = w.last_signals[f"collision_{s}"][:, 0, 0] * gain[s]
            if bool(far.any()):
                best = max(best, float(x[far].max()))
    return {"own_body_max_current": best, "ticks": o["ticks"], "worlds": len(ids)}


def generation0(iface, spec, sigma, device) -> dict:
    g0 = REGISTERED["generation0"]
    cfg = config(sigma)
    ids = PILOT_IDS[: g0["pilot_worlds"]]
    g = Genome.random(spec, cfg.brain, g0["genomes"], generator=torch.Generator().manual_seed(g0["genome_seed"]))
    g = Genome(g.spec.to(device), g.cfg, **{k: None if v is None else v.to(device) for k, v in g.params().items()})
    torch.cuda.synchronize() if str(device).startswith("cuda") else None
    t = time.perf_counter()
    r = rollout(cfg, iface, g, ids, REGISTERED["run_seed"], device, chunk_worlds=g0["genomes"] * len(ids))
    torch.cuda.synchronize() if str(device).startswith("cuda") else None
    dt = time.perf_counter() - t
    per_genome = r.score.mean(axis=1)
    return {"genomes": g0["genomes"], "worlds": len(ids), "share_genomes_scoring_zero": float((per_genome == 0).mean()),
            "mean_count": float(r.score.mean()), "max_genome_mean": float(per_genome.max()),
            "strain_worlds_per_s": g0["genomes"] * len(ids) / dt,
            "composition": {"strains_per_chunk": g0["genomes"], "worlds_per_strain": len(ids), "weys_per_world": 1}}


# ----------------------------------------------------------------------------- tuning

MAKERS = {
    "S-const": lambda k, speed, turn: C.s_const(k, speed, turn),
    "M-avg": lambda slow, fast, threshold, turn, fall_turn, fall_threshold: C.m_avg(slow, fast, threshold, turn, fall_turn, fall_threshold),
    "K": lambda slow, fast, threshold, turn: LevelKinesis(slow, fast, threshold, turn),
    "constant": lambda speed, turn: C.ConstantMotion(speed, turn),
    "random-walk": lambda speed, rate, persistence: C.PersistentRandomWalk(
        speed, rate, persistence, seed=REGISTERED["tuning"]["random_walk_seed"]),
    "wall-follower": lambda speed, seek_turn, avoid_turn, threshold: C.WallFollower(speed, seek_turn, avoid_turn, threshold),
}


def grid_for(name: str, own_level: float, max_k: float | None = None) -> dict:
    g = dict(REGISTERED["tuning"]["grids"][name])
    if name == "wall-follower":
        g = {k: v for k, v in g.items() if k != "threshold_above_own_body"}
        g["threshold"] = [own_level + d for d in REGISTERED["tuning"]["grids"]["wall-follower"]["threshold_above_own_body"]]
    if max_k is not None:
        g["k"] = [k for k in g["k"] if k <= max_k]
    return g


def tune(name: str, grid: dict, cfg, iface, ids, device, t0) -> dict:
    """Every grid point as one strain, in chunks of a registered size; the first maximum of the mean
    count over the tuning worlds wins."""
    keys = list(grid)
    combos = list(itertools.product(*(grid[k] for k in keys)))
    per = REGISTERED["tuning"]["combos_per_chunk"]
    means = []
    for lo in range(0, len(combos), per):
        check_cap(t0)
        chunk = combos[lo:lo + per]
        n = len(chunk)
        params = {k: torch.tensor([c[i] for c in chunk], dtype=torch.float32, device=device).view(n, 1)
                  for i, k in enumerate(keys)}
        brain = C.scripted(iface, MAKERS[name](**params), cfg, n_strains=n, device=device)
        with acct.category("tuning"):
            r = rollout_brain(cfg, iface, brain, ids, REGISTERED["run_seed"], device)
        means.extend(r.score.mean(axis=1).tolist())
    i = int(np.argmax(means))
    return {"params": dict(zip(keys, [float(x) for x in combos[i]])), "tuned_mean": float(means[i]),
            "grid_size": len(combos)}


def cmd_pilot(args):
    prov = provenance()
    if prov["dirty"] and not args.smoke:
        raise SystemExit("uncommitted changes in wormwars/, scripts/ or configs/: commit before the pilot")
    if FREEZE.exists():
        raise SystemExit(f"{FREEZE} exists: the pilot runs once")
    t0 = time.perf_counter()
    check_cap(t0)
    con = load_connectome()
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con)
    with acct.category("measure"):
        cov = [coverage(iface, spec, s, args.device) for s in REGISTERED["sigma_rule"]["candidates"]]
    sigma, flagged = choose_sigma(cov)
    with acct.category("measure"):
        body = own_body_level(iface, spec, sigma, args.device)
        gen0 = generation0(iface, spec, sigma, args.device)
    cfg = config(sigma)
    ids = TUNING_IDS[: REGISTERED["tuning"]["worlds"]]
    tuned = {}
    for name in ("S-const", "M-avg", "K", "constant", "random-walk", "wall-follower"):
        tuned[name] = tune(name, grid_for(name, body["own_body_max_current"]), cfg, iface, ids, args.device, t0)
    tuned["S-const k<=32"] = tune("S-const", grid_for("S-const", 0.0, REGISTERED["tuning"]["s_small_gain_max_k"]),
                                  cfg, iface, ids, args.device, t0)
    oracle = C.OracleBrain(iface, 302, cfg.world.forward_gain, cfg.world.turn_gain, device=args.device,
                           **REGISTERED["oracle"])
    with acct.category("tuning"):
        tuned["oracle"] = {"params": REGISTERED["oracle"], "tuned_mean": float(
            rollout_brain(cfg, iface, oracle, ids, REGISTERED["run_seed"], args.device).score.mean())}
    navigator = "S-const" if tuned["S-const"]["tuned_mean"] >= tuned["M-avg"]["tuned_mean"] else "M-avg"
    freeze = {"registered": REGISTERED, "provenance_at_start": prov, "device": args.device,
              "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None, "torch": torch.__version__,
              "sigma": sigma, "sigma_flagged": flagged, "coverage": cov, "own_body": body, "generation0": gen0,
              "tuned": tuned, "navigator": navigator, "seconds": time.perf_counter() - t0}
    _json(FREEZE, freeze)
    print(json.dumps({k: freeze[k] for k in ("sigma", "sigma_flagged", "navigator")}, indent=1))
    print({k: round(v["tuned_mean"], 3) for k, v in tuned.items()})


# ----------------------------------------------------------------------------- the gate

def lower_bound(diff: np.ndarray) -> float:
    iv = REGISTERED["gate"]["interval"]
    rng = np.random.default_rng(iv["seed"])
    idx = rng.integers(0, diff.size, size=(iv["resamples"], diff.size))
    return float(np.quantile(diff[idx].mean(axis=1), 0.05))


def secondary(events: dict, horizon: int) -> dict:
    act, reach, path = events["activation_tick"][0], events["reach_tick"][0], events["path_length"][0]
    first = reach[:, 0]
    latency = np.where(first >= 0, first + 1, horizon)
    legs = reach >= 0
    leg_time = (reach - act + 1)[legs]
    x, y = events["target_x"][0], events["target_y"][0]
    start_x = np.concatenate([np.full((x.shape[0], 1), np.nan), x[:, :-1]], axis=1)
    start_y = np.concatenate([np.full((y.shape[0], 1), np.nan), y[:, :-1]], axis=1)
    straight = np.hypot(x - start_x, y - start_y)
    eff = (straight / np.maximum(path, 1e-9))[:, 1:][legs[:, 1:]]  # legs after the first, whose start is known
    return {"first_arrival_share": float((first >= 0).mean()), "latency_mean": float(latency.mean()),
            "leg_time_median": float(np.median(leg_time)) if leg_time.size else None,
            "path_efficiency_median": float(np.median(eff)) if eff.size else None}


def cmd_gate(args):
    prov = provenance()
    if prov["dirty"] and not args.smoke:
        raise SystemExit("uncommitted changes in wormwars/, scripts/ or configs/: commit before the gate")
    if GATE_RESULT.exists():
        raise SystemExit(f"{GATE_RESULT} exists: the gate worlds are used once")
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(FREEZE)], cwd=ROOT, capture_output=True).returncode == 0
    clean = not subprocess.check_output(["git", "status", "--porcelain", "--", str(FREEZE)], cwd=ROOT, text=True).strip()
    if not (tracked and clean) and not args.smoke:
        raise SystemExit("the freeze must be committed and unchanged before the gate")
    freeze_sha = hashlib.sha256(FREEZE.read_bytes()).hexdigest()
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze["registered"] != json.loads(json.dumps(REGISTERED)):
        raise SystemExit("the freeze's registered numbers differ from this script's")
    t0 = time.perf_counter()
    check_cap(t0)
    con = load_connectome()
    iface = load_interface(con)
    cfg = config(freeze["sigma"])
    G = REGISTERED["gate"]
    ids = GATE_IDS[: G["worlds"]]
    tuned = freeze["tuned"]

    def run(name, params, probe="real"):
        c = cfg.copy()
        c.world.food_probe = probe
        if name == "oracle":
            brain = C.OracleBrain(iface, 302, c.world.forward_gain, c.world.turn_gain, device=args.device, **params)
        else:
            brain = C.scripted(iface, MAKERS[name](**params), c, device=args.device)
        check_cap(t0)
        with acct.category("final"):
            r = rollout_brain(c, iface, brain, ids, REGISTERED["run_seed"], args.device)
        return r.score[0], r.events

    nav = freeze["navigator"]
    counts, events = {}, {}
    for label, name, params, probe in (
            [("navigator", nav, tuned[nav]["params"], "real"),
             ("navigator mirrored", nav, tuned[nav]["params"], "mirrored"),
             ("navigator constant", nav, tuned[nav]["params"], "constant"),
             ("S-const k<=32", "S-const", tuned["S-const k<=32"]["params"], "real"),
             ("oracle", "oracle", tuned["oracle"]["params"], "real")]
            + [(b, b, tuned[b]["params"], "real") for b in G["baselines"]]
            + [(f"{b} constant", b, tuned[b]["params"], "constant") for b in G["baselines"]]):
        counts[label], events[label] = run(name, params, probe)
    real = counts["navigator"]
    rel = float((real >= G["reliability"]["min_arrivals"]).mean())
    rules = {"reliability": {"share": rel, "required": G["reliability"]["required_share"],
                             "passed": rel >= G["reliability"]["required_share"]}}
    rules["baselines"] = {}
    for b in G["baselines"]:
        d = real - counts[b]
        lb = lower_bound(d)
        rules["baselines"][b] = {"mean_difference": float(d.mean()), "lower_95": lb, "margin": G["baseline_margin"],
                                 "passed": lb > G["baseline_margin"]}
    d = real - counts["navigator mirrored"]
    need = G["cue"]["required_drop_fraction_of_real_mean"] * float(real.mean())
    lb = lower_bound(d)
    rules["cue"] = {"mean_drop": float(d.mean()), "lower_95": lb, "required": need, "passed": lb >= need}
    passed = rules["reliability"]["passed"] and all(v["passed"] for v in rules["baselines"].values()) \
        and rules["cue"]["passed"]
    oracle_mean = float(counts["oracle"].mean())
    result = {
        "outcome": "E1 positive control: passed" if passed else "E1 positive control: not passed",
        "failed_rules": [k for k, v in {"reliability": rules["reliability"]["passed"],
                                        **{f"beats {b}": v["passed"] for b, v in rules["baselines"].items()},
                                        "uses the cue": rules["cue"]["passed"]}.items() if not v],
        "rules": rules, "freeze_sha256": freeze_sha, "provenance_at_start": prov, "device": args.device,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None, "worlds": len(ids),
        "means": {k: float(v.mean()) for k, v in counts.items()},
        "fraction_of_oracle": {k: (float(v.mean()) / oracle_mean if oracle_mean > 0 else None) for k, v in counts.items()},
        "secondary": {k: secondary(events[k], REGISTERED["task"]["horizon"]) for k in counts},
        "per_world_counts": {k: v.astype(int).tolist() for k, v in counts.items()},
        "seconds": time.perf_counter() - t0,
    }
    _json(GATE_RESULT, result)
    print(result["outcome"], result["failed_rules"])
    print({k: round(v, 3) for k, v in result["means"].items()})


SMOKE_IDS = np.arange(10_000)  # outside every E1 range: a smoke run never sees pilot, tuning or gate worlds


def use_smoke(command: str) -> None:
    """Tiny sizes, world ids outside every E1 range, and a scratch output folder, to exercise the
    whole pipeline without touching the real worlds or the real freeze and gate files. Never used
    for results."""
    global EXP, OUT, FREEZE, GATE_RESULT, PILOT_IDS, TUNING_IDS, GATE_IDS
    EXP = OUT = ROOT / "runs" / "e1-smoke"
    FREEZE, GATE_RESULT = EXP / "freeze.json", EXP / "gate.json"
    PILOT_IDS = TUNING_IDS = GATE_IDS = SMOKE_IDS
    for f in ((FREEZE, GATE_RESULT) if command == "pilot" else (GATE_RESULT,)):
        f.unlink(missing_ok=True)
    R = REGISTERED
    R["task"]["horizon"] = 40
    R["sigma_rule"]["pilot_worlds"] = 8
    R["own_body"].update(pilot_worlds=4, ticks=20)
    R["generation0"].update(genomes=4, pilot_worlds=4)
    R["tuning"]["worlds"] = 8
    R["tuning"]["grids"] = {k: {kk: vv[:2] for kk, vv in g.items()} for k, g in R["tuning"]["grids"].items()}
    R["gate"]["worlds"] = 16
    R["gate"]["interval"]["resamples"] = 200


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=["pilot", "gate"])
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--smoke", action="store_true", help="tiny sizes, scratch folder, no git checks")
    args = ap.parse_args()
    if args.smoke:
        use_smoke(args.command)
    {"pilot": cmd_pilot, "gate": cmd_gate}[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    run_script(main, out_default=str(ROOT / "runs" / ("e1-smoke" if "--smoke" in sys.argv else "e1")),
               default="measure", name="e1")
