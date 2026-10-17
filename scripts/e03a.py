"""03a's pilot-dev (experiments/03a-self-consistency/PILOT-DEV.md; DESIGN.md v7.1 §8).

    python scripts/e03a.py setup           # the SH-mirror graph (rebuilt, hashed, never saved) and its motor gains
    python scripts/e03a.py evolve-intact   # the selector brain and the MIP brain, in one lockstep batch
    python scripts/e03a.py panel           # the deletion scan on the selector brain, the panel rule, the two targets
    python scripts/e03a.py evolve-nip      # one NIP brain per target, pinned (X's edges zero), in one batch
    python scripts/e03a.py baseline        # intact, deleted and restored scores on the final-evaluation worlds
    python scripts/e03a.py tune            # rounds A (ladder), B (moves), C (shaping), each chosen by its rule
    python scripts/e03a.py full            # the frozen settings: every search of the four target-brains, diagnostics
    python scripts/e03a.py probe           # the replay probe on the scripted calibrators and the evolved brains
    python scripts/e03a.py report          # throughputs, resolution, the projection and the cuts; no GPU
    python scripts/e03a.py family2         # family 2's simulated-null validation (DESIGN.md §7); CPU only
    python scripts/e03a.py <stage> --smoke # tiny sizes on the CPU, runs/e03a-smoke/

Pilot-dev is development: its output is the frozen pilot protocol, written into the pre-registration before
pilot-check. It runs on one SH-mirror graph, never on N2, inside its own 6 GPU-hour cap (counted by T0's accounting
across attempts) and 03a's 72. Every number it uses is in `DEV`. Records (JSON) go to
experiments/03a-self-consistency/pilot-dev/; genomes and the graph stay local (the graph carries N2's weights,
permuted, and is rebuilt from its seed and checked by hash).
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
STAGES = ["setup", "evolve-intact", "panel", "evolve-nip", "baseline", "tune", "full", "probe", "report", "family2"]
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
    return ROOT / "runs" / ("e03a-smoke" if SMOKE else "e03a") / "pilot-dev"


def rec_dir() -> Path:
    return out_dir() / "records" if SMOKE else EXP / "pilot-dev"


def rec_path(stage: str) -> Path:
    if stage == "family2" and not SMOKE:
        return EXP / "family2-validation.json"
    return rec_dir() / f"{stage}.json"


def read(stage: str) -> dict:
    p = rec_path(stage)
    if not p.exists():
        raise SystemExit(f"{stage} has not run ({p.relative_to(ROOT)} is missing)")
    doc = json.loads(p.read_text(encoding="utf-8"))
    if doc.get("status") != "completed":
        raise SystemExit(f"{stage} did not complete")
    return doc


def ids(name: str) -> np.ndarray:
    first, n = dev()["ids"][name]
    return np.arange(first, first + n)


def clock() -> reg.CapClock:
    if (out_dir() / "compute").exists():
        acct.write_aggregate(out_dir() / "compute", out_dir() / "compute.json")
    return reg.CapClock(dev()["cap_gpu_hours"], out_dir() / "compute.json")


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
    con, info = SM.build(n2, g["kind"], g["seed"], passes=g["passes"])
    return con, info


def the_graph(n2):
    """The pilot graph, rebuilt from its seed and checked against setup's hash."""
    con, _ = build_graph(n2)
    want = read("setup")["graph"]["sha256"]
    if graph_sha256(con) != want:
        raise SystemExit("the rebuilt pilot graph does not match setup's hash")
    return con


def configured():
    n2 = load_connectome()
    con = the_graph(n2)
    iface = load_interface(con)
    cfg = task_config(read("setup")["gains"])
    return con, iface, cfg


def device(args) -> str:
    if SMOKE or args.stage in CPU_STAGES:
        return "cpu"
    if not torch.cuda.is_available():
        raise SystemExit("pilot-dev runs on CUDA")
    return "cuda"


# ----------------------------------------------------------------------------- genomes

def genomes_path(run: int) -> Path:
    return out_dir() / "genomes" / f"run{run:02d}-candidates.npz"


def save_candidates(rec: EV.RunRecord, cfg) -> None:
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


# ----------------------------------------------------------------------------- stages

def stage_setup(args, dv, ck):
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


def _evolve(dv, ck, runs, target_of):
    con, iface, cfg = configured()
    spec = BrainSpec.from_connectome(con)
    first, span = dev()["ids"]["train"]
    initial, scales = A.hooks(spec, cfg.brain, cfg.evo.population, target_of) if target_of else (None, None)
    recs = EV.evolve_batch(cfg, iface, spec, runs, generations=generations(), checkpoint_every=dev()["checkpoint_every"],
                           validation_ids=ids("validation"), world_seed=dev()["world_seed"], id_base=first,
                           id_span=span, device=dv, check=ck.check, category=acct.category, initial=initial,
                           mutation_scales=scales)
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
    return {"runs": out, "generations": generations()}


def stage_evolve_intact(args, dv, ck):
    r = dev()["runs"]
    runs = [EV.RunSpec(run=0, run_seed=r["selector"], shaping=0.0), EV.RunSpec(run=1, run_seed=r["mip"], shaping=0.0)]
    return {**_evolve(dv, ck, runs, {}), "roles": {"0": "selector", "1": "MIP"}}


def stage_panel(args, dv, ck):
    con, iface, cfg = configured()
    sel = champion(0, "evolve-intact", con, cfg)
    pn = dev()["panel"]
    el = P.eligible(con, iface)
    reps = P.representatives(con, el, pn["pair_seed"])
    neurons = list(reps)[:dev()["panel_neurons"]] if SMOKE else list(reps)
    ck.check()
    with acct.category("measure"):
        intact, deleted = A.deletion_scan(cfg, iface, sel, neurons, ids("selection"), dev()["world_seed"], dv)
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


def stage_evolve_nip(args, dv, ck):
    targets = read("panel")["targets"]
    base = dev()["runs"]["nip_base"]
    runs = [EV.RunSpec(run=10 + k, run_seed=base + k, shaping=0.0) for k in range(len(targets))]
    return _evolve(dv, ck, runs, {10 + k: int(x) for k, x in enumerate(targets)})


def target_brains(con, cfg):
    """The four target-brains: (label, arm, X, source brain, intact brain or None)."""
    targets = read("panel")["targets"]
    mip = champion(1, "evolve-intact", con, cfg)
    out = []
    for k, x in enumerate(targets):
        out.append((f"MIP/{con.names[x]}", "MIP", int(x), mip, mip))
    for k, x in enumerate(targets):
        out.append((f"NIP/{con.names[x]}", "NIP", int(x), champion(10 + k, "evolve-nip", con, cfg), None))
    return out


def _ints(a) -> list:
    return np.asarray(a).astype(int).tolist()


def stage_baseline(args, dv, ck):
    con, iface, cfg = configured()
    ws, fin = dev()["world_seed"], ids("final")
    rows = []
    with acct.category("final"):
        mip = champion(1, "evolve-intact", con, cfg)
        ck.check()
        mip_intact = A.counts(cfg, iface, mip, fin, ws, dv)[0]
        for label, arm, x, src, intact in target_brains(con, cfg):
            reins = R.Reinsertion(con, x, src)
            ck.check()
            deleted = A.score_states(cfg, iface, reins, reins.empty_state(), fin, ws, dv)[0]
            row = {"label": label, "arm": arm, "x": x, "name": con.names[x], "deleted": _ints(deleted),
                   "counts": R.true_counts(con, x), "self_loop": reins.self_loop,
                   "degree": int((con.chem[x] > 0).sum() + (con.chem[:, x] > 0).sum() + (con.gap[x] > 0).sum())}
            if arm == "MIP":
                restored = A.score_states(cfg, iface, reins, reins.saved_state(intact), fin, ws, dv)[0]
                row["restored"] = _ints(restored)
                row["restoration_exact"] = bool(np.array_equal(restored, mip_intact))
            else:
                ck.check()
                own = A.counts(cfg, iface, src, fin, ws, dv)[0]
                row["own_brain"] = _ints(own)
                row["own_equals_deleted"] = bool(np.array_equal(own, deleted))
            rows.append(row)
    return {"mip_intact": _ints(mip_intact), "mip_intact_mean": float(mip_intact.mean()),
            "p": dev()["margin_fraction"] * float(mip_intact.mean()), "target_brains": rows}


def _scfg(setting: dict) -> S.SearchConfig:
    pm = float(setting["p_move"])
    kw = {}
    if SMOKE:
        kw = dict(dev()["search"])
    return S.SearchConfig(temperatures=tuple(setting["temperatures"]), p_move=pm, p_weights=(1 - pm) / 2,
                          p_tau_bias=(1 - pm) / 2, max_moves=int(setting["max_moves"]),
                          shaping=float(setting["shaping"]), **kw)


def _setup_searches(con, iface, cfg):
    tbs = []
    for label, arm, x, src, intact in target_brains(con, cfg):
        reins = R.Reinsertion(con, x, src)
        tbs.append({"label": label, "arm": arm, "x": x, "reins": reins, "truth": R.truth(con, x),
                    "strat": N.strata(con, iface, x), "intact": intact})
    return tbs


def _run(searches, reins_of, cfg, iface, dv, ck, category="search"):
    ev_by_shaping = {}

    def evaluate(asks):
        out = [None] * len(asks)
        by = {}
        for i, (s, st, w) in enumerate(asks):
            by.setdefault(s.scfg.shaping, []).append(i)
        for sh, idx in by.items():
            ev = ev_by_shaping.setdefault(sh, S.simulator(cfg, iface, lambda s: reins_of[id(s)], dev()["world_seed"],
                                                          dv, shaping=sh))
            for i, sc in zip(idx, ev([asks[i] for i in idx])):
                out[i] = sc
        return out

    with acct.category(category):
        S.run_lockstep(searches, evaluate, check=ck.check)


def _final_scores(groups, cfg, iface, dv, ck):
    """{reinsertion id: [states, worlds]} for lists of one-state results grouped by reinsertion."""
    out = {}
    with acct.category("final"):
        for key, (reins, states) in groups.items():
            ck.check()
            out[key] = A.score_states(cfg, iface, reins, R.XState.cat(states), ids("final"), dev()["world_seed"], dv)
    return out


def _swap_rate(searches) -> float:
    att = sum(len(sw) for s in searches for sw in s.trace.swaps)
    acc = sum(ok for s in searches for sw in s.trace.swaps for _, ok in sw)
    return acc / att if att else float("nan")


def _q(trace_masks, truth) -> list:
    tot = sum(int(np.asarray(truth[t]).sum()) for t in R.TYPES)
    return [round(sum(int((m[t].cpu().numpy() & truth[t]).sum()) for t in R.TYPES) / tot, 4) for m in trace_masks]


def stage_tune(args, dv, ck):
    con, iface, cfg = configured()
    tbs = _setup_searches(con, iface, cfg)
    tn = dev()["tune"]
    base = dev()["search_seed_base"]
    first, span = dev()["ids"]["search"]
    chosen = dict(tn["default"])
    carried = None  # (setting, its results): the previous round's pick, reused rather than run again
    rounds = []
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
        groups = {}
        for srch, (si, bi) in zip(searches, where):
            groups.setdefault(bi, (tbs[bi]["reins"], []))[1].append(srch.result())
        fin = _final_scores(groups, cfg, iface, dv, ck)
        per = {si: {"swap_rate": None, "final_means": [], "q_final": []} for si in range(len(settings))
               if si not in reused}
        pos = {bi: 0 for bi in range(len(tbs))}
        for srch, (si, bi) in zip(searches, where):
            per[si]["final_means"].append(float(fin[bi][pos[bi]].mean()))
            per[si]["q_final"].append(_q([srch.trace.cold_masks[-1]], tbs[bi]["truth"])[0])
            pos[bi] += 1
        for si in per:
            per[si]["swap_rate"] = _swap_rate([s for s, (sj, _) in zip(searches, where) if sj == si])
            per[si]["mean_final"] = float(np.mean(per[si]["final_means"]))
        for si, (_, res) in reused.items():
            per[si] = {**res, "reused_from_previous_round": True}
        per = dict(sorted(per.items()))
        if key == "temperatures":
            lo, hi = tn["swap_band"]
            inside = [si for si in per if lo <= per[si]["swap_rate"] <= hi]
            pool = inside or list(per)
            pick = min(pool, key=lambda si: (abs(per[si]["swap_rate"] - tn["swap_aim"]), si))
            flag = None if inside else "no ladder inside the swap band: the closest to the aim"
        else:
            pick, best = 0, per[0]["mean_final"]
            for si in range(1, len(settings)):
                if per[si]["mean_final"] > best + tn["tie"]:
                    pick, best = si, per[si]["mean_final"]
            flag = None
        chosen = settings[pick]
        carried = (chosen, {k: v for k, v in per[pick].items() if k != "reused_from_previous_round"})
        rounds.append({"round": name, "varied": key, "settings": settings, "results": per, "chosen": pick,
                       "flag": flag})
    return {"rounds": rounds, "chosen": chosen}


def _comparisons(fin_tb, refits, randoms, frees, deleted, restored, margin, boot):
    ref = fin_tb[refits].mean(axis=0)
    out = {"headroom": T.compare(ref, deleted, margin, over_brains=False, **boot),
           "advantage": T.compare(ref, fin_tb[randoms].mean(axis=0), margin, over_brains=False, **boot),
           "functional": T.compare(fin_tb[frees].mean(axis=0), ref, margin, over_brains=False, **boot)}
    if restored is not None:
        out["restoration"] = T.compare(ref, restored, margin, over_brains=False, **boot)
    return out


def _turnover(masks, every=10) -> float:
    vals = []
    for a, b in zip(masks[:-every:every], masks[every::every]):
        tot = sum(int(a[t].sum()) for t in R.TYPES)
        if tot:
            vals.append(sum(int((a[t] & ~b[t]).sum()) for t in R.TYPES) / tot)
    return float(np.mean(vals)) if vals else float("nan")


def stage_full(args, dv, ck):
    con, iface, cfg = configured()
    tbs = _setup_searches(con, iface, cfg)
    base_rec = read("baseline")
    setting = read("tune")["chosen"]
    scfg = _scfg(setting)
    first, span = dev()["ids"]["search"]
    plan = dev().get("plan", S.PLAN) if SMOKE else S.PLAN
    base = dev()["search_seed_base"] + 10_000
    lg = dev()["longer"]
    searches, reins_of, owner = [], {}, []
    for bi, tb in enumerate(tbs):
        for s in S.target_brain_searches(tb["reins"], tb["truth"], tb["strat"], scfg, cfg.brain, cfg.mutation,
                                         seed=base + bi, plan=plan, world_base=first, world_span=span):
            searches.append(s)
            reins_of[id(s)] = tb["reins"]
            owner.append(bi)
        if tb["arm"] == "MIP":
            long_cfg = S.SearchConfig(**{**asdict_scfg(scfg), "generations": scfg.generations * lg["factor"]})
            pr = S.problem_of(tb["reins"], R.true_counts(con, tb["x"]))
            for k in range(lg["searches"]):
                s = S.free_search(pr, long_cfg, cfg.brain, cfg.mutation, S.search_seed(base + 500 + bi, "free", k),
                                  world_base=first, world_span=span, label=f"longer-{k}")
                searches.append(s)
                reins_of[id(s)] = tb["reins"]
                owner.append(bi)
    _run(searches, reins_of, cfg, iface, dv, ck)
    groups = {}
    for s, bi in zip(searches, owner):
        groups.setdefault(bi, (tbs[bi]["reins"], []))[1].append(s.result())
    fin = _final_scores(groups, cfg, iface, dv, ck)
    margin = base_rec["p"]
    boot = dev()["boot"]
    m = SM.mirror_map(con)
    rows = []
    for bi, tb in enumerate(tbs):
        mine = [s for s, b in zip(searches, owner) if b == bi]
        labels = [s.label for s in mine]
        idx = lambda pre: [i for i, l in enumerate(labels) if l.startswith(pre)]  # noqa: E731
        brow = base_rec["target_brains"][bi]
        deleted = np.asarray(brow["deleted"], dtype=float)
        restored = np.asarray(brow["restored"], dtype=float) if "restored" in brow else None
        f = fin[bi]
        comp = _comparisons(f, idx("refit"), idx("random"), idx("free"), deleted, restored, margin, boot)
        frees = [mine[i].result() for i in idx("free")]
        rk = S.ranking(frees)
        test = N.test({t: rk[t][None] for t in R.TYPES}, tb["truth"], tb["strat"], dev()["null_B"],
                      dev()["null_seed"] + bi)
        struct = {}
        for name, sc in (("mirror", ST.mirror(con, tb["x"], m)), ("class model", ST.class_model(con, tb["x"])),
                         ("degree", ST.degree(con, tb["x"]))):
            if sc is not None:
                struct[name] = float(N.recovery({t: sc[t][None] for t in R.TYPES}, tb["truth"])["stat"][0])
        per_search = []
        for i in idx("free"):
            r = mine[i].result()
            one = {t: (r.weights()[t][0].abs() * r.masks()[t][0]).cpu().numpy()[None] for t in R.TYPES}
            per_search.append({"label": labels[i], "final_mean": float(f[i].mean()),
                               "auc": float(N.recovery(one, tb["truth"])["stat"][0]),
                               "q": _q(mine[i].trace.cold_masks[::10] + [mine[i].trace.cold_masks[-1]], tb["truth"]),
                               "turnover_per_10": _turnover([{t: mm[t].cpu().numpy() for t in R.TYPES}
                                                             for mm in mine[i].trace.cold_masks]),
                               "accepted_moves": int(sum(k == "move" for g in mine[i].trace.accepted_kind
                                                         for k in g)),
                               "swap_rate": _swap_rate([mine[i]])})
        vecs = [np.concatenate([(r.weights()[t][0].abs() * r.masks()[t][0]).cpu().numpy() for t in R.TYPES])
                for r in frees]
        agree = [float(spearmanr(a, b).statistic) for i, a in enumerate(vecs) for b in vecs[i + 1:]]
        row = {"label": tb["label"], "arm": tb["arm"], "x": tb["x"], "name": con.names[tb["x"]],
               "states": labels, "final_counts": {labels[i]: _ints(f[i]) for i in range(len(labels))},
               "refit_means": [float(f[i].mean()) for i in idx("refit")],
               "refit_sd": float(np.std([f[i].mean() for i in idx("refit")], ddof=1)) if len(idx("refit")) > 1
               else float("nan"),
               "comparisons": comp, "enrichment": test, "structural_auc": struct, "per_search": per_search,
               "ranking_agreement_pairwise_spearman": agree,
               "support_log10": N.support(tb["truth"], tb["strat"])["log10"],
               "strata": N.strata_report(tb["truth"], tb["strat"])}
        if idx("longer"):
            row["longer_gain"] = float(np.mean([f[i].mean() for i in idx("longer")])
                                       - np.mean([f[i].mean() for i in idx("free")]))
        rows.append(row)
    d_eval = T.pooled_rms([c["half_width"] for r in rows for c in r["comparisons"].values()])
    d_search = T.pooled_rms([r["refit_sd"] for r in rows if np.isfinite(r["refit_sd"])])
    return {"setting": setting, "plan": plan, "p": margin, "delta_eval": d_eval, "delta_search": d_search,
            "delta_search_fraction_of_p": d_search / margin if margin else float("nan"),
            "resolution_ok": bool(d_eval <= margin / 2 and d_search <= margin / 2), "target_brains": rows}


def asdict_scfg(scfg: S.SearchConfig) -> dict:
    return {k: getattr(scfg, k) for k in scfg.__dataclass_fields__}


def _calibrators():
    """D303's KT and KTM winners and D304's KTS winners at T = 5, 10, 20, from the committed records."""
    mem = json.loads((DEVREC / "memoryless-check.json").read_text(encoding="utf-8"))
    slow = json.loads((DEVREC / "slow-memory-check.json").read_text(encoding="utf-8"))
    out = {"KT": KT(**mem["KT_check"]["params"]),
           "KTM": KT(fall_turn=mem["KTM_check"]["fall_turn"], **mem["KTM_check"]["params"])}
    for T_ in ("5.0", "10.0", "20.0"):
        p = dict(slow["by_T"][T_]["params"])
        out[f"KTS T={int(float(T_))}"] = KTS(float(T_), **p)
    return out


def stage_probe(args, dv, ck):
    con, iface, cfg = configured()
    ws, pids = dev()["world_seed"], ids("probe")
    Ls = dev()["probe"]["L"]
    out = {"scripted": {}, "evolved": {}}
    with acct.category("probe"):
        for name, pol in _calibrators().items():
            row = {}
            for L in [None] + Ls:
                b = scripted(iface, pol, cfg, device=dv, n=con.n)
                brain = b if L is None else ReplayBrain(b, L=L)
                ck.check()
                row["plain" if L is None else f"L={L}"] = _ints(rollout_brain(cfg, iface, brain, pids, ws, dv).score[0])
            out["scripted"][name] = row
        brains = [("selector", champion(0, "evolve-intact", con, cfg)), ("MIP", champion(1, "evolve-intact", con, cfg))]
        for k, x in enumerate(read("panel")["targets"]):
            brains.append((f"NIP/{con.names[x]}", champion(10 + k, "evolve-nip", con, cfg)))
        for name, g in brains:
            g = EV.moved(g, dv)
            row = {}
            for L in [None] + Ls:
                brain = Brain(g) if L is None else ReplayBrain(Brain(g), L=L)
                ck.check()
                row["plain" if L is None else f"L={L}"] = _ints(rollout_brain(cfg, iface, brain, pids, ws, dv).score[0])
            ck.check()
            ctl = rollout_brain(cfg, iface, ReplayBrain(Brain(g), L=dev()["probe"]["control_L"], window=None), pids, ws,
                                dv)
            row["full_replay_equals_plain"] = bool(np.array_equal(ctl.score[0], np.asarray(row["plain"])))
            tau = g.tau[0].cpu().numpy()
            row["tau_quantiles"] = np.quantile(tau, [0.1, 0.5, 0.9]).round(3).tolist()
            out["evolved"][name] = row
    return out


def stage_report(args, dv, ck):
    """No simulation: measured throughputs, resolution, and the formal design projected at them (DESIGN.md §10)."""
    acct.write_aggregate(out_dir() / "compute", out_dir() / "compute.json")
    comp = json.loads((out_dir() / "compute.json").read_text(encoding="utf-8"))
    rates = {}
    for k, v in comp["categories"].items():
        if v.get("seconds") and v.get("worlds_built"):
            rates[k] = {"worlds": v["worlds_built"], "seconds": v["seconds"],
                        "per_second": v["worlds_built"] / v["seconds"]}
    full = read("full")
    spent = comp["totals"]["seconds_timed"] / 3600
    evo_rate = rates.get("selection", {}).get("per_second", 420.0)
    search_rate = rates.get("search", {}).get("per_second", 420.0)
    final_rate = rates.get("final", {}).get("per_second", 420.0)
    probe_rate = rates.get("probe", {}).get("per_second", 420.0)

    def projection(random_refits=5, free=5, worlds=16):
        per_search = 100 * 4 * 9 * worlds
        tb = (3 + random_refits + free) * per_search
        hours = {
            "N2 target-brains": 60 * tb / search_rate / 3600,
            "N2 evolutions": 38 * 266_496 / evo_rate / 3600,
            "N2 final evaluations": 1.80e6 / final_rate / 3600,
            "N2 scan and selection check": 0.40e6 / final_rate / 3600,
            "N2 probes": 1.09e6 / probe_rate / 3600,
            "pilot-check": (2 * 8 * tb / search_rate + 2 * 8 * 266_496 / evo_rate
                            + (0.46e6 + 0.25e6 + 0.02e6) / final_rate + 0.34e6 / probe_rate) / 3600,
            "scripted re-measurement and calibration": 0.20e6 / probe_rate / 3600}
        return {"random_refits": random_refits, "free": free, "worlds": worlds, "hours": hours,
                "total": sum(hours.values())}

    remaining = dev()["experiment_cap_gpu_hours"] - dev()["charged_before_hours"] - spent
    options = [projection(), projection(random_refits=3), projection(random_refits=3, free=4)]
    fits = [o for o in options if o["total"] <= remaining]
    plan = fits[0] if fits else None
    w32 = projection(worlds=32)
    return {"rates": rates, "pilot_dev_hours": spent, "remaining_hours": remaining, "projections": options,
            "plan": plan, "cut": None if plan is None else {(5, 5): "none", (3, 5): "random refits 5 -> 3",
                                                             (3, 4): "and free searches 5 -> 4"}[
                (plan["random_refits"], plan["free"])],
            "search_worlds_32": {"projection": w32, "allowed": bool(remaining - w32["total"] >= 8.0)},
            "delta_eval": full["delta_eval"], "delta_search": full["delta_search"], "p": full["p"],
            "delta_search_fraction_of_p": full["delta_search_fraction_of_p"], "setting": full["setting"]}


def stage_family2(args, dv, ck):
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
    doc = {"stage": stage, "smoke": SMOKE, "provenance": prov, "dev": dev(), "rerun_reason": args.reason,
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        with acct.recorded(out_dir() / "compute", out_dir() / "compute.json", default=DEFAULT_CATEGORY[stage],
                           experiment="03a", stage=stage, script="scripts/e03a.py"):
            doc.update(FUNCS[stage](args, dv, ck))
        doc["status"] = "completed"
    except BaseException as e:  # noqa: BLE001  (recorded, then re-raised)
        doc["status"], doc["error"] = "failed", f"{type(e).__name__}: {e}"
        raise
    finally:
        doc["seconds"] = time.time() - t0
        reg.write_json(path, doc, atomic=True)
    return doc


def main(argv=None):
    global SMOKE
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=STAGES)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--reason")
    args = ap.parse_args(argv)
    SMOKE = args.smoke
    doc = run_stage(args)
    print(f"{args.stage}: {doc['status']} in {doc['seconds']:.0f} s -> {rec_path(args.stage)}")
    return doc


if __name__ == "__main__":
    main()
