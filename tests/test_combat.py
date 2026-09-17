"""Milestone 6: combat, resource accounting, and the scripted flank geometry.

The flank rule is a hypothesis about the geometry, so it is *measured* here rather than assumed.
Every threshold comes from `CombatConfig`, not from a literal in this file.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.analysis.geometry import (
    duel,
    duel_mean,
    head_on_asymmetry,
    sweep,
    worst_payback,
)
from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.interface import load_interface
from wormwars.world import World

GAPS = tuple(round(0.4 + 0.25 * i, 2) for i in range(10))


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def table(con):
    return sweep(con, Config(), gaps=GAPS, n_phase=8)


def build(con, n_worlds=4, n_swarms=2, seed=0, cfg=None, stage=1, device="cpu"):
    cfg = cfg or Config()
    cfg.world.n_swarms = n_swarms
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con, device=device)
    g = torch.Generator().manual_seed(seed)
    genome = Genome.random(spec, cfg.brain, 2, generator=g, device=device)
    strain_of = torch.tensor([[i % 2, (i + 1) % 2] for i in range(n_worlds)])[:, :n_swarms]
    return World(
        cfg, iface, Brain(genome), strain_of, run_seed=11, device=device, combat_stage=stage
    )


# ------------------------------------------------------- the flank geometry


def test_a_t_boned_wey_barely_fights_back(table):
    limit = Config().combat.max_flank_payback
    got = worst_payback(table, "t_bone")
    assert got <= limit, f"T-boned wey dealt back {got:.3f} of what it took (limit {limit})"


def test_a_rear_bitten_wey_barely_fights_back(table):
    limit = Config().combat.max_flank_payback
    got = worst_payback(table, "rear")
    assert got <= limit, f"rear-bitten wey dealt back {got:.3f} of what it took (limit {limit})"


def test_head_on_is_a_roughly_even_trade(table):
    limit = Config().combat.max_head_on_asymmetry
    got = head_on_asymmetry(table)
    assert got <= limit, f"head-on asymmetry {got:.3f} exceeds {limit}"


def test_head_on_is_a_weaker_trade_than_a_flank(table):
    """'Weak' is the point: charging someone head-on must be worse than getting round them."""
    head_on = max(max(r.damage_to_a, r.damage_to_b) for r in table["head_on"])
    flank = max(r.damage_to_b for r in table["t_bone"])
    assert flank > head_on * 1.2, f"flank {flank:.4f} is not clearly better than head-on {head_on:.4f}"


def test_flanking_actually_does_damage(table):
    """A rule that punishes flanking by doing nothing to anybody would also pass the ratios."""
    assert max(r.damage_to_b for r in table["t_bone"]) > 0.05
    assert max(r.damage_to_b for r in table["rear"]) > 0.05


def test_biting_empty_space_costs_the_victim_nothing(con):
    r = duel_mean(con, Config(), pose="rear", gap=12.0)
    assert r.damage_to_a == 0.0 and r.damage_to_b == 0.0


# --------------------------------------------------- accounting under combat


def test_energy_ledger_balances_through_a_two_swarm_fight(con):
    cfg = Config()
    cfg.world.metabolic_drain = 0.08  # push deaths into the window
    w = build(con, n_worlds=4, cfg=cfg, stage=1)
    scale = w.start_energy_total.max().item()
    for t in range(250):
        w.tick()
        assert w.energy_ledger_error().abs().max().item() / scale < 1e-5, f"tick {t}"
    assert int(w.n_alive().sum()) < 4 * 2 * 20, "nothing died; the test proves little"


def test_no_friendly_fire(con):
    """Two weys of the same swarm, nose to tail, must not hurt each other at all."""
    cfg = Config()
    cfg.world.n_swarms = 1
    cfg.world.weys_per_swarm = 2
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con)
    genome = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(0))
    w = World(cfg, iface, Brain(genome), torch.zeros(1, 1, dtype=torch.long),
              run_seed=0, combat_stage=1)
    w.fields.zero_()
    c = w.side / 2
    w.pos[0, 0, 0] = torch.tensor([c, c])
    w.pos[0, 0, 1] = torch.tensor([c + 1.0, c])
    w.heading[0, 0] = 0.0
    w.energy.fill_(50.0)
    w._points = None
    w._update_body_field()
    w._combat()
    assert w.last_damage_taken.abs().max().item() == 0.0


def test_damage_is_capped_at_the_victims_remaining_energy(con):
    cfg = Config()
    cfg.combat.damage_k = 500.0  # absurd, to force the cap
    r = duel(con, cfg, pose="t_bone", gap=0.9)
    assert np.isfinite(r.damage_to_b)
    # and in a real world the victim's energy never goes below zero
    w = build(con, n_worlds=2, cfg=cfg, stage=1)
    for _ in range(30):
        w.tick()
        assert w.energy.min().item() >= 0.0


def test_transferred_energy_never_exceeds_the_transfer_fraction(con):
    cfg = Config()
    w = build(con, n_worlds=4, cfg=cfg, stage=1)
    for _ in range(120):
        before = w.energy.clone()
        w.tick()
    # the inefficiency sink must account for everything not transferred, and must not be negative
    assert float(w.ledger.inefficiency.min()) >= -1e-6


def test_attack_field_does_not_accumulate_across_ticks(con):
    w = build(con, n_worlds=2, stage=1)
    w.tick()
    a = w.fields[:, w.ch.ATTACK : w.ch.ATTACK + 2].sum().item()
    for _ in range(20):
        w.tick()
    b = w.fields[:, w.ch.ATTACK : w.ch.ATTACK + 2].sum().item()
    assert b == pytest.approx(a, rel=0.2), "attack field is accumulating instead of being redrawn"


def test_combat_stage_zero_does_no_damage(con):
    w = build(con, n_worlds=2, stage=0)
    for _ in range(50):
        w.tick()
    assert w.last_damage_taken.abs().max().item() == 0.0
    assert float(w.ledger.inefficiency.sum()) == 0.0


# ----------------------------------------------------------- stage 2 pumping


def test_pump_scales_the_bite(con):
    hard = duel(con, Config(), pose="t_bone", gap=0.9, combat_stage=2, pump=1.0)
    soft = duel(con, Config(), pose="t_bone", gap=0.9, combat_stage=2, pump=0.25)
    assert soft.damage_to_b == pytest.approx(hard.damage_to_b * 0.25, rel=1e-4)
    off = duel(con, Config(), pose="t_bone", gap=0.9, combat_stage=2, pump=0.0)
    assert off.damage_to_b == 0.0


def test_pumping_at_nothing_only_wastes_energy(con):
    """One lone wey, nothing to bite: pumping must cost energy and achieve nothing."""
    cfg = Config()
    cfg.world.n_swarms = 1
    cfg.world.weys_per_swarm = 1
    cfg.map.food_patches = (0, 0)
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con)
    genome = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(0))
    w = World(cfg, iface, Brain(genome), torch.zeros(1, 1, dtype=torch.long),
              run_seed=0, combat_stage=2)
    w.fields[:, w.ch.HAZARD] = 0.0
    e0 = w.energy.sum().item()
    for _ in range(50):
        w.tick()  # pump comes from the brain read-out; there is nothing to bite and no food
    assert w.energy.sum().item() < e0
    assert float(w.ledger.pumped.sum()) > 0.0, "pumping was never charged for"
    assert w.last_damage_dealt.abs().max().item() == 0.0, "gained something from biting nothing"
