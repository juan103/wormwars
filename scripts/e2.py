"""E2: a short optimizer screen (experiments/E2-optimizer-screen/PREREGISTRATION.md; docs/E2/DESIGN.md).

    python scripts/e2.py project                # the budget projection: every training shape, on smoke ids
    python scripts/e2.py pilot --stage 1        # the ES pilot: σ ∈ {0.5, 1, 2} at a learning rate of 0.3 σ
    python scripts/e2.py pilot --stage 2        # the learning rate at the chosen σ; selects the ES's setting
    python scripts/e2.py train --method ga      # 02's GA, through 04a's `evolve_batch`
    python scripts/e2.py train --method random  # random sampling
    python scripts/e2.py train --method es      # OpenAI-ES at the pilot's setting, generations 0-622
    python scripts/e2.py extend                 # the ES's descriptive extension, generations 623-999
    python scripts/e2.py evaluate               # once, on the hold-out
    python scripts/e2.py <stage> --smoke        # tiny sizes, ids 0-9 999, runs/e2-smoke/
    python scripts/e2.py <stage> --rerun --reason "..."   # once, after a crash, an interrupt or a kill

The stages run in that order, each needing the one before. A training stage that stops is rerun
once; if its rerun stops too, it is final and not completed, and the later stages go on (the
decision rule says what an incomplete method means). The projection and the pilot must complete.

Every number the pre-registration fixes is in `REGISTERED`, and every rule is applied mechanically.
Task N and the controls are E1's, imported from `scripts/e1.py` unchanged; the GA is 04a's
`evolve_batch` with 04a's registered settings; the guards are the shared ones in
`wormwars/registration.py`. Genome files and the ES's saved state stay local under `runs/e2/`
(they derive from the connectome's weights, which this project does not redistribute; D028).
"""

from __future__ import annotations

import argparse
import calendar
import dataclasses
import hashlib
import importlib
import importlib.util
import json
import os
import statistics
import sys
import time
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e2 import loops as LP  # noqa: E402
from wormwars.e2.optimizers import SCALES  # noqa: E402
from wormwars.evo.genomes import genome_hash, load_population, save_population  # noqa: E402
from wormwars.evo.rollout import rollout_brain  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

rollout_mod = importlib.import_module("wormwars.evo.rollout")  # the module: `wormwars.evo.rollout` is also a function

_spec = importlib.util.spec_from_file_location("e1_frozen", ROOT / "scripts" / "e1.py")
E1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E1)  # Task N's config and the controls, unchanged

EXP = ROOT / "experiments" / "E2-optimizer-screen"
OUT = ROOT / "runs" / "e2"
PREREG = "experiments/E2-optimizer-screen/PREREGISTRATION.md"
E1_FREEZE = ROOT / "experiments" / "E1-navigation" / "freeze.json"
E1_GATE = ROOT / "experiments" / "E1-navigation" / "gate.json"
E1_INPUTS = ["experiments/E1-navigation/freeze.json", "experiments/E1-navigation/gate.json"]
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PREREG, *E1_INPUTS]
SMOKE_IDS = np.arange(10_000)  # outside every E1, 04a and E2 range
SMOKE = False

# Seeds: one per run number, shared by the three methods, so run r of each method starts from the
# same generation-0 population on the same generation-0 worlds (paired starts). The pilot's runs share
# their seeds across settings (paired settings). Every group is disjoint from the others and from 04a's
# 1 104 000-1 109 999.
FORMAL_SEED_BASE = 1_120_000
PILOT_SEED_BASE = 1_121_000
# moved from 1 129 000 after the development smoke projection used 1 129 000-1 129 002 (review v1, D120)
PROJECTION_SEED_BASE = 1_129_100
SMOKE_SEED_BASE = 1_128_000
SMOKE_PILOT_SEED_BASE = 1_128_500
SMOKE_PROJECTION_SEED_BASE = 1_128_900

REGISTERED = {
    "world_seed": 1_100_001,  # E1's run seed: with the world id it generates each world and its targets
    "task_sigma": 6.0,  # E1's frozen σ for Task N (not the ES's σ)
    "cap_gpu_hours": 7.0,  # every stage together, T0's accounting across attempts
    # 02's GA exactly as 04a registered it (a test checks the equality)
    "ga": {"population": 32, "elites": 3, "truncation": 8, "worlds_per_strain": 8, "generations": 1000,
           "islands": 1, "mutation": {"w_sigma": 0.08, "g_sigma": 0.04, "tau_sigma": 0.15,
                                      "bias_sigma": 0.05, "p_mutate": 1.0}},
    # generations are counted from 0: a method with n runs generations 0 .. n-1; the extension
    # continues the formal ES runs from generation `es` to `extension` - 1
    "generations": {"ga": 1000, "random": 1000, "es": 623, "extension": 1000, "pilot": 200},
    "runs": {"n": 8, "seed_base": FORMAL_SEED_BASE},
    "es": {"pairs": 16, "encoding_scales": SCALES, "beta1": 0.9, "beta2": 0.999, "eps": 1e-8,
           "start": "the best of generation 0's 32 random genomes by training count, ties to the earliest",
           "candidate": "the mean, decoded, after that generation's update"},
    "pilot": {"sigmas": [0.5, 1.0, 2.0], "stage1_lr_multiple": 0.3, "lr_multiples": [0.1, 0.3, 1.0],
              "replicates": 3, "seed_base": PILOT_SEED_BASE, "generations": 200,
              "select": "the highest total validation count at the last checkpoint over the setting's runs; "
                        "ties in the order of `tie_order` (the middle setting first)",
              "tie_order": {"sigma": [1.0, 0.5, 2.0], "lr_multiple": [0.3, 0.1, 1.0]}},
    "ids": {"pilot_train": {"base": 995_000_000, "span": 200_000},
            "pilot_validation": {"first": 995_200_000, "worlds": 256},
            "train": {"base": 995_300_000, "span": 500_000},
            "validation": {"first": 995_800_000, "worlds": 256},
            "holdout": {"first": 995_900_000, "worlds": 1024}},
    "checkpoint_every": 25,
    "decision": {"margin": 0.5, "above_ga_median": 6, "floor_margin": 0.5},
    "probes": ["real", "mirrored", "constant"],
    "controls": ["constant", "random-walk", "wall-follower", "K", "S-const", "S-const k<=32", "M-avg", "oracle"],
    "projection": {"generations_timed": 6, "seed_base": PROJECTION_SEED_BASE, "max_training_hours": 5.5},
    "rerun": ("once per stage, from scratch with the same seeds, after a crash, an interrupt or a kill, with the "
              "reason written first; never after the cap. A training stage whose rerun also stops is final and "
              "not completed"),
    "rerun_kill_tail_seconds": 900,  # charged beyond a killed attempt's last file write (04a, D107)
    # the descriptive extension starts only if the cap's remainder covers its projected time and this
    # reserve for the evaluation, so it can never use up the budget of the primary result (review v2)
    "evaluation_reserve_hours": 0.5,
}
METHODS = ("ga", "random", "es")
STAGES = ["project", "pilot-1", "pilot-2", "train-ga", "train-random", "train-es", "extend", "evaluate"]
RECORD = {"project": "projection", "pilot-1": "pilot-1", "pilot-2": "pilot-2", "train-ga": "train-ga",
          "train-random": "train-random", "train-es": "train-es", "extend": "extension", "evaluate": "evaluation"}
WHAT = {"project": "the projection", "pilot-1": "pilot stage 1", "pilot-2": "pilot stage 2",
        "train-ga": "the GA's batch", "train-random": "random sampling's batch", "train-es": "the ES's batch",
        "extend": "the extension", "evaluate": "the evaluation"}
OUTCOMES = {"replace": "E2: the ES replaces 02's GA as E3's provisional default (unshaped fitness)",
            "keep": ("E2: keep 02's GA (unshaped fitness; the ES did not satisfy both replacement criteria after "
                     "paying for its tuning)"),
            "es incomplete": ("E2: keep 02's GA (unshaped fitness; the ES's batch did not complete, so no comparison "
                              "was made)"),
            "no decision": "E2: no decision (02's GA did not complete)",
            "over limit": "E2: not started (the projection exceeds its limit)",
            "skipped": "not run (the cap's remainder is kept for the evaluation)",
            "cap": "E2: not completed (the registered cap was reached)",
            "stopped": "E2: not completed (the run stopped)"}
FLOOR = {"clears": "the GA clears the random-sampling floor (random sampling's mean is more than 0.5 below it)",
         "diagnose": ("diagnose first: random sampling's mean is at least the GA's minus 0.5; saturation, noise and "
                      "budget are diagnosed before building on the task, whatever the ES did"),
         "not made": "the floor check is not made (a batch did not complete)"}


# ----------------------------------------------------------------------------- registered arithmetic

def n_checkpoints(start: int, stop: int, every: int) -> int:
    """Checkpoints among generations start .. stop-1: every multiple of `every`, and the last."""
    return len({g for g in range(start, stop) if g % every == 0} | {stop - 1})


def pilot_runs() -> tuple[int, int]:
    p = REGISTERED["pilot"]
    return len(p["sigmas"]) * p["replicates"], (len(p["lr_multiples"]) - 1) * p["replicates"]


def allowance() -> dict:
    """Selection episodes per method: training plus the checkpoint validations that select champions
    (design v2.2). The ES pays for its pilot."""
    g, every, R = REGISTERED["generations"], REGISTERED["checkpoint_every"], REGISTERED["runs"]["n"]
    per_gen = REGISTERED["ga"]["population"] * REGISTERED["ga"]["worlds_per_strain"]
    V, PV = REGISTERED["ids"]["validation"]["worlds"], REGISTERED["ids"]["pilot_validation"]["worlds"]
    run = lambda n, vw: n * per_gen + n_checkpoints(0, n, every) * vw  # noqa: E731
    pilot = sum(pilot_runs()) * run(g["pilot"], PV)
    formal = R * run(g["es"], V)
    return {"ga": R * run(g["ga"], V), "random": R * run(g["random"], V), "es": pilot + formal,
            "es_parts": {"pilot": pilot, "formal": formal}}


def training_plan() -> dict:
    """What the projection projects: each training stage's shape, generations and checkpoints."""
    g, every = REGISTERED["generations"], REGISTERED["checkpoint_every"]
    return {"pilot-1": {"shape": "pilot-1", "generations": g["pilot"], "checkpoints": n_checkpoints(0, g["pilot"], every)},
            "pilot-2": {"shape": "pilot-2", "generations": g["pilot"], "checkpoints": n_checkpoints(0, g["pilot"], every)},
            "train-ga": {"shape": "ga", "generations": g["ga"], "checkpoints": n_checkpoints(0, g["ga"], every)},
            "train-random": {"shape": "random", "generations": g["random"],
                             "checkpoints": n_checkpoints(0, g["random"], every)},
            "train-es": {"shape": "es", "generations": g["es"], "checkpoints": n_checkpoints(0, g["es"], every)},
            "extend": {"shape": "es", "generations": g["extension"] - g["es"],
                       "checkpoints": n_checkpoints(g["es"], g["extension"], every)}}


def id_spans() -> dict:
    return {k: (v["base"], v["base"] + v["span"]) if "base" in v else (v["first"], v["first"] + v["worlds"])
            for k, v in REGISTERED["ids"].items()}


def seed_groups() -> dict:
    p = REGISTERED["pilot"]
    return {"formal": [FORMAL_SEED_BASE + i for i in range(8)],
            "pilot": [PILOT_SEED_BASE + k for k in range(3)],
            "projection": [PROJECTION_SEED_BASE + i for i in range(max(8, len(p["sigmas"]) * 3))],
            "smoke": [SMOKE_SEED_BASE + i for i in range(8)],
            "smoke pilot": [SMOKE_PILOT_SEED_BASE + k for k in range(3)],
            "smoke projection": [SMOKE_PROJECTION_SEED_BASE + i for i in range(9)]}


def _totals_by(rows: list[dict], key: str) -> dict:
    tot = {}
    for r in rows:
        tot[r[key]] = tot.get(r[key], 0) + r["total"]
    return tot


def select_sigma(rows: list[dict]) -> float:
    """Stage 1: the σ whose runs at the stage-1 learning rate have the highest total validation count
    at the last checkpoint; ties in the registered order (σ 1, then 0.5, then 2: review v1, so an
    all-zero pilot does not pick the setting least able to leave a plateau). Every setting has the
    same number of runs."""
    m = REGISTERED["pilot"]["stage1_lr_multiple"]
    tot = _totals_by([r for r in rows if r["lr_multiple"] == m], "sigma")
    order = REGISTERED["pilot"]["tie_order"]["sigma"]
    return min(tot, key=lambda s: (-tot[s], order.index(s)))


def select_rate(rows: list[dict], sigma: float) -> float:
    """Stage 2: at the chosen σ, the learning-rate multiple with the highest total; ties in the
    registered order (0.3, then 0.1, then 1)."""
    tot = _totals_by([r for r in rows if r["sigma"] == sigma], "lr_multiple")
    order = REGISTERED["pilot"]["tie_order"]["lr_multiple"]
    return min(tot, key=lambda m: (-tot[m], order.index(m)))


def uninformative(rows: list[dict]) -> bool:
    """Every setting compared in a stage has the same total: the selection is the tie order alone."""
    key = "sigma" if len({r["sigma"] for r in rows}) > 1 else "lr_multiple"
    return len(set(_totals_by(rows, key).values())) == 1


def decide(totals: dict, complete: dict, worlds: int) -> dict:
    """The registered decision, in exact arithmetic. `totals[method]` holds each champion's hold-out
    count summed over the `worlds` worlds; a champion's mean is its total / worlds."""
    D = REGISTERED["decision"]
    means = {k: (Fraction(sum(v), len(v) * worlds) if v else None) for k, v in totals.items()}
    out = {"means": {k: (float(v) if v is not None else None) for k, v in means.items()}, "complete": dict(complete)}
    if not complete["ga"] or means["ga"] is None:
        return {**out, "outcome": OUTCOMES["no decision"], "floor": FLOOR["not made"], "provisional": False}
    ga_median = statistics.median(Fraction(t, worlds) for t in totals["ga"])
    es_ok = complete["es"] and means["es"] is not None
    if not complete["es"]:
        verdict = "es incomplete"
    above = sum(Fraction(t, worlds) > ga_median for t in totals["es"]) if es_ok else 0
    margin_ok = es_ok and means["es"] - means["ga"] >= Fraction(D["margin"])
    replace = bool(margin_ok and above >= D["above_ga_median"])
    if complete["es"]:
        verdict = "replace" if replace else "keep"
    if not complete["random"] or means["random"] is None:
        floor = "not made"
    else:
        floor = "diagnose" if means["random"] >= means["ga"] - Fraction(D["floor_margin"]) else "clears"
    return {**out, "outcome": OUTCOMES[verdict], "floor": FLOOR[floor],
            "provisional": floor == "not made", "ga_median": float(ga_median), "es_above_ga_median": int(above),
            "es_minus_ga": float(means["es"] - means["ga"]) if es_ok else None,
            "random_minus_ga": float(means["random"] - means["ga"]) if means["random"] is not None else None}


# ----------------------------------------------------------------------------- paths and guards

def record_path(stage: str) -> Path:
    return EXP / f"{RECORD[stage]}.json"


def partial_path(stage: str) -> Path:
    return EXP / f"{RECORD[stage]}-partial.json"


def genomes_path(prefix: str, run: int) -> Path:
    return OUT / "genomes" / f"{prefix}-run{run:02d}-candidates.npz"


def state_path() -> Path:
    return OUT / "es-state.npz"


def sha256_bytes(path: Path) -> str:
    """A plain sha256 of a binary file (`registration.file_sha256` normalises line endings, for text)."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rerun_note(path: Path) -> Path:
    return path.with_name(path.stem + "-rerun.json")


def marker_path(stage: str) -> Path:
    return EXP / f"{stage}-started.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def marker_attempt(stage: str) -> int | None:
    m = read_json(marker_path(stage))
    return None if m is None else int(m.get("attempt", 1))


def rerun_state(stage: str) -> str:
    """'none' (no rerun set up), 'setup' (set up but not started: the archiving was interrupted, or
    the rerun stopped before its marker) or 'used' (the rerun started: its marker, attempt 2, or its
    record exists). The note is written before the first file is archived, and marked 'applied' after
    the last (review v2)."""
    note = read_json(rerun_note(record_path(stage)))
    if note is None:
        return "none"
    if note.get("status") == "applied" and (record_path(stage).exists() or marker_attempt(stage) == 2):
        return "used"
    return "setup"


def start_marker(stage: str, prov: dict, attempt: int) -> Path:
    """`registration.start_marker`, with the attempt number, so a killed rerun is told apart from a
    killed first attempt durably (review v2)."""
    path = marker_path(stage)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as f:
            json.dump({"stage": stage, "attempt": attempt, "provenance": prov,
                       "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, f, indent=1)
    except FileExistsError:
        raise SystemExit(f"{path.name} exists: {stage} has started before and is not rerun") from None
    return path


def clock() -> reg.CapClock:
    """The cap clock, after rebuilding the accounting's total from every attempt record (04a)."""
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
    """E1's Task N, exactly (checked against E1's gate record), with 02's GA as 04a registered it."""
    cfg = E1.config(REGISTERED["task_sigma"])
    want = json.loads(E1_GATE.read_text(encoding="utf-8"))["resolved_config"]
    if hashlib.sha256(json.dumps(want, sort_keys=True).encode()).hexdigest() != config_sha256(cfg):
        raise SystemExit("Task N's resolved configuration differs from E1's gate: refusing to run")
    if SMOKE:
        cfg.world.max_ticks = 40
    e, m = cfg.evo, REGISTERED["ga"]
    e.population, e.elites, e.truncation = m["population"], m["elites"], m["truncation"]
    e.worlds_per_strain, e.generations, e.islands = m["worlds_per_strain"], m["generations"], m["islands"]
    for k, v in m["mutation"].items():
        setattr(cfg.mutation, k, v)
    return cfg


def run_specs() -> list[EV.RunSpec]:
    r = REGISTERED["runs"]
    return [EV.RunSpec(run=i, run_seed=r["seed_base"] + i, shaping=0.0) for i in range(r["n"])]


def _range_ids(key: str) -> np.ndarray:
    v = REGISTERED["ids"][key]
    return np.arange(v["first"], v["first"] + v["worlds"])


def validation_ids() -> np.ndarray:
    return _range_ids("validation")


def pilot_validation_ids() -> np.ndarray:
    return _range_ids("pilot_validation")


def holdout_ids() -> np.ndarray:
    return _range_ids("holdout")


def id_record(ids) -> dict:
    ids = np.asarray(ids)
    return {"first": int(ids[0]), "last": int(ids[-1]), "count": int(len(ids))}


def require_committed(path: Path) -> None:
    """Tracked, unchanged, and (with the HEAD check in `require_formal`) pushed."""
    import subprocess
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(path)], cwd=ROOT,
                             capture_output=True).returncode == 0
    if not tracked or reg.git("status", "--porcelain", "--", str(path), root=ROOT):
        raise SystemExit(f"{Path(path).name} must be committed, unchanged and pushed first")


def attempt1(f: Path) -> Path:
    return f.with_name(f.stem.replace(".tmp", "") + "-attempt1" + f.suffix)


def require_earlier(args, prov: dict, stage: str, final_ok: bool = False) -> dict:
    """An earlier stage: completed (or, with `final_ok`, stopped twice: its one rerun used), committed
    (formal), on the same code and environment (guarded)."""
    path = record_path(stage)
    if not path.exists():
        state = rerun_state(stage)
        if marker_path(stage).exists():
            if state == "used":
                raise SystemExit(f"{WHAT[stage]}'s rerun was killed: run it with --rerun once more, which charges it "
                                 "and records it as final")
            raise SystemExit(f"{WHAT[stage]} was killed, or its rerun's setup was interrupted: rerun it "
                             "(--rerun --reason)")
        if state == "setup":
            raise SystemExit(f"{WHAT[stage]}'s rerun was set up but did not start: continue it with --rerun")
        raise SystemExit(f"{WHAT[stage]} has not run")
    rec = json.loads(path.read_text(encoding="utf-8"))
    if rec.get("outcome") == OUTCOMES["skipped"] and final_ok:
        return rec  # the extension, not run to keep the evaluation's budget (it has no provenance to check)
    if rec.get("outcome") != "completed":
        stopped = rec.get("outcome") == OUTCOMES["stopped"]
        if not (final_ok and stopped and rerun_state(stage) == "used"):
            if final_ok and stopped:
                raise SystemExit(f"{WHAT[stage]} stopped: rerun it once first (--rerun --reason)")
            raise SystemExit(f"{WHAT[stage]} did not complete")
    if formal(args):
        if not args.smoke:
            require_committed(path)
        reg.require_same_code(rec["provenance_at_start"]["git_commit"], GUARDED)
        reg.require_same_env(rec["provenance_at_start"], prov)
    return rec


def require_projection(args, prov) -> dict:
    p = require_earlier(args, prov, "project")
    if not p.get("within_limit"):
        raise SystemExit("the projection is over its limit: E2 does not start without a dated, reviewed amendment")
    return p


def write_atomic(path: Path, doc, attempts: int = 10) -> None:
    """Atomic, retried briefly: Windows can refuse a replace while another process (an indexer, an
    antivirus) holds the file for a moment (seen in this suite, review v1)."""
    for k in range(attempts):
        try:
            return reg.write_json(path, doc, atomic=True)
        except PermissionError:
            if k == attempts - 1:
                raise
            time.sleep(0.05 * (k + 1))


def replace(src: Path, dst: Path, attempts: int = 10) -> None:
    """`os.replace`, retried briefly on the same transient Windows refusal."""
    for k in range(attempts):
        try:
            return os.replace(src, dst)
        except PermissionError:
            if k == attempts - 1:
                raise
            time.sleep(0.05 * (k + 1))


def rerun_plan(stage: str, files: list[Path], reason: str | None) -> dict:
    """The registered rerun, checked but not yet applied: once per stage, after a crash, an interrupt or
    a kill (never the cap), with a reason. `files[0]` is the record and `files[1]` the start marker. A
    killed attempt's compute is reconciled into the accounting first (04a, D107)."""
    if not reason or not reason.strip():
        raise SystemExit("a rerun needs --reason, written before it runs")
    record, marker = files[0], files[1]
    state = rerun_state(stage)
    if state == "used":
        if marker.exists() and not record.exists():  # the rerun itself was killed: charged, and now final
            reconciled = reconcile_kill(stage, files)
            final_killed_record(stage, record, marker, reconciled)
            raise SystemExit(f"{WHAT[stage]} has been rerun once already; its killed rerun is charged and "
                             "recorded as final (not completed)")
        raise SystemExit(f"{WHAT[stage]} has been rerun once already")
    if state == "setup":  # continue the interrupted setup; the first attempt was charged when it was planned
        note = read_json(rerun_note(record))
        return {"stage": stage, "files": files, "reason": note["reason"], "how": note["how_the_first_attempt_ended"],
                "reconciled": note.get("reconciled_compute"), "resume": reason.strip()}
    if any(attempt1(f).exists() for f in files[:2]):
        raise SystemExit(f"{WHAT[stage]} has archived attempt files but no rerun note: resolve by hand")
    reconciled = reconcile_kill(stage, files) if (marker.exists() and not record.exists()) else None
    if record.exists():
        rec = json.loads(record.read_text(encoding="utf-8"))
        if rec.get("outcome") != OUTCOMES["stopped"]:
            raise SystemExit(f"only a stage stopped by a crash, an interrupt or a kill is rerun, not: {rec.get('outcome')}")
        how = "stopped"
    elif marker.exists():
        how = "killed: a start marker and no record"
    else:
        raise SystemExit(f"{WHAT[stage]} has not run: nothing to rerun")
    return {"stage": stage, "files": files, "reason": reason.strip(), "how": how, "reconciled": reconciled,
            "resume": None}


def final_killed_record(stage: str, record: Path, marker: Path, reconciled: dict) -> None:
    """A killed rerun leaves a marker and no record. Its record is written here, final and not
    completed, from the marker and the last partial record (the checkpoints or arms that completed)."""
    part = partial_path(stage)
    doc = json.loads(part.read_text(encoding="utf-8")) if part.exists() else {}
    doc = doc if isinstance(doc, dict) else {}
    m = json.loads(marker.read_text(encoding="utf-8"))
    if stage == "extend" and "champions_over_both" not in doc:  # killed before its first partial record
        doc.update(extension_fallback_champions(read_json(record_path("train-es")) or {}))
    doc.update(stage=stage, outcome=OUTCOMES["stopped"], final=True, reconciled_compute=reconciled,
               error="killed during the rerun: no record was written; this record is built from the marker and "
                     "the last partial record",
               provenance_at_start=doc.get("provenance_at_start", m.get("provenance")), start_marker=marker.name)
    write_atomic(record, doc)


def reconcile_kill(stage: str, files: list[Path]) -> dict:
    """A kill skips the accounting's cleanup, so the attempt's time is missing from compute.json. It is
    charged here, once: from the marker's start to the attempt's last file write, plus the registered
    tail (04a's rule, D107)."""
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
    if path.exists():
        seconds = float(json.loads(path.read_text(encoding="utf-8"))["categories"]["killed attempt"]["seconds"])
    else:
        tmp = path.with_name(path.name + ".partial")
        reg.write_json(tmp, doc)
        replace(tmp, path)
    acct.write_aggregate(compute, OUT / "compute.json")
    return {"file": name, "seconds": seconds}


def apply_rerun(plan: dict | None) -> dict | None:
    """After every other check has passed: keep the stopped attempt's files beside, renamed
    `-attempt1`. The note (`<record>-rerun.json`: the reason and the mapping) is written first, marked
    'archiving', and marked 'applied' after the last move, so an interrupted setup is continued by the
    next `--rerun` and never mistaken for a killed rerun (review v2)."""
    if plan is None:
        return None
    record = plan["files"][0]
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if plan.get("resume") is None:
        note = {"stage": plan["stage"], "how_the_first_attempt_ended": plan["how"], "reason": plan["reason"],
                "reconciled_compute": plan["reconciled"], "status": "archiving",
                "archived": {f.name: attempt1(f).name for f in plan["files"] if f.exists()}, "written_utc": now}
        write_atomic(rerun_note(record), note)
    else:
        note = read_json(rerun_note(record))
        note.setdefault("resumed", []).append({"utc": now, "reason": plan["resume"]})
    for f in plan["files"]:
        if f.name in note["archived"] and f.exists():
            if attempt1(f).exists():
                raise SystemExit(f"both {f.name} and {attempt1(f).name} exist: resolve by hand")
            replace(f, attempt1(f))
    note["status"] = "applied"
    write_atomic(rerun_note(record), note)
    return note


# ----------------------------------------------------------------------------- one stage

def run_stage(args, stage: str, requires, body, local_files=()) -> dict:
    """Every stage's frame: the guards, the once-only rule and the rerun, the order of stages, the cap,
    the start marker, and a not-completed record if the body stops."""
    prov = reg.provenance(GUARDED)
    if formal(args):
        reg.require_formal(args.device, prov)
    path = record_path(stage)
    files = [path, EXP / f"{stage}-started.json", partial_path(stage), *local_files]
    plan = rerun_plan(stage, files, args.reason) if args.rerun else None
    if plan is None and path.exists():
        raise SystemExit(f"{path.name} exists: {WHAT[stage]} runs once")
    if plan is None and rerun_state(stage) != "none":
        raise SystemExit(f"{WHAT[stage]}'s rerun was set up: continue it with --rerun")
    earlier = requires(args, prov)
    cap = clock()
    try:
        cap.check()
    except reg.CapReached as e:
        raise SystemExit(f"{WHAT[stage]} did not start: {e}") from None
    con, iface = preflight(args.device)
    spec = BrainSpec.from_connectome(con)
    cfg = task_config()
    rerun = apply_rerun(plan)
    attempt = 1 if plan is None else 2
    marker = start_marker(stage, prov, attempt)
    doc = {"stage": stage, "attempt": attempt, "registered": REGISTERED, "provenance_at_start": prov,
           "device": args.device,
           "resolved_config": cfg.to_dict(), "resolved_config_sha256": config_sha256(cfg),
           "e1_inputs_sha256": e1_input_hashes(), "start_marker": marker.name, "rerun": rerun}
    ctx = SimpleNamespace(args=args, cfg=cfg, iface=iface, spec=spec, cap=cap, earlier=earlier, doc=doc,
                          salvage=lambda: {}, after_fail=lambda: None)
    t0 = time.perf_counter()
    try:
        out = body(ctx)
        cap.check()  # the final budget decision, before the record is written
    except reg.CapReached as e:
        _not_completed(path, doc, ctx, "cap", str(e), t0)
        raise SystemExit(doc["outcome"]) from None
    except BaseException as e:  # noqa: BLE001  (recorded as not completed, then re-raised)
        doc["final"] = attempt == 2  # a stopped rerun is final; a first stop awaits its rerun
        _not_completed(path, doc, ctx, "stopped", f"{type(e).__name__}: {e}", t0)
        raise
    doc.update({"outcome": "completed", **out, "seconds": time.perf_counter() - t0})
    write_atomic(path, doc)
    partial_path(stage).unlink(missing_ok=True)
    return doc


def _not_completed(path, doc, ctx, reason, error, t0):
    """The record first, so it survives even if saving genomes is what failed; then one attempt to
    save what the last checkpoint left, whose own failure is added to the record."""
    doc.update(outcome=OUTCOMES[reason], error=error, seconds=time.perf_counter() - t0, **ctx.salvage())
    write_atomic(path, doc)
    try:
        ctx.after_fail()
    except Exception as e:  # noqa: BLE001
        doc["genome_save_error"] = f"{type(e).__name__}: {e} (the files from the previous checkpoint remain)"
        write_atomic(path, doc)


# ----------------------------------------------------------------------------- records

def run_record(rec, **extra) -> dict:
    out = {"spec": asdict(rec.spec), **extra, "log": rec.log, "checkpoints": rec.checkpoints,
           "generation0": rec.generation0, "generations_completed": len(rec.log)}
    if rec.checkpoints:
        ci = rec.champion_index()
        out["champion"] = {"checkpoint": ci, **{k: v for k, v in rec.checkpoints[ci].items() if k != "validation_counts"}}
    if isinstance(rec, LP.ESRecord):
        clips = [x["clip_share"] for x in rec.log if x.get("clip_share") is not None]
        out.update(start={k: v for k, v in rec.start.items() if k != "mean"},
                   flat_generations=rec.flat_generations, first_non_flat=rec.first_non_flat,
                   mean_clip_share=float(np.mean(clips)) if clips else None)
    if rec.final is not None:
        out["final_sha256"] = [genome_hash(rec.final, i) for i in range(rec.final.n_strains)]
    return out


def save_genomes(records, cfg, prefix: str) -> None:
    """Each run's checkpoint candidates, local, written to a temporary file and moved into place."""
    for rec in records:
        if not rec.candidates:
            continue
        path = genomes_path(prefix, rec.spec.run)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.stem + ".tmp.npz")
        save_population(tmp, Genome.cat(rec.candidates), cfg=cfg, run=rec.spec.run, run_seed=rec.spec.run_seed,
                        stage=prefix, checkpoint_generations=[c["generation"] for c in rec.checkpoints])
        replace(tmp, path)


def save_state(states: list[dict], path: Path) -> None:
    """The ES's state per run (the mean, Adam's moments and counter, the noise generator, the start),
    in one file without pickles."""
    arrays, meta = {}, []
    for i, s in enumerate(states):
        for k in ("mean", "m", "v", "start_mean"):
            arrays[f"{k}_{i}"] = np.asarray(s[k], dtype=np.float64)
        meta.append({**{k: v for k, v in s.items() if k not in ("mean", "m", "v", "start_mean", "start")},
                     "start": {k: v for k, v in s["start"].items() if k != "mean"}})
    arrays["meta"] = np.array(json.dumps(meta))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez(tmp, **arrays)
    replace(tmp, path)


def load_state(path: Path) -> list[dict]:
    with np.load(path, allow_pickle=False) as z:
        meta = json.loads(str(z["meta"]))
        states = []
        for i, s in enumerate(meta):
            arr = {k: z[f"{k}_{i}"].copy() for k in ("mean", "m", "v", "start_mean")}
            states.append({**s, **arr, "start": {**s["start"], "mean": arr["start_mean"]}})
    return states


def run_method(method, cfg, iface, spec, runs, *, generations, checkpoint_every, validation_ids, world_seed,
               id_base, id_span, device="cpu", rollout_fn=None, check=None, category=None, on_checkpoint=None,
               sigma=None, lr=None, resume=None):
    """One method's batch: (records, ES states or None). The GA is 04a's `evolve_batch`, unchanged."""
    kw = dict(generations=generations, checkpoint_every=checkpoint_every, validation_ids=validation_ids,
              world_seed=world_seed, id_base=id_base, id_span=id_span, device=device,
              rollout_fn=rollout_fn or rollout_mod.rollout, check=check, category=category, on_checkpoint=on_checkpoint)
    if method == "ga":
        return EV.evolve_batch(cfg, iface, spec, runs, **kw), None
    if method == "random":
        return LP.random_batch(cfg, iface, spec, runs, **kw), None
    if method == "es":
        return LP.es_batch(cfg, iface, spec, runs, sigma=sigma, lr=lr, resume=resume, **kw)
    raise ValueError(method)


def _episodes(runs: int, generations: int, checkpoints: int, cfg, validation_worlds: int) -> dict:
    t = runs * generations * cfg.evo.population * cfg.evo.worlds_per_strain
    v = runs * checkpoints * validation_worlds
    return {"training": t, "checkpoint_validation": v, "selection_total": t + v}


def train_batch(ctx, stage, method, runs, *, generations, ids, val, prefix, sigma=None, lr=None, resume=None,
                extra=None, summary=None):
    """A training body: the batch, partial records and local genomes at every checkpoint, and what a
    not-completed record keeps."""
    cfg, records = ctx.cfg, []
    extra = extra or (lambda i: {})
    summary = summary or (lambda recs: {})
    ctx.doc.update(runs=[asdict(r) for r in runs], training_ids=[ids["base"], ids["base"] + ids["span"] - 1],
                   validation_worlds=id_record(val),
                   composition={"training": [len(runs) * cfg.evo.population, cfg.evo.worlds_per_strain, 1],
                                "validation": [len(runs), len(val), 1]},
                   genome_files=f"local, {OUT.name}/genomes/{prefix}-run*.npz (not published; D028)")

    def partial(recs, g):
        records[:] = recs
        save_genomes(recs, cfg, prefix)
        write_atomic(partial_path(stage), {**ctx.doc, "generation": g, **summary(recs),
                                           "records": [run_record(r, **extra(i)) for i, r in enumerate(recs)]})

    ctx.salvage = lambda: {"records": [run_record(r, **extra(i)) for i, r in enumerate(records)], **summary(records)}
    ctx.after_fail = lambda: save_genomes(records, cfg, prefix)
    # before the first generation, so even a kill before the first checkpoint leaves what a stopped
    # record would hold (the extension's fallback champions; review v2)
    write_atomic(partial_path(stage), {**ctx.doc, "generation": None, **summary([]), "records": []})
    recs, states = run_method(method, cfg, ctx.iface, ctx.spec, runs, generations=generations,
                              checkpoint_every=REGISTERED["checkpoint_every"], validation_ids=val,
                              world_seed=REGISTERED["world_seed"], id_base=ids["base"], id_span=ids["span"],
                              device=ctx.args.device, check=ctx.cap.check, category=acct.category,
                              on_checkpoint=partial, sigma=sigma, lr=lr, resume=resume)
    records[:] = recs
    save_genomes(recs, cfg, prefix)
    return recs, states


# ----------------------------------------------------------------------------- the projection

def projection_verdict(secs: dict) -> dict:
    """Per shape, the median time of the timed generations after the first (which includes warm-up and
    the first checkpoint) and the last generation's excess over it (one checkpoint); every training
    stage projected at its shape's rates."""
    rates = {}
    for shape, s in secs.items():
        per_gen = float(np.median(s[1:-1])) if len(s) > 2 else float(s[-1])
        rates[shape] = {"seconds_per_generation": per_gen, "seconds_per_checkpoint": max(0.0, float(s[-1]) - per_gen)}
    plan = training_plan()
    hours = sum(p["generations"] * rates[p["shape"]]["seconds_per_generation"]
                + p["checkpoints"] * rates[p["shape"]]["seconds_per_checkpoint"] for p in plan.values()) / 3600
    limit = REGISTERED["projection"]["max_training_hours"]
    return {"plan": plan, "rates": rates, "projected_training_hours": hours, "limit_hours": limit,
            "within_limit": hours <= limit}


def cmd_project(args):
    """Every training shape at full size, on smoke ids and the projection's own seeds, timed per
    generation, once. The pilot refuses to start without a completed projection within its limit."""
    n1, n2 = pilot_runs()
    shapes = {"ga": ("ga", REGISTERED["runs"]["n"]), "random": ("random", REGISTERED["runs"]["n"]),
              "es": ("es", REGISTERED["runs"]["n"]), "pilot-1": ("es", n1), "pilot-2": ("es", n2)}

    def body(ctx):
        n = REGISTERED["projection"]["generations_timed"]
        val = SMOKE_IDS[5000:5000 + REGISTERED["ids"]["validation"]["worlds"]]
        secs = {}
        for shape, (method, k) in shapes.items():
            runs = [EV.RunSpec(i, REGISTERED["projection"]["seed_base"] + i, 0.0) for i in range(k)]
            with acct.category("measure"):
                recs, _ = run_method(method, ctx.cfg, ctx.iface, ctx.spec, runs, generations=n, checkpoint_every=n - 1,
                                     validation_ids=val, world_seed=REGISTERED["world_seed"], id_base=0, id_span=5000,
                                     device=ctx.args.device, check=ctx.cap.check, sigma=1.0, lr=0.3,
                                     on_checkpoint=lambda rs, g: save_genomes(rs, ctx.cfg, f"projection-{shape}"))
            secs[shape] = [x["batch_seconds"] for x in recs[0].log]
        verdict = projection_verdict(secs)
        if not verdict["within_limit"]:
            verdict["experiment_outcome"] = OUTCOMES["over limit"]
        return {"shapes": {k: {"method": m, "runs": r} for k, (m, r) in shapes.items()}, "generations_timed": n,
                "seeds_base": REGISTERED["projection"]["seed_base"], "ids": {"training": [0, 4999], "validation": id_record(val)},
                "batch_seconds": secs, **verdict}

    doc = run_stage(args, "project", lambda a, p: {}, body)
    print(f"training projected at {doc['projected_training_hours']:.2f} h (limit {doc['limit_hours']} h): "
          f"{'within' if doc['within_limit'] else 'OVER: E2 does not start'}")


# ----------------------------------------------------------------------------- the pilot

def pilot_rows(records: list[dict]) -> list[dict]:
    return [{"sigma": r["sigma"], "lr_multiple": r["lr_multiple"], "run": r["spec"]["run"],
             "total": int(sum(r["checkpoints"][-1]["validation_counts"]))} for r in records]


def cmd_pilot(args):
    stage = f"pilot-{args.stage}"
    P = REGISTERED["pilot"]

    def requires(a, prov):
        if args.stage == 1:
            return {"projection": require_projection(a, prov)}
        return {"pilot-1": require_earlier(a, prov, "pilot-1")}

    def body(ctx):
        if args.stage == 1:
            settings, offset = [(s, P["stage1_lr_multiple"]) for s in P["sigmas"]], 0
        else:
            s = ctx.earlier["pilot-1"]["selected_sigma"]
            settings = [(s, m) for m in P["lr_multiples"] if m != P["stage1_lr_multiple"]]
            offset = len(P["sigmas"]) * P["replicates"]
        runs, sig, lrs, mults = [], [], [], []
        for a, (s, mult) in enumerate(settings):
            for k in range(P["replicates"]):  # replicate k shares its seed across settings (paired)
                runs.append(EV.RunSpec(run=offset + a * P["replicates"] + k, run_seed=P["seed_base"] + k, shaping=0.0))
                sig.append(s)
                lrs.append(mult * s)
                mults.append(mult)
        extra = lambda i: {"sigma": sig[i], "lr": lrs[i], "lr_multiple": mults[i]}  # noqa: E731
        recs, _ = train_batch(ctx, stage, "es", runs, generations=P["generations"], ids=REGISTERED["ids"]["pilot_train"],
                              val=pilot_validation_ids(), prefix=stage, sigma=sig, lr=lrs, extra=extra)
        records = [run_record(r, **extra(i)) for i, r in enumerate(recs)]
        out = {"records": records,
               "episodes": _episodes(len(runs), P["generations"], n_checkpoints(0, P["generations"],
                                     REGISTERED["checkpoint_every"]), ctx.cfg, len(pilot_validation_ids()))}
        if args.stage == 1:
            out["selected_sigma"] = select_sigma(pilot_rows(records))
            out["table"] = pilot_rows(records)
            out["uninformative"] = uninformative(pilot_rows(records))
        else:
            s = ctx.earlier["pilot-1"]["selected_sigma"]
            rows = pilot_rows(records) + [r for r in pilot_rows(ctx.earlier["pilot-1"]["records"]) if r["sigma"] == s]
            m = select_rate(rows, s)
            out.update(table=rows, selected={"sigma": s, "lr_multiple": m, "lr": m * s},
                       uninformative=uninformative(rows))
        return out

    local = [genomes_path(stage, i) for i in range(sum(pilot_runs()))]
    doc = run_stage(args, stage, requires, body, local)
    print(f"{stage}: selected {doc.get('selected_sigma', doc.get('selected'))}")


# ----------------------------------------------------------------------------- training

def cmd_train(args):
    method = args.method
    stage = f"train-{method}"

    def requires(a, prov):
        if method == "ga":
            return {"pilot-2": require_earlier(a, prov, "pilot-2")}
        if method == "random":
            return {"train-ga": require_earlier(a, prov, "train-ga", final_ok=True)}
        return {"train-random": require_earlier(a, prov, "train-random", final_ok=True),
                "pilot-2": require_earlier(a, prov, "pilot-2")}

    def body(ctx):
        runs, g = run_specs(), REGISTERED["generations"][method]
        kw = dict(generations=g, ids=REGISTERED["ids"]["train"], val=validation_ids(), prefix=method)
        extra, out = (lambda i: {}), {}
        if method == "es":
            sel = ctx.earlier["pilot-2"]["selected"]
            extra = lambda i: {"sigma": sel["sigma"], "lr": sel["lr"]}  # noqa: E731
            recs, states = train_batch(ctx, stage, "es", runs, sigma=sel["sigma"], lr=sel["lr"], extra=extra, **kw)
            save_state(states, state_path())
            out["state_sha256"] = sha256_bytes(state_path())
            out["state_file"] = f"local, {OUT.name}/{state_path().name} (not published; D028)"
        else:
            recs, _ = train_batch(ctx, stage, method, runs, **kw)
        out["records"] = [run_record(r, **extra(i)) for i, r in enumerate(recs)]
        out["episodes"] = _episodes(len(runs), g, n_checkpoints(0, g, REGISTERED["checkpoint_every"]), ctx.cfg,
                                    len(validation_ids()))
        return out

    local = [genomes_path(method, r.run) for r in run_specs()] + ([state_path()] if method == "es" else [])
    doc = run_stage(args, stage, requires, body, local)
    for r in doc["records"]:
        print(f"{method} run {r['spec']['run']}: champion g{r['champion']['generation']} "
              f"validation {r['champion']['validation_mean']:.3f}")


def cmd_extend(args):
    """The descriptive extension: each formal ES run resumed from its saved state at its last
    generation, to generation 999. Its champions never enter the decision."""

    def requires(a, prov):
        es = require_earlier(a, prov, "train-es")
        if not state_path().exists() or sha256_bytes(state_path()) != es["state_sha256"]:
            raise SystemExit("the ES's saved state is missing or differs from its record")
        need = extension_hours(read_json(record_path("project"))) + REGISTERED["evaluation_reserve_hours"]
        left = REGISTERED["cap_gpu_hours"] - clock().spent_hours()
        if not a.rerun and need > left:  # a started extension is finished or finalised by the rerun rule
            write_atomic(record_path("extend"), {"stage": "extend", "outcome": OUTCOMES["skipped"], "final": True,
                                                 "hours_needed": need, "hours_left": left})
            raise SystemExit(f"the extension is skipped: it needs {need:.2f} h with the evaluation's reserve, "
                             f"and {left:.2f} h of the cap remain")
        return {"train-es": es}

    def body(ctx):
        es = ctx.earlier["train-es"]
        runs = [EV.RunSpec(**r["spec"]) for r in es["records"]]
        sig, lr = es["records"][0]["sigma"], es["records"][0]["lr"]
        g0, g1 = REGISTERED["generations"]["es"], REGISTERED["generations"]["extension"]
        extra = lambda i: {"sigma": sig, "lr": lr}  # noqa: E731

        def summary(recs):  # over the formal checkpoints and whatever extension checkpoints completed
            done = {r.spec.run: r.checkpoints for r in recs}
            return {"champions_over_both": [{"run": f["spec"]["run"],
                                             **champion_over_both(f, done.get(f["spec"]["run"], []))}
                                            for f in es["records"]]}

        recs, _ = train_batch(ctx, "extend", "es", runs, generations=g1, ids=REGISTERED["ids"]["train"],
                              val=validation_ids(), prefix="extension", sigma=sig, lr=lr, resume=load_state(state_path()),
                              extra=extra, summary=summary)
        return {"records": [run_record(r, **extra(i)) for i, r in enumerate(recs)], **summary(recs),
                "resumed_from_state_sha256": es["state_sha256"],
                "episodes": _episodes(len(runs), g1 - g0, n_checkpoints(g0, g1, REGISTERED["checkpoint_every"]),
                                      ctx.cfg, len(validation_ids()))}

    run_stage(args, "extend", requires, body, [genomes_path("extension", r.run) for r in run_specs()])


def extension_fallback_champions(es: dict) -> dict:
    """The extension's champions when none of its checkpoints completed: each formal run's own."""
    return {"champions_over_both": [{"run": f["spec"]["run"], **champion_over_both(f, [])}
                                    for f in es.get("records", []) if f.get("checkpoints")]}


def extension_hours(projection: dict) -> float:
    p, r = projection["plan"]["extend"], projection["rates"][projection["plan"]["extend"]["shape"]]
    return (p["generations"] * r["seconds_per_generation"] + p["checkpoints"] * r["seconds_per_checkpoint"]) / 3600


def champion_over_both(formal_rec: dict, extension_checkpoints: list[dict]) -> dict:
    """The first best checkpoint over the formal run's checkpoints, then the extension's (so a tie goes
    to the formal one)."""
    both = [("formal", k, c) for k, c in enumerate(formal_rec["checkpoints"])] + \
           [("extension", k, c) for k, c in enumerate(extension_checkpoints)]
    src, k, c = both[int(np.argmax([c["validation_mean"] for _, _, c in both]))]
    return {"source": src, "checkpoint": k, "generation": c["generation"], "validation_mean": c["validation_mean"],
            "sha256": c["sha256"]}


# ----------------------------------------------------------------------------- the evaluation

def load_candidates(prefix: str, run: int, spec, cfg) -> Genome:
    g, _ = load_population(genomes_path(prefix, run), spec, cfg.brain)
    want = dataclasses.asdict(cfg.brain)
    if dataclasses.asdict(g.cfg) != want:  # a file's metadata can override padding (04a, Astra)
        diff = {k: (want[k], v) for k, v in dataclasses.asdict(g.cfg).items() if want.get(k) != v}
        raise SystemExit(f"{prefix} run {run}'s genome file loads with another brain configuration: {diff}")
    return g


def champions(trains: dict, ext: dict | None, spec, cfg) -> dict:
    """Every champion from the local files, checked against its committed hash before any hold-out
    world is used: {(label, run): genome}."""
    out = {}
    for m in METHODS:
        for r in trains[m].get("records", []):
            if "champion" not in r:
                continue
            run = r["spec"]["run"]
            g = load_candidates(m, run, spec, cfg).select([r["champion"]["checkpoint"]])
            if genome_hash(g, 0) != r["champion"]["sha256"]:
                raise SystemExit(f"{m} run {run}'s champion does not match its committed hash")
            out[(m, run)] = g
    if ext is not None:
        for c in ext.get("champions_over_both", []):
            run = c["run"]
            g = load_candidates("es" if c["source"] == "formal" else "extension", run, spec, cfg).select([c["checkpoint"]])
            if genome_hash(g, 0) != c["sha256"]:
                raise SystemExit(f"the extension's run {run} champion does not match its committed hash")
            out[("extension", run)] = g
    return out


def cmd_evaluate(args):
    def requires(a, prov):
        trains = {m: require_earlier(a, prov, f"train-{m}", final_ok=True) for m in METHODS}
        ext = require_earlier(a, prov, "extend", final_ok=True) if trains["es"]["outcome"] == "completed" else None
        recorded = [t["e1_inputs_sha256"] for t in trains.values() if "e1_inputs_sha256" in t]
        if any(r != e1_input_hashes() for r in recorded):
            raise SystemExit("E1's freeze or gate record differs from what a training stage recorded")
        return {"trains": trains, "extension": ext}

    def body(ctx):
        trains, ext = ctx.earlier["trains"], ctx.earlier["extension"]
        cfg, device, ids, ws = ctx.cfg, ctx.args.device, holdout_ids(), REGISTERED["world_seed"]
        tuned = json.loads(E1_FREEZE.read_text(encoding="utf-8"))["tuned"]
        counts = {}
        ctx.salvage = lambda: {"arms_completed": list(counts),
                               "per_world_counts": {k: v.astype(int).tolist() for k, v in counts.items()}}

        def neural(g, probe):
            c = cfg.copy()
            c.world.food_probe = probe
            ctx.cap.check()
            with acct.category("final"):
                r = rollout_mod.rollout(c, ctx.iface, EV.moved(g, device), ids, ws, device, chunk_worlds=len(ids))
            return np.asarray(r.score[0])

        def scripted(name, params):
            c = cfg.copy()
            base = "S-const" if name == "S-const k<=32" else name
            if base == "oracle":
                brain = E1.C.OracleBrain(ctx.iface, 302, c.world.forward_gain, c.world.turn_gain, device=device, **params)
            else:
                brain = E1.C.scripted(ctx.iface, E1.MAKERS[base](**params), c, device=device)
            ctx.cap.check()
            with acct.category("final"):
                r = rollout_brain(c, ctx.iface, brain, ids, ws, device)
            return np.asarray(r.score[0])

        def keep():  # after every arm, so a kill (which skips every handler) keeps the completed arms
            write_atomic(partial_path("evaluate"), {**ctx.doc, **ctx.salvage()})

        for (label, run), g in ctx.genomes.items():
            for probe in (REGISTERED["probes"] if label != "extension" else ["real"]):
                counts[f"{label} run{run:02d} {probe}"] = neural(g, probe)
                keep()
        for name in REGISTERED["controls"]:
            counts[name] = scripted(name, tuned[name]["params"])
            keep()
        return analyse(counts, trains, ext, len(ids))

    trains_seen = {}

    def requires_and_check(a, prov):
        e = requires(a, prov)
        con = load_connectome()
        spec, cfg = BrainSpec.from_connectome(con), task_config()
        trains_seen["genomes"] = champions(e["trains"], e["extension"], spec, cfg)  # before any hold-out world
        return e

    def body_with_genomes(ctx):
        ctx.genomes = trains_seen["genomes"]
        ctx.doc.update(worlds=id_record(holdout_ids()),
                       composition={"neural arms": [1, len(holdout_ids()), 1], "scripted arms": [1, len(holdout_ids()), 1]},
                       champion_sha256={f"{k[0]} run{k[1]:02d}": genome_hash(g, 0) for k, g in ctx.genomes.items()})
        return body(ctx)

    doc = run_stage(args, "evaluate", requires_and_check, body_with_genomes)
    print(doc["outcome"])
    print(doc["floor"])


def analyse(counts: dict, trains: dict, ext: dict | None, worlds: int) -> dict:
    complete = {m: trains[m]["outcome"] == "completed" for m in METHODS}
    runs = {m: [r["spec"]["run"] for r in trains[m].get("records", []) if "champion" in r] for m in METHODS}
    totals = {m: [int(counts[f"{m} run{r:02d} real"].sum()) for r in runs[m]] for m in METHODS}
    d = decide(totals, complete, worlds)
    oracle = float(counts["oracle"].mean())
    methods = {}
    for m in METHODS:
        per = {f"run{r:02d}": {p: float(counts[f"{m} run{r:02d} {p}"].mean()) for p in REGISTERED["probes"]}
               for r in runs[m]}
        real = [v["real"] for v in per.values()]
        methods[m] = {"complete": complete[m], "runs": per, "mean": float(np.mean(real)) if real else None,
                      "sd": float(np.std(real, ddof=1)) if len(real) > 1 else None,
                      "fraction_of_oracle": (float(np.mean(real)) / oracle) if real and oracle > 0 else None}
    extension = None
    if ext is not None:
        er = {f"run{c['run']:02d}": {"source": c["source"], "generation": c["generation"],
                                     "real": float(counts[f"extension run{c['run']:02d} real"].mean())}
              for c in ext.get("champions_over_both", []) if f"extension run{c['run']:02d} real" in counts}
        extension = {"complete": ext["outcome"] == "completed", "outcome": ext["outcome"], "runs": er,
                     "mean": float(np.mean([v["real"] for v in er.values()])) if er else None,
                     "note": "descriptive: never enters the decision"}
    return {"outcome": d["outcome"], "floor": d["floor"], "provisional": d["provisional"], "decision": d,
            "pairing": pairing(trains), "es_minus_ga_per_run": per_run_differences(counts, runs),
            "methods": methods, "extension": extension,
            "controls": {k: float(counts[k].mean()) for k in REGISTERED["controls"]},
            "per_world_counts": {k: v.astype(int).tolist() for k, v in counts.items()}}


def pairing(trains: dict) -> dict:
    """Paired starts, checked: in each run, the three methods' generation-0 checkpoint candidates (and
    the ES's start genome) are the same genome, by hash."""
    g0 = {m: {r["spec"]["run"]: r["checkpoints"][0]["sha256"] for r in trains[m].get("records", [])
              if r.get("checkpoints")} for m in METHODS}
    starts = {r["spec"]["run"]: r["start"]["sha256"] for r in trains["es"].get("records", []) if r.get("start")}
    shared = sorted(set(g0["ga"]) & set(g0["random"]) & set(g0["es"]) & set(starts))
    bad = [r for r in shared if not g0["ga"][r] == g0["random"][r] == g0["es"][r] == starts[r]]
    return {"runs_compared": shared, "mismatched_runs": bad,
            "generation0_candidates_match": (not bad) if shared else None,
            "note": "each method's generation-0 checkpoint candidate and the ES's start genome, by hash"}


def per_run_differences(counts: dict, runs: dict) -> dict:
    """Each run's ES-minus-GA hold-out mean (real probe), for the runs both methods have."""
    return {f"run{r:02d}": float(np.mean(counts[f"es run{r:02d} real"]) - np.mean(counts[f"ga run{r:02d} real"]))
            for r in sorted(set(runs["es"]) & set(runs["ga"]))}


# ----------------------------------------------------------------------------- smoke

def use_smoke(args, folder: Path | None = None) -> None:
    """Tiny sizes, ids 0-9 999 (outside every E1, 04a and E2 range) for every stage, and a scratch
    folder. Never results. Only files inside that folder are removed: this stage's and every later
    stage's records."""
    global EXP, OUT, SMOKE
    EXP = OUT = Path(folder) if folder is not None else ROOT / "runs" / "e2-smoke"
    SMOKE = True
    R = REGISTERED
    R["ga"].update(generations=3, population=4, elites=1, truncation=2, worlds_per_strain=2)
    R["generations"] = {"ga": 3, "random": 3, "es": 3, "extension": 5, "pilot": 3}
    R["runs"] = {"n": 2, "seed_base": SMOKE_SEED_BASE}
    R["pilot"].update(replicates=1, seed_base=SMOKE_PILOT_SEED_BASE, generations=3)
    R["ids"] = {"pilot_train": {"base": 0, "span": 2500}, "pilot_validation": {"first": 5500, "worlds": 4},
                "train": {"base": 2500, "span": 2500}, "validation": {"first": 5000, "worlds": 4},
                "holdout": {"first": 6000, "worlds": 16}}
    R["checkpoint_every"] = 2
    R["projection"].update(generations_timed=3, seed_base=SMOKE_PROJECTION_SEED_BASE)
    name = {"project": "project", "pilot": f"pilot-{getattr(args, 'stage', None) or 1}",
            "train": f"train-{getattr(args, 'method', None) or 'ga'}", "extend": "extend",
            "evaluate": "evaluate"}[args.command]
    for stage in STAGES[STAGES.index(name):]:
        for f in (record_path(stage), EXP / f"{stage}-started.json", partial_path(stage)):
            if EXP in f.parents:
                f.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=["project", "pilot", "train", "extend", "evaluate"])
    ap.add_argument("--stage", type=int, choices=[1, 2])
    ap.add_argument("--method", choices=list(METHODS))
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true", help="tiny sizes, ids outside E1, 04a and E2, scratch folder")
    ap.add_argument("--guarded", action="store_true", help="with --smoke: keep the formal guards")
    ap.add_argument("--rerun", action="store_true", help="once, after a crash, an interrupt or a kill (never the cap)")
    ap.add_argument("--reason", help="with --rerun: why the first attempt stopped, recorded before the rerun")
    args = ap.parse_args()
    if args.command == "pilot" and not args.stage:
        ap.error("pilot needs --stage 1 or 2")
    if args.command == "train" and not args.method:
        ap.error("train needs --method ga, random or es")
    if args.smoke:
        use_smoke(args)
    {"project": cmd_project, "pilot": cmd_pilot, "train": cmd_train, "extend": cmd_extend,
     "evaluate": cmd_evaluate}[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    out = ROOT / "runs" / ("e2-smoke" if smoke else "e2")
    try:
        run_script(main, out_default=str(out), default="measure", name="e2")
    finally:
        agg = out / "compute.json"
        if agg.exists() and not smoke:
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
