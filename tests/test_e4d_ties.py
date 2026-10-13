"""The evolutionary E4-D's random tie-breaking (design v2.1 §3; both reviewers, D265): exact fitness ties ordered by a
recorded per-run stream, a flag that is off for every earlier experiment; the lineage replay follows it."""

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
import importlib

EVO = importlib.import_module("wormwars.evo.evolve")  # the module (the package re-exports a function of this name)


def test_without_a_stream_the_ranking_is_unchanged():
    f = np.array([0.5, 0.75, 0.5, 0.25, 0.5])
    assert np.array_equal(EVO.ranking(f), np.argsort(-f))


def test_with_a_stream_ties_are_shuffled_and_order_kept():
    f = np.array([0.5] * 10 + [0.9])
    seen = set()
    for s in range(20):
        r = EVO.ranking(f, np.random.default_rng(s))
        assert r[0] == 10  # the best stays first
        seen.add(tuple(r[1:4]))
    assert len(seen) > 1  # the tied strains are not always taken in index order


@pytest.fixture(scope="module")
def evolved():
    cfg = MW.maze_config(c=6, horizon=40, colony=8, mu=0.01, lam=0.02, delta=0.05, d0=1.142, access="shared",
                         family="islands", k_r=0)
    cfg.evo.population, cfg.evo.elites, cfg.evo.truncation, cfg.evo.worlds_per_strain = 6, 2, 3, 1
    cx = AR.context(load_connectome(), A.load_l1(), cfg.brain)
    org = cx["org"]
    sc = AR.scales(cx, "x_plus", cross_factor=0.5)
    start = Genome.cat([org.genome.select([0])] * cfg.evo.population)
    runs = [EV.RunSpec(0, 1_420_000, 0.0), EV.RunSpec(1, 1_420_001, 0.0)]
    cap = LI.Capture(TR.gated_rollout(org.gate))
    recs = EV.evolve_batch(cfg, org.iface, org.genome.spec, runs, generations=4, checkpoint_every=10 ** 6,
                           validation_ids=np.array([42_000]), world_seed=1_420_000, id_base=50_000_000,
                           id_span=1_000_000, device="cpu", rollout_fn=cap, initial=lambda r: start,
                           mutation_scales=lambda r: sc, random_ties=True)
    return cfg, runs, start, sc, cap, recs


def test_the_replay_follows_random_ties(evolved):
    cfg, runs, start, sc, cap, recs = evolved
    rep = LI.replay(cfg, runs, cap.selections, initial=lambda r: start, mutation_scales=lambda r: sc, device="cpu",
                    random_ties=True)
    for i, rec in enumerate(recs):
        for k in ("w", "bias", "tau", "g"):
            assert torch.equal(getattr(rep[i]["final"], k), getattr(rec.final, k))


def test_a_replay_without_the_flag_differs(evolved):
    """The sabotage: replaying random-tie runs with index ties does not reproduce them (H = 40 makes ties common)."""
    cfg, runs, start, sc, cap, recs = evolved
    rep = LI.replay(cfg, runs, cap.selections, initial=lambda r: start, mutation_scales=lambda r: sc, device="cpu")
    assert not all(torch.equal(rep[i]["final"].w, rec.final.w) for i, rec in enumerate(recs))


def _old_breed(genome, fitness, cfg, generator, scales=None):
    """`breed` as it was before the evolutionary E4-D (81bc127^), for the flag-off equivalence (Astra)."""
    e = cfg.evo
    order = np.argsort(-fitness)
    elites = order[: e.elites]
    parents = order[: min(e.truncation, len(order))]
    n_children = e.population - len(elites)
    pick = parents[torch.randint(len(parents), (n_children,), generator=generator, device=genome.device).cpu().numpy()]
    children = genome.select(list(pick))
    children.mutate(cfg.mutation, generator=generator, scales=scales)
    return Genome.cat([genome.select(list(elites)), children])


def test_tied_fitness_without_a_stream_keeps_index_order():
    """The contract (Fable): with no stream, tied strains rank in index order, so the elites are the first indices."""
    assert EVO.ranking(np.zeros(6)).tolist()[:3] == [0, 1, 2]


def test_breed_without_a_stream_equals_the_old_breed(evolved):
    cfg, runs, start, sc, cap, recs = evolved
    g = start.clone()
    g = g.with_params(bias=g.bias + torch.arange(g.n_strains, dtype=g.bias.dtype)[:, None] * 1e-3)
    fit = np.array([0.5, 0.25, 0.5, 0.75, 0.5, 0.0])
    a_gen, b_gen = torch.Generator().manual_seed(9), torch.Generator().manual_seed(9)
    a = EVO.breed(g.clone(), fit, cfg, a_gen, sc)
    b = _old_breed(g.clone(), fit, cfg, b_gen, sc)
    for k in ("w", "bias", "tau", "g"):
        assert torch.equal(getattr(a, k), getattr(b, k))
    assert torch.equal(a_gen.get_state(), b_gen.get_state())


def test_the_recovered_parents_with_random_ties(evolved):
    """With mutation off and a diverse start, each final strain equals the start strain its recorded lineage leads to,
    under random ties too (both: the final population alone cannot catch a wrong parents record)."""
    cfg, runs, start, sc, cap, recs = evolved
    diverse = start.with_params(bias=start.bias + torch.arange(start.n_strains, dtype=start.bias.dtype)[:, None] * 1e-3)
    zero = {k: torch.zeros_like(v) for k, v in sc.items()}
    rep = LI.replay(cfg, runs, cap.selections, initial=lambda r: diverse, mutation_scales=lambda r: zero, device="cpu",
                    random_ties=True)
    for r in rep:
        for k in range(cfg.evo.population):
            j = k
            for p in reversed(r["parents"]):
                j = p["source"][j]
            assert torch.equal(r["final"].bias[k], diverse.bias[j])
