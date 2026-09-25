"""Graph covariates for the primary outcome (Fable 5.1's pre-registration review, points 1 and 7):
mirror symmetry, which a degree-preserving shuffle destroys, and the food pairs' routing."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import shuffled
from wormwars.exp02 import structure
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con)


def test_mirror_maps_left_and_right_names_and_leaves_unpaired_ones(parts):
    con, _ = parts
    m = structure.mirror_index(con)
    i, j = con.index("AWCL"), con.index("AWCR")
    assert m[i] == j and m[j] == i
    k = con.index("DVA")
    assert m[k] == k
    assert sorted(m) == list(range(con.n)), "a permutation"


def test_a_mirror_symmetric_graph_scores_one(parts):
    con, _ = parts
    m = structure.mirror_index(con)
    chem = con.chem.copy()
    sym = np.maximum(chem, chem[np.ix_(m, m)])
    gap = np.maximum(con.gap, con.gap[np.ix_(m, m)])
    s = structure.mirror_symmetry(con.with_masks(sym, gap, "sym"))
    assert s["chem_edges_mirrored"] == pytest.approx(1.0)
    assert s["food_out_jaccard"] == pytest.approx(1.0)


def test_a_shuffle_is_less_mirror_symmetric_than_the_graph_it_came_from(parts):
    con, _ = parts
    sym = structure.mirror_symmetry(con)
    sh = structure.mirror_symmetry(shuffled(con, 101, "SH101"))
    assert sh["chem_edges_mirrored"] < sym["chem_edges_mirrored"]


def test_covariates_are_scalars_and_carry_no_edges(parts):
    con, iface = parts
    c = structure.covariates(shuffled(con, 101, "SH101"), iface)
    assert set(c) == {"mirror", "food_routing"}
    assert set(c["food_routing"]) == {"AWA", "AWC", "ASE"}
    for v in list(c["mirror"].values()) + [x for f in c["food_routing"].values() for x in f.values()]:
        assert isinstance(v, float)
