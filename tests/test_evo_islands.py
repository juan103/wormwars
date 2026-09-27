"""The island path (roadmap v3, T0): three bugs, each confirmed by a failing test before its fix
(D064). No published run used islands: every recorded config has `islands: 1`."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo.evolve import _breed_islands, _migrate


@pytest.fixture(scope="module")
def spec():
    return BrainSpec.from_connectome(load_connectome())


def _cfg(pop, islands, dale=False):
    cfg = Config()
    cfg.evo.population, cfg.evo.islands, cfg.evo.elites, cfg.evo.truncation = pop, islands, 3, 6
    cfg.evo.migrants = 1
    cfg.mutation.w_sigma = cfg.mutation.g_sigma = cfg.mutation.tau_sigma = cfg.mutation.bias_sigma = 0.0
    cfg.brain.dale = dale
    return cfg


def _sources(child: Genome, slot: int, parents: Genome) -> set:
    return {s for s in range(parents.n_strains) if torch.equal(child.w[slot], parents.w[s])}


def test_every_slot_keeps_its_island_after_breeding(spec):
    """Bug 1: islands are assigned interleaved (strain i -> island i % k), but breeding put each
    island's children back in contiguous blocks, so from the second generation on the 'islands'
    mixed members of every island."""
    cfg = _cfg(12, 3)
    p = Genome.random(spec, cfg.brain, 12, generator=torch.Generator().manual_seed(1))
    island_of = np.arange(12) % 3
    fit = np.random.default_rng(0).normal(size=12)
    nxt = _breed_islands(p, fit, island_of, cfg, torch.Generator().manual_seed(2))
    for slot in range(12):
        members = set(np.flatnonzero(island_of == island_of[slot]).tolist())
        assert _sources(nxt, slot, p) & members, f"slot {slot} holds a genome from another island"


def test_migrants_carry_their_own_fitness_into_breeding(spec):
    """Bug 2: migration copied the best genomes over the worst but left `fit` unchanged, so the
    migrants entered selection with the fitness of the strains they replaced and were culled."""
    cfg = _cfg(9, 3)
    p = Genome.random(spec, cfg.brain, 9, generator=torch.Generator().manual_seed(3))
    island_of = np.arange(9) % 3
    fit = np.array([5.0, 1.0, 9.0, 0.0, 2.0, 3.0, 7.0, 4.0, 6.0])
    moved, new_fit = _migrate(p, fit, island_of, cfg.evo, torch.Generator().manual_seed(4))
    # island 0 = {0, 3, 6}: its best is 6 (7.0); island 1 = {1, 4, 7}: its worst is 1 (1.0)
    torch.testing.assert_close(moved.w[1], p.w[6], rtol=0, atol=0)
    assert new_fit[1] == 7.0
    assert fit[1] == 1.0  # the caller's array is not modified in place


def test_migrants_keep_their_sign_vector(spec):
    """Bug 3: migration copied weights, gaps, time constants and biases but kept the destination's
    per-strain Dale sign vector, so a migrant arrived as a different brain."""
    cfg = _cfg(9, 3, dale=True)
    p = Genome.random(spec, cfg.brain, 9, generator=torch.Generator().manual_seed(5))
    assert p.dale_sign is not None and not torch.equal(p.dale_sign[1], p.dale_sign[6])
    island_of = np.arange(9) % 3
    fit = np.array([5.0, 1.0, 9.0, 0.0, 2.0, 3.0, 7.0, 4.0, 6.0])
    moved, _ = _migrate(p, fit, island_of, cfg.evo, torch.Generator().manual_seed(6))
    torch.testing.assert_close(moved.dale_sign[1], p.dale_sign[6], rtol=0, atol=0)


def test_one_island_is_unchanged_by_the_island_code(spec):
    """Every published run used one island: that path must not change."""
    from wormwars.evo.evolve import breed
    cfg = _cfg(12, 1)
    cfg.mutation.w_sigma = 0.08
    p = Genome.random(spec, cfg.brain, 12, generator=torch.Generator().manual_seed(7))
    fit = np.random.default_rng(1).normal(size=12)
    a = _breed_islands(p, fit, np.zeros(12, int), cfg, torch.Generator().manual_seed(8))
    b = breed(p, fit, cfg, torch.Generator().manual_seed(8))
    torch.testing.assert_close(a.w, b.w, rtol=0, atol=0)


def test_an_island_run_with_migration_runs_end_to_end(spec):
    from wormwars.evo.evolve import evolve
    from wormwars.interface import load_interface
    cfg = _cfg(6, 2, dale=True)
    cfg.mutation.w_sigma = 0.08
    cfg.world.max_ticks = 60
    cfg.evo.generations, cfg.evo.worlds_per_strain, cfg.evo.holdout_worlds, cfg.evo.migrate_every = 3, 2, 2, 1
    cfg.evo.elites, cfg.evo.truncation = 2, 4
    r = evolve(cfg, load_interface(load_connectome()), spec, run=0, run_seed=5, verbose=False, holdout_every=9)
    assert len(r.log) == 3 and r.champion.n_strains == 1
    assert all(np.isfinite(g.best) for g in r.log)
