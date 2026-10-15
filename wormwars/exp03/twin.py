"""03mc's history probe: 03's matched-input history test (`measures.history`) with the rising and falling
histories as two rows of each strain (experiments/03mc-p4-confirm/DESIGN.md §5).

The rows share the strain's matrices and never interact, so the dynamics are 03's. The brain step reads its
dense matrices once per substep for all rows, so the second row costs almost nothing: on the RTX 5080, 6.6 s
for 2 048 genomes against 13.0 s for 03's one-row probe (D285). The numbers are not bitwise 03's (a different
batch shape); the declared tolerance is a relative 1e-5 on P4's terms.

One run also gives what 03m needed separate runs for: the history followed for `follow` ticks of the final
input (03m's decay), the turn read-out's state before the tanh (saturation), and the settling ranges."""

from __future__ import annotations

import numpy as np
import torch

from ..brain import Brain, Genome
from .measures import _current, _readout


class _Range:
    """The largest range over a window's ticks, per strain (max minus min per unit, then the largest unit
    over rows and neurons): an oscillation that returns to its start still shows (03m's settling rule)."""

    def __init__(self):
        self.lo = self.hi = None

    def add(self, x: torch.Tensor) -> None:
        self.lo = x.clone() if self.lo is None else torch.minimum(self.lo, x)
        self.hi = x.clone() if self.hi is None else torch.maximum(self.hi, x)

    def value(self) -> np.ndarray:
        r = self.hi - self.lo
        return r.reshape(r.shape[0], -1).amax(dim=1).cpu().numpy()


def history(genome: Genome, cfg, iface, bank: dict, rising_start=0.25, falling_start=1.75, warm=100, span=10,
            follow=5, every=10, extra=(5,), window=10) -> dict:
    """Per genome: the raw turn's rising-minus-falling difference at the ramp's end ("final") and `extra[0]`
    ticks later ("after", 03's 5), and the falling-minus-rising steady contrast after `warm` ticks of the two
    start levels: 03's terms. Also the same terms on the turn neurons' state before the tanh ("pre_turn"); the
    signed difference at ticks 0, `extra` and every `every` up to `follow` ("diff" [ticks, genomes]); the
    settling ranges of the full state over the last `window` ticks of the holds and of the follow; and the
    turn read-out neurons' mean tanh slope at the holds' end and the ramp's end."""
    brain = Brain(genome)
    s, n, dev = genome.n_strains, genome.spec.n, genome.device
    food = (bank["food_left"] + bank["food_right"]) / 2
    starts = (rising_start * food, falling_start * food)

    def at(levels):
        return torch.cat([_current(iface, cfg, dict(bank, food_left=lv, food_right=lv), n, s, dev) for lv in levels], 1)

    plus, minus = list(iface.turn_plus), list(iface.turn_minus)
    turn_idx = plus + minus

    def pre(v):  # [S, 2]: the turn read-out before the tanh
        return v[..., plus].mean(-1) - v[..., minus].mean(-1)

    def raw(v):  # [S, 2]: 03's raw turn, row by row
        return torch.stack([_readout(iface, cfg, v[:, r:r + 1])[:, 1] for r in range(v.shape[1])], 1)

    def slope(v):  # [S]
        return (1 - torch.tanh(v[..., turn_idx]) ** 2).mean(dim=(1, 2))

    ticks = sorted({0, *[t for t in extra if t <= follow], *range(every, follow + 1, every)})
    v = brain.initial_state(2)
    hold = _Range()
    cur = at(starts)
    for t in range(1, warm + 1):
        v = brain.step(v, cur)
        if t > warm - window:
            hold.add(v)
    steady_raw, steady_pre, slope_hold = raw(v), pre(v), slope(v)
    for t in range(span):
        v = brain.step(v, at([a + (food - a) * (t + 1) / span for a in starts]))
    slope_ramp = slope(v)
    final_raw, final_pre = raw(v), pre(v)
    rows = {0: final_raw[:, 0] - final_raw[:, 1]}
    end = _Range()
    cur = at([food, food])
    for t in range(1, follow + 1):
        v = brain.step(v, cur)
        if t in ticks:
            r = raw(v)
            rows[t] = r[:, 0] - r[:, 1]
        if t > follow - window:
            end.add(v)
    np_ = lambda x: x.cpu().numpy()  # noqa: E731
    after = extra[0] if extra and extra[0] <= follow else None
    return {
        "raw_turn": {"final": np_(final_raw[:, 0] - final_raw[:, 1]),
                     "after": np_(rows[after]) if after is not None else None,
                     "steady_contrast": np_(steady_raw[:, 1] - steady_raw[:, 0])},
        "pre_turn": {"final": np_(final_pre[:, 0] - final_pre[:, 1]),
                     "steady_contrast": np_(steady_pre[:, 1] - steady_pre[:, 0])},
        "ticks": ticks, "diff": np.stack([np_(rows[t]) for t in ticks]),
        "hold_state_range": hold.value(), "end_state_range": end.value() if follow >= window else None,
        "slope_hold": np_(slope_hold), "slope_ramp": np_(slope_ramp)}
