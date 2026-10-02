"""E3a's samplers and mutation masks (experiments/E3-ab-organism/E3a/PREREGISTRATION.md §7).

The selector's 13 parameters, in `SELECTOR` order:
τ_q, w_qq, b_q, w_aq (RA → Q), w_bq (RB → Q), the four gate edges (Q → each comparator) and the four
comparator biases.

- `ga_draw`: Stage 2's start. Per module, one gate weight U[−0.5, 0.5] and one bias N(0, 0.5²) clipped
  to ±2, each given to both comparators; w_qq, w_aq, w_bq U[−0.5, 0.5]; b_q N(0, 0.5²) clipped;
  τ_q log-uniform over [0.5, 20].
- `rs_draw`: random sampling's, the same tie, with the weights U[−3, 3] and the biases U[−2, 2].
- `b_task_module`, `b_task_draw`: B-task's mask (all 121 edges among the 11 neurons, 32 output edges)
  and its draw, with the full within-pair blocks (§7).
- `stage2_scales`, `stage3_scales`, `b_task_scales`: the mutation factors ("w", "g", "tau", "bias").

The draws' order inside each function is part of the definition: a seed reproduces a draw exactly.
"""

from __future__ import annotations

import math

import numpy as np
import torch

from .. import graft as G
from ..brain import BrainSpec, Genome
from ..e4s import comparator as C
from . import organism as O

SELECTOR = ("tau_q", "w_qq", "b_q", "w_aq", "w_bq", "gate_A_CL", "gate_A_CR", "gate_B_CL", "gate_B_CR",
            "bias_A_CL", "bias_A_CR", "bias_B_CL", "bias_B_CR")
SELECTOR_INDEX = {k: i for i, k in enumerate(SELECTOR)}
_EDGES = {"w_qq": (O.Q, O.Q), "w_aq": ("E3_RA", O.Q), "w_bq": ("E3_RB", O.Q),
          "gate_A_CL": (O.Q, "E3_A_CL"), "gate_A_CR": (O.Q, "E3_A_CR"),
          "gate_B_CL": (O.Q, "E3_B_CL"), "gate_B_CR": (O.Q, "E3_B_CR")}
_BIASES = {"b_q": O.Q, "bias_A_CL": "E3_A_CL", "bias_A_CR": "E3_A_CR", "bias_B_CL": "E3_B_CL", "bias_B_CR": "E3_B_CR"}
TAU_MIN, TAU_MAX = 0.5, 20.0


def _log_uniform(rng, n):
    return np.exp(rng.uniform(math.log(TAU_MIN), math.log(TAU_MAX), n))


def _tied_draw(rng, n, weight, bias) -> np.ndarray:
    """One gate weight and one bias per module, given to both comparators; then the latch's own."""
    p = np.zeros((n, len(SELECTOR)))
    i = SELECTOR_INDEX
    for mod in ("A", "B"):
        g = weight(n)
        p[:, i[f"gate_{mod}_CL"]] = p[:, i[f"gate_{mod}_CR"]] = g
    for mod in ("A", "B"):
        b = bias(n)
        p[:, i[f"bias_{mod}_CL"]] = p[:, i[f"bias_{mod}_CR"]] = b
    for k in ("w_qq", "w_aq", "w_bq"):
        p[:, i[k]] = weight(n)
    p[:, i["b_q"]] = bias(n)
    p[:, i["tau_q"]] = _log_uniform(rng, n)
    return p


def ga_draw(rng: np.random.Generator, n: int) -> np.ndarray:
    return _tied_draw(rng, n, lambda k: rng.uniform(-0.5, 0.5, k), lambda k: np.clip(rng.normal(0.0, 0.5, k), -2.0, 2.0))


def rs_draw(rng: np.random.Generator, n: int) -> np.ndarray:
    return _tied_draw(rng, n, lambda k: rng.uniform(-3.0, 3.0, k), lambda k: rng.uniform(-2.0, 2.0, k))


def _positions(ext):
    spec = BrainSpec.from_connectome(ext)
    pos = {(int(a), int(b)): p for p, (a, b) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist()))}
    return spec, pos


def with_selector(base: Genome, ext, params: np.ndarray) -> Genome:
    """`base`'s first strain, repeated once per row of `params` [n, 13], with the selector set."""
    params = np.asarray(params, dtype=np.float64)
    n = params.shape[0]
    _, pos = _positions(ext)
    one = base.select([0])
    w, tau, bias = one.w.repeat(n, 1).clone(), one.tau.repeat(n, 1).clone(), one.bias.repeat(n, 1).clone()
    g = one.g.repeat(n, 1).clone()
    for k, (a, b) in _EDGES.items():
        w[:, pos[(ext.index(a), ext.index(b))]] = torch.as_tensor(params[:, SELECTOR_INDEX[k]], dtype=w.dtype)
    for k, name in _BIASES.items():
        bias[:, ext.index(name)] = torch.as_tensor(params[:, SELECTOR_INDEX[k]], dtype=bias.dtype)
    tau[:, ext.index(O.Q)] = torch.as_tensor(params[:, SELECTOR_INDEX["tau_q"]], dtype=tau.dtype)
    out = one.with_params(w=w, g=g, tau=tau, bias=bias)
    out.clamp_()
    return out


def read_selector(genome: Genome, ext) -> np.ndarray:
    _, pos = _positions(ext)
    out = np.zeros((genome.n_strains, len(SELECTOR)))
    for k, (a, b) in _EDGES.items():
        out[:, SELECTOR_INDEX[k]] = genome.w[:, pos[(ext.index(a), ext.index(b))]].cpu().double().numpy()
    for k, name in _BIASES.items():
        out[:, SELECTOR_INDEX[k]] = genome.bias[:, ext.index(name)].cpu().double().numpy()
    out[:, SELECTOR_INDEX["tau_q"]] = genome.tau[:, ext.index(O.Q)].cpu().double().numpy()
    return out


def selector_masks(ext) -> dict:
    spec, pos = _positions(ext)
    w = torch.zeros(spec.n_chem, dtype=torch.bool)
    tau = torch.zeros(spec.n, dtype=torch.bool)
    bias = torch.zeros(spec.n, dtype=torch.bool)
    for a, b in _EDGES.values():
        w[pos[(ext.index(a), ext.index(b))]] = True
    for name in _BIASES.values():
        bias[ext.index(name)] = True
    tau[ext.index(O.Q)] = True
    return {"w": w, "tau": tau, "bias": bias}


def _scales(spec, w_mask, node_tau, node_bias, factor):
    f = lambda m: torch.where(m, torch.tensor(float(factor)), torch.tensor(0.0)).float()  # noqa: E731
    return {"w": f(w_mask), "g": torch.zeros(spec.n_gap), "tau": f(node_tau), "bias": f(node_bias)}


def stage2_scales(ext) -> dict:
    spec, _ = _positions(ext)
    m = selector_masks(ext)
    return _scales(spec, m["w"], m["tau"], m["bias"], 1.0)


def _grafted(ext):
    spec, _ = _positions(ext)
    n0 = int(ext.meta["worm_neurons"])
    edges = (spec.chem_i >= n0) | (spec.chem_j >= n0)
    nodes = torch.arange(spec.n) >= n0
    for r in O.RELAYS:
        nodes[ext.index(r)] = False
    return spec, edges, nodes


def stage3_scales(ext) -> dict:
    spec, edges, nodes = _grafted(ext)
    return _scales(spec, edges, nodes, nodes, 0.25)


def b_task_scales(ext) -> dict:
    spec, edges, nodes = _grafted(ext)
    return _scales(spec, edges, nodes, nodes, 1.0)


# ------------------------------------------------------------------ B-task

NEURONS = ("E3_A_NL", "E3_A_NR", "E3_A_CL", "E3_A_CR", "E3_B_NL", "E3_B_NR", "E3_B_CL", "E3_B_CR", "E3_RA", "E3_RB", O.Q)


def b_task_module(l1: G.Module) -> G.Module:
    """E's 11 neurons, routing and output positions, with every edge among them (121) and every
    comparator-to-turn-neuron edge (32) in the mask, at weight 0 until drawn."""
    turn = C.TURN_DORSAL + C.TURN_VENTRAL
    syn = [(a, b, 0.0) for a in NEURONS for b in NEURONS]
    syn += [(c, t, 0.0) for c in ("E3_A_CL", "E3_A_CR", "E3_B_CL", "E3_B_CR") for t in turn]
    noses = {"E3_A_NL": ("a_left", 1.0), "E3_A_NR": ("a_right", 1.0), "E3_B_NL": ("b_left", 1.0),
             "E3_B_NR": ("b_right", 1.0), "E3_RA": ("at_a", O.LEVEL_GAIN), "E3_RB": ("at_b", O.LEVEL_GAIN)}
    m = G.Module("e3-b-task", NEURONS, tuple(syn), tau={"E3_RA": 0.5, "E3_RB": 0.5}, bias={"E3_RA": 0.0, "E3_RB": 0.0},
                 noses=noses, nose_gain=1.0, neuron_class=l1.neuron_class)
    G.MODULES[m.name] = m
    return m


def b_task_draw(rng: np.random.Generator, ext, module: G.Module, bcfg, n: int) -> Genome:
    """n B-task genomes on the carrier (PREREGISTRATION §7, "B-task's draws")."""
    base = C.carrier_genome(ext, module, bcfg, forward=1.0, turn=0.2, n_strains=n)
    _, pos = _positions(ext)
    idx = ext.index
    w, tau, bias = base.w.clone(), base.tau.clone(), base.bias.clone()

    def setw(a, b, vals):
        w[:, pos[(idx(a), idx(b))]] = torch.as_tensor(vals, dtype=w.dtype)

    def getw(a, b):
        return w[:, pos[(idx(a), idx(b))]].clone()

    # every grafted edge first, U[-0.5, 0.5], in the module's synapse order
    for a, b, _ in module.synapses:
        setw(a, b, rng.uniform(-0.5, 0.5, n))
    pairs = {}
    for mod in ("A", "B"):
        pairs[f"N{mod}"] = (f"E3_{mod}_NL", f"E3_{mod}_NR")
        pairs[f"C{mod}"] = (f"E3_{mod}_CL", f"E3_{mod}_CR")
    # each pair: one τ and one bias
    for key in ("NA", "CA", "NB", "CB"):
        left, right = pairs[key]
        t = torch.as_tensor(_log_uniform(rng, n), dtype=tau.dtype)
        b = torch.as_tensor(np.clip(rng.normal(0.0, 0.5, n), -2.0, 2.0), dtype=bias.dtype)
        tau[:, idx(left)] = tau[:, idx(right)] = t
        bias[:, idx(left)] = bias[:, idx(right)] = b
    tau[:, idx(O.Q)] = torch.as_tensor(_log_uniform(rng, n), dtype=tau.dtype)
    bias[:, idx(O.Q)] = torch.as_tensor(np.clip(rng.normal(0.0, 0.5, n), -2.0, 2.0), dtype=bias.dtype)
    # the within-pair blocks: inputs from outside the pair equal; self and mutual edges symmetric
    for key in ("NA", "CA", "NB", "CB"):
        left, right = pairs[key]
        for j in NEURONS:
            if j not in (left, right):
                setw(j, right, getw(j, left))
        setw(right, right, getw(left, left))
        setw(right, left, getw(left, right))
    # each comparator pair's own noses, in L1's pattern with one magnitude
    for mod in ("A", "B"):
        nl, nr = pairs[f"N{mod}"]
        cl, cr = pairs[f"C{mod}"]
        a = torch.as_tensor(rng.uniform(-0.5, 0.5, n), dtype=w.dtype)
        setw(nl, cl, a); setw(nl, cr, -a); setw(nr, cr, a); setw(nr, cl, -a)  # noqa: E702
    # each comparator pair's outputs: one value per turn neuron, opposite signs
    for mod in ("A", "B"):
        cl, cr = pairs[f"C{mod}"]
        for t in C.TURN_DORSAL + C.TURN_VENTRAL:
            v = torch.as_tensor(rng.uniform(-0.5, 0.5, n), dtype=w.dtype)
            setw(cl, t, v); setw(cr, t, -v)  # noqa: E702
    out = base.with_params(w=w, tau=tau, bias=bias)
    out.clamp_()
    return out
