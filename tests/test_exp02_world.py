"""World options for experiment 02: mono food sensing, food probes, and pure measurements."""

from __future__ import annotations

import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.fields import sample_bilinear
from wormwars.interface import load_interface
from wormwars.world import N_POINTS, P_FRONT_C, P_FRONT_L, P_FRONT_R, World


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def build(parts, cfg=None, n=4, seed=0):
    con, iface, spec = parts
    cfg = cfg or Config()
    genome = Genome.random(spec, cfg.brain, n, generator=torch.Generator().manual_seed(seed))
    return World(cfg, iface, Brain(genome), torch.arange(n).reshape(n, 1), run_seed=3)


def signals_now(w):
    pts = w.sample_points()
    sampled = sample_bilinear(w.fields, pts).reshape(
        w.n_worlds, w.ch.n, w.n_swarms, w.n_weys, N_POINTS
    )
    return sampled, w._sensor_signals(sampled)


def test_defaults_are_stereo_and_real():
    c = Config()
    assert c.world.food_sensing == "stereo" and c.world.food_probe == "real"


def test_mono_copies_the_head_sample_to_both_sides(parts):
    cfg = Config()
    cfg.world.food_sensing = "mono"
    w = build(parts, cfg)
    for _ in range(5):
        w.tick()
    sampled, sig = signals_now(w)
    food = sampled[:, w.ch.FOOD] + sampled[:, w.ch.PELLET]
    expect = food[..., P_FRONT_C] * cfg.world.sense_scale_food
    torch.testing.assert_close(sig["food_left"], expect)
    torch.testing.assert_close(sig["food_right"], expect)


def test_stereo_default_reads_left_and_right(parts):
    w = build(parts)
    for _ in range(5):
        w.tick()
    sampled, sig = signals_now(w)
    food = sampled[:, w.ch.FOOD] + sampled[:, w.ch.PELLET]
    sf = w.cfg.world.sense_scale_food
    torch.testing.assert_close(sig["food_left"], food[..., P_FRONT_L] * sf)
    torch.testing.assert_close(sig["food_right"], food[..., P_FRONT_R] * sf)


def test_constant_probe_carries_no_spatial_information(parts):
    cfg = Config()
    cfg.world.food_probe = "constant"
    w = build(parts, cfg)
    for _ in range(5):
        w.tick()
    _, sig = signals_now(w)
    left = sig["food_left"]
    # one value per world, identical for every wey and both sides
    assert torch.allclose(left, left[:, :1, :1].expand_as(left))
    torch.testing.assert_close(sig["food_left"], sig["food_right"])


def test_mirrored_probe_reads_the_point_reflection(parts):
    cfg = Config()
    cfg.world.food_probe = "mirrored"
    w = build(parts, cfg)
    for _ in range(5):
        w.tick()
    pts = w.sample_points()
    w._food_sample = w._probe_food(pts)
    sampled, sig = signals_now(w)
    x, y = pts[..., 0], pts[..., 1]
    mirrored = torch.stack((w.W - 1 - x, w.H - 1 - y), dim=-1)
    s = sample_bilinear(w.fields[:, w.ch.FOOD : w.ch.PELLET + 1].contiguous(), mirrored)
    food = (s[:, 0] + s[:, 1]).reshape(w.n_worlds, w.n_swarms, w.n_weys, N_POINTS)
    sf = cfg.world.sense_scale_food
    torch.testing.assert_close(sig["food_left"], food[..., P_FRONT_L] * sf)


def test_unknown_options_are_rejected(parts):
    for field, bad in (("food_sensing", "trinocular"), ("food_probe", "psychic")):
        cfg = Config()
        setattr(cfg.world, field, bad)
        with pytest.raises(ValueError, match=field):
            build(parts, cfg)


def test_intake_splits_into_plant_food_and_pellets(parts):
    w = build(parts)
    food0 = w.fields[:, w.ch.FOOD].double().sum(dim=(1, 2))
    for _ in range(300):
        w.tick()
    plant = food0 - w.fields[:, w.ch.FOOD].double().sum(dim=(1, 2))
    total = w.energy_eaten.sum(dim=1)
    assert (w.pellet_eaten >= -1e-6).all()
    torch.testing.assert_close(total, plant + w.pellet_eaten, rtol=1e-4, atol=1e-3)


def test_motor_commands_are_recorded_each_tick(parts):
    w = build(parts)
    w.tick()
    assert w.last_forward.shape == (w.n_worlds, w.n_swarms, w.n_weys)
    assert w.last_turn.shape == w.last_forward.shape
    assert w.last_forward.abs().max() <= 1.0
