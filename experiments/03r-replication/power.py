"""Posterior-predictive probability that 03r passes its rank gates (pre-registration §7), from
03's P4 ensemble counts. Not the power of the whole registered procedure: the margin gate,
exclusions and completeness are not simulated, and the "03's rule" column uses alpha/3, which is
P4's Holm threshold only when P4 has the smallest p of the three signals (true in 03).

For each ensemble, the probability that one fresh graph is at or above N2's measured value gets
a posterior from 03's count, Beta(r + a, n - r + a): Jeffreys (a = 1/2) or uniform (a = 1).
Fresh ensembles of 03r's sizes are drawn from it. The tails are assumed to be as 03 sampled
them. With `noise`, N2's fresh measurement is drawn around the stated value with 03's SE
(0.006), and the counts are taken at that draw (Astra, D060).

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


def power(p4: dict, n2: float, alpha: float, rng, prior: float = 0.5, noise: float = 0.0) -> float:
    draws = n2 + noise * rng.standard_normal(SIMS) if noise else np.full(SIMS, n2)
    ok = np.ones(SIMS, bool)
    for e, d in p4.items():
        v = np.sort(np.asarray(d["values"]))
        n = len(v)
        k = n - np.searchsorted(v, draws, side="left")  # graphs at or above each N2 draw
        q = rng.beta(k + prior, n - k + prior)
        ok &= rng.binomial(NEW_N[e], q) <= crit(NEW_N[e], alpha)
    return float(ok.mean())


def main() -> None:
    p4 = json.loads((ROOT / "experiments" / "03-generation0" / "report.json").read_text(encoding="utf-8"))["signals"]["P4"]
    rng = np.random.default_rng(0)
    print("critical counts, P4 alone:", {e: crit(n, 0.05) for e, n in NEW_N.items()},
          "03's rule:", {e: crit(n, 0.05 / 3) for e, n in NEW_N.items()})
    for n2 in (0.9309, 0.925, 0.915, 0.905):
        print(f"N2 = {n2}: Jeffreys: P4 alone {power(p4, n2, 0.05, rng):.2f}, 03's rule {power(p4, n2, 0.05 / 3, rng):.2f}"
              f" | uniform prior: {power(p4, n2, 0.05, rng, prior=1.0):.2f}, {power(p4, n2, 0.05 / 3, rng, prior=1.0):.2f}"
              f" | with N2 noise (SE 0.006): {power(p4, n2, 0.05, rng, noise=0.006):.2f},"
              f" {power(p4, n2, 0.05 / 3, rng, noise=0.006):.2f}")
    for alpha, label in ((0.05, "P4 alone"), (0.05 / 3, "03's rule")):
        tot = 1.0
        for e, d in p4.items():
            q = 1 - st.norm.cdf((d["n2"] - d["ensemble_mean"]) / d["ensemble_latent_sd"])
            tot *= st.binom.cdf(crit(NEW_N[e], alpha), NEW_N[e], q)
        print(f"Gaussian tails at 03's z, {label}: {tot:.2f}")


if __name__ == "__main__":
    main()
