"""E2's batched loops for random sampling and the ES (`wormwars/e2/loops.py`), with a fake simulator
whose score is a known function of the genome and the world."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e04a.evolve import RunSpec, train_ids
from wormwars.e2 import loops as L
from wormwars.evo.genomes import genome_hash


@pytest.fixture(scope="module")
def spec():
    return BrainSpec.from_connectome(load_connectome())


def _cfg(population=6, worlds=3):
    c = Config()
    c.evo.population, c.evo.worlds_per_strain = population, worlds
    return c


class Fake:
    """score = 10 × mean bias + (world id % 3) / 10, the same for every world of a strain up to that
    offset; `flat=True` scores everything 0. Records calls."""

    def __init__(self, flat=False, nan_at=None):
        self.flat, self.nan_at, self.calls = flat, nan_at, []

    def __call__(self, cfg, iface, genome, ids, world_seed, device, chunk_worlds=None):
        ids = np.asarray(ids)
        self.calls.append({"strains": genome.n_strains, "ids": ids.copy(), "chunk": chunk_worlds})
        b = genome.bias.mean(dim=1).cpu().numpy()
        s = 10 * b[:, None] + (ids % 3) / 10.0  # ids are [worlds] or [strains, worlds]
        if self.flat:
            s = np.zeros_like(s)
        if self.nan_at is not None and len(self.calls) == self.nan_at:
            s = s * np.nan
        return SimpleNamespace(score=s.astype(np.float32))


def _runs(n=2):
    return [RunSpec(run=i, run_seed=500 + i, shaping=0.0) for i in range(n)]


KW = dict(checkpoint_every=2, validation_ids=np.arange(4), world_seed=7, id_base=100, id_span=1000)


# ------------------------------------------------------------------ random sampling

def test_random_sampling_plays_each_runs_own_worlds_in_one_batch(spec):
    fake = Fake()
    L.random_batch(_cfg(), None, spec, _runs(), generations=1, rollout_fn=fake, **KW)
    c = fake.calls[0]
    assert c["strains"] == 12 and c["ids"].shape == (12, 3) and c["chunk"] == 36
    for i, r in enumerate(_runs()):
        assert (c["ids"][i * 6:(i + 1) * 6] == train_ids(r.run_seed, 0, 3, 100, 1000)).all()


def test_random_sampling_nominates_the_best_since_the_last_checkpoint(spec):
    fake = Fake()
    recs = L.random_batch(_cfg(), None, spec, _runs(1), generations=5, rollout_fn=fake, **KW)
    rec = recs[0]
    # the candidate at each checkpoint is the best training score of the generations since the last one
    bests = [x["best_fitness"] for x in rec.log]
    assert [c["generation"] for c in rec.checkpoints] == [0, 2, 4]
    assert rec.checkpoints[1]["training_score"] == pytest.approx(max(bests[1:3]))
    assert rec.checkpoints[2]["training_score"] == pytest.approx(max(bests[3:5]))


def test_random_sampling_is_seeded_by_run_not_batch_position(spec):
    both = L.random_batch(_cfg(), None, spec, _runs(2), generations=3, rollout_fn=Fake(), **KW)
    alone = L.random_batch(_cfg(), None, spec, [RunSpec(1, 501, 0.0)], generations=3, rollout_fn=Fake(), **KW)
    assert [c["sha256"] for c in both[1].checkpoints] == [c["sha256"] for c in alone[0].checkpoints]


# ------------------------------------------------------------------ the ES

def _es(spec, fake, generations=5, runs=None, **kw):
    return L.es_batch(_cfg(), None, spec, runs or _runs(1), generations=generations, sigma=1.0, lr=0.3,
                      rollout_fn=fake, **{**KW, **kw})


def test_the_es_starts_from_the_best_of_its_start_screen(spec):
    fake = Fake()
    recs, states = _es(spec, fake, generations=1)
    rec = recs[0]
    assert rec.log[0]["generation"] == 0 and rec.checkpoints[0]["generation"] == 0
    assert rec.start["score"] == pytest.approx(rec.log[0]["best_fitness"])
    assert rec.checkpoints[0]["training_score"] == pytest.approx(rec.start["score"])


def test_the_es_climbs_on_the_fake_score(spec):
    recs, _ = _es(spec, Fake(), generations=30)
    v = [c["validation_mean"] for c in recs[0].checkpoints]
    assert v[-1] > v[0]


def test_a_flat_run_leaves_the_mean_exactly_at_the_start(spec):
    """No update and no projection on flat generations: the mean stays the start genome's encoding."""
    recs, states = _es(spec, Fake(flat=True), generations=6)
    rec = recs[0]
    assert rec.flat_generations == 5 and rec.first_non_flat is None
    assert states[0]["t"] == 0
    np.testing.assert_array_equal(states[0]["mean"], states[0]["start_mean"])


def test_resuming_from_a_saved_state_continues_the_same_run(spec):
    whole, _ = _es(spec, Fake(), generations=9)
    first, states = _es(spec, Fake(), generations=5)
    rest, _ = L.es_batch(_cfg(), None, spec, _runs(1), generations=9, sigma=1.0, lr=0.3, rollout_fn=Fake(),
                         resume=states, **KW)
    assert [c["sha256"] for c in whole[0].checkpoints if c["generation"] >= 5] == \
           [c["sha256"] for c in rest[0].checkpoints]
    assert rest[0].log[0]["generation"] == 5


def test_the_es_checkpoints_on_the_common_schedule(spec):
    recs, _ = _es(spec, Fake(), generations=6)
    assert [c["generation"] for c in recs[0].checkpoints] == [0, 2, 4, 5]


def test_the_es_is_seeded_by_run_not_batch_position(spec):
    both, _ = _es(spec, Fake(), generations=4, runs=_runs(2))
    alone, _ = _es(spec, Fake(), generations=4, runs=[RunSpec(1, 501, 0.0)])
    assert [c["sha256"] for c in both[1].checkpoints] == [c["sha256"] for c in alone[0].checkpoints]


@pytest.mark.parametrize("method", ["random", "es"])
def test_a_non_finite_score_stops_the_batch(spec, method):
    fake = Fake(nan_at=3)  # a training call after the first checkpoint
    with pytest.raises(FloatingPointError):
        if method == "random":
            L.random_batch(_cfg(), None, spec, _runs(), generations=3, rollout_fn=fake, **KW)
        else:
            _es(spec, fake, generations=3)


def test_the_es_records_clipping_and_candidate_hashes(spec):
    recs, _ = _es(spec, Fake(), generations=3)
    assert all("clip_share" in x for x in recs[0].log[1:])
    assert all(len(c["sha256"]) == 64 for c in recs[0].checkpoints)


def test_every_method_starts_from_the_gas_generation_0_population(spec):
    """Paired starts: for one run seed, random sampling's first draw, the ES's start screen and the GA's
    initial population are the same genomes on the same worlds."""
    from wormwars.e04a.evolve import initial_population
    ga0 = initial_population(spec, _cfg().brain, 500, 6, "cpu")
    for method in ("random", "es"):
        fake = Fake()
        if method == "random":
            L.random_batch(_cfg(), None, spec, _runs(1), generations=1, rollout_fn=fake, **KW)
        else:
            _es(spec, fake, generations=1)
        first = fake.calls[0]
        assert (first["ids"] == train_ids(500, 0, 3, 100, 1000)).all()
    recs = L.random_batch(_cfg(), None, spec, _runs(1), generations=1, rollout_fn=Fake(), **KW)
    assert recs[0].log[0]["best_sha256"] == genome_hash(ga0, int(np.argmax(ga0.bias.mean(dim=1).numpy())))
    es, _ = _es(spec, Fake(), generations=1)
    assert es[0].start["sha256"] == recs[0].log[0]["best_sha256"]


def test_the_pilot_pairs_settings_on_one_seed_in_one_batch(spec):
    """The pilot's settings share run seeds (the same start screen, worlds and noise), each run with
    its own σ and learning rate; a run in a batch alone gives the same result."""
    runs = [RunSpec(0, 700, 0.0), RunSpec(1, 700, 0.0)]
    both, _ = L.es_batch(_cfg(), None, spec, runs, generations=4, sigma=[0.5, 2.0], lr=[0.15, 0.6], rollout_fn=Fake(),
                         **KW)
    alone, _ = L.es_batch(_cfg(), None, spec, [RunSpec(1, 700, 0.0)], generations=4, sigma=2.0, lr=0.6,
                          rollout_fn=Fake(), **KW)
    assert both[0].start["sha256"] == both[1].start["sha256"]
    assert [c["sha256"] for c in both[1].checkpoints] == [c["sha256"] for c in alone[0].checkpoints]
    assert [c["sha256"] for c in both[0].checkpoints][1:] != [c["sha256"] for c in both[1].checkpoints][1:]


def test_a_repeated_seed_needs_a_different_setting(spec):
    runs = [RunSpec(0, 700, 0.0), RunSpec(1, 700, 0.0)]
    with pytest.raises(ValueError):
        L.es_batch(_cfg(), None, spec, runs, generations=2, sigma=1.0, lr=0.3, rollout_fn=Fake(), **KW)
    with pytest.raises(ValueError):
        L.random_batch(_cfg(), None, spec, runs, generations=1, rollout_fn=Fake(), **KW)
