"""03h's pilot readings (wormwars/e03h/pilot.py; PILOT.md §5): reliability matches the committed record's estimator;
the decile breaks ties by index; the power formula; B's U, the decile shift and its rule."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from wormwars.e03h import pilot as P

ROOT = Path(__file__).resolve().parents[1]


def test_reliability_is_the_committed_estimator():
    d = json.loads((ROOT / "experiments" / "03-generation0" / "pilot.json").read_text(encoding="utf-8"))
    rec = json.loads((ROOT / "experiments" / "03h-history-use" / "development-records" / "t1-generation0.json")
                     .read_text(encoding="utf-8"))
    g = d["graphs"][0]
    r = P.crossed_reliability(np.asarray(g["fitness"]["T1-M0"]), 16)
    assert abs(r - rec["per_graph"][g["name"]]["ranking_reliability"]["16"]) < 1e-12


def test_the_decile_breaks_ties_by_index():
    m = np.array([1.0, 3.0, 3.0, 2.0, 3.0])
    assert P.select_decile(m, 3).tolist() == [1, 2, 4]
    assert P.select_decile(m, 4).tolist() == [1, 2, 4, 3]


def test_the_power_formula():
    p = P.power(0.06, 0.0)
    assert abs(p["se"] - 0.06 / 8) < 1e-12 and p["power"] > 0.999
    q = P.power(0.06, 0.05)
    assert abs(q["se"] - np.sqrt(0.06 ** 2 / 64 + 0.05 ** 2)) < 1e-12 and q["power"] < 0.6


def test_b_readings_and_the_shift_rule():
    rng = np.random.default_rng(0)
    base = [rng.normal(1.0, 0.2, (26, 64)) for _ in range(3)]
    test = {"level": base, "sham": [b + 0.0 for b in base], "relief": [b + 0.2 for b in base]}
    r = P.b_readings(test, 500, 1)
    assert r["decile_shift"]["moves"] and abs(r["decile_shift"]["mean"] - 0.2) < 1e-9
    assert all(abs(u + 0.2) < 1e-9 for u in r["U"])
    worse = {"level": base, "sham": base, "relief": [b - 0.2 for b in base]}
    assert not P.b_readings(worse, 500, 1)["decile_shift"]["moves"]
