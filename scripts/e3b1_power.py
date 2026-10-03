"""E3b-1's gate, simulated as it will be computed (design v2; both reviewers of v1, D182). On the CPU.

    python scripts/e3b1_power.py      # writes experiments/E3-ab-organism/E3b-1/power.json

The gate compares 16 tuned runs with the frozen seed: 8 of schedule A (125 generations, 16 mazes) and 8 of
schedule F (300 generations, 8 mazes). Each run's difference d = tuned − seed is in units of the seed's mean.
- **The estimand:** the equally weighted mean of the two schedules' effects, (mean d_A + mean d_F) / 2
  (Astra). With 8 runs each it equals the pooled mean.
- **The primary rule:** a one-sided Welch t-test of that estimand, with variance from within each schedule,
  (s_A² / 8 + s_F² / 8) / 4, and Satterthwaite's degrees of freedom; "better" at p ≤ 0.05.
- **Beside it:** the pooled one-sided t-test on all 16, and the exact sign-flip test over all 2^16 patterns.
- **Scenarios:**
  - equal effects, with a CV of 0.267, 0.282 or 0.40 in both schedules;
  - unequal spreads (0.15 and 0.40);
  - different means (the effect ± 0.10);
  - opposite effects averaging zero (−0.15 and +0.15), a false-positive check for the estimand's null.
  Each scenario uses the normal and E3a's two-cluster empirical shape.
- **Also:** the power to reject "an improvement of at most 10%" (a shifted null), for reference.

For each, the false-positive rate at effect 0 and the power on a 0.01 grid, 4 000 trials, seed 20 261 005.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "E3-ab-organism" / "E3b-1" / "power.json"
STAGE3 = np.array([8.92, 8.78, 14.68, 15.98, 15.77, 8.53, 9.54, 14.50])  # E3a summary.json, test means
Z = (STAGE3 - STAGE3.mean()) / STAGE3.std(ddof=1)
SIGNS16 = np.array(list(itertools.product((1.0, -1.0), repeat=16)), dtype=np.float32)  # 65 536 x 16
N = 8


def draw(rng, shape, trials, mean, sd):
    if shape == "normal":
        return mean + sd * rng.standard_normal((trials, N))
    return mean + sd * rng.choice(Z, size=(trials, N), replace=True)


def welch_p(a, b, shift=0.0):
    est = (a.mean(1) + b.mean(1)) / 2 - shift
    va, vb = a.var(1, ddof=1) / N, b.var(1, ddof=1) / N
    se = np.sqrt(va + vb) / 2
    df = (va + vb) ** 2 / (va ** 2 / (N - 1) + vb ** 2 / (N - 1))
    return stats.t.sf(est / se, df)


def pooled_p(a, b):
    return stats.ttest_1samp(np.concatenate([a, b], 1), 0.0, axis=1, alternative="greater").pvalue


def signflip_p(a, b, chunk=500):
    d = np.concatenate([a, b], 1).astype(np.float32)
    out = np.empty(len(d))
    for i in range(0, len(d), chunk):
        x = d[i:i + chunk]
        null = x @ SIGNS16.T / 16  # [chunk, 65 536]
        out[i:i + chunk] = (null >= x.mean(1, keepdims=True) - 1e-7).mean(1)
    return out


def scenario(rng, shape, trials, effect, sd_a, sd_f, shift_a=0.0, shift_f=0.0, signflip=False):
    a = draw(rng, shape, trials, effect + shift_a, sd_a)
    b = draw(rng, shape, trials, effect + shift_f, sd_f)
    out = {"welch": float(np.mean(welch_p(a, b) <= 0.05)), "pooled_t": float(np.mean(pooled_p(a, b) <= 0.05)),
           "welch_vs_10pct": float(np.mean(welch_p(a, b, shift=0.10) <= 0.05))}
    if signflip:
        out["signflip"] = float(np.mean(signflip_p(a, b) <= 0.05))
    return out


def main():
    rng = np.random.default_rng(20_261_005)
    effects = [round(0.01 * k, 2) for k in range(0, 41)]
    trials = 4000
    res = {}
    cases = {"equal_cv0.267": (0.267, 0.267, 0, 0), "equal_cv0.282": (0.282, 0.282, 0, 0),
             "equal_cv0.40": (0.40, 0.40, 0, 0), "unequal_sd_0.15_0.40": (0.15, 0.40, 0, 0),
             "different_means_pm0.10": (0.282, 0.282, -0.10, 0.10)}
    for shape in ("normal", "empirical"):
        for name, (sa, sf, ma, mf) in cases.items():
            rows = {str(e): scenario(rng, shape, trials, e, sa, sf, ma, mf,
                                     signflip=(name == "equal_cv0.282" and e in (0.0, 0.1, 0.2, 0.3)))
                    for e in effects}
            mde = {rule: next((e for e in effects[1:] if rows[str(e)][rule] >= 0.8), None)
                   for rule in ("welch", "pooled_t", "welch_vs_10pct")}
            fp = {rule: v for rule, v in rows["0.0"].items()}
            res[f"{shape}, {name}"] = {"false_positive": fp, "mde_80": mde, "power": rows}
            print(shape, name, "fp", {k: round(v, 3) for k, v in fp.items()}, "mde", mde, flush=True)
        opp = scenario(rng, shape, trials, 0.0, 0.282, 0.282, -0.15, 0.15, signflip=True)
        res[f"{shape}, opposite_effects_-0.15_+0.15"] = {"rejection_rate": opp}
        print(shape, "opposite", opp, flush=True)
    doc = {"note": __doc__.split("\n\n")[1], "trials": trials, "seed": 20_261_005, "effects_step": 0.01,
           "results": res}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
