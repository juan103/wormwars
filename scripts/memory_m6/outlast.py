"""M6, step 1 (docs/memory/M6-OUTLAST-PLAN.md): do the switches' states outlast the input? Every N2 switch genome
classified so far (M2's census, seeds 7600 and 7700; M4c's, seeds 7801 to 7808) is rebuilt and run in three phases:
A, the standard probe (classified; must reproduce the census class); B, from A's end states under a changed input
(F0: food channels 0; Z: every channel 0), classified under it; C, from B's end states under 03mc's bank again,
classified, with each history's root compared with A's. Writes runs/memory-m6-outlast/; readings by outlast_read.py.
CPU only: the GPU is hidden when run.

Usage: python scripts/memory_m6/outlast.py [stage ...]   (stages: genomes run; both, in that order)
"""

from __future__ import annotations

import os

if __name__ == "__main__":  # CPU only; not on import (tests)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m1"))
import census  # noqa: E402
import classify as K  # noqa: E402
import common as c  # noqa: E402
import pilot as P  # noqa: E402
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402

torch.set_grad_enabled(False)
OUT = Path(os.environ.get("MEMORY_M6_OUTLAST_OUT", ROOT / "runs" / "memory-m6-outlast"))
PANELS = [("M2", s, ROOT / "runs" / "memory-m2-census" / f"N2__{s}.json") for s in (7600, 7700)] + \
         [("M4c", s, ROOT / "runs" / "memory-m4c" / "census" / f"N2__{s}.json") for s in range(7801, 7809)]
N_PANEL = 1024  # both censuses' panel size
EXPECT = 169
SWITCH = ("separate states", "separate states, read-out silent")
TOL = K.DISTINCT  # the classifier's distinctness level (1e-6), for matching roots between phases (Fable)
SEP_TICKS = (0, 10, 30, 100, 300)  # B's recorded separations, with the end (Fable)
STOP_FRACTION = 0.05  # consistency: more than this fraction failing to reproduce the census class stops the run
STOP_HOURS = 1.0  # a checkpointed cap: checked before every phase and before the record is written
CAP = reg.CapClock(STOP_HOURS, OUT / "compute.json")
ARMS = ("F0", "Z")
SEEN_SEED, SEEN_N = 7700, 4  # the plan's smoke run: the first 4 switch genomes of seed 7700's panel


class Stop(SystemExit):
    pass


def dump(obj, name):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1), encoding="utf-8")


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def bank_for(arm):
    """The changed input: F0, both food channels 0 and every other channel of 03mc's bank kept; Z, every channel 0."""
    if arm == "F0":
        return dict(c.S.BANK, food_left=0.0, food_right=0.0)
    if arm == "Z":
        return {k: 0.0 for k in c.S.BANK}
    raise ValueError(arm)


# ------------------------------------------------------------------------------------------------------------- genomes
def switch_ids(path, seed):
    """A census panel's switch genomes (both subclasses), checked: N2, this seed, a valid panel."""
    rec = json.loads(Path(path).read_text(encoding="utf-8"))
    if (rec.get("graph"), rec.get("seed"), rec.get("valid")) != ("N2", seed, True):
        raise Stop(f"{path}: not a valid N2 panel at seed {seed}")
    return [{"genome": g["genome"], "census_class": g["class"]} for g in rec["genomes"] if g["class"] in SWITCH]


def genome_list():
    rows = []
    for source, seed, path in PANELS:
        if not path.exists():
            raise Stop(f"missing census record {path}")
        rows += [{"source": source, "seed": seed, **x} for x in switch_ids(path, seed)]
    if len(rows) != EXPECT:
        raise Stop(f"{len(rows)} switch genomes, expected {EXPECT}")
    seen = [r["genome"] for r in rows if r["seed"] == SEEN_SEED][:SEEN_N]
    return [{**r, "seen_before_plan": r["seed"] == SEEN_SEED and r["genome"] in seen} for r in rows]


def build(seed, ids):
    """The census's own route: the whole panel first, then the recorded ids."""
    g, cfg = c.S.genomes(census.graph_of("N2"), N_PANEL, seed)
    return g.select(ids), cfg


def stage_genomes():
    rows = genome_list()
    dump({"genomes": rows, "n": len(rows), "panels": [[s, str(p.relative_to(ROOT))] for _, s, p in PANELS]},
         "genomes.json")
    print(f"genomes: {len(rows)}", flush=True)


def check_genomes():
    if load("genomes.json")["genomes"] != genome_list():
        raise Stop("genomes.json differs from the census records")


# ----------------------------------------------------------------------------------------------------------- phases
def sub(run):
    return {"end": run["end"], "cur": run["cur"], "y": run["y"], "tail": run["tail"]}


def phase_a(g, cfg):
    run = P.probe_states(g, cfg)
    recs, roots = P.full_classify(g, cfg, sub(run), compact=True)
    return run, recs, roots


def phase_from(g, cfg, start, bank=None):
    """B (bank given: the changed input) or C (bank None: 03mc's bank): 2000 ticks from start [S, 2, N], classified
    under that input, the oscillation check rerunning from the same start. The input changes in one step."""
    def go():
        run = P.follow_from(g, cfg, start.float())
        recs, roots = P.full_classify(g, cfg, sub(run), compact=True, initial=start.float())
        return run, recs, roots
    if bank is None:
        return go()
    with c.probe_input(c.S.IFACE, bank):
        return go()


def arm_phases(g, cfg, a_end, arm):
    """B from A's end states under the arm's input, then C from B's end states under 03mc's bank."""
    b = phase_from(g, cfg, a_end, bank_for(arm))
    CAP.check()
    return b, phase_from(g, cfg, b[0]["end"])


def separation(run):
    """The max-norm state difference between the two histories at SEP_TICKS and at the run's end: [S, 6]."""
    dense = torch.as_tensor(run["dense"])  # [S, 301, 2, N], ticks 0..300
    cols = [(dense[:, t, 0] - dense[:, t, 1]).abs().amax(-1) for t in SEP_TICKS]
    cols.append((run["end"][:, 0] - run["end"][:, 1]).abs().amax(-1).float())
    return torch.stack(cols, 1)


def match(roots_a, roots_c, tol=TOL):
    """C's roots against A's, per genome [S, 2, N]: 'same' (each history at its own A root), 'swapped', 'both at 0' or
    'both at 1' (both histories at the rising-start or the falling-start history's A root), 'new', or 'ambiguous'
    when A's two roots are closer than twice the tolerance."""
    d = (roots_c[:, :, None] - roots_a[:, None]).abs().amax(-1) < tol  # [S, C history, A root]
    close = ((roots_a[:, 0] - roots_a[:, 1]).abs().amax(-1) < 2 * tol).tolist()
    out = []
    for x, amb in zip(d.tolist(), close):
        out.append("ambiguous" if amb else "same" if x[0][0] and x[1][1] else "swapped" if x[0][1] and x[1][0] else
                   "both at 0" if x[0][0] and x[1][0] else "both at 1" if x[0][1] and x[1][1] else "new")
    return out


def outcome(cls_c, m):
    """After restoration, from C alone (Fable): recovered, merged, other or unresolved."""
    if cls_c == "unresolved":
        return "unresolved"
    if cls_c in SWITCH and m == "same":
        return "recovered"
    if cls_c == "fading":
        return "merged"
    return "other"


def held(cls_b):
    """During the removal, from B alone: held (two states), not held, or unresolved."""
    return "unresolved" if cls_b == "unresolved" else "held" if cls_b in SWITCH else "not held"


def census_roots(seed, ids):
    """The census's stored roots for these genomes [S, 2, N], or None where the local arrays are absent."""
    for _, s, path in PANELS:
        if s == seed and path.with_suffix(".npz").exists():
            z = np.load(path.with_suffix(".npz"), allow_pickle=False)
            pos = {int(k): i for i, k in enumerate(z["idx"])}
            return torch.as_tensor(z["roots"][[pos[i] for i in ids]]).double()
    return None


def brief(r):
    return {k: r[k] for k in ("class", "reason", "root_distance", "readout_difference", "a")}


def stage_run():
    if (OUT / "run.json").exists():
        return
    rows = load("genomes.json")["genomes"]
    out, states, t0, failed = [], {}, time.time(), 0
    limit = int(STOP_FRACTION * len(rows))  # 8 of 169: a ninth failure stops the run
    for _, seed, _ in PANELS:
        pr = [r for r in rows if r["seed"] == seed]
        ids = [r["genome"] for r in pr]
        CAP.check()
        g, cfg = build(seed, ids)
        run_a, rec_a, roots_a = phase_a(g, cfg)
        ref = census_roots(seed, ids)
        ref_diff = (roots_a - ref).abs().amax(-1).amax(-1).tolist() if ref is not None else [None] * len(pr)
        consistent = [ra["class"] == r["census_class"] for ra, r in zip(rec_a, pr)]
        failed += consistent.count(False)
        base = [{**r, "A": brief(ra), "consistent": ok, "census_root_diff": rd}
                for r, ra, ok, rd in zip(pr, rec_a, consistent, ref_diff)]
        if failed > limit:
            dump({"rows": out + base, "inconsistent": failed, "stopped": True, "complete": False}, "run.json")
            raise Stop(f"{failed} genomes did not reproduce their census class: stopped for investigation")
        states[f"{seed}__roots_a"] = roots_a.numpy()
        for arm in ARMS:
            CAP.check()
            (run_b, rec_b, roots_b), (run_c, rec_c, roots_c) = arm_phases(g, cfg, run_a["end"], arm)
            m = match(roots_a, roots_c)
            sep = separation(run_b).tolist()
            dca = (roots_c[:, :, None] - roots_a[:, None]).abs().amax(-1).tolist()  # [S, C history, A root]
            for i, b in enumerate(base):
                b[arm] = {"B": brief(rec_b[i]), "C": brief(rec_c[i]), "held": held(rec_b[i]["class"]),
                          "match": m[i], "outcome": outcome(rec_c[i]["class"], m[i]),
                          "separation_B": dict(zip([str(t) for t in SEP_TICKS] + ["2000"], sep[i])),
                          "C_to_A_root_distance": dca[i]}
            states[f"{seed}__{arm}__roots_b"] = roots_b.numpy()
            states[f"{seed}__{arm}__roots_c"] = roots_c.numpy()
        out += base
        print(f"seed {seed}: {len(pr)} genomes, A consistent {consistent.count(True)}, "
              + ", ".join(f"{arm} held {sum(b[arm]['held'] == 'held' for b in base)} recovered "
                          f"{sum(b[arm]['outcome'] == 'recovered' for b in base)}" for arm in ARMS)
              + f", {time.time() - t0:.0f} s", flush=True)
    CAP.check()
    np.savez(OUT / "roots.npz", **states)
    dump({"rows": out, "seconds": round(time.time() - t0, 1), "inconsistent": failed, "stopped": False,
          "complete": True}, "run.json")


STAGES = {"genomes": stage_genomes, "run": stage_run}


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
    if torch.cuda.is_initialized():
        raise Stop("CUDA was initialised")


if __name__ == "__main__":
    todo = sys.argv[1:] or list(STAGES)
    OUT.mkdir(parents=True, exist_ok=True)
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M6-outlast",
                       script="outlast.py"):
        try:
            main(todo)
        except reg.CapReached:
            raise Stop(f"the run's {STOP_HOURS}-hour cap was reached: what finished is incomplete, not read")
