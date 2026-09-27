"""T0 items 3-5, CPU parts (docs/foundations/T0.md v2.1; D073).

Item 3: save, load and re-simulate exactly on CPU. Item 4: the energy ledger (relative 1e-5 per
world at every tick) and numerical checks. Item 5: island validation and stronger island tests.
The CUDA parts (replay mode, the default-CUDA tolerance, historical replay) wait for the GPU.
Plus the jitter test owed from item 1: a (1, 3) match beside a (2, 2) match."""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import random_graph, shuffled
from wormwars.evo import rollout
from wormwars.evo.genomes import genome_hash, load_genome, save_genome
from wormwars.exp02 import grid
from wormwars.interface import load_interface
from wormwars.world import World

E = importlib.import_module("wormwars.evo.evolve")


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


# ------------------------------------------------------------------ item 3 (CPU)

def test_save_load_and_resimulate_exactly_on_cpu(parts, tmp_path):
    con, iface, spec = parts
    cfg = grid.task_config(Config(), "T1")
    cfg.world.max_ticks = 50
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(1))
    loaded, _ = load_genome(save_genome(tmp_path / "g.npz", g, 0, cfg=cfg), spec)
    for k in Genome.PARAMS:
        a, b = getattr(g, k), getattr(loaded, k)
        assert (a is None and b is None) or torch.equal(a, b)
    ids = np.array([3, 4, 5])
    first = rollout(cfg, iface, g, ids, run_seed=2).score
    np.testing.assert_array_equal(rollout(cfg, iface, loaded, ids, run_seed=2).score, first)
    np.testing.assert_array_equal(rollout(cfg, iface, g, ids, run_seed=2).score, first)


# ------------------------------------------------------------------ item 4

def _graphs(con):
    return {"N2": con, "SH": shuffled(con, seed=11), "RD": random_graph(con, seed=12)}


@pytest.mark.parametrize("task", ["T0", "T1"])
def test_the_energy_ledger_balances_at_every_tick(parts, task):
    """The declared bound: relative error below 1e-5 per world against its own starting energy,
    at every tick, for N2, SH and RD on 8 worlds at 02's task settings."""
    con, iface, spec = parts
    for name, graph in _graphs(con).items():
        cfg = grid.task_config(Config(), task)
        cfg.world.check_ledger_every_tick = True
        gspec = BrainSpec.from_connectome(graph)
        g = Genome.random(gspec, cfg.brain, 1, generator=torch.Generator().manual_seed(3))
        r = rollout(cfg, load_interface(graph) if name != "N2" else iface, g, np.arange(8), run_seed=4)
        assert math.isfinite(r.ledger_rel_error), name
        assert r.ledger_rel_error < 1e-5, f"{name} {task}: relative ledger error {r.ledger_rel_error:.2e}"
        assert np.isfinite(r.score).all() and np.isfinite(r.energy).all(), name


def test_a_nan_ledger_error_is_not_swallowed(parts, monkeypatch):
    """max(0.0, nan) is 0.0 in Python: the rollout used to report a NaN residual as 0."""
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 3
    g = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(5))
    monkeypatch.setattr(World, "energy_ledger_error",
                        lambda self: torch.full((self.n_worlds,), float("nan"), dtype=torch.float64))
    r = rollout(cfg, iface, g, np.array([1]), run_seed=1, chunk_worlds=1)
    assert math.isnan(r.ledger_error) and math.isnan(r.ledger_rel_error)


@pytest.mark.parametrize("sign", [1.0, -1.0])
def test_extreme_genomes_stay_finite_over_a_full_episode(parts, sign):
    con, iface, spec = parts
    cfg = grid.task_config(Config(), "T0")
    b = cfg.brain
    g = Genome.random(spec, b, 1, generator=torch.Generator().manual_seed(6)).with_params(
        w=torch.full((1, spec.n_chem), sign * b.w_max), g=torch.full((1, spec.n_gap), b.g_max),
        tau=torch.full((1, spec.n), b.tau_min), bias=torch.full((1, spec.n), sign * b.b_max))
    w = World(cfg, iface, Brain(g), torch.zeros(4, 1, dtype=torch.long), run_seed=7,
              world_ids=np.arange(4))
    w.run()
    assert all(torch.isfinite(v).all() for v in w.v)
    assert torch.isfinite(w.energy).all()


def test_a_published_champion_stays_finite_over_a_full_episode(parts):
    from pathlib import Path
    from wormwars.evo.genomes import apply_world_meta, brain_config_for
    con, iface, spec = parts
    f = sorted(Path(__file__).resolve().parents[1].glob("runs/exp01b-direction-corrected/champion-N2-run*.npz"))[0]
    champ, meta = load_genome(f, spec)
    cfg, _ = apply_world_meta(Config(), meta)
    cfg.brain = champ.cfg
    w = World(cfg, iface, Brain(champ), torch.zeros(4, 1, dtype=torch.long), run_seed=8,
              world_ids=np.arange(4))
    w.run()
    assert all(torch.isfinite(v).all() for v in w.v) and torch.isfinite(w.energy).all()


# ------------------------------------------------------------------ item 5

def _island_cfg(pop=6, islands=2, migrants=1, migrate_every=1):
    cfg = Config()
    cfg.world.max_ticks = 10
    cfg.evo.population, cfg.evo.islands, cfg.evo.migrants = pop, islands, migrants
    cfg.evo.migrate_every, cfg.evo.generations, cfg.evo.worlds_per_strain = migrate_every, 2, 1
    cfg.evo.holdout_worlds, cfg.evo.elites, cfg.evo.truncation = 1, 2, 4
    return cfg


@pytest.mark.parametrize("kw, msg", [
    ({"pop": 3, "islands": 4}, "empty"),
    ({"migrate_every": 0}, "migrate_every"),
    ({"pop": 5, "islands": 2, "migrants": 2}, "migrants"),
])
def test_unsupported_island_settings_are_refused_before_anything_runs(parts, kw, msg):
    con, iface, spec = parts
    with pytest.raises(ValueError, match=msg):
        E.evolve(_island_cfg(**kw), iface, spec, run=0, run_seed=1, verbose=False)


def test_a_migrant_survives_breeding_with_every_field(parts):
    con, iface, spec = parts
    cfg = _island_cfg(pop=6)
    cfg.brain.dale = True
    cfg.mutation.w_sigma = cfg.mutation.g_sigma = cfg.mutation.tau_sigma = cfg.mutation.bias_sigma = 0.0
    p = Genome.random(spec, cfg.brain, 6, generator=torch.Generator().manual_seed(9))
    isl = np.arange(6) % 2
    fit = np.array([9.0, 1.0, 2.0, 3.0, 0.0, 5.0])  # island 0's best (0, 9.0) is better than all of island 1
    moved, new_fit = E._migrate(p, fit, isl, cfg.evo, torch.Generator().manual_seed(10))
    bred = E._breed_islands(moved, new_fit, isl, cfg, torch.Generator().manual_seed(11))
    donor = genome_hash(p, 0)
    island1 = np.flatnonzero(isl == 1)
    assert donor in {genome_hash(bred, int(i)) for i in island1}  # an elite of island 1 now


def test_islands_stay_isolated_over_generations_without_migration(parts):
    """The first version checked winners against the union of both islands' ancestors, so it could
    not fail (both reviewers, D074). Now every slot of every generation's population must descend,
    unmutated, from its own island's generation-0 members."""
    con, iface, spec = parts
    cfg = _island_cfg(pop=6, migrate_every=99)
    cfg.mutation.w_sigma = cfg.mutation.g_sigma = cfg.mutation.tau_sigma = cfg.mutation.bias_sigma = 0.0
    isl = np.arange(6) % 2
    p = Genome.random(spec, cfg.brain, 6, generator=torch.Generator().manual_seed(1))
    own = {i: {genome_hash(p, j) for j in np.flatnonzero(isl == i)} for i in (0, 1)}
    rng = np.random.default_rng(0)
    for gen in range(4):
        fit = rng.normal(size=6)
        p = E._breed_islands(p, fit, isl, cfg, torch.Generator().manual_seed(gen))
        for slot in range(6):
            assert genome_hash(p, slot) in own[isl[slot]], f"generation {gen}, slot {slot}"


# ------------------------------------------------------------------ owed from item 1

def test_jitter_end_to_end_a_3_wey_neighbour_does_not_change_a_2_2_match(parts):
    """Astra: a (1, 3) match beside a (2, 2) match changed swarm 1's noise in the (2, 2) match.
    The first version of this test left the radius at 0, so it compared zeros (both reviewers,
    D074). Now: radius 1; jitter must move points; and the (2, 2) world's draws, taken from the
    real layouts, are identical alone and beside a (1, 3) world. (The two layouts place weys
    differently, a separate map defect recorded in D073/D074, so offsets are compared through the
    keyed draws, not through points that differ.)"""
    con, iface, spec = parts
    cfg = Config()
    cfg.world.n_swarms, cfg.world.food_probe, cfg.world.food_probe_radius = 2, "jitter", 1.0
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(12))

    def world(sizes, ids):
        return World(cfg, iface, Brain(g), torch.zeros(len(ids), 2, dtype=torch.long), run_seed=5,
                     world_ids=np.array(ids), swarm_sizes=torch.tensor(sizes))

    alone, beside = world([[2, 2]], [7]), world([[2, 2], [1, 3]], [7, 8])
    assert beside.n_weys == 3 and alone.n_weys == 2
    pts = alone.sample_points()
    assert (alone._jittered(pts) - pts).abs().max() > 0.1  # jitter really moves points
    for stream in (0, 1):
        a, b = alone._keyed_uniform(stream), beside._keyed_uniform(stream)  # real layouts
        torch.testing.assert_close(b[0, :, :2], a[0], rtol=0, atol=0)
