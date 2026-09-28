"""The registered rules in `scripts/e1.py` (experiments/E1-navigation/PREREGISTRATION.md): the σ
choice, the one-sided bootstrap bound, the grids, and the secondary measures."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def e1():
    spec = importlib.util.spec_from_file_location("e1_script", ROOT / "scripts" / "e1.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _row(sigma, share):
    return {"sigma": sigma, "share_above_floor": share}


def test_sigma_is_the_smallest_candidate_meeting_the_share(e1):
    rows = [_row(2.0, 0.1), _row(3.0, 0.95), _row(4.0, 0.99), _row(6.0, 1.0)]
    assert e1.choose_sigma(rows) == (3.0, False)


def test_sigma_falls_back_to_the_largest_candidate_flagged(e1):
    rows = [_row(2.0, 0.0), _row(3.0, 0.0), _row(4.0, 0.3), _row(6.0, 0.875)]
    assert e1.choose_sigma(rows) == (6.0, True)


def test_the_share_boundary_is_inclusive(e1):
    assert e1.choose_sigma([_row(2.0, 0.90), _row(6.0, 1.0)]) == (2.0, False)


def test_the_lower_bound_is_below_the_mean_and_reproducible(e1):
    d = np.random.default_rng(1).normal(1.0, 1.0, 500)
    lb = e1.lower_bound(d)
    assert lb < d.mean() and lb == e1.lower_bound(d)
    assert e1.lower_bound(np.full(50, 2.0)) == 2.0


def test_the_wall_follower_thresholds_sit_above_the_own_body_level(e1):
    g = e1.grid_for("wall-follower", 0.3)
    assert "threshold_above_own_body" not in g
    assert min(g["threshold"]) > 0.3


def test_the_small_gain_grid_stops_at_32(e1):
    assert max(e1.grid_for("S-const", 0.0, 32)["k"]) == 32
    assert max(e1.grid_for("S-const", 0.0)["k"]) == 8192


def test_secondary_measures_count_failures_at_the_horizon(e1):
    ev = {"activation_tick": np.array([[[0, 11, -1], [0, -1, -1]]]),
          "reach_tick": np.array([[[10, -1, -1], [-1, -1, -1]]]),
          "path_length": np.array([[[5.0, 2.0, 0.0], [30.0, 0.0, 0.0]]]),
          "target_x": np.array([[[5.0, 5.0, 5.0], [5.0, 5.0, 5.0]]]),
          "target_y": np.array([[[5.0, 9.0, 13.0], [5.0, 9.0, 13.0]]])}
    s = e1.secondary(ev, horizon=300)
    assert s["first_arrival_share"] == 0.5
    assert s["latency_mean"] == (11 + 300) / 2
    assert s["leg_time_median"] == 11
