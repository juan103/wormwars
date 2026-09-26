"""Power of 03r's tests (pre-registration §7), from 03's P4 ensemble counts.

For each ensemble, the probability that one fresh graph is at or above N2 gets a Jeffreys
posterior from 03's count, Beta(r + 1/2, n - r + 1/2); fresh ensembles of 03r's sizes are drawn
from it. It assumes the tails are as 03 sampled them and ignores N2's own noise (SE 0.006).

    py -3.13 experiments/03r-replication/power.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy import stats as st

ROOT = Path(__file__).parents[2]
NEW_N = {"SH": 128, "SH-route": 256, "SH-class": 128, "SH-mirror": 128, "SH-recip": 128}
SIMS = 200_000


def crit(n: int, alpha: float) -> int:
    """The largest count r with (r + 1)/(n + 1) <= alpha."""
    return int(np.floor(alpha * (n + 1) - 1 + 1e-12))


def power(p4: dict, n2: float, alpha: float, rng) -> float:
    ok = np.ones(SIMS, bool)
    for e, d in p4.items():
        v = np.asarray(d["values"])
        k, n = int((v >= n2).sum()), len(v)
        q = rng.beta(k + 0.5, n - k + 0.5, SIMS)
        ok &= rng.binomial(NEW_N[e], q) <= crit(NEW_N[e], alpha)
    return float(ok.mean())


def main() -> None:
    p4 = json.loads((ROOT / "experiments" / "03-generation0" / "report.json").read_text(encoding="utf-8"))["signals"]["P4"]
    rng = np.random.default_rng(0)
    print("critical counts, P4 alone:", {e: crit(n, 0.05) for e, n in NEW_N.items()},
          "03's rule:", {e: crit(n, 0.05 / 3) for e, n in NEW_N.items()})
    for n2 in (0.9309, 0.925, 0.915, 0.905):
        print(f"N2 = {n2}: P4 alone {power(p4, n2, 0.05, rng):.2f}, 03's rule {power(p4, n2, 0.05 / 3, rng):.2f}")
    for alpha, label in ((0.05, "P4 alone"), (0.05 / 3, "03's rule")):
        tot = 1.0
        for e, d in p4.items():
            q = 1 - st.norm.cdf((d["n2"] - d["ensemble_mean"]) / d["ensemble_latent_sd"])
            tot *= st.binom.cdf(crit(NEW_N[e], alpha), NEW_N[e], q)
        print(f"Gaussian tails at 03's z, {label}: {tot:.2f}")


if __name__ == "__main__":
    main()
