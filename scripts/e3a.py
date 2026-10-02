"""E3a: the shuttle, a two-module organism with a latch (confirmatory; experiments/E3-ab-organism/E3a/
PREREGISTRATION.md, bound at 989da99, D165).

    python scripts/e3a.py project | g-e | g0 | g1 | calibrate-e | census | train --batch B | champions-2 |
                          champions-3 | calibrate | evaluate
    add --smoke for toy sizes in runs/e3a-smoke (never results)

Every stage runs once, inside E2's stage frame, and its record is committed and pushed before the next
stage starts. A gate that completes and fails is final; E3a then stops. The cap is 30 GPU-hours, counted
through `wormwars.accounting`; training batches are admitted one by one, and the evaluation is admitted
before it starts (§9). Per-world counts and the per-tick logs go to compressed .npz files beside the
records (committed); genomes stay local (rule 1), with every champion's and qualifier's grafted
parameters and hash in the records.
"""

from __future__ import annotations

import argparse
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
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e3 import assays as AS  # noqa: E402
from wormwars.e3 import controls as K  # noqa: E402
from wormwars.e3 import latch as L  # noqa: E402
from wormwars.e3 import organism as O  # noqa: E402
from wormwars.e3 import probe as P  # noqa: E402
from wormwars.e3 import readings as RD  # noqa: E402
from wormwars.e3 import samplers as S  # noqa: E402
from wormwars.e3.task import to_shuttle  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.e4s import comparator as C  # noqa: E402
from wormwars.evo.genomes import genome_hash, load_population, save_population  # noqa: E402
from wormwars.evo.rollout import rollout as _rollout  # noqa: E402
from wormwars.evo.rollout import rollout_brain  # noqa: E402


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


E = _load("e2_for_e3a", "e2.py")
D2 = _load("e2d_for_e3a", "e2d.py")
EQ = _load("e3_equivalence_for_e3a", "e3_equivalence.py")

EXP = ROOT / "experiments" / "E3-ab-organism" / "E3a"
OUT = ROOT / "runs" / "e3a"
PREREG = "experiments/E3-ab-organism/E3a/PREREGISTRATION.md"
EQ_REFERENCE = "experiments/E3-ab-organism/E3a/development-records/equivalence-reference.json"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PREREG, EQ_REFERENCE,
           "experiments/E4s-stereo-module/E4s-0/module.json", *E.E1_INPUTS]
SMOKE = False
TEST_OPEN = False  # the test worlds are read only inside stage 14 (§7)

BATCHES = ["ga", "rs", "stage3", "btask"]
TRAIN_STAGES = [f"train-{b}" for b in range(1, 5)]
STAGES = ["project", "g-e", "g0", "g1", "calibrate-e", "census", "train-1", "train-2", "champions-2",
          "train-3", "train-4", "champions-3", "calibrate", "evaluate"]
TERMINAL = ("completed", "skipped", "final-stopped", "refused")
CHUNK = 32  # strains per chunk for validation, calibration and test-world scoring (§5)

REGISTERED = {
    "world_seed": 1_171_000, "task_sigma": 6.0, "horizon": 600,
    "ga": {"population": 32, "elites": 3, "truncation": 8, "worlds_per_strain": 16, "generations": 300,
           "islands": 1, "mutation": {"w_sigma": 0.08, "g_sigma": 0.04, "tau_sigma": 0.15, "bias_sigma": 0.05,
                                      "p_mutate": 1.0}},
    "generations": {"ga": 300, "rs": 300, "stage3": 500, "btask": 800},
    "runs": 8, "checkpoint_every": 25, "rerun_kill_tail_seconds": 900,
    "cap_gpu_hours": 30.0, "admit_hours": 28.0, "reserve_factor": 1.25,
    "seeds": {"ga": 1_170_000, "ga_init": 1_172_000, "rs": 1_173_000, "census_ga": 1_174_000, "census_rs": 1_174_001,
              "btask_init": 1_175_000, "stage3": 1_176_000, "btask": 1_177_000, "projection": 1_179_000,
              "equivalence": 1_179_500},
    "ids": {"train": {"base": 944_000_000, "span": 500_000}, "validation": {"first": 945_000_000, "worlds": 256},
            "test": {"first": 946_000_000, "worlds": 256}, "census": {"first": 947_000_000, "worlds": 16},
            "assays": {"first": 947_100_000, "worlds": 256}, "gates": {"first": 947_200_000, "worlds": 1024},
            "calibration": {"first": 948_000_000, "worlds": 256}},
    "census": {"draws": 1024, "screen": 0.8, "cap": 64, "projected_qualifiers": 64},
    "e_stimulus": 2, "trace_worlds": 16,
    "carrier": {"forward": 1.0, "turn": 0.2},
    "scripted": {"s_shuttle_k32": {"k": 32.0, "speed": 1.0, "turn": 0.2},
                 "s_shuttle_k8192": {"k": 8192.0, "speed": 1.0, "turn": 0.0}},
    "batches": BATCHES,
}
RECORD = {s: s for s in STAGES}
WHAT = {s: f"E3a's {s}" for s in STAGES}


def configure() -> None:
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, OUT, GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E3a: not completed (the run stopped)",
                  "cap": "E3a: not completed (the cap was reached)"}
    E.RECORD.update(RECORD)
    E.WHAT.update(WHAT)


configure()
_E2_TASK_CONFIG = E.task_config


def task_config():
    """E1's Task N, checked against E1's gate record (E2's own check), with 02's GA, made the shuttle."""
    cfg = _E2_TASK_CONFIG()
    return to_shuttle(cfg, horizon=150 if SMOKE else REGISTERED["horizon"])


E.task_config = task_config  # the stage frame builds every stage's configuration through this


# ============================================================================== ids, seeds, context

SMOKE_OFFSETS = {"validation": 1000, "test": 2000, "census": 3000, "assays": 4000, "gates": 5000, "calibration": 6000}


def ids(key: str) -> np.ndarray:
    if key == "test" and not TEST_OPEN:
        raise SystemExit("the test worlds are read only in stage 14 (evaluate), after every champion is frozen")
    v = REGISTERED["ids"][key]
    if SMOKE:
        return E.SMOKE_IDS[SMOKE_OFFSETS[key]:SMOKE_OFFSETS[key] + v["worlds"]]
    return np.arange(v["first"], v["first"] + v["worlds"])


def train_span() -> tuple[int, int]:
    T = REGISTERED["ids"]["train"]
    return (T["base"], T["span"]) if not SMOKE else (0, 1000)


def formal_ranges() -> dict:
    out = {}
    for k, v in REGISTERED["ids"].items():
        out[k] = (v["base"], v["base"] + v["span"]) if "base" in v else (v["first"], v["first"] + v["worlds"])
    return out


def world_seed() -> int:
    return REGISTERED["world_seed"] if not SMOKE else REGISTERED["seeds"]["projection"]


def run_seed(arm: str, i: int) -> int:
    return REGISTERED["seeds"][{"ga": "ga", "rs": "ga", "stage3": "stage3", "btask": "btask"}[arm]] + int(i)


def n_runs() -> int:
    return REGISTERED["runs"]


def context(cfg, device: str) -> dict:
    """Every organism's grafted connectome, interface and engineered genome."""
    con = load_connectome()
    l1 = A.load_l1()
    mods = {"E": O.engineered(l1), "b_shared": O.b_shared(l1), "l1_switch": O.l1_switch(l1),
            "b_task": S.b_task_module(l1), "carrier": O.carrier_only()}
    ext = {k: G.graft_connectome(con, m) for k, m in mods.items()}
    iface = {k: G.graft_interface(ext[k], m) for k, m in mods.items()}
    for key, sig in (("A", {"a_left", "a_right"}), ("B", {"b_left", "b_right"})):
        iface[f"E_mean_{key}"] = G.graft_interface(ext["E"], mods["E"], probe="mean", probe_on=sig)
    car = REGISTERED["carrier"]

    def carrier(key, module=None):
        return C.carrier_genome(ext[key], module or mods[key], cfg.brain, forward=car["forward"], turn=car["turn"])

    genomes = {"E": carrier("E"), "no_latch": carrier("E", O.no_latch(l1)), "one_module": carrier("E", O.one_module(l1)),
               "b_shared": carrier("b_shared"), "l1_switch": carrier("l1_switch"), "carrier": carrier("carrier")}
    return {"con": con, "l1": l1, "mods": mods, "ext": ext, "iface": iface, "genomes": genomes,
            "spec": {k: BrainSpec.from_connectome(e) for k, e in ext.items()}}


def finite(a, what: str):
    a = np.asarray(a, dtype=np.float64)
    if not np.isfinite(a).all():
        raise FloatingPointError(f"non-finite {what}")
    return a


def play(cfg, iface, genome: Genome, world_ids, device, cap, chunk_strains: int, category: str = "final",
         brain_hook=None, seed: int | None = None) -> np.ndarray:
    w = np.asarray(world_ids)
    cap.check()
    with acct.category(category):
        r = _rollout(cfg, iface, EV.moved(genome, device), w, world_seed() if seed is None else seed, device,
                     chunk_worlds=chunk_strains * w.shape[-1], brain_hook=brain_hook)
    return finite(r.score, "a score")


def play_brain(cfg, iface, brain, world_ids, device, cap, category: str = "final") -> np.ndarray:
    cap.check()
    with acct.category(category):
        r = rollout_brain(cfg, iface, brain, np.asarray(world_ids), world_seed(), device=device)
    return finite(r.score, "a score")


def score_many(cfg, iface, genomes: list[Genome], world_ids, device, cap, category="final", hooks=None) -> list[np.ndarray]:
    """Single-strain organisms scored together, CHUNK strains per chunk (§5's composition); `hooks` maps
    an organism's position to {neuron: value} clamps."""
    pop = Genome.cat([g.select([0]) for g in genomes])
    hook = None
    if hooks:
        def hook(brain, lo, hi):
            brain.clamp([dict(hooks.get(k, {})) for k in range(lo, hi)])
    sc = play(cfg, iface, pop, world_ids, device, cap, CHUNK, category, brain_hook=hook)
    return [sc[k] for k in range(len(genomes))]


def selector_doc(genome: Genome, ext) -> list:
    return S.read_selector(genome, ext).tolist()


def grafted_doc(genome: Genome, ext) -> dict:
    """A genome's grafted parameters (every edge with a grafted end, every grafted neuron's τ and bias),
    by name: the record of an evolved organism without the worm block (rule 1)."""
    spec = BrainSpec.from_connectome(ext)
    n0 = int(ext.meta["worm_neurons"])
    edges = {}
    for p, (i, j) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist())):
        if i >= n0 or j >= n0:
            edges[f"{ext.names[i]}->{ext.names[j]}"] = [float(x) for x in genome.w[:, p].cpu()]
    nodes = {ext.names[k]: {"tau": [float(x) for x in genome.tau[:, k].cpu()],
                            "bias": [float(x) for x in genome.bias[:, k].cpu()]} for k in range(n0, ext.n)}
    return {"edges": edges, "neurons": nodes}


def save_npz(name: str, arrays: dict) -> None:
    path = EXP / f"{name}.npz"
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, **{k: np.asarray(v) for k, v in arrays.items()})
    E.replace(tmp, path)


def spent_hours() -> float:
    return E.clock().spent_hours()


def require(args, prov, *stages):
    return {s: E.require_earlier(args, prov, s) for s in stages}


def require_passed(args, prov, *gates) -> dict:
    recs = require(args, prov, *gates)
    for g in gates:
        if g != "project" and not recs[g].get("passed"):
            raise SystemExit(f"{g} completed and failed: E3a stops (only a dated, reviewed amendment goes on)")
    return recs


def require_gates(args, prov) -> dict:
    return require_passed(args, prov, "project", "g-e", "g0", "g1")


def require_fits(args, prov) -> dict:
    p = E.require_earlier(args, prov, "project")
    if not p["plan"]["fits"]:
        raise SystemExit("even E3a's minimum exceeds the cap: E3a does not start, and the owner is asked (§9)")
    return p


def genomes_file(arm: str, i: int, kind: str) -> Path:
    return E.OUT / "genomes" / f"{arm}-run{i:02d}-{kind}.npz"


def batch_state(stage: str) -> str:
    path = E.record_path(stage)
    if path.exists():
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("outcome") == "completed":
            return "skipped" if rec.get("skipped") else "completed"
        if rec.get("outcome") == E.OUTCOMES["cap"] or rec.get("final"):
            return "final-stopped"
        return "awaiting-rerun"
    if (E.EXP / f"{stage}-refused.json").exists():
        return "refused"
    if E.marker_path(stage).exists():
        return "killed"
    return "absent"


def require_batch(args, prov, k: int) -> dict:
    """An earlier training batch, settled: completed or skipped (its record, committed), stopped finally
    (its record, committed), or refused. Anything else refuses."""
    st = batch_state(f"train-{k}")
    if st == "absent" and any(batch_state(f"train-{j}") == "refused" for j in range(1, k)):
        st = "refused"  # §9: once a batch is refused, no later batch starts
    if st not in TERMINAL:
        raise SystemExit(f"train-{k} is {st}: it must be settled first")
    if st == "refused":
        return {"state": "refused"}
    rec = E.require_earlier(args, prov, f"train-{k}", final_ok=(st == "final-stopped"))
    return {**rec, "state": st}


# ============================================================================== the projection

def stage_hours(proj: dict, p: dict, qualifiers: int) -> dict:
    """§9's projected hours of every non-training stage, given the plan's run counts and the number of
    census qualifiers that get the full check."""
    R = n_runs()
    h = proj["unit"]
    btask_runs = R if p["btask_generations"] else 0
    organisms = R + p["rs_runs"] + p["stage3_runs"]  # Stage 2's, random sampling's and Stage 3's champions
    return {
        "champions-2": (R + p["rs_runs"]) * h["validation_per_run"],
        "champions-3": (p["stage3_runs"] + btask_runs) * h["validation_per_run"],
        "calibrate": (organisms + qualifiers) * h["calibration_per_organism"],
        "evaluate": ((organisms + qualifiers) * h["evaluation_per_organism"] + btask_runs * h["scoring_per_organism"]
                     + h["evaluation_fixed"]),
    }


def reductions(proj: dict, spent: float) -> dict:
    """§9: the planned total is every stage's projection x 1.25; reductions apply in order until it fits."""
    q = REGISTERED["census"]["projected_qualifiers"] * 2
    p = {"btask_generations": REGISTERED["generations"]["btask"], "stage3_runs": n_runs(), "rs_runs": n_runs(), "steps": []}

    def total():
        h = proj["unit"]
        t = proj["fixed"] + h["ga_batch"] + h["rs_batch"] * p["rs_runs"] / n_runs()
        t += h["stage3_batch"] * p["stage3_runs"] / n_runs() + h["btask_per_generation"] * p["btask_generations"]
        t += sum(stage_hours(proj, p, q).values())
        return REGISTERED["reserve_factor"] * t

    steps = [("B-task, to 300 generations", lambda: p.update(btask_generations=REGISTERED["generations"]["ga"])),
             ("B-task, dropped", lambda: p.update(btask_generations=0)),
             ("Stage 3, to runs 0-3", lambda: p.update(stage3_runs=4)),
             ("Stage 3, dropped", lambda: p.update(stage3_runs=0)),
             ("random sampling, to runs 0-3", lambda: p.update(rs_runs=4))]
    for name, apply in steps:
        if spent + total() <= REGISTERED["cap_gpu_hours"]:
            break
        apply()
        p["steps"].append(name)
    p["planned_total_hours"] = total()
    p["fits"] = spent + total() <= REGISTERED["cap_gpu_hours"]
    return p


def cmd_project(args):
    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg, dev)
        smoke = E.SMOKE_IDS
        seed = REGISTERED["seeds"]["projection"]
        Pn = cfg.evo.population
        R = n_runs() if not SMOKE else 2
        timing = {}

        def twice(fn):
            out = []
            for _ in range(2):
                t0 = time.perf_counter()
                fn()
                if dev != "cpu":
                    torch.cuda.synchronize()
                out.append(time.perf_counter() - t0)
            return {"seconds_first": out[0], "seconds": out[1]}

        ext, iface, base = cx["ext"]["E"], cx["iface"]["E"], cx["genomes"]["E"]
        n_gen = 4 if not SMOKE else 3
        runs = [EV.RunSpec(k, seed + k, 0.0) for k in range(R)]
        recs = EV.evolve_batch(cfg, iface, cx["spec"]["E"], runs, generations=n_gen, checkpoint_every=n_gen - 1,
                               validation_ids=smoke[9000:9000 + len(ids("validation"))], world_seed=seed, id_base=0,
                               id_span=5000, device=dev, check=ctx.cap.check, category=acct.category,
                               initial=lambda r: S.with_selector(base, ext, S.ga_draw(np.random.default_rng(r.run_seed), Pn)),
                               mutation_scales=lambda r: S.stage2_scales(ext))
        s = [x["batch_seconds"] for x in recs[0].log]
        per = float(np.median(s[1:-1])) if len(s) > 2 else float(s[-1])
        timing["training"] = {"seconds_per_generation": per, "seconds_per_checkpoint": max(0.0, float(s[-1]) - per),
                              "batch_seconds": s, "composition": [R * Pn, cfg.evo.worlds_per_strain, 1]}
        pop = S.with_selector(base, ext, S.ga_draw(np.random.default_rng(seed), Pn))
        n256 = min(256 // Pn, 8) if not SMOKE else 1
        shapes = {"validation_32x256": (pop, smoke[:len(ids("validation"))], CHUNK),
                  "census_256x16": (Genome.cat([pop] * n256), smoke[:len(ids("census"))], 256),
                  "single_1x1024": (base, smoke[:len(ids("gates"))], 1),
                  "assay_1x256": (base, smoke[:len(ids("assays"))], 1)}
        for k, (g, w, ch) in shapes.items():
            t = twice(lambda g=g, w=w, ch=ch: play(cfg, iface, g, w, dev, ctx.cap, ch, category="calibration", seed=seed))
            timing[k] = {**t, "episodes": int(g.n_strains * len(w)), "rate": g.n_strains * len(w) / t["seconds"],
                         "composition": [ch, len(w), 1]}
        g_dev = EV.moved(base, dev)
        pcd = P.ProbeContext(ext, iface, cfg, device=dev)
        cal_pop = EV.moved(Genome.cat([base] * (CHUNK if not SMOKE else 2)), dev)
        with acct.category("probe"):
            timing["component_tests"] = twice(lambda: P.component_tests(g_dev, pcd, states={"A": O.Q_STAR, "B": -O.Q_STAR}))
            timing["memory_assays"] = twice(lambda: AS.memory_assays(g_dev, pcd, w_qq=2.0, b_q=0.0, tau_q=1.0, stim=2, D=40,
                                                                     assignment=None))
            timing["hysteresis"] = twice(lambda: AS.hysteresis(g_dev, pcd, w_qq=2.0, b_q=0.0))
        with acct.category("calibration"):
            timing["calibration_32x256"] = twice(lambda: AS.calibrate(cal_pop, ext, iface, cfg, world_ids=smoke[:len(ids("calibration"))],
                                                                       run_seed=seed, device=dev))
            timing["traces_32x16"] = twice(lambda: AS.traces(cal_pop, ext, iface, cfg, world_ids=smoke[:REGISTERED["trace_worlds"]],
                                                             run_seed=seed, device=dev))
        sec = lambda k: timing[k]["seconds"]  # noqa: E731
        r1, r32, r256, ra = (timing[k]["rate"] for k in ("single_1x1024", "validation_32x256", "census_256x16", "assay_1x256"))
        H = 3600.0
        G_ = REGISTERED["generations"]
        n_ckpt = lambda g: len([x for x in range(g) if x % REGISTERED["checkpoint_every"] == 0 or x == g - 1])  # noqa: E731
        batch = lambda g: (g * per + n_ckpt(g) * timing["training"]["seconds_per_checkpoint"]) / H  # noqa: E731
        nv, nt, na, ng = (len(ids(k)) for k in ("validation", "calibration", "assays", "gates"))
        unit = {
            "ga_batch": batch(G_["ga"]), "rs_batch": G_["rs"] * per / H, "stage3_batch": batch(G_["stage3"]),
            "btask_per_generation": batch(G_["btask"]) / G_["btask"],
            "validation_per_run": Pn * nv / r32 / H,
            "calibration_per_organism": sec("calibration_32x256") / CHUNK / H,
            "scoring_per_organism": nt / r32 / H,
            "evaluation_per_organism": (nt / r32 + 2 * na / ra + 2 * sec("memory_assays") + sec("hysteresis")
                                        + 2 * nt / r1) / H,
            "evaluation_fixed": (7 * nt / r1 + sec("component_tests") + sec("memory_assays")
                                 + 2 * sec("traces_32x16") + 0.1 * H) / H,
        }
        fixed = (7 * ng / r1 + 3 * ng / r1 + sec("component_tests") + sec("memory_assays") + 3 * na / ra  # G0, G1
                 + sec("calibration_32x256") / CHUNK                                                 # calibrate-e
                 + 2 * REGISTERED["census"]["draws"] * len(ids("census")) / r256 + 16 / r1          # census
                 + 0.1 * H) / H                                                                       # G-E's CPU leg
        proj = {"unit": unit, "fixed": fixed}
        p = reductions(proj, spent_hours())
        return {"timing": timing, "projected_hours": proj, "plan": p,
                "stage_hours_at_plan": stage_hours(proj, p, 2 * REGISTERED["census"]["projected_qualifiers"]),
                "seeds": {"projection": seed}, "note": "timings only, on smoke ids and the smoke seed; no score is read"}
    return E.run_stage(args, "project", lambda a, prov: {}, body)


# ============================================================================== G-E, G0, G1

def cmd_ge(args):
    def body(ctx):
        dev = ctx.args.device
        ref_path = ROOT / EQ_REFERENCE
        ref = json.loads(ref_path.read_text(encoding="utf-8"))
        with acct.category("calibration"):
            new = EQ.run(ROOT, Path(ROOT / "data" / "cache" / "cook2019_herm.npz"))
        cpu = EQ.compare(ref, new)
        cpu["reference_sha256"] = E.sha256_bytes(ref_path)
        cpu["engines"] = {"reference": ref.get("engine"), "compared": new["engine"]}
        gpu = {"skipped": "smoke"}
        if not SMOKE:
            E2 = _load("e2_pristine_for_e3a_ge", "e2.py")
            cfg2 = E2.task_config()
            con = load_connectome()
            from wormwars.interface import load_interface
            iface2, spec2 = load_interface(con), BrainSpec.from_connectome(con)
            committed = json.loads((ROOT / "experiments" / "E2-optimizer-screen" / "train-ga.json").read_text(encoding="utf-8"))
            runs = [EV.RunSpec(**r["spec"]) for r in committed["records"]]
            want = [[g["best_sha256"] for g in r["log"][:26]] for r in committed["records"]]
            idsd = E2.REGISTERED["ids"]["train"]
            recs = EV.evolve_batch(cfg2, iface2, spec2, runs, generations=26, checkpoint_every=E2.REGISTERED["checkpoint_every"],
                                   validation_ids=E2.validation_ids(), world_seed=E2.REGISTERED["world_seed"],
                                   id_base=idsd["base"], id_span=idsd["span"], device=dev, check=ctx.cap.check,
                                   category=acct.category)
            got = [[g["best_sha256"] for g in r.log] for r in recs]
            gpu = {"all_match": got == want, "matching_generations_per_run": [sum(a == b for a, b in zip(x, y)) for x, y in zip(got, want)],
                   "composition": [len(runs) * cfg2.evo.population, cfg2.evo.worlds_per_strain, 1]}
        passed = cpu["passed"] and gpu.get("all_match", True)
        return {"passed": bool(passed), "cpu": cpu, "gpu": gpu}
    return E.run_stage(args, "g-e", lambda a, prov: require_fits(a, prov), body)


def cmd_g0(args):
    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg, dev)
        w = ids("gates")
        ext_s, iface_s = cx["ext"]["l1_switch"], cx["iface"]["l1_switch"]
        n = ext_s.n
        sc = REGISTERED["scripted"]
        runs = {
            "oracle": play_brain(cfg, iface_s, K.oracle(iface_s, cfg, n, device=dev), w, dev, ctx.cap, "calibration")[0],
            "s_8192": play_brain(cfg, iface_s, K.s_shuttle(iface_s, cfg, n, device=dev, **sc["s_shuttle_k8192"]), w, dev, ctx.cap,
                                 "calibration")[0],
            "s_32": play_brain(cfg, iface_s, K.s_shuttle(iface_s, cfg, n, device=dev, **sc["s_shuttle_k32"]), w, dev, ctx.cap,
                               "calibration")[0],
            "l1_switch": play(cfg, iface_s, cx["genomes"]["l1_switch"], w, dev, ctx.cap, 1, "calibration")[0],
            "constant": play_brain(cfg, iface_s, K.constant(iface_s, cfg, n, device=dev), w, dev, ctx.cap, "calibration")[0],
            "random-walk": play_brain(cfg, iface_s, K.random_walk(iface_s, cfg, n, device=dev), w, dev, ctx.cap, "calibration")[0],
            "circle": play(cfg, cx["iface"]["carrier"], cx["genomes"]["carrier"], w, dev, ctx.cap, 1, "calibration")[0],
        }
        geo = geometry(cfg, cx, w, dev)
        ref = RD.straight_run_reference(geo["spawn"], geo["a"], geo["b"])
        res = RD.g0(oracle=runs["oracle"], reference=ref, s_8192=runs["s_8192"], s_32=runs["s_32"], l1_switch=runs["l1_switch"],
                    blind={k: runs[k] for k in ("constant", "random-walk", "circle")}, world_ci=D2.world_ci)
        save_npz("g0-counts", {**runs, "reference": ref})
        return {"passed": bool(res["passed"] or SMOKE), "reading": res, "worlds": [int(w[0]), len(w)],
                "composition": [1, len(w), 1]}
    return E.run_stage(args, "g0", lambda a, prov: (require_fits(a, prov), require_passed(a, prov, "g-e")), body)


def geometry(cfg, cx, world_ids, device) -> dict:
    """Each world's spawn and sources, from a world built and not run."""
    from wormwars.brain import Brain
    from wormwars.world import World
    w = np.asarray(world_ids)
    world = World(cfg, cx["iface"]["carrier"], Brain(EV.moved(cx["genomes"]["carrier"], device)),
                  torch.zeros(len(w), 1, dtype=torch.long, device=device), run_seed=world_seed(), world_ids=w, device=device)
    return {"spawn": world.pos[:, 0, 0].cpu().numpy(), "a": world.shuttle_sources[:, 0].cpu().numpy(),
            "b": world.shuttle_sources[:, 1].cpu().numpy()}


def cmd_g1(args):
    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg, dev)
        w = ids("gates")
        iface, ext = cx["iface"]["E"], cx["ext"]["E"]
        sc = {k: play(cfg, iface, cx["genomes"][k], w, dev, ctx.cap, 1, "measure")[0] for k in ("E", "no_latch", "one_module")}
        l1_switch = np.load(E.EXP / "g0-counts.npz", allow_pickle=False)["l1_switch"]
        g = EV.moved(cx["genomes"]["E"], dev)
        pc = P.ProbeContext(ext, iface, cfg, device=dev)
        e_states = {"A": O.Q_STAR, "B": -O.Q_STAR}
        with acct.category("probe"):
            comp = P.component_tests(g, pc, states=e_states)
            mem = AS.memory_assays(g, pc, w_qq=2.0, b_q=0.0, tau_q=1.0, stim=REGISTERED["e_stimulus"], D=40,
                                   assignment=e_states)
        with acct.category("measure"):
            clamp = AS.clamp_assays(g, ext, iface, cfg, states=(-O.Q_STAR, O.Q_STAR), world_ids=ids("assays"),
                                    run_seed=world_seed(), device=dev)
            reset = AS.reset_test(g, ext, iface, cfg, go_to_a=O.Q_STAR, world_ids=ids("assays"), run_seed=world_seed(),
                                  device=dev)
        e_assign_ok = clamp.get("assignment") == e_states
        assays = {"clamp": bool(clamp["passed"] and e_assign_ok), "settable": bool(mem["settable"]),
                  "hold": bool(mem["hold"]), "reset": bool(reset["passed"])}
        res = RD.g1(e=sc["E"], l1_switch=l1_switch, no_latch=sc["no_latch"], one_module=sc["one_module"],
                    component=comp["passed"], assays=assays, world_ci=D2.world_ci, classify=D2.classify)
        save_npz("g1-counts", sc)
        mem.pop("release_detail", None)
        mem.pop("release", None)
        return {"passed": bool(res["passed"] or SMOKE), "reading": res, "component_tests": comp, "memory": mem,
                "clamp": clamp, "reset": reset, "composition": [1, len(w), 1],
                "note": "E's release test needs D: calibrate-e reports it"}
    return E.run_stage(args, "g1", lambda a, prov: (require_fits(a, prov), require_passed(a, prov, "g-e", "g0")), body)


# ============================================================================== calibration of E, the censuses

def cmd_calibrate_e(args):
    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg, dev)
        ext, iface = cx["ext"]["E"], cx["iface"]["E"]
        g = EV.moved(cx["genomes"]["E"], dev)
        ctx.cap.check()
        with acct.category("measure"):
            cal = AS.calibrate(g, ext, iface, cfg, world_ids=ids("calibration"), run_seed=world_seed(), device=dev)[0]
        D = AS.leg_median(cal["legs_after_first_visit"])
        pc = P.ProbeContext(ext, iface, cfg, device=dev)
        with acct.category("probe"):
            rel = {f"from {k}": AS._release(g, pc, q, REGISTERED["e_stimulus"], D) for k, q in (("A", O.Q_STAR), ("B", -O.Q_STAR))}
        return {"D": D, "e_measured_stimulus": cal["stimulus"], "e_stimulus_used": REGISTERED["e_stimulus"],
                "median_q": cal["median_q"], "level_pool": cal["pool"], "visits": cal["visits"],
                "e_release_reported": rel, "composition": [1, len(ids("calibration")), 1]}
    return E.run_stage(args, "calibrate-e", lambda a, prov: require_gates(a, prov), body)


def qualifier_file(key: str) -> Path:
    return E.OUT / "genomes" / f"census-{key}-checked.npz"


def cmd_census(args):
    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg, dev)
        ext, iface, base = cx["ext"]["E"], cx["iface"]["E"], cx["genomes"]["E"]
        w = ids("census")
        Cn = REGISTERED["census"]
        n = Cn["draws"]
        e_scores = play(cfg, iface, base, w, dev, ctx.cap, 1, "measure")[0]
        e_mean = float(e_scores.mean())
        out, counts = {"e_census_mean": e_mean}, {"E": e_scores}
        for key, draw, seed in (("ga", S.ga_draw, REGISTERED["seeds"]["census_ga"]), ("rs", S.rs_draw, REGISTERED["seeds"]["census_rs"])):
            params = draw(np.random.default_rng(seed), n)
            pop = S.with_selector(base, ext, params)
            sc = play(cfg, iface, pop, w, dev, ctx.cap, min(256, n), "measure")
            means = sc.mean(axis=1)
            qual = [int(k) for k in np.flatnonzero(means >= Cn["screen"] * e_mean)]
            checked = sorted(qual, key=lambda k: (-means[k], k))[:Cn["cap"]]
            if checked:
                chk = pop.select(checked)
                path = qualifier_file(key)
                path.parent.mkdir(parents=True, exist_ok=True)
                save_population(path, chk, cfg=cfg, stage="census")
                hashes = [genome_hash(chk, k) for k in range(chk.n_strains)]
            else:
                hashes = []
            g0 = generation0_offsets(cfg, cx, pop.select(list(range(min(64, n)))), dev) if key == "ga" else None
            out[key] = {"draws": n, "seed": seed, "qualifiers": len(qual), "checked": checked, "checked_sha256": hashes,
                        "unchecked": max(0, len(qual) - Cn["cap"]), "checked_selectors": params[checked].tolist(),
                        "screen_means": {str(k): float(means[k]) for k in qual}, "generation0_first64": g0}
            counts[f"{key}_means"] = means
        save_npz("census-counts", counts)
        return {**out, "composition": [min(256, n), len(w), 1]}
    return E.run_stage(args, "census", lambda a, prov: (require_gates(a, prov), E.require_earlier(a, prov, "calibrate-e")), body)


def generation0_offsets(cfg, cx, genomes: Genome, dev) -> dict:
    """Turn offsets (u − the carrier's 0.2 at zero nose difference, q free from 0 with no levels, after 60
    ticks) and A's K_D (q held at 0), per strain; descriptive (§6)."""
    ext, iface = cx["ext"]["E"], cx["iface"]["E"]
    g = EV.moved(genomes, dev)
    pc = P.ProbeContext(ext, iface, cfg, device=dev)
    with acct.category("probe"):
        st = pc.latch_state(g, 0.0)
        u = P._free_run(g, pc, st, 60, None, 0)[-1]
        off = (pc.turn(u) - REGISTERED["carrier"]["turn"]).tolist()
        kd = P.k_d(g, pc, "A", 0.05, st).tolist()
    return {"turn_offset": off, "K_D_A_at_q0": kd}


# ============================================================================== training

def training_closed() -> bool:
    return E.marker_path("calibrate").exists() or E.record_path("calibrate").exists()


def census_checked() -> int:
    path = E.record_path("census")
    if not path.exists():
        return 2 * REGISTERED["census"]["projected_qualifiers"]
    rec = json.loads(path.read_text(encoding="utf-8"))
    return len(rec["ga"]["checked"]) + len(rec["rs"]["checked"])


def remaining_hours(b: int, p: dict, proj: dict) -> float:
    """The non-training stages still to run after batch b, at the plan's counts and the census's actual
    number of checked qualifiers (§5, §9)."""
    sh = stage_hours(proj, p, census_checked())
    later = ["champions-3", "calibrate", "evaluate"] + (["champions-2"] if b <= 2 else [])
    return sum(sh[k] for k in later)


def batch_hours(arm: str, p: dict, proj: dict) -> float:
    h = proj["unit"]
    if arm == "ga":
        return h["ga_batch"]
    if arm == "rs":
        return h["rs_batch"] * p["rs_runs"] / n_runs()
    if arm == "stage3":
        return h["stage3_batch"] * p["stage3_runs"] / n_runs()
    return h["btask_per_generation"] * p["btask_generations"]


def cmd_train(args):
    b = int(args.batch)
    stage = f"train-{b}"
    arm = BATCHES[b - 1]
    loaded = {}

    def requires(a, prov):
        require_gates(a, prov)
        require(a, prov, "calibrate-e", "census")
        if training_closed():
            raise SystemExit("calibration has started: training is closed")
        for k in range(1, b):
            if require_batch(a, prov, k)["state"] == "refused":
                raise SystemExit(f"train-{k} was refused: no later batch starts (§9)")
        if b >= 3:
            loaded["champions2"] = E.require_earlier(a, prov, "champions-2")
        project = E.require_earlier(a, prov, "project")
        p = project["plan"]
        loaded["plan"] = p
        need = batch_hours(arm, p, project["projected_hours"]) + REGISTERED["reserve_factor"] * remaining_hours(
            b, p, project["projected_hours"])
        spent = spent_hours()
        if not SMOKE and spent + need > REGISTERED["admit_hours"]:
            E.write_atomic(E.EXP / f"{stage}-refused.json", {"stage": stage, "spent_hours": spent, "needed_hours": need,
                                                              "admit_hours": REGISTERED["admit_hours"], "provenance": prov,
                                                              "decision": "not admitted (§9); no later batch starts"})
            raise SystemExit(f"{stage} not admitted: {spent:.2f} h spent + {need:.2f} h exceeds {REGISTERED['admit_hours']} h")
        return p

    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg, dev)
        p = loaded["plan"]
        runs = {"ga": list(range(n_runs())), "rs": list(range(p["rs_runs"])), "stage3": list(range(p["stage3_runs"])),
                "btask": list(range(n_runs())) if p["btask_generations"] else []}[arm]
        if SMOKE:
            runs = runs[:2]
        if arm == "stage3":  # only the runs whose Stage 2 champion exists
            have = {c["run"] for c in loaded["champions2"].get("ga", {}).get("champions", [])}
            missing = [i for i in runs if i not in have]
            runs = [i for i in runs if i in have]
        else:
            missing = []
        if not runs:
            return {"arm": arm, "skipped": True, "runs": [], "not_run": missing,
                    "reason": "removed by the projection's reductions (§9)" if not missing else "no Stage 2 champion"}
        if arm == "rs":
            return train_rs(ctx, cx, runs)
        return {**train_ga(ctx, cx, arm, runs, p, stage, loaded.get("champions2")), "not_run": missing}

    return E.run_stage(args, stage, requires, body)


def train_ga(ctx, cx, arm: str, runs_i: list[int], p: dict, stage: str, champions2: dict | None = None) -> dict:
    cfg, dev = ctx.cfg.copy(), ctx.args.device
    key = "b_task" if arm == "btask" else "E"
    ext, iface, spec = cx["ext"][key], cx["iface"][key], cx["spec"][key]
    gens = {"ga": REGISTERED["generations"]["ga"], "stage3": REGISTERED["generations"]["stage3"],
            "btask": p["btask_generations"]}[arm]
    if SMOKE:
        gens = 3
    cfg.evo.generations = gens
    Pn = cfg.evo.population
    base, span = train_span()
    runs = [EV.RunSpec(i, run_seed(arm, i), 0.0) for i in runs_i]
    champs = {}
    if arm == "stage3":
        for c in champions2["ga"]["champions"]:
            g = load_genomes("ga", c["run"], "champion", cx["spec"]["E"], ctx.cfg)
            if genome_hash(g, 0) != c["sha256"]:
                raise SystemExit(f"Stage 2 run {c['run']}'s champion does not match its record")
            champs[c["run"]] = g

    def initial(r):
        if arm == "ga":
            return S.with_selector(cx["genomes"]["E"], ext, S.ga_draw(np.random.default_rng(REGISTERED["seeds"]["ga_init"] + r.run), Pn))
        if arm == "stage3":
            return Genome.cat([champs[r.run]] * Pn)
        return S.b_task_draw(np.random.default_rng(REGISTERED["seeds"]["btask_init"] + r.run), ext, cx["mods"]["b_task"], cfg.brain, Pn)

    scales = {"ga": S.stage2_scales, "stage3": S.stage3_scales, "btask": S.b_task_scales}[arm](ext)
    records = []

    def partial(recs, g):
        records[:] = recs
        E.write_atomic(E.partial_path(stage), {**ctx.doc, "generation": g, "records": [E.run_record(r) for r in recs]})

    ctx.salvage = lambda: {"records": [E.run_record(r) for r in records]}
    recs = EV.evolve_batch(cfg, iface, spec, runs, generations=gens, checkpoint_every=REGISTERED["checkpoint_every"],
                           validation_ids=ids("validation"), world_seed=world_seed(), id_base=base, id_span=span, device=dev,
                           check=ctx.cap.check, category=acct.category, on_checkpoint=partial, initial=initial,
                           mutation_scales=lambda r: scales)
    bad = {}
    for rec in recs:
        for kind, pop in (("candidates", Genome.cat(rec.candidates)), ("final", rec.final)):
            path = genomes_file(arm, rec.spec.run, kind)
            path.parent.mkdir(parents=True, exist_ok=True)
            save_population(path, pop, cfg=cfg, run=rec.spec.run, run_seed=rec.spec.run_seed, stage=stage)
        problems = assertions(arm, [rec.final, *rec.candidates], cx)
        if problems:
            bad[str(rec.spec.run)] = problems
    return {"arm": arm, "generations": gens, "runs": [r.spec.run for r in recs], "assertions_failed": bad or None,
            "records": [E.run_record(r) for r in recs],
            "composition": {"training": [len(recs) * Pn, cfg.evo.worlds_per_strain, 1], "validation": [len(recs), len(ids("validation")), 1]},
            "genome_files": "local (rule 1): runs/e3a/genomes/"}


def assertions(arm: str, pops: list[Genome], cx) -> list[str]:
    """§7's end-of-run assertions: the mask unchanged in every arm; in Stage 2 and random sampling every
    non-selector parameter is E's; in Stage 3 the relays' τ and bias, the 302 worm neurons, the worm's
    edges and the conductances are E's; in B-task the relays' τ and bias, the worm block and the
    conductances are the carrier's."""
    key = "b_task" if arm == "btask" else "E"
    ext = cx["ext"][key]
    spec = cx["spec"][key]
    ref = cx["genomes"]["E"] if key == "E" else C.carrier_genome(ext, cx["mods"]["b_task"], pops[0].cfg,
                                                                 forward=REGISTERED["carrier"]["forward"],
                                                                 turn=REGISTERED["carrier"]["turn"])
    bad = []
    n0 = int(ext.meta["worm_neurons"])
    same = lambda a, b: torch.equal(a, b.expand(a.shape[0], -1))  # noqa: E731
    for pop in pops:
        if not (torch.equal(pop.spec.chem_i, spec.chem_i) and torch.equal(pop.spec.chem_j, spec.chem_j)
                and torch.equal(pop.spec.gap_i, spec.gap_i) and torch.equal(pop.spec.gap_j, spec.gap_j)):
            bad.append("the mask changed")
            break
        if arm in ("ga", "rs"):
            m = S.selector_masks(ext)
            if not (same(pop.w[:, ~m["w"]], ref.w[:, ~m["w"]]) and same(pop.tau[:, ~m["tau"]], ref.tau[:, ~m["tau"]])
                    and same(pop.bias[:, ~m["bias"]], ref.bias[:, ~m["bias"]]) and same(pop.g, ref.g)):
                bad.append("a non-selector parameter changed")
                break
        else:
            keep = torch.zeros(ext.n, dtype=torch.bool)
            keep[:n0] = True
            for r in O.RELAYS:
                keep[ext.index(r)] = True
            worm_edges = (spec.chem_i < n0) & (spec.chem_j < n0)
            if not (same(pop.tau[:, keep], ref.tau[:, keep]) and same(pop.bias[:, keep], ref.bias[:, keep])
                    and same(pop.w[:, worm_edges], ref.w[:, worm_edges]) and same(pop.g, ref.g)):
                bad.append("a fixed parameter changed (relays, worm block or conductances)")
                break
    return bad


def train_rs(ctx, cx, runs_i: list[int]) -> dict:
    """Random sampling (§7): draw j of run i is scored on GA run i's selection worlds of generation
    ⌊j / 32⌋; the top 32 by that score (ties to the lower j) go to validation (champions-2)."""
    cfg, dev = ctx.cfg, ctx.args.device
    ext, iface, base = cx["ext"]["E"], cx["iface"]["E"], cx["genomes"]["E"]
    Pn, W = cfg.evo.population, cfg.evo.worlds_per_strain
    gens = REGISTERED["generations"]["rs"] if not SMOKE else 3
    b0, span = train_span()
    params = {i: S.rs_draw(np.random.default_rng(REGISTERED["seeds"]["rs"] + i), Pn * gens) for i in runs_i}
    scores = {i: np.zeros(Pn * gens) for i in runs_i}
    for g in range(gens):
        pops, wids = [], []
        for i in runs_i:
            pops.append(S.with_selector(base, ext, params[i][g * Pn:(g + 1) * Pn]))
            wids.append(np.tile(EV.train_ids(run_seed("ga", i), g, W, b0, span), (Pn, 1)))
        sc = play(cfg, iface, Genome.cat(pops), np.concatenate(wids), dev, ctx.cap, len(runs_i) * Pn, "selection")
        for k, i in enumerate(runs_i):
            scores[i][g * Pn:(g + 1) * Pn] = sc[k * Pn:(k + 1) * Pn].mean(axis=1)
    top, bad = {}, {}
    for i in runs_i:
        order = sorted(range(len(scores[i])), key=lambda j: (-scores[i][j], j))[:Pn]
        top[i] = order
        pop = S.with_selector(base, ext, params[i][order])
        save_population(genomes_file("rs", i, "top32"), pop, cfg=cfg, run=i, run_seed=run_seed("ga", i), stage="train-2")
        problems = assertions("rs", [pop], cx)
        if problems:
            bad[str(i)] = problems
    save_npz("train-2-scores", {f"run{i:02d}": scores[i] for i in runs_i})
    return {"arm": "rs", "runs": list(runs_i), "draws_per_run": Pn * gens, "assertions_failed": bad or None,
            "top32": {str(i): [{"j": int(j), "selection_mean": float(scores[i][j]), "selector": params[i][j].tolist()}
                               for j in top[i]] for i in runs_i},
            "top32_sha256": {str(i): [genome_hash(S.with_selector(base, ext, params[i][[j]]), 0) for j in top[i]]
                             for i in runs_i},
            "composition": {"selection": [len(runs_i) * Pn, W, 1]}}


def load_genomes(arm: str, i: int, kind: str, spec, cfg) -> Genome:
    g, _ = load_population(genomes_file(arm, i, kind), spec, cfg.brain)
    return g


# ============================================================================== champions

def champion_of(means: np.ndarray, keys=None) -> int:
    """The best validation mean; ties to the lower key (the index, or random sampling's draw j)."""
    best = float(np.max(means))
    keys = list(range(len(means))) if keys is None else list(keys)
    return int(min((keys[k], k) for k, m in enumerate(means) if m == best)[1])


def cmd_champions(args, which: int):
    stage = f"champions-{which}"
    arms = ["ga", "rs"] if which == 2 else ["stage3", "btask"]
    first_batch = 1 if which == 2 else 3

    def requires(a, prov):
        require_gates(a, prov)
        return {arm: require_batch(a, prov, k) for k, arm in zip((first_batch, first_batch + 1), arms)}

    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg, dev)
        res = {}
        for arm in arms:
            rec = ctx.earlier[arm]
            if rec["state"] in ("refused", "skipped", "final-stopped"):
                res[arm] = {"not_read": rec["state"], "champions": []}
                continue
            if rec.get("assertions_failed"):  # §7: a failure makes that batch "not read"
                res[arm] = {"not_read": "end-of-run assertions failed", "assertions_failed": rec["assertions_failed"],
                            "champions": []}
                continue
            key = "b_task" if arm == "btask" else "E"
            champs = []
            for i in rec["runs"]:
                kind = "top32" if arm == "rs" else "final"
                pop = load_genomes(arm, i, kind, cx["spec"][key], cfg)
                want = (rec["top32_sha256"][str(i)] if arm == "rs"
                        else next(r["final_sha256"] for r in rec["records"] if r["spec"]["run"] == i))
                if [genome_hash(pop, k) for k in range(pop.n_strains)] != want:
                    raise SystemExit(f"{arm} run {i}'s genomes do not match their record")
                sc = play(cfg, cx["iface"][key], pop, ids("validation"), dev, ctx.cap, CHUNK, "holdout")
                means = sc.mean(axis=1)
                js = [t["j"] for t in rec["top32"][str(i)]] if arm == "rs" else None
                k = champion_of(means, js)
                ch = pop.select([k])
                entry = {"run": i, "index": k, "sha256": genome_hash(ch, 0), "validation_mean": float(means[k]),
                         "validation_means": [float(m) for m in means]}
                if arm == "rs":
                    entry["j"] = js[k]
                if arm in ("ga", "rs"):
                    entry["selector"] = selector_doc(ch, cx["ext"]["E"])[0]
                else:
                    entry["grafted"] = grafted_doc(ch, cx["ext"][key])
                save_population(genomes_file(arm, i, "champion"), ch, cfg=cfg, run=i, stage=stage)
                champs.append(entry)
            res[arm] = {"champions": champs}
        return {**res, "composition": {"validation": [CHUNK, len(ids("validation")), 1]}}

    return E.run_stage(args, stage, requires, body)


# ============================================================================== calibration of champions and qualifiers

def organisms(earlier: dict, cx, cfg) -> list[dict]:
    """Every organism that gets calibration and the memory assays: Stage 2's, random sampling's and
    Stage 3's champions, and the census qualifiers that were checked, each verified against its record."""
    out = []
    ch2, ch3, census = earlier["champions-2"], earlier["champions-3"], earlier["census"]
    for arm, rec in (("ga", ch2.get("ga", {})), ("rs", ch2.get("rs", {})), ("stage3", ch3.get("stage3", {}))):
        for c in rec.get("champions", []):
            g = load_genomes(arm, c["run"], "champion", cx["spec"]["E"], cfg)
            if genome_hash(g, 0) != c["sha256"]:
                raise SystemExit(f"{arm} run {c['run']}'s champion does not match its record")
            out.append({"arm": arm, "run": c["run"], "genome": g})
    for key in ("ga", "rs"):
        if not census[key]["checked"]:
            continue
        g, _ = load_population(qualifier_file(key), cx["spec"]["E"], cfg.brain)
        if [genome_hash(g, k) for k in range(g.n_strains)] != census[key]["checked_sha256"]:
            raise SystemExit(f"the census's {key} qualifiers do not match their record")
        for k, idx in enumerate(census[key]["checked"]):
            out.append({"arm": f"census-{key}", "run": int(idx), "genome": g.select([k])})
    return out


def cmd_calibrate(args):
    def requires(a, prov):
        require_gates(a, prov)
        recs = require(a, prov, "calibrate-e", "census", "champions-2", "champions-3")
        project = E.require_earlier(a, prov, "project")
        sh = stage_hours(project["projected_hours"], project["plan"], census_checked())
        if not SMOKE and spent_hours() + sh["calibrate"] + sh["evaluate"] > REGISTERED["cap_gpu_hours"]:
            raise SystemExit("calibration and evaluation are not admitted: they would exceed the cap (§9)")
        return recs

    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg, dev)
        ext, iface = cx["ext"]["E"], cx["iface"]["E"]
        orgs = organisms(ctx.earlier, cx, cfg)
        out = []
        for lo in range(0, len(orgs), CHUNK):
            chunk = orgs[lo:lo + CHUNK]
            ctx.cap.check()
            with acct.category("measure"):
                cal = AS.calibrate(EV.moved(Genome.cat([o["genome"] for o in chunk]), dev), ext, iface, cfg,
                                   world_ids=ids("calibration"), run_seed=world_seed(), device=dev)
            for o, c in zip(chunk, cal):
                out.append({"arm": o["arm"], "run": o["run"], "stimulus": c["stimulus"], "pool": c["pool"],
                            "median_q": c["median_q"], "visits": c["visits"]})
        return {"organisms": out, "composition": [CHUNK, len(ids("calibration")), 1]}
    return E.run_stage(args, "calibrate", requires, body)


# ============================================================================== evaluation

def cmd_evaluate(args):
    def requires(a, prov):
        require_gates(a, prov)
        recs = require(a, prov, "calibrate-e", "census", "champions-2", "champions-3", "calibrate")
        project = E.require_earlier(a, prov, "project")
        sh = stage_hours(project["projected_hours"], project["plan"], census_checked())
        if not SMOKE and spent_hours() + sh["evaluate"] > REGISTERED["cap_gpu_hours"]:
            raise SystemExit("the evaluation is not admitted: it would exceed the cap (§9)")
        recs["plan"] = project["plan"]
        return recs

    def body(ctx):
        global TEST_OPEN
        TEST_OPEN = True
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg, dev)
        ext, iface = cx["ext"]["E"], cx["iface"]["E"]
        test = ids("test")
        D = ctx.earlier["calibrate-e"]["D"]
        cal = {(c["arm"], c["run"]): c for c in ctx.earlier["calibrate"]["organisms"]}
        orgs = organisms(ctx.earlier, cx, cfg)
        q_index = ext.index(O.Q)
        # every single-strain organism on E's mask, scored together (§5's composition): E, its controls,
        # the q-zero ablation, then the champions and qualifiers (the registered ones first)
        order = sorted(orgs, key=lambda o: o["arm"] == "stage3")
        named = [("E", cx["genomes"]["E"]), ("no_latch", cx["genomes"]["no_latch"]),
                 ("one_module", cx["genomes"]["one_module"]), ("q_zero", cx["genomes"]["E"])]
        genomes = [g for _, g in named] + [o["genome"] for o in order]
        scores = score_many(cfg, iface, genomes, test, dev, ctx.cap, hooks={3: {q_index: 0.0}})
        counts = {name: scores[k] for k, (name, _) in enumerate(named)}
        e_mean = float(counts["E"].mean())
        pc = P.ProbeContext(ext, iface, cfg, device=dev)
        evals = {}
        for k, o in enumerate(order):
            sc = scores[len(named) + k]
            counts[f"{o['arm']}-{o['run']}"] = sc
            evals[(o["arm"], o["run"])] = evaluate_organism(o, sc, cal[(o["arm"], o["run"])], cfg, cx, pc, D, e_mean, dev, ctx.cap)
        champ = [o for o in order if o["arm"] in ("ga", "rs", "stage3")]
        for key in ("A", "B"):  # the mean-nose probes, E's and every champion's
            sc = score_many(cfg, cx["iface"][f"E_mean_{key}"], [cx["genomes"]["E"]] + [o["genome"] for o in champ], test,
                            dev, ctx.cap)
            counts[f"E_mean_{key}"] = sc[0]
            for o, s in zip(champ, sc[1:]):
                evals[(o["arm"], o["run"])]["mean_nose"][key] = float(s.mean())
        btask = {}
        bt = ctx.earlier["champions-3"].get("btask", {}).get("champions", [])
        if bt:
            gs = []
            for c in bt:
                g = load_genomes("btask", c["run"], "champion", cx["spec"]["b_task"], cfg)
                if genome_hash(g, 0) != c["sha256"]:
                    raise SystemExit(f"B-task run {c['run']}'s champion does not match its record")
                gs.append(g)
            for c, s in zip(bt, score_many(cfg, cx["iface"]["b_task"], gs, test, dev, ctx.cap)):
                counts[f"btask-{c['run']}"] = s
                btask[c["run"]] = float(s.mean())
        counts["b_shared"] = play(cfg, cx["iface"]["b_shared"], cx["genomes"]["b_shared"], test, dev, ctx.cap, 1)[0]
        counts["l1_switch"] = play(cfg, cx["iface"]["l1_switch"], cx["genomes"]["l1_switch"], test, dev, ctx.cap, 1)[0]
        desc = {"E": {"mean": e_mean, **{k: D2.world_ci(counts["E"], counts[k]) for k in ("no_latch", "one_module", "q_zero",
                                                                                           "E_mean_A", "E_mean_B")}},
                "b_shared_mean": float(counts["b_shared"].mean()), "l1_switch_mean": float(counts["l1_switch"].mean())}
        pcb = P.ProbeContext(cx["ext"]["b_shared"], cx["iface"]["b_shared"], cfg, device=dev)
        gb = EV.moved(cx["genomes"]["b_shared"], dev)
        with acct.category("probe"):
            desc["b_shared_component_tests"] = P.component_tests(gb, pcb, states={"A": O.Q_STAR, "B": -O.Q_STAR})
            desc["b_shared_memory"] = strip(AS.memory_assays(gb, pcb, w_qq=2.0, b_q=0.0, tau_q=1.0, stim=REGISTERED["e_stimulus"],
                                                             D=D, assignment={"A": O.Q_STAR, "B": -O.Q_STAR}))
        desc["checkpoint_offsets"] = checkpoint_offsets(ctx.earlier, cx, cfg, dev)
        # the per-tick logs, on the first test worlds: E and every champion
        tr_orgs = [cx["genomes"]["E"]] + [o["genome"] for o in champ]
        tr = {}
        for lo in range(0, len(tr_orgs), CHUNK):
            ctx.cap.check()
            with acct.category("measure"):
                t = AS.traces(EV.moved(Genome.cat(tr_orgs[lo:lo + CHUNK]), dev), ext, iface, cfg,
                              world_ids=test[:REGISTERED["trace_worlds"]], run_seed=world_seed(), device=dev)
            for k, v in t.items():
                tr.setdefault(k, []).append(v)
        traces = {k: np.concatenate(v) for k, v in tr.items()}
        traces["organisms"] = np.array(["E"] + [f"{o['arm']}-{o['run']}" for o in champ])
        readings = read(ctx.earlier, evals, btask)
        save_npz("evaluate-counts", counts)
        save_npz("evaluate-traces", traces)
        return {"organisms": [{"arm": a, "run": r, **v} for (a, r), v in evals.items()], "btask_means": btask,
                "descriptive": desc, "readings": readings, "D": D, "e_test_mean": e_mean,
                "composition": {"scores": [CHUNK, len(test), 1], "assays": [1, len(ids("assays")), 1],
                                "traces": [CHUNK, REGISTERED["trace_worlds"], 1]}}
    return E.run_stage(args, "evaluate", requires, body)


def checkpoint_offsets(earlier: dict, cx, cfg, dev) -> dict:
    """Each Stage 2 run's checkpoint candidates' turn offsets (the logged generations; descriptive)."""
    out = {}
    rec = earlier.get("champions-2", {})
    for c in rec.get("ga", {}).get("champions", []):
        cands = load_genomes("ga", c["run"], "candidates", cx["spec"]["E"], cfg)
        out[str(c["run"])] = generation0_offsets(cfg, cx, cands, dev)["turn_offset"]
    return out


def evaluate_organism(o, sc, cal, cfg, cx, pc, D, e_mean, dev, cap) -> dict:
    ext, iface = cx["ext"]["E"], cx["iface"]["E"]
    g = EV.moved(o["genome"], dev)
    lo = D2.world_ci(sc, np.zeros_like(sc))["lo95"]
    sel = S.read_selector(o["genome"], ext)[0]
    w_qq, b_q, tau_q = (float(sel[S.SELECTOR_INDEX[k]]) for k in ("w_qq", "b_q", "tau_q"))
    st = L.structure(w_qq, b_q)
    if st.kind == "bistable":
        states, applicable = st.states, True
    else:
        mq = cal["median_q"]
        applicable = mq["A"] is not None and mq["B"] is not None
        states = (min(mq["A"], mq["B"]), max(mq["A"], mq["B"])) if applicable else (0.0, 0.0)
    cap.check()
    with acct.category("measure"):
        clamp = AS.clamp_assays(g, ext, iface, cfg, states=states, world_ids=ids("assays"), run_seed=world_seed(),
                                device=dev, applicable=applicable)
    asg = clamp.get("assignment") if clamp.get("applicable") else None
    with acct.category("probe"):
        mem = AS.memory_assays(g, pc, w_qq=w_qq, b_q=b_q, tau_q=tau_q, stim=cal["stimulus"], D=D, assignment=asg)
        two = AS.memory_assays(g, pc, w_qq=w_qq, b_q=b_q, tau_q=tau_q, stim=2, D=D, assignment=asg) if cal["stimulus"] != 2 else None
        hyst = AS.hysteresis(g, pc, w_qq=w_qq, b_q=b_q)
        skill = {}
        if asg and o["arm"] in ("ga", "stage3"):
            for goal in ("A", "B"):
                skill[goal] = {"first_entry_share": clamp["share"][goal],
                               "K_D_at_state": float(P.k_d(g, pc, goal, 0.05, pc.latch_state(g, asg[goal])))}
    working = AS.working(lower_bound=lo, e_mean=e_mean, clamp=clamp)
    return {"test_mean": float(sc.mean()), "test_lower_bound": lo, "selector": sel.tolist(), "structure": st.kind,
            "clamp": {k: v for k, v in clamp.items() if k != "first_entries"}, "memory": strip(mem),
            "two_tick": strip(two) if two else "the organism's own stimulus is 2 ticks", "class": mem["class"],
            "working": working, "hysteresis": hyst, "module_skill": skill, "mean_nose": {}}


def strip(m: dict) -> dict:
    return json.loads(json.dumps(m, default=float))


def read(earlier: dict, evals: dict, btask: dict) -> dict:
    """§8's readings."""
    runs = range(n_runs())
    ga = {r: evals.get(("ga", r)) for r in runs}
    rs = {r: evals.get(("rs", r)) for r in runs}
    st3 = {r: evals.get(("stage3", r)) for r in runs}
    s2a = RD.s2a([None if ga[r] is None else ga[r]["working"] for r in runs])
    s2a["classes"] = {str(r): (ga[r]["class"] if ga[r] else None) for r in runs}
    pairs = [r for r in runs if ga[r] and rs[r]]
    if any(batch_state(f"train-{k}") == "final-stopped" for k in (1, 2)):
        s2b = {"label": "not read", "reason": "batch 1 or 2 stopped finally"}
    elif pairs:
        s2b = RD.s2b([ga[r]["test_mean"] - rs[r]["test_mean"] for r in pairs], [ga[r]["working"] for r in pairs],
                     [rs[r]["working"] for r in pairs], boot=D2._boot_means,
                     ga_all=[v["working"] for v in ga.values() if v], rs_all=[v["working"] for v in rs.values() if v])
    else:
        s2b = {"label": "not read", "pairs": 0}
    s2c = {}
    census = earlier["census"]
    for key in ("ga", "rs"):
        checked = [evals.get((f"census-{key}", int(idx))) for idx in census[key]["checked"]]
        count = sum(bool(c and c["working"]) for c in checked)
        s2c[key] = RD.s2c(count, census[key]["draws"], unchecked=census[key]["unchecked"], ga_distribution=(key == "ga"))
    p3 = [r for r in runs if st3[r] and ga[r]]
    stage3 = (RD.compare([st3[r]["test_mean"] - ga[r]["test_mean"] for r in p3], boot=D2._boot_means,
                         a_working=[st3[r]["working"] for r in p3], b_working=[ga[r]["working"] for r in p3])
              if p3 else {"label": "not read"})
    stage3["wording"] = "joint tuning"
    reduced = "B-task, to 300 generations" in earlier["plan"]["steps"]
    bt_ref = ga if reduced else st3
    pb = [r for r in runs if r in btask and bt_ref.get(r)]
    bt = RD.compare([btask[r] - bt_ref[r]["test_mean"] for r in pb], boot=D2._boot_means) if pb else {"label": "not read"}
    bt["against"] = "Stage 2 (reduction step 1)" if reduced else "Stage 3"
    bt["wording"] = "the same neurons, inputs and outputs, not the same trainable capacity"
    return {"S2-a": s2a, "S2-b": s2b, "S2-c": s2c, "stage3": stage3, "btask": bt}


# ============================================================================== smoke and main

def use_smoke(args) -> None:
    global EXP, OUT, SMOKE, GUARDED
    EXP = OUT = ROOT / "runs" / "e3a-smoke"
    SMOKE = True
    GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PREREG, *E.E1_INPUTS]
    R = REGISTERED
    R["ga"].update(generations=3, population=4, elites=1, truncation=2, worlds_per_strain=2)
    R["generations"] = {"ga": 3, "rs": 3, "stage3": 3, "btask": 3}
    R["runs"] = 2
    R["checkpoint_every"] = 2
    R["trace_worlds"] = 2
    R["census"].update(draws=8, cap=2, projected_qualifiers=2)
    for k in R["ids"]:
        if "worlds" in R["ids"][k]:
            R["ids"][k]["worlds"] = 4 if k != "gates" else 8
    configure()
    stage = args.command if args.command != "train" else f"train-{args.batch}"
    for s in STAGES[STAGES.index(stage):]:
        for f in (E.record_path(s), E.marker_path(s), E.partial_path(s)):
            if EXP in f.parents:
                f.unlink(missing_ok=True)


COMMANDS = {"project": cmd_project, "g-e": cmd_ge, "g0": cmd_g0, "g1": cmd_g1, "calibrate-e": cmd_calibrate_e,
            "census": cmd_census, "train": cmd_train, "champions-2": lambda a: cmd_champions(a, 2),
            "champions-3": lambda a: cmd_champions(a, 3), "calibrate": cmd_calibrate, "evaluate": cmd_evaluate}


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=list(COMMANDS))
    ap.add_argument("--batch", type=int, choices=range(1, 5))
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--guarded", action="store_true")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--reason")
    args = ap.parse_args()
    if args.command == "train" and not args.batch:
        ap.error("train needs --batch 1-4")
    if args.smoke:
        use_smoke(args)
    COMMANDS[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    out = ROOT / "runs" / ("e3a-smoke" if smoke else "e3a")
    try:
        run_script(main, out_default=str(out), default="measure", name="e3a")
    finally:
        agg = out / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
