"""E4s-1's arms (experiments/E4s-stereo-module/E4s-1/PREREGISTRATION.md, D150).

- `load_l1`: the frozen module from E4s-0's `module.json`, checked against its bound sha256 (LF line
  endings) and registered in `graft.MODULES`, so the publication guard can check grafted genomes.
- `arm_scales`: each arm's mutation factors. Host parameters at 1; the module's (its neurons' tau and
  bias, every edge with a module neuron at either end) at the arm's factor; N's output edges at 0.
- `r_signs` and `with_signs`: R's draw, edge k's weight s_k x 3.0 in the module's synapse order.
- `without_output`: N's construction, the 16 output edges kept in the mask at weight 0.
- `mc_genome`: a genome's module transplanted onto the carrier (its own biases on the turn neurons).
- `module_replaced`: the module's parameters set to a given module's (reset to the run's own
  generation 0, or the L1 rescue).

R's and N's modules keep L1's name, so every arm's grafted connectome has the same mask and label.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import torch

from .. import graft as G
from ..brain import BrainSpec
from . import comparator as C

ROOT = Path(__file__).resolve().parents[2]
L1_PATH = ROOT / "experiments" / "E4s-stereo-module" / "E4s-0" / "module.json"
L1_SHA256 = "9613cd155a20ed2cfb891c1bd10fed16814f24a04f912a1940524f2378e877d4"
L1_NAME = "comparator-L1"
FACTORS = {"M": 0.25, "N": 0.25, "R": 0.25, "F0": 0.0, "U": 1.0, "S": 0.125, "C2": 0.25}
R_SEED_BASE = 1_165_000


def load_l1(path: Path = L1_PATH, expected_sha256: str = L1_SHA256) -> G.Module:
    text = Path(path).read_bytes().decode("utf-8").replace("\r\n", "\n")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if sha != expected_sha256:
        raise SystemExit(f"{Path(path).name} has sha256 {sha}, not the bound {expected_sha256}")
    doc = json.loads(text)
    m = G.Module(name=L1_NAME, neurons=tuple(doc["neurons"]),
                 synapses=tuple((a, b, float(w)) for a, b, w in doc["synapses"]),
                 tau={k: float(v) for k, v in doc["tau"].items()}, bias={k: float(v) for k, v in doc["bias"].items()},
                 noses=dict(doc["noses"]), nose_gain=float(doc["nose_gain"]))
    G.MODULES[L1_NAME] = m
    return m


def _masks(ext):
    spec = BrainSpec.from_connectome(ext)
    n0 = int(ext.meta["worm_neurons"])
    module_edge = (spec.chem_i >= n0) | (spec.chem_j >= n0)
    module_gap = (spec.gap_i >= n0) | (spec.gap_j >= n0)
    module_node = torch.arange(spec.n) >= n0
    return spec, n0, module_edge.cpu(), module_gap.cpu(), module_node


def output_edge_mask(ext, module: G.Module) -> torch.Tensor:
    """The module's edges onto host neurons."""
    spec, n0, _, _, _ = _masks(ext)
    return ((spec.chem_i >= n0) & (spec.chem_j < n0)).cpu()


def arm_scales(ext, module: G.Module, arm: str) -> dict:
    if arm not in FACTORS:
        raise ValueError(f"arm must be one of {sorted(FACTORS)}")
    f = float(FACTORS[arm])
    spec, n0, me, mg, mn = _masks(ext)
    w = torch.where(me, torch.tensor(f), torch.tensor(1.0))
    if arm == "N":
        w = torch.where(output_edge_mask(ext, module), torch.tensor(0.0), w)
    g = torch.where(mg, torch.tensor(f), torch.tensor(1.0))
    node = torch.where(mn, torch.tensor(f), torch.tensor(1.0))
    return {"w": w.float(), "g": g.float(), "tau": node.float().clone(), "bias": node.float().clone()}


def r_signs(i: int) -> np.ndarray:
    return np.random.default_rng(R_SEED_BASE + int(i)).choice([-1, 1], size=20)


def with_signs(module: G.Module, signs) -> G.Module:
    signs = list(np.asarray(signs).tolist())
    if len(signs) != len(module.synapses):
        raise ValueError("one sign per synapse")
    syn = tuple((a, b, float(s) * 3.0) for (a, b, _), s in zip(module.synapses, signs))
    return G.Module(module.name, module.neurons, syn, dict(module.tau), dict(module.bias), dict(module.noses),
                    module.nose_gain, module.neuron_class)


def without_output(module: G.Module) -> G.Module:
    host_targets = set(C.TURN_DORSAL + C.TURN_VENTRAL)
    syn = tuple((a, b, 0.0 if b in host_targets else w) for a, b, w in module.synapses)
    return G.Module(module.name, module.neurons, syn, dict(module.tau), dict(module.bias), dict(module.noses),
                    module.nose_gain, module.neuron_class)


def _copy_module(dst, src, ext):
    """`dst` with `src`'s module-owned parameters (the module's neurons' tau and bias, its edges)."""
    _, _, me, _, mn = _masks(ext)
    w, tau, bias = dst.w.clone(), dst.tau.clone(), dst.bias.clone()
    w[:, me] = src.w[:, me].to(w.device)
    tau[:, mn] = src.tau[:, mn].to(tau.device)
    bias[:, mn] = src.bias[:, mn].to(bias.device)
    return dst.with_params(w=w, tau=tau, bias=bias)


def mc_genome(genome, ext, module: G.Module, bcfg, *, turn: float, forward: float = 1.0):
    """The genome's module moved onto the carrier (a silent worm with the carrier's own forward and turn
    biases). `module` gives the mask; its weights are overwritten by the genome's."""
    carrier = C.carrier_genome(ext, module, bcfg, forward=forward, turn=turn, n_strains=genome.n_strains)
    return _copy_module(carrier, genome.select(list(range(genome.n_strains))), ext)


def module_replaced(genome, ext, module: G.Module, bcfg):
    """The genome with its module's parameters set to `module`'s designed values."""
    designed = G.seeded_genome(ext, module, bcfg, n_strains=genome.n_strains)
    return _copy_module(genome, designed, ext)
