"""03h's pilot (experiments/03h-history-use/PILOT.md; DESIGN.md v3.3 §7).

    python scripts/e03h.py bind          # records PILOT.md's hash; then commit and push before any stage runs
    python scripts/e03h.py gate          # G1: the scripted gate's level and relief parts
    python scripts/e03h.py sham-rates    # S1: level trajectories on the 3 pilot graphs; the sham's rates; timing
    python scripts/e03h.py gate-sham     # G2: the gate's sham part, with S1's rates
    python scripts/e03h.py pilot         # P: the three conditions on the 3 pilot graphs; PILOT.md §5's readings
    python scripts/e03h.py pilot --amplitude 0.5 --rerun --reason "..."   # P': only by PILOT.md §5.4's rule
    python scripts/e03h.py <stage> --smoke    # tiny sizes on the CPU, to runs/e03h-smoke/
    python scripts/e03h.py <stage> --smoke --device cuda    # the same on CUDA, to runs/e03h-smoke-cuda/: the preflight

Every stage refuses if:
- the stage before it has not completed with its criteria met;
- PILOT.md's hash differs from the bound one;
- the guarded tree is dirty (outside smoke).

The cap is 1.0 GPU-hour for everything before the pre-registration, step 0 included, counted across attempts. Records
go to experiments/03h-history-use/pilot/; genomes and the pilot graphs stay local, the graphs rebuilt from their
seeds and checked by hash.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import calibration as calib  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e03h import AMPLITUDE, gate as GT, interface_03h, pilot as PL  # noqa: E402
from wormwars.e03h.probes import bit_turn_response  # noqa: E402
from wormwars.evo.bundle import replay_mode  # noqa: E402
from wormwars.evo.rollout import rollout  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.exp03 import samplers as SM  # noqa: E402
from wormwars.exp03.measures import genome_seed, history  # noqa: E402

EXP = ROOT / "experiments" / "03h-history-use"
PILOT_MD = EXP / "PILOT.md"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", "experiments/03h-history-use/DESIGN.md",
           "experiments/03h-history-use/PILOT.md", "experiments/03-generation0/pilot.json",
           "experiments/02-screening/calibration.json"]
STAGES = ["bind", "gate", "sham-rates", "gate-sham", "pilot"]
SMOKE = False
SMOKE_DEVICE = "cpu"

CFG = {
    "gate": {"tuning": [3_610_000, 64], "check": [3_611_000, 256], "seeds": [3_612_001, 3_612_002]},
    "graphs": {"kind": "SH-mirror-ASK", "first_seed": 3_630_001, "n": 3, "passes": 20, "max_tries": 10},
    "calibration": {"seed": 3_631_000, "strains": 1024},
    "genome_salt": "03h-pilot:", "genomes": 256,
    "selection": [3_620_000, 16], "test": [3_621_000, 64], "run_seeds": [3_622_001, 3_622_002],
    "boot_seed": 3_623_000, "shared_boots": 2000, "cap_hours": 1.0, "delta_A": 0.05,
    "reliability_floor": 0.85, "formal": {"graphs": 64, "cap_hours": 6.0},
}
SMOKE_CFG = {
    "gate": {"tuning": [3_610_000, 3], "check": [3_611_000, 6], "seeds": [3_612_001, 3_612_002]},
    "graphs": {"kind": "SH-mirror-ASK", "first_seed": 3_630_001, "n": 2, "passes": 1, "max_tries": 10},
    "calibration": {"seed": 3_631_000, "strains": 8},
    "genomes": 32, "selection": [3_620_000, 3], "test": [3_621_000, 4], "shared_boots": 20,
}
SMOKE_GRIDS = {"K_GRID": {"slow": [0.0, 1.0], "fast": [1.0], "threshold": [0.1, 1.0], "turn": [0.0, 0.2]},
               "G_GRID": {"slow": [0.0], "fast": [1.0], "scale": [1.0], "turn": [0.2]},
               "FALL_GRID": {"fall_turn": [0.7], "fall_threshold": [0.0]}, "T_GRID": [1.0, 5.0]}


def cfg() -> dict:
    c = copy.deepcopy(CFG)
    if SMOKE:
        for k, v in SMOKE_CFG.items():
            c[k] = {**c.get(k, {}), **v} if isinstance(v, dict) and isinstance(c.get(k), dict) else v
    return c


def out_dir() -> Path:
    name = "e03h" if not SMOKE else "e03h-smoke" if SMOKE_DEVICE == "cpu" else "e03h-smoke-cuda"
    return ROOT / "runs" / name / "pilot"


def rec_dir() -> Path:
    return out_dir() / "records" if SMOKE else EXP / "pilot"


def rec_path(stage: str) -> Path:
    return rec_dir() / f"{stage}.json"


def read(stage: str) -> dict:
    p = rec_path(stage)
    if not p.exists():
        raise SystemExit(f"{stage} has not run ({p} is missing)")
    doc = json.loads(p.read_text(encoding="utf-8"))
    if doc.get("status") != "completed":
        raise SystemExit(f"{stage} did not complete")
    return doc


def ids(name: str) -> np.ndarray:
    first, n = cfg()[name] if name in ("selection", "test") else cfg()["gate"][name]
    return np.arange(first, first + n)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Clock(reg.CapClock):
    """The pre-registration cap: the pilot's recorded seconds plus step 0's (runs/e03h/step0/compute.json)."""

    def spent_hours(self) -> float:
        total = super().spent_hours()
        s0 = ROOT / "runs" / "e03h" / "step0" / "compute.json"
        if not SMOKE and s0.exists():
            total += json.loads(s0.read_text(encoding="utf-8"))["totals"]["seconds_timed"] / 3600
        return total


def clock() -> reg.CapClock:
    if (out_dir() / "compute").exists():
        acct.write_aggregate(out_dir() / "compute", out_dir() / "compute.json")
    return Clock(cfg()["cap_hours"], out_dir() / "compute.json")


def device() -> str:
    if SMOKE:
        if SMOKE_DEVICE == "cuda" and not torch.cuda.is_available():
            raise SystemExit("--device cuda without CUDA")
        return SMOKE_DEVICE
    if not torch.cuda.is_available():
        raise SystemExit("the pilot runs on CUDA")
    return "cuda"


def mode():
    return replay_mode() if device() == "cuda" else _Null()


class _Null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def t1(mode_: str | None, gains, rates=None) -> Config:
    """02's T1 with 03h's food_fell mode; `gains` None keeps T1's default motor gains (calibration's start)."""
    c = grid.task_config(Config(), "T1")
    if gains is not None:
        c.world.forward_gain, c.world.turn_gain = gains
    c.world.food_fell = mode_
    c.world.food_fell_rates = tuple(rates) if rates is not None else None
    return c


def n2_gains() -> tuple:
    """N2's motor gains from 02's committed calibration, as 02's own gate used them (PILOT.md §2)."""
    c = json.loads((ROOT / "experiments" / "02-screening" / "calibration.json").read_text(encoding="utf-8"))["N2"]
    return (float(c["forward_gain"]), float(c["turn_gain"]))


def smoke_grids() -> None:
    for k, v in SMOKE_GRIDS.items():
        setattr(GT, k, v)


# ----------------------------------------------------------------------------- stages

def stage_bind(args, dv, ck, progress):
    """Records PILOT.md's and DESIGN.md's hashes at the current commit. Commit and push the record before any stage."""
    return {"pilot_md_sha256": sha(PILOT_MD), "design_md_sha256": sha(EXP / "DESIGN.md"),
            "note": "binding: this record is committed and pushed before G1 runs (PILOT.md status)"}


def _gate(fams_parts: str, other: str, rates=None) -> dict:
    if SMOKE:
        smoke_grids()
    dv, gains = device(), n2_gains()
    con = load_connectome()
    iface = interface_03h(con)
    cfgs = {"level": t1("level", gains), other: t1(other, gains, rates)}
    tun, chk = ids("tuning"), ids("check")
    s_t, s_c = cfg()["gate"]["seeds"]
    with acct.category("calibration"):
        fams = GT.tune_families(cfgs, iface, tun, s_t, dv, parts=fams_parts)
    with acct.category("measure"):
        scores = GT.check_scores(fams, cfgs, iface, chk, s_c, dv)
    return {"families": fams, "check_means": {k: float(v.mean()) for k, v in scores.items()},
            "check_scores": {k: v.round(6).tolist() for k, v in scores.items()}, "gains": list(gains), "_s": scores}


def stage_gate(args, dv, ck, progress):
    read("bind")
    g = _gate("all", "relief")
    v = GT.g1_verdicts(g.pop("_s"))
    passed = v["level"]["pass"] and v["relief"]["pass"]
    stop = None if passed else ("stop: reported (the level part failed)" if not v["level"]["pass"]
                                else "stop: redesign (the relief part failed)")
    return {**g, "verdicts": v, "passed": bool(passed), "stop": stop}


def _graphs(con) -> tuple[list, list]:
    """The pilot graphs: SH-mirror-ASK at consecutive seeds, a failed sampler taking the next seed (PILOT.md §3).
    Returns (graphs, failures)."""
    c = cfg()["graphs"]
    out, failures, seed = [], [], c["first_seed"]
    while len(out) < c["n"]:
        if len(failures) > c["max_tries"]:
            raise RuntimeError("too many sampler failures")
        try:
            g, info = SM.build(con, c["kind"], seed, passes=c["passes"])
            out.append({"name": f"pilot{c['kind']}-{seed}", "seed": seed, "graph": g, "info": info})
        except SM.SamplerFailure as e:
            failures.append({"seed": seed, "error": str(e)})
        seed += 1
    return out, failures


def _graph_sha(con) -> str:
    h = hashlib.sha256()
    for a in (con.chem, con.gap):
        h.update(np.ascontiguousarray(a, dtype=np.float32).tobytes())
    return h.hexdigest()


def _genomes(graph, name, cfg_, dv):
    spec = BrainSpec.from_connectome(graph, device=dv)
    gen = torch.Generator(device=dv).manual_seed(genome_seed(name, cfg()["genome_salt"]))
    return Genome.random(spec, cfg_.brain, cfg()["genomes"], generator=gen, device=dv)


def stage_sham_rates(args, dv, ck, progress):
    g1 = read("gate")
    if not g1["passed"]:
        raise SystemExit(f"G1 did not pass: {g1['stop']}")
    con = load_connectome()
    iface = interface_03h(con)
    sel, s_seed = ids("selection"), cfg()["run_seeds"][0]
    rows, counts = [], np.zeros(4, dtype=np.int64)
    states = {}
    graphs, failures = _graphs(con)
    for gr in graphs:
        graph, name = gr["graph"], gr["name"]
        ck.check()
        t0 = time.perf_counter()
        with acct.category("calibration"):
            cal = calib.calibrate_in_world(graph, t1("level", None), iface, grid.TARGET_DRIVE,
                                           n_strains=cfg()["calibration"]["strains"], seed=cfg()["calibration"]["seed"],
                                           device=dv)
        t_cal = time.perf_counter() - t0
        gains = (cal.forward_gain, cal.turn_gain)
        c_lv = t1("level", gains)
        g = _genomes(graph, name, c_lv, dv)
        ck.check()
        t0 = time.perf_counter()
        with acct.category("measure"), mode():
            r = rollout(c_lv, iface, g, sel, s_seed, dv, chunk_worlds=4096)
        t_sel = time.perf_counter() - t0
        n = r.food_fell_counts["relief"]
        counts += n
        states[name] = np.asarray(r.score, dtype=np.float32)
        rows.append({"name": name, "seed": gr["seed"], "graph_sha256": _graph_sha(graph), "gains": list(gains),
                     "calibration": cal.as_dict(), "relief_counts": n.tolist(),
                     "seconds": {"calibration": t_cal, "selection_level": t_sel}})
    n00, n01, n10, n11 = (int(x) for x in counts)
    if n00 + n01 == 0 or n10 + n11 == 0:
        raise RuntimeError("a zero denominator in the sham's rates: 03h stops for redesign (DESIGN §3)")
    p01, p10 = n01 / (n00 + n01), n10 / (n10 + n11)
    path = out_dir() / "states" / "level-selection.npz"
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **{k.replace("/", "_"): v for k, v in states.items()})
    return {"graphs": rows, "sampler_failures": failures, "counts": [n00, n01, n10, n11], "rates": [p01, p10],
            "stationary_occupancy": p01 / (p01 + p10), "level_selection_npz_sha256": sha(path),
            "note": "level trajectories only, bits computed but not injected (DESIGN §3)"}


def stage_gate_sham(args, dv, ck, progress):
    s1 = read("sham-rates")
    g = _gate("memoryless", "sham", s1["rates"])
    v = GT.g2_verdict(g.pop("_s"))
    return {**g, "rates": s1["rates"], "verdict": v, "passed": bool(v["pass"]),
            "stop": None if v["pass"] else "stop: redesign (the sham gate failed)"}


def _rollout_scores(c, iface, g, world_ids, seed, dv):
    with acct.category("measure"), mode():
        return np.asarray(rollout(c, iface, g, world_ids, seed, dv, chunk_worlds=4096).score, dtype=np.float64)


def stage_pilot(args, dv, ck, progress):
    g2 = read("gate-sham")
    if not g2["passed"]:
        raise SystemExit(f"G2 did not pass: {g2['stop']}")
    s1 = read("sham-rates")
    amp = float(args.amplitude)
    if amp != AMPLITUDE:  # P': only after a P whose decile shift did not move (PILOT.md §5.4)
        prev = sorted(rec_path("pilot").parent.glob("pilot.attempt*.json"))
        last = json.loads(prev[-1].read_text(encoding="utf-8")) if prev else {}
        if not prev or last.get("amplitude") != AMPLITUDE or last["readings"]["manipulation"]["decile_shift"]["moves"]:
            raise SystemExit("--amplitude 0.5 only after a completed P at 0.25 whose decile shift did not move")
    con = load_connectome()
    iface = interface_03h(con, amp)
    bank = json.loads((ROOT / "experiments" / "03-generation0" / "pilot.json").read_text(encoding="utf-8"))["bank"]
    sel, test = ids("selection"), ids("test")
    s_sel, s_test = cfg()["run_seeds"]
    with np.load(out_dir() / "states" / "level-selection.npz", allow_pickle=False) as z:
        level_sel = {k: z[k] for k in z.files}
    if sha(out_dir() / "states" / "level-selection.npz") != s1["level_selection_npz_sha256"]:
        raise SystemExit("S1's saved level scores do not match their recorded hash")
    graphs = {gr["name"]: gr for gr in _graphs(con)[0]}
    selsc = {c: [] for c in ("level", "relief", "sham")}
    testsc = {c: [] for c in selsc}
    H, S, Hdir, per_graph, timing = [], [], [], [], []
    for row in s1["graphs"]:
        name = row["name"]
        graph = graphs[name]["graph"]
        if _graph_sha(graph) != row["graph_sha256"]:
            raise SystemExit(f"{name}: the rebuilt graph does not match S1's hash")
        gains = tuple(row["gains"])
        cfgs = {"level": t1("level", gains), "relief": t1("relief", gains), "sham": t1("sham", gains, s1["rates"])}
        g = _genomes(graph, name, cfgs["level"], dv)
        t = {}
        for c in ("level", "relief", "sham"):
            ck.check()
            t0 = time.perf_counter()
            sc = level_sel[name.replace("/", "_")].astype(np.float64) if c == "level" and amp == AMPLITUDE else \
                _rollout_scores(cfgs[c], iface, g, sel, s_sel, dv)
            t[f"selection_{c}"] = time.perf_counter() - t0
            selsc[c].append(sc)
            top = PL.select_decile(sc.mean(1))
            t0 = time.perf_counter()
            testsc[c].append(_rollout_scores(cfgs[c], iface, g.select(top.tolist()), test, s_test, dv))
            t[f"test_{c}"] = time.perf_counter() - t0
        ck.check()
        t0 = time.perf_counter()
        with mode():
            h = history(g, cfgs["level"], iface, bank, per_history=True)
            turn = bit_turn_response(g, cfgs["level"], iface, bank)
        t["history_and_probe"] = time.perf_counter() - t0
        timing.append({"name": name, **t})
        H.append(np.abs(h["raw_turn"]["final"]))
        S.append(np.abs(h["raw_turn"]["steady_contrast"]))
        mt = h["motor_turn"]
        Hdir.append(np.abs(mt["falling"]["final"]) - np.abs(mt["rising"]["final"]))
        rhos = {c: PL.rho(H[-1], S[-1], selsc[c][-1].mean(1)) for c in selsc}
        per_graph.append({
            "name": name, "reliability_level": PL.crossed_reliability(selsc["level"][-1]),
            "rho": {c: r[0] for c, r in rhos.items()}, "degenerate": {c: r[1] for c, r in rhos.items()},
            "D": rhos["sham"][0] - rhos["relief"][0],
            "rho_H_dir_level": PL.rho(Hdir[-1], S[-1], selsc["level"][-1].mean(1))[0],
            "turn_response_mean_abs": float(np.abs(turn).mean()),
        })
    rel = float(np.mean([r["reliability_level"] for r in per_graph]))
    D = np.array([r["D"] for r in per_graph])
    step0 = EXP / "development-records" / "step0.json"
    s0_sd = (json.loads(step0.read_text(encoding="utf-8"))["summary"]["between_graph_sd_rho_level"]
             if step0.exists() and not SMOKE else 0.0)
    s_graph = max(float(D.std(ddof=1)) if len(D) > 1 else 0.0, s0_sd)
    s_shared = PL.shared_world_sd_of_mean_D(selsc, H, S, cfg()["shared_boots"], cfg()["boot_seed"])
    b = PL.b_readings(testsc, cfg()["shared_boots"], cfg()["boot_seed"] + 1)
    W = 16 if rel >= cfg()["reliability_floor"] else 32
    proj = _projection(timing, s1, W)
    moves = b["decile_shift"]["moves"]
    if moves:
        action = "proceed to the pre-registration"
    elif amp == AMPLITUDE:
        action = "rerun as P' at amplitude 0.5 (PILOT.md §5.4)"
    else:
        action = "stop: redesign (the decile shift did not move at 0.5; B could not be read)"
    if moves and not proj["fits"]:
        action = "stop: redesign (the formal run does not fit the cap)"
    return {"amplitude": amp, "per_graph": per_graph, "timing": timing,
            "readings": {"reliability_level_mean": rel, "W": W, "A_secondary": {"D": D.tolist(), "D_mean": float(D.mean())},
                         "power_A2_reported": PL.power(s_graph, s_shared, cfg()["delta_A"], cfg()["formal"]["graphs"]),
                         "B": {k: v for k, v in b.items() if k != "decile_shift"},
                         "manipulation": {"decile_shift": b["decile_shift"],
                                          "turn_response_mean_abs": [r["turn_response_mean_abs"] for r in per_graph]},
                         "projection": proj},
            "action": action}


def _projection(timing, s1, W) -> dict:
    """The formal run's GPU-hours from the pilot's timing (PILOT.md §5.5): per graph, 3 conditions x (256 x W + 26 x 64)
    episodes, scaled from the pilot's measured seconds, plus calibration and the history probe."""
    g = cfg()["genomes"]
    sel_s = np.mean([t[f"selection_{c}"] for t in timing for c in ("relief", "sham")]) / (g * len(ids("selection")))
    test_s = np.mean([t[f"test_{c}"] for t in timing for c in ("level", "relief", "sham")]) / (PL.DECILE * len(ids("test")))
    hist_s = np.mean([t["history_and_probe"] for t in timing])
    cal_s = np.mean([r["seconds"]["calibration"] for r in s1["graphs"]])
    per_graph = 3 * (256 * W * sel_s + PL.DECILE * 64 * test_s) + hist_s + cal_s
    n = cfg()["formal"]["graphs"] + 1
    hours = n * per_graph / 3600
    return {"per_graph_seconds": float(per_graph), "graphs": n, "W": W, "hours": float(hours),
            "cap_hours": cfg()["formal"]["cap_hours"], "fits": bool(hours <= cfg()["formal"]["cap_hours"]),
            "note": "an extrapolation from the pilot's compositions"}


FUNCS = {"bind": stage_bind, "gate": stage_gate, "sham-rates": stage_sham_rates, "gate-sham": stage_gate_sham,
         "pilot": stage_pilot}
DEFAULT_CATEGORY = {"bind": "measure", "gate": "calibration", "sham-rates": "measure", "gate-sham": "calibration",
                    "pilot": "measure"}


def run_stage(args) -> dict:
    stage = args.stage
    prov = reg.provenance(GUARDED)
    if not SMOKE:
        if prov["dirty"]:
            raise SystemExit("uncommitted changes in the guarded files: commit first")
        reg.require_pins(prov)
    if stage != "bind":
        bound = read("bind")
        if sha(PILOT_MD) != bound["pilot_md_sha256"]:
            raise SystemExit("PILOT.md differs from the bound registration")
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
    dv = device()
    ck = clock()
    t0 = time.time()
    doc = {"stage": stage, "smoke": SMOKE, "device": dv, "provenance": prov, "config": cfg(),
           "rerun_reason": args.reason, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    progress: dict = {}
    try:
        with acct.recorded(out_dir() / "compute", out_dir() / "compute.json", default=DEFAULT_CATEGORY[stage],
                           experiment="03h", stage=stage, script="scripts/e03h.py"):
            doc.update(FUNCS[stage](args, dv, ck, progress))
        doc["status"] = "completed"
    except BaseException as e:  # noqa: BLE001  (recorded, then re-raised)
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
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--reason")
    ap.add_argument("--amplitude", type=float, default=AMPLITUDE)
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="with --smoke only")
    args = ap.parse_args(argv)
    if args.device != "cpu" and not args.smoke:
        raise SystemExit("--device is for smoke runs; the pilot itself runs on CUDA")
    SMOKE, SMOKE_DEVICE = args.smoke, args.device
    if args.amplitude not in (AMPLITUDE, 0.5):
        raise SystemExit("the amplitude is 0.25, or 0.5 by PILOT.md §5.4's rule")
    doc = run_stage(args)
    print(f"{args.stage}: {doc['status']} in {doc['seconds']:.0f} s -> {rec_path(args.stage)}"
          + (f"; {doc.get('action') or doc.get('stop') or ''}" if args.stage != "bind" else ""))
    return doc


if __name__ == "__main__":
    main()
