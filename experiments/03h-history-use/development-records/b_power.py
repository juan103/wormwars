"""03h, after the pilot (D336): how much power does B's registered rank test have? Exploratory, CPU only.

B (DESIGN §6, §13): per graph, U = T_sham - T_relief (the selected decile's test-bank means). B passes when at most two
of the 64 SH-mirror-ASK graphs have U at or above N2's (p = 3/65 = 0.046 at most).

The model, from the pilot's committed record (`pilot/pilot.json`):
- the null graphs' U is normal, with the pilot's mean (-0.0077) and between-graph SD (0.0102, from three graphs, so
  two degrees of freedom; the SD is also taken at its 90% chi-square bounds);
- N2's U is read two ways (the review of 2026-10-19, Fable 2, Astra 3):
  - "world noise only": its true value u plus the per-graph shared-world SE (the SE of the three-graph mean times
    sqrt(3), which assumes equal variances and no covariance across graphs; Astra);
  - "graph spread": u plus the nulls' own between-graph SD, as if N2 were one more graph whose idiosyncratic response
    varies like theirs (Fable);
- u is varied: N2 like the nulls (u = mean), N2 gaining half, N2 gaining nothing (u = 0), and N2 doing as much
  better, or twice as much better, under sham than under relief as the nulls do under relief. U > 0 means relief
  under sham's score, not under level's, so it is not "harm" against level (Astra 4).
- These are scenario probabilities for the rank part of B alone, under a normal model fitted to three graphs. They are
  not B's power: B is conjunctive, the tail is extrapolated, and N2 was not in the pilot (Astra 1-3).
- Written after the pilot, exploratory; it changes nothing in B's statistic.

If the pilot's local per-genome arrays are present and match the recorded sha256, the script also reports, per
graph, the relief - sham difference on the selection bank, over all 256 genomes and over the level-selected decile.
Without them, it writes `b-power-without-arrays.json` and leaves the committed `b-power.json` as it is.

    python experiments/03h-history-use/development-records/b_power.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT / "experiments" / "03h-history-use"
SRC = EXP / "pilot" / "pilot.json"
ARRAYS = ROOT / "runs" / "e03h" / "pilot" / "states"
OUT = Path(__file__).with_name("b-power.json")
# without the local arrays the committed record is left alone (the review of RESULTS.md, Fable 7, Astra 8)
OUT_WITHOUT_ARRAYS = Path(__file__).with_name("b-power-without-arrays.json")
N_NULL, MAX_ABOVE, SIMS, SEED = 64, 2, 200_000, 3_670_000


def pass_rate(mu: float, sd: float, u: float, se: float, rng) -> float:
    nulls = rng.normal(mu, sd, (SIMS, N_NULL))
    n2 = rng.normal(u, se, (SIMS, 1))
    return float(((nulls >= n2).sum(1) <= MAX_ABOVE).mean())


def u_for_power(mu: float, sd: float, se: float, target: float = 0.8) -> float:
    """The smallest u (on a 0.0005 grid) at which B passes with the target probability."""
    rng = np.random.default_rng(SEED + 1)
    for u in np.arange(mu, mu + 12 * sd, 0.0005):
        if pass_rate(mu, sd, float(u), se, rng) >= target:
            return float(u)
    return float("nan")


def selection_bank(rec: dict) -> dict | None:
    path = ARRAYS / rec["arrays_npz"]
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != rec["arrays_npz_sha256"]:
        return None
    out = {}
    with np.load(path, allow_pickle=False) as z:
        for row in rec["per_graph"]:
            n = row["name"]
            diff = (z[f"{n}::selection_relief"] - z[f"{n}::selection_sham"]).mean(1)
            top = z[f"{n}::decile_level"]
            out[n] = {"all_genomes_mean": float(diff.mean()), "all_genomes_sd": float(diff.std(ddof=1)),
                      "level_decile_mean": float(diff[top].mean()),
                      "decile_overlap_relief_sham": len(set(z[f"{n}::decile_relief"].tolist())
                                                        & set(z[f"{n}::decile_sham"].tolist()))}
    return {"arrays_sha256": rec["arrays_npz_sha256"], "per_graph": out}


def main() -> dict:
    rec = json.loads(SRC.read_text(encoding="utf-8"))
    B = rec["readings"]["B"]
    U = np.array(B["U"])
    mu, sd = float(U.mean()), float(B["U_between_graph_sd"])
    se = float(B["U_mean_shared_world_se"]) * np.sqrt(len(U))
    df = len(U) - 1
    sds = {"point": sd,
           "lower_90": sd * np.sqrt(df / stats.chi2.ppf(0.95, df)),
           "upper_90": sd * np.sqrt(df / stats.chi2.ppf(0.05, df))}
    us = {"N2 like the nulls": mu, "N2 gains half": mu / 2, "N2 gains nothing": 0.0,
          "N2 better under sham by the nulls' gain": -mu, "N2 better under sham by twice the nulls' gain": -2 * mu}
    rng = np.random.default_rng(SEED)
    table = {"world_noise_only": {k: {name: pass_rate(mu, s, u, se, rng) for name, u in us.items()}
                                  for k, s in sds.items()},
             "graph_spread": {k: {name: pass_rate(mu, s, u, s, rng) for name, u in us.items()}
                              for k, s in sds.items()}}
    needed = {"world_noise_only": {k: u_for_power(mu, s, se) for k, s in sds.items()},
              "graph_spread": {k: u_for_power(mu, s, s) for k, s in sds.items()}}
    out = {"source": str(SRC.relative_to(ROOT)).replace("\\", "/"), "source_sha256":
           hashlib.sha256(SRC.read_bytes()).hexdigest(),
           "model": {"null_mean_U": mu, "null_sd_U": sds, "n2_se": se, "n_null": N_NULL, "max_above": MAX_ABOVE,
                     "sims": SIMS, "seed": SEED},
           "u": us, "pass_rate": table, "u_for_80pct_power": needed,
           "decile_shift_mean": rec["readings"]["manipulation"]["decile_shift"]["mean"],
           "selection_bank_relief_minus_sham": selection_bank(rec)}
    target = OUT if out["selection_bank_relief_minus_sham"] is not None else OUT_WITHOUT_ARRAYS
    target.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
