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


def test_the_shared_world_sd_pairs_worlds_across_graphs():
    """A world effect shared by every graph moves both conditions together and leaves D unchanged (sd near 0); a
    world effect that differs by condition makes D vary across resamples (Astra: heterogeneous world effects)."""
    rng = np.random.default_rng(3)
    G, W = 40, 16
    H = [rng.normal(size=G) for _ in range(3)]
    S = [rng.normal(size=G) for _ in range(3)]
    base = [rng.normal(size=(G, 1)) + rng.normal(0, 0.01, (G, W)) for _ in range(3)]
    shared = rng.normal(size=(1, W))
    same = {"sham": [b + shared for b in base], "relief": [b + shared for b in base]}
    assert P.shared_world_sd_of_mean_D(same, H, S, 200, 0) < 1e-9
    het = {"sham": [b + H[i][:, None] * rng.normal(size=(1, W)) for i, b in enumerate(base)],
           "relief": [b for b in base]}
    assert P.shared_world_sd_of_mean_D(het, H, S, 200, 0) > 0.05


def test_the_quartile_difference():
    H = np.arange(8.0)
    f = np.array([0, 0, 1, 1, 1, 1, 3, 3.0])
    assert P.quartile_difference(H, f) == 3.0


def test_the_projection_follows_the_cut_order():
    t = P.projection_table({64: 200.0, 32: 120.0}, 6.0)  # 65 x 200 s = 3.6 h; with SH 7.2 h
    assert t["plan"] == {"W_t": 64, "SH": False}
    t = P.projection_table({64: 100.0, 32: 60.0}, 6.0)  # 1.8 h; with SH 3.6 h
    assert t["plan"] == {"W_t": 64, "SH": True}
    t = P.projection_table({64: 400.0, 32: 300.0}, 6.0)  # 7.2 h; at 32, 5.4 h
    assert t["plan"] == {"W_t": 32, "SH": False}
    assert P.projection_table({64: 900.0, 32: 800.0}, 6.0)["plan"] is None


def test_b_intervals_follow_heterogeneous_world_effects():
    """B's shared-world intervals (Astra, round 2): a constant shift has no world uncertainty; a world-specific effect
    shared by every graph gives an SE near its SD over sqrt(W); graph-specific offsets do not widen it."""
    rng = np.random.default_rng(3)
    W, G = 400, 3
    base = [rng.normal(1.0, 0.5, (26, W)) for _ in range(G)]
    lv = [b.copy() for b in base]
    flat = P.b_readings({"level": lv, "relief": [b + 0.2 for b in base], "sham": base}, 300, 0)
    assert abs(flat["decile_shift"]["lo"] - 0.2) < 1e-9 and abs(flat["decile_shift"]["hi"] - 0.2) < 1e-9
    assert flat["U_mean_shared_world_se"] < 1e-9
    e = rng.normal(0.0, 0.4, W)  # the same world-specific effect on every graph
    offs = [0.0, 0.3, -0.2]  # and graph-specific offsets
    het = P.b_readings({"level": lv, "relief": [b + 0.2 + o + e for b, o in zip(base, offs)], "sham": base}, 2000, 1)
    want = e.std() / np.sqrt(W)
    assert abs(het["U_mean_shared_world_se"] - want) < 0.15 * want
    assert het["decile_shift"]["lo"] < het["decile_shift"]["mean"] < het["decile_shift"]["hi"]
    assert abs(het["decile_shift"]["mean"] - (0.2 + np.mean(offs) + e.mean())) < 1e-9
