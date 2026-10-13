"""The evolutionary E4-D's pilot (docs/E4/E4-D-EVO-DESIGN.md v2.1 §4; exploratory; GPU, after the owner's word).

    python scripts/e4d_evo.py precheck --device cuda   # the positive control on the GPU, selection visibility, timing
    python scripts/e4d_evo.py screen --device cuda     # arm L at the slot factors 0.25, 1, 2, 4; the factor's choice
    python scripts/e4d_evo.py f --device cuda          # arm F at the chosen factor
    add --smoke for toy sizes in runs/e4d-evo-smoke (never results)

**precheck** (design §4, before any training):
- the comparator-origin control at w = 3, E-G and the oracle on the control block (64 mazes × 2 assignments), with the
  integrity check on E-G;
- selection visibility: E-G and the comparator-origin controls at w = 0.5, 1 and 2, each on 8 independent draws of W
  mazes, for W in 8, 16, 32 and 64; per W and control, the share of draws on which the control out-ranks E-G (a tie
  counts one half, as random tie-breaking would break it). **The formal W is the smallest at which the w = 1 control
  out-ranks E-G on at least 90% of draws;** if none, the design stops (D265);
- timing and memory: one generation of 8 runs × 32 strains at each W.

**screen:** arm L (only the 32 slots mutate) at slot factors 0.25, 1, 2 and 4, 4 runs each, 100 generations at the
chosen W, random tie-breaking, populations saved every 10 generations. Each run's champion (`evo_trial.champion`, from
the whole final population on the pilot validation block) is assessed on the pilot assessment block, with E-G on both.
**The factor:** the highest median assessment share over all trials, ties to the smaller factor, excluding any factor
whose generation-1 children's entry rate is below 0.95 of E-G's.

**f:** arm F (weights and τ at 0.25, the module biases at 0.02, the slots at the chosen factor), 4 runs, the same
readings; its champions are assessed beside their own links-cut versions.

**Blocks** (maze seed 1 420 000, the evolutionary E4-D's own; mazes without a qualifying start move to the next id):
control 53 000-53 063; visibility draws 53 100-53 611; validation 53 700-53 763; assessment 53 800-53 863; training ids
from 70 000 000 (span 10 000 000).
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars.brain import Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e4 import arms as AR  # noqa: E402
from wormwars.e4 import evo_trial as ET  # noqa: E402
from wormwars.e4 import lineage as LI  # noqa: E402
from wormwars.e4 import trial as TL  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.evo.genomes import genome_hash, save_population  # noqa: E402


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


E = _load("e2_for_e4d_evo", "e2.py")  # E2's stage frame, configured for this pilot's own folders
X = _load("e3c_for_e4d_evo", "e3c.py")  # E3c's base configuration (Task N, checked against E1's gate)

EXP = ROOT / "experiments" / "E4-two-minds" / "E4-D-evo"
OUT = ROOT / "runs" / "e4d-evo"
SMOKE_DIR = ROOT / "runs" / "e4d-evo-smoke"
DESIGN = "docs/E4/E4-D-EVO-DESIGN.md"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", DESIGN, "docs/E4/E4-D-DESIGN.md"]
SMOKE = False
STAGES = ["precheck", "screen", "f"]
REGISTERED = {
    "design": DESIGN, "maze_seed": 1_420_000, "sigma_D": 6.0, "H_t": 600,
    "ga": {"population": 32, "elites": 3, "truncation": 8,
           "mutation": {"w_sigma": 0.08, "tau_sigma": 0.15, "bias_sigma": 0.05, "p_mutate": 1.0}},
    "blocks": {"control": [53_000, 53_064], "visibility": [53_100, 53_612], "validation": [53_700, 53_764],
               "assessment": [53_800, 53_864]},
    "train_base": 70_000_000, "train_span": 10_000_000,
    "visibility": {"W": [8, 16, 32, 64], "draws": 8, "weights": [0.5, 1.0, 2.0], "rank_share": 0.9},
    "timing_runs": 8,
    "screen": {"factors": [0.25, 1.0, 2.0, 4.0], "runs_per_factor": 4, "G": 100, "checkpoint_every": 10,
               "run_seed_base": 1_420_100, "entry_safeguard": 0.95},
    "f": {"runs": 4, "bias_factor": 0.02, "run_seed_base": 1_420_200, "keep_entry": 0.9},
    "cap_gpu_hours": 6.0,  # the pilot's ceiling inside E4's remaining 25.80 (D258); the owner is told before each stage
    "rerun_kill_tail_seconds": 900,
}


def configure() -> None:
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, OUT, GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E4-D evo: not completed (the run stopped)",
                  "cap": "E4-D evo: not completed (the cap was reached)"}
    E.RECORD.update({s: s for s in STAGES})
    E.WHAT.update({s: f"the evolutionary E4-D's {s}" for s in STAGES})
    E.task_config = lambda: cfg_for(8)


def cfg_for(W: int):
    R = REGISTERED
    cfg = TL.trial_config(sigma=R["sigma_D"], horizon=R["H_t"], base=X.base_config())
    g = R["ga"]
    cfg.evo.population, cfg.evo.elites, cfg.evo.truncation = g["population"], g["elites"], g["truncation"]
    cfg.evo.worlds_per_strain = int(W)
    for k, v in g["mutation"].items():
        setattr(cfg.mutation, k, v)
    return cfg


configure()


def seed() -> int:
    return REGISTERED["maze_seed"]


def block(name: str) -> np.ndarray:
    return np.arange(*REGISTERED["blocks"][name])


def context(cfg):
    return AR.context(load_connectome(), A.load_l1(), cfg.brain)


def control(cx, w: float) -> Genome:
    return TL.control_genome(cx["org"].genome.select([0]), cx, "comparator", w)


def readout(res, k: int = 0) -> dict:
    n = int(res.real_first[k] + res.decoy_first[k] + res.neither[k])
    return {"trials": n, "real_first": int(res.real_first[k]), "decoy_first": int(res.decoy_first[k]),
            "neither": int(res.neither[k]), "real_first_all": float(res.real_first[k]) / n,
            "entry_rate": float(n - res.neither[k]) / n}


def cmd_precheck(args):
    def body(ctx):
        dev = ctx.args.device
        R = REGISTERED
        cfg = cfg_for(8)
        cx = context(cfg)
        org = cx["org"]
        eg = org.genome.select([0])
        out = {"composition": {}}
        with acct.category("probe"):
            ids = block("control")
            res = ET.trial_rollout(cx)(cfg, org.iface, Genome.cat([eg, control(cx, 3.0)]), ids, seed(), dev)
            orc = ET.trial_rollout(cx, b_source="real", check=False)(cfg, org.iface, eg, ids, seed(), dev)
            out["positive_control"] = {"eg": readout(res, 0), "control_w3": readout(res, 1), "oracle": readout(orc, 0),
                                       "integrity": "held (the rollout raises otherwise)"}
            out["composition"]["positive_control"] = [2, len(ids) * 2, 1]
            ctx.doc.update(out)
            vis, pool = {}, block("visibility")
            V = R["visibility"]
            genomes = [eg] + [control(cx, w) for w in V["weights"]]
            for W in V["W"]:
                draws = [pool[(d * W) % len(pool):][:W] if (d * W) % len(pool) + W <= len(pool)
                         else np.roll(pool, -(d * W))[:W] for d in range(V["draws"])]
                batch = Genome.cat([g for g in genomes for _ in draws])
                rows = np.stack([dr for _ in genomes for dr in draws])
                t0 = time.perf_counter()
                r = ET.trial_rollout(cx)(cfg_for(W), org.iface, batch, rows, seed(), dev)
                fit = r.score.mean(axis=1).reshape(len(genomes), V["draws"])
                vis[str(W)] = {"seconds": time.perf_counter() - t0, "eg_fitness": fit[0].tolist(),
                               "controls": {str(w): {"fitness": fit[1 + j].tolist(),
                                                     "outranks_eg": float(np.mean((fit[1 + j] > fit[0])
                                                                                  + 0.5 * (fit[1 + j] == fit[0])))}
                                            for j, w in enumerate(V["weights"])}}
            out["visibility"] = vis
            ok = [W for W in V["W"] if vis[str(W)]["controls"]["1.0"]["outranks_eg"] >= V["rank_share"]]
            out["W"] = min(ok) if ok else None
            timing = {}
            for W in V["W"]:
                n = R["timing_runs"] * R["ga"]["population"]
                g = Genome.cat([eg] * n)
                if str(dev).startswith("cuda"):
                    torch.cuda.reset_peak_memory_stats()
                t0 = time.perf_counter()
                ET.trial_rollout(cx)(cfg_for(W), org.iface, g, np.stack([block("validation")[:W]] * n), seed(), dev)
                timing[str(W)] = {"seconds_per_generation_8_runs": time.perf_counter() - t0,
                                  "peak_memory_mb": (torch.cuda.max_memory_allocated() / 2 ** 20
                                                     if str(dev).startswith("cuda") else None)}
            out["timing"] = timing
        out["outcome"] = ("W fixed" if out["W"] is not None
                          else "no tested W lets the w = 1 control out-rank E-G on 90% of draws: the design stops")
        return out

    return E.run_stage(args, "precheck", lambda a, prov: {}, body)


def _train(ctx, cx, runs: list, scale_of, W: int, tag: str, state: dict) -> dict:
    """One evolve_batch over `runs` ({"run", "seed", ...}), random ties, saved every checkpoint; per run its final
    population, captured selections and replayed lineage (checked bitwise)."""
    dev = ctx.args.device
    P_ = REGISTERED["screen"]
    cfg = cfg_for(W)
    org = cx["org"]
    start = Genome.cat([org.genome.select([0])] * cfg.evo.population)
    specs = [EV.RunSpec(r["run"], r["seed"], 0.0) for r in runs]
    cap = LI.Capture(ET.trial_rollout(cx))
    snaps = tuple(range(0, P_["G"], P_["checkpoint_every"]))
    pdir = OUT / "pilot"
    pdir.mkdir(parents=True, exist_ok=True)

    def on_checkpoint(records, g):
        for rec in records:
            if g in rec.snapshots:
                save_population(pdir / f"{tag}-run{rec.spec.run:03d}-gen{g:03d}.npz", rec.snapshots[g], cfg=cfg,
                                run=rec.spec.run, generation=g)
        state[f"{tag}_progress"] = {"generation": g}
        E.write_atomic(E.partial_path(ctx.doc["stage"]), state)

    t0 = time.perf_counter()
    recs = EV.evolve_batch(cfg, org.iface, org.genome.spec, specs, generations=P_["G"],
                           checkpoint_every=P_["checkpoint_every"], validation_ids=block("validation")[:W],
                           world_seed=seed(), id_base=REGISTERED["train_base"], id_span=REGISTERED["train_span"],
                           device=dev, rollout_fn=cap, check=ctx.cap.check, category=acct.category,
                           initial=lambda r: start, mutation_scales=lambda r: scale_of(r.run),
                           on_checkpoint=on_checkpoint, snapshot_at=snaps, random_ties=True)
    seconds = time.perf_counter() - t0
    rep = LI.replay(cfg, specs, cap.selections, initial=lambda r: start, mutation_scales=lambda r: scale_of(r.run),
                    device=dev, random_ties=True)
    for rec, rp in zip(recs, rep):
        if not all(torch.equal(getattr(rec.final, k), getattr(rp["final"], k)) for k in ("w", "bias", "tau", "g")):
            raise RuntimeError(f"run {rec.spec.run}: the lineage replay differs from the run")
        save_population(pdir / f"{tag}-run{rec.spec.run:03d}-final.npz", rec.final, cfg=cfg, run=rec.spec.run)
    return {"records": recs, "replay": rep, "selections": cap.selections, "seconds": seconds, "cfg": cfg}


def _assess(ctx, cx, tr: dict, runs: list, W: int, cut_too: bool = False) -> list:
    """Each run's champion from its whole final population on the validation block, then on the assessment block."""
    dev = ctx.args.device
    org = cx["org"]
    cfg = cfg_for(W)
    slots = AR.slot_indices(cx)
    P = cfg.evo.population
    out = []
    for i, (rec, rp, r) in enumerate(zip(tr["records"], tr["replay"], runs)):
        ctx.cap.check()
        final = rec.final
        val = ET.trial_rollout(cx)(cfg, org.iface, final, block("validation"), seed(), dev)
        last = tr["selections"][-1]
        fit = last["score"][i * P:(i + 1) * P].mean(axis=1)
        norm = final.w[:, slots].norm(dim=1).cpu().numpy()
        k = ET.champion(val.score.mean(axis=1), fit, norm)
        champ = final.select([k])
        conds = [champ] + ([AR.cut(champ, slots)] if cut_too else [])
        a = ET.trial_rollout(cx)(cfg, org.iface, Genome.cat(conds), block("assessment"), seed(), dev)
        entry = []
        for g, sel in enumerate(tr["selections"][:2]):
            n = sel["neither"][i * P:(i + 1) * P]
            entry.append(float(1 - n.mean() / (2 * W)) if g == 0 else
                         float(1 - n[REGISTERED["ga"]["elites"]:].mean() / (2 * W)))
        ties = [float(np.mean([np.sum(s["score"][i * P:(i + 1) * P].mean(axis=1) == x) > 1
                               for x in s["score"][i * P:(i + 1) * P].mean(axis=1)])) for s in tr["selections"]]
        out.append({**r, "champion_index": k, "champion_sha256": genome_hash(champ, 0),
                    "validation_shares": np.round(val.score.mean(axis=1), 6).tolist(),
                    "assessment": readout(a, 0), "assessment_links_cut": readout(a, 1) if cut_too else None,
                    "slot_weights": np.round(champ.w[0, slots].cpu().numpy(), 6).tolist(),
                    "lineage_mutations": LI.mutations(rp["parents"], k),
                    "entry_rate_generation0": entry[0], "entry_rate_children_generation1": entry[1] if len(entry) > 1 else None,
                    "fitness_curve": [float(s["score"][i * P:(i + 1) * P].mean(axis=1).max()) for s in tr["selections"]],
                    "tie_share_curve": np.round(ties, 4).tolist()})
    return out


def cmd_screen(args):
    def body(ctx):
        import json
        W = json.loads(E.record_path("precheck").read_text(encoding="utf-8")).get("W")
        if W is None:
            raise SystemExit("the precheck fixed no W: the design stops")
        S = REGISTERED["screen"]
        cfg = cfg_for(W)
        cx = context(cfg)
        runs = [{"factor": f, "run": 100 * j + k, "seed": S["run_seed_base"] + 10 * j + k}
                for j, f in enumerate(S["factors"]) for k in range(S["runs_per_factor"])]
        factor_of = {r["run"]: r["factor"] for r in runs}
        scales = {f: AR.combined_scales(cx, bias_factor=0.0, cross_factor=f, inherited=False) for f in S["factors"]}
        state = {"stage": "screen", "partial": True, "W": W}
        ctx.salvage = lambda: state
        tr = _train(ctx, cx, runs, lambda run: scales[factor_of[run]], W, "L", state)
        with acct.category("holdout"):
            per_run = _assess(ctx, cx, tr, runs, W)
            eg = ET.trial_rollout(cx)(cfg, cx["org"].iface, cx["org"].genome.select([0]), block("assessment"), seed(),
                                      ctx.args.device)
        by_factor = {}
        for f in S["factors"]:
            rs = [x for x in per_run if x["factor"] == f]
            by_factor[str(f)] = {"median_assessment": float(np.median([x["assessment"]["real_first_all"] for x in rs])),
                                 "entry_children_generation1": float(np.mean([x["entry_rate_children_generation1"] for x in rs])),
                                 "entry_generation0": float(np.mean([x["entry_rate_generation0"] for x in rs]))}
        ok = [f for f in S["factors"]
              if by_factor[str(f)]["entry_children_generation1"] >= S["entry_safeguard"] * by_factor[str(f)]["entry_generation0"]]
        choice = (max(ok, key=lambda f: (by_factor[str(f)]["median_assessment"], -f)) if ok else None)
        return {"W": W, "runs": per_run, "by_factor": by_factor, "eg_assessment": readout(eg, 0),
                "factor": choice, "training_seconds": tr["seconds"],
                "composition": [len(runs) * cfg.evo.population, W * 2, 1],
                "note": "exploratory (design v2.1 §4); the formal runs are fresh"}

    return E.run_stage(args, "screen", lambda a, prov: {}, body)


def cmd_f(args):
    def body(ctx):
        import json
        sc = json.loads(E.record_path("screen").read_text(encoding="utf-8"))
        if sc.get("factor") is None:
            raise SystemExit("the screen chose no factor")
        W, f = int(sc["W"]), float(sc["factor"])
        F_ = REGISTERED["f"]
        cfg = cfg_for(W)
        cx = context(cfg)
        runs = [{"factor": f, "run": 900 + k, "seed": F_["run_seed_base"] + k} for k in range(F_["runs"])]
        sc_f = AR.combined_scales(cx, bias_factor=F_["bias_factor"], cross_factor=f)
        state = {"stage": "f", "partial": True}
        ctx.salvage = lambda: state
        tr = _train(ctx, cx, runs, lambda run: sc_f, W, "F", state)
        with acct.category("holdout"):
            per_run = _assess(ctx, cx, tr, runs, W, cut_too=True)
        g0 = float(np.mean([x["entry_rate_generation0"] for x in per_run]))
        g1 = float(np.mean([x["entry_rate_children_generation1"] for x in per_run]))
        return {"W": W, "factor": f, "runs": per_run, "entry_generation0": g0, "entry_children_generation1": g1,
                "keep_for_formal": bool(g1 >= F_["keep_entry"] * g0), "training_seconds": tr["seconds"],
                "note": "exploratory (design v2.1 §4, §8)"}

    return E.run_stage(args, "f", lambda a, prov: {}, body)


def use_smoke(args) -> None:
    global EXP, OUT, SMOKE
    EXP = OUT = SMOKE_DIR
    SMOKE = True
    R = REGISTERED
    R["H_t"] = 40
    R["ga"].update({"population": 6, "elites": 2, "truncation": 3})
    R["blocks"] = {"control": [53_000, 53_002], "visibility": [53_100, 53_116], "validation": [53_700, 53_702],
                   "assessment": [53_800, 53_802]}
    R["visibility"].update({"W": [2], "draws": 2, "rank_share": 0.0})
    R["timing_runs"] = 1
    R["screen"].update({"factors": [1.0, 4.0], "runs_per_factor": 1, "G": 3, "checkpoint_every": 2})
    R["f"].update({"runs": 1})
    configure()
    for s in STAGES[STAGES.index(args.command):]:
        files = [E.record_path(s), E.marker_path(s), E.partial_path(s)]
        files += [E.rerun_note(E.record_path(s))] + [E.attempt1(f) for f in list(files)]
        for f in files:
            if EXP in f.parents:
                f.unlink(missing_ok=True)


COMMANDS = {"precheck": cmd_precheck, "screen": cmd_screen, "f": cmd_f}


def main():
    import argparse
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
    if any(a == "--out" or a.startswith("--out=") for a in sys.argv[1:]):
        raise SystemExit("--out is not accepted: the pilot writes only to its own folders")
    smoke = "--smoke" in sys.argv
    out_dir = ROOT / "runs" / ("e4d-evo-smoke" if smoke else "e4d-evo")
    try:
        run_script(main, out_default=str(out_dir), default="measure", name="e4d-evo")
    finally:
        agg = out_dir / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
