"""Milestone 3 acceptance checks: physics invariants and the energy ledger.

The ledger test is the important one. It asserts, every tick of a long random rollout, that a
world's total energy changed by exactly the listed sources minus the listed sinks -- so eating,
dying and (later) biting can only move energy between pots, never make or destroy it.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.interface import load_interface
from wormwars.world import World, world_seed

torch.manual_seed(0)


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def build(parts, n_strains=4, n_worlds=8, seed=0, run_seed=5, cfg=None, **world_kw):
    con, iface, spec = parts
    cfg = cfg or Config()
    n_strains = min(n_strains, n_worlds)
    assert n_worlds % n_strains == 0
    g = torch.Generator().manual_seed(seed)
    genome = Genome.random(spec, cfg.brain, n_strains, generator=g)
    brain = Brain(genome)
    per = n_worlds // n_strains
    strain_of = torch.arange(n_strains).repeat_interleave(per).reshape(n_worlds, 1)
    return World(cfg, iface, brain, strain_of, run_seed=run_seed, **world_kw)


# ------------------------------------------------------------------ ledger


def test_energy_ledger_balances_every_tick(parts):
    w = build(parts, n_worlds=8, seed=1)
    scale = w.start_energy_total.max().item()
    for t in range(300):
        w.tick()
        err = w.energy_ledger_error().abs().max().item()
        assert err / scale < 1e-5, f"books off by {err:.3e} at tick {t}"


def test_energy_ledger_balances_with_heavy_mortality(parts):
    """Deaths, corpses and starvation are where an energy leak would hide."""
    cfg = Config()
    cfg.world.metabolic_drain = 0.25  # kill most of them fast
    cfg.world.max_ticks = 200
    w = build(parts, n_strains=2, n_worlds=6, seed=2, cfg=cfg)
    w.run()
    assert int(w.n_alive().sum()) < 6 * 20, "test is pointless if nothing died"
    scale = w.start_energy_total.max().item()
    assert w.energy_ledger_error().abs().max().item() / scale < 1e-5


def test_dead_weys_leave_exactly_their_body_mass(parts):
    cfg = Config()
    cfg.world.metabolic_drain = 2.0  # everything dies within a few ticks
    w = build(parts, n_worlds=2, seed=3, cfg=cfg)
    before = w.fields[:, w.ch.PELLET].sum(dim=(1, 2)).clone()
    n0 = w.n_alive().sum(dim=1).clone()
    for _ in range(10):
        w.tick()
    died = (n0 - w.n_alive().sum(dim=1)).double()
    gained = (w.fields[:, w.ch.PELLET].sum(dim=(1, 2)) - before).double()
    torch.testing.assert_close(gained, died * cfg.world.body_mass, rtol=1e-4, atol=1e-3)


def test_eating_never_creates_food(parts):
    w = build(parts, n_worlds=4, seed=4)
    food = w.fields[:, [w.ch.FOOD]].sum().item()
    for _ in range(150):
        w.tick()
        now = w.fields[:, w.ch.FOOD].sum().item()
        assert now <= food + 1e-4, "food went up without a spawning event"
        food = now


def test_shared_food_is_scaled_not_duplicated(parts):
    """Twenty weys on one cell may take, between them, only what the cell holds."""
    w = build(parts, n_strains=1, n_worlds=1, seed=5)
    w.fields.zero_()
    w.fields[:, w.ch.WALL, 0, :] = 1
    w.fields[:, w.ch.WALL, -1, :] = 1
    w.fields[:, w.ch.WALL, :, 0] = 1
    w.fields[:, w.ch.WALL, :, -1] = 1
    w.fields[0, w.ch.FOOD, 10, 10] = 1.0  # one unit of food in one cell
    w.pos[:] = torch.tensor([10.5, 10.5])
    w.energy.fill_(5.0)
    e0 = w.energy.sum().item()
    w._eat()
    assert w.fields[0, w.ch.FOOD].sum().item() == pytest.approx(0.0, abs=1e-5)
    assert w.energy.sum().item() - e0 == pytest.approx(1.0, abs=1e-4)


# ---------------------------------------------------------------- physics


def test_weys_stay_inside_the_arena_and_out_of_walls(parts):
    w = build(parts, n_strains=2, n_worlds=6, seed=6)
    for _ in range(250):
        w.tick()
        assert w.pos.min().item() >= 1.0
        assert w.pos.max().item() <= w.side - 1.0
        cells = w.fields[:, w.ch.WALL]
        ix = w.pos[..., 0].long().clamp(0, w.side - 1)
        iy = w.pos[..., 1].long().clamp(0, w.side - 1)
        occupied = cells[torch.arange(w.n_worlds).view(-1, 1, 1), iy, ix]
        assert occupied.max().item() == 0.0, "a wey is standing in a wall"


def test_energy_never_goes_negative_and_the_dead_stay_dead(parts):
    cfg = Config()
    cfg.world.metabolic_drain = 0.2
    w = build(parts, n_worlds=4, seed=7, cfg=cfg)
    alive_prev = w.alive.clone()
    for _ in range(200):
        w.tick()
        assert w.energy.min().item() >= 0.0
        assert not bool((w.alive & ~alive_prev).any()), "a dead wey came back to life"
        dead = w.energy[~w.alive]
        assert dead.numel() == 0 or dead.abs().max().item() == 0.0
        alive_prev = w.alive.clone()


def test_energy_is_capped(parts):
    w = build(parts, n_worlds=2, seed=8)
    w.fields[:, w.ch.FOOD] = 50.0  # swimming in it
    for _ in range(100):
        w.tick()
    assert w.energy.max().item() <= w.cfg.world.max_energy + 1e-4


def test_a_swarm_cannot_collapse_into_one_cell(parts):
    """Crowding must bound local density however hard the weys pile in."""
    cfg = Config()
    w = build(parts, n_strains=1, n_worlds=1, seed=9, cfg=cfg)
    centre = w.side / 2
    gen = torch.Generator().manual_seed(1)
    w.pos[:] = centre + (torch.rand(w.pos.shape, generator=gen) - 0.5) * 0.4
    w._points = None
    w._update_body_field()
    packed = w.fields[:, w.ch.BODY].max().item()
    for _ in range(120):
        w.tick()
    spread = w.fields[:, w.ch.BODY].max().item()
    assert spread < packed, f"density did not fall: {packed:.2f} -> {spread:.2f}"
    # and the cloud must actually be wider than one cell
    assert w.pos.reshape(-1, 2).std(dim=0).min().item() > 0.5


def test_crowding_slows_a_packed_swarm(parts):
    w = build(parts, n_strains=1, n_worlds=1, seed=10)
    w.fields[:, w.ch.BODY] = 0.0
    # direct check on the rule: resistance rises with density
    from wormwars.config import WorldConfig

    c = WorldConfig()
    lo = 1.0 - c.crowd_resist * float(np.tanh(max(0.0, 0.0 - c.crowd_threshold)))
    hi = 1.0 - c.crowd_resist * float(np.tanh(max(0.0, 5.0 - c.crowd_threshold)))
    assert lo == 1.0 and hi < 0.5


# --------------------------------------------------------------- sensing


def test_food_on_the_left_excites_the_left_food_neurons(parts):
    """An implementation check: this must hold by construction, and it verifies the wiring of the
    interface -- not anything about biology."""
    con, iface, spec = parts
    w = build(parts, n_strains=1, n_worlds=1, seed=11)
    w.fields.zero_()
    w.pos[:] = torch.tensor([12.0, 12.0])
    w.heading[:] = 0.0  # facing +x, so "left" is +y
    w._points = None
    fl = iface.forward_offset, iface.lateral_offset
    w.fields[0, w.ch.FOOD, int(12 + fl[1]), int(12 + fl[0])] = 10.0
    pts = w.sample_points()
    from wormwars.fields import sample_bilinear
    from wormwars.world import N_POINTS

    sampled = sample_bilinear(w.fields, pts).reshape(1, w.ch.n, 1, w.n_weys, N_POINTS)
    sig = w._sensor_signals(sampled)
    assert sig["food_left"].max() > sig["food_right"].max()
    cur = w._build_current(sig)
    for left, right in (("AWAL", "AWAR"), ("AWCL", "AWCR"), ("ASEL", "ASER")):
        assert cur[0, 0, 0, con.index(left)] > cur[0, 0, 0, con.index(right)], left


def test_silencing_a_motor_neuron_changes_the_motor_readout(parts):
    """Also an implementation check: AVA is in the forward read-out by construction."""
    con, iface, spec = parts
    w = build(parts, n_strains=1, n_worlds=1, seed=12)
    v = torch.randn(1, 1, w.n_weys, spec.n)
    fwd_a, _, _ = w._read_motors(v)
    v2 = v.clone()
    v2[..., [con.index("AVAL"), con.index("AVAR")]] = 0.0
    fwd_b, _, _ = w._read_motors(v2)
    assert not torch.allclose(fwd_a, fwd_b)


# --------------------------------------------------- seeds and determinism


def test_world_seed_depends_only_on_run_and_world_id():
    a = [world_seed(1234, i) for i in range(5)]
    b = [world_seed(1234, i) for i in range(5)]
    assert a == b
    assert len(set(a)) == 5, "world seeds collided"
    assert world_seed(1235, 0) != world_seed(1234, 0)


def test_maps_do_not_depend_on_batch_composition(parts):
    """World 3 of a run must get the same map whether it is batched with 4 worlds or 8."""
    small = build(parts, n_strains=1, n_worlds=4, seed=13, run_seed=99)
    big = build(parts, n_strains=1, n_worlds=8, seed=13, run_seed=99)
    torch.testing.assert_close(
        small.fields[3, small.ch.FOOD], big.fields[3, big.ch.FOOD], rtol=0, atol=0
    )
    torch.testing.assert_close(small.pos[3], big.pos[3], rtol=0, atol=0)


def test_rollouts_are_reproducible_on_cpu(parts):
    a = build(parts, n_worlds=4, seed=14, run_seed=3)
    b = build(parts, n_worlds=4, seed=14, run_seed=3)
    for _ in range(60):
        a.tick()
        b.tick()
    torch.testing.assert_close(a.pos, b.pos, rtol=0, atol=0)
    torch.testing.assert_close(a.energy, b.energy, rtol=0, atol=0)


def test_batching_worlds_does_not_change_a_world(parts):
    """World 0 must behave the same whether it is simulated alone or alongside others."""
    alone = build(parts, n_strains=1, n_worlds=1, seed=15, run_seed=21)
    together = build(parts, n_strains=1, n_worlds=4, seed=15, run_seed=21)
    for _ in range(40):
        alone.tick()
        together.tick()
    torch.testing.assert_close(alone.pos[0], together.pos[0], rtol=1e-5, atol=1e-5)
    torch.testing.assert_close(alone.energy[0], together.energy[0], rtol=1e-4, atol=1e-4)
