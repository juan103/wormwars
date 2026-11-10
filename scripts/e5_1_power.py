"""E5-1's design numbers (docs/E5/E5-1-DESIGN.md §2, §5): the effect scale from E5-0, and O1's simulated labels.

1. The suite score (three strata, equally weighted: H1-bite; the mean of the 10 route speeds; the mean of the 6
   H2b settings) of every reused hunter in E5-0's `reading.json`, summarised by family. Exploratory: the score was
   defined after E5-0's reading.
2. O1's rules (`wormwars.e5.stats`) simulated under normal scores: N2's runs have run SD σr; SH-route's graphs
   have a graph effect of SD σg and runs within them σr. For each design (N2 runs; graphs × runs) and true Δ, the
   share of each label, and the interval's coverage of Δ. No E5-1 data exists; the scenarios are assumptions.

    python scripts/e5_1_power.py      # writes experiments/E5-hunter/E5-1/design-power.json (CPU, a few minutes)
"""

from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.e5 import stats as S  # noqa: E402

OUT = ROOT / "experiments" / "E5-hunter" / "E5-1" / "design-power.json"
DELTA = 0.25
DESIGNS = [(16, 16, 2), (32, 16, 4), (32, 20, 4), (32, 24, 2), (24, 16, 4), (32, 24, 4)]
RUN_SD = (0.2, 0.3, 0.45)
GRAPH_SD = (0.15, 0.3, 0.45)
TRUE = (0.0, DELTA, 2 * DELTA)
SIMS, BOOT, CHUNK, SEED = 2000, 2000, 100, 0


def family(lab: str) -> str:
    if lab.startswith("e4s1"):
        return "e4s1"
    if lab.startswith(("e2 ", "04a ")):
        return "e2d"
    if lab.startswith("L1"):
        return "L1 carrier"
    return "generation0"


def scale() -> dict:
    rd = json.loads((ROOT / "experiments/E5-hunter/E5-0/reading.json").read_text(encoding="utf-8"))
    s = rd["settings"]
    route = [n for n in s if n.startswith("H2-")]
    movers = [n for n in s if n.startswith("H2b-")]
    assert len(route) == 10 and len(movers) == 6
    fams: dict = {}
    for lab in s["H1-bite"]["hunters"]:
        m = lambda n: s[n]["hunters"][lab]["mean"]  # noqa: E731
        score = (m("H1-bite") + st.mean(m(n) for n in route) + st.mean(m(n) for n in movers)) / 3
        fams.setdefault(family(lab), []).append(score)
    return {f: {"n": len(v), "mean": round(st.mean(v), 4), "sd": round(st.stdev(v), 4) if len(v) > 1 else None,
                "min": round(min(v), 4), "max": round(max(v), 4)} for f, v in fams.items()}


def simulate(n, g, r, sr, sg, true, rng) -> dict:
    counts = dict.fromkeys(S.LABELS, 0)
    covered = 0
    for _ in range(SIMS // CHUNK):
        n2 = true + rng.normal(0, sr, (CHUNK, n))
        gm = rng.normal(0, sg, (CHUNK, g))[:, :, None] + rng.normal(0, sr, (CHUNK, g, r))
        d, lo, hi = S.intervals(n2, gm.mean(2), BOOT, rng)
        covered += int(((lo <= true) & (true <= hi)).sum())
        for k in range(CHUNK):
            counts[S.label(d[k], lo[k], hi[k], DELTA)] += 1
    return {"labels": {k: v / SIMS for k, v in counts.items()}, "coverage": covered / SIMS}


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # the labels carry δ; a Windows console is cp1252
    rng = np.random.default_rng(SEED)
    rows = []
    for n, g, r in DESIGNS:
        for sr in RUN_SD:
            for sg in GRAPH_SD:
                for true in TRUE:
                    res = simulate(n, g, r, sr, sg, true, rng)
                    rows.append({"n2_runs": n, "graphs": g, "runs_per_graph": r, "run_sd": sr, "graph_sd": sg,
                                 "true_delta": true, **res})
                    print(n, g, r, sr, sg, true, res["coverage"],
                          {k[:22]: round(v, 3) for k, v in res["labels"].items() if v})
    out = {"note": __doc__, "delta": DELTA, "sims": SIMS, "boot": BOOT, "seed": SEED,
           "suite_score_e5_0": scale(), "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
