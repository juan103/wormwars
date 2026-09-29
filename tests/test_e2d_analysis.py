"""E2d's registered analysis rules (`scripts/e2d.py`, experiments/E2d-taskn-diagnosis/PLAN.md v4), as
pure functions: the intervals, Part B's classes and readings, Part C's readings with and without run 2,
the interaction, the budget reading, and C0's ranking measures."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def d():
    spec = importlib.util.spec_from_file_location("e2d_script", ROOT / "scripts" / "e2d.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ intervals

def test_the_sign_flip_test_is_exact(d):
    assert d.sign_flip_p(np.full(8, 0.5)) == pytest.approx(2 / 256)  # only all-plus and all-minus reach it
    assert d.sign_flip_p(np.zeros(8)) == 1.0


def test_the_run_summary_reports_mean_median_improved_and_an_interval(d):
    s = d.run_summary(np.array([0.5, 0.4, 0.6, 0.5, 0.3, 0.7, 0.5, 0.4]))
    assert s["mean"] == pytest.approx(0.4875) and s["median"] == pytest.approx(0.5) and s["improved"] == 8
    assert 0.3 < s["lo90"] < s["mean"] < s["hi90"] < 0.7


# ------------------------------------------------------------------ Part B

def _ci(lo, hi):
    return {"mean": (lo + hi) / 2, "lo95": lo, "hi95": hi}


@pytest.mark.parametrize("m,s,cls", [
    ((0.6, 1.0), (0.7, 1.2), "uses"),
    ((0.6, 1.0), (0.4, 1.2), "unclear"),           # one lower bound at 0.4
    ((-0.2, 0.2), (-0.1, 0.24), "no material benefit"),
    ((-0.3, 0.1), (-0.1, 0.1), "unclear"),          # a lower bound below -0.25: two-sided
])
def test_the_classes_are_two_sided(d, m, s, cls):
    assert d.classify(_ci(*m), _ci(*s)) == cls


@pytest.mark.parametrize("classes,reading", [
    (["uses"] * 3 + ["no material benefit"] * 5, "stereo use present"),
    (["uses"] * 2 + ["no material benefit"] * 6, "non-stereo"),
    (["unclear"] * 6 + ["no material benefit"] * 2, "mixed"),       # v2's gap: unclear is not non-stereo
    (["no material benefit"] * 3 + ["unclear"], "non-stereo"),      # a set of 4: three-quarters
])
def test_a_sets_reading(d, classes, reading):
    assert d.set_reading(classes) == reading


def test_a_non_stereo_plateau_needs_every_read_set_and_the_fixed_band(d):
    ok = {"a": ("non-stereo", 2.1), "b": ("non-stereo", 1.95)}
    assert d.plateau_reading(ok) is True
    assert d.plateau_reading({**ok, "c": ("mixed", 2.1)}) is False
    assert d.plateau_reading({**ok, "c": ("non-stereo", 2.6)}) is False


def test_the_budget_reading_uses_the_mean_gain_with_its_interval(d):
    # E2's hold-out figures (disclosed in the plan): the rule is expected to fire on them
    gains = np.array([0.379, 0.11, 0.045, 0.694, 0.241, 0.078, 0.0, 0.419])
    assert d.budget_reading(gains)["reading"] == "budget-limited"
    assert d.budget_reading(np.array([0.3, -0.3] * 4))["reading"] == "not budget-limited"


# ------------------------------------------------------------------ Part C

def test_supports_needs_both_the_eight_and_the_seven_without_run_2(d):
    both = np.array([0.4, 0.5, 0.4, 0.45, 0.35, 0.5, 0.4, 0.45])
    assert d.arm_reading(both)["reading"] == "supports"
    carried = np.array([0.0, 0.1, 2.0, 0.05, 0.1, 0.0, 0.1, 0.05])  # run 2 alone
    assert d.arm_reading(carried)["reading"] == "supports, carried by run 2"
    harm = -both
    assert d.arm_reading(harm)["reading"] == "harmful"
    assert d.arm_reading(np.array([0.9, -0.3, 0.8, -0.2, 0.7, -0.3, 0.6, -0.2]))["reading"] == "inconclusive"


def test_leaving_the_plateau_is_separate_from_a_gain(d):
    assert d.leaves_plateau(["uses", "unclear", "uses", "unclear"] + ["no material benefit"] * 4,
                            [2.0, 2.6, 2.0, 2.5, 1.0, 2.0, 2.0, 2.0]) is True  # 2 use it, 2 score >= 2.5
    assert d.leaves_plateau(["uses", "unclear", "uses", "unclear"] + ["no material benefit"] * 4,
                            [2.0, 2.6, 2.0, 2.4, 1.0, 2.0, 2.0, 2.0]) is False  # only 3
    assert d.leaves_plateau(["no material benefit"] * 8, [2.2] * 8) is False


def test_an_interaction_is_claimed_only_from_the_difference_of_differences(d):
    c1, c4, c2p, gap = np.full(8, 2.3), np.full(8, 2.4), np.full(8, 2.2), np.full(8, 2.1)
    jitter = np.array([0.01, -0.01] * 4)
    r = d.interaction(c4 + jitter, c1, c2p, gap)
    assert r["claimed"] is False  # (2.4 - 2.3) - (2.2 - 2.1) = 0, give or take the jitter
    r = d.interaction(np.full(8, 3.0) + jitter, c1, c2p, gap)
    assert r["claimed"] is True


# ------------------------------------------------------------------ C0

def test_sibling_ranking_scores_each_draw_against_its_complement(d):
    W = 16
    a = np.array([1] * 8 + [0] * 8)  # mean 0.5
    b = np.array([0] * 8 + [0] * 8)  # mean 0.0
    draws = np.array([[0, 1], [8, 9], [0, 8]])  # the complement differs in every draw
    r = d.sibling_ranking(np.stack([a, b]), draws, bins=[(0.3, 0.6)])
    row = r["rows"][0]
    assert row["pairs"] == 1
    # draw 1: [8, 9] both 0, a tie; draws 0 and 2 rank a above b
    assert row["correct"] == pytest.approx(2 / 3) and row["tied"] == pytest.approx(1 / 3)


def test_a_draw_whose_complement_shows_no_difference_is_excluded(d):
    a = np.array([1, 1, 0, 0])
    b = np.array([0, 0, 0, 0])  # 256-style difference 0.5
    draws = np.array([[0, 1]])  # the complement [2, 3] shows no difference
    row = d.sibling_ranking(np.stack([a, b]), draws, bins=[(0.3, 0.6)])["rows"][0]
    assert row["excluded_draws"] == 1 and row["scored_pairs"] == 0


def test_truncation_ties_go_to_the_lower_index(d):
    v = np.array([1.0, 2.0, 2.0, 0.5])
    assert d.top_k(v, 2).tolist() == [1, 2]
    assert d.top_k(np.array([2.0, 2.0, 2.0]), 2).tolist() == [0, 1]


def test_the_same_noise_at_every_scale(d):
    """C0's children: the generator is reset per scale, so the draws are equal and only scaled."""
    import torch

    from wormwars.brain import BrainSpec, Genome
    from wormwars.config import Config
    from wormwars.connectome import load_connectome
    spec = BrainSpec.from_connectome(load_connectome())
    cfg = Config()
    parent = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(3))
    full = d.children(parent, cfg.mutation, 1.0, 16, seed=1_131_000)
    half = d.children(parent, cfg.mutation, 0.5, 16, seed=1_131_000)
    free = (full.w.abs() < cfg.brain.w_max - 1e-4) & (half.w.abs() < cfg.brain.w_max - 1e-4)
    torch.testing.assert_close(((half.w - parent.w) * 2)[free], (full.w - parent.w)[free], rtol=1e-4, atol=1e-5)


# ------------------------------------------------------------------ code review (D133): pins that can fail

def test_world_ci_is_a_paired_bootstrap_at_the_2_5_and_97_5_percentiles(d):
    rng = np.random.default_rng(5)
    a, b = rng.integers(0, 5, 200), rng.integers(0, 5, 200)
    r = d.world_ci(a, b)
    diff = (a - b).astype(float)
    idx = np.random.default_rng(0).integers(0, 200, size=(10_000, 200))
    m = diff[idx].mean(1)
    assert (r["lo95"], r["hi95"]) == (pytest.approx(np.percentile(m, 2.5)), pytest.approx(np.percentile(m, 97.5)))


def test_run_summary_uses_the_5th_and_95th_percentiles(d):
    x = np.array([0.5, 0.4, 0.6, 0.5, 0.3, 0.7, 0.5, 0.4])
    s = d.run_summary(x)
    m = x[np.random.default_rng(0).integers(0, 8, size=(10_000, 8))].mean(1)
    assert (s["lo90"], s["hi90"]) == (pytest.approx(np.percentile(m, 5)), pytest.approx(np.percentile(m, 95)))


def test_a_gain_of_0_3_whose_interval_crosses_0_is_inconclusive(d):
    x = np.array([2.0, -0.2, -0.2, -0.2, 0.5, -0.2, -0.2, 0.9])
    r = d.arm_reading(x)
    assert r["all_runs"]["mean"] >= 0.3 and r["all_runs"]["lo90"] <= 0 and r["reading"] == "inconclusive"


def test_harm_carried_by_run_2(d):
    x = -np.array([0.0, 0.1, 2.0, 0.05, 0.1, 0.0, 0.1, 0.05])
    assert d.arm_reading(x)["reading"] == "harmful, carried by run 2"


def test_the_interaction_needs_both_the_eight_and_the_seven(d):
    assert d.claimed({"lo90": 0.1, "hi90": 0.3}, {"lo90": -0.1, "hi90": 0.2}) is False
    assert d.claimed({"lo90": 0.1, "hi90": 0.3}, {"lo90": 0.05, "hi90": 0.2}) is True
    r = d.interaction(np.arange(8.0), np.zeros(8), np.zeros(8), np.zeros(8))
    assert r["without_run_2"]["n"] == 7 and 2.0 not in r["without_run_2"]["per_run"]


def test_the_budget_rule_needs_both_the_mean_and_the_interval(d):
    wide = np.array([3.2, -0.2, -0.2, -0.2, -0.2, -0.2, -0.2, 0.0])  # mean 0.25, interval crossing 0
    r = d.budget_reading(wide)
    assert r["mean"] == pytest.approx(0.25) and r["lo90"] <= 0 and r["reading"] == "not budget-limited"
    small = np.full(8, 0.15) + np.array([0.01, -0.01] * 4)  # interval above 0, mean below 0.2
    assert d.budget_reading(small)["reading"] == "not budget-limited"


@pytest.mark.parametrize("n_nomat,reading", [(5, "mixed"), (6, "non-stereo")])
def test_three_quarters_of_a_set(d, n_nomat, reading):
    assert d.set_reading(["no material benefit"] * n_nomat + ["unclear"] * (8 - n_nomat)) == reading


def test_a_reversed_complement_scores_against_the_complement(d):
    a, b = np.array([2, 2, 0, 0]), np.array([0, 0, 1, 0])  # full means 1.0 and 0.25
    row = d.sibling_ranking(np.stack([a, b]), np.array([[0, 1]]), bins=[(0.6, 0.9)])["rows"][0]
    # the draw ranks a above b; its complement [2, 3] ranks b above a: incorrect, not tied
    assert row["correct"] == 0.0 and row["tied"] == 0.0


def test_c0s_analysis_on_known_batches(d, monkeypatch):
    monkeypatch.setitem(d.REGISTERED["c0"], "draws", 50)
    monkeypatch.setitem(d.REGISTERED["c0"], "k", 4)
    monkeypatch.setitem(d.REGISTERED["c0"], "top", 2)
    monkeypatch.setitem(d.REGISTERED["c0"], "scales", [1.0])
    monkeypatch.setitem(d.REGISTERED["c0"], "sigmas", [0.5])
    monkeypatch.setitem(d.REGISTERED["analysis"], "bins", [[0.0, 0.5], [0.5, 1.5], [1.5, 9.0]])
    monkeypatch.setitem(d.REGISTERED["analysis"], "min_pairs", 1)
    W = 16
    kids = np.stack([np.full(W, v) for v in (0, 1, 2, 3)])  # constant per child: every draw ranks exactly
    ga = np.vstack([np.full(W, 2), kids])
    es = np.vstack([np.full(W, 2)] + [np.full(W, 2), np.full(W, 1)] * 2)  # plus scores 2, minus 1
    r = d.analyse_c0({"ga run00 scale 1.0": ga, "es run00 sigma 0.5": es})
    row = r["ga"]["1.0"]["pooled"][1]  # gaps of 1: pairs (0,1), (1,2), (2,3)
    assert row["pairs"] == 3 and row["correct"] == 1.0 and row["tied"] == 0.0
    assert r["reading"] == "selection noise is not material by this rule"
    assert r["ga"]["1.0"]["top8_overlap"] == [1.0]
    assert r["es"]["0.5"]["sign_agreement"] == 1.0 and r["es"]["0.5"]["mean_score"] == 2.0
    assert r["ga"]["1.0"]["children"][0]["parent"] == 2.0


def test_the_es_pairs_share_their_noise_and_alternate(d):
    """Same draws at both σ (halved), and mean + σε, mean − σε interleaved. Clamping can move a few
    coordinates, so nearly all, not all, must match."""
    import torch

    from wormwars.brain import BrainSpec, Genome
    from wormwars.config import Config
    from wormwars.connectome import load_connectome
    from wormwars.e2.optimizers import encode
    spec = BrainSpec.from_connectome(load_connectome())
    t = Genome.random(spec, Config().brain, 1, generator=torch.Generator().manual_seed(4))
    z = encode(t)[0]
    half, full = encode(d.es_pairs(t, 0.25, 3, seed=9)) - z, encode(d.es_pairs(t, 0.5, 3, seed=9)) - z
    assert float(((half * 2 - full).abs() < 1e-3).float().mean()) > 0.95
    assert float(((half[0] + half[1]).abs() < 1e-3).float().mean()) > 0.95
    assert float((half[0].abs() > 1e-3).float().mean()) > 0.95  # the noise is not zero


def test_c0s_seeds_and_the_training_clock_are_pinned(d):
    assert (d.REGISTERED["c0"]["seed_ga"], d.REGISTERED["c0"]["seed_es"]) == (1_131_000, 1_131_100)
    assert d.training_clock().cap_hours == 6.5
