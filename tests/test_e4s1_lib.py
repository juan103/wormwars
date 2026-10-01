"""E4s-1's building blocks (`wormwars/e4s/arms.py`, `wormwars/e4s/readings.py`), against the bound
pre-registration (`experiments/E4s-stereo-module/E4s-1/PREREGISTRATION.md`, D150): the frozen module and
its registration, the arms' mutation masks, R's sign draws, N's construction, the Mc transplant, reset
and rescue, and the registered outcome rules."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars import graft as G
from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e4s import arms as A
from wormwars.e4s import comparator as C
from wormwars.e4s import readings as RD


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def l1():
    return A.load_l1()


def test_l1_loads_from_its_file_with_its_hash_and_is_registered(l1):
    assert l1.name == "comparator-L1" and len(l1.synapses) == 20
    assert all(abs(w) == 3.0 for _, _, w in l1.synapses)
    assert G.MODULES["comparator-L1"] is l1 or G.MODULES["comparator-L1"] == l1
    with pytest.raises(SystemExit):
        A.load_l1(expected_sha256="0" * 64)


def test_arm_scales_give_every_factor(con, l1):
    ext = G.graft_connectome(con, l1)
    spec = BrainSpec.from_connectome(ext)
    n0 = con.n
    module_edge = (spec.chem_i >= n0) | (spec.chem_j >= n0)
    out = A.output_edge_mask(ext, l1)
    assert int(out.sum()) == 16 and bool((out <= module_edge).all())
    for arm, f in (("M", 0.25), ("R", 0.25), ("U", 1.0), ("S", 0.125), ("C2", 0.25)):
        s = A.arm_scales(ext, l1, arm)
        assert torch.all(s["w"][~module_edge] == 1.0) and torch.all(s["w"][module_edge] == f)
        assert torch.all(s["tau"][:n0] == 1.0) and torch.all(s["tau"][n0:] == f) and torch.all(s["bias"][n0:] == f)
        assert torch.all(s["g"] == 1.0)
    n = A.arm_scales(ext, l1, "N")
    assert torch.all(n["w"][out] == 0.0) and torch.all(n["w"][module_edge & ~out] == 0.25)
    f0 = A.arm_scales(ext, l1, "F0")
    assert torch.all(f0["w"][module_edge] == 0.0) and torch.all(f0["tau"][n0:] == 0.0) and torch.all(f0["w"][~module_edge] == 1.0)


def test_r_signs_are_seeded_ordered_and_applied_as_s_times_3(l1):
    s = A.r_signs(3)
    np.testing.assert_array_equal(s, np.random.default_rng(1_165_003).choice([-1, 1], size=20))
    r = A.with_signs(l1, s)
    for k, ((a, b, w), (a2, b2, w2)) in enumerate(zip(l1.synapses, r.synapses)):
        assert (a, b) == (a2, b2) and w2 == s[k] * 3.0
    assert A.r_signs(3).tolist() == s.tolist() and A.r_signs(4).tolist() != s.tolist()


def test_n_keeps_the_output_edges_in_the_mask_at_zero(con, l1):
    nmod = A.without_output(l1)
    ext = G.graft_connectome(con, nmod)
    ext_l1 = G.graft_connectome(con, l1)
    np.testing.assert_array_equal(ext.chem, ext_l1.chem)  # the same mask
    gen = G.seeded_genome(ext, nmod, Config().brain, n_strains=1)
    W, _ = gen.dense()
    for d in C.TURN_DORSAL + C.TURN_VENTRAL:
        assert float(W[0, ext.index("E4S_CL"), ext.index(d)]) == 0.0
    assert float(W[0, ext.index("E4S_NL"), ext.index("E4S_CL")]) == 3.0


def test_the_mc_transplant_moves_the_module_and_keeps_the_carriers_biases(con, l1):
    ext = G.graft_connectome(con, l1)
    host = C.embedded_population(con, ext, l1, Config().brain, run_seed=1_160_000, population=1)
    host = host.with_params(tau=host.tau.clone(), bias=host.bias.clone(), w=host.w.clone())
    cl, smdd = ext.index("E4S_CL"), ext.index("SMDDL")
    spec = BrainSpec.from_connectome(ext)
    pos = {(int(a), int(b)): p for p, (a, b) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist()))}
    host.w[0, pos[(cl, smdd)]] = 1.7  # an evolved output weight
    host.bias[0, cl] = 0.3
    host.bias[0, smdd] = 1.9  # a host bias on a turn neuron: must not move
    mc = A.mc_genome(host, ext, l1, Config().brain, turn=-0.2)
    W, _ = mc.dense()
    assert float(W[0, cl, smdd]) == pytest.approx(1.7) and float(mc.bias[0, cl]) == pytest.approx(0.3)
    import math
    assert float(mc.bias[0, smdd]) == pytest.approx(math.atanh(-0.1))  # the carrier's dorsal bias at turn -0.2
    assert float(W[0, ext.index("AIYL"), ext.index("AIZL")]) == 0.0  # the host itself does not move


def test_reset_and_rescue_replace_only_the_module(con, l1):
    ext = G.graft_connectome(con, l1)
    g = C.embedded_population(con, ext, l1, Config().brain, run_seed=1_160_001, population=2)
    r = A.with_signs(l1, A.r_signs(1))
    changed = g.with_params(w=g.w.clone() * 0.5)
    rescued = A.module_replaced(changed, ext, l1, Config().brain)
    reset = A.module_replaced(changed, ext, r, Config().brain)
    spec = BrainSpec.from_connectome(ext)
    me = ((spec.chem_i >= con.n) | (spec.chem_j >= con.n)).numpy()
    np.testing.assert_array_equal(rescued.w[:, ~me].numpy(), changed.w[:, ~me].numpy())
    assert set(np.abs(rescued.w[:, me].numpy()).ravel().tolist()) == {3.0}
    W_r, _ = reset.dense()
    k = [s for s in r.synapses if s[0] == "E4S_NL" and s[1] == "E4S_CL"][0][2]
    assert float(W_r[0, ext.index("E4S_NL"), ext.index("E4S_CL")]) == k


@pytest.mark.parametrize("lo,hi,est,want", [
    (-0.9, -0.1, -0.5, "reversed: M is worse"),
    (0.2, 1.4, 0.8, "supports"),
    (0.05, 0.7, 0.3, "positive; estimate below 0.5"),
    (-0.3, 0.4, 0.05, "does not support an effect of at least 0.5"),
    (-0.2, 1.2, 0.5, "inconclusive"),
])
def test_o1_rules(lo, hi, est, want):
    assert RD.o1_label(lo, hi, est) == want


def test_o1_bootstrap_uses_the_registered_seed_and_percentiles():
    d = np.array([0.5, 1.2, -0.3, 0.9, 1.4, 0.2, 0.7, 1.1, 0.0, 0.8, 1.3, 0.6])
    out = RD.o1(d)
    m = RD.boot_means(d, 10_000, 20_261_001)
    assert out["lo"] == pytest.approx(np.percentile(m, 5)) and out["hi"] == pytest.approx(np.percentile(m, 95))
    assert out["label"] == RD.o1_label(out["lo"], out["hi"], d.mean())
    assert RD.o1(d[:11])["label"] == "not read"  # fewer than 12 complete pairs


def test_the_companion_sentences():
    assert RD.o1_companion("supports", climb_lo=-0.1, climb_hi=0.4) == "N ended lower; M did not improve"
    assert RD.o1_companion("supports", climb_lo=0.1, climb_hi=0.9) is None
    assert RD.o1b_companion("supports", r_minus_n=-0.3) == "random signs were worse than no graft"
    assert RD.o1b_companion("inconclusive", r_minus_n=-0.3) is None


def test_the_nine_o2_labels():
    u, c, n = "uses", "unclear", "no material benefit"
    want = {(u, u): "uses at both endpoints", (u, c): "uses at G0; F unclear", (u, n): "uses at G0 only",
            (c, u): "uses at F; G0 unclear", (c, c): "unclear at both endpoints", (c, n): "no use at F; G0 unclear",
            (n, u): "uses at F only", (n, c): "no use at G0; F unclear", (n, n): "uses at neither endpoint"}
    assert {k: RD.o2_label(*k) for k in want} == want
    assert len(set(want.values())) == 9


def test_the_arm_reading_and_retention():
    labels = ["uses at both endpoints"] * 12 + ["uses at G0 only"] * 3 + ["not read"]
    out = RD.arm_reading(labels, threshold=12, denominator=16)
    assert out["reading"] == "uses at both endpoints"
    assert RD.arm_reading(labels[:11] + ["uses at G0 only"] * 5, 12, 16)["reading"] == "no label named"
    g0 = ["uses"] * 4 + ["unclear"]
    f = ["uses", "no material benefit", "uses", None, "uses"]
    assert RD.retention(g0, f) == pytest.approx(2 / 3)
    assert RD.retention(["unclear"], ["uses"]) == "not applicable"


@pytest.mark.parametrize("mean_ci,swap_ci,want", [
    ({"lo95": 0.6, "hi95": 1.0}, {"lo95": 0.7, "hi95": 1.1}, "uses"),
    ({"lo95": -1.8, "hi95": -1.7}, {"lo95": 0.8, "hi95": 0.9}, "harmful"),
    ({"lo95": -0.2, "hi95": -0.1}, {"lo95": -0.1, "hi95": 0.1}, "neutral"),  # inside +-0.25: not "harmful"
    ({"lo95": -0.4, "hi95": 0.1}, {"lo95": -0.1, "hi95": 0.1}, "unclear"),
])
def test_c2s_ordered_reading(mean_ci, swap_ci, want):
    assert RD.c2_reading(mean_ci, swap_ci) == want


def test_the_o3_split_is_eight_against_eight_by_rank():
    offsets = np.array([0.3, 0.1, 0.1, 0.5, 0.2, 0.9, 0.0, 0.4, 0.6, 0.7, 0.05, 0.25, 0.35, 0.45, 0.55, 0.65])
    low, high = RD.o3_split(offsets)
    assert len(low) == 8 and len(high) == 8 and set(low) | set(high) == set(range(16))
    assert 1 in low and 2 in low  # the tie at 0.1 goes to the lower run index first
    assert max(offsets[low]) <= min(offsets[high])
    # a tie across the boundary: ranks 8 and 9 share 0.5; the lower run index (3) goes low
    tie = np.array([0.1, 0.2, 0.3, 0.5, 0.35, 0.25, 0.15, 0.05, 0.9, 0.8, 0.7, 0.6, 0.5, 0.95, 0.85, 0.75])
    low, high = RD.o3_split(tie)
    assert 3 in low and 12 in high
