"""03h's scripted gate families (experiments/03h-history-use/DESIGN.md §4), beside 02's (`wormwars/exp02/scripted.py`).

Both take MemoryKinesis's speed rule (slow above `threshold`, fast below) and turn by `fall_turn` instead of `turn` when
the level is judged to have fallen. Parameters may be [strains, 1] tensors, for `tune_batched`."""

from __future__ import annotations

import torch


class BitKinesis:
    """Memoryless, reading food_fell: falling is the bit. Under relief it is exactly MemoryKinesis with
    fall_threshold 0 (the bit is the fall of the same injected current, 0 on the first tick)."""

    needs_fell = True

    def __init__(self, slow, fast, threshold, turn, fall_turn):
        self.slow, self.fast, self.threshold, self.turn, self.fall_turn = slow, fast, threshold, turn, fall_turn

    def init(self, s, b):
        return None

    def __call__(self, left, right, state, fell):
        level = (left + right) / 2
        one = torch.ones_like(level)
        fwd = torch.where(level > self.threshold, self.slow * one, self.fast * one)
        turn = torch.where(fell, self.fall_turn * one, self.turn * one)
        return fwd, turn, state


class SlowMemoryKinesis:
    """KTS's memory mechanism (`wormwars/e03a/probe.py`) in MemoryKinesis's policy (Astra, round 3): falling when the
    level is below the previous tick's average m_{t-1} - `fall_threshold`, then m_t = m_{t-1} + (x_t - m_{t-1}) / T.
    At T = 1 the average stores the level itself, so the policy is exactly MemoryKinesis. `use_memory` and `use_bit`
    (1 or 0) switch the two sources of "falling"; with both on, either suffices."""

    needs_fell = True

    def __init__(self, slow, fast, threshold, turn, fall_turn, fall_threshold, T, use_memory, use_bit):
        self.slow, self.fast, self.threshold, self.turn = slow, fast, threshold, turn
        self.fall_turn, self.fall_threshold, self.T = fall_turn, fall_threshold, T
        self.use_memory, self.use_bit = use_memory, use_bit

    def init(self, s, b):
        return None

    def __call__(self, left, right, state, fell):
        level = (left + right) / 2
        one = torch.ones_like(level)
        fwd = torch.where(level > self.threshold, self.slow * one, self.fast * one)
        if state is None:
            by_memory = torch.zeros_like(level, dtype=torch.bool)
            m = level.clone()
        else:
            by_memory = level < state - self.fall_threshold
            T = torch.as_tensor(self.T, dtype=level.dtype, device=level.device)
            m = torch.where(T == 1, level, state + (level - state) / T)
        falling = (by_memory & (torch.as_tensor(self.use_memory, device=level.device) > 0.5)) | (
            fell & (torch.as_tensor(self.use_bit, device=level.device) > 0.5))
        turn = torch.where(falling, self.fall_turn * one, self.turn * one)
        return fwd, turn, m
