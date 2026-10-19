"""03h's pilot (experiments/03h-history-use/PILOT.md; DESIGN.md v3.3 §7).

    python scripts/e03h.py bind          # records PILOT.md's and DESIGN.md's hashes; commit and push before any stage
    python scripts/e03h.py gate          # G1: the scripted gate's level and relief parts
    python scripts/e03h.py sham-rates    # S1: level trajectories on the 3 pilot graphs; the sham's rates; timing
    python scripts/e03h.py gate-sham     # G2: the gate's sham part, with S1's rates (G1's families reused)
    python scripts/e03h.py pilot         # P: the three conditions on the 3 pilot graphs; PILOT.md §5's readings
    python scripts/e03h.py pilot --amplitude 0.5 --rerun --reason "..."   # P': only by PILOT.md §5.4's rule
    python scripts/e03h.py <stage> --smoke                 # tiny sizes on the CPU, to runs/e03h-smoke/
    python scripts/e03h.py <stage> --smoke --device cuda   # the same on CUDA, to runs/e03h-smoke-cuda/: the preflight

Smoke runs use their own world ids, seeds and graph seeds, disjoint from the registered ones (Astra).

**Every stage refuses when:**
- the stage before it has not completed with its criteria met;
- an upstream record has changed since a downstream record read it (each record carries its predecessors' hashes;
  Astra);
- PILOT.md or DESIGN.md differs from the bound hashes;
- outside smoke, the guarded tree is dirty, HEAD is not pushed, or the implementation (`CODE`) has changed since the
  bound commit (Astra, round 2);
- the cap is reached before it starts.

**The cap:** 1.0 GPU-hour for everything before the pre-registration, step 0 included, counted across attempts. It is
checked before every bounded unit of work. A unit that has started runs to completion, and the record notes any
overrun.

Records go to experiments/03h-history-use/pilot/. Genomes, pilot graphs and per-genome arrays stay local: the graphs
and genomes are rebuilt from their seeds and checked by hash, and the arrays' hash is recorded.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
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
PILOT_MD, DESIGN_MD = EXP / "PILOT.md", EXP / "DESIGN.md"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", "experiments/03h-history-use/DESIGN.md",
           "experiments/03h-history-use/PILOT.md", "experiments/03h-history-use/pilot/bind.json",
           "experiments/03-generation0/pilot.json", "experiments/02-screening/calibration.json"]
CODE = [p for p in GUARDED if not p.endswith("bind.json")]  # fixed from the bound commit on; bind.json comes after
STAGES = ["bind", "gate", "sham-rates", "gate-sham", "pilot"]
UPSTREAM = {"gate": ["bind"], "sham-rates": ["gate"], "gate-sham": ["sham-rates", "gate"],
            "pilot": ["gate-sham", "sham-rates", "gate"]}
SMOKE = False
SMOKE_DEVICE = "cpu"

# registered (PILOT.md §7). Fresh banks: the first draft's were played by the CUDA smoke preflight (D333)
CFG = {
    "gate": {"tuning": [3_640_000, 64], "check": [3_641_000, 256], "seeds": [3_642_001, 3_642_002]},
    "graphs": {"kind": "SH-mirror-ASK", "first_seed": 3_660_001, "n": 3, "passes": 20, "max_failures": 10},
    "calibration": {"seed": 3_661_000, "strains": 1024},
    "genome_salt": "03h-pilot:", "genomes": 256,
    "selection": [3_650_000, 16], "test": [3_651_000, 64], "run_seeds": [3_652_001, 3_652_002],
    "boot_seeds": [3_653_000, 3_653_001], "shared_boots": 2000, "cap_hours": 1.0, "delta_A": 0.05,
    "reliability_floor": 0.85, "formal": {"primary_graphs": 65, "sh_graphs": 64, "cap_hours": 6.0},
}
# smoke: its own ids and seeds, disjoint from the registered ones
SMOKE_CFG = {
    "gate": {"tuning": [3_690_000, 3], "check": [3_691_000, 6], "seeds": [3_692_001, 3_692_002]},
    "graphs": {"kind": "SH-mirror-ASK", "first_seed": 3_695_001, "n": 2, "passes": 1, "max_failures": 10},
    "calibration": {"seed": 3_696_000, "strains": 8},
    "genome_salt": "03h-smoke:", "genomes": 32, "selection": [3_693_000, 3], "test": [3_694_000, 4],
    "run_seeds": [3_697_001, 3_697_002], "boot_seeds": [3_698_000, 3_698_001], "shared_boots": 20,
}
SMOKE_GRIDS = {"K": {"slow": [0.0, 1.0], "fast": [1.0], "threshold": [0.1, 1.0], "turn": [0.0, 0.2]},
               "G": {"slow": [0.0], "fast": [1.0], "scale": [1.0], "turn": [0.2]},
               "FALL": {"fall_turn": [0.7], "fall_threshold": [0.0]}, "T": [1.0, 5.0]}


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


def sha(path: Path) -> str:
    return reg.file_sha256(path)  # line endings normalised (Fable)


def read(stage: str) -> dict:
    """A completed stage's record, whose own upstream records are unchanged since it read them (Astra)."""
    p = rec_path(stage)
    if not p.exists():
        raise SystemExit(f"{stage} has not run ({p} is missing)")
    doc = json.loads(p.read_text(encoding="utf-8"))
    if doc.get("status") != "completed":
        raise SystemExit(f"{stage} did not complete")
    for up, h in doc.get("upstream", {}).items():
        if not rec_path(up).exists() or sha(rec_path(up)) != h:
            raise SystemExit(f"{stage} is stale: {up} changed after {stage} read it; rerun {stage}")
    return doc


def ids(name: str) -> np.ndarray:
    first, n = cfg()[name] if name in ("selection", "test") else cfg()["gate"][name]
    return np.arange(first, first + n)


class Clock(reg.CapClock):
    """The pre-registration cap: the pilot's recorded seconds plus step 0's (runs/e03h/step0/compute.json)."""

    def spent_hours(self) -> float:
        total = super().spent_hours()
        s0 = ROOT / "runs" / "e03h" / "step0" / "compute.json"
        if not SMOKE and s0.exists():
            total += json.loads(s0.read_text(encoding="utf-8"))["totals"]["seconds_timed"] / 3600
        return total

    def over_at_end(self) -> bool:
        """After a stage's attempt is in the aggregate: its time counted once (Fable, Astra, round 2)."""
        return self.spent_hours() > self.cap_hours


def clock() -> Clock:
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


class _Null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def mode():
    return replay_mode() if device() == "cuda" else _Null()


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


def graph_sha(con) -> str:
    h = hashlib.sha256()
    for a in (con.chem, con.gap):
        h.update(np.ascontiguousarray(a, dtype=np.float32).tobytes())
    return h.hexdigest()


def genome_sha(g: Genome) -> str:
    return hashlib.sha256(g.flat().detach().cpu().numpy().astype(np.float32).tobytes()).hexdigest()


def genomes_for(graph, name, cfg_, dv) -> Genome:
    spec = BrainSpec.from_connectome(graph, device=dv)
    gen = torch.Generator(device=dv).manual_seed(genome_seed(name, cfg()["genome_salt"]))
    return Genome.random(spec, cfg_.brain, cfg()["genomes"], generator=gen, device=dv)


def graph_name(seed: int) -> str:
    return f"pilot{cfg()['graphs']['kind']}-{seed}"


# ----------------------------------------------------------------------------- stages

def stage_bind(args, dv, ck, progress):
    """Records PILOT.md's and DESIGN.md's hashes and the bound commit. Commit and push the record before any stage
    (PILOT.md §1)."""
    return {"pilot_md_sha256": sha(PILOT_MD), "design_md_sha256": sha(DESIGN_MD),
            "bound_commit": reg.git("rev-parse", "HEAD"),
            "note": "binding: this record is committed and pushed before G1 runs; the implementation stays as at "
                    "bound_commit for every stage"}


def _gate(other: str, rates=None, base=None, parts="all", ck=None) -> tuple[dict, dict]:
    dv, gains = device(), n2_gains()
    con = load_connectome()
    iface = interface_03h(con)
    cfgs = {"level": t1("level", gains), other: t1(other, gains, rates)}
    s_t, s_c = cfg()["gate"]["seeds"]
    check = None if ck is None else ck.check
    with mode():
        with acct.category("calibration"):
            fams = GT.tune_families(cfgs, iface, ids("tuning"), s_t, dv, parts=parts,
                                    grids=SMOKE_GRIDS if SMOKE else None, check=check, base=base)
        with acct.category("measure"):
            scores = GT.check_scores(fams, cfgs, iface, ids("check"), s_c, dv, check=check)
    rec = {"families": fams, "check_means": {k: float(v.mean()) for k, v in scores.items()},
           "check_scores": {k: v.round(6).tolist() for k, v in scores.items()}, "gains": list(gains)}
    return rec, scores


def stage_gate(args, dv, ck, progress):
    rec, scores = _gate("relief", ck=ck)
    v = GT.g1_verdicts(scores)
    passed = v["level"]["pass"] and v["relief"]["pass"]
    stop = None if passed else ("stop: reported (the level part failed)" if not v["level"]["pass"]
                                else "stop: redesign (the relief part failed)")
    return {**rec, "verdicts": v, "passed": bool(passed), "stop": stop}


def _accepted_graphs(con, dv, ck, progress):
    """S1's graphs (PILOT.md §3): SH-mirror-ASK at consecutive seeds; a sampler failure or a calibration failure takes
    the next seed, recorded. Returns ([(seed, graph, calibration)], failures)."""
    c = cfg()["graphs"]
    iface = interface_03h(con)
    out, failures = [], []
    progress["failures"] = failures  # live: a cap or an excess of failures keeps the trail (Astra, round 2)
    seconds = progress.setdefault("seconds_s1", {"sampler_cpu": 0.0, "calibration": 0.0})
    for seed in itertools.count(c["first_seed"]):
        if len(out) == c["n"]:
            break
        if len(failures) > c["max_failures"]:
            raise RuntimeError("too many sampler or calibration failures")
        ck.check()
        t0 = time.perf_counter()
        try:
            g, _ = SM.build(con, c["kind"], seed, passes=c["passes"])
        except SM.SamplerFailure as e:
            failures.append({"seed": seed, "failed": "sampler", "error": str(e)})
            continue
        finally:
            seconds["sampler_cpu"] += time.perf_counter() - t0
        t0 = time.perf_counter()
        try:
            with acct.category("calibration"):
                cal = calib.calibrate_in_world(g, t1("level", None), iface, grid.TARGET_DRIVE,
                                               n_strains=cfg()["calibration"]["strains"],
                                               seed=cfg()["calibration"]["seed"], device=dv)
        except RuntimeError as e:  # calibrate_in_world raises on non-convergence (Fable, Astra)
            failures.append({"seed": seed, "failed": "calibration", "error": str(e)})
            continue
        finally:
            seconds["calibration"] += time.perf_counter() - t0
        out.append((seed, g, cal))
    return out, failures


def stage_sham_rates(args, dv, ck, progress):
    con = load_connectome()
    iface = interface_03h(con)
    sel, s_seed = ids("selection"), cfg()["run_seeds"][0]
    rows, counts, states = [], np.zeros(4, dtype=np.int64), {}
    graphs, failures = _accepted_graphs(con, dv, ck, progress)
    for seed, graph, cal in graphs:
        name = graph_name(seed)
        gains = (cal.forward_gain, cal.turn_gain)
        c_lv = t1("level", gains)
        g = genomes_for(graph, name, c_lv, dv)
        ck.check()
        t0 = time.perf_counter()
        with acct.category("measure"), mode():
            r = rollout(c_lv, iface, g, sel, s_seed, dv, chunk_worlds=4096)
        t_sel = time.perf_counter() - t0
        n = r.food_fell_counts["relief"]
        counts += n
        states[name] = np.asarray(r.score, dtype=np.float32)
        rows.append({"name": name, "seed": seed, "graph_sha256": graph_sha(graph), "genome_sha256": genome_sha(g),
                     "gains": list(gains), "calibration": cal.as_dict(), "relief_counts": n.tolist(),
                     "seconds": {"selection_level": t_sel}})
    n00, n01, n10, n11 = (int(x) for x in counts)
    if n00 + n01 == 0 or n10 + n11 == 0:
        raise RuntimeError("a zero denominator in the sham's rates: 03h stops for redesign (DESIGN §3)")
    p01, p10 = n01 / (n00 + n01), n10 / (n10 + n11)
    path = out_dir() / "states" / "level-selection.npz"
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **states)
    return {"graphs": rows, "failures": failures, "seconds_s1": progress["seconds_s1"],
            "counts": [n00, n01, n10, n11], "rates": [p01, p10], "stationary_occupancy": p01 / (p01 + p10),
            "level_selection_npz_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "note": "level trajectories only, bits computed but not injected (DESIGN §3)"}


def stage_gate_sham(args, dv, ck, progress):
    g1, s1 = read("gate"), read("sham-rates")
    rec, scores = _gate("sham", s1["rates"], base=g1["families"], parts="memoryless", ck=ck)
    v = GT.g2_verdict(scores)
    return {**rec, "rates": s1["rates"], "verdict": v, "passed": bool(v["pass"]),
            "stop": None if v["pass"] else "stop: redesign (the sham gate failed)"}


def _scores(c, iface, g, world_ids, seed, dv) -> tuple[np.ndarray, dict | None]:
    with acct.category("measure"), mode():
        r = rollout(c, iface, g, world_ids, seed, dv, chunk_worlds=4096)
    counts = None if r.food_fell_counts is None else {k: v.tolist() for k, v in r.food_fell_counts.items()}
    return np.asarray(r.score, dtype=np.float64), counts


def _escalation_allowed(upstream: dict) -> None:
    """P' at 0.5 (PILOT.md §5.4): only after a completed P at 0.25 on the current chain (the same G1, S1 and G2
    records; Astra, round 2) whose decile shift did not move, and only once; a P' that failed to complete may be retried
    (Astra)."""
    d = rec_path("pilot").parent
    files = [d / "pilot.json", *sorted(d.glob("pilot.attempt*.json"))]
    attempts = [json.loads(p.read_text(encoding="utf-8")) for p in files if p.exists()]
    qualifying = [a for a in attempts if a.get("status") == "completed" and a.get("amplitude") == AMPLITUDE
                  and a.get("upstream") == upstream
                  and not a["readings"]["manipulation"]["decile_shift"]["moves"]
                  and a.get("action", "").startswith("rerun as P'")]
    if not qualifying:
        raise SystemExit("--amplitude 0.5 only after a completed P at 0.25, on the current G1, S1 and G2 records, "
                         "whose decile shift did not move")
    if any(a.get("status") == "completed" and a.get("amplitude") == 0.5 for a in attempts):
        raise SystemExit("the amplitude was already raised once (PILOT.md §5.4)")


def _eligible(stage: str, args, upstream: dict) -> None:
    """A stage's entry conditions, all checked before a rerun moves the old record aside (Fable, round 2)."""
    if stage in ("sham-rates", "gate-sham"):
        g1 = read("gate")
        if not g1["passed"]:
            raise SystemExit(f"G1 did not pass: {g1['stop']}")
    if stage == "pilot":
        g2, s1 = read("gate-sham"), read("sham-rates")
        if not g2["passed"]:
            raise SystemExit(f"G2 did not pass: {g2['stop']}")
        if list(g2["rates"]) != list(s1["rates"]):
            raise SystemExit("G2 tested other sham rates than S1's")
        if float(args.amplitude) != AMPLITUDE:
            _escalation_allowed(upstream)


def stage_pilot(args, dv, ck, progress):
    s1 = read("sham-rates")
    amp = float(args.amplitude)
    con = load_connectome()
    iface = interface_03h(con, amp)
    bank = json.loads((ROOT / "experiments" / "03-generation0" / "pilot.json").read_text(encoding="utf-8"))["bank"]
    sel, test = ids("selection"), ids("test")
    s_sel, s_test = cfg()["run_seeds"]
    npz = out_dir() / "states" / "level-selection.npz"
    if hashlib.sha256(npz.read_bytes()).hexdigest() != s1["level_selection_npz_sha256"]:
        raise SystemExit("S1's saved level scores do not match their recorded hash")
    with np.load(npz, allow_pickle=False) as z:
        level_sel = {k: z[k] for k in z.files}
    conds = ("level", "relief", "sham")
    selsc, testsc = {c: [] for c in conds}, {c: [] for c in conds}
    H, S, Hdir, per_graph, timing, arrays = [], [], [], [], [], {}
    for row in s1["graphs"]:
        name = row["name"]
        graph, _ = SM.build(con, cfg()["graphs"]["kind"], row["seed"], passes=cfg()["graphs"]["passes"])
        if graph_sha(graph) != row["graph_sha256"]:
            raise SystemExit(f"{name}: the rebuilt graph does not match S1's hash")
        gains = tuple(row["gains"])
        cfgs = {"level": t1("level", gains), "relief": t1("relief", gains), "sham": t1("sham", gains, s1["rates"])}
        g = genomes_for(graph, name, cfgs["level"], dv)
        if genome_sha(g) != row["genome_sha256"]:
            raise SystemExit(f"{name}: the regenerated genomes do not match S1's (Fable)")
        t, realised, deciles = {}, {}, {}
        for c in conds:
            ck.check()
            t0 = time.perf_counter()
            if c == "level" and amp == AMPLITUDE:  # S1's, same genomes, worlds, run seed and interface
                sc, realised[c] = level_sel[name].astype(np.float64), None
            else:
                sc, realised[c] = _scores(cfgs[c], iface, g, sel, s_sel, dv)
            t[f"selection_{c}"] = time.perf_counter() - t0
            selsc[c].append(sc)
            top = PL.select_decile(sc.mean(1))
            deciles[c] = top
            ck.check()
            t0 = time.perf_counter()
            ts, _ = _scores(cfgs[c], iface, g.select(top.tolist()), test, s_test, dv)
            testsc[c].append(ts)
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
        rhos = {c: PL.rho(H[-1], S[-1], selsc[c][-1].mean(1)) for c in conds}
        per_graph.append({
            "name": name, "reliability_level": PL.crossed_reliability(selsc["level"][-1]),
            "rho": {c: r[0] for c, r in rhos.items()}, "degenerate": {c: r[1] for c, r in rhos.items()},
            "D": rhos["sham"][0] - rhos["relief"][0],
            "rho_H_dir_level": PL.rho(Hdir[-1], S[-1], selsc["level"][-1].mean(1))[0],
            "quartile_difference_level": PL.quartile_difference(H[-1], selsc["level"][-1].mean(1)),
            "turn_response_mean_abs": float(np.abs(turn).mean()),
            "realised_food_fell_counts": realised,  # per condition: the relief bit's and the injected bit's (DESIGN §3)
        })
        arrays.update({f"{name}::H": H[-1], f"{name}::S": S[-1], f"{name}::H_dir": Hdir[-1], f"{name}::turn": turn})
        for c in conds:
            arrays.update({f"{name}::selection_{c}": selsc[c][-1], f"{name}::test_{c}": testsc[c][-1],
                           f"{name}::decile_{c}": deciles[c]})
    apath = out_dir() / "states" / f"pilot-arrays-amp{amp}.npz"
    np.savez(apath, **arrays)  # per-genome arrays, kept locally with their hash (Fable)
    rel = float(np.mean([r["reliability_level"] for r in per_graph]))
    D = np.array([r["D"] for r in per_graph])
    step0 = EXP / "development-records" / "step0.json"
    s0_sd = (json.loads(step0.read_text(encoding="utf-8"))["summary"]["between_graph_sd_rho_level"]
             if step0.exists() and not SMOKE else 0.0)
    s_graph = max(float(D.std(ddof=1)) if len(D) > 1 else 0.0, s0_sd)
    b1, b2 = cfg()["boot_seeds"]
    s_shared = PL.shared_world_sd_of_mean_D(selsc, H, S, cfg()["shared_boots"], b1)
    b = PL.b_readings(testsc, cfg()["shared_boots"], b2)
    W = 16 if rel >= cfg()["reliability_floor"] else 32
    proj = _projection(timing, s1, W)
    moves = b["decile_shift"]["moves"]
    if not proj["fits"]:  # the budget takes precedence over the amplitude rule (Astra)
        action = "stop: redesign (no formal plan fits the cap)"
    elif moves:
        action = "proceed to the pre-registration"
    elif amp == AMPLITUDE:
        action = "rerun as P' at amplitude 0.5 (PILOT.md §5.4)"
    else:
        action = "stop: redesign (the decile shift did not move at 0.5; B could not be read)"
    return {"amplitude": amp, "per_graph": per_graph, "timing": timing,
            "arrays_npz": apath.name, "arrays_npz_sha256": hashlib.sha256(apath.read_bytes()).hexdigest(),
            "readings": {"reliability_level_mean": rel, "W": W,
                         "A_secondary": {"D": D.tolist(), "D_mean": float(D.mean())},
                         "power_A2_reported": PL.power(s_graph, s_shared, cfg()["delta_A"], 64),
                         "B": {k: v for k, v in b.items() if k != "decile_shift"},
                         "manipulation": {"decile_shift": b["decile_shift"],
                                          "turn_response_mean_abs": [r["turn_response_mean_abs"] for r in per_graph]},
                         "projection": proj},
            "action": action}


def _projection(timing, s1, W) -> dict:
    """PILOT.md §5.5: per graph, 3 conditions x (256 x W + 26 x W_t) episodes at the pilot's measured per-episode
    seconds, plus calibration and the history probe; then DESIGN §8's cut order (`projection_table`). The sampler's CPU
    seconds are reported but not counted, as DESIGN §8 excludes them (Astra, round 2). An extrapolation from the
    pilot's compositions."""
    g, n_sel, n_test = cfg()["genomes"], len(ids("selection")), len(ids("test"))
    sel_s = np.mean([t[f"selection_{c}"] for t in timing for c in ("relief", "sham")]) / (g * n_sel)
    test_s = np.mean([t[f"test_{c}"] for t in timing for c in ("level", "relief", "sham")]) / (PL.DECILE * n_test)
    fixed = np.mean([t["history_and_probe"] for t in timing]) + s1["seconds_s1"]["calibration"] / len(timing)
    per = {wt: float(3 * (256 * W * sel_s + PL.DECILE * wt * test_s) + fixed) for wt in (64, 32)}
    f = cfg()["formal"]
    return {**PL.projection_table(per, f["cap_hours"], f["primary_graphs"], f["sh_graphs"]),
            "per_graph_seconds": {str(k): v for k, v in per.items()}, "W": W,
            "sampler_cpu_seconds_per_graph_not_counted": s1["seconds_s1"]["sampler_cpu"] / len(timing),
            "note": "an extrapolation from the pilot's compositions (at smoke size it is meaningless)"}


FUNCS = {"bind": stage_bind, "gate": stage_gate, "sham-rates": stage_sham_rates, "gate-sham": stage_gate_sham,
         "pilot": stage_pilot}
DEFAULT_CATEGORY = {"bind": "measure", "gate": "calibration", "sham-rates": "measure", "gate-sham": "calibration",
                    "pilot": "measure"}


def run_stage(args) -> dict:
    stage = args.stage
    prov = reg.provenance(GUARDED)
    if not SMOKE:
        if stage == "bind":
            if prov["dirty"]:
                raise SystemExit("uncommitted changes in the guarded files: commit first")
        else:
            reg.require_pushed(prov)  # the bound registration is public before any stage (Fable, Astra)
        reg.require_pins(prov)
    upstream = {}
    if stage != "bind":
        bound = read("bind")
        if sha(PILOT_MD) != bound["pilot_md_sha256"] or sha(DESIGN_MD) != bound["design_md_sha256"]:
            raise SystemExit("PILOT.md or DESIGN.md differs from the bound registration")
        if not SMOKE:
            reg.require_same_code(bound["bound_commit"], CODE)  # the implementation as bound (Astra, round 2)
        for up in UPSTREAM[stage]:
            read(up)
            upstream[up] = sha(rec_path(up))
        _eligible(stage, args, upstream)
    dv = device()
    ck = clock()
    ck.check()  # the cap, before the stage starts and before a rerun moves anything (Astra; Fable, round 2)
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
    t0 = time.time()
    doc = {"stage": stage, "smoke": SMOKE, "device": dv, "provenance": prov, "config": cfg(), "upstream": upstream,
           "rerun_reason": args.reason, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    progress: dict = {}
    try:
        with acct.recorded(out_dir() / "compute", out_dir() / "compute.json", default=DEFAULT_CATEGORY[stage],
                           experiment="03h", stage=stage, script="scripts/e03h.py"):
            doc.update(FUNCS[stage](args, dv, ck, progress))
        doc["status"] = "completed"
        # a started unit runs to completion; the overrun is recorded. The aggregate already holds this attempt, so it
        # is counted once (Fable, Astra, round 2)
        doc["over_cap_at_end"] = bool(ck.over_at_end())
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
    if args.amplitude not in (AMPLITUDE, 0.5):
        raise SystemExit("the amplitude is 0.25, or 0.5 by PILOT.md §5.4's rule")
    SMOKE, SMOKE_DEVICE = args.smoke, args.device
    doc = run_stage(args)
    print(f"{args.stage}: {doc['status']} in {doc['seconds']:.0f} s -> {rec_path(args.stage)}"
          + (f"; {doc.get('action') or doc.get('stop') or ''}" if args.stage != "bind" else ""))
    return doc


if __name__ == "__main__":
    main()
