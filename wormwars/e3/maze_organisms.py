"""E3b's candidate organisms on the maze (docs/E3/E3b-0-PLAN.md §2a, §2c).

- **The seeds:** E, E3a's engineered organism on the silent carrier (forward 1.0, turn 0.2), and S3r3,
  E3a's Stage 3 run 3 champion. S3r3 is rebuilt from its committed record (`champions-3.json`: every
  grafted edge, τ and bias by name; Stage 3 left the worm block at the carrier's) on E's carrier genome,
  and refused unless its sha256 equals the record's.
- **The maze-ready additions,** grafted beside the seed's modules and frozen for every arm:
  - W1, a symmetric wall reflex: E3B_WL and E3B_WR read the front collision sensors (wall-only in the
    maze) at gain 1, with bias −0.5 and τ 0.5, and drive the 4 dorsal and 4 ventral turn neurons away
    from their side at ±3;
  - W2, a one-sided reflex: W1 with E3B_WR's outputs at ±1.5, and a resting turn of +0.4;
  - M, an oscillator: E3B_M1 and E3B_M2, self-weights 1.5, M1 → M2 +1, M2 → M1 −1, bias 0, τ 4 (M40) or
    8 (M80); M1 drives the dorsal turn neurons at +0.5 and the ventral at −0.5.
- **The resting turn** is set through the carrier's turn biases. A reflex neuron rests at tanh(−0.5) =
  −0.46, not 0: in W1 the two sides cancel, but in W2 they leave a net push on the turn neurons, which
  would saturate the turn. The carrier's turn bias is therefore set so that the resting turn command is
  the declared one: 0.2 for W0, W1 and their M variants, and 0.4 for W2's (D176).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import torch

from .. import graft as G
from ..brain import Brain, BrainSpec, Genome
from ..connectome import load_connectome
from ..e4s import comparator as C
from ..evo.genomes import genome_hash
from . import organism as O

VARIANTS = ("W0", "W1", "W1+M40", "W1+M80", "W2", "W2+M40", "W2+M80")
REFLEX_BIAS, REFLEX_TAU, REFLEX_W, W2_RIGHT_W = -0.5, 0.5, 3.0, 1.5
M_SELF, M_CROSS, M_OUT = 1.5, 1.0, 0.5
M_START = 0.1  # M1's initial state: at rest M sits at its unstable fixed point 0 for ever (Astra, D179)
M_TAU = {"M40": 4.0, "M80": 8.0}
CARRIER_FORWARD = 1.0
REST_TURN = {"W0": 0.2, "W1": 0.2, "W2": 0.4}

ROOT = Path(__file__).resolve().parents[2]
CHAMPIONS_3 = ROOT / "experiments" / "E3-ab-organism" / "E3a" / "champions-3.json"
S3R3_RUN = 3
S3R3_SHA256 = "57414a22cd778830cd2d3a3da2a9b112d26e8a46fc6451edab30861718435452"


@dataclass(frozen=True)
class Seed:
    name: str
    module: G.Module
    ext: object  # the seed's grafted connectome
    genome: Genome


@dataclass(frozen=True)
class Organism:
    name: str
    module: G.Module
    ext: object
    iface: object
    genome: Genome


class StartedBrain(Brain):
    """A Brain whose initial state sets the given neurons, the same on every row: the organism's own start."""

    def __init__(self, genome: Genome, start: dict):
        super().__init__(genome)
        self.start = dict(start)

    def initial_state(self, n_weys: int):
        v = super().initial_state(n_weys)
        for k, x in self.start.items():
            v[..., k] = x
        return v


def brain(org: "Organism", device="cpu") -> StartedBrain:
    """The organism's brain on `device`, with M1 started at M_START when the variant has M."""
    from ..e04a.evolve import moved
    g = org.genome if str(device) == "cpu" else moved(org.genome, device)
    start = {org.ext.index("E3B_M1"): M_START} if "E3B_M1" in org.ext.names else {}
    return StartedBrain(g, start)


def _register(m: G.Module) -> G.Module:
    G.MODULES[m.name] = m
    return m


def reflex(right_weight: float = REFLEX_W) -> G.Module:
    syn = []
    for side, w in (("E3B_WL", -REFLEX_W), ("E3B_WR", float(right_weight))):
        syn += [(side, d, w) for d in C.TURN_DORSAL] + [(side, v, -w) for v in C.TURN_VENTRAL]
    return G.Module("e3b-reflex", ("E3B_WL", "E3B_WR"), tuple(syn),
                    tau={"E3B_WL": REFLEX_TAU, "E3B_WR": REFLEX_TAU},
                    bias={"E3B_WL": REFLEX_BIAS, "E3B_WR": REFLEX_BIAS},
                    noses={"E3B_WL": ("collision_front_left", 1.0), "E3B_WR": ("collision_front_right", 1.0)})


def oscillator(tau: float) -> G.Module:
    syn = [("E3B_M1", "E3B_M1", M_SELF), ("E3B_M2", "E3B_M2", M_SELF),
           ("E3B_M1", "E3B_M2", M_CROSS), ("E3B_M2", "E3B_M1", -M_CROSS)]
    syn += [("E3B_M1", d, M_OUT) for d in C.TURN_DORSAL] + [("E3B_M1", v, -M_OUT) for v in C.TURN_VENTRAL]
    return G.Module("e3b-oscillator", ("E3B_M1", "E3B_M2"), tuple(syn), tau={"E3B_M1": tau, "E3B_M2": tau},
                    bias={"E3B_M1": 0.0, "E3B_M2": 0.0})


def additions(variant: str) -> list:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}")
    base, _, osc = variant.partition("+")
    out = []
    if base == "W1":
        out.append(reflex(REFLEX_W))
    elif base == "W2":
        out.append(reflex(W2_RIGHT_W))
    if osc:
        out.append(oscillator(M_TAU[osc]))
    return out


def resting_reflex_push(variant: str) -> float:
    """The reflex neurons' net resting input to each dorsal turn neuron (the ventral get its negative)."""
    base = variant.partition("+")[0]
    if base == "W0":
        return 0.0
    r0 = math.tanh(REFLEX_BIAS)
    right = REFLEX_W if base == "W1" else W2_RIGHT_W
    return -REFLEX_W * r0 + right * r0


def carrier_turn(variant: str) -> float:
    """The carrier's turn command (`carrier_genome`'s `turn`, 2 tanh(b)) whose bias b, added to the
    reflex's resting push, gives the variant's declared resting turn."""
    rest = REST_TURN[variant.partition("+")[0]]
    return 2 * math.tanh(math.atanh(rest / 2) - resting_reflex_push(variant))


def named_edges(genome: Genome, ext, strain: int = 0) -> dict:
    """{(pre, post): weight} for every chemical edge with a grafted end."""
    spec = BrainSpec.from_connectome(ext)
    n0 = int(ext.meta["worm_neurons"])
    return {(ext.names[i], ext.names[j]): float(genome.w[strain, p])
            for p, (i, j) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist())) if i >= n0 or j >= n0}


def _set_grafted(genome: Genome, ext, edges: dict, neurons: dict) -> Genome:
    """A copy of `genome` with the named grafted edges' weights and neurons' τ and bias set."""
    spec = BrainSpec.from_connectome(ext)
    pos = {(ext.names[i], ext.names[j]): p for p, (i, j) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist()))}
    w, tau, bias = genome.w.clone(), genome.tau.clone(), genome.bias.clone()
    for key, val in edges.items():
        w[:, pos[key]] = float(val)
    for name, (t, b) in neurons.items():
        tau[:, ext.index(name)] = float(t)
        bias[:, ext.index(name)] = float(b)
    return genome.with_params(w=w, tau=tau, bias=bias)


def seed(name: str, l1: G.Module, bcfg, con=None, record: Path = CHAMPIONS_3) -> Seed:
    """E, or S3r3 rebuilt from E3a's champion record and checked against its sha256."""
    con = con if con is not None else load_connectome()
    module = O.engineered(l1)
    ext = G.graft_connectome(con, module)
    genome = C.carrier_genome(ext, module, bcfg, forward=CARRIER_FORWARD, turn=REST_TURN["W0"])
    if name == "E":
        return Seed("E", module, ext, genome)
    if name != "S3r3":
        raise ValueError("the seeds are E and S3r3")
    rec = json.loads(Path(record).read_text(encoding="utf-8"))
    entry = next(c for c in rec["stage3"]["champions"] if c["run"] == S3R3_RUN)
    gr = entry["grafted"]
    edges = {tuple(k.split("->")): v[0] for k, v in gr["edges"].items()}
    neurons = {n: (d["tau"][0], d["bias"][0]) for n, d in gr["neurons"].items()}
    genome = _set_grafted(genome, ext, edges, neurons)
    got = genome_hash(genome, 0)
    if got != entry["sha256"] or got != S3R3_SHA256:
        raise ValueError(f"S3r3 rebuilt from its record hashes to {got}, not {entry['sha256']}")
    return Seed("S3r3", module, ext, genome)


def maze_module(seed_module: G.Module, variant: str) -> G.Module:
    adds = additions(variant)
    if not adds:
        return seed_module
    return _register(G.combine(f"e3b-{seed_module.name}-{variant}", seed_module, *adds))


def maze_organism(con, sd: Seed, variant: str, bcfg) -> Organism:
    """The seed with the variant's additions: the carrier at the variant's resting turn, the additions'
    designed values, and every grafted value of the seed copied by name."""
    module = maze_module(sd.module, variant)
    ext = G.graft_connectome(con, module) if module is not sd.module else sd.ext
    genome = C.carrier_genome(ext, module, bcfg, forward=CARRIER_FORWARD, turn=carrier_turn(variant))
    n0 = int(sd.ext.meta["worm_neurons"])
    neurons = {sd.ext.names[k]: (float(sd.genome.tau[0, k]), float(sd.genome.bias[0, k])) for k in range(n0, sd.ext.n)}
    genome = _set_grafted(genome, ext, named_edges(sd.genome, sd.ext), neurons)
    return Organism(f"{sd.name}+{variant}", module, ext, G.graft_interface(ext, module), genome)
