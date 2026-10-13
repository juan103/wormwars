"""E4's arms and interventions (docs/E4/E4-DESIGN.md v3 §1-§2): X0 and X+ scales on one connectome, the frozen
selector, E4's own frozen check, cutting the cross-links, and mean substitution without clipping."""

from __future__ import annotations

import pytest
import torch

from wormwars.connectome import load_connectome
from wormwars.e3 import organism as O
from wormwars.e3.task import shuttle_config
from wormwars.e4 import arms as AR
from wormwars.e4s import arms as A


@pytest.fixture(scope="module")
def cx():
    return AR.context(load_connectome(), A.load_l1(), shuttle_config().brain)


def _edge(cx, pre, post):
    spec, ext = cx["spec"], cx["org"].ext
    return int(((spec.chem_i == ext.index(pre)) & (spec.chem_j == ext.index(post))).nonzero()[0, 0])


def test_x0_and_x_plus_differ_only_on_the_32_slots(cx):
    s0, s1 = AR.scales(cx, "x0"), AR.scales(cx, "x_plus", cross_factor=1.0)
    slots = AR.slot_indices(cx)
    assert len(slots) == 32
    assert torch.all(s0["w"][slots] == 0) and torch.all(s1["w"][slots] == 1.0)
    other = torch.ones_like(s0["w"], dtype=torch.bool)
    other[slots] = False
    assert torch.equal(s0["w"][other], s1["w"][other])
    for k in ("tau", "bias", "g"):
        assert torch.equal(s0[k], s1[k])


def test_the_selector_is_frozen(cx):
    ext = cx["org"].ext
    for arm in ("x0", "x_plus"):
        s = AR.scales(cx, arm, cross_factor=0.5)
        for n in ("E3_Q", "E3_RA", "E3_RB"):
            assert s["tau"][ext.index(n)] == 0 and s["bias"][ext.index(n)] == 0
        for pre, post in [("E3_Q", "E3_Q"), ("E3_RA", "E3_Q"), ("E3_RB", "E3_Q")] + [("E3_Q", c) for c in O.COMPARATORS]:
            assert s["w"][_edge(cx, pre, post)] == 0, (pre, post)
        assert s["bias"][ext.index("E3_A_CL")] > 0  # the comparators' biases stay mutable


def test_the_inherited_factor_is_t_fs(cx):
    s = AR.scales(cx, "x0")
    assert float(s["w"][_edge(cx, "E3_A_NL", "E3_A_CL")]) == pytest.approx(0.25)


def test_mutable_counts(cx):
    assert AR.mutable_count(cx, "x_plus", cross_factor=0.25) == AR.mutable_count(cx, "x0") + 32


def test_x_plus_needs_its_cross_factor(cx):
    """The cross-link scale comes from the registered rule, never from a default."""
    with pytest.raises(ValueError):
        AR.scales(cx, "x_plus")


def test_assert_frozen_catches_a_moved_slot_in_x0(cx):
    g0 = cx["org"].genome
    AR.assert_frozen(g0, g0, AR.scales(cx, "x0"))
    w = g0.w.clone()
    w[:, AR.slot_indices(cx)[0]] = 0.5
    with pytest.raises(AssertionError):
        AR.assert_frozen(g0, g0.with_params(w=w), AR.scales(cx, "x0"))


def test_cut_zeroes_exactly_the_listed_links(cx):
    g = cx["org"].genome
    w = g.w.clone()
    slots = AR.slot_indices(cx)
    w[:, slots] = torch.linspace(0.1, 3.0, len(slots))
    g = g.with_params(w=w)
    cut = AR.cut(g, slots)
    assert torch.all(cut.w[:, slots] == 0)
    keep = torch.ones(g.w.shape[1], dtype=torch.bool)
    keep[slots] = False
    assert torch.equal(cut.w[:, keep], g.w[:, keep]) and torch.equal(cut.bias, g.bias)


def test_mean_substitution_adds_each_links_mean_drive_unclipped(cx):
    """b'_j = b_j + Σ_{i→j} w_ij · mean(tanh v_i), without clipping at b_max (Fable, Astra)."""
    g = cx["org"].genome
    ext, spec = cx["org"].ext, cx["spec"]
    slots = AR.slot_indices(cx)
    w = g.w.clone()
    w[:, slots] = 3.0
    g = g.with_params(w=w)
    means = torch.zeros(ext.n)
    means[ext.index("E3_A_NL")] = 0.9  # a large constant source: four of its links reach B's neurons
    sub = AR.mean_substitute(g, slots, means)
    assert torch.all(sub.w[:, slots] == 0)
    target = ext.index("E3_B_CL")
    add = sum(3.0 * float(means[int(spec.chem_i[k])]) for k in slots if int(spec.chem_j[k]) == target)
    assert float(sub.bias[0, target]) == pytest.approx(float(g.bias[0, target]) + add)
    assert add > 2.0 and abs(float(sub.bias[0, target])) > shuttle_config().brain.b_max - 1e-6  # not clipped


def test_a_constant_source_is_reproduced_exactly(cx):
    """The constant-source check (Astra): a source held at a constant activation drives its targets identically
    through the links and through the substituted biases."""
    g = cx["org"].genome
    ext, spec = cx["org"].ext, cx["spec"]
    slots = AR.slot_indices(cx)
    w = g.w.clone()
    w[:, slots] = torch.linspace(-2.0, 2.0, len(slots))
    g = g.with_params(w=w)
    act = torch.zeros(ext.n)
    act[[ext.index(n) for n in ("E3_A_NL", "E3_A_NR", "E3_A_CL", "E3_A_CR", "E3_B_NL", "E3_B_NR", "E3_B_CL", "E3_B_CR")]] = 0.37
    sub = AR.mean_substitute(g, slots, act)
    W, _ = g.dense()
    Ws, _ = sub.dense()
    through_links = act @ W[0] + g.bias[0]
    through_bias = act @ Ws[0] + sub.bias[0]
    assert torch.allclose(through_links, through_bias, atol=1e-5)


def test_mean_substitution_refuses_the_legacy_direction(cx):
    """It reads chem_i as the source, true only under pre_to_post (Fable)."""
    import dataclasses
    g = cx["org"].genome
    legacy = g.with_params(cfg=dataclasses.replace(g.cfg, chem_direction="post_to_pre"))
    with pytest.raises(ValueError):
        AR.mean_substitute(legacy, AR.slot_indices(cx), torch.zeros(cx["org"].ext.n))


def test_class_scales_partition_x0s_mask(cx):
    """The diagnostics' classes (Fable, pilot review): each a subset of X0's mutable set; w, tau and bias partition it;
    modules A and B are disjoint; the gated edges are both modules' comparator → motor edges."""
    x0 = AR.scales(cx, "x0")
    parts = {k: AR.class_scales(cx, k) for k in ("w", "tau", "bias", "module_A", "module_B", "gated_edges")}
    for k, sc in parts.items():
        for p in ("w", "tau", "bias", "g"):
            assert torch.all((sc[p] != 0) <= (x0[p] != 0)), (k, p)
            assert torch.all((sc[p] == 0) | (sc[p] == x0[p])), (k, p)
    for p in ("w", "tau", "bias"):
        n = sum(int((parts[k][p] != 0).sum()) for k in ("w", "tau", "bias"))
        assert n == int((x0[p] != 0).sum())
    a, b = parts["module_A"], parts["module_B"]
    for p in ("w", "tau", "bias"):
        assert not torch.any((a[p] != 0) & (b[p] != 0))
    gated = parts["gated_edges"]["w"] != 0
    assert int(gated.sum()) == 32 and int((parts["gated_edges"]["bias"] != 0).sum()) == 0


def test_scaled_x0(cx):
    x0 = AR.scales(cx, "x0")
    half = AR.class_scales(cx, "all", factor=0.10)
    assert torch.allclose(half["w"], x0["w"] * (0.10 / 0.25))


def test_nose_and_comparator_bias_classes(cx):
    ext = cx["org"].ext
    n = AR.class_scales(cx, "nose_bias")["bias"] != 0
    c = AR.class_scales(cx, "comparator_bias")["bias"] != 0
    assert int(n.sum()) == 4 and int(c.sum()) == 4 and not torch.any(n & c)
    assert bool(n[ext.index("E3_A_NL")]) and bool(c[ext.index("E3_B_CR")])
    assert torch.equal(n | c, AR.class_scales(cx, "bias")["bias"] != 0)


def test_combined_factors(cx):
    """Weights and τ at 0.25, the module biases at `bias_factor`, the slots at `cross_factor` (0: X0)."""
    x0 = AR.scales(cx, "x0")
    sc = AR.combined_scales(cx, bias_factor=0.02, cross_factor=0.0)
    assert torch.equal(sc["w"], x0["w"]) and torch.equal(sc["tau"], x0["tau"])
    assert torch.allclose(sc["bias"], x0["bias"] * (0.02 / 0.25))
    sp = AR.combined_scales(cx, bias_factor=0.02, cross_factor=1.0)
    assert torch.all(sp["w"][AR.slot_indices(cx)] == 1.0)


def test_cross_links_only(cx):
    sc = AR.combined_scales(cx, bias_factor=0.0, cross_factor=0.5, inherited=False)
    slots = AR.slot_indices(cx)
    assert torch.all(sc["w"][slots] == 0.5) and int((sc["w"] != 0).sum()) == 32
    assert torch.all(sc["tau"] == 0) and torch.all(sc["bias"] == 0)


def test_centering_removes_the_constant_part(cx):
    """Astra's fourth condition: links intact, each target's bias minus Σ w_ij · m_i, so a source held at its mean
    contributes nothing and a deviation passes unchanged."""
    g = cx["org"].genome
    ext = cx["org"].ext
    slots = AR.slot_indices(cx)
    w = g.w.clone()
    w[:, slots] = torch.linspace(-2.0, 2.0, len(slots))
    g = g.with_params(w=w)
    m = torch.zeros(ext.n)
    src = [ext.index(n) for n in ("E3_A_NL", "E3_A_NR", "E3_A_CL", "E3_A_CR", "E3_B_NL", "E3_B_NR", "E3_B_CL", "E3_B_CR")]
    m[src] = 0.3
    cen = AR.center(g, slots, m)
    assert torch.equal(cen.w, g.w)
    W, _ = g.dense()
    at_mean = m @ W[0] + cen.bias[0]
    sub = AR.mean_substitute(g, slots, m)
    cut_drive = m @ AR.cut(g, slots).dense()[0][0] + g.bias[0]
    assert torch.allclose(at_mean, cut_drive, atol=1e-5)  # at the mean, centred links add nothing beyond the cut
    assert torch.allclose(sub.bias[0] - g.bias[0], g.bias[0] - cen.bias[0], atol=1e-6)
