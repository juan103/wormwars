"""E4s-1 design: the simulated power of O1's registered rules, and gate 1's chance of a fail (rule 5).

    python scripts/e4s1_power.py   # writes experiments/E4s-stereo-module/E4s-1/development-records/power.json

O1's rules, in order, on the mean of 16 paired run differences with a 90% percentile bootstrap over
runs: "reversed" (upper bound < 0); "supports" (lower bound > 0 and estimate >= 0.5); "positive,
below 0.5" (lower bound > 0, estimate < 0.5); "does not support an effect of at least 0.5" (upper
bound < 0.5); "inconclusive". Scenarios: normal differences, and a bimodal one in which a share of
runs keep the graft's benefit and the rest do not (E4s-0's robustness was bimodal).
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "experiments" / "E4s-stereo-module" / "E4s-1" / "development-records" / "power.json"
SEED, SIMS, BOOT, RUNS = 20_261_001, 1000, 2000, 16
LABELS = ("reversed", "supports", "positive; estimate below 0.5", "does not support an effect of at least 0.5", "inconclusive")


def decide(d, rng):
    m = d[rng.integers(0, len(d), size=(BOOT, len(d)))].mean(axis=1)
    lo, hi = np.percentile(m, [5, 95])
    est = d.mean()
    if hi < 0:
        return LABELS[0]
    if lo > 0 and est >= 0.5:
        return LABELS[1]
    if lo > 0:
        return LABELS[2]
    if hi < 0.5:
        return LABELS[3]
    return LABELS[4]


def rates(draw, rng):
    out = [decide(draw(rng), rng) for _ in range(SIMS)]
    return {k: out.count(k) / SIMS for k in LABELS}


def gate1(mean=5.1767578125, se=0.0408842585057886, bar=5.0):
    """A pass needs the fresh 95% lower bound >= bar, i.e. a fresh mean >= bar + 1.96 se (the same se).
    Plug-in: the pilot mean taken as the truth. Predictive: the fresh mean minus the pilot mean has
    sd sqrt(2) se (a flat prior on the true mean)."""
    need = bar + 1.96 * se
    phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))  # noqa: E731
    return {"needed_fresh_mean": need, "plug_in_fail": phi((need - mean) / se),
            "predictive_fail": phi((need - mean) / (math.sqrt(2) * se)), "pilot_mean": mean, "se": se}


def main():
    rng = np.random.default_rng(SEED)
    normal = {f"sd {sd} effect {e}": rates(lambda r, e=e, sd=sd: r.normal(e, sd, RUNS), rng)
              for sd in (1.3, 2.0) for e in (0.0, 0.5, 1.0, 1.5)}

    def bimodal(share, gain):
        def draw(r):
            keep = r.random(RUNS) < share
            return np.where(keep, r.normal(gain, 0.7, RUNS), r.normal(0.0, 0.7, RUNS))
        return draw
    bi = {f"share {s} keep +{g}": rates(bimodal(s, g), rng) for s in (0.25, 0.5, 0.75) for g in (2.0, 3.0)}
    zero = normal["sd 1.3 effect 0.0"]["supports"], normal["sd 2.0 effect 0.0"]["supports"]
    doc = {"seed": SEED, "simulations": SIMS, "bootstrap": BOOT, "runs": RUNS, "normal": normal, "bimodal": bi,
           "family_false_supports_two_tests_if_independent": {"sd 1.3": 1 - (1 - zero[0]) ** 2, "sd 2.0": 1 - (1 - zero[1]) ** 2},
           "gate1": gate1(),
           "bootstrap_note": "2 000 resamples per simulated decision, against the registered 10 000 (for speed); "
                             "the family rate assumes the two tests are independent, an illustration only: "
                             "M - N and M - R share M",
           "gate1_note": "the score-threshold component of gate 1 only, under a fixed-se normal model",
           "note": "the bimodal scenario: each run keeps the benefit (normal around the gain, sd 0.7) with the "
                   "given share, else none (normal around 0, sd 0.7)"}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"gate1": doc["gate1"], "family": doc["family_false_supports_two_tests_if_independent"],
                      "normal sd1.3": {k: v["supports"] for k, v in normal.items() if "1.3" in k},
                      "bimodal": {k: (v["supports"], v["positive; estimate below 0.5"]) for k, v in bi.items()}}, indent=1))


if __name__ == "__main__":
    main()
