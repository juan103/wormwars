"""E1's scripted navigators, blind baselines and the oracle (docs/E1/DESIGN.md, "Controls").

Policies follow `wormwars.exp02.scripted`: `init(strains, rows)` returns a state, and
`__call__(left, right, state)` returns (forward, turn, state), all [strains, rows], with parameters
that may be [strains, 1] tensors so `tune_batched` can run a whole grid as one batch. A policy with
`needs_collision = True` also receives the declared collision inputs as `collision`, the same
current a brain gets at those sensor neurons; no control gets privileged coordinates. The oracle
alone is privileged, and it is kept outside that observation path.
"""

from __future__ import annotations

import math

import torch

from ..exp02.scripted import MemoryKinesis, ScriptedBrain, StereoKinesis


def scripted(iface, policy, cfg, n_strains: int = 1, device="cpu", n: int = 302) -> ScriptedBrain:
    return ScriptedBrain(iface, n, policy, cfg.world.forward_gain, cfg.world.turn_gain,
                         n_strains=n_strains, device=device)


def s_const(k, speed, turn) -> StereoKinesis:
    """S-const: stereo steering added to a constant turn, at one constant speed. It is
    `StereoKinesis` with slow = fast, as the design defines it; with no signal it keeps turning, so
    it does not jam in a corner (Fable, D078)."""
    return StereoKinesis(k, speed, speed, 0.0, turn)


def m_avg(slow, fast, threshold, turn, fall_turn, fall_threshold) -> MemoryKinesis:
    """M-avg: the M family on the average of the two stereo readings (`MemoryKinesis` already reads
    the mean), comparing with the previous tick."""
    return MemoryKinesis(slow, fast, threshold, turn, fall_turn, fall_threshold)


class ConstantMotion:
    """Blind: constant speed and constant turn, which covers circling at any curvature."""

    def __init__(self, speed, turn):
        self.speed, self.turn = speed, turn

    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        one = torch.ones_like(left)
        return self.speed * one, self.turn * one, state


class PersistentRandomWalk:
    """Blind: constant speed with a persistent random turn, u_t = p u_(t-1) + sqrt(1 - p^2) e_t and
    turn = rate x u_t. The noise comes from a generator seeded at `init`, so a run repeats exactly."""

    def __init__(self, speed, rate, persistence, seed: int = 0):
        self.speed, self.rate, self.persistence, self.seed = speed, rate, persistence, int(seed)

    def init(self, s, b):
        return {"gen": torch.Generator().manual_seed(self.seed), "u": None}

    def __call__(self, left, right, state):
        u = torch.zeros_like(left) if state["u"] is None else state["u"]
        eps = torch.randn(tuple(left.shape), generator=state["gen"]).to(left.device, left.dtype)
        p = torch.as_tensor(self.persistence, dtype=left.dtype, device=left.device)
        u = p * u + torch.sqrt(1 - p * p) * eps
        turn = (self.rate * u).clamp(-1, 1)
        return self.speed * torch.ones_like(left), turn, {"gen": state["gen"], "u": u}


class WallFollower:
    """Blind, using the declared collision inputs: keep a wall on the right. Turn left by
    `avoid_turn` when the front or front-right reading exceeds `threshold`, otherwise curve right by
    `seek_turn` to find the wall again. The threshold must sit above what the wey's own body
    produces at those sensors (Fable, D078); the pilot measures that level."""

    needs_collision = True

    def __init__(self, speed, seek_turn, avoid_turn, threshold):
        self.speed, self.seek_turn, self.avoid_turn, self.threshold = speed, seek_turn, avoid_turn, threshold

    def init(self, s, b):
        return None

    def __call__(self, left, right, state, collision=None):
        near = torch.maximum(collision["front"], collision["front_right"]) > self.threshold
        one = torch.ones_like(left)
        turn = torch.where(near, self.avoid_turn * one, self.seek_turn * one)
        return self.speed * one, turn, state


class OracleBrain(ScriptedBrain):
    """The ceiling, not a control: it steers at the true target position. Its position, heading and
    target come from the world directly (privileged plumbing), never through the observation path
    the controls use. One strain only."""

    def __init__(self, iface, n, forward_gain, turn_gain, k: float = 2.0, speed: float = 1.0, device="cpu"):
        super().__init__(iface, n, ConstantMotion(speed, 0.0), forward_gain, turn_gain, n_strains=1, device=device)
        self.k, self.speed, self.world = float(k), float(speed), None

    def attach_world(self, world) -> None:
        self.world = world

    def step(self, v, current):
        w = self.world
        head, heading = w.pos[:, 0, 0], w.heading[:, 0, 0]
        c = w.current_target()
        want = torch.atan2(c[:, 1] - head[:, 1], c[:, 0] - head[:, 0])
        diff = torch.remainder(want - heading + math.pi, 2 * math.pi) - math.pi
        turn = (self.k * diff).clamp(-1, 1).view(1, -1)
        fwd = torch.full_like(turn, self.speed)
        return self.command(current, fwd, turn)
