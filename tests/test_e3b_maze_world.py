"""E3b-0's maze world (docs/E3/E3b-0-PLAN.md §1a-§1e).

The maze shuttle: a colony of weys in a tree maze, two sources A and B at dead ends, each wey with its
own goal (starting at A) that switches at its own confirmed visit; supercover movement with per-axis
sliding; linear per-wey trails (deposit d0·exp(−λt) onto the trail of the source last visited, flux
diffusion, evaporation); occluded noses; crowding and every BODY reading off.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import torch

from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e1 import controllers as C
from wormwars.e3 import maze as M
from wormwars.e3 import maze_world as MW
from wormwars.evo.rollout import rollout_brain
from wormwars.fields import sample_bilinear
from wormwars.interface import load_interface
from wormwars import world as W
from wormwars.world import World

C5 = dict(c=5, horizon=40, colony=2, mu=0.01, lam=0.03, delta=0.15, d0=0.571)


@pytest.fixture(scope="module")
def iface():
    return load_interface(load_connectome())


def _world(iface, ids, cfg=None, policy=None, run_seed=7, **kw):
    cfg = cfg or MW.maze_config(**C5)
    brain = C.scripted(iface, policy or C.ConstantMotion(0.0, 0.0), cfg)
    strain_of = torch.zeros(len(ids), 1, dtype=torch.long)
    return MW.MazeWorld(cfg, iface, brain, strain_of, run_seed=run_seed, world_ids=np.asarray(ids), **kw)


def _block_centre(cell):
    x, y = M.cell_centre(cell)
    return torch.tensor([x, y], dtype=torch.float32)


# ------------------------------------------------------------------ the configuration

def test_the_builder_sets_the_maze_task_with_crowding_off():
    cfg = MW.maze_config(**C5)
    w = cfg.world
    assert w.task == "maze_shuttle" and w.max_ticks == 40 and w.n_swarms == 1 and w.weys_per_swarm == 2
    assert w.maze_cells == 5 and w.min_side == 21 and w.maze_spawns == 4 and w.maze_sliding is True
    assert (w.maze_trail_mu, w.maze_trail_lambda, w.maze_trail_delta, w.maze_trail_d0) == (0.01, 0.03, 0.15, 0.571)
    assert (w.maze_scent_sigma, w.maze_scent_reach, w.maze_trail_access) == (3.0, 9, "shared")
    assert w.crowd_resist == 0.0 and w.crowd_push == 0.0
    assert w.shuttle_cue_ticks == 5 and w.sense_scale_food == 0.35
    assert w.metabolic_drain == 0.0 and w.move_cost == 0.0


def test_unset_maze_fields_leave_every_earlier_config_serialised_as_before():
    d = Config().to_dict()["world"]
    assert not any(k.startswith("maze_") for k in d)
    cfg = MW.maze_config(**C5)
    assert Config.from_dict(cfg.to_dict()).to_dict() == cfg.to_dict()


def test_the_plain_world_refuses_the_maze_task(iface):
    cfg = MW.maze_config(**C5)
    brain = C.scripted(iface, C.ConstantMotion(0.0, 0.0), cfg)
    with pytest.raises(ValueError, match="MazeWorld"):
        World(cfg, iface, brain, torch.zeros(1, 1, dtype=torch.long), run_seed=7, world_ids=np.arange(1))


# ------------------------------------------------------------------ the maze and the placements

def test_walls_and_placements_come_from_maze_for(iface):
    ids = np.arange(6)
    world = _world(iface, ids, episodes=np.array([0, 0, 3, 3, 1000, 1000]))
    assert world.side == 21
    for w, mid in enumerate(ids):
        mz, pl = M.maze_for(run_seed=7, maze_id=int(mid), episode=int(world.episodes[w]), c=5)
        assert np.array_equal(world.fields[w, world.ch.WALL].numpy() > 0, mz.wall)
        assert world.placements[w] == pl
        for b in range(2):  # round-robin at the spawn cells' centres
            assert torch.equal(world.pos[w, 0, b], _block_centre(pl.spawns[b % len(pl.spawns)]))


def test_the_episode_moves_the_placement_never_the_walls(iface):
    a = _world(iface, np.arange(4), episodes=np.zeros(4, dtype=np.int64))
    b = _world(iface, np.arange(4), episodes=np.full(4, 1000))
    assert torch.equal(a.fields[:, a.ch.WALL], b.fields[:, b.ch.WALL])
    assert any(a.placements[w] != b.placements[w] for w in range(4))
    assert not torch.equal(a.heading, b.heading)


# ------------------------------------------------------------------ movement

def _wall(rows):
    return torch.tensor([[ch == "#" for ch in r] for r in rows]).unsqueeze(0)


def test_the_supercover_check_catches_a_diagonal_squeeze_between_two_walls():
    wall = _wall(["....",
                  ".#..",
                  "..#.",
                  "...."])
    p0 = torch.tensor([[[1.6, 2.3]]], dtype=torch.float64)  # open cell (x 1, y 2)
    p1 = torch.tensor([[[2.3, 1.6]]], dtype=torch.float64)  # open cell (x 2, y 1), across the shared corner (2, 2)
    open_ = torch.tensor([[[0.5, 0.5]]], dtype=torch.float64), torch.tensor([[[3.5, 0.5]]], dtype=torch.float64)
    assert bool(MW.segment_hits(wall, p0, p1)[0, 0])
    assert not bool(MW.segment_hits(wall, *open_)[0, 0])
    inside = torch.tensor([[[1.5, 1.5]]], dtype=torch.float64)
    assert bool(MW.segment_hits(wall, torch.tensor([[[0.5, 1.5]]], dtype=torch.float64), inside)[0, 0])


def test_the_supercover_check_catches_a_single_corner_clip():
    wall = _wall(["...",
                  ".#.",
                  "..."])
    p0 = torch.tensor([[[0.9, 1.2]]], dtype=torch.float64)  # open, left of the wall cell
    p1 = torch.tensor([[[1.2, 0.9]]], dtype=torch.float64)  # open, above it; the segment clips its corner
    assert bool(MW.segment_hits(wall, p0, p1)[0, 0])


@pytest.mark.parametrize("sliding", [True, False])
def test_a_random_colony_never_enters_or_crosses_a_wall(iface, sliding):
    cfg = MW.maze_config(**{**C5, "colony": 8, "horizon": 300}, sliding=sliding)
    world = _world(iface, np.arange(8), cfg=cfg, policy=C.PersistentRandomWalk(1.0, 1.0, 0.5, seed=3))
    wall = world.fields[:, world.ch.WALL] > 0
    for _ in range(300):
        before = world.pos.clone()
        world.tick()
        after = world.pos
        seg = MW.segment_hits(wall, before[:, 0].double(), after[:, 0].double())
        assert not bool(seg.any())
        ix, iy = after[..., 0].floor().long(), after[..., 1].floor().long()
        assert not bool(wall[torch.arange(8).view(-1, 1, 1), iy, ix].any())


def test_a_diagonal_step_into_a_wall_slides_along_it(iface):
    for sliding, expect_x in ((True, True), (False, False)):
        cfg = MW.maze_config(**C5, sliding=sliding)
        world = _world(iface, np.arange(1), cfg=cfg)
        wall = world.fields[0, world.ch.WALL] > 0
        # the top-left maze cell's block spans x, y in [1, 4); row 0 is the outer wall
        start = torch.tensor([2.0, 1.2])
        world.pos[0, 0, :] = start
        proposed = start + torch.tensor([0.25, -0.25])
        new = world._resolve_move(proposed.view(1, 1, 1, 2).expand(1, 1, 2, 2).clone())[0, 0, 0]
        assert not bool(wall[int(new[1]), int(new[0])])
        if expect_x:
            assert torch.allclose(new, torch.tensor([2.25, 1.2]))
        else:
            assert torch.equal(new, start)


# ------------------------------------------------------------------ the trails

def test_flux_diffusion_conserves_mass_and_keeps_walls_empty():
    mz, _ = M.maze_for(run_seed=1, maze_id=0, episode=0, c=5)
    open_ = torch.from_numpy(~mz.wall).float()
    g = torch.Generator().manual_seed(0)
    x = torch.rand(3, 2, *open_.shape, generator=g, dtype=torch.float64) * open_
    total = x.sum()
    for _ in range(50):
        x = MW.diffuse(x, open_.double(), 0.15)
    assert abs(float(x.sum() - total)) < 1e-9 * float(total)
    assert float((x * (1 - open_)).abs().max()) == 0.0


def test_flux_diffusion_flattens_a_closed_corridor():
    wall = torch.ones(5, 9, dtype=torch.bool)
    wall[1:4, 1:8] = False  # one 3-wide closed corridor
    open_ = (~wall).double()
    x = torch.zeros(1, 5, 9, dtype=torch.float64)
    x[0, 2, 1] = 21.0
    for _ in range(4000):
        x = MW.diffuse(x, open_, 0.15)
    inside = x[0][~wall]
    assert float(inside.max() - inside.min()) < 1e-6 and abs(float(inside.mean()) - 1.0) < 1e-9


def test_per_wey_trails_sum_to_a_single_field_fed_every_deposit():
    mz, _ = M.maze_for(run_seed=1, maze_id=2, episode=0, c=6)
    open_ = torch.from_numpy(~mz.wall).float()
    free = np.argwhere(~mz.wall)
    rng = np.random.default_rng(0)
    per = torch.zeros(8, 2, *open_.shape)
    one = torch.zeros(1, 2, *open_.shape)
    for _ in range(300):
        for b in range(8):
            y, x = free[rng.integers(len(free))]
            s, amt = int(rng.integers(2)), float(rng.uniform(0, 1))
            per[b, s, y, x] += amt
            one[0, s, y, x] += amt
        per = MW.diffuse(per, open_, 0.15) * (1 - 0.01)
        one = MW.diffuse(one, open_, 0.15) * (1 - 0.01)
    total = per.sum(0, keepdim=True)
    assert float((total - one).abs().max()) <= 1e-5 * float(one.abs().max())


def _teleport(world, w, b, cell):
    world.pos[w, 0, b] = _block_centre(cell)
    world._points = None


def test_a_visit_switches_that_weys_goal_and_starts_its_trail(iface):
    cfg = MW.maze_config(**C5)
    world = _world(iface, np.arange(1), cfg=cfg)
    a_cell = world.placements[0].a
    _teleport(world, 0, 1, a_cell)
    world.tick()  # wey 1 enters A, its goal; wey 0 stays at its spawn
    assert world.goal[0].tolist() == [0, 1]
    assert world.visits[0].tolist() == [0, 1]
    tr = world.trails[0]  # [weys, (A, B), H, W]
    d0, mu, lam = 0.571, 0.01, 0.03
    assert float(tr[0].abs().sum()) == 0.0 and float(tr[1, 1].abs().sum()) == 0.0
    assert abs(float(tr[1, 0].sum()) - d0 * (1 - mu)) < 1e-6  # deposit, diffuse (mass kept), evaporate
    world.tick()  # inside still: no new visit; the timer is 1
    assert world.visits[0].tolist() == [0, 1]
    tr = world.trails[0]
    assert abs(float(tr[1, 0].sum()) - (d0 * (1 - mu) + d0 * math.exp(-lam)) * (1 - mu)) < 1e-6
    assert float(tr[1, 1].abs().sum()) == 0.0


def test_entering_the_other_source_is_an_entry_not_a_visit(iface):
    world = _world(iface, np.arange(1))
    _teleport(world, 0, 0, world.placements[0].b)
    world.tick()
    assert world.visits[0].tolist() == [0, 0] and world.goal[0].tolist() == [0, 0]
    ev = world.task_events()
    assert ev["entries"][0, 0].tolist() == [0, 1]  # (A, B) raw entries
    assert float(world.trails.abs().sum()) == 0.0  # no visit behind it: no deposit


def test_the_score_is_mean_visits_per_wey(iface):
    world = _world(iface, np.arange(2))
    _teleport(world, 1, 0, world.placements[1].a)
    world.tick()
    _teleport(world, 1, 0, world.placements[1].b)
    world.tick()
    assert world.visits.tolist() == [[0, 0], [2, 0]]
    assert world.task_score().tolist() == [0.0, 1.0]
    ev = world.task_events()
    assert ev["visit_tick"][1, 0, :3].tolist() == [0, 1, -1]
    assert ev["first_b_tick"][1].tolist() == [1, -1]


def test_the_rollout_scores_the_maze_task(iface):
    cfg = MW.maze_config(**C5)
    brain = C.scripted(iface, C.ConstantMotion(1.0, 0.2), cfg)
    r = rollout_brain(cfg, iface, brain, np.arange(3), run_seed=7)
    assert r.score.shape == (1, 3) and r.events is not None and "visit_tick" in r.events
    assert np.all(r.progress == 0)


# ------------------------------------------------------------------ sensing

def test_an_unoccluded_nose_reads_bitwise_as_the_plain_bilinear_read():
    g = torch.Generator().manual_seed(1)
    field = torch.rand(1, 2, 9, 9, generator=g)
    wall = torch.zeros(1, 9, 9, dtype=torch.bool)
    wall[0, 0], wall[0, -1], wall[0, :, 0], wall[0, :, -1] = True, True, True, True
    head = torch.tensor([[[4.3, 4.6], [3.1, 5.2]]])
    nose = torch.tensor([[[4.9, 4.1], [3.7, 5.9]]])
    got = MW.occluded_bilinear(field, wall, head, nose)
    assert torch.equal(got, sample_bilinear(field, nose))


def test_a_nose_across_a_wall_reads_zero():
    field = torch.ones(1, 2, 7, 7)
    wall = torch.zeros(1, 7, 7, dtype=torch.bool)
    wall[0, :, 3] = True  # a vertical wall at x in [3, 4)
    head = torch.tensor([[[2.8, 3.5]]])
    nose = torch.tensor([[[3.4, 3.5]]])  # inside the wall
    assert float(MW.occluded_bilinear(field, wall, head, nose).abs().max()) == 0.0
    head = torch.tensor([[[2.9, 3.5]]])
    nose = torch.tensor([[[4.1, 3.5]]])  # beyond the wall, its column-4 support cells in its own view
    assert float(MW.occluded_bilinear(field, wall, head, nose).abs().max()) == 0.0


def test_a_support_cell_behind_a_corner_is_dropped_without_renormalising():
    wall = _wall([".......",
                  ".......",
                  "...#...",
                  ".......",
                  "......."])  # one wall cell, x in [3, 4), y in [2, 3)
    head = torch.tensor([[[2.3, 2.55]]])
    nose = torch.tensor([[[2.7, 2.55]]])  # support cells x 2-3, y 2-3; weights 0.76, 0.19 (x 3), 0.04, 0.01
    behind = torch.zeros(1, 1, 5, 7)
    behind[0, 0, 3, 3] = 1.0  # (3, 3): the segment from the nose to its centre clips the wall cell
    assert float(sample_bilinear(behind, nose)[0, 0, 0]) > 0
    assert float(MW.occluded_bilinear(behind, wall, head, nose)[0, 0, 0]) == 0.0
    seen = torch.zeros(1, 1, 5, 7)
    seen[0, 0, 3, 2] = 1.0  # (2, 3): straight below the nose, in view
    assert torch.equal(MW.occluded_bilinear(seen, wall, head, nose), sample_bilinear(seen, nose))
    ones = torch.ones(1, 1, 5, 7)  # every support cell at 1: the two hidden ones drop out, the rest are not rescaled
    got = float(MW.occluded_bilinear(ones, wall, head, nose)[0, 0, 0])
    assert abs(got - 0.8) < 1e-6


def _set_trails(world, values):
    """Every open cell of wey b's A trail at values[b]; B trails empty."""
    open_ = (world.fields[:, world.ch.WALL] == 0).float()
    world.trails.zero_()
    for b, v in enumerate(values):
        world.trails[:, b, 0] = v * open_


def _a_reading(world):
    world.tick()
    s = world.last_signals
    return (s["a_left"][:, 0] + s["a_right"][:, 0]) / 2  # [worlds, weys]


@pytest.mark.parametrize("mode,expect", [("shared", [3.0, 3.0]), ("own", [1.0, 2.0]), ("peers", [2.0, 1.0]),
                                         ("none", [0.0, 0.0])])
def test_the_access_modes(iface, mode, expect):
    cfg = MW.maze_config(**{**C5, "mu": 0.0, "delta": 0.0, "d0": 0.0})
    base = _world(iface, np.arange(1), cfg=cfg, access="none")
    _set_trails(base, [1.0, 2.0])
    zero = _a_reading(base)
    world = _world(iface, np.arange(1), cfg=cfg, access=mode)
    _set_trails(world, [1.0, 2.0])
    got = (_a_reading(world) - zero) / 0.35
    assert int(world.last_occluded.sum()) == 0  # at the spawn centres every support cell is open
    assert torch.allclose(got, torch.tensor(expect)[None].expand_as(got), atol=1e-5)


def test_replay_adds_the_donors_total_times_its_coefficient(iface):
    cfg = MW.maze_config(**{**C5, "mu": 0.0, "delta": 0.0, "d0": 0.0})
    ids = np.array([0, 0])
    eps = np.array([0, 1000])
    base = _world(iface, ids, cfg=cfg, episodes=eps, access=["own", "own"])
    world = _world(iface, ids, cfg=cfg, episodes=eps, access=["replay", "own"], donors=np.array([1, -1]),
                   replay_coef=np.array([0.5, 0.0]))
    for wd in (base, world):
        _set_trails(wd, [1.0, 2.0])
    got = (_a_reading(world) - _a_reading(base)) / 0.35
    assert torch.allclose(got[0], torch.full((2,), 0.5 * 3.0), atol=1e-5)
    assert torch.allclose(got[1], torch.zeros(2), atol=1e-6)


def test_scramble_permutes_the_peers_open_cells_and_keeps_their_mass(iface):
    cfg = MW.maze_config(**{**C5, "mu": 0.0, "delta": 0.0, "d0": 0.0})
    world = _world(iface, np.arange(2), cfg=cfg, access="scramble")
    g = torch.Generator().manual_seed(2)
    open_ = (world.fields[:, world.ch.WALL] == 0).float()
    world.trails[:] = torch.rand(world.trails.shape, generator=g) * open_[:, None, None]
    f = world.sensed_trails()  # [worlds, weys, 2, H, W]
    own = world.trails
    peers = world.trails.sum(1, keepdim=True) - own
    other = f - own
    assert torch.allclose(other.sum(dim=(-1, -2)), peers.sum(dim=(-1, -2)), rtol=1e-5)
    assert float((other * (1 - open_[:, None, None])).abs().max()) == 0.0
    assert not torch.allclose(other, peers)
    again = _world(iface, np.arange(2), cfg=cfg, access="scramble")
    again.trails[:] = world.trails
    assert torch.equal(again.sensed_trails(), f)


def test_collision_reads_walls_only_and_peer_channels_are_silent(iface):
    world = _world(iface, np.arange(3))
    world.tick()
    s = world.last_signals
    assert float(world.fields[:, world.ch.BODY].abs().max()) > 0  # two weys share a spawn: a body field exists
    pts = world.sample_points()  # the weys did not move: the same points as at the tick's sensing
    wall = sample_bilinear(world.fields[:, world.ch.WALL:world.ch.WALL + 1], pts)[:, 0]
    wall = wall.reshape(3, 1, 2, -1) * world.cfg.world.sense_scale_collision
    for k, p in (("collision_front", W.P_FRONT_C), ("collision_front_left", W.P_FRONT_L),
                 ("collision_front_right", W.P_FRONT_R), ("collision_rear_left", W.P_REAR_L),
                 ("collision_rear_right", W.P_REAR_R)):
        assert torch.equal(s[k], wall[..., p])
    for k in ("ally_pheromone_left", "ally_pheromone_right", "enemy_pheromone_left", "damage_left"):
        assert float(s[k].abs().max()) == 0.0


def test_the_cue_holds_at_b_for_five_ticks_for_every_wey(iface):
    world = _world(iface, np.arange(2))
    seen = []
    for _ in range(7):
        world.tick()
        seen.append(world.last_signals["at_b"][:, 0].clone())
    assert all(bool((x == 1).all()) for x in seen[:5])
    assert all(bool((x == 0).all()) for x in seen[5:])


def test_scents_follow_path_distance_and_stop_at_the_reach(iface):
    world = _world(iface, np.arange(1))
    mz = M.maze_for(run_seed=7, maze_id=0, episode=0, c=5)[0]
    pl = world.placements[0]
    d = mz.free_distance(pl.a)
    scent = world.scent[0, 0].numpy()
    expect = np.where(d <= 9, np.exp(-d ** 2 / (2 * 3.0 ** 2)), 0.0)
    expect[~np.isfinite(d)] = 0.0
    assert np.allclose(scent, expect, atol=1e-6)
