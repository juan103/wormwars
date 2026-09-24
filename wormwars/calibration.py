"""Per-graph motor gain calibration.

**Why this exists.** The motor read-out is a difference of means of `tanh(v)` over named neurons,
scaled by a constant gain. That gain was chosen by looking at N2 (DECISIONS.md D014). But the raw
read-out magnitude depends on the *graph*: how much drive reaches `AVB`/`PVC` versus `AVA`/`AVD`
from a random genome is a property of the wiring around those particular neurons.

Measured, 24 random genomes per graph, 80 ticks, identical seeds:

    graph   mean |forward| (raw)
    N2      0.322      <- the weakest of the seven (see the note below)
    SH1     0.603
    SH2     0.397
    SH3     0.399
    RD1     0.450
    RD2     0.591
    RD3     0.401

With one fixed gain, N2 weys simply *move less* than the controls before evolution starts, and
foraging rewards moving. A comparison run that way is partly measuring which graph happens to drive
the read-out harder, which is not the claim under test.

**Note (DECISIONS.md D031):** this table was measured with chemical synapses running backwards.
With them the right way round, N2 is among the strongest drivers, not the weakest (random-
population |forward| at unit gain: N2 0.157, second of eleven graphs). And calibration equalises
drive only approximately: measured again at the fitted gains, the eleven graphs of experiment
01b reach 84-97% of the target |forward| (N2 95%), because clipping and sensory feedback make
the response to gain non-linear (D033).

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


@dataclass
class DriveReport:
    """What a random population actually does at the configured gains, in the real world."""

    forward: float  # mean |forward command| over ticks and living weys
    turn: float
    clip_forward: float  # share of commands at the +-1 clip
    clip_turn: float
    displacement: float  # mean distance moved per tick
    forward_signed: float  # mean signed forward command: moving forward vs reversing
    reversing: float  # share of commands below zero

    def as_dict(self) -> dict:
        return dict(vars(self))


def achieved_drive(graph, cfg, iface, n_strains=24, ticks=80, seed=0, device="cpu") -> DriveReport:
    """Drive of a random population at `cfg`'s gains, measured inside the world it will run in.

    With the same seed and n_strains = population, the genomes are exactly the generation-0
    population `evolve` starts from for that run seed.
    """
    from .world import World

    probe = cfg.copy()
    probe.world.n_swarms = 1
    spec = BrainSpec.from_connectome(graph, device=device)
    gen = torch.Generator(device=device).manual_seed(seed)
    genome = Genome.random(spec, probe.brain, n_strains, generator=gen, device=device)
    world = World(probe, iface, Brain(genome), torch.arange(n_strains).reshape(n_strains, 1),
                  run_seed=seed, device=device)
    acc = np.zeros(7)
    n = 0
    for _ in range(ticks):
        pos0 = world.pos.clone()
        world.tick()
        alive = world.alive
        if not bool(alive.any()):
            break
        fs, ts = world.last_forward[alive], world.last_turn[alive]
        f, t = fs.abs(), ts.abs()
        acc += [float(f.mean()), float(t.mean()), float((f >= 1 - 1e-6).float().mean()),
                float((t >= 1 - 1e-6).float().mean()),
                float((world.pos - pos0).norm(dim=-1)[alive].mean()),
                float(fs.mean()), float((fs < 0).float().mean())]
        n += 1
    acc /= max(n, 1)
    return DriveReport(*[float(x) for x in acc])


@dataclass
class InWorldCalibration:
    graph: str
    forward_gain: float
    turn_gain: float
    target: tuple
    achieved: DriveReport
    iterations: int
    history: list

    def as_dict(self) -> dict:
        d = dict(vars(self))
        d["achieved"] = self.achieved.as_dict()
        d["target"] = list(self.target)
        return d


def calibrate_in_world(graph, cfg, iface, target, *, n_strains=24, ticks=80, seed=0,
                       device="cpu", tol=0.02, max_iter=8, max_gain=40.0) -> InWorldCalibration:
    """Multiplicative fixed-point iteration on the gains until the achieved drive is within `tol`
    of `target` on both axes. Clipping and sensory feedback make the response non-linear, which is
    why one linear fit (the old `calibrate`) lands at 84-97% of target and this iterates."""
    c = cfg.copy()
    history = []
    for it in range(1, max_iter + 1):
        d = achieved_drive(graph, c, iface, n_strains, ticks, seed, device)
        history.append({"forward_gain": c.world.forward_gain, "turn_gain": c.world.turn_gain,
                        **d.as_dict()})
        if abs(d.forward / target[0] - 1) <= tol and abs(d.turn / target[1] - 1) <= tol:
            return InWorldCalibration(graph.label, float(c.world.forward_gain),
                                      float(c.world.turn_gain), tuple(target), d, it, history)
        c.world.forward_gain = min(c.world.forward_gain * target[0] / max(d.forward, 1e-9), max_gain)
        c.world.turn_gain = min(c.world.turn_gain * target[1] / max(d.turn, 1e-9), max_gain)
    raise RuntimeError(
        f"calibration of {graph.label} did not converge within {max_iter} iterations: {history[-1]}"
    )
