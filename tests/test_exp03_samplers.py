"""Experiment 03's control ensembles (design v3, D051): every sampler preserves degrees, meets its
constraint exactly on the final graph, reports its counts, and fails loudly."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import shuffled
from wormwars.exp03 import samplers as S


@pytest.fixture(scope="module")
def con():
    return load_connectome()


def degrees(c):
    ch, gp = c.chem > 0, c.gap > 0
    return ch.sum(1), ch.sum(0), gp.sum(1)


def test_mirror_map_is_an_involution_from_the_curated_file(con):
    m = S.mirror_map(con)
    assert np.all(m[m] == np.arange(con.n))
    assert m[con.index("AWCL")] == con.index("AWCR") and m[con.index("AVL")] == con.index("AVL")
    assert int((m != np.arange(con.n)).sum()) == 198  # 99 pairs


@pytest.mark.parametrize("kind", ["SH", "SH-route", "SH-class", "SH-mirror"])
def test_every_ensemble_preserves_degrees_and_weights_multiset(con, kind):
    g, info = S.build(con, kind, seed=5, passes=4)
    for a, b in zip(degrees(con), degrees(g)):
        np.testing.assert_array_equal(a, b)
    np.testing.assert_allclose(np.sort(g.chem[g.chem > 0]), np.sort(con.chem[con.chem > 0]))
    np.testing.assert_allclose(np.sort(g.gap[g.gap > 0]), np.sort(con.gap[con.gap > 0]))
    assert np.allclose(g.gap, g.gap.T) and np.all(np.diag(g.gap) == 0)
    assert info["chem"]["accepted"] == info["chem"]["target"] and info["chem"]["attempted"] >= info["chem"]["accepted"]


def test_ordinary_ensemble_mixes_like_the_published_sampler(con):
    g, _ = S.build(con, "SH", seed=7, passes=20)
    old = shuffled(con, 7, "SH7")
    j_new, j_old = S.jaccard(g.chem > 0, con.chem > 0), S.jaccard(old.chem > 0, con.chem > 0)
    assert abs(j_new - j_old) < 0.05


def test_routing_constraint_holds_on_the_final_weighted_graph(con):
    g, info = S.build(con, "SH-route", seed=3, passes=6)
    for name in S.constrained_neurons(con):
        k = con.index(name)
        for mat in ("chem", "gap"):
            assert S.direct_readout(g, k, mat)["count"] <= S.direct_readout(con, k, mat)["count"]
            assert S.direct_readout(g, k, mat)["weight"] <= S.direct_readout(con, k, mat)["weight"] + 1e-9


def test_class_ensemble_keeps_partner_class_profiles(con):
    g, _ = S.build(con, "SH-class", seed=2, passes=4)
    np.testing.assert_array_equal(S.class_profile(con), S.class_profile(g))


def test_mirror_ensemble_keeps_the_symmetric_share_exactly_and_is_routing_matched(con):
    g, _ = S.build(con, "SH-mirror", seed=4, passes=4)
    m = S.mirror_map(con)
    for mat in ("chem", "gap"):
        assert S.mirror_share(getattr(g, mat) > 0, m) == pytest.approx(S.mirror_share(getattr(con, mat) > 0, m))
    for name in S.constrained_neurons(con):
        k = con.index(name)
        assert S.direct_readout(g, k, "chem")["weight"] <= S.direct_readout(con, k, "chem")["weight"] + 1e-9


def test_mirror_ensemble_actually_moves_edges(con):
    g, _ = S.build(con, "SH-mirror", seed=4, passes=4)
    assert S.jaccard(g.chem > 0, con.chem > 0) < 0.7


def test_a_sampler_that_cannot_reach_its_target_fails_loudly(con):
    with pytest.raises(S.SamplerFailure):
        S.build(con, "SH-class", seed=1, passes=4, attempt_factor=0.5)


def test_build_is_reproducible(con):
    a, _ = S.build(con, "SH-route", seed=9, passes=3)
    b, _ = S.build(con, "SH-route", seed=9, passes=3)
    np.testing.assert_array_equal(a.chem, b.chem)
    np.testing.assert_array_equal(a.gap, b.gap)


def test_ordinary_ensemble_is_identical_to_the_published_shuffles(con):
    """The SH ensemble must be the sampler 01b and 02 used, graph for graph."""
    for seed in (1, 4):
        g, _ = S.build(con, "SH", seed=seed, passes=20)
        old = shuffled(con, seed, f"SH{seed}")
        np.testing.assert_array_equal(g.chem, old.chem)
        np.testing.assert_array_equal(g.gap, old.gap)
