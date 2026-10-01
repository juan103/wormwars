"""E4s-0's analysis pieces (`wormwars/e4s/diagnostics.py`; docs/E4s/E4s-0-PLAN.md v2): the sweep's
classes, the generation-0 selection E4s-1 will make, module-only mutation, per-strain motor
statistics over an episode, and the settling rule for open-loop responses."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars import graft as G
from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.e1.task import task_n_config
from wormwars.connectome import load_connectome
from wormwars.e04a import evolve as EV
from wormwars.e4s import comparator as C
from wormwars.e4s import diagnostics as D
from wormwars.evo.genomes import genome_hash
from wormwars.evo.rollout import rollout

def task_n(ticks: int) -> Config:
    """A Task N-shaped config (one wey per world, a moving scent source), short."""
    return task_n_config(sigma=6.0, amplitude=1.0, radius=1.5, separation=8.0, horizon=ticks)


KS = [0, 0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 256]


@pytest.fixture(scope="module")
def con():
    return load_connectome()


def intervals(good=(), bad=()):
    """Bounds per k (k = 0 excluded): (lo, hi), positive at `good`, negative at `bad`, else straddling."""
    lo, hi = [], []
    for k in KS[1:]:
        if k in good:
            lo.append(0.1), hi.append(0.5)
        elif k in bad:
            lo.append(-0.5), hi.append(-0.1)
        else:
            lo.append(-0.1), hi.append(0.1)
    return KS[1:], np.array(lo), np.array(hi)


@pytest.mark.parametrize("good,bad,want,kstar,later", [
    ((0.5, 1, 2), (), "rises early", 0.5, False),
    ((4, 8, 16), (), "rises late", 4, False),
    ((8, 16), (0.1, 0.25), "dips first", 8, False),
    ((8, 16), (64, 256), "rises late", 8, True),
    ((), (2, 4), "harmed", None, False),
    ((), (), "no detected benefit on the tested grid", None, False),
    ((256,), (), "no detected benefit on the tested grid", None, False),  # k = 256 alone makes no class
    ((), (256,), "no detected benefit on the tested grid", None, False),
    ((64, 256), (), "rises late", 64, False),  # 64 improves with its neighbour 256
    ((1, 4), (), "no detected benefit on the tested grid", None, False),  # not adjacent: no k*
])
def test_the_sweep_classes(good, bad, want, kstar, later):
    ks, lo, hi = intervals(good, bad)
    got = D.sweep_class(ks, lo, hi)
    assert got["class"] == want and got["k_star"] == kstar and got["harmed_at_larger_k"] == later


def test_g0_bests_take_the_first_best_within_each_population():
    score = np.array([[1, 1], [3, 3], [3, 3],      # population 0: a tie between strains 1 and 2
                      [0, 0], [0, 0], [5, 5]])     # population 1: strain 2
    np.testing.assert_array_equal(D.g0_bests(score, population=3), [1, 2])
    # a population-major layout must not be read strain-major: [0 9 0 | 9 0 0] -> [1, 0]
    np.testing.assert_array_equal(D.g0_bests(np.array([[0], [9], [0], [9], [0], [0]]), population=3), [1, 0])
    with pytest.raises(ValueError):
        D.g0_bests(score, population=4)


def test_the_simulated_g0_best_is_the_one_evolve_batch_logs(con):
    cfg = task_n(30)
    cfg.evo.population, cfg.evo.worlds_per_strain, cfg.evo.elites, cfg.evo.truncation = 6, 3, 1, 3
    m = C.comparator("L1", w_n=3, w_o=3, tau=0.5, bias=0.0)
    ext = G.graft_connectome(con, m)
    iface = G.graft_interface(ext, m)
    spec = BrainSpec.from_connectome(ext)
    runs = [EV.RunSpec(run=i, run_seed=1_150_000 + i, shaping=0.0) for i in range(2)]
    pops = {r.run_seed: C.embedded_population(con, ext, m, cfg.brain, run_seed=r.run_seed, population=6) for r in runs}
    recs = EV.evolve_batch(cfg, iface, spec, runs, generations=1, checkpoint_every=1, validation_ids=np.arange(2),
                           world_seed=7, id_base=500, id_span=1000, initial=lambda r: pops[r.run_seed])
    sel = np.stack([EV.train_ids(r.run_seed, 0, 3, 500, 1000) for r in runs])  # the selection worlds
    from wormwars.brain import Genome
    genome = Genome.cat([pops[r.run_seed] for r in runs])
    res = rollout(cfg, iface, genome, np.repeat(sel, 6, axis=0), run_seed=7)
    best = D.g0_bests(res.score, population=6)
    for i, r in enumerate(runs):
        assert genome_hash(pops[r.run_seed], int(best[i])) == recs[i].log[0]["best_sha256"]
    # the diagnostic worlds are not the selection worlds: scoring elsewhere can pick another strain
    other = rollout(cfg, iface, genome, np.arange(40, 43), run_seed=7)
    assert D.g0_bests(other.score, population=6).shape == (2,)


def test_module_scales_mutate_only_the_module(con):
    m = C.comparator("L1", w_n=2, w_o=2, tau=0.5, bias=0.0)
    ext = G.graft_connectome(con, m)
    parent = C.carrier_genome(ext, m, Config().brain, forward=1.0, turn=0.1)
    s = D.module_scales(ext, 0.25)
    child = parent.clone().mutate(Config().mutation, torch.Generator().manual_seed(1_151_000), scales=s)
    n0 = con.n
    wp, gp = G.worm_parameters(ext, parent.w.numpy(), parent.g.numpy())
    wc, gc = G.worm_parameters(ext, child.w.numpy(), child.g.numpy())
    np.testing.assert_array_equal(wp, wc)
    np.testing.assert_array_equal(gp, gc)
    assert torch.equal(parent.tau[:, :n0], child.tau[:, :n0]) and torch.equal(parent.bias[:, :n0], child.bias[:, :n0])
    W0, _ = parent.dense()
    W1, _ = child.dense()
    cl, smdd = ext.index("E4S_CL"), ext.index("SMDDL")
    assert float(W0[0, cl, smdd]) != float(W1[0, cl, smdd])  # a graft-to-host weight mutated
    assert not torch.equal(parent.tau[:, n0:], child.tau[:, n0:])


def test_motor_stats_are_per_strain_episode_means(con):
    cfg = task_n(25)
    m = C.comparator("L1", w_n=0.0, w_o=0.0, tau=0.5, bias=0.0)  # a module with no effect
    ext = G.graft_connectome(con, m)
    iface = G.graft_interface(ext, m)
    from wormwars.brain import Genome
    a = C.carrier_genome(ext, m, cfg.brain, forward=0.5, turn=0.1)
    b = C.carrier_genome(ext, m, cfg.brain, forward=1.0, turn=-0.2)
    # settle the biases first: the worm's states start at 0, so the commands ramp up over a few ticks
    with D.motor_stats() as stats:
        rollout(cfg, iface, Genome.cat([a, b]), np.arange(3), run_seed=7, chunk_worlds=3)
    out = stats.per_strain(n_strains=2, n_worlds=3, skip_ticks=10)
    np.testing.assert_allclose(out["forward"], [[0.5] * 3, [1.0] * 3], atol=1e-4)
    np.testing.assert_allclose(out["turn"], [[0.1] * 3, [-0.2] * 3], atol=1e-4)
    np.testing.assert_array_equal(out["saturated_share"], np.zeros((2, 3)))


def test_the_settling_rule():
    t = np.arange(400)
    fast = 0.2 * (1 - np.exp(-t / 10))
    r = D.settle(fast)
    assert r["settled"] and r["final"] == pytest.approx(0.2, rel=1e-3)
    assert r["t90"] == pytest.approx(np.ceil(10 * np.log(10)), abs=1)
    slow = 0.2 * (1 - np.exp(-t / 300))
    assert not D.settle(slow)["settled"]
    assert D.settle(np.full(400, 5e-5))["flag"] == "negligible"
    assert D.settle(-fast, expected_sign=1)["flag"] == "wrong sign"
