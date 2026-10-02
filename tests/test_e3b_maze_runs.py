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
