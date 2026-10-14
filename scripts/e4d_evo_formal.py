"""The evolutionary E4-D's formal run, as the bound pre-registration fixes it
(`experiments/E4-two-minds/E4-D-evo/PREREGISTRATION.md`, bound at c3fe432, D274). GPU, after the owner's word.

    python scripts/e4d_evo_formal.py check --device cuda --owner-word "<the owner's words and date>"
    python scripts/e4d_evo_formal.py train-l --device cuda      # then evaluate-l, report-l
    python scripts/e4d_evo_formal.py train-f --device cuda      # then evaluate-f, report-f
    python scripts/e4d_evo_formal.py train-s --device cuda --owner-word "..."   # only if report-l triggers S
    add --smoke for toy sizes in runs/e4d-evo-formal-smoke (never results)
    a rerun after an infrastructure stop: --rerun --reason "infrastructure: <the cause>"

**The stages and their dependencies** are §5's table (`evo_formal.DEPENDS`); every stage refuses unless its
predecessors completed under the same code, registration and environment (`check`'s), and unless the pinned files
(§2) hash as registered.
- **`check`:** the pre-flight of every block; the positive control (the comparator-origin control at w = 3, E-G and
  the oracle) on the check block; the formal evaluation path on the control (its cue-removed, cue-fixed and cut
  versions and E-G, with every per-maze balance assertion; reversed beside); the pilot's replay (11 generations of the
  screen's batch, snapshot at index 10, against `screen.json`'s generation-10 checkpoint hashes and the local `gen010`
  populations' registered digest); the formal composition's timing (3 generations of L's batch), whose projection
  `train-l` must pass.
- **`train-<arm>`:** the arm's runs in one batch, W = 8, G = 100, random ties; populations and selections saved every
  10 generations and at the last, each saved population checked against the frozen set; the final populations saved
  before the lineage replay, which must match bitwise.
- **`evaluate-<arm>`:** per run, the champion from the whole final population on its validation block, then on its test
  block, one genome per batch: intact, reversed, removed, fixed, cut and E-G (and S₀ for S), per maze, with the
  registered assertions.
- **`report-<arm>`:** the readings, only through `evo_stats` (`evo_formal.report`, `improvement_report`).

**Failures** (§5): a registered assertion (`evo_formal.IntegrityError`, the rollout's integrity check, a non-finite
fitness) records the stage "not evaluable" and is never rerun; an infrastructure stop is rerun once, with a reason
naming the cause; the caps are per group (`check` and L 8 GPU-hours, F 1.5, S 6), each counting its own attempts.
"""

from __future__ import annotations

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
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e4 import arms as AR  # noqa: E402
from wormwars.e4 import evo_formal as FM  # noqa: E402
from wormwars.e4 import evo_stats as ES  # noqa: E402
from wormwars.e4 import evo_trial as ET  # noqa: E402
from wormwars.e4 import lineage as LI  # noqa: E402
from wormwars.e4 import trial as TL  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.evo.genomes import genome_hash, load_population, save_population  # noqa: E402


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


E = _load("e2_for_e4d_evo_formal", "e2.py")  # E2's stage frame, configured for these folders
X = _load("e3c_for_e4d_evo_formal", "e3c.py")  # E3c's base configuration

PREREG = "experiments/E4-two-minds/E4-D-evo/PREREGISTRATION.md"
PILOT_DIR = ROOT / "experiments" / "E4-two-minds" / "E4-D-evo"
EXP = PILOT_DIR / "formal"
OUT_ROOT = ROOT / "runs" / "e4d-evo-formal"
SMOKE_ROOT = ROOT / "runs" / "e4d-evo-formal-smoke"
PILOT_POPS = ROOT / "runs" / "e4d-evo" / "pilot"
PINNED = {
    "docs/E4/E4-D-EVO-DESIGN.md": "f61427e59e6d58cedb6979cfe252fae0bb5bd257219dd8a604b178bc068f2af4",
    "docs/E4/E4-D-DESIGN.md": "84016143855b511018c386c943ac6db57ba4cda27e9a03c0fe9dbdb070add49b",
    "experiments/E4-two-minds/E4-D-evo/precheck.json": "d30506c306f4911455bace0ba4b773aac0e026c12a8eca34dadfd87c5a3c11c3",
    "experiments/E4-two-minds/E4-D-evo/screen.json": "efcbf2c931e55c0e1270e54b44711a9efc3b68534cd39b9660ac80bad75b42a5",
    "experiments/E4-two-minds/E4-D-evo/f.json": "4a6cbab8f5140c7f41a661fd15528304ed60e4e1d4c8c186be9ef6bb5cde5640",
    "experiments/E4-two-minds/E4-D-evo/power.json": "85df1b7adb72570a83c231fe78a4f029c5b2106ba38ef147f874dce90c5a45c2",
}
PILOT_DIGEST = "e5a300013c12ba7b23338cdba9569249e41fa4a1e12ffb9977e7c08c8b5da9b5"
PILOT_RUNS = [{"factor": f, "run": 100 * j + k, "seed": 1_420_100 + 10 * j + k}
              for j, f in enumerate((0.25, 1.0, 2.0, 4.0)) for k in range(4)]
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PREREG, *PINNED]
STAGES = list(FM.DEPENDS)
SMOKE = False
REGISTERED = {
    "preregistration": PREREG, "bound_at": "c3fe432", "maze_seed": FM.MAZE_SEED, "sigma_D": 6.0, "H_t": 600,
    "ga": {"population": 32, "elites": 3, "truncation": 8,
           "mutation": {"w_sigma": 0.08, "tau_sigma": 0.15, "bias_sigma": 0.05, "p_mutate": 1.0}},
    "W": 8, "G": 100, "checkpoint_every": 10, "slot_factor": 0.25, "f_bias_factor": 0.02, "s_weight": 0.5,
    "runs": dict(FM.N_RUNS), "seed_base": FM.SEED_BASE, "caps": dict(FM.CAPS),
    "control_threshold": 0.75, "timing": {"generations": 3, "overhead": 1.2, "share_of_remainder": 0.8},
    "replay": {"generations": 11, "snapshot": 10, "train_base": 70_000_000, "train_span": 10_000_000,
               "checkpoint_ids": [53_700, 53_708], "pilot_digest": PILOT_DIGEST},
    "rerun_kill_tail_seconds": 900,
}


def group_of(stage: str) -> str:
    return FM.GROUP[stage]


def out_dir(stage: str) -> Path:
    return (SMOKE_ROOT if SMOKE else OUT_ROOT) / group_of(stage)


def configure(stage: str) -> None:
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, out_dir(stage), GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E4-D evo formal: not completed (the run stopped)",
                  "cap": "E4-D evo formal: not completed (the cap was reached)",
                  "integrity": "E4-D evo formal: not evaluable (a registered assertion failed)"}
    E.RECORD.update({s: s for s in STAGES})
    E.WHAT.update({s: f"the evolutionary E4-D's formal {s}" for s in STAGES})
    E.task_config = lambda: cfg_for(REGISTERED["W"])
    cap = REGISTERED["caps"][group_of(stage)]

    def clock():
        if (E.OUT / "compute").exists():
            acct.write_aggregate(E.OUT / "compute", E.OUT / "compute.json")
        return reg.CapClock(cap, E.OUT / "compute.json")

    E.clock = clock
    E._not_completed = _not_completed


_frame_not_completed = E._not_completed


def _not_completed(path, doc, ctx, reason, error, t0):
    """The frame's record of a stop, with a registered assertion's failure recorded as "not evaluable" and final (the
    frame reruns only "stopped" records)."""
    if reason == "stopped" and FM.is_integrity(error):
        reason = "integrity"
        doc["final"] = True
    return _frame_not_completed(path, doc, ctx, reason, error, t0)


def cfg_for(W: int):
    R = REGISTERED
    cfg = TL.trial_config(sigma=R["sigma_D"], horizon=R["H_t"], base=X.base_config())
    g = R["ga"]
    cfg.evo.population, cfg.evo.elites, cfg.evo.truncation = g["population"], g["elites"], g["truncation"]
    cfg.evo.worlds_per_strain = int(W)
    for k, v in g["mutation"].items():
        setattr(cfg.mutation, k, v)
    return cfg


def context(cfg):
    return AR.context(load_connectome(), A.load_l1(), cfg.brain)


def eg_of(cx) -> Genome:
    return cx["org"].genome.select([0])


def s0_of(cx) -> Genome:
    return TL.control_genome(eg_of(cx), cx, "comparator", REGISTERED["s_weight"])


def scales_of(cx, arm: str) -> dict:
    f = REGISTERED["slot_factor"]
    if arm == "F":
        return AR.combined_scales(cx, bias_factor=REGISTERED["f_bias_factor"], cross_factor=f)
    return AR.combined_scales(cx, bias_factor=0.0, cross_factor=f, inherited=False)


def start_of(cx, arm: str) -> Genome:
    return s0_of(cx) if arm == "S" else eg_of(cx)


def check_pinned() -> None:
    if SMOKE:
        return
    for p, want in PINNED.items():
        got = reg.file_sha256(ROOT / p)
        if got != want:
            raise SystemExit(f"{p} does not hash as registered ({got[:12]} against {want[:12]}): refusing")


OWNER_STAGES = ("check", "train-s")


def owner_word(args, stage: str) -> str | None:
    """§0.4: the owner's word before `check` and before S, recorded; checked before anything starts."""
    if stage in OWNER_STAGES and not SMOKE:
        if not args.owner_word or not args.owner_word.strip():
            raise SystemExit(f"{stage} needs --owner-word: the owner's words and their date (§0.4)")
        return args.owner_word.strip()
    return None


def requires(stage: str):
    """§5's table: each predecessor completed, under the same code, registration and environment (`check`'s)."""
    def check(args, prov):
        check_pinned()
        got = {}
        for s in FM.DEPENDS[stage]:
            path = E.record_path(s)
            rec = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
            if rec is None or rec.get("outcome") != "completed":
                raise SystemExit(f"{s} has not completed")
            if not SMOKE:
                reg.require_same_code(rec["provenance_at_start"]["git_commit"], GUARDED)
                if rec["registered"] != json.loads(json.dumps(REGISTERED)):
                    raise SystemExit(f"the registration differs from {s}'s")
            got[s] = rec
        if stage != "check":
            chk = E.record_path("check")
            if not chk.exists():
                raise SystemExit("check has not run")
            c = json.loads(chk.read_text(encoding="utf-8"))
            if not SMOKE:
                reg.require_same_env(c["provenance_at_start"], prov)
        if stage == "train-l" and not got["check"].get("timing", {}).get("within_cap"):
            raise SystemExit("check's timing projection exceeds the L cap's allowance: an amendment is needed, and the "
                             "owner decides (§5)")
        if stage == "train-s" and not FM.s_triggered(got["report-l"]["reading"]):
            raise SystemExit(f"S is not triggered: L reads {got['report-l']['reading'].get('state')!r}")
        return got
    return check


def readout(res, k: int = 0) -> dict:
    out = {"real_first": int(res.real_first[k]), "decoy_first": int(res.decoy_first[k]), "neither": int(res.neither[k])}
    n = sum(out.values())
    out.update(trials=n, real_first_all=out["real_first"] / n, entry_rate=(n - out["neither"]) / n)
    if res.real_first_maze is not None:
        out["per_maze"] = {"real_first": res.real_first_maze[k].tolist(), "decoy_first": res.decoy_first_maze[k].tolist()}
    return out


def play(ctx, cx, cfg, genome, ids, *, a_source="real", b_source="sum", check=True):
    """One rollout, after the cap's check; the rollout's integrity error raised as an `IntegrityError`."""
    ctx.cap.check()
    try:
        return ET.trial_rollout(cx, a_source=a_source, b_source=b_source, check=check)(
            cfg, cx["org"].iface, genome, ids, FM.MAZE_SEED, ctx.args.device)
    except RuntimeError as e:
        if str(e).startswith("integrity:"):
            raise FM.IntegrityError(str(e)) from e
        raise


def evaluate_conditions(ctx, cx, cfg, champ: Genome, ids, *, arm: str | None, start: Genome | None = None) -> dict:
    """The test block's conditions, one genome per batch, with the registered assertions (§5): per maze, the removed,
    fixed, cut and E-G conditions balanced; an L or S champion cut equal to E-G, bitwise."""
    slots = AR.slot_indices(cx)
    eg = eg_of(cx)
    cut = AR.cut(champ, slots)
    cut_is_eg = all(torch.equal(getattr(cut, k).cpu(), getattr(eg, k).cpu()) for k in ("w", "bias", "tau", "g"))
    if arm in ("L", "S") and not cut_is_eg:
        raise FM.IntegrityError(f"an {arm} champion with its slots cut is not E-G")
    out = {}
    for name, src in FM.CONDITIONS.items():
        res = play(ctx, cx, cfg, champ, ids, a_source=src)
        out[name] = readout(res)
        if name in FM.BALANCED:
            FM.assert_balanced(res.real_first_maze, res.decoy_first_maze, f"{name}")
    for name, g in (("cut", cut), ("eg", eg)) + ((("start", start),) if start is not None else ()):
        res = play(ctx, cx, cfg, g, ids)
        out[name] = readout(res)
        if name in FM.BALANCED:
            FM.assert_balanced(res.real_first_maze, res.decoy_first_maze, name)
    return out


def checked_rollout(cx, allowed):
    """Training's rollout: the resolved ids checked against their range, integrity errors as `IntegrityError`, zero
    progress asserted."""
    inner = ET.trial_rollout(cx)

    def fn(cfg, iface, genome, world_ids, run_seed, device="cpu", **kw):
        allowed(ET.qualifying(np.asarray(world_ids), run_seed))
        try:
            res = inner(cfg, iface, genome, world_ids, run_seed, device, **kw)
        except RuntimeError as e:
            if str(e).startswith("integrity:"):
                raise FM.IntegrityError(str(e)) from e
            raise
        if not np.all(res.progress == 0):
            raise FM.IntegrityError("the trial rollout's progress is not zero")
        return res
    return fn


def save_selections(path: Path, selections: list, runs: list, P: int) -> None:
    arrays = {}
    for i, r in enumerate(runs):
        sl = slice(i * P, (i + 1) * P)
        for k in ("score", "real_first", "decoy_first", "neither"):
            arrays[f"{k}_run{r['run']:03d}"] = np.stack([s[k][sl] for s in selections])
    np.savez_compressed(path, **arrays)


def population_digest(hashes: list[str]) -> str:
    return hashlib.sha256("".join(hashes).encode()).hexdigest()


def compare_replay(snapshots: dict, checkpoints: dict, screen: dict, local: dict | None) -> dict:
    """§5.1's replay comparison. `snapshots`: run → the replay's generation-10 strain hashes; `checkpoints`: run → the
    replay's generation-10 checkpoint sha256; `screen`: the pilot's record; `local`: run → the local `gen010` file's
    strain hashes, or None where absent. Raises `IntegrityError` on any mismatch."""
    snap = REGISTERED["replay"]["snapshot"]
    out = {"checkpoints": {}, "populations": "not compared"}
    for r in PILOT_RUNS:
        want = next(c["sha256"] for c in screen["L_logs"][str(r["run"])]["checkpoints"] if c["generation"] == snap)
        if checkpoints[r["run"]] != want:
            raise FM.IntegrityError(f"replay: run {r['run']}'s generation-{snap} checkpoint differs from the pilot's")
        out["checkpoints"][str(r["run"])] = want
    if local is not None:
        for r in PILOT_RUNS:
            if snapshots[r["run"]] != local[r["run"]]:
                raise FM.IntegrityError(f"replay: run {r['run']}'s generation-{snap} population differs from the pilot's")
        digest = population_digest([population_digest(local[r["run"]]) for r in PILOT_RUNS])
        if digest != REGISTERED["replay"]["pilot_digest"]:
            raise FM.IntegrityError("the local generation-10 populations do not match the registered digest")
        out["populations"] = "equal, bitwise (strain hashes), and the registered digest matches"
    return out


def local_gen010() -> dict | None:
    snap = REGISTERED["replay"]["snapshot"]
    files = {r["run"]: PILOT_POPS / f"L-run{r['run']:03d}-gen{snap:03d}.npz" for r in PILOT_RUNS}
    if not all(f.exists() for f in files.values()):
        return None
    out = {}
    for run, f in files.items():
        z = np.load(f, allow_pickle=False)
        out[run] = json.loads(str(z["meta"]))["genome_sha256s"]
    return out


def timing_ok(per_gen_seconds: float, spent_hours: float, cap_hours: float) -> dict:
    T = REGISTERED["timing"]
    projected = per_gen_seconds * REGISTERED["G"] * T["overhead"] / 3600
    allowance = T["share_of_remainder"] * (cap_hours - spent_hours)
    return {"seconds_per_generation": per_gen_seconds, "projected_hours": projected, "allowance_hours": allowance,
            "within_cap": bool(projected <= allowance)}


# ----------------------------------------------------------------------------- the stages

def cmd_check(args):
    def body(ctx):
        state = {"stage": "check", "partial": True, "owner_word": owner_word(args, "check")}
        ctx.salvage = lambda: state
        cfg = cfg_for(REGISTERED["W"])
        cx = context(cfg)
        eg = eg_of(cx)
        state["preflight"] = FM.preflight(FM.all_blocks(), lambda ids: ET.qualifying(ids, FM.MAZE_SEED))
        E.write_atomic(E.partial_path("check"), state)
        with acct.category("probe"):
            ids = FM.CHECK_IDS
            ctl = TL.control_genome(eg, cx, "comparator", 3.0)
            pc = {"control_w3": readout(play(ctx, cx, cfg, ctl, ids)), "eg": readout(play(ctx, cx, cfg, eg, ids)),
                  "oracle": readout(play(ctx, cx, cfg, eg, ids, b_source="real", check=False))}
            FM.assert_balanced([pc["eg"]["per_maze"]["real_first"]], [pc["eg"]["per_maze"]["decoy_first"]], "E-G")
            if pc["control_w3"]["real_first_all"] < REGISTERED["control_threshold"]:
                raise FM.IntegrityError(f"the positive control made {pc['control_w3']['real_first_all']:.3f}, below "
                                        f"{REGISTERED['control_threshold']}")
            state["positive_control"] = pc
            state["evaluation_path"] = evaluate_conditions(ctx, cx, cfg, ctl, ids, arm=None)
            E.write_atomic(E.partial_path("check"), state)
        with acct.category("selection"):
            state["replay"] = replay_pilot(ctx, cx, cfg) if not SMOKE else "smoke: not replayed"
            E.write_atomic(E.partial_path("check"), state)
            state["timing"] = time_formal(ctx, cx, cfg)
        state.pop("partial", None)
        return state

    return E.run_stage(args, "check", requires("check"), body)


def replay_pilot(ctx, cx, cfg) -> dict:
    Rp = REGISTERED["replay"]
    eg = eg_of(cx)
    start = Genome.cat([eg] * cfg.evo.population)
    scales = {f: AR.combined_scales(cx, bias_factor=0.0, cross_factor=f, inherited=False)
              for f in sorted({r["factor"] for r in PILOT_RUNS})}
    specs = [EV.RunSpec(r["run"], r["seed"], 0.0) for r in PILOT_RUNS]
    factor = {r["run"]: r["factor"] for r in PILOT_RUNS}
    recs = EV.evolve_batch(cfg, cx["org"].iface, cx["org"].genome.spec, specs, generations=Rp["generations"],
                           checkpoint_every=REGISTERED["checkpoint_every"],
                           validation_ids=np.arange(*Rp["checkpoint_ids"]), world_seed=FM.MAZE_SEED,
                           id_base=Rp["train_base"], id_span=Rp["train_span"], device=ctx.args.device,
                           rollout_fn=LI.Capture(ET.trial_rollout(cx)), check=ctx.cap.check, category=acct.category,
                           initial=lambda r: start, mutation_scales=lambda r: scales[factor[r.run]],
                           snapshot_at=(Rp["snapshot"],), random_ties=True)
    snaps = {rec.spec.run: [genome_hash(rec.snapshots[Rp["snapshot"]], i)
                            for i in range(rec.snapshots[Rp["snapshot"]].n_strains)] for rec in recs}
    cks = {rec.spec.run: next(c["sha256"] for c in rec.checkpoints if c["generation"] == Rp["snapshot"]) for rec in recs}
    screen = json.loads((PILOT_DIR / "screen.json").read_text(encoding="utf-8"))
    return compare_replay(snaps, cks, screen, local_gen010())


def time_formal(ctx, cx, cfg) -> dict:
    T = REGISTERED["timing"]
    runs = FM.runs("L")
    eg = eg_of(cx)
    start = Genome.cat([eg] * cfg.evo.population)
    sc = scales_of(cx, "L")
    if str(ctx.args.device).startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()

    def allowed(ids):
        ids = np.asarray(ids)
        if not np.all(((ids >= FM.TIMING[0]) & (ids < FM.TIMING[1])) | np.isin(ids, FM.CHECKPOINT_IDS)):
            raise FM.IntegrityError("timing ids outside their range")

    t0 = time.perf_counter()
    EV.evolve_batch(cfg, cx["org"].iface, cx["org"].genome.spec, [EV.RunSpec(r["run"], r["seed"], 0.0) for r in runs],
                    generations=T["generations"], checkpoint_every=REGISTERED["checkpoint_every"],
                    validation_ids=FM.CHECKPOINT_IDS, world_seed=FM.MAZE_SEED, id_base=FM.TIMING[0],
                    id_span=FM.TIMING[1] - FM.TIMING[0], device=ctx.args.device, rollout_fn=checked_rollout(cx, allowed),
                    check=ctx.cap.check, category=acct.category, initial=lambda r: start,
                    mutation_scales=lambda r: sc, random_ties=True)
    per_gen = (time.perf_counter() - t0) / T["generations"]
    spent = ctx.cap.spent_hours() + (time.perf_counter() - ctx.cap.t_start) / 3600
    out = timing_ok(per_gen, spent, REGISTERED["caps"]["l"])
    out.update(composition=[len(runs) * cfg.evo.population, 2 * REGISTERED["W"], 1],
               peak_memory_mb=(torch.cuda.max_memory_allocated() / 2 ** 20
                               if str(ctx.args.device).startswith("cuda") else None))
    return out


def pop_path(arm: str, run: int, tag: str) -> Path:
    return out_dir(f"train-{arm.lower()}") / "populations" / f"{arm}-run{run:03d}-{tag}.npz"


def cmd_train(args, arm: str):
    stage = f"train-{arm.lower()}"

    def body(ctx):
        state = {"stage": stage, "partial": True, "owner_word": owner_word(args, stage)}
        ctx.salvage = lambda: state
        W, G, every = REGISTERED["W"], REGISTERED["G"], REGISTERED["checkpoint_every"]
        cfg = cfg_for(W)
        cx = context(cfg)
        runs = FM.runs(arm)
        P = cfg.evo.population
        s0 = start_of(cx, arm)
        start = Genome.cat([s0] * P)
        sc = scales_of(cx, arm)
        specs = [EV.RunSpec(r["run"], r["seed"], 0.0) for r in runs]
        cap = LI.Capture(checked_rollout(cx, FM.check_ids))
        snaps = tuple(sorted(set(range(0, G, every)) | {G - 1}))
        pdir = pop_path(arm, 0, "x").parent
        pdir.mkdir(parents=True, exist_ok=True)
        sel_path = pdir / f"{arm}-selections.npz"

        def on_checkpoint(records, g):
            for rec in records:
                if g in rec.snapshots:
                    try:
                        AR.assert_frozen(start, rec.snapshots[g], sc)
                    except AssertionError as e:
                        raise FM.IntegrityError(f"run {rec.spec.run}, generation {g}: {e}") from e
                    save_population(pop_path(arm, rec.spec.run, f"gen{g:03d}"), rec.snapshots[g], cfg=cfg,
                                    run=rec.spec.run, generation=g)
            save_selections(sel_path, cap.selections, runs, P)
            state["progress"] = {"generation": g}
            E.write_atomic(E.partial_path(stage), state)

        ctx.after_fail = lambda: save_selections(sel_path, cap.selections, runs, P)
        t0 = time.perf_counter()
        recs = EV.evolve_batch(cfg, cx["org"].iface, cx["org"].genome.spec, specs, generations=G,
                               checkpoint_every=every, validation_ids=FM.CHECKPOINT_IDS, world_seed=FM.MAZE_SEED,
                               id_base=FM.TRAIN[0], id_span=FM.TRAIN[1] - FM.TRAIN[0], device=ctx.args.device,
                               rollout_fn=cap, check=ctx.cap.check, category=acct.category,
                               initial=lambda r: start, mutation_scales=lambda r: sc, on_checkpoint=on_checkpoint,
                               snapshot_at=snaps, random_ties=True)
        seconds = time.perf_counter() - t0
        for rec in recs:
            save_population(pop_path(arm, rec.spec.run, "final"), rec.final, cfg=cfg, run=rec.spec.run)
        save_selections(sel_path, cap.selections, runs, P)
        rep = LI.replay(cfg, specs, cap.selections, initial=lambda r: start, mutation_scales=lambda r: sc,
                        device=ctx.args.device, random_ties=True)
        for rec, rp in zip(recs, rep):
            if not all(torch.equal(getattr(rec.final, k), getattr(rp["final"], k)) for k in ("w", "bias", "tau", "g")):
                raise FM.IntegrityError(f"run {rec.spec.run}: the lineage replay differs from the run")
            try:
                AR.assert_frozen(start, rec.final, sc)
            except AssertionError as e:
                raise FM.IntegrityError(f"run {rec.spec.run}, final: {e}") from e
        np.savez_compressed(pdir / f"{arm}-parents.npz",
                            **{f"source_run{rp['run']:03d}": np.array([p["source"] for p in rp["parents"]]) for rp in rep},
                            **{f"child_run{rp['run']:03d}": np.array([p["child"] for p in rp["parents"]]) for rp in rep})
        state.update(runs=[{**r, "final_sha256": [genome_hash(rec.final, i) for i in range(rec.final.n_strains)],
                            "log": rec.log, "checkpoints": [{k: c[k] for k in ("generation", "validation_mean", "sha256")}
                                                            for c in rec.checkpoints]} for r, rec in zip(runs, recs)],
                     start_sha256=genome_hash(s0, 0), training_seconds=seconds,
                     composition=[len(runs) * P, 2 * W, 1], selections=str(sel_path.relative_to(ROOT)))
        state.pop("partial", None)
        return state

    return E.run_stage(args, stage, requires(stage), body)


def cmd_evaluate(args, arm: str):
    stage = f"evaluate-{arm.lower()}"

    def body(ctx):
        state = {"stage": stage, "partial": True, "runs": []}
        ctx.salvage = lambda: state
        cfg = cfg_for(REGISTERED["W"])
        cx = context(cfg)
        spec = cx["org"].genome.spec
        tr = ctx.earlier[f"train-{arm.lower()}"]
        slots = AR.slot_indices(cx)
        P = cfg.evo.population
        sel = np.load(pop_path(arm, 0, "x").parent / f"{arm}-selections.npz", allow_pickle=False)
        s0 = s0_of(cx) if arm == "S" else None
        with acct.category("holdout"):
            for r, rt in zip(FM.runs(arm), tr["runs"]):
                final, _ = load_population(pop_path(arm, r["run"], "final"), spec, cfg.brain, ctx.args.device)
                if [genome_hash(final, i) for i in range(final.n_strains)] != rt["final_sha256"]:
                    raise FM.IntegrityError(f"run {r['run']}'s saved final population differs from the training record")
                v_ids, t_ids = FM.blocks(arm, r["run"])
                val = play(ctx, cx, cfg, final, v_ids)
                fit = sel[f"score_run{r['run']:03d}"][-1].mean(axis=1)
                norm = final.w[:, slots.to(final.w.device)].norm(dim=1).cpu().numpy()
                k = ET.champion(val.score.mean(axis=1), fit, norm)
                champ = final.select([k])
                test = evaluate_conditions(ctx, cx, cfg, champ, t_ids, arm=arm, start=s0)
                state["runs"].append({**r, "champion_index": k, "champion_sha256": genome_hash(champ, 0),
                                      "validation_shares": np.round(val.score.mean(axis=1), 6).tolist(),
                                      "slot_weights": np.round(champ.w[0, slots.to(champ.w.device)].cpu().numpy(),
                                                               6).tolist(),
                                      "test": {c: v for c, v in test.items() if c != "start"},
                                      **({"start": test["start"]} if "start" in test else {})})
                E.write_atomic(E.partial_path(stage), state)
        state.pop("partial", None)
        return state

    return E.run_stage(args, stage, requires(stage), body)


JOINT = {(ES.STATES[3], ES.IMPROVEMENT_STATES[0]): "transfer not detected from zero; the GA improved a seeded weak link, "
                                                    "at this budget",
         (ES.STATES[3], ES.IMPROVEMENT_STATES[1]): "transfer not detected from zero, and no improvement on a seeded weak "
                                                    "link detected, at this budget",
         (ES.STATES[4], ES.IMPROVEMENT_STATES[0]): "discovery from zero unresolved; the GA improved a seeded weak link, "
                                                    "at this budget",
         (ES.STATES[4], ES.IMPROVEMENT_STATES[1]): "discovery from zero unresolved; no improvement on a seeded weak link "
                                                    "detected, at this budget"}


def cmd_report(args, arm: str):
    stage = f"report-{arm.lower()}"

    def body(ctx):
        ev = ctx.earlier[f"evaluate-{arm.lower()}"]
        out = FM.report(arm, ev["runs"])
        out["label"] = {"L": "confirmatory", "F": "secondary", "S": "secondary, after seeded initialization"}[arm]
        if arm == "S":
            out["against_start"] = FM.improvement_report(ev["runs"])
            lrep = json.loads(E.record_path("report-l").read_text(encoding="utf-8"))
            out["joint"] = JOINT[(lrep["reading"]["state"], out["against_start"]["reading"]["state"])]
        return out

    return E.run_stage(args, stage, requires(stage), body)


COMMANDS = {"check": cmd_check,
            **{f"train-{a.lower()}": (lambda a: lambda args: cmd_train(args, a))(a) for a in "LFS"},
            **{f"evaluate-{a.lower()}": (lambda a: lambda args: cmd_evaluate(args, a))(a) for a in "LFS"},
            **{f"report-{a.lower()}": (lambda a: lambda args: cmd_report(args, a))(a) for a in "LFS"}}


def use_smoke(args) -> None:
    """Toy sizes in their own folders; never results."""
    global EXP, SMOKE
    EXP = SMOKE_ROOT / "records"
    SMOKE = True
    R = REGISTERED
    R["H_t"], R["G"], R["checkpoint_every"], R["W"] = 40, 3, 2, 2
    R["ga"].update({"population": 6, "elites": 2, "truncation": 3})
    R["control_threshold"] = 0.0
    R["timing"]["generations"] = 2
    R["caps"] = {"l": 1e6, "f": 1e6, "s": 1e6}
    FM.N_RUNS.update({"L": 2, "F": 2, "S": 2})
    FM.MAZES, FM.TRIALS = 2, 4
    FM.CHECK_IDS = np.arange(54_000, 54_002)
    FM.CHECKPOINT_IDS = np.arange(54_100, 54_102)
    R["runs"] = dict(FM.N_RUNS)


def main():
    import argparse
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=list(COMMANDS))
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--guarded", action="store_true")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--reason")
    ap.add_argument("--owner-word")
    args = ap.parse_args()
    if args.rerun:
        FM.check_rerun_reason(args.reason)
    if args.smoke:
        use_smoke(args)
    owner_word(args, args.command)  # before the frame writes a start marker
    configure(args.command)
    COMMANDS[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    if any(a == "--out" or a.startswith("--out=") for a in sys.argv[1:]):
        raise SystemExit("--out is not accepted: the formal run writes only to its own folders")
    smoke = "--smoke" in sys.argv
    cmd = next((a for a in sys.argv[1:] if a in FM.DEPENDS), None)
    if cmd is None:
        raise SystemExit(f"a stage is required: {list(FM.DEPENDS)}")
    od = (SMOKE_ROOT if smoke else OUT_ROOT) / FM.GROUP[cmd]
    try:
        run_script(main, out_default=str(od), default="measure", name="e4d-evo-formal")
    finally:
        agg = od / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / f"compute-record-{FM.GROUP[cmd]}.json").write_text(agg.read_text(encoding="utf-8"),
                                                                        encoding="utf-8", newline="\n")
