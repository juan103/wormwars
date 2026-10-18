"""03a's recovery statistic and stratified null (DESIGN.md v7.1 §6, §8): the strata rules, the permutations, the AUC,
the support, and the no-task control's AUCs against the null."""

from __future__ import annotations

from itertools import permutations as all_perms

import numpy as np
import pytest
import torch

from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e03a import null as N
from wormwars.e03a import reinsert as R
from wormwars.e03a import search as S
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def iface(con):
    return load_interface(con)


def test_kinds_put_the_pump_motors_with_motors(con, iface):
    k = N.kinds(con, iface)
    for name in ("MCL", "MCR"):
        assert N.KINDS[k[con.index(name)]] == "motor" and con.classes[con.index(name)] == "pharyngeal"
    for i in iface.sensor_neuron:
        assert N.KINDS[k[int(i)]] == "sensor"
    others = [i for i in range(con.n) if i not in set(iface.mapped_neurons)]
    assert all(N.KINDS[k[i]] == ("pharyngeal" if con.classes[i] == "pharyngeal" else "other") for i in others)


def test_tertiles_split_after_floor_ranks():
    np.testing.assert_array_equal(N.tertile_bins(np.arange(9)), [0, 0, 0, 1, 1, 1, 2, 2, 2])
    np.testing.assert_array_equal(N.tertile_bins(np.arange(10)), [0, 0, 0, 1, 1, 1, 2, 2, 2, 2])


def test_a_tied_group_goes_wholly_to_the_lower_bin():
    deg = np.array([1, 2, 3, 3, 3, 3, 7, 8, 9])  # ranks 2..5 are tied at 3, straddling the first boundary (after 3)
    b = N.tertile_bins(deg)
    assert len(set(b[deg == 3])) == 1 and b[deg == 3][0] == 0


def test_small_bins_merge_downward_and_the_lowest_upward():
    deg = np.array([0, 5, 5, 5, 5, 6, 6, 6, 7, 7])  # bins of 5, 3 and 2: the top one joins the one below
    b = N.tertile_bins(deg)
    np.testing.assert_array_equal(b, [0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    deg = np.array([0, 1, 2, 2, 3, 3, 3])  # bins of 2, 2 and 3: the lowest joins the one above
    b = N.tertile_bins(deg)
    np.testing.assert_array_equal(b, [0, 0, 0, 0, 1, 1, 1])
    deg = np.array([0, 1, 2, 2, 3, 3])  # 2, 2, 2: merges until every bin has 3, here one bin
    np.testing.assert_array_equal(N.tertile_bins(deg), np.zeros(6, int))


def test_degree_ignores_x_and_self_connections(con):
    x = 10
    d = N.degrees_without(con, x)
    assert d[x] == 0
    chem = (con.chem > 0).copy()
    gap = (con.gap > 0).copy()
    chem[x, :] = chem[:, x] = False
    gap[x, :] = gap[:, x] = False
    np.fill_diagonal(chem, False)
    i = 20
    assert d[i] == chem[i].sum() + chem[:, i].sum() + gap[i].sum()


def test_strata_do_not_read_the_truth(con, iface):
    """Strata depend on the graph with X deleted and the interface only."""
    x = con.index("AIYL")
    other = con.with_masks(con.chem.copy(), con.gap.copy(), "copy")
    other.chem[:, x] = np.roll(con.chem[:, x], 3)
    np.testing.assert_array_equal(N.strata(con, iface, x), N.strata(other, iface, x))


def test_permutations_stay_within_strata_and_are_permutations():
    strat = np.array([0, 0, 1, 1, 1, 10, 10, 11, 11, 11, 11])
    P = N.permutations(strat, 500, 3)
    for row in P:
        assert sorted(row) == list(range(len(strat)))
        assert (strat[row] == strat).all()
    # every within-stratum arrangement of a stratum of 3 appears, roughly uniformly
    sub = [tuple(r[2:5]) for r in P]
    counts = {p: sub.count(p) for p in set(sub)}
    assert len(counts) == 6 and min(counts.values()) > 500 / 6 * 0.6


def test_auc_matches_a_brute_force_count():
    rng = np.random.default_rng(0)
    for _ in range(20):
        s = rng.integers(0, 4, size=12).astype(float)
        y = np.zeros(12, bool)
        y[rng.choice(12, 4, replace=False)] = True
        pos, neg = s[y], s[~y]
        brute = np.mean([(p > q) + 0.5 * (p == q) for p in pos for q in neg])
        got = N.auc_from_ranks(N.ranks(s)[None], y[None])[0, 0]
        assert abs(got - brute) < 1e-12


def test_recovery_averages_types_then_brains_and_skips_unscoreable_types():
    K = 6
    truth = {"in": np.array([1, 1, 0, 0, 0, 0], bool), "out": np.array([0, 0, 0, 0, 1, 0], bool),
             "gap": np.zeros(K, bool)}
    rank = {"in": np.array([[6, 5, 1, 1, 1, 1], [1, 1, 6, 5, 1, 1]], float),
            "out": np.array([[0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 1, 0]], float), "gap": np.zeros((2, K))}
    r = N.recovery(rank, truth)
    assert r["types"] == ["in", "out"]
    np.testing.assert_allclose(r["per_type"]["in"][0], [1.0, 0.25])  # brain 2: below 6 and 5, tied with two 1s
    np.testing.assert_allclose(r["per_brain"][0], [(1.0 + 1.0) / 2, (0.25 + 1.0) / 2])
    assert abs(r["stat"][0] - np.mean([(1.0 + 1.0) / 2, (0.25 + 1.0) / 2])) < 1e-12


def test_observed_ties_with_identity_draws_are_counted():
    K = 6
    truth = {"in": np.array([1, 0, 0, 0, 0, 0], bool), "out": np.zeros(K, bool), "gap": np.zeros(K, bool)}
    rank = {"in": np.ones((1, K)), "out": np.zeros((1, K)), "gap": np.zeros((1, K))}  # every candidate tied
    t = N.test(rank, truth, np.zeros(K, int), B=200, seed=0)
    assert t["observed"] == 0.5 and t["p"] == 1.0  # every draw ties the observed value


def test_support_counts_distinct_joint_patterns_by_brute_force():
    strat = np.array([0, 0, 0, 1, 1])
    truth = {"in": np.array([1, 0, 0, 1, 0], bool), "out": np.array([1, 1, 0, 0, 0], bool),
             "gap": np.zeros(5, bool)}
    lab = np.stack([truth[t] for t in R.TYPES], 1)
    seen = set()
    for p in all_perms(range(5)):
        p = np.array(p)
        if (strat[p] == strat).all():
            seen.add(lab[p].tobytes())
    assert N.support(truth, strat)["patterns"] == len(seen)


def test_precision_at_k_and_average_precision():
    s = np.array([0.9, 0.8, 0.8, 0.1])
    y = np.array([[1, 0, 1, 0]], float)
    np.testing.assert_allclose(N.precision_at_k(s, y), [(1 + 0.5) / 2])  # one tie at the 2nd place, shared
    np.testing.assert_allclose(N.average_precision(s, y), [0.5 * 1.0 + 0.5 * (2 / 3)])


def _no_task_ranking(problem, cfg, seeds, gens):
    results = []
    for sd in seeds:
        s = S.free_search(problem, S.SearchConfig(generations=gens), cfg.brain, cfg.mutation, sd)
        S.run_lockstep([s], S.no_task)
        results.append(s.result())
    return S.ranking(results)


def test_no_task_control_matches_the_stratified_null(con, iface):
    """The no-task control: the search with fitness zero has no bias toward true partners. Over independent replicate
    target-arms (five brains of five free searches each), the stratified p values are close to uniform."""
    cfg = Config()
    x = con.index("AIYL")
    truth = R.truth(con, x)
    strat = N.strata(con, iface, x)
    problem = S.Problem(con.n - 1, R.true_counts(con, x), R.has_self_loop(con, x))
    ps, obs, nulls = [], [], []
    for rep in range(24):
        ranks = [_no_task_ranking(problem, cfg, [1000 * rep + 10 * b + k for k in range(5)], gens=10)
                 for b in range(5)]
        rk = {t: np.stack([r[t] for r in ranks]) for t in R.TYPES}
        t = N.test(rk, truth, strat, B=999, seed=rep)
        ps.append(t["p"])
        obs.append(t["observed"])
        nulls.append(t["null_mean"])
    ps = np.array(ps)
    assert 0.25 < ps.mean() < 0.75 and (ps < 0.05).sum() <= 4
    assert abs(np.mean(obs) - np.mean(nulls)) < 0.03


def test_no_task_check_can_fail_when_the_search_is_biased(con, iface):
    """Sabotage: a 'search' that ends on the true partners is flagged by the same test."""
    x = con.index("AIYL")
    truth = R.truth(con, x)
    strat = N.strata(con, iface, x)
    rk = {t: np.stack([truth[t].astype(float) + 0.01 * np.random.default_rng(b).random(len(truth[t]))
                       for b in range(5)]) for t in R.TYPES}
    assert N.test(rk, truth, strat, B=999, seed=0)["p"] < 0.01


def test_subset_recovery_and_expected_jaccard():
    truth = {"in": np.array([1, 0, 1, 0, 0, 1], bool), "out": np.zeros(6, bool), "gap": np.zeros(6, bool)}
    rank = {"in": np.array([[5, 0, 4, 1, 2, 0]], float), "out": np.zeros((1, 6)), "gap": np.zeros((1, 6))}
    keep = np.array([1, 1, 1, 1, 0, 0], bool)  # candidates 0-3: partners 0 and 2, both ranked above 1 and 3
    assert N.subset_recovery(rank, truth, keep) == 1.0
    assert N.subset_recovery(rank, truth, np.array([0, 1, 0, 1, 0, 0], bool)) is None  # no partner inside
    rng = np.random.default_rng(0)
    sim = [N.jaccard(np.isin(np.arange(40), rng.choice(40, 6, replace=False)),
                     np.isin(np.arange(40), rng.choice(40, 6, replace=False))) for _ in range(20000)]
    assert abs(np.mean(sim) - N.expected_jaccard(40, 6)) < 0.003


def test_expected_jaccard_edges():
    assert N.expected_jaccard(10, 10) == 1.0
    assert np.isnan(N.expected_jaccard(10, 0))
