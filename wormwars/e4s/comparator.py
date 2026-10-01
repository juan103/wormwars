"""E4s-0's building blocks (docs/E4s/E4s-0-PLAN.md): the comparator ladder, the carrier, the residual
stereo term, and generation-0 populations drawn on N2 and embedded.

- `comparator(step, ...)` builds a `graft.Module`. Noses NL and NR take `food_left` and `food_right`
  at the interface's gain 1. Each comparator pair (CL, CR) subtracts them (NL excites CL and inhibits
  CR; NR the reverse) and drives the turn neurons push-pull. CL excites the dorsal ones and inhibits
  the ventral ones, so a stronger left nose gives a left turn. L2 adds self-excitation, L3 mutual
  inhibition between the pair, L4 P parallel pairs on the same noses. A pair with w_s + |w_m| >= 1
  is bistable (a latch, not an amplifier) and is refused.
- `carrier_genome` silences the worm and gives it a declared forward and turn command through biases:
  forward = 2 tanh(b_f) on AVB/PVC, turn = 2 tanh(b_t) with +b_t dorsal and -b_t ventral.
- `residual_turn(k)` adds k (L - R) to the world's turn command before its clamp, for the residual
  sweep. It patches `World._read_motors` for the duration of a `with` block; at k = 0 the read-out is
  the world's own, operation for operation.
"""

from __future__ import annotations

import contextlib
import math

import torch

from .. import graft as G
from ..brain import BrainSpec
from ..e04a import evolve as EV
from ..world import World

TURN_DORSAL = ("SMDDL", "SMDDR", "RMDDL", "RMDDR")
TURN_VENTRAL = ("SMDVL", "SMDVR", "RMDVL", "RMDVR")
FORWARD = ("AVBL", "AVBR", "PVCL", "PVCR")
STEPS = ("L1", "L2", "L3", "L4")
NOSE_TAU = 0.5


def comparator(step: str, *, w_n: float, w_o: float, tau: float, bias: float, w_s: float = 0.0,
               w_m: float = 0.0, pairs: int = 1) -> G.Module:
    if step not in STEPS:
        raise ValueError(f"step must be one of {STEPS}")
    if (step == "L1" and (w_s or w_m)) or (step == "L2" and w_m) or (step == "L3" and w_s):
        raise ValueError(f"{step} takes {'no' if step == 'L1' else 'only its own'} recurrent parameter")
    if step != "L4" and pairs != 1:
        raise ValueError("only L4 has parallel pairs")
    if w_s < 0 or w_m > 0 or w_s + abs(w_m) >= 1:
        raise ValueError("the comparator must stay monostable: 0 <= w_s, w_m <= 0, w_s + |w_m| < 1")
    names = [("E4S_CL", "E4S_CR")] if pairs == 1 else [(f"E4S_CL_{p}", f"E4S_CR_{p}") for p in range(pairs)]
    syn = []
    for cl, cr in names:
        syn += [("E4S_NL", cl, w_n), ("E4S_NL", cr, -w_n), ("E4S_NR", cr, w_n), ("E4S_NR", cl, -w_n)]
        syn += [(cl, d, w_o) for d in TURN_DORSAL] + [(cl, v, -w_o) for v in TURN_VENTRAL]
        syn += [(cr, d, -w_o) for d in TURN_DORSAL] + [(cr, v, w_o) for v in TURN_VENTRAL]
        if w_s:
            syn += [(cl, cl, w_s), (cr, cr, w_s)]
        if w_m:
            syn += [(cl, cr, w_m), (cr, cl, w_m)]
    comps = [n for pair in names for n in pair]
    tag = f"{step}" + (f"x{pairs}" if pairs > 1 else "")
    return G.Module(name=f"comparator-{tag}", neurons=("E4S_NL", "E4S_NR", *comps), synapses=tuple(syn),
                    tau={"E4S_NL": NOSE_TAU, "E4S_NR": NOSE_TAU, **{c: float(tau) for c in comps}},
                    bias={c: float(bias) for c in comps},
                    noses={"E4S_NL": "food_left", "E4S_NR": "food_right"}, nose_gain=1.0)


def carrier_genome(ext, module: G.Module, bcfg, *, forward: float, turn: float, n_strains: int = 1):
    """The module on a silent worm, with the carrier's declared forward and turn commands."""
    if not (0 <= forward < 2 and -2 < turn < 2):
        raise ValueError("commands of 2 or more are out of reach of 2 tanh(b)")
    gen = G.seeded_genome(ext, module, bcfg, n_strains=n_strains)
    bias = gen.bias.clone()
    b_f, b_t = math.atanh(forward / 2), math.atanh(turn / 2)
    for name in FORWARD:
        bias[:, ext.index(name)] = b_f
    for name in TURN_DORSAL:
        bias[:, ext.index(name)] = b_t
    for name in TURN_VENTRAL:
        bias[:, ext.index(name)] = -b_t
    return gen.with_params(bias=bias)


def motor_commands(v, iface, cfg):
    """The world's forward and turn commands for a brain state `v` [..., N] (`World._read_motors`)."""
    act = torch.tanh(v)
    idx = lambda xs: torch.as_tensor(list(xs), dtype=torch.long)  # noqa: E731
    fwd = act[..., idx(iface.forward_plus)].mean(-1) - act[..., idx(iface.forward_minus)].mean(-1)
    turn = act[..., idx(iface.turn_plus)].mean(-1) - act[..., idx(iface.turn_minus)].mean(-1)
    w = cfg.world
    return (fwd * 0.5 * w.forward_gain).clamp(-1, 1), (turn * 0.5 * w.turn_gain).clamp(-1, 1)


@contextlib.contextmanager
def residual_turn(k: float):
    """Inside the block, every world's turn command is clamp(own + k (L - R)), L and R being the same
    tick's `food_left` and `food_right` signals. Not thread-safe; for exploratory scripts only."""
    original = World._read_motors
    k = float(k)

    def read(self, v_world):
        act = torch.tanh(v_world)
        fwd = act[..., self._m_fwd_p].mean(-1) - act[..., self._m_fwd_m].mean(-1)
        turn = act[..., self._m_turn_p].mean(-1) - act[..., self._m_turn_m].mean(-1)
        pump = torch.sigmoid(self.iface.pump_gain * act[..., self._m_pump].mean(-1))
        wcfg = self.cfg.world
        turn = turn * 0.5 * wcfg.turn_gain
        if k != 0.0:
            s = self.last_signals
            turn = turn + k * (s["food_left"] - s["food_right"])
        return (fwd * 0.5 * wcfg.forward_gain).clamp(-1, 1), turn.clamp(-1, 1), pump

    World._read_motors = read
    try:
        yield
    finally:
        World._read_motors = original


def embedded_population(con, ext, module: G.Module, bcfg, *, run_seed: int, population: int):
    """04a's generation-0 draw on N2's own spec, embedded in the grafted connectome with the module."""
    base = EV.initial_population(BrainSpec.from_connectome(con), bcfg, run_seed, population, "cpu")
    return G.seeded_genome(ext, module, bcfg, base=base)
