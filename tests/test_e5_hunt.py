"""E5-0's Task H (docs/E5/E5-0-PLAN.md §2, §7): the hunt world, its ledger, its rules and its prey.

The code was written before these tests; each was seen failing under a sabotage of the behaviour it checks
(runs/e5-0/sabotage_log.txt, scripts/e5_0_sabotage.py).
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.connectome.loader import load_connectome
from wormwars.e1 import controllers as C
from wormwars.e5.hunt import HuntWorld, e1_task_n, hunt_config
from wormwars.e5.play import play
from wormwars.e5.prey import PreyBrain, PursuitBrain
from wormwars.evo.rollout import rollout_brain
from wormwars.interface import load_interface
from wormwars.world import World

IDS = np.arange(996_201_000, 996_201_008)  # E1's first gate worlds: an engine check, not a test of the navigator
SEED = 1_100_001


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def iface(con):
    return load_interface(con)


NAV = {"k": 8192.0, "speed": 1.0, "turn": 0.0}  # E1's frozen S-const (freeze.json)


def _cfgs(ticks=150):
    cn, ch = e1_task_n(), hunt_config()
    cn.world.max_ticks = ch.world.max_ticks = ticks
    return cn, ch


def _prey(iface, cfg, kind="stationary", **kw):
    return PreyBrain(iface, 302, cfg.world.forward_gain, cfg.world.turn_gain, kind, **kw)


def _pursuit(iface, cfg, **kw):
    return PursuitBrain(iface, 302, cfg.world.forward_gain, cfg.world.turn_gain, **kw)


def test_a_ghost_prey_is_task_n(iface):
    """H1-ghost reproduces Task N bit for bit: the same counts and the same capture ticks, for a scripted navigator
    and for the oracle."""
    cn, ch = _cfgs()
    for task_brain, hunt_brain in ((C.scripted(iface, C.s_const(**NAV), cn), C.scripted(iface, C.s_const(**NAV), ch)),
                                   (C.OracleBrain(iface, 302, cn.world.forward_gain, cn.world.turn_gain),
                                    _pursuit(iface, ch))):
        rn = rollout_brain(cn, iface, task_brain, IDS, SEED)
        rh = play(ch, iface, hunt_brain, _prey(iface, ch), IDS, SEED, rule="ghost")
        assert rn.score[0].sum() > 0
        assert np.array_equal(rn.score[0].astype(int), rh.captures[0])
        assert np.array_equal(rn.events["reach_tick"][0], rh.events["capture_tick"][0])
        assert np.array_equal(rn.events["path_length"][0], rh.events["hunter_path"][0])


@pytest.mark.parametrize("rule", ["reach", "bite"])
def test_the_ledger_balances_through_captures(iface, rule):
    cn, ch = _cfgs()
    ch.world.check_ledger_every_tick = True
    r = play(ch, iface, _pursuit(iface, ch), _prey(iface, ch), IDS, SEED, rule=rule, prey_energy=2.0)
    assert r.captures.sum() > 0
    assert r.ledger_rel_error < 1e-5


def _world(iface, ch, hunter, prey, **kw):
    strain_of = torch.zeros(len(IDS), 2, dtype=torch.long)
    return HuntWorld(ch, iface, [hunter, prey], strain_of, run_seed=SEED, world_ids=IDS, **kw)


def test_a_pinned_prey_never_moves_and_one_on_one_crowding_never_pushes(iface):
    """Two bodies in contact reach a body density of 2/3, below the crowding threshold of 0.8 (measured 2026-11-05),
    so a one-on-one hunt has no crowding: the pin refuses nothing, and an unpinned stationary prey stays put too."""
    _, ch = _cfgs(120)
    w = _world(iface, ch, _pursuit(iface, ch), _prey(iface, ch), rule="bite", prey_energy=1e6, pinned=True)
    start = w.pos[:, 1].clone()
    peak = 0.0
    while not w.done():
        w.tick()
        peak = max(peak, float(w.fields[:, w.ch.BODY].max()))
    assert torch.equal(w.pos[:, 1], start)
    assert float(w.ev_contact.sum()) > 0 and peak < ch.world.crowd_threshold
    assert float(w.pin_push.sum()) == 0.0
    w = _world(iface, ch, _pursuit(iface, ch), _prey(iface, ch), rule="bite", prey_energy=1e6, pinned=False)
    start = w.pos[:, 1].clone()
    w.run()
    assert torch.equal(w.pos[:, 1], start)


def test_bites_need_the_hunters_attack_and_the_prey_never_bites(iface):
    _, ch = _cfgs()
    off = play(ch, iface, _pursuit(iface, ch), _prey(iface, ch), IDS, SEED, rule="bite", prey_energy=2.0,
               hunter_attack=0.0)
    assert off.captures.sum() == 0 and off.events["damage"].sum() == 0
    w = _world(iface, ch, _pursuit(iface, ch), _prey(iface, ch), rule="bite", prey_energy=2.0)
    w.run()
    assert int(w.captures.sum()) > 0
    assert float(w.last_damage_taken[:, 0].abs().sum()) == 0.0  # the hunter took nothing, ever (no deposit)
    assert torch.all(w.energy[:, 0] >= ch.world.start_energy)  # energy off: the hunter only gains


def test_each_new_life_starts_at_least_d_minus_r_from_the_hunter(iface):
    _, ch = _cfgs(200)
    w = _world(iface, ch, _pursuit(iface, ch), _prey(iface, ch), rule="bite", prey_energy=2.0)
    D, R = ch.world.target_separation, ch.world.target_radius
    seen = 0
    while not w.done():
        before = w.life.clone()
        w.tick()
        new = w.life != before
        if bool(new.any()):
            d = (w.pos[new, 1, 0] - w.pos[new, 0, 0]).norm(dim=-1)
            assert bool((d >= D - R - 1e-5).all())
            seen += int(new.sum())
    assert seen > 0
    assert int(w.captures.sum()) == seen


def test_the_route_follower_moves_along_its_loop(iface):
    """At half speed and alone (a hunter that never moves and never reaches it), the route follower's path length per
    tick is at least 0.8 of its commanded speed, it visits its waypoints in order and closes laps, and walls refuse
    few of its moves."""
    _, ch = _cfgs(600)
    prey = _prey(iface, ch, "route", speed=0.5)
    stay = C.scripted(iface, C.ConstantMotion(0.0, 0.0), ch)
    w = _world(iface, ch, stay, prey, rule="ghost", pinned=False)
    w.hunt_events()  # the table exists before the run, too
    w.run()
    caught = w.captures > 0  # a route may pass the motionless hunter's head; those worlds' lives restart
    speed = torch.as_tensor(w.hunt_events()["prey_path"].sum(axis=1)) / 600
    assert bool((speed >= 0.8 * 0.5 * ch.world.max_speed).all())
    assert bool((prey.laps_done[~caught] >= 1).all())
    assert bool((prey.visits[~caught] >= 4).all())
    assert bool(prey.seen[~caught].all())  # every waypoint, not the start over and over
    assert int(w.prey_wall_limited.sum()) <= 0.05 * 600 * len(IDS)
    first = prey.waypoints[:, 0]
    assert torch.equal(first[~caught], w.target_centres[~caught, 0])  # the loop starts at the life's centre


def test_the_body_probe_keeps_the_bites_and_removes_the_prey_from_the_body_field(iface):
    """`prey_body=False` with the bite rule: the hunter's bites still land and capture, but the body field never holds
    the prey, so the hunter's collision inputs never see it."""
    _, ch = _cfgs()
    r = play(ch, iface, _pursuit(iface, ch), _prey(iface, ch), IDS, SEED, rule="bite", prey_energy=2.0, prey_body=False)
    assert r.captures.sum() > 0
    from wormwars.world import blur, splat
    w = _world(iface, ch, _pursuit(iface, ch), _prey(iface, ch), rule="bite", prey_energy=2.0, prey_body=False)
    for _ in range(40):
        w.tick()
        pts = w.body_points().reshape(w.n_worlds, 2, 1, 3, 2)[:, 0].reshape(w.n_worlds, -1, 2)  # the hunter's only
        dens = splat(torch.zeros(w.n_worlds, w.H, w.W), pts, torch.full((w.n_worlds, 3), ch.world.body_splat))
        assert torch.equal(w.fields[:, w.ch.BODY], blur(dens, ch.world.crowd_blur))
    with pytest.raises(ValueError, match="ghost"):
        _world(iface, ch, _pursuit(iface, ch), _prey(iface, ch), rule="ghost", prey_body=True)


def test_the_constant_probe_replaces_the_hunters_food_channels_only(iface):
    """Under `constant`, the hunter's food channels carry the tick-0 mean scent; the prey keeps its own food reading
    (zero here: no food on the map)."""
    _, ch = _cfgs(3)
    ch.world.food_probe = "constant"
    w = _world(iface, ch, _pursuit(iface, ch), _prey(iface, ch), rule="reach")
    w.tick()
    sig = w.last_signals
    for k in ("food_left", "food_right"):
        assert torch.equal(sig[k][:, 0, 0], w._food_constant * ch.world.sense_scale_food)
        assert float(sig[k][:, 0, 0].abs().min()) > 0
        assert float(sig[k][:, 1].abs().sum()) == 0.0


def test_damage_is_booked_from_combat_without_rounding(iface):
    """The event table's damage is combat's capped damage summed in float64, not a float32 energy difference: with a
    measuring energy of 1e6, a difference would round to multiples of 0.0625."""
    _, ch = _cfgs(30)
    w = _world(iface, ch, _pursuit(iface, ch), _prey(iface, ch), rule="bite", prey_energy=1e6)
    total = torch.zeros(len(IDS), dtype=torch.float64)
    while not w.done():
        w.tick()
        total += w.last_damage_taken[:, 1, 0].double()
    assert float(total.sum()) > 0
    assert torch.equal(w.ev_damage.sum(dim=1), total)


def test_the_episode_runs_to_the_horizon(iface):
    _, ch = _cfgs(60)
    r = play(ch, iface, _pursuit(iface, ch), _prey(iface, ch), IDS, SEED, rule="bite", prey_energy=0.5)
    assert r.ticks == 60


def test_the_hunt_task_needs_its_world_and_the_world_needs_its_task(iface):
    _, ch = _cfgs(5)
    with pytest.raises(ValueError, match="HuntWorld"):
        World(ch, iface, [_pursuit(iface, ch), _prey(iface, ch)], torch.zeros(2, 2, dtype=torch.long), run_seed=1)
    cn, _ = _cfgs(5)
    with pytest.raises(ValueError, match="hunt task"):
        HuntWorld(cn, iface, [_pursuit(iface, cn), _prey(iface, cn)], torch.zeros(2, 2, dtype=torch.long),
                  run_seed=1, rule="ghost")


def test_an_attack_scale_of_one_changes_nothing_in_an_existing_fight(iface):
    """The world's new attack-scale hook multiplies by exactly 1.0 when set to ones, and is skipped when None: two
    swarms of six, placed head to flank so they bite from the first tick."""
    from wormwars.config import Config
    cfg = Config()
    cfg.world.n_swarms, cfg.world.weys_per_swarm, cfg.world.max_ticks = 2, 6, 20
    out = []
    for scale in (None, torch.ones(2)):
        b = [C.scripted(iface, C.ConstantMotion(0.3, 0.0), cfg), C.scripted(iface, C.ConstantMotion(0.0, 0.0), cfg)]
        w = World(cfg, iface, b, torch.zeros(1, 2, dtype=torch.long), run_seed=5, combat_stage=1)
        for i in range(6):
            w.pos[0, 0, i] = torch.tensor([8.0, 6.0 + 3 * i])
            w.heading[0, 0, i] = 0.0
            w.pos[0, 1, i] = torch.tensor([10.0, 7.2 + 3 * i])
            w.heading[0, 1, i] = -torch.pi / 2
        w._points = None
        w._update_body_field()
        w.attack_scale = scale
        w.run()
        out.append((w.energy.clone(), w.pos.clone(), float(w.damage_points.sum())))
    assert out[0][2] > 0  # they did bite
    assert torch.equal(out[0][0], out[1][0]) and torch.equal(out[0][1], out[1][1])
