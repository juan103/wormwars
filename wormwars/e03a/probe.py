"""The bounded-history replay probe and its scripted calibrators (experiments/03a-self-consistency/DESIGN.md v7.1 §8).

**The probe.** After the action of every tick t that is a multiple of L, and before sensing at t + 1, the controller's
state is rebuilt: started from its canonical initial state and replayed through the inputs it received at ticks
t − L + 1 to t; the episode then continues. `ReplayBrain` wraps any controller the world accepts (a `Brain`, whose
state is its voltage tensor started at zeros, or a `ScriptedBrain`, whose state is its policy's) and does this inside
`step`: at tick t + 1 it first rebuilds, then steps on the current input. The replayed inputs are the ones this
(perturbed) trajectory actually received, and the replay uses the controller's own `step`, so the integration settings
are the same. Before the first reset nothing changes, and the first reset changes nothing (its window is the whole
history), so the first action that can differ is at 2L + 1. The body's position and heading are untouched.

`window=None` replays the whole episode so far at every reset: the implementation control, which must reproduce the
unperturbed episode bitwise on the CPU (and on CUDA within one batch composition).

**The calibrators** (D303, D304's families, here as library code): KT, memoryless; KTM, one tick of memory (KT with a
turn whenever the level fell since the previous tick); KTS with time constant T, KT with a turn whenever the level is
below its exponential average over T ticks. Under the probe KT and KTM must be unaffected (KTM's memory, one tick, is
shorter than every L); KTS's stored average changes when L is short against T.
"""

from __future__ import annotations

import torch

COLLISION_THRESHOLD = 0.5023  # the D303 families' "near a wall" level (development-records/memoryless_check.py)


class ReplayBrain:
    """`inner` with its state rebuilt every `L` ticks. `window="L"` (the probe) replays the last L inputs;
    `window=None` (the full-replay control) replays every input so far."""

    def __init__(self, inner, L: int, window="L"):
        if int(L) < 1:
            raise ValueError("L must be at least 1")
        self.inner, self.L = inner, int(L)
        self.window = self.L if window == "L" else None if window is None else int(window)
        self.history: list = []
        self.t = 0  # ticks stepped so far
        self.resets = 0

    def __getattr__(self, name):  # n, n_strains, device, ... from the controller
        return getattr(self.__dict__["inner"], name)

    def initial_state(self, n_weys: int):
        self.history, self.t, self.resets = [], 0, 0
        return self.inner.initial_state(n_weys)

    def rebuild(self, v):
        """The state rebuilt from the canonical initial state through the kept inputs."""
        keep = self.history if self.window is None else self.history[-self.window:]
        v = self.inner.initial_state(v.shape[1])
        for cur in keep:
            v = self.inner.step(v, cur)
        return v

    def step(self, v, current):
        if self.t > 0 and self.t % self.L == 0:
            v = self.rebuild(v)
            self.resets += 1
        out = self.inner.step(v, current)
        self.history.append(current.clone())
        if self.window is not None and len(self.history) > self.window:
            self.history.pop(0)
        self.t += 1
        return out


class KT:
    """Speed and turn by level against one threshold, and collision avoidance (D303's memoryless family). With
    `fall_turn` set it is KTM: a turn by fall_turn whenever the level is below the previous tick's."""

    needs_collision = True

    def __init__(self, threshold, slow, fast, turn_hi, turn_lo, avoid, fall_turn=None):
        self.t, self.slow, self.fast, self.th, self.tl = threshold, slow, fast, turn_hi, turn_lo
        self.avoid, self.ft = avoid, fall_turn

    def init(self, s, b):
        return None

    def _base(self, level, collision):
        one = torch.ones_like(level)
        hi = level > self.t
        fwd = torch.where(hi, self.slow * one, self.fast * one)
        turn = torch.where(hi, self.th * one, self.tl * one)
        return one, fwd, turn

    def _avoid(self, turn, one, collision):
        near = torch.maximum(collision["front"],
                             torch.maximum(collision["front_left"], collision["front_right"])) > COLLISION_THRESHOLD
        return torch.where(near & (torch.as_tensor(self.avoid) > 0), one, turn)

    def __call__(self, left, right, state, collision=None):
        level = (left + right) / 2
        one, fwd, turn = self._base(level, collision)
        if self.ft is not None and state is not None:
            turn = torch.where(level < state, self.ft * one, turn)
        turn = self._avoid(turn, one, collision)
        return fwd, turn, level.clone()


class KTS(KT):
    """KT plus a slow memory: a turn by fall_turn when the level is below its exponential average with time constant T
    ticks (T = 1: the previous tick's level, so KTS(T=1) is KTM)."""

    def __init__(self, T, **kw):
        super().__init__(**kw)
        self.T = T

    def __call__(self, left, right, state, collision=None):
        level = (left + right) / 2
        one, fwd, turn = self._base(level, collision)
        avg = level.clone() if state is None else state
        turn = torch.where(level < avg, self.ft * one, turn)
        turn = self._avoid(turn, one, collision)
        return fwd, turn, avg + (level - avg) / self.T
