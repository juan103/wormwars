"""E4's source means for P1-info (docs/E4/E4-DESIGN.md v3 §2): `Brain.substep_hook` sees every substep's
end-state; `SourceMeans` averages tanh(v) per strain over substeps, weys and mazes; `source_means` plays the
validation block and returns them."""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
import torch

from wormwars.brain import Brain
from wormwars.connectome import load_connectome
from wormwars.e3 import maze_world as MW
from wormwars.e4 import arms as AR
from wormwars.e4 import means as ME
from wormwars.e4s import arms as A


@pytest.fixture(scope="module")
def setup():
    cfg = MW.maze_config(c=6, horizon=1800, colony=8, mu=0.01, lam=0.02, delta=0.05, d0=1.142, access="shared",
                         family="islands", k_r=0)
    return cfg, AR.context(load_connectome(), A.load_l1(), cfg.brain)


@pytest.mark.parametrize("pad", [False, True])
def test_the_hook_sees_every_substep_and_the_last_is_the_result(setup, pad):
    cfg, cx = setup
    g = cx["org"].genome.select([0])
    g = g.with_params(cfg=dataclasses.replace(g.cfg, pad_single_strain=pad))
    b = Brain(g)
    seen = []
    b.substep_hook = lambda v: seen.append(v.clone())
    v = torch.randn(1, 3, g.spec.n, generator=torch.Generator().manual_seed(0))
    cur = torch.randn(1, 3, g.spec.n, generator=torch.Generator().manual_seed(1))
    out = b.step(v, cur)
    assert len(seen) == g.cfg.substeps and all(s.shape == out.shape for s in seen)
    assert torch.equal(seen[-1], out)
    plain = Brain(g).step(v, cur)
    assert torch.equal(plain, out)


def test_source_means_weights_every_substep_and_wey_equally():
    acc = ME.SourceMeans()
    acc(torch.tensor([[[0.0, 1.0], [0.0, 3.0]]]))  # [S=1, B=2, N=2], as v
    acc(torch.tensor([[[0.0, -1.0], [0.0, 2.0]]]))
    want = torch.tanh(torch.tensor([1.0, 3.0, -1.0, 2.0], dtype=torch.float64)).mean()
    m = acc.mean()
    assert m.shape == (1, 2) and float(m[0, 0]) == 0.0
    assert float(m[0, 1]) == pytest.approx(float(want))


def test_source_means_on_the_validation_play(setup):
    cfg, cx = setup
    org = cx["org"]
    from wormwars.brain import Genome
    pop = Genome.cat([org.genome.select([0])] * 2)
    m = ME.source_means(cfg, org.iface, pop, org.gate, np.array([42_000, 42_001]), 1_192_000, "cpu", ticks=120)
    assert m.shape == (2, org.ext.n) and torch.isfinite(m).all()
    assert torch.equal(m[0], m[1])
    src = [org.ext.index(n) for n in ("E3_A_NL", "E3_B_NL")]
    assert torch.all(m[:, src].abs() <= 1.0)


def _strong_b(cx):
    """E-G with strong B-motor edges, which the gate silences in mode A, so gated and ungated play differ."""
    org = cx["org"]
    g = org.genome.select([0])
    w = g.w.clone()
    spec = g.spec
    for pre, post in AR.O.motor_edges(org.module, "B"):
        k = int(((spec.chem_i == org.ext.index(pre)) & (spec.chem_j == org.ext.index(post))).nonzero()[0, 0])
        w[0, k] = 3.0
    return g.with_params(w=w)


def test_source_means_equal_an_independent_trajectory_mean(setup):
    """With one substep per tick, the substep end-states are the world's tick states: the means must equal tanh of the
    world's own state averaged over ticks, weys and mazes, read by a world recorder (another path), gated."""
    cfg, cx = setup
    org = cx["org"]
    g = _strong_b(cx)
    g1 = g.with_params(cfg=dataclasses.replace(g.cfg, substeps=1))
    ids, T = np.array([42_000, 42_001]), 80
    got = ME.source_means(cfg, org.iface, g1, org.gate, ids, 1_192_000, "cpu", ticks=T)

    class Rec:
        def __init__(self):
            self.sum, self.n = None, 0

        def attach(self, world):
            pass

        def record(self, world):
            t = torch.tanh(world.v[0].to(torch.float64)).sum(dim=1)
            self.sum = t if self.sum is None else self.sum + t
            self.n += world.v[0].shape[1]

    from wormwars.e4.train import gated_brain
    strain_of = torch.zeros(len(ids), 1, dtype=torch.long)
    w = MW.MazeWorld(cfg, org.iface, gated_brain(g1, org.gate), strain_of, run_seed=1_192_000, world_ids=ids,
                     access="shared")
    rec = Rec()
    w.recorder = rec
    w.run(T)
    want = rec.sum / rec.n
    assert torch.allclose(got, want, atol=1e-9)
    assert got.abs().sum() > 0


def test_source_means_count_every_substep_wey_and_maze(setup, monkeypatch):
    cfg, cx = setup
    org = cx["org"]
    seen = []
    orig = ME.SourceMeans.mean
    monkeypatch.setattr(ME.SourceMeans, "mean", lambda self: (seen.append(self.count), orig(self))[1])
    ME.source_means(cfg, org.iface, org.genome.select([0]), org.gate, np.array([42_000, 42_001]), 1_192_000, "cpu",
                    ticks=30)
    assert seen == [30 * org.genome.cfg.substeps * 2 * 8]


def test_source_means_are_gated(setup):
    """Sabotage of the evaluation wrapper: the same genome played ungated gives other means."""
    cfg, cx = setup
    org = cx["org"]
    g = _strong_b(cx)
    ids = np.array([42_000])
    gated = ME.source_means(cfg, org.iface, g, org.gate, ids, 1_192_000, "cpu", ticks=300)
    ungated = ME.source_means(cfg, org.iface, g, None, ids, 1_192_000, "cpu", ticks=300)
    assert not torch.allclose(gated, ungated)
