"""E4's training pieces (docs/E4/E4-DESIGN.md v3 §1): the output gate applied in training rollouts and in
evaluation, and the arms' pairing (X0 and X+ draw the same noise for every shared parameter)."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import Genome
from wormwars.config import MutationConfig
from wormwars.connectome import load_connectome
from wormwars.e3 import maze_runs as MR
from wormwars.e3 import maze_world as MW
from wormwars.e4 import arms as AR
from wormwars.e4 import train as TR
from wormwars.e4s import arms as A
from wormwars.evo.rollout import rollout

IDS = np.array([42_000, 42_001])
TICKS = 240


@pytest.fixture(scope="module")
def setup():
    cfg = MW.maze_config(c=6, horizon=1800, colony=8, mu=0.01, lam=0.02, delta=0.05, d0=1.142, access="shared",
                         family="islands", k_r=0)
    cx = AR.context(load_connectome(), A.load_l1(), cfg.brain)
    return cfg, cx


def _pair(cx):
    """Two strains: E-G, and E-G with large motor drive from the B comparators (which the gate silences in mode A)."""
    org = cx["org"]
    g = org.genome.select([0])
    w = g.w.clone()
    spec = g.spec
    for pre, post in AR.O.motor_edges(org.module, "B"):
        k = int(((spec.chem_i == org.ext.index(pre)) & (spec.chem_j == org.ext.index(post))).nonzero()[0, 0])
        w[0, k] = 3.0
    return Genome.cat([g, g.with_params(w=w)])


def test_training_rollouts_are_gated(setup):
    cfg, cx = setup
    org = cx["org"]
    pop = _pair(cx)
    fn = TR.gated_rollout(org.gate)
    gated = fn(cfg, org.iface, pop, IDS, 1_192_000, "cpu", chunk_worlds=4, ticks=TICKS)
    plain = rollout(cfg, org.iface, pop, IDS, 1_192_000, "cpu", chunk_worlds=4, ticks=TICKS)
    hooked = rollout(cfg, org.iface, pop, IDS, 1_192_000, "cpu", chunk_worlds=4, ticks=TICKS,
                     brain_hook=lambda b, lo, hi: b.gate_outputs(org.gate))
    assert np.array_equal(gated.score, hooked.score) and np.array_equal(gated.progress, hooked.progress)
    assert not (np.array_equal(gated.score, plain.score) and np.array_equal(gated.progress, plain.progress))


def test_evaluation_brains_are_gated(setup):
    cfg, cx = setup
    org = cx["org"]
    pop = _pair(cx)
    b = TR.gated_brain(pop, org.gate, "cpu")
    assert b.output_gate is not None
    ev = MR.play_batch(cfg, org.iface, b, np.arange(2), IDS, 1_192_000, "cpu", access="shared", ticks=TICKS)
    tr = TR.gated_rollout(org.gate)(cfg, org.iface, pop, IDS, 1_192_000, "cpu", chunk_worlds=4, ticks=TICKS)
    assert np.allclose(np.asarray(ev["visits"]).reshape(2, len(IDS), -1).mean(-1), tr.score)


def test_the_arms_draw_the_same_noise_on_shared_parameters(setup):
    _, cx = setup
    g = Genome.cat([cx["org"].genome.select([0])] * 4)
    mcfg = MutationConfig()
    s0, s1 = AR.scales(cx, "x0"), AR.scales(cx, "x_plus", cross_factor=0.5)
    m0 = g.clone().mutate(mcfg, torch.Generator().manual_seed(7), scales=s0)
    m1 = g.clone().mutate(mcfg, torch.Generator().manual_seed(7), scales=s1)
    slots = AR.slot_indices(cx)
    keep = torch.ones(g.w.shape[1], dtype=torch.bool)
    keep[slots] = False
    assert torch.equal(m0.w[:, keep], m1.w[:, keep]) and torch.equal(m0.bias, m1.bias) and torch.equal(m0.tau, m1.tau)
    assert torch.all(m0.w[:, slots] == 0) and torch.any(m1.w[:, slots] != 0)
