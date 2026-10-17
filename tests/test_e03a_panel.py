"""03a's panel rule and structural comparators (DESIGN.md v7.1 §4, §6)."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.connectome import load_connectome
from wormwars.e03a import panel as P
from wormwars.e03a import reinsert as R
from wormwars.e03a import structural as ST
from wormwars.exp03.samplers import mirror_map
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def iface(con):
    return load_interface(con)


def test_eligible_neurons_are_unmapped_non_pharyngeal_and_connected_both_ways(con, iface):
    el = P.eligible(con, iface)
    mapped = set(iface.mapped_neurons)
    assert 200 < len(el) < 280  # "about 245 neurons in N2" (§4)
    assert not set(el) & mapped
    assert all(con.classes[i] != "pharyngeal" for i in el)
    for name in ("AIYL", "AIZL", "RIAL"):
        assert con.index(name) in el


def test_a_neuron_with_no_path_to_the_interface_is_not_eligible(con, iface):
    """Sabotage: cut every output of an eligible neuron and it stops being eligible."""
    k = con.index("AIYL")
    chem, gap = con.chem.copy(), con.gap.copy()
    chem[k, :] = 0
    gap[k, :] = gap[:, k] = 0
    cut = con.with_masks(chem, gap, "cut")
    assert k not in P.eligible(cut, iface)


def test_representatives_take_one_member_per_pair_by_a_fixed_seed(con, iface):
    el = P.eligible(con, iface)
    a, b = P.representatives(con, el, 0), P.representatives(con, el, 0)
    assert a == b
    m = mirror_map(con)
    reps = set(a)
    for i in el:
        j = int(m[i])
        if j != i and j in el:
            assert (i in reps) != (j in reps)
    c = P.representatives(con, el, 1)
    assert set(c) != set(a) and len(c) == len(a)


def test_relevance_interval_is_a_world_bootstrap_of_the_three_brain_mean():
    rng = np.random.default_rng(0)
    intact = rng.integers(0, 5, size=(3, 200)).astype(float)
    deleted = intact[None] - np.array([1.0, 0.0, 0.2])[:, None, None]  # exact drops, no noise
    r = P.relevance(intact, deleted, B=500, seed=0)
    np.testing.assert_allclose(r["mean"], [1.0, 0.0, 0.2])
    np.testing.assert_allclose(r["lo"], r["hi"])


def test_tiers_follow_the_rule():
    neurons = list(range(100, 130))
    mean = np.linspace(3.0, 0.0, 30)
    lo, hi = mean - 0.3, mean + 0.3
    rel = {"mean": mean, "lo": lo, "hi": hi}
    p_sel = 1.0
    t = P.tiers(neurons, rel, p_sel, seed=0)
    assert t["high"] == [100, 101, 102]
    assert len(t["medium"]) == 2 and all(lo[n - 100] <= p_sel <= hi[n - 100] for n in t["medium"])
    assert len(t["low"]) == 1 and -p_sel <= lo[t["low"][0] - 100] and hi[t["low"][0] - 100] <= p_sel
    assert len(set(t["high"] + t["medium"] + t["low"])) == 6
    assert P.tiers(neurons, rel, p_sel, seed=0) == t


def test_tiers_flag_the_fallbacks():
    neurons = list(range(10))
    mean = np.array([5, 4, 3, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3])
    rel = {"mean": mean, "lo": mean - 0.01, "hi": mean + 0.01}
    t = P.tiers(neurons, rel, p_sel=1.0, seed=0)  # nothing contains 1.0, nothing lies inside ±1.0
    assert all("medium from ranks 4-20" in t["flags"][n] for n in t["medium"])
    assert "low by smallest absolute drop" in t["flags"][t["low"][0]] and t["low"][0] == 9
    rel2 = {"mean": mean, "lo": mean - 3, "hi": mean + 3}
    t2 = P.tiers(neurons, rel2, p_sel=2.5, seed=0)
    assert all("relatively high only" in t2["flags"][n] for n in t2["high"])


def test_mirror_ranking_reads_the_partners_mirror(con):
    m = mirror_map(con)
    x = con.index("AIYL")
    xp = con.index("AIYR")
    mr = ST.mirror(con, x, m)
    c = R.candidates(con.n, x)
    k = int(np.nonzero(c == con.index("AIZL"))[0][0])
    assert mr["out"][k] == con.chem[xp, con.index("AIZR")]
    assert mr["in"][k] == con.chem[con.index("AIZR"), xp]
    kp = int(np.nonzero(c == xp)[0][0])  # X' itself takes the class-model score
    assert mr["gap"][kp] == ST.class_model(con, x)["gap"][kp]
    assert ST.mirror(con, con.index("AVL"), m) is None  # an unpaired neuron


def test_class_model_is_a_probability_and_ignores_x(con):
    x = con.index("AIYL")
    cm = ST.class_model(con, x)
    for t in R.TYPES:
        assert ((0 <= cm[t]) & (cm[t] <= 1)).all()
    other = con.with_masks(con.chem.copy(), con.gap.copy(), "copy")
    other.chem[:, x] = np.roll(con.chem[:, x], 5)
    for t in R.TYPES:
        np.testing.assert_array_equal(ST.class_model(other, x)[t], cm[t])
    d = ST.degree(con, x)
    c = R.candidates(con.n, x)
    i = 3
    chem = (con.chem > 0).copy()
    chem[x, :] = chem[:, x] = False
    np.fill_diagonal(chem, False)
    assert d["in"][i] == chem[c[i]].sum() and d["out"][i] == chem[:, c[i]].sum()
