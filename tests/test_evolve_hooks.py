"""The E4s hooks in 04a's `evolve_batch`: `initial` (each run's generation-0 population) and
`mutation_scales` (per-parameter factors on the sigmas). With the defaults, or with hooks that
restate the defaults, the batch is unchanged bit for bit."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e04a import evolve as E
from wormwars.evo.genomes import genome_hash


@pytest.fixture(scope="module")
def spec():
    return BrainSpec.from_connectome(load_connectome())


def _cfg():
    c = Config()
    c.evo.population, c.evo.worlds_per_strain, c.evo.elites, c.evo.truncation = 6, 3, 1, 3
    return c


def fake(cfg, iface, genome, ids, world_seed, device, chunk_worlds=None):
    """count = the strain's mean bias above 0, as a 0/1; progress a function of the world id."""
    ids = np.asarray(ids)
    b = genome.bias.mean(dim=1).cpu().numpy()
    count = np.repeat((b > 0.0).astype(np.float32)[:, None], ids.shape[-1], axis=1)
    prog = ((ids % 7) / 7.0) if ids.ndim == 2 else np.tile((ids % 7) / 7.0, (genome.n_strains, 1))
    return SimpleNamespace(score=count, progress=prog.astype(np.float32))


RUNS = [E.RunSpec(run=0, run_seed=1000, shaping=0.5), E.RunSpec(run=1, run_seed=1001, shaping=0.0)]


def _evolve(spec, **hooks):
    return E.evolve_batch(_cfg(), None, spec, RUNS, generations=6, checkpoint_every=2, validation_ids=np.arange(4),
                          world_seed=7, id_base=500, id_span=1000, rollout_fn=fake, **hooks)


def _ones(spec):
    return {"w": torch.ones(spec.n_chem), "g": torch.ones(spec.n_gap), "tau": torch.ones(spec.n),
            "bias": torch.ones(spec.n)}


def _hashes(records):
    return [[entry["best_sha256"] for entry in r.log] for r in records] + \
           [[genome_hash(r.final, i) for i in range(r.final.n_strains)] for r in records]


def test_hooks_that_restate_the_defaults_change_nothing(spec):
    base = _hashes(_evolve(spec))
    same_init = _hashes(_evolve(spec, initial=lambda r: E.initial_population(spec, _cfg().brain, r.run_seed, 6, "cpu")))
    ones = _hashes(_evolve(spec, mutation_scales=lambda r: _ones(spec)))
    assert base == same_init == ones


def test_the_initial_hook_sets_generation_0(spec):
    seed_genome = E.initial_population(spec, _cfg().brain, 77, 1, "cpu")
    clones = lambda r: seed_genome.select([0] * 6)  # noqa: E731
    recs = _evolve(spec, initial=clones)
    for r in recs:
        assert r.log[0]["best_sha256"] == genome_hash(seed_genome, 0)


def test_the_scales_reach_every_mutation(spec):
    seed_genome = E.initial_population(spec, _cfg().brain, 78, 1, "cpu")
    pinned = _ones(spec)
    pinned["w"] = torch.zeros(spec.n_chem)  # every chemical weight pinned
    recs = _evolve(spec, initial=lambda r: seed_genome.select([0] * 6), mutation_scales=lambda r: pinned)
    for r in recs:
        assert torch.equal(r.final.w, seed_genome.w.expand_as(r.final.w))
        assert not torch.equal(r.final.bias, seed_genome.bias.expand_as(r.final.bias))  # the rest mutated


def test_an_initial_population_of_the_wrong_size_is_refused(spec):
    with pytest.raises(ValueError, match="population"):
        _evolve(spec, initial=lambda r: E.initial_population(spec, _cfg().brain, r.run_seed, 5, "cpu"))
