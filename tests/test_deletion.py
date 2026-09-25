"""Deleting a neuron (roadmap 02b; 03a's deletion test): no term involving it remains in any
other neuron's update. It must match a separately built network in which the neuron never
existed. Silencing does not, when gap junctions are present (D044)."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import BrainConfig
from wormwars.connectome import load_connectome
from wormwars.deletion import delete_neurons, reindexed_without, without_neuron


@pytest.fixture(scope="module")
def con():
    return load_connectome()


def _genome(spec, s=1, seed=0):
    return Genome.random(spec, BrainConfig(), s, generator=torch.Generator().manual_seed(seed))


def _gap_neuron(con):
    """A neuron with both chemical and gap partners."""
    for k in range(con.n):
        if (con.gap[k] > 0).sum() >= 2 and (con.chem[k] > 0).sum() >= 2 and (con.chem[:, k] > 0).sum() >= 2:
            return k
    raise AssertionError("no such neuron")


def _small_genome(big: Genome, small_spec: BrainSpec, keep: np.ndarray) -> Genome:
    """The same parameters on the re-indexed network without the deleted neuron."""
    old = {int(n): i for i, n in enumerate(keep)}
    ci = {(old[int(a)], old[int(b)]): e for e, (a, b) in enumerate(zip(big.spec.chem_i, big.spec.chem_j))
          if int(a) in old and int(b) in old}
    gi = {(old[int(a)], old[int(b)]): e for e, (a, b) in enumerate(zip(big.spec.gap_i, big.spec.gap_j))
          if int(a) in old and int(b) in old}
    w = big.w[:, [ci[(int(a), int(b))] for a, b in zip(small_spec.chem_i, small_spec.chem_j)]]
    g = big.g[:, [gi[(int(a), int(b))] for a, b in zip(small_spec.gap_i, small_spec.gap_j)]]
    idx = torch.as_tensor(keep)
    dale = None if big.dale_sign is None else big.dale_sign[:, idx]
    return Genome(small_spec, big.cfg, w, g, big.tau[:, idx], big.bias[:, idx], dale)


def test_deletion_matches_a_network_without_the_neuron(con):
    k = _gap_neuron(con)
    spec = BrainSpec.from_connectome(con)
    genome = _genome(spec)
    small_con, keep = reindexed_without(con, k)
    assert small_con.n == con.n - 1 and k not in keep
    small = _small_genome(genome, BrainSpec.from_connectome(small_con), keep)
    deleted = delete_neurons(genome, [[k]])
    big_brain, small_brain = Brain(deleted), Brain(small)
    cur = torch.randn(1, 2, con.n, generator=torch.Generator().manual_seed(1)) * 0.3
    vb, vs = big_brain.initial_state(2), small_brain.initial_state(2)
    for _ in range(30):
        vb, vs = big_brain.step(vb, cur), small_brain.step(vs, cur[..., keep])
    torch.testing.assert_close(vb[..., keep], vs, rtol=1e-5, atol=1e-6)


def test_deletion_is_per_strain_and_leaves_other_strains_alone(con):
    k = _gap_neuron(con)
    spec = BrainSpec.from_connectome(con)
    genome = _genome(spec, s=2)
    d = delete_neurons(genome, [[], [k]])
    torch.testing.assert_close(d.w[0], genome.w[0])
    torch.testing.assert_close(d.g[0], genome.g[0])
    touching = (spec.chem_i == k) | (spec.chem_j == k)
    assert torch.all(d.w[1, touching] == 0) and torch.all(d.w[1, ~touching] == genome.w[1, ~touching])
    gtouch = (spec.gap_i == k) | (spec.gap_j == k)
    assert torch.all(d.g[1, gtouch] == 0) and float(d.bias[1, k]) == 0.0


def test_deletion_differs_from_silencing_when_the_neuron_has_gap_junctions(con):
    k = _gap_neuron(con)
    spec = BrainSpec.from_connectome(con)
    genome = _genome(spec)
    cur = torch.full((1, 1, con.n), 0.3)
    a, b = Brain(delete_neurons(genome, [[k]])), Brain(genome).silence([[k]])
    va, vb = a.initial_state(1), b.initial_state(1)
    for _ in range(20):
        va, vb = a.step(va, cur), b.step(vb, cur)
    others = [i for i in range(con.n) if i != k]
    assert (va[0, 0, others] - vb[0, 0, others]).abs().max() > 1e-4


def test_without_neuron_keeps_indexing_and_drops_every_edge_touching_it(con):
    k = _gap_neuron(con)
    c = without_neuron(con, k)
    assert c.n == con.n and c.names == con.names
    assert c.chem[k].sum() == 0 and c.chem[:, k].sum() == 0 and c.gap[k].sum() == 0 and c.gap[:, k].sum() == 0
    mask = np.ones(con.n, bool)
    mask[k] = False
    np.testing.assert_array_equal(c.chem[np.ix_(mask, mask)], con.chem[np.ix_(mask, mask)])
