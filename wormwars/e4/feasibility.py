"""E4-D's feasibility rules (docs/E4/E4-D-DESIGN.md v2.1 §2, §4), fixed before anything is played.

- `readout`: real-first, decoy-first and "neither" counts and shares, over all trials and over entries (undefined,
  None, when nothing was entered).
- `choose_sigma`: the smallest σ in the list at which the oracle's real-first share over all trials and X0's entry
  rate both reach 0.75; None if none does.
- `choose_control`: the highest real-first share over all trials; ties to the smaller w, then comparator-origin.
- `per_maze`, `maze_bound`: per maze the mean of its two trials' real-first indicators (trials ordered maze-major,
  assignment 0 then 1), and the one-sided 95% percentile bootstrap lower bound over mazes.
- `reversal_ok`: the control's decoy-first count under cue reversal equals its real-first count without it (a mapping
  check).
- `verdict`: success needs every criterion of §4.
"""

from __future__ import annotations

import numpy as np

SIGMAS = (3.0, 6.0, 9.0, 12.0)
WIRINGS = ("comparator", "nose")
WEIGHTS = (0.5, 1.0, 2.0, 3.0)
LEVEL = 0.75
BOOT_SEED, BOOT_RESAMPLES = 20_261_013, 10_000


def _flat(ev):
    fc = np.asarray(ev["first_candidate"]).reshape(-1)
    real = np.asarray(ev["assign"]).reshape(-1)
    return fc, real


def readout(ev) -> dict:
    fc, real = _flat(ev)
    n = len(fc)
    entered = fc >= 0
    rf = int((entered & (fc == real)).sum())
    df = int((entered & (fc != real)).sum())
    e = int(entered.sum())
    return {"trials": n, "entries": e, "real_first": rf, "decoy_first": df, "neither": n - e,
            "real_first_all": rf / n if n else None, "entry_rate": e / n if n else None,
            "real_first_entries": rf / e if e else None}


def choose_sigma(scout: dict):
    for s in sorted(scout):
        r = scout[s]
        if r["oracle_real_first_all"] >= LEVEL and r["x0_entry_rate"] >= LEVEL:
            return s
    return None


def choose_control(results: dict):
    """`results`: {(wiring, w): real-first share over all trials}."""
    return max(results, key=lambda k: (results[k], -k[1], k[0] == "comparator"))


def per_maze(ev, n_mazes: int) -> np.ndarray:
    fc, real = _flat(ev)
    hit = ((fc >= 0) & (fc == real)).astype(np.float64)
    return hit.reshape(n_mazes, 2).mean(axis=1)


def maze_bound(per_maze_means: np.ndarray, *, seed: int = BOOT_SEED, resamples: int = BOOT_RESAMPLES) -> float:
    x = np.asarray(per_maze_means, dtype=np.float64)
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, len(x), size=(resamples, len(x)))].mean(axis=1)
    return float(np.quantile(means, 0.05))


def reversal_ok(normal, reversed_) -> bool:
    return readout(reversed_)["decoy_first"] == readout(normal)["real_first"]


def verdict(r: dict) -> dict:
    checks = {"control_real_first_all": r["control"]["real_first_all"] >= LEVEL,
              "control_bound_above_half": r["control_bound"] > 0.5,
              "x0_invariant": bool(r["x0_invariant"]), "reversal_mapping": bool(r["reversal_ok"]),
              "fixed_cue_invariant": bool(r["fixed_cue_invariant"]),
              "removal_identical_to_x0": bool(r["removal_identical"])}
    return {"passed": all(checks.values()), "checks": checks}
