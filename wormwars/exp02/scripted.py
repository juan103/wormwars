"""Scripted controllers: reference levels for each task, played through the real world.

A ScriptedBrain stands in for Brain. It reads the injected current at the food neurons of the
interface it is given (the same observation an evolved brain gets) and writes motor commands by
setting the read-out neurons so that the world's own read-out reproduces the command exactly:
forward = mean(tanh v+) - mean(tanh v-), scaled by 0.5 x gain. With tanh v+ = c / gain and
tanh v- = -c / gain, the final command is c.
"""

from __future__ import annotations

import itertools

import numpy as np
import torch

from ..evo.rollout import rollout_brain


class ScriptedBrain:
    def __init__(self, iface, n, policy, forward_gain, turn_gain, n_strains=1, device="cpu"):
        self.n, self.n_strains, self.policy = n, n_strains, policy
        self.forward_gain, self.turn_gain = float(forward_gain), float(turn_gain)
        self.device = torch.device(device)
        names = list(iface.signal_names)
        self.left = int(iface.sensor_neuron[names.index("food_left")])
        self.right = int(iface.sensor_neuron[names.index("food_right")])
        t = lambda a: torch.as_tensor(np.asarray(a), dtype=torch.long, device=self.device)  # noqa: E731
        self.fp, self.fm = t(iface.forward_plus), t(iface.forward_minus)
        self.tp, self.tm = t(iface.turn_plus), t(iface.turn_minus)
        self.state = None

    def initial_state(self, n_weys: int) -> torch.Tensor:
        self.state = self.policy.init(self.n_strains, n_weys)
        return torch.zeros(self.n_strains, n_weys, self.n, device=self.device)

    def step(self, v: torch.Tensor, current: torch.Tensor) -> torch.Tensor:
        left, right = current[..., self.left], current[..., self.right]
        fwd, turn, self.state = self.policy(left, right, self.state)
        out = torch.zeros_like(current)
        a_f = torch.atanh((fwd / self.forward_gain).clamp(-0.999999, 0.999999))
        a_t = torch.atanh((turn / self.turn_gain).clamp(-0.999999, 0.999999))
        out[..., self.fp] = a_f.unsqueeze(-1)
        out[..., self.fm] = -a_f.unsqueeze(-1)
        out[..., self.tp] = a_t.unsqueeze(-1)
        out[..., self.tm] = -a_t.unsqueeze(-1)
        return out


class Stationary:
    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        z = torch.zeros_like(left)
        return z, z, state


class Straight:
    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        return torch.ones_like(left), torch.zeros_like(left), state


class StereoProportional:
    """Memoryless, stereo: steer toward the stronger side at a constant speed."""

    def __init__(self, k: float, speed: float):
        self.k, self.speed = k, speed

    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        turn = (self.k * (left - right)).clamp(-1, 1)
        return self.speed * torch.ones_like(left), turn, state


class LevelKinesis:
    """Memoryless, mono: slow down where food is strong, speed up where it is weak, keep turning."""

    def __init__(self, slow: float, fast: float, threshold: float, turn: float):
        self.slow, self.fast, self.threshold, self.turn = slow, fast, threshold, turn

    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        level = (left + right) / 2
        one = torch.ones_like(level)
        fwd = torch.where(level > self.threshold, self.slow * one, self.fast * one)
        return fwd, self.turn * one, state


class OneStepMemory:
    """Mono, one tick of memory: go straight while concentration holds, turn when it falls."""

    def __init__(self, speed: float, turn: float, threshold: float):
        self.speed, self.turn, self.threshold = speed, turn, threshold

    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        level = (left + right) / 2
        if state is None:
            falling = torch.zeros_like(level, dtype=torch.bool)
        else:
            falling = level < state - self.threshold
        one = torch.ones_like(level)
        turn = torch.where(falling, self.turn * one, torch.zeros_like(level))
        return self.speed * one, turn, level.clone()


class MemoryKinesis:
    """Everything LevelKinesis does, plus one tick of memory: turn by `fall_turn` instead of
    `turn` when concentration has fallen since the last tick. With fall_turn == turn it IS
    LevelKinesis, so a gate comparing the two measures what memory adds, not a different policy."""

    def __init__(self, slow, fast, threshold, turn, fall_turn, fall_threshold):
        self.slow, self.fast, self.threshold, self.turn = slow, fast, threshold, turn
        self.fall_turn, self.fall_threshold = fall_turn, fall_threshold

    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        level = (left + right) / 2
        one = torch.ones_like(level)
        fwd = torch.where(level > self.threshold, self.slow * one, self.fast * one)
        if state is None:
            falling = torch.zeros_like(level, dtype=torch.bool)
        else:
            falling = level < state - self.fall_threshold
        turn = torch.where(falling, self.fall_turn * one, self.turn * one)
        return fwd, turn, level.clone()


class StereoKinesis:
    """Everything LevelKinesis does, plus stereo steering toward the stronger side. With k == 0
    it IS LevelKinesis."""

    def __init__(self, k, slow, fast, threshold, turn):
        self.k, self.slow, self.fast, self.threshold, self.turn = k, slow, fast, threshold, turn

    def init(self, s, b):
        return None

    def __call__(self, left, right, state):
        level = (left + right) / 2
        one = torch.ones_like(level)
        fwd = torch.where(level > self.threshold, self.slow * one, self.fast * one)
        turn = (self.turn * one + self.k * (left - right)).clamp(-1, 1)
        return fwd, turn, state


def score_policy(cfg, iface, policy, world_ids, run_seed, device) -> np.ndarray:
    """Per-world foraging score of one scripted policy, shape [worlds]."""
    brain = ScriptedBrain(iface, 302, policy, cfg.world.forward_gain, cfg.world.turn_gain,
                          device=device)
    return rollout_brain(cfg, iface, brain, world_ids, run_seed, device).score[0]


def tune(make_policy, grid: dict, cfg, iface, world_ids, run_seed, device) -> tuple[dict, float]:
    """Exhaustive grid search on tuning worlds; returns (best parameters, their mean score)."""
    keys = sorted(grid)
    best, best_score = None, -np.inf
    for values in itertools.product(*(grid[k] for k in keys)):
        params = dict(zip(keys, values))
        s = float(score_policy(cfg, iface, make_policy(**params), world_ids, run_seed, device).mean())
        if s > best_score:
            best, best_score = params, s
    return best, best_score


def tune_batched(make_policy, grid: dict, cfg, iface, world_ids, run_seed, device) -> tuple[dict, float]:
    """`tune`, with every grid point run as one strain of a single batched world: the same maps,
    the same winner and score, in one rollout instead of one per point. Policies take their
    parameters as [strains, 1] tensors and broadcast them."""
    keys = sorted(grid)
    combos = list(itertools.product(*(grid[k] for k in keys)))
    n = len(combos)
    params = {k: torch.tensor([c[i] for c in combos], dtype=torch.float32, device=device).view(n, 1)
              for i, k in enumerate(keys)}
    brain = ScriptedBrain(iface, 302, make_policy(**params), cfg.world.forward_gain,
                          cfg.world.turn_gain, n_strains=n, device=device)
    scores = rollout_brain(cfg, iface, brain, world_ids, run_seed, device).score.mean(axis=1)
    i = int(np.argmax(scores))  # first maximum: the same tie-break as the sequential search
    return dict(zip(keys, combos[i])), float(scores[i])
