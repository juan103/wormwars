"""03a's pilot-dev (experiments/03a-self-consistency/PILOT-DEV.md; DESIGN.md v7.1 §8).

    python scripts/e03a.py setup           # the SH-mirror graph (rebuilt, hashed, never saved) and its motor gains
    python scripts/e03a.py evolve-intact   # the selector brain and the MIP brain, in one lockstep batch
    python scripts/e03a.py panel           # the deletion scan on the selector brain, the panel rule, the two targets
    python scripts/e03a.py evolve-nip      # one NIP brain per target, pinned (X's edges zero), in one batch
    python scripts/e03a.py baseline        # intact, deleted and restored scores; the restoration controls must hold
    python scripts/e03a.py tune            # rounds A (ladder), B (moves), C (shaping), each chosen by its rule
    python scripts/e03a.py full            # the chosen settings: every search of the four target-brains, diagnostics
    python scripts/e03a.py probe           # the replay probe on the scripted calibrators and the evolved brains
    python scripts/e03a.py report          # throughputs, resolution, the projection and the cuts; no simulation
    python scripts/e03a.py family2         # family 2's simulated-null validation (DESIGN.md §7); CPU only
    python scripts/e03a.py <stage> --smoke                 # tiny sizes on the CPU, runs/e03a-smoke/
    python scripts/e03a.py <stage> --smoke --device cuda   # the same on CUDA, runs/e03a-smoke-cuda/: the preflight

Pilot-dev is development: its output is the frozen pilot protocol, written into the pre-registration before
pilot-check. It runs on one SH-mirror graph, never on N2, inside its own 6 GPU-hour cap (counted by T0's accounting
across attempts, the CUDA preflight included) and 03a's 72. Every number it uses is in `DEV`. Records (JSON) go to
experiments/03a-self-consistency/pilot-dev/; genomes and the graph stay local (the graph carries N2's weights,
permuted, and is rebuilt from its seed and checked by hash).

A stage that stops early (an error, or the cap) still writes its record, status "failed", with whatever it finished:
evolution checkpoints, completed tuning rounds, completed target-brains. A failed implementation control (restoration,
NIP deletion equivalence, the full-replay control, KT and KTM invariance under the probe) fails its stage, so nothing
downstream runs on it.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import calibration as calib  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e03a import arms as A  # noqa: E402
from wormwars.e03a import null as N  # noqa: E402
from wormwars.e03a import panel as P  # noqa: E402
from wormwars.e03a import reinsert as R  # noqa: E402
from wormwars.e03a import search as S  # noqa: E402
from wormwars.e03a import stats as T  # noqa: E402
from wormwars.e03a import structural as ST  # noqa: E402
from wormwars.e03a.probe import KT, KTS, ReplayBrain  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e1.controllers import scripted  # noqa: E402
from wormwars.evo.bundle import replay_mode  # noqa: E402
from wormwars.evo.genomes import genome_hash, load_population, save_population  # noqa: E402
from wormwars.evo.rollout import rollout_brain  # noqa: E402
from wormwars.exp03 import samplers as SM  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

_spec = importlib.util.spec_from_file_location("e04a_for_e03a", ROOT / "scripts" / "e04a.py")
E4 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E4)  # 04a's Task N and GA, checked against E1's gate record, unchanged

EXP = ROOT / "experiments" / "03a-self-consistency"
DEVREC = EXP / "development-records"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", "experiments/03a-self-consistency/PILOT-DEV.md",
           "experiments/03a-self-consistency/DESIGN.md"]
SMOKE = False
SMOKE_DEVICE = "cpu"
# probe runs before tune and full, so a cap reached in the searches still leaves its timings for the report (Fable)
STAGES = ["setup", "evolve-intact", "panel", "evolve-nip", "baseline", "probe", "tune", "full", "report", "family2"]
CPU_STAGES = {"report", "family2"}

DEV = {
    "graph": {"kind": "SH-mirror", "seed": 3_403_000, "passes": 20},  # outside 03's and 03r's SH-mirror seeds
    "cap_gpu_hours": 6.0,  # pilot-dev's own cap (DESIGN.md §8, §10)
    "experiment_cap_gpu_hours": 72.0, "charged_before_hours": 0.53,  # D094; the exploratory checks (D303, D304)
    "world_seed": 1_100_001,  # E1's run seed, as 04a: with the world id it generates each world
    "ids": {"train": [1_482_000_000, 500_000], "validation": [1_482_600_000, 256], "selection": [1_482_610_000, 512],
            "final": [1_482_620_000, 2048], "probe": [1_482_630_000, 2048], "search": [1_482_700_000, 100_000]},
    "runs": {"selector": 3_403_010, "mip": 3_403_011, "nip_base": 3_403_020},
    "checkpoint_every": 25,
    "panel": {"pair_seed": 3_403_001, "tier_seed": 3_403_002, "bootstrap": 10_000, "boot_seed": 3_403_003,
              "targets": "the two highest-relevance representatives (high tier, ranks 1 and 2)"},
    "search_seed_base": 3_403_100,
    "tune": {
        "default": {"temperatures": [0.1, 0.2, 0.4, 0.8], "p_move": 1 / 3, "max_moves": 1, "shaping": 0.0},
        "ladders": [[0.03, 0.06, 0.12, 0.24], [0.1, 0.2, 0.4, 0.8], [0.3, 0.6, 1.2, 2.4]],
        "moves": [[1 / 3, 1], [1 / 3, 3], [0.6, 1], [0.6, 3]],  # (p_move, max_moves); the rest split evenly
        "shaping": [0.0, 0.5],
        "searches": 2,  # free searches per setting and target-brain
        "swap_band": [0.2, 0.4], "swap_aim": 0.3,
        "tie": 0.02,  # a later setting must beat the earlier ones' best mean final count by more than this
    },
    "longer": {"factor": 2, "searches": 2, "on": "the MIP target-brains"},
    "probe": {"L": [5, 10, 20, 50], "control_L": 10},
    "null_B": 10_000, "null_seed": 3_403_004, "boot": {"B": 10_000, "seed": 3_403_005},
    "margin_fraction": 0.05,
    "family2": {"datasets": 20_000, "seed": 3_403_006},
}
SMOKE_DEV = {
    "graph": {"kind": "SH-mirror", "seed": 3_403_000, "passes": 1},
    "ids": {"train": [0, 1000], "validation": [2000, 4], "selection": [2100, 4], "final": [2200, 6],
            "probe": [2300, 4], "search": [3000, 1000]},
    "evolution": {"generations": 3, "population": 6, "elites": 1, "truncation": 3, "worlds_per_strain": 2},
    "horizon": 25, "panel_neurons": 6, "search": {"generations": 2, "worlds": 2, "offspring": 2},
    "tune": {"ladders": [[0.03, 0.06, 0.12, 0.24], [0.1, 0.2, 0.4, 0.8]], "moves": [[1 / 3, 1], [0.6, 3]],
             "searches": 1},
    "plan": {"refit": 2, "random": 1, "free": 2}, "null_B": 99, "boot": {"B": 200, "seed": 1},
    "panel": {"bootstrap": 200}, "probe": {"L": [5, 10]}, "family2": {"datasets": 500, "seed": 1},
}


def dev() -> dict:
    d = copy.deepcopy(DEV)
    if SMOKE:
        for k, v in SMOKE_DEV.items():
            d[k] = {**d.get(k, {}), **v} if isinstance(v, dict) and isinstance(d.get(k), dict) else v
    return d


def out_dir() -> Path:
    name = "e03a" if not SMOKE else "e03a-smoke" if SMOKE_DEVICE == "cpu" else "e03a-smoke-cuda"
    return ROOT / "runs" / name / "pilot-dev"


def preflight_dir() -> Path:
    return ROOT / "runs" / "e03a-smoke-cuda" / "pilot-dev"


def rec_dir() -> Path:
    return out_dir() / "records" if SMOKE else EXP / "pilot-dev"


def rec_path(stage: str) -> Path:
    if stage == "family2" and not SMOKE:
        return EXP / "family2-validation.json"
    return rec_dir() / f"{stage}.json"


def read(stage: str, partial: bool = False) -> dict:
    """A stage's record; it must have completed, unless `partial` accepts a stopped one (the report)."""
    p = rec_path(stage)
    if not p.exists():
        raise SystemExit(f"{stage} has not run ({p} is missing)")
    doc = json.loads(p.read_text(encoding="utf-8"))
    if doc.get("status") != "completed" and not partial:
        raise SystemExit(f"{stage} did not complete")
    return doc


def ids(name: str) -> np.ndarray:
    first, n = dev()["ids"][name]
    return np.arange(first, first + n)


class PilotClock(reg.CapClock):
    """Pilot-dev's cap: its own recorded seconds plus the CUDA preflight's, plus this process's time."""

    def spent_hours(self) -> float:
        total = super().spent_hours()
        pre = preflight_dir() / "compute.json"
        if not SMOKE and pre.exists():
            total += json.loads(pre.read_text(encoding="utf-8"))["totals"]["seconds_timed"] / 3600
        return total


def clock() -> reg.CapClock:
    if (out_dir() / "compute").exists():
        acct.write_aggregate(out_dir() / "compute", out_dir() / "compute.json")
    return PilotClock(dev()["cap_gpu_hours"], out_dir() / "compute.json")


def sync(dv) -> None:
    if str(dv).startswith("cuda"):
        torch.cuda.synchronize()


# ----------------------------------------------------------------------------- the task and the graph

def task_config(gains: dict | None = None):
    """04a's Task N (E1's, checked against E1's gate) and 04a's GA, with mono food sensing (DESIGN.md §2)."""
    cfg = E4.task_config()
    cfg.world.food_sensing = "mono"
    if SMOKE:
        s = dev()
        cfg.world.max_ticks = s["horizon"]
        for k, v in s["evolution"].items():
            if k != "generations":
                setattr(cfg.evo, k, v)
    if gains is not None:
        cfg.world.forward_gain, cfg.world.turn_gain = gains["forward_gain"], gains["turn_gain"]
    return cfg


def generations() -> int:
    return dev()["evolution"]["generations"] if SMOKE else E4.REGISTERED["evolution"]["generations"]


def graph_sha256(con) -> str:
    h = hashlib.sha256()
    for a in (con.chem, con.gap):
        h.update(np.ascontiguousarray(a, dtype=np.float32).tobytes())
    return h.hexdigest()


def build_graph(n2):
    g = dev()["graph"]
    return SM.build(n2, g["kind"], g["seed"], passes=g["passes"])


def the_graph(n2):
    """The pilot graph, rebuilt from its seed and checked against setup's hash."""
    con, _ = build_graph(n2)
    if graph_sha256(con) != read("setup")["graph"]["sha256"]:
        raise SystemExit("the rebuilt pilot graph does not match setup's hash")
    return con


def configured():
    n2 = load_connectome()
    con = the_graph(n2)
    return con, load_interface(con), task_config(read("setup")["gains"])


def device(args) -> str:
    if args.stage in CPU_STAGES:
        return "cpu"
    if SMOKE:
        if SMOKE_DEVICE != "cpu" and not torch.cuda.is_available():
            raise SystemExit("--device cuda without CUDA")
        return SMOKE_DEVICE
    if not torch.cuda.is_available():
        raise SystemExit("pilot-dev runs on CUDA")
    return "cuda"


# ----------------------------------------------------------------------------- genomes

def genomes_path(run: int) -> Path:
    return out_dir() / "genomes" / f"run{run:02d}-candidates.npz"


def save_candidates(rec: EV.RunRecord, cfg) -> None:
    if not rec.candidates:
        return
    path = genomes_path(rec.spec.run)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".tmp.npz")
    save_population(tmp, Genome.cat(rec.candidates), cfg=cfg, run=rec.spec.run, run_seed=rec.spec.run_seed,
                    checkpoint_generations=[c["generation"] for c in rec.checkpoints])
    os.replace(tmp, path)


def champion(run: int, stage: str, con, cfg) -> Genome:
    """A run's champion from its local file, checked against the committed hash."""
    r = next(x for x in read(stage)["runs"] if x["spec"]["run"] == run)
    cands, _ = load_population(genomes_path(run), BrainSpec.from_connectome(con), cfg.brain)
    g = cands.select([r["champion"]["checkpoint"]])
    if genome_hash(g, 0) != r["champion"]["sha256"]:
        raise SystemExit(f"run {run}'s champion does not match its record")
    return g


def run_record(rec: EV.RunRecord) -> dict:
    out = E4.run_record(rec)
    out.pop("generation0", None)  # per-world generation-0 tables are not needed here
    return out


def _ints(a) -> list:
    return np.asarray(a).astype(int).tolist()


# ----------------------------------------------------------------------------- stages

def stage_setup(args, dv, ck, progress):
    ck.check()
    n2 = load_connectome()
    con, info = build_graph(n2)
    iface = load_interface(con)
    cfg = task_config()
    with acct.category("calibration"):
        ref = calib.achieved_drive(n2, cfg, iface, n_strains=24, ticks=80, seed=0, device=dv)
        cal = calib.calibrate_in_world(con, cfg, iface, (ref.forward, ref.turn), n_strains=24, ticks=80, seed=0,
                                       device=dv)
    el = P.eligible(con, iface)
    reps = P.representatives(con, el, dev()["panel"]["pair_seed"])
    return {"graph": {"label": con.label, "sha256": graph_sha256(con), "sampler": info,
                      "chemical_edges": int((con.chem > 0).sum()), "gap_junctions": int((con.gap > 0).sum()) // 2},
            "gains": {"forward_gain": cal.forward_gain, "turn_gain": cal.turn_gain},
            "calibration": {"n2_reference": ref.as_dict(), "iterations": cal.iterations, "history": cal.history},
            "eligible": len(el), "representatives": len(reps),
            "task_config_sha256": E4.config_sha256(task_config())}


def _evolve(dv, ck, progress, runs, target_of):
    con, iface, cfg = configured()
    spec = BrainSpec.from_connectome(con)
    first, span = dev()["ids"]["train"]
    initial, scales = A.hooks(spec, cfg.brain, cfg.evo.population, target_of) if target_of else (None, None)

    def keep(records, generation):  # every checkpoint: genomes saved, records kept, so a stop loses no checkpoint
        for rec in records:
            save_candidates(rec, cfg)
        progress["runs"] = [run_record(rec) for rec in records]
        progress["checkpointed_through"] = int(generation)

    recs = EV.evolve_batch(cfg, iface, spec, runs, generations=generations(), checkpoint_every=dev()["checkpoint_every"],
                           validation_ids=ids("validation"), world_seed=dev()["world_seed"], id_base=first,
                           id_span=span, device=dv, check=ck.check, category=acct.category, initial=initial,
                           mutation_scales=scales, on_checkpoint=keep)
    out = []
    for rec in recs:
        save_candidates(rec, cfg)
        r = run_record(rec)
        x = target_of.get(rec.spec.run)
        if x is not None:
            r["target"] = {"index": int(x), "name": con.names[x]}
            r["pinned"] = all(R.x_edges_zero(g, x) for g in rec.candidates + [rec.final])
            if not r["pinned"]:
                raise RuntimeError(f"run {rec.spec.run}: X's edges are not zero")
        out.append(r)
    progress.pop("runs", None)
    return {"runs": out, "generations": generations()}


def stage_evolve_intact(args, dv, ck, progress):
    r = dev()["runs"]
    runs = [EV.RunSpec(run=0, run_seed=r["selector"], shaping=0.0), EV.RunSpec(run=1, run_seed=r["mip"], shaping=0.0)]
    return {**_evolve(dv, ck, progress, runs, {}), "roles": {"0": "selector", "1": "MIP"}}


def stage_panel(args, dv, ck, progress):
    con, iface, cfg = configured()
    sel = champion(0, "evolve-intact", con, cfg)
    pn = dev()["panel"]
    el = P.eligible(con, iface)
    reps = P.representatives(con, el, pn["pair_seed"])
    neurons = list(reps)[:dev()["panel_neurons"]] if SMOKE else list(reps)
    ck.check()
    with acct.category("measure"):
        intact, deleted = A.deletion_scan(cfg, iface, sel, neurons, ids("selection"), dev()["world_seed"], dv,
                                          chunk_worlds=FINAL_CHUNK)
    rel = P.relevance(intact[None], deleted[:, None, :], pn["bootstrap"], pn["boot_seed"])
    p_sel = dev()["margin_fraction"] * float(intact.mean())
    tiers = P.tiers(neurons, rel, p_sel, pn["tier_seed"])
    targets = tiers["high"][:2]
    return {"selector_intact_mean": float(intact.mean()), "p_sel": p_sel, "neurons": neurons,
            "names": [con.names[i] for i in neurons], "classes": [con.classes[i] for i in neurons],
            "relevance": {k: np.asarray(rel[k]).round(6).tolist() for k in ("mean", "lo", "hi")},
            "tiers": {k: tiers[k] for k in ("high", "medium", "low")},
            "tier_names": {k: [con.names[i] for i in tiers[k]] for k in ("high", "medium", "low")},
            "flags": {con.names[k]: v for k, v in tiers["flags"].items()},
            "paired": {con.names[i]: (con.names[reps[i]] if reps[i] is not None else None) for i in neurons},
            "targets": targets, "target_names": [con.names[i] for i in targets]}


def stage_evolve_nip(args, dv, ck, progress):
    targets = read("panel")["targets"]
    base = dev()["runs"]["nip_base"]
    runs = [EV.RunSpec(run=10 + k, run_seed=base + k, shaping=0.0) for k in range(len(targets))]
    return _evolve(dv, ck, progress, runs, {10 + k: int(x) for k, x in enumerate(targets)})


def target_brains(con, cfg):
    """The four target-brains: (label, arm, X, source brain, intact brain or None)."""
    targets = read("panel")["targets"]
    mip = champion(1, "evolve-intact", con, cfg)
    out = [(f"MIP/{con.names[x]}", "MIP", int(x), mip, mip) for x in targets]
    out += [(f"NIP/{con.names[x]}", "NIP", int(x), champion(10 + k, "evolve-nip", con, cfg), None)
            for k, x in enumerate(targets)]
    return out


def stage_baseline(args, dv, ck, progress):
    """The deleted and restored scores, and two implementation controls that must hold exactly, each pair run alone in
    the same batch composition inside `replay_mode()`: MIP's exact restoration reproduces the intact brain's episodes,
    and a NIP brain plays exactly as its deleted state on the union mask (X's edges are zero in both)."""
    con, iface, cfg = configured()
    ws, fin = dev()["world_seed"], ids("final")
    rows, failures = [], []
    with acct.category("final"), replay_mode():
        mip = champion(1, "evolve-intact", con, cfg)
        ck.check()
        intact_r = A.play(cfg, iface, mip, fin, ws, dv)
        mip_intact = np.asarray(intact_r.score[0])
        for label, arm, x, src, intact in target_brains(con, cfg):
            reins = R.Reinsertion(con, x, src, device=dv)
            ck.check()
            del_r = A.play(cfg, iface, reins.genome(reins.empty_state()), fin, ws, dv)
            deleted = np.asarray(del_r.score[0])
            row = {"label": label, "arm": arm, "x": x, "name": con.names[x], "deleted": _ints(deleted),
                   "counts": R.true_counts(con, x), "self_loop": reins.self_loop,
                   "degree": int((con.chem[x] > 0).sum() + (con.chem[:, x] > 0).sum() + (con.gap[x] > 0).sum())}
            if arm == "MIP":
                res_r = A.play(cfg, iface, reins.genome(reins.saved_state(intact)), fin, ws, dv)
                row["restored"] = _ints(res_r.score[0])
                row["restoration_exact"] = A.same_episodes(res_r, intact_r)
                row["deletion_deficit"] = float(mip_intact.mean() - deleted.mean())
                if not row["restoration_exact"]:
                    failures.append(f"{label}: restoration does not reproduce the intact brain")
                    rows.append(row)
                    break  # fail at once, keeping the offending result (Astra)
            else:
                ck.check()
                own_r = A.play(cfg, iface, src, fin, ws, dv)
                row["own_brain"] = _ints(own_r.score[0])
                row["own_equals_deleted"] = A.same_episodes(own_r, del_r)
                if not row["own_equals_deleted"]:
                    failures.append(f"{label}: the NIP brain does not play as its deleted state")
                    rows.append(row)
                    break
            rows.append(row)
    progress.update({"mip_intact": _ints(mip_intact), "target_brains": rows, "failures": failures})
    if failures:
        raise RuntimeError("implementation controls failed: " + "; ".join(failures))
    progress.clear()
    return {"mip_intact": _ints(mip_intact), "mip_intact_mean": float(mip_intact.mean()),
            "p": dev()["margin_fraction"] * float(mip_intact.mean()), "target_brains": rows}


def _scfg(setting: dict, **over) -> S.SearchConfig:
    pm = float(setting["p_move"])
    kw = dict(dev()["search"]) if SMOKE else {}
    kw.update(over)
    return S.SearchConfig(temperatures=tuple(setting["temperatures"]), p_move=pm, p_weights=(1 - pm) / 2,
                          p_tau_bias=(1 - pm) / 2, max_moves=int(setting["max_moves"]),
                          shaping=float(setting["shaping"]), **kw)


def _target_brain_inputs(con, iface, cfg, dv):
    tbs = []
    for label, arm, x, src, intact in target_brains(con, cfg):
        tbs.append({"label": label, "arm": arm, "x": x, "reins": R.Reinsertion(con, x, src, device=dv),
                    "truth": R.truth(con, x), "strat": N.strata(con, iface, x), "intact": intact})
    return tbs


def _run(searches, reins_of, cfg, iface, dv, ck, category="search", after=None, timing=None):
    """Every search to its end in lockstep. `timing`, if a list, receives (strains, worlds per strain, seconds) for each
    rollout group, so throughput is known per batch composition (Astra)."""
    evaluators = {}

    def evaluate(asks):
        out = [None] * len(asks)
        by = {}
        for i, (s, st, w) in enumerate(asks):
            by.setdefault(s.scfg.shaping, []).append(i)
        for sh, idx in by.items():
            ev = evaluators.setdefault(sh, S.simulator(cfg, iface, lambda s: reins_of[id(s)], dev()["world_seed"],
                                                       dv, shaping=sh))
            sync(dv)
            t0 = time.perf_counter()
            for i, sc in zip(idx, ev([asks[i] for i in idx])):
                out[i] = sc
            sync(dv)
            if timing is not None:
                timing.append((int(sum(asks[i][1].n for i in idx)), int(len(asks[idx[0]][2])),
                               round(time.perf_counter() - t0, 4)))
        return out

    with acct.category(category):
        S.run_lockstep(searches, evaluate, check=ck.check, after=after)


FINAL_CHUNK = 8 * 2048  # worlds per rollout chunk in final scoring and the scan (Fable: below E2d's tested 16 384)


def _final_scores(reins, states, cfg, iface, dv, ck) -> np.ndarray:
    with acct.category("final"):
        ck.check()
        return A.score_states(cfg, iface, reins, R.XState.cat(states), ids("final"), dev()["world_seed"], dv,
                              chunk_worlds=FINAL_CHUNK)


def _pair_rates(searches) -> list:
    """Swap acceptance per neighbour pair (m, m + 1), over the given searches."""
    R_ = searches[0].scfg.replicas if searches else 0
    att, acc = np.zeros(max(R_ - 1, 0)), np.zeros(max(R_ - 1, 0))
    for s in searches:
        for sw in s.trace.swaps:
            for m, ok in sw:
                att[m] += 1
                acc[m] += ok
    return [float(a / n) if n else float("nan") for a, n in zip(acc, att)]


def _q_trace(search, truth) -> list:
    """Q at generation 0 and after every 10 generations (index g - 1 holds the state after generation g)."""
    tot = sum(int(np.asarray(truth[t]).sum()) for t in R.TYPES)
    masks = [search.trace.initial_cold] + search.trace.cold_masks[9::10]
    return [round(sum(int((m[t].cpu().numpy() & truth[t]).sum()) for t in R.TYPES) / tot, 4) for m in masks]


def _chance_q(truth, K) -> float:
    k = [int(np.asarray(truth[t]).sum()) for t in R.TYPES]
    return float(sum(v * v for v in k) / K / sum(k))


def _ladder_pick(per, band, aim):
    """Round A's rule: a ladder qualifies if every neighbour pair's swap rate is inside the band; among those, the one
    whose mean pair rate is closest to the aim; if none qualifies, the one whose worst pair is nearest the band
    (flagged)."""
    lo, hi = band

    def gap(r):
        return 0.0 if lo <= r <= hi else min(abs(r - lo), abs(r - hi)) if np.isfinite(r) else np.inf

    ok = [si for si in per if all(gap(r) == 0.0 for r in per[si]["pair_rates"])]
    if ok:
        return min(ok, key=lambda si: (abs(np.mean(per[si]["pair_rates"]) - aim), si)), None
    return (min(per, key=lambda si: (max(gap(r) for r in per[si]["pair_rates"]), si)),
            "no ladder has every neighbour pair inside the swap band: the nearest")


def stage_tune(args, dv, ck, progress):
    read("baseline")  # the implementation controls must have held
    con, iface, cfg = configured()
    tbs = _target_brain_inputs(con, iface, cfg, dv)
    tn = dev()["tune"]
    base = dev()["search_seed_base"]
    first, span = dev()["ids"]["search"]
    chosen = dict(tn["default"])
    carried = None  # (setting, its results): the previous round's pick, reused rather than run again
    rounds = []
    progress["rounds"] = rounds
    plan = [("A", "temperatures", tn["ladders"]), ("B", "moves", tn["moves"]), ("C", "shaping", tn["shaping"])]
    for ri, (name, key, options) in enumerate(plan):
        settings = []
        for opt in options:
            s = dict(chosen)
            if key == "moves":
                s["p_move"], s["max_moves"] = opt
            else:
                s[key] = opt
            settings.append(s)
        reused = {si: carried for si, s in enumerate(settings) if carried is not None and s == carried[0]}
        searches, reins_of, where = [], {}, []
        for si, s in enumerate(settings):
            if si in reused:
                continue
            for bi, tb in enumerate(tbs):
                pr = S.problem_of(tb["reins"], R.true_counts(con, tb["x"]))
                for k in range(tn["searches"]):
                    seed = S.search_seed(base + 1000 * ri + 100 * si + bi, "free", k)
                    srch = S.free_search(pr, _scfg(s), cfg.brain, cfg.mutation, seed, world_base=first,
                                         world_span=span, label=f"{name}{si}/{tb['label']}/free-{k}")
                    searches.append(srch)
                    reins_of[id(srch)] = tb["reins"]
                    where.append((si, bi))
        _run(searches, reins_of, cfg, iface, dv, ck, category="tuning")
        per = {si: {"final_means": [], "q": []} for si in range(len(settings)) if si not in reused}
        for bi, tb in enumerate(tbs):
            mine = [(s, si) for s, (si, b) in zip(searches, where) if b == bi]
            if not mine:
                continue
            fin = _final_scores(tb["reins"], [s.result() for s, _ in mine], cfg, iface, dv, ck)
            for (s, si), row in zip(mine, fin):
                per[si]["final_means"].append(float(row.mean()))
                per[si]["q"].append(_q_trace(s, tb["truth"]))
        for si in per:
            mine = [s for s, (sj, _) in zip(searches, where) if sj == si]
            per[si]["pair_rates"] = _pair_rates(mine)
            per[si]["swap_rate"] = float(np.mean(per[si]["pair_rates"])) if per[si]["pair_rates"] else float("nan")
            per[si]["mean_final"] = float(np.mean(per[si]["final_means"]))
        for si, (_, res) in reused.items():
            per[si] = {**res, "reused_from_previous_round": True}
        per = dict(sorted(per.items()))
        if key == "temperatures":
            pick, flag = _ladder_pick(per, tn["swap_band"], tn["swap_aim"])
        else:
            pick, best, flag = 0, per[0]["mean_final"], None
            for si in range(1, len(settings)):
                if per[si]["mean_final"] > best + tn["tie"]:
                    pick, best = si, per[si]["mean_final"]
        chosen = settings[pick]
        carried = (chosen, {k: v for k, v in per[pick].items() if k != "reused_from_previous_round"})
        rounds.append({"round": name, "varied": key, "settings": settings, "results": per, "chosen": pick,
                       "flag": flag})
    progress.clear()
    return {"rounds": rounds, "chosen": chosen,
            "note": "B and C are chosen by their rule, far below their noise (two searches per setting and "
                    "target-brain): the settings are chosen, not shown optimal (Fable, Astra)"}


def _comparisons(fin, refits, randoms, frees, deleted, restored, margin, boot):
    ref = fin[refits].mean(axis=0)
    out = {"headroom": T.compare(ref, deleted, margin, over_brains=False, **boot),
           "advantage": T.compare(ref, fin[randoms].mean(axis=0), margin, over_brains=False, **boot),
           "functional": T.compare(fin[frees].mean(axis=0), ref, margin, over_brains=False, **boot)}
    if restored is not None:
        out["restoration"] = T.compare(ref, restored, margin, over_brains=False, **boot)
    return out


def _turnover(search, every=10) -> list:
    """The share of the coldest replica's partners replaced over each window of `every` generations: 0 -> 10, 10 -> 20,
    ..., up to the last generation (masks[g] is the state after generation g, masks[0] the initial one)."""
    masks = [search.trace.initial_cold] + search.trace.cold_masks
    masks = [{t: m[t].cpu().numpy() for t in R.TYPES} for m in masks]
    out = []
    for g in range(0, len(masks) - every, every):
        a, b = masks[g], masks[g + every]
        tot = sum(int(a[t].sum()) for t in R.TYPES)
        out.append(round(sum(int((a[t] & ~b[t]).sum()) for t in R.TYPES) / tot, 4) if tot else float("nan"))
    return out


def _weights(state) -> dict:
    return {t: (state.weights()[t][0].abs() * state.masks()[t][0]).cpu().numpy().astype(np.float64)
            for t in R.TYPES}


def _auc(state, truth) -> float:
    return float(N.recovery({t: v[None] for t, v in _weights(state).items()}, truth)["stat"][0])


def _diagnostics(search, truth, label) -> dict:
    return {"label": label, "q_every_10_from_0": _q_trace(search, truth),
            "turnover_per_10_from_0": _turnover(search),
            "accepted_moves": int(sum(k == "move" for g in search.trace.accepted_kind for k in g)),
            "pair_rates": _pair_rates([search]),
            # Fable's signal-to-noise record: the coldest replica's score across generations, and the paired
            # offspring-minus-current spread per generation (mean and SD of each, over generations)
            "cold_score_sd_over_generations": float(np.std([sc[0] for sc in search.trace.scores])),
            "paired_diff_mean": float(np.mean([p[0] for p in search.trace.paired])),
            "paired_diff_sd_mean": float(np.mean([p[1] for p in search.trace.paired]))}


def _agreement(results, truth) -> dict:
    """Pairwise agreement of the free searches' final states: Spearman of the |weight| vectors (Astra's and Fable's
    caution: mostly shared zeros) and, per type, the Jaccard index of the partner sets beside its expectation for
    independent random sets of the same size."""
    vecs = [np.concatenate([w for w in _weights(r).values()]) for r in results]
    spear = [float(spearmanr(a, b).statistic) for i, a in enumerate(vecs) for b in vecs[i + 1:]]
    jac = {}
    for t in R.TYPES:
        m = int(np.asarray(truth[t]).sum())
        K = len(truth[t])
        sets = [r.masks()[t][0].cpu().numpy() for r in results]
        jac[t] = {"pairwise": [N.jaccard(a, b) for i, a in enumerate(sets) for b in sets[i + 1:]],
                  "expected_random": N.expected_jaccard(K, m)}
    return {"spearman_pairwise": spear, "jaccard": jac}


def _descriptive(con, iface, tb, rank, m_map) -> dict:
    """§6's 'also reported': interface and non-interface AUCs, precision at k and average precision with their null,
    and, for paired targets, the AUC on the candidates the mirror ranking leaves at zero; the structural AUCs and the
    composite contrast."""
    truth, strat, x = tb["truth"], tb["strat"], tb["x"]
    cand = R.candidates(con.n, x)
    mapped = np.isin(cand, list(iface.mapped_neurons))
    out = {"auc_interface": N.subset_recovery({t: rank[t][None] for t in R.TYPES}, truth, mapped),
           "auc_non_interface": N.subset_recovery({t: rank[t][None] for t in R.TYPES}, truth, ~mapped)}
    perm = N.permutations(strat, dev()["null_B"], dev()["null_seed"] + x)
    pk, ap = {}, {}
    for t in R.TYPES:
        if not N.scoreable(truth[t]):
            continue
        obs_p = float(N.precision_at_k(rank[t], np.asarray(truth[t])[None])[0])
        null_p = N.precision_at_k(rank[t], np.asarray(truth[t], dtype=bool)[perm])
        pk[t] = {"observed": obs_p, "null_mean": float(null_p.mean()), "p": N.p_value(null_p, obs_p)}
        ap[t] = {"observed": float(N.average_precision(rank[t], np.asarray(truth[t])[None])[0]),
                 "chance": float(np.asarray(truth[t]).mean())}
    out["precision_at_k"], out["average_precision"] = pk, ap
    struct = {}
    for name, sc in (("mirror", ST.mirror(con, x, m_map)), ("class model", ST.class_model(con, x)),
                     ("degree", ST.degree(con, x))):
        if sc is not None:
            struct[name] = float(N.recovery({t: sc[t][None] for t in R.TYPES}, truth)["stat"][0])
    out["structural_auc"] = struct
    comp_name, comp = ST.composite(con, x, m_map)
    task = float(N.recovery({t: rank[t][None] for t in R.TYPES}, truth)["stat"][0])
    out["composite"] = {"name": comp_name, "task_minus_composite": task - struct[comp_name]}
    if comp_name == "mirror":
        # per type: the candidates whose mirror score of that type is zero (Astra, Fable: the design's "tied at zero" is
        # per ranking, so per type); each type's AUC on its own subset, averaged over the scoreable ones
        per_type = {}
        for t in R.TYPES:
            zero = np.asarray(comp[t]) == 0
            lab = np.asarray(truth[t], dtype=bool)[zero]
            row = {"size": int(zero.sum()), "partners": int(lab.sum()), "scoreable": bool(N.scoreable(lab))}
            if row["scoreable"]:
                row["auc"] = float(N.auc_from_ranks(N.ranks(rank[t][zero])[None], lab[None])[0, 0])
            per_type[t] = row
        aucs = [r["auc"] for r in per_type.values() if r["scoreable"]]
        out["mirror_zero_subset"] = {"per_type": per_type, "auc": float(np.mean(aucs)) if aucs else None,
                                     "definition": "per type: candidates with that type's mirror score zero"}
    return out


def _states_path(label: str) -> Path:
    return out_dir() / "states" / (label.replace("/", "_") + ".npz")


def _save_states(label: str, named: dict) -> None:
    """Search states kept locally as they finish (Astra): {name: one-state XState}."""
    path = _states_path(label)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".tmp.npz")
    flat = {f"{name}::{k}": v for name, st in named.items() for k, v in st.arrays().items()}
    np.savez(tmp, **flat)
    os.replace(tmp, path)


def _no_task(problem, scfg, bcfg, mcfg, seed, n) -> dict:
    """§8's no-task control for one target-brain: n free searches with fitness identically zero (nothing simulated),
    ranked as the real ones are."""
    results = []
    for k in range(n):
        s = S.free_search(problem, scfg, bcfg, mcfg, S.search_seed(seed, "free", k))
        S.run_lockstep([s], S.no_task)
        results.append(s.result())
    return S.ranking(results)


def _attributes(row, delta_search) -> dict:
    """The five attributes of DESIGN.md §6 for one target-brain, with pilot-dev's own δ_search (one brain per arm, so
    these are per target-brain, descriptive)."""
    c = row["comparisons"]
    rel = T.reliable_brain(row["refit_means"], delta_search, c.get("restoration")) if len(row["refit_means"]) > 1 \
        else None
    return {"reliable": rel, "headroom_present": c["headroom"]["verdict"] == "above",
            "advantage_present": c["advantage"]["verdict"] == "above", "functional": T.functional(c["functional"]),
            "enrichment_p_below_0.05": row["enrichment"]["p"] < 0.05,
            "outcome": T.outcome(bool(rel), T.functional(c["functional"]), row["enrichment"]["p"] < 0.05)}


def stage_full(args, dv, ck, progress):
    """The chosen settings on each target-brain in turn. What finishes is kept: the record's metadata from the start,
    each target-brain's search states (locally) as soon as its ordinary searches end, and its row once scored."""
    con, iface, cfg = configured()
    tbs = _target_brain_inputs(con, iface, cfg, dv)
    base_rec = read("baseline")
    setting = read("tune")["chosen"]
    scfg = _scfg(setting)
    first, span = dev()["ids"]["search"]
    plan = dev().get("plan", S.PLAN) if SMOKE else S.PLAN
    base = dev()["search_seed_base"] + 10_000
    lg = dev()["longer"]
    margin, boot = base_rec["p"], dev()["boot"]
    m_map = SM.mirror_map(con)
    rows, timing = [], []
    progress.update({"setting": setting, "plan": plan, "p": margin, "target_brains": rows, "search_timing": timing,
                     "searches_finished": [], "states_saved": []})
    for bi, tb in enumerate(tbs):
        brow = base_rec["target_brains"][bi]
        if brow["label"] != tb["label"]:
            raise RuntimeError(f"baseline's target-brain {bi} is {brow['label']}, not {tb['label']}")
        searches = S.target_brain_searches(tb["reins"], tb["truth"], tb["strat"], scfg, cfg.brain, cfg.mutation,
                                           seed=base + bi, plan=plan, world_base=first, world_span=span)
        if tb["arm"] == "MIP":
            long_cfg = _scfg(setting, generations=scfg.generations * lg["factor"])
            pr = S.problem_of(tb["reins"], R.true_counts(con, tb["x"]))
            for k in range(lg["searches"]):
                searches.append(S.free_search(pr, long_cfg, cfg.brain, cfg.mutation,
                                              S.search_seed(base + 500 + bi, "free", k), world_base=first,
                                              world_span=span, label=f"longer-{k}", snapshot_at=(scfg.generations,)))
        ordinary = [s for s in searches if not s.label.startswith("longer")]
        kept = {"done": False}

        def keep_finished(_, ordinary=ordinary, label=tb["label"], kept=kept, searches=searches):
            if not kept["done"] and all(s.done for s in ordinary):
                named = {s.label: s.result() for s in ordinary}
                named.update({f"{s.label}@{scfg.generations}": s.snapshots[scfg.generations]
                              for s in searches if s.label.startswith("longer") and s.snapshots})
                _save_states(label + "-at-ordinary-length", named)
                progress["states_saved"].append(label + "-at-ordinary-length")
                kept["done"] = True

        _run(searches, {id(s): tb["reins"] for s in searches}, cfg, iface, dv, ck, after=keep_finished, timing=timing)
        labels = [s.label for s in searches]
        states = [s.result() for s in searches]
        longer = [s for s in searches if s.label.startswith("longer")]
        states += [s.snapshots[scfg.generations] for s in longer]  # the same long searches at the ordinary length
        labels += [f"{s.label}@{scfg.generations}" for s in longer]
        _save_states(tb["label"], dict(zip(labels, states)))
        progress["states_saved"].append(tb["label"])
        progress["searches_finished"].append(tb["label"])
        fin = _final_scores(tb["reins"], states, cfg, iface, dv, ck)
        idx = lambda pre: [i for i, l in enumerate(labels) if l.startswith(pre) and "@" not in l]  # noqa: E731
        deleted = np.asarray(brow["deleted"], dtype=float)
        restored = np.asarray(brow["restored"], dtype=float) if "restored" in brow else None
        comp = _comparisons(fin, idx("refit"), idx("random"), idx("free"), deleted, restored, margin, boot)
        frees = [states[i] for i in idx("free")]
        rank = S.ranking(frees)
        # one permutation bank per target, shared by both arms (DESIGN.md §6; Astra, Fable)
        test = N.test({t: rank[t][None] for t in R.TYPES}, tb["truth"], tb["strat"], dev()["null_B"],
                      dev()["null_seed"] + tb["x"])
        pr = S.problem_of(tb["reins"], R.true_counts(con, tb["x"]))
        nt = _no_task(pr, scfg, cfg.brain, cfg.mutation, base + 900 + bi, len(idx("free")))
        no_task = N.test({t: nt[t][None] for t in R.TYPES}, tb["truth"], tb["strat"], dev()["null_B"],
                         dev()["null_seed"] + tb["x"])
        per_search = [{**_diagnostics(searches[i], tb["truth"], labels[i]), "final_mean": float(fin[i].mean()),
                       "auc": _auc(states[i], tb["truth"])} for i in idx("free") + idx("longer") + idx("refit")]
        long_rows = []
        for s in longer:
            i200, i100 = labels.index(s.label), labels.index(f"{s.label}@{scfg.generations}")
            long_rows.append({"label": s.label,
                              "final_mean": {str(scfg.generations): float(fin[i100].mean()),
                                             str(s.scfg.generations): float(fin[i200].mean())},
                              "auc": {str(scfg.generations): _auc(states[i100], tb["truth"]),
                                      str(s.scfg.generations): _auc(states[i200], tb["truth"])}})
        row = {"label": tb["label"], "arm": tb["arm"], "x": tb["x"], "name": con.names[tb["x"]],
               "deletion_deficit": brow.get("deletion_deficit"), "final_evaluation": "complete",
               "states": labels, "final_counts": {labels[i]: _ints(fin[i]) for i in range(len(labels))},
               "refit_means": [float(fin[i].mean()) for i in idx("refit")],
               "refit_sd": float(np.std([fin[i].mean() for i in idx("refit")], ddof=1)) if len(idx("refit")) > 1
               else float("nan"),
               "comparisons": comp, "enrichment": test, "no_task": no_task, "per_search": per_search,
               "ranking": {t: np.asarray(rank[t]).round(6).tolist() for t in R.TYPES},
               "chance_q": _chance_q(tb["truth"], tb["reins"].K), "agreement": _agreement(frees, tb["truth"]),
               "longer": long_rows, "descriptive": _descriptive(con, iface, tb, rank, m_map),
               "support_log10": N.support(tb["truth"], tb["strat"])["log10"],
               "strata": N.strata_report(tb["truth"], tb["strat"])}
        rows.append(row)
    res = resolution(rows, margin)
    for row in rows:
        row["attributes"] = _attributes(row, res["delta_search"])
    progress.clear()
    return {"setting": setting, "plan": plan, "p": margin, **res, "target_brains": rows, "search_timing": timing}


def resolution(rows, margin) -> dict:
    d_eval = T.pooled_rms([c["half_width"] for r in rows for c in r["comparisons"].values()])
    d_search = T.pooled_rms([r["refit_sd"] for r in rows if np.isfinite(r["refit_sd"])])
    return {"delta_eval": d_eval, "delta_search": d_search,
            "delta_search_fraction_of_p": d_search / margin if margin else float("nan"),
            "resolution_ok": bool(d_eval <= margin / 2 and d_search <= margin / 2)}


def _calibrators():
    """D303's KT and KTM winners and D304's KTS winners at T = 5, 10, 20, from the committed records."""
    mem = json.loads((DEVREC / "memoryless-check.json").read_text(encoding="utf-8"))
    slow = json.loads((DEVREC / "slow-memory-check.json").read_text(encoding="utf-8"))
    out = {"KT": KT(**mem["KT_check"]["params"]),
           "KTM": KT(fall_turn=mem["KTM_check"]["fall_turn"], **mem["KTM_check"]["params"])}
    for T_ in ("5.0", "10.0", "20.0"):
        out[f"KTS T={int(float(T_))}"] = KTS(float(T_), **dict(slow["by_T"][T_]["params"]))
    return out


def stage_probe(args, dv, ck, progress):
    """The replay probe. Controls that must hold, inside `replay_mode()` and in the probe's own batch composition: KT and
    KTM play exactly the same episodes at every L, and the full-replay control reproduces each evolved brain's episodes
    (counts, final head positions, every target event). The first failure stops the stage (Astra). Each condition,
    the control included, is timed for the projection."""
    read("baseline")  # the implementation controls must have held
    con, iface, cfg = configured()
    ws, pids = dev()["world_seed"], ids("probe")
    Ls = dev()["probe"]["L"]
    out = {"scripted": {}, "evolved": {}, "worlds": len(pids),
           "timing": {"plain": [], "replay": {str(L): [] for L in Ls}, "full_replay_control": []}}
    progress.update(out)

    def timed(brain, kind):
        ck.check()
        sync(dv)
        t0 = time.perf_counter()
        r = rollout_brain(cfg, iface, brain, pids, ws, dv)
        sync(dv)
        dt = time.perf_counter() - t0
        if kind == "plain":
            out["timing"]["plain"].append(dt)
        elif kind == "control":
            out["timing"]["full_replay_control"].append(dt)
        elif kind is not None:
            out["timing"]["replay"][kind].append(dt)
        return r

    def fail(msg):
        progress["failures"] = [msg]
        raise RuntimeError("probe control failed: " + msg)

    with acct.category("probe"), replay_mode():
        for name, pol in _calibrators().items():
            row, results = {}, {}
            for L in [None] + Ls:
                b = scripted(iface, pol, cfg, device=dv, n=con.n)
                results[L] = timed(b if L is None else ReplayBrain(b, L=L), None)
                row["plain" if L is None else f"L={L}"] = _ints(results[L].score[0])
            out["scripted"][name] = row
            if name in ("KT", "KTM"):
                row["unaffected"] = all(A.same_episodes(results[L], results[None]) for L in Ls)
                if not row["unaffected"]:
                    fail(f"{name} is affected by the probe")
        brains = [("selector", champion(0, "evolve-intact", con, cfg)), ("MIP", champion(1, "evolve-intact", con, cfg))]
        brains += [(f"NIP/{con.names[x]}", champion(10 + k, "evolve-nip", con, cfg))
                   for k, x in enumerate(read("panel")["targets"])]
        for name, g in brains:
            g = EV.moved(g, dv)
            row = {}
            out["evolved"][name] = row
            plain = timed(Brain(g), "plain")
            row["plain"] = _ints(plain.score[0])
            ctl = timed(ReplayBrain(Brain(g), L=dev()["probe"]["control_L"], window=None), "control")
            row["full_replay_equals_plain"] = A.same_episodes(ctl, plain)
            if not row["full_replay_equals_plain"]:
                fail(f"{name}: the full-replay control differs from the plain episodes")
            for L in Ls:
                row[f"L={L}"] = _ints(timed(ReplayBrain(Brain(g), L=L), str(L)).score[0])
            row["tau_quantiles"] = np.quantile(g.tau[0].cpu().numpy(), [0.1, 0.5, 0.9]).round(3).tolist()
    progress.clear()
    return out


def stage_report(args, dv, ck, progress):
    """No simulation. Reports what was measured, and projects the formal design only when every input is measured:
    a missing measurement withholds the projection and the 32-world permission instead of assuming a rate (Astra,
    Fable). A stopped `full` is reported as far as it got."""
    acct.write_aggregate(out_dir() / "compute", out_dir() / "compute.json")
    comp = json.loads((out_dir() / "compute.json").read_text(encoding="utf-8"))
    pre = preflight_dir() / "compute.json"
    pre_hours = (json.loads(pre.read_text(encoding="utf-8"))["totals"]["seconds_timed"] / 3600
                 if pre.exists() and not SMOKE else 0.0)
    spent = comp["totals"]["seconds_timed"] / 3600 + pre_hours
    remaining = dev()["experiment_cap_gpu_hours"] - dev()["charged_before_hours"] - spent
    rates = {}
    for k, v in comp["categories"].items():
        if v.get("seconds") and v.get("worlds_built"):
            rates[k] = {"worlds": v["worlds_built"], "seconds": v["seconds"],
                        "per_second": v["worlds_built"] / v["seconds"]}
    margin = read("baseline")["p"]  # the same p as `full`'s, available even when `full` stopped (Fable)
    out = {"rates": rates, "pilot_dev_hours": spent, "cuda_preflight_hours": pre_hours, "remaining_hours": remaining,
           "p": margin, "missing": []}
    full = read("full", partial=True) if rec_path("full").exists() else {}
    rows = full.get("target_brains", [])
    out.update({"full_complete": full.get("status") == "completed", "target_brains_measured": len(rows),
                "target_brains_measured_labels": [r["label"] for r in rows], "setting": full.get("setting"),
                "search_timing": full.get("search_timing", [])})
    if rows:
        out.update(resolution(rows, margin))
    if not out["full_complete"]:
        out["missing"].append("full did not complete: resolution and diagnostics cover the target-brains listed")
    need = ["selection", "holdout", "measure", "final", "search"]
    lacking = [k for k in need if k not in rates]
    probe = read("probe", partial=True) if rec_path("probe").exists() else {}
    pt = probe.get("timing") if probe.get("status") == "completed" else None
    if lacking:
        out["missing"].append(f"no measured rate for {lacking}")
    if pt is None:
        out["missing"].append("no completed probe: its timings are unknown")
    if lacking or pt is None:
        out["projection"] = None
        out["note"] = "projection and the 32-world permission withheld: not every input is measured"
        return out
    scale = 2048 / probe["worlds"]
    plain_s = float(np.mean(pt["plain"])) * scale
    replay_s = {L: float(np.mean(v)) * scale for L, v in pt["replay"].items()}
    control_s = float(np.mean(pt["full_replay_control"])) * scale
    # per brain: four replay probes, plus constant, two jitters, hold and a two-phase ramp (6 plain-like episodes), and
    # one full-replay control, priced at its own measured time (Astra: it replays far more than a bounded probe)
    probe_brain_s = 6 * plain_s + sum(replay_s.values()) + control_s
    r = {k: v["per_second"] for k, v in rates.items()}
    evolution_s = 256_000 / r["selection"] + 10_496 / r["holdout"]

    def projection(random_refits=5, free=5, worlds=16):
        tb_episodes = (3 + random_refits + free) * 100 * 4 * 9 * worlds
        states = 3 + random_refits + free + 1
        hours = {
            "N2 target-brains (60)": 60 * tb_episodes / r["search"] / 3600,
            "N2 evolutions (38)": 38 * evolution_s / 3600,
            "N2 final evaluations": (60 * states + 30 + 5) * 2048 / r["final"] / 3600,
            "N2 relevance scan and selection check": (3 * 246 * 512 + 5 * 7 * 512) / r["measure"] / 3600,
            "N2 probes (38 brains, one full-replay control each)": 38 * probe_brain_s / 3600,
            "pilot-check": (16 * tb_episodes / r["search"] + 14 * evolution_s + 16 * states * 2048 / r["final"]
                            + (2 * 246 * 512 + 2 * 4 * 2048) / r["measure"] + 12 * probe_brain_s) / 3600,
            "scripted re-measurement and calibration": 0.20e6 / r["final"] / 3600}
        return {"random_refits": random_refits, "free": free, "worlds": worlds, "hours": hours,
                "total": sum(hours.values())}

    options = [projection(), projection(random_refits=3), projection(random_refits=3, free=4)]
    fits = [o for o in options if o["total"] <= remaining]
    plan = fits[0] if fits else None
    w32 = projection(worlds=32)
    out.update({
        "probe_seconds_per_brain": probe_brain_s, "projections": options, "plan": plan,
        "cut": None if plan is None else {(5, 5): "none", (3, 5): "random refits 5 -> 3",
                                          (3, 4): "random refits 5 -> 3 and free searches 5 -> 4"}[
            (plan["random_refits"], plan["free"])],
        "search_worlds_32": {"projection": w32, "allowed": bool(remaining - w32["total"] >= 8.0)},
        "extrapolations": [
            "evolution is priced at pilot-dev's two-run lockstep rate (512 worlds a rollout); the formal batches have "
            "other compositions, and their rate is assumed, not measured",
            "searches are priced at the overall `search` rate, which mixes the measured compositions listed in "
            "`search_timing` (strains, worlds per strain, seconds); the formal compositions, the cuts and 32 worlds "
            "change them again, so the rate is an assumption for those",
            "probes are priced per brain from the evolved brains' measured condition times, one full-replay control "
            "per brain included"]})
    return out


def stage_family2(args, dv, ck, progress):
    """DESIGN.md §7: 20 000 simulated datasets per scenario; every sharp-null scenario at most 0.0531."""
    f2 = dev()["family2"]
    return T.validate_family2(f2["datasets"], f2["seed"])


DEFAULT_CATEGORY = {"setup": "calibration", "evolve-intact": "selection", "panel": "measure", "evolve-nip": "selection",
                    "baseline": "final", "tune": "tuning", "full": "search", "probe": "probe", "report": "measure",
                    "family2": "measure"}
FUNCS = {"setup": stage_setup, "evolve-intact": stage_evolve_intact, "panel": stage_panel,
         "evolve-nip": stage_evolve_nip, "baseline": stage_baseline, "tune": stage_tune, "full": stage_full,
         "probe": stage_probe, "report": stage_report, "family2": stage_family2}


def run_stage(args) -> dict:
    stage = args.stage
    prov = reg.provenance(GUARDED)
    if not SMOKE:
        if prov["dirty"]:
            raise SystemExit("uncommitted changes in the guarded files: commit first")
        reg.require_pins(prov)
    path = rec_path(stage)
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        if not args.rerun:
            raise SystemExit(f"{stage} has a record ({old.get('status')}); rerun with --rerun --reason")
        if not args.reason:
            raise SystemExit("--rerun needs --reason")
        k = 1
        while path.with_name(f"{stage}.attempt{k}.json").exists():
            k += 1
        os.replace(path, path.with_name(f"{stage}.attempt{k}.json"))
    dv = device(args)
    ck = clock()
    t0 = time.time()
    doc = {"stage": stage, "smoke": SMOKE, "device": dv, "provenance": prov, "dev": dev(), "rerun_reason": args.reason,
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    progress: dict = {}
    try:
        with acct.recorded(out_dir() / "compute", out_dir() / "compute.json", default=DEFAULT_CATEGORY[stage],
                           experiment="03a", stage=stage, script="scripts/e03a.py"):
            doc.update(FUNCS[stage](args, dv, ck, progress))
        doc["status"] = "completed"
    except BaseException as e:  # noqa: BLE001  (recorded, with what finished, then re-raised)
        doc["status"], doc["error"] = "failed", f"{type(e).__name__}: {e}"
        doc.update({k: v for k, v in progress.items() if k not in doc})
        raise
    finally:
        doc["seconds"] = time.time() - t0
        reg.write_json(path, doc, atomic=True)
    return doc


def main(argv=None):
    global SMOKE, SMOKE_DEVICE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=STAGES)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="with --smoke only")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--reason")
    args = ap.parse_args(argv)
    if args.device != "cpu" and not args.smoke:
        raise SystemExit("--device is for smoke runs; pilot-dev itself runs on CUDA")
    SMOKE, SMOKE_DEVICE = args.smoke, args.device
    doc = run_stage(args)
    print(f"{args.stage}: {doc['status']} in {doc['seconds']:.0f} s -> {rec_path(args.stage)}")
    return doc


if __name__ == "__main__":
    main()
