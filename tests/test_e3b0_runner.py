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


def test_stage_b2_follows_stage_b_and_every_later_stage_reads_it(m):
    assert m.STAGES.index("stage-b2") == m.STAGES.index("stage-b") + 1
    with pytest.raises(SystemExit, match="Stage B2"):
        m.chosen_cfg({"stage-b2": {"chosen": None}})


def test_the_widening_goes_one_factor_of_two_beyond_each_edge_the_winner_sits_on(m):
    grid = m.REGISTERED["stage_b"]
    d0 = m.REGISTERED["pilot"]["d0"]
    win = {"setting": {"mu": 0.005, "lam": 0.02, "delta": 0.05, "d0": d0 * 0.5}}
    extra, new = m.b2_widening(win, grid, d0)
    assert new == {"mu": 0.0025, "lam": None, "d0_scale": 0.25}
    assert extra and all(s["mu"] == 0.0025 or abs(s["d0"] - 0.25 * d0) < 1e-12 for s in extra)
    assert all(m.live(s["mu"], s["lam"]) for s in extra)
    inner = {"setting": {"mu": 0.01, "lam": 0.02, "delta": 0.05, "d0": d0 * 0.5}}
    extra2, new2 = m.b2_widening(inner, grid, d0)
    assert new2 == {"mu": None, "lam": None, "d0_scale": 0.25}
    assert len(extra2) == sum(m.live(a, b) for a in grid["mu"] for b in grid["lam"]) * len(grid["delta"])



def _rows(m, rates):
    d0 = m.REGISTERED["pilot"]["d0"]
    return [{"setting": {"mu": mu, "lam": lam, "delta": 0.05, "d0": d0 * k}, "follower_later_leg_rate": r, "passed": True}
            for (mu, lam, k), r in rates.items()]


def test_the_widening_skips_directions_where_the_rate_falls_toward_the_edge(m):
    grid, d0 = m.REGISTERED["stage_b"], m.REGISTERED["pilot"]["d0"]
    win = {"setting": {"mu": 0.02, "lam": 0.04, "delta": 0.05, "d0": d0 * 0.5}}
    falling = _rows(m, {(0.02, 0.04, 0.5): 4.0, (0.01, 0.04, 0.5): 5.0, (0.02, 0.02, 0.5): 0.0, (0.02, 0.04, 1.0): 4.5})
    extra, new = m.b2_widening(win, grid, d0, falling)
    assert new == {"mu": None, "lam": None, "d0_scale": None} and extra == []
    rising = _rows(m, {(0.02, 0.04, 0.5): 4.0, (0.01, 0.04, 0.5): 3.0, (0.02, 0.04, 1.0): 3.5})
    extra, new = m.b2_widening(win, grid, d0, rising)
    assert new["mu"] == 0.04 and new["d0_scale"] == 0.25 and new["lam"] is None  # λ 0.02 at μ 0.02 is not live


def test_ties_go_to_smaller_mu_then_lambda_then_d0(m):
    rows = [{"setting": {"mu": 0.01, "lam": 0.02, "d0": 0.5}, "follower_later_leg_rate": 5.0, "passed": True},
            {"setting": {"mu": 0.01, "lam": 0.02, "d0": 0.25}, "follower_later_leg_rate": 5.0, "passed": True}]
    assert m.choose(rows)["setting"]["d0"] == 0.25


def test_the_historical_records_are_checked_by_hash(m, tmp_path):
    f = tmp_path / "stage-a.json"
    f.write_text('{"outcome": "completed"}', encoding="utf-8")
    with pytest.raises(SystemExit, match="hash"):
        m.check_historical(f, "0" * 64)
    import hashlib
    m.check_historical(f, hashlib.sha256(f.read_bytes()).hexdigest())


def test_the_seed_cap_fails_on_an_empty_count_or_a_share_above_5_percent(m):
    assert not m.seed_cap({"qualified_inputs": 0, "above_high_share_qualified": 0.0})["passed"]
    assert not m.seed_cap({"qualified_inputs": 100, "above_high_share_qualified": 0.06})["passed"]
    assert m.seed_cap({"qualified_inputs": 100, "above_high_share_qualified": 0.05})["passed"]


def test_criterion_4_levels_are_floored_and_include_the_boundary(m):
    q = {"5": 1e-6, "25": 0.0004, "50": 0.02, "75": 0.2, "95": 0.6, "99": 1.4}
    lv = m.component_levels(q)
    assert min(lv) == 0.001 and 0.35 in lv and 0.003 in lv and 1.4 in lv and 0.02 in lv
    assert lv == sorted(set(lv))


def test_the_one_nose_check_holds_for_e_and_catches_a_reversed_turn(m):
    from wormwars.connectome import load_connectome
    from wormwars.e3 import maze_organisms as MO
    from wormwars.e3 import organism as O
    from wormwars.e3 import probe as P
    from wormwars.e3.task import shuttle_config
    from wormwars.e4s import arms as A
    cfg = shuttle_config()
    con = load_connectome()
    org = MO.maze_organism(con, MO.seed("E", A.load_l1(), cfg.brain, con=con), "W0", cfg.brain)
    pc = P.ProbeContext(org.ext, org.iface, cfg)
    states = {"A": O.Q_STAR, "B": -O.Q_STAR}
    res = m.one_nose_checks(org.genome, pc, states, [0.01, 0.1])
    assert res["passed_up_to_high_level"]
    flipped = P.ProbeContext(org.ext, org.iface, cfg)
    flipped.pairs = {k: (j, i) for k, (i, j) in pc.pairs.items()}  # left and right noses exchanged
    assert not m.one_nose_checks(org.genome, flipped, states, [0.01, 0.1])["passed_up_to_high_level"]
