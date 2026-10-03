"""04a's lockstep batch of independent runs (`wormwars/e04a/evolve.py`, D103), with a fake rollout
whose count and progress are known functions of the genome and the world id."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e04a import evolve as E


@pytest.fixture(scope="module")
def spec():
    return BrainSpec.from_connectome(load_connectome())


def _cfg(population=6, worlds=3):
    c = Config()
    c.evo.population, c.evo.worlds_per_strain, c.evo.elites, c.evo.truncation = population, worlds, 1, 3
    return c


class FakeRollout:
    """count = 1 if the strain's mean bias exceeds a threshold, else 0; progress = a fixed function of
    the world id. Records every call's genome size, ids and chunk."""

    def __init__(self):
        self.calls = []

    def __call__(self, cfg, iface, genome, ids, world_seed, device, chunk_worlds=None):
        ids = np.asarray(ids)
        self.calls.append({"strains": genome.n_strains, "ids": ids.copy(), "chunk": chunk_worlds, "seed": world_seed})
        b = genome.bias.mean(dim=1).cpu().numpy()
        n_w = ids.shape[-1]
        count = np.repeat((b > 0.0).astype(np.float32)[:, None], n_w, axis=1)
        prog = ((ids % 7) / 7.0) if ids.ndim == 2 else np.tile((ids % 7) / 7.0, (genome.n_strains, 1))
        return SimpleNamespace(score=count, progress=prog.astype(np.float32))


def _runs(shapings=(0.5, 0.0)):
    return [E.RunSpec(run=i, run_seed=1000 + i, shaping=c) for i, c in enumerate(shapings)]


def _evolve(spec, runs, fake, generations=5, every=2):
    return E.evolve_batch(_cfg(), None, spec, runs, generations=generations, checkpoint_every=every,
                          validation_ids=np.arange(4), world_seed=7, id_base=500, id_span=1000, rollout_fn=fake)


def test_shaping_must_stay_below_one_arrival():
    with pytest.raises(ValueError):
        E.RunSpec(0, 1, 1.0)
    with pytest.raises(ValueError):
        E.fitness(np.zeros((2, 2)), np.zeros((2, 2)), -0.1)
    with pytest.raises(ValueError):
        E.fitness(np.zeros((1, 2)), np.array([[0.0, 1.5]]), 0.5)


def test_fitness_is_the_count_plus_c_times_progress():
    count = np.array([[1, 0], [2, 2]], dtype=float)
    prog = np.array([[0.5, 1.0], [0.0, 0.2]])
    np.testing.assert_allclose(E.fitness(count, prog, 0.5), [(1.25 + 0.5) / 2, (2 + 2.1) / 2])
    np.testing.assert_allclose(E.fitness(count, prog, 0.0), count.mean(axis=1))
    # the bonus never adds a whole arrival
    assert (E.fitness(count, np.ones_like(prog), 0.99) - count.mean(axis=1)).max() < 1.0


def test_training_ids_depend_on_the_run_seed_and_generation_only():
    a = E.train_ids(11, 3, 8, 997_000_000, 1_000_000)
    assert np.array_equal(a, E.train_ids(11, 3, 8, 997_000_000, 1_000_000))
    assert not np.array_equal(a, E.train_ids(12, 3, 8, 997_000_000, 1_000_000))
    assert not np.array_equal(a, E.train_ids(11, 4, 8, 997_000_000, 1_000_000))
    assert a.min() >= 997_000_000 and a.max() < 998_000_000


def test_each_strain_plays_its_own_runs_worlds_in_one_rollout(spec):
    fake = FakeRollout()
    runs = _runs()
    _evolve(spec, runs, fake, generations=1, every=1)
    train = fake.calls[0]
    assert train["strains"] == 12 and train["ids"].shape == (12, 3) and train["chunk"] == 36
    for i, r in enumerate(runs):
        want = E.train_ids(r.run_seed, 0, 3, 500, 1000)
        assert (train["ids"][i * 6:(i + 1) * 6] == want).all()
    assert train["seed"] == 7


def test_a_run_does_not_depend_on_its_batch_mates(spec):
    """Seeded by run, not by batch position: run 1 alone and run 1 beside run 0 evolve identically."""
    both = _evolve(spec, _runs((0.5, 0.0)), FakeRollout())
    alone = _evolve(spec, [E.RunSpec(1, 1001, 0.0)], FakeRollout())
    assert [x["best_sha256"] for x in both[1].log] == [x["best_sha256"] for x in alone[0].log]
    assert [c["sha256"] for c in both[1].checkpoints] == [c["sha256"] for c in alone[0].checkpoints]


def test_runs_in_a_batch_need_distinct_seeds(spec):
    with pytest.raises(ValueError):
        _evolve(spec, [E.RunSpec(0, 5, 0.0), E.RunSpec(1, 5, 0.0)], FakeRollout())


def test_checkpoints_fall_on_generation_zero_every_k_and_the_last(spec):
    recs = _evolve(spec, _runs(), FakeRollout(), generations=5, every=2)
    for rec in recs:
        assert [c["generation"] for c in rec.checkpoints] == [0, 2, 4]
        assert len(rec.candidates) == 3 and all(c.n_strains == 1 for c in rec.candidates)
    recs = _evolve(spec, _runs(), FakeRollout(), generations=6, every=4)
    assert [c["generation"] for c in recs[0].checkpoints] == [0, 4, 5]


def test_the_champion_is_the_first_best_validation_checkpoint():
    rec = E.RunRecord(E.RunSpec(0, 1, 0.0))
    rec.checkpoints = [{"validation_mean": v} for v in (0.1, 0.9, 0.3, 0.9)]
    assert rec.champion_index() == 1


def test_generation_zero_is_saved_per_genome_and_world(spec):
    recs = _evolve(spec, _runs(), FakeRollout(), generations=2, every=1)
    g0 = recs[0].generation0
    assert np.array(g0["counts"]).shape == (6, 3) and np.array(g0["progress"]).shape == (6, 3)
    assert len(g0["train_ids"]) == 3


def test_validation_scores_the_raw_count(spec):
    """A shaped run's validation mean is the count alone: the fake's progress is nonzero."""
    recs = _evolve(spec, _runs((0.9,)), FakeRollout(), generations=1, every=1)
    v = recs[0].checkpoints[0]["validation_mean"]
    assert v in (0.0, 1.0)


def test_the_check_runs_before_every_rollout(spec):
    fake, n = FakeRollout(), []
    E.evolve_batch(_cfg(), None, spec, _runs(), generations=3, checkpoint_every=2, validation_ids=np.arange(4),
                   world_seed=7, id_base=500, id_span=1000, rollout_fn=fake, check=lambda: n.append(1))
    assert len(n) == len(fake.calls) == 3 + 2


def test_a_non_finite_score_stops_the_batch(spec):
    def bad(cfg, iface, genome, ids, world_seed, device, chunk_worlds=None):
        s = np.full(np.asarray(ids).shape, np.nan, dtype=np.float32)
        return SimpleNamespace(score=s, progress=np.zeros_like(s))

    with pytest.raises(FloatingPointError):
        _evolve(spec, _runs(), bad)


def test_the_initial_population_does_not_depend_on_the_device_argument(spec):
    a = E.initial_population(spec, Config().brain, 3, 4, "cpu")
    b = E.initial_population(spec, Config().brain, 3, 4, torch.device("cpu"))
    assert all(torch.equal(x, y) for x, y in zip(a.params().values(), b.params().values()) if x is not None)
    assert E.init_seed(3) != E.breed_seed(3)


def test_a_non_finite_validation_count_stops_the_batch(spec):
    good = FakeRollout()

    def bad_validation(cfg, iface, genome, ids, world_seed, device, chunk_worlds=None):
        r = good(cfg, iface, genome, ids, world_seed, device, chunk_worlds)
        if np.asarray(ids).ndim == 1:  # the checkpoint's shared validation ids
            r.score = np.full_like(r.score, np.nan)
        return r

    with pytest.raises(FloatingPointError, match="validation"):
        _evolve(spec, _runs(), bad_validation, generations=2, every=1)


# ------------------------------------------------------------------ E3b-1's hooks (PREREGISTRATION §5, §12 tests 3-4)

class Recorder(FakeRollout):
    """Also keeps every training rollout's genome, so a snapshot can be compared with what was evaluated."""

    def __init__(self):
        super().__init__()
        self.genomes = []

    def __call__(self, cfg, iface, genome, ids, world_seed, device, chunk_worlds=None):
        if np.asarray(ids).ndim == 2:
            self.genomes.append(genome.clone())
        return super().__call__(cfg, iface, genome, ids, world_seed, device, chunk_worlds)


def test_the_snapshot_is_the_population_evaluated_at_its_index_before_breeding(spec):
    fake = Recorder()
    recs = E.evolve_batch(_cfg(), None, spec, _runs(), generations=5, checkpoint_every=2, validation_ids=np.arange(4),
                          world_seed=7, id_base=500, id_span=1000, rollout_fn=fake, snapshot_at=(2,))
    P = _cfg().evo.population
    evaluated = fake.genomes[2]  # generation index 2's training rollout: both runs' populations, stacked
    for i, rec in enumerate(recs):
        snap = rec.snapshots[2]
        assert snap.n_strains == P
        assert all(torch.equal(a, b) for a, b in zip(snap.params().values(),
                                                       evaluated.select(list(range(i * P, (i + 1) * P))).params().values())
                   if a is not None)
    assert set(recs[0].snapshots) == {2}


def test_the_snapshot_hook_changes_nothing_else(spec):
    a = _evolve(spec, _runs(), FakeRollout())
    b = E.evolve_batch(_cfg(), None, spec, _runs(), generations=5, checkpoint_every=2, validation_ids=np.arange(4),
                       world_seed=7, id_base=500, id_span=1000, rollout_fn=FakeRollout(), snapshot_at=(1, 3))
    for x, y in zip(a, b):
        assert [g["best_sha256"] for g in x.log] == [g["best_sha256"] for g in y.log]
        assert all(torch.equal(p, q) for p, q in zip(x.final.params().values(), y.final.params().values()) if p is not None)
        assert x.checkpoints == y.checkpoints


def test_a_non_finite_score_names_its_runs(spec):
    good = FakeRollout()
    P = _cfg().evo.population

    def bad_run_1(cfg, iface, genome, ids, world_seed, device, chunk_worlds=None):
        r = good(cfg, iface, genome, ids, world_seed, device, chunk_worlds)
        if np.asarray(ids).ndim == 2:
            r.score = r.score.copy()
            r.score[P + 2] = np.nan  # a strain of the second run
        return r

    with pytest.raises(FloatingPointError) as err:
        _evolve(spec, _runs(), bad_run_1)
    assert err.value.runs == [1]
    assert "run 1" in str(err.value)


def test_a_non_finite_validation_count_names_its_runs(spec):
    good = FakeRollout()

    def bad_validation_run_1(cfg, iface, genome, ids, world_seed, device, chunk_worlds=None):
        r = good(cfg, iface, genome, ids, world_seed, device, chunk_worlds)
        if np.asarray(ids).ndim == 1:
            r.score = r.score.astype(float)
            r.score[1, 0] = np.nan
        return r

    with pytest.raises(FloatingPointError) as err:
        _evolve(spec, _runs(), bad_validation_run_1, generations=2, every=1)
    assert err.value.runs == [1] and "run 1" in str(err.value)


def test_fractional_counts_are_kept_and_whole_ones_stay_integers(spec):
    good = FakeRollout()

    def eighths(cfg, iface, genome, ids, world_seed, device, chunk_worlds=None):
        r = good(cfg, iface, genome, ids, world_seed, device, chunk_worlds)
        r.score = r.score.astype(float) + 0.125
        return r

    recs = _evolve(spec, _runs(), eighths, generations=2, every=1)
    assert any(x % 1 == 0.125 for x in recs[0].checkpoints[0]["validation_counts"])
    assert any(x % 1 == 0.125 for row in recs[0].generation0["counts"] for x in row)
    plain = _evolve(spec, _runs(), FakeRollout(), generations=2, every=1)
    assert all(isinstance(x, int) for x in plain[0].checkpoints[0]["validation_counts"])
