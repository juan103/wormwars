"""E3a's shuttle task (experiments/E3-ab-organism/E3a/PREREGISTRATION.md §3; tests 1-4).

One wey, two fixed sources A and B per world. The goal starts at A; an entry into the current goal is
a confirmed visit and switches the goal; an entry into the other source changes nothing. The visit
levels `at_a`/`at_b` are sensed one tick after the movement that put the head inside, and `at_b` is
held at 1 for the first 5 ticks (the start cue), which never enters the ledger.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import torch

from wormwars.connectome import load_connectome
from wormwars.e1 import controllers as C
from wormwars.e3.task import SHUTTLE_SOURCES_STREAM, shuttle_config
from wormwars.evo.rollout import rollout_brain
from wormwars.interface import load_interface
from wormwars.world import World


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def iface(con):
    return load_interface(con)


def _world(iface, ids, cfg=None, speed=0.0, turn=0.0, run_seed=7):
    cfg = cfg or shuttle_config(horizon=60)
    brain = C.scripted(iface, C.ConstantMotion(speed, turn), cfg)
    strain_of = torch.zeros(len(ids), 1, dtype=torch.long)
    return World(cfg, iface, brain, strain_of, run_seed=run_seed, world_ids=np.asarray(ids))


# ------------------------------------------------------------------ the builder and the geometry

def test_the_builder_sets_the_shuttle_on_task_n():
    cfg = shuttle_config()
    w = cfg.world
    assert w.task == "shuttle" and w.max_ticks == 600 and w.n_swarms == 1 and w.weys_per_swarm == 1
    assert (w.target_sigma, w.target_amplitude, w.target_radius, w.target_wall_clearance) == (6.0, 1.0, 1.5, 3.0)
    assert (w.shuttle_separation_min, w.shuttle_separation_max) == (8.0, 14.0)
    assert (w.shuttle_spawn_min, w.shuttle_spawn_max, w.shuttle_cue_ticks) == (6.0, 16.0, 5)
    assert cfg.brain.substeps == 32 and cfg.brain.pad_single_strain is True
    assert w.sense_scale_food == 0.35


def test_every_world_meets_the_geometry_rule(iface):
    world = _world(iface, np.arange(200))
    src = world.shuttle_sources.numpy().astype(np.float64)  # [worlds, 2, 2]
    spawn = world.pos[:, 0, 0].numpy().astype(np.float64)
    a, b = src[:, 0], src[:, 1]
    dab = np.hypot(*(a - b).T)
    assert np.all((dab >= 8.0) & (dab <= 14.0))
    for s in (a, b):
        d = np.hypot(*(s - spawn).T)
        assert np.all((d >= 6.0) & (d <= 16.0))
        assert np.all((s >= 4.0) & (s <= 20.0))


def test_the_sources_depend_only_on_run_seed_and_world_id(iface):
    one = _world(iface, [11, 12, 13]).shuttle_sources
    again = _world(iface, [13, 11]).shuttle_sources
    assert torch.equal(one[2], again[0]) and torch.equal(one[0], again[1])
    other = _world(iface, [11], run_seed=8).shuttle_sources
    assert not torch.equal(one[0], other[0])
    assert SHUTTLE_SOURCES_STREAM != 0x5CE27  # its own stream, not Task N's


# ------------------------------------------------------------------ events

def _put(world, xy):
    world.pos[:, 0, 0] = torch.as_tensor(xy, dtype=world.pos.dtype)
    world._points = None


def test_entries_confirmed_visits_and_the_goal(iface):
    world = _world(iface, [3])
    a, b = world.shuttle_sources[0, 0].clone(), world.shuttle_sources[0, 1].clone()
    far = (a + b) / 2 + torch.tensor([0.0, 0.0])
    # into B first: an entry, but B is not the goal, so nothing is counted or switched
    _put(world, b); world.tick()
    assert int(world.shuttle_visits[0]) == 0 and int(world.shuttle_goal[0]) == 0
    _put(world, far); world.tick()
    _put(world, a); world.tick()  # into A: a confirmed visit; the goal switches to B
    assert int(world.shuttle_visits[0]) == 1 and int(world.shuttle_goal[0]) == 1
    world.tick()  # still inside A: not an entry
    assert int(world.shuttle_visits[0]) == 1
    _put(world, b); world.tick()
    assert int(world.shuttle_visits[0]) == 2 and int(world.shuttle_goal[0]) == 0
    _put(world, b + torch.tensor([0.5, 0.0])); world.tick()  # still inside B
    _put(world, far); world.tick()
    _put(world, b); world.tick()  # back into B: an entry, but the goal is A
    assert int(world.shuttle_visits[0]) == 2
    ev = world.shuttle_events()
    entries_a = ev["entry_a"][0][ev["entry_a"][0] >= 0]
    entries_b = ev["entry_b"][0][ev["entry_b"][0] >= 0]
    assert entries_a.tolist() == [2] and entries_b.tolist() == [0, 4, 7]
    assert ev["visit_tick"][0][ev["visit_tick"][0] >= 0].tolist() == [2, 4]
    assert ev["goal"][0][:8].tolist() == [0, 0, 0, 1, 1, 0, 0, 0]


def test_the_levels_are_sensed_a_tick_later_and_the_cue_holds_b_for_five_ticks(iface):
    world = _world(iface, [3])
    a = world.shuttle_sources[0, 0].clone()
    seen = []
    for t in range(8):
        if t == 6:
            _put(world, a)
        world.tick()
        s = world.last_signals
        seen.append((float(s["at_a"].reshape(-1)[0]), float(s["at_b"].reshape(-1)[0])))
    assert seen[:5] == [(0.0, 1.0)] * 5  # the cue
    assert seen[5] == (0.0, 0.0) and seen[6] == (0.0, 0.0)  # inside after tick 6's movement ...
    assert seen[7] == (1.0, 0.0)  # ... sensed at tick 7
    ev = world.shuttle_events()
    assert ev["entry_b"][0][0] == -1  # the cue is not an event


def test_the_scents_are_bilateral_scaled_and_follow_the_goal(iface):
    world = _world(iface, [3])
    a = world.shuttle_sources[0, 0]
    _put(world, a + torch.tensor([2.0, 0.0]))
    world.tick()
    s = {k: float(v.reshape(-1)[0]) for k, v in world.last_signals.items()}
    assert 0 < s["a_left"] <= 0.35 and 0 < s["a_right"] <= 0.35
    assert s["goal_left"] == s["a_left"] and s["goal_right"] == s["a_right"]
    assert s["food_left"] == 0.0 and s["food_right"] == 0.0  # no food, and no scent in the food channel
    peak = 0.35 * math.exp(-0.0)
    assert s["a_left"] < peak


def test_the_ledger_dtypes(iface):
    world = _world(iface, [3, 4])
    world.run(10)
    ev = world.shuttle_events()
    assert ev["goal"].dtype == np.int8
    for k in ("entry_a", "entry_b", "visit_tick"):
        assert ev[k].dtype == np.int64
    assert ev["path_length"].dtype == np.float64
    assert world.shuttle_visits.dtype == torch.int64


def test_the_rollout_scores_confirmed_visits(iface):
    cfg = shuttle_config(horizon=60)
    brain = C.scripted(iface, C.ConstantMotion(1.0, 0.1), cfg)
    res = rollout_brain(cfg, iface, brain, np.arange(4), run_seed=7)
    world = _world(iface, np.arange(4), cfg=cfg, speed=1.0, turn=0.1)
    world.run()
    assert np.array_equal(res.score.reshape(-1), world.shuttle_visits.numpy().astype(np.float32))
    assert res.events is not None and "visit_tick" in res.events


def test_other_tasks_do_not_build_the_shuttle(iface):
    from wormwars.e1.task import task_n_config
    cfg = task_n_config(sigma=6.0, amplitude=1.0, radius=1.5, separation=8.0, horizon=10)
    world = _world(iface, [1], cfg=cfg)
    world.tick()
    assert not world.shuttle and "a_left" not in world.last_signals


# ------------------------------------------------------------------ earlier configurations unchanged

def test_earlier_configurations_serialise_exactly_as_before():
    """The shuttle's settings are unset (None) by default and left out of `to_dict` while unset, so
    every earlier configuration keeps its hash (E1's gate record, E2's and E4s's guards)."""
    import hashlib
    import json
    from pathlib import Path
    from wormwars.config import Config
    from wormwars.e1.task import task_n_config
    assert not any(k.startswith("shuttle_") for k in Config().to_dict()["world"])
    assert not any(k.startswith("shuttle_") for k in task_n_config(sigma=6.0, amplitude=1.0, radius=1.5,
                                                                   separation=8.0).to_dict()["world"])
    assert shuttle_config().to_dict()["world"]["shuttle_spawn_max"] == 16.0
    gate = json.loads((Path(__file__).resolve().parents[1] / "experiments" / "E1-navigation" / "gate.json")
                      .read_text(encoding="utf-8"))["resolved_config"]
    from wormwars.e1 import task as E1  # noqa: F401
    import importlib.util
    spec = importlib.util.spec_from_file_location("e04a_for_test", Path(__file__).resolve().parents[1] / "scripts" / "e04a.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    cfg = m.E1.config(m.REGISTERED["sigma"])
    assert hashlib.sha256(json.dumps(gate, sort_keys=True).encode()).hexdigest() == m.config_sha256(cfg)
    assert shuttle_config().copy().to_dict() == shuttle_config().to_dict()


def test_the_shuttle_refuses_unset_settings(iface):
    from wormwars.e1.task import task_n_config
    cfg = task_n_config(sigma=6.0, amplitude=1.0, radius=1.5, separation=8.0, horizon=10)
    cfg.world.task = "shuttle"
    with pytest.raises(ValueError):
        _world(iface, [1], cfg=cfg)


def test_the_ledger_records_each_visits_level_duration(iface):
    """For calibration (§5): the number of consecutive ticks inside the visited source from each
    confirmed visit's tick; -2 where the episode ends first (censored)."""
    world = _world(iface, [3], cfg=shuttle_config(horizon=12))
    a, b = world.shuttle_sources[0, 0].clone(), world.shuttle_sources[0, 1].clone()
    far = (a + b) / 2
    for t in range(12):
        _put(world, a if t in (1, 2, 3) else b if t >= 9 else far)
        world.tick()
    ev = world.shuttle_events()
    assert ev["visit_tick"][0][:2].tolist() == [1, 9]
    assert ev["visit_level_ticks"][0][:2].tolist() == [3, -2]
    assert ev["visit_level_ticks"].dtype == np.int64
