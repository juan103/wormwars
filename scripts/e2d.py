"""E2d: diagnosing Task N after E2's floor fired (experiments/E2d-taskn-diagnosis/PLAN.md, v4).

    python scripts/e2d.py project          # time every new composition; writes projection.json
    python scripts/e2d.py probe            # Part B: stereo probes of E2's and 04a's champions; the budget reading
    python scripts/e2d.py siblings         # Part C0: ranking among siblings and antithetic pairs
    python scripts/e2d.py replay           # E2's GA and ES, generations 0-25, twice; must match E2's hashes
    python scripts/e2d.py arm --arm c1     # Part C's arms, in order: c1, c2, c4, c3
    python scripts/e2d.py evaluate         # Part C's hold-out pass and readings
    python scripts/e2d.py <stage> --smoke  # tiny sizes, smoke ids, E2's and 04a's smoke records as sources
    python scripts/e2d.py <stage> --rerun --reason "..."

Exploratory: every measure and reading is fixed in the plan, and each is applied mechanically here.
The stage frame (markers with attempt numbers, the cap, reruns, not-completed records, retried atomic
writes) is E2's own, reused from `scripts/e2.py` with E2d's folders, stages and registered numbers.
Genome files stay local under `runs/e2d/` (D028).
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import importlib
import importlib.util
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e2.optimizers import decode, encode  # noqa: E402
from wormwars.evo.genomes import genome_hash, load_population  # noqa: E402
from wormwars.evo.rollout import rollout_brain  # noqa: E402

rollout_mod = importlib.import_module("wormwars.evo.rollout")

_spec = importlib.util.spec_from_file_location("e2_for_e2d", ROOT / "scripts" / "e2.py")
E = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(E)  # E2's stage frame, loops and guards, reconfigured below

EXP = ROOT / "experiments" / "E2d-taskn-diagnosis"
OUT = ROOT / "runs" / "e2d"
PLAN = "experiments/E2d-taskn-diagnosis/PLAN.md"
E2_EXP, E2_OUT = ROOT / "experiments" / "E2-optimizer-screen", ROOT / "runs" / "e2"
E04A_EXP, E04A_OUT = ROOT / "experiments" / "04a-navigation-primitive", ROOT / "runs" / "e04a"
SOURCE_RECORDS = ["experiments/E2-optimizer-screen/train-ga.json", "experiments/E2-optimizer-screen/train-random.json",
                  "experiments/E2-optimizer-screen/train-es.json", "experiments/E2-optimizer-screen/extension.json",
                  "experiments/E2-optimizer-screen/pilot-2.json",
                  "experiments/04a-navigation-primitive/train-A.json", "experiments/04a-navigation-primitive/train-B.json"]
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PLAN, *E.E1_INPUTS, *SOURCE_RECORDS]
SMOKE = False

REGISTERED = {
    # E2's task and GA, unchanged (the stage frame reads these keys)
    "world_seed": E.REGISTERED["world_seed"], "task_sigma": E.REGISTERED["task_sigma"],
    "ga": copy.deepcopy(E.REGISTERED["ga"]), "checkpoint_every": 25, "rerun_kill_tail_seconds": 900,
    "cap_gpu_hours": 7.0, "training_cap_hours": 6.5, "reserve_hours": 0.5,
    "ids": {"holdout": {"first": 992_700_000, "worlds": 1024}, "probe": {"first": 992_800_000, "worlds": 256}},
    # Part C: one change each from E2, paired with E2's runs (E2's seeds, training range and validation ids)
    "arms": {"c1": {"method": "ga", "worlds": 32, "mutation_scale": 1.0, "generations": 250},
             "c2": {"method": "ga", "worlds": 8, "mutation_scale": 0.5, "generations": 1000},
             "c4": {"method": "ga", "worlds": 32, "mutation_scale": 0.5, "generations": 250},
             "c3": {"method": "es", "worlds": 8, "sigma": 0.25, "lr": 0.15, "generations": 623}},
    "arm_order": ["c1", "c2", "c4", "c3"],
    "matched_generations": [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 999],
    "probes": ["real", "mean", "swapped"],
    "references": {"S-const": "E1's frozen parameters", "S-const k=4": {"k": 4.0, "speed": 1.0, "turn": 0.1},
                   "M-avg": "E1's frozen parameters"},
    "checks": {"stereo_lower_bound": 0.5, "m_avg_mean_tolerance": 0.05},
    "c0": {"children": 64, "scales": [1.0, 0.5, 0.25], "pairs": 32, "sigmas": [0.5, 0.25],
           "seed_ga": 1_131_000, "seed_es": 1_131_100, "draws": 400, "k": 8, "top": 8},
    "analysis": {"resamples": 10_000, "seed": 0, "bins": [[0.05, 0.15], [0.15, 0.30], [0.30, 0.60]], "min_pairs": 30},
    "readings": {"uses": 0.5, "negligible": 0.25, "set_share": 0.75, "set_uses_max": 2, "band": [1.90, 2.50],
                 "arm_gain": 0.3, "plateau_score": 2.5, "plateau_count": 4, "budget_gain": 0.2, "failure": 1.0,
                 "drop_run": 2, "noise_material": 0.8},
    "replay": {"repeats": 2},
    "projection": {"seed_base": 1_139_100, "limit_hours": 6.2, "generations_timed": 6},
}
SMOKE_SEED_BASE = 1_138_000
STAGES = ["project", "probe", "siblings", "replay", "arm-c1", "arm-c2", "arm-c4", "arm-c3", "evaluate"]
RECORD = {"project": "projection", "probe": "part-b", "siblings": "part-c0", "replay": "replay",
          "arm-c1": "arm-c1", "arm-c2": "arm-c2", "arm-c4": "arm-c4", "arm-c3": "arm-c3", "evaluate": "evaluation"}
WHAT = {"project": "the projection", "probe": "Part B", "siblings": "Part C0", "replay": "the controls' replay",
        "arm-c1": "arm C1", "arm-c2": "arm C2", "arm-c4": "arm C4", "arm-c3": "arm C3", "evaluate": "Part C's hold-out pass"}


def configure() -> None:
    """Point E2's stage frame at E2d's folders, stages and registered numbers."""
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, OUT, GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E2d: not completed (the run stopped)",
                  "cap": "E2d: not completed (the registered cap was reached)"}
    E.RECORD.update(RECORD)
    E.WHAT.update(WHAT)


configure()


# ============================================================================== the registered rules

def _boot_means(x: np.ndarray, resamples: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(resamples, len(x)))
    return x[idx].mean(axis=1)


def world_ci(a: np.ndarray, b: np.ndarray) -> dict:
    """Paired percentile bootstrap over worlds of mean(a - b), with a two-sided 95% interval."""
    A = REGISTERED["analysis"]
    d = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    m = _boot_means(d, A["resamples"], A["seed"])
    return {"mean": float(d.mean()), "lo95": float(np.percentile(m, 2.5)), "hi95": float(np.percentile(m, 97.5))}


def sign_flip_p(d: np.ndarray) -> float:
    """Exact two-sided sign-flip test over the runs: the share of all sign patterns whose mean is at
    least as far from 0 as the observed one."""
    d = np.asarray(d, dtype=np.float64)
    obs = abs(d.mean())
    means = [abs((d * np.array(s)).mean()) for s in itertools.product((1, -1), repeat=len(d))]
    return float(np.mean([m >= obs - 1e-12 for m in means]))


def run_summary(d: np.ndarray) -> dict:
    """Paired differences over runs: mean, median, runs improved, a 90% percentile bootstrap interval
    over runs, and the sign-flip p-value beside it (the interval decides)."""
    A = REGISTERED["analysis"]
    d = np.asarray(d, dtype=np.float64)
    m = _boot_means(d, A["resamples"], A["seed"])
    return {"n": int(len(d)), "per_run": d.tolist(), "mean": float(d.mean()), "median": float(np.median(d)),
            "improved": int((d > 0).sum()), "lo90": float(np.percentile(m, 5)), "hi90": float(np.percentile(m, 95)),
            "sign_flip_p": sign_flip_p(d)}


def classify(mean_ci: dict, swapped_ci: dict) -> str:
    """Part B's classes: 'uses' (both 95% lower bounds above 0.5), 'no material benefit' (both
    intervals inside (-0.25, 0.25), two-sided), else 'unclear'."""
    R = REGISTERED["readings"]
    if mean_ci["lo95"] > R["uses"] and swapped_ci["lo95"] > R["uses"]:
        return "uses"
    inside = lambda c: c["lo95"] > -R["negligible"] and c["hi95"] < R["negligible"]  # noqa: E731
    if inside(mean_ci) and inside(swapped_ci):
        return "no material benefit"
    return "unclear"


def set_reading(classes: list[str]) -> str:
    R = REGISTERED["readings"]
    uses = sum(c == "uses" for c in classes)
    if uses >= R["set_uses_max"] + 1:
        return "stereo use present"
    if sum(c == "no material benefit" for c in classes) >= R["set_share"] * len(classes) and uses <= R["set_uses_max"]:
        return "non-stereo"
    return "mixed"


def plateau_reading(sets: dict) -> bool:
    """`sets`: {name: (reading, median real-probe score)} for the read sets."""
    lo, hi = REGISTERED["readings"]["band"]
    return bool(sets) and all(r == "non-stereo" and lo <= med <= hi for r, med in sets.values())


def budget_reading(gains: np.ndarray) -> dict:
    s = run_summary(gains)
    ok = s["mean"] >= REGISTERED["readings"]["budget_gain"] and s["lo90"] > 0
    return {**s, "reading": "budget-limited" if ok else "not budget-limited"}


def _drop(d: np.ndarray) -> np.ndarray:
    r = REGISTERED["readings"]["drop_run"]
    return np.delete(d, r) if len(d) > r else d


def arm_reading(d: np.ndarray) -> dict:
    """Part C's reading over all runs and over the runs without run 2 (both must agree)."""
    g = REGISTERED["readings"]["arm_gain"]
    s8, s7 = run_summary(d), run_summary(_drop(np.asarray(d)))
    up = lambda s: s["mean"] >= g and s["lo90"] > 0  # noqa: E731
    down = lambda s: s["mean"] <= -g and s["hi90"] < 0  # noqa: E731
    if up(s8):
        reading = "supports" if up(s7) else "supports, carried by run 2"
    elif down(s8):
        reading = "harmful" if down(s7) else "harmful, carried by run 2"
    else:
        reading = "inconclusive"
    return {"reading": reading, "all_runs": s8, "without_run_2": s7}


def leaves_plateau(classes: list[str], scores: list[float]) -> bool:
    R = REGISTERED["readings"]
    n = sum(c == "uses" or s >= R["plateau_score"] for c, s in zip(classes, scores))
    return n >= R["plateau_count"]


def interaction(c4, c1, c2p, gap) -> dict:
    d = (np.asarray(c4) - np.asarray(c1)) - (np.asarray(c2p) - np.asarray(gap))
    s8, s7 = run_summary(d), run_summary(_drop(d))
    excl = lambda s: s["lo90"] > 0 or s["hi90"] < 0  # noqa: E731
    return {"all_runs": s8, "without_run_2": s7, "claimed": bool(excl(s8) and excl(s7))}


def top_k(v: np.ndarray, k: int) -> np.ndarray:
    """The k highest, ties to the lower index (C0's own convention)."""
    v = np.asarray(v, dtype=np.float64)
    return np.lexsort((np.arange(len(v)), -v))[:k]


def draws(n_worlds: int) -> np.ndarray:
    C = REGISTERED["c0"]
    rng = np.random.default_rng(REGISTERED["analysis"]["seed"])
    return np.stack([rng.choice(n_worlds, size=C["k"], replace=False) for _ in range(C["draws"])])


def _pair_rates(counts: np.ndarray, dr: np.ndarray) -> list[dict]:
    """Per pair of rows: the full-world difference, and over the draws the share ranked like the
    complement (correct), tied, and the draws excluded because the complement shows no difference."""
    counts = np.asarray(counts, dtype=np.float64)
    W, k = counts.shape[1], dr.shape[1]
    full = counts.mean(1)
    tot = counts.sum(1)
    s8 = np.stack([counts[:, d].sum(1) for d in dr]) / k  # [draws, n]
    sc = (tot[None, :] - s8 * k) / (W - k)
    out = []
    for i, j in itertools.combinations(range(counts.shape[0]), 2):
        dc, d8 = sc[:, i] - sc[:, j], s8[:, i] - s8[:, j]
        keep = dc != 0
        n = int(keep.sum())
        rec = {"gap": float(abs(full[i] - full[j])), "excluded": int((~keep).sum()), "scored": n > 0}
        if n:
            rec["correct"] = float(((np.sign(d8) == np.sign(dc)) & (d8 != 0))[keep].mean())
            rec["tied"] = float((d8 == 0)[keep].mean())
        out.append(rec)
    return out


def _bin_rows(pairs: list[dict], bins) -> list[dict]:
    rows = []
    for lo, hi in bins:
        inb = [p for p in pairs if lo <= p["gap"] < hi]
        sc = [p for p in inb if p["scored"]]
        row = {"gap": [lo, hi], "pairs": len(inb), "scored_pairs": len(sc),
               "excluded_draws": int(sum(p["excluded"] for p in inb))}
        if sc:
            row["correct"] = float(np.mean([p["correct"] for p in sc]))
            row["tied"] = float(np.mean([p["tied"] for p in sc]))
            row["ties_half"] = row["correct"] + row["tied"] / 2
        row["drawn"] = len(inb) >= REGISTERED["analysis"]["min_pairs"]
        rows.append(row)
    return rows


def sibling_ranking(counts: np.ndarray, dr: np.ndarray, bins=None) -> dict:
    bins = bins or REGISTERED["analysis"]["bins"]
    pairs = _pair_rates(counts, dr)
    return {"pairs": pairs, "rows": _bin_rows(pairs, bins)}


def children(parent: Genome, mcfg, scale: float, n: int, seed: int) -> Genome:
    """n children of a one-strain parent at `scale` × 02's mutation, the generator reset to `seed`, so
    every scale takes the same draws."""
    kids = parent.select([0] * n)
    m = dataclasses.replace(mcfg, w_sigma=mcfg.w_sigma * scale, g_sigma=mcfg.g_sigma * scale,
                            tau_sigma=mcfg.tau_sigma * scale, bias_sigma=mcfg.bias_sigma * scale)
    return kids.mutate(m, generator=torch.Generator(device=parent.device).manual_seed(int(seed)))


def es_pairs(template: Genome, sigma: float, pairs: int, seed: int) -> Genome:
    """Antithetic candidates around a champion's encoding, mean ± σε, with the noise reset to `seed`."""
    z = encode(template)[0].detach().cpu().numpy().astype(np.float64)
    eps = np.random.default_rng(int(seed)).standard_normal((pairs, z.size))
    c = np.empty((2 * pairs, z.size))
    c[0::2], c[1::2] = z + sigma * eps, z - sigma * eps
    return decode(torch.as_tensor(c, dtype=template.w.dtype, device=template.device), template)


# ============================================================================== sources and ids

def read(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def e2_record(name: str) -> dict:
    return read(E2_EXP / f"{name}.json")


def e2_runs() -> list[EV.RunSpec]:
    return [EV.RunSpec(**r["spec"]) for r in e2_record("train-ga")["records"]]


def e2_ids() -> tuple[dict, np.ndarray]:
    t = e2_record("train-ga")
    base, last = t["training_ids"]
    v = t["validation_worlds"]
    return {"base": base, "span": last - base + 1}, np.arange(v["first"], v["first"] + v["count"])


def ids(key: str) -> np.ndarray:
    v = REGISTERED["ids"][key]
    return np.arange(v["first"], v["first"] + v["worlds"])


def _load(path: Path, index: int, sha: str, spec, cfg) -> Genome:
    g, _ = load_population(path, spec, cfg.brain)
    want = dataclasses.asdict(cfg.brain)
    if dataclasses.asdict(g.cfg) != want:
        raise SystemExit(f"{path.name} loads with another brain configuration")
    g = g.select([index])
    if genome_hash(g, 0) != sha:
        raise SystemExit(f"{path.name} checkpoint {index} does not match its committed hash")
    return g


def e2_champions(spec, cfg) -> dict:
    """{label: (genome, sha)} for E2's champions, each checked against its committed hash."""
    out = {}
    for m in ("ga", "es", "random"):
        for r in e2_record(f"train-{m}")["records"]:
            c, run = r["champion"], r["spec"]["run"]
            out[f"e2 {m} run{run:02d}"] = (_load(E2_OUT / "genomes" / f"{m}-run{run:02d}-candidates.npz",
                                                 c["checkpoint"], c["sha256"], spec, cfg), c["sha256"])
    for c in e2_record("extension")["champions_over_both"]:
        prefix = "es" if c["source"] == "formal" else "extension"
        out[f"e2 extension run{c['run']:02d}"] = (_load(E2_OUT / "genomes" / f"{prefix}-run{c['run']:02d}-candidates.npz",
                                                        c["checkpoint"], c["sha256"], spec, cfg), c["sha256"])
    return out


def e04a_champions(spec, cfg) -> dict:
    out = {}
    for b in ("A", "B"):
        path = E04A_EXP / f"train-{b}.json"
        if not path.exists():
            continue
        for r in read(path)["records"]:
            run, c = r["spec"]["run"], r["champion"]
            out[f"04a run{run:02d}"] = (_load(E04A_OUT / "genomes" / f"run{run:02d}-candidates.npz", c["checkpoint"],
                                               c["sha256"], spec, cfg), c["sha256"], r["spec"]["shaping"] > 0)
    return out


def references() -> dict:
    tuned = read(E.E1_FREEZE)["tuned"]
    return {"S-const": ("S-const", tuned["S-const"]["params"]),
            "S-const k=4": ("S-const", REGISTERED["references"]["S-const k=4"]),
            "M-avg": ("M-avg", tuned["M-avg"]["params"])}


# ============================================================================== rollouts

def neural(cfg, iface, g: Genome, world_ids, probe: str, device, cap) -> np.ndarray:
    c = cfg.copy()
    c.world.food_probe = probe
    cap.check()
    with acct.category("final"):
        r = rollout_mod.rollout(c, iface, EV.moved(g, device), world_ids, REGISTERED["world_seed"], device,
                                chunk_worlds=g.n_strains * len(world_ids))
    return np.asarray(r.score)


def scripted(cfg, iface, maker: str, params: dict, world_ids, probe: str, device, cap) -> np.ndarray:
    c = cfg.copy()
    c.world.food_probe = probe
    brain = E.E1.C.scripted(iface, E.E1.MAKERS[maker](**params), c, device=device)
    cap.check()
    with acct.category("final"):
        r = rollout_brain(c, iface, brain, world_ids, REGISTERED["world_seed"], device)
    return np.asarray(r.score[0])


def arm_config(arm: str):
    a, cfg = REGISTERED["arms"][arm], E.task_config()
    cfg.evo.worlds_per_strain = a["worlds"]
    s = a.get("mutation_scale", 1.0)
    for k in ("w_sigma", "g_sigma", "tau_sigma", "bias_sigma"):
        setattr(cfg.mutation, k, getattr(cfg.mutation, k) * s)
    return cfg


# ============================================================================== guards

def require(args, prov, stage: str, final_ok: bool = False) -> dict:
    """An earlier stage: completed; or, with `final_ok`, final and not completed (stopped with its
    rerun used or refused, or skipped); committed (formal); the same code and environment."""
    path = E.record_path(stage)
    if not path.exists():
        return E.require_earlier(args, prov, stage, final_ok)  # its messages for a missing or killed stage
    rec = read(path)
    final = rec.get("outcome") == E.OUTCOMES["skipped"] or (
        rec.get("outcome") == E.OUTCOMES["stopped"] and (rec.get("final") or E.rerun_state(stage) == "used"))
    if rec.get("outcome") != "completed" and not (final_ok and final):
        return E.require_earlier(args, prov, stage, final_ok)
    if E.formal(args):
        if not args.smoke:
            E.require_committed(path)
        reg.require_same_code(rec["provenance_at_start"]["git_commit"], GUARDED)
        reg.require_same_env(rec["provenance_at_start"], prov)
    return rec


def projected_hours(proj: dict, arm: str) -> float:
    p, r = proj["plan"][f"arm-{arm}"], proj["rates"][proj["plan"][f"arm-{arm}"]["shape"]]
    return (p["generations"] * r["seconds_per_generation"] + p["checkpoints"] * r["seconds_per_checkpoint"]) / 3600


def admit(args, prov, stage: str, hours: float) -> None:
    """Every training stage, a rerun included, starts only if the cap's remainder covers its projected
    time plus the reserve. A first attempt is skipped; a refused rerun is final and not completed."""
    need = hours + REGISTERED["reserve_hours"]
    left = REGISTERED["cap_gpu_hours"] - E.clock().spent_hours()
    if need <= left:
        return
    note = {"hours_needed": need, "hours_left": left}
    path = E.record_path(stage)
    if args.rerun:
        rec = read(path) if path.exists() else {"stage": stage, "outcome": E.OUTCOMES["stopped"],
                                                "provenance_at_start": prov}
        rec.update(final=True, rerun_refused=note)
        E.write_atomic(path, rec)
        raise SystemExit(f"{WHAT[stage]}'s rerun is not admitted ({need:.2f} h needed, {left:.2f} h left): final, "
                         "not completed")
    E.write_atomic(path, {"stage": stage, "outcome": E.OUTCOMES["skipped"], "final": True, **note,
                          "provenance_at_start": prov, "registered": REGISTERED})
    raise SystemExit(f"{WHAT[stage]} is skipped: {need:.2f} h needed with the reserve, {left:.2f} h left")


def training_clock() -> reg.CapClock:
    """The hard stop: training runs under the cap less the reserve."""
    if (OUT / "compute").exists():
        acct.write_aggregate(OUT / "compute", OUT / "compute.json")
    return reg.CapClock(REGISTERED["training_cap_hours"], OUT / "compute.json")


# ============================================================================== the projection

def plan_counts(n_b: int, n_eval: int) -> dict:
    every, arms = REGISTERED["checkpoint_every"], REGISTERED["arms"]
    nck = lambda g: E.n_checkpoints(0, g, every)  # noqa: E731
    rg = replay_generations()
    plan = {"replay": {"parts": [("ga8", rg, nck(rg)), ("es8", rg, nck(rg))], "repeats": REGISTERED["replay"]["repeats"]}}
    for a, s in arms.items():
        base = REGISTERED["ga"]["worlds_per_strain"]
        shape = "es8" if s["method"] == "es" else ("ga32" if s["worlds"] > base else "ga8")
        plan[f"arm-{a}"] = {"shape": shape, "generations": s["generations"], "checkpoints": nck(s["generations"])}
    C = REGISTERED["c0"]
    plan["siblings"] = {"batches": len(e2_runs()) * (len(C["scales"]) + len(C["sigmas"]))}
    plan["probe"] = {"arms": n_b}
    plan["evaluate"] = {"arms": n_eval}
    return plan


def replay_generations() -> int:
    return int(e2_record("train-ga")["registered"]["checkpoint_every"]) + 1


def projection_verdict(rates: dict, plan: dict) -> dict:
    h = 0.0
    for part, g, c in plan["replay"]["parts"]:
        h += plan["replay"]["repeats"] * (g * rates[part]["seconds_per_generation"] + c * rates[part]["seconds_per_checkpoint"])
    for a in REGISTERED["arms"]:
        p = plan[f"arm-{a}"]
        h += p["generations"] * rates[p["shape"]]["seconds_per_generation"] + p["checkpoints"] * rates[p["shape"]]["seconds_per_checkpoint"]
    h += plan["siblings"]["batches"] * rates["c0"]["seconds_per_batch"]
    h += (plan["probe"]["arms"] + plan["evaluate"]["arms"]) * rates["b"]["seconds_per_arm"]
    hours = h / 3600
    lim = REGISTERED["projection"]["limit_hours"]
    return {"plan": plan, "rates": rates, "projected_hours": hours, "limit_hours": lim, "within_limit": hours <= lim}


def cmd_project(args):
    def body(ctx):
        P, cfg0 = REGISTERED["projection"], ctx.cfg
        n = P["generations_timed"]
        val = E.SMOKE_IDS[5000:5000 + 256] if not SMOKE else E.SMOKE_IDS[5000:5004]
        runs = [EV.RunSpec(i, P["seed_base"] + i, 0.0) for i in range(len(e2_runs()))]
        rates = {}
        for shape, method, worlds in (("ga8", "ga", REGISTERED["ga"]["worlds_per_strain"]),
                                      ("ga32", "ga", REGISTERED["arms"]["c1"]["worlds"]), ("es8", "es", None)):
            cfg = cfg0.copy()
            if worlds:
                cfg.evo.worlds_per_strain = worlds
            with acct.category("measure"):
                recs, _ = E.run_method(method, cfg, ctx.iface, ctx.spec, runs, generations=n, checkpoint_every=n - 1,
                                       validation_ids=val, world_seed=REGISTERED["world_seed"], id_base=0, id_span=5000,
                                       device=ctx.args.device, check=ctx.cap.check, sigma=0.5, lr=0.15)
            s = [x["batch_seconds"] for x in recs[0].log]
            per = float(np.median(s[1:-1])) if len(s) > 2 else float(s[-1])
            rates[shape] = {"seconds_per_generation": per, "seconds_per_checkpoint": max(0.0, float(s[-1]) - per),
                            "batch_seconds": s}
        g = Genome.random(ctx.spec, cfg0.brain, REGISTERED["c0"]["children"] + 1,
                          generator=torch.Generator().manual_seed(P["seed_base"]))
        t = []
        for _ in range(2):
            t0 = time.perf_counter()
            neural(cfg0, ctx.iface, g, E.SMOKE_IDS[:len(ids("probe"))], "real", ctx.args.device, ctx.cap)
            t.append(time.perf_counter() - t0)
        rates["c0"] = {"seconds_per_batch": t[-1]}
        t = []
        for _ in range(2):
            t0 = time.perf_counter()
            neural(cfg0, ctx.iface, g.select([0]), E.SMOKE_IDS[:len(ids("holdout"))], "real", ctx.args.device, ctx.cap)
            t.append(time.perf_counter() - t0)
        rates["b"] = {"seconds_per_arm": t[-1]}
        n_b = (len(e2_record("train-ga")["records"]) * 4 + 16 + 3) * len(REGISTERED["probes"])
        n_eval = (len(e2_runs()) * (len(REGISTERED["arms"]) + 2)) * len(REGISTERED["probes"])
        v = projection_verdict(rates, plan_counts(n_b, n_eval))
        return {"seeds_base": P["seed_base"], **v}

    doc = E.run_stage(args, "project", lambda a, p: {}, body)
    print(f"projected {doc['projected_hours']:.2f} h (limit {doc['limit_hours']} h): "
          f"{'within' if doc['within_limit'] else 'OVER: nothing further starts'}")


def require_projection(args, prov) -> dict:
    p = require(args, prov, "project")
    if not p.get("within_limit"):
        raise SystemExit("the projection is over its limit: nothing further starts without a reviewed amendment")
    return p


# ============================================================================== Part B

def cmd_probe(args):
    def body(ctx):
        cfg, dev, hold = ctx.cfg, ctx.args.device, ids("holdout")
        genomes = {k: v[:2] for k, v in e2_champions(ctx.spec, cfg).items()}
        shaped = {}
        for k, v in e04a_champions(ctx.spec, cfg).items():
            genomes[k] = v[:2]
            shaped[k] = v[2]
        counts, done = {}, {}
        ctx.salvage = lambda: {"arms_completed": list(counts),
                               "per_world_counts": {k: v.astype(int).tolist() for k, v in counts.items()}}
        keep = lambda: E.write_atomic(E.partial_path("probe"), {**ctx.doc, **ctx.salvage()})  # noqa: E731
        for label, (g, sha) in genomes.items():
            for p in REGISTERED["probes"]:
                key = f"{label} {p}"
                if (sha, p) in done:  # the same genome in two sets: evaluated once
                    counts[key] = counts[done[(sha, p)]]
                    continue
                counts[key] = neural(cfg, ctx.iface, g, hold, p, dev, ctx.cap)[0]
                done[(sha, p)] = key
                keep()
        for name, (maker, params) in references().items():
            for p in REGISTERED["probes"]:
                counts[f"ref {name} {p}"] = scripted(cfg, ctx.iface, maker, params, hold, p, dev, ctx.cap)
                keep()
        ctx.doc.update(worlds=E.id_record(hold), champion_sha256={k: v[1] for k, v in genomes.items()})
        return analyse_b(counts, list(genomes), shaped)

    doc = E.run_stage(args, "probe", require_projection, body)
    print(doc["checks"]["passed"], {k: v["reading"] for k, v in doc["sets"].items()}, doc["budget"]["reading"])


def contrasts(counts: dict, label: str) -> dict:
    real = counts[f"{label} real"]
    m, s = world_ci(real, counts[f"{label} mean"]), world_ci(real, counts[f"{label} swapped"])
    return {"real": float(real.mean()), "mean": float(counts[f"{label} mean"].mean()),
            "swapped": float(counts[f"{label} swapped"].mean()), "real_minus_mean": m, "real_minus_swapped": s,
            "class": classify(m, s)}


def analyse_b(counts: dict, labels: list[str], shaped: dict) -> dict:
    C = REGISTERED["checks"]
    per = {lab: contrasts(counts, lab) for lab in labels}
    refs = {name: contrasts(counts, f"ref {name}") for name in references()}
    checks = {"S-const": refs["S-const"]["real_minus_mean"]["lo95"] > C["stereo_lower_bound"]
              and refs["S-const"]["real_minus_swapped"]["lo95"] > C["stereo_lower_bound"],
              "S-const k=4": refs["S-const k=4"]["real_minus_mean"]["lo95"] > C["stereo_lower_bound"]
              and refs["S-const k=4"]["real_minus_swapped"]["lo95"] > C["stereo_lower_bound"],
              "M-avg swapped identical": bool(np.array_equal(counts["ref M-avg real"], counts["ref M-avg swapped"])),
              "M-avg mean within tolerance": abs(refs["M-avg"]["real"] - refs["M-avg"]["mean"]) <= C["m_avg_mean_tolerance"]}
    checks["passed"] = all(checks.values())
    groups = {"e2 ga": [k for k in labels if k.startswith("e2 ga ")], "e2 es": [k for k in labels if k.startswith("e2 es ")],
              "e2 extension": [k for k in labels if k.startswith("e2 extension ")],
              "e2 random": [k for k in labels if k.startswith("e2 random ")],
              "04a shaped": [k for k in labels if k.startswith("04a") and shaped.get(k)],
              "04a unshaped": [k for k in labels if k.startswith("04a") and not shaped.get(k)]}
    read_sets = ("e2 ga", "e2 es", "e2 extension", "04a shaped", "04a unshaped")
    sets = {}
    for name, labs in groups.items():
        if not labs:
            continue
        cls = [per[k]["class"] for k in labs]
        sets[name] = {"genomes": labs, "classes": {c: cls.count(c) for c in ("uses", "no material benefit", "unclear")},
                      "median_real": float(np.median([per[k]["real"] for k in labs])), "read": name in read_sets,
                      "reading": set_reading(cls) if name in read_sets else "classified, not read"}
    plateau = None
    if checks["passed"]:
        plateau = plateau_reading({n: (s["reading"], s["median_real"]) for n, s in sets.items() if s["read"]})
    runs = sorted(int(k.split("run")[1]) for k in groups["e2 es"])
    gains = np.array([counts[f"e2 extension run{r:02d} real"].mean() - counts[f"e2 es run{r:02d} real"].mean() for r in runs])
    return {"checks": checks, "references": refs, "genomes": per, "sets": sets,
            "non_stereo_plateau": plateau if checks["passed"] else "not drawn (a check failed)",
            "budget": {**budget_reading(gains), "runs": runs},
            "per_world_counts": {k: np.asarray(v).astype(int).tolist() for k, v in counts.items()}}


# ============================================================================== Part C0

def cmd_siblings(args):
    def body(ctx):
        cfg, dev, pw, C = ctx.cfg, ctx.args.device, ids("probe"), REGISTERED["c0"]
        champs = e2_champions(ctx.spec, cfg)
        batches = {}
        ctx.salvage = lambda: {"batches_completed": list(batches)}
        for r in [x.run for x in e2_runs()]:
            parent = EV.moved(champs[f"e2 ga run{r:02d}"][0], dev)
            for s in C["scales"]:
                kids = children(parent, cfg.mutation, s, C["children"], C["seed_ga"] + 10 * r)
                batches[f"ga run{r:02d} scale {s}"] = neural(cfg, ctx.iface, Genome.cat([parent, kids]), pw, "real", dev,
                                                             ctx.cap).astype(int)
                E.write_atomic(E.partial_path("siblings"), {**ctx.doc, "batches_completed": list(batches)})
            mean = EV.moved(champs[f"e2 es run{r:02d}"][0], dev)
            for sg in C["sigmas"]:
                cands = es_pairs(mean, sg, C["pairs"], C["seed_es"] + 10 * r)
                batches[f"es run{r:02d} sigma {sg}"] = neural(cfg, ctx.iface, Genome.cat([mean, cands]), pw, "real", dev,
                                                              ctx.cap).astype(int)
                E.write_atomic(E.partial_path("siblings"), {**ctx.doc, "batches_completed": list(batches)})
        ctx.doc.update(worlds=E.id_record(pw))
        return analyse_c0(batches)

    doc = E.run_stage(args, "siblings", lambda a, p: {"probe": require(a, p, "probe")}, body)
    print(doc["reading"])


def analyse_c0(batches: dict) -> dict:
    C, A = REGISTERED["c0"], REGISTERED["analysis"]
    any_batch = next(iter(batches.values()))
    dr = draws(any_batch.shape[1])
    W, k = any_batch.shape[1], dr.shape[1]
    ga, es = {}, {}
    for s in C["scales"]:
        pooled, per_champ, kids_stats, overlap = [], {}, [], []
        for key, b in batches.items():
            if not key.startswith("ga ") or not key.endswith(f"scale {s}"):
                continue
            parent, kids = b[0].astype(float), b[1:].astype(float)
            pm, km = parent.mean(), kids.mean(1)
            kids_stats.append({"parent": float(pm), "children_mean": float(km.mean()),
                               "share_under_half_parent": float((km < 0.5 * pm).mean()),
                               "share_zero": float((km == 0).mean())})
            pr = _pair_rates(kids, dr)
            pooled += pr
            per_champ[key.split(" scale")[0]] = _bin_rows(pr, A["bins"])
            tot = kids.sum(1)
            ov = []
            for d in dr:
                s8 = kids[:, d].sum(1) / k
                sc = (tot - kids[:, d].sum(1)) / (W - k)
                ov.append(len(set(top_k(s8, C["top"]).tolist()) & set(top_k(sc, C["top"]).tolist())) / C["top"])
            overlap.append(float(np.mean(ov)))
        ga[str(s)] = {"children": kids_stats, "pooled": _bin_rows(pooled, A["bins"]), "per_champion": per_champ,
                      "top8_overlap": overlap}
    for sg in C["sigmas"]:
        agree, tie, excl, se = [], [], 0, []
        for key, b in batches.items():
            if not key.startswith("es ") or not key.endswith(f"sigma {sg}"):
                continue
            cand = b[1:].astype(float)
            plus, minus = cand[0::2], cand[1::2]
            se.append(float((cand.std(1, ddof=1) / np.sqrt(W - k)).mean()))
            for d in dr:
                d8 = plus[:, d].mean(1) - minus[:, d].mean(1)
                dc = (plus.sum(1) - plus[:, d].sum(1) - minus.sum(1) + minus[:, d].sum(1)) / (W - k)
                keep = dc != 0
                excl += int((~keep).sum())
                agree += ((np.sign(d8) == np.sign(dc)) & (d8 != 0))[keep].tolist()
                tie += (d8 == 0)[keep].tolist()
        es[str(sg)] = {"sign_agreement": float(np.mean(agree)) if agree else None,
                       "tied": float(np.mean(tie)) if tie else None, "excluded_draws": excl,
                       "reference_se": float(np.mean(se)) if se else None, "note": "a proxy: the ES ranks all 32"}
    ref_se = []
    for key, b in batches.items():
        if key.startswith("ga "):
            ref_se.append(float((b[1:].std(1, ddof=1) / np.sqrt(W - k)).mean()))
    row = next(r for r in ga["1.0"]["pooled"] if r["gap"] == REGISTERED["analysis"]["bins"][1])
    if not row["drawn"] or "ties_half" not in row:
        reading = "not drawn (fewer than the minimum of distinct pairs)"
    else:
        reading = ("selection noise is material" if row["ties_half"] < REGISTERED["readings"]["noise_material"]
                   else "selection noise is not material by this rule")
    return {"ga": ga, "es": es, "reference_se_ga": float(np.mean(ref_se)) if ref_se else None, "reading": reading,
            "surrogate": "one parent's children, not E2's population; ES pair signs, not its rank update",
            "per_world_counts": {k: v.tolist() for k, v in batches.items()}}


# ============================================================================== the controls' replay

def cmd_replay(args):
    def body(ctx):
        runs, (train, val) = e2_runs(), e2_ids()
        G, every = replay_generations(), int(e2_record("train-ga")["registered"]["checkpoint_every"])
        sel = e2_record("pilot-2")["selected"]
        want = {m: [[c["sha256"] for c in r["checkpoints"][:2]] for r in e2_record(f"train-{m}")["records"]]
                for m in ("ga", "es")}
        got = []
        for rep in range(REGISTERED["replay"]["repeats"]):
            one = {}
            for m in ("ga", "es"):
                recs, _ = E.run_method(m, ctx.cfg, ctx.iface, ctx.spec, runs, generations=G, checkpoint_every=every,
                                       validation_ids=val, world_seed=REGISTERED["world_seed"], id_base=train["base"],
                                       id_span=train["span"], device=ctx.args.device, check=ctx.cap.check,
                                       category=acct.category, sigma=sel["sigma"], lr=sel["lr"])
                one[m] = [[c["sha256"] for c in r.checkpoints[:2]] for r in recs]
            got.append(one)
        agree = all(g == got[0] for g in got)
        match = all(g == want for g in got)
        diagnosis = ("reproduces E2" if match else "drift: the replays agree with each other, not with E2" if agree
                     else "nondeterminism: the replays disagree with each other")
        return {"generations": G, "replays": got, "e2": want, "replays_agree": agree, "matches_e2": match,
                "passed": bool(agree and match), "diagnosis": diagnosis}

    doc = E.run_stage(args, "replay", lambda a, p: {"siblings": require(a, p, "siblings")}, body)
    print(doc["diagnosis"])


def require_replay(args, prov) -> dict:
    r = require(args, prov, "replay")
    if not r.get("passed"):
        raise SystemExit(f"the controls' replay did not pass ({r.get('diagnosis')}): Part C does not start")
    return r


# ============================================================================== Part C's arms

def cmd_arm(args):
    arm, order = args.arm, REGISTERED["arm_order"]
    stage = f"arm-{arm}"

    def requires(a, prov):
        rp = require_replay(a, prov)
        i = order.index(arm)
        if i:
            require(a, prov, f"arm-{order[i - 1]}", final_ok=True)
        proj = require_projection(a, prov)
        admit(a, prov, stage, projected_hours(proj, arm))
        return {"replay": rp}

    def body(ctx):
        spec_a = REGISTERED["arms"][arm]
        ctx.cfg = arm_config(arm)
        ctx.cap = training_clock()  # the hard stop at the cap less the reserve
        runs, (train, val) = e2_runs(), e2_ids()
        extra = (lambda i: {"sigma": spec_a["sigma"], "lr": spec_a["lr"]}) if spec_a["method"] == "es" else None
        recs, _ = E.train_batch(ctx, stage, spec_a["method"], runs, generations=spec_a["generations"], ids=train, val=val,
                                prefix=arm, sigma=spec_a.get("sigma"), lr=spec_a.get("lr"), extra=extra)
        return {"arm": spec_a, "records": [E.run_record(r, **(extra(i) if extra else {})) for i, r in enumerate(recs)],
                "pairing": pairing_check(arm, recs, train),
                "episodes": E._episodes(len(runs), spec_a["generations"],
                                        E.n_checkpoints(0, spec_a["generations"], REGISTERED["checkpoint_every"]),
                                        ctx.cfg, len(val))}

    local = [E.genomes_path(arm, r.run) for r in e2_runs()]
    doc = E.run_stage(args, stage, requires, body, local)
    print(arm, [round(r["champion"]["validation_mean"], 3) for r in doc["records"]], doc["pairing"]["passed"])


def pairing_check(arm: str, recs, train: dict) -> dict:
    a = REGISTERED["arms"][arm]
    ref = e2_record("train-es" if a["method"] == "es" else "train-ga")["records"]
    rows = []
    for rec, e in zip(recs, ref):
        if a["worlds"] == REGISTERED["ga"]["worlds_per_strain"]:  # E2's own worlds: the same generation 0
            rows.append(rec.checkpoints[0]["sha256"] == e["checkpoints"][0]["sha256"])
        else:
            g0 = rec.generation0["train_ids"][:len(e["generation0"]["train_ids"])] == e["generation0"]["train_ids"]
            last = a["generations"] - 1
            e8 = EV.train_ids(rec.spec.run_seed, last, REGISTERED["ga"]["worlds_per_strain"], train["base"],
                              train["span"])
            e32 = EV.train_ids(rec.spec.run_seed, last, a["worlds"], train["base"], train["span"])
            rows.append(bool(g0 and (e32[:len(e8)] == e8).all()))
    return {"per_run": rows, "passed": all(rows)}


# ============================================================================== Part C's hold-out pass

def matched(rec: dict, gens: list[int]) -> dict | None:
    """The first best checkpoint among those at the matched generations."""
    cks = [(i, c) for i, c in enumerate(rec["checkpoints"]) if c["generation"] in gens]
    if not cks:
        return None
    i, c = cks[int(np.argmax([c["validation_mean"] for _, c in cks]))]
    return {"checkpoint": i, **{k: c[k] for k in ("generation", "validation_mean", "sha256")}}


def cmd_evaluate(args):
    genomes = {}

    def requires(a, prov):
        b = require(a, prov, "probe")
        require_replay(a, prov)
        arms = {x: require(a, prov, f"arm-{x}", final_ok=True) for x in REGISTERED["arm_order"]}
        con = load_connectome()
        spec, cfg = BrainSpec.from_connectome(con), E.task_config()
        gens = REGISTERED["matched_generations"]
        for r in e2_record("train-ga")["records"]:  # E2's GA at the matched checkpoints (GA')
            m = matched(r, gens)
            genomes[f"ga' run{r['spec']['run']:02d}"] = _load(
                E2_OUT / "genomes" / f"ga-run{r['spec']['run']:02d}-candidates.npz", m["checkpoint"], m["sha256"], spec, cfg)
        for x, rec in arms.items():
            for r in rec.get("records", []):
                run = r["spec"]["run"]
                if "champion" in r:
                    c = r["champion"]
                    genomes[f"{x} run{run:02d}"] = _load(OUT / "genomes" / f"{x}-run{run:02d}-candidates.npz",
                                                         c["checkpoint"], c["sha256"], spec, cfg)
                if x == "c2" and matched(r, gens):
                    m = matched(r, gens)
                    genomes[f"c2' run{run:02d}"] = _load(OUT / "genomes" / f"c2-run{run:02d}-candidates.npz",
                                                         m["checkpoint"], m["sha256"], spec, cfg)
        return {"probe": b, "arms": arms}

    def body(ctx):
        hold, counts = ids("holdout"), {}
        ctx.salvage = lambda: {"arms_completed": list(counts),
                               "per_world_counts": {k: v.astype(int).tolist() for k, v in counts.items()}}
        for label, g in genomes.items():
            for p in REGISTERED["probes"]:
                counts[f"{label} {p}"] = neural(ctx.cfg, ctx.iface, g, hold, p, ctx.args.device, ctx.cap)[0]
                E.write_atomic(E.partial_path("evaluate"), {**ctx.doc, **ctx.salvage()})
        ctx.doc.update(worlds=E.id_record(hold), champion_sha256={k: genome_hash(g, 0) for k, g in genomes.items()})
        return analyse_c(counts, ctx.earlier["probe"], ctx.earlier["arms"])

    doc = E.run_stage(args, "evaluate", requires, body)
    print({k: v.get("reading") for k, v in doc["arms"].items()})


def analyse_c(counts: dict, b: dict, arms: dict) -> dict:
    bc = {k: np.asarray(v) for k, v in b["per_world_counts"].items()}
    allc = {**bc, **counts}
    runs = sorted({int(k.split("run")[1][:2]) for k in counts if k.startswith("ga' ")})
    score = lambda lab: float(allc[f"{lab} real"].mean())  # noqa: E731
    out, ref_of = {}, {"c1": "ga'", "c4": "ga'", "c2": "e2 ga", "c3": "e2 es"}
    for x in REGISTERED["arm_order"]:
        have = [r for r in runs if f"{x} run{r:02d} real" in allc]
        if len(have) < len(runs):
            out[x] = {"reading": "not drawn (the arm did not complete)", "outcome": arms[x].get("outcome")}
            continue
        diffs = np.array([score(f"{x} run{r:02d}") - score(f"{ref_of[x]} run{r:02d}") for r in runs])
        cls = [contrasts(allc, f"{x} run{r:02d}")["class"] for r in runs]
        sc = [score(f"{x} run{r:02d}") for r in runs]
        refs = [score(f"{ref_of[x]} run{r:02d}") for r in runs]
        out[x] = {**arm_reading(diffs), "outcome": arms[x].get("outcome"), "reference": ref_of[x],
                  "classes": cls, "scores": sc, "failures": int(sum(s < REGISTERED["readings"]["failure"] for s in sc)),
                  "leaves_plateau": leaves_plateau(cls, sc),
                  "arm_reference_correlation": float(np.corrcoef(sc, refs)[0, 1]) if np.std(sc) and np.std(refs) else None}
    extra = {}
    ok = lambda *xs: all(f"{x} run{r:02d} real" in allc for x in xs for r in runs)  # noqa: E731
    vec = lambda lab: np.array([score(f"{lab} run{r:02d}") for r in runs])  # noqa: E731
    if ok("c4", "c1"):
        extra["c4_minus_c1"] = arm_reading(vec("c4") - vec("c1"))
    if ok("c4", "c2'"):
        extra["c4_minus_c2prime (work allocation)"] = arm_reading(vec("c4") - vec("c2'"))
    if ok("c4", "c1", "c2'", "ga'"):
        extra["interaction"] = interaction(vec("c4"), vec("c1"), vec("c2'"), vec("ga'"))
    else:
        extra["interaction"] = "not drawn (an arm did not complete)"
    return {"arms": out, "contrasts": extra, "references": {"ga'": vec("ga'").tolist()},
            "per_world_counts": {k: v.astype(int).tolist() for k, v in counts.items()}}


# ============================================================================== smoke and main

def use_smoke(args, folder: Path | None = None, e2_folder: Path | None = None, e04a_folder: Path | None = None) -> None:
    """Tiny sizes, smoke ids (below 10 000), E2's and 04a's smoke folders as the sources, a scratch
    folder. Never results. Only files inside that folder are removed."""
    global EXP, OUT, SMOKE, E2_EXP, E2_OUT, E04A_EXP, E04A_OUT, GUARDED
    EXP = OUT = Path(folder) if folder is not None else ROOT / "runs" / "e2d-smoke"
    E2_EXP = E2_OUT = Path(e2_folder) if e2_folder is not None else ROOT / "runs" / "e2-smoke"
    E04A_EXP = E04A_OUT = Path(e04a_folder) if e04a_folder is not None else ROOT / "runs" / "e04a-smoke"
    SMOKE = True
    GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PLAN, *E.E1_INPUTS]
    R = REGISTERED
    R["ga"].update(generations=3, population=4, elites=1, truncation=2, worlds_per_strain=2)
    R["checkpoint_every"] = 2
    R["ids"] = {"holdout": {"first": 6000, "worlds": 16}, "probe": {"first": 7000, "worlds": 16}}
    R["arms"] = {"c1": {"method": "ga", "worlds": 8, "mutation_scale": 1.0, "generations": 3},
                 "c2": {"method": "ga", "worlds": 2, "mutation_scale": 0.5, "generations": 5},
                 "c4": {"method": "ga", "worlds": 8, "mutation_scale": 0.5, "generations": 3},
                 "c3": {"method": "es", "worlds": 2, "sigma": 0.25, "lr": 0.15, "generations": 3}}
    R["matched_generations"] = [0, 2]
    R["c0"].update(children=6, pairs=3, draws=20, k=4, top=2)
    R["analysis"].update(resamples=200, min_pairs=1)
    R["projection"].update(generations_timed=3, seed_base=SMOKE_SEED_BASE + 100)
    configure()
    name = {"project": "project", "probe": "probe", "siblings": "siblings", "replay": "replay",
            "arm": f"arm-{getattr(args, 'arm', None) or 'c1'}", "evaluate": "evaluate"}[args.command]
    for stage in STAGES[STAGES.index(name):]:
        for f in (E.record_path(stage), E.marker_path(stage), E.partial_path(stage)):
            if EXP in f.parents:
                f.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=["project", "probe", "siblings", "replay", "arm", "evaluate"])
    ap.add_argument("--arm", choices=["c1", "c2", "c4", "c3"])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--guarded", action="store_true")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--reason")
    args = ap.parse_args()
    if args.command == "arm" and not args.arm:
        ap.error("arm needs --arm c1, c2, c4 or c3")
    if args.smoke:
        use_smoke(args)
    {"project": cmd_project, "probe": cmd_probe, "siblings": cmd_siblings, "replay": cmd_replay, "arm": cmd_arm,
     "evaluate": cmd_evaluate}[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    out = ROOT / "runs" / ("e2d-smoke" if smoke else "e2d")
    try:
        run_script(main, out_default=str(out), default="measure", name="e2d")
    finally:
        agg = out / "compute.json"
        if agg.exists() and not smoke:
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
