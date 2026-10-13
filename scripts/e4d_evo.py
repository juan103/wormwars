"""The evolutionary E4-D's pilot (docs/E4/E4-D-EVO-DESIGN.md v2.1 §4; exploratory; GPU, after the owner's word).

    python scripts/e4d_evo.py precheck --device cuda   # the positive control on the GPU, selection visibility, timing
    python scripts/e4d_evo.py screen --device cuda     # arm L at the slot factors 0.25, 1, 2, 4; the factor's choice
    python scripts/e4d_evo.py f --device cuda          # arm F at the chosen factor
    add --smoke for toy sizes in runs/e4d-evo-smoke (never results)

**precheck** (design §4, before any training):
- **the positive control,** at the assessment's composition (one genome per batch): the comparator-origin control at
  w = 3, E-G and the oracle on the control block (64 mazes × 2 assignments);
- **selection visibility:** E-G and the comparator-origin controls at w = 0.5, 1 and 2, each on 8 independent draws of
  W mazes, for W in 8, 16, 32 and 64; per W and control, the share of draws on which the control strictly out-ranks E-G
  (eligibility; Astra), with ties counted one half reported beside;
- **the full workload's timing** at each W (both): 3 generations of the screen's actual batch (all its runs, their
  scales, random ties, checkpoint validation), on fresh training ids, with peak memory; the screen's and f's GPU-hours
  projected from it;
- **the formal W:** the smallest W at which the w = 1 control strictly out-ranks E-G on at least 90% of draws **and** the
  projected screen and f fit the cap's remainder; if none, the design stops (D265).

**screen:** arm L (only the 32 slots mutate) at slot factors 0.25, 1, 2 and 4, 4 runs each, 100 generations at the
chosen W, random tie-breaking. Populations and the selections so far are saved every 10 generations and at the last;
the final populations before the lineage replay, which is then checked bitwise. Each run's champion
(`evo_trial.champion`, from the whole final population on the pilot validation block) is assessed on the pilot
assessment block, per maze; E-G on both blocks. **The factor:** the highest median assessment share over all trials,
ties to the smaller factor, excluding any factor whose generation-1 children's entry rate is below 0.95 of the
generation-1 elites' (unchanged copies of E-G on the same mazes; both).

**f:** arm F (weights and τ at 0.25, the module biases at 0.02, the slots at the chosen factor), 4 runs, the same
readings; its champions are assessed beside their own links-cut versions. Kept for the formal run only if its children's
entry rate at generation 1 is at least 0.9 of its elites'.

Each stage refuses unless its predecessor completed under the same code and registration. Every rollout is preceded by
the cap's check, and every result is written to the stage's partial record as it completes.

**Blocks** (maze seed 1 420 000; ids without a qualifying start move to the next unused one): control 53 000-53 063;
visibility draws 53 100-53 611; validation 53 700-53 763; assessment 53 800-53 863; training ids from 70 000 000
(span 10 000 000); the timing's training ids from 90 000 000.
"""

from __future__ import annotations

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
from wormwars import registration as reg  # noqa: E402
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
    "train_base": 70_000_000, "train_span": 10_000_000, "timing_train_base": 90_000_000, "timing_generations": 3,
    "visibility": {"W": [8, 16, 32, 64], "draws": 8, "weights": [0.5, 1.0, 2.0], "rank_share": 0.9},
    "screen": {"factors": [0.25, 1.0, 2.0, 4.0], "runs_per_factor": 4, "G": 100, "checkpoint_every": 10,
               "run_seed_base": 1_420_100, "entry_safeguard": 0.95},
    "f": {"runs": 4, "bias_factor": 0.02, "run_seed_base": 1_420_200, "keep_entry": 0.9},
    "cap_gpu_hours": 6.0,  # the pilot's ceiling inside E4's remaining 25.80 (D258); the owner is told before each stage
    "afford_margin": 0.8,  # the projected screen and f must fit 80% of the cap's remainder
    "rerun_kill_tail_seconds": 900,
}


def configure() -> None:
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, OUT, GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E4-D evo: not completed (the run stopped)",
                  "cap": "E4-D evo: not completed (the cap was reached)"}
    E.RECORD.update({s: s for s in STAGES})
    E.WHAT.update({s: f"the evolutionary E4-D's {s}" for s in STAGES})
    E.task_config = lambda: cfg_for(8)  # the frame's record; each stage also records its own W's configuration


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


def config_record(cfg) -> dict:
    return {"resolved_config": cfg.to_dict(), "resolved_config_sha256": E.config_sha256(cfg)}


def requires(*earlier):
    """A stage's predecessors: completed, under the same code and registration (Astra)."""
    def check(args, prov):
        got = {}
        for stage in earlier:
            rec = json.loads(E.record_path(stage).read_text(encoding="utf-8")) if E.record_path(stage).exists() else None
            if rec is None or rec.get("outcome") != "completed":
                raise SystemExit(f"{stage} has not completed")
            if not SMOKE:
                reg.require_same_code(rec["provenance_at_start"]["git_commit"], GUARDED)
                if rec["registered"] != json.loads(json.dumps(REGISTERED)):
                    raise SystemExit(f"the registration differs from {stage}'s")
            got[stage] = rec
        return got
    return check


def play(ctx, fn, cfg, iface, genome, ids, state: dict, key: str):
    """One rollout, after the cap's check; its readouts written to the partial record at once."""
    ctx.cap.check()
    res = fn(cfg, iface, genome, ids, seed(), ctx.args.device)
    state.setdefault("results", {})[key] = [readout(res, k) for k in range(len(res.real_first))]
    E.write_atomic(E.partial_path(ctx.doc["stage"]), state)
    return res


def screen_runs(cx, factors=None):
    S = REGISTERED["screen"]
    factors = S["factors"] if factors is None else factors
    runs = [{"factor": f, "run": 100 * j + k, "seed": S["run_seed_base"] + 10 * j + k}
            for j, f in enumerate(factors) for k in range(S["runs_per_factor"])]
    scales = {f: AR.combined_scales(cx, bias_factor=0.0, cross_factor=f, inherited=False) for f in factors}
    return runs, scales


def cmd_precheck(args):
    def body(ctx):
        R = REGISTERED
        cfg = cfg_for(8)
        cx = context(cfg)
        org = cx["org"]
        eg = org.genome.select([0])
        state = {"stage": "precheck", "partial": True}
        ctx.salvage = lambda: state
        with acct.category("probe"):
            ids = block("control")
            pc = {name: readout(play(ctx, fn, cfg, org.iface, g, ids, state, f"control:{name}"))
                  for name, fn, g in (("control_w3", ET.trial_rollout(cx), control(cx, 3.0)),
                                      ("eg", ET.trial_rollout(cx), eg),
                                      ("oracle", ET.trial_rollout(cx, b_source="real", check=False), eg))}
            state["positive_control"] = pc
            V, pool = R["visibility"], block("visibility")
            genomes = [eg] + [control(cx, w) for w in V["weights"]]
            vis = state["visibility"] = {}
            for W in V["W"]:
                draws = [pool[d * W:(d + 1) * W] if (d + 1) * W <= len(pool) else np.roll(pool, -(d * W))[:W]
                         for d in range(V["draws"])]
                batch = Genome.cat([g for g in genomes for _ in draws])
                rows = np.stack([dr for _ in genomes for dr in draws])
                t0 = time.perf_counter()
                r = play(ctx, ET.trial_rollout(cx), cfg_for(W), org.iface, batch, rows, state, f"visibility:{W}")
                fit = r.score.mean(axis=1).reshape(len(genomes), V["draws"])
                vis[str(W)] = {"seconds": time.perf_counter() - t0, "eg_fitness": fit[0].tolist(),
                               "controls": {str(w): {"fitness": fit[1 + j].tolist(),
                                                     "outranks_eg_strict": float(np.mean(fit[1 + j] > fit[0])),
                                                     "outranks_eg_ties_half": float(np.mean((fit[1 + j] > fit[0])
                                                                                            + 0.5 * (fit[1 + j] == fit[0])))}
                                            for j, w in enumerate(V["weights"])}}
                E.write_atomic(E.partial_path("precheck"), state)
        with acct.category("selection"):
            runs, scales = screen_runs(cx)
            timing = state["timing"] = {}
            for W in V["W"]:
                c = cfg_for(W)
                start = Genome.cat([eg] * c.evo.population)
                if str(ctx.args.device).startswith("cuda"):
                    torch.cuda.reset_peak_memory_stats()
                t0 = time.perf_counter()
                EV.evolve_batch(c, org.iface, org.genome.spec, [EV.RunSpec(r["run"], r["seed"], 0.0) for r in runs],
                                generations=R["timing_generations"], checkpoint_every=R["screen"]["checkpoint_every"],
                                validation_ids=block("validation")[:W], world_seed=seed(),
                                id_base=R["timing_train_base"], id_span=R["train_span"], device=ctx.args.device,
                                rollout_fn=ET.trial_rollout(cx), check=ctx.cap.check, category=acct.category,
                                initial=lambda r: start, mutation_scales=lambda r: scales[r_factor(runs, r.run)],
                                random_ties=True)
                per_gen = (time.perf_counter() - t0) / R["timing_generations"]
                screen_h = per_gen * R["screen"]["G"] / 3600 * 1.15  # + 15% for validation, assessment and saving
                f_h = screen_h * R["f"]["runs"] / len(runs)
                timing[str(W)] = {"seconds_per_generation": per_gen, "composition": [len(runs) * c.evo.population, 2 * W, 1],
                                  "peak_memory_mb": (torch.cuda.max_memory_allocated() / 2 ** 20
                                                     if str(ctx.args.device).startswith("cuda") else None),
                                  "projected_screen_hours": screen_h, "projected_f_hours": f_h}
                E.write_atomic(E.partial_path("precheck"), state)
        spent = ctx.cap.spent_hours() + (time.perf_counter() - ctx.cap.t_start) / 3600
        left = R["afford_margin"] * (R["cap_gpu_hours"] - spent)
        ok = [W for W in V["W"] if vis[str(W)]["controls"]["1.0"]["outranks_eg_strict"] >= V["rank_share"]
              and timing[str(W)]["projected_screen_hours"] + timing[str(W)]["projected_f_hours"] <= left]
        W = min(ok) if ok else None
        state.update({"W": W, "affordable_hours": left, "spent_hours_at_choice": spent,
                      **(config_record(cfg_for(W)) if W else {})})
        state["outcome_reading"] = ("W fixed" if W is not None else
                                    "no tested W is both visible and affordable: the design stops")
        state.pop("partial", None)
        return state

    return E.run_stage(args, "precheck", requires(), body)


def r_factor(runs: list, run: int) -> float:
    return next(r["factor"] for r in runs if r["run"] == run)


def _save_selections(path: Path, selections: list, runs: list, P: int) -> None:
    arrays = {}
    for i, r in enumerate(runs):
        sl = slice(i * P, (i + 1) * P)
        for k in ("score", "real_first", "decoy_first", "neither"):
            arrays[f"{k}_run{r['run']:03d}"] = np.stack([s[k][sl] for s in selections])
    np.savez_compressed(path, **arrays)


def _train(ctx, cx, runs: list, scale_of, W: int, tag: str, state: dict) -> dict:
    """One evolve_batch over `runs`, random ties; populations and selections saved every checkpoint and at the last;
    finals saved before the lineage replay, which is checked bitwise; logs, validation curves and parents saved."""
    R = REGISTERED
    P_ = R["screen"]
    cfg = cfg_for(W)
    org = cx["org"]
    P = cfg.evo.population
    start = Genome.cat([org.genome.select([0])] * P)
    specs = [EV.RunSpec(r["run"], r["seed"], 0.0) for r in runs]
    inner = ET.trial_rollout(cx)

    def checked(*a, **k):
        res = inner(*a, **k)
        assert np.all(res.progress == 0), "the trial rollout's progress must be zero"
        return res

    cap = LI.Capture(checked)
    snaps = tuple(sorted(set(range(0, P_["G"], P_["checkpoint_every"])) | {P_["G"] - 1}))
    pdir = OUT / "pilot"
    pdir.mkdir(parents=True, exist_ok=True)

    def on_checkpoint(records, g):
        for rec in records:
            if g in rec.snapshots:
                save_population(pdir / f"{tag}-run{rec.spec.run:03d}-gen{g:03d}.npz", rec.snapshots[g], cfg=cfg,
                                run=rec.spec.run, generation=g)
        _save_selections(pdir / f"{tag}-selections.npz", cap.selections, runs, P)
        state[f"{tag}_progress"] = {"generation": g, "selections": f"runs/e4d-evo/pilot/{tag}-selections.npz"}
        E.write_atomic(E.partial_path(ctx.doc["stage"]), state)

    ctx.after_fail = lambda: _save_selections(pdir / f"{tag}-selections.npz", cap.selections, runs, P)
    t0 = time.perf_counter()
    recs = EV.evolve_batch(cfg, org.iface, org.genome.spec, specs, generations=P_["G"],
                           checkpoint_every=P_["checkpoint_every"], validation_ids=block("validation")[:W],
                           world_seed=seed(), id_base=R["train_base"], id_span=R["train_span"], device=ctx.args.device,
                           rollout_fn=cap, check=ctx.cap.check, category=acct.category,
                           initial=lambda r: start, mutation_scales=lambda r: scale_of(r.run),
                           on_checkpoint=on_checkpoint, snapshot_at=snaps, random_ties=True)
    seconds = time.perf_counter() - t0
    for rec in recs:  # before the replay, so a failure there loses nothing
        save_population(pdir / f"{tag}-run{rec.spec.run:03d}-final.npz", rec.final, cfg=cfg, run=rec.spec.run)
    _save_selections(pdir / f"{tag}-selections.npz", cap.selections, runs, P)
    rep = LI.replay(cfg, specs, cap.selections, initial=lambda r: start, mutation_scales=lambda r: scale_of(r.run),
                    device=ctx.args.device, random_ties=True)
    for rec, rp in zip(recs, rep):
        if not all(torch.equal(getattr(rec.final, k), getattr(rp["final"], k)) for k in ("w", "bias", "tau", "g")):
            raise RuntimeError(f"run {rec.spec.run}: the lineage replay differs from the run")
        AR.assert_frozen(start, rec.final, scale_of(rec.spec.run))
    np.savez_compressed(pdir / f"{tag}-parents.npz",
                        **{f"source_run{rp['run']:03d}": np.array([p["source"] for p in rp["parents"]]) for rp in rep},
                        **{f"child_run{rp['run']:03d}": np.array([p["child"] for p in rp["parents"]]) for rp in rep})
    state[f"{tag}_logs"] = {str(rec.spec.run): {"log": rec.log, "checkpoints": [
        {k: c[k] for k in ("generation", "validation_mean", "validation_counts", "sha256")} for c in rec.checkpoints],
        "generation0_train_ids": rec.generation0.get("train_ids")} for rec in recs}
    return {"records": recs, "replay": rep, "selections": cap.selections, "seconds": seconds, "cfg": cfg}


def _entry(sel: dict, i: int, P: int, W: int, rows) -> float:
    n = sel["neither"][i * P:(i + 1) * P][rows]
    return float(1 - n.mean() / (2 * W))


def _assess(ctx, cx, tr: dict, runs: list, W: int, state: dict, tag: str, cut_too: bool = False) -> list:
    """Each run's champion from its whole final population on the validation block, then on the assessment block, per
    maze; the generation-1 entry rates of the children against the elites, on the same mazes."""
    org = cx["org"]
    cfg = cfg_for(W)
    slots = AR.slot_indices(cx)
    P, El = cfg.evo.population, cfg.evo.elites
    pdir = OUT / "pilot"
    out = []
    for i, (rec, rp, r) in enumerate(zip(tr["records"], tr["replay"], runs)):
        final = rec.final
        val = play(ctx, ET.trial_rollout(cx), cfg, org.iface, final, block("validation"), state, f"{tag}:val:{r['run']}")
        fit = tr["selections"][-1]["score"][i * P:(i + 1) * P].mean(axis=1)
        norm = final.w[:, slots].norm(dim=1).cpu().numpy()
        k = ET.champion(val.score.mean(axis=1), fit, norm)
        champ = final.select([k])
        conds = Genome.cat([champ] + ([AR.cut(champ, slots)] if cut_too else []))
        a = play(ctx, ET.trial_rollout(cx), cfg, org.iface, conds, block("assessment"), state, f"{tag}:assess:{r['run']}")
        np.savez_compressed(pdir / f"{tag}-run{r['run']:03d}-assessment.npz", validation=val.score, assessment=a.score)
        sel1 = tr["selections"][1] if len(tr["selections"]) > 1 else tr["selections"][0]
        ties = [float(np.mean([np.sum(s["score"][i * P:(i + 1) * P].mean(axis=1) == x) > 1
                               for x in s["score"][i * P:(i + 1) * P].mean(axis=1)])) for s in tr["selections"]]
        out.append({**r, "champion_index": k, "champion_sha256": genome_hash(champ, 0),
                    "validation_shares": np.round(val.score.mean(axis=1), 6).tolist(),
                    "assessment": readout(a, 0), "assessment_links_cut": readout(a, 1) if cut_too else None,
                    "slot_weights": np.round(champ.w[0, slots].cpu().numpy(), 6).tolist(),
                    "lineage_mutations": LI.mutations(rp["parents"], k),
                    "entry_elites_generation1": _entry(sel1, i, P, W, slice(0, El)),
                    "entry_children_generation1": _entry(sel1, i, P, W, slice(El, P)),
                    "fitness_curve": [float(s["score"][i * P:(i + 1) * P].mean(axis=1).max()) for s in tr["selections"]],
                    "tie_share_curve": np.round(ties, 4).tolist()})
        state[f"{tag}_assessed"] = out
        E.write_atomic(E.partial_path(ctx.doc["stage"]), state)
    return out


def cmd_screen(args):
    def body(ctx):
        W = ctx.earlier["precheck"]["W"]
        if W is None:
            raise SystemExit("the precheck fixed no W: the design stops")
        S = REGISTERED["screen"]
        cfg = cfg_for(W)
        cx = context(cfg)
        runs, scales = screen_runs(cx)
        state = {"stage": "screen", "partial": True, "W": W, **config_record(cfg)}
        ctx.salvage = lambda: state
        tr = _train(ctx, cx, runs, lambda run: scales[r_factor(runs, run)], W, "L", state)
        with acct.category("holdout"):
            per_run = _assess(ctx, cx, tr, runs, W, state, "L")
            eg = cx["org"].genome.select([0])
            state["eg"] = {b: readout(play(ctx, ET.trial_rollout(cx), cfg, cx["org"].iface, eg, block(b), state,
                                           f"eg:{b}")) for b in ("validation", "assessment")}
        by_factor = {}
        for f in S["factors"]:
            rs = [x for x in per_run if x["factor"] == f]
            by_factor[str(f)] = {"median_assessment": float(np.median([x["assessment"]["real_first_all"] for x in rs])),
                                 "entry_children_generation1": float(np.mean([x["entry_children_generation1"] for x in rs])),
                                 "entry_elites_generation1": float(np.mean([x["entry_elites_generation1"] for x in rs]))}
        ok = [f for f in S["factors"] if by_factor[str(f)]["entry_children_generation1"]
              >= S["entry_safeguard"] * by_factor[str(f)]["entry_elites_generation1"]]
        state.update({"runs": per_run, "by_factor": by_factor,
                      "factor": max(ok, key=lambda f: (by_factor[str(f)]["median_assessment"], -f)) if ok else None,
                      "training_seconds": tr["seconds"], "composition": [len(runs) * cfg.evo.population, 2 * W, 1],
                      "note": "exploratory (design v2.1 §4); the formal runs are fresh"})
        state.pop("partial", None)
        return state

    return E.run_stage(args, "screen", requires("precheck"), body)


def cmd_f(args):
    def body(ctx):
        sc = ctx.earlier["screen"]
        if sc.get("factor") is None:
            raise SystemExit("the screen chose no factor")
        W, f = int(sc["W"]), float(sc["factor"])
        F_ = REGISTERED["f"]
        cfg = cfg_for(W)
        cx = context(cfg)
        runs = [{"factor": f, "run": 900 + k, "seed": F_["run_seed_base"] + k} for k in range(F_["runs"])]
        sc_f = AR.combined_scales(cx, bias_factor=F_["bias_factor"], cross_factor=f)
        state = {"stage": "f", "partial": True, "W": W, "factor": f, **config_record(cfg)}
        ctx.salvage = lambda: state
        tr = _train(ctx, cx, runs, lambda run: sc_f, W, "F", state)
        with acct.category("holdout"):
            per_run = _assess(ctx, cx, tr, runs, W, state, "F", cut_too=True)
        el = float(np.mean([x["entry_elites_generation1"] for x in per_run]))
        ch = float(np.mean([x["entry_children_generation1"] for x in per_run]))
        state.update({"runs": per_run, "entry_elites_generation1": el, "entry_children_generation1": ch,
                      "keep_for_formal": bool(ch >= F_["keep_entry"] * el), "training_seconds": tr["seconds"],
                      "note": "exploratory (design v2.1 §4, §8)"})
        state.pop("partial", None)
        return state

    return E.run_stage(args, "f", requires("precheck", "screen"), body)


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
    R["timing_generations"] = 2
    R["screen"].update({"factors": [1.0, 4.0], "runs_per_factor": 1, "G": 3, "checkpoint_every": 2})
    R["f"].update({"runs": 1})
    R["cap_gpu_hours"] = 1e6
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
