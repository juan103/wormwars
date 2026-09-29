"""E2's optimizers (`wormwars/e2/optimizers.py`): the encoding, the utilities, the ES update on known
functions, and random sampling's best-since-checkpoint rule, with fake simulators."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e2 import optimizers as O


@pytest.fixture(scope="module")
def spec():
    return BrainSpec.from_connectome(load_connectome())


def _genomes(spec, n=4, seed=0):
    return Genome.random(spec, Config().brain, n, generator=torch.Generator().manual_seed(seed))


# ------------------------------------------------------------------ the encoding

def test_encoding_round_trips_inside_the_bounds(spec):
    g = _genomes(spec)
    z = O.encode(g)
    assert z.shape == (4, O.n_params(spec))
    back = O.decode(z, g)
    for k in ("w", "g", "tau", "bias"):
        torch.testing.assert_close(getattr(back, k), getattr(g, k), rtol=1e-5, atol=1e-6)


def test_the_encoding_scales_by_the_ga_mutation_sigmas(spec):
    g = _genomes(spec, n=1)
    z = O.encode(g)
    nw, ng, nn = spec.n_chem, spec.n_gap, spec.n
    torch.testing.assert_close(z[0, :nw], g.w[0] / 0.08)
    torch.testing.assert_close(z[0, nw:nw + ng], g.g[0] / 0.04)
    torch.testing.assert_close(z[0, nw + ng:nw + ng + nn], torch.log(g.tau[0]) / 0.15)
    torch.testing.assert_close(z[0, nw + ng + nn:], g.bias[0] / 0.05)


def test_decoding_clamps_to_the_genome_bounds(spec):
    g = _genomes(spec, n=1)
    z = O.encode(g) * 1000.0
    d = O.decode(z, g)
    c = g.cfg
    assert float(d.w.abs().max()) <= c.w_max and float(d.g.min()) >= 0 and float(d.g.max()) <= c.g_max
    assert float(d.tau.min()) >= c.tau_min - 1e-6 and float(d.tau.max()) <= c.tau_max + 1e-4
    assert float(d.bias.abs().max()) <= c.b_max


def test_projection_puts_the_mean_back_inside_the_bounds(spec):
    g = _genomes(spec, n=1)
    z = O.encode(g)[0] * 1000.0
    p = O.project(z, g)
    torch.testing.assert_close(O.encode(O.decode(p[None], g))[0], p, rtol=1e-5, atol=1e-4)


# ------------------------------------------------------------------ utilities

def test_utilities_are_centred_average_ranks():
    u = O.utilities(np.array([3.0, 1.0, 2.0, 2.0]))
    np.testing.assert_allclose(u, [0.5, -0.5, 0.0, 0.0])
    assert O.utilities(np.array([5.0, 5.0, 5.0])).tolist() == [0.0, 0.0, 0.0]


def test_equal_fitness_gives_equal_utility():
    u = O.utilities(np.array([0.0, 1.0, 0.0, 1.0, 0.0, 2.0]))
    assert u[0] == u[2] == u[4] and u[1] == u[3] and u[5] == 0.5


# ------------------------------------------------------------------ the ES on known functions

def _run_es(f, dim=6, sigma=0.5, lr=0.15, steps=300, seed=0, start=None):
    es = O.OpenAIES(np.full(dim, 3.0) if start is None else start, sigma=sigma, lr=lr, pairs=16,
                    generator=np.random.default_rng(seed))
    for _ in range(steps):
        cands = es.ask()
        es.tell(np.array([f(c) for c in cands]))
    return es


def test_the_es_climbs_a_quadratic():
    es = _run_es(lambda x: -float(np.sum(x ** 2)))
    assert float(np.linalg.norm(es.mean)) < 0.5 < float(np.linalg.norm(np.full(6, 3.0)))


def test_the_es_does_not_move_on_a_flat_function():
    es = _run_es(lambda x: 0.0, steps=50)
    np.testing.assert_array_equal(es.mean, np.full(6, 3.0))
    assert es.flat_generations == 50


def test_antithetic_pairs_share_their_noise():
    es = O.OpenAIES(np.zeros(3), sigma=0.5, lr=0.1, pairs=4, generator=np.random.default_rng(1))
    c = es.ask()
    assert c.shape == (8, 3)
    np.testing.assert_allclose(c[0::2] + c[1::2], 0.0, atol=1e-12)  # mean 0: x+ and x- are mirror images


def test_the_update_sign_follows_the_fitness():
    """With fitness rising along the first axis, the mean moves up that axis."""
    es = _run_es(lambda x: float(x[0]), steps=5, start=np.zeros(6))
    assert es.mean[0] > 0


# ------------------------------------------------------------------ random sampling

def test_random_sampling_keeps_the_best_since_the_last_checkpoint():
    rs = O.BestSinceCheckpoint()
    rs.offer(np.array([0.1, 0.5]), ["a", "b"])
    rs.offer(np.array([0.7, 0.2]), ["c", "d"])
    assert rs.take() == "c"
    rs.offer(np.array([0.3]), ["e"])
    assert rs.take() == "e"  # reset after each checkpoint


def test_random_sampling_breaks_ties_by_the_earliest():
    rs = O.BestSinceCheckpoint()
    rs.offer(np.array([0.5, 0.5]), ["a", "b"])
    rs.offer(np.array([0.5]), ["c"])
    assert rs.take() == "a"


def test_a_flat_batch_after_real_updates_moves_nothing():
    """Review v2 (Astra): a zero gradient does not stop Adam's momentum, so a flat batch must leave the
    mean, the moments and the step counter untouched."""
    es = O.OpenAIES(np.zeros(4), sigma=0.5, lr=0.1, pairs=4, generator=np.random.default_rng(2))
    for _ in range(5):
        c = es.ask()
        es.tell(np.array([float(x[0]) for x in c]))
    mean, m, v, t = es.mean.copy(), es.m.copy(), es.v.copy(), es.t
    es.ask()
    es.tell(np.zeros(8))
    np.testing.assert_array_equal(es.mean, mean)
    np.testing.assert_array_equal(es.m, m)
    np.testing.assert_array_equal(es.v, v)
    assert es.t == t and es.flat_generations == 1


def test_a_batch_tied_within_every_pair_moves_nothing():
    """Review v2.1 (Fable): if every antithetic pair ties within itself, the gradient is zero although
    the batch is not flat; it is treated as flat, so Adam's momentum does not move the mean."""
    es = O.OpenAIES(np.zeros(4), sigma=0.5, lr=0.1, pairs=4, generator=np.random.default_rng(3))
    for _ in range(5):
        c = es.ask()
        es.tell(np.array([float(x[0]) for x in c]))
    mean, t = es.mean.copy(), es.t
    es.ask()
    es.tell(np.array([1.0, 1.0, 2.0, 2.0, 3.0, 3.0, 0.0, 0.0]))  # pairs tie within, not across
    np.testing.assert_array_equal(es.mean, mean)
    assert es.t == t and es.flat_generations == 1
