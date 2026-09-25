"""Stereo ablations (Astra's decision review, point 5): the bilateral mean removes only the
left-right difference and keeps the common mode; the swap reverses the difference."""

from __future__ import annotations

import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.interface import load_interface
from wormwars.world import World

from test_exp02_world import signals_now


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def pair(parts, probe, odour=0.0):
    """The same world run twice for five ticks, once real and once under the probe, read on the
    real world's state (the probe only changes what is sensed, so the reads are comparable)."""
    con, iface, spec = parts
    cfg = Config()
    cfg.world.food_odour_sigma = odour
    genome = Genome.random(spec, cfg.brain, 4, generator=torch.Generator().manual_seed(0))
    w = World(cfg, iface, Brain(genome), torch.arange(4).reshape(4, 1), run_seed=3)
    for _ in range(5):
        w.tick()
    _, real = signals_now(w)
    w.cfg = cfg.copy()
    w.cfg.world.food_probe = probe
    _, probed = signals_now(w)
    return real, probed


@pytest.mark.parametrize("odour", [0.0, 1.0])
def test_mean_feeds_the_bilateral_mean_to_both_sides(parts, odour):
    real, probed = pair(parts, "mean", odour)
    mean = (real["food_left"] + real["food_right"]) / 2
    torch.testing.assert_close(probed["food_left"], mean)
    torch.testing.assert_close(probed["food_right"], mean)


@pytest.mark.parametrize("odour", [0.0, 1.0])
def test_swap_exchanges_the_sides(parts, odour):
    real, probed = pair(parts, "swapped", odour)
    torch.testing.assert_close(probed["food_left"], real["food_right"])
    torch.testing.assert_close(probed["food_right"], real["food_left"])


def test_stereo_probes_leave_other_signals_alone(parts):
    for probe in ("mean", "swapped"):
        real, probed = pair(parts, probe)
        for k in real:
            if not k.startswith("food_"):
                torch.testing.assert_close(probed[k], real[k])
