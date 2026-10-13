"""E4-D's feasibility check (docs/E4/E4-D-DESIGN.md v2.1 §2, §4): CPU, exploratory engineering, before E4's formal
run. Three stages, each once, in order:

    python scripts/e4d.py scout       # σ_D, the start rule's skips, the nose readings, the frozen manifests
    python scripts/e4d.py calibrate   # the control's wiring and weight
    python scripts/e4d.py evaluate    # the control, X0, the oracle and the checks; the verdict
    add --smoke for toy sizes in runs/e4d-smoke (never results)

**Blocks** (maze seed 1 410 000, E4-D's own): scouting ids 51 000-51 031 (a fixed range; its skips counted, limit
25%); calibration the first 32 qualifying ids in [51 100, 51 300); evaluation the first 64 qualifying ids in
[51 300, 51 700). Every maze is played under both assignments, maze-major (assignment 0, then 1). H_t = 600 ticks.

**Each genome plays alone in its batch** (2n worlds of one strain), so every comparison (X0's pairs, the reversal, the
cue held fixed, cross-link removal against X0) is within one composition (v2.3). Per tick, positions, headings and
random projections of the non-A neurons' states are traced and compared bitwise; per substep, the latch is checked to
stay in mode B until each world's first entry. Each later stage refuses to run unless the earlier stages' records came
from the same code and registration.
"""

from __future__ import annotations

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
from wormwars.e3 import islands as IS  # noqa: E402
from wormwars.e4 import arms as AR  # noqa: E402
from wormwars.e4 import feasibility as F  # noqa: E402
from wormwars.e4 import trial as TL  # noqa: E402
from wormwars.e4.train import gated_brain  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402

EXP = ROOT / "experiments" / "E4-two-minds" / "E4-D"
DESIGN = "docs/E4/E4-D-DESIGN.md"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", DESIGN]
REGISTERED = {"design": DESIGN, "maze_seed": 1_410_000, "c": 6, "H_t": 600, "sigmas": list(F.SIGMAS),
              "scouting": [51_000, 51_032], "calibration_from": 51_100, "calibration_n": 32,
              "evaluation_from": 51_300, "evaluation_n": 64, "evaluation_end": 51_700, "skip_limit": 0.25,
              "wirings": list(F.WIRINGS), "weights": list(F.WEIGHTS), "bootstrap": [F.BOOT_SEED, F.BOOT_RESAMPLES]}
SMOKE = False


def record(stage: str) -> Path:
    return EXP / f"{stage}.json"


def write(stage: str, doc: dict) -> None:
    EXP.mkdir(parents=True, exist_ok=True)
    reg.write_json(record(stage), doc, atomic=True)


def read(stage: str) -> dict:
    p = record(stage)
    if not p.exists():
        raise SystemExit(f"{p.name} is missing: run {stage} first")
    return json.loads(p.read_text(encoding="utf-8"))


def qualifies(mid: int) -> bool:
    mz, pl, _ = IS.maze_for(run_seed=REGISTERED["maze_seed"], maze_id=int(mid), episode=0, c=REGISTERED["c"], k_r=0,
                            n_spawns=4)
    c0, c1 = sorted((tuple(pl.a), tuple(pl.b)))
    return TL.start_cell(mz.wall, TL.block_distance(mz, c0), TL.block_distance(mz, c1)) is not None


def first_qualifying(start: int, n: int, end: int) -> list:
    """The first `n` qualifying ids in [start, end): bounded, so the blocks cannot overlap (Astra)."""
    out, mid = [], start
    while len(out) < n:
        if mid >= end:
            raise SystemExit(f"fewer than {n} qualifying mazes in [{start}, {end})")
        if qualifies(mid):
            out.append(mid)
        mid += 1
    return out


def context(sigma: float):
    cfg = TL.trial_config(sigma=sigma, horizon=REGISTERED["H_t"], c=REGISTERED["c"])
    cx = AR.context(load_connectome(), A.load_l1(), cfg.brain)
    return cfg, cx


PROJECTIONS = 4  # random projections of the non-A neurons' state, recorded per tick for the invariance checks


def _trial(cfg, cx, genome: Genome, ids, *, a_source, b_source, start_signals) -> dict:
    """One genome on every maze under both assignments (maze-major), alone in its batch, so every comparison is within
    one composition (2n worlds of one strain; both reviewers). Per tick: positions, headings and fixed random
    projections of the non-A neurons' states; per substep, whether q reached 0 before the world's first entry."""
    org, ext = cx["org"], cx["org"].ext
    ids = [int(i) for i in ids]
    n = len(ids)
    w = TL.TrialWorld(cfg, org.iface, gated_brain(genome, org.gate), torch.zeros(2 * n, 1, dtype=torch.long),
                      run_seed=REGISTERED["maze_seed"], world_ids=np.repeat(ids, 2), assign=np.tile([0, 1], n),
                      q_index=org.gate["q"], a_source=a_source, b_source=b_source)
    q = org.gate["q"]
    a_idx = [ext.index(f"E3_A_{k}") for k in ("NL", "NR", "CL", "CR")]
    keep = torch.ones(ext.n, dtype=torch.bool)
    keep[a_idx] = False
    proj = torch.from_numpy(np.random.default_rng(20_261_014).normal(size=(int(keep.sum()), PROJECTIONS)))
    q_hit = torch.zeros(2 * n, dtype=torch.bool)

    def hook(v):
        pending = (w.first_candidate[:, 0] < 0).cpu()
        q_hit.logical_or_(((v[0, :, q] >= 0).cpu()) & pending)

    w.brains[0].substep_hook = hook
    sig0 = w.trial_signals()["cand"].reshape(2 * n, 2, 2).cpu().numpy() if start_signals else None
    pos, head, state = [], [], []
    for _ in range(int(cfg.world.max_ticks)):
        w.tick()
        pos.append(w.pos[:, 0, 0].cpu().numpy().copy())
        head.append(w.heading[:, 0, 0].cpu().numpy().copy())
        state.append((w.v[0][0][:, keep].double().cpu() @ proj).numpy())
    ev = w.trial_events()
    e = {"first_candidate": ev["first_candidate"][:, 0], "first_tick": ev["first_tick"][:, 0], "assign": ev["assign"]}
    out = {"events": e, "readout": F.readout(e), "starts": ev["starts"], "latch_held": bool(not q_hit.any()),
           "trace": {"pos": np.stack(pos, 1), "heading": np.stack(head, 1), "state": np.stack(state, 1)}}
    if sig0 is not None:
        out["start_readings"] = sig0
    return out


def trials(cfg, cx, genomes: dict, ids, *, a_source="real", b_source="sum", start_signals=False) -> dict:
    return {k: _trial(cfg, cx, g, ids, a_source=a_source, b_source=b_source, start_signals=start_signals)
            for k, g in genomes.items()}


def paired_identical(res: dict) -> bool:
    """Assignment 0 and 1 of every maze, bitwise: first entries, and every tick's position, heading and non-A state
    projections (both reviewers: a divergence that re-converges must be caught)."""
    e, tr = res["events"], res["trace"]
    same = (np.array_equal(e["first_candidate"][0::2], e["first_candidate"][1::2])
            and np.array_equal(e["first_tick"][0::2], e["first_tick"][1::2]))
    return bool(same and all(np.array_equal(tr[k][0::2], tr[k][1::2]) for k in ("pos", "heading", "state")))


def identical(a: dict, b: dict) -> bool:
    """Two runs of the same composition, bitwise (cross-link removal against X0)."""
    return bool(np.array_equal(a["events"]["first_candidate"], b["events"]["first_candidate"])
                and np.array_equal(a["events"]["first_tick"], b["events"]["first_tick"])
                and all(np.array_equal(a["trace"][k], b["trace"][k]) for k in ("pos", "heading", "state")))


def _lists(e: dict) -> dict:
    return {k: np.asarray(v).tolist() for k, v in e.items()}


def provenance() -> dict:
    return reg.provenance(GUARDED)


def guard(stage: str, after: tuple = ()) -> dict:
    """Once only, from a clean tree; and every earlier stage's record made by this same code and registration
    (Astra: the freeze is enforced, not only recorded)."""
    prov = provenance()
    if not SMOKE:
        if record(stage).exists():
            raise SystemExit(f"{record(stage).name} exists: E4-D's {stage} runs once (a change is a new version)")
        if prov["dirty"]:
            raise SystemExit("uncommitted changes in the guarded files: commit first")
        for earlier in after:
            doc = read(earlier)
            reg.require_same_code(doc["provenance"]["commit"], GUARDED)
            if doc["registered"] != json.loads(json.dumps(REGISTERED)):
                raise SystemExit(f"the registration differs from {earlier}'s: refusing to run")
    return prov


def cmd_scout(args):
    prov = guard("scout")
    t0 = time.perf_counter()
    R = REGISTERED
    ids = list(range(*R["scouting"]))
    ok = [i for i in ids if qualifies(i)]
    skipped = [i for i in ids if i not in ok]
    doc = {"stage": "scout", "registered": R, "provenance": prov, "ids": ids, "qualifying": ok, "skipped": skipped,
           "skip_share": len(skipped) / len(ids), "by_sigma": {}}
    partial = EXP / "scout-partial.json"  # never the record's name, so a crash cannot block the rerun's guard
    if doc["skip_share"] > R["skip_limit"]:
        doc["outcome"] = "the start rule skips more than the limit: a new version revises it before anything is played"
        write("scout", doc)
        return
    for s in R["sigmas"]:
        cfg, cx = context(s)
        eg = cx["org"].genome.select([0])
        with acct.category("probe"):
            x0 = trials(cfg, cx, {"x0": eg}, ok, start_signals=True)["x0"]
            orc = trials(cfg, cx, {"oracle": eg}, ok, b_source="real")["oracle"]
        rd = x0["start_readings"]  # [trials (maze-major, assignment 0 then 1), (candidate 0, 1), (L, R)]
        doc["by_sigma"][str(s)] = {
            "x0": x0["readout"], "oracle": orc["readout"], "latch_held": x0["latch_held"] and orc["latch_held"],
            "oracle_real_first_all": orc["readout"]["real_first_all"], "x0_entry_rate": x0["readout"]["entry_rate"],
            "start_readings": {"per_trial": np.round(rd, 8).tolist(), "starts": x0["starts"],
                               "candidate_lr_abs_median": float(np.median(np.abs(rd[..., 0] - rd[..., 1]))),
                               "sum_lr_abs_median": float(np.median(np.abs(rd.sum(-2)[..., 0] - rd.sum(-2)[..., 1]))),
                               "zero_lr_share": float(np.mean(rd[..., 0] == rd[..., 1]))}}
        EXP.mkdir(parents=True, exist_ok=True)
        reg.write_json(partial, {**doc, "partial": True}, atomic=True)
    sigma = F.choose_sigma({float(k): v for k, v in doc["by_sigma"].items()})
    if sigma is None and SMOKE:  # toy horizons enter nothing; the smoke still exercises the later stages
        sigma, doc["smoke_forced_sigma"] = R["sigmas"][-1], True
    doc["sigma_D"] = sigma
    if sigma is None:
        doc["outcome"] = "no σ meets the rule: the task is infeasible as specified (a new version)"
    else:
        cal = first_qualifying(R["calibration_from"], R["calibration_n"], R["evaluation_from"])
        ev = first_qualifying(R["evaluation_from"], R["evaluation_n"], R["evaluation_end"])
        if set(cal) & set(ev) or set(cal + ev) & set(ids):
            raise SystemExit("the manifests overlap")
        doc["manifests"] = {"calibration": cal, "evaluation": ev}
        doc["outcome"] = "σ_D and the manifests frozen"
    doc["seconds"] = time.perf_counter() - t0
    write("scout", doc)


def cmd_calibrate(args):
    prov = guard("calibrate", after=("scout",))
    sc = read("scout")
    if sc.get("sigma_D") is None:
        raise SystemExit("the scouting stage fixed no σ_D")
    t0 = time.perf_counter()
    cfg, cx = context(float(sc["sigma_D"]))
    eg = cx["org"].genome.select([0])
    configs = [(wr, w) for wr in REGISTERED["wirings"] for w in REGISTERED["weights"]]
    genomes = {f"{wr}:{w:g}": TL.control_genome(eg, cx, wr, w) for wr, w in configs}
    ids = sc["manifests"]["calibration"]
    with acct.category("probe"):
        res = trials(cfg, cx, genomes, ids)
        oracle = trials(cfg, cx, {"oracle": eg}, ids, b_source="real")["oracle"]
    shares = {(wr, w): res[f"{wr}:{w:g}"]["readout"]["real_first_all"] for wr, w in configs}
    choice = F.choose_control(shares)
    write("calibrate", {"stage": "calibrate", "registered": REGISTERED, "provenance": prov, "sigma_D": sc["sigma_D"],
                        "results": {k: v["readout"] for k, v in res.items()}, "oracle": oracle["readout"],
                        "latch_held": all(v["latch_held"] for v in res.values()) and oracle["latch_held"],
                        "choice": {"wiring": choice[0], "w": choice[1]}, "seconds": time.perf_counter() - t0})


def cmd_evaluate(args):
    prov = guard("evaluate", after=("scout", "calibrate"))
    sc, cal = read("scout"), read("calibrate")
    t0 = time.perf_counter()
    cfg, cx = context(float(sc["sigma_D"]))
    eg = cx["org"].genome.select([0])
    ctl = TL.control_genome(eg, cx, cal["choice"]["wiring"], float(cal["choice"]["w"]))
    ids = sc["manifests"]["evaluation"]
    with acct.category("probe"):  # each genome alone in its batch: every comparison within one composition
        runs = {"x0": trials(cfg, cx, {"x0": eg}, ids)["x0"],
                "control": trials(cfg, cx, {"control": ctl}, ids)["control"],
                "control_cut": trials(cfg, cx, {"control_cut": AR.cut(ctl, AR.slot_indices(cx))}, ids)["control_cut"],
                "oracle": trials(cfg, cx, {"oracle": eg}, ids, b_source="real")["oracle"],
                "reversal": trials(cfg, cx, {"control": ctl}, ids, a_source="decoy")["control"],
                "cue_fixed": trials(cfg, cx, {"control": ctl}, ids, a_source="fixed0")["control"],
                "cue_removed": trials(cfg, cx, {"control": ctl}, ids, a_source="none")["control"]}
    x0, c = runs["x0"], runs["control"]
    pm = F.per_maze(c["events"], len(ids))
    r = {"control": c["readout"], "control_bound": F.maze_bound(pm),
         "x0_invariant": paired_identical(x0), "reversal_ok": F.reversal_ok(c["events"], runs["reversal"]["events"]),
         "fixed_cue_invariant": paired_identical(runs["cue_fixed"]),
         "removal_identical": identical(runs["control_cut"], x0),
         "latch_held": all(v["latch_held"] for v in runs.values()),
         "oracle_real_first_all": runs["oracle"]["readout"]["real_first_all"]}
    v = F.verdict(r)
    write("evaluate", {"stage": "evaluate", "registered": REGISTERED, "provenance": prov, "sigma_D": sc["sigma_D"],
                       "control": cal["choice"], "ids": ids,
                       "readouts": {k: run["readout"] for k, run in runs.items()},
                       "per_maze_control": pm.tolist(), **{k: v_ for k, v_ in r.items() if k != "control"},
                       "verdict": v, "reading": v["reading"],
                       "events": {k: _lists(runs[k]["events"]) for k in ("x0", "control", "oracle")},
                       "seconds": time.perf_counter() - t0})


def use_smoke() -> None:
    global EXP, SMOKE
    EXP, SMOKE = ROOT / "runs" / "e4d-smoke", True
    REGISTERED.update({"H_t": 40, "sigmas": [9.0, 12.0], "scouting": [51_000, 51_003], "calibration_n": 2,
                       "evaluation_n": 2, "weights": [0.05, 1.0], "skip_limit": 1.0})


COMMANDS = {"scout": cmd_scout, "calibrate": cmd_calibrate, "evaluate": cmd_evaluate}


def main():
    import argparse
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=list(COMMANDS))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        use_smoke()
    COMMANDS[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    out_dir = ROOT / "runs" / ("e4d-smoke" if smoke else "e4d")
    run_script(main, out_default=str(out_dir), default="measure", name="e4d")
