"""E4's output gate and E-G (docs/E4/E4-DESIGN.md v3 §1).

- `Brain.gate_outputs`: a declared set of edges per module, multiplied per wey by g_A = [q ≥ 0] (the latch's
  state) or g_B = 1 − g_A. Unset, the step is bitwise unchanged.
- `organism.engineered_gated`: E with ungated comparators (biases 0, Q → comparator edges 0) and the 32 cross-link
  slots at weight 0; its gated edges are each module's comparator → motor edges.
"""

from __future__ import annotations

import pytest
import torch

from wormwars import graft as G
from wormwars.brain import Brain, BrainSpec
from wormwars.connectome import load_connectome
from wormwars.e3 import organism as O
from wormwars.e3.task import shuttle_config
from wormwars.e4s import arms as A
from wormwars.e4s import comparator as C


@pytest.fixture(scope="module")
def eg():
    con, l1 = load_connectome(), A.load_l1()
    bcfg = shuttle_config().brain
    m = O.engineered_gated(l1)
    ext = G.graft_connectome(con, m)
    genome = C.carrier_genome(ext, m, bcfg, forward=1.0, turn=0.2)
    return m, ext, genome


def _gated_brain(genome, ext, m):
    b = Brain(genome)
    return b.gate_outputs(O.gate_spec(ext, m))


def _zeroed(genome, ext, edges):
    """The same genome with the named edges' weights set to 0."""
    w = genome.w.clone()
    spec = genome.spec
    for (pre, post) in edges:
        k = int(((spec.chem_i == ext.index(pre)) & (spec.chem_j == ext.index(post))).nonzero()[0, 0])
        w[:, k] = 0.0
    return genome.with_params(w=w)


def _state(ext, n_weys, q_sign, seed=0):
    g = torch.Generator().manual_seed(seed)
    v = torch.randn(1, n_weys, ext.n, generator=g) * 2.0
    v[..., ext.index(O.Q)] = q_sign
    return v


def test_the_module_has_32_cross_link_slots_at_zero(eg):
    m, ext, genome = eg
    a = [n for n in m.neurons if n.startswith("E3_A_")]
    b = [n for n in m.neurons if n.startswith("E3_B_")]
    cross = {(x, y) for x, y, w in m.synapses if (x in a and y in b) or (x in b and y in a)}
    assert len(a) == len(b) == 4 and len(cross) == 32
    assert all(w == 0.0 for x, y, w in m.synapses if (x, y) in cross)
    assert set(O.cross_links(m)) == cross


def test_the_comparators_are_ungated(eg):
    m, ext, genome = eg
    for c in O.COMPARATORS:
        assert m.bias[c] == 0.0
    assert all(w == 0.0 for x, y, w in m.synapses if x == O.Q and y in O.COMPARATORS)


@pytest.mark.parametrize("q_sign, off", [(1.0, "B"), (-1.0, "A")])
def test_a_gated_step_equals_the_inactive_modules_motor_edges_at_zero(eg, q_sign, off):
    m, ext, genome = eg
    v = _state(ext, 5, q_sign)
    cur = torch.randn(1, 5, ext.n, generator=torch.Generator().manual_seed(1))
    got = _gated_brain(genome, ext, m).step(v, cur, substeps=1)
    want = Brain(_zeroed(genome, ext, O.motor_edges(m, off))).step(v, cur, substeps=1)
    assert torch.allclose(got, want, atol=1e-6)


def test_q_at_zero_is_mode_a(eg):
    m, ext, genome = eg
    v = _state(ext, 3, 0.0)
    cur = torch.zeros(1, 3, ext.n)
    got = _gated_brain(genome, ext, m).step(v, cur, substeps=1)
    want = Brain(_zeroed(genome, ext, O.motor_edges(m, "B"))).step(v, cur, substeps=1)
    assert torch.allclose(got, want, atol=1e-6)


def test_modes_are_per_wey(eg):
    m, ext, genome = eg
    v = torch.cat([_state(ext, 2, 1.0, seed=3), _state(ext, 2, -1.0, seed=4)], dim=1)
    cur = torch.zeros(1, 4, ext.n)
    got = _gated_brain(genome, ext, m).step(v, cur, substeps=1)
    a_on = Brain(_zeroed(genome, ext, O.motor_edges(m, "B"))).step(v, cur, substeps=1)
    b_on = Brain(_zeroed(genome, ext, O.motor_edges(m, "A"))).step(v, cur, substeps=1)
    assert torch.allclose(got[:, :2], a_on[:, :2], atol=1e-6) and torch.allclose(got[:, 2:], b_on[:, 2:], atol=1e-6)


def test_the_gate_unset_is_bitwise_unchanged(eg):
    m, ext, genome = eg
    v = _state(ext, 4, 1.0, seed=5)
    cur = torch.randn(1, 4, ext.n, generator=torch.Generator().manual_seed(6))
    plain = Brain(genome).step(v, cur)
    unset = Brain(genome).gate_outputs(None).step(v, cur)
    assert torch.equal(plain, unset)


def test_the_check_can_fail(eg):
    """Sabotage: gating the wrong module (A off while q > 0) differs from zeroing B's edges."""
    m, ext, genome = eg
    v = _state(ext, 5, 1.0, seed=7)
    cur = torch.zeros(1, 5, ext.n)
    spec = O.gate_spec(ext, m)
    wrong = Brain(genome).gate_outputs({"q": spec["q"], "a": spec["b"], "b": spec["a"]}).step(v, cur, substeps=1)
    want = Brain(_zeroed(genome, ext, O.motor_edges(m, "B"))).step(v, cur, substeps=1)
    assert not torch.allclose(wrong, want, atol=1e-6)
