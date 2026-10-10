"""E3d's gate, the choice of k_r, the champions' predictions and the bootstrap (docs/E3/E3d-DESIGN.md v2.2 §4-5).

A block summary: {"conditions": {name: {"role": "blind" | "navigator" | "organism", "strains": [{"visits":
[per maze], "legs": [...], "visited_share": [...]}, ...]}}}, mazes paired across conditions. The gate's names:
"follower_shared", "oracle", "seed".
"""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.e3 import e3d_gate as GT

TH = GT.THRESHOLDS


def _cond(role, *visits, legs=None, visited=None):
    strains = []
    for v in visits:
        v = np.asarray(v, dtype=float)
        strains.append({"visits": v.tolist(), "legs": (np.maximum(v - 1, 0) if legs is None else np.asarray(legs)).tolist(),
                        "visited_share": (np.ones_like(v) if visited is None else np.asarray(visited)).tolist()})
    return {"role": role, "strains": strains}


def _block(follower=8.0, oracle=20.0, seed=4.0, blind=(1.0, 1.5), seed_legs=None, oracle_visited=None):
    n = 4
    c = {"follower_shared": _cond("navigator", [follower] * n), "oracle": _cond("navigator", [oracle] * n, visited=oracle_visited),
         "seed": _cond("organism", [seed] * n, legs=seed_legs),
         "walk": _cond("blind", [blind[0]] * n), "champs_noses": _cond("blind", [blind[1]] * n, [0.5] * n)}
    return {"conditions": c}


def test_a_passing_block():
    g = GT.gate(_block(), TH)
    assert g["verdict"] == "E3d: passed" and g["failed"] == []
    assert g["b_max"] == 1.5 and g["b_max_member"] == "champs_noses#0"
    assert g["precondition"]


@pytest.mark.parametrize("kw, failed", [
    (dict(blind=(2.1, 0.0)), ["G1a", "G1b"]),  # B_max 2.1 > 2.0 and > 0.25 × 8 (the seed's 1.9 margin holds)
    (dict(follower=5.0, oracle=12.0, blind=(1.5, 0.0)), ["G1a"]),  # 1.5 > 0.25 × 5 = 1.25
    (dict(follower=6.0, oracle=19.0), ["G2a"]),  # 6 < 19 / 3
    (dict(follower=3.9, oracle=10.0, blind=(0.9, 0.0)), ["G2b"]),
    (dict(seed=1.9), ["G3a", "G3b"]),  # 1.9 − 1.5 = 0.4 < max(0.5, 0.19); legs 0.9 per maze
])
def test_each_criterion_can_fail(kw, failed):
    g = GT.gate(_block(**kw), TH)
    assert g["failed"] == failed and g["verdict"] == "E3d: failed"


def test_g3b_is_the_median_over_mazes_of_the_colony_mean_legs():
    assert "G3b" not in GT.gate(_block(seed_legs=[1, 1, 3, 3]), TH)["failed"]  # median 2.0 meets ≥ 2
    assert GT.gate(_block(seed_legs=[1, 1, 1.5, 3]), TH)["failed"] == ["G3b"]  # median 1.25
    assert "G3b" not in GT.gate(_block(seed_legs=[0, 2.5, 2.5, 2.5]), TH)["failed"]  # median 2.5; the mean is 1.875


def test_every_strain_of_a_blind_condition_is_a_member():
    b = _block()
    b["conditions"]["champs_noses"] = _cond("blind", [0.2] * 4, [1.8] * 4)
    g = GT.gate(b, TH)
    assert g["b_max_member"] == "champs_noses#1" and g["b_max"] == pytest.approx(1.8)


def test_the_practical_margin_is_the_larger_of_half_a_visit_and_a_tenth():
    assert GT.gate(_block(seed=7.0, blind=(1.5, 0.0), follower=12.0), TH)["criteria"]["G3a"]  # 5.5 ≥ 0.7
    g = GT.gate(_block(seed=1.99, blind=(1.5, 0.0)), TH)  # 0.49 < 0.5
    assert not g["criteria"]["G3a"]
    big = GT.gate(_block(seed=8.0, blind=(1.4, 7.4), follower=40.0, oracle=60.0), TH)  # 0.6 < 0.10 × 8 = 0.8
    assert not big["criteria"]["G3a"]


def test_the_oracle_precondition():
    assert GT.gate(_block(oracle=7.0), TH)["verdict"] == "E3d: not evaluable"  # below the follower's 8
    assert GT.gate(_block(oracle_visited=[1, 1, 1, 0.7]), TH)["verdict"] == "E3d: not evaluable"  # 0.925 < 0.95


def test_choose_the_smallest_qualifying_k_r():
    ok, bad = GT.gate(_block(), TH), GT.gate(_block(blind=(3.0, 0.0)), TH)
    assert GT.choose_k({0: bad, 2: ok, 4: ok}, {0: 0.9, 2: 0.7, 4: 0.6}, 0.5)["k_r"] == 2
    assert GT.choose_k({0: ok, 2: ok, 4: ok}, {0: 0.4, 2: 0.7, 4: 0.6}, 0.5)["k_r"] == 2  # k_r = 0 infeasible
    none = GT.choose_k({0: bad, 2: bad, 4: bad}, {0: 0.9, 2: 0.9, 4: 0.9}, 0.5)
    assert none["k_r"] is None and none["verdict"] == "E3d: failed at calibration"
    assert none["failures"][0] == ["G1a", "G1b"]  # the seed's margin 4 − 3 = 1 still holds


def test_the_champions_predictions_per_arm():
    isl = {"conditions": {"s_mod_intact": _cond("organism", [3.0] * 4, [3.4] * 4),
                          "s_dense_intact": _cond("organism", [1.0] * 4),
                          "p_joint_intact": _cond("organism", [3.6] * 4, [2.4] * 4)}}
    tree = {"conditions": {"s_mod_intact": _cond("organism", [6.0] * 4, [6.0] * 4),
                           "s_dense_intact": _cond("organism", [6.0] * 4),
                           "p_joint_intact": _cond("organism", [5.0] * 4, [5.0] * 4)}}
    p = GT.predictions(isl, tree)
    assert p["s_mod"]["ratio"] == pytest.approx(3.2 / 6.0) and not p["s_mod"]["holds"]  # 0.53 > 0.5
    assert p["s_dense"]["holds"] and p["s_dense"]["ratio"] == pytest.approx(1 / 6)
    assert p["p_joint"]["ratio"] == pytest.approx(0.6) and p["p_joint"]["holds"]  # ≥ 0.5
    assert p["s_mod"]["per_champion"] == pytest.approx([0.5, 3.4 / 6.0])
    tree["conditions"]["s_dense_intact"] = _cond("organism", [0.0] * 4)
    assert GT.predictions(isl, tree)["s_dense"]["per_champion"] == [None]  # no ratio to a zero tree score


def test_the_bootstrap_recomputes_b_max_per_resample():
    b = _block()
    b["conditions"]["walk"] = _cond("blind", [3.0, 0.0, 3.0, 0.0])
    b["conditions"]["champs_noses"] = _cond("blind", [0.0, 2.0, 0.0, 2.0])
    bs = GT.bootstrap(b, resamples=500, seed=20_261_011)
    assert bs["b_max"]["point"] == pytest.approx(1.5)
    lo, hi = bs["b_max"]["interval"]
    assert lo >= 1.0 - 1e-12 and hi <= 3.0
    assert set(bs) >= {"b_max", "follower", "oracle", "seed", "b_max_over_follower", "follower_over_oracle", "seed_minus_b_max"}
