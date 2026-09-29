"""E2d, Part A: what E2's committed records say about noise, nomination and the plateau (no GPU).

    python scripts/e2d_records.py     # writes experiments/E2d-taskn-diagnosis/part-a.json

Reads only `experiments/E2-optimizer-screen/` (the hold-out's per-world counts and the training and
checkpoint records). Descriptive; see experiments/E2d-taskn-diagnosis/PLAN.md, Part A.
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
E2 = ROOT / "experiments" / "E2-optimizer-screen"
OUT = ROOT / "experiments" / "E2d-taskn-diagnosis" / "part-a.json"
SETS = ("ga", "es", "random", "extension")
BINS = ((0.05, 0.15), (0.15, 0.30), (0.30, 0.60))  # gaps between hold-out means, [lo, hi)
KS = (8, 32, 128)
RESAMPLES, SEED = 400, 0


def load(name: str) -> dict:
    return json.loads((E2 / f"{name}.json").read_text(encoding="utf-8"))


def champion_counts(ev: dict) -> dict:
    """{(set, run): per-world hold-out counts, real probe}."""
    pw = ev["per_world_counts"]
    return {(s, r): np.asarray(pw[f"{s} run{r:02d} real"]) for s in SETS for r in range(8)
            if f"{s} run{r:02d} real" in pw}


def ranking(counts: dict, sha: dict) -> list[dict]:
    """For pairs of distinct genomes whose hold-out means differ by a gap in each bin: how often the
    mean over k shared worlds, resampled from the 1 024, ranks them like their 1 024-world means.
    Reported strictly correct, tied, and with ties counted half. A genome that appears in two sets
    (the same hash) is counted once."""
    rng = np.random.default_rng(SEED)
    keys, seen = [], set()
    for k in counts:
        if sha[k] not in seen:
            seen.add(sha[k])
            keys.append(k)
    rows = []
    for lo, hi in BINS:
        pairs = [(a, b) for a, b in itertools.combinations(keys, 2)
                 if lo <= abs(counts[a].mean() - counts[b].mean()) < hi]
        row = {"gap": [lo, hi], "pairs": len(pairs)}
        for k in KS:
            right = tied = 0.0
            for a, b in pairs:
                x, y = counts[a], counts[b]
                if x.mean() < y.mean():
                    x, y = y, x
                idx = rng.integers(0, len(x), size=(RESAMPLES, k))
                dx, dy = x[idx].mean(1), y[idx].mean(1)
                right += (dx > dy).mean()
                tied += (dx == dy).mean()
            n = max(len(pairs), 1)
            row[f"k{k}"] = {"strict": right / n, "tied": tied / n, "ties_half": (right + tied / 2) / n}
        rows.append(row)
    return rows


def nomination(rec: dict, method: str) -> dict:
    """Each checkpoint's nominee after generation 0: its training score against its validation mean."""
    tr, va, per_run = [], [], {}
    for r in rec["records"]:
        logs = {x["generation"]: x for x in r["log"]}
        t_run, v_run = [], []
        for c in r["checkpoints"][1:]:
            t = c.get("training_score")
            t = logs[c["generation"]]["best_fitness"] if t is None else t
            t_run.append(t)
            v_run.append(c["validation_mean"])
        per_run[str(r["spec"]["run"])] = {"training": float(np.mean(t_run)), "validation": float(np.mean(v_run))}
        tr += t_run
        va += v_run
    tr, va = np.asarray(tr), np.asarray(va)
    pool = "the best of 800 draws (768 for the last)" if method == "random" else "the best of its generation's 32"
    return {"nominees": int(len(tr)), "training_mean": float(tr.mean()), "validation_mean": float(va.mean()),
            "drop": float(tr.mean() - va.mean()), "correlation": float(np.corrcoef(tr, va)[0, 1]),
            "nominee_is": pool, "per_run": per_run}


def population(rec: dict, first: int) -> dict:
    """Per run, over generations `first` on: the generation's best and mean training score and its
    share of zero scores."""
    out = {}
    for r in rec["records"]:
        logs = r["log"][first:]
        out[str(r["spec"]["run"])] = {k: float(np.mean([x[f] for x in logs]))
                                      for k, f in (("best", "best_fitness"), ("mean", "mean_fitness"),
                                                   ("zero_share", "zero_share"))}
    return out


def main() -> dict:
    ev = load("evaluation")
    counts = champion_counts(ev)
    sha = {k: ev["champion_sha256"][f"{k[0]} run{k[1]:02d}"] for k in counts}
    m_avg = float(ev["controls"]["M-avg"])
    sds = {s: [float(counts[(s, r)].std(ddof=1)) for r in range(8)] for s in SETS}
    doc = {
        "source": "experiments/E2-optimizer-screen/ (evaluation.json, train-*.json, extension.json)",
        "noise": {
            "per_world_sd": {s: [min(v), max(v)] for s, v in sds.items()},
            "se_of_an_8_world_mean": {s: [min(v) / 8 ** 0.5, max(v) / 8 ** 0.5] for s, v in sds.items()},
            "note": "a proxy: the SE of a champion's mean over 8 hold-out worlds; training worlds come from the same "
                    "generator, and their per-world spread for training candidates was not recorded",
        },
        "ranking": {"resamples_per_pair": RESAMPLES, "seed": SEED, "rows": ranking(counts, sha),
                    "note": "pairs of distinct champions; not parent-offspring pairs, ES antithetic pairs or random "
                            "sampling's nominations; the 1 024-world mean is the reference"},
        "nomination": {"random": nomination(load("train-random"), "random"), "ga": nomination(load("train-ga"), "ga")},
        "population": {"ga_generations_500_999": population(load("train-ga"), 500),
                       "es_generations_300_622": population(load("train-es"), 300)},
        "plateau": {"m_avg": m_avg, "s_const": float(ev["controls"]["S-const"]),
                    "champions": {s: [float(counts[(s, r)].mean()) for r in range(8)] for s in SETS},
                    "within_0.25_of_m_avg": {s: int(sum(abs(counts[(s, r)].mean() - m_avg) <= 0.25 for r in range(8)))
                                             for s in SETS},
                    "above_m_avg": {s: int(sum(counts[(s, r)].mean() > m_avg for r in range(8))) for s in SETS}},
        "shared_genomes": sorted({f"{a[0]} run{a[1]:02d} = {b[0]} run{b[1]:02d}"
                                  for a, b in itertools.combinations(counts, 2) if sha[a] == sha[b]}),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    return doc


if __name__ == "__main__":
    d = main()
    for row in d["ranking"]["rows"]:
        print(row["gap"], row["pairs"], {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in row.items()
                                         if k.startswith("k")})
    print(d["plateau"]["within_0.25_of_m_avg"], d["plateau"]["above_m_avg"], d["shared_genomes"])
    sys.exit(0)
