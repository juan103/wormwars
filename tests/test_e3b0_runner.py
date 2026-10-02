"""E3b-0's runner (scripts/e3b0.py): its fixed rules, checked without running a stage."""

from __future__ import annotations

import importlib.util
import itertools
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def m():
    s = importlib.util.spec_from_file_location("e3b0_under_test", ROOT / "scripts" / "e3b0.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


def test_the_trail_grid_has_36_settings_and_24_live(m):
    R = m.REGISTERED["stage_b"]
    grid = list(itertools.product(R["mu"], R["lam"], R["delta"], R["d0_scale"]))
    assert len(grid) == 36
    assert sum(m.live(mu, lam) for mu, lam, _, _ in grid) == 24
    assert not m.live(0.01, 0.01) and not m.live(0.02, 0.02) and m.live(0.02, 0.04)


def test_stage_a_tries_candidates_in_order_of_c_times_h_then_c(m):
    R = m.REGISTERED["stage_a"]
    order = sorted(itertools.product(R["c"], R["H"]), key=lambda t: (t[0] * t[1], t[0]))
    assert order[:3] == [(5, 1200), (6, 1200), (7, 1200)] and order[-1] == (8, 2400)


def test_stage_b_chooses_the_best_rate_among_passing_ties_to_smaller_mu_then_lambda(m):
    rows = [{"setting": {"mu": 0.02, "lam": 0.04}, "follower_later_leg_rate": 5.0, "passed": True},
            {"setting": {"mu": 0.01, "lam": 0.04}, "follower_later_leg_rate": 5.0, "passed": True},
            {"setting": {"mu": 0.01, "lam": 0.02}, "follower_later_leg_rate": 5.0, "passed": True},
            {"setting": {"mu": 0.005, "lam": 0.01}, "follower_later_leg_rate": 9.0, "passed": False}]
    assert m.choose(rows)["setting"] == {"mu": 0.01, "lam": 0.02}
    assert m.choose([dict(r, passed=False) for r in rows]) is None


def test_the_maze_blocks_are_disjoint_and_as_planned(m):
    sel, rep, fresh = (set(m.ids(k).tolist()) for k in ("selection", "report", "fresh"))
    assert sel == set(range(256)) and rep == set(range(1000, 1256)) and fresh == set(range(2000, 2256))
    assert not (sel & rep or sel & fresh or rep & fresh)


def test_the_headroom_uses_the_committed_minimum_detectable_effect(m):
    import json
    p = json.loads((ROOT / "experiments" / "E3-ab-organism" / "E3b-0" / "power.json").read_text())
    fine = p["fine"]["results"]
    worst = max(fine[f"12 runs, {shape}, CV 0.282"]["t"]["mde_80"] for shape in ("normal", "empirical"))
    assert m.REGISTERED["criterion2"]["mde"] == worst


def test_stage_c_refuses_a_failed_recheck(m):
    with pytest.raises(SystemExit, match="recheck"):
        m.require_recheck_passed({"recheck-a": {"passed": False}})
    m.require_recheck_passed({"recheck-a": {"passed": True}})
