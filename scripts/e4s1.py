"""E4s-1: the comparator graft under evolution (confirmatory; experiments/E4s-stereo-module/E4s-1/
PREREGISTRATION.md, bound at 023267d, D150).

    python scripts/e4s1.py project | gate-1 | gate-2 | gate-3 | r-draws | train --batch B | eval-endpoints | eval-training
    add --smoke for toy sizes in runs/e4s1-smoke (never results)

Every stage runs once, inside E2's stage frame (this script's own copy), and its record is committed and
pushed before the next stage starts. A gate that completes and fails is final; E4s-1 then stops. The cap is
24 GPU-hours, counted through `wormwars.accounting`; training batches are admitted one by one (§8).
Per-world counts go to compressed .npz files beside each record (committed); genomes stay local (rule 1).
"""

from __future__ import annotations

import argparse
import copy
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
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.e4s import comparator as C  # noqa: E402
from wormwars.e4s import diagnostics as DG  # noqa: E402
from wormwars.evo.genomes import genome_hash, load_population, save_population  # noqa: E402
from wormwars.evo.rollout import rollout as _rollout  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


E = _load("e2_for_e4s1", "e2.py")
D2 = _load("e2d_for_e4s1", "e2d.py")

EXP = ROOT / "experiments" / "E4s-stereo-module" / "E4s-1"
OUT = ROOT / "runs" / "e4s1"
PREREG = "experiments/E4s-stereo-module/E4s-1/PREREGISTRATION.md"
SOURCES = "experiments/E4s-stereo-module/E4s-1/development-records/source-genomes.json"
SOURCES_SHA256 = "dbd09d0db196e8ff1170fcb8be42f18f795457f5554887b9df39bf263207e2c6"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PREREG, SOURCES,
           "experiments/E4s-stereo-module/E4s-0/module.json", *E.E1_INPUTS, *D2.SOURCE_RECORDS]
SMOKE = False

BATCHES = [("M", list(range(0, 8))), ("N", list(range(0, 8))), ("R", list(range(0, 8))),
           ("M", list(range(8, 16))), ("N", list(range(8, 16))), ("R", list(range(8, 16))),
           ("F0", list(range(8))), ("U", list(range(8))), ("S", list(range(8))), ("C2", list(range(8)))]
TRAIN_STAGES = [f"train-{b}" for b in range(1, len(BATCHES) + 1)]
STAGES = ["project", "gate-1", "gate-2", "gate-3", "r-draws", *TRAIN_STAGES, "eval-endpoints", "eval-training"]

REGISTERED = {
    "world_seed": E.REGISTERED["world_seed"], "task_sigma": E.REGISTERED["task_sigma"],
    "ga": copy.deepcopy(E.REGISTERED["ga"]), "checkpoint_every": 25, "rerun_kill_tail_seconds": 900,
    "cap_gpu_hours": 24.0, "admit_hours": 22.5, "reserve_factor": 1.25,
    "seeds": {"run": 1_160_000, "c2": 1_166_000, "r": A.R_SEED_BASE, "g2_genomes": 1_167_000, "g2_inputs": 1_168_000,
              "projection": 1_169_000},
    "ids": {"train": {"base": 942_000_000, "span": 500_000}, "validation": {"first": 942_600_000, "worlds": 256},
            "holdout": {"first": 942_700_000, "worlds": 1024}, "gate1": {"first": 942_800_000, "worlds": 1024},
            "along": {"first": 942_900_000, "worlds": 256}, "finalpop": {"first": 942_910_000, "worlds": 256},
            "g0pop": {"first": 942_920_000, "worlds": 256}, "gate3": {"first": 942_950_000, "worlds": 256}},
    "gate1": {"lower_bound": 5.0}, "gate2": {"ticks": 300, "high": 0.35, "tolerance": 1e-4, "genomes": 48},
    "gate3": {"tolerance": 0.05},
    "along_generations": [0, 100, 250, 500, 750, 999],
    "open_loop": {"levels": [0.02, 0.08, 0.25], "d": 0.001, "dm": 0.01, "ticks": 40, "average": 10},
    "carrier": {"forward": 1.0, "turns": [0.2, -0.2]},
    "batches": [[a, r] for a, r in BATCHES],
}
RECORD = {s: s for s in STAGES}
WHAT = {s: f"E4s-1's {s}" for s in STAGES}


def configure() -> None:
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, OUT, GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E4s-1: not completed (the run stopped)",
                  "cap": "E4s-1: not completed (the cap was reached)"}
    E.RECORD.update(RECORD)
    E.WHAT.update(WHAT)


configure()


# ============================================================================== ids, seeds, modules

def ids(key: str) -> np.ndarray:
    v = REGISTERED["ids"][key]
    if SMOKE:
        offsets = {"validation": 1000, "holdout": 2000, "gate1": 3000, "along": 4000, "finalpop": 5000,
                   "g0pop": 6000, "gate3": 7000}
        return E.SMOKE_IDS[offsets[key]:offsets[key] + v["worlds"]]
    return np.arange(v["first"], v["first"] + v["worlds"])


def formal_ranges() -> dict:
    out = {}
    for k, v in REGISTERED["ids"].items():
        out[k] = (v["base"], v["base"] + v["span"]) if "base" in v else (v["first"], v["first"] + v["worlds"])
    return out


def run_seed(arm: str, i: int) -> int:
    return (REGISTERED["seeds"]["c2"] if arm == "C2" else REGISTERED["seeds"]["run"]) + int(i)


def arm_module(arm: str, i: int, l1: G.Module) -> G.Module:
    if arm == "N":
        return A.without_output(l1)
    if arm == "R":
        return A.with_signs(l1, A.r_signs(i))
    return l1


def context(cfg):
    """The connectome, the grafted connectome (one mask for every arm), its spec and interfaces."""
    con = load_connectome()
    l1 = A.load_l1()
    ext = G.graft_connectome(con, l1)
    return {"con": con, "l1": l1, "ext": ext, "spec": BrainSpec.from_connectome(ext),
            "iface": {p: G.graft_interface(ext, l1, probe=p) for p in ("real", "mean", "swapped")},
            "n2_iface": load_interface(con), "n2_spec": BrainSpec.from_connectome(con)}


def sources(cfg) -> dict:
    """The named source genomes, each checked against `source-genomes.json` (whose own hash is bound)."""
    text = (ROOT / SOURCES).read_bytes().decode("utf-8").replace("\r\n", "\n")
    if hashlib.sha256(text.encode()).hexdigest() != SOURCES_SHA256:
        raise SystemExit("source-genomes.json does not match its bound sha256")
    want = json.loads(text)
    spec = BrainSpec.from_connectome(load_connectome())
    out = {}
    e04a = D2.e04a_champions(spec, cfg)
    for lab, v in want["e04a"].items():
        g, sha = e04a[lab][:2]
        if sha != v["sha256"]:
            raise SystemExit(f"{lab} does not match source-genomes.json")
        out[lab] = g
    e2 = D2.e2_champions(spec, cfg)
    for lab, v in want["e2_ga"].items():
        g, sha = e2[lab]
        if sha != v["sha256"]:
            raise SystemExit(f"{lab} does not match source-genomes.json")
        out[lab] = g
    return out


def initial(arm: str, i: int, ctx_, cfg, size: int, c2_base=None) -> Genome:
    """Run i's generation 0 for an arm (§4)."""
    con, ext, l1 = ctx_["con"], ctx_["ext"], ctx_["l1"]
    mod = arm_module(arm, i, l1)
    if arm == "C2":
        one = G.seeded_genome(ext, mod, cfg.brain, base=c2_base)
        return one.select([0] * size)
    return C.embedded_population(con, ext, mod, cfg.brain, run_seed=run_seed(arm, i), population=size)


# ============================================================================== rollouts and probes

CONDITIONS = {1: ("real", "real"), 2: ("mean", "real"), 3: ("swapped", "real"), 4: ("mean", "mean"),
              5: ("mean", "swapped")}  # (the module's interface, the world's food probe), §5


def finite(a, what: str):
    a = np.asarray(a)
    if not np.isfinite(a).all():
        raise FloatingPointError(f"{what} is not finite: the stage stops")
    return a


def finite_max(values, what: str) -> float:
    v = np.asarray(list(values), dtype=np.float64)
    finite(v, what)
    return float(v.max()) if v.size else 0.0


def g2_coverage(n: int) -> dict:
    """G2's schedule (§3): every genome in every shape."""
    S_tr = 256 if not SMOKE else 4
    return {"training": [[k % n for k in range(S_tr)]],
            "validation": [list(range(j, min(j + 8, n))) for j in range(0, n, 8)],
            "evaluation_1x1024": [[k] for k in range(n)], "probe_1x256": [[k] for k in range(n)]}


def r_draws_doc() -> dict:
    draws = {str(i): A.r_signs(i).tolist() for i in range(16)}
    return {"signs": draws, "sha256": hashlib.sha256(json.dumps(draws, sort_keys=True).encode()).hexdigest(),
            "rule": "default_rng(1 165 000 + i).choice([-1, 1], size=20); edge k's weight s_k x 3.0"}


def module_parameters(genome: Genome, ext, module: G.Module) -> dict:
    """The genome's module, by name: its edges in `module.json`'s order, and its neurons' tau and bias."""
    W, _ = genome.dense()
    return {"edges": [{"edge": f"{a}->{b}", "weight": float(W[0, ext.index(a), ext.index(b)])}
                      for a, b, _ in module.synapses],
            "tau": {n: float(genome.tau[0, ext.index(n)]) for n in module.neurons},
            "bias": {n: float(genome.bias[0, ext.index(n)]) for n in module.neurons}}


def evaluated_batches(states: list[str]) -> list[int]:
    """Which training batches the evaluation covers (§8, Amendment 1.4). Completed batches are covered and
    finally stopped ones named; after a refusal nothing may have started; a killed attempt, a first stop
    awaiting its rerun, or a gap refuses the evaluation."""
    out, ended = [], False
    for b, s in enumerate(states):
        if s in ("killed", "awaiting-rerun"):
            raise SystemExit(f"batch {b + 1} is {s}: settle it (rerun) before the evaluation")
        if ended and s != "absent":
            raise SystemExit(f"batch {b + 1} is {s} after the training ended: the batches run in order")
        if s == "completed":
            out.append(b)
        elif s in ("refused", "absent"):
            ended = True
        elif s != "final-stopped":
            raise SystemExit(f"batch {b + 1} has an unknown state {s!r}")
    return out


def play(cfg, iface, genome: Genome, world_ids, device, cap, chunk_strains: int, probe: str = "real",
         brain_hook=None, category: str = "final") -> np.ndarray:
    c = cfg.copy()
    c.world.food_probe = probe
    w = np.asarray(world_ids)
    cap.check()
    with acct.category(category):
        r = _rollout(c, iface, EV.moved(genome, device), w, REGISTERED["world_seed"], device,
                     chunk_worlds=chunk_strains * w.shape[-1], brain_hook=brain_hook)
    return finite(r.score, "a score")


def module_indices(ext) -> list[int]:
    n0 = int(ext.meta["worm_neurons"])
    return list(range(n0, ext.n))


def open_loop(genome: Genome, ext, iface, cfg, device) -> dict:
    """u(m, 0), signed K_D and K_C at the registered levels, and the forward command (zero start, 40 ticks,
    the mean of the last 10; L = m + d/2, R = m - d/2 at every food sensor, the noses included)."""
    O = REGISTERED["open_loop"]
    names = list(iface.signal_names)
    left = [int(iface.sensor_neuron[i]) for i, s in enumerate(names) if s == "food_left"]
    right = [int(iface.sensor_neuron[i]) for i, s in enumerate(names) if s == "food_right"]
    brain = Brain(EV.moved(genome, device))
    S, n = genome.n_strains, ext.n

    def run(m, d):
        cur = torch.zeros(S, 1, n, device=device)
        cur[..., left], cur[..., right] = m + d / 2, m - d / 2
        v, turns, fwds = brain.initial_state(1), [], []
        for _ in range(O["ticks"]):
            v = brain.step(v, cur)
            f, t = C.motor_commands(v.cpu(), iface, cfg)
            turns.append(t.reshape(S))
            fwds.append(f.reshape(S))
        k = O["average"]
        return torch.stack(turns[-k:]).mean(0).numpy(), torch.stack(fwds[-k:]).mean(0).numpy()

    out = {}
    with acct.category("probe"):
        for m in O["levels"]:
            u0, f0 = run(m, 0.0)
            finite(u0, "the open loop")
            up, _ = run(m, O["d"])
            un, _ = run(m, -O["d"])
            cp, _ = run(m + O["dm"], 0.0)
            cn, _ = run(m - O["dm"], 0.0)
            out[str(m)] = {"u": u0.tolist(), "forward": f0.tolist(), "K_D": ((up - un) / (2 * O["d"])).tolist(),
                           "K_C": ((cp - cn) / (2 * O["dm"])).tolist()}
    return out


def classes(c: dict, base: int, mean: int, swapped: int) -> dict:
    """E2d's class of base against two conditions, with the signed contrasts."""
    a, b = D2.world_ci(c[base], c[mean]), D2.world_ci(c[base], c[swapped])
    return {"class": D2.classify(a, b), "contrast_mean": a, "contrast_swapped": b}


def endpoint(genome: Genome, arm: str, i: int, which: str, ctx_, cfg, device, cap, l1) -> tuple[dict, dict]:
    """The hold-out conditions of §5 for one genome; returns (summary, per-world counts by condition)."""
    ext, I = ctx_["ext"], ctx_["iface"]
    hold = ids("holdout")
    counts, motors = {}, {}

    def cond(k, motor=False):
        iface_key, probe = CONDITIONS[k]
        if motor:
            with DG.motor_stats() as st:
                counts[k] = play(cfg, I[iface_key], genome, hold, device, cap, 1, probe=probe)[0]
            motors[k] = {q: finite(v[0], "a motor measure") for q, v in st.per_strain(1, len(hold)).items()}
        else:
            counts[k] = play(cfg, I[iface_key], genome, hold, device, cap, 1, probe=probe)[0]

    cond(1, motor=True)
    cond(2)
    cond(4, motor=True)
    cond(5)
    out = {"score": float(counts[1].mean()), "H": classes(counts, 2, 4, 5),
           "closed_loop_real": {k: float(v.mean()) for k, v in motors[1].items()},
           "closed_loop_no_cue": {k: float(v.mean()) for k, v in motors[4].items()},
           "open_loop": open_loop(genome, ext, I["real"], cfg, device),
           "composition": [1, len(hold), 1]}
    if arm != "N":
        out["module_parameters"] = module_parameters(genome, ext, l1)
        cond(3)
        out["D"] = classes(counts, 1, 2, 3)
        mc = {}
        for turn, base in zip(REGISTERED["carrier"]["turns"], (6, 9)):
            g = A.mc_genome(genome, ext, l1, cfg.brain, turn=turn, forward=REGISTERED["carrier"]["forward"])
            counts[base] = play(cfg, I["real"], g, hold, device, cap, 1)[0]
            counts[base + 1] = play(cfg, I["mean"], g, hold, device, cap, 1)[0]
            counts[base + 2] = play(cfg, I["swapped"], g, hold, device, cap, 1)[0]
            mc[str(turn)] = {**classes(counts, base, base + 1, base + 2), "score": float(counts[base].mean())}
        out["Mc"] = {"holds": any(v["class"] == "uses" for v in mc.values()), "per_turn": mc}
        if which != "G0":
            idx = module_indices(ext)
            counts[12] = play(cfg, I["real"], genome, hold, device, cap, 1,
                              brain_hook=lambda b, lo, hi: b.silence([idx] * (hi - lo)))[0]
            counts[13] = play(cfg, I["real"], A.module_replaced(genome, ext, arm_module(arm, i, l1), cfg.brain),
                              hold, device, cap, 1)[0]
            counts[14] = play(cfg, I["real"], A.module_replaced(genome, ext, l1, cfg.brain), hold, device, cap, 1)[0]
            out.update(lesion_cost=float(counts[1].mean() - counts[12].mean()), reset=float(counts[13].mean()),
                       rescue=float(counts[14].mean()))
    per_world_motor = {f"motor{k}_{q}": v.astype(np.float32) for k, m in motors.items() for q, v in m.items()}
    return out, {**counts, **per_world_motor}


# ============================================================================== guards

def require_gates(args, prov) -> None:
    for g in ("gate-1", "gate-2", "gate-3"):
        rec = E.require_earlier(args, prov, g)
        if not rec.get("passed"):
            raise SystemExit(f"{g} completed and failed: E4s-1 stops (only a dated, reviewed amendment goes on)")


def projection(args, prov) -> dict:
    p = E.require_earlier(args, prov, "project")
    return p


def refused_path(stage: str) -> Path:
    return E.EXP / f"{stage}-refused.json"


def batch_state(stage: str) -> str:
    """completed, final-stopped, awaiting-rerun, refused, killed or absent (Amendment 1.4)."""
    path = E.record_path(stage)
    if path.exists():
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("outcome") == "completed":
            return "completed"
        if rec.get("outcome") == E.OUTCOMES["cap"] or rec.get("final"):
            return "final-stopped"
        return "awaiting-rerun"
    if refused_path(stage).exists():
        return "refused"
    if E.marker_path(stage).exists():
        return "killed"
    return "absent"


def training_closed() -> bool:
    return E.marker_path("eval-endpoints").exists() or E.record_path("eval-endpoints").exists()


def spent_hours() -> float:
    return E.clock().spent_hours()


# ============================================================================== the projection

def cmd_project(args):
    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg)
        smoke = E.SMOKE_IDS
        seed = REGISTERED["seeds"]["projection"]
        P = REGISTERED["ga"]["population"] if not SMOKE else 4
        timing = {}

        def timed(fn):
            t0 = time.perf_counter()
            fn()
            if dev != "cpu":
                torch.cuda.synchronize()
            return time.perf_counter() - t0

        # training: a few generations of a batch of 8 runs on smoke ids (E2d's projection)
        n_gen = 6 if not SMOKE else 3
        runs = [EV.RunSpec(k, seed + k, 0.0) for k in range(8 if not SMOKE else 2)]
        recs = EV.evolve_batch(cfg, cx["iface"]["real"], cx["spec"], runs, generations=n_gen, checkpoint_every=n_gen - 1,
                               validation_ids=smoke[5000:5000 + (256 if not SMOKE else 4)], world_seed=REGISTERED["world_seed"],
                               id_base=0, id_span=5000, device=dev, check=ctx.cap.check, category=acct.category,
                               initial=lambda r: C.embedded_population(cx["con"], cx["ext"], cx["l1"], cfg.brain,
                                                                      run_seed=r.run_seed, population=P),
                               mutation_scales=lambda r: A.arm_scales(cx["ext"], cx["l1"], "M"))
        s = [x["batch_seconds"] for x in recs[0].log]
        per = float(np.median(s[1:-1])) if len(s) > 2 else float(s[-1])
        timing["training"] = {"seconds_per_generation": per, "seconds_per_checkpoint": max(0.0, float(s[-1]) - per),
                              "batch_seconds": s}
        g1 = C.embedded_population(cx["con"], cx["ext"], cx["l1"], cfg.brain, run_seed=seed + 50, population=32)
        shapes = {"eval_1x1024": (g1.select([0]), smoke[:1024 if not SMOKE else 8], 1, False),
                  "eval_1x1024_instrumented": (g1.select([0]), smoke[:1024 if not SMOKE else 8], 1, True),
                  "probe_1x256": (g1.select([0]), smoke[:256 if not SMOKE else 8], 1, True),
                  "along_8x256": (g1.select(list(range(8))), smoke[:256 if not SMOKE else 8], 8, False),
                  "pop_32x256": (g1, smoke[:256 if not SMOKE else 8], 32, False)}
        for k, (g, w, ch, inst) in shapes.items():
            def run(g=g, w=w, ch=ch, inst=inst):
                if inst:
                    with DG.motor_stats():
                        play(cfg, cx["iface"]["real"], g, w, dev, ctx.cap, ch, category="calibration")
                else:
                    play(cfg, cx["iface"]["real"], g, w, dev, ctx.cap, ch, category="calibration")
            first, second = timed(run), timed(run)  # the second timing is used (Amendment 1.2)
            timing[k] = {"episodes": int(g.n_strains * len(w)), "seconds_first": first, "seconds": second,
                         "rate": g.n_strains * len(w) / second, "composition": [ch, len(w), 1], "instrumented": inst}
        first = timed(lambda: open_loop(g1.select([0]), cx["ext"], cx["iface"]["real"], cfg, dev))
        timing["open_loop_per_genome"] = timed(lambda: open_loop(g1.select([0]), cx["ext"], cx["iface"]["real"], cfg, dev))
        timing["open_loop_first"] = first
        G_ = REGISTERED["ga"]["generations"] if not SMOKE else 3
        n_ckpt = len([g for g in range(G_) if g % REGISTERED["checkpoint_every"] == 0 or g == G_ - 1])
        batch_h = (G_ * per + n_ckpt * timing["training"]["seconds_per_checkpoint"]) / 3600
        r1, r1i, r8, r32 = (timing[k]["rate"] for k in ("eval_1x1024", "eval_1x1024_instrumented", "along_8x256",
                                                           "pop_32x256"))
        ol = timing["open_loop_per_genome"]
        n_runs_non_n, n_runs_n = 64, 16
        # per genome, 2 instrumented conditions (1 and 4) and the rest plain; references: 2 turns x 3 + 1
        endpoints = (n_runs_non_n * 3 * 2 * 1024 / r1i + n_runs_non_n * (12 + 12 + 9) * 1024 / r1
                     + n_runs_n * 3 * 2 * 1024 / r1i + n_runs_n * 3 * 2 * 1024 / r1 + 7 * 1024 / r1
                     + (n_runs_non_n + n_runs_n) * 3 * ol + 16 * ol
                     + 32 * 32 * 3 * 256 / r32) / 3600  # the G0 population counts run in this stage
        along = (80 * 6 * 3 * 256 / r8 + 80 * 6 * ol / 8 + 16 * 32 * 2 * 256 / r32) / 3600
        hours = {"batch": batch_h, "eval-endpoints": endpoints, "eval-training": along}
        reserve = REGISTERED["reserve_factor"] * (endpoints + along)
        return {"timing": timing, "projected_hours": hours, "evaluation_reserve_hours": reserve,
                "projected_total_hours": 10 * batch_h + endpoints + along,
                "within_cap": spent_hours() + 10 * batch_h + reserve <= REGISTERED["cap_gpu_hours"],
                "seeds": {"projection": seed}, "note": "timings only, on smoke ids; no score is read"}
    return E.run_stage(args, "project", lambda a, prov: {}, body)


# ============================================================================== the gates

def cmd_gate1(args):
    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg)
        l1, ext = cx["l1"], cx["ext"]
        g = C.carrier_genome(ext, l1, cfg.brain, forward=REGISTERED["carrier"]["forward"], turn=0.2)
        w = ids("gate1")
        c = {k: play(cfg, cx["iface"][CONDITIONS[k][0]], g, w, dev, ctx.cap, 1)[0] for k in (1, 2, 3)}
        lower = D2.world_ci(c[1], np.zeros_like(c[1]))
        cls = classes(c, 1, 2, 3)
        bound = REGISTERED["gate1"]["lower_bound"] if not SMOKE else -1.0
        passed = lower["lo95"] >= bound and (cls["class"] == "uses" or SMOKE)
        np.savez_compressed(EXP / "gate-1-counts.npz", **{str(k): v for k, v in c.items()})
        return {"passed": bool(passed), "mean": lower, "uses": cls, "worlds": [int(w[0]), len(w)],
                "composition": [1, len(w), 1]}
    return E.run_stage(args, "gate-1", lambda a, prov: projection(a, prov), body)


def g2_current(iface, values: np.ndarray, n: int, bcfg, device) -> torch.Tensor:
    """The interface's injection of signal values (World._build_current, one world)."""
    names = list(iface.signal_names)
    order = list(dict.fromkeys(names))
    cur = torch.zeros(n, device=device)
    for k, (s, neuron, gain) in enumerate(zip(names, iface.sensor_neuron, iface.sensor_gain)):
        cur[int(neuron)] += float(values[order.index(s)]) * float(gain) * bcfg.input_gain
    return cur.clamp(-bcfg.input_max, bcfg.input_max)


def g2_inputs(iface) -> tuple[list[str], np.ndarray]:
    order = list(dict.fromkeys(iface.signal_names))
    T = REGISTERED["gate2"]["ticks"] if not SMOKE else 5
    return order, np.random.default_rng(REGISTERED["seeds"]["g2_inputs"]).uniform(0, REGISTERED["gate2"]["high"],
                                                                                  size=(T, len(order)))


def cmd_gate2(args):
    loaded = {}

    def requires(a, prov):
        p = projection(a, prov)
        if not E.require_earlier(a, prov, "gate-1").get("passed"):
            raise SystemExit("gate-1 failed: E4s-1 stops")
        loaded["src"] = sources(E.task_config())  # before the marker: a missing file spends no rerun
        return p

    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg)
        con, ext, l1 = cx["con"], cx["ext"], cx["l1"]
        nmod = A.without_output(l1)
        src = loaded["src"]
        champs = [src[k] for k in sorted(k for k in src if k.startswith("04a"))]
        n_rand = 32 if not SMOKE else 2
        base = Genome.cat([EV.initial_population(cx["n2_spec"], cfg.brain, REGISTERED["seeds"]["g2_genomes"], n_rand, "cpu"),
                           *champs[:(16 if not SMOKE else 1)]])
        grafted = G.seeded_genome(ext, nmod, cfg.brain, base=base)
        order, X = g2_inputs(cx["n2_iface"])
        cur_n2 = torch.stack([g2_current(cx["n2_iface"], x, con.n, cfg.brain, dev) for x in X])
        cur_ext = torch.stack([g2_current(cx["iface"]["real"], x, ext.n, cfg.brain, dev) for x in X])
        nG = base.n_strains
        worst, per_shape = 0.0, {}

        def compare(idx: list[int], rows: int) -> float:
            ctx.cap.check()
            b0, b1 = Brain(EV.moved(base.select(idx), dev)), Brain(EV.moved(grafted.select(idx), dev))
            v0, v1, w = b0.initial_state(rows), b1.initial_state(rows), []
            for t in range(len(X)):
                c0 = cur_n2[t].expand(len(idx), rows, con.n)
                c1 = cur_ext[t].expand(len(idx), rows, ext.n)
                v0, v1 = b0.step(v0, c0), b1.step(v1, c1)
                w.append(float((v0 - v1[..., :con.n]).abs().max()))  # NaN propagates; checked below
            return finite_max(w, "G2's state difference")

        rows = {"training": 8, "validation": 256, "evaluation_1x1024": 1024, "probe_1x256": 256}
        if SMOKE:
            rows = {k: (2 if k == "training" else 4) for k in rows}
        cov = g2_coverage(nG)
        with acct.category("calibration"):
            for shape, batches in cov.items():
                per_shape[shape] = finite_max([compare(idx, rows[shape]) for idx in batches], "G2's state difference")
        worst = finite_max(per_shape.values(), "G2's state difference")
        tol = REGISTERED["gate2"]["tolerance"]
        return {"passed": bool(worst <= tol), "max_abs_difference": worst, "per_shape": per_shape, "tolerance": tol,
                "coverage": {k: len(v) for k, v in cov.items()},
                "compositions": {k: [len(v[0]), rows[k]] for k, v in cov.items()},
                "genomes": {"random_n2": n_rand, "04a_champions": len(champs[:(16 if not SMOKE else 1)])},
                "signals": order, "input_sha256": hashlib.sha256(X.tobytes()).hexdigest()}
    return E.run_stage(args, "gate-2", requires, body)


def cmd_gate3(args):
    loaded = {}

    def requires(a, prov):
        p = projection(a, prov)
        for g in ("gate-1", "gate-2"):
            if not E.require_earlier(a, prov, g).get("passed"):
                raise SystemExit(f"{g} failed: E4s-1 stops")
        loaded["src"] = sources(E.task_config())
        return p

    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg)
        nmod = A.without_output(cx["l1"])
        src = loaded["src"]
        labels = sorted(src) if not SMOKE else sorted(src)[:2]
        w = ids("gate3")
        per, counts, ok = {}, {}, True
        for lab in labels:
            g = src[lab]
            a = play(cfg, cx["n2_iface"], g, w, dev, ctx.cap, 1)[0]
            b = play(cfg, cx["iface"]["real"], G.seeded_genome(cx["ext"], nmod, cfg.brain, base=g), w, dev, ctx.cap, 1)[0]
            counts[f"{lab} ungrafted"], counts[f"{lab} N"] = a, b
            diff = abs(float(a.mean()) - float(b.mean()))
            per[lab] = {"ungrafted": float(a.mean()), "N": float(b.mean()), "difference": diff,
                        "identical_worlds": float((a == b).mean())}
            ok = ok and diff <= REGISTERED["gate3"]["tolerance"]
        np.savez_compressed(EXP / "gate-3-counts.npz", **counts)
        return {"passed": bool(ok), "per_genome": per, "composition": [1, len(w), 1], "tolerance": REGISTERED["gate3"]["tolerance"]}
    return E.run_stage(args, "gate-3", requires, body)


def cmd_rdraws(args):
    def requires(a, prov):
        p = projection(a, prov)
        require_gates(a, prov)
        return p

    def body(ctx):
        return r_draws_doc()
    return E.run_stage(args, "r-draws", requires, body)


# ============================================================================== training

def genomes_file(arm: str, i: int, kind: str) -> Path:
    return E.OUT / "genomes" / f"{arm}-run{i:02d}-{kind}.npz"


def check_assertions(arm: str, rec, ext, l1) -> list[str]:
    """§4's end-of-run assertions, on every candidate and the final population."""
    bad = []
    pops = [rec.final, *rec.candidates]
    if arm == "N":
        out = A.output_edge_mask(ext, l1)
        if any(float(p.w[:, out].abs().max()) != 0.0 for p in pops):
            bad.append("N's output edges are not all 0")
    if arm == "F0":
        ref = G.seeded_genome(ext, l1, rec.final.cfg, n_strains=1)
        _, _, me, _, mn = A._masks(ext)
        for p in pops:
            if not (torch.equal(p.w[:, me], ref.w[:, me].expand_as(p.w[:, me]))
                    and torch.equal(p.tau[:, mn], ref.tau[:, mn].expand_as(p.tau[:, mn]))
                    and torch.equal(p.bias[:, mn], ref.bias[:, mn].expand_as(p.bias[:, mn]))):
                bad.append("F0's module is not bit-identical to L1")
                break
    return bad


def mutation_counts(ext, l1, arm: str, cfg) -> dict:
    """With p_mutate 1, each child mutates every parameter with a non-zero factor: the per-generation counts
    are the children times each block's non-zero parameters."""
    s = A.arm_scales(ext, l1, arm)
    children = cfg.evo.population - cfg.evo.elites
    out_mask = A.output_edge_mask(ext, l1)
    _, _, me, _, mn = A._masks(ext)
    nz = lambda t: int((t != 0).sum())  # noqa: E731
    return {"children_per_generation": children, "p_mutate": cfg.mutation.p_mutate,
            "host": children * (nz(s["w"][~me]) + nz(s["g"]) + nz(s["tau"][~mn]) + nz(s["bias"][~mn])),
            "module_non_output": children * (nz(s["w"][me & ~out_mask]) + nz(s["tau"][mn]) + nz(s["bias"][mn])),
            "output_edges": children * nz(s["w"][out_mask])}


def cmd_train(args):
    b = int(args.batch)
    stage = f"train-{b}"
    arm, runs_i = BATCHES[b - 1]
    loaded = {}

    def requires(a, prov):
        p = projection(a, prov)
        require_gates(a, prov)
        E.require_earlier(a, prov, "r-draws")
        if training_closed():
            raise SystemExit("the evaluation has started: training is closed")
        for k in range(1, b):
            st = batch_state(f"train-{k}")
            if st == "completed":
                rec = E.require_earlier(a, prov, f"train-{k}")
                if rec.get("assertions_failed"):
                    raise SystemExit(f"train-{k}'s end-of-run assertions failed: E4s-1 stops")
            elif st != "final-stopped":  # Amendment 1.4: later batches run after a final stop
                raise SystemExit(f"train-{k} is {st}: batches run in order, and none after a refusal")
        spent = spent_hours()
        need = p["projected_hours"]["batch"] + p["evaluation_reserve_hours"]
        if not SMOKE and spent + need > REGISTERED["admit_hours"]:  # smoke prices formal work at toy rates
            E.write_atomic(refused_path(stage), {"stage": stage, "spent_hours": spent, "needed_hours": need,
                                                 "admit_hours": REGISTERED["admit_hours"], "provenance": prov,
                                                 "decision": "not admitted (§8); no later batch starts"})
            raise SystemExit(f"{stage} not admitted: {spent:.2f} h spent + {need:.2f} h exceeds {REGISTERED['admit_hours']} h")
        if arm == "C2":
            loaded["c2"] = sources(E.task_config())["04a run02"]
        return p

    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg)
        ext, l1 = cx["ext"], cx["l1"]
        runs = [EV.RunSpec(i, run_seed(arm, i), 0.0) for i in (runs_i if not SMOKE else runs_i[:2])]
        T = REGISTERED["ids"]["train"]
        base, span = (T["base"], T["span"]) if not SMOKE else (0, 1000)
        P = cfg.evo.population
        records = []

        def partial(recs, g):
            records[:] = recs
            E.write_atomic(E.partial_path(stage), {**ctx.doc, "generation": g,
                                                    "records": [E.run_record(r) for r in recs]})

        ctx.salvage = lambda: {"records": [E.run_record(r) for r in records]}
        recs = EV.evolve_batch(cfg, cx["iface"]["real"], cx["spec"], runs, generations=cfg.evo.generations,
                               checkpoint_every=REGISTERED["checkpoint_every"], validation_ids=ids("validation"),
                               world_seed=REGISTERED["world_seed"], id_base=base, id_span=span, device=dev,
                               check=ctx.cap.check, category=acct.category, on_checkpoint=partial,
                               initial=lambda r: initial(arm, r.run, cx, cfg, P, loaded.get("c2")),
                               mutation_scales=lambda r: A.arm_scales(ext, l1, arm))
        bad = {}
        for rec in recs:
            for kind, pop, extra in (("candidates", Genome.cat(rec.candidates),
                                      {"checkpoint_generations": [c["generation"] for c in rec.checkpoints]}),
                                     ("final", rec.final, {})):
                path = genomes_file(arm, rec.spec.run, kind)
                path.parent.mkdir(parents=True, exist_ok=True)
                save_population(path, pop, cfg=cfg, run=rec.spec.run, run_seed=rec.spec.run_seed, stage=stage, **extra)
            problems = check_assertions(arm, rec, ext, l1)
            if problems:
                bad[str(rec.spec.run)] = problems
        return {"arm": arm, "runs": [r.spec.run for r in recs], "assertions_failed": bad or None,
                "records": [E.run_record(r) for r in recs], "mutation_counts_per_generation": mutation_counts(ext, l1, arm, cfg),
                "composition": {"training": [len(recs) * P, cfg.evo.worlds_per_strain, 1],
                                "validation": [len(recs), len(ids("validation")), 1]},
                "genome_files": "local (rule 1): runs/e4s1/genomes/"}
    return E.run_stage(args, stage, requires, body)


# ============================================================================== evaluation

def completed_batches(args, prov) -> tuple[list[tuple[str, list[int], dict]], list[str]]:
    """The batches the evaluation covers, frozen at its start, and the ones it names as not covered."""
    states = [batch_state(s) for s in TRAIN_STAGES]
    covered = evaluated_batches(states)
    out = []
    for b in covered:
        rec = E.require_earlier(args, prov, TRAIN_STAGES[b])
        if rec.get("assertions_failed"):
            raise SystemExit(f"{TRAIN_STAGES[b]}'s assertions failed: E4s-1 stops")
        out.append((BATCHES[b][0], rec["runs"], rec))
    if not out:
        raise SystemExit("no training batch completed: nothing to evaluate")
    named = [f"{TRAIN_STAGES[b]} ({s})" for b, s in enumerate(states) if b not in covered]
    return out, named


def load_genomes(arm: str, i: int, kind: str, spec, cfg, run_record: dict) -> Genome:
    """A run's local genome file, checked against its committed training record: the brain configuration,
    every strain's hash, and (for candidates) the checkpoint generations."""
    g, meta = load_population(genomes_file(arm, i, kind), spec, cfg.brain)
    import dataclasses
    if dataclasses.asdict(g.cfg) != dataclasses.asdict(cfg.brain):
        raise SystemExit(f"{arm} run {i}'s {kind} file loads with another brain configuration")
    if kind == "candidates":
        want = [c["sha256"] for c in run_record["checkpoints"]]
        gens = [c["generation"] for c in run_record["checkpoints"]]
        if meta.get("checkpoint_generations") is not None and list(meta["checkpoint_generations"]) != gens:
            raise SystemExit(f"{arm} run {i}'s candidates are not the record's checkpoints")
    else:
        want = run_record["final_sha256"]
    got = [genome_hash(g, k) for k in range(g.n_strains)]
    if got != want:
        raise SystemExit(f"{arm} run {i}'s {kind} file does not match its committed record")
    return g


def save_counts(path: Path, counts: dict) -> None:
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, **counts)
    E.replace(tmp, path)


def cmd_eval_endpoints(args):
    loaded = {}

    def requires(a, prov):
        p = projection(a, prov)
        require_gates(a, prov)
        E.require_earlier(a, prov, "r-draws")
        loaded["batches"], loaded["not_covered"] = completed_batches(a, prov)
        loaded["c2"] = sources(E.task_config())["04a run02"]
        if not SMOKE and spent_hours() + p["projected_hours"]["eval-endpoints"] > REGISTERED["cap_gpu_hours"]:
            raise SystemExit("eval-endpoints not admitted: it would exceed the cap")
        return p

    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg)
        ext, l1, spec = cx["ext"], cx["l1"], cx["spec"]
        runs, counts = {}, {}
        cpath = EXP / "eval-endpoints-counts.npz"
        ctx.salvage = lambda: {"runs": runs, "counts_file_partial": cpath.name, "not_covered": loaded["not_covered"]}
        for arm, run_list, rec in loaded["batches"]:
            for r_i, r in zip(run_list, rec["records"]):
                key = f"{arm} run{r_i:02d}"
                cands = load_genomes(arm, r_i, "candidates", spec, cfg, r)
                genomes = {"F": cands.select([len(r["checkpoints"]) - 1]),
                           "C": cands.select([r["champion"]["checkpoint"]]), "G0": cands.select([0])}
                for w, g in genomes.items():
                    if genome_hash(g, 0) != r["checkpoints"][{"F": -1, "C": r["champion"]["checkpoint"], "G0": 0}[w]]["sha256"]:
                        raise SystemExit(f"{key} {w} does not match its record")
                runs[key] = {"arm": arm, "run": r_i}
                for w, g in genomes.items():
                    summ, c = endpoint(g, arm, r_i, w, cx, cfg, dev, ctx.cap, l1)
                    runs[key][w] = summ
                    for cond, v in c.items():
                        counts[f"{key}|{w}|{cond}"] = v.astype(np.int16)
                if arm == "R":  # the draw's own module on the carrier (turn 0): its K_D and K_C at generation 0
                    rmod = arm_module("R", r_i, l1)
                    alone = C.carrier_genome(ext, rmod, cfg.brain, forward=REGISTERED["carrier"]["forward"], turn=0.0)
                    runs[key]["R_draw_open_loop_g0"] = open_loop(alone, ext, cx["iface"]["real"], cfg, dev)
                    _, _, me, _, _ = A._masks(ext)
                    runs[key]["R_final_module"] = module_parameters(genomes["F"], ext, l1)
                if arm in ("M", "R"):
                    pop0 = initial(arm, r_i, cx, cfg, cfg.evo.population)
                    if r["checkpoints"][0]["sha256"] not in {genome_hash(pop0, s) for s in range(pop0.n_strains)}:
                        raise SystemExit(f"{key}'s regenerated generation 0 does not hold its G0 best")
                    w0 = ids("g0pop")
                    c = {k: play(cfg, cx["iface"][CONDITIONS[k][0]], pop0, w0, dev, ctx.cap, pop0.n_strains)
                         for k in (1, 2, 3)}
                    cis = [(D2.world_ci(c[1][s], c[2][s]), D2.world_ci(c[1][s], c[3][s])) for s in range(pop0.n_strains)]
                    cls = [D2.classify(a_, b_) for a_, b_ in cis]
                    runs[key]["g0_population_users"] = cls.count("uses")
                    runs[key]["g0_population_classes"] = cls
                    runs[key]["g0_population_contrasts"] = [{"mean": a_, "swapped": b_} for a_, b_ in cis]
                    runs[key]["g0_population_composition"] = [pop0.n_strains, len(w0), 1]
                    for k in c:
                        counts[f"{key}|g0pop|{k}"] = c[k].astype(np.int16)
                E.write_atomic(E.partial_path("eval-endpoints"), {**ctx.doc, "runs": runs})
                save_counts(cpath, counts)  # every finished run's counts survive an interruption
        refs = {}
        hold = ids("holdout")
        for turn in REGISTERED["carrier"]["turns"]:
            g = C.carrier_genome(ext, l1, cfg.brain, forward=REGISTERED["carrier"]["forward"], turn=turn)
            c = {k: play(cfg, cx["iface"][p], g, hold, dev, ctx.cap, 1)[0] for k, p in ((1, "real"), (2, "mean"), (3, "swapped"))}
            refs[f"L1 carrier turn {turn}"] = {"score": float(c[1].mean()), **classes(c, 1, 2, 3), "composition": [1, len(hold), 1]}
            for k, v in c.items():
                counts[f"ref L1 {turn}|{k}"] = v.astype(np.int16)
        c2 = play(cfg, cx["n2_iface"], loaded["c2"], hold, dev, ctx.cap, 1)[0]
        refs["04a run02 ungrafted"] = {"score": float(c2.mean())}
        counts["ref 04a run02 ungrafted|1"] = c2.astype(np.int16)
        save_counts(cpath, counts)
        return {"runs": runs, "references": refs, "not_covered": loaded["not_covered"],
                "composition": {"endpoints": [1, len(hold), 1]}, "counts_file": cpath.name,
                "counts_sha256": hashlib.sha256(cpath.read_bytes()).hexdigest()}
    return E.run_stage(args, "eval-endpoints", requires, body,
                       local_files=(EXP / "eval-endpoints-counts.npz",))


def cmd_eval_training(args):
    loaded = {}

    def requires(a, prov):
        p = projection(a, prov)
        require_gates(a, prov)
        ep = E.require_earlier(a, prov, "eval-endpoints")
        loaded["batches"], loaded["not_covered"] = completed_batches(a, prov)
        if [f"{arm} run{i:02d}" for arm, rl, _ in loaded["batches"] for i in rl] != list(ep["runs"]):
            raise SystemExit("the batches differ from those the endpoint evaluation covered")
        if not SMOKE and spent_hours() + p["projected_hours"]["eval-training"] > REGISTERED["cap_gpu_hours"]:
            raise SystemExit("eval-training not admitted: it would exceed the cap")
        return p

    def body(ctx):
        cfg, dev = ctx.cfg, ctx.args.device
        cx = context(cfg)
        ext, spec = cx["ext"], cx["spec"]
        along, finals, counts = {}, {}, {}
        cpath = EXP / "eval-training-counts.npz"
        ctx.salvage = lambda: {"along": along, "final_populations_M": finals, "counts_file_partial": cpath.name}
        w = ids("along")
        for arm, run_list, rec in loaded["batches"]:
            recs = dict(zip(run_list, rec["records"]))
            cands = {i: load_genomes(arm, i, "candidates", spec, cfg, recs[i]) for i in run_list}
            for gen in REGISTERED["along_generations"]:
                gens = [c["generation"] for c in recs[run_list[0]]["checkpoints"]]
                if gen not in gens:
                    raise SystemExit(f"generation {gen} is not a checkpoint")
                k = gens.index(gen)
                batch = Genome.cat([cands[i].select([k]) for i in run_list])
                c = {kk: play(cfg, cx["iface"][p], batch, w, dev, ctx.cap, batch.n_strains)
                     for kk, p in ((1, "real"), (2, "mean"), (3, "swapped"))}
                ol = open_loop(batch, ext, cx["iface"]["real"], cfg, dev)
                for s, i in enumerate(run_list):
                    key = f"{arm} run{i:02d}"
                    along.setdefault(key, {})[str(gen)] = {
                        "checkpoint": k, "sha256": recs[i]["checkpoints"][k]["sha256"],
                        "D": {"class": D2.classify(D2.world_ci(c[1][s], c[2][s]), D2.world_ci(c[1][s], c[3][s])),
                              "contrast_mean": D2.world_ci(c[1][s], c[2][s]), "contrast_swapped": D2.world_ci(c[1][s], c[3][s])},
                        "score": float(c[1][s].mean()),
                        "open_loop": {m: {q: v[q][s] for q in v} for m, v in ol.items()}}
                    for kk in c:
                        counts[f"{key}|{gen}|{kk}"] = c[kk][s].astype(np.int16)
            if arm == "M":
                for i in run_list:
                    fin = load_genomes(arm, i, "final", spec, cfg, recs[i])
                    wf = ids("finalpop")
                    c1 = play(cfg, cx["iface"]["real"], fin, wf, dev, ctx.cap, fin.n_strains)
                    c2 = play(cfg, cx["iface"]["mean"], fin, wf, dev, ctx.cap, fin.n_strains)
                    finals[f"M run{i:02d}"] = [D2.world_ci(c1[s], c2[s]) for s in range(fin.n_strains)]
                    counts[f"final M run{i:02d}|1"] = c1.astype(np.int16)
                    counts[f"final M run{i:02d}|2"] = c2.astype(np.int16)
            E.write_atomic(E.partial_path("eval-training"), {**ctx.doc, "along": along, "final_populations_M": finals})
            save_counts(cpath, counts)
        save_counts(cpath, counts)
        sizes = {arm: len(rl) for arm, rl, _ in loaded["batches"]}
        return {"along": along, "final_populations_M": finals, "counts_file": cpath.name,
                "counts_sha256": hashlib.sha256(cpath.read_bytes()).hexdigest(), "not_covered": loaded["not_covered"],
                "composition": {"along": {arm: [n, len(w), 1] for arm, n in sizes.items()},
                                "final_populations": [cfg.evo.population, len(ids("finalpop")), 1]}}
    return E.run_stage(args, "eval-training", requires, body,
                       local_files=(EXP / "eval-training-counts.npz",))


# ============================================================================== smoke and main

def use_smoke(args) -> None:
    global EXP, OUT, SMOKE, GUARDED
    EXP = OUT = ROOT / "runs" / "e4s1-smoke"
    SMOKE = True
    GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PREREG, *E.E1_INPUTS]
    R = REGISTERED
    R["ga"].update(generations=3, population=4, elites=1, truncation=2, worlds_per_strain=2)
    R["checkpoint_every"] = 2
    R["along_generations"] = [0, 2]
    for k in R["ids"]:
        if "worlds" in R["ids"][k]:
            R["ids"][k]["worlds"] = 8
    R["open_loop"]["ticks"], R["open_loop"]["average"] = 6, 2
    configure()
    stage = args.command if args.command != "train" else f"train-{args.batch}"
    for s in STAGES[STAGES.index(stage):]:
        for f in (E.record_path(s), E.marker_path(s), E.partial_path(s)):
            if EXP in f.parents:
                f.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=["project", "gate-1", "gate-2", "gate-3", "r-draws", "train", "eval-endpoints",
                                        "eval-training"])
    ap.add_argument("--batch", type=int, choices=range(1, len(BATCHES) + 1))
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--guarded", action="store_true")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--reason")
    args = ap.parse_args()
    if args.command == "train" and not args.batch:
        ap.error("train needs --batch 1-10")
    if args.smoke:
        use_smoke(args)
    {"project": cmd_project, "gate-1": cmd_gate1, "gate-2": cmd_gate2, "gate-3": cmd_gate3, "r-draws": cmd_rdraws,
     "train": cmd_train, "eval-endpoints": cmd_eval_endpoints, "eval-training": cmd_eval_training}[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    out = ROOT / "runs" / ("e4s1-smoke" if smoke else "e4s1")
    try:
        run_script(main, out_default=str(out), default="measure", name="e4s1")
    finally:
        agg = out / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
