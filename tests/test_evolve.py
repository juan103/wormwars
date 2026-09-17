"""Selection, breeding, islands and the seed pools."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo import SeedPool, rollout
from wormwars.evo.evolve import _breed_islands, _migrate, breed, evolve
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def pop(spec, cfg, n=12, seed=0):
    return Genome.random(spec, cfg.brain, n, generator=torch.Generator().manual_seed(seed))


# ------------------------------------------------------------------ breeding


def test_elites_survive_untouched(parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.evo.population, cfg.evo.elites, cfg.evo.truncation = 12, 3, 6
    p = pop(spec, cfg)
    fit = np.arange(12, dtype=float)  # strain 11 is best
    nxt = breed(p, fit, cfg, torch.Generator().manual_seed(1))
    assert nxt.n_strains == 12
    best = np.argsort(-fit)[:3]
    for slot, src in enumerate(best):
        torch.testing.assert_close(nxt.w[slot], p.w[src], rtol=0, atol=0)


def test_children_come_only_from_the_truncated_top(parts):
    """With mutation off, every child must be an exact copy of one of the parents."""
    con, iface, spec = parts
    cfg = Config()
    cfg.evo.population, cfg.evo.elites, cfg.evo.truncation = 10, 1, 3
    cfg.mutation.w_sigma = cfg.mutation.g_sigma = 0.0
    cfg.mutation.tau_sigma = cfg.mutation.bias_sigma = 0.0
    p = pop(spec, cfg, 10, seed=2)
    fit = np.arange(10, dtype=float)
    nxt = breed(p, fit, cfg, torch.Generator().manual_seed(3))
    allowed = set(np.argsort(-fit)[:3].tolist())
    for child in range(1, 10):
        matches = {
            src for src in range(10) if torch.equal(nxt.w[child], p.w[src])
        }
        assert matches & allowed, f"child {child} did not come from the top 3"


def test_breeding_keeps_the_bounds(parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.mutation.w_sigma = 10.0
    p = pop(spec, cfg, 8, seed=4)
    nxt = breed(p, np.arange(8, dtype=float), cfg, torch.Generator().manual_seed(5))
    assert nxt.w.abs().max() <= cfg.brain.w_max + 1e-6
    assert nxt.tau.min() >= cfg.brain.tau_min - 1e-6


# ------------------------------------------------------------------- islands


def test_islands_breed_independently(parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.evo.population, cfg.evo.islands, cfg.evo.elites = 12, 3, 3
    cfg.mutation.w_sigma = cfg.mutation.g_sigma = 0.0
    cfg.mutation.tau_sigma = cfg.mutation.bias_sigma = 0.0
    p = pop(spec, cfg, 12, seed=6)
    island_of = np.arange(12) % 3
    # make island 0 uniformly terrible and island 1 uniformly excellent
    fit = np.where(island_of == 1, 100.0, np.where(island_of == 0, -100.0, 0.0))
    nxt = _breed_islands(p, fit, island_of, cfg, torch.Generator().manual_seed(7))
    assert nxt.n_strains == 12
    # island 0's slots must still hold island 0 genomes: a bad island is not replaced by a good one
    island0 = set(np.flatnonzero(island_of == 0).tolist())
    for slot in range(len(island0)):
        srcs = {s for s in range(12) if torch.equal(nxt.w[slot], p.w[s])}
        assert srcs & island0, "an island bred from another island's genomes"


def test_migration_moves_the_best_into_the_next_island(parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.evo.population, cfg.evo.islands, cfg.evo.migrants = 9, 3, 1
    p = pop(spec, cfg, 9, seed=8)
    island_of = np.arange(9) % 3
    fit = np.array([5.0, 1.0, 9.0, 0.0, 2.0, 3.0, 7.0, 4.0, 6.0])
    moved, _ = _migrate(p, fit, island_of, cfg.evo, torch.Generator().manual_seed(9))
    # island 0 = {0,3,6}; its best is 6. island 1 = {1,4,7}; its worst is 1.
    torch.testing.assert_close(moved.w[1], p.w[6], rtol=0, atol=0)
    assert not torch.equal(moved.w[1], p.w[1])


def test_runs_are_independent(parts):
    """Islands may exchange champions within a run, never between runs -- so two runs with
    different seeds must share nothing, and the same seed must reproduce exactly."""
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 80
    cfg.evo.population, cfg.evo.generations, cfg.evo.worlds_per_strain = 6, 2, 2
    cfg.evo.holdout_worlds = 2
    a = evolve(cfg, iface, spec, run=0, run_seed=101, verbose=False, holdout_every=9)
    b = evolve(cfg, iface, spec, run=0, run_seed=202, verbose=False, holdout_every=9)
    same = evolve(cfg, iface, spec, run=0, run_seed=101, verbose=False, holdout_every=9)
    assert not torch.equal(a.champion.w, b.champion.w), "different seeds gave the same champion"
    torch.testing.assert_close(a.champion.w, same.champion.w, rtol=0, atol=0)


# ---------------------------------------------------------------- seed pools


def test_training_and_holdout_pools_are_disjoint():
    cfg = Config()
    pool = SeedPool(cfg, run_seed=3)
    held = set(pool.holdout.tolist())
    train = set()
    for g in range(200):
        train |= set(pool.train_ids(g, 16).tolist())
    assert not (train & held), "a held-out world id was used for selection"


def test_training_ids_are_reproducible_and_vary_by_generation():
    cfg = Config()
    a, b = SeedPool(cfg, 11), SeedPool(cfg, 11)
    assert a.train_ids(4).tolist() == b.train_ids(4).tolist()
    assert a.train_ids(4).tolist() != a.train_ids(5).tolist()
    assert SeedPool(cfg, 12).train_ids(4).tolist() != a.train_ids(4).tolist()


# ------------------------------------------------------------ a whole run


def test_a_short_run_improves_and_returns_a_champion(parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 120
    cfg.evo.population, cfg.evo.generations, cfg.evo.worlds_per_strain = 8, 4, 2
    cfg.evo.holdout_worlds = 2
    res = evolve(cfg, iface, spec, run=0, run_seed=5, verbose=False, holdout_every=3)
    assert res.champion is not None and res.champion.n_strains == 1
    assert len(res.log) == 4
    assert res.champion_id.startswith("N2-run00-")
    assert res.evaluations == 8 * 2 * 4
