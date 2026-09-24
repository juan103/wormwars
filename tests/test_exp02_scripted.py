"""Scripted controllers drive the motors directly, through the same world as evolved brains."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo.rollout import rollout, rollout_brain
from wormwars.exp02 import scripted
from wormwars.interface import load_interface
from wormwars.world import World


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con)


def world_for(cfg, iface, policy, n_worlds=2):
    b = scripted.ScriptedBrain(iface, 302, policy, cfg.world.forward_gain, cfg.world.turn_gain)
    return World(cfg, iface, b, torch.zeros(n_worlds, 1, dtype=torch.long), run_seed=1)


def test_commands_arrive_at_the_motors_exactly(parts):
    _, iface = parts
    cfg = Config()

    class Fixed:
        def init(self, s, b):
            return None

        def __call__(self, left, right, state):
            return torch.full_like(left, 0.5), torch.full_like(left, -0.25), state

    w = world_for(cfg, iface, Fixed())
    w.tick()
    alive = w.alive
    torch.testing.assert_close(w.last_forward[alive], torch.full_like(w.last_forward[alive], 0.5))
    torch.testing.assert_close(w.last_turn[alive], torch.full_like(w.last_turn[alive], -0.25))


def test_stationary_does_not_move_and_straight_does(parts):
    _, iface = parts
    cfg = Config()
    w = world_for(cfg, iface, scripted.Stationary())
    p0 = w.pos.clone()
    for _ in range(20):
        w.tick()
        assert (w.last_forward[w.alive] == 0).all()
    moved = (w.pos - p0).norm(dim=-1)[w.alive]
    # weys start packed in a spawn box, and crowding pushes them apart by up to crowd_push a tick
    assert moved.max() <= 20 * cfg.world.crowd_push + 1e-5
    w = world_for(cfg, iface, scripted.Straight())
    p0 = w.pos.clone()
    for _ in range(20):
        w.tick()
    assert (w.pos - p0).norm(dim=-1)[w.alive].mean() > 2.0


def test_one_step_memory_turns_only_when_concentration_falls():
    pol = scripted.OneStepMemory(speed=0.8, turn=0.9, threshold=0.0)
    s = pol.init(1, 2)
    x = torch.tensor([[1.0, 1.0]])
    f, t, s = pol(x, x, s)                       # first step: no history
    assert torch.all(t == 0)
    f, t, s = pol(torch.tensor([[1.2, 0.5]]), torch.tensor([[1.2, 0.5]]), s)
    assert t[0, 0] == 0 and t[0, 1] == pytest.approx(0.9)


def test_rollout_brain_matches_rollout_for_a_real_brain(parts):
    con, iface = parts
    cfg = Config()
    cfg.world.max_ticks = 60
    spec = BrainSpec.from_connectome(con)
    g = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(1))
    ids = np.arange(3)
    a = rollout(cfg, iface, g, ids, 4)
    b = rollout_brain(cfg, iface, Brain(g), ids, 4)
    np.testing.assert_array_equal(a.score, b.score)
    assert a.pellet_eaten is not None and a.pellet_eaten.shape == a.score.shape


def test_scores_are_finite_when_everyone_starves(parts):
    _, iface = parts
    cfg = Config()
    cfg.world.max_ticks = 500
    s = scripted.score_policy(cfg, iface, scripted.Stationary(), np.arange(2), 1, "cpu")
    assert np.isfinite(s).all() and (s >= 0).all()


@pytest.mark.skipif(not torch.cuda.is_available(), reason="needs CUDA")
def test_state_lives_on_the_requested_device(parts):
    _, iface = parts
    b = scripted.ScriptedBrain(iface, 302, scripted.Stationary(), 4.0, 2.0, device="cuda")
    assert b.initial_state(3).device.type == "cuda"


def test_tune_returns_the_best_grid_point(parts):
    _, iface = parts
    cfg = Config()
    cfg.world.max_ticks = 80
    best, score = scripted.tune(
        lambda speed: scripted.StereoProportional(k=2.0, speed=speed),
        {"speed": [0.0, 0.8]}, cfg, iface, np.arange(2), 1, "cpu",
    )
    assert best == {"speed": 0.8} and np.isfinite(score)
