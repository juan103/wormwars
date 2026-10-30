"""M6, option 0 (docs/memory/M6-0-PLAN.md): is the history effect selection built on T1 (02b) a switch or slow fading?
Every T1 genome 02 saved (g00, g39, g79) and a mutation-only drift control (each g00 mutated 39 times, 4 replicates)
are classified by M2's frozen classifier, with M4e's second pass, under each run's food mapping, on two banks: each
run's own (02b's typical input) and 03mc's. Writes runs/memory-m6-0/; readings by m6_0_read.py. CPU only: the GPU is
hidden before torch is imported.

Usage: python scripts/memory_m6/m6_0.py [stage ...]   (stages: genomes banks first second; all, in that order)
"""

from __future__ import annotations

import os

if __name__ == "__main__":  # before torch: 02b's module picks CUDA when it can (Astra, Fable); not on import (tests)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

import dataclasses  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
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
import common as c  # noqa: E402
import pilot as P  # noqa: E402
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import Brain, Genome  # noqa: E402
from wormwars.evo import load_genome  # noqa: E402

torch.set_grad_enabled(False)
OUT = Path(os.environ.get("MEMORY_M6_OUT", ROOT / "runs" / "memory-m6-0"))
GENOMES = ROOT / "runs" / "exp02-screening"
_A = []


def analyse():
    """02b's analysis module, loaded on first use (it reads the local records.jsonl on import), on the CPU."""
    if not _A:
        spec = importlib.util.spec_from_file_location("analyse_02b",
                                                      ROOT / "experiments" / "02b-champion-analysis" / "analyse.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.DEV = "cpu"  # read at call time by its setup, load and typical_input
        _A.append(mod)
    return _A[0]

TAGS = ("g00", "g39", "g79")
DRIFT_REPS, DRIFT_GENERATIONS = 4, 39
BANKS = ("own", "03mc")
EXTRA, TAIL = 20_000, 200  # M4e's second pass: the hold continued from tick 2000 to 22,000
AUDIT_PER_BANK, AUDIT_SEED = 20, 20261130
FADING = "fading"
STOP_HOURS = 5.0
CAP = reg.CapClock(STOP_HOURS, OUT / "compute.json")
EXPECT = {"g00": 102, "g39": 102, "g79": 4, "drift": 408}


class Stop(SystemExit):
    pass


def dump(obj, name):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(obj, indent=1), encoding="utf-8")


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------------------- genomes
def t1_records():
    return sorted((r for r in analyse().RECORDS if r["task"] == "T1"), key=lambda r: r["key"])


def block_of(r):
    """The independent unit: graph and run index (02 seeds a run from them, not from the mapping)."""
    return f"{r['graph']}-run{r['run']:02d}"


def drift_seed(key, k):
    """From the run's key and the replicate, not the order of records.jsonl (Fable)."""
    return int.from_bytes(hashlib.sha256(f"{key}/drift{k}".encode()).digest()[:8], "big") >> 1


def param_hash(g: Genome, i=0):
    h = hashlib.sha256()
    for k in g.PARAMS:
        x = getattr(g, k)
        if x is not None:
            h.update(np.ascontiguousarray(x[i].numpy()).tobytes())
    return h.hexdigest()


def drifted(g00: Genome, cfg, seed):
    """02b's control on the CPU: g00 mutated 39 times with the run's mutation settings, no selection."""
    gen = torch.Generator(device="cpu").manual_seed(seed)
    g = g00.clone()
    for _ in range(DRIFT_GENERATIONS):
        g.mutate(cfg.mutation, generator=gen)
    return g


def setup(r):
    """02b's setup on the CPU (T1's configuration for the graph, the calibrated gains, the mapping's interface)."""
    cfg, iface, graph, spec = analyse().setup(r)
    if spec.device.type != "cpu":
        raise Stop("02b's setup did not run on the CPU")
    return cfg, iface, spec


def load_one(r, tag, spec, cfg):
    """A saved genome, its stored configuration checked against the constructed one (Fable)."""
    g, _ = load_genome(GENOMES / f"{r['key']}-{tag}.npz", spec, None, device="cpu")
    if dataclasses.asdict(g.cfg) != dataclasses.asdict(cfg.brain):
        raise Stop(f"{r['key']}-{tag}: the stored brain configuration differs from T1's for {r['graph']}")
    return g


def run_genomes(r, cfg, spec):
    """[(label, genome)] for one run: g00, g39, g79 if saved, then the four drift replicates."""
    out = [(tag, load_one(r, tag, spec, cfg)) for tag in TAGS if (GENOMES / f"{r['key']}-{tag}.npz").exists()]
    g00 = out[0][1]
    out += [(f"drift{k}", drifted(g00, cfg, drift_seed(r["key"], k))) for k in range(DRIFT_REPS)]
    return out


def tag_of(label):
    return "drift" if label.startswith("drift") else label


def stage_genomes():
    """The genome list, checked against the files: every T1 file and nothing else."""
    files = sorted(p.name for p in GENOMES.glob("T1-*.npz"))
    rows, used = [], []
    for r in t1_records():
        cfg, _, spec = setup(r)
        for label, g in run_genomes(r, cfg, spec):
            f = None if label.startswith("drift") else f"{r['key']}-{label}.npz"
            used += [f] if f else []
            rows.append({"key": r["key"], "block": block_of(r), "mapping": r["mapping"], "graph": r["graph"],
                         "family": analyse().family(r["graph"]), "label": label, "tag": tag_of(label), "file": f,
                         "drift_seed": drift_seed(r["key"], int(label[5:])) if f is None else None,
                         "param_sha256": param_hash(g)})
    if sorted(used) != files:
        raise Stop("the genome list is not exactly the T1 files")
    counts = {t: sum(x["tag"] == t for x in rows) for t in EXPECT}
    if counts != EXPECT:
        raise Stop(f"genome counts {counts}, the plan's {EXPECT}")
    dump({"genomes": rows, "counts": counts, "blocks": len({x["block"] for x in rows}),
          "distinct_g00": len({x["param_sha256"] for x in rows if x["tag"] == "g00"})}, "genomes.json")


def check_genomes():
    """The saved list regenerates (files, drift seeds and parameter hashes)."""
    saved = load("genomes.json")["genomes"]
    want = []
    for r in t1_records():
        cfg, _, spec = setup(r)
        want += [(r["key"], label, param_hash(g)) for label, g in run_genomes(r, cfg, spec)]
    if [(x["key"], x["label"], x["param_sha256"]) for x in saved] != want:
        raise Stop("genomes.json does not regenerate")


# --------------------------------------------------------------------------------------------------------------- banks
def stage_banks():
    """Each run's own bank: 02b's typical_input (the g39 champion's mean sensed signals, ticks 20 to 60), on the CPU."""
    if (OUT / "banks.json").exists():
        return
    out = {}
    for r in t1_records():
        cfg, iface, spec = setup(r)
        out[r["key"]] = analyse().typical_input(r, cfg, iface, spec)
    dump({"own": out, "03mc": c.S.BANK}, "banks.json")


def bank_for(name, key):
    b = load("banks.json")
    return b["own"][key] if name == "own" else b["03mc"]


# ---------------------------------------------------------------------------------------------------------- the passes
def persistence(y, floor=c.START_FLOOR, remain=c.REMAIN):
    """Per genome, from the read-out difference d(t) = |y_rising - y_falling| at every tick 0..T (y [S, T + 1, 2]):
    a and d(5); d(5), d(30), d(100), d(300) over a; tau_stay (the first tick after which d stays below remain * a
    through T, None if d(T) >= remain * a: censored); tau_first (the first tick with d < remain * a, None if never)
    and whether d returns above remain * a after it. The ratios and times only for a >= floor (absent below)."""
    d = np.abs(y[:, :, 0] - y[:, :, 1])
    T = d.shape[1] - 1
    out = []
    for row in d:
        a = float(row[0])
        rec = {"a": a, "d5": float(row[5]), "eligible": a >= floor}  # d5 for the check against 02b's "after"
        if a >= floor:
            below = row < remain * a
            for t in (5, 30, 100, 300):
                rec[f"r{t}"] = float(row[t] / a)
            above = np.where(~below)[0]
            last_above = int(above[-1]) if len(above) else -1
            rec["tau_stay"] = None if last_above == T else last_above + 1
            first = np.where(below)[0]
            rec["tau_first"] = int(first[0]) if len(first) else None
            rec["returns"] = bool(len(first) and last_above > first[0])
        out.append(rec)
    return out


def continue_hold(gs, cfg, end, ticks, tail=TAIL):
    """M4e's continue_hold (scripts/memory_m4/m4e.py), copied: importing M4e creates run folders (Fable). A test checks
    the copy against M4e's bitwise."""
    brain = Brain(gs)
    s, n = gs.n_strains, gs.spec.n
    food = c.final_food()
    cf = c.at(cfg, n, s, [food, food]).to(torch.float32)
    v = end.to(torch.float32).clone()
    rec, pre = [], v.clone()
    for t in range(1, ticks + 1):
        v = c.finite(brain.step(v, cf, None), f"second pass {t}")
        if t == ticks - tail:
            pre = v.clone()
        if t > ticks - tail:
            rec.append(v.clone())
    return {"end": v.double(), "cur": cf.double(), "tail": torch.stack(rec, 1).numpy().astype(np.float32),
            "pre_tail": pre}


def second_pass(g, cfg, idx, ends, ys):
    """M4e's second_pass, copied: the hold continued to 22,000 ticks and classified by the same rules, with the first
    pass's write amplitude and read-out differences kept."""
    if not idx:
        return []
    gs = g.select(list(idx))
    run = continue_hold(gs, cfg, ends, EXTRA)
    run["y"] = ys
    recs, _ = P.full_classify(gs, cfg, run, compact=True, initial=run["pre_tail"], follow_ticks=TAIL, tail_from=1)
    return recs


def first_file(bank):
    return OUT / f"first-{bank}.json"


def stage_first():
    """The first pass on every genome and both banks, run by run (one batch per run), with persistence. The tick-2000
    states and the first 301 ticks of the read-out are kept locally for the second pass."""
    for bank in BANKS:
        f = first_file(bank)
        if f.exists():
            continue
        rows, local = [], {}
        t0 = time.time()
        for r in t1_records():
            CAP.check()
            cfg, iface, spec = setup(r)
            labels, gs = zip(*run_genomes(r, cfg, spec))
            g = Genome.cat(list(gs))
            with c.probe_input(iface, bank_for(bank, r["key"])):
                run = P.probe_states(g, cfg)
                sub = {"end": run["end"], "cur": run["cur"], "y": run["y"], "tail": run["tail"]}
                recs, _ = P.full_classify(g, cfg, sub, compact=True)
            per = persistence(run["y"])
            for label, rec, p in zip(labels, recs, per):
                rows.append({"key": r["key"], "label": label, "tag": tag_of(label), "class": rec["class"],
                             "reason": rec["reason"], "root_distance": rec["root_distance"],
                             "readout_difference": rec["readout_difference"], **p})
            local[r["key"]] = (run["end"].numpy(), run["y"][:, :301])
            print(f"{bank} {r['key']}: {[x['class'] for x in rows[-len(labels):]]}", flush=True)
        np.savez(OUT / f"first-{bank}-states.npz", **{f"{k}__end": v[0] for k, v in local.items()},
                 **{f"{k}__y": v[1] for k, v in local.items()})
        dump({"bank": bank, "rows": rows, "seconds": round(time.time() - t0, 1)}, f.name)


def audit_ids(rows, bank):
    """20 first-pass-fading genomes per bank: 10 among g39 and g79, 10 among g00 and drift."""
    rng = np.random.default_rng(AUDIT_SEED + BANKS.index(bank))
    pick = []
    for tags in (("g39", "g79"), ("g00", "drift")):
        pool = [i for i, x in enumerate(rows) if x["tag"] in tags and x["class"] == FADING]
        pick += [pool[j] for j in sorted(rng.choice(len(pool), min(AUDIT_PER_BANK // 2, len(pool)), replace=False))]
    return sorted(pick)


def stage_second():
    """The second pass on every genome not fading on the first, plus the audit, run by run. Its time is forecast from
    the first batches; a forecast past the cap stops the run before more is spent (Astra)."""
    t_start, done_n = time.time(), 0
    for bank in BANKS:
        f = OUT / f"second-{bank}.json"
        if f.exists():
            continue
        first = json.loads(first_file(bank).read_text(encoding="utf-8"))["rows"]
        audit = audit_ids(first, bank)
        who = sorted(set(audit) | {i for i, x in enumerate(first) if x["class"] != FADING})
        z = np.load(OUT / f"first-{bank}-states.npz", allow_pickle=False)
        out = {}
        for r in t1_records():
            idx = [i for i in who if first[i]["key"] == r["key"]]
            if not idx:
                continue
            CAP.check()
            cfg, iface, spec = setup(r)
            labels, gs = zip(*run_genomes(r, cfg, spec))
            pos = [labels.index(first[i]["label"]) for i in idx]
            g = Genome.cat(list(gs))
            ends = torch.from_numpy(z[f"{r['key']}__end"])[pos]
            ys = z[f"{r['key']}__y"][pos]
            with c.probe_input(iface, bank_for(bank, r["key"])):
                recs = second_pass(g, cfg, pos, ends, ys)
            for i, rec in zip(idx, recs):
                out[i] = {"class": rec["class"], "reason": rec["reason"], "root_distance": rec["root_distance"],
                          "readout_difference": rec["readout_difference"]}
            done_n += len(idx)
            left = len(who) - len(out)  # this bank's; the next bank's is forecast when it starts
            per = (time.time() - t_start) / done_n
            if CAP.spent_hours() + (time.perf_counter() - CAP.t_start + per * left) / 3600 > STOP_HOURS:
                raise Stop(f"the second pass's forecast ({per:.0f} s a genome, {left} left) passes the "
                           f"{STOP_HOURS}-hour cap: stopped for the owner")
        dump({"bank": bank, "audit": audit, "ids": who, "records": {str(i): out[i] for i in who}}, f.name)
    if torch.cuda.is_initialized():
        raise Stop("CUDA was initialised")


STAGES = {"genomes": stage_genomes, "banks": stage_banks, "first": stage_first, "second": stage_second}


def main(stages):
    """genomes.json is written once and regenerated before every later stage."""
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
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M6-0",
                       script="m6_0.py"):
        try:
            main(todo)
        except reg.CapReached:
            raise Stop(f"the run's {STOP_HOURS}-hour cap was reached: what finished is incomplete, not read")
