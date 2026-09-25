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


def test_batched_tuning_matches_one_at_a_time(parts):
    """Every grid point becomes one strain in a single world batch; the winner and its score
    must be exactly what evaluating the points one by one gives."""
    _, iface = parts
    cfg = Config()
    cfg.world.max_ticks = 60
    grid_ = {"slow": [0.0, 0.3], "fast": [0.6, 1.0], "threshold": [0.02], "turn": [0.0, 0.2]}
    make = lambda slow, fast, threshold, turn: scripted.LevelKinesis(slow, fast, threshold, turn)  # noqa: E731
    seq = scripted.tune(make, grid_, cfg, iface, np.arange(3), 1, "cpu")
    bat = scripted.tune_batched(make, grid_, cfg, iface, np.arange(3), 1, "cpu")
    assert seq[0] == bat[0]
    assert abs(seq[1] - bat[1]) < 1e-5


def test_memory_kinesis_contains_level_kinesis_as_a_special_case():
    """With no reaction to falling concentration, the memory controller IS the memoryless one,
    so a fair gate compares 'everything memoryless can do' with 'that plus memory'."""
    lk = scripted.LevelKinesis(slow=0.3, fast=0.9, threshold=0.05, turn=0.1)
    mk = scripted.MemoryKinesis(slow=0.3, fast=0.9, threshold=0.05, turn=0.1, fall_turn=0.1, fall_threshold=0.0)
    s1, s2 = lk.init(1, 3), mk.init(1, 3)
    for lvl in ([0.01, 0.2, 0.06], [0.5, 0.1, 0.07], [0.2, 0.3, 0.01]):
        x = torch.tensor([lvl])
        f1, t1, s1 = lk(x, x, s1)
        f2, t2, s2 = mk(x, x, s2)
        assert torch.equal(f1, f2) and torch.allclose(t1, t2)


def test_memory_kinesis_turns_harder_when_concentration_falls():
    mk = scripted.MemoryKinesis(slow=0.3, fast=0.9, threshold=0.05, turn=0.1, fall_turn=0.8, fall_threshold=0.0)
    s = mk.init(1, 1)
    _, _, s = mk(torch.tensor([[0.5]]), torch.tensor([[0.5]]), s)
    _, t, s = mk(torch.tensor([[0.4]]), torch.tensor([[0.4]]), s)
    assert t.item() == pytest.approx(0.8)


def test_stereo_kinesis_contains_level_kinesis_when_k_is_zero():
    lk = scripted.LevelKinesis(slow=0.3, fast=0.9, threshold=0.05, turn=0.1)
    sk = scripted.StereoKinesis(k=0.0, slow=0.3, fast=0.9, threshold=0.05, turn=0.1)
    l, r = torch.tensor([[0.2, 0.01]]), torch.tensor([[0.1, 0.02]])
    f1, t1, _ = lk(l, r, None)
    f2, t2, _ = sk(l, r, None)
    assert torch.equal(f1, f2) and torch.allclose(t1, t2)
