"""The bootstrap must be honest: wide when the evidence is thin, and not fooled by pseudo-replication."""

from __future__ import annotations

import numpy as np

from wormwars.analysis import area_under_curve, compare, hierarchical_bootstrap


def _groups(rng, n_graphs, n_runs, graph_sd, run_sd, mean=0.0):
    out = {}
    for g in range(n_graphs):
        offset = rng.normal(0, graph_sd)
        out[f"G{g}"] = list(mean + offset + rng.normal(0, run_sd, n_runs))
    return out


def test_interval_covers_the_truth_most_of_the_time():
    rng = np.random.default_rng(0)
    hits = 0
    trials = 60
    for _ in range(trials):
        groups = _groups(rng, 5, 3, graph_sd=0.3, run_sd=0.2, mean=1.0)
        r = hierarchical_bootstrap(groups, n_boot=800, rng=np.random.default_rng(1))
        hits += r.lo <= 1.0 <= r.hi
    assert hits >= trials * 0.75, f"covered the truth only {hits}/{trials} times"


def test_more_graphs_narrows_the_interval():
    """In expectation, not per draw: with only 2 graphs the interval width is itself very noisy."""
    rng = np.random.default_rng(1)
    widths = {2: [], 12: []}
    for _ in range(25):
        for k in widths:
            r = hierarchical_bootstrap(
                _groups(rng, k, 3, 0.4, 0.1), n_boot=600, rng=np.random.default_rng(2)
            )
            widths[k].append(r.hi - r.lo)
    assert np.mean(widths[12]) < np.mean(widths[2])


def test_graph_level_variance_widens_the_interval():
    """Pseudo-replication check: 15 runs on 5 graphs must be less certain than 15 runs on 1."""
    rng = np.random.default_rng(2)
    spread = _groups(rng, 5, 3, graph_sd=0.5, run_sd=0.05)
    single = {"G0": list(rng.normal(0, 0.05, 15))}
    a = hierarchical_bootstrap(spread, n_boot=2000, rng=np.random.default_rng(3))
    b = hierarchical_bootstrap(single, n_boot=2000, rng=np.random.default_rng(3))
    assert (a.hi - a.lo) > (b.hi - b.lo) * 3


def test_compare_finds_a_real_difference():
    rng = np.random.default_rng(3)
    a = _groups(rng, 5, 3, 0.05, 0.05, mean=1.0)
    b = _groups(rng, 5, 3, 0.05, 0.05, mean=0.5)
    c = compare(a, b, "A", "B", n_boot=3000)
    assert c.lo > 0 and c.p_a_greater > 0.99
    assert c.verdict() == "A > B"


def test_compare_reports_no_separation_when_there_is_none():
    rng = np.random.default_rng(4)
    a = _groups(rng, 5, 3, 0.3, 0.2, mean=1.0)
    b = _groups(rng, 5, 3, 0.3, 0.2, mean=1.0)
    c = compare(a, b, "A", "B", n_boot=3000)
    assert c.lo < 0 < c.hi
    assert "no separation" in c.verdict()


def test_area_under_curve_ignores_missing_points():
    assert area_under_curve([1.0, np.nan, 3.0]) == 2.0
