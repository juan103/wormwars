"""03a's reinsertion (DESIGN.md v7.1 §8, "Implementation tests"): deletion equals a network built without X; the union
mask with zeroed edges equals the network built with exactly that partner set, gap denominators included; the
background is bitwise unchanged; MIP's exact restoration; NIP's pinning; direction; gap symmetry."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.deletion import delete_neurons, reindexed_without, without_neuron
from wormwars.e03a import reinsert as R
from wormwars.e03a import search as S

# Declared tolerances. The union mask and the network built with exactly the same partners materialise identical
# dense matrices, so they must agree bitwise. A re-indexed network (n - 1 neurons) changes the matrix shapes and so
# the summation order: rtol 1e-5, atol 1e-6, as tests/test_deletion.py.
EXACT = dict(rtol=0.0, atol=0.0)
REINDEXED = dict(rtol=1e-5, atol=1e-6)


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def cfg():
    return Config()


def _genome(spec, cfg, seed=0, s=1):
    return Genome.random(spec, cfg.brain, s, generator=torch.Generator().manual_seed(seed))


def _target(con):
    """A neuron with chemical in, chemical out and gap partners."""
    for k in range(con.n):
        if (con.gap[k] > 0).sum() >= 2 and (con.chem[k] > 0).sum() >= 2 and (con.chem[:, k] > 0).sum() >= 2:
            return k
    raise AssertionError


def _random_state(reins, cfg, seed):
    pr = S.Problem(reins.K, R.true_counts(reins.con, reins.x), reins.self_loop)
    st = S.initial_states(pr, 3, cfg.brain, torch.Generator().manual_seed(seed))
    st.w_in += torch.randn(st.w_in.shape, generator=torch.Generator().manual_seed(seed + 1)) * 0.3
    st.g += 0.1 * torch.rand(st.g.shape, generator=torch.Generator().manual_seed(seed + 2))
    return S.clamp_(st, cfg.brain)


def _on_spec(src: Genome, spec: BrainSpec) -> Genome:
    """`src`'s parameters on another spec over the same neurons, by edge identity (absent edges must be zero)."""
    pc, pg = R.edge_positions(src.spec, "chem"), R.edge_positions(src.spec, "gap")
    qc = list(zip(spec.chem_i.tolist(), spec.chem_j.tolist()))
    qg = list(zip(spec.gap_i.tolist(), spec.gap_j.tolist()))
    w = src.w[:, [pc[e] for e in qc]]
    g = src.g[:, [pg[e] for e in qg]]
    dropped_c = [p for e, p in pc.items() if e not in set(qc)]
    dropped_g = [p for e, p in pg.items() if e not in set(qg)]
    assert torch.all(src.w[:, dropped_c] == 0) and torch.all(src.g[:, dropped_g] == 0)
    return src.with_params(spec=spec, w=w, g=g)


def _run(brain, cur, ticks=25):
    v = brain.initial_state(cur.shape[1])
    for _ in range(ticks):
        v = brain.step(v, cur)
    return v


def test_union_mask_equals_the_network_built_with_exactly_those_partners(con, cfg):
    x = _target(con)
    src = _genome(BrainSpec.from_connectome(con), cfg)
    reins = R.Reinsertion(con, x, src)
    st = _random_state(reins, cfg, 7)
    ug = reins.genome(st)
    cur = torch.randn(st.n, 2, con.n, generator=torch.Generator().manual_seed(3)) * 0.3
    for s in range(st.n):
        partners = {t: st.masks()[t][s].numpy() for t in R.TYPES}
        exact = BrainSpec.from_connectome(R.partner_connectome(con, x, partners))
        built = _on_spec(ug.select([s]), exact)
        Wu, Gu = ug.select([s]).dense()
        Wb, Gb = built.dense()
        assert torch.equal(Wu, Wb) and torch.equal(Gu, Gb)
        bu, bb = Brain(ug.select([s])), Brain(built)
        torch.testing.assert_close(bu.den, bb.den, **EXACT)  # gap conductances in the neighbours' denominators
        torch.testing.assert_close(_run(bu, cur[s:s + 1]), _run(bb, cur[s:s + 1]), **EXACT)


def test_an_absent_gap_partner_changes_its_neighbours_denominator_when_present(con, cfg):
    """Sabotage for the test above: the denominators do register a gap junction, so the comparison can fail."""
    x = _target(con)
    reins = R.Reinsertion(con, x, _genome(BrainSpec.from_connectome(con), cfg))
    st = _random_state(reins, cfg, 7).select([0])
    k = int(torch.nonzero(~st.m_gap[0])[0])
    st2 = st.clone()
    st2.m_gap[0, k] = True
    d1, d2 = Brain(reins.genome(st)).den, Brain(reins.genome(st2)).den
    assert d1[0, reins.cand[k]] != d2[0, reins.cand[k]] and d1[0, x] != d2[0, x]


def test_deletion_through_the_union_equals_a_network_without_x(con, cfg):
    x = _target(con)
    src = _genome(BrainSpec.from_connectome(con), cfg, seed=4)
    reins = R.Reinsertion(con, x, src)
    deleted = reins.genome(reins.empty_state())
    small_con, keep = reindexed_without(con, x)
    small = _on_spec_reindexed(src, BrainSpec.from_connectome(small_con), keep)
    cur = torch.randn(1, 2, con.n, generator=torch.Generator().manual_seed(1)) * 0.3
    torch.testing.assert_close(_run(Brain(deleted), cur)[..., keep], _run(Brain(small), cur[..., keep]), **REINDEXED)
    # and with `delete_neurons` on the intact graph, every neuron but X agrees bitwise
    a = _run(Brain(deleted), cur)
    b = _run(Brain(delete_neurons(src, [[x]])), cur)
    torch.testing.assert_close(a[..., keep], b[..., keep], **EXACT)


def _on_spec_reindexed(big: Genome, small_spec: BrainSpec, keep: np.ndarray) -> Genome:
    old = {int(n): i for i, n in enumerate(keep)}
    ci = {(old[int(a)], old[int(b)]): e for e, (a, b) in enumerate(zip(big.spec.chem_i, big.spec.chem_j))
          if int(a) in old and int(b) in old}
    gi = {(old[int(a)], old[int(b)]): e for e, (a, b) in enumerate(zip(big.spec.gap_i, big.spec.gap_j))
          if int(a) in old and int(b) in old}
    w = big.w[:, [ci[(int(a), int(b))] for a, b in zip(small_spec.chem_i, small_spec.chem_j)]]
    g = big.g[:, [gi[(int(a), int(b))] for a, b in zip(small_spec.gap_i, small_spec.gap_j)]]
    idx = torch.as_tensor(keep)
    return Genome(small_spec, big.cfg, w, g, big.tau[:, idx], big.bias[:, idx], None)


def test_the_background_is_bitwise_unchanged_by_reinsertion(con, cfg):
    x = _target(con)
    src = _genome(BrainSpec.from_connectome(con), cfg, seed=5)
    before = src.clone()
    reins = R.Reinsertion(con, x, src)
    for seed in (1, 2):
        ug = reins.genome(_random_state(reins, cfg, seed))
        pu_c, pu_g = R.edge_positions(reins.spec, "chem"), R.edge_positions(reins.spec, "gap")
        for p, (a, b) in enumerate(zip(src.spec.chem_i.tolist(), src.spec.chem_j.tolist())):
            if x not in (a, b):
                assert torch.equal(ug.w[:, pu_c[(a, b)]], src.w[0, p].expand(ug.n_strains))
        for p, (a, b) in enumerate(zip(src.spec.gap_i.tolist(), src.spec.gap_j.tolist())):
            if x not in (a, b):
                assert torch.equal(ug.g[:, pu_g[(a, b)]], src.g[0, p].expand(ug.n_strains))
        others = [i for i in range(con.n) if i != x]
        assert torch.equal(ug.tau[:, others], src.tau[:, others].expand(ug.n_strains, -1))
        assert torch.equal(ug.bias[:, others], src.bias[:, others].expand(ug.n_strains, -1))
    assert all(torch.equal(getattr(before, k), getattr(src, k)) for k in ("w", "g", "tau", "bias"))


def test_mip_exact_restoration_reproduces_the_intact_brain(con, cfg):
    x = _target(con)
    src = _genome(BrainSpec.from_connectome(con), cfg, seed=6)
    reins = R.Reinsertion(con, x, src)
    restored = reins.genome(reins.saved_state(src))
    W1, G1 = src.dense()
    W2, G2 = restored.dense()
    assert torch.equal(W1, W2) and torch.equal(G1, G2)
    assert torch.equal(src.tau, restored.tau) and torch.equal(src.bias, restored.bias)
    cur = torch.randn(1, 2, con.n, generator=torch.Generator().manual_seed(2)) * 0.3
    torch.testing.assert_close(_run(Brain(src), cur), _run(Brain(restored), cur), **EXACT)


def test_restoration_with_a_self_connection(con, cfg):
    diag = np.nonzero(np.diag(con.chem) > 0)[0]
    if not len(diag):
        pytest.skip("no chemical self-connection in this dataset")
    x = int(diag[0])
    src = _genome(BrainSpec.from_connectome(con), cfg, seed=8)
    reins = R.Reinsertion(con, x, src)
    assert reins.self_loop and reins.pos_self is not None
    restored = reins.genome(reins.saved_state(src))
    assert torch.equal(src.dense()[0], restored.dense()[0])


def test_nip_pinning_holds_through_initialisation_and_mutation(con, cfg):
    x = _target(con)
    spec = BrainSpec.from_connectome(without_neuron(con, x))
    g = _genome(spec, cfg, seed=9, s=4)
    assert R.x_edges_zero(g, x)
    gen = torch.Generator().manual_seed(1)
    for _ in range(5):
        g.mutate(cfg.mutation, gen)
        assert R.x_edges_zero(g, x)
    # NIP's brain reinserts like any other
    reins = R.Reinsertion(con, x, g.select([0]))
    assert R.x_edges_zero(reins.genome(reins.empty_state()), x)


def test_pinning_check_fails_when_x_keeps_its_edges(con, cfg):
    """Sabotage: on the intact mask, initialisation gives X's edges weights, and the check says so."""
    x = _target(con)
    g = _genome(BrainSpec.from_connectome(con), cfg, seed=9)
    assert not R.x_edges_zero(g, x)


def test_a_source_on_another_graph_is_refused(con, cfg):
    x = _target(con)
    other = con.with_masks(np.roll(con.chem, 1, axis=0), con.gap, "rolled")
    g = _genome(BrainSpec.from_connectome(other), cfg)
    with pytest.raises(ValueError):
        R.Reinsertion(con, x, g)


def test_direction_in_partners_drive_x_and_out_partners_are_driven_by_it(con, cfg):
    x = _target(con)
    reins = R.Reinsertion(con, x, _genome(BrainSpec.from_connectome(con), cfg))
    st = reins.empty_state()
    k = 0
    c = int(reins.cand[k])
    st.m_in[0, k], st.w_in[0, k] = True, 1.5
    W, _ = reins.genome(st).dense()
    assert float(W[0, c, x]) == 1.5 and float(W[0, x, c]) == 0.0  # W[pre, post]
    st2 = reins.empty_state()
    st2.m_out[0, k], st2.w_out[0, k] = True, -1.25
    W2, _ = reins.genome(st2).dense()
    assert float(W2[0, x, c]) == -1.25 and float(W2[0, c, x]) == 0.0
    # behaviourally: driving c moves X through an in-edge, and not through an out-edge
    cur = torch.zeros(1, 1, con.n)
    cur[..., c] = 2.0
    vx_in = _run(Brain(reins.genome(st)), cur)[0, 0, x]
    vx_out = _run(Brain(reins.genome(st2)), cur)[0, 0, x]
    vx_none = _run(Brain(reins.genome(reins.empty_state())), cur)[0, 0, x]
    assert abs(float(vx_in - vx_none)) > 1e-3 and float(vx_out) == float(vx_none)


def test_gap_junctions_are_symmetric_after_moves(con, cfg):
    x = _target(con)
    reins = R.Reinsertion(con, x, _genome(BrainSpec.from_connectome(con), cfg))
    pr = S.Problem(reins.K, R.true_counts(con, x), reins.self_loop)
    sc = S.SearchConfig(p_move=1.0, p_weights=0.0, p_tau_bias=0.0, max_moves=3)
    gen = torch.Generator().manual_seed(4)
    st = S.initial_states(pr, 4, cfg.brain, gen)
    for _ in range(10):
        st, _ = S.propose(st, pr, sc, cfg.brain, cfg.mutation, gen)
        st = st.select(list(range(0, st.n, sc.offspring)))
        _, G = reins.genome(st).dense()
        assert torch.equal(G, G.transpose(1, 2))
        on = st.m_gap
        gx = G[:, x, torch.as_tensor(reins.cand)]
        assert torch.equal(gx > 0, on)
