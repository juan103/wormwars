"""03a's statistics (DESIGN.md v7.1 §6, §7): Holm, family 2's exact test and its simulated-null validation, the
three-state comparisons, and the outcome rules."""

from __future__ import annotations

from itertools import combinations

import numpy as np

from wormwars.e03a import stats as T


def test_holm_step_down():
    np.testing.assert_array_equal(T.holm([0.01, 0.04, 0.03, 0.2], 0.05), [True, False, False, False])
    np.testing.assert_array_equal(T.holm([0.001, 0.012, 0.02, 0.2], 0.05), [True, True, True, False])
    np.testing.assert_array_equal(T.holm([0.02, 0.001], 0.05), [True, True])
    np.testing.assert_array_equal(T.holm([0.06, 0.001], 0.05), [False, True])


def test_exact_p_matches_brute_force_and_counts_the_observed_split():
    rng = np.random.default_rng(1)
    for _ in range(10):
        mip, nip = rng.random(5), rng.random(5)
        d, p = T.exact_p(mip, nip)
        x = np.concatenate([mip, nip])
        diffs = [x[list(c)].mean() - np.delete(x, list(c)).mean() for c in combinations(range(10), 5)]
        assert len(diffs) == 252
        assert abs(d - (mip.mean() - nip.mean())) < 1e-12
        assert p == np.mean(np.array(diffs) >= d - 1e-12)
    # complete separation: only the observed split is as extreme
    assert T.exact_p(np.ones(5) + np.arange(5), np.zeros(5))[1] == 1 / 252


def test_batched_exact_p_equals_the_scalar_one():
    rng = np.random.default_rng(2)
    mip, nip = rng.random((7, 3, 5)), rng.random((7, 3, 5))
    obs, p = T.exact_p_batch(mip, nip)
    for i in range(7):
        for j in range(3):
            d, q = T.exact_p(mip[i, j], nip[i, j])
            assert abs(obs[i, j] - d) < 1e-12 and p[i, j] == q


def test_family2_floor_withholding_and_holm():
    sep = (np.linspace(0.8, 0.9, 5), np.linspace(0.5, 0.6, 5))  # complete separation, difference 0.3
    small = (np.linspace(0.51, 0.52, 5), np.linspace(0.50, 0.505, 5))  # separated, but below the floor
    out = T.family2({"a": sep[0], "b": small[0], "c": None, "d": sep[0], "e": sep[0]},
                    {"a": sep[1], "b": small[1], "c": sep[1], "d": sep[1], "e": sep[1]}, ["a", "b", "c", "d", "e"])
    rows = {r["target"]: r for r in out["targets"]}
    assert rows["c"]["withheld"] and rows["c"]["p"] == 1.0 and not rows["c"]["counts"]
    assert rows["a"]["holm_rejected"] and rows["a"]["counts"]
    assert rows["b"]["holm_rejected"] and not rows["b"]["counts"]  # rejected, but the difference is below 0.05
    assert out["any"]


def test_family2_simulation_under_the_sharp_null_is_at_most_nominal():
    for icc in (0.0, 0.5):
        r = T.simulate_family2(4000, seed=3, icc=icc)
        assert r["rate"] <= 0.05 + 3 * r["se"]


def test_family2_simulation_detects_a_real_difference():
    """Sabotage for the null check: with a large MIP advantage the simulated procedure rejects often, so the
    validation is not passing because it can never reject."""
    rng = np.random.default_rng(0)
    mip = 3.0 + rng.standard_normal((500, 5, 5))
    nip = rng.standard_normal((500, 5, 5))
    obs, p = T.exact_p_batch(mip, nip)
    assert (p.min(axis=1) <= 0.01).mean() > 0.9


def test_family2_simulation_floor_never_adds_rejections():
    a = T.simulate_family2(2000, seed=4)
    b = T.simulate_family2(2000, seed=4, floor=0.05)
    assert b["rate"] <= a["rate"]


def test_validation_report_shape():
    r = T.validate_family2(n_datasets=500, seed=1)
    assert len(r["scenarios"]) == 5 and r["accept"] == 0.0531
    assert all(s["passes"] is None for s in r["scenarios"] if not s["null"])


def test_verdicts():
    assert T.verdict(0.2, 0.3, 0.1) == "above"
    assert T.verdict(-0.3, -0.2, 0.1) == "below"
    assert T.verdict(-0.05, 0.08, 0.1) == "equivalent"
    assert T.verdict(-0.05, 0.2, 0.1) == "undetermined"


def test_compare_is_paired_by_world_and_shares_the_resample():
    rng = np.random.default_rng(0)
    world = rng.normal(0, 3, size=(5, 400))  # a large world effect shared by both states
    a = world + 0.5
    b = world.copy()
    c = T.compare(a, b, margin=0.1, B=2000, seed=1)
    assert c["verdict"] == "above" and abs(c["difference"] - 0.5) < 1e-12 and c["half_width"] < 1e-9
    # the same seed gives the same world resample whatever the states
    np.testing.assert_array_equal(T.world_resamples(400, 10, 1), T.world_resamples(400, 10, 1))
    d = T.compare(rng.normal(size=(5, 400)), rng.normal(size=(5, 400)), margin=0.01, B=2000, seed=1)
    assert d["verdict"] in ("undetermined", "equivalent")


def test_outcomes_and_separation():
    assert T.outcome(False, "reached", True) == "excluded"
    assert T.outcome(True, "exceeded", True) == "anatomical recovery"
    assert T.outcome(True, "reached", False) == "functional success, anatomy undetermined"
    assert T.outcome(True, "failed", True) == "search failure"
    assert T.outcome(True, "undetermined", True) == "inconclusive"
    assert T.separates(["anatomical recovery", "search failure", "excluded"])
    assert not T.separates(["anatomical recovery", "anatomical recovery", "inconclusive"])


def test_reliability_requires_restoration_in_mip():
    ok = {"verdict": "equivalent"}
    assert T.reliable_brain([1.0, 1.01, 0.99], delta_search=0.05, restoration=ok)
    assert not T.reliable_brain([1.0, 1.01, 0.99], delta_search=0.05, restoration={"verdict": "undetermined"})
    assert not T.reliable_brain([1.0, 1.5, 0.5], delta_search=0.05)
    assert T.functional({"verdict": "below"}) == "failed"


def test_family2_withholds_a_target_with_a_non_finite_brain():
    """Astra: a NaN would otherwise give p = 0 and enter Holm."""
    sep = (np.linspace(0.8, 0.9, 5), np.linspace(0.5, 0.6, 5))
    bad = np.array([0.8, np.nan, 0.85, 0.9, 0.88])
    out = T.family2({"a": bad, "b": sep[0]}, {"a": sep[1], "b": sep[1]}, ["a", "b"])
    rows = {r["target"]: r for r in out["targets"]}
    assert rows["a"]["withheld"] and rows["a"]["p"] == 1.0 and not rows["a"]["counts"]
    assert rows["b"]["p"] == 1 / 252


def test_compare_resamples_brains_and_worlds_as_an_explicit_loop_does():
    rng = np.random.default_rng(3)
    a = rng.normal(size=(4, 30)) + rng.normal(size=(4, 1))  # brain effects and world effects
    b = rng.normal(size=(4, 30))
    B, seed = 300, 7
    c = T.compare(a, b, margin=0.1, B=B, seed=seed)
    wi, bi = T.world_resamples(30, B, seed), T.brain_resamples(4, B, seed)
    boot = np.array([np.mean([(a - b)[bi[k, j], wi[k]].mean() for j in range(4)]) for k in range(B)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    assert abs(c["lo"] - lo) < 1e-12 and abs(c["hi"] - hi) < 1e-12
