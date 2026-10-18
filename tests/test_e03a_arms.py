"""03a's arms (DESIGN.md v7.1 §3, §8): NIP brains pinned through initialisation and every mutation in a real lockstep
evolution, intact runs in the same batch unchanged; the deletion scan; scoring reinserted states."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.connectome import load_connectome
from wormwars.deletion import delete_neurons
from wormwars.e03a import arms as A
from wormwars.e03a import reinsert as R
from wormwars.e04a import evolve as EV
from wormwars.e1.task import task_n_config
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    iface = load_interface(con)
    cfg = task_n_config(sigma=6.0, amplitude=1.0, radius=1.5, separation=8.0, horizon=12)
    cfg.world.food_sensing = "mono"
    cfg.brain.substeps = 4
    cfg.evo.population, cfg.evo.elites, cfg.evo.truncation, cfg.evo.worlds_per_strain = 6, 1, 3, 2
    return con, iface, cfg


def _evolve(parts, target_of, scales=True, generations=4):
    con, iface, cfg = parts
    spec = BrainSpec.from_connectome(con)
    initial, sc = A.hooks(spec, cfg.brain, cfg.evo.population, target_of)
    runs = [EV.RunSpec(run=i, run_seed=500 + i, shaping=0.0) for i in range(3)]
    return EV.evolve_batch(cfg, iface, spec, runs, generations=generations, checkpoint_every=2,
                           validation_ids=np.arange(100, 103), world_seed=9, id_base=0, id_span=50,
                           initial=initial, mutation_scales=sc if scales else None, snapshot_at=(0, 1, 2, 3))


def test_nip_runs_stay_pinned_through_evolution_and_intact_runs_are_unchanged(parts):
    con, _, cfg = parts
    x = con.index("AIYL")
    recs = _evolve(parts, {1: x, 2: x})
    for rec in recs[1:]:
        for g in list(rec.snapshots.values()) + rec.candidates + [rec.final]:
            assert R.x_edges_zero(g, x)
    # run 0 is an ordinary intact run: its generation 0 is e04a's initial population, X's edges included
    spec = BrainSpec.from_connectome(con)
    g0 = EV.initial_population(spec, cfg.brain, 500, cfg.evo.population, "cpu")
    assert torch.equal(recs[0].snapshots[0].w, g0.w) and not R.x_edges_zero(recs[0].final, x)


def test_without_the_scales_x_regrows_its_edges(parts):
    """Sabotage: the pinning test fails when the mutation scales are not applied."""
    con, _, _ = parts
    x = con.index("AIYL")
    recs = _evolve(parts, {1: x}, scales=False, generations=2)
    assert R.x_edges_zero(recs[1].snapshots[0], x) and not R.x_edges_zero(recs[1].final, x)


def test_a_pinned_brain_is_x_deleted(parts):
    con, iface, cfg = parts
    x = con.index("AIYL")
    spec = BrainSpec.from_connectome(con)
    g = A.nip_initial(spec, cfg.brain, 3, 2, x)
    d = delete_neurons(g, [[x], [x]])
    a = A.counts(cfg, iface, g, np.arange(3), 4, "cpu")
    b = A.counts(cfg, iface, d, np.arange(3), 4, "cpu")
    np.testing.assert_array_equal(a, b)


def test_deletion_scan_matches_deleting_one_at_a_time(parts):
    con, iface, cfg = parts
    g = Genome.random(BrainSpec.from_connectome(con), cfg.brain, 1, generator=torch.Generator().manual_seed(1))
    ks = [con.index("AIYL"), con.index("AVAL")]
    intact, dele = A.deletion_scan(cfg, iface, g, ks, np.arange(4), 4, "cpu")
    assert intact.shape == (4,) and dele.shape == (2, 4)
    one = A.counts(cfg, iface, delete_neurons(g, [[ks[1]]]), np.arange(4), 4, "cpu")
    np.testing.assert_array_equal(dele[1], one[0])


def test_score_states_restoration_equals_the_intact_brain(parts):
    con, iface, cfg = parts
    g = Genome.random(BrainSpec.from_connectome(con), cfg.brain, 1, generator=torch.Generator().manual_seed(2))
    x = con.index("AIYL")
    reins = R.Reinsertion(con, x, g)
    a = A.score_states(cfg, iface, reins, reins.saved_state(g), np.arange(4), 4, "cpu")
    b = A.counts(cfg, iface, g, np.arange(4), 4, "cpu")
    np.testing.assert_array_equal(a, b)


def test_intact_runs_evolve_exactly_as_without_the_nip_hooks(parts):
    """Astra: 'intact runs unchanged' must mean equal to an ordinary evolution, not only an ordinary generation 0."""
    con, _, _ = parts
    x = con.index("AIYL")
    with_hooks = _evolve(parts, {1: x, 2: x}, generations=3)
    without = _evolve(parts, {}, generations=3)
    a, b = with_hooks[0], without[0]
    assert [c["sha256"] for c in a.checkpoints] == [c["sha256"] for c in b.checkpoints]
    assert torch.equal(a.final.w, b.final.w) and [g["best_fitness"] for g in a.log] == [g["best_fitness"] for g in b.log]


def test_same_episodes_compares_trajectories_not_only_counts(parts):
    """Sabotage for the driver's controls: two brains with equal counts but different movement are told apart."""
    con, iface, cfg = parts
    spec = BrainSpec.from_connectome(con)
    g1 = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(3))
    g2 = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(4))
    a = A.play(cfg, iface, g1, np.arange(3), 4, "cpu")
    b = A.play(cfg, iface, g2, np.arange(3), 4, "cpu")
    assert A.same_episodes(a, A.play(cfg, iface, g1, np.arange(3), 4, "cpu"))
    assert not A.same_episodes(a, b)
