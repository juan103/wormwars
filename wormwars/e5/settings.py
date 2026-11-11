"""E5-1's settings, training mixture, suite and score (docs/E5/E5-1-DESIGN.md §3).

- `e5_0_settings`: E5-0's 18 read settings, as `scripts/e5_0.py` defines them (a test checks the equality).
- `TRAINING`: the 8 training slots, in slot order; `TRAINING_WEIGHTS`: the selection fitness's weights in thirtieths,
  (1/3)[c1 + (c2 + ... + c6)/5 + (c7 + c8)/2] = (10 c1 + 2 (c2 + ... + c6) + 5 (c7 + c8)) / 30. Integer weights keep
  equal fitnesses exactly equal, so ties are broken as the GA always broke them.
- `SUITE`: the 17 held-out suite settings in §3's order (trained settings first, then the held-out speeds), which fixes
  the suite's world ids; `STRATA`; `suite_score`, the mean of the three strata.
- `prey_params`: the prey's parameters from E5-0's committed records (the route's gain and spacing and E_prey from
  `calibration.json`, the wall follower's from E1's `freeze.json`).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
E5_0 = ROOT / "experiments" / "E5-hunter" / "E5-0"
E1_FREEZE = ROOT / "experiments" / "E1-navigation" / "freeze.json"

SPEEDS_H2 = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
SPEEDS_H2B = (0.25, 0.5, 0.75)
ROUTE_REACH = 1.0  # E5-0's registered waypoint reach
WALK = {"rate": 0.4, "persistence": 0.9}  # E5-0's registered random walk


def e5_0_settings() -> list[dict]:
    S = [{"name": "H1-ghost", "rule": "ghost", "prey": "stationary", "speed": 0.0, "pinned": True},
         {"name": "H1-reach", "rule": "reach", "prey": "stationary", "speed": 0.0, "pinned": True},
         {"name": "H1-bite", "rule": "bite", "prey": "stationary", "speed": 0.0, "pinned": True}]
    for s in SPEEDS_H2:
        S.append({"name": f"H2-{s:g}", "rule": "bite", "prey": "route", "speed": s, "pinned": False})
    for kind, label in (("random_walk", "walk"), ("wall_follower", "wall")):
        for s in SPEEDS_H2B:
            S.append({"name": f"H2b-{label}-{s:g}", "rule": "bite", "prey": kind, "speed": s, "pinned": False})
    return S


BY_NAME = {s["name"]: s for s in e5_0_settings()}

TRAINING = ("H1-bite", "H2-0.2", "H2-0.4", "H2-0.6", "H2-0.8", "H2-1", "H2b-walk-0.5", "H2b-wall-0.5")
TRAINING_WEIGHTS = (10, 2, 2, 2, 2, 2, 5, 5)  # thirtieths
SUITE = TRAINING + ("H2-0.1", "H2-0.3", "H2-0.5", "H2-0.7", "H2-0.9", "H2b-walk-0.25", "H2b-walk-0.75",
                    "H2b-wall-0.25", "H2b-wall-0.75")
HELD_OUT = SUITE[len(TRAINING):]
PROBE_SETTINGS = ("H1-bite", "H2-0.5", "H2-1", "H2b-walk-0.5")
BRIDGES = ("H1-ghost", "H1-reach")


def stratum(name: str) -> str:
    s = BY_NAME[name]
    return {"stationary": "static", "route": "route"}.get(s["prey"], "movers")


STRATA = {k: tuple(n for n in SUITE if stratum(n) == k) for k in ("static", "route", "movers")}


def weighted_fitness(counts: np.ndarray, weights=TRAINING_WEIGHTS) -> np.ndarray:
    """[strains]: the weighted mean of [strains, slots] counts, (counts @ weights) / sum(weights). The weights are
    integers, so the numerator is exact."""
    w = np.asarray(weights, dtype=np.int64)
    c = np.asarray(counts, dtype=np.float64)
    if c.shape[-1] != w.size:
        raise ValueError(f"{c.shape[-1]} columns for {w.size} weights")
    return (c @ w.astype(np.float64)) / float(w.sum())


def column_weights(slots: np.ndarray) -> np.ndarray:
    """Integer weights per column for columns holding training slots (validation: 32 columns per slot)."""
    slots = np.asarray(slots, dtype=np.int64)
    counts = np.bincount(slots, minlength=len(TRAINING))
    if len(set(counts.tolist())) != 1:
        raise ValueError("every training slot needs the same number of columns for the score's weights")
    return np.asarray(TRAINING_WEIGHTS, dtype=np.int64)[slots]


def suite_score(means: dict) -> float:
    """The mean of the three strata: static (H1-bite), route (the mean over the 10 route speeds), movers (the mean over
    the 6 H2b settings). `means` maps every suite setting to a genome's mean captures per episode."""
    missing = [n for n in SUITE if n not in means]
    if missing:
        raise ValueError(f"the suite score needs every suite setting: missing {missing}")
    vals = [float(np.mean([float(means[n]) for n in STRATA[k]])) for k in ("static", "route", "movers")]
    if not all(np.isfinite(vals)):
        raise ValueError("non-finite mean in the suite score")
    return float(np.mean(vals))


def _read(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def prey_params() -> dict:
    """The prey's parameters, from E5-0's committed calibration and E1's frozen wall follower."""
    cal = _read(E5_0 / "calibration.json")
    if not cal.get("complete"):
        raise SystemExit("E5-0's calibration record is not complete")
    wf = _read(E1_FREEZE)["tuned"]["wall-follower"]["params"]
    return {"route": {"gain": float(cal["route"]["gain"]), "spacing": float(cal["route"]["spacing"]),
                      "reach": ROUTE_REACH},
            "walk": dict(WALK), "wall": {k: float(wf[k]) for k in ("seek_turn", "avoid_turn", "threshold")},
            "e_prey": float(cal["e_prey"]["e_prey"])}
