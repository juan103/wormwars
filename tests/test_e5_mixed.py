"""E5-1's mixed world and route cache (docs/E5/E5-1-DESIGN.md §3, §9): one world per training slot in one rollout,
each world with its own prey kind, speed and pin, checked slot by slot against the single-setting path at the same
batch composition; the route's waypoints from a cache keyed by (world seed, sequence index), checked against E5-0's
sampler, copied here verbatim.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import BrainConfig
from wormwars.connectome.loader import load_connectome
from wormwars.e5 import mixed as MX
from wormwars.e5 import settings as ST
from wormwars.e5.hunt import HuntWorld, hunt_config
from wormwars.e5.play import play
from wormwars.e5.prey import PreyBrain, PursuitBrain
from wormwars.interface import load_interface
from wormwars.world import world_seed

ROOT = Path(__file__).resolve().parents[1]
SEED = 1_529_001  # outside every E5-1 block (the formal and pilot seed is 1 520 001)
IDS = np.arange(987_000_000, 987_000_008)  # outside every E5-1 block


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def iface(con):
    return load_interface(con)


@pytest.fixture(scope="module")
def params():
    return ST.prey_params()


def _cfg(ticks=200):
    c = hunt_config()
    c.world.max_ticks = ticks
    c.world.check_ledger_every_tick = True
    return c


def _pursuit(iface, cfg, k=2.0, speed=1.0):
    return PursuitBrain(iface, 302, cfg.world.forward_gain, cfg.world.turn_gain, k=k, speed=speed)


def _single_prey(iface, cfg, st, params, n=302):
    p = params
    return PreyBrain(iface, n, cfg.world.forward_gain, cfg.world.turn_gain, st["prey"], speed=st["speed"],
                     gain=p["route"]["gain"], spacing=p["route"]["spacing"], reach=p["route"]["reach"],
                     rate=p["walk"]["rate"], persistence=p["walk"]["persistence"], wall=p["wall"])


def _same_result(a, b, cols=None):
    """Every per-world output of two `play` results, optionally on some columns only: [strains, worlds, ...]."""
    sel = (lambda x: x) if cols is None else (lambda x: x[:, cols])
    bad = []
    for k in ("captures", "bite_energy", "pin_push", "prey_wall_limited"):
        if not np.array_equal(sel(getattr(a, k)), sel(getattr(b, k))):
            bad.append(k)
    for k in a.events:
        if not np.array_equal(sel(a.events[k]), sel(b.events[k]), equal_nan=True):
            bad.append(f"ev {k}")
    return bad


# ------------------------------------------------------------------------------------------------- settings
def test_the_settings_are_e5_0s():
    spec = importlib.util.spec_from_file_location("e5_0_for_e5_1_test", ROOT / "scripts" / "e5_0.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert ST.e5_0_settings() == m.settings()
    assert tuple(ST.SPEEDS_H2) == tuple(m.REGISTERED["speeds_h2"])
    assert tuple(ST.SPEEDS_H2B) == tuple(m.REGISTERED["speeds_h2b"])
    assert ST.WALK == m.REGISTERED["walk"] and ST.ROUTE_REACH == m.REGISTERED["route"]["reach"]


def test_the_suite_and_training_mixture_follow_the_design():
    assert len(ST.SUITE) == 17 and len(set(ST.SUITE)) == 17
    # §3's order fixes the suite's world ids (985 700 000 + 512 k + i)
    assert ST.SUITE == ("H1-bite", "H2-0.2", "H2-0.4", "H2-0.6", "H2-0.8", "H2-1", "H2b-walk-0.5", "H2b-wall-0.5",
                        "H2-0.1", "H2-0.3", "H2-0.5", "H2-0.7", "H2-0.9", "H2b-walk-0.25", "H2b-walk-0.75",
                        "H2b-wall-0.25", "H2b-wall-0.75")
    assert ST.SUITE[:8] == ST.TRAINING
    assert all(ST.BY_NAME[n]["rule"] == "bite" for n in ST.SUITE)
    assert {k: len(v) for k, v in ST.STRATA.items()} == {"static": 1, "route": 10, "movers": 6}
    assert set(ST.PROBE_SETTINGS) <= set(ST.SUITE)


def test_the_weighted_fitness_is_the_scores_thirds():
    rng = np.random.default_rng(0)
    c = rng.integers(0, 9, size=(50, 8))
    want = (c[:, 0] + c[:, 1:6].mean(1) + c[:, 6:8].mean(1)) / 3
    assert np.allclose(ST.weighted_fitness(c), want, rtol=0, atol=1e-12)
    # equal weighted sums are exactly equal, whichever slots they come from
    a, b = np.zeros((1, 8)), np.zeros((1, 8))
    a[0, 0], b[0, 1:6] = 1, 1
    assert ST.weighted_fitness(a)[0] == ST.weighted_fitness(b)[0]


def test_validation_weights_follow_the_slots():
    slots = np.repeat(np.arange(8), 32)
    w = ST.column_weights(slots)
    c = np.random.default_rng(1).integers(0, 5, size=(3, 256))
    per_slot = np.stack([c[:, slots == k].mean(1) for k in range(8)], 1)
    assert np.allclose(ST.weighted_fitness(c, w), ST.weighted_fitness(per_slot), rtol=0, atol=1e-12)
    with pytest.raises(ValueError):
        ST.column_weights(np.array([0, 0, 1]))


def test_the_suite_score_is_the_mean_of_three_strata():
    means = {n: 0.0 for n in ST.SUITE}
    means["H1-bite"] = 3.0
    for n in ST.STRATA["route"]:
        means[n] = 1.0
    for n in ST.STRATA["movers"]:
        means[n] = 2.0
    assert ST.suite_score(means) == pytest.approx(2.0)
    with pytest.raises(ValueError):
        ST.suite_score({"H1-bite": 1.0})


def test_the_prey_parameters_come_from_e5_0s_records(params):
    assert params["route"] == {"gain": 2.0, "spacing": 6.0, "reach": 1.0}
    assert params["e_prey"] == pytest.approx(1.375, abs=1e-6)


# ------------------------------------------------------------------------------------------------- the pin
def test_a_per_world_pin_matches_the_single_pin(iface, params):
    """Pinned columns as in an all-pinned run, unpinned as in an unpinned one, at the same composition."""
    cfg = _cfg()
    st = ST.BY_NAME["H2-0.6"]
    mask = np.array([True, False] * 4)
    runs = {}
    for label, pin in (("mixed", mask), ("all", True), ("none", False)):
        runs[label] = play(cfg, iface, _pursuit(iface, cfg), _single_prey(iface, cfg, st, params), IDS, SEED,
                           rule="bite", prey_energy=params["e_prey"], pinned=pin)
    assert runs["all"].captures.sum() > 0
    assert _same_result(runs["mixed"], runs["all"], np.flatnonzero(mask)) == []
    assert _same_result(runs["mixed"], runs["none"], np.flatnonzero(~mask)) == []
    assert (runs["mixed"].pin_push[:, ~mask] == 0).all() and (runs["mixed"].pin_push[:, mask] > 0).any()


# ------------------------------------------------------------------------------------------------- the prey
@pytest.mark.parametrize("name", ["H1-bite", "H2-0.6", "H2b-walk-0.5", "H2b-wall-0.5"])
def test_a_mixed_prey_of_one_kind_is_the_prey(iface, params, name):
    cfg = _cfg()
    st = ST.BY_NAME[name]
    a = play(cfg, iface, _pursuit(iface, cfg), _single_prey(iface, cfg, st, params), IDS, SEED, rule="bite",
             prey_energy=params["e_prey"], pinned=st["pinned"])
    b = play(cfg, iface, _pursuit(iface, cfg), MX.prey(iface, cfg, [name] * len(IDS), params), IDS, SEED,
             rule="bite", prey_energy=params["e_prey"], pinned=st["pinned"])
    assert a.captures.sum() > 0
    assert _same_result(a, b) == []


def test_the_mixed_world_is_each_slot_alone(iface, params):
    """The 8 training slots in one world, against each slot's setting in every column, same composition: identical in
    the slot's column. A scripted pursuit and a neural hunter of 3 strains, each strain on its own worlds."""
    cfg = _cfg()
    con = load_connectome()
    hunters = [("pursuit", lambda: _pursuit(iface, cfg), IDS),
               ("neural", lambda: Brain(Genome.random(BrainSpec.from_connectome(con), BrainConfig(), 3,
                                                      generator=torch.Generator().manual_seed(5))),
                np.stack([IDS, IDS + 8, IDS + 16]))]
    for label, make, ids in hunters:
        mixed = MX.play_settings(cfg, iface, make(), list(ST.TRAINING), ids, SEED, params)
        if label == "pursuit":
            assert mixed.captures.sum() > 0
        assert mixed.ledger_rel_error < 1e-5
        for k, name in enumerate(ST.TRAINING):
            alone = MX.play_settings(cfg, iface, make(), [name] * len(ST.TRAINING), ids, SEED, params)
            assert _same_result(mixed, alone, [k]) == [], (label, name)


def test_two_dimensional_ids_equal_shared_ids(iface, params, con):
    cfg = _cfg(120)
    g = Genome.random(BrainSpec.from_connectome(con), BrainConfig(), 2, generator=torch.Generator().manual_seed(6))
    a = MX.play_settings(cfg, iface, Brain(g), list(ST.TRAINING), IDS, SEED, params)
    b = MX.play_settings(cfg, iface, Brain(g), list(ST.TRAINING), np.stack([IDS, IDS]), SEED, params)
    assert _same_result(a, b) == []


def test_play_settings_refuses_mixed_rules(iface, params):
    cfg = _cfg(10)
    with pytest.raises(ValueError, match="rule"):
        MX.play_settings(cfg, iface, _pursuit(iface, cfg), ["H1-ghost", "H1-bite"], IDS[:2], SEED, params)


# ------------------------------------------------------------------------------------------------- the route cache
def _old_route(w, i, life, spacing):
    """E5-0's `PreyBrain._route_for`, for one world and life, verbatim in its arithmetic."""
    wcfg = w.cfg.world
    lo, hi = 1.0 + wcfg.target_wall_clearance, w.side - 1.0 - wcfg.target_wall_clearance
    start = w.target_centres[i, life].cpu().numpy().astype(np.float64)
    rng = np.random.default_rng([world_seed(w.run_seed, int(w.world_ids[i])), 0x5E7B, int(life)])
    pts, prev = [start], start
    for k in range(3):
        for _try in range(10_000):
            c = rng.uniform(lo, hi, 2)
            if float(np.hypot(*(c - prev))) >= spacing and (k < 2 or float(np.hypot(*(c - start))) >= spacing):
                break
        else:
            raise ValueError("no waypoint")
        pts.append(c)
        prev = c
    return torch.as_tensor(np.array(pts), dtype=w.dtype)


def test_the_route_cache_draws_e5_0s_waypoints(iface, params):
    """Every life a route prey lived, in a world with many captures, has E5-0's waypoints; so does a later lookup of
    the same (world, life), which the cache serves."""
    cfg = _cfg(300)
    st = ST.BY_NAME["H2-0.2"]
    prey = _single_prey(iface, cfg, st, params)
    seen = []
    orig = prey._route_for

    def spy(worlds):
        orig(worlds)
        for i in np.flatnonzero(worlds.cpu().numpy()):
            seen.append((int(i), int(prey.world.life[i]), prey.waypoints[i].clone()))

    prey._route_for = spy
    hunter = _pursuit(iface, cfg)
    w = HuntWorld(cfg, iface, [hunter, prey], torch.zeros(len(IDS), 2, dtype=torch.long), run_seed=SEED,
                  world_ids=IDS, rule="bite", prey_energy=params["e_prey"], pinned=False)
    for i in range(len(IDS)):  # life 0, drawn at attach before the spy
        seen.append((i, 0, prey.waypoints[i].clone()))
    w.run()
    assert int(w.captures.sum()) >= 8
    for i, life, got in seen:
        assert torch.equal(got, _old_route(w, i, life, params["route"]["spacing"])), (i, life)
    # a cached lookup returns the same arrays
    again = [prey.routes.get(w, i, life) for i, life, _ in seen[:4]]
    for (i, life, got), arr in zip(seen[:4], again):
        assert torch.equal(torch.as_tensor(arr, dtype=w.dtype), got)
