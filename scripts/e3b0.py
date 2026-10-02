"""E3b-0: the maze engine, the controls and the task's feasibility (exploratory; docs/E3/E3b-0-PLAN.md v3,
agreed, D175).

    python scripts/e3b0.py stage-a | stage-b | recheck-a | stage-c | report | timing
    add --smoke for toy sizes in runs/e3b0-smoke (never results)

Every stage runs once, inside E2's stage frame, and its record is committed and pushed before the next
starts. The cap is 3 GPU-hours, counted through `wormwars.accounting`. Per-maze arrays go to compressed
.npz files beside the records (committed); no genome is saved (the seeds are rebuilt from committed records).

- **stage-a** (§4): (c, H) in order of c·H, then c; the scripted controls on the selection mazes at the
  pilot trail constants; the first candidate meeting conditions 1-5 is chosen.
- **stage-b** (§4): the trail grid on the chosen (c, H), with the scripted follower; the setting with the
  highest later-leg rate among those passing λ > m, polarity, gradient and nose range; one widening if
  the winner is on the grid's edge in μ or λ. The polarity null is the route-permuted trail (§3b; §4's
  "flat" is a leftover of v2, D177).
- **recheck-a** (§4): Stage A's conditions 2, 4 and 5 at the chosen constants.
- **stage-c** (§2b, §2c): each seed's first variant, in order, meeting criterion 2's thresholds and a
  trail effect (shared − none, later-leg rate) above 0 on the selection mazes; then the seed rule.
- **report** (§5): criteria 2-4 on the report mazes, with the peer controls (own, peers, replay with a
  coefficient frozen from a selection-maze pre-pass, scramble), single-wey colonies, occlusion,
  the component tests at the trail levels met, and the seed's median later leg.
- **timing** (§5, criterion 5): E3b-1's composition (256 strains × 16 worlds × 8 weys), with and without
  replay donors, and the projection.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars.brain import Brain, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a.evolve import moved  # noqa: E402
from wormwars.e3 import latch as L  # noqa: E402
from wormwars.e3 import maze_controls as MC  # noqa: E402
from wormwars.e3 import maze_measures as MM  # noqa: E402
from wormwars.e3 import maze_organisms as MO  # noqa: E402
from wormwars.e3 import maze_runs as MR  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e3 import organism as O  # noqa: E402
from wormwars.e3 import probe as P  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.evo.rollout import rollout  # noqa: E402


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


E = _load("e2_for_e3b0", "e2.py")

EXP = ROOT / "experiments" / "E3-ab-organism" / "E3b-0"
OUT = ROOT / "runs" / "e3b0"
PLAN = "docs/E3/E3b-0-PLAN.md"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PLAN,
           "experiments/E3-ab-organism/E3a/champions-3.json", "experiments/E4s-stereo-module/E4s-0/module.json",
           *E.E1_INPUTS]
SMOKE = False
STAGES = ["stage-a", "stage-b", "stage-b2", "stage-b3", "recheck-a", "stage-c", "report", "timing"]

REGISTERED = {
    "maze_seed": 1_180_000, "colony": 8, "spawns": 4,
    "pilot": {"mu": 0.01, "lam": 0.03, "delta": 0.15, "d0": 0.571},
    "stage_a": {"c": [5, 6, 7, 8], "H": [1200, 2400], "oracle_visits_min": 8.0, "follower_legs_median_min": 4.0,
                "w2_share_max": 0.5, "walk_share_max": 0.25, "discovery_share_of_H_max": 0.25},
    "stage_b": {"mu": [0.005, 0.01, 0.02], "lam": [0.01, 0.02, 0.04], "delta": [0.05, 0.15], "d0_scale": [0.5, 1.0],
                "polarity_min": 0.3, "gradient_min": 0.8, "range_min": 0.9, "saturated_max": 0.05},
    "criterion2": {"legs_median_min": 2.0, "mde": 0.22, "headroom_factor": 2.0, "lb_min": 0.0,
                   "mde_source": "power.json fine: 12 runs, t-test, CV 0.282, normal (the larger of the two shapes)"},
    "criterion3": {"rate_lb_min": 0.5},
    # Amendment 1 (after Stage B, D178): stage-b2 reads Stage B's record
    "stage_b2": {"gradient_min": 0.8, "high_level": 0.35, "high_share_max": 0.05, "trail_lb_min": 0.0,
                 "d0_scale_edges": {"low": 0.25, "high": 2.0}, "component_quantiles": [5, 25, 50, 75, 95, 99],
                 "component_floor": 0.001,
                 "trail_effect_rule": "world_ci: paired bootstrap over mazes, 10 000 resamples, seed 0, two-sided 95%; "
                                      "lower end above 0"},
    # Stage A's and Stage B's records ran on earlier code; they are reused under a narrow transition: their
    # committed files by hash, the environment unchanged, and stage-b2's shared rates equal to Stage B's
    # (Astra, Fable; D178)
    "historical": {"stage-a": "50187714b13f8d489fb112339bf4f3e1cb561b12ab8251741a80ba21dd40c80b",
                   "stage-b": "71c8b2aada4756c6679a30729d0a1fd7597e4b3fe1525cc155beb337017e19b6",
                   "stage-b2": "023018f4c6d863298e26a7eef6956389d782a3e7a389dc807f4c264301c743df"},
    # Amendment 2 (after stage-b2 and diagnosis 4, D179): the high level at 1.0, from E's K_D x level; the
    # cap measured on the seed E + W2's own inputs; criterion 4 above 0.35 at K_D x level >= 10.5, the
    # registered K_D >= 30 at 0.35 (30 x 0.35)
    "stage_b3": {"gradient_min": 0.8, "high_level": 1.0, "high_share_max": 0.05, "trail_lb_min": 0.0,
                 "d0_scale_edges": {"low": 0.25, "high": 2.0}, "component_quantiles": [5, 25, 50, 75, 95, 99],
                 "component_floor": 0.001, "relative_min": 10.5,
                 "cap_seed": ["E", "W2"],
                 "trail_effect_rule": "world_ci: paired bootstrap over mazes, 10 000 resamples, seed 0, two-sided 95%; "
                                      "lower end above 0"},
    "component_levels_fixed": [0.001, 0.003],
    "ids": {"selection": [0, 256], "report": [1000, 1256], "fresh": [2000, 2256]},
    "seeds": ["E", "S3r3"], "variants": list(MO.VARIANTS),
    "cap_gpu_hours": 3.0,
    "e3b1": {"strains": 256, "worlds_per_strain": 16, "weys": 8, "runs_per_arm": 12, "population": 32,
             "generations": 500, "training_arms": 2, "budget_hours": 24.0, "reserve_factor": 1.25,
             "note": "the projection's generations follow E3a's Stage 3 (500); E3b-1's design sets its own"},
}
RECORD = {s: s for s in STAGES}
WHAT = {s: f"E3b-0's {s}" for s in STAGES}


def configure() -> None:
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, OUT, GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E3b-0: not completed (the run stopped)",
                  "cap": "E3b-0: not completed (the cap was reached)"}
    E.RECORD.update(RECORD)
    E.WHAT.update(WHAT)


configure()


def base_config():
    """E1's Task N (σ 6), checked against E1's gate record as E2 checks it: the brain and energy settings
    under every maze configuration."""
    cfg = E.E1.config(6.0)
    want = json.loads(E.E1_GATE.read_text(encoding="utf-8"))["resolved_config"]
    if hashlib.sha256(json.dumps(want, sort_keys=True).encode()).hexdigest() != E.config_sha256(cfg):
        raise SystemExit("Task N's resolved configuration differs from E1's gate: refusing to run")
    return cfg


def cfg_for(c: int, H: int, *, mu: float, lam: float, delta: float, d0: float, colony: int | None = None):
    return MW.maze_config(base_config(), c=int(c), horizon=int(H), colony=int(colony or REGISTERED["colony"]),
                          mu=mu, lam=lam, delta=delta, d0=d0, spawns=REGISTERED["spawns"])


def task_config():
    P_ = REGISTERED["pilot"]
    return cfg_for(5, 1200, **P_)


E.task_config = task_config  # the stage frame records this as each stage's starting configuration


# ============================================================================== ids, io

def ids(key: str) -> np.ndarray:
    lo, hi = REGISTERED["ids"][key]
    if SMOKE:
        lo = {"selection": 9000, "report": 9100, "fresh": 9200}[key]
        hi = lo + 6
    return np.arange(lo, hi)


def seed() -> int:
    return REGISTERED["maze_seed"]


def save_npz(name: str, arrays: dict) -> None:
    path = EXP / f"{name}.npz"
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, **{k: np.asarray(v) for k, v in arrays.items()})
    E.replace(tmp, path)


def load_npz(name: str) -> dict:
    with np.load(EXP / f"{name}.npz", allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def check_historical(path: Path, sha256: str) -> dict:
    rec_bytes = Path(path).read_bytes()
    import hashlib as _h
    if _h.sha256(rec_bytes).hexdigest() != sha256:
        raise SystemExit(f"{Path(path).name}'s hash differs from the pinned one: not the record Amendment 1 reuses")
    return json.loads(rec_bytes.decode("utf-8"))


def require_historical(args, prov, stage: str) -> dict:
    """Stage A's and Stage B's records, made on earlier code: completed, committed, the same file by hash,
    and the same environment. Their code is not required to be the current code (D178)."""
    path = E.record_path(stage)
    if not path.exists():
        raise SystemExit(f"{WHAT[stage]} has not run")
    if E.formal(args) and not args.smoke:
        E.require_committed(path)
        rec = check_historical(path, REGISTERED["historical"][stage])
        E.reg.require_same_env(rec["provenance_at_start"], prov)
    else:
        rec = json.loads(path.read_text(encoding="utf-8"))
    if rec.get("outcome") != "completed":
        raise SystemExit(f"{WHAT[stage]} did not complete")
    return rec


def require(args, prov, *stages):
    return {s: (require_historical(args, prov, s) if s in REGISTERED["historical"] else E.require_earlier(args, prov, s))
            for s in stages}


AMENDED = ("stage-b3", "stage-b2")  # the latest amended selection stage that ran decides


def amended(earlier: dict) -> tuple[str, dict]:
    """(registered key, record) of the amended selection stage in force: stage-b3 if it ran, else stage-b2."""
    for stage in AMENDED:
        if stage in earlier:
            return stage.replace("-", "_"), earlier[stage]
    raise SystemExit("no amended selection stage has run")


def require_selection(args, prov, *later):
    """Stage A, Stage B and the amended selection stages that exist, then `later`."""
    stages = ["stage-a", "stage-b", "stage-b2"] + (["stage-b3"] if E.record_path("stage-b3").exists() else [])
    return require(args, prov, *stages, *later)


def seed_cap(nr: dict, key: str = "stage_b2") -> dict:
    """The high-level cap on the chosen seed's own inputs (Astra, D178): an empty count fails."""
    R = REGISTERED[key]
    share = nr["above_share_qualified_by_level"][str(R["high_level"])]
    ok = nr["qualified_inputs"] > 0 and share <= R["high_share_max"]
    return {"qualified_inputs": nr["qualified_inputs"], "high_level": R["high_level"], "above_high_share": share,
            "max": R["high_share_max"], "passed": bool(ok)}


def component_levels(quantiles: dict, key: str = "stage_b2") -> list:
    """Criterion 4's levels: 0.001, 0.003 and the boundary 0.35, and the seed's measured quantiles floored at
    0.001 (the probe steps by ±0.0005, so a lower level would make a nose input negative)."""
    R = REGISTERED[key]
    qs = [max(float(quantiles[str(q)]), R["component_floor"]) for q in R["component_quantiles"]]
    return sorted(set(REGISTERED["component_levels_fixed"] + [0.35, R["high_level"]] + qs))


def live(mu: float, lam: float) -> bool:
    return lam > -math.log(1.0 - mu)


# ============================================================================== summaries

def summary(ev: dict, H: int) -> dict:
    """Per maze (colony means), as arrays."""
    vt = ev["visit_tick"]
    rate, unvisited = MM.later_leg_rate(vt, H)
    out = {"visits": MM.colony_mean(ev["visits"]), "legs": MM.colony_mean(MM.legs(vt)), "later_leg_rate": rate,
           "unvisited_share": unvisited, "first_discovery": MM.first_discovery(vt, H).astype(np.float64),
           "occluded_share": MM.colony_mean(ev["occluded_ticks"] / np.maximum(ev["ticks"][:, None], 1)),
           "exposure_mean": MM.colony_mean(ev["exposure_sum"] / np.maximum(ev["ticks"][:, None], 1)),
           "exposure_zero_share": MM.colony_mean(ev["exposure_zero_ticks"] / np.maximum(ev["ticks"][:, None], 1))}
    if vt.shape[1] > 1:
        out["later_first_b"] = MM.later_first_b(ev["first_b_tick"], H)
    return out


def brief(s: dict) -> dict:
    """Means and medians over mazes, for the record."""
    return {k: {"mean": float(np.mean(v)), "median": float(np.median(v)), "sd": float(np.std(v, ddof=1)) if len(v) > 1 else 0.0}
            for k, v in s.items()}


def flat(prefix: str, s: dict) -> dict:
    return {f"{prefix}.{k}": v for k, v in s.items()}


# ============================================================================== controllers

def makers(cfg, iface, dev):
    return {"oracle": lambda: MC.oracle(iface, cfg, device=dev), "follower": lambda: MC.follower(iface, cfg, device=dev),
            "w2": lambda: MC.w2_alone(iface, cfg, device=dev), "walk": lambda: MC.reflex_walk(iface, cfg, device=dev)}


def organism(con, l1, cfg, seed_name: str, variant: str):
    sd = MO.seed(seed_name, l1, cfg.brain, con=con)
    return MO.maze_organism(con, sd, variant, cfg.brain)


def carrier_variant(con, cfg, variant: str):
    """The carrier with the variant's additions and no seed module: the blind baseline (§2b)."""
    carrier = O.carrier_only()
    import wormwars.graft as G
    ext = G.graft_connectome(con, carrier)
    sd = MO.Seed("carrier", carrier, ext, MO.C.carrier_genome(ext, carrier, cfg.brain, forward=1.0, turn=0.2))
    return MO.maze_organism(con, sd, variant, cfg.brain)


def active_passes(values: dict, key: str) -> bool:
    """Criterion 4: active K_D >= 30 at every level up to 0.35; under Amendment 2, K_D x level >= 11.06 (E's
    value at 0.35) at levels in (0.35, 1.0]."""
    R = REGISTERED[key]
    ok = True
    for k, v in values.items():
        m = float(k.split("@")[1])
        if m <= 0.35:
            ok &= v >= P.ACTIVE_MIN
        elif m <= R["high_level"]:
            ok &= v * m >= R.get("relative_min", float("inf"))
    return bool(ok)


def one_nose_checks(genome, pc, states: dict, levels: list, high_level: float = 0.35) -> dict:
    """The active module's response to one nose at q and the other at 0 (an occluded nose reads 0): its turn
    must move toward the positive nose, (q, 0) above (0, 0) and (0, q) below, at every level up to 0.35
    (Astra, D178). The other module's noses stay at 0."""
    out, ok = {}, True
    for goal, q in states.items():
        st = pc.latch_state(genome, q)
        zero = float(P._run(genome, pc, st, pc.noses(genome.n_strains, 0.0))[0])
        for m in levels:
            i, j = pc.pairs[goal]
            left = pc.noses(genome.n_strains, 0.0)
            left[..., i] = m
            right = pc.noses(genome.n_strains, 0.0)
            right[..., j] = m
            ul, ur = float(P._run(genome, pc, st, left)[0]), float(P._run(genome, pc, st, right)[0])
            good = ul > zero > ur
            out[f"{goal}@{m}"] = {"u_left_only": ul, "u_none": zero, "u_right_only": ur, "toward_positive": good}
            if m <= high_level:
                ok &= good
    return {"values": out, "passed_up_to_high_level": bool(ok)}


def latch_states(org) -> dict:
    """The seed's latch states for the component tests: the stable roots of −q + w·tanh q + b with its own
    q self-weight and bias (E's are ±1.915), the upper for goal A (q excites A's comparators) and the lower
    for B."""
    w = MO.named_edges(org.genome, org.ext)[(O.Q, O.Q)]
    b = float(org.genome.bias[0, org.ext.index(O.Q)])
    r = L.stable_roots(w, b)
    if len(r) < 2:
        raise SystemExit(f"the seed's latch has {len(r)} stable root(s) (w {w}, b {b}): no component test states")
    return {"A": max(r), "B": min(r)}


def play_org(cfg, org, ids_, dev, **kw):
    """An organism on the mazes, its brain started as its own (M1 at 0.1 when it has M; D179)."""
    return MR.play(cfg, org.iface, lambda: MO.brain(org, dev), ids_, seed(), dev, **kw)


def run(category: str, cap, fn):
    cap.check()
    with acct.category(category):
        return fn()


# ============================================================================== stage A

def stage_a_conditions(o, f, w2, wk, H) -> dict:
    R = REGISTERED["stage_a"]
    cond = {
        "1_oracle_visits": {"value": float(np.mean(o["visits"])), "min": R["oracle_visits_min"]},
        "2_follower_legs_median": {"value": float(np.median(f["legs"])), "min": R["follower_legs_median_min"]},
        "3_w2_share_of_oracle": {"value": float(np.mean(w2["visits"]) / max(np.mean(o["visits"]), 1e-12)),
                                 "max": R["w2_share_max"]} if w2 is not None else None,
        "4_walk_share_of_follower": {"value": float(np.mean(wk["visits"]) / max(np.mean(f["visits"]), 1e-12)),
                                     "max": R["walk_share_max"]},
        "5_discovery_median_share_of_H": {"value": float(np.median(f["first_discovery"]) / H),
                                          "max": R["discovery_share_of_H_max"]},
    }
    cond = {k: v for k, v in cond.items() if v is not None}
    for v in cond.values():
        v["passed"] = bool(v["value"] >= v["min"]) if "min" in v else bool(v["value"] <= v["max"])
    return cond


def cmd_stage_a(args):
    def body(ctx):
        dev, R, P_ = ctx.args.device, REGISTERED["stage_a"], REGISTERED["pilot"]
        cands = sorted(itertools.product(R["c"], R["H"]), key=lambda t: (t[0] * t[1], t[0]))
        if SMOKE:
            cands = [(5, 120), (6, 120)]
        sel = ids("selection")
        evaluated, chosen = [], None
        for c, H in cands:
            cfg = cfg_for(c, H, **P_)
            mk = makers(cfg, ctx.iface, dev)
            res = {}
            for name, access in (("oracle", "none"), ("follower", "shared"), ("w2", "none"), ("walk", "none")):
                ev = run("measure", ctx.cap, lambda: MR.play(cfg, ctx.iface, mk[name], sel, seed(), dev, access=access))
                res[name] = summary(ev, H)
            cond = stage_a_conditions(res["oracle"], res["follower"], res["w2"], res["walk"], H)
            save_npz(f"stage-a-c{c}-H{H}", {f"{n}.{k}": v for n, s in res.items() for k, v in s.items()})
            ok = all(v["passed"] for v in cond.values())
            evaluated.append({"c": c, "H": H, "conditions": cond, "passed": ok,
                              "brief": {n: brief(s) for n, s in res.items()}})
            print(f"stage-a c={c} H={H}: {'pass' if ok else 'fail'} {[(k, round(v['value'], 3)) for k, v in cond.items()]}",
                  flush=True)
            if ok:
                chosen = {"c": c, "H": H}
                break
        return {"candidates_in_order": [list(t) for t in cands], "evaluated": evaluated, "chosen": chosen,
                "maze_ids": {"selection": [int(sel[0]), int(sel[-1]) + 1]}}

    return E.run_stage(args, "stage-a", lambda a, prov: {}, body)


# ============================================================================== stage B

def evaluate_setting(ctx, c, H, s, dev) -> dict:
    """One trail setting: the follower's run with the nose range, the polarity test, the gradient shares."""
    cfg = cfg_for(c, H, mu=s["mu"], lam=s["lam"], delta=s["delta"], d0=s["d0"])
    sel = ids("selection")
    mk = makers(cfg, ctx.iface, dev)
    ev = run("measure", ctx.cap, lambda: MR.play(cfg, ctx.iface, mk["follower"], sel, seed(), dev, access="shared",
                                                 nose_range=True))
    f = summary(ev, H)
    one = cfg_for(c, H, mu=s["mu"], lam=s["lam"], delta=s["delta"], d0=s["d0"], colony=1)
    pol = run("measure", ctx.cap, lambda: MR.polarity(one, ctx.iface, sel, seed(), dev))
    g1 = run("measure", ctx.cap, lambda: MR.gradient(one, ctx.iface, sel, seed(), dev))
    g8 = run("measure", ctx.cap, lambda: MR.gradient(cfg, ctx.iface, sel, seed(), dev))
    R = REGISTERED["stage_b"]
    single = pol["single_pass"].astype(bool)
    real, none, perm = (float(np.mean(pol[k][single])) if single.any() else float("nan")
                        for k in ("pass_real", "pass_none", "pass_permuted"))
    polarity = real - max(none, perm)
    grad = {f"{n}_age{k}": float(np.nanmean(g[f"share_age{k}"])) for n, g in (("one", g1), ("eight", g8)) for k in (1, 2, 4)}
    nr = ev["nose_range"]
    checks = {"live": live(s["mu"], s["lam"]),
              "polarity": bool(polarity >= R["polarity_min"]),
              "gradient": bool(grad["one_age1"] >= R["gradient_min"] and grad["eight_age1"] >= R["gradient_min"]),
              "range": bool(nr["in_range_share"] >= R["range_min"] and nr["above_share"] <= R["saturated_max"])}
    tag = f"mu{s['mu']}-lam{s['lam']}-delta{s['delta']}-d0{s['d0']:.4f}"
    save_npz(f"stage-b-{tag}", {**flat("follower", f), **{f"polarity.{k}": v for k, v in pol.items()},
                                **{f"gradient1.{k}": v for k, v in g1.items()}, **{f"gradient8.{k}": v for k, v in g8.items()}})
    return {"setting": s, "follower_later_leg_rate": float(np.mean(f["later_leg_rate"])),
            "follower_brief": brief(f), "polarity": {"real": real, "none": none, "permuted": perm, "reading": polarity,
                                                     "single_pass_mazes": int(single.sum())},
            "gradient": grad, "nose_range": nr, "checks": checks, "passed": all(checks.values())}


def choose(rows: list) -> dict | None:
    ok = [r for r in rows if r["passed"]]
    if not ok:
        return None
    return sorted(ok, key=lambda r: (-r["follower_later_leg_rate"], r["setting"]["mu"], r["setting"]["lam"],
                                     r["setting"].get("d0", 0.0)))[0]


def cmd_stage_b(args):
    def body(ctx):
        dev, R, P_ = ctx.args.device, REGISTERED["stage_b"], REGISTERED["pilot"]
        a = ctx.earlier["stage-a"]
        if not a.get("chosen"):
            raise SystemExit("Stage A chose no (c, H): Stage B does not run (a report and a redesign, §6)")
        c, H = a["chosen"]["c"], a["chosen"]["H"]
        grid = [{"mu": m, "lam": l, "delta": d, "d0": P_["d0"] * k}
                for m, l, d, k in itertools.product(R["mu"], R["lam"], R["delta"], R["d0_scale"])]
        if SMOKE:
            grid = grid[:3]
        rows, skipped = [], []
        for s in grid:
            if not live(s["mu"], s["lam"]):
                skipped.append(s)
                continue
            rows.append(evaluate_setting(ctx, c, H, s, dev))
            r = rows[-1]
            print(f"stage-b {s}: rate {r['follower_later_leg_rate']:.2f} {r['checks']}", flush=True)
        win = choose(rows)
        widened = None
        if win is not None and not SMOKE:
            mus, lams = R["mu"], R["lam"]
            new_mu = {mus[0]: mus[0] / 2, mus[-1]: mus[-1] * 2}.get(win["setting"]["mu"])
            new_lam = {lams[0]: lams[0] / 2, lams[-1]: lams[-1] * 2}.get(win["setting"]["lam"])
            if new_mu is not None or new_lam is not None:
                extra = []
                mu_set = mus + ([new_mu] if new_mu else [])
                lam_set = lams + ([new_lam] if new_lam else [])
                for m, l, d, k in itertools.product(mu_set, lam_set, R["delta"], R["d0_scale"]):
                    if (m == new_mu or l == new_lam) and live(m, l):
                        extra.append({"mu": m, "lam": l, "delta": d, "d0": P_["d0"] * k})
                for s in extra:
                    rows.append(evaluate_setting(ctx, c, H, s, dev))
                widened = {"mu": new_mu, "lam": new_lam, "settings": len(extra)}
                win = choose(rows)
        return {"c": c, "H": H, "grid": grid, "skipped_not_live": skipped, "rows": rows, "widened": widened,
                "chosen": None if win is None else win["setting"],
                "note": "the polarity null is the route-permuted trail (§3b); §4's 'flat' is a v2 leftover (D177)"}

    return E.run_stage(args, "stage-b", lambda a, prov: require(a, prov, "stage-a"), body)


# ============================================================================== stage B2 (Amendment 1)

WORDING = ("Stage B failed the registered behavioural polarity criterion. Gradient-sign qualification does not "
           "establish directional trail use; the amended stage reports behavioural polarity separately.")


def b2_tag(s: dict) -> str:
    return f"mu{s['mu']}-lam{s['lam']}-delta{s['delta']}-d0{s['d0']:.4f}"


def b2_row(ctx, c, H, s, dev, none_rate, gradient=None, gradients_by_shape=None, key: str = "stage_b2") -> dict:
    """One setting under Amendment 1: the follower's shared colony with the nose recorder; the gradient
    from Stage B's row, or measured here for a widened setting; the trail effect against the no-trail run."""
    R = REGISTERED[key]
    cfg = cfg_for(c, H, mu=s["mu"], lam=s["lam"], delta=s["delta"], d0=s["d0"])
    sel = ids("selection")
    ev = run("measure", ctx.cap, lambda: MR.play(cfg, ctx.iface, makers(cfg, ctx.iface, dev)["follower"], sel, seed(),
                                                 dev, access="shared", nose_range=True))
    f = summary(ev, H)
    arrays = flat("follower", f)
    if gradient is None and gradients_by_shape:  # linear trails: the gradient's signs do not depend on d0
        gradient = gradients_by_shape.get((s["mu"], s["lam"], s["delta"]))
    if gradient is None:
        one = cfg_for(c, H, mu=s["mu"], lam=s["lam"], delta=s["delta"], d0=s["d0"], colony=1)
        g1 = run("measure", ctx.cap, lambda: MR.gradient(one, ctx.iface, sel, seed(), dev))
        g8 = run("measure", ctx.cap, lambda: MR.gradient(cfg, ctx.iface, sel, seed(), dev))
        gradient = {f"{n}_age{k}": float(np.nanmean(g[f"share_age{k}"])) for n, g in (("one", g1), ("eight", g8))
                    for k in (1, 2, 4)}
        arrays.update({**{f"gradient1.{k}": v for k, v in g1.items()}, **{f"gradient8.{k}": v for k, v in g8.items()}})
    trail = MM.world_ci(f["later_leg_rate"], none_rate)
    nr = ev["nose_range"]
    checks = {"live": live(s["mu"], s["lam"]),
              "gradient": bool(gradient["one_age1"] >= R["gradient_min"] and gradient["eight_age1"] >= R["gradient_min"]),
              "high_cap": bool(nr["qualified_inputs"] > 0 and
                               nr["above_share_qualified_by_level"][str(R["high_level"])] <= R["high_share_max"]),
              "trail_effect": bool(trail["lo95"] > R["trail_lb_min"])}
    save_npz(f"{key.replace('_', '-')}-{b2_tag(s)}", arrays)
    return {"setting": s, "config_sha256": E.config_sha256(cfg),
            "follower_later_leg_rate": float(np.mean(f["later_leg_rate"])), "trail_effect": trail,
            "follower_brief": brief(f), "gradient": gradient, "nose_range": nr, "checks": checks,
            "passed": all(checks.values())}


def b2_widening(win: dict, grid: dict, d0_pilot: float, rows: list | None = None):
    """Every live setting that uses a value one factor of 2 beyond an edge the winner sits on, in mu, lambda or
    d0, crossed with the rest of the grid and each other (Amendment 1). With `rows`, a direction is widened
    only if the rate still rises toward that edge: the winner's rate exceeds that of the live row one grid step
    inside, its other constants the same (fixed before stage-b2 ran; D178)."""
    R = REGISTERED["stage_b2"]["d0_scale_edges"]  # the same in stage_b3
    mus, lams, ks = list(grid["mu"]), list(grid["lam"]), list(grid["d0_scale"])
    s = win["setting"]
    new_mu = {mus[0]: mus[0] / 2, mus[-1]: mus[-1] * 2}.get(s["mu"])
    new_lam = {lams[0]: lams[0] / 2, lams[-1]: lams[-1] * 2}.get(s["lam"])
    k = round(s["d0"] / d0_pilot, 6)
    new_k = {round(ks[0], 6): R["low"], round(ks[-1], 6): R["high"]}.get(k)
    if rows is not None:
        def rate_at(mu, lam, kk):
            for r in rows:
                t = r["setting"]
                if (t["mu"] == mu and t["lam"] == lam and t["delta"] == s["delta"]
                        and abs(t["d0"] - d0_pilot * kk) < 1e-12 and live(mu, lam)):
                    return r["follower_later_leg_rate"]
            return None

        base = win.get("follower_later_leg_rate", rate_at(s["mu"], s["lam"], k))

        def rising(inner):
            return inner is not None and base > inner

        if new_mu is not None and not rising(rate_at(mus[1] if s["mu"] == mus[0] else mus[-2], s["lam"], k)):
            new_mu = None
        if new_lam is not None and not rising(rate_at(s["mu"], lams[1] if s["lam"] == lams[0] else lams[-2], k)):
            new_lam = None
        if new_k is not None and not rising(rate_at(s["mu"], s["lam"], ks[1] if k == round(ks[0], 6) else ks[-2])):
            new_k = None
    out = []
    for m, l_, d, kk in itertools.product(mus + ([new_mu] if new_mu else []), lams + ([new_lam] if new_lam else []),
                                          grid["delta"], ks + ([new_k] if new_k else [])):
        if (m == new_mu or l_ == new_lam or kk == new_k) and live(m, l_):
            out.append({"mu": m, "lam": l_, "delta": d, "d0": d0_pilot * kk})
    return out, {"mu": new_mu, "lam": new_lam, "d0_scale": new_k}


def amended_selection(args, stage: str):
    """Amendment 1's rule (stage-b2), or Amendment 2's with the high level at 1.0 (stage-b3)."""
    key = stage.replace("-", "_")

    def body(ctx):
        dev, R = ctx.args.device, REGISTERED["stage_b"]
        b = ctx.earlier["stage-b"]
        c, H = b["c"], b["H"]
        sel = ids("selection")
        cfg0 = cfg_for(c, H, **REGISTERED["pilot"])
        none = summary(run("measure", ctx.cap, lambda: MR.play(cfg0, ctx.iface, makers(cfg0, ctx.iface, dev)["follower"],
                                                               sel, seed(), dev, access="none")), H)
        save_npz(f"{stage}-none", flat("follower_none", none))
        rows, equal = [], []
        for old in b["rows"]:
            r = b2_row(ctx, c, H, old["setting"], dev, none["later_leg_rate"], gradient=old["gradient"], key=key)
            same = r["follower_later_leg_rate"] == old["follower_later_leg_rate"]
            equal.append(same)
            print(f"{stage} {r['setting']}: rate {r['follower_later_leg_rate']:.2f} (Stage B equal: {same}) "
                  f"{r['checks']}", flush=True)
            if not same and not SMOKE:
                raise SystemExit(f"{stage}'s shared rate differs from Stage B's on the same setting: the reuse of "
                                 "Stage B's records is not supported (D178)")
            rows.append(r)
        shapes = {(r["setting"]["mu"], r["setting"]["lam"], r["setting"]["delta"]): r["gradient"] for r in rows}
        win = choose(rows)
        widened = None
        if win is not None and not SMOKE:
            extra, new = b2_widening(win, R, REGISTERED["pilot"]["d0"], rows)
            if extra:
                for s in extra:
                    rows.append(b2_row(ctx, c, H, s, dev, none["later_leg_rate"], gradients_by_shape=shapes, key=key))
                    r = rows[-1]
                    print(f"{stage} widened {s}: rate {r['follower_later_leg_rate']:.2f} {r['checks']}", flush=True)
                widened = {**new, "settings": len(extra)}
                win = choose(rows)
        polarity = None
        if win is not None:
            s = win["setting"]
            one = cfg_for(c, H, mu=s["mu"], lam=s["lam"], delta=s["delta"], d0=s["d0"], colony=1)
            polarity = {}
            for facing in ("away", "toward", "random"):
                for age_legs in (1.0, 0.0):
                    p = run("measure", ctx.cap, lambda: MR.polarity(one, ctx.iface, sel, seed(), dev, facing=facing,
                                                                    limit_factor=4.0, age_legs=age_legs))
                    polarity[f"{facing}_age{int(age_legs)}"] = MR.polarity_readings(p)
                p = run("measure", ctx.cap, lambda: MR.polarity(one, ctx.iface, sel, seed(), dev, facing=facing,
                                                                limit_factor=4.0, synthetic=MR.synthetic_slope))
                polarity[f"synthetic_{facing}"] = MR.polarity_readings(p)
        return {"c": c, "H": H, "follower_none_brief": brief(none), "rows": rows, "widened": widened,
                "stage_b_rates_equal": equal,
                "resolved_config_note": "resolved_config is the frame's base configuration; each row's effective "
                                        "setting is its 'setting' and 'config_sha256'",
                "chosen": None if win is None else win["setting"], "polarity_reported": polarity, "wording": WORDING,
                "high_level": REGISTERED[key]["high_level"],
                "label": ("adaptively selected: Amendment 1 was decided after seeing Stage B's data (D178)" if key == "stage_b2"
                          else "adaptively selected: Amendment 2 was decided after seeing stage-b2 and diagnosis 4 (D179)")}

    return E.run_stage(args, stage, lambda a, prov: require(a, prov, "stage-a", "stage-b"), body)


def cmd_stage_b2(args):
    return amended_selection(args, "stage-b2")


def cmd_stage_b3(args):
    """Amendment 2: the high level at 1.0, measured on the seed E + W2's own inputs (Fable, Astra; D179).
    The ranking (the follower's later-leg rate) and the gradient come from Stage B's rows, the follower's
    trail-effect gate from stage-b2's rows; for each setting the seed's shared colony runs with the nose
    recorder, and its own trail effect is reported. A widened setting runs the follower too, against
    stage-b2's no-trail run."""
    key = "stage_b3"

    def body(ctx):
        dev, RB, R = ctx.args.device, REGISTERED["stage_b"], REGISTERED[key]
        b, b2 = ctx.earlier["stage-b"], ctx.earlier["stage-b2"]
        c, H = b["c"], b["H"]
        sel = ids("selection")
        con, l1 = load_connectome(), A.load_l1()
        cfg0 = cfg_for(c, H, **REGISTERED["pilot"])
        sname, variant = R["cap_seed"]
        org = organism(con, l1, cfg0, sname, variant)
        seed_none = summary(run("measure", ctx.cap, lambda: play_org(cfg0, org, sel, dev, access="none")), H)
        follower_none = load_npz("stage-b2-none")["follower_none.later_leg_rate"]
        save_npz("stage-b3-seed-none", flat("seed_none", seed_none))
        b2_rows = {b2_tag(r["setting"]): r for r in b2["rows"]}

        def row(s, rate=None, gradient=None, follower_effect=None, shapes=None):
            cfg = cfg_for(c, H, mu=s["mu"], lam=s["lam"], delta=s["delta"], d0=s["d0"])
            arrays = {}
            if rate is None:  # a widened setting: the follower runs here
                ev = run("measure", ctx.cap, lambda: MR.play(cfg, ctx.iface, makers(cfg, ctx.iface, dev)["follower"],
                                                             sel, seed(), dev, access="shared"))
                f = summary(ev, H)
                rate, follower_effect = float(np.mean(f["later_leg_rate"])), MM.world_ci(f["later_leg_rate"], follower_none)
                arrays.update(flat("follower", f))
                gradient = (shapes or {}).get((s["mu"], s["lam"], s["delta"]))
                if gradient is None:
                    one = cfg_for(c, H, mu=s["mu"], lam=s["lam"], delta=s["delta"], d0=s["d0"], colony=1)
                    g1 = run("measure", ctx.cap, lambda: MR.gradient(one, ctx.iface, sel, seed(), dev))
                    g8 = run("measure", ctx.cap, lambda: MR.gradient(cfg, ctx.iface, sel, seed(), dev))
                    gradient = {f"{n}_age{k}": float(np.nanmean(g[f"share_age{k}"])) for n, g in (("one", g1), ("eight", g8))
                                for k in (1, 2, 4)}
            ev = run("measure", ctx.cap, lambda: play_org(cfg, org, sel, dev, access="shared", nose_range=True))
            sd = summary(ev, H)
            arrays.update(flat("seed", sd))
            nr = ev["nose_range"]
            share = nr["above_share_qualified_by_level"][str(R["high_level"])]
            checks = {"live": live(s["mu"], s["lam"]),
                      "gradient": bool(gradient["one_age1"] >= R["gradient_min"] and gradient["eight_age1"] >= R["gradient_min"]),
                      "seed_cap": bool(nr["qualified_inputs"] > 0 and share <= R["high_share_max"]),
                      "trail_effect": bool(follower_effect["lo95"] > R["trail_lb_min"])}
            save_npz(f"stage-b3-{b2_tag(s)}", arrays)
            return {"setting": s, "config_sha256": E.config_sha256(cfg), "follower_later_leg_rate": rate,
                    "trail_effect": follower_effect, "gradient": gradient,
                    "seed": {"name": f"{sname}+{variant}", "brief": brief(sd), "nose_range": nr, "above_high_share": share,
                             "trail_effect": MM.world_ci(sd["later_leg_rate"], seed_none["later_leg_rate"])},
                    "checks": checks, "passed": all(checks.values())}

        rows = []
        for old in b["rows"]:
            r = row(old["setting"], rate=old["follower_later_leg_rate"], gradient=old["gradient"],
                    follower_effect=b2_rows[b2_tag(old["setting"])]["trail_effect"])
            rows.append(r)
            print(f"stage-b3 {r['setting']}: rate {r['follower_later_leg_rate']:.2f} seed effect "
                  f"{r['seed']['trail_effect']['mean']:+.2f} above1.0 {r['seed']['above_high_share']:.3f} {r['checks']}",
                  flush=True)
        shapes = {(r["setting"]["mu"], r["setting"]["lam"], r["setting"]["delta"]): r["gradient"] for r in rows}
        win = choose(rows)
        widened = None
        if win is not None and not SMOKE:
            extra, new = b2_widening(win, RB, REGISTERED["pilot"]["d0"], rows)
            if extra:
                for s_ in extra:
                    rows.append(row(s_, shapes=shapes))
                    r = rows[-1]
                    print(f"stage-b3 widened {s_}: rate {r['follower_later_leg_rate']:.2f} {r['checks']}", flush=True)
                widened = {**new, "settings": len(extra)}
                win = choose(rows)
        polarity = None
        if win is not None:
            s_ = win["setting"]
            one = cfg_for(c, H, mu=s_["mu"], lam=s_["lam"], delta=s_["delta"], d0=s_["d0"], colony=1)
            polarity = {}
            for facing in ("away", "toward", "random"):
                for age_legs in (1.0, 0.0):
                    p_ = run("measure", ctx.cap, lambda: MR.polarity(one, ctx.iface, sel, seed(), dev, facing=facing,
                                                                     limit_factor=4.0, age_legs=age_legs))
                    polarity[f"{facing}_age{int(age_legs)}"] = MR.polarity_readings(p_)
                p_ = run("measure", ctx.cap, lambda: MR.polarity(one, ctx.iface, sel, seed(), dev, facing=facing,
                                                                 limit_factor=4.0, synthetic=MR.synthetic_slope))
                polarity[f"synthetic_{facing}"] = MR.polarity_readings(p_)
        return {"c": c, "H": H, "seed_none_brief": brief(seed_none), "rows": rows, "widened": widened,
                "chosen": None if win is None else win["setting"], "polarity_reported": polarity, "wording": WORDING,
                "high_level": R["high_level"], "cap_seed": f"{sname}+{variant}",
                "resolved_config_note": "resolved_config is the frame's base configuration; each row's effective "
                                        "setting is its 'setting' and 'config_sha256'",
                "label": "adaptively selected: Amendment 2 was decided after seeing stage-b2 and diagnosis 4 (D179)"}

    return E.run_stage(args, "stage-b3", lambda a, prov: require(a, prov, "stage-a", "stage-b", "stage-b2"), body)


# ============================================================================== Stage A's recheck

def chosen_cfg(earlier: dict, colony: int | None = None):
    """The chosen trail setting: that of the amended selection stage in force (stage-b3 if it ran)."""
    key, b = amended(earlier)
    if not b.get("chosen"):
        raise SystemExit(f"{key} qualified no setting: a report (Amendments 1 and 2)")
    s = b["chosen"]
    return cfg_for(b["c"], b["H"], mu=s["mu"], lam=s["lam"], delta=s["delta"], d0=s["d0"], colony=colony), b["H"]


def cmd_recheck_a(args):
    def body(ctx):
        dev = ctx.args.device
        cfg, H = chosen_cfg(ctx.earlier)
        mk = makers(cfg, ctx.iface, dev)
        sel = ids("selection")
        f = summary(run("measure", ctx.cap, lambda: MR.play(cfg, ctx.iface, mk["follower"], sel, seed(), dev, access="shared")), H)
        wk = summary(run("measure", ctx.cap, lambda: MR.play(cfg, ctx.iface, mk["walk"], sel, seed(), dev, access="none")), H)
        o = load_npz(f"stage-a-c{amended(ctx.earlier)[1]['c']}-H{H}")
        oracle = {"visits": o["oracle.visits"]}
        cond = stage_a_conditions(oracle, f, None, wk, H)
        cond = {k: v for k, v in cond.items() if k[0] in "245"}
        save_npz("recheck-a", {**flat("follower", f), **flat("walk", wk)})
        return {"conditions": cond, "passed": all(v["passed"] for v in cond.values()),
                "brief": {"follower": brief(f), "walk": brief(wk)}}

    return E.run_stage(args, "recheck-a", lambda a, prov: require_selection(a, prov), body)


# ============================================================================== stage C

def criterion2(seed_s, walk_s, oracle_visits, R) -> dict:
    ci = MM.world_ci(seed_s["visits"], walk_s["visits"])
    legs_med = float(np.median(seed_s["legs"]))
    head = float(np.mean(oracle_visits) - np.mean(seed_s["visits"]))
    need = R["headroom_factor"] * R["mde"] * float(np.mean(seed_s["visits"]))
    return {"above_walk": {**ci, "passed": ci["lo95"] > R["lb_min"]},
            "legs_median": {"value": legs_med, "min": R["legs_median_min"], "passed": legs_med >= R["legs_median_min"]},
            "headroom": {"value": head, "min": need, "passed": head >= need}}


def require_recheck_passed(earlier: dict) -> None:
    """Stage C runs only after Stage A's recheck passed, not merely completed (Astra, D178)."""
    if not earlier["recheck-a"].get("passed"):
        raise SystemExit("Stage A's recheck failed: the next (c, H) with Stage B rerun comes first (§6)")


def cmd_stage_c(args):
    def body(ctx):
        require_recheck_passed(ctx.earlier)
        dev = ctx.args.device
        cfg, H = chosen_cfg(ctx.earlier)
        sel = ids("selection")
        con, l1 = load_connectome(), A.load_l1()
        R2 = REGISTERED["criterion2"]
        rc = load_npz("recheck-a")
        walk = {"visits": rc["walk.visits"]}
        oracle_visits = load_npz(f"stage-a-c{amended(ctx.earlier)[1]['c']}-H{H}")["oracle.visits"]
        out, choice = {}, {}
        variants = REGISTERED["variants"] if not SMOKE else REGISTERED["variants"][:2]
        for sname in REGISTERED["seeds"]:
            tried = []
            for v in variants:
                org = organism(con, l1, cfg, sname, v)
                sh = summary(run("measure", ctx.cap, lambda: play_org(cfg, org, sel, dev, access="shared")), H)
                no = summary(run("measure", ctx.cap, lambda: play_org(cfg, org, sel, dev, access="none")), H)
                blind = summary(run("measure", ctx.cap, lambda: play_org(cfg, carrier_variant(con, cfg, v), sel, dev,
                                                                         access="none")), H)
                c2 = criterion2(sh, walk, oracle_visits, R2)
                trail = MM.world_ci(sh["later_leg_rate"], no["later_leg_rate"])
                trail["passed"] = trail["lo95"] > R2["lb_min"]
                ok = c2["above_walk"]["passed"] and c2["legs_median"]["passed"] and c2["headroom"]["passed"] and trail["passed"]
                save_npz(f"stage-c-{sname}-{v}", {**flat("shared", sh), **flat("none", no), **flat("carrier", blind)})
                tried.append({"variant": v, "criterion2": c2, "trail_effect": trail, "passed": bool(ok),
                              "brief": {"shared": brief(sh), "none": brief(no), "carrier_with_variant": brief(blind)}})
                print(f"stage-c {sname} {v}: {'pass' if ok else 'fail'}", flush=True)
                if ok:
                    break
            out[sname] = tried
            win = next((t for t in tried if t["passed"]), None)
            choice[sname] = None if win is None else {"variant": win["variant"],
                                                      "rank": REGISTERED["variants"].index(win["variant"])}
        # the seed rule (§2c): the less engineered variant first; between equal variants the higher
        # later-leg rate with shared trails, a tie (paired interval including 0) to E
        passed = {k: v for k, v in choice.items() if v is not None}
        if not passed:
            seed_choice = None
        elif len(passed) == 1:
            seed_choice = next(iter(passed))
        else:
            ranks = {k: v["rank"] for k, v in passed.items()}
            if ranks["E"] != ranks["S3r3"]:
                seed_choice = min(ranks, key=ranks.get)
            else:
                v = passed["E"]["variant"]
                e = load_npz(f"stage-c-E-{v}")["shared.later_leg_rate"]
                s = load_npz(f"stage-c-S3r3-{v}")["shared.later_leg_rate"]
                ci = MM.world_ci(s, e)
                seed_choice = "S3r3" if ci["lo95"] > 0 else "E"
                choice["tie_check"] = ci
        return {"tried": out, "passed": choice, "seed": seed_choice,
                "variant": None if seed_choice is None else passed[seed_choice]["variant"]}

    return E.run_stage(args, "stage-c", lambda a, prov: require_selection(a, prov, "recheck-a"), body)


# ============================================================================== report

def coefficient(cfg, iface, make, dev, H) -> dict:
    """The replay coefficient: one pre-pass on the selection mazes at coefficient 1; the ratio of the mean
    nose exposure to live peers (shared) to the exposure to the donor. Frozen, with no iteration."""
    sel = ids("selection")
    eps, exc = MR.replay_donors(sel, seed(), int(cfg.world.maze_cells))
    shared = MR.play(cfg, iface, make, sel, seed(), dev, access="shared")
    rep = MR.play_replay(cfg, iface, make, sel, seed(), donor_episodes=eps, coef=1.0, device=dev)
    es = float(np.mean(shared["exposure_sum"] / shared["ticks"][:, None]))
    er = float(np.mean(rep["exposure_sum"] / rep["ticks"][:, None]))
    return {"coef": es / er if er > 0 else float("nan"), "exposure_shared": es, "exposure_donor_at_1": er,
            "donor_exceptions": exc}


def peer_block(cfg, iface, make, rid, dev, H, coef) -> dict:
    """Every access condition on the report mazes, as per-maze summaries."""
    res = {m: summary(MR.play(cfg, iface, make, rid, seed(), dev, access=m), H)
           for m in ("shared", "own", "none", "peers", "scramble")}
    eps, exc = MR.replay_donors(rid, seed(), int(cfg.world.maze_cells))
    rep = MR.play_replay(cfg, iface, make, rid, seed(), donor_episodes=eps, coef=coef, device=dev)
    res["replay"] = summary(rep, H)
    res["replay"]["route_overlap"] = rep["route_overlap"]
    res["_donor_exceptions"] = exc
    return res


def peer_readings(res: dict) -> dict:
    R3 = REGISTERED["criterion3"]
    r = lambda m: res[m]["later_leg_rate"]  # noqa: E731
    out = {"shared_minus_none": MM.world_ci(r("shared"), r("none")), "own_minus_none": MM.world_ci(r("own"), r("none")),
           "shared_minus_own": MM.world_ci(r("shared"), r("own")), "peers_minus_none": MM.world_ci(r("peers"), r("none")),
           "replay_minus_own": MM.world_ci(r("replay"), r("own")), "scramble_minus_own": MM.world_ci(r("scramble"), r("own"))}
    for k in ("shared_minus_none", "own_minus_none"):
        out[k]["passed_0.5"] = out[k]["lo95"] > R3["rate_lb_min"]
    if "later_first_b" in res["shared"]:
        fb = MM.world_ci(res["shared"]["later_first_b"], res["own"]["later_first_b"])
        fb["share_of_own"] = fb["mean"] / float(np.mean(res["own"]["later_first_b"]))
        fb["faster"] = fb["hi95"] < 0
        out["peer_first_b_shared_minus_own"] = fb
    out["exposure"] = {m: {"mean": float(np.mean(res[m]["exposure_mean"])),
                           "zero_share": float(np.mean(res[m]["exposure_zero_share"]))}
                       for m in ("shared", "peers", "replay", "scramble")}
    out["exposure"]["replay_residual_vs_shared"] = out["exposure"]["replay"]["mean"] - out["exposure"]["shared"]["mean"]
    out["route_overlap"] = {"mean": float(np.mean(res["replay"]["route_overlap"])),
                            "median": float(np.median(res["replay"]["route_overlap"]))}
    out["donor_exceptions"] = res["_donor_exceptions"]
    return out


def level_quantiles(cfg, iface, make, dev) -> dict:
    """The goal-channel nose inputs met on route cells (the follower's shared run on the selection mazes)."""
    ev = MR.play(cfg, iface, make, ids("selection"), seed(), dev, access="shared", nose_range=True)
    return ev["nose_range"]


def cmd_report(args):
    def body(ctx):
        dev = ctx.args.device
        cfg, H = chosen_cfg(ctx.earlier)
        one, _ = chosen_cfg(ctx.earlier, colony=1)
        c = ctx.earlier["stage-c"]
        if not c.get("seed"):
            raise SystemExit("Stage C chose no seed: criterion 2 failed (§6)")
        rid = ids("report")
        con, l1 = load_connectome(), A.load_l1()
        org = organism(con, l1, cfg, c["seed"], c["variant"])
        seed_make = lambda: MO.brain(org, dev)  # noqa: E731
        mk = makers(cfg, ctx.iface, dev)
        out, arrays = {}, {}
        # the high-level cap on the seed's own inputs, on the selection mazes, before any report maze (D178)
        nr = run("measure", ctx.cap, lambda: MR.play(cfg, org.iface, seed_make, ids("selection"), seed(), dev,
                                                     access="shared", nose_range=True))["nose_range"]
        out["seed_nose_range_selection"] = nr
        key = amended(ctx.earlier)[0]
        out["seed_high_cap"] = seed_cap(nr, key)
        if not out["seed_high_cap"]["passed"]:
            out["stopped_before_report_mazes"] = True
            out["note"] = "the seed's own inputs exceed the high-level cap: a report (Amendments 1 and 2)"
            return out
        # criterion 4, before any report maze (Astra, D179): the chosen seed and variant at its own levels
        levels = component_levels(nr["quantiles_unoccluded_positive"], key)
        pc = P.ProbeContext(org.ext, org.iface, cfg, device="cpu")
        with acct.category("probe"):
            states = latch_states(org)
            comp = P.component_tests(org.genome, pc, states=states, levels=levels)
            one_nose = one_nose_checks(org.genome, pc, states, levels, REGISTERED[key]["high_level"])
        out["component_tests"] = {"levels": levels, "active": comp["active"], "inactive": comp["inactive"],
                                  "switching": comp["switching"]["passed"], "startup": comp["startup"]["passed"],
                                  "offset": comp["offset"]["passed"],
                                  "active_passed_up_to_high_level": active_passes(comp["active"]["values"], key),
                                  "seed_level_quantiles": nr["quantiles_unoccluded_positive"],
                                  "quantiles_note": "histogram bin upper bounds (bins 2.3% wide), approximate",
                                  "one_nose": one_nose, "latch_states": states,
                                  "note": ("required: active K_D >= 30 up to 0.35, K_D x level >= the registered "
                                           "minimum above it up to the high level, and the one-nose checks; S3r3's "
                                           "inactive limit is reported only")}
        if not (out["component_tests"]["active_passed_up_to_high_level"] and one_nose["passed_up_to_high_level"]):
            out["stopped_before_report_mazes"] = True
            out["note"] = "criterion 4 failed on the selection mazes' levels: a report (Amendment 2)"
            return out
        with acct.category("measure"):
            ctx.cap.check()
            coefs = {"seed": coefficient(cfg, org.iface, seed_make, dev, H),
                     "follower": coefficient(cfg, ctx.iface, mk["follower"], dev, H)}
            ctx.cap.check()
            blocks = {"seed": peer_block(cfg, org.iface, seed_make, rid, dev, H, coefs["seed"]["coef"]),
                      "follower": peer_block(cfg, ctx.iface, mk["follower"], rid, dev, H, coefs["follower"]["coef"])}
            ctx.cap.check()
            base = {n: summary(MR.play(cfg, ctx.iface, mk[n], rid, seed(), dev, access="none"), H) for n in ("oracle", "w2", "walk")}
            base["carrier_with_variant"] = summary(play_org(cfg, carrier_variant(con, cfg, c["variant"]), rid, dev, access="none"), H)
            mk1 = makers(one, ctx.iface, dev)
            single = {"seed": summary(MR.play(one, org.iface, seed_make, rid, seed(), dev, access="own"), H),
                      "follower": summary(MR.play(one, ctx.iface, mk1["follower"], rid, seed(), dev, access="own"), H)}
        for who, res in blocks.items():
            for m, s in res.items():
                if not m.startswith("_"):
                    arrays.update(flat(f"{who}.{m}", s))
        for n, s in {**base, **{f"single_{k}": v for k, v in single.items()}}.items():
            arrays.update(flat(n, s))
        save_npz("report", arrays)
        seed_s = blocks["seed"]["shared"]
        out["criterion2"] = criterion2(seed_s, base["walk"], base["oracle"]["visits"], REGISTERED["criterion2"])
        out["criterion2"]["seed_vs_w2"] = MM.world_ci(seed_s["visits"], base["w2"]["visits"])
        out["criterion2"]["seed_vs_follower"] = MM.world_ci(seed_s["visits"], blocks["follower"]["shared"]["visits"])
        out["criterion3"] = {"follower": peer_readings(blocks["follower"]), "seed": peer_readings(blocks["seed"])}
        out["criterion3"]["seed_trail_effect_above_0"] = out["criterion3"]["seed"]["shared_minus_none"]["lo95"] > 0
        out["replay_coefficients"] = coefs
        out["single_wey"] = {k: brief(v) for k, v in single.items()}
        out["baselines"] = {k: brief(v) for k, v in base.items()}
        out["seed_brief"] = brief(seed_s)
        out["between_maze_cv"] = float(np.std(seed_s["visits"], ddof=1) / np.mean(seed_s["visits"]))
        out["occluded_share"] = {"seed": float(np.mean(seed_s["occluded_share"])),
                                 "follower": float(np.mean(blocks["follower"]["shared"]["occluded_share"]))}
        # the seed's median later leg (the memory assays' delay D is recalibrated to it)
        ev = MR.play(cfg, org.iface, seed_make, rid, seed(), dev, access="shared")
        d = np.concatenate([np.diff(r[r >= 0]) for row in ev["visit_tick"] for r in row if (r >= 0).sum() > 1] or [np.array([])])
        out["seed_median_leg_ticks"] = float(np.median(d)) if len(d) else None
        out["seed"], out["variant"] = c["seed"], c["variant"]
        return out

    return E.run_stage(args, "report", lambda a, prov: require_selection(a, prov, "recheck-a", "stage-c"), body)


# ============================================================================== timing

def cmd_timing(args):
    def body(ctx):
        dev = ctx.args.device
        cfg, H = chosen_cfg(ctx.earlier)
        c = ctx.earlier["stage-c"]
        T = REGISTERED["e3b1"]
        con, l1 = load_connectome(), A.load_l1()
        sname, variant = c.get("seed") or "E", c.get("variant") or "W1"
        org = organism(con, l1, cfg, sname, variant)
        S, Wn = (T["strains"], T["worlds_per_strain"]) if not SMOKE else (4, 2)
        pop = Genome.cat([org.genome] * S)
        ticks = 50 if not SMOKE else 5
        out = {}
        for label, donors in (("plain", False), ("with_replay_donors", True)):
            torch.cuda.reset_peak_memory_stats() if dev != "cpu" else None
            g = moved(pop, dev)
            brain = MO.StartedBrain(g, MO.brain(org).start)
            ids_ = np.tile(np.arange(Wn), S)
            strain_of = torch.arange(S, device=dev).repeat_interleave(Wn).reshape(-1, 1)
            kw = {}
            if donors:
                n = len(ids_)
                ids_ = np.concatenate([ids_, ids_])
                strain_of = torch.cat([strain_of, strain_of])
                kw = {"episodes": np.concatenate([np.zeros(n, dtype=np.int64), np.full(n, 1000)]),
                      "access": ["replay"] * n + ["shared"] * n, "donors": np.concatenate([np.arange(n, 2 * n), np.full(n, -1)]),
                      "replay_coef": np.concatenate([np.ones(n), np.zeros(n)])}
            with acct.category("measure"):
                w = MW.MazeWorld(cfg, org.iface, brain, strain_of, run_seed=seed(), world_ids=ids_, device=dev, **kw)
                for _ in range(3):
                    w.tick()
                if dev != "cpu":
                    torch.cuda.synchronize()
                t0 = time.perf_counter()
                for _ in range(ticks):
                    w.tick()
                if dev != "cpu":
                    torch.cuda.synchronize()
                sec = (time.perf_counter() - t0) / ticks
            out[label] = {"seconds_per_tick": sec, "worlds": int(len(ids_)), "weys": int(cfg.world.weys_per_swarm),
                          "peak_memory_mb": (torch.cuda.max_memory_allocated() / 1e6) if dev != "cpu" else None}
            del w, brain, g
        per_gen_worlds = T["runs_per_arm"] * T["population"] * T["worlds_per_strain"]
        sec_gen = out["plain"]["seconds_per_tick"] * H * per_gen_worlds / (T["strains"] * T["worlds_per_strain"])
        arm_h = sec_gen * T["generations"] / 3600
        total = arm_h * T["training_arms"] * T["reserve_factor"]
        out["projection"] = {"seconds_per_generation_12_runs": sec_gen, "hours_per_training_arm": arm_h,
                             "hours_two_arms_with_reserve": total, "within_24h": total <= T["budget_hours"],
                             "horizon": H, "generations": T["generations"],
                             "note": "training only, linear in worlds; validation and evaluation come on top"}
        return out

    return E.run_stage(args, "timing", lambda a, prov: require_selection(a, prov, "stage-c"), body)


# ============================================================================== smoke and main

def use_smoke(args) -> None:
    global EXP, OUT, SMOKE, GUARDED
    EXP = OUT = ROOT / "runs" / "e3b0-smoke"
    SMOKE = True
    GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PLAN, *E.E1_INPUTS]
    R = REGISTERED  # toy sizes cannot meet the thresholds: the smoke checks the plumbing only
    R["stage_a"].update(oracle_visits_min=0.0, follower_legs_median_min=0.0, w2_share_max=1e9, walk_share_max=1e9,
                        discovery_share_of_H_max=1e9)
    R["stage_b"].update(polarity_min=-1.0, gradient_min=0.0, range_min=0.0, saturated_max=1.0)
    R["criterion2"].update(legs_median_min=0.0, mde=-1e9, lb_min=-1e9)
    R["stage_b2"].update(gradient_min=0.0, high_share_max=1.0, trail_lb_min=-1e9)
    R["stage_b3"].update(gradient_min=0.0, high_share_max=1.0, trail_lb_min=-1e9)
    configure()
    for s in STAGES[STAGES.index(args.command):]:
        for f in (E.record_path(s), E.marker_path(s), E.partial_path(s)):
            if EXP in f.parents:
                f.unlink(missing_ok=True)


COMMANDS = {"stage-a": cmd_stage_a, "stage-b": cmd_stage_b, "stage-b2": cmd_stage_b2, "stage-b3": cmd_stage_b3, "recheck-a": cmd_recheck_a, "stage-c": cmd_stage_c,
            "report": cmd_report, "timing": cmd_timing}


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
    out = ROOT / "runs" / ("e3b0-smoke" if smoke else "e3b0")
    try:
        run_script(main, out_default=str(out), default="measure", name="e3b0")
    finally:
        agg = out / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
