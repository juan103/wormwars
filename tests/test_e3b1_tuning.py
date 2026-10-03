"""E3b-1's tuning pieces and registered statistics (experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md §3, §7;
§12 tests 1, 6, 9 and 10)."""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
import torch
from scipy import stats

from wormwars.brain import BrainSpec
from wormwars.connectome import load_connectome
from wormwars.e3 import maze_organisms as MO
from wormwars.e3 import organism as O
from wormwars.e3 import tuning as T
from wormwars.e3.task import shuttle_config
from wormwars.e4s import arms as A
from wormwars.e4s import comparator as C


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def l1():
    return A.load_l1()


@pytest.fixture(scope="module")
def seed_org(con, l1):
    return T.start_organism("seed", con, l1, shuttle_config().brain)


# ------------------------------------------------------------------ test 1: the mutation mask

def test_the_mask_freezes_w2_the_relays_and_the_worm(seed_org):
    ext = seed_org.ext
    sc = T.scales(ext)
    spec = BrainSpec.from_connectome(ext)
    n0 = int(ext.meta["worm_neurons"])
    w2 = {ext.index("E3B_WL"), ext.index("E3B_WR")}
    for p, (i, j) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist())):
        grafted = i >= n0 or j >= n0
        want = 0.25 if grafted and i not in w2 else 0.0
        assert float(sc["w"][p]) == want, (ext.names[i], ext.names[j])
    for k in range(spec.n):
        frozen = k < n0 or k in w2 or ext.names[k] in O.RELAYS
        assert float(sc["tau"][k]) == (0.0 if frozen else 0.25) and float(sc["bias"][k]) == float(sc["tau"][k])
    assert float(sc["g"].abs().max()) == 0.0
    w2_edges = sum(1 for i in spec.chem_i.tolist() if i in w2)
    assert w2_edges == 16


def test_the_end_of_run_assertion_catches_a_changed_frozen_parameter(seed_org):
    g = seed_org.genome
    T.assert_frozen(g, g, seed_org.ext)
    spec = BrainSpec.from_connectome(seed_org.ext)
    k = next(p for p, i in enumerate(spec.chem_i.tolist()) if i == seed_org.ext.index("E3B_WL"))
    w = g.w.clone()
    w[0, k] += 0.01
    with pytest.raises(AssertionError, match="frozen"):
        T.assert_frozen(g, g.with_params(w=w), seed_org.ext)
    bias = g.bias.clone()
    bias[0, seed_org.ext.index("E3_RA")] += 0.01
    with pytest.raises(AssertionError, match="frozen"):
        T.assert_frozen(g, g.with_params(bias=bias), seed_org.ext)
    # a mutable parameter may change
    m = next(p for p, (i, j) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist()))
             if seed_org.ext.names[i] == "E3_A_CL" and seed_org.ext.names[j] == "SMDDL")
    w = g.w.clone()
    w[0, m] += 0.01
    T.assert_frozen(g, g.with_params(w=w), seed_org.ext)


# ------------------------------------------------------------------ test 6: the degraded start

def test_the_degraded_start_zeroes_the_gate_on_es_mask_with_w2_as_in_the_seed(con, l1, seed_org):
    deg = T.start_organism("degraded", con, l1, shuttle_config().brain)
    assert deg.ext.names == seed_org.ext.names  # E's mask, the same organism layout
    e_s, e_d = MO.named_edges(seed_org.genome, seed_org.ext), MO.named_edges(deg.genome, deg.ext)
    for comp in ("E3_A_CL", "E3_A_CR", "E3_B_CL", "E3_B_CR"):
        assert e_d[(O.Q, comp)] == 0.0 and e_s[(O.Q, comp)] != 0.0
        assert float(deg.genome.bias[0, deg.ext.index(comp)]) == 0.0
    for key, val in e_s.items():
        if key[0] in ("E3B_WL", "E3B_WR"):
            assert e_d[key] == val
    for name in ("E3B_WL", "E3B_WR"):
        k = deg.ext.index(name)
        assert float(deg.genome.bias[0, k]) == float(seed_org.genome.bias[0, k])
    assert torch.equal(deg.genome.bias[0, :302], seed_org.genome.bias[0, :302])  # the same carrier


# ------------------------------------------------------------------ test 9: the gate's statistic

def _welch_by_hand(a, b):
    va, vb = np.var(a, ddof=1) / len(a), np.var(b, ddof=1) / len(b)
    est = (np.mean(a) + np.mean(b)) / 2
    se = math.sqrt(va + vb) / 2
    nu = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    return est, se, nu, stats.t.sf(est / se, nu)


def test_the_gate_matches_a_hand_computation_with_unequal_spreads_and_n():
    rng = np.random.default_rng(3)
    a, b = rng.normal(0.2, 0.1, 8), rng.normal(0.1, 0.4, 6)
    est, se, nu, p = _welch_by_hand(a, b)
    g = T.gate(a, b)
    assert g["estimate"] == pytest.approx(est) and g["se"] == pytest.approx(se) and g["df"] == pytest.approx(nu)
    assert g["p_greater"] == pytest.approx(p) and g["p_less"] == pytest.approx(stats.t.cdf(est / se, nu))
    assert g["lower_bound_95"] == pytest.approx(est - stats.t.ppf(0.95, nu) * se)


def test_the_gate_reaches_every_label():
    assert T.gate(np.full(8, 0.5) + np.linspace(0, 0.1, 8), np.full(8, 0.4) + np.linspace(0, 0.1, 8))["label"] == "better"
    assert T.gate(-np.full(8, 0.5) + np.linspace(0, 0.1, 8), -np.full(8, 0.4) + np.linspace(0, 0.1, 8))["label"] == "worse"
    assert T.gate(np.array([0.3, -0.3] * 4), np.array([0.2, -0.2] * 4))["label"] == "unclear"


def test_zero_spread_gives_directional_p_and_a_point_interval():
    g = T.gate(np.full(8, 0.2), np.full(8, 0.2))
    assert g["se"] == 0 and g["p_greater"] == 0.0 and g["p_less"] == 1.0 and g["label"] == "better"
    assert g["lower_bound_95"] == pytest.approx(0.2)
    z = T.gate(np.zeros(8), np.zeros(8))
    assert z["label"] == "unclear" and z["p_greater"] == 1.0 and z["p_less"] == 1.0


def test_the_gate_is_not_read_below_4_runs_per_schedule():
    assert T.gate(np.ones(3) * 0.2 + [0, 0.1, 0.2], np.ones(8))["label"] == "not read"


def test_better_but_concentrated_when_fewer_than_half_reach_2_legs():
    d = np.full(8, 0.5) + np.linspace(0, 0.1, 8)
    legs = np.array([1.0] * 9 + [3.0] * 7)  # 7 of 16 reach 2
    assert T.gate(d, d, legs_medians=legs)["label"] == "better, but concentrated"
    legs = np.array([1.0] * 8 + [3.0] * 8)  # 8 of 16, half rounded up: enough
    assert T.gate(d, d, legs_medians=legs)["label"] == "better"
    legs15 = np.array([1.0] * 7 + [3.0] * 8)  # 15 read: 8 needed
    assert T.gate(d[:7], d, legs_medians=legs15)["label"] == "better"
    legs15_short = np.array([1.0] * 8 + [3.0] * 7)  # 15 read, 7 reach: half of 15 rounded up is 8
    assert T.gate(d[:7], d, legs_medians=legs15_short)["label"] == "better, but concentrated"


def test_the_stratified_sign_flip_uses_the_estimand():
    a, b = np.array([0.3, 0.1, 0.2, 0.4]), np.array([0.5, -0.1, 0.2, 0.0, 0.3])
    obs = (a.mean() + b.mean()) / 2
    count = 0
    pats = list(itertools.product((1, -1), repeat=9))
    for s in pats:
        s = np.array(s)
        count += (a * s[:4]).mean() / 2 + (b * s[4:]).mean() / 2 >= obs - 1e-12
    assert T.sign_flip(a, b) == pytest.approx(count / len(pats))


# ------------------------------------------------------------------ test 10: the secondary tests and Holm

def test_the_paired_secondary_and_its_direction():
    late, early = np.array([5.0, 6, 7, 8]), np.array([4.0, 5.5, 6, 7.5])
    r = T.paired(late - early)
    assert r["p"] == pytest.approx(stats.ttest_1samp(late - early, 0, alternative="greater").pvalue)
    assert T.paired(np.zeros(4))["p"] == 1.0 and T.paired(np.full(4, 0.1))["p"] == 0.0
    assert T.paired(np.ones(3))["label"] == "not read"


def test_s_peer_tests_less_than_zero():
    a, b = -np.linspace(0.1, 0.4, 8), -np.linspace(0.2, 0.3, 8)
    r = T.gate(a, b, alternative="less")
    assert r["p"] == r["p_less"] and r["p"] < 0.05


def test_holm_keeps_three_with_an_unread_test_at_one():
    adj = T.holm({"S-gen": 0.01, "S-trail": None, "S-peer": 0.03})
    assert adj["S-gen"]["p_holm"] == pytest.approx(0.03) and adj["S-gen"]["rejected"]
    assert adj["S-peer"]["p_holm"] == pytest.approx(0.06) and not adj["S-peer"]["rejected"]
    assert adj["S-trail"]["p_holm"] == 1.0 and adj["S-trail"]["read"] is False


def test_a_zero_denominator_is_not_read():
    assert T.normalised(np.array([1.0, 2.0]), 0.0) is None
    assert np.allclose(T.normalised(np.array([1.0, 2.0]), 2.0), [0.5, 1.0])


def test_the_paired_secondary_gives_its_one_sided_bound():
    d = np.array([0.1, 0.2, 0.15, 0.05])
    r = T.paired(d)
    se = d.std(ddof=1) / 2
    assert r["lower_bound_95"] == pytest.approx(d.mean() - stats.t.ppf(0.95, 3) * se)
    assert T.paired(np.full(4, 0.1))["lower_bound_95"] == pytest.approx(0.1)
