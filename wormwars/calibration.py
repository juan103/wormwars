"""Per-graph motor gain calibration.

**Why this exists.** The motor read-out is a difference of means of `tanh(v)` over named neurons,
scaled by a constant gain. That gain was chosen by looking at N2 (DECISIONS.md D014). But the raw
read-out magnitude depends on the *graph*: how much drive reaches `AVB`/`PVC` versus `AVA`/`AVD`
from a random genome is a property of the wiring around those particular neurons.

Measured, 24 random genomes per graph, 80 ticks, identical seeds:

    graph   mean |forward| (raw)
    N2      0.322      <- the weakest of the seven
    SH1     0.603
    SH2     0.397
    SH3     0.399
    RD1     0.450
    RD2     0.591
    RD3     0.401

With one fixed gain, N2 weys simply *move less* than the controls before evolution starts, and
foraging rewards moving. A comparison run that way is partly measuring which graph happens to drive
the read-out harder, which is not the claim under test.

Calibration removes that nuisance variable: each graph's gain is set so that a random population
produces the same mean |forward| and |turn| as N2 does at the hand-chosen gain. Everything else --
initialisation distribution, mutation, population size, evaluation budget -- stays identical, as the
experimental design requires.

This is a judgement call, so results are reported **both ways**: uncalibrated (one fixed gain, as
the spec literally describes) and calibrated. Saying which is which is part of the result.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from .brain import Brain, BrainSpec, Genome
from .config import Config
from .connectome.loader import Connectome
from .interface import Interface


@dataclass(frozen=True)
class MotorCalibration:
    graph: str
    forward_gain: float
    turn_gain: float
    raw_forward: float  # what a random population produced before scaling
    raw_turn: float
    reference_forward: float
    reference_turn: float
    n_strains: int
    ticks: int
    seed: int

    def as_dict(self) -> dict:
        return {
            "graph": self.graph,
            "forward_gain": self.forward_gain,
            "turn_gain": self.turn_gain,
            "raw_forward": self.raw_forward,
            "raw_turn": self.raw_turn,
            "reference_forward": self.reference_forward,
            "reference_turn": self.reference_turn,
            "n_strains": self.n_strains,
            "ticks": self.ticks,
            "seed": self.seed,
        }


def raw_motor_magnitude(
    graph: Connectome,
    cfg: Config,
    iface: Interface,
    n_strains: int = 24,
    ticks: int = 80,
    seed: int = 0,
    device: str = "cpu",
) -> tuple[float, float]:
    """Mean |forward| and |turn| of a random population, measured *before* the configured gains.

    Deliberately measured inside a real world rather than on white noise, so that whatever the
    sensors feed back into the network is part of the measurement.
    """
    from .world import World

    probe = cfg.copy()
    probe.world.forward_gain = 1.0
    probe.world.turn_gain = 1.0
    probe.world.n_swarms = 1
    spec = BrainSpec.from_connectome(graph, device=device)
    gen = torch.Generator(device=device).manual_seed(seed)
    genome = Genome.random(spec, probe.brain, n_strains, generator=gen, device=device)
    world = World(
        probe, iface, Brain(genome),
        torch.arange(n_strains).reshape(n_strains, 1), run_seed=seed, device=device,
    )
    for _ in range(ticks):
        world.tick()
    fwd, turn, _ = world._read_motors(world.neuron_state())
    return float(fwd.abs().mean()), float(turn.abs().mean())


def calibrate(
    graph: Connectome,
    cfg: Config,
    iface: Interface,
    reference: tuple[float, float] | None = None,
    n_strains: int = 24,
    ticks: int = 80,
    seed: int = 0,
    device: str = "cpu",
    max_gain: float = 40.0,
) -> MotorCalibration:
    """Gains for `graph` that match `reference` = (target |forward|, target |turn|) after scaling.

    With `reference = None` the graph's own measurement is used, i.e. the configured gains are
    returned unchanged -- useful for establishing the reference from N2 itself.
    """
    raw_f, raw_t = raw_motor_magnitude(graph, cfg, iface, n_strains, ticks, seed, device)
    if reference is None:
        ref_f = raw_f * cfg.world.forward_gain
        ref_t = raw_t * cfg.world.turn_gain
        gain_f, gain_t = cfg.world.forward_gain, cfg.world.turn_gain
    else:
        ref_f, ref_t = reference
        gain_f = min(ref_f / max(raw_f, 1e-9), max_gain)
        gain_t = min(ref_t / max(raw_t, 1e-9), max_gain)
    return MotorCalibration(
        graph=graph.label,
        forward_gain=float(gain_f),
        turn_gain=float(gain_t),
        raw_forward=raw_f,
        raw_turn=raw_t,
        reference_forward=float(ref_f),
        reference_turn=float(ref_t),
        n_strains=n_strains,
        ticks=ticks,
        seed=seed,
    )


def reference_from(
    con: Connectome, cfg: Config, iface: Interface, **kw
) -> tuple[float, float]:
    """The target magnitudes, taken from N2 at the hand-chosen gains. N2 is the reference so that
    its own behaviour is unchanged by calibration and only the controls move."""
    c = calibrate(con, cfg, iface, reference=None, **kw)
    return c.reference_forward, c.reference_turn


def apply(cfg: Config, cal: MotorCalibration) -> Config:
    """A copy of `cfg` with this graph's calibrated gains."""
    out = cfg.copy()
    out.world.forward_gain = cal.forward_gain
    out.world.turn_gain = cal.turn_gain
    return out
