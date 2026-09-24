"""Renumbering the neurons consistently everywhere must change nothing the world can see.

A cheap defence against indexing errors: any code that ties behaviour to a neuron's position
rather than its identity (an interface index resolved against the wrong ordering, a hard-coded
index, a mask built in a different order from the weights) fails this. It would NOT have caught
experiment 01's reversed synapses: a transpose applied consistently survives any relabelling.
`tests/test_direction.py` guards orientation.
"""

from __future__ import annotations

import numpy as np
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.loader import Connectome
from wormwars.evo.rollout import rollout
from wormwars.interface import load_interface


def _relabel(con, perm):
    """New index perm[i] holds old neuron i."""
    n = con.n
    names = [None] * n
    classes = [None] * n
    for i in range(n):
        names[perm[i]] = con.names[i]
        classes[perm[i]] = con.classes[i]
    chem = np.zeros_like(con.chem)
    gap = np.zeros_like(con.gap)
    chem[np.ix_(perm, perm)] = con.chem
    gap[np.ix_(perm, perm)] = con.gap
    return Connectome(tuple(names), tuple(classes), chem, gap, con.weight_kind, con.meta, con.label)


def _transport(g, spec_a, spec_b, perm):
    p = torch.as_tensor(perm)
    idx_b = {(int(i), int(j)): k for k, (i, j) in enumerate(zip(spec_b.chem_i, spec_b.chem_j))}
    gidx_b = {(int(i), int(j)): k for k, (i, j) in enumerate(zip(spec_b.gap_i, spec_b.gap_j))}
    w = torch.zeros_like(g.w)
    for k, (i, j) in enumerate(zip(spec_a.chem_i, spec_a.chem_j)):
        w[:, idx_b[(int(p[i]), int(p[j]))]] = g.w[:, k]
    gg = torch.zeros_like(g.g)
    for k, (i, j) in enumerate(zip(spec_a.gap_i, spec_a.gap_j)):
        a, b = sorted((int(p[i]), int(p[j])))
        gg[:, gidx_b[(a, b)]] = g.g[:, k]
    tau = torch.zeros_like(g.tau)
    bias = torch.zeros_like(g.bias)
    tau[:, p] = g.tau
    bias[:, p] = g.bias
    return Genome(spec_b, g.cfg, w, gg, tau, bias)


def test_relabelling_changes_neither_brain_nor_world():
    con = load_connectome()
    perm = np.random.default_rng(0).permutation(con.n)
    con_b = _relabel(con, perm)
    spec_a, spec_b = BrainSpec.from_connectome(con), BrainSpec.from_connectome(con_b)
    cfg = Config()
    cfg.world.max_ticks = 30
    g_a = Genome.random(spec_a, cfg.brain, 2, generator=torch.Generator().manual_seed(4))
    g_b = _transport(g_a, spec_a, spec_b, perm)

    v = torch.randn(2, 3, con.n, generator=torch.Generator().manual_seed(5)) * 0.5
    cur = torch.randn(2, 3, con.n, generator=torch.Generator().manual_seed(6)) * 0.5
    p = torch.as_tensor(perm)
    vb, cb = torch.zeros_like(v), torch.zeros_like(cur)
    vb[..., p], cb[..., p] = v, cur
    out_a = Brain(g_a).step(v, cur)
    out_b = Brain(g_b).step(vb, cb)
    torch.testing.assert_close(out_b[..., p], out_a, rtol=1e-5, atol=1e-5)

    ids = np.arange(4)
    s_a = rollout(cfg, load_interface(con), g_a, ids, 9).score
    s_b = rollout(cfg, load_interface(con_b), g_b, ids, 9).score
    np.testing.assert_allclose(s_a, s_b, rtol=0, atol=1e-3)
