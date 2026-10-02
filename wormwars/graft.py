"""Grafting extra neurons onto a connectome (E4s; docs/E4s/DESIGN.md).

A `Module` is a small hand-designed circuit: named neurons appended after the connectome's own, its
synapses (among its neurons, and from them onto named worm neurons, or from worm neurons onto
them), their initial weights, each neuron's time constant and bias, and its noses: module neurons
that receive a scent signal through the interface.

- `graft_connectome` returns an extended `Connectome`. The worm's neurons keep their indices, and
  their chemical and gap masks are copied unchanged; the module's synapses are new chemical edges
  with an anatomical weight of 1. A module may not rewrite an existing worm-to-worm edge.
- `seeded_genome` builds a genome on the extended connectome. The worm part comes from a background
  genome on the original connectome (for example 02's random initialisation or a champion), placed
  edge by edge; with no background it is silent (all weights, conductances and biases 0, τ = 1). The
  module part takes its designed values.
- `graft_interface` is the worm's interface plus the noses' entries. Its `probe` gives the
  module-only probes: "mean" feeds each nose the average of the two sides, "swapped" feeds each nose
  the other side. They act on the module alone; the world's own probes act on every consumer.
  `probe_on` limits a probe to some signals, so one pair of noses can be probed alone (E3a).
- A nose reads any declared signal: a plain name takes the module's `nose_gain`, and a
  `(signal, gain)` pair its own gain (E3a's relays read the visit levels at gain 3).
- `combine` merges several modules into one graft; synapses may run between them (E3a's selector).

The brain and world code take the neuron count from the connectome, so nothing else changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch

from .brain import BrainSpec, Genome
from .connectome.loader import Connectome
from .interface import Interface, interface_from_spec, load_interface_spec

PROBES = ("real", "mean", "swapped")

# Every module whose genomes may be saved, by name, so the publication guard can rebuild a grafted
# genome's edge order from its label ("<graph>+<module>") and check its worm block (rule 1).
MODULES: dict = {}


@dataclass(frozen=True)
class Module:
    name: str
    neurons: tuple[str, ...]
    synapses: tuple[tuple[str, str, float], ...]  # (pre, post, initial weight)
    tau: dict = field(default_factory=dict)  # neuron -> τ (default 1.0)
    bias: dict = field(default_factory=dict)  # neuron -> bias (default 0.0)
    noses: dict = field(default_factory=dict)  # module neuron -> signal, or (signal, gain)
    nose_gain: float = 1.0
    neuron_class: str = "inter"

    def without_outputs(self, worm_names) -> "Module":
        """The inert variant: every synapse onto a worm neuron removed."""
        worm = set(worm_names)
        return Module(f"{self.name}-inert", self.neurons,
                      tuple(s for s in self.synapses if s[1] not in worm),
                      dict(self.tau), dict(self.bias), dict(self.noses), self.nose_gain, self.neuron_class)


# Left/right partners for the module-only probes; a signal without one (a level) is never probed.
PAIRS = {"food_left": "food_right", "a_left": "a_right", "b_left": "b_right", "goal_left": "goal_right"}
PAIRS.update({v: k for k, v in list(PAIRS.items())})


def nose_entry(module: Module, nose: str) -> tuple[str, float]:
    """(signal, gain) for one nose: a plain signal name takes the module's `nose_gain`."""
    entry = module.noses[nose]
    if isinstance(entry, str):
        return entry, float(module.nose_gain)
    signal, gain = entry
    return str(signal), float(gain)


def combine(name: str, *modules: Module, neuron_class: str = "inter") -> Module:
    """One module from several, in order. Neuron names must be distinct; every nose keeps its own
    gain, so modules with different `nose_gain`s combine exactly."""
    neurons, synapses, tau, bias, noses = [], [], {}, {}, {}
    for m in modules:
        if set(m.neurons) & set(neurons):
            raise ValueError(f"module {m.name} reuses neuron names: {sorted(set(m.neurons) & set(neurons))}")
        neurons += list(m.neurons)
        synapses += list(m.synapses)
        tau.update(m.tau)
        bias.update(m.bias)
        noses.update({n: nose_entry(m, n) for n in m.noses})
    return Module(name, tuple(neurons), tuple(synapses), tau, bias, noses, 1.0, neuron_class)


def graft_connectome(con: Connectome, module: Module) -> Connectome:
    n0, k = con.n, len(module.neurons)
    if set(module.neurons) & set(con.names):
        raise ValueError("module neurons must have new names")
    names = tuple(con.names) + tuple(module.neurons)
    classes = tuple(con.classes) + (module.neuron_class,) * k
    chem = np.zeros((n0 + k, n0 + k), dtype=np.float32)
    gap = np.zeros_like(chem)
    chem[:n0, :n0] = con.chem
    gap[:n0, :n0] = con.gap
    ext = Connectome(names, classes, chem, gap, con.weight_kind,
                     {**con.meta, "graft": module.name, "worm_neurons": n0}, f"{con.label}+{module.name}")
    for pre, post, _ in module.synapses:
        i, j = ext.index(pre), ext.index(post)
        if i < n0 and j < n0:
            raise ValueError(f"a module may not rewrite the worm's own wiring ({pre} -> {post})")
        chem[i, j] = 1.0
    return ext


def _edge_positions(spec: BrainSpec, kind: str) -> dict:
    ii, jj = (spec.chem_i, spec.chem_j) if kind == "chem" else (spec.gap_i, spec.gap_j)
    return {(int(a), int(b)): p for p, (a, b) in enumerate(zip(ii.tolist(), jj.tolist()))}


def seeded_genome(ext: Connectome, module: Module, bcfg, base: Genome | None = None, n_strains: int | None = None,
                  device="cpu") -> Genome:
    """Genomes on `ext`: the background's parameters (or a silent background), then the module's.

    Dale's law is refused: the designed weights are signed in `w`, and a presynaptic sign would
    override them."""
    if bcfg.dale or (base is not None and base.dale_sign is not None):
        raise ValueError("grafts assume Dale's law is off (the designed weights carry their own signs)")
    spec = BrainSpec.from_connectome(ext)
    n0 = int(ext.meta["worm_neurons"])
    S = base.n_strains if base is not None else int(n_strains or 1)
    w = torch.zeros(S, spec.n_chem)
    g = torch.zeros(S, spec.n_gap)
    tau = torch.ones(S, spec.n)
    bias = torch.zeros(S, spec.n)
    if base is not None:
        if base.spec.n != n0:
            raise ValueError("the background genome must be on the original connectome")
        base = base.select(list(range(S)))  # a CPU-independent copy
        pc, pg = _edge_positions(spec, "chem"), _edge_positions(spec, "gap")
        bc = [pc[(int(a), int(b))] for a, b in zip(base.spec.chem_i.tolist(), base.spec.chem_j.tolist())]
        bg = [pg[(int(a), int(b))] for a, b in zip(base.spec.gap_i.tolist(), base.spec.gap_j.tolist())]
        w[:, bc] = base.w.cpu()
        g[:, bg] = base.g.cpu()
        tau[:, :n0] = base.tau.cpu()
        bias[:, :n0] = base.bias.cpu()
    pc = _edge_positions(spec, "chem")
    for pre, post, weight in module.synapses:
        w[:, pc[(ext.index(pre), ext.index(post))]] = float(weight)
    for name in module.neurons:
        tau[:, ext.index(name)] = float(module.tau.get(name, 1.0))
        bias[:, ext.index(name)] = float(module.bias.get(name, 0.0))
    # built through `with_params` from a template (the T0 guard against hand-built genomes)
    template = base if base is not None else Genome.random(spec, bcfg, 1, generator=torch.Generator().manual_seed(0))
    genome = template.with_params(spec=spec, cfg=bcfg, w=w, g=g, tau=tau, bias=bias, dale_sign=None)
    genome.clamp_()
    if device != "cpu":
        from .e04a.evolve import moved
        genome = moved(genome, device)
    return genome


def graft_interface(ext: Connectome, module: Module, probe: str = "real", path=None, probe_on=None) -> Interface:
    """The worm's interface, with the noses' entries appended (after the worm's own, so every existing
    entry keeps its position). `probe_on`, if given, is the set of signals the probe acts on."""
    if probe not in PROBES:
        raise ValueError(f"probe must be one of {PROBES}")
    spec = load_interface_spec(path)
    sensors = list(spec["sensors"])
    for nose in module.noses:
        signal, gain = nose_entry(module, nose)
        probed = probe != "real" and signal in PAIRS and (probe_on is None or signal in probe_on)
        if not probed:
            sensors.append({"signal": signal, "neurons": [nose], "gain": gain})
        elif probe == "swapped":
            sensors.append({"signal": PAIRS[signal], "neurons": [nose], "gain": gain})
        else:  # the mean of the two sides, the left side first
            left, right = sorted((signal, PAIRS[signal]), key=lambda s: not s.endswith("_left"))
            sensors.append({"signal": left, "neurons": [nose], "gain": gain / 2})
            sensors.append({"signal": right, "neurons": [nose], "gain": gain / 2})
    return interface_from_spec(ext, {**spec, "sensors": sensors})


def worm_parameters(ext: Connectome, w, g):
    """The worm-to-worm part of a grafted genome's chemical and gap parameters ([..., edges]), in the
    original connectome's edge order (edges are enumerated row-major, so the worm's keep their order)."""
    spec = BrainSpec.from_connectome(ext)
    n0 = int(ext.meta["worm_neurons"])
    chem = ((spec.chem_i < n0) & (spec.chem_j < n0)).cpu().numpy()
    gap = ((spec.gap_i < n0) & (spec.gap_j < n0)).cpu().numpy()
    return np.asarray(w)[..., chem], np.asarray(g)[..., gap]
