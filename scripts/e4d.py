"""E4-D's feasibility check (docs/E4/E4-D-DESIGN.md v2.1 §2, §4): CPU, exploratory engineering, before E4's formal
run. Three stages, each once, in order:

    python scripts/e4d.py scout       # σ_D, the start rule's skips, the nose readings, the frozen manifests
    python scripts/e4d.py calibrate   # the control's wiring and weight
    python scripts/e4d.py evaluate    # the control, X0, the oracle and the checks; the verdict
    add --smoke for toy sizes in runs/e4d-smoke (never results)

**Blocks** (maze seed 1 410 000, E4-D's own): scouting ids 51 000-51 031 (a fixed range; its skips counted, limit
25%); calibration the first 32 qualifying ids from 51 100; evaluation the first 64 qualifying ids from 51 300. Every
maze is played under both assignments, maze-major (assignment 0, then 1). H_t = 600 ticks.
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
              "evaluation_from": 51_300, "evaluation_n": 64, "skip_limit": 0.25,
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
    return TL.start_cell(mz.wall, mz.free_distance(c0), mz.free_distance(c1)) is not None


def first_qualifying(start: int, n: int, limit: int = 10_000) -> list:
    out, mid = [], start
    while len(out) < n:
        if mid - start > limit:
            raise SystemExit(f"fewer than {n} qualifying mazes from {start}")
        if qualifies(mid):
            out.append(mid)
        mid += 1
    return out


def context(sigma: float):
    cfg = TL.trial_config(sigma=sigma, horizon=REGISTERED["H_t"], c=REGISTERED["c"])
    cx = AR.context(load_connectome(), A.load_l1(), cfg.brain)
    return cfg, cx


def trials(cfg, cx, genomes: dict, ids, *, a_source="real", b_source="sum", start_signals=False) -> dict:
    """Every named genome on every maze under both assignments (maze-major), in one batch; per genome its trial
    events, its final positions, and (with `start_signals`) the candidates' readings at the start."""
    org = cx["org"]
    names, ids = list(genomes), [int(i) for i in ids]
    S, n = len(names), len(ids)
    world_ids = np.tile(np.repeat(ids, 2), S)
    assign = np.tile(np.tile([0, 1], n), S)
    strain_of = torch.as_tensor(np.repeat(np.arange(S), 2 * n)).view(-1, 1)
    batch = Genome.cat([genomes[k] for k in names])
    w = TL.TrialWorld(cfg, org.iface, gated_brain(batch, org.gate), strain_of, run_seed=REGISTERED["maze_seed"],
                      world_ids=world_ids, assign=assign, q_index=org.gate["q"], a_source=a_source, b_source=b_source)
    sig0 = w.trial_signals()["cand"].reshape(S, 2 * n, 2, 2).numpy() if start_signals else None
    w.run(cfg.world.max_ticks)
    ev = w.trial_events()
    pos = w.pos[:, 0, 0].cpu().numpy().reshape(S, 2 * n, 2)
    out = {}
    for k, name in enumerate(names):
        sl = slice(2 * n * k, 2 * n * (k + 1))
        e = {"first_candidate": ev["first_candidate"][sl, 0], "first_tick": ev["first_tick"][sl, 0],
             "assign": ev["assign"][sl]}
        out[name] = {"events": e, "readout": F.readout(e), "final_pos": pos[k]}
        if sig0 is not None:
            out[name]["start_readings"] = sig0[k]
    return out


def paired_identical(res: dict) -> bool:
    """Assignment 0 and 1 of every maze: the same first candidate, first tick and final position, bitwise."""
    e, p = res["events"], res["final_pos"]
    return bool(np.array_equal(e["first_candidate"][0::2], e["first_candidate"][1::2])
                and np.array_equal(e["first_tick"][0::2], e["first_tick"][1::2])
                and np.array_equal(p[0::2], p[1::2]))


def _lists(e: dict) -> dict:
    return {k: np.asarray(v).tolist() for k, v in e.items()}


def provenance() -> dict:
    return reg.provenance(GUARDED)


def guard(stage: str) -> dict:
    prov = provenance()
    if not SMOKE:
        if record(stage).exists():
            raise SystemExit(f"{record(stage).name} exists: E4-D's {stage} runs once (a change is a new version)")
        if prov["dirty"]:
            raise SystemExit("uncommitted changes in the guarded files: commit first")
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
    if doc["skip_share"] > R["skip_limit"]:
        doc["outcome"] = "the start rule skips more than the limit: v3 revises it before anything else is played"
        write("scout", doc)
        return
    for s in R["sigmas"]:
        cfg, cx = context(s)
        eg = cx["org"].genome.select([0])
        with acct.category("probe"):
            x0 = trials(cfg, cx, {"x0": eg}, ok, start_signals=True)["x0"]
            orc = trials(cfg, cx, {"oracle": eg}, ok, b_source="real")["oracle"]
        rd = x0["start_readings"]  # [trials, (candidate 0, 1), (L, R)]
        doc["by_sigma"][str(s)] = {
            "x0": x0["readout"], "oracle": orc["readout"],
            "oracle_real_first_all": orc["readout"]["real_first_all"], "x0_entry_rate": x0["readout"]["entry_rate"],
            "start_readings": {"candidate_level_median": float(np.median(rd.sum(-1))),
                               "candidate_lr_abs_median": float(np.median(np.abs(rd[..., 0] - rd[..., 1]))),
                               "sum_lr_abs_median": float(np.median(np.abs(rd.sum(-2)[..., 0] - rd.sum(-2)[..., 1]))),
                               "zero_lr_share": float(np.mean(rd[..., 0] == rd[..., 1]))}}
        write("scout", {**doc, "partial": True})
    sigma = F.choose_sigma({float(k): v for k, v in doc["by_sigma"].items()})
    if sigma is None and SMOKE:  # toy horizons enter nothing; the smoke still exercises the later stages
        sigma, doc["smoke_forced_sigma"] = R["sigmas"][-1], True
    doc["sigma_D"] = sigma
    if sigma is None:
        doc["outcome"] = "no σ meets the rule: the task is infeasible as specified (v3)"
    else:
        doc["manifests"] = {"calibration": first_qualifying(R["calibration_from"], R["calibration_n"]),
                            "evaluation": first_qualifying(R["evaluation_from"], R["evaluation_n"])}
        doc["outcome"] = "σ_D and the manifests frozen"
    doc["seconds"] = time.perf_counter() - t0
    write("scout", doc)


def cmd_calibrate(args):
    prov = guard("calibrate")
    sc = read("scout")
    if sc.get("sigma_D") is None:
        raise SystemExit("the scouting stage fixed no σ_D")
    t0 = time.perf_counter()
    cfg, cx = context(float(sc["sigma_D"]))
    eg = cx["org"].genome.select([0])
    configs = [(wr, w) for wr in REGISTERED["wirings"] for w in REGISTERED["weights"]]
    genomes = {f"{wr}:{w:g}": TL.control_genome(eg, cx, wr, w) for wr, w in configs}
    with acct.category("probe"):
        res = trials(cfg, cx, genomes, sc["manifests"]["calibration"])
    shares = {(wr, w): res[f"{wr}:{w:g}"]["readout"]["real_first_all"] for wr, w in configs}
    choice = F.choose_control(shares)
    write("calibrate", {"stage": "calibrate", "registered": REGISTERED, "provenance": prov, "sigma_D": sc["sigma_D"],
                        "results": {k: v["readout"] for k, v in res.items()},
                        "choice": {"wiring": choice[0], "w": choice[1]}, "seconds": time.perf_counter() - t0})


def cmd_evaluate(args):
    prov = guard("evaluate")
    sc, cal = read("scout"), read("calibrate")
    t0 = time.perf_counter()
    cfg, cx = context(float(sc["sigma_D"]))
    eg = cx["org"].genome.select([0])
    ctl = TL.control_genome(eg, cx, cal["choice"]["wiring"], float(cal["choice"]["w"]))
    ids = sc["manifests"]["evaluation"]
    with acct.category("probe"):
        main = trials(cfg, cx, {"x0": eg, "control": ctl, "control_cut": AR.cut(ctl, AR.slot_indices(cx))}, ids)
        oracle = trials(cfg, cx, {"oracle": eg}, ids, b_source="real")["oracle"]
        rev = trials(cfg, cx, {"control": ctl}, ids, a_source="decoy")["control"]
        fixed = trials(cfg, cx, {"control": ctl}, ids, a_source="fixed0")["control"]
        removal = trials(cfg, cx, {"control": ctl}, ids, a_source="none")["control"]
    x0, c, cc = main["x0"], main["control"], main["control_cut"]
    pm = F.per_maze(c["events"], len(ids))
    r = {"control": c["readout"], "control_bound": F.maze_bound(pm),
         "x0_invariant": paired_identical(x0), "reversal_ok": F.reversal_ok(c["events"], rev["events"]),
         "fixed_cue_invariant": paired_identical(fixed),
         "removal_identical": bool(np.array_equal(cc["events"]["first_candidate"], x0["events"]["first_candidate"])
                                   and np.array_equal(cc["events"]["first_tick"], x0["events"]["first_tick"])
                                   and np.array_equal(cc["final_pos"], x0["final_pos"]))}
    v = F.verdict(r)
    reading = ("passed: the architecture can carry an engineered A → B steering signal through the slots" if v["passed"]
               else "failed with a working oracle: the slots, as configured, did not carry the signal"
               if oracle["readout"]["real_first_all"] >= F.LEVEL
               else "failed with a failed oracle: the task is infeasible (v3 changes the task)")
    write("evaluate", {"stage": "evaluate", "registered": REGISTERED, "provenance": prov, "sigma_D": sc["sigma_D"],
                       "control": cal["choice"], "ids": ids,
                       "readouts": {"x0": x0["readout"], "control": c["readout"], "control_cut": cc["readout"],
                                    "oracle": oracle["readout"], "reversal": rev["readout"], "cue_fixed": fixed["readout"],
                                    "cue_removed": removal["readout"]},
                       "per_maze_control": pm.tolist(), **{k: v_ for k, v_ in r.items() if k != "control"},
                       "verdict": v, "reading": reading,
                       "events": {"x0": _lists(x0["events"]), "control": _lists(c["events"]),
                                  "oracle": _lists(oracle["events"])},
                       "seconds": time.perf_counter() - t0})


def use_smoke() -> None:
    global EXP, SMOKE
    EXP, SMOKE = ROOT / "runs" / "e4d-smoke", True
    REGISTERED.update({"H_t": 40, "sigmas": [9.0, 12.0], "scouting": [51_000, 51_003], "calibration_n": 2,
                       "evaluation_n": 2, "weights": [1.0], "skip_limit": 1.0})


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
