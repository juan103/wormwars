"""SH and RD must be matched controls: same nodes, same indices, same edge and weight counts."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import degree_summary, make_graphs, random_graph, shuffled
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def sh(con):
    return shuffled(con, seed=1)


@pytest.fixture(scope="module")
def rd(con):
    return random_graph(con, seed=1)


def test_shuffle_preserves_degrees_exactly(con, sh):
    a, b = degree_summary(con), degree_summary(sh)
    np.testing.assert_array_equal(a["chem_in_degree"], b["chem_in_degree"])
    np.testing.assert_array_equal(a["chem_out_degree"], b["chem_out_degree"])
    np.testing.assert_array_equal(a["gap_degree"], b["gap_degree"])


def test_shuffle_preserves_edge_and_weight_totals(con, sh):
    assert int((con.chem > 0).sum()) == int((sh.chem > 0).sum())
    assert int((con.gap > 0).sum()) == int((sh.gap > 0).sum())
    assert con.chem.sum() == pytest.approx(sh.chem.sum(), rel=1e-5)
    assert con.gap.sum() == pytest.approx(sh.gap.sum(), rel=1e-5)
    np.testing.assert_allclose(
        np.sort(con.chem[con.chem > 0]), np.sort(sh.chem[sh.chem > 0]), rtol=1e-5
    )


def test_shuffle_actually_moves_edges(con, sh):
    same = ((con.chem > 0) & (sh.chem > 0)).sum()
    total = (con.chem > 0).sum()
    assert same / total < 0.25, f"shuffle left {same / total:.1%} of edges in place"


def test_shuffled_gap_stays_symmetric_with_no_self_edges(con, sh):
    assert np.array_equal(sh.gap, sh.gap.T)
    assert np.all(np.diag(sh.gap) == 0)
    assert (sh.gap >= 0).all()


def test_random_graph_matches_counts(con, rd):
    assert rd.n == con.n
    assert int((rd.chem > 0).sum()) == int((con.chem > 0).sum())
    assert int((rd.gap > 0).sum()) == int((con.gap > 0).sum())
    np.testing.assert_allclose(
        np.sort(con.chem[con.chem > 0]), np.sort(rd.chem[rd.chem > 0]), rtol=1e-5
    )


def test_random_gap_symmetric(con, rd):
    assert np.array_equal(rd.gap, rd.gap.T)
    assert np.all(np.diag(rd.gap) == 0)


def test_random_graph_destroys_degree_structure(con, rd):
    """RD should NOT preserve degrees -- that is what makes it a different control from SH."""
    a, b = degree_summary(con), degree_summary(rd)
    assert not np.array_equal(a["chem_in_degree"], b["chem_in_degree"])
    # N2 is much more heavy-tailed than a uniform random graph of the same density
    assert a["chem_in_degree"].std() > b["chem_in_degree"].std() * 1.5


def test_neuron_names_classes_and_indices_are_untouched(con, sh, rd):
    """The sensor/motor map addresses neurons by index, so indices must not move."""
    iface = load_interface(con)
    for other in (sh, rd):
        assert other.names == con.names
        assert other.classes == con.classes
        assert load_interface(other).sensor_neuron.tolist() == iface.sensor_neuron.tolist()
        assert load_interface(other).pump_neurons.tolist() == iface.pump_neurons.tolist()


def test_independent_graphs_differ(con):
    graphs = make_graphs(con, "SH", 3)
    assert len({g.label for g in graphs}) == 3
    assert not np.array_equal(graphs[0].chem, graphs[1].chem)
    rds = make_graphs(con, "RD", 3)
    assert not np.array_equal(rds[0].chem, rds[1].chem)


def test_generation_is_deterministic(con):
    assert np.array_equal(shuffled(con, 4).chem, shuffled(con, 4).chem)
    assert np.array_equal(random_graph(con, 4).gap, random_graph(con, 4).gap)


def test_n2_condition_returns_the_real_graph(con):
    graphs = make_graphs(con, "N2", 5)
    assert len(graphs) == 1 and graphs[0].label == "N2"
