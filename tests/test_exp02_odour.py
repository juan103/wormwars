"""Food odour: an opt-in long-range scent, so a gradient reaches beyond a patch's edge."""

from __future__ import annotations

import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.fields import sample_bilinear
from wormwars.interface import load_interface
from wormwars.world import N_POINTS, P_FRONT_C, P_FRONT_L, World, gaussian_blur


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def build(parts, cfg, n=2):
    con, iface, spec = parts
    g = Genome.random(spec, cfg.brain, n, generator=torch.Generator().manual_seed(0))
    return World(cfg, iface, Brain(g), torch.arange(n).reshape(n, 1), run_seed=3)


def test_default_is_no_odour():
    assert Config().world.food_odour_sigma == 0.0


def test_blur_spreads_a_point_and_keeps_its_mass_away_from_walls():
    f = torch.zeros(1, 21, 21)
    f[0, 10, 10] = 1.0
    b = gaussian_blur(f, 2.0)
    assert abs(float(b.sum()) - 1.0) < 1e-4
    assert b[0, 10, 10] < 1.0 and b[0, 10, 13] > 0 and b[0, 13, 10] > 0
    assert torch.allclose(b[0], b[0].T, atol=1e-7), "isotropic"


def test_sensing_reads_the_blurred_field(parts):
    cfg = Config()
    cfg.world.food_odour_sigma = 2.0
    w = build(parts, cfg)
    w.tick()
    pts = w.sample_points()
    odour = gaussian_blur(w.fields[:, w.ch.FOOD] + w.fields[:, w.ch.PELLET], 2.0)
    expect = sample_bilinear(odour.unsqueeze(1), pts)[:, 0].reshape(
        w.n_worlds, w.n_swarms, w.n_weys, N_POINTS)
    w._food_sample = w._sensed_food(pts)
    sampled = sample_bilinear(w.fields, pts).reshape(w.n_worlds, w.ch.n, w.n_swarms, w.n_weys, N_POINTS)
    sig = w._sensor_signals(sampled)
    sf = cfg.world.sense_scale_food
    torch.testing.assert_close(sig["food_left"], expect[..., P_FRONT_L] * sf)


def test_odour_reaches_further_than_raw_food(parts):
    raw, od = Config(), Config()
    od.world.food_odour_sigma = 2.0
    w_raw, w_od = build(parts, raw), build(parts, od)
    f = w_raw.fields[:, w_raw.ch.FOOD]
    blurred = gaussian_blur(f, 2.0)
    assert int((blurred > 1e-3).sum()) > int((f > 1e-3).sum())


def test_mono_with_odour_copies_the_head_sample(parts):
    cfg = Config()
    cfg.world.food_odour_sigma = 2.0
    cfg.world.food_sensing = "mono"
    w = build(parts, cfg)
    w.tick()
    pts = w.sample_points()
    w._food_sample = w._sensed_food(pts)
    sampled = sample_bilinear(w.fields, pts).reshape(w.n_worlds, w.ch.n, w.n_swarms, w.n_weys, N_POINTS)
    sig = w._sensor_signals(sampled)
    torch.testing.assert_close(sig["food_left"], sig["food_right"])
    torch.testing.assert_close(sig["food_left"], w._food_sample[..., P_FRONT_C] * cfg.world.sense_scale_food)
