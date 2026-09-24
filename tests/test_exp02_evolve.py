"""Checkpoints on their own suite, and snapshots that let an 80-generation run stand in for a
40-generation one."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo.evolve import evolve
from wormwars.interface import load_interface

import importlib

evolve_mod = importlib.import_module("wormwars.evo.evolve")  # the package re-exports the function under this name


@pytest.fixture(scope="module")
def small():
    con = load_connectome()
    cfg = Config()
    cfg.world.max_ticks = 40
    cfg.evo.population = 6
    cfg.evo.elites = 1
    cfg.evo.truncation = 3
    cfg.evo.worlds_per_strain = 2
    cfg.evo.holdout_worlds = 2
    return cfg, load_interface(con), BrainSpec.from_connectome(con)


def test_checkpoints_use_the_given_suite(small, monkeypatch):
    cfg, iface, spec = small
    cfg = cfg.copy()
    cfg.evo.generations = 3
    seen = []
    orig = evolve_mod.evaluate_on

    def spy(cfg_, iface_, genome, ids, *a, **k):
        seen.append(tuple(np.asarray(ids)))
        return orig(cfg_, iface_, genome, ids, *a, **k)

    monkeypatch.setattr(evolve_mod, "evaluate_on", spy)
    suite = np.array([123456789, 123456790])
    evolve(cfg, iface, spec, 0, 7, holdout_every=1, checkpoint_ids=suite, verbose=False)
    assert tuple(suite) in seen


def test_a_checkpoint_is_taken_at_every_snapshot_generation(small):
    cfg, iface, spec = small
    cfg = cfg.copy()
    cfg.evo.generations = 5
    r = evolve(cfg, iface, spec, 0, 7, holdout_every=10, snapshots=(3,), verbose=False)
    gens = [x.generation for x in r.log if x.holdout_best is not None]
    assert 3 in gens, gens


def test_snapshot_of_the_last_generation_is_the_champion(small):
    cfg, iface, spec = small
    cfg = cfg.copy()
    cfg.evo.generations = 3
    r = evolve(cfg, iface, spec, 0, 7, snapshots=(0, 2), verbose=False)
    assert set(r.snapshots) == {0, 2}
    assert torch.equal(r.snapshots[2].w, r.champion.w)


def test_a_longer_run_reproduces_the_shorter_one_up_to_its_length(small):
    cfg, iface, spec = small
    short, long_ = cfg.copy(), cfg.copy()
    short.evo.generations, long_.evo.generations = 2, 4
    a = evolve(short, iface, spec, 0, 9, verbose=False)
    b = evolve(long_, iface, spec, 0, 9, snapshots=(1,), verbose=False)
    assert torch.equal(a.champion.w, b.snapshots[1].w)
