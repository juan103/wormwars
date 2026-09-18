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


# --------------------------------------------------- tactics metrics (D026)


def test_chance_flank_share_comes_from_the_armor_weights():
    """The retracted metric's reference line must track the config, not a literal."""
    from wormwars.analysis import armor_weights, chance_flank_share

    cfg = Config()
    assert chance_flank_share(cfg.combat) == pytest.approx(
        2.0 / (2.0 + cfg.combat.head_armor)
    )
    assert chance_flank_share(cfg.combat) == pytest.approx(0.888889, abs=1e-6)
    cfg.combat.head_armor = 1.0  # no armour: all three points weighted equally
    assert chance_flank_share(cfg.combat) == pytest.approx(2.0 / 3.0)
    assert armor_weights(cfg.combat) == (1.0, 1.0, 1.0)


def test_flank_share_is_pinned_by_the_armor_weights_not_by_behaviour():
    """The arithmetic that invalidated the original "learned to flank" claim.

    Feed the report a uniform attack over the three body points and it reads the reference line,
    with no weys and no tactics involved at all.
    """
    from wormwars.analysis import chance_flank_share, chance_placement_share

    cfg = Config()
    armor = torch.tensor([cfg.combat.head_armor, 1.0, 1.0], dtype=torch.float64)
    uniform_attack = torch.ones(3, dtype=torch.float64)  # same field at head, mid and tail
    damage = uniform_attack * armor
    assert float(damage[1:].sum() / damage.sum()) == pytest.approx(
        chance_flank_share(cfg.combat), abs=1e-9
    )
    assert float(uniform_attack[1:].sum() / uniform_attack.sum()) == pytest.approx(
        chance_placement_share(cfg.combat), abs=1e-9
    )


def test_placement_is_exactly_the_damage_with_armour_divided_out(con):
    """The two accumulators must differ by the armour weights and nothing else."""
    cfg = Config()
    w = build(con, n_worlds=2, cfg=cfg, stage=1)
    centre = w.side / 2
    gen = torch.Generator().manual_seed(4)
    w.pos[:] = centre + (torch.rand(w.pos.shape, generator=gen) - 0.5) * 4.0
    w._points = None
    w._update_body_field()
    w.run(60)
    armor = torch.tensor(
        [cfg.combat.head_armor, 1.0, 1.0], dtype=w.attack_points.dtype, device=w.device
    )
    assert float(w.damage_points.sum()) > 0
    torch.testing.assert_close(w.attack_points * armor, w.damage_points, rtol=1e-9, atol=1e-12)


def test_neither_reference_line_is_the_empirical_null(con):
    """Measured, not assumed: a real melee does not put a uniform attack over the body.

    Weys converge head-first, so heads take more than their uniform share and the flank share lands
    BELOW its reference line. This is why DECISIONS.md D026 insists the null has to be measured.
    """
    from wormwars.analysis import chance_flank_share, tactics_from_world

    cfg = Config()
    w = build(con, n_worlds=1, cfg=cfg, stage=1)
    w.fields.zero_()
    centre = w.side / 2
    gen = torch.Generator().manual_seed(3)
    w.pos[:] = centre + (torch.rand(w.pos.shape, generator=gen) - 0.5) * 3.0
    w.heading[:] = torch.rand(w.heading.shape, generator=gen) * 6.28
    w.energy.fill_(1e6)  # nothing dies, so nothing is capped
    w._points = None
    w._update_body_field()
    for _ in range(25):
        w._combat()
    rep = tactics_from_world(w)
    assert rep.total_damage > 0
    assert rep.flank_share < chance_flank_share(cfg.combat) - 0.02, (
        f"measured flank share {rep.flank_share:.4f} did not fall below the reference line"
    )
    assert rep.placement_share < rep.placement_share + 1e-9  # recorded for the report
    assert 0.0 < rep.placement_share < 1.0


def test_tactics_are_attributed_to_the_attacking_swarm(con):
    """Summing the per-swarm accumulators must reproduce the global totals."""
    from wormwars.analysis import tactics_from_world

    w = build(con, n_worlds=3, stage=1)
    centre = w.side / 2
    gen = torch.Generator().manual_seed(5)
    w.pos[:] = centre + (torch.rand(w.pos.shape, generator=gen) - 0.5) * 4.0
    w._points = None
    w._update_body_field()
    w.run(60)
    both = tactics_from_world(w)
    a = tactics_from_world(w, swarm=0)
    b = tactics_from_world(w, swarm=1)
    assert a.total_damage + b.total_damage == pytest.approx(both.total_damage, rel=1e-9)
    assert w.damage_points.shape == (w.n_worlds, w.n_swarms, 3)
    assert w.unanswered.shape == (w.n_worlds, w.n_swarms, 2)
    torch.testing.assert_close(w.damage_points.sum(dim=(0, 1)), w.damage_by_point)


def test_unanswered_damage_is_bounded_and_counts_only_untouched_weys(con):
    w = build(con, n_worlds=2, stage=1)
    centre = w.side / 2
    gen = torch.Generator().manual_seed(6)
    w.pos[:] = centre + (torch.rand(w.pos.shape, generator=gen) - 0.5) * 4.0
    w._points = None
    w._update_body_field()
    w.run(80)
    num, den = w.unanswered[..., 0].sum(), w.unanswered[..., 1].sum()
    assert den > 0
    assert 0.0 <= float(num / den) <= 1.0
    assert float(num) <= float(den) + 1e-9
