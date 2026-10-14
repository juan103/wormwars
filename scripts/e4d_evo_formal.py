"""The evolutionary E4-D's formal run, as the bound pre-registration fixes it
(`experiments/E4-two-minds/E4-D-evo/PREREGISTRATION.md`, bound at c3fe432, D274; Amendment 1, D276). GPU, after the
owner's word.

    python scripts/e4d_evo_formal.py check --device cuda --owner-word "<the owner's words and date>"
    python scripts/e4d_evo_formal.py train-l --device cuda      # then evaluate-l, report-l
    python scripts/e4d_evo_formal.py train-f --device cuda      # then evaluate-f, report-f
    python scripts/e4d_evo_formal.py train-s --device cuda --owner-word "..."   # only if report-l triggers S
    add --smoke for toy sizes in runs/e4d-evo-formal-smoke (never results; its own maze seed, seeds and ids)
    a rerun after an infrastructure stop: --rerun --reason "infrastructure: <the cause>"

**Provenance, before any stage starts** (both reviewers, D276): the pinned files hash as registered; the
pre-registration is the bound text with only additions after it (amendments are appended), committed; the registered
rule, its tests and `power.json` are unchanged since binding; the code (`wormwars`, `scripts`, `configs`,
`requirements.txt`) is unchanged since the formal commit that Amendment 1 records; a rerun's code and environment equal
its first attempt's.

**The stages and their dependencies** are §5's table (`evo_formal.DEPENDS`); every stage refuses unless its
predecessors completed under the same code, registration and environment (`check`'s).
- **`check`:** the pre-flight of every block; the positive control (the comparator-origin control at w = 3, E-G and
  the oracle) on the check block; the formal evaluation path on the control (its cue-removed, cue-fixed and cut
  versions and E-G, with every per-maze balance assertion; reversed beside); the pilot's replay (11 generations of the
  screen's batch, snapshot at index 10, against `screen.json`'s generation-10 checkpoint hashes and the local `gen010`
  populations, loaded and hashed from their arrays); the formal composition's timing (3 generations of L's batch).
- **`train-<arm>`:** the arm's runs in one batch, W = 8, G = 100, random ties; populations, selections and checkpoint
  records saved every 10 generations and at the last (selections atomically), each saved population checked against
  the frozen set; the final populations saved before the lineage replay, which must match bitwise. `train-l`
  recomputes the timing projection against L's clock before every attempt.
- **`evaluate-<arm>`:** per run, the saved final population and selections checked against the training record; the
  champion from the whole final population on its validation block; on its test block, one genome per batch: intact,
  reversed, removed, fixed, cut and E-G (and S₀ for S), per maze, each saved before its assertion; the descriptives of
  §7.4 (tie shares, parent-pool turnover, the champion's lineage mutations); a complete arm, checked.
- **`report-<arm>`:** the readings, only through `evo_stats` (`evo_formal.report`, `improvement_report`), on a complete
  arm.

**Failures** (§5): a registered assertion (`evo_formal.IntegrityError`, the rollout's integrity check, a non-finite
fitness) records the stage "not evaluable" and is never rerun; an infrastructure stop is rerun once, with a reason
naming the cause, and the first attempt's files are kept beside as `-attempt1`; the caps are per group (`check` and L 8
GPU-hours, F 1.5, S 6), each counting its own attempts. An arm that is "not evaluable" or "not completed" has no
report: its state is the outcome of its last stage's record.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
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
BOUND = "c3fe432"
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
BOUND_FILES = ["wormwars/e4/evo_stats.py", "tests/test_e4d_evo_stats.py", "experiments/E4-two-minds/E4-D-evo/power.json"]
CODE = ["wormwars", "scripts", "configs", "requirements.txt"]
PILOT_DIGEST = "e5a300013c12ba7b23338cdba9569249e41fa4a1e12ffb9977e7c08c8b5da9b5"
PILOT_RUNS = [{"factor": f, "run": 100 * j + k, "seed": 1_420_100 + 10 * j + k}
              for j, f in enumerate((0.25, 1.0, 2.0, 4.0)) for k in range(4)]
GUARDED = [*CODE, *PINNED]  # the pre-registration is checked append-only instead (Fable, D276)
FORMAL_COMMIT_RE = re.compile(r"\*\*The formal code's commit:\*\* `([0-9a-f]{7,40})`")
STAGES = list(FM.DEPENDS)
OWNER_STAGES = ("check", "train-s")
SMOKE = False
REGISTERED = {
    "preregistration": PREREG, "bound_at": BOUND, "amendment": 1, "maze_seed": FM.MAZE_SEED, "sigma_D": 6.0,
    "H_t": 600, "ga": {"population": 32, "elites": 3, "truncation": 8,
                       "mutation": {"w_sigma": 0.08, "tau_sigma": 0.15, "bias_sigma": 0.05, "p_mutate": 1.0}},
    "W": 8, "G": 100, "checkpoint_every": 10, "slot_factor": 0.25, "f_bias_factor": 0.02, "s_weight": 0.5,
    "runs": dict(FM.N_RUNS), "seed_base": FM.SEED_BASE, "caps": dict(FM.CAPS),
    "blocks": {"check": [int(FM.CHECK_IDS[0]), int(FM.CHECK_IDS[-1])],
               "checkpoints": [int(FM.CHECKPOINT_IDS[0]), int(FM.CHECKPOINT_IDS[-1])], "bases": dict(FM.BASES),
               "train": list(FM.TRAIN), "timing": list(FM.TIMING)},
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


# ----------------------------------------------------------------------------- provenance

def _lf(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


def check_pinned() -> None:
    if SMOKE:
        return
    for p, want in PINNED.items():
        got = reg.file_sha256(ROOT / p)
        if got != want:
            raise SystemExit(f"{p} does not hash as registered ({got[:12]} against {want[:12]}): refusing")


def prereg_append_only(bound_text: bytes, now_text: bytes) -> None:
    """The pre-registration as bound, with only additions after it (dated amendments are appended; Fable, D276)."""
    if not _lf(now_text).startswith(_lf(bound_text).rstrip(b"\n")):
        raise SystemExit("the pre-registration's bound text was changed, not only appended to: refusing")


def formal_commit(text: str) -> str:
    found = FORMAL_COMMIT_RE.findall(text)
    if not found:
        raise SystemExit("the pre-registration records no formal code's commit (Amendment 1): refusing")
    return found[-1]


def prereg_at(commit: str) -> bytes:
    import subprocess
    return subprocess.check_output(["git", "show", f"{commit}:{PREREG}"], cwd=ROOT)  # bytes: the text is UTF-8


def check_prereg(now: bytes, refs: dict) -> None:
    """The text at every reference commit survives as a prefix: the bound text and every amendment already in force
    (Astra, D277)."""
    for commit, text in refs.items():
        try:
            prereg_append_only(text, now)
        except SystemExit:
            raise SystemExit(f"the pre-registration as of {commit} was changed, not only appended to: refusing") from None


def first_marker(stage: str):
    """The first attempt's start marker, or its archived copy when a rerun's setup was interrupted (Astra, D277)."""
    m = E.marker_path(stage)
    if m.exists():
        return m
    a = E.attempt1(m)
    return a if a.exists() else None


def check_provenance(args, prov: dict, stage: str, predecessors=()) -> None:
    """Before any stage (Astra, D276-D277): the bound inputs and the reviewed code; the pre-registration append-only
    against the bound commit, the formal commit, the predecessors' commits and a rerun's first attempt; a rerun's code
    and environment against its first attempt's."""
    if SMOKE:
        return
    check_pinned()
    E.require_committed(ROOT / PREREG)
    now = (ROOT / PREREG).read_bytes()
    fc = formal_commit(now.decode("utf-8"))
    refs = {BOUND: prereg_at(BOUND), fc: prereg_at(fc)}
    reg.require_same_code(BOUND, BOUND_FILES)
    reg.require_same_code(fc, CODE)
    m = first_marker(stage)
    if m is None and getattr(args, "rerun", False):
        raise SystemExit("a rerun, but no first attempt's start marker (nor its archived copy): refusing")
    if m is not None:
        first = json.loads(m.read_text(encoding="utf-8"))["provenance"]
        refs[first["git_commit"]] = prereg_at(first["git_commit"])
        reg.require_same_code(first["git_commit"], CODE)
        reg.require_same_env(first, prov)
    for c in predecessors:
        refs.setdefault(c, prereg_at(c))
    check_prereg(now, refs)


def owner_word(args, stage: str) -> str | None:
    """§0.4: the owner's word before `check` and before S, recorded; checked before anything starts."""
    if stage in OWNER_STAGES and not SMOKE:
        if not args.owner_word or not args.owner_word.strip():
            raise SystemExit(f"{stage} needs --owner-word: the owner's words and their date (§0.4)")
        return args.owner_word.strip()
    return None


def timing_ok(per_gen_seconds: float, spent_hours: float, cap_hours: float) -> dict:
    T = REGISTERED["timing"]
    projected = per_gen_seconds * REGISTERED["G"] * T["overhead"] / 3600
    allowance = T["share_of_remainder"] * (cap_hours - spent_hours)
    return {"seconds_per_generation": per_gen_seconds, "projected_hours": projected, "allowance_hours": allowance,
            "within_cap": bool(projected <= allowance)}


def requires(stage: str):
    """§5's table: each predecessor completed, under the same code, registration and environment (`check`'s)."""
    def check(args, prov):
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
        check_provenance(args, prov, stage, [r["provenance_at_start"]["git_commit"] for r in got.values()])
        if stage == "check" and not SMOKE and local_gen010() is None:
            raise SystemExit("the pilot's local generation-10 populations are required on the tested machine (§5.1)")
        if stage != "check":
            chk = E.record_path("check")
            if not chk.exists():
                raise SystemExit("check has not run")
            c = json.loads(chk.read_text(encoding="utf-8"))
            got.setdefault("check", c)
            if not SMOKE:
                reg.require_same_env(c["provenance_at_start"], prov)
        if stage == "train-l":  # recomputed against L's clock before every attempt (Astra, D276)
            t = timing_ok(got["check"]["timing"]["seconds_per_generation"], E.clock().spent_hours(),
                          REGISTERED["caps"]["l"])
            if not t["within_cap"]:
                raise SystemExit(f"the timing projection ({t['projected_hours']:.2f} h) exceeds the L cap's allowance "
                                 f"({t['allowance_hours']:.2f} h): an amendment is needed, and the owner decides (§5)")
        if stage == "train-s" and not FM.s_triggered(got["report-l"]["reading"]):
            raise SystemExit(f"S is not triggered: L reads {got['report-l']['reading'].get('state')!r}")
        return got
    return check


# ----------------------------------------------------------------------------- rollouts and checks

def readout(res, k: int = 0) -> dict:
    out = {"real_first": int(res.real_first[k]), "decoy_first": int(res.decoy_first[k]), "neither": int(res.neither[k])}
    n = sum(out.values())
    out.update(trials=n, real_first_all=out["real_first"] / n, entry_rate=(n - out["neither"]) / n)
    out["per_maze"] = {"real_first": res.real_first_maze[k].tolist(), "decoy_first": res.decoy_first_maze[k].tolist(),
                       "neither": res.neither_maze[k].tolist()}
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


def same_genome(a: Genome, b: Genome) -> bool:
    return all(torch.equal(getattr(a, k).cpu(), getattr(b, k).cpu()) for k in ("w", "bias", "tau", "g"))


def evaluate_conditions(ctx, cx, cfg, champ: Genome, ids, *, arm: str | None, start: Genome | None = None,
                        persist=lambda name, r: None) -> dict:
    """The test block's conditions, one genome per batch, each saved (`persist`) before its assertion (§5): per maze,
    the removed, fixed, cut and E-G conditions balanced; an L or S champion cut equal to E-G, bitwise."""
    slots = AR.slot_indices(cx)
    eg = eg_of(cx)
    cut = AR.cut(champ, slots)
    if arm in ("L", "S") and not same_genome(cut, eg):
        raise FM.IntegrityError(f"an {arm} champion with its slots cut is not E-G")
    plays = [(name, champ, src) for name, src in FM.CONDITIONS.items()]
    plays += [("cut", cut, "real"), ("eg", eg, "real")] + ([("start", start, "real")] if start is not None else [])
    out = {}
    for name, g, src in plays:
        res = play(ctx, cx, cfg, g, ids, a_source=src)
        out[name] = readout(res)
        persist(name, out[name])
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


def check_frozen(start: Genome, pop: Genome, sc: dict, label: str) -> None:
    try:
        AR.assert_frozen(start, pop, sc)
    except AssertionError as e:
        raise FM.IntegrityError(f"{label}: {e}") from e


def check_lineage(recs, rep) -> None:
    for rec, rp in zip(recs, rep, strict=True):
        if not same_genome(rec.final, rp["final"]):
            raise FM.IntegrityError(f"run {rec.spec.run}: the lineage replay differs from the run")


def save_selections(path: Path, selections: list, runs: list, P: int) -> None:
    """Atomically: a temporary file, then a replace (Astra, D276)."""
    arrays = {}
    for i, r in enumerate(runs):
        sl = slice(i * P, (i + 1) * P)
        for k in ("score", "real_first", "decoy_first", "neither"):
            arrays[f"{k}_run{r['run']:03d}"] = np.stack([s[k][sl] for s in selections])
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, **arrays)
    E.replace(tmp, path)


def population_digest(hashes: list[str]) -> str:
    return hashlib.sha256("".join(hashes).encode()).hexdigest()


def compare_replay(snapshots: dict, checkpoints: dict, screen: dict, local: dict | None) -> dict:
    """§5.1's replay comparison. `snapshots`: run → the replay's generation-10 strain hashes; `checkpoints`: run → the
    replay's generation-10 checkpoint sha256; `screen`: the pilot's record; `local`: run → the local `gen010` strain
    hashes computed from the files' arrays, or None (only outside the tested machine). Raises `IntegrityError` on any
    mismatch."""
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
        out["populations"] = "equal, bitwise (strain hashes from the arrays), and the registered digest matches"
    return out


def gen010_files() -> dict:
    snap = REGISTERED["replay"]["snapshot"]
    return {r["run"]: PILOT_POPS / f"L-run{r['run']:03d}-gen{snap:03d}.npz" for r in PILOT_RUNS}


def local_gen010(spec=None, brain_cfg=None) -> dict | bool | None:
    """None if any local file is absent; with no spec, True if all are present; with a spec, run → the strain hashes
    computed from each file's arrays (Astra, D276)."""
    files = gen010_files()
    if not all(f.exists() for f in files.values()):
        return None
    if spec is None:
        return True
    out = {}
    for run, f in files.items():
        pop, _ = load_population(f, spec, brain_cfg, "cpu")
        out[run] = [genome_hash(pop, i) for i in range(pop.n_strains)]
    return out


# ----------------------------------------------------------------------------- the stages

def cmd_check(args):
    def body(ctx):
        state = {"stage": "check", "partial": True, "owner_word": owner_word(args, "check")}
        ctx.salvage = lambda: state
        cfg = cfg_for(REGISTERED["W"])
        cx = context(cfg)
        eg = eg_of(cx)
        state["eg_sha256"] = genome_hash(eg, 0)
        state["preflight"] = FM.preflight(FM.all_blocks(), lambda ids: ET.qualifying(ids, FM.MAZE_SEED))
        E.write_atomic(E.partial_path("check"), state)
        with acct.category("probe"):
            ids = FM.CHECK_IDS
            ctl = TL.control_genome(eg, cx, "comparator", 3.0)
            pc = state["positive_control"] = {}
            for name, g, kw in (("control_w3", ctl, {}), ("eg", eg, {}),
                                ("oracle", eg, {"b_source": "real", "check": False})):
                pc[name] = readout(play(ctx, cx, cfg, g, ids, **kw))
                E.write_atomic(E.partial_path("check"), state)
            FM.assert_balanced([pc["eg"]["per_maze"]["real_first"]], [pc["eg"]["per_maze"]["decoy_first"]], "E-G")
            if pc["control_w3"]["real_first_all"] < REGISTERED["control_threshold"]:
                raise FM.IntegrityError(f"the positive control made {pc['control_w3']['real_first_all']:.3f}, below "
                                        f"{REGISTERED['control_threshold']}")
            ev = state["evaluation_path"] = {}

            def persist(name, r):
                ev[name] = r
                E.write_atomic(E.partial_path("check"), state)

            evaluate_conditions(ctx, cx, cfg, ctl, ids, arm=None, persist=persist)
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
                           validation_ids=np.arange(*Rp["checkpoint_ids"]), world_seed=1_420_000,
                           id_base=Rp["train_base"], id_span=Rp["train_span"], device=ctx.args.device,
                           rollout_fn=LI.Capture(ET.trial_rollout(cx)), check=ctx.cap.check, category=acct.category,
                           initial=lambda r: start, mutation_scales=lambda r: scales[factor[r.run]],
                           snapshot_at=(Rp["snapshot"],), random_ties=True)
    snaps = {rec.spec.run: [genome_hash(rec.snapshots[Rp["snapshot"]], i)
                            for i in range(rec.snapshots[Rp["snapshot"]].n_strains)] for rec in recs}
    cks = {rec.spec.run: next(c["sha256"] for c in rec.checkpoints if c["generation"] == Rp["snapshot"]) for rec in recs}
    screen = json.loads((PILOT_DIR / "screen.json").read_text(encoding="utf-8"))
    return compare_replay(snaps, cks, screen, local_gen010(cx["org"].genome.spec, cfg.brain))


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


def pop_dir(arm: str) -> Path:
    return out_dir(f"train-{arm.lower()}") / "populations"


def pop_path(arm: str, run: int, tag: str) -> Path:
    return pop_dir(arm) / f"{arm}-run{run:03d}-{tag}.npz"


def train_files(arm: str) -> list[Path]:
    """Every file `train-<arm>` writes, kept beside as `-attempt1` on a rerun (Fable, Astra, D276)."""
    G, every = REGISTERED["G"], REGISTERED["checkpoint_every"]
    tags = [f"gen{g:03d}" for g in sorted(set(range(0, G, every)) | {G - 1})] + ["final"]
    return ([pop_dir(arm) / f"{arm}-selections.npz", pop_dir(arm) / f"{arm}-parents.npz"]
            + [pop_path(arm, r["run"], t) for r in FM.runs(arm) for t in tags])


def cmd_train(args, arm: str):
    stage = f"train-{arm.lower()}"

    def body(ctx):
        state = {"stage": stage, "partial": True, "owner_word": owner_word(args, stage), "checkpoints": {}}
        ctx.salvage = lambda: state
        W, G, every = REGISTERED["W"], REGISTERED["G"], REGISTERED["checkpoint_every"]
        cfg = cfg_for(W)
        cx = context(cfg)
        if genome_hash(eg_of(cx), 0) != ctx.earlier["check"]["eg_sha256"]:
            raise FM.IntegrityError("E-G differs from check's")
        runs = FM.runs(arm)
        P = cfg.evo.population
        s0 = start_of(cx, arm)
        start = Genome.cat([s0] * P)
        sc = scales_of(cx, arm)
        specs = [EV.RunSpec(r["run"], r["seed"], 0.0) for r in runs]
        cap = LI.Capture(checked_rollout(cx, FM.check_ids))
        snaps = tuple(sorted(set(range(0, G, every)) | {G - 1}))
        pop_dir(arm).mkdir(parents=True, exist_ok=True)
        sel_path = pop_dir(arm) / f"{arm}-selections.npz"

        def on_checkpoint(records, g):
            for rec in records:
                if g in rec.snapshots:
                    check_frozen(start, rec.snapshots[g], sc, f"run {rec.spec.run}, generation {g}")
                    save_population(pop_path(arm, rec.spec.run, f"gen{g:03d}"), rec.snapshots[g], cfg=cfg,
                                    run=rec.spec.run, generation=g)
                state["checkpoints"][str(rec.spec.run)] = [
                    {k: c[k] for k in ("generation", "validation_mean", "validation_counts", "sha256")}
                    for c in rec.checkpoints]
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
        check_lineage(recs, rep)
        for rec in recs:
            check_frozen(start, rec.final, sc, f"run {rec.spec.run}, final")
        par_path = pop_dir(arm) / f"{arm}-parents.npz"
        np.savez_compressed(par_path,
                            **{f"source_run{rp['run']:03d}": np.array([p["source"] for p in rp["parents"]]) for rp in rep},
                            **{f"child_run{rp['run']:03d}": np.array([p["child"] for p in rp["parents"]]) for rp in rep})
        state.update(runs=[{**r, "final_sha256": [genome_hash(rec.final, i) for i in range(rec.final.n_strains)],
                            "log": rec.log} for r, rec in zip(runs, recs)],
                     start_sha256=genome_hash(s0, 0), training_seconds=seconds,
                     composition=[len(runs) * P, 2 * W, 1], selections=str(sel_path.relative_to(ROOT)),
                     selections_sha256=E.sha256_bytes(sel_path), parents_sha256=E.sha256_bytes(par_path))
        FM.validate_runs(arm, state["runs"], stage="train")
        state.pop("partial", None)
        return state

    return E.run_stage(args, stage, requires(stage), body, local_files=train_files(arm))


def load_final(arm: str, run: int, want: list[str], spec, brain_cfg, device) -> Genome:
    """The saved final population, its strain hashes equal to the training record's, else `IntegrityError`."""
    final, _ = load_population(pop_path(arm, run, "final"), spec, brain_cfg, device)
    if [genome_hash(final, i) for i in range(final.n_strains)] != list(want):
        raise FM.IntegrityError(f"run {run}'s saved final population differs from the training record")
    return final


def champion_of(final: Genome, validation_scores, selection_scores, slots) -> int:
    """§6: the whole final population on its validation block; ties to the final generation's fitness (the last
    selection), then the smaller cross-link norm, then the lowest index."""
    fit = np.asarray(selection_scores)[-1].mean(axis=1)
    norm = final.w[:, slots.to(final.w.device)].norm(dim=1).cpu().numpy()
    return ET.champion(np.asarray(validation_scores).mean(axis=1), fit, norm)


def cmd_evaluate(args, arm: str):
    stage = f"evaluate-{arm.lower()}"

    def body(ctx):
        state = {"stage": stage, "partial": True, "runs": []}
        ctx.salvage = lambda: state
        cfg = cfg_for(REGISTERED["W"])
        cx = context(cfg)
        spec = cx["org"].genome.spec
        tr = ctx.earlier[f"train-{arm.lower()}"]
        FM.validate_runs(arm, tr["runs"], stage="train")
        if genome_hash(eg_of(cx), 0) != ctx.earlier["check"]["eg_sha256"]:
            raise FM.IntegrityError("E-G differs from check's")
        sel_path, par_path = pop_dir(arm) / f"{arm}-selections.npz", pop_dir(arm) / f"{arm}-parents.npz"
        if (E.sha256_bytes(sel_path), E.sha256_bytes(par_path)) != (tr["selections_sha256"], tr["parents_sha256"]):
            raise FM.IntegrityError("the saved selections or parents differ from the training record")
        sel = np.load(sel_path, allow_pickle=False)
        par = np.load(par_path, allow_pickle=False)
        slots = AR.slot_indices(cx)
        s0 = None
        if arm == "S":
            s0 = s0_of(cx)
            if genome_hash(s0, 0) != tr["start_sha256"]:
                raise FM.IntegrityError("S₀ differs from the training record's start")
        with acct.category("holdout"):
            for r, rt in zip(FM.runs(arm), tr["runs"], strict=True):
                final = load_final(arm, r["run"], rt["final_sha256"], spec, cfg.brain, ctx.args.device)
                v_ids, t_ids = FM.blocks(arm, r["run"])
                val = play(ctx, cx, cfg, final, v_ids)
                scores = sel[f"score_run{r['run']:03d}"]
                k = champion_of(final, val.score, scores, slots)
                champ = final.select([k])
                src, ch = par[f"source_run{r['run']:03d}"], par[f"child_run{r['run']:03d}"]
                entry = {**r, "champion_index": k, "champion_sha256": genome_hash(champ, 0),
                         "validation_shares": np.round(val.score.mean(axis=1), 6).tolist(),
                         "slot_weights": np.round(champ.w[0, slots.to(champ.w.device)].cpu().numpy(), 6).tolist(),
                         "tie_shares": FM.tie_shares(scores), "turnover": FM.turnover(src, ch),
                         "lineage_mutations": FM.lineage_mutations(src, ch, k), "test": {}}
                state["runs"].append(entry)

                def persist(name, rd, entry=entry):
                    (entry.__setitem__("start", rd) if name == "start" else entry["test"].__setitem__(name, rd))
                    E.write_atomic(E.partial_path(stage), state)

                evaluate_conditions(ctx, cx, cfg, champ, t_ids, arm=arm, start=s0, persist=persist)
        FM.validate_runs(arm, state["runs"], stage="evaluate")
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


def use_smoke(args=None) -> None:
    """Toy sizes in their own folders, with their own maze seed, run seeds and ids (Astra, D276); never results."""
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
    FM.MAZES, FM.TRIALS, FM.POP = 2, 4, 6
    FM.MAZE_SEED, FM.SEED_BASE = 1_429_000, 1_449_000
    FM.BASES.update({"L": 40_000, "F": 41_000, "S": 42_000})
    FM.CHECK_IDS, FM.CHECKPOINT_IDS = np.arange(43_000, 43_002), np.arange(43_100, 43_102)
    FM.TRAIN, FM.TIMING = (200_000_000, 210_000_000), (210_000_000, 220_000_000)
    R.update(maze_seed=FM.MAZE_SEED, seed_base=FM.SEED_BASE, runs=dict(FM.N_RUNS))
    R["blocks"] = {"check": [int(FM.CHECK_IDS[0]), int(FM.CHECK_IDS[-1])],
                   "checkpoints": [int(FM.CHECKPOINT_IDS[0]), int(FM.CHECKPOINT_IDS[-1])], "bases": dict(FM.BASES),
                   "train": list(FM.TRAIN), "timing": list(FM.TIMING)}  # the smoke's own (Fable, D277)


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
