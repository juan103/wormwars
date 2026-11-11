"""E5-1's GA on Task H (docs/E5/E5-1-DESIGN.md §3, §6, §9): `evolve_batch`'s optional integer weights for the training
fitness and the validation score, and the Task H rollout (the mixed world at the training and validation shapes, the
ledger and the sequence-overflow checks on every rollout, the highest sequence index).
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import BrainConfig, Config
from wormwars.connectome.loader import load_connectome
from wormwars.e04a import evolve as EV
from wormwars.e5 import ga as GA
from wormwars.e5 import mixed as MX
from wormwars.e5 import settings as ST
from wormwars.e5.hunt import hunt_config
from wormwars.evo.genomes import genome_hash
from wormwars.evo.rollout import RolloutResult
from wormwars.interface import load_interface

SEED = 1_529_002
IDS = np.arange(987_000_100, 987_000_108)


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def iface(con):
    return load_interface(con)


# ------------------------------------------------------------------------------------------- evolve_batch's weights
TRAIN_W = np.array(ST.TRAINING_WEIGHTS)
VAL_W = ST.column_weights(np.repeat(np.arange(8), 2))  # 16 validation columns, 2 per slot


def _cfg(pop=4):
    c = Config()
    c.evo.population, c.evo.elites, c.evo.truncation, c.evo.worlds_per_strain = pop, 1, 2, 8
    return c


def _fake_rollout(kind_of):
    """Counts by strain kind: kind 0 catches 3 in slot 0 only (plain mean 0.375, weighted 1.0); kind 1 catches 1 in
    every slot but the first (plain 0.875, weighted 0.667); others nothing. A strain's kind is read from its first
    bias, which the test sets."""
    def fn(cfg, iface, genome, world_ids, world_seed, device, chunk_worlds=None):
        ids = np.asarray(world_ids)
        S, W = genome.n_strains, ids.shape[-1]
        out = np.zeros((S, W))
        for s in range(S):
            k = kind_of(genome, s)
            if k == 0:
                out[s, :W // 8] = 3  # the first slot's columns
            elif k == 1:
                out[s, W // 8:] = 1
        return RolloutResult(score=out, energy=out, alive=out, eaten=out, ticks=1, ledger_error=0.0,
                             progress=np.zeros_like(out))
    return fn


def _kind(genome, s):
    b = float(genome.bias[s, 0])
    return 0 if b > 100 else 1 if b > 50 else 2


def _initial(spec, bcfg, pop):
    def init(r):
        g = Genome.random(spec, bcfg, pop, generator=torch.Generator().manual_seed(r.run_seed))
        bias = g.bias.clone()
        bias[0, 0], bias[1, 0] = 0.0, 60.0  # strain 1 is kind 1 (plain mean best)
        bias[2, 0] = 200.0  # strain 2 is kind 0 (weighted best)
        return g.with_params(bias=bias)
    return init


def _small_spec():
    from wormwars.connectome.loader import Connectome
    n = 4
    chem = np.zeros((n, n), np.float32)
    chem[0, 1] = chem[1, 2] = 1.0
    gap = np.zeros((n, n), np.float32)
    gap[2, 3] = gap[3, 2] = 1.0
    return BrainSpec.from_connectome(Connectome(tuple("ABCD"), ("inter",) * 4, chem, gap, "em_sections", {}, "toy"))


def test_weights_drive_selection_and_the_validation_score():
    cfg = _cfg()
    cfg.brain.b_max = 1000.0  # so the kind markers survive the clamp
    spec = _small_spec()
    runs = [EV.RunSpec(0, 11, 0.0)]
    common = dict(generations=2, checkpoint_every=1, validation_ids=np.arange(16), world_seed=1, id_base=0,
                  id_span=100, rollout_fn=_fake_rollout(_kind), initial=_initial(spec, cfg.brain, 4))
    plain = EV.evolve_batch(cfg, None, spec, runs, **common)[0]
    weighted = EV.evolve_batch(cfg, None, spec, runs, weights=(TRAIN_W, VAL_W), **common)[0]
    assert plain.log[0]["best_fitness"] == pytest.approx(0.875)
    assert weighted.log[0]["best_fitness"] == pytest.approx(1.0)
    # the checkpoint's candidate is the weighted best, and its validation score is weighted; the raw counts are kept
    c = weighted.checkpoints[0]
    assert c["validation_mean"] == pytest.approx(1.0)
    assert c["validation_counts"] == [3, 3] + [0] * 14
    assert c["sha256"] == genome_hash(_initial(spec, cfg.brain, 4)(runs[0]), 2)
    # breeding used the weighted fitness: the elite is the weighted best
    assert _kind(weighted.candidates[1], 0) == 0
    assert _kind(plain.candidates[1], 0) == 1


def test_weights_need_unshaped_runs_and_matching_columns():
    cfg = _cfg()
    spec = _small_spec()
    common = dict(generations=1, checkpoint_every=1, validation_ids=np.arange(16), world_seed=1, id_base=0,
                  id_span=100, rollout_fn=_fake_rollout(_kind))
    with pytest.raises(ValueError, match="unshaped"):
        EV.evolve_batch(cfg, None, spec, [EV.RunSpec(0, 1, 0.5)], weights=(TRAIN_W, VAL_W), **common)
    with pytest.raises(ValueError, match="weights"):
        EV.evolve_batch(cfg, None, spec, [EV.RunSpec(0, 1, 0.0)], weights=(TRAIN_W[:7], VAL_W), **common)
    with pytest.raises(ValueError, match="weights"):
        EV.evolve_batch(cfg, None, spec, [EV.RunSpec(0, 1, 0.0)], weights=(TRAIN_W, VAL_W[:15]), **common)


# ------------------------------------------------------------------------------------------- the Task H rollout
def _hcfg(ticks=120):
    c = hunt_config()
    c.world.max_ticks = ticks
    return c


def test_the_rollout_is_play_settings_with_the_slot_layouts(con, iface):
    cfg = _hcfg()
    params = ST.prey_params()
    g = Genome.random(BrainSpec.from_connectome(con), BrainConfig(), 2, generator=torch.Generator().manual_seed(4))
    roll = GA.TaskHRollout(params, prey_iface=iface, validation_per_slot=2)
    ids = np.stack([IDS, IDS + 8])
    r = roll(cfg, iface, g, ids, SEED, "cpu", chunk_worlds=16)
    ref = MX.play_settings(cfg, iface, GA.Brain(g), list(ST.TRAINING), ids, SEED, params, prey_iface=iface)
    assert np.array_equal(r.score, ref.captures.astype(np.float64))
    assert (r.progress == 0).all()
    v_ids = np.arange(987_000_200, 987_000_216)
    v = roll(cfg, iface, g, v_ids, SEED, "cpu", chunk_worlds=32)
    ref = MX.play_settings(cfg, iface, GA.Brain(g), [ST.TRAINING[k] for k in np.repeat(np.arange(8), 2)], v_ids, SEED,
                           params, prey_iface=iface)
    assert np.array_equal(v.score, ref.captures.astype(np.float64))
    assert roll.rollouts == 2 and roll.max_index >= 0


def test_the_rollout_refuses_other_shapes_and_split_chunks(con, iface):
    cfg = _hcfg(5)
    g = Genome.random(BrainSpec.from_connectome(con), BrainConfig(), 2, generator=torch.Generator().manual_seed(4))
    roll = GA.TaskHRollout(ST.prey_params(), prey_iface=iface, validation_per_slot=2)
    with pytest.raises(ValueError, match="columns"):
        roll(cfg, iface, g, np.arange(987_000_300, 987_000_305), SEED, "cpu")
    with pytest.raises(ValueError, match="one world"):
        roll(cfg, iface, g, np.stack([IDS, IDS]), SEED, "cpu", chunk_worlds=8)


def test_the_rollout_stops_on_sequence_overflow_and_on_the_ledger(iface):
    """A pursuit hunter on a sequence of 2 centres exhausts it; a ledger tolerance below zero always trips."""
    cfg = _hcfg(300)
    cfg.world.target_sequence_length = 2
    params = ST.prey_params()
    pursuit = lambda genome: GA.pursuit_hunter(iface, cfg, genome.n_strains)  # noqa: E731
    g = Genome.random(BrainSpec.from_connectome(load_connectome()), BrainConfig(), 1,
                      generator=torch.Generator().manual_seed(1))
    with pytest.raises(GA.SequenceOverflow):
        GA.TaskHRollout(params, prey_iface=iface, validation_per_slot=2, make_hunter=pursuit)(
            cfg, iface, g, IDS, SEED, "cpu")
    cfg = _hcfg(30)
    with pytest.raises(GA.LedgerError):
        GA.TaskHRollout(params, prey_iface=iface, validation_per_slot=2, ledger_tol=-1.0, make_hunter=pursuit)(
            cfg, iface, g, IDS, SEED, "cpu")


class _NaNHunter:
    """A hunter whose state turns non-finite after a few ticks (a NaN brain state must stop the batch, §6)."""

    def __init__(self, inner, after=5):
        self._b, self.after, self.t = inner, after, 0

    def __getattr__(self, name):
        return getattr(self._b, name)

    def step(self, v, current):
        out = self._b.step(v, current)
        self.t += 1
        return out * float("nan") if self.t > self.after else out


def test_a_non_finite_state_stops_the_rollout(iface):
    cfg = _hcfg(30)
    params = ST.prey_params()
    g = Genome.random(BrainSpec.from_connectome(load_connectome()), BrainConfig(), 1,
                      generator=torch.Generator().manual_seed(1))
    with pytest.raises(FloatingPointError, match="non-finite"):
        MX.play_settings(cfg, iface, _NaNHunter(GA.Brain(g)), list(ST.TRAINING), IDS, SEED, params, prey_iface=iface)
    roll = GA.TaskHRollout(params, prey_iface=iface, validation_per_slot=2,
                           make_hunter=lambda genome: _NaNHunter(GA.Brain(genome)))
    with pytest.raises(FloatingPointError, match="non-finite"):
        roll(cfg, iface, g, IDS, SEED, "cpu")
