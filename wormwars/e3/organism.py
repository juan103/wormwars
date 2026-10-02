"""E3a's organisms (experiments/E3-ab-organism/E3a/PREREGISTRATION.md §4).

- `engineered`: E, two renamed copies of E4s-0's L1 (A's noses read `a_left`/`a_right`, B's read
  `b_left`/`b_right`), the relays E3_RA and E3_RB (the visit levels at gain 3), and the latch E3_Q,
  gating the comparators by saturation: their biases at −1.914, q → A's comparators +2, → B's −2.
- `no_latch`, `one_module`: the controls, each a stated change to E's values on E's mask. They keep
  E's name and mask and are not registered: the guard rebuilds their edge order from E's entry.
- `b_shared`: one L1 whose two nose pairs are gated (the nose biases at −1.914, q → A's noses +2,
  → B's −2), with the same relays and latch.
- `l1_switch`: one L1 whose noses read the current goal's scent.

Every module is registered in `graft.MODULES` so the publication guard can rebuild its genomes.
"""

from __future__ import annotations

import math

from .. import graft as G

GATE_BIAS = -1.914
GATE_WEIGHT = 2.0
LEVEL_GAIN = 3.0
COMPARATORS = ("E3_A_CL", "E3_A_CR", "E3_B_CL", "E3_B_CR")
RELAYS = ("E3_RA", "E3_RB")
Q = "E3_Q"


def _fixed_point(w: float = 2.0, b: float = 0.0) -> float:
    """The positive stable root of −q + w tanh q + b, by bisection."""
    lo, hi = 1e-6, abs(w) + abs(b) + 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if -mid + w * math.tanh(mid) + b > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


Q_STAR = _fixed_point()


def _register(m: G.Module) -> G.Module:
    G.MODULES[m.name] = m
    return m


def module_copy(l1: G.Module, prefix: str, scent: str, *, comparator_bias: float = 0.0) -> G.Module:
    """L1 renamed E4S_* → E3_<prefix>_*, its noses reading `<scent>_left`/`<scent>_right`."""
    ren = lambda n: n.replace("E4S_", f"E3_{prefix}_")  # noqa: E731
    neurons = tuple(ren(n) for n in l1.neurons)
    synapses = tuple((ren(a), ren(b), float(w)) for a, b, w in l1.synapses)
    tau = {ren(n): float(v) for n, v in l1.tau.items()}
    bias = {ren(n): float(v) for n, v in l1.bias.items()}
    for side in ("CL", "CR"):
        bias[f"E3_{prefix}_{side}"] = comparator_bias
    sides = {"food_left": f"{scent}_left", "food_right": f"{scent}_right"}
    noses = {ren(n): (sides[G.nose_entry(l1, n)[0]], G.nose_entry(l1, n)[1]) for n in l1.noses}
    return G.Module(f"l1-{prefix}", neurons, synapses, tau, bias, noses, 1.0, l1.neuron_class)


def _selector(targets_a, targets_b, w_a: float = GATE_WEIGHT, w_b: float = -GATE_WEIGHT) -> G.Module:
    syn = [(Q, Q, 2.0), ("E3_RA", Q, -LEVEL_GAIN), ("E3_RB", Q, LEVEL_GAIN)]
    syn += [(Q, n, w_a) for n in targets_a] + [(Q, n, w_b) for n in targets_b]
    return G.Module("e3-selector", ("E3_RA", "E3_RB", Q), tuple(syn), tau={"E3_RA": 0.5, "E3_RB": 0.5, Q: 1.0},
                    bias={"E3_RA": 0.0, "E3_RB": 0.0, Q: 0.0},
                    noses={"E3_RA": ("at_a", LEVEL_GAIN), "E3_RB": ("at_b", LEVEL_GAIN)})


def _organism(l1: G.Module, name: str, *, bias_a: float, bias_b: float, gate_a: float, gate_b: float,
              b_outputs: bool = True, register: bool = False) -> G.Module:
    a = module_copy(l1, "A", "a", comparator_bias=bias_a)
    b = module_copy(l1, "B", "b", comparator_bias=bias_b)
    if not b_outputs:
        mods = set(b.neurons)
        b = G.Module(b.name, b.neurons, tuple((x, y, 0.0 if (x in mods and y not in mods) else w) for x, y, w in b.synapses),
                     b.tau, b.bias, b.noses, b.nose_gain, b.neuron_class)
    sel = _selector(("E3_A_CL", "E3_A_CR"), ("E3_B_CL", "E3_B_CR"), gate_a, gate_b)
    m = G.combine(name, a, b, sel)
    return _register(m) if register else m


def engineered(l1: G.Module) -> G.Module:
    return _organism(l1, "e3-organism-E", bias_a=GATE_BIAS, bias_b=GATE_BIAS, gate_a=GATE_WEIGHT, gate_b=-GATE_WEIGHT,
                     register=True)


def no_latch(l1: G.Module) -> G.Module:
    """Both modules always on: the comparator biases and the gate edges at 0, on E's mask."""
    return _organism(l1, "e3-organism-E", bias_a=0.0, bias_b=0.0, gate_a=0.0, gate_b=0.0)


def one_module(l1: G.Module) -> G.Module:
    """L1-A alone and always on: B's 16 output edges at 0, A's comparator biases and gate edges at 0."""
    return _organism(l1, "e3-organism-E", bias_a=0.0, bias_b=GATE_BIAS, gate_a=0.0, gate_b=-GATE_WEIGHT,
                     b_outputs=False)


def b_shared(l1: G.Module) -> G.Module:
    """One L1 with two nose pairs, A's and B's, gated by saturating the noses."""
    out = [(a, b, float(w)) for a, b, w in l1.synapses if a in ("E4S_CL", "E4S_CR")]
    out = [(a.replace("E4S_", "E3_S_"), b, w) for a, b, w in out]
    noses = ("E3_S_AL", "E3_S_AR", "E3_S_BL", "E3_S_BR")
    syn = []
    for left, right in (("E3_S_AL", "E3_S_AR"), ("E3_S_BL", "E3_S_BR")):
        syn += [(left, "E3_S_CL", 3.0), (left, "E3_S_CR", -3.0), (right, "E3_S_CR", 3.0), (right, "E3_S_CL", -3.0)]
    pair = G.Module("b-shared-pair", noses + ("E3_S_CL", "E3_S_CR"), tuple(syn + out),
                    tau={n: 0.5 for n in noses + ("E3_S_CL", "E3_S_CR")},
                    bias={**{n: GATE_BIAS for n in noses}, "E3_S_CL": 0.0, "E3_S_CR": 0.0},
                    noses={"E3_S_AL": ("a_left", 1.0), "E3_S_AR": ("a_right", 1.0),
                           "E3_S_BL": ("b_left", 1.0), "E3_S_BR": ("b_right", 1.0)})
    sel = _selector(("E3_S_AL", "E3_S_AR"), ("E3_S_BL", "E3_S_BR"))
    return _register(G.combine("e3-b-shared", pair, sel))


def l1_switch(l1: G.Module) -> G.Module:
    """L1 on the carrier, its noses fed the current goal's scent."""
    sides = {"food_left": "goal_left", "food_right": "goal_right"}
    noses = {n: (sides[G.nose_entry(l1, n)[0]], G.nose_entry(l1, n)[1]) for n in l1.noses}
    return _register(G.Module("e3-l1-switch", l1.neurons, l1.synapses, dict(l1.tau), dict(l1.bias), noses,
                              1.0, l1.neuron_class))


def carrier_only() -> G.Module:
    """The carrier with no graft: the blind circle (forward 1.0, turn 0.2)."""
    return _register(G.Module("e3-carrier", (), ()))
