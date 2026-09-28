"""E1's Task N (docs/E1/DESIGN.md v2.1): a sensing-only moving target, energy off, one wey.

The design's targeted tests: target sequencing and pairing, score selection, ledger balance with
energy off, deterministic replay of counts and events, and batch and chunk invariance. Plus the
config builder (padding on, D092), the target field's shape, the probes, and the controls'
collision access.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e1 import controllers as C
from wormwars.e1.task import GATE_IDS, HOLDOUT_04A_IDS, PILOT_IDS, TUNING_IDS, task_n_config
from wormwars.evo import rollout
from wormwars.evo.rollout import rollout_brain
from wormwars.interface import load_interface
from wormwars.world import World


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def iface(con):
    return load_interface(con)


@pytest.fixture(scope="module")
def spec(con):
    return BrainSpec.from_connectome(con)


def _cfg(**kw):
    return task_n_config(sigma=3.0, amplitude=1.0, radius=1.5, separation=8.0, horizon=kw.pop("horizon", 120), **kw)


def _world(cfg, iface, spec, ids, run_seed=5, strains=1):
    g = Genome.random(spec, cfg.brain, strains, generator=torch.Generator().manual_seed(0))
    from wormwars.brain import Brain
    strain_of = torch.arange(strains).repeat_interleave(len(ids)).reshape(-1, 1)
    return World(cfg, iface, Brain(g), strain_of, run_seed=run_seed, world_ids=np.tile(ids, strains))


# ------------------------------------------------------------------ the config builder

def test_the_builder_sets_task_n_and_keeps_padding_on():
    """E1 must not be built on grid.task_config, which pins padding off (D092)."""
    cfg = _cfg()
    w = cfg.world
    assert w.task == "navigate" and w.n_swarms == 1 and w.weys_per_swarm == 1 and w.max_ticks == 120
    assert (w.metabolic_drain, w.move_cost, w.eat_rate) == (0.0, 0.0, 0.0)
    assert cfg.map.food_patches == (0, 0) and cfg.map.hazard_patches == (0, 0)
    assert w.pheromone_deposit == 0.0 and w.sense_scale_pheromone == 0.0
    assert cfg.brain.pad_single_strain is True
    assert (w.target_sigma, w.target_amplitude, w.target_radius, w.target_separation) == (3.0, 1.0, 1.5, 8.0)


def test_the_id_ranges_are_disjoint():
    sets = [set(PILOT_IDS.tolist()), set(TUNING_IDS.tolist()), set(GATE_IDS.tolist()), set(HOLDOUT_04A_IDS.tolist())]
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            assert not sets[i] & sets[j]


def test_navigate_refuses_more_than_one_wey(iface, spec):
    cfg = _cfg()
    cfg.world.weys_per_swarm = 2
    with pytest.raises(ValueError):
        _world(cfg, iface, spec, np.arange(2))


def test_a_blur_that_does_not_fit_the_wall_clearance_is_refused(iface, spec):
    cfg = _cfg()
    cfg.world.target_radius = 3.5  # R above the 3-cell clearance
    with pytest.raises(ValueError):
        _world(cfg, iface, spec, np.arange(2))


# ------------------------------------------------------------------ the target sequence

def test_the_sequence_is_a_function_of_run_seed_and_world_id_only(iface, spec):
    cfg = _cfg()
    a = _world(cfg, iface, spec, np.array([3, 7, 11]))
    b = _world(cfg, iface, spec, np.array([11, 3]), strains=2)  # other batch, other composition
    ca, cb = a.target_centres.numpy(), b.target_centres.numpy()
    np.testing.assert_array_equal(ca[0], cb[1])  # world 3
    np.testing.assert_array_equal(ca[2], cb[0])  # world 11
    np.testing.assert_array_equal(cb[0], cb[2])  # both strains on world 11 face the same targets
    assert not np.array_equal(ca[0], ca[1])
    c = _world(cfg, iface, spec, np.array([3]), run_seed=6)
    assert not np.array_equal(c.target_centres.numpy()[0], ca[0])


def test_the_sequence_respects_the_geometry(iface, spec):
    cfg = _cfg()
    w = _world(cfg, iface, spec, np.arange(40))
    c = w.target_centres.numpy()
    lo, hi = 1 + cfg.world.target_wall_clearance, w.side - 1 - cfg.world.target_wall_clearance
    assert c.min() >= lo - 1e-6 and c.max() <= hi + 1e-6
    step = np.linalg.norm(np.diff(c, axis=1), axis=-1)
    assert step.min() >= cfg.world.target_separation - 1e-6
    spawn = w.pos[:, 0, 0].numpy()
    assert np.linalg.norm(c[:, 0] - spawn, axis=-1).min() >= cfg.world.target_separation - 1e-6


def test_adding_the_target_does_not_change_the_map_draws(iface, spec):
    """The target stream is separate: spawn positions and headings are those of the same world
    without a target."""
    cfg = _cfg()
    plain = dataclasses.replace(cfg.world, task="forage")
    cfg2 = cfg.copy()
    cfg2.world = plain
    a, b = _world(cfg, iface, spec, np.arange(5)), _world(cfg2, iface, spec, np.arange(5))
    assert torch.equal(a.pos, b.pos) and torch.equal(a.heading, b.heading)


# ------------------------------------------------------------------ the scent

def test_the_scent_is_sensing_only_and_a_truncated_gaussian(iface, spec):
    cfg = _cfg()
    w = _world(cfg, iface, spec, np.arange(3))
    assert float(w.fields[:, w.ch.FOOD].abs().sum()) == 0.0  # never written into FOOD
    f = w.target_field()
    cx, cy = w.target_centres[0, 0].tolist()
    yy, xx = np.mgrid[0:w.H, 0:w.W] + 0.5
    reach = int(np.ceil(3 * cfg.world.target_sigma))
    outside = (np.abs(xx - cx) > reach) | (np.abs(yy - cy) > reach)
    assert float(f[0][torch.from_numpy(outside)].abs().max()) == 0.0
    assert float(f[0].max()) <= cfg.world.target_amplitude + 1e-6
    assert float(f[0].max()) > 0.5 * cfg.world.target_amplitude


def test_the_constant_probe_senses_the_arena_mean_of_the_starting_scent(iface, spec):
    cfg = _cfg()
    cfg.world.food_probe = "constant"
    w = _world(cfg, iface, spec, np.arange(2))
    np.testing.assert_allclose(w._food_constant.numpy(), w.target_field().mean(dim=(1, 2)).numpy(), rtol=1e-6)


# ------------------------------------------------------------------ reaching, events, energy

def _oracle_run(cfg, iface, ids, run_seed=5, ticks=None):
    brain = C.OracleBrain(iface, 302, cfg.world.forward_gain, cfg.world.turn_gain, k=2.0, speed=1.0)
    return rollout_brain(cfg, iface, brain, ids, run_seed, "cpu", ticks=ticks)


def test_the_oracle_reaches_several_targets_and_the_score_is_the_count(iface):
    cfg = _cfg(horizon=200)
    r = _oracle_run(cfg, iface, np.arange(6))
    assert r.score.dtype == np.float32
    assert np.all(r.score >= 2)
    ev = r.events
    reached = (ev["reach_tick"] >= 0).sum(axis=-1)
    np.testing.assert_array_equal(reached, r.score)


def test_events_are_consistent(iface):
    cfg = _cfg(horizon=200)
    ev = _oracle_run(cfg, iface, np.arange(4)).events
    act, reach, path = ev["activation_tick"], ev["reach_tick"], ev["path_length"]
    for w in range(act.shape[1]):
        k_done = int((reach[0, w] >= 0).sum())
        assert act[0, w, 0] == 0
        for k in range(k_done):
            assert reach[0, w, k] >= act[0, w, k]
            assert act[0, w, k + 1] == reach[0, w, k] + 1  # the next leg starts on the next tick
            assert path[0, w, k] > 0
        assert reach[0, w, k_done] == -1  # the unfinished leg is kept, unreached
        assert np.all(act[0, w, k_done + 1:] == -1)
    assert ev["target_x"].shape == ev["target_y"].shape == act.shape


def test_energy_is_off_and_the_ledger_stays_balanced_across_relocations(iface):
    cfg = _cfg(horizon=200)
    cfg.world.check_ledger_every_tick = True
    r = _oracle_run(cfg, iface, np.arange(4))
    assert np.all(r.score >= 2)  # relocations happened
    assert r.ledger_rel_error == 0.0
    np.testing.assert_array_equal(r.energy, np.full_like(r.energy, cfg.world.start_energy))
    np.testing.assert_array_equal(r.alive, np.ones_like(r.alive))


def test_counts_and_events_replay_exactly_and_do_not_depend_on_chunking(iface, spec):
    cfg = _cfg(horizon=80)
    g = Genome.random(spec, cfg.brain, 3, generator=torch.Generator().manual_seed(4))
    ids = np.arange(5)
    a = rollout(cfg, iface, g, ids, 5, "cpu", chunk_worlds=15)
    b = rollout(cfg, iface, g, ids, 5, "cpu", chunk_worlds=15)
    c = rollout(cfg, iface, g, ids, 5, "cpu", chunk_worlds=5)  # one strain per chunk (padded)
    np.testing.assert_array_equal(a.score, b.score)
    np.testing.assert_array_equal(a.score, c.score)
    for k in a.events:
        np.testing.assert_array_equal(a.events[k], b.events[k])
        np.testing.assert_array_equal(a.events[k], c.events[k])


def test_the_mirrored_probe_reads_the_reflected_scent(iface, spec):
    cfg = _cfg()
    cfg.world.food_probe = "mirrored"
    w = _world(cfg, iface, spec, np.arange(2))
    pts = w.sample_points()
    sensed = w._sensed_food(pts)
    x, y = pts[..., 0], pts[..., 1]
    from wormwars.fields import sample_bilinear
    refl = torch.stack((w.W - 1 - x, w.H - 1 - y), dim=-1)
    direct = sample_bilinear(w.target_field().unsqueeze(1).contiguous(), refl)[:, 0].reshape(sensed.shape)
    torch.testing.assert_close(sensed, direct)


# ------------------------------------------------------------------ controls

def test_scripted_controls_get_the_collision_readings(iface):
    seen = {}

    class Probe(C.ConstantMotion):
        needs_collision = True

        def __call__(self, left, right, state, collision=None):
            seen.update(collision)
            return super().__call__(left, right, state)
    cfg = _cfg(horizon=5)
    brain = C.scripted(iface, Probe(speed=0.5, turn=0.0), cfg)
    rollout_brain(cfg, iface, brain, np.arange(2), 5, "cpu")
    assert set(seen) == {"front", "front_left", "front_right", "rear_left", "rear_right"}
    assert all(v.shape == seen["front"].shape for v in seen.values())


def test_s_const_is_stereo_kinesis_at_one_speed():
    p = C.s_const(k=4.0, speed=0.6, turn=0.1)
    left, right = torch.tensor([[0.3]]), torch.tensor([[0.1]])
    fwd, turn, _ = p(left, right, None)
    assert float(fwd) == pytest.approx(0.6)
    assert float(turn) == pytest.approx(min(1.0, 0.1 + 4.0 * 0.2))


def test_a_wall_follower_turns_away_from_a_wall_ahead():
    p = C.WallFollower(speed=0.5, seek_turn=-0.2, avoid_turn=0.8, threshold=0.5)
    z = torch.zeros(1, 1)
    near = {"front": torch.ones(1, 1), "front_left": z, "front_right": torch.ones(1, 1),
            "rear_left": z, "rear_right": z}
    far = {k: z for k in near}
    _, t_near, _ = p(z, z, None, collision=near)
    _, t_far, _ = p(z, z, None, collision=far)
    assert float(t_near) == pytest.approx(0.8) and float(t_far) == pytest.approx(-0.2)


def test_the_random_walk_is_reproducible_and_persistent():
    a, b = C.PersistentRandomWalk(speed=0.5, rate=0.8, persistence=0.9, seed=3), \
        C.PersistentRandomWalk(speed=0.5, rate=0.8, persistence=0.9, seed=3)
    sa, sb = a.init(1, 4), b.init(1, 4)
    z = torch.zeros(1, 4)
    for _ in range(5):
        _, ta, sa = a(z, z, sa)
        _, tb, sb = b(z, z, sb)
        assert torch.equal(ta, tb)
