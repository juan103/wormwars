"""03h's bit probe and amplitude override (PILOT.md §4, §5.4): the turn response is zero without the channel's
neurons connected, nonzero with them, and scales with the amplitude; the override changes only food_fell's gain."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e03h import AMPLITUDE, interface_03h
from wormwars.e03h.probes import bit_turn_response
from wormwars.exp02 import grid

ROOT = Path(__file__).resolve().parents[1]


def test_the_amplitude_override_changes_only_the_bits_gain():
    con = load_connectome()
    a, b = interface_03h(con), interface_03h(con, 0.5)
    ff = [i for i, n in enumerate(a.signal_names) if n == "food_fell"]
    other = [i for i in range(len(a.signal_names)) if i not in ff]
    assert np.allclose(a.sensor_gain[ff], AMPLITUDE) and np.allclose(b.sensor_gain[ff], 0.5)
    assert np.array_equal(a.sensor_gain[other], b.sensor_gain[other])
    assert np.array_equal(a.sensor_neuron, b.sensor_neuron)


def test_the_bit_reaches_the_turn_readout_and_scales_with_the_amplitude():
    con = load_connectome()
    cfg = grid.task_config(Config(), "T1")
    bank = json.loads((ROOT / "experiments" / "03-generation0" / "pilot.json").read_text(encoding="utf-8"))["bank"]
    g = Genome.random(BrainSpec.from_connectome(con), cfg.brain, 8, generator=torch.Generator().manual_seed(2))
    r25 = bit_turn_response(g, cfg, interface_03h(con), bank, warm=20)
    r50 = bit_turn_response(g, cfg, interface_03h(con, 0.5), bank, warm=20)
    r0 = bit_turn_response(g, cfg, interface_03h(con, 0.0), bank, warm=20)
    assert np.all(r0 == 0) and np.abs(r25).sum() > 0
    assert np.abs(r50).mean() > np.abs(r25).mean()
