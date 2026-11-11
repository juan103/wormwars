"""`Genome.cat` and `Genome.assign` refuse genomes on different graphs or configurations (docs/E5/E5-1-DESIGN.md §9).

A batch of E5-1 holds one graph, but nothing used to stop two populations of the same size on different graphs from
being concatenated: the result took the first part's spec, so the second part's weights would be read on the wrong
edges. The specs are compared by value, because `moved()` and `BrainSpec.to` make new spec objects for one graph.
The graphs here are small synthetic ones, not connectome data.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import BrainConfig
from wormwars.connectome.loader import Connectome


def _toy(chem_edges, gap_edges=((0, 1),), n=6, label="toy", weight=1.0):
    chem = np.zeros((n, n), dtype=np.float32)
    gap = np.zeros((n, n), dtype=np.float32)
    for i, j in chem_edges:
        chem[i, j] = weight
    for i, j in gap_edges:
        gap[i, j] = gap[j, i] = 1.0
    return Connectome(tuple(f"T{i}" for i in range(n)), ("inter",) * n, chem, gap, "em_sections", {}, label)


A_EDGES = ((0, 1), (1, 2), (2, 3), (3, 4))
B_EDGES = ((0, 2), (1, 3), (2, 4), (4, 5))  # as many edges, wired differently


def _genome(con, n=2, seed=0, cfg=None):
    return Genome.random(BrainSpec.from_connectome(con), cfg or BrainConfig(), n,
                         generator=torch.Generator().manual_seed(seed))


def test_cat_refuses_equal_sized_graphs_wired_differently():
    a, b = _genome(_toy(A_EDGES)), _genome(_toy(B_EDGES))
    assert a.w.shape == b.w.shape  # the old code would have concatenated them silently
    with pytest.raises(ValueError, match="spec"):
        Genome.cat([a, b])


def test_assign_refuses_a_genome_on_another_graph():
    a, b = _genome(_toy(A_EDGES)), _genome(_toy(B_EDGES), n=1)
    with pytest.raises(ValueError, match="spec"):
        a.assign([0], b)


def test_equal_specs_built_separately_still_combine():
    a, b = _genome(_toy(A_EDGES), seed=1), _genome(_toy(A_EDGES), seed=2)
    assert a.spec is not b.spec
    c = Genome.cat([a, b])
    assert torch.equal(c.w, torch.cat([a.w, b.w]))
    d = a.assign([1], b.select([0]))
    assert torch.equal(d.w[1], b.w[0])


def test_a_moved_spec_still_combines():
    a = _genome(_toy(A_EDGES))
    moved = a.with_params(spec=a.spec.to("cpu"))
    assert moved.spec is not a.spec
    assert Genome.cat([a, moved]).n_strains == 4


def test_cat_refuses_other_anatomical_weights_or_labels():
    a = _genome(_toy(A_EDGES))
    with pytest.raises(ValueError, match="spec"):
        Genome.cat([a, _genome(_toy(A_EDGES, weight=2.0))])
    with pytest.raises(ValueError, match="spec"):
        Genome.cat([a, _genome(_toy(A_EDGES, label="other"))])


def test_cat_and_assign_refuse_another_brain_configuration():
    con = _toy(A_EDGES)
    a = _genome(con)
    other = dataclasses.replace(BrainConfig(), substeps=BrainConfig().substeps * 2)
    b = a.with_params(cfg=other)
    with pytest.raises(ValueError, match="configuration"):
        Genome.cat([a, b])
    with pytest.raises(ValueError, match="configuration"):
        a.assign([0], b.select([0]))


def test_an_explicit_configuration_still_overrides_the_result():
    a = _genome(_toy(A_EDGES))
    other = dataclasses.replace(BrainConfig(), substeps=BrainConfig().substeps * 2)
    assert Genome.cat([a, a.clone()], cfg=other).cfg == other


def test_configurations_differing_only_in_initialisation_combine():
    """The frozen opponent suite (`make_frozen_suite`) spreads its initialisation scales: the init_* fields only decide
    how a genome is drawn, never how it runs."""
    a = _genome(_toy(A_EDGES))
    other = dataclasses.replace(BrainConfig(), init_w_scale=BrainConfig().init_w_scale * 2, init_bias_std=0.5,
                                init_chem_magnitude="permuted", init_permutation_seed=4)
    b = a.with_params(cfg=other)
    assert Genome.cat([a, b]).n_strains == 4
    assert a.assign([0], b.select([0])).n_strains == 2
