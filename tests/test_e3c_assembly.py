"""E3c's arms (docs/E3/E3c-DESIGN.md v2.1 §3-§4): the from-scratch draws, the evolved selector's draw, and the
mutation masks."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec
from wormwars.connectome import load_connectome
from wormwars.e3 import assembly as AS
from wormwars.e3 import maze_organisms as MO
from wormwars.e3 import organism as O
from wormwars.e3 import samplers as SA
from wormwars.e3 import tuning as T
from wormwars.e3.task import shuttle_config
from wormwars.e4s import arms as A


@pytest.fixture(scope="module")
def cx():
    con, l1 = load_connectome(), A.load_l1()
    bcfg = shuttle_config().brain
    return AS.context(con, l1, bcfg)


def _count(sc):
    return sum(int((sc[k] > 0).sum()) for k in ("w", "tau", "bias", "g"))


def test_the_masks_count_as_the_design_says(cx):
    assert _count(AS.arm_scales("s_mod", cx)) == 65
    assert _count(AS.arm_scales("s_dense", cx)) == 171
    assert _count(AS.arm_scales("p_sel", cx)) == 13
    for arm in AS.TRAINED:
        sc = AS.arm_scales(arm, cx)
        assert set(float(x) for k in ("w", "tau", "bias") for x in sc[k].unique()) <= {0.0, 1.0}  # factor 1.0


def test_the_frozen_set_in_every_arm(cx):
    for arm in AS.TRAINED:
        ext = AS.arm_ext(arm, cx)
        sc = AS.arm_scales(arm, cx)
        spec = BrainSpec.from_connectome(ext)
        n0 = int(ext.meta["worm_neurons"])
        for name in ("E3B_WL", "E3B_WR", *O.RELAYS):
            k = ext.index(name)
            assert float(sc["tau"][k]) == 0 and float(sc["bias"][k]) == 0, (arm, name)
        w2 = {ext.index("E3B_WL"), ext.index("E3B_WR")}
        for p, (i, j) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist())):
            if i in w2 or (i < n0 and j < n0):
                assert float(sc["w"][p]) == 0, (arm, ext.names[i], ext.names[j])
        assert all(float(sc["tau"][k]) == 0 for k in range(n0))


def test_s_dense_is_the_b_task_draw_on_the_carrier_with_w2(cx):
    rng = np.random.default_rng(5)
    pop = AS.draw("s_dense", cx, rng, 4)
    ref = SA.b_task_draw(np.random.default_rng(5), cx["bt_ext"], cx["bt_module"], cx["bcfg"], 4)
    ext = cx["dense"].ext
    for s in range(4):
        want = MO.named_edges(ref.select([s]), cx["bt_ext"])
        got = MO.named_edges(pop.select([s]), ext)
        assert all(got[k] == pytest.approx(v) for k, v in want.items())
        for name in SA.NEURONS:
            assert float(pop.bias[s, ext.index(name)]) == pytest.approx(float(ref.bias[s, cx["bt_ext"].index(name)]))
    seed_g = cx["dense"].genome
    n0 = int(ext.meta["worm_neurons"])
    assert torch.equal(pop.bias[:, :n0], seed_g.bias[:, :n0].expand(4, -1))  # the carrier at W2's resting turn
    assert torch.equal(pop.bias[:, ext.index("E3B_WL")], seed_g.bias[:, ext.index("E3B_WL")].expand(4))


def test_s_mod_is_the_same_draw_projected_onto_es_mask(cx):
    pop = AS.draw("s_mod", cx, np.random.default_rng(5), 4)
    dense = AS.draw("s_dense", cx, np.random.default_rng(5), 4)
    ext_e, ext_d = cx["seed"].ext, cx["dense"].ext
    seed_edges = MO.named_edges(cx["seed"].genome, ext_e)
    for s in range(4):
        got, dn = MO.named_edges(pop.select([s]), ext_e), MO.named_edges(dense.select([s]), ext_d)
        for key in seed_edges:
            if key[0].startswith("E3B_"):
                assert got[key] == seed_edges[key]  # W2's outputs as in the seed
            elif key in dn:
                assert got[key] == pytest.approx(dn[key]), key  # E's mask, the draw's value
        for name in SA.NEURONS:
            assert float(pop.tau[s, ext_e.index(name)]) == pytest.approx(float(dense.tau[s, ext_d.index(name)]))
    n0 = int(ext_e.meta["worm_neurons"])
    assert torch.equal(pop.bias[:, :n0], cx["seed"].genome.bias[:, :n0].expand(4, -1))


def test_p_sel_draws_only_the_selector(cx):
    pop = AS.draw("p_sel", cx, np.random.default_rng(7), 6)
    ref = SA.ga_draw(np.random.default_rng(7), 6)
    assert np.allclose(SA.read_selector(pop, cx["seed"].ext), ref, atol=1e-6)
    mask = SA.selector_masks(cx["seed"].ext)
    seed = cx["seed"].genome
    assert torch.equal(pop.w[:, ~mask["w"]], seed.w[:, ~mask["w"]].expand(6, -1))
    assert torch.equal(pop.bias[:, ~mask["bias"]], seed.bias[:, ~mask["bias"]].expand(6, -1))
    assert float(np.abs(ref[:, [SA.SELECTOR_INDEX[k] for k in ("b_q", "bias_A_CL", "bias_B_CL")]]).max()) <= 2.0


def test_a_draw_is_reproducible_by_its_seed_and_strains_are_independent(cx):
    for arm in AS.TRAINED:
        a = AS.draw(arm, cx, np.random.default_rng(11), 3)
        b = AS.draw(arm, cx, np.random.default_rng(11), 3)
        assert all(torch.equal(x, y) for x, y in zip(a.params().values(), b.params().values()) if x is not None)
        assert not torch.equal(a.w[0], a.w[1])


def test_tunings_default_factor_is_unchanged(cx):
    sc = T.scales(cx["seed"].ext)
    assert set(float(x) for x in sc["w"].unique()) == {0.0, 0.25}
