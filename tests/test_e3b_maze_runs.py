"""E3b-0's simulation drivers (docs/E3/E3b-0-PLAN.md §3b, §3c), on small CPU cases."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.connectome import load_connectome
from wormwars.e3 import maze as M
from wormwars.e3 import maze_controls as MC
from wormwars.e3 import maze_measures as MM
from wormwars.e3 import maze_runs as MR
from wormwars.e3 import maze_world as MW
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def iface():
    return load_interface(load_connectome())


def _cfg(**kw):
    base = dict(c=5, horizon=300, colony=2, mu=0.01, lam=0.03, delta=0.15, d0=0.571)
    base.update(kw)
    return MW.maze_config(**base)


def test_play_returns_the_events_and_repeats_exactly(iface):
    cfg = _cfg()
    a = MR.play(cfg, iface, lambda: MC.oracle(iface, cfg), np.arange(4), run_seed=5)
    b = MR.play(cfg, iface, lambda: MC.oracle(iface, cfg), np.arange(4), run_seed=5)
    assert a["visit_tick"].shape == (4, 2, 256) and np.array_equal(a["visit_tick"], b["visit_tick"])
    assert (a["visits"] > 0).all()


def test_replay_donors_differ_in_an_endpoint(iface):
    eps, exceptions = MR.replay_donors(np.arange(40), run_seed=5, c=5)
    for mid, ep in zip(range(40), eps):
        _, p0 = M.maze_for(run_seed=5, maze_id=mid, episode=0, c=5)
        _, p1 = M.maze_for(run_seed=5, maze_id=mid, episode=int(ep), c=5)
        assert ep >= 1000 and (p0.a != p1.a or p0.b != p1.b) or mid in exceptions
    assert len(exceptions) == 0


def test_play_with_replay_donors_senses_the_donor(iface):
    cfg = _cfg(colony=2, horizon=200)
    ids = np.arange(3)
    eps, _ = MR.replay_donors(ids, run_seed=5, c=5)
    out = MR.play_replay(cfg, iface, lambda: MC.follower(iface, cfg), ids, run_seed=5, donor_episodes=eps, coef=1.0)
    assert out["visit_tick"].shape == (3, 2, 256)
    assert out["exposure_sum"].sum() > 0  # the donors' trails reach the recipients' noses
    assert 0.0 <= out["route_overlap"].min() and out["route_overlap"].max() <= 1.0


def test_the_polarity_test_runs_its_three_conditions(iface):
    cfg = _cfg(colony=1, horizon=600)
    res = MR.polarity(cfg, iface, np.arange(6), run_seed=5)
    for k in ("pass_real", "pass_none", "pass_permuted", "oracle_ticks", "leg_ticks"):
        assert res[k].shape == (6,)
    assert (res["oracle_ticks"] > 0).all() and (res["leg_ticks"] > 0).all()
    assert set(np.unique(res["pass_real"])) <= {0.0, 1.0}


def test_the_aged_trail_follows_the_pure_diffusion(iface):
    mz, _ = M.maze_for(run_seed=1, maze_id=0, episode=0, c=5)
    open_ = torch.from_numpy(~mz.wall).float()
    x = torch.zeros(2, *open_.shape)
    x[:, 2, 2] = 1.0
    aged = MR.age(x, open_, delta=0.15, mu=0.01, steps=torch.tensor([3, 5]))
    y = x.clone()
    for k in range(5):
        y = MW.diffuse(y, open_, 0.15) * (1 - 0.01)
        if k == 2:
            assert torch.allclose(aged[0], y[0])
    assert torch.allclose(aged[1], y[1])


def test_the_gradient_shares_are_measured_at_three_ages(iface):
    cfg = _cfg(colony=1, horizon=400)
    res = MR.gradient(cfg, iface, np.arange(4), run_seed=5)
    for age in (1, 2, 4):
        assert res[f"share_age{age}"].shape == (4,)
        assert np.all((res[f"share_age{age}"] >= 0) & (res[f"share_age{age}"] <= 1))


def test_the_nose_range_recorder_counts_on_route_noses(iface):
    cfg = _cfg(colony=2, horizon=200)
    out = MR.play(cfg, iface, lambda: MC.follower(iface, cfg), np.arange(3), run_seed=5, nose_range=True)
    nr = out["nose_range"]
    assert nr["on_route_noses"] > 0
    assert nr["in_range"] + nr["above"] <= nr["on_route_noses"]


def test_the_polarity_start_can_face_toward_the_source_or_at_random(iface):
    cfg = _cfg(colony=1, horizon=600)
    ids = np.arange(4)
    for facing in ("toward", "random"):
        res = MR.polarity(cfg, iface, ids, run_seed=5, facing=facing)
        assert res["facing"] == facing and res["pass_real"].shape == (4,)
    away = MR._start(*M.maze_for(run_seed=5, maze_id=0, episode=0, c=5), 5, 0, facing="away")[2]
    toward = MR._start(*M.maze_for(run_seed=5, maze_id=0, episode=0, c=5), 5, 0, facing="toward")[2]
    assert abs(abs((away - toward + np.pi) % (2 * np.pi) - np.pi) - np.pi) < 1e-9  # opposite, same jitter


def test_the_nose_range_counts_occluded_and_zero_noses_apart(iface):
    cfg = _cfg(colony=2, horizon=200)
    nr = MR.play(cfg, iface, lambda: MC.follower(iface, cfg), np.arange(3), run_seed=5, nose_range=True)["nose_range"]
    assert 0 <= nr["occluded"] <= nr["zero"] <= nr["on_route_noses"]
    assert nr["in_range_share_unoccluded"] >= nr["in_range_share"]


def test_the_toward_start_faces_the_previous_route_cell():
    """Toward A is the direction of the route's previous maze cell, not away + π, which faces a wall where
    the route bends at the start (Astra, Fable; D178)."""
    def wrap(a):
        return (a + np.pi) % (2 * np.pi) - np.pi

    bends = 0
    for mid in range(30):
        mz, pl = M.maze_for(run_seed=5, maze_id=mid, episode=0, c=5)
        path = MM.tree_path(mz, pl.a, pl.b)
        k = len(path) // 2
        (x0, y0), (xp, yp), (xn, yn) = (M.cell_centre(path[i]) for i in (k, k - 1, k + 1))
        back, fwd = np.arctan2(yp - y0, xp - x0), np.arctan2(yn - y0, xn - x0)
        bends += abs(wrap(back - fwd - np.pi)) > 1e-6
        jitter = wrap(MR._start(mz, pl, 5, mid, facing="away")[2] - fwd)
        toward = MR._start(mz, pl, 5, mid, facing="toward")[2]
        assert abs(wrap(toward - (back + jitter))) < 1e-9
    assert bends > 0


def test_the_polarity_test_takes_a_deadline_factor_a_trail_age_and_a_synthetic_trail(iface):
    cfg = _cfg(colony=1, horizon=600)
    ids = np.arange(4)
    base = MR.polarity(cfg, iface, ids, run_seed=5, facing="toward")
    loose = MR.polarity(cfg, iface, ids, run_seed=5, facing="toward", limit_factor=4.0)
    assert (loose["pass_none"] >= base["pass_none"]).all()  # a later deadline only adds passes
    early = base["first_tick_none"] >= 0  # arrivals within the shorter run are the same arrivals
    assert (loose["first_tick_none"][early] == base["first_tick_none"][early]).all()
    fresh = MR.polarity(cfg, iface, ids, run_seed=5, facing="toward", age_legs=0)
    assert fresh["age_legs"] == 0
    synth = MR.polarity(cfg, iface, ids, run_seed=5, facing="toward",
                        synthetic=lambda mz, pl, route: np.where(route, np.exp(-mz.free_distance(pl.a) / 8.0), 0.0))
    assert synth["synthetic"] is True and synth["pass_real"].shape == (4,)


def test_the_nose_range_reports_quantiles_of_the_levels_met(iface):
    cfg = _cfg(colony=2, horizon=300)
    nr = MR.play(cfg, iface, lambda: MC.follower(iface, cfg), np.arange(3), run_seed=5, nose_range=True)["nose_range"]
    q = nr["quantiles_unoccluded_positive"]
    assert set(q) == {"1", "5", "25", "50", "75", "95", "99"}
    vals = [q[k] for k in ("1", "5", "25", "50", "75", "95", "99")]
    assert vals == sorted(vals) and vals[0] > 0


def test_the_high_level_share_is_counted_exactly_among_qualified_inputs(iface):
    cfg = _cfg(colony=2, horizon=300, d0=3.0)  # a heavy trail, so some inputs exceed 0.35
    nr = MR.play(cfg, iface, lambda: MC.follower(iface, cfg), np.arange(3), run_seed=5, nose_range=True)["nose_range"]
    assert nr["qualified_inputs"] == nr["positive_unoccluded_after_trail"] > 0
    assert 0 < nr["above_high_share_qualified"] <= 1
    assert nr["above_high_share_qualified"] == nr["qualified_above_high"] / nr["qualified_inputs"]



def test_polarity_readings_report_censoring_instead_of_nan():
    p = {"single_pass": np.ones(4), "oracle_ticks": np.array([10, 10, 10, 10]), "facing": "away", "age_legs": 1.0,
         "synthetic": False}
    for name in ("real", "none", "permuted"):
        p[f"first_tick_{name}"] = np.array([5, -1, -1, -1])
    r = MR.polarity_readings(p)
    assert r["real_censored_share"] == 0.75
    q = r["real_time_over_oracle_quartiles"]
    assert q[0] == pytest.approx(0.6) and q[1] is None and q[2] is None  # beyond the run: censored, not NaN


def test_the_recorder_reports_branch_occupancy_and_pair_differences(iface):
    cfg = _cfg(colony=2, horizon=300, d0=1.0)
    nr = MR.play(cfg, iface, lambda: MC.follower(iface, cfg), np.arange(3), run_seed=5, nose_range=True)["nose_range"]
    assert 0 <= nr["steering_share_on_route"] <= 1 and 0 <= nr["steering_share_all"] <= 1
    assert nr["pairs_unoccluded"] > 0 and 0 <= nr["pairs_turn_relevant_share"] <= 1
    assert set(nr["pair_abs_difference_quantiles"]) == {"25", "50", "75", "95"}


def test_the_recorder_counts_exactly_above_each_high_level(iface):
    cfg = _cfg(colony=2, horizon=300, d0=3.0)
    nr = MR.play(cfg, iface, lambda: MC.follower(iface, cfg), np.arange(3), run_seed=5, nose_range=True)["nose_range"]
    by = nr["above_share_qualified_by_level"]
    assert set(by) == {"0.35", "1.0"}
    assert by["0.35"] == nr["above_high_share_qualified"] >= by["1.0"] >= 0


def test_play_batch_plays_several_organisms_and_counts_noses_per_world():
    """E3b-1's evaluation chunks (PREREGISTRATION §6): strains side by side, each on every maze, with the
    nose recorder's counts per world; identical strains give identical worlds."""
    from wormwars.brain import Brain, Genome
    from wormwars.e3 import maze_organisms as MO
    from wormwars.e4s import arms as A
    con = load_connectome()
    cfg = _cfg(colony=2, horizon=150)
    org = MO.maze_organism(con, MO.seed("E", A.load_l1(), cfg.brain, con=con), "W2", cfg.brain)
    g = org.genome
    w = g.w.clone()
    w[0] *= 0.5  # a different organism
    pop = Genome.cat([g, g, g.with_params(w=w)])
    ids = np.arange(3)
    out = MR.play_batch(cfg, org.iface, Brain(pop), np.arange(3), ids, run_seed=5, access="shared", nose_range=True)
    assert out["visit_tick"].shape == (3, 3, 2, 256)  # [strains, mazes, weys, legs]
    assert np.array_equal(out["visit_tick"][0], out["visit_tick"][1])
    nr = out["nose_range"]
    assert nr["qualified"].shape == (3, 3) and nr["above"]["1.0"].shape == (3, 3)
    assert np.array_equal(nr["qualified"][0], nr["qualified"][1])
    assert (nr["above"]["1.0"] <= nr["above"]["0.35"]).all() and (nr["above"]["0.35"] <= nr["qualified"]).all()


def test_play_batch_with_replay_donors_per_strain():
    from wormwars.brain import Brain, Genome
    from wormwars.e3 import maze_organisms as MO
    from wormwars.e4s import arms as A
    con = load_connectome()
    cfg = _cfg(colony=2, horizon=600)  # long enough for the donors to lay trails
    org = MO.maze_organism(con, MO.seed("E", A.load_l1(), cfg.brain, con=con), "W2", cfg.brain)
    pop = Genome.cat([org.genome, org.genome])
    ids = np.arange(3)
    eps, _ = MR.replay_donors(ids, run_seed=5, c=5)
    out = MR.play_batch(cfg, org.iface, Brain(pop), np.arange(2), ids, run_seed=5, access="replay",
                        donor_episodes=eps, replay_coef=np.array([1.0, 1.0]))
    assert out["visit_tick"].shape == (2, 3, 2, 256)
    assert np.array_equal(out["visit_tick"][0], out["visit_tick"][1])
    assert out["exposure_sum"].sum() > 0
