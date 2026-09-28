"""E1's positive control (experiments/E1-navigation/PREREGISTRATION.md; docs/E1/DESIGN.md v2.1).

    python scripts/e1.py pilot          # pilot + tuning; writes experiments/E1-navigation/freeze.json
    python scripts/e1.py gate           # once, on the gate worlds; needs the committed, pushed freeze
    python scripts/e1.py pilot --smoke  # tiny sizes, world ids outside every E1 range, runs/e1-smoke/

Every number the pre-registration fixes is in `REGISTERED`. The pilot applies the registered rules
mechanically and writes the freeze; nothing is chosen by hand. The guards (D095) are functions below:
- a formal stage needs CUDA, a clean tree (code and the pre-registration), and a pushed HEAD;
- each stage writes an exclusive start marker before touching its worlds, so an interrupted stage
  is never silently rerun;
- the gate re-derives every choice in the freeze from the freeze's own rows, and refuses code that
  differs from the pilot's commit;
- the cap is checked before every rollout and once more before any result is written.
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
from wormwars.brain import BrainSpec, Genome  # noqa: E402
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
GATE_EVENTS = EXP / "gate_events.npz"
SMOKE_IDS = np.arange(10_000)  # outside every E1 range: smoke runs and throughput never see E1 worlds
GUARDED = ["wormwars", "scripts", "configs", "experiments/E1-navigation/PREREGISTRATION.md"]

REGISTERED = {
    "run_seed": 1_100_001,
    "cap_gpu_hours": 8.0,  # pilot, tuning and gate together, T0's accounting (synchronised wall clock)
    # each stage starts at this index of its range: the first smoke run touched the first 8 pilot
    # and tuning worlds, and a debug run the first 32 pilot worlds (PREREGISTRATION.md §7)
    "id_offset": 1000,
    "task": {"amplitude": 1.0, "radius": 1.5, "separation": 8.0, "max_separation": 0.0, "horizon": 300,
             "wall_clearance": 3.0, "sense_scale_food": 0.35},
    "sigma_rule": {"candidates": [2.0, 3.0, 4.0, 6.0], "pilot_worlds": 256, "legs_per_world": 5,
                   "usable_floor_fraction_of_amplitude": 0.05, "required_share": 0.90,
                   "if_none": "the largest candidate, flagged"},
    "own_body": {"pilot_worlds": 64, "ticks": 100, "speed": 0.5, "turn": 0.2, "min_wall_distance": 3.0},
    "generation0": {"genomes": 256, "pilot_worlds": 64, "genome_seed": 11},
    "throughput": {"shape": "32 strains x 8 worlds x 1 wey, and 4 and 8 such batches together",
                   "repeats": 3, "ids": "0-7 (outside every E1 range)"},
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
        "reliability": {"min_arrivals": 2, "required_share": 0.80},  # at least 820 of 1 024 episodes
        "baselines": ["constant", "random-walk", "wall-follower", "K"],
        "baseline_margin": 0.5,  # targets per episode, on the lower bound of the paired difference
        "cue": {"probe": "mirrored", "contrast": "0.5 x real - mirrored, per world", "required_lower_bound": 0.0},
        "interval": {"method": "paired percentile bootstrap over worlds, one-sided 95% lower bound",
                     "resamples": 10_000, "seed": 0},
        "mode": "CUDA default mode; each controller is one strain on all gate worlds, in one rollout",
    },
}
CONTROLS = ("S-const", "M-avg", "K", "constant", "random-walk", "wall-follower")


class CapReached(Exception):
    pass


# ----------------------------------------------------------------------------- guards

def git(*a) -> str:
    return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()


def provenance() -> dict:
    return {"git_commit": git("rev-parse", "HEAD"), "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(git("status", "--porcelain", "--", *GUARDED)),
            "torch": torch.__version__, "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}


def require_formal(device: str, prov: dict) -> None:
    """A formal stage: CUDA, a clean tree (code and the pre-registration), and HEAD pushed."""
    if not (str(device).startswith("cuda") and torch.cuda.is_available()):
        raise SystemExit("formal E1 stages run on CUDA only (PREREGISTRATION.md §2)")
    if prov["dirty"]:
        raise SystemExit(f"uncommitted changes in {GUARDED}: commit first")
    subprocess.run(["git", "fetch", "-q", "origin"], cwd=ROOT, check=True)
    pushed = subprocess.run(["git", "merge-base", "--is-ancestor", "HEAD", f"origin/{prov['branch']}"],
                            cwd=ROOT).returncode == 0
    if not pushed:
        raise SystemExit("HEAD is not pushed: the registration and the freeze are public before the run")


def start_marker(stage: str, prov: dict) -> Path:
    """Exclusive: created before the stage touches its worlds. If it exists, the stage has started
    before, and it is not rerun (PREREGISTRATION.md §5)."""
    path = EXP / f"{stage}-started.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as f:
            json.dump({"stage": stage, "provenance": prov,
                       "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, f, indent=1)
    except FileExistsError:
        raise SystemExit(f"{path.name} exists: the {stage} has started before and is not rerun") from None
    return path


def write_json(path: Path, doc) -> None:
    """LF line endings on every platform, so the committed bytes are the written bytes (D056's class
    of bug; Fable, D095)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=1))
        f.write("\n")


def file_sha256(path: Path) -> str:
    """The sha256 of a text file with line endings normalised to LF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def spent_hours() -> float:
    path = OUT / "compute.json"
    if not path.exists():
        return 0.0
    return float(json.loads(path.read_text(encoding="utf-8"))["totals"]["seconds_timed"]) / 3600


def check_cap(t0: float) -> None:
    if spent_hours() + (time.perf_counter() - t0) / 3600 > REGISTERED["cap_gpu_hours"]:
        raise CapReached(f"the registered cap of {REGISTERED['cap_gpu_hours']} GPU-hours is reached")


def ids_for(stage: str, n: int) -> np.ndarray:
    base = {"pilot": PILOT_IDS, "tuning": TUNING_IDS, "gate": GATE_IDS}[stage]
    off = REGISTERED["id_offset"]
    return base[off:off + n]


def id_record(ids: np.ndarray) -> dict:
    return {"first": int(ids[0]), "last": int(ids[-1]), "count": int(len(ids))}


# ----------------------------------------------------------------------------- the task

def config(sigma: float):
    t = REGISTERED["task"]
    c = task_n_config(sigma=sigma, amplitude=t["amplitude"], radius=t["radius"], separation=t["separation"],
                      max_separation=t["max_separation"], horizon=t["horizon"])
    c.world.target_wall_clearance = t["wall_clearance"]
    c.world.sense_scale_food = t["sense_scale_food"]
    return c


def _sync(device):
    if str(device).startswith("cuda"):
        torch.cuda.synchronize()


# ----------------------------------------------------------------------------- pilot measures

def coverage(iface, sigma: float, device, ids) -> dict:
    """The σ rule's measure: for each leg start (the spawn, then each previous centre) the scent of
    the *next* target at that point, from the actual sampled field, as a fraction of the amplitude."""
    r = REGISTERED["sigma_rule"]
    cfg = config(sigma)
    brain = C.scripted(iface, C.ConstantMotion(0.0, 0.0), cfg, device=device)
    w = World(cfg, iface, brain, torch.zeros(len(ids), 1, dtype=torch.long), run_seed=REGISTERED["run_seed"],
              world_ids=ids, device=device)
    starts = [w.pos[:, 0, 0]] + [w.target_centres[:, k] for k in range(r["legs_per_world"] - 1)]
    vals = []
    for k, p in enumerate(starts):
        w.target_index = torch.full((len(ids),), k, dtype=torch.long, device=w.device)
        f = w.target_field()
        v = sample_bilinear(f.unsqueeze(1).contiguous(), p.view(-1, 1, 2))[:, 0, 0]
        vals.append(v / cfg.world.target_amplitude)
    v = torch.stack(vals).flatten().cpu().numpy()
    peak = cfg.world.target_amplitude * cfg.world.sense_scale_food * max(iface.sensor_gain) * cfg.brain.input_gain
    return {"sigma": sigma, "leg_starts": int(v.size),
            "share_above_floor": float((v >= r["usable_floor_fraction_of_amplitude"]).mean()),
            "median": float(np.median(v)), "p10": float(np.quantile(v, 0.1)),
            "peak_input_current": float(peak), "input_max": float(cfg.brain.input_max),
            "clamp_saturated": bool(peak >= cfg.brain.input_max)}


def choose_sigma(rows: list[dict]) -> tuple[float, bool]:
    r = REGISTERED["sigma_rule"]
    for row in sorted(rows, key=lambda x: x["sigma"]):
        if row["share_above_floor"] >= r["required_share"]:
            return row["sigma"], False
    return max(r["candidates"]), True


def own_body_level(iface, sigma, device, ids) -> dict:
    """The largest collision current the wey's own body produces at the front and front-right
    sensors, while its head is at least `min_wall_distance` cells from the wall ring."""
    o = REGISTERED["own_body"]
    cfg = config(sigma)
    brain = C.scripted(iface, C.ConstantMotion(o["speed"], o["turn"]), cfg, device=device)
    w = World(cfg, iface, brain, torch.zeros(len(ids), 1, dtype=torch.long), run_seed=REGISTERED["run_seed"],
              world_ids=ids, device=device)
    names = list(iface.signal_names)
    gain = {s: float(iface.sensor_gain[names.index(f"collision_{s}")]) * cfg.brain.input_gain
            for s in ("front", "front_right")}
    best, samples = 0.0, 0
    for _ in range(o["ticks"]):
        w.tick()
        head = w.pos[:, 0, 0]
        far = torch.minimum(head - 1.0, (w.side - 1.0) - head).min(dim=-1).values >= o["min_wall_distance"]
        n = int(far.sum())
        samples += n
        if n:
            for s in gain:
                best = max(best, float((w.last_signals[f"collision_{s}"][:, 0, 0] * gain[s])[far].max()))
    if samples == 0:
        raise SystemExit("no own-body sample away from the wall: the level cannot be measured")
    return {"own_body_max_current": best, "samples": samples, "ticks": o["ticks"], "worlds": id_record(ids)}


def generation0(iface, spec, sigma, device, ids) -> dict:
    g0 = REGISTERED["generation0"]
    cfg = config(sigma)
    g = Genome.random(spec, cfg.brain, g0["genomes"], generator=torch.Generator().manual_seed(g0["genome_seed"]))
    g = Genome(g.spec.to(device), g.cfg, **{k: None if v is None else v.to(device) for k, v in g.params().items()})
    r = rollout(cfg, iface, g, ids, REGISTERED["run_seed"], device, chunk_worlds=g0["genomes"] * len(ids))
    per_genome = r.score.mean(axis=1)
    return {"worlds": id_record(ids), "genomes": g0["genomes"],
            "share_genomes_scoring_zero": float((per_genome == 0).mean()), "mean_count": float(r.score.mean()),
            "max_genome_mean": float(per_genome.max()),
            "composition": {"strains_per_chunk": g0["genomes"], "worlds_per_strain": len(ids), "weys_per_world": 1}}


def throughput(iface, spec, sigma, device) -> dict:
    """04a's evolution shape, on ids outside every E1 range (Fable, D095)."""
    cfg = config(sigma)
    reps = REGISTERED["throughput"]["repeats"]
    out = {}
    for runs in (1, 4, 8):
        g = Genome.random(spec, cfg.brain, 32 * runs, generator=torch.Generator().manual_seed(1))
        g = Genome(g.spec.to(device), g.cfg, **{k: None if v is None else v.to(device) for k, v in g.params().items()})
        ids = SMOKE_IDS[:8]
        rollout(cfg, iface, g, ids, 1, device, chunk_worlds=256 * runs, ticks=5)
        ts = []
        for _ in range(reps):
            _sync(device)
            t = time.perf_counter()
            rollout(cfg, iface, g, ids, 1, device, chunk_worlds=256 * runs)
            _sync(device)
            ts.append(time.perf_counter() - t)
        med = statistics.median(ts)
        out[str(runs)] = {"strains": 32 * runs, "worlds_per_strain": 8, "strain_worlds_per_s": 32 * runs * 8 / med,
                          "range_s": [min(ts), max(ts)]}
    return out


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


def combos_of(grid: dict) -> tuple[list, list]:
    keys = list(grid)
    return keys, [list(c) for c in itertools.product(*(grid[k] for k in keys))]


def tune(name: str, grid: dict, cfg, iface, ids, device, t0) -> dict:
    """Every grid point as one strain, in chunks of a registered size; the first maximum of the mean
    count over the tuning worlds wins. Every point's mean is kept, for the gate's audit."""
    keys, combos = combos_of(grid)
    per = REGISTERED["tuning"]["combos_per_chunk"]
    means, per_world = [], []
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
        per_world.extend(list(r.score))
    i = int(np.argmax(means))
    winner = per_world[i]
    return {"keys": keys, "grid": grid, "means": means, "winner_index": i,
            "params": dict(zip(keys, [float(x) for x in combos[i]])), "tuned_mean": float(means[i]),
            "share_at_least_1": float((winner >= 1).mean()), "share_at_least_2": float((winner >= 2).mean()),
            "chunking": {"combos_per_chunk": per, "last_chunk": len(combos) - per * ((len(combos) - 1) // per)}}


def navigator_of(tuned: dict) -> str:
    return "S-const" if tuned["S-const"]["tuned_mean"] >= tuned["M-avg"]["tuned_mean"] else "M-avg"


def cmd_pilot(args):
    prov = provenance()
    if not args.smoke:
        require_formal(args.device, prov)
    if FREEZE.exists():
        raise SystemExit(f"{FREEZE} exists: the pilot runs once")
    marker = start_marker("pilot", prov)
    t0 = time.perf_counter()
    check_cap(t0)
    con = load_connectome()
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con)
    r = REGISTERED
    with acct.category("measure"):
        cov_ids = ids_for("pilot", r["sigma_rule"]["pilot_worlds"])
        cov = [coverage(iface, s, args.device, cov_ids) for s in r["sigma_rule"]["candidates"]]
    sigma, flagged = choose_sigma(cov)
    with acct.category("measure"):
        body = own_body_level(iface, sigma, args.device, ids_for("pilot", r["own_body"]["pilot_worlds"]))
        gen0 = generation0(iface, spec, sigma, args.device, ids_for("pilot", r["generation0"]["pilot_worlds"]))
        speed = throughput(iface, spec, sigma, args.device)
    cfg = config(sigma)
    ids = ids_for("tuning", r["tuning"]["worlds"])
    tuned = {name: tune(name, grid_for(name, body["own_body_max_current"]), cfg, iface, ids, args.device, t0)
             for name in CONTROLS}
    tuned["S-const k<=32"] = tune("S-const", grid_for("S-const", 0.0, r["tuning"]["s_small_gain_max_k"]),
                                  cfg, iface, ids, args.device, t0)
    oracle = C.OracleBrain(iface, 302, cfg.world.forward_gain, cfg.world.turn_gain, device=args.device, **r["oracle"])
    check_cap(t0)
    with acct.category("tuning"):
        o = rollout_brain(cfg, iface, oracle, ids, r["run_seed"], args.device).score[0]
    tuned["oracle"] = {"params": r["oracle"], "tuned_mean": float(o.mean()),
                       "share_at_least_1": float((o >= 1).mean()), "share_at_least_2": float((o >= 2).mean())}
    check_cap(t0)  # the final budget decision, before anything is written
    freeze = {"registered": r, "provenance_at_start": prov, "device": args.device,
              "worlds": {"coverage": id_record(cov_ids), "tuning": id_record(ids)},
              "sigma": sigma, "sigma_flagged": flagged, "coverage": cov, "own_body": body, "generation0": gen0,
              "throughput_04a_shape": speed, "tuned": tuned, "navigator": navigator_of(tuned),
              "seconds": time.perf_counter() - t0, "start_marker": marker.name}
    write_json(FREEZE, freeze)
    print(json.dumps({k: freeze[k] for k in ("sigma", "sigma_flagged", "navigator")}, indent=1))
    print({k: round(v["tuned_mean"], 3) for k, v in tuned.items()})


# ----------------------------------------------------------------------------- the gate

def validate_freeze(freeze: dict) -> None:
    """Re-derive every choice in the freeze from its own rows (Fable, Astra, D095): the registered
    numbers, σ from the coverage rows, each tuned winner from its grid and means (the first maximum,
    with its parameters in the grid), the small-gain grid, the oracle, and the navigator rule."""
    if freeze["registered"] != json.loads(json.dumps(REGISTERED)):
        raise SystemExit("the freeze's registered numbers differ from this script's")
    if list(choose_sigma(freeze["coverage"])) != [freeze["sigma"], freeze["sigma_flagged"]]:
        raise SystemExit("the freeze's σ does not follow from its coverage rows")
    own = freeze["own_body"]["own_body_max_current"]
    for name in (*CONTROLS, "S-const k<=32"):
        t = freeze["tuned"][name]
        base = "S-const" if name == "S-const k<=32" else name
        grid = grid_for(base, own, REGISTERED["tuning"]["s_small_gain_max_k"] if name == "S-const k<=32" else None)
        keys, combos = combos_of(grid)
        if t["keys"] != keys or json.loads(json.dumps(t["grid"])) != json.loads(json.dumps(grid)) \
                or len(t["means"]) != len(combos):
            raise SystemExit(f"{name}: the freeze's grid is not the registered grid")
        i = int(np.argmax(t["means"]))
        if i != t["winner_index"] or t["params"] != dict(zip(keys, [float(x) for x in combos[i]])) \
                or t["tuned_mean"] != float(t["means"][i]):
            raise SystemExit(f"{name}: the freeze's winner is not the first maximum of its grid")
    if freeze["tuned"]["oracle"]["params"] != REGISTERED["oracle"]:
        raise SystemExit("the freeze's oracle is not the registered oracle")
    if freeze["navigator"] != navigator_of(freeze["tuned"]):
        raise SystemExit("the freeze's navigator does not follow the registered rule")


def require_same_code_as_pilot(freeze: dict) -> None:
    """Only the freeze and other outputs may change between the pilot and the gate."""
    diff = git("diff", "--name-only", freeze["provenance_at_start"]["git_commit"], "HEAD", "--", *GUARDED)
    if diff:
        raise SystemExit(f"code or the pre-registration changed since the pilot: {diff.splitlines()[:5]}")


def lower_bound(values: np.ndarray) -> float:
    """One-sided 95% lower bound of the mean of per-world values: the 5th percentile of the
    bootstrap distribution over worlds."""
    iv = REGISTERED["gate"]["interval"]
    rng = np.random.default_rng(iv["seed"])
    idx = rng.integers(0, values.size, size=(iv["resamples"], values.size))
    return float(np.quantile(values[idx].mean(axis=1), 0.05))


def secondary(events: dict, horizon: int) -> dict:
    """First-arrival success; latency as mean of min(first arrival, horizon); the median time of
    finished legs; and path efficiency, the head's straight-line displacement over its path, for
    finished legs (at most 1 by construction)."""
    act, reach, path = events["activation_tick"][0], events["reach_tick"][0], events["path_length"][0]
    first = reach[:, 0]
    latency = np.where(first >= 0, first + 1, horizon)
    legs = reach >= 0
    leg_time = (reach - act + 1)[legs]
    disp = np.hypot(events["end_x"][0] - events["start_x"][0], events["end_y"][0] - events["start_y"][0])
    eff = (disp / np.maximum(path, 1e-9))[legs]
    return {"first_arrival_share": float((first >= 0).mean()), "latency_mean": float(latency.mean()),
            "finished_leg_time_median": float(np.median(leg_time)) if leg_time.size else None,
            "finished_leg_path_efficiency_median": float(np.median(eff)) if eff.size else None}


def gate_rules(counts: dict) -> dict:
    G = REGISTERED["gate"]
    real = counts["navigator"]
    n_ok = int((real >= G["reliability"]["min_arrivals"]).sum())
    rules = {"reliability": {"episodes_with_at_least_2": n_ok, "episodes": int(real.size),
                             "share": n_ok / real.size, "required_share": G["reliability"]["required_share"],
                             "passed": n_ok / real.size >= G["reliability"]["required_share"]},
             "baselines": {}}
    for b in G["baselines"]:
        d = real - counts[b]
        lb = lower_bound(d)
        rules["baselines"][b] = {"mean_difference": float(d.mean()), "lower_95": lb, "margin": G["baseline_margin"],
                                 "passed": lb > G["baseline_margin"]}
    contrast = 0.5 * real - counts["navigator mirrored"]
    lb = lower_bound(contrast)
    rules["cue"] = {"contrast": G["cue"]["contrast"], "mean": float(contrast.mean()), "lower_95": lb,
                    "required": G["cue"]["required_lower_bound"], "passed": lb >= G["cue"]["required_lower_bound"]}
    rules["passed"] = rules["reliability"]["passed"] and all(v["passed"] for v in rules["baselines"].values()) \
        and rules["cue"]["passed"]
    rules["failed"] = [k for k, v in {"reliability": rules["reliability"]["passed"],
                                      **{f"beats {b}": v["passed"] for b, v in rules["baselines"].items()},
                                      "uses the cue": rules["cue"]["passed"]}.items() if not v]
    return rules


def cmd_gate(args):
    prov = provenance()
    if not args.smoke:
        require_formal(args.device, prov)
    if GATE_RESULT.exists():
        raise SystemExit(f"{GATE_RESULT} exists: the gate worlds are used once")
    if not args.smoke:
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(FREEZE)], cwd=ROOT,
                                 capture_output=True).returncode == 0
        if not tracked or git("status", "--porcelain", "--", str(FREEZE)):
            raise SystemExit("the freeze must be committed, unchanged and pushed before the gate")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    validate_freeze(freeze)
    if not args.smoke:
        require_same_code_as_pilot(freeze)
    marker = start_marker("gate", prov)
    t0 = time.perf_counter()
    con = load_connectome()
    iface = load_interface(con)
    cfg = config(freeze["sigma"])
    G = REGISTERED["gate"]
    ids = ids_for("gate", G["worlds"])
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
    arms = [("navigator", nav, tuned[nav]["params"], "real"), ("navigator mirrored", nav, tuned[nav]["params"], "mirrored"),
            ("oracle", "oracle", tuned["oracle"]["params"], "real")]
    for name in (*CONTROLS, "S-const k<=32"):  # every controller, and its own blind level (the constant probe)
        base = "S-const" if name == "S-const k<=32" else name
        if name != nav:  # the navigator's real arm is "navigator"
            arms.append((name, base, tuned[name]["params"], "real"))
        arms.append((f"{name} constant", base, tuned[name]["params"], "constant"))
    counts, events = {}, {}
    result = {"freeze_sha256_lf": file_sha256(FREEZE), "provenance_at_start": prov, "device": args.device,
              "worlds": id_record(ids), "start_marker": marker.name}
    try:
        for label, name, params, probe in arms:
            counts[label], events[label] = run(name, params, probe)
        check_cap(t0)  # the final budget decision, before the result is written
    except CapReached as e:
        result.update(outcome="E1 positive control: not completed (the registered cap was reached)", error=str(e),
                      arms_completed=list(counts))
        write_json(GATE_RESULT, result)
        raise SystemExit(result["outcome"]) from None
    counts[nav], events[nav] = counts["navigator"], events["navigator"]
    rules = gate_rules(counts)
    oracle_mean = float(counts["oracle"].mean())
    result.update({
        "outcome": "E1 positive control: passed" if rules["passed"] else "E1 positive control: not passed",
        "failed_rules": rules["failed"], "rules": rules, "navigator": nav,
        "means": {k: float(v.mean()) for k, v in counts.items()},
        "fraction_of_oracle": {k: (float(v.mean()) / oracle_mean if oracle_mean > 0 else None) for k, v in counts.items()},
        "secondary": {k: secondary(events[k], REGISTERED["task"]["horizon"]) for k in counts},
        "per_world_counts": {k: v.astype(int).tolist() for k, v in counts.items()},
        "events_file": GATE_EVENTS.name, "seconds": time.perf_counter() - t0})
    np.savez_compressed(GATE_EVENTS, world_ids=ids, **{f"{label}|{k}": v[0] for label, ev in events.items()
                                                       for k, v in ev.items() if label != nav})
    write_json(GATE_RESULT, result)
    print(result["outcome"], result["failed_rules"])
    print({k: round(v, 3) for k, v in result["means"].items()})


# ----------------------------------------------------------------------------- smoke

def use_smoke(command: str) -> None:
    """Tiny sizes, world ids outside every E1 range, and a scratch folder: exercises the pipeline
    without touching E1's worlds or its real freeze and gate files. Never used for results."""
    global EXP, OUT, FREEZE, GATE_RESULT, GATE_EVENTS, PILOT_IDS, TUNING_IDS, GATE_IDS
    EXP = OUT = ROOT / "runs" / "e1-smoke"
    FREEZE, GATE_RESULT, GATE_EVENTS = EXP / "freeze.json", EXP / "gate.json", EXP / "gate_events.npz"
    PILOT_IDS = TUNING_IDS = GATE_IDS = SMOKE_IDS
    stale = (FREEZE, GATE_RESULT, EXP / "pilot-started.json", EXP / "gate-started.json") if command == "pilot" \
        else (GATE_RESULT, EXP / "gate-started.json")
    for f in stale:
        f.unlink(missing_ok=True)
    R = REGISTERED
    R["id_offset"] = 0
    R["task"]["horizon"] = 40
    R["sigma_rule"]["pilot_worlds"] = 8
    R["own_body"].update(pilot_worlds=4, ticks=20)
    R["generation0"].update(genomes=4, pilot_worlds=4)
    R["throughput"]["repeats"] = 1
    R["tuning"]["worlds"] = 8
    R["tuning"]["grids"] = {k: {kk: vv[:2] for kk, vv in g.items()} for k, g in R["tuning"]["grids"].items()}
    R["gate"]["worlds"] = 16
    R["gate"]["interval"]["resamples"] = 200


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=["pilot", "gate"])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true", help="tiny sizes, ids outside E1, scratch folder, no git checks")
    args = ap.parse_args()
    if args.smoke:
        use_smoke(args.command)
    {"pilot": cmd_pilot, "gate": cmd_gate}[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    run_script(main, out_default=str(ROOT / "runs" / ("e1-smoke" if "--smoke" in sys.argv else "e1")),
               default="measure", name="e1")
