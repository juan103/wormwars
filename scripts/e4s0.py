"""E4s-0: diagnostics before the comparator graft (exploratory; docs/E4s/E4s-0-PLAN.md v2).

    python scripts/e4s0.py project       # times each formal composition, projects, freezes the sizes
    python scripts/e4s0.py sweep         # 1. the residual stereo-gain sweep on the 47 champions
    python scripts/e4s0.py attenuation   # 2. where the champions' response is attenuated (open loop)
    python scripts/e4s0.py ladder        # 3. the comparator ladder: tuning, qualification, dynamics
    python scripts/e4s0.py populations   # 3. simulated generation-0 populations, backgrounds, 04a run 2
    python scripts/e4s0.py robustness    # 4. mutational robustness of the comparator
    add --smoke for toy sizes in runs/e4s0-smoke (never results)

Each stage runs once, inside E2's stage frame (markers, the cap clock, reruns, not-completed records),
configured for E4s-0's folder. The 2 GPU-hour cap covers everything, the projection included; a stage
starts only if the hours spent plus its projected remaining work stay within 1.8 h.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import graft as G  # noqa: E402
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e4s import comparator as C  # noqa: E402
from wormwars.e4s import diagnostics as DG  # noqa: E402
from wormwars.evo.rollout import rollout as _rollout  # noqa: E402
from wormwars.evo.genomes import genome_hash  # noqa: E402


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


E = _load("e2_for_e4s0", "e2.py")  # E4s-0's own copy of E2's stage frame
D2 = _load("e2d_for_e4s0", "e2d.py")  # E2d's registered rules and champion loaders, unchanged

EXP = ROOT / "experiments" / "E4s-stereo-module" / "E4s-0"
OUT = ROOT / "runs" / "e4s0"
PLAN = "docs/E4s/E4s-0-PLAN.md"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PLAN, *E.E1_INPUTS, *D2.SOURCE_RECORDS]
SMOKE = False

LADDER_STEPS = ["L1", "L2", "L3", "L4x2", "L4x4"]
REGISTERED = {
    # E2's task (the stage frame reads these keys)
    "world_seed": E.REGISTERED["world_seed"], "task_sigma": E.REGISTERED["task_sigma"],
    "ga": copy.deepcopy(E.REGISTERED["ga"]), "checkpoint_every": 25, "rerun_kill_tail_seconds": 900,
    "cap_gpu_hours": 2.0, "admit_hours": 1.8, "champions": 47,
    "sweep": {"ks": [0, 0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 256], "first": 940_000_000, "worlds": 512,
              "chunk_strains": 8},
    "attenuation": {"levels": [0.02, 0.08, 0.25], "d": 0.001, "dm": 0.01, "ticks": 40, "average": 10,
                    "neurons": ["ASEL", "ASER", "AWAL", "AWAR", "AWCL", "AWCR", "AIYL", "AIYR", "AIZL", "AIZR",
                                "AIAL", "AIAR", "AIBL", "AIBR", "RIAL", "RIAR", "SMDDL", "SMDDR", "SMDVL", "SMDVR",
                                "RMDDL", "RMDDR", "RMDVL", "RMDVR"]},
    "ladder": {"steps": LADDER_STEPS, "w_n": [1.0, 2.0, 3.0], "w_o": [1.0, 2.0, 3.0], "tau": [0.5, 2.0],
               "bias": [-0.5, 0.0], "forward": [0.5, 1.0], "turn": [0.0, 0.1, 0.2], "w_s": [0.5, 0.8, 0.95],
               "w_m": [-0.5, -0.8, -0.95], "tune_first": 940_100_000, "step_stride": 20_000, "tune_worlds": 128,
               "rescore_offset": 1_000, "rescore_worlds": 512, "top": 5, "qual_first": 940_300_000,
               "qual_stride": 10_000, "qual_worlds": 1024, "lower_bound": 5.0, "tune_chunk_strains": 32},
    "dynamics": {"levels": [0.02, 0.08, 0.25], "precondition": 60, "horizon": 400, "step": 0.01},
    "populations": {"n": 16, "size": 32, "seed_base": 1_150_000, "select_first": 940_500_000, "select_worlds": 8,
                    "d_first": 940_510_000, "d_worlds": 1024, "bg_first": 940_520_000, "bg_worlds": 64,
                    "e04a_first": 940_540_000, "e04a_worlds": 1024, "e04a_label": "04a run02", "needed": 12,
                    "g0_chunk_strains": 4, "bg_chunk_strains": 64},
    "robustness": {"mutants": 256, "scales": [0.125, 0.25, 1.0], "seed_base": 1_151_000, "first": 940_560_000,
                   "worlds": 64, "chunk_strains": 64},
    "probes": ["real", "mean", "swapped"],
    "shrink": [["populations", "bg_worlds", 32], ["ladder", "tune_worlds", 64], ["sweep", "worlds", 256]],
}
REGISTERED_FULL = copy.deepcopy(REGISTERED)  # the sizes before any shrink
STAGES = ["project", "sweep", "attenuation", "ladder", "populations", "robustness"]
RECORD = {s: s for s in STAGES}
WHAT = {"project": "the projection", "sweep": "the residual sweep", "attenuation": "the attenuation probe",
        "ladder": "the comparator ladder", "populations": "the generation-0 populations",
        "robustness": "the robustness measurement"}


def configure() -> None:
    """Point this copy of E2's stage frame at E4s-0's folders, stages and registered numbers."""
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, OUT, GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E4s-0: not completed (the run stopped)",
                  "cap": "E4s-0: not completed (the cap was reached)"}
    E.RECORD.update(RECORD)
    E.WHAT.update(WHAT)


configure()


# ============================================================================== ids and pure rules

def ladder_ids(step: int, what: str) -> np.ndarray:
    L = REGISTERED["ladder"]
    if what == "tune":
        first, n = L["tune_first"] + L["step_stride"] * step, L["tune_worlds"]
    elif what == "rescore":
        first, n = L["tune_first"] + L["step_stride"] * step + L["rescore_offset"], L["rescore_worlds"]
    elif what == "qual":
        first, n = L["qual_first"] + L["qual_stride"] * step, L["qual_worlds"]
    else:
        raise ValueError(what)
    return np.arange(first, first + n)


def selection_ids(i: int) -> np.ndarray:
    P = REGISTERED["populations"]
    if SMOKE:
        return E.SMOKE_IDS[8 * i:8 * i + P["select_worlds"]]
    return P["select_first"] + P["select_worlds"] * i + np.arange(P["select_worlds"])


def population_selection_ids(n: int, size: int) -> np.ndarray:
    """[n x size, worlds]: every strain of population i reads population i's selection worlds."""
    return np.concatenate([np.tile(selection_ids(i), (size, 1)) for i in range(n)])


def pick_g0(play_fn, n: int, size: int) -> np.ndarray:
    """Each population's generation-0 best, scored on its own selection worlds (`play_fn(ids)` returns
    [strains, worlds] counts), as `evolve_batch` picks generation 0's best."""
    return DG.g0_bests(play_fn(population_selection_ids(n, size)), size)


def rescore_choice(top: list[int], means) -> int:
    """Among the re-scored candidates (`top`, in screening order), the best re-score; ties to the
    lowest grid index (Astra)."""
    order = sorted(range(len(top)), key=lambda i: (-float(means[i]), top[i]))
    return top[order[0]]


def robustness_shares(child_counts: np.ndarray, parent_mean: float):
    """Each child's mean as a share of the parent's; undefined (None) when the parent scores 0."""
    if parent_mean <= 0:
        return None
    return (np.asarray(child_counts, dtype=np.float64).mean(axis=1) / parent_mean).tolist()


def robustness_reading(parent_mean: float, median_0125, median_025) -> dict:
    """The plan's fallback: 0.125x if the median child keeps less than half at 0.25x and at least half at
    0.125x; 0.25x if 0.25x keeps half; otherwise not drawn."""
    if parent_mean <= 0 or median_0125 is None or median_025 is None:
        return {"fallback": "undefined (the parent scores 0)"}
    if median_025 >= 0.5:
        return {"fallback": "0.25x"}
    if median_0125 >= 0.5:
        return {"fallback": "0.125x"}
    return {"fallback": "neither scale keeps half: not drawn"}


def on_bounds(c: dict, bcfg) -> list[str]:
    """The candidate's parameters that sit on the genome's hard bounds (mutation is clamped there; Fable)."""
    out = [k for k in ("w_n", "w_o", "w_s", "w_m") if k in c and abs(abs(float(c[k])) - bcfg.w_max) < 1e-9]
    if abs(float(c["tau"]) - bcfg.tau_min) < 1e-9 or abs(float(c["tau"]) - bcfg.tau_max) < 1e-9:
        out.append("tau")
    if abs(abs(float(c["bias"])) - bcfg.b_max) < 1e-9:
        out.append("bias")
    return out


def formal_ranges() -> dict:
    """Every formal world range, as half-open [first, last + 1), for the disjointness test."""
    S, L, P, R = REGISTERED["sweep"], REGISTERED["ladder"], REGISTERED["populations"], REGISTERED["robustness"]
    out = {"sweep": (S["first"], S["first"] + S["worlds"])}
    for s, name in enumerate(LADDER_STEPS):
        for what in ("tune", "rescore", "qual"):
            ids = ladder_ids(s, what)
            out[f"{name} {what}"] = (int(ids[0]), int(ids[-1]) + 1)
    out["selection"] = (P["select_first"], P["select_first"] + P["select_worlds"] * P["n"])
    for key in ("d", "bg", "e04a"):
        out[key] = (P[f"{key}_first"], P[f"{key}_first"] + P[f"{key}_worlds"])
    out["robustness"] = (R["first"], R["first"] + R["worlds"])
    return out


def ladder_grid(step: str, base: dict | None = None) -> list[dict]:
    """The step's candidates in grid order: its own parameter first, then w_n, w_o, tau, bias, forward,
    turn (the order ties are broken by)."""
    L = REGISTERED["ladder"]
    rest = list(itertools.product(L["w_n"], L["w_o"], L["tau"], L["bias"], L["forward"], L["turn"]))
    keys = ("w_n", "w_o", "tau", "bias", "forward", "turn")
    if step == "L1":
        return [{"step": "L1", **dict(zip(keys, r))} for r in rest]
    if step in ("L2", "L3"):
        own = "w_s" if step == "L2" else "w_m"
        return [{"step": step, own: o, **dict(zip(keys, r))} for o in L[own] for r in rest]
    if step.startswith("L4x"):
        if base is None:
            raise ValueError("L4 needs its base")
        fixed = {k: base[k] for k in ("w_s", "w_m") if k in base}
        return [{"step": step, "base": base["step"], **fixed, **dict(zip(keys, r))} for r in rest]
    raise ValueError(step)


def module_of(c: dict) -> G.Module:
    kw = dict(w_n=c["w_n"], w_o=c["w_o"], tau=c["tau"], bias=c["bias"], w_s=c.get("w_s", 0.0), w_m=c.get("w_m", 0.0))
    if c["step"].startswith("L4x"):
        return C.comparator("L4", pairs=int(c["step"][3:]), **kw)
    return C.comparator(c["step"], **kw)


def ladder_search(evaluate, qualify, base_select) -> dict:
    """The ladder's orchestration, independent of the GPU. `evaluate(step_index, step, candidates)`
    tunes and re-scores and returns the step's chosen candidate; `qualify(step_index, candidate)`
    returns (passed, details); `base_select(finalists)` picks L4's base among L1-L3's. Stops at the
    first qualifying step."""
    attempts, finalists = [], []
    for s, step in enumerate(LADDER_STEPS):
        base = None
        if step.startswith("L4x"):
            if not any(a["step"] == "L4x2" for a in attempts):
                base = base_select(finalists)
            else:
                base = next(a["base"] for a in attempts if a["step"] == "L4x2")
        chosen = evaluate(s, step, ladder_grid(step, base))
        passed, details = qualify(s, chosen)
        attempts.append({"step": step, "index": s, "candidate": chosen, "passed": bool(passed), "details": details,
                         "base": base})
        if step in ("L1", "L2", "L3"):
            finalists.append(chosen)
        if passed:
            return {"qualified": chosen, "attempts": attempts}
    return {"qualified": None, "attempts": attempts}


def take_best(means: np.ndarray, n: int) -> list[int]:
    """The n best by mean, ties to the first in grid order."""
    return [int(i) for i in np.argsort(-np.asarray(means, dtype=np.float64), kind="stable")[:n]]


# ============================================================================== rollouts

def play(cfg, iface, genome: Genome, world_ids, device, cap, chunk_strains: int,
         category: str = "measure") -> np.ndarray:
    """[strains, worlds] counts, in a fixed chunking of `chunk_strains` strains per chunk. The world's
    own food probe stays "real"; the module-only probes are interface variants (`graft_interface`)."""
    ids = np.asarray(world_ids)
    cap.check()
    with acct.category(category):
        r = _rollout(cfg, iface, EV.moved(genome, device), ids, REGISTERED["world_seed"], device,
                                chunk_worlds=chunk_strains * ids.shape[-1])
    return np.asarray(r.score)


def module_probe_counts(cfg, ext, module, genome, ids, device, cap, chunk_strains) -> dict:
    """Real, and the module-only probes (the noses fed the mean, or the other side), on the same worlds."""
    return {p: play(cfg, G.graft_interface(ext, module, probe=p), genome, ids, device, cap, chunk_strains)
            for p in REGISTERED["probes"]}


def uses_class(counts: dict, i: int) -> str:
    real = counts["real"][i]
    return D2.classify(D2.world_ci(real, counts["mean"][i]), D2.world_ci(real, counts["swapped"][i]))


def champions(spec, cfg) -> list[tuple[str, Genome, str]]:
    """The 47 distinct champions (E2's and 04a's), by label, deduplicated by genome hash."""
    found = {k: v[:2] for k, v in D2.e2_champions(spec, cfg).items()}
    found.update({k: v[:2] for k, v in D2.e04a_champions(spec, cfg).items()})
    seen, out = set(), []
    for label in sorted(found):
        g, sha = found[label]
        if sha not in seen:
            seen.add(sha)
            out.append((label, g, sha))
    if not SMOKE and len(out) != REGISTERED["champions"]:
        raise SystemExit(f"{len(out)} distinct champions, not the plan's {REGISTERED['champions']}")
    return out


# ============================================================================== guards

def require(args, prov, stage: str) -> dict:
    return E.require_earlier(args, prov, stage)


def admit(args, prov, stage: str) -> dict:
    """The projection, completed and within its limit, and the hours spent plus this stage's and the
    later stages' projected work within the admission limit."""
    proj = E.require_projection(args, prov)
    left = sum(proj["projected_hours"][s] for s in STAGES[STAGES.index(stage):] if s != "project")
    spent = E.clock().spent_hours()
    if spent + left > REGISTERED["admit_hours"]:
        raise SystemExit(f"{WHAT[stage]} not admitted: {spent:.2f} h spent + {left:.2f} h projected exceeds "
                         f"{REGISTERED['admit_hours']} h")
    sizes = proj["frozen_sizes"]
    for section, key, _ in REGISTERED["shrink"]:
        REGISTERED[section][key] = min(REGISTERED[section][key], sizes[f"{section}.{key}"])
    return proj


# ============================================================================== the projection

def stage_episodes(R: dict) -> dict:
    """{stage: {shape: episodes}} at the sizes in R; the ladder at its worst case (every step). A
    shrunk size is priced at its own measured composition (the "_small" shapes)."""
    S, L, P, Rb = R["sweep"], R["ladder"], R["populations"], R["robustness"]
    F = REGISTERED_FULL
    n_ch, n_k = R["champions"], len(S["ks"])
    cands = {"L1": 216, "L2": 648, "L3": 648, "L4x2": 216, "L4x4": 216}
    probes = len(R["probes"])
    small = lambda shape, sec, key: shape + ("_small" if R[sec][key] < F[sec][key] else "")  # noqa: E731
    return {
        "sweep": {small("sweep", "sweep", "worlds"): n_ch * (n_k + 1) * S["worlds"]},
        "attenuation": {},
        "ladder": {small("tuning", "ladder", "tune_worlds"): sum(cands.values()) * L["tune_worlds"],
                   "rescore": len(cands) * L["top"] * L["rescore_worlds"],
                   "base_rescore": 3 * L["rescore_worlds"],
                   "qualification": len(cands) * probes * L["qual_worlds"]},
        "populations": {"selection": P["n"] * P["size"] * P["select_worlds"],
                        "g0": P["n"] * probes * P["d_worlds"],
                        small("backgrounds", "populations", "bg_worlds"): P["n"] * P["size"] * probes * P["bg_worlds"],
                        "qualification": probes * P["e04a_worlds"]},
        "robustness": {"robustness": len(Rb["scales"]) * Rb["mutants"] * Rb["worlds"], "robustness_parent": Rb["worlds"]},
    }


def analysis_seconds(R: dict, boot: dict) -> dict:
    """Bootstrap calls per stage, priced by the measured seconds per call at each world count."""
    S, L, P = R["sweep"], R["ladder"], R["populations"]
    n_ch, n_k = R["champions"], len(S["ks"]) - 1
    per = lambda n: boot.get(str(n), max(boot.values()) if boot else 0.0)  # noqa: E731
    return {"sweep": n_ch * n_k * per(S["worlds"]),
            "ladder": 5 * 3 * per(L["qual_worlds"]),
            "populations": P["n"] * 2 * per(P["d_worlds"]) + P["n"] * P["size"] * 2 * per(P["bg_worlds"]) + 2 * per(P["e04a_worlds"]),
            "robustness": 0.0, "attenuation": 0.0}


def project_hours(rates: dict, R: dict, extra_seconds: dict | None = None) -> dict:
    """Rollouts at the measured rates, plus the measured non-rollout work (attenuation, dynamics, the
    bootstrap) in `extra_seconds` {stage: seconds}."""
    eps = stage_episodes(R)
    extra = extra_seconds or {}
    return {s: (sum(n / rates[shape] for shape, n in eps[s].items()) + extra.get(s, 0.0)) / 3600.0 for s in eps}


def freeze_sizes(rates: dict, spent_hours: float, extra=None) -> tuple[dict, dict, bool]:
    """Apply the shrink order until the projection fits; return (sizes, projected hours, within).
    `extra(R)` gives the non-rollout seconds per stage at the sizes in R."""
    R = copy.deepcopy(REGISTERED)
    ex = (lambda r: extra(r)) if extra is not None else (lambda r: {})
    hours = project_hours(rates, R, ex(R))
    for section, key, small in [[None, None, None]] + REGISTERED["shrink"]:
        if section is not None:
            R[section][key] = min(R[section][key], small)  # a shrink never grows a size
            hours = project_hours(rates, R, ex(R))
        if spent_hours + sum(hours.values()) <= REGISTERED["admit_hours"]:
            break
    sizes = {f"{s}.{k}": R[s][k] for s, k, _ in REGISTERED["shrink"]}
    return sizes, hours, spent_hours + sum(hours.values()) <= REGISTERED["admit_hours"]


def cmd_project(args):
    def body(ctx):
        cfg, dev, con = ctx.cfg, ctx.args.device, load_connectome()
        spec = BrainSpec.from_connectome(con)
        smoke = E.SMOKE_IDS
        m = C.comparator("L1", w_n=3, w_o=3, tau=0.5, bias=0.0)
        ext = G.graft_connectome(con, m)
        gif = G.graft_interface(ext, m)

        def n2(n, seed):
            return EV.initial_population(spec, cfg.brain, seed, n, "cpu")

        def grafted(n, seed):
            return C.embedded_population(con, ext, m, cfg.brain, run_seed=seed, population=n)

        def carrier(n):
            return Genome.cat([C.carrier_genome(ext, m, cfg.brain, forward=1.0, turn=0.1) for _ in range(n)])

        S, L, P, Rb = REGISTERED["sweep"], REGISTERED["ladder"], REGISTERED["populations"], REGISTERED["robustness"]
        small = {k: dict(v) for k, v in REGISTERED_FULL.items() if isinstance(v, dict)}
        for sec, key, val in REGISTERED["shrink"]:
            small[sec][key] = min(REGISTERED[sec][key], val)
        shapes = {  # one chunk of each formal composition: (genome, interface, ids, chunk strains, instrumented)
            "sweep": (n2(S["chunk_strains"], 1), ctx.iface, smoke[:S["worlds"]], S["chunk_strains"], False),
            "sweep_small": (n2(S["chunk_strains"], 1), ctx.iface, smoke[:small["sweep"]["worlds"]], S["chunk_strains"], False),
            "tuning": (carrier(L["tune_chunk_strains"]), gif, smoke[:L["tune_worlds"]], L["tune_chunk_strains"], False),
            "tuning_small": (carrier(L["tune_chunk_strains"]), gif, smoke[:small["ladder"]["tune_worlds"]],
                             L["tune_chunk_strains"], False),
            "rescore": (carrier(L["top"]), gif, smoke[:L["rescore_worlds"]], L["top"], False),
            "base_rescore": (carrier(1), gif, smoke[:L["rescore_worlds"]], 1, False),
            "qualification": (carrier(1), gif, smoke[:L["qual_worlds"]], 1, False),
            "selection": (grafted(P["n"] * P["size"], 2), gif,
                          np.tile(smoke[:P["select_worlds"]], (P["n"] * P["size"], 1)), P["n"] * P["size"], False),
            "g0": (grafted(P["g0_chunk_strains"], 3), gif, smoke[:P["d_worlds"]], P["g0_chunk_strains"], False),
            "backgrounds": (grafted(P["bg_chunk_strains"], 4), gif, smoke[:P["bg_worlds"]], P["bg_chunk_strains"], True),
            "backgrounds_small": (grafted(P["bg_chunk_strains"], 4), gif, smoke[:small["populations"]["bg_worlds"]],
                                  P["bg_chunk_strains"], True),
            "robustness": (carrier(Rb["chunk_strains"]), gif, smoke[:Rb["worlds"]], Rb["chunk_strains"], False),
            "robustness_parent": (carrier(1), gif, smoke[:Rb["worlds"]], 1, False),
        }
        if SMOKE:
            shapes = {k: (g.select(list(range(min(2, g.n_strains)))), i, ids[..., :4] if ids.ndim == 1 else ids[:2, :4],
                          min(2, c), inst) for k, (g, i, ids, c, inst) in shapes.items()}
        import time
        rates, timing = {}, {}
        play(cfg, ctx.iface, n2(1, 9), smoke[:4], dev, ctx.cap, 1, category="calibration")  # warm-up
        def timed(fn):
            t0 = time.perf_counter()
            fn()
            if dev != "cpu":
                torch.cuda.synchronize()
            return time.perf_counter() - t0

        for shape, (g, iface, ids, chunk, inst) in shapes.items():
            def run(g=g, iface=iface, ids=ids, chunk=chunk, inst=inst):
                if inst:
                    with DG.motor_stats():
                        play(cfg, iface, g, ids, dev, ctx.cap, chunk, category="calibration")
                else:
                    play(cfg, iface, g, ids, dev, ctx.cap, chunk, category="calibration")
            first, secs = timed(run), timed(run)  # the second timing is used (warm), as E2d's projection
            episodes = g.n_strains * ids.shape[-1]
            rates[shape] = episodes / secs
            timing[shape] = {"episodes": int(episodes), "seconds_first": first, "seconds": secs,
                             "composition": [int(chunk), int(ids.shape[-1]), 1]}
        # the non-rollout work, measured: attenuation (12 settles of 40 ticks per level, 47 strains), the
        # open-loop dynamics (3 levels x 2 tests x (60 + 2 x 400) ticks, one strain, read every tick), and
        # the bootstrap per call at each world count
        A, Dy = REGISTERED["attenuation"], REGISTERED["dynamics"]
        b47 = Brain(EV.moved(n2(47 if not SMOKE else 2, 5), dev))

        def settle47():
            v = b47.initial_state(1)
            cur = torch.zeros(b47.n_strains, 1, spec.n, device=dev)
            for _ in range(A["ticks"]):
                v = b47.step(v, cur)
        att = timed(settle47) * 4 * len(A["levels"])
        b1 = Brain(EV.moved(carrier(1), dev))

        def ticks100():
            v = b1.initial_state(1)
            cur = torch.zeros(1, 1, ext.n, device=dev)
            for _ in range(100):
                v = b1.step(v, cur)
                float(C.motor_commands(v.cpu(), gif, cfg)[1])
        dyn = timed(ticks100) / 100 * len(Dy["levels"]) * 2 * (Dy["precondition"] + 2 * Dy["horizon"])
        boot = {}
        for nw in sorted({S["worlds"], small["sweep"]["worlds"], L["qual_worlds"], P["d_worlds"], P["bg_worlds"],
                          small["populations"]["bg_worlds"], P["e04a_worlds"]}):
            x = np.arange(nw, dtype=np.float64) % 3
            boot[str(nw)] = timed(lambda x=x: D2.world_ci(x, x[::-1]))

        def extra(R):
            a = analysis_seconds(R, boot)
            return {"sweep": a["sweep"], "attenuation": att, "ladder": a["ladder"] + dyn,
                    "populations": a["populations"], "robustness": 0.0}
        elapsed = (time.perf_counter() - ctx.cap.t_start) / 3600.0  # this attempt so far (Fable, Astra)
        spent = E.clock().spent_hours() + elapsed
        sizes, hours, within = freeze_sizes(rates, spent, extra)
        return {"rates_episodes_per_second": rates, "timing": timing, "projected_hours": hours,
                "non_rollout_seconds": {"attenuation": att, "dynamics": dyn, "bootstrap_per_call": boot},
                "spent_hours_at_freeze": spent, "projected_total_hours": float(sum(hours.values())),
                "frozen_sizes": sizes, "within_limit": within, "admit_hours": REGISTERED["admit_hours"]}
    return E.run_stage(args, "project", lambda a, prov: {}, body)


# ============================================================================== 1. the sweep

def cmd_sweep(args):
    loaded = {}

    def requires(a, prov):
        proj = admit(a, prov, "sweep")
        cfg = E.task_config()
        loaded["champions"] = champions(BrainSpec.from_connectome(load_connectome()), cfg)
        return proj

    def body(ctx):
        S, dev = REGISTERED["sweep"], ctx.args.device
        ids = np.arange(S["first"], S["first"] + S["worlds"]) if not SMOKE else E.SMOKE_IDS[:S["worlds"]]
        labels = [c[0] for c in loaded["champions"]]
        genome = Genome.cat([c[1] for c in loaded["champions"]])
        ctx.doc["champions"] = {lab: sha for lab, _, sha in loaded["champions"]}
        counts = {}
        ctx.salvage = lambda: {"per_world_counts": {str(k): v.astype(int).tolist() for k, v in counts.items()}}
        reference = play(ctx.cfg, ctx.iface, genome, ids, dev, ctx.cap, S["chunk_strains"])
        for k in S["ks"]:
            with C.residual_turn(k):
                counts[k] = play(ctx.cfg, ctx.iface, genome, ids, dev, ctx.cap, S["chunk_strains"])
            if k == 0 and not np.array_equal(counts[0], reference):
                raise SystemExit("with k = 0 the wrapped world does not reproduce the unwrapped counts")
        ks = S["ks"][1:]
        per = {}
        for i, lab in enumerate(labels):
            cis = [D2.world_ci(counts[k][i], counts[0][i]) for k in ks]
            per[lab] = {"mean_k0": float(counts[0][i].mean()),
                        "difference": {str(k): ci for k, ci in zip(ks, cis)},
                        **DG.sweep_class(ks, [c["lo95"] for c in cis], [c["hi95"] for c in cis])}
        tally = {cls: sum(p["class"] == cls for p in per.values()) for cls in DG.CLASSES}
        return {"k0_reproduces_reference": True, "worlds": {"first": int(ids[0]), "count": int(len(ids))},
                "composition": [S["chunk_strains"], int(len(ids)), 1], "per_champion": per, "class_counts": tally,
                "per_world_counts": {str(k): v.astype(int).tolist() for k, v in counts.items()},
                "reference_counts": reference.astype(int).tolist()}
    return E.run_stage(args, "sweep", requires, body)


# ============================================================================== 2. attenuation

def cmd_attenuation(args):
    loaded = {}

    def requires(a, prov):
        proj = admit(a, prov, "attenuation")
        loaded["champions"] = champions(BrainSpec.from_connectome(load_connectome()), E.task_config())
        return proj

    def body(ctx):
        A, dev = REGISTERED["attenuation"], ctx.args.device
        iface, con = ctx.iface, load_connectome()
        names = list(iface.signal_names)
        left = [int(iface.sensor_neuron[i]) for i, s in enumerate(names) if s == "food_left"]
        right = [int(iface.sensor_neuron[i]) for i, s in enumerate(names) if s == "food_right"]
        read = [con.index(n) for n in A["neurons"]]
        tp, tm = torch.as_tensor(list(iface.turn_plus)), torch.as_tensor(list(iface.turn_minus))
        genome = EV.moved(Genome.cat([c[1] for c in loaded["champions"]]), dev)
        brain, S, n = Brain(genome), genome.n_strains, con.n

        def settled(m, d):
            cur = torch.zeros(S, 1, n, device=dev)
            cur[..., left], cur[..., right] = m + d / 2, m - d / 2
            v, acts, turns = brain.initial_state(1), [], []
            for _ in range(A["ticks"]):
                v = brain.step(v, cur)
                a = torch.tanh(v)[:, 0]
                acts.append(a[:, read])
                turns.append(((a[:, tp.to(dev)].mean(-1) - a[:, tm.to(dev)].mean(-1)) * 0.5
                              * ctx.cfg.world.turn_gain).clamp(-1, 1))  # the world's command, clamped
            k = A["average"]
            return (torch.stack(acts[-k:]).mean(0).cpu().numpy(), torch.stack(turns[-k:]).mean(0).cpu().numpy())

        out = {}
        with acct.category("probe"):
            for m in A["levels"]:
                ap, tp_ = settled(m, A["d"])
                an, tn = settled(m, -A["d"])
                cp, ctp = settled(m + A["dm"], 0.0)
                cn, ctn = settled(m - A["dm"], 0.0)
                kd, kc = (ap - an) / (2 * A["d"]), (cp - cn) / (2 * A["dm"])
                out[str(m)] = {lab: {"K_D": dict(zip(A["neurons"], kd[i].tolist())),
                                     "K_C": dict(zip(A["neurons"], kc[i].tolist())),
                                     "K_D_turn": float((tp_[i] - tn[i]) / (2 * A["d"])),
                                     "K_C_turn": float((ctp[i] - ctn[i]) / (2 * A["dm"]))}
                               for i, (lab, _, _) in enumerate(loaded["champions"])}
        return {"per_level": out, "note": "descriptive; open loop, zero start, other inputs zero"}
    return E.run_stage(args, "attenuation", requires, body)


# ============================================================================== 3. the ladder

def candidate_genome(ext, cands: list[dict], bcfg) -> Genome:
    return Genome.cat([C.carrier_genome(ext, module_of(c), bcfg, forward=c["forward"], turn=c["turn"]) for c in cands])


def open_loop_dynamics(c: dict, cfg, con, device) -> dict:
    """The qualifying comparator on its carrier at turn command 0: step and carried-state reversal,
    each against an unchanged control, with the settling rule."""
    Dy = REGISTERED["dynamics"]
    m = module_of(c)
    ext = G.graft_connectome(con, m)
    iface = G.graft_interface(ext, m)
    g = EV.moved(C.carrier_genome(ext, m, cfg.brain, forward=c["forward"], turn=0.0), device)
    brain = Brain(g)
    names = list(iface.signal_names)
    left = [int(iface.sensor_neuron[i]) for i, s in enumerate(names) if s == "food_left"]
    right = [int(iface.sensor_neuron[i]) for i, s in enumerate(names) if s == "food_right"]

    def current(mm, d):
        cur = torch.zeros(1, 1, ext.n, device=device)
        cur[..., left], cur[..., right] = mm + d / 2, mm - d / 2
        return cur

    def trace(v, cur, ticks):
        out = []
        for _ in range(ticks):
            v = brain.step(v, cur)
            out.append(float(C.motor_commands(v.cpu(), iface, cfg)[1]))
        return v, np.array(out)

    res = {}
    for mm in Dy["levels"]:
        for name, (d0, d1, sign) in {"step": (0.0, Dy["step"], 1), "reversal": (Dy["step"], -Dy["step"], -1)}.items():
            v0, _ = trace(brain.initial_state(1), current(mm, d0), Dy["precondition"])
            _, changed = trace(v0.clone(), current(mm, d1), Dy["horizon"])
            _, control = trace(v0.clone(), current(mm, d0), Dy["horizon"])
            res[f"{name} m={mm}"] = DG.settle(changed - control, expected_sign=sign, endpoint=float(changed[-20:].mean()))
    return res


def cmd_ladder(args):
    def body(ctx):
        cfg, dev, con, L = ctx.cfg, ctx.args.device, load_connectome(), REGISTERED["ladder"]
        log = {"steps": []}
        ctx.salvage = lambda: {"ladder_log": log}

        def ids(s, what):
            return ladder_ids(s, what) if not SMOKE else E.SMOKE_IDS[1000 * (s + 1) + {"tune": 0, "rescore": 300, "qual": 600}[what]:][:L[{"tune": "tune_worlds", "rescore": "rescore_worlds", "qual": "qual_worlds"}[what]]]

        def evaluate(s, step, cands):
            if SMOKE:
                cands = cands[:4]
            ext = G.graft_connectome(con, module_of(cands[0]))
            gif = G.graft_interface(ext, module_of(cands[0]))
            tune = play(cfg, gif, candidate_genome(ext, cands, cfg.brain), ids(s, "tune"), dev, ctx.cap,
                        L["tune_chunk_strains"], category="tuning")
            top = take_best(tune.mean(axis=1), L["top"])
            res = play(cfg, gif, candidate_genome(ext, [cands[i] for i in top], cfg.brain), ids(s, "rescore"), dev,
                       ctx.cap, L["top"], category="tuning")
            best = rescore_choice(top, res.mean(axis=1))
            log["steps"].append({"step": step, "candidates": len(cands), "tune_means": tune.mean(axis=1).tolist(),
                                 "top": top, "rescore_means": res.mean(axis=1).tolist(), "chosen": cands[best],
                                 "tune_worlds": [int(ids(s, "tune")[0]), len(ids(s, "tune"))],
                                 "rescore_worlds": [int(ids(s, "rescore")[0]), len(ids(s, "rescore"))],
                                 "composition": {"tuning": [L["tune_chunk_strains"], len(ids(s, "tune")), 1],
                                                 "tuning_last_chunk_strains": len(cands) % L["tune_chunk_strains"]
                                                 or L["tune_chunk_strains"],
                                                 "rescore": [L["top"], len(ids(s, "rescore")), 1],
                                                 "qualification": [1, len(ids(s, "qual")), 1]},
                                 "tune_per_world_counts": tune.astype(int).tolist(),
                                 "rescore_per_world_counts": res.astype(int).tolist()})
            E.write_atomic(E.partial_path("ladder"), {**ctx.doc, "ladder_log": log})
            return cands[best]

        def qualify(s, c):
            m = module_of(c)
            ext = G.graft_connectome(con, m)
            g = C.carrier_genome(ext, m, cfg.brain, forward=c["forward"], turn=c["turn"])
            counts = module_probe_counts(cfg, ext, m, g, ids(s, "qual"), dev, ctx.cap, 1)
            lower = D2.world_ci(counts["real"][0], np.zeros_like(counts["real"][0]))
            cls = uses_class(counts, 0)
            passed = lower["lo95"] >= L["lower_bound"] and (cls == "uses" or SMOKE)  # smoke: exercise the qualified path
            return passed, {"mean": lower, "uses": cls, "per_world_counts": {p: v[0].astype(int).tolist()
                                                                             for p, v in counts.items()}}

        def base_select(finalists):
            s = LADDER_STEPS.index("L4x2")
            means, per_world = [], []
            for c in finalists:
                m = module_of(c)
                ext = G.graft_connectome(con, m)
                g = C.carrier_genome(ext, m, cfg.brain, forward=c["forward"], turn=c["turn"])
                counts = play(cfg, G.graft_interface(ext, m), g, ids(s, "rescore"), dev, ctx.cap, 1, category="tuning")
                means.append(float(counts.mean()))
                per_world.append(counts[0].astype(int).tolist())
            log["base_selection"] = {"finalists": finalists, "means": means, "per_world_counts": per_world,
                                     "composition": [1, len(ids(s, "rescore")), 1]}
            return finalists[take_best(means, 1)[0]]

        result = ladder_search(evaluate, qualify, base_select)
        out = {"attempts": result["attempts"], "ladder_log": log, "qualified": result["qualified"]}
        if result["qualified"] is None:
            out["reading"] = "none of the tested candidates passed within the search budget"
            return out
        c = result["qualified"]
        with acct.category("probe"):
            out["dynamics"] = open_loop_dynamics(c, cfg, con, dev)
        out["on_bounds"] = on_bounds(c, cfg.brain)
        m = module_of(c)
        module_doc = {"candidate": c, "neurons": list(m.neurons), "synapses": [list(s) for s in m.synapses],
                      "tau": m.tau, "bias": m.bias, "noses": m.noses, "nose_gain": m.nose_gain,
                      "carrier": {"forward": c["forward"], "turn": c["turn"]}}
        text = json.dumps(module_doc, indent=1) + "\n"
        path = E.EXP / "module.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        ctx.after_fail = lambda: path.unlink(missing_ok=True)  # never beside a not-completed record (Fable)
        out["module_file"] = {"path": path.name, "sha256": hashlib.sha256(text.encode()).hexdigest()}
        return out
    return E.run_stage(args, "ladder", lambda a, prov: admit(a, prov, "ladder"), body)


# ============================================================================== 3. populations

def qualified_module(args, prov) -> dict | None:
    rec = require(args, prov, "ladder")
    return rec.get("qualified")


def cmd_populations(args):
    loaded = {}

    def requires(a, prov):
        proj = admit(a, prov, "populations")
        loaded["candidate"] = qualified_module(a, prov)
        cfg = E.task_config()
        spec = BrainSpec.from_connectome(load_connectome())
        e04a = D2.e04a_champions(spec, cfg)
        lab = REGISTERED["populations"]["e04a_label"]
        if lab not in e04a and not SMOKE:
            raise SystemExit(f"{lab} is missing: item 3.4 would be dropped silently")
        loaded["e04a"] = e04a[lab][:2] if lab in e04a else None
        return proj

    def body(ctx):
        c = loaded["candidate"]
        if c is None:
            return {"skipped": "no step qualified", "reading": "not drawn"}
        cfg, dev, con, P = ctx.cfg, ctx.args.device, load_connectome(), REGISTERED["populations"]
        m = module_of(c)
        ext = G.graft_connectome(con, m)
        n, size = (P["n"], P["size"]) if not SMOKE else (2, 4)
        pops = [C.embedded_population(con, ext, m, cfg.brain, run_seed=P["seed_base"] + i, population=size)
                for i in range(n)]
        genome = Genome.cat(pops)
        held = {}

        def select_play(ids2d):
            held["ids"], held["score"] = ids2d, play(cfg, G.graft_interface(ext, m), genome, ids2d, dev, ctx.cap,
                                                     n * size, category="selection")
            return held["score"]
        best = pick_g0(select_play, n, size)
        bests = Genome.cat([pops[i].select([int(b)]) for i, b in enumerate(best)])
        d_ids = np.arange(P["d_first"], P["d_first"] + P["d_worlds"]) if not SMOKE else E.SMOKE_IDS[2000:2016]
        g0 = module_probe_counts(cfg, ext, m, bests, d_ids, dev, ctx.cap, P["g0_chunk_strains"])
        g0_classes = [uses_class(g0, i) for i in range(n)]
        tally = {k: g0_classes.count(k) for k in ("uses", "unclear", "no material benefit")}
        bg_ids = np.arange(P["bg_first"], P["bg_first"] + P["bg_worlds"]) if not SMOKE else E.SMOKE_IDS[3000:3008]
        with DG.motor_stats() as stats:
            bg = {"real": play(cfg, G.graft_interface(ext, m), genome, bg_ids, dev, ctx.cap, P["bg_chunk_strains"])}
        motors = stats.per_strain(genome.n_strains, len(bg_ids))
        for p in ("mean", "swapped"):
            bg[p] = play(cfg, G.graft_interface(ext, m, probe=p), genome, bg_ids, dev, ctx.cap, P["bg_chunk_strains"])
        bg_classes = [uses_class(bg, i) for i in range(genome.n_strains)]
        out = {"selection": {"world_ids": held["ids"].astype(int).tolist(), "per_world_counts": held["score"].astype(int).tolist(),
                             "composition": [n * size, int(held["ids"].shape[1]), 1]},
               "composition": {"g0": [P["g0_chunk_strains"], len(d_ids), 1], "backgrounds": [P["bg_chunk_strains"], len(bg_ids), 1],
                               "e04a_run02": [1, P["e04a_worlds"] if not SMOKE else 16, 1]},
               "g0_best_index": best.tolist(), "g0_best_sha256": [genome_hash(bests, i) for i in range(n)],
               "g0_classes": g0_classes, "g0_counts": tally,
               "reading": ("E4s-1 proceeds on random N2" if tally["uses"] >= P["needed"] else
                           "E4s-1's design must change its background, its reading, or both"),
               "g0_per_world_counts": {p: v.astype(int).tolist() for p, v in g0.items()},
               "backgrounds": {"classes": {k: bg_classes.count(k) for k in ("uses", "unclear", "no material benefit")},
                               "label": "descriptive; on 64 worlds D is mostly 'unclear'",
                               "mean_score": bg["real"].mean(axis=1).tolist(),
                               "forward": motors["forward"].mean(axis=1).tolist(),
                               "turn": motors["turn"].mean(axis=1).tolist(),
                               "saturated_share": motors["saturated_share"].mean(axis=1).tolist(),
                               "per_world_counts": {p: v.astype(int).tolist() for p, v in bg.items()}}}
        if loaded["e04a"] is not None:
            base, sha = loaded["e04a"]
            g = G.seeded_genome(ext, m, cfg.brain, base=base)
            e_ids = np.arange(P["e04a_first"], P["e04a_first"] + P["e04a_worlds"]) if not SMOKE else E.SMOKE_IDS[4000:4016]
            with DG.motor_stats() as stats:
                real = play(cfg, G.graft_interface(ext, m), g, e_ids, dev, ctx.cap, 1)
            mot = stats.per_strain(1, len(e_ids))
            ec = {"real": real, **{p: play(cfg, G.graft_interface(ext, m, probe=p), g, e_ids, dev, ctx.cap, 1)
                                   for p in ("mean", "swapped")}}
            out["e04a_run02"] = {"sha256": sha, "mean": float(real.mean()), "uses": uses_class(ec, 0),
                                 "forward": float(mot["forward"].mean()), "turn": float(mot["turn"].mean()),
                                 "saturated_share": float(mot["saturated_share"].mean()),
                                 "per_world_counts": {p: v[0].astype(int).tolist() for p, v in ec.items()}}
        return out
    return E.run_stage(args, "populations", requires, body)


# ============================================================================== 4. robustness

def mutants(parent: Genome, ext, mcfg, scale: float, n: int, seed_base: int) -> Genome:
    """Mutant j from a generator seeded seed_base + j, at every scale (paired draws)."""
    s = DG.module_scales(ext, scale)
    return Genome.cat([parent.clone().mutate(mcfg, torch.Generator().manual_seed(seed_base + j), scales=s)
                       for j in range(n)])


def cmd_robustness(args):
    loaded = {}

    def requires(a, prov):
        proj = admit(a, prov, "robustness")
        rec = require(a, prov, "ladder")
        loaded["candidate"], loaded["labelled"] = rec.get("qualified"), "qualified"
        if loaded["candidate"] is None:  # the closest to qualifying, labelled
            tries = [t for t in rec["attempts"]]
            best = max(tries, key=lambda t: t["details"]["mean"]["mean"])
            loaded["candidate"], loaded["labelled"] = best["candidate"], "not qualified (closest attempt)"
        return proj

    def body(ctx):
        cfg, dev, con, Rb = ctx.cfg, ctx.args.device, load_connectome(), REGISTERED["robustness"]
        c = loaded["candidate"]
        m = module_of(c)
        ext = G.graft_connectome(con, m)
        gif = G.graft_interface(ext, m)
        parent = C.carrier_genome(ext, m, cfg.brain, forward=c["forward"], turn=c["turn"])
        ids = np.arange(Rb["first"], Rb["first"] + Rb["worlds"]) if not SMOKE else E.SMOKE_IDS[5000:5008]
        n = Rb["mutants"] if not SMOKE else 4
        p_counts = play(cfg, gif, parent, ids, dev, ctx.cap, 1)
        pm = float(p_counts.mean())
        out = {"candidate": c, "label": loaded["labelled"], "parent_mean": pm, "per_scale": {},
               "composition": {"parent": [1, len(ids), 1], "children": [Rb["chunk_strains"], len(ids), 1],
                               "note": "the parent runs as one padded strain and the children in chunks of "
                                       f"{Rb['chunk_strains']}: the share compares across compositions (descriptive)"}}
        for scale in Rb["scales"]:
            kids = mutants(parent, ext, cfg.mutation, scale, n, Rb["seed_base"])
            k_counts = play(cfg, gif, kids, ids, dev, ctx.cap, Rb["chunk_strains"])
            shares = robustness_shares(k_counts, pm)
            out["per_scale"][str(scale)] = {"median_share": None if shares is None else float(np.median(shares)),
                                            "child_means": k_counts.mean(axis=1).tolist(),
                                            "per_world_counts": k_counts.astype(int).tolist()}
        out.update(robustness_reading(pm, out["per_scale"]["0.125"]["median_share"],
                                      out["per_scale"]["0.25"]["median_share"]))
        out["parent_per_world_counts"] = p_counts[0].astype(int).tolist()
        return out
    return E.run_stage(args, "robustness", requires, body)


# ============================================================================== smoke and main

def use_smoke(args) -> None:
    global EXP, OUT, SMOKE, GUARDED
    EXP = OUT = ROOT / "runs" / "e4s0-smoke"
    SMOKE, GUARDED = True, ["wormwars", "scripts", "configs", "requirements.txt", PLAN, *E.E1_INPUTS]
    R = REGISTERED
    R["sweep"].update(ks=[0, 1, 256], worlds=4, chunk_strains=2)
    R["ladder"].update(tune_worlds=4, rescore_worlds=4, qual_worlds=8, top=2, tune_chunk_strains=4,
                       lower_bound=-1.0)  # smoke only: the first step "qualifies", so every later path runs
    R["dynamics"].update(precondition=5, horizon=45)
    R["robustness"].update(worlds=4, chunk_strains=4)
    R["populations"].update(d_worlds=16, bg_worlds=8, bg_chunk_strains=4, select_worlds=2)
    configure()
    for stage in STAGES[STAGES.index(args.command):]:
        for f in (E.record_path(stage), E.marker_path(stage), E.partial_path(stage)):
            if EXP in f.parents:
                f.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=STAGES)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--guarded", action="store_true")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--reason")
    args = ap.parse_args()
    if args.smoke:
        use_smoke(args)
    {"project": cmd_project, "sweep": cmd_sweep, "attenuation": cmd_attenuation, "ladder": cmd_ladder,
     "populations": cmd_populations, "robustness": cmd_robustness}[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    out = ROOT / "runs" / ("e4s0-smoke" if smoke else "e4s0")
    try:
        run_script(main, out_default=str(out), default="measure", name="e4s0")
    finally:
        agg = out / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
