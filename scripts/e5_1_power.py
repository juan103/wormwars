"""E5-1's design numbers (docs/E5/E5-1-DESIGN.md §2, §5): the effect scale from E5-0, and O1's simulated labels.

1. The suite score (three strata, equally weighted: H1-bite; the mean of the 10 route speeds; the mean of the 6
   H2b settings) of every reused hunter in E5-0's `reading.json`, summarised by family. Exploratory: the score was
   defined after E5-0's reading.
2. O1's rules (`wormwars.e5.stats`) simulated. N2's runs have run SD σ_N2; SH-route's graphs have a graph effect of
   SD σ_g and runs within them σ_SH. Scenarios (draft 3, after review round 2): normal scores; unequal run SDs; no
   graph effect; "dead" graphs (with probability p a graph's mean is 2 captures lower, as if L1 failed on it); and
   right-skewed run scores (centred lognormal residuals). The true Δ is N2's mean minus the ensemble's expected
   graph mean. For each design and scenario: the share of each label under Welch's interval (registered) and the
   percentile bootstrap (beside it), and each interval's coverage of Δ. No E5-1 data exists; the scenarios are
   assumptions.

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
DESIGNS = [(32, 20, 4), (32, 16, 4), (32, 24, 4)]
# name: (σ_N2, σ_SH, σ_g, dead share, skewed)
SCENARIOS = {
    "normal 0.2/0.2/0.15": (0.2, 0.2, 0.15, 0.0, False),
    "normal 0.3/0.3/0.3": (0.3, 0.3, 0.3, 0.0, False),
    "normal 0.3/0.3/0.45": (0.3, 0.3, 0.45, 0.0, False),
    "normal 0.45/0.45/0.45": (0.45, 0.45, 0.45, 0.0, False),
    "no graph effect 0.3/0.3/0": (0.3, 0.3, 0.0, 0.0, False),
    "unequal 0.2/0.4/0.3": (0.2, 0.4, 0.3, 0.0, False),
    "unequal 0.4/0.2/0.3": (0.4, 0.2, 0.3, 0.0, False),
    "dead 10% 0.3/0.3/0.3": (0.3, 0.3, 0.3, 0.1, False),
    "dead 30% 0.3/0.3/0.3": (0.3, 0.3, 0.3, 0.3, False),
    "skewed 0.3/0.3/0.3": (0.3, 0.3, 0.3, 0.0, True),
}
DEAD_DROP = 2.0
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


def noise(rng, sd, shape, skewed):
    if not skewed:
        return rng.normal(0, sd, shape)
    z = rng.lognormal(0.0, 0.8, shape)
    m, v = np.exp(0.32), (np.exp(0.64) - 1) * np.exp(0.64)  # lognormal(0, 0.8): mean and variance
    return (z - m) / np.sqrt(v) * sd


def simulate(n, g, r, scen, true, rng) -> dict:
    s_n2, s_sh, s_g, dead, skewed = scen
    out = {k: dict.fromkeys(S.LABELS, 0) for k in ("welch", "bootstrap")}
    cov = {"welch": 0, "bootstrap": 0}
    for _ in range(SIMS // CHUNK):
        n2 = -DEAD_DROP * dead + true + noise(rng, s_n2, (CHUNK, n), skewed)
        graph = rng.normal(0, s_g, (CHUNK, g)) - DEAD_DROP * (rng.random((CHUNK, g)) < dead)
        gm = (graph[:, :, None] + noise(rng, s_sh, (CHUNK, g, r), skewed)).mean(2)
        for name, (d, lo, hi) in (("welch", S.welch_many(n2, gm)), ("bootstrap", S.intervals(n2, gm, BOOT, rng))):
            cov[name] += int(((lo <= true) & (true <= hi)).sum())
            for k in range(CHUNK):
                out[name][S.label(d[k], lo[k], hi[k], DELTA)] += 1
    return {name: {"labels": {k: v / SIMS for k, v in out[name].items()}, "coverage": cov[name] / SIMS}
            for name in out}


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # the labels carry δ; a Windows console is cp1252
    rng = np.random.default_rng(SEED)
    rows = []
    for n, g, r in DESIGNS:
        for name, scen in SCENARIOS.items():
            for true in TRUE:
                res = simulate(n, g, r, scen, true, rng)
                rows.append({"n2_runs": n, "graphs": g, "runs_per_graph": r, "scenario": name,
                             "true_delta": true, **res})
                w = res["welch"]
                print(n, g, r, name, true, "welch cov", w["coverage"], "boot cov", res["bootstrap"]["coverage"],
                      {k[:22]: round(v, 3) for k, v in w["labels"].items() if v})
    worst = {k: min(row[k]["coverage"] for row in rows) for k in ("welch", "bootstrap")}
    out = {"note": __doc__, "delta": DELTA, "sims": SIMS, "boot": BOOT, "seed": SEED, "dead_drop": DEAD_DROP,
           "scenarios": SCENARIOS, "suite_score_e5_0": scale(), "worst_coverage": worst, "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("worst coverage", worst)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
