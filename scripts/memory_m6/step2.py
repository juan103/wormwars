"""M6, step 2 (docs/memory/M6-STEP2-PLAN.md): does the champions' T1 foraging depend on their neural time scale? Every
neuron's time constant is multiplied by k, with the substeps divided by k so that the discrete update is an exact
time rescaling (fixed points unchanged). Arms: T1 champions (g39) at k = 0.25, 0.5, 1, 2, 4 and an interior-only
k = 0.25 (sensory and motor neurons unscaled); the same runs' g00 and drift0 (M6-0's first drift replicate) at
k = 0.25, 1, 4; T0's champions at the five k. Scores on 02b's 32 criticality worlds; a probe validation on each T1
run's own bank. Writes runs/memory-m6-step2/; readings by step2_read.py. CPU only: the GPU is hidden when run.

Usage: python scripts/memory_m6/step2.py [stage ...]   (stages: genomes scores probe; all, in that order)
"""

from __future__ import annotations

import os

if __name__ == "__main__":  # CPU only; not on import (tests)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

import dataclasses  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m6"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m1"))
import common as c  # noqa: E402
import m6_0 as M  # noqa: E402
import pilot as P  # noqa: E402
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import Genome  # noqa: E402
from wormwars.evo.rollout import rollout  # noqa: E402

torch.set_grad_enabled(False)
OUT = Path(os.environ.get("MEMORY_M6_STEP2_OUT", ROOT / "runs" / "memory-m6-step2"))
M6_0 = ROOT / "runs" / "memory-m6-0"
BASE_SUBSTEPS = 32
KS = (0.25, 0.5, 1, 2, 4)
CTRL_KS = (0.25, 1, 4)
INTERIOR = "interior 0.25"
ALONE = "1 alone"  # k = 1 in a one-strain batch: the baseline for the one-strain arms (Astra)
CTRL = ("g00", "drift0")
HORIZON = 100  # the probe validation's continuation, in ticks
PROBE_ALLOWANCE = 1800  # seconds the forecast leaves for the probe stage under the cap
STOP_HOURS = 5.0
CAP = reg.CapClock(STOP_HOURS, OUT / "compute.json")
EXPECT = {"T1": 102, "T0": 72}


class Stop(SystemExit):
    pass


def dump(obj, name):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1), encoding="utf-8")


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------------- intervention
def boundary(iface):
    """The neurons the interior arm leaves unscaled: every sensory neuron and every motor read-out neuron."""
    idx = set(int(j) for j in iface.sensor_neuron)
    for name in ("forward_plus", "forward_minus", "turn_plus", "turn_minus", "pump_neurons"):
        idx |= set(int(j) for j in getattr(iface, name))
    return sorted(idx)


def scaled(g: Genome, k: float, keep=None) -> Genome:
    """tau x k (all neurons, or all but `keep`) and substeps / k: an exact time rescaling of the discrete update for
    the scaled neurons. The genome is never clamped afterwards, so tau may leave evolution's bounds."""
    sub = BASE_SUBSTEPS / k
    if g.cfg.substeps != BASE_SUBSTEPS or abs(sub - round(sub)) > 1e-9:
        raise Stop(f"substeps {g.cfg.substeps} and k {k} do not give an exact rescaling")
    out = g.clone()
    if keep is None:
        out.tau.mul_(k)
    else:
        mask = torch.ones(out.tau.shape[1], dtype=torch.bool)
        mask[keep] = False
        out.tau[:, mask] *= k
    out.cfg = dataclasses.replace(out.cfg, substeps=int(round(sub)))
    return out


def arm_genome(g, arm, iface):
    if arm == INTERIOR:
        return scaled(g, 0.25, keep=boundary(iface))
    return scaled(g, 1 if arm == ALONE else arm)


# ------------------------------------------------------------------------------------------------------------- genomes
def t0_records():
    return sorted((r for r in M.analyse().RECORDS if r["task"] == "T0"), key=lambda r: r["key"])


def run_genomes(r, cfg, spec):
    """{label: genome}: T1 runs carry g39, g00 and drift0 (M6-0's first replicate); T0 runs carry g39."""
    if r["task"] == "T0":
        return {"g39": M.load_one(r, "g39", spec, cfg)}
    g00 = M.load_one(r, "g00", spec, cfg)
    return {"g39": M.load_one(r, "g39", spec, cfg), "g00": g00,
            "drift0": M.drifted(g00, cfg, M.drift_seed(r["key"], 0))}


def tau_profile(g, cfg):
    t = g.tau[0]
    return {"median": float(t.median()), "at_min": float((t <= cfg.brain.tau_min * 1.0001).float().mean()),
            "at_max": float((t >= cfg.brain.tau_max * 0.9999).float().mean())}


def records():
    return M.t1_records() + t0_records()


def stage_genomes():
    """The genome list with parameter hashes and tau profiles; drift0 must equal M6-0's recorded hash."""
    m60 = {(x["key"], x["label"]): x["param_sha256"]
           for x in json.loads((M6_0 / "genomes.json").read_text(encoding="utf-8"))["genomes"]}
    rows = []
    for r in records():
        cfg, iface, spec = M.setup(r)
        for label, g in run_genomes(r, cfg, spec).items():
            h = M.param_hash(g)
            if r["task"] == "T1" and m60.get((r["key"], label)) != h:
                raise Stop(f"{r['key']} {label}: differs from M6-0's genome")
            rows.append({"key": r["key"], "task": r["task"], "block": M.block_of(r), "mapping": r["mapping"],
                         "graph": r["graph"], "family": M.analyse().family(r["graph"]), "label": label,
                         "param_sha256": h, "tau": tau_profile(g, cfg)})
    counts = {t: sum(x["task"] == t and x["label"] == "g39" for x in rows) for t in EXPECT}
    if counts != EXPECT:
        raise Stop(f"champion counts {counts}, the plan's {EXPECT}")
    dump({"genomes": rows, "counts": counts}, "genomes.json")


def check_genomes():
    saved = [(x["key"], x["label"], x["param_sha256"]) for x in load("genomes.json")["genomes"]]
    want = []
    for r in records():
        cfg, _, spec = M.setup(r)
        want += [(r["key"], label, M.param_hash(g)) for label, g in run_genomes(r, cfg, spec).items()]
    if saved != want:
        raise Stop("genomes.json does not regenerate")


# -------------------------------------------------------------------------------------------------------------- scores
def batches(r):
    """[(arm, labels)] per run, in a fixed order; one batch per arm (the plan's batch composition)."""
    if r["task"] == "T0":
        return [(k, ["g39"]) for k in KS]
    out = []
    for k in KS:
        out.append((k, ["g39", *CTRL] if k in CTRL_KS else ["g39"]))
    return out + [(INTERIOR, ["g39"]), (ALONE, ["g39"])]


def score_run(r, worlds=None):
    worlds = M.analyse().CRIT_WORLDS if worlds is None else worlds
    cfg, iface, spec = M.setup(r)
    gs = run_genomes(r, cfg, spec)
    res = {}
    for arm, labels in batches(r):
        CAP.check()
        g = Genome.cat([arm_genome(gs[lb], arm, iface) for lb in labels])
        sc = rollout(cfg, iface, g, worlds, r["run_seed"], "cpu").score
        for i, lb in enumerate(labels):
            res.setdefault(lb, {})[str(arm)] = {"mean": float(sc[i].mean()), "worlds": sc[i].tolist()}
    return res


def load_of(r):
    """A run's compute load: strains times substeps, summed over its batches."""
    return sum(len(labels) * BASE_SUBSTEPS / (0.25 if arm == INTERIOR else 1 if arm == ALONE else arm)
               for arm, labels in batches(r))


def forecast(done_runs, elapsed, recs):
    """Seconds for the whole scores stage, from the load done so far, not run counts (Fable, Astra)."""
    return elapsed / sum(load_of(r) for r in done_runs) * sum(load_of(r) for r in recs)


def stage_scores():
    if (OUT / "scores.json").exists():
        return
    part = OUT / "scores.partial.json"
    saved = json.loads(part.read_text(encoding="utf-8")) if part.exists() else {"scores": {}, "seconds": 0.0}
    out, t0, before = saved["scores"], time.time(), saved["seconds"]
    recs = records()
    for n, r in enumerate(recs, 1):
        if r["key"] in out:
            continue
        out[r["key"]] = score_run(r)
        el = before + time.time() - t0
        dump({"scores": out, "seconds": round(el, 1)}, part.name)  # resumable after a stop (Fable, Astra)
        if len(out) == 3:
            f = forecast([x for x in recs if x["key"] in out], el, recs)
            if f > STOP_HOURS * 3600 - PROBE_ALLOWANCE:
                raise Stop(f"forecast {f / 3600:.1f} h for the scores passes the cap: stopped for the owner")
        print(f"{r['key']}: " + ", ".join(f"{a}={v['mean']:.3f}" for a, v in out[r['key']]['g39'].items())
              + f"  ({el:.0f} s)", flush=True)
    dump({"scores": out, "seconds": round(before + time.time() - t0, 1)}, "scores.json")
    part.unlink()


# --------------------------------------------------------------------------------------------------------------- probe
def own_bank(key):
    return json.loads((M6_0 / "banks.json").read_text(encoding="utf-8"))["own"][key]


def probe_one(g, cfg, iface, bank, arms):
    """Per arm: the continuation (ramp-end states written at k = 1, continued HORIZON ticks under the arm) and the
    writing (the whole probe under the arm): the read-out difference integrated over ticks 1..HORIZON, and a."""
    with c.probe_input(iface, bank):
        base = P.probe_states(g, cfg, ticks=0, record=False)
        start = base["end"].float()
        out = {}
        for arm in arms:
            CAP.check()
            ga = arm_genome(g, arm, iface)
            cont = P.follow_from(ga, cfg, start, ticks=HORIZON, record=False)["y"]
            full = P.probe_states(ga, cfg, ticks=HORIZON, record=False)["y"]
            dc = np.abs(cont[0, :, 0] - cont[0, :, 1])
            df = np.abs(full[0, :, 0] - full[0, :, 1])
            out[str(arm)] = {"a_written_at_1": float(dc[0]), "continued_integral": float(dc[1:].sum()),
                             "a_full": float(df[0]), "full_integral": float(df[1:].sum())}
    return out


def stage_probe():
    if (OUT / "probe.json").exists():
        return
    out, t0 = {}, time.time()
    for r in M.t1_records():
        CAP.check()
        cfg, iface, spec = M.setup(r)
        gs = run_genomes(r, cfg, spec)
        bank = own_bank(r["key"])
        arms = [a for a, labels in batches(r) if "g39" in labels and a != ALONE]
        out[r["key"]] = {"g39": probe_one(gs["g39"], cfg, iface, bank, arms)}  # champions only (both: cut)
    dump({"probe": out, "horizon": HORIZON, "seconds": round(time.time() - t0, 1)}, "probe.json")
    print(f"probe: {len(out)} runs, {time.time() - t0:.0f} s", flush=True)


STAGES = {"genomes": stage_genomes, "scores": stage_scores, "probe": stage_probe}


def main(stages):
    if (OUT / "genomes.json").exists():
        check_genomes()
    elif "genomes" in stages:
        stage_genomes()
    else:
        raise Stop("genomes.json missing: run the genomes stage first")
    for s in stages:
        if s != "genomes":
            STAGES[s]()
    CAP.check()
    if torch.cuda.is_initialized():
        raise Stop("CUDA was initialised")


if __name__ == "__main__":
    todo = sys.argv[1:] or list(STAGES)
    OUT.mkdir(parents=True, exist_ok=True)
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="measure", experiment="memory-M6-step2",
                       script="step2.py"):
        try:
            main(todo)
        except reg.CapReached:
            raise Stop(f"the run's {STOP_HOURS}-hour cap was reached: what finished is incomplete, not read")
