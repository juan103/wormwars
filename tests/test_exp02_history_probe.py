"""History-only ablations of the food signal: evaluation probes, never used in selection."""

from __future__ import annotations

import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.fields import sample_bilinear
from wormwars.interface import load_interface
from wormwars.world import N_POINTS, P_FRONT_C, World


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def build(parts, cfg, n=4):
    con, iface, spec = parts
    g = Genome.random(spec, cfg.brain, n, generator=torch.Generator().manual_seed(0))
    return World(cfg, iface, Brain(g), torch.arange(n).reshape(n, 1), run_seed=3)


def head_food(w):
    pts = w.sample_points()
    sampled = sample_bilinear(w.fields, pts).reshape(w.n_worlds, w.ch.n, w.n_swarms, w.n_weys, N_POINTS)
    return w._sensor_signals(sampled)["food_left"]


def test_hold_refreshes_only_every_h_ticks(parts):
    cfg = Config()
    cfg.world.food_sensing = "mono"
    cfg.world.food_probe = "hold"
    cfg.world.food_probe_hold = 4
    w = build(parts, cfg)
    seen = []
    for _ in range(8):
        w.tick()
        seen.append(w._held_food.clone())
    for t in (1, 2, 3):
        assert torch.equal(seen[t], seen[0])
    assert not torch.equal(seen[4], seen[3]) or torch.equal(seen[4], seen[0])  # refreshed at t=4


def test_jitter_is_reproducible_and_changes_the_reading(parts):
    cfg = Config()
    cfg.world.food_sensing = "mono"
    cfg.world.food_probe = "jitter"
    cfg.world.food_probe_radius = 2.0
    a, b = build(parts, cfg), build(parts, cfg)
    for _ in range(3):
        a.tick()
        b.tick()
    torch.testing.assert_close(a._food_sample, b._food_sample)  # seeded: identical worlds agree
    real = cfg.copy()
    real.world.food_probe = "real"
    r = build(parts, real)
    for _ in range(3):
        r.tick()
    assert not torch.allclose(a._food_sample[..., P_FRONT_C], r._sensed_food(r.sample_points())[..., P_FRONT_C])


def test_probe_parameters_default_to_no_effect():
    c = Config()
    assert c.world.food_probe_radius == 0.0 and c.world.food_probe_hold == 1
