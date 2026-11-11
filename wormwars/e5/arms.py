"""E5-1's arms (docs/E5/E5-1-DESIGN.md §4, §5): generation 0, the mutation masks, the host-wiring lesion, P's
initialisation and the run records' identity.

- **G-N2, G-SHr:** L1 on random backgrounds of the host, E4s-1's M construction (`embedded_population`), the module's
  mutation at 0.25x and the host's at 1x (`arm_scales(..., "M")`).
- **A0r:** G-N2's own generation-0 draw for the run, with every host-to-host chemical weight `w` and gap conductance
  `g` zeroed and pinned (factor 0); the host's biases and tau free.
- **A0:** 32 identical copies of L1 on its carrier (forward 1.0, turn 0.2; `carrier_genome`), the same pins.
- **P:** L1 on random N2 backgrounds drawn with 02's `permuted` initial magnitudes (permutation seed 4, 5 or 6) on the
  ungrafted host, then L1's designed values; the genome keeps the standard brain configuration.
- **B:** one E4s-1 validation champion (C), 32 identical copies.
- `lesioned`: every host-to-host `w` and `g` at 0; biases, tau and the module kept.
"""

from __future__ import annotations

import dataclasses
import hashlib

import numpy as np
import torch

from .. import graft as G
from ..brain import BrainSpec, Genome
from ..e04a import evolve as EV
from ..e4s import arms as A
from ..e4s import comparator as CMP
from ..evo.genomes import edge_hash
from . import plan as PL

ARMS = ("G-N2", "G-SHr", "A0r", "A0", "P", "B")
CARRIER = {"forward": 1.0, "turn": 0.2}  # E4s-0's qualified carrier, as E5-0 played it
PINNED_HOST = ("A0r", "A0")


def host_masks(ext) -> tuple[torch.Tensor, torch.Tensor]:
    """(chemical, gap) masks of the host-to-host edges, in the grafted spec's edge order."""
    spec = BrainSpec.from_connectome(ext)
    n0 = int(ext.meta["worm_neurons"])
    return ((spec.chem_i < n0) & (spec.chem_j < n0)).cpu(), ((spec.gap_i < n0) & (spec.gap_j < n0)).cpu()


def scales(ext, l1: G.Module, arm: str) -> dict:
    if arm not in ARMS and arm not in ("pilot_null", "pilot_n2"):
        raise ValueError(f"unknown arm {arm!r}")
    s = A.arm_scales(ext, l1, "M")
    if A.FACTORS["M"] != PL.MODULE_FACTOR:
        raise SystemExit("E4s-1's M factor is not E5-1's module factor")
    if arm in PINNED_HOST:
        hw, hg = host_masks(ext)
        s = {**s, "w": torch.where(hw, torch.tensor(0.0), s["w"]), "g": torch.where(hg, torch.tensor(0.0), s["g"])}
    return s


def lesioned(genome: Genome, ext) -> Genome:
    """Every host-to-host w and g at 0; biases, tau and the module kept."""
    hw, hg = host_masks(ext)
    w, g = genome.w.clone(), genome.g.clone()
    w[:, hw.to(w.device)] = 0.0
    g[:, hg.to(g.device)] = 0.0
    return genome.with_params(w=w, g=g)


def permuted_config(bcfg, k: int):
    """02's N2permK initialisation (`exp02.grid.brain_config_for_graph`): permuted chemical and gap magnitudes."""
    return dataclasses.replace(bcfg, init_chem_magnitude="permuted", init_gap_magnitude="permuted",
                               init_permutation_seed=int(k))


def initial(arm: str, run_seed: int, graph, ext, l1: G.Module, bcfg, population: int, *, perm_seed: int | None = None,
            champion: Genome | None = None, n2_graph=None) -> Genome:
    """Generation 0 of one run (`population` strains) on the grafted host `ext` of `graph`."""
    if arm in ("G-N2", "G-SHr", "pilot_null", "pilot_n2"):
        return CMP.embedded_population(graph, ext, l1, bcfg, run_seed=run_seed, population=population)
    if arm == "A0r":
        if graph.label != "N2":
            raise ValueError("A0r is G-N2's draws")
        return lesioned(CMP.embedded_population(graph, ext, l1, bcfg, run_seed=run_seed, population=population), ext)
    if arm == "A0":
        return CMP.carrier_genome(ext, l1, bcfg, n_strains=population, **CARRIER)
    if arm == "P":
        if graph.label != "N2" or perm_seed is None:
            raise ValueError("P is N2 with a permutation seed")
        base = EV.initial_population(BrainSpec.from_connectome(graph), permuted_config(bcfg, perm_seed), run_seed,
                                     population, "cpu")
        return G.seeded_genome(ext, l1, bcfg, base=base)
    if arm == "B":
        if champion is None or champion.n_strains != 1:
            raise ValueError("B starts from one champion")
        return champion.select([0] * population)
    raise ValueError(f"unknown arm {arm!r}")


def host_magnitude_sha256(genome: Genome, ext) -> str:
    """sha256 of the first strain's host |w| and g (float32), for P's record."""
    hw, hg = host_masks(ext)
    h = hashlib.sha256()
    h.update(genome.w[0, hw.to(genome.device)].abs().cpu().numpy().astype(np.float32).tobytes())
    h.update(genome.g[0, hg.to(genome.device)].cpu().numpy().astype(np.float32).tobytes())
    return h.hexdigest()


def identity(arm: str, run: int, run_seed: int, graph_name: str, ext) -> dict:
    """What every run record carries: arm, run, seed, graph name and hashes (§9)."""
    spec = BrainSpec.from_connectome(ext)
    return {"arm": arm, "run": int(run), "run_seed": int(run_seed), "graph": graph_name, "label": ext.label,
            "edge_sha256": edge_hash(spec), "n": spec.n, "n_chem": spec.n_chem, "n_gap": spec.n_gap}
