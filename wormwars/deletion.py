"""Deleting neurons: no term involving the neuron remains in any other neuron's update.

This is not silencing. `Brain.silence` clamps a neuron at 0, but its gap-junction partners keep
their conductance to it, so it still pulls them toward 0 (D044). Deletion removes every chemical
edge into and out of the neuron, every gap junction touching it, and its bias. The neuron keeps
its index, so interface indices are unchanged, and it becomes an isolated unit whose state
affects nothing. Do not delete a mapped motor neuron: the read-out would still read it.
"""

from __future__ import annotations

import numpy as np
import torch

from .brain import Genome
from .connectome.loader import Connectome


def delete_neurons(genome: Genome, per_strain: list[list[int]]) -> Genome:
    """A copy of `genome` where strain s has the neurons in `per_strain[s]` deleted: the weights
    of every chemical edge and gap junction touching them, and their biases, set to zero. The
    mask is unchanged, so many different deletions of one genome run in one batch."""
    if len(per_strain) != genome.n_strains:
        raise ValueError(f"{len(per_strain)} deletion lists for {genome.n_strains} strains")
    spec = genome.spec
    w, g, bias = genome.w.clone(), genome.g.clone(), genome.bias.clone()
    for s, ks in enumerate(per_strain):
        if not ks:
            continue
        k = torch.as_tensor(list(ks), device=genome.device)
        w[s, torch.isin(spec.chem_i, k) | torch.isin(spec.chem_j, k)] = 0.0
        g[s, torch.isin(spec.gap_i, k) | torch.isin(spec.gap_j, k)] = 0.0
        bias[s, k] = 0.0
    return Genome(spec, genome.cfg, w, g, genome.tau.clone(), bias,
                  None if genome.dale_sign is None else genome.dale_sign.clone())


def without_neuron(con: Connectome, k: int, label: str | None = None) -> Connectome:
    """The same neurons and indexing, with every edge touching neuron k removed. A brain built
    on it can never grow those edges back, which the NIP arm of 03a needs for evolution."""
    chem, gap = con.chem.copy(), con.gap.copy()
    chem[k, :] = chem[:, k] = 0
    gap[k, :] = gap[:, k] = 0
    return con.with_masks(chem, gap, label or f"{con.label}-without-{con.names[k]}")


def reindexed_without(con: Connectome, k: int) -> tuple[Connectome, np.ndarray]:
    """A network in which neuron k never existed: n - 1 neurons, re-indexed. Returns it and the
    original indices of the kept neurons, in order. Used to test deletion."""
    keep = np.array([i for i in range(con.n) if i != k])
    sub = np.ix_(keep, keep)
    return (Connectome(tuple(con.names[i] for i in keep), tuple(con.classes[i] for i in keep),
                       con.chem[sub].copy(), con.gap[sub].copy(), con.weight_kind, con.meta,
                       f"{con.label}-reindexed-without-{con.names[k]}"), keep)
