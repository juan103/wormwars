"""E3b-0's power criterion (docs/E3/E3b-0-PLAN.md §5, criterion 6), on the CPU, before anything else.

    python scripts/e3b0_power.py      # writes experiments/E3-ab-organism/E3b-0/power.json

The gate compares each tuned run's test-maze mean with the frozen seed's on the same mazes. The seed is
one fixed organism, so the run-level difference d_i = tuned_i − seed has the spread of the tuned runs
alone: a one-sample problem on 8 differences.
- **The spread:** in units of the seed's mean, the coefficient of variation, by two readings of E3a's
  Stage 3 champions: 0.267 (SD / E's mean) and 0.282 (SD / their own mean). Sensitivity at 0.15 and 0.40.
- **The shape:** normal, and E3a's two-cluster empirical shape (the 8 Stage 3 test means, centred and
  scaled to the CV).
- **The rules, one-sided 5% nominal:**
  - the 90% percentile bootstrap's lower bound > 0 (E2d's `_boot_means`, 10 000 resamples);
  - the exact sign-flip test over the 2^8 patterns;
  - a one-sided t-test.

For each: the false-positive rate at effect 0, the power at effects of 0.05-0.50 of the seed's mean, and
the minimum detectable effect at 80% power.

**Added 2026-10-02 (rule 5):** the plan's figures for 12 and 16 runs, and its finer ones for 8, were not in
this file's first output (8 runs, a 0.05 grid). `fine` now holds, for 8, 12 and 16 runs, the t-test's and
the exact sign-flip test's power on a 0.01 grid of effects (sign-flip for 8 and 12 only: 16 needs 65 536
patterns per trial), the bootstrap's false-positive rate, and the minimum detectable effects read from it.
The first output (`results`) is unchanged.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "E3-ab-organism" / "E3b-0" / "power.json"
STAGE3 = np.array([8.92, 8.78, 14.68, 15.98, 15.77, 8.53, 9.54, 14.50])  # E3a summary.json, test means
SIGNS = np.array(list(itertools.product((1.0, -1.0), repeat=8)))


def bootstrap_reject(d, rng, resamples=2000):
    m = d[rng.integers(0, len(d), size=(resamples, len(d)))].mean(axis=1)
    return np.percentile(m, 5) > 0


def signflip_reject(d):
    obs = d.mean()
    null = (SIGNS * d).mean(axis=1)
    return np.mean(null >= obs - 1e-12) <= 0.05


def t_reject(d):
    return stats.ttest_1samp(d, 0.0, alternative="greater").pvalue <= 0.05


def draws(shape, cv, effect, rng, n=8):
    if shape == "normal":
        return effect + cv * rng.standard_normal(n)
    z = (STAGE3 - STAGE3.mean()) / STAGE3.std(ddof=1)  # the empirical two-cluster shape, unit SD
    return effect + cv * rng.choice(z, size=n, replace=True)


def fine(rng, trials: int = 4000) -> dict:
    """Vectorised: power on a 0.01 grid for 8, 12 and 16 runs."""
    effects = [round(0.01 * k, 2) for k in range(0, 51)]
    out = {}
    for n in (8, 12, 16):
        signs = np.array(list(itertools.product((1.0, -1.0), repeat=n))) if n <= 12 else None
        for shape in ("normal", "empirical"):
            for cv in (0.267, 0.282):
                res = {"t": {}, "signflip": {}} if signs is not None else {"t": {}}
                for e in effects:
                    d = np.stack([draws(shape, cv, e, rng, n=n) for _ in range(trials)])
                    res["t"][str(e)] = float(np.mean(stats.ttest_1samp(d, 0.0, axis=1, alternative="greater").pvalue <= 0.05))
                    if signs is not None:
                        null = d @ signs.T / n
                        p = np.mean(null >= d.mean(axis=1, keepdims=True) - 1e-12, axis=1)
                        res["signflip"][str(e)] = float(np.mean(p <= 0.05))
                d0 = np.stack([draws(shape, cv, 0.0, rng, n=n) for _ in range(1000)])
                boot_fp = float(np.mean([bootstrap_reject(x, rng) for x in d0]))
                row = {r: {"false_positive": v["0.0"], "power": v,
                           "mde_80": next((e for e in effects[1:] if v[str(e)] >= 0.8), None)} for r, v in res.items()}
                row["bootstrap90_false_positive"] = boot_fp
                out[f"{n} runs, {shape}, CV {cv}"] = row
                print(n, shape, cv, {r: (round(x["false_positive"], 3), x["mde_80"]) for r, x in row.items()
                                     if isinstance(x, dict)}, "boot fp", round(boot_fp, 3))
    return {"trials": trials, "effects_step": 0.01, "results": out}


def main():
    rng = np.random.default_rng(20_261_003)
    effects = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]
    trials = 2000
    out = {"note": __doc__.split("\n\n")[1], "trials": trials, "results": {}}
    for shape in ("normal", "empirical"):
        for cv in (0.15, 0.267, 0.282, 0.40):
            key = f"{shape}, CV {cv}"
            res = {}
            for rule, fn in (("bootstrap90", lambda d: bootstrap_reject(d, rng)), ("signflip", signflip_reject),
                             ("t", t_reject)):
                pw = {}
                for e in effects:
                    pw[str(e)] = float(np.mean([fn(draws(shape, cv, e, rng)) for _ in range(trials)]))
                mde = next((e for e in effects[1:] if pw[str(e)] >= 0.8), None)
                res[rule] = {"false_positive": pw["0.0"], "power": pw, "mde_80": mde}
            out["results"][key] = res
            print(key, {r: (round(v["false_positive"], 3), v["mde_80"]) for r, v in res.items()})
    out["fine"] = fine(np.random.default_rng(20_261_004))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
