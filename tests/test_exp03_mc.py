"""03mc's statistics and rules (`wormwars/exp03/mc.py`, experiments/03mc-p4-confirm/DESIGN.md §4, §6)."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import norm

from wormwars.exp03 import mc


def test_rank_p_counts_ties_against_n2_in_the_registered_direction():
    vals = np.array([0.1, 0.2, 0.2, 0.5])
    # Q-A: graphs whose change is as small as N2's or smaller
    r = mc.rank_p(vals, 0.2, at_or_below=True)
    assert (r["r"], r["n"]) == (3, 4) and r["p"] == pytest.approx(4 / 5)
    # Q-D, Q-C: graphs as large as N2 or larger
    r = mc.rank_p(vals, 0.2, at_or_below=False)
    assert (r["r"], r["n"]) == (3, 4) and r["p"] == pytest.approx(4 / 5)
    assert mc.rank_p(vals, 0.6, at_or_below=False)["p"] == pytest.approx(1 / 5)


def test_rank_p_drops_invalid_values_from_n():
    r = mc.rank_p(np.array([0.1, np.nan, 0.9, np.inf]), 0.5, at_or_below=False)
    assert (r["r"], r["n"], r["invalid"]) == (1, 2, 2)


def test_intersection_union_takes_the_largest_p_and_needs_every_ensemble():
    per = {"SH": {"p": 0.01}, "SH-route": {"p": 0.04}, "SH-class": {"p": 0.008}, "SH-mirror": {"p": 0.02},
           "SH-recip": {"p": 0.03}}
    assert mc.intersection_union(per) == pytest.approx(0.04)
    del per["SH-recip"]
    assert mc.intersection_union(per) == 1.0  # a missing ensemble cannot pass


def test_holm_passes_in_order_and_stops_at_the_first_failure():
    out = mc.holm({"A": 0.02, "B": 0.001, "C": 0.004, "D": 0.03})
    # sorted: B 0.001 <= .0125, C 0.004 <= .0167, A 0.02 <= .025, D 0.03 <= .05
    assert all(out[q]["passed"] for q in "ABCD")
    out = mc.holm({"A": 0.026, "B": 0.001, "C": 0.004, "D": 0.03})
    assert out["B"]["passed"] and out["C"]["passed"]
    assert not out["A"]["passed"] and not out["D"]["passed"]  # A fails at .025, so D is not tested
    assert out["D"]["alone_at_alpha"]  # 0.03 alone would pass: the "Holm stops" wording applies


def test_holm_keeps_four_members_when_one_is_missing():
    out = mc.holm({"A": 0.011, "B": None, "C": 0.004, "D": 0.016})
    assert out["B"]["p"] == 1.0 and not out["B"]["passed"]
    # with four members: C .004 <= .0125, A .011 <= .0167, D .016 <= .025
    assert out["A"]["passed"] and out["D"]["passed"]
    out3 = mc.holm({"A": 0.014, "B": None, "C": 0.004, "D": 0.016})
    assert out3["A"]["passed"]  # .014 <= .0167


def test_paired_bootstrap_uses_the_same_genomes_for_both_conditions():
    rng = np.random.default_rng(0)
    n = 4000
    s_int = np.abs(rng.normal(1.0, 0.3, n))
    f_int = 0.9 * s_int * np.abs(rng.normal(1.0, 0.1, n))
    s_del, f_del = 0.5 * s_int, 0.5 * f_int  # an exact halving: the cut is 0.5 in every resample, dP4 is 0
    b = mc.paired_bootstrap(f_int, s_int, f_del, s_del, resamples=500, seed=1)
    assert b["cut"] == pytest.approx(0.5) and b["cut_se"] == pytest.approx(0.0, abs=1e-12)
    assert b["dP4"] == pytest.approx(0.0, abs=1e-12) and b["dP4_se"] == pytest.approx(0.0, abs=1e-12)
    assert b["dropped"] == 0


def test_paired_bootstrap_se_shrinks_with_pairing():
    """A sabotage check of the pairing: independent resampling of the two conditions would give a much larger
    SE for a deletion that scales every genome alike."""
    rng = np.random.default_rng(2)
    n = 3000
    s = np.abs(rng.standard_cauchy(n)) + 0.1
    f = 0.9 * s
    b = mc.paired_bootstrap(f, s, 0.6 * f * (1 + 0.01 * rng.normal(size=n)), 0.6 * s, resamples=300, seed=3)
    assert b["cut_se"] < 1e-9 and b["dP4_se"] < 0.01


def test_qb_tests_are_the_registered_normal_theory_tests():
    t = mc.qb_tests(cut=0.55, cut_se=0.01, dP4=0.004, dP4_se=0.003)
    assert t["p_cut"] == pytest.approx(norm.sf((0.55 - 0.40) / 0.01))
    assert t["p_eq"] == pytest.approx(max(norm.sf((0.004 + 0.02) / 0.003), norm.sf((0.02 - 0.004) / 0.003)))
    assert t["p"] == max(t["p_cut"], t["p_eq"])
    assert mc.qb_tests(cut=0.55, cut_se=0.0, dP4=0.0, dP4_se=0.0)["p"] == 0.0  # degenerate SE: a sure pass
    assert mc.qb_tests(cut=0.35, cut_se=0.0, dP4=0.0, dP4_se=0.0)["p"] == 1.0


def test_matched_controls_are_the_four_nearest_in_total_degree_ties_alphabetical():
    deg = {"A": 100, "B": 90, "C": 110, "D": 105, "E": 95, "F": 300, "T": 99}
    total = {k: v for k, v in deg.items()}
    got = mc.matched_controls(total, targets=["A"], exclude={"T"}, k=4)
    # distances from 100: D 5, E 5, B 10, C 10, F 200 (T excluded); ties alphabetical
    assert got["A"] == ["D", "E", "B", "C"]


def test_the_design_s_matched_controls_come_from_the_connectome():
    """DESIGN §4 Q-B names the controls; the code derives them and must agree."""
    from wormwars.connectome import load_connectome
    deg = mc.pair_total_degrees(load_connectome())
    assert deg["RIA"] == 135 and deg["AIY"] == 58
    got = mc.matched_controls(deg, targets=["RIA", "AIY"], exclude={"RMDD", "RMDV", "SMDD", "SMDV"}, k=4)
    assert got == {"RIA": ["AIB", "AVJ", "RIM", "AVH"], "AIY": ["AWB", "RIF", "RIP", "RIV"]}


def test_the_freshness_audit_passes_disjoint_plans_and_names_every_collision():
    old = {"": ["N2", "SH-10000"], "03r:": ["N2", "SH-1010000"]}
    new = {"03mc:": ["N2", "SH-2010000", "N2#1"]}
    a = mc.freshness_audit(new, old, new_perm_seeds=[1000, 1001], old_perm_seeds=[1, 100])
    assert a["ok"], a
    # a planted collision: the new plan reuses 03r's salt for one name (the sabotage check)
    bad = mc.freshness_audit({"03mc:": ["N2"], "03r:": ["SH-2010000"]}, old, [1000], [1])
    assert not bad["ok"] and bad["genome_seed_collisions_with_old"] == []  # different names: no seed clash
    clash = mc.freshness_audit({"03r:": ["N2"]}, old, [1000], [1])
    assert not clash["ok"] and clash["genome_seed_collisions_with_old"]
    # the permutation generator is seeded with 2 * seed + type (brain._apply_magnitude_mode): 1000 hits 2000 and
    # 2001, so an old seed of 1000 collides, and so would any old seed mapping to the same generator seed
    perm = mc.freshness_audit(new, old, [1000], [1000])
    assert not perm["ok"] and perm["permutation_collisions"] == [1000]


def test_a_new_name_list_with_a_repeat_is_refused():
    a = mc.freshness_audit({"03mc:": ["N2", "N2"]}, {}, [1000], [])
    assert not a["ok"] and a["repeated_new_seeds"]


def test_the_content_check_names_duplicates_within_and_against_old():
    c = mc.content_check({"a": "h1", "b": "h2", "c": "h1"}, old_hashes={"h2"})
    assert not c["ok"] and c["within_new"] == [["a", "c"]] and c["against_old"] == ["b"]
    assert mc.content_check({"a": "h1"}, {"h2"})["ok"]
