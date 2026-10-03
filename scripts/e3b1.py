"""E3b-1: the E3 gate in mazes (confirmatory; experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md, bound at
1c65e4e, D186).

    python scripts/e3b1.py project | g-e | train-ta | train-tf | train-n | train-r | champions | evaluate
    python scripts/e3b1.py readings          # recompute the readings from the saved chunks (no stage)
    add --smoke for toy sizes in runs/e3b1-smoke (never results)

Every stage runs inside E2's stage frame, once (one rerun after a crash or a kill), and its record is
committed and pushed before the next starts (§5). Training stages have up to three attempts (§5): a
non-finite score is retried inside the stage, and a crash or a kill is the frame's rerun. The cap is 24
GPU-hours (§10), counted through `wormwars.accounting`. Genomes stay local (rule 1); every champion's hash
and validation scores are in the records. `evaluate` saves each chunk's per-maze arrays when the chunk
completes, and a rerun resumes at the first chunk that did not complete (§5).
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e3 import latch as L  # noqa: E402
from wormwars.e3 import maze_controls as MC  # noqa: E402
from wormwars.e3 import maze_measures as MM  # noqa: E402
from wormwars.e3 import maze_organisms as MO  # noqa: E402
from wormwars.e3 import maze_runs as MR  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e3 import organism as O  # noqa: E402
from wormwars.e3 import probe as P  # noqa: E402
from wormwars.e3 import tuning as T  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.evo.genomes import genome_hash, load_population, save_population  # noqa: E402
from wormwars.evo.rollout import rollout  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


E = _load("e2_for_e3b1", "e2.py")
EQ = _load("e3_equivalence_for_e3b1", "e3_equivalence.py")
B0 = _load("e3b0_for_e3b1", "e3b0.py")  # E3b-0's blind carrier with a variant, and its one-nose checks

EXP = ROOT / "experiments" / "E3-ab-organism" / "E3b-1"
OUT = ROOT / "runs" / "e3b1"
PREREG = "experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md"
EQ_REFERENCE = "experiments/E3-ab-organism/E3b-0/development-records/reference.json"  # the engine at 84ff98a
REPORT_B0 = "experiments/E3-ab-organism/E3b-0/report.json"
FIXED = {  # §2: every fixed input, checked at load
    "experiments/E4s-stereo-module/E4s-0/module.json": "9613cd155a20ed2cfb891c1bd10fed16814f24a04f912a1940524f2378e877d4",
    "experiments/E3-ab-organism/E3b-0/stage-b3.json": "a54003cfbdf4a00e4e4ff72203258211877d62d96c2f431e458ab14401e600e9",
    "experiments/E3-ab-organism/E3b-0/stage-c.json": "c3861dec78d8015902aff233f63cac331dd4594fe651c79c15f04d64dd6a082b",
    REPORT_B0: "af82e1c9573b0f2b73d228d065c277f9bb46310f2fd8d395439a557e359d7df8",
    "experiments/E3-ab-organism/E3b-0/timing.json": "c4cb4df44a6bdcf81b6f506103d2fe40f4d8991a1d97cb8dc8df9849921c7afd",
    "experiments/E3-ab-organism/E3b-1/power.json": "2b4e618e884dc678170e5d7ac8f569c0907609638e5086cd3b6e82df45129145",
    "experiments/E1-navigation/freeze.json": "c5c48f83079a6bd0dd48bdeb13d02ab211a08eb64433fdc8372cbd6e74bcaae9",
    "experiments/E1-navigation/gate.json": "a18b5a53845360107448527b2af038b9c613e4bf11fdfe843c328b7c2a01afa0",
    "experiments/E2-optimizer-screen/train-ga.json": "88a3ed88de2f89042970c11fc8e4de49b8432e533a2e9e802de3e1333e538d7c",
}
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PREREG, EQ_REFERENCE, *FIXED]
SMOKE = False
TEST_OPEN = False  # the test block is opened only inside `evaluate` (§4)

ARMS = ("ta", "tf", "n", "r")
ARM_NAME = {"ta": "T-A", "tf": "T-F", "n": "N", "r": "R"}
STAGES = ["project", "g-e", "train-ta", "train-tf", "train-n", "train-r", "champions", "evaluate"]
TRAINING = [s for s in STAGES if s.startswith("train-")]
SNAP_READ = "snap124"  # T-F's read at index 124, by its registered name
SETTLED = ("completed", "skipped", "final-stopped", "cap-stopped")
REGISTERED = {
    "maze_seed": 1_180_000, "c": 5, "H": 2400, "colony": 8, "spawns": 4,
    "trail": {"mu": 0.01, "lam": 0.02, "delta": 0.05, "d0": 1.142},
    "ga": {"population": 32, "elites": 3, "truncation": 8,
           "mutation": {"w_sigma": 0.08, "tau_sigma": 0.15, "bias_sigma": 0.05, "p_mutate": 1.0},
           "factor": T.FACTOR},
    "arms": {
        "ta": {"runs": 8, "G": 125, "W": 16, "access": "shared", "start": "seed", "seed_base": 1_190_000, "snapshot": []},
        "tf": {"runs": 8, "G": 300, "W": 8, "access": "shared", "start": "seed", "seed_base": 1_190_100,
               "snapshot": [124]},
        "n": {"runs": 6, "G": 125, "W": 16, "access": "none", "start": "seed", "seed_base": 1_190_200, "snapshot": []},
        "r": {"runs": 2, "G": 125, "W": 16, "access": "shared", "start": "degraded", "seed_base": 1_190_300,
              "snapshot": []},
    },
    "checkpoint_every": 25,
    "ids": {"validation": [4000, 4128], "learning": [4500, 4628], "calibration": [5000, 5256], "test": [6000, 6256]},
    "train": {"base": 10_000_000, "span": 10_000_000},
    "projection": {"seed": 1_190_900, "ids_first": 9_500, "train_base": 9_000_000, "train_span": 100_000},
    "cap_gpu_hours": 24.0, "admit_hours": 22.0, "reserve_factor": 1.25, "ge_allowance_hours": 0.3,
    "chunk": 16, "chunk_replay": 8, "min_runs": T.MIN_RUNS,
    "probe": {"k_d_min": 30.0, "relative_min": 10.5, "low": 0.35, "high": 1.0},
    "cuts": ["n to runs 0-3", "r dropped", "tf to 250 generations"],
}
RECORD = {s: s for s in STAGES}
WHAT = {s: f"E3b-1's {s}" for s in STAGES}


def configure() -> None:
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, OUT, GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E3b-1: not completed (the run stopped)",
                  "cap": "E3b-1: not completed (the cap was reached)"}
    E.RECORD.update(RECORD)
    E.WHAT.update(WHAT)


configure()


def check_inputs() -> dict:
    """§2: every fixed input's sha256, with LF line endings as committed."""
    got = {}
    for path, want in FIXED.items():
        h = hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if h != want:
            raise SystemExit(f"{path} has changed (sha256 {h}, registered {want}): refusing to run")
        got[path] = h
    return got


def base_config():
    """E1's Task N (σ 6), checked against E1's gate record as E2 checks it."""
    cfg = E.E1.config(6.0)
    want = json.loads(E.E1_GATE.read_text(encoding="utf-8"))["resolved_config"]
    if hashlib.sha256(json.dumps(want, sort_keys=True).encode()).hexdigest() != E.config_sha256(cfg):
        raise SystemExit("Task N's resolved configuration differs from E1's gate: refusing to run")
    return cfg


def cfg_for(access: str, W: int = 16):
    R = REGISTERED
    cfg = MW.maze_config(base_config(), c=R["c"], horizon=R["H"], colony=R["colony"], access=access,
                         spawns=R["spawns"], **R["trail"])
    g = R["ga"]
    cfg.evo.population, cfg.evo.elites, cfg.evo.truncation = g["population"], g["elites"], g["truncation"]
    cfg.evo.worlds_per_strain = int(W)
    for k, v in g["mutation"].items():
        setattr(cfg.mutation, k, v)
    return cfg


def arm_cfg(arm: str):
    a = REGISTERED["arms"][arm]
    return cfg_for(a["access"], a["W"])


def task_config():
    return cfg_for("shared")


E.task_config = task_config  # the stage frame records this as each stage's starting configuration


def ids(key: str) -> np.ndarray:
    if key == "test" and not TEST_OPEN:
        raise SystemExit("the test block is opened only in the evaluation stage (§4)")
    lo, hi = REGISTERED["ids"][key]
    return np.arange(lo, hi)


@contextlib.contextmanager
def test_block_open():
    global TEST_OPEN
    TEST_OPEN = True
    try:
        yield
    finally:
        TEST_OPEN = False


def n_test() -> int:
    lo, hi = REGISTERED["ids"]["test"]
    return hi - lo


def seed() -> int:
    return REGISTERED["maze_seed"]


def run_seed(arm: str, i: int) -> int:
    return REGISTERED["arms"][arm]["seed_base"] + i


def levels() -> list:
    """Criterion 4's levels, E3b-0's at full precision (§6)."""
    return json.loads((ROOT / REPORT_B0).read_text(encoding="utf-8"))["component_tests"]["levels"]


# ============================================================================== organisms

_CX: dict = {}


def context(cfg) -> dict:
    """The start organisms (the seed E + W2, R's degraded start), their brain layout, W2 alone on the carrier."""
    if not _CX:
        con, l1 = load_connectome(), A.load_l1()
        s = T.start_organism("seed", con, l1, cfg.brain)
        d = T.start_organism("degraded", con, l1, cfg.brain)
        if s.ext.names != d.ext.names:
            raise SystemExit("the degraded start does not share the seed's layout")
        if "E3B_M1" in s.ext.names:  # rollout's plain Brain equals the organism's started brain only without M
            raise SystemExit("the seed has an oscillator: training would not start it")
        _CX.update(con=con, l1=l1, seed=s, degraded=d, spec=BrainSpec.from_connectome(s.ext),
                   w2=B0.carrier_variant(con, cfg, "W2"), plain_iface=load_interface(con))
    return _CX


def start_genome(cx, arm: str) -> Genome:
    return cx["seed"].genome if REGISTERED["arms"][arm]["start"] == "seed" else cx["degraded"].genome


def genomes_file(arm: str, i: int, kind: str) -> Path:
    return OUT / "genomes" / f"{arm}-run{i:02d}-{kind}.npz"


def load_genomes(arm: str, i: int, kind: str, cx, cfg) -> Genome:
    g, _ = load_population(genomes_file(arm, i, kind), cx["spec"], cfg.brain)
    return g


def on(genome: Genome, dev) -> Genome:
    return genome if str(dev) == "cpu" else EV.moved(genome, dev)


# ============================================================================== the plan, projections, admission

def default_plan() -> dict:
    R = REGISTERED["arms"]
    return {"runs": {a: R[a]["runs"] for a in ARMS}, "G": {a: R[a]["G"] for a in ARMS}, "cuts": []}


def final_index(plan: dict, arm: str) -> int:
    return plan["G"][arm] - 1


def wording(plan: dict) -> str:
    return (f"T-A at {plan['G']['ta']} generations and T-F at {plan['G']['tf']} generations (read also at index 124), "
            f"averaged over the two schedules")


def n_checkpoints(G: int, every: int) -> int:
    return len([g for g in range(G) if g % every == 0 or g == G - 1])


def train_timing(timing: dict, arm: str, runs: int) -> dict:
    return timing["training"]["n4" if arm == "n" and runs == 4 and "n4" in timing["training"] else arm]


def prepass_seconds(timing: dict, k: int) -> float:
    """§9: the replay pre-passes for k organisms, a shared leg in chunks of 16 and a replay leg in chunks of 8."""
    return math.ceil(k / REGISTERED["chunk"]) * timing["eval_plain"] + math.ceil(k / REGISTERED["chunk_replay"]) * timing["eval_donor"]


def synthetic_champions(runs: dict) -> list:
    out = [{"arm": a, "run": i, "read": "final"} for a in ARMS for i in range(runs[a])]
    return out + [{"arm": "tf", "run": i, "read": "snap124"} for i in range(runs["tf"])]


def projections(timing: dict, plan: dict, done: dict | None = None) -> dict:
    """§9: each stage's projected GPU-hours, without reserve. `done` restricts `champions` and `evaluate` to
    the runs that completed."""
    every = REGISTERED["checkpoint_every"]
    out = {}
    for arm in ARMS:
        G, n = plan["G"][arm], plan["runs"][arm]
        t = train_timing(timing, arm, n)
        out[f"train-{arm}"] = 0.0 if n == 0 else (G * t["t_gen"] + n_checkpoints(G, every) * t["t_ckpt"]) / 3600
    runs = done if done is not None else plan["runs"]
    champs = synthetic_champions(runs)
    out["champions"] = len(champs) * timing["validation_32"] / 3600
    secs = 0.0
    for c in eval_plan(champs, coefs=None):
        secs += {"batch": timing["eval_plain"], "replay": timing["eval_donor"], "single": timing["eval_single"]}[c["kind"]]
    k = 1 + runs["ta"] + runs["tf"]
    secs += prepass_seconds(timing, k) + len(champs) * timing["probes"]
    out["evaluate"] = secs / 3600
    out["g-e"] = REGISTERED["ge_allowance_hours"]
    return out


def planned_total(spent: float, proj: dict) -> float:
    R = REGISTERED["reserve_factor"]
    return spent + sum(v * (R if k.startswith("train-") else 1.0) for k, v in proj.items())


CUT_STEPS = {"n to runs 0-3": lambda p: p["runs"].__setitem__("n", min(4, p["runs"]["n"])),
             "r dropped": lambda p: p["runs"].__setitem__("r", 0),
             "tf to 250 generations": lambda p: p["G"].__setitem__("tf", 250)}


def apply_cuts(timing: dict, spent: float) -> dict:
    """§10: the cuts in order, until the planned total fits the cap; "fits": False if none does."""
    plan = default_plan()
    for name in [None] + REGISTERED["cuts"]:
        if name is not None:
            CUT_STEPS[name](plan)
            plan["cuts"].append(name)
        proj = projections(timing, plan)
        total = planned_total(spent, proj)
        if total <= REGISTERED["cap_gpu_hours"]:
            break
    return {**plan, "projected_hours": proj, "planned_total": total, "fits": total <= REGISTERED["cap_gpu_hours"]}


def admit_training(stage: str, spent: float, proj: dict) -> bool:
    return spent + proj[stage] * REGISTERED["reserve_factor"] + proj["champions"] + proj["evaluate"] \
        <= REGISTERED["admit_hours"] + 1e-12


def admit_champions(spent: float, proj: dict) -> bool:
    return spent + proj["champions"] + proj["evaluate"] <= REGISTERED["cap_gpu_hours"] + 1e-12


def admit_evaluate(spent: float, proj: dict) -> bool:
    return spent + proj["evaluate"] <= REGISTERED["cap_gpu_hours"] + 1e-12


# ============================================================================== stage states

def stage_state(stage: str) -> str:
    if refused_path(stage).exists():  # a refusal settles the stage, even a refused rerun after a stop
        return "refused"
    path = E.record_path(stage)
    if path.exists():
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("outcome") == "completed":
            return "skipped" if rec.get("skipped") else "completed"
        if rec.get("outcome") == E.OUTCOMES["cap"]:
            return "cap-stopped"
        return "final-stopped" if rec.get("final") else "awaiting-rerun"
    if E.marker_path(stage).exists():
        return "killed"
    return "absent"


def refused_path(stage: str) -> Path:
    return EXP / f"{stage}-refused.json"


def check_order(stage: str, state_of) -> None:
    """§10: every earlier training stage settled; none refused (a refusal stops every later training stage)."""
    for earlier in TRAINING[:TRAINING.index(stage)]:
        st = state_of(earlier)
        if st == "refused":
            raise SystemExit(f"{earlier} was refused: no later training stage starts (§10)")
        if st not in SETTLED:
            raise SystemExit(f"{earlier} is {st}: it must be settled first")


def require_champions_state(state: str) -> None:
    if state != "completed":
        raise SystemExit(f"evaluate requires a completed champions stage (it is {state}, §5)")


def require_plan(args, prov) -> dict:
    p = E.require_earlier(args, prov, "project")
    if not p["plan"]["fits"]:
        raise SystemExit("even after every cut the planned total exceeds the cap: E3b-1 does not start; the owner is "
                         "asked (§10)")
    return {"project": p}


def require_ge_passed(args, prov) -> dict:
    out = require_plan(args, prov)
    g = E.require_earlier(args, prov, "g-e")
    if not g.get("passed"):
        raise SystemExit("g-e did not pass: no training stage starts (§10)")
    out["g-e"] = g
    return out


def spent_hours(t_start: float | None = None) -> float:
    """The cap clock's hours (completed attempts), plus this stage's own running time since `t_start`
    (`time.perf_counter`), which the clock only counts once the attempt ends."""
    extra = 0.0 if t_start is None else max(0.0, time.perf_counter() - t_start) / 3600
    return E.clock().spent_hours() + extra


def plan_of(earlier: dict) -> dict:
    return earlier["project"]["plan"]


def trained_records(args, prov) -> dict:
    """Every training stage's record, or None for one not run (refused, after a refusal, or cut to 0 runs)."""
    out, refused = {}, False
    for stage in TRAINING:
        st = stage_state(stage)
        if st == "refused" or (refused and st == "absent"):
            refused, out[stage] = True, None
        elif st in ("completed", "skipped"):
            out[stage] = E.require_earlier(args, prov, stage)
        elif st in ("final-stopped", "cap-stopped"):
            out[stage] = json.loads(E.record_path(stage).read_text(encoding="utf-8"))
        else:
            raise SystemExit(f"{stage} is {st}: every training stage must be settled first")
    return out


def completed_runs(trained: dict) -> dict:
    return {arm: [r["run"] for r in ((trained.get(f"train-{arm}") or {}).get("runs") or [])
                  if (trained.get(f"train-{arm}") or {}).get("outcome") == "completed"] for arm in ARMS}


# ============================================================================== stage: project

def time_second(fn, dev) -> float:
    """The second of two repeats (§9)."""
    out = 0.0
    for _ in range(2):
        if str(dev) != "cpu":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        fn()
        if str(dev) != "cpu":
            torch.cuda.synchronize()
        out = time.perf_counter() - t0
    return out


def cmd_project(args):
    def body(ctx):
        t_start = time.perf_counter()
        inputs = check_inputs()
        dev = ctx.args.device
        cfg = cfg_for("shared")
        cx = context(cfg)
        PR = REGISTERED["projection"]
        smoke_ids = lambda n: np.arange(PR["ids_first"], PR["ids_first"] + n)  # noqa: E731
        n_val, n_test_ = len(ids("validation")), n_test()
        timing = {"training": {}}
        for key, arm, n_runs in (("ta", "ta", None), ("tf", "tf", None), ("n", "n", None), ("n4", "n", 4), ("r", "r", None)):
            a = REGISTERED["arms"][arm]
            n_runs = n_runs or a["runs"]
            cfga = arm_cfg(arm)
            start = start_genome(cx, arm)
            runs = [EV.RunSpec(k, PR["seed"] + 100 * len(timing["training"]) + k, 0.0) for k in range(n_runs)]
            cands = Genome.cat([start] * n_runs)
            recs = []

            def train():
                recs[:] = EV.evolve_batch(cfga, cx["seed"].iface, cx["spec"], runs, generations=2, checkpoint_every=10 ** 6,
                                          validation_ids=smoke_ids(n_val), world_seed=PR["seed"], id_base=PR["train_base"],
                                          id_span=PR["train_span"], device=dev, check=ctx.cap.check, category=acct.category,
                                          initial=lambda r: Genome.cat([start] * cfga.evo.population), mutation_scales=lambda r: T.scales(cx["seed"].ext))

            def ckpt():
                with acct.category("holdout"):
                    rollout(cfga, cx["seed"].iface, on(cands, dev), smoke_ids(n_val), PR["seed"], dev,
                            chunk_worlds=n_runs * n_val)

            t_ckpt = time_second(ckpt, dev)
            time_second(train, dev)
            per_gen = [g["batch_seconds"] for g in recs[0].log]  # both generations carry a checkpoint (0 and the last)
            timing["training"][key] = {"t_gen": max(0.0, float(np.mean(per_gen)) - t_ckpt), "t_ckpt": t_ckpt,
                                       "composition": [n_runs * cfga.evo.population, a["W"], REGISTERED["colony"]],
                                       "batch_seconds": per_gen}
        pop32 = Genome.cat([cx["seed"].genome] * REGISTERED["ga"]["population"])
        with acct.category("holdout"):
            timing["validation_32"] = time_second(lambda: rollout(cfg, cx["seed"].iface, on(pop32, dev), smoke_ids(n_val),
                                                                  PR["seed"], dev), dev)
        names16 = ["seed"] * REGISTERED["chunk"]
        names8 = ["seed"] * REGISTERED["chunk_replay"]
        mazes = smoke_ids(n_test_)
        eps, _ = MR.replay_donors(mazes, PR["seed"], REGISTERED["c"])
        with acct.category("final"):
            timing["eval_plain"] = time_second(lambda: play_names(names16, "shared", mazes, cx, dev, recorder=True,
                                                                  run_seed=PR["seed"]), dev)
            timing["eval_donor"] = time_second(lambda: play_names(names8, "replay", mazes, cx, dev, run_seed=PR["seed"],
                                                                  coefs=np.ones(len(names8)), donor_eps=eps), dev)
            timing["eval_single"] = time_second(lambda: play_single("w2_alone", "shared", mazes, cx, dev, recorder=True,
                                                                    run_seed=PR["seed"]), dev)
        with acct.category("probe"):
            timing["probes"] = time_second(lambda: probe_organism(cx["seed"].genome, cx, cfg), "cpu")
        plan = apply_cuts(timing, spent_hours(t_start))
        return {"timing": timing, "plan": plan, "fixed_inputs": inputs,
                "note": "timings only, on smoke ids from 9 500 with the projection seed; no score is read"}

    return E.run_stage(args, "project", lambda a, prov: {}, body)


# ============================================================================== stage: g-e

def ge_verdict(got, want, composition) -> dict:
    return {"all_match": got == want,
            "matching_generations_per_run": [sum(a == b for a, b in zip(x, y)) for x, y in zip(got, want)],
            "composition": composition}


def ge_passed(cpu: dict, gpu: dict, hook: dict, smoke: bool | None = None) -> bool:
    smoke = SMOKE if smoke is None else smoke
    gpu_ok = bool(gpu.get("all_match")) or (smoke and "skipped" in gpu)
    return bool(cpu.get("passed")) and bool(hook.get("identical")) and gpu_ok


def gpu_leg(dev, cap) -> dict:
    """E2's formal GA batch, generations 0-25, every generation's best-genome hash against `train-ga.json`."""
    E2 = _load("e2_pristine_for_e3b1_ge", "e2.py")
    cfg2 = E2.task_config()
    con = load_connectome()
    iface2, spec2 = load_interface(con), BrainSpec.from_connectome(con)
    committed = json.loads((ROOT / "experiments" / "E2-optimizer-screen" / "train-ga.json").read_text(encoding="utf-8"))
    runs = [EV.RunSpec(**r["spec"]) for r in committed["records"]]
    want = [[g["best_sha256"] for g in r["log"][:26]] for r in committed["records"]]
    idsd = E2.REGISTERED["ids"]["train"]
    recs = EV.evolve_batch(cfg2, iface2, spec2, runs, generations=26, checkpoint_every=E2.REGISTERED["checkpoint_every"],
                           validation_ids=E2.validation_ids(), world_seed=E2.REGISTERED["world_seed"],
                           id_base=idsd["base"], id_span=idsd["span"], device=dev, check=cap.check, category=acct.category)
    got = [[g["best_sha256"] for g in r.log] for r in recs]
    return ge_verdict(got, want, [len(runs) * cfg2.evo.population, cfg2.evo.worlds_per_strain, 1])


def hook_leg(cap) -> dict:
    """§5: `evolve_batch` with the snapshot hook off leaves E2's CPU smoke batch bit-identical (against the hook
    on, which must change nothing but the snapshots)."""
    E2 = _load("e2_pristine_for_e3b1_hook", "e2.py")
    cfg2 = E2.task_config()
    cfg2.world.max_ticks = 40
    cfg2.evo.population, cfg2.evo.elites, cfg2.evo.truncation, cfg2.evo.worlds_per_strain = 4, 1, 2, 2
    con = load_connectome()
    iface2, spec2 = load_interface(con), BrainSpec.from_connectome(con)
    runs = [EV.RunSpec(i, 1_128_000 + i, 0.0) for i in range(2)]
    kw = dict(generations=3, checkpoint_every=2, validation_ids=np.arange(5000, 5004), world_seed=1_128_000,
              id_base=2500, id_span=2500, device="cpu", check=cap.check, category=acct.category)
    off = EV.evolve_batch(cfg2, iface2, spec2, runs, **kw)
    with_hook = EV.evolve_batch(cfg2, iface2, spec2, runs, snapshot_at=(1,), **kw)
    same = all([g["best_sha256"] for g in a.log] == [g["best_sha256"] for g in b.log]
               and [genome_hash(a.final, k) for k in range(a.final.n_strains)]
               == [genome_hash(b.final, k) for k in range(b.final.n_strains)]
               and a.checkpoints == b.checkpoints for a, b in zip(off, with_hook))
    return {"identical": bool(same), "composition": [len(runs) * 4, 2, 1], "device": "cpu"}


def cmd_ge(args):
    def body(ctx):
        check_inputs()
        ref_path = ROOT / EQ_REFERENCE
        ref = json.loads(ref_path.read_text(encoding="utf-8"))
        with acct.category("calibration"):
            new = EQ.run(ROOT, Path(ROOT / "data" / "cache" / "cook2019_herm.npz"))
            hook = hook_leg(ctx.cap)
        cpu = EQ.compare(ref, new)
        cpu["reference_sha256"] = E.sha256_bytes(ref_path)
        cpu["engines"] = {"reference": ref.get("engine"), "compared": new.get("engine")}
        with acct.category("calibration"):
            gpu = {"skipped": "smoke"} if SMOKE else gpu_leg(ctx.args.device, ctx.cap)
        return {"passed": ge_passed(cpu, gpu, hook), "cpu": cpu, "gpu": gpu, "snapshot_hook": hook}

    return E.run_stage(args, "g-e", require_plan, body)


# ============================================================================== stages: training

def attempts_path(stage: str) -> Path:
    return OUT / f"{stage}-attempts.json"


def read_attempts(stage: str) -> list:
    p = attempts_path(stage)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def next_attempt(entries: list) -> dict:
    """§5's training rules over the earlier attempts' outcomes ("non-finite" with its `runs`, "crash or kill",
    "completed"): {"attempt": k, "exclude": [...]} or {"final": reason}."""
    k = len(entries) + 1
    if k == 1:
        return {"attempt": 1, "exclude": []}
    if k == 2:
        return {"attempt": 2, "exclude": []}  # unchanged, after a crash, a kill or a non-finite score
    if k == 3 and entries[1].get("outcome") == "non-finite":
        bad = sorted({r for e in entries if e.get("outcome") == "non-finite" for r in e.get("runs", [])})
        return {"attempt": 3, "exclude": bad}
    return {"final": "no further attempt (§5)"}


def _closed(entries: list) -> list:
    e = [dict(x) for x in entries]
    if e and e[-1].get("outcome") is None:
        e[-1]["outcome"] = "crash or kill"
    return e


def attempts_final(entries: list) -> bool:
    """After a stop: does §5 allow no further attempt?"""
    return "final" in next_attempt(_closed(entries))


def train_attempts(entries: list, runs_all: list, run_batch, save, admit=lambda k: True) -> dict:
    """Attempts inside one stage attempt: a non-finite score is retried here; a crash propagates, with its attempt
    left open (outcome None) for the next start to close. `entries` is updated in place and saved before each
    attempt runs, so the record names a non-finite run before the batch aborts. Only a completed attempt's
    populations are returned. `admit(k)` admits each later attempt inside the stage under §10, as its stage was
    admitted; a refusal ends the stage, its runs not run."""
    entries[:] = _closed(entries)
    while True:
        nxt = next_attempt(entries)
        if "final" in nxt:
            save(entries)
            return {"final": True, "records": None, "runs": [], "failed": list(runs_all), "entries": entries}
        if len(entries) and entries[-1].get("outcome") == "non-finite" and not admit(nxt["attempt"]):
            entries.append({"attempt": nxt["attempt"], "outcome": "not admitted"})
            save(entries)
            return {"final": True, "not_admitted": True, "records": None, "runs": [], "failed": list(runs_all),
                    "entries": entries}
        runs = [r for r in runs_all if r not in nxt["exclude"]]
        entries.append({"attempt": nxt["attempt"], "runs_in_batch": runs, "outcome": None})
        save(entries)
        try:
            recs = run_batch(runs)
        except FloatingPointError as e:
            entries[-1].update(outcome="non-finite", runs=sorted(getattr(e, "runs", [])), error=str(e))
            save(entries)
            continue
        entries[-1]["outcome"] = "completed"
        save(entries)
        return {"final": False, "records": recs, "runs": runs, "failed": sorted(set(runs_all) - set(runs)),
                "entries": entries}


def cmd_train(args, arm: str):
    stage = f"train-{arm}"
    held = {}

    def requires(a, prov):
        out = require_ge_passed(a, prov)
        check_order(stage, stage_state)
        entries = read_attempts(stage)
        if entries and attempts_final(entries):
            raise SystemExit(f"{stage} has used every attempt §5 allows: it is final")
        p = plan_of(out)
        proj = p["projected_hours"]
        spent = spent_hours()
        if p["runs"][arm] > 0 and not SMOKE and not admit_training(stage, spent, proj):
            E.write_atomic(refused_path(stage), {
                "stage": stage, "spent_hours": spent, "projected_hours": proj, "admit_hours": REGISTERED["admit_hours"],
                "provenance": prov, "decision": "not admitted (§10); no later training stage starts, and their runs "
                                                "are not run"})
            raise SystemExit(f"{stage} not admitted under §10 (spent {spent:.2f} h)")
        held["plan"] = p
        return out

    def body(ctx):
        check_inputs()
        dev = ctx.args.device
        p = held["plan"]
        a = REGISTERED["arms"][arm]
        runs_all = list(range(p["runs"][arm]))
        if not runs_all:
            return {"arm": arm, "skipped": True, "runs": [], "reason": "removed by the cuts (§10)", "cuts": p["cuts"]}
        G = p["G"][arm]
        cfg = arm_cfg(arm)
        cx = context(cfg)
        start = start_genome(cx, arm)
        snap = tuple(s for s in a["snapshot"] if s < G)
        entries = read_attempts(stage)
        save = lambda e: E.write_atomic(attempts_path(stage), e)  # noqa: E731
        ctx.salvage = lambda: {"attempts": entries, "final": attempts_final(entries), "failed_runs": runs_all}

        def run_batch(runs):
            specs = [EV.RunSpec(i, run_seed(arm, i), 0.0) for i in runs]
            return EV.evolve_batch(cfg, cx["seed"].iface, cx["spec"], specs, generations=G,
                                   checkpoint_every=REGISTERED["checkpoint_every"], validation_ids=ids("learning"),
                                   world_seed=seed(), id_base=REGISTERED["train"]["base"],
                                   id_span=REGISTERED["train"]["span"], device=dev, check=ctx.cap.check,
                                   category=acct.category, initial=lambda r: Genome.cat([start] * cfg.evo.population),
                                   mutation_scales=lambda r: T.scales(cx["seed"].ext), snapshot_at=snap)

        admit = lambda k: SMOKE or admit_training(stage, spent_hours(), p["projected_hours"])  # noqa: E731
        res = train_attempts(entries, runs_all, run_batch, save, admit=admit)
        if res.get("not_admitted"):
            raise RuntimeError(f"attempt {res['entries'][-1]['attempt']} was not admitted under §10: the stage ends, "
                               "its runs not run")
        if res["final"]:
            raise RuntimeError("every attempt §5 allows ended with a non-finite score: every run failed")
        out_runs = []
        for rec in res["records"]:
            i = rec.spec.run
            T.assert_frozen(start, rec.final, cx["seed"].ext)
            for g_idx, s in rec.snapshots.items():
                T.assert_frozen(start, s, cx["seed"].ext)
        for rec in res["records"]:  # saved only once every run of the completed attempt has passed the assertion
            i = rec.spec.run
            for g_idx, s in rec.snapshots.items():
                save_population(genomes_file(arm, i, SNAP_READ), s, cfg=cfg, run=i, stage=stage, generation=g_idx)
            save_population(genomes_file(arm, i, "final"), rec.final, cfg=cfg, run=i, stage=stage, generation=G - 1)
            out_runs.append({"run": i, "run_seed": rec.spec.run_seed, "generations": G,
                             "final_sha256": [genome_hash(rec.final, k) for k in range(rec.final.n_strains)],
                             "snapshot_sha256": {str(g): [genome_hash(s, k) for k in range(s.n_strains)]
                                                 for g, s in rec.snapshots.items()},
                             "log": rec.log, "generation0": rec.generation0,
                             "learning_curve": [{k: v for k, v in c.items() if k != "validation_counts"}
                                                for c in rec.checkpoints],
                             "learning_curve_counts": [c["validation_counts"] for c in rec.checkpoints],
                             "frozen_assertion": "passed"})
        return {"arm": arm, "access": a["access"], "G": G, "W": a["W"], "start": a["start"], "runs": out_runs,
                "failed_runs": res["failed"], "attempts": res["entries"], "cuts": p["cuts"],
                "composition": {"training": [len(res["runs"]) * cfg.evo.population, a["W"], REGISTERED["colony"]],
                                "learning_curve": [len(res["runs"]), len(ids("learning")), REGISTERED["colony"]]}}

    return E.run_stage(args, stage, requires, body)


# ============================================================================== stage: champions

def read_points(trained: dict) -> list:
    """(arm, run, read) for every completed run: "final" (index G − 1) and, for T-F, "snap124"."""
    out = []
    runs = completed_runs(trained)
    for arm in ARMS:
        for i in runs[arm]:
            out.append((arm, i, "final"))
            if arm == "tf":
                out.append((arm, i, "snap124"))
    return out


def snap_index() -> int:
    """T-F's read during training: the population evaluated at index 124 (index 1 in smoke)."""
    return REGISTERED["arms"]["tf"]["snapshot"][0]


def champion_index(means: np.ndarray) -> int:
    """The best validation mean, ties to the lower population index."""
    means = np.asarray(means)
    return int(np.flatnonzero(means == means.max())[0])


def validate_read_point(pop: Genome, arm: str, dev, rollout_fn=rollout):
    """All 32 genomes on the 128 validation mazes with the arm's own access, at episode 0 (§6)."""
    cfg = arm_cfg(arm)
    cx = context(cfg)
    r = rollout_fn(cfg, cx["seed"].iface, on(pop, dev), ids("validation"), seed(), dev)
    means = np.asarray(r.score, dtype=np.float64).mean(axis=1)
    return champion_index(means), means


def cmd_champions(args):
    def requires(a, prov):
        out = require_ge_passed(a, prov)
        out["trained"] = trained_records(a, prov)
        done = {arm: len(v) for arm, v in completed_runs(out["trained"]).items()}
        proj = projections(out["project"]["timing"], plan_of(out), done)
        if not SMOKE and not admit_champions(E.clock().spent_hours(), proj):
            raise SystemExit("champions not admitted: champions and evaluate together would exceed the cap (§10)")
        return out

    def body(ctx):
        check_inputs()
        dev = ctx.args.device
        trained = ctx.earlier["trained"]
        champs = []
        for arm, i, read in read_points(trained):
            cfg = arm_cfg(arm)
            cx = context(cfg)
            pop = load_genomes(arm, i, read, cx, cfg)
            rec = next(r for r in trained[f"train-{arm}"]["runs"] if r["run"] == i)
            want = rec["final_sha256"] if read == "final" else rec["snapshot_sha256"][str(snap_index())]
            if [genome_hash(pop, k) for k in range(pop.n_strains)] != want:
                raise SystemExit(f"{arm} run {i}'s {read} population does not match its record")
            ctx.cap.check()
            with acct.category("holdout"):
                k, means = validate_read_point(pop, arm, dev)
            ch = pop.select([k])
            save_population(genomes_file(arm, i, f"champion-{read}"), ch, cfg=cfg, run=i, read=read, index=k)
            champs.append({"arm": arm, "run": i, "read": read, "index": k, "sha256": genome_hash(ch, 0),
                           "validation_mean": float(means[k]), "validation_means": [float(x) for x in means],
                           "access": REGISTERED["arms"][arm]["access"]})
        return {"champions": champs, "read_points": len(champs),
                "composition": {"validation": [REGISTERED["ga"]["population"], len(ids("validation")),
                                               REGISTERED["colony"]]}}

    return E.run_stage(args, "champions", requires, body)


# ============================================================================== stage: evaluate

def name_of(c: dict) -> str:
    return f"{c['arm']}:{c['run']}:{c['read']}"


def chunks(items: list, size: int) -> list:
    return [items[k:k + size] for k in range(0, len(items), size)]


def eval_plan(champs: list, coefs: dict | None) -> list:
    """§6's chunks, in their fixed order: blocks 1-6, within a block the organisms in the order of §6's table
    (the arms T-A, T-F, N, R, runs by index). `coefs` None plans replay for every block-1 organism."""
    key = lambda c: (ARMS.index(c["arm"]), c["run"])  # noqa: E731
    final = sorted([c for c in champs if c["read"] == "final"], key=key)
    b1 = ["seed"] + [name_of(c) for c in final if c["arm"] in ("ta", "tf")]
    b4 = [name_of(c) for c in sorted([c for c in champs if c["read"] == "snap124"], key=key)]
    b6 = [name_of(c) for c in final if c["arm"] in ("n", "r")] + (["degraded"] if any(c["arm"] == "r" for c in champs) else [])
    plan = []

    def add(block, cond, names, kind, size):
        for k, part in enumerate(chunks(names, size)):
            plan.append({"block": block, "cond": cond, "names": part, "kind": kind, "k": k,
                         "recorder": cond == "shared" and block in (1, 4, 6)})

    for block, cond in ((1, "shared"), (2, "none"), (3, "own")):
        add(block, cond, b1, "batch", REGISTERED["chunk"])
    add(4, "shared", b4, "batch", REGISTERED["chunk"])
    for cond in ("peers", "scramble"):
        add(5, cond, b1, "batch", REGISTERED["chunk"])
    add(5, "replay", [n for n in b1 if coefs is None or coefs.get(n) is not None], "replay", REGISTERED["chunk_replay"])
    for cond, singles in (("shared", ("w2_alone", "follower")), ("none", ("w2_alone", "follower", "oracle", "walk"))):
        add(6, cond, b6, "batch", REGISTERED["chunk"])
        for s in singles:
            plan.append({"block": 6, "cond": cond, "names": [s], "kind": "single", "k": s,
                         "recorder": cond == "shared"})
    return plan


def chunk_path(c: dict) -> Path:
    tail = f"c{c['k']:02d}" if isinstance(c["k"], int) else c["k"]
    return EXP / f"eval-b{c['block']}-{c['cond']}-{tail}.npz"


def run_chunk(path: Path, names: list, play) -> None:
    """One chunk: skipped if a completed attempt saved it (its observations stand, §5), else played and saved
    atomically. `play(names)` returns per-organism, per-maze arrays."""
    names = [str(n) for n in names]
    if path.exists():
        with np.load(path, allow_pickle=False) as z:
            have = [str(n) for n in z["names"]]
        if have != names:
            raise SystemExit(f"{path.name} holds other organisms than planned ({have} against {names})")
        return
    arrays = dict(play(names))
    arrays["names"] = np.asarray(names)
    tmp = path.with_name(path.stem + ".tmp.npz")
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(tmp, **{k: np.asarray(v) for k, v in arrays.items()})
    E.replace(tmp, path)


def summary_arrays(ev: dict, H: int) -> dict:
    """[organisms, mazes] per measure (§6), from events shaped [organisms, mazes, ...]."""
    vt = ev["visit_tick"]
    S, n = vt.shape[:2]
    f = lambda x: np.asarray(x).reshape(S * n, *np.asarray(x).shape[2:])  # noqa: E731
    ticks = np.maximum(f(ev["ticks"]).astype(np.float64), 1)[:, None]
    legs = MM.legs(f(vt))
    rate, unvisited = MM.later_leg_rate(f(vt), H)
    out = {"visits": MM.colony_mean(f(ev["visits"])), "legs": MM.colony_mean(legs), "later_leg_rate": rate,
           "unvisited_share": unvisited, "later_first_b": MM.later_first_b(f(ev["first_b_tick"]), H),
           "entries": f(ev["entries"]).reshape(S * n, -1).sum(axis=1) / vt.shape[2],
           "round_trip_share": (legs >= 2).mean(axis=-1),
           "occluded_share": MM.colony_mean(f(ev["occluded_ticks"]) / ticks),
           "exposure_mean": MM.colony_mean(f(ev["exposure_sum"]) / ticks),
           "exposure_zero_share": MM.colony_mean(f(ev["exposure_zero_ticks"]) / ticks)}
    return {k: np.asarray(v, dtype=np.float64).reshape(S, n) for k, v in out.items()}


def nose_arrays(nr: dict, S: int, n: int) -> dict:
    return {"nose_qualified": np.asarray(nr["qualified"]).reshape(S, n),
            "nose_above_1.0": np.asarray(nr["above"]["1.0"]).reshape(S, n)}


def org_genome(name: str, cx, cfg) -> Genome:
    if name == "seed":
        return cx["seed"].genome
    if name == "degraded":
        return cx["degraded"].genome
    arm, i, read = name.split(":")
    return load_genomes(arm, int(i), f"champion-{read}", cx, cfg)


def play_names(names, cond, mazes, cx, dev, *, recorder=False, coefs=None, donor_eps=None, run_seed=None):
    """A chunk of organisms that share the seed's layout, in one batch (§6's composition)."""
    cfg = cfg_for("shared" if cond == "replay" else cond)
    pop = Genome.cat([org_genome(n, cx, cfg) for n in names])
    ev = MR.play_batch(cfg, cx["seed"].iface, Brain(on(pop, dev)), np.arange(len(names)), mazes,
                       seed() if run_seed is None else run_seed, dev, access=cond, donor_episodes=donor_eps,
                       replay_coef=coefs, nose_range=recorder)
    out = summary_arrays(ev, int(cfg.world.max_ticks))
    if recorder:
        out.update(nose_arrays(ev["nose_range"], len(names), len(mazes)))
    return out


def play_single(name, cond, mazes, cx, dev, *, recorder=False, run_seed=None):
    """W2 alone on the carrier (an organism of its own layout) or a scripted controller, on every maze."""
    cfg = cfg_for(cond)
    rs = seed() if run_seed is None else run_seed
    if name == "w2_alone":
        org = cx["w2"]
        ev = MR.play(cfg, org.iface, lambda: MO.brain(org, dev), mazes, rs, dev, access=cond, nose_range=recorder)
    else:
        iface = cx["plain_iface"]
        mk = {"follower": MC.follower, "oracle": MC.oracle, "walk": MC.reflex_walk}[name]
        ev = MR.play(cfg, iface, lambda: mk(iface, cfg, device=dev), mazes, rs, dev, access=cond, nose_range=recorder)
    n = len(mazes)
    ev1 = {k: (v[None] if isinstance(v, np.ndarray) and v.shape[:1] == (n,) else v) for k, v in ev.items()}
    out = summary_arrays(ev1, int(cfg.world.max_ticks))
    if recorder:
        pw = ev["nose_range"]["per_world"]
        out.update(nose_arrays({"qualified": pw["qualified"], "above": pw["above"]}, 1, n))
    return out


def replay_coefficient(shared: float, donor: float):
    """The organism's own coefficient (§6): its exposure to live peers over its exposure to the donor at
    coefficient 1; None ("not read") when the donor exposure is 0."""
    return None if donor == 0 else float(shared / donor)


def replay_prepass(names: list, play, maze_ids) -> dict:
    """§6's pre-pass on the replay-calibration block: a shared leg (numerator) in chunks of 16, then a replay
    leg at coefficient 1 (denominator) in chunks of 8. `play(names, cond, maze_ids, coefs)` returns arrays."""
    shared, donor = {}, {}
    for part in chunks(names, REGISTERED["chunk"]):
        ex = play(part, "shared", maze_ids, None)["exposure_mean"]
        shared.update({n: float(np.mean(ex[i])) for i, n in enumerate(part)})
    for part in chunks(names, REGISTERED["chunk_replay"]):
        ex = play(part, "replay", maze_ids, {n: 1.0 for n in part})["exposure_mean"]
        donor.update({n: float(np.mean(ex[i])) for i, n in enumerate(part)})
    return {n: replay_coefficient(shared[n], donor[n]) for n in names}


def probe_organism(genome: Genome, cx, cfg) -> dict:
    """Block 7: the latch structure from the organism's own q self-weight and bias; if bistable, the component
    tests and the one-nose checks at its two stable states, the upper for goal A (§6)."""
    ext = cx["seed"].ext
    w = MO.named_edges(genome, ext)[(O.Q, O.Q)]
    b = float(genome.bias[0, ext.index(O.Q)])
    st = L.structure(w, b)
    out = {"structure": st.kind, "w_qq": float(w), "b_q": b}
    if st.kind != "bistable":
        return out
    states = {"A": max(st.states), "B": min(st.states)}
    pc = P.ProbeContext(ext, cx["seed"].iface, cfg, device="cpu")
    g = genome if str(genome.w.device) == "cpu" else EV.moved(genome, "cpu")
    comp = P.component_tests(g, pc, states=states, levels=levels())
    one = B0.one_nose_checks(g, pc, states, levels(), REGISTERED["probe"]["high"])
    out.update(states=states, active=comp["active"], inactive=comp["inactive"],
               switching=comp["switching"]["passed"], startup=comp["startup"]["passed"], offset=comp["offset"]["passed"],
               active_passed=active_passes(comp["active"]["values"]), one_nose=one["values"],
               one_nose_passed=one["passed_up_to_high_level"])
    return out


def active_passes(values: dict) -> bool:
    """E3b-0's thresholds (§6): K_D ≥ 30 at levels m ≤ 0.35; K_D × m ≥ 10.5 at 0.35 < m ≤ 1.0; above 1.0, reported
    only. Keys are "<goal>@<level>"."""
    R = REGISTERED["probe"]
    ok = True
    for k, v in values.items():
        m = float(k.split("@")[1])
        if m <= R["low"]:
            ok &= v >= R["k_d_min"]
        elif m <= R["high"]:
            ok &= v * m >= R["relative_min"]
    return bool(ok)


def cmd_evaluate(args):
    def requires(a, prov):
        out = require_ge_passed(a, prov)
        require_champions_state(stage_state("champions"))
        out["champions"] = E.require_earlier(a, prov, "champions")
        done = {arm: 0 for arm in ARMS}
        for c in out["champions"]["champions"]:
            done[c["arm"]] += c["read"] == "final"
        proj = projections(out["project"]["timing"], plan_of(out), done)
        if not SMOKE and not admit_evaluate(E.clock().spent_hours(), proj):
            raise SystemExit("evaluate not admitted (§10)")
        return out

    def body(ctx):
        check_inputs()
        dev = ctx.args.device
        cfg = cfg_for("shared")
        cx = context(cfg)
        champs = ctx.earlier["champions"]["champions"]
        for c in champs:
            if genome_hash(org_genome(name_of(c), cx, cfg), 0) != c["sha256"]:
                raise SystemExit(f"{name_of(c)}'s champion does not match its record")
        b1 = [n for c in eval_plan(champs, None) if c["block"] == 1 for n in c["names"]]
        out = {}
        with test_block_open():
            test = ids("test")
            replay_or_later = lambda c: c["block"] == 6 or (c["block"] == 5 and c["cond"] == "replay")  # noqa: E731
            for c in eval_plan(champs, None):  # blocks 1-4, then block 5's peers and scramble
                if not replay_or_later(c):
                    run_planned(c, test, cx, dev, ctx.cap)
            calib = ids("calibration")
            calib_eps, calib_exc = MR.replay_donors(calib, seed(), REGISTERED["c"])

            def calib_play(names, cond, maze_ids, coefs):
                k = calib_play.k[cond]
                calib_play.k[cond] += 1
                path = EXP / f"calib-{cond}-c{k:02d}.npz"
                run_chunk(path, names, lambda nm: timed(ctx.cap, lambda: play_names(
                    nm, cond, maze_ids, cx, dev, coefs=None if coefs is None else np.ones(len(nm)),
                    donor_eps=calib_eps if cond == "replay" else None)))
                with np.load(path, allow_pickle=False) as z:
                    return {"exposure_mean": z["exposure_mean"]}
            calib_play.k = {"shared": 0, "replay": 0}
            coefs = replay_prepass(b1, calib_play, calib)
            test_eps, test_exc = MR.replay_donors(test, seed(), REGISTERED["c"])
            for c in eval_plan(champs, coefs):  # then block 5's replay, then block 6
                if replay_or_later(c):
                    run_planned(c, test, cx, dev, ctx.cap, coefs=coefs, donor_eps=test_eps)
        with acct.category("probe"):
            probes = {name_of(c): probe_organism(org_genome(name_of(c), cx, cfg), cx, cfg) for c in champs}
        plan = plan_of(ctx.earlier)
        readings = compute_readings(load_blocks(), champs, plan, n_mazes=n_test())
        out.update(replay_coefficients=coefs, donor_exceptions={"calibration": calib_exc, "test": test_exc},
                   probes=probes, readings=readings, wording=wording(plan),
                   composition={"plain": [REGISTERED["chunk"], n_test(), REGISTERED["colony"]],
                                "replay": [2 * REGISTERED["chunk_replay"], n_test(), REGISTERED["colony"]],
                                "single": [1, n_test(), REGISTERED["colony"]]})
        return out

    return E.run_stage(args, "evaluate", requires, body)


def timed(cap, fn):
    cap.check()
    with acct.category("final"):
        return fn()


def run_planned(c: dict, test, cx, dev, cap, coefs=None, donor_eps=None) -> None:
    if c["kind"] == "single":
        play = lambda nm: timed(cap, lambda: play_single(nm[0], c["cond"], test, cx, dev, recorder=c["recorder"]))  # noqa: E731
    elif c["kind"] == "replay":
        play = lambda nm: timed(cap, lambda: play_names(nm, "replay", test, cx, dev, coefs=np.asarray([coefs[n] for n in nm]),  # noqa: E731
                                                         donor_eps=donor_eps))
    else:
        play = lambda nm: timed(cap, lambda: play_names(nm, c["cond"], test, cx, dev, recorder=c["recorder"]))  # noqa: E731
    run_chunk(chunk_path(c), c["names"], play)


# ============================================================================== readings (§7)

def load_blocks() -> dict:
    """{"b<block>-<cond>": {organism: {measure: [mazes]}}} from every completed chunk."""
    out = {}
    for p in sorted(EXP.glob("eval-b*.npz")):
        if p.name.endswith(".tmp.npz"):
            continue
        key = "-".join(p.stem.split("-")[1:3])
        with np.load(p, allow_pickle=False) as z:
            for i, n in enumerate(str(x) for x in z["names"]):
                out.setdefault(key, {})[n] = {k: z[k][i] for k in z.files if k != "names"}
    return out


def _mean(block: dict, name: str, measure: str, n_mazes: int):
    """The organism's mean over the test block, or None unless it covers every maze (§7)."""
    if name not in block or measure not in block[name]:
        return None
    x = np.asarray(block[name][measure], dtype=np.float64)
    return float(x.mean()) if len(x) == n_mazes else None


def compute_readings(blocks: dict, champs: list, plan: dict, *, n_mazes: int) -> dict:
    """§7's registered readings, their descriptors and the descriptive ones, from whatever blocks completed."""
    sh, no, own = blocks.get("b1-shared", {}), blocks.get("b2-none", {}), blocks.get("b3-own", {})
    b4, b6s, b6n = blocks.get("b4-shared", {}), blocks.get("b6-shared", {}), blocks.get("b6-none", {})
    finals = {arm: [name_of(c) for c in sorted(champs, key=lambda c: c["run"]) if c["arm"] == arm and c["read"] == "final"]
              for arm in ARMS}
    seed_sh = _mean(sh, "seed", "visits", n_mazes)
    out = {"wording": wording(plan), "final_index_tf": final_index(plan, "tf")}
    nr = {"label": "not read", "p": 1.0}
    if not seed_sh:  # missing, short, or a zero denominator
        out.update({k: dict(nr, reason="block 1's seed is missing or its mean is 0") for k in ("G", "S-gen", "S-trail", "S-peer")})
        out["holm"] = T.holm({"S-gen": None, "S-trail": None, "S-peer": None})
        return out

    def d_of(names, block_a, block_b=None, measure="visits", den=seed_sh, base=None):
        vals = []
        for n in names:
            a = _mean(block_a, n, measure, n_mazes)
            b = base if block_b is None else _mean(block_b, n, measure, n_mazes)
            if a is not None and b is not None:
                vals.append((a - b) / den)
        return vals

    # G
    dA, dF = d_of(finals["ta"], sh, base=seed_sh), d_of(finals["tf"], sh, base=seed_sh)
    legs = [float(np.median(sh[n]["legs"])) for n in finals["ta"] + finals["tf"]
            if _mean(sh, n, "visits", n_mazes) is not None]
    g = T.gate(dA, dF, legs_medians=legs)
    if g["label"] != "not read":
        g["delta_visits"] = g["estimate"] * seed_sh
        g["at_least_10pct"] = bool(g["lower_bound_95"] >= 0.10)
        g["pooled_t_p"] = float(stats.ttest_1samp(np.r_[dA, dF], 0, alternative="greater").pvalue) \
            if np.std(np.r_[dA, dF]) > 0 else (0.0 if np.mean(np.r_[dA, dF]) > 0 else 1.0)
        g["sign_flip_p"] = T.sign_flip(dA, dF)
        for nm, arr in (("schedule_A", np.asarray(dA)), ("schedule_F", np.asarray(dF))):
            se = arr.std(ddof=1) / math.sqrt(len(arr))
            tq = float(stats.t.ppf(0.975, len(arr) - 1))
            g[nm] = {"n": len(arr), "mean": float(arr.mean()), "ci95": [float(arr.mean() - tq * se), float(arr.mean() + tq * se)]}
        w2 = _mean(b6s, "w2_alone", "visits", n_mazes)
        fol = _mean(b6s, "follower", "visits", n_mazes)
        den_w2 = None if w2 is None else seed_sh - w2
        den_f = None if fol is None else fol - seed_sh
        g["multiple_of_seed_minus_w2"] = None if not den_w2 or den_w2 <= 0 else float(g["delta_visits"] / den_w2)
        g["multiple_of_follower_minus_seed"] = None if not den_f or den_f <= 0 else float(g["delta_visits"] / den_f)
        g["legs_medians"] = legs
        g["d"] = {"ta": dA, "tf": dF}
    out["G"] = g
    # S-gen
    pairs = []
    for n in finals["tf"]:
        a, b = _mean(sh, n, "visits", n_mazes), _mean(b4, n.replace(":final", ":snap124"), "visits", n_mazes)
        if a is not None and b is not None:
            pairs.append((a - b) / seed_sh)
    out["S-gen"] = {**T.paired(pairs), "diffs": pairs}
    # S-trail
    seed_no = _mean(no, "seed", "visits", n_mazes)
    e = {}
    for arm in ("ta", "tf"):
        e[arm] = [] if seed_no is None else [(x - y - (seed_sh - seed_no)) / seed_sh
                                             for x, y in ((_mean(sh, n, "visits", n_mazes), _mean(no, n, "visits", n_mazes))
                                                          for n in finals[arm]) if x is not None and y is not None]
    out["S-trail"] = {**T.gate(e["ta"], e["tf"]), "e": e}
    if seed_no is not None:
        out["S-trail"]["four_means"] = {
            "seed_shared": seed_sh, "seed_none": seed_no,
            "t_shared": float(np.mean([_mean(sh, n, "visits", n_mazes) for n in finals["ta"] + finals["tf"]
                                       if _mean(sh, n, "visits", n_mazes) is not None] or [np.nan])),
            "t_none": float(np.mean([_mean(no, n, "visits", n_mazes) for n in finals["ta"] + finals["tf"]
                                     if _mean(no, n, "visits", n_mazes) is not None] or [np.nan]))}
    # S-peer
    seed_own_fb = _mean(own, "seed", "later_first_b", n_mazes)
    pe = {}
    for arm in ("ta", "tf"):
        pe[arm] = [] if not seed_own_fb else d_of(finals[arm], sh, own, measure="later_first_b", den=seed_own_fb)
    out["S-peer"] = {**T.gate(pe["ta"], pe["tf"], alternative="less"), "values": pe}
    if seed_own_fb:
        out["S-peer"]["seed_shared_minus_own"] = (_mean(sh, "seed", "later_first_b", n_mazes) - seed_own_fb) / seed_own_fb
    out["holm"] = T.holm({k: (None if out[k]["label"] == "not read" else out[k]["p"]) for k in ("S-gen", "S-trail", "S-peer")})
    # descriptive
    shares = {}
    for blk in (sh, b4, b6s):
        for n, v in blk.items():
            if "nose_qualified" in v:
                q = float(np.sum(v["nose_qualified"]))
                shares[n] = None if q == 0 else float(np.sum(v["nose_above_1.0"]) / q)
    out["nose_share_above_1"] = shares
    out["descriptive"] = descriptive(blocks, champs, finals, seed_sh, n_mazes)
    out["means"] = {key: {n: {m: float(np.mean(x)) for m, x in v.items()} for n, v in blk.items()}
                    for key, blk in blocks.items()}
    out["not_read_blocks"] = sorted({"b5-peers", "b5-scramble", "b5-replay", "b6-shared", "b6-none"} - set(blocks))
    return out


def descriptive(blocks: dict, champs: list, finals: dict, seed_sh: float, n_mazes: int) -> dict:
    """§7's descriptive readings, as differences of means over the test block (no test)."""
    sh, no, own = blocks.get("b1-shared", {}), blocks.get("b2-none", {}), blocks.get("b3-own", {})
    b4, b6s, b6n = blocks.get("b4-shared", {}), blocks.get("b6-shared", {}), blocks.get("b6-none", {})

    def mean_d(names, block, base, measure="visits"):
        v = [(_mean(block, n, measure, n_mazes) - base) / seed_sh for n in names if _mean(block, n, measure, n_mazes) is not None]
        return {"n": len(v), "mean": float(np.mean(v)) if v else None, "values": v}

    seed_no = _mean(no, "seed", "visits", n_mazes)
    snaps = [n.replace(":final", ":snap124") for n in finals["tf"]]
    out = {"S-worlds": {"T-A": mean_d(finals["ta"], sh, seed_sh), "T-F at index 124": mean_d(snaps, b4, seed_sh)},
           "N_vs_T-A": {"shared": {"N": mean_d(finals["n"], b6s, seed_sh), "T-A": mean_d(finals["ta"], sh, seed_sh)}},
           "R": {"champions_vs_seed": mean_d(finals["r"], b6s, seed_sh)}}
    if seed_no is not None:
        out["N_vs_T-A"]["none"] = {"N": mean_d(finals["n"], b6n, seed_no), "T-A": mean_d(finals["ta"], no, seed_no)}
    deg = _mean(b6s, "degraded", "visits", n_mazes)
    if deg is not None:
        out["R"]["degraded_vs_seed"] = (deg - seed_sh) / seed_sh
        out["R"]["champions_vs_degraded"] = mean_d(finals["r"], b6s, deg)
    peer = {}
    for cond in ("replay", "scramble", "peers"):
        blk = blocks.get(f"b5-{cond}", {})
        for n in ["seed"] + finals["ta"] + finals["tf"]:
            a, b = _mean(blk, n, "later_leg_rate", n_mazes), _mean(own, n, "later_leg_rate", n_mazes)
            if a is not None and b is not None:
                peer.setdefault(f"{cond}_minus_own_later_leg_rate", {})[n] = a - b
            x = _mean(blk, n, "exposure_mean", n_mazes)
            if x is not None:
                peer.setdefault(f"{cond}_exposure", {})[n] = x
    out["peer_conditions"] = peer
    out["later_leg_rate_trail_contrast"] = {
        n: (_mean(sh, n, "later_leg_rate", n_mazes) - _mean(no, n, "later_leg_rate", n_mazes))
        for n in ["seed"] + finals["ta"] + finals["tf"]
        if _mean(sh, n, "later_leg_rate", n_mazes) is not None and _mean(no, n, "later_leg_rate", n_mazes) is not None}
    return out


def cmd_readings(args):
    rec = json.loads(E.record_path("champions").read_text(encoding="utf-8"))
    plan = json.loads(E.record_path("project").read_text(encoding="utf-8"))["plan"]
    out = compute_readings(load_blocks(), rec["champions"], plan, n_mazes=n_test())
    E.write_atomic(EXP / "readings.json", out)
    print(json.dumps({k: out[k].get("label") for k in ("G", "S-gen", "S-trail", "S-peer")}, indent=1))


# ============================================================================== smoke and main

def use_smoke(args) -> None:
    """Toy sizes on ids 9 300 and up, in runs/e3b1-smoke. Never results. This stage's and every later stage's
    files there are removed first."""
    global EXP, OUT, SMOKE, GUARDED
    EXP = OUT = ROOT / "runs" / "e3b1-smoke"
    SMOKE = True
    R = REGISTERED
    R["H"] = 120
    R["ga"].update(population=4, elites=1, truncation=2)
    for arm, a in R["arms"].items():
        a.update(runs=2, G=3, W=2)
    R["arms"]["tf"].update(G=4, snapshot=[1])
    R["checkpoint_every"] = 2
    R["ids"] = {"validation": [9300, 9303], "learning": [9310, 9313], "calibration": [9320, 9323], "test": [9330, 9334]}
    R["train"] = {"base": 9_000_000, "span": 1000}
    R["projection"].update(ids_first=9_400)
    configure()
    if args.command in STAGES:
        for s in STAGES[STAGES.index(args.command):]:
            for f in (E.record_path(s), E.marker_path(s), E.partial_path(s), refused_path(s), attempts_path(s)):
                if EXP in f.parents:
                    f.unlink(missing_ok=True)
        for f in list(EXP.glob("eval-*.npz")) + list(EXP.glob("calib-*.npz")):
            f.unlink()


COMMANDS = {"project": cmd_project, "g-e": cmd_ge, "train-ta": lambda a: cmd_train(a, "ta"),
            "train-tf": lambda a: cmd_train(a, "tf"), "train-n": lambda a: cmd_train(a, "n"),
            "train-r": lambda a: cmd_train(a, "r"), "champions": cmd_champions, "evaluate": cmd_evaluate,
            "readings": cmd_readings}


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
    smoke = "--smoke" in sys.argv
    out_dir = ROOT / "runs" / ("e3b1-smoke" if smoke else "e3b1")
    try:
        run_script(main, out_default=str(out_dir), default="measure", name="e3b1")
    finally:
        agg = out_dir / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
