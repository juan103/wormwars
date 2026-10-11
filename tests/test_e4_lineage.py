"""E4's champion lineages (docs/E4/E4-DESIGN.md v3 §1, the scale rule): the selection results captured through the
rollout wrapper, `breed` replayed with each run's own generator, and the mutations along a strain's lineage."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import Genome
from wormwars.connectome import load_connectome
from wormwars.e04a import evolve as EV
from wormwars.e3 import maze_world as MW
from wormwars.e4 import arms as AR
from wormwars.e4 import lineage as LI
from wormwars.e4 import train as TR
from wormwars.e4s import arms as A


@pytest.fixture(scope="module")
def evolved():
    cfg = MW.maze_config(c=6, horizon=40, colony=8, mu=0.01, lam=0.02, delta=0.05, d0=1.142, access="shared",
                         family="islands", k_r=0)
    cfg.evo.population, cfg.evo.elites, cfg.evo.truncation, cfg.evo.worlds_per_strain = 6, 2, 3, 1
    cx = AR.context(load_connectome(), A.load_l1(), cfg.brain)
    org = cx["org"]
    sc = AR.scales(cx, "x_plus", cross_factor=0.5)
    start = Genome.cat([org.genome.select([0])] * cfg.evo.population)
    runs = [EV.RunSpec(0, 1_400_000, 0.0), EV.RunSpec(1, 1_400_001, 0.0)]
    cap = LI.Capture(TR.gated_rollout(org.gate))
    recs = EV.evolve_batch(cfg, org.iface, org.genome.spec, runs, generations=4, checkpoint_every=10 ** 6,
                           validation_ids=np.array([42_000]), world_seed=1_400_000, id_base=50_000_000,
                           id_span=1_000_000, device="cpu", rollout_fn=cap, initial=lambda r: start,
                           mutation_scales=lambda r: sc)
    return cfg, runs, start, sc, cap, recs


def test_the_capture_keeps_one_selection_per_generation(evolved):
    cfg, runs, start, sc, cap, recs = evolved
    assert len(cap.selections) == 4
    assert all(s["score"].shape == (len(runs) * cfg.evo.population, 1) for s in cap.selections)


def test_the_replay_reproduces_the_final_populations(evolved):
    cfg, runs, start, sc, cap, recs = evolved
    rep = LI.replay(cfg, runs, cap.selections, initial=lambda r: start, mutation_scales=lambda r: sc, device="cpu")
    for i, rec in enumerate(recs):
        for k in ("w", "bias", "tau", "g"):
            assert torch.equal(getattr(rep[i]["final"], k), getattr(rec.final, k))


def test_mutations_along_a_lineage(evolved):
    cfg, runs, start, sc, cap, recs = evolved
    rep = LI.replay(cfg, runs, cap.selections, initial=lambda r: start, mutation_scales=lambda r: sc, device="cpu")
    for r in rep:
        for k in range(cfg.evo.population):
            n = LI.mutations(r["parents"], k)
            assert 0 <= n <= 3


def test_mutations_count_children_not_elites():
    """`parents[g]` maps generation g + 1's strains to generation g's: `source` the index, `child` whether mutated."""
    parents = [{"source": [1, 0, 0, 1], "child": [False, False, True, True]},
               {"source": [0, 1, 2, 3], "child": [False, False, True, True]},
               {"source": [2, 0, 1, 2], "child": [False, False, True, True]}]
    assert LI.mutations(parents, 3) == 3  # 3 <- child of 2 <- child of 2 <- child of 0
    assert LI.mutations(parents, 0) == 2  # 0 <- elite copy of 2 <- child of 2 <- child of 0
    assert LI.mutations(parents, 1) == 0  # 1 <- elite copy of 0 <- elite copy of 0 <- elite copy of 1


def test_the_recovered_parents_are_the_real_ones(evolved):
    """With every mutation scale at 0 and a diverse start, each final strain equals the start strain its recorded
    lineage leads to, bitwise; a wrong parent would land on a different start strain."""
    cfg, runs, start, sc, cap, recs = evolved
    org_g = start.select([0])
    bias = start.bias.clone() + torch.arange(start.n_strains, dtype=start.bias.dtype)[:, None] * 1e-3
    diverse = start.with_params(bias=bias)
    zero = {k: torch.zeros_like(v) for k, v in sc.items()}
    rep = LI.replay(cfg, runs, cap.selections, initial=lambda r: diverse, mutation_scales=lambda r: zero, device="cpu")
    for r in rep:
        for k in range(cfg.evo.population):
            j = k
            for p in reversed(r["parents"]):
                j = p["source"][j]
            assert torch.equal(r["final"].bias[k], diverse.bias[j])
    assert org_g.n_strains == 1
