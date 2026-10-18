"""03a's search (DESIGN.md v7.1 §6, §8): degrees constant, refits never move, the information boundary (with sabotage
checks), a planted optimum, common random numbers, and the replica-exchange rules."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e03a import null as N
from wormwars.e03a import reinsert as R
from wormwars.e03a import search as S
from wormwars.e1.task import task_n_config
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def cfg():
    return Config()


def _target(con):
    for k in range(con.n):
        if (con.gap[k] > 0).sum() >= 2 and (con.chem[k] > 0).sum() >= 2 and (con.chem[:, k] > 0).sum() >= 2:
            return k
    raise AssertionError


def _rewired(con, x, seed):
    """`con` with X's partners redrawn, the same number per type: a different truth, every allowed input the same."""
    rng = np.random.default_rng(seed)
    chem, gap = con.chem.copy(), con.gap.copy()
    c = R.candidates(con.n, x)
    tr = R.truth(con, x)
    chem[x, :] = chem[:, x] = 0
    gap[x, :] = gap[:, x] = 0
    for t in R.TYPES:
        pick = rng.choice(c, size=int(tr[t].sum()), replace=False)
        if t == "in":
            chem[pick, x] = 1.0
        elif t == "out":
            chem[x, pick] = 1.0
        else:
            gap[pick, x] = gap[x, pick] = 1.0
    if con.chem[x, x] > 0:
        chem[x, x] = con.chem[x, x]
    out = con.with_masks(chem, gap, f"{con.label}-rewired")
    assert any(not np.array_equal(R.truth(out, x)[t], tr[t]) for t in R.TYPES)
    assert R.true_counts(out, x) == R.true_counts(con, x)
    return out


def _fixed_fitness(asks):
    """A fitness that reads states but not the truth: deterministic in the partner masks and weights."""
    out = []
    for _, st, ids in asks:
        v = (st.w_in.abs() * st.m_in).sum(1) + st.m_out[:, ::7].sum(1) + 0.1 * st.bias + 0.001 * float(ids.sum() % 97)
        out.append(v.numpy().astype(np.float64))
    return out


def _free_trajectory(con, x, src, cfg, factory, gens=6):
    """Every free search's initial states and every proposal it makes, under `_fixed_fitness`."""
    reins = R.Reinsertion(con, x, src)
    iface = load_interface(con)
    strat = N.strata(con, iface, x)
    searches = factory(reins, R.truth(con, x), strat)
    free = [s for s in searches if s.label.startswith("free")]
    seen = [[s.current.clone() for s in free]]
    for _ in range(gens):
        asks = [(s, *s.ask()) for s in free]
        seen.append([a[1].clone() for a in asks])
        for (s, _, _), sc in zip(asks, _fixed_fitness(asks)):
            s.tell(sc)
    return reins, seen


def _factory(cfg, scfg):
    def make(reins, truth, strat):
        return S.target_brain_searches(reins, truth, strat, scfg, cfg.brain, cfg.mutation, seed=11,
                                       plan={"refit": 1, "random": 1, "free": 2}, world_span=1000)
    return make


def _boundary_holds(con, x, cfg, factory) -> bool:
    other = _rewired(con, x, 3)
    src_a = Genome.random(BrainSpec.from_connectome(con), cfg.brain, 1, generator=torch.Generator().manual_seed(0))
    # the same background: the source brain's parameters on edges not touching X are what the arm hands over
    ra, sa = _free_trajectory(con, x, src_a, cfg, factory)
    src_b = R.Reinsertion(con, x, src_a).genome(R.Reinsertion(con, x, src_a).empty_state())
    src_b = _with_graph(src_b, other, x)
    rb, sb = _free_trajectory(other, x, src_b, cfg, factory)
    same_union = (torch.equal(ra.spec.chem_i, rb.spec.chem_i) and torch.equal(ra.spec.chem_j, rb.spec.chem_j)
                  and torch.equal(ra.spec.gap_i, rb.spec.gap_i) and torch.equal(ra.w_bg, rb.w_bg)
                  and torch.equal(ra.g_bg, rb.g_bg))
    others = [i for i in range(con.n) if i != x]
    same_bg = torch.equal(ra.tau_bg[others], rb.tau_bg[others]) and torch.equal(ra.bias_bg[others], rb.bias_bg[others])
    same_free = all(a.equal(b) for ga, gb in zip(sa, sb) for a, b in zip(ga, gb))
    return same_union and same_bg and same_free


def _with_graph(union_genome, graph, x):
    """A one-strain genome on `graph` carrying `union_genome`'s non-X parameters (X's own edges at zero)."""
    spec = BrainSpec.from_connectome(graph)
    pc, pg = R.edge_positions(union_genome.spec, "chem"), R.edge_positions(union_genome.spec, "gap")
    w = torch.stack([union_genome.w[0, pc[(a, b)]] if x not in (a, b) else torch.tensor(0.0)
                     for a, b in zip(spec.chem_i.tolist(), spec.chem_j.tolist())]).unsqueeze(0)
    g = torch.stack([union_genome.g[0, pg[(a, b)]] if x not in (a, b) else torch.tensor(0.0)
                     for a, b in zip(spec.gap_i.tolist(), spec.gap_j.tolist())]).unsqueeze(0)
    return union_genome.with_params(spec=spec, w=w, g=g)


def test_information_boundary_free_searches_do_not_see_the_truth(con, cfg):
    x = _target(con)
    assert _boundary_holds(con, x, cfg, _factory(cfg, S.SearchConfig(generations=6)))


def test_information_boundary_sabotage_a_leaking_initialisation_is_caught(con, cfg):
    """Sabotage: a factory whose free searches start from the true partners must fail the boundary check."""
    x = _target(con)
    scfg = S.SearchConfig(generations=6)

    def leaky(reins, truth, strat):
        out = S.target_brain_searches(reins, truth, strat, scfg, cfg.brain, cfg.mutation, seed=11,
                                      plan={"refit": 1, "random": 1, "free": 0}, world_span=1000)
        pr = S.problem_of(reins, {t: int(np.asarray(truth[t]).sum()) for t in R.TYPES})
        for i in range(2):
            s = S.ReplicaExchange(pr, scfg, cfg.brain, cfg.mutation, S.search_seed(11, "free", i), world_span=1000,
                                  partners=None, label=f"free-{i}")
            s.current = S.initial_states(pr, scfg.replicas, cfg.brain, torch.Generator().manual_seed(0),
                                         partners={t: np.asarray(truth[t], dtype=bool) for t in R.TYPES})
            out.append(s)
        return out

    assert not _boundary_holds(con, x, cfg, leaky)


def test_information_boundary_sabotage_a_leaking_proposal_is_caught(con, cfg, monkeypatch):
    """Sabotage: a proposal that peeks at the truth (here, through a module global) fails the check."""
    x = _target(con)
    real = S.propose
    leak = {}

    def peeking(current, problem, scfg, bcfg, mcfg, gen, moves=True):
        off, kinds = real(current, problem, scfg, bcfg, mcfg, gen, moves)
        if moves and "truth" in leak:
            off.bias += 1e-3 * float(np.asarray(leak["truth"]["in"]).nonzero()[0][0])
        return off, kinds

    def factory(reins, truth, strat):
        leak["truth"] = truth
        return _factory(cfg, S.SearchConfig(generations=6))(reins, truth, strat)

    monkeypatch.setattr(S, "propose", peeking)
    assert not _boundary_holds(con, x, cfg, factory)


def test_partner_counts_never_change_and_refits_never_move(con, cfg):
    x = _target(con)
    reins = R.Reinsertion(con, x, Genome.random(BrainSpec.from_connectome(con), cfg.brain, 1,
                                                generator=torch.Generator().manual_seed(0)))
    truth = R.truth(con, x)
    strat = N.strata(con, load_interface(con), x)
    scfg = S.SearchConfig(generations=15, max_moves=3, p_move=0.6, p_weights=0.2, p_tau_bias=0.2)
    searches = S.target_brain_searches(reins, truth, strat, scfg, cfg.brain, cfg.mutation, seed=2,
                                       plan={"refit": 1, "random": 1, "free": 1}, world_span=10)
    rng = np.random.default_rng(0)
    counts = R.true_counts(con, x)
    start = {s.label: {t: s.current.masks()[t].clone() for t in R.TYPES} for s in searches}
    for _ in range(scfg.generations):
        for s in searches:
            st, _ = s.ask()
            for t in R.TYPES:
                assert torch.all(st.counts()[t] == counts[t])
            if s.refit:
                for t in R.TYPES:
                    assert torch.equal(st.masks()[t], start[s.label][t][:1].expand_as(st.masks()[t]))
            s.tell(rng.random(st.n))
    free = searches[-1]
    assert any(not torch.equal(free.current.masks()[t], start[free.label][t]) for t in R.TYPES)


def test_random_partner_refits_keep_the_truths_strata_composition(con):
    x = _target(con)
    strat = N.strata(con, load_interface(con), x)
    truth = R.truth(con, x)
    p = S.random_partners(truth, strat, np.random.default_rng(1))
    for t in R.TYPES:
        for s in np.unique(strat):
            assert p[t][strat == s].sum() == truth[t][strat == s].sum()
    assert any(not np.array_equal(p[t], truth[t]) for t in R.TYPES)


def test_planted_optimum_is_found(cfg):
    """A small synthetic problem: fitness is the overlap with a planted partner set."""
    K = 16
    counts = {"in": 3, "out": 2, "gap": 2}
    rng = np.random.default_rng(5)
    planted = {t: np.zeros(K, bool) for t in R.TYPES}
    for t in R.TYPES:
        planted[t][rng.choice(K, counts[t], replace=False)] = True
    pr = S.Problem(K, counts, False)
    scfg = S.SearchConfig(generations=100, p_move=0.6, p_weights=0.2, p_tau_bias=0.2)

    def overlap(asks):
        return [sum((st.masks()[t].numpy() & planted[t]).sum(1) for t in R.TYPES).astype(float) for _, st, _ in asks]

    found = 0
    for seed in range(3):
        s = S.free_search(pr, scfg, cfg.brain, cfg.mutation, seed)
        S.run_lockstep([s], overlap)
        r = s.result()
        found += all(np.array_equal(r.masks()[t][0].numpy(), planted[t]) for t in R.TYPES)
    assert found == 3


def test_planted_optimum_is_not_found_without_moves(cfg):
    """Sabotage for the planted test: with moves disabled the search cannot reach it."""
    K = 30
    counts = {"in": 3, "out": 2, "gap": 2}
    planted = {t: np.zeros(K, bool) for t in R.TYPES}
    for t in R.TYPES:
        planted[t][K - counts[t]:] = True
    pr = S.Problem(K, counts, False)
    scfg = S.SearchConfig(generations=30, p_move=0.0, p_weights=0.5, p_tau_bias=0.5)

    def overlap(asks):
        return [sum((st.masks()[t].numpy() & planted[t]).sum(1) for t in R.TYPES).astype(float) for _, st, _ in asks]

    s = S.free_search(pr, scfg, cfg.brain, cfg.mutation, 0)
    start = [{t: s.current.masks()[t][r].clone() for t in R.TYPES} for r in range(scfg.replicas)]
    S.run_lockstep([s], overlap)
    # replicas swap states, so the result is one of the initial partner sets, never the planted one
    assert any(all(torch.equal(s.result().masks()[t][0], st[t]) for t in R.TYPES) for st in start)
    assert s.trace.scores[-1][0] < sum(counts.values())


def test_acceptance_and_swaps_follow_the_rules(cfg):
    pr = S.Problem(10, {"in": 2, "out": 2, "gap": 1}, False)
    scfg = S.SearchConfig(generations=10, swap_every=5)
    s = S.free_search(pr, scfg, cfg.brain, cfg.mutation, 0)
    R_, lam = scfg.replicas, scfg.offspring
    # generation 0: replica r's offspring 3 beats its current state; everything else worse
    st, _ = s.ask()
    sc = np.zeros(st.n)
    sc[:R_] = 1.0
    for r in range(R_):
        sc[R_ + r * lam + 3] = 2.0
    s.tell(sc)
    for r in range(R_):
        assert s.current.select([r]).equal(st.select([R_ + r * lam + 3]))
    assert s.trace.accepted[0] == [True] * R_
    # an offspring far worse is rejected at every temperature (exp(-1000 / T) is 0)
    for g in range(1, 4):
        cur = s.current.clone()
        st, _ = s.ask()
        sc = np.full(st.n, -1000.0)
        sc[:R_] = 0.0
        s.tell(sc)
        assert s.current.equal(cur)
    # generation 4 ends a swap period: the hotter replica of each pair is better, so the pair always swaps
    cur = s.current.clone()
    st, _ = s.ask()
    sc = np.full(st.n, -1000.0)
    sc[:R_] = np.arange(R_, dtype=float)
    s.tell(sc)
    parity = (5 // scfg.swap_every) % 2
    expect = list(range(R_))
    for m in range(parity, R_ - 1, 2):
        expect[m], expect[m + 1] = expect[m + 1], expect[m]
    assert s.current.equal(cur.select(expect))
    assert all(ok for _, ok in s.trace.swaps[4])


def test_no_task_accepts_every_best_offspring_and_every_swap(cfg):
    pr = S.Problem(20, {"in": 2, "out": 2, "gap": 1}, False)
    s = S.free_search(pr, S.SearchConfig(generations=20), cfg.brain, cfg.mutation, 3)
    S.run_lockstep([s], S.no_task)
    assert all(all(a) for a in s.trace.accepted)
    assert all(ok for sw in s.trace.swaps for _, ok in sw) and sum(len(sw) for sw in s.trace.swaps) > 0


def test_common_random_numbers_every_state_of_a_generation_plays_the_same_worlds(con, cfg):
    x = _target(con)
    src = Genome.random(BrainSpec.from_connectome(con), cfg.brain, 1, generator=torch.Generator().manual_seed(0))
    reins = R.Reinsertion(con, x, src)
    pr = S.problem_of(reins, R.true_counts(con, x))
    searches = [S.free_search(pr, S.SearchConfig(generations=2, worlds=4), cfg.brain, cfg.mutation, i,
                              world_base=1000, world_span=10_000) for i in range(2)]
    seen = []

    class Res:
        def __init__(self, n, w):
            self.score = np.zeros((n, w))
            self.progress = np.zeros((n, w))

    def fake(c, i, genome, ids, seed, device, chunk_worlds=None):
        seen.append(ids.copy())
        return Res(genome.n_strains, ids.shape[1])

    ev = S.simulator(cfg, None, lambda s: reins, world_seed=1, rollout_fn=fake)
    S.run_lockstep(searches, ev)
    n = S.SearchConfig().replicas * (1 + S.SearchConfig().offspring)
    for g, ids in enumerate(seen):
        for k, s in enumerate(searches):
            rows = ids[k * n:(k + 1) * n]
            assert (rows == S.search_worlds(s.seed, g, 4, 1000, 10_000)).all()
    assert not np.array_equal(seen[0][:n], seen[0][n:])  # each search its own schedule


def test_identical_states_score_identically_in_one_batch(con, cfg):
    """Paired evaluation in the real simulator: two copies of a state on the same worlds get the same counts."""
    tcfg = task_n_config(sigma=6.0, amplitude=1.0, radius=1.5, separation=8.0, horizon=30)
    tcfg.world.food_sensing = "mono"
    iface = load_interface(con)
    x = _target(con)
    src = Genome.random(BrainSpec.from_connectome(con), tcfg.brain, 1, generator=torch.Generator().manual_seed(0))
    reins = R.Reinsertion(con, x, src)
    pr = S.problem_of(reins, R.true_counts(con, x))
    st = S.initial_states(pr, 1, tcfg.brain, torch.Generator().manual_seed(1))
    two = R.XState.cat([st, st])
    ev = S.simulator(tcfg, iface, lambda s: reins, world_seed=5)

    class Dummy:
        pass

    sc = ev([(Dummy(), two, np.arange(4))])[0]
    assert sc[0] == sc[1]


def test_ranking_is_the_mean_absolute_final_weight_over_free_searches():
    K = 4
    z = torch.zeros(1, K, dtype=torch.bool)

    def st(m_in, w_in):
        f = torch.zeros(1, K)
        return R.XState(torch.tensor([m_in]), z.clone(), z.clone(), torch.tensor([w_in]), f, f.clone(),
                        torch.ones(1), torch.zeros(1), torch.zeros(1))

    a = st([True, False, True, False], [0.5, 9.0, -1.0, 0.0])
    b = st([True, True, False, False], [-0.25, 2.0, 7.0, 0.0])
    r = S.ranking([a, b])
    np.testing.assert_allclose(r["in"], [0.375, 1.0, 0.5, 0.0])
    np.testing.assert_allclose(r["out"], 0.0)


def test_the_simulator_moves_genomes_to_the_requested_device(con, cfg):
    """Astra's blocking finding: `rollout` does not move a genome, so the evaluator must (checked with the meta
    device, so the test runs without CUDA)."""
    x = _target(con)
    reins = R.Reinsertion(con, x, Genome.random(BrainSpec.from_connectome(con), cfg.brain, 1,
                                                generator=torch.Generator().manual_seed(0)))
    pr = S.problem_of(reins, R.true_counts(con, x))
    seen = []

    class Res:
        def __init__(self, n, w):
            self.score, self.progress = np.zeros((n, w)), np.zeros((n, w))

    def fake(c, i, genome, ids, seed, device, chunk_worlds=None):
        seen.append((genome.w.device.type, genome.spec.chem_i.device.type, device))
        return Res(genome.n_strains, ids.shape[1])

    s = S.free_search(pr, S.SearchConfig(generations=1, worlds=2), cfg.brain, cfg.mutation, 0)
    S.run_lockstep([s], S.simulator(cfg, None, lambda _: reins, world_seed=1, device="meta", rollout_fn=fake))
    assert seen == [("meta", "meta", "meta")]


@pytest.mark.gpu
def test_a_search_generation_runs_on_cuda(con):
    if not torch.cuda.is_available():
        pytest.skip("no CUDA")
    tcfg = task_n_config(sigma=6.0, amplitude=1.0, radius=1.5, separation=8.0, horizon=10)
    tcfg.world.food_sensing = "mono"
    x = _target(con)
    reins = R.Reinsertion(con, x, Genome.random(BrainSpec.from_connectome(con), tcfg.brain, 1,
                                                generator=torch.Generator().manual_seed(0)))
    s = S.free_search(S.problem_of(reins, R.true_counts(con, x)), S.SearchConfig(generations=1, worlds=2),
                      tcfg.brain, tcfg.mutation, 0, world_span=10)
    S.run_lockstep([s], S.simulator(tcfg, load_interface(con), lambda _: reins, world_seed=1, device="cuda"))
    assert s.done


def test_metropolis_acceptance_has_the_registered_probability(cfg):
    """A worse best offspring, d = -T ln 2 below the current state, is accepted half the time (Astra: intermediate
    probabilities and the temperature scaling were untested)."""
    pr = S.Problem(10, {"in": 2, "out": 2, "gap": 1}, False)
    scfg = S.SearchConfig(generations=400, swap_every=10_000)
    s = S.free_search(pr, scfg, cfg.brain, cfg.mutation, 1)
    R_, lam, T_ = scfg.replicas, scfg.offspring, np.array(scfg.temperatures)
    for _ in range(scfg.generations):
        st, _ = s.ask()
        sc = np.full(st.n, -1e9)
        sc[:R_] = 0.0
        sc[R_ + np.arange(R_) * lam] = -T_ * np.log(2.0)  # each replica's best offspring
        s.tell(sc)
    rate = np.mean(s.trace.accepted, axis=0)
    assert np.all(np.abs(rate - 0.5) < 0.08)


def test_adverse_swaps_have_the_registered_probability_and_both_parities_occur(cfg):
    pr = S.Problem(10, {"in": 2, "out": 2, "gap": 1}, False)
    scfg = S.SearchConfig(generations=2000, swap_every=1, temperatures=(1.0, 2.0, 4.0, 8.0))
    s = S.free_search(pr, scfg, cfg.brain, cfg.mutation, 2)
    R_ = scfg.replicas
    a = np.log(2.0) / (1.0 / 1.0 - 1.0 / 2.0)  # s_0 - s_1 that makes the (0, 1) swap probability exactly 1/2
    for _ in range(scfg.generations):
        st, _ = s.ask()
        sc = np.full(st.n, -1e9)
        sc[:R_] = [a, 0.0, -100.0, -200.0]  # pair (0, 1) adverse at 1/2; the others favourable or not
        s.tell(sc)
    pairs = [m for sw in s.trace.swaps for m, _ in sw]
    assert set(pairs) == {0, 1, 2}  # even pairs (0, 1), (2, 3) and the odd pair (1, 2), alternating
    first = [ok for sw in s.trace.swaps for m, ok in sw if m == 0]
    assert abs(np.mean(first) - 0.5) < 0.05


def test_the_result_is_the_coldest_replica(cfg):
    pr = S.Problem(10, {"in": 2, "out": 2, "gap": 1}, False)
    s = S.free_search(pr, S.SearchConfig(generations=3), cfg.brain, cfg.mutation, 3)
    S.run_lockstep([s], lambda asks: [np.random.default_rng(0).random(st.n) for _, st, _ in asks])
    assert s.result().equal(s.current.select([0]))


def test_snapshots_hold_the_state_after_that_generation_and_q_starts_at_generation_0(cfg):
    pr = S.Problem(20, {"in": 3, "out": 2, "gap": 1}, False)
    f = lambda asks: [st.m_in[:, :5].sum(1).numpy().astype(float) for _, st, _ in asks]  # noqa: E731
    a = S.free_search(pr, S.SearchConfig(generations=6), cfg.brain, cfg.mutation, 4, snapshot_at=(3,))
    b = S.free_search(pr, S.SearchConfig(generations=3), cfg.brain, cfg.mutation, 4)
    init = {t: a.current.masks()[t][0].clone() for t in R.TYPES}
    S.run_lockstep([a], f)
    S.run_lockstep([b], f)
    assert a.snapshots[3].equal(b.result())
    assert all(torch.equal(a.trace.initial_cold[t], init[t]) for t in R.TYPES)
