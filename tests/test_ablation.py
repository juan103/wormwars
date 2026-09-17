"""Milestone 10: ablation, convergence and tactics tools.

These tests check the *tools*, not any biological claim. The distinction between implementation
checks and emergent tests is itself under test: an implementation check must be labelled as one.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.analysis.ablation import (
    EMERGENT_TARGETS,
    RIP_I1_BRIDGE,
    AblationSpec,
    degree_of,
    emergent_checks,
    evaluate_ablations,
    implementation_checks,
    matched_random,
    profile_correlation,
    sensitivity,
    tactics_from_world,
)
from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def champion(spec, cfg, seed=0):
    return Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(seed))


# ------------------------------------------------------------- the machinery


def test_silencing_holds_a_neuron_at_zero(parts):
    con, iface, spec = parts
    cfg = Config()
    g = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(0))
    brain = Brain(g).silence([[], [con.index("AIYL"), con.index("AIYR")]])
    v = brain.initial_state(3)
    cur = torch.randn_like(v) * 0.4
    for _ in range(25):
        v = brain.step(v, cur)
    assert v[1, :, [con.index("AIYL"), con.index("AIYR")]].abs().max().item() == 0.0
    assert v[0, :, con.index("AIYL")].abs().max().item() > 0.0, "silencing leaked across strains"


def test_cutting_the_rip_i1_bridge_removes_exactly_those_junctions(parts):
    con, iface, spec = parts
    cfg = Config()
    g = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(1))
    brain = Brain(g)
    pairs = [(con.index(a), con.index(b)) for a, b in RIP_I1_BRIDGE]
    before = [float(brain.G[0, i, j]) for i, j in pairs]
    assert all(x > 0 for x in before), "the bridge was not there to begin with"
    brain.cut_gap([pairs, []])
    for i, j in pairs:
        assert float(brain.G[0, i, j]) == 0.0 and float(brain.G[0, j, i]) == 0.0
        assert float(brain.G[1, i, j]) > 0.0, "cut the wrong strain"


def test_an_empty_ablation_changes_nothing(parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 60
    champ = champion(spec, cfg)
    ids = np.array([1, 2])
    scores = evaluate_ablations(
        cfg, iface, con, champ,
        [AblationSpec("none", [], kind="none"), AblationSpec("none2", [], kind="none")],
        ids, run_seed=3,
    )
    assert scores[0] == pytest.approx(scores[1], rel=1e-6)


def test_ablations_are_evaluated_on_the_same_worlds(parts):
    """Paired comparison: two identical ablations must score identically, so any difference between
    different ablations is the ablation and not the map."""
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 60
    champ = champion(spec, cfg, seed=2)
    specs = [
        AblationSpec("a", ["AIYL", "AIYR"]),
        AblationSpec("a-again", ["AIYL", "AIYR"]),
        AblationSpec("b", ["AIZL", "AIZR"]),
    ]
    s = evaluate_ablations(cfg, iface, con, champ, specs, np.array([5, 6]), run_seed=7)
    assert s[0] == pytest.approx(s[1], rel=1e-6)


# --------------------------------------------------------- matched controls


def test_matched_random_matches_size_class_and_degree(parts):
    con, iface, spec = parts
    rng = np.random.default_rng(0)
    target = AblationSpec("emergent:AIY", ["AIYL", "AIYR"])
    deg = degree_of(con)
    controls = matched_random(con, target, 20, rng)
    assert len(controls) == 20
    for c in controls:
        assert len(c.neurons) == len(target.neurons)
        assert c.kind == "matched_random"
        for got, want in zip(c.neurons, target.neurons):
            i, j = con.index(got), con.index(want)
            assert con.classes[i] == con.classes[j], f"{got} is not the same class as {want}"
            assert abs(deg[i] - deg[j]) <= 0.5 * max(deg[j], 1.0) + 1e-9


def test_matched_random_never_picks_the_target_itself(parts):
    con, iface, spec = parts
    rng = np.random.default_rng(1)
    target = AblationSpec("emergent:RIM", ["RIML", "RIMR"])
    for c in matched_random(con, target, 30, rng):
        assert not set(c.neurons) & set(target.neurons)
        assert len(set(c.neurons)) == len(c.neurons), "picked the same neuron twice"


def test_emergent_targets_are_not_in_the_sensor_motor_map(parts):
    """The whole point of the emergent list: if a neuron is in the map, ablating it proves nothing
    about the evolved dynamics."""
    con, iface, spec = parts
    mapped = set(iface.mapped_neurons)
    for group, names in EMERGENT_TARGETS.items():
        for name in names:
            assert con.index(name) not in mapped, f"{name} is in the interface; not an emergent test"
    for a, b in RIP_I1_BRIDGE:
        assert con.index(a) not in mapped


def test_implementation_checks_are_labelled_as_such(parts):
    con, iface, spec = parts
    checks = implementation_checks(con, iface)
    assert checks and all(c.kind == "implementation" for c in checks)
    mapped = set(iface.mapped_neurons)
    for c in checks:
        assert all(con.index(n) in mapped for n in c.neurons), (
            f"{c.name} claims to be an implementation check but names an unmapped neuron"
        )


def test_emergent_checks_cover_the_named_groups():
    names = {c.name for c in emergent_checks()}
    for group in EMERGENT_TARGETS:
        assert f"emergent:{group}" in names
    assert "emergent:RIP-I1 bridge" in names


# -------------------------------------------------------------- the readouts


def test_sensitivity_is_a_fractional_loss():
    s = sensitivity(np.array([1.0, 0.5, 0.0]), baseline=1.0)
    np.testing.assert_allclose(s, [0.0, 0.5, 1.0])
    assert (sensitivity(np.array([1.0]), baseline=0.0) == 0).all()


def test_profile_correlation_detects_agreement_and_disagreement():
    a = np.array([0.1, 0.5, 0.9, 0.2])
    assert profile_correlation(a, a) == pytest.approx(1.0)
    assert profile_correlation(a, -a) == pytest.approx(-1.0)
    assert np.isnan(profile_correlation(a, np.ones(4)))


def test_tactics_report_shares_sum_to_one(parts):
    con, iface, spec = parts
    from wormwars.world import World

    cfg = Config()
    cfg.world.n_swarms = 2
    cfg.world.max_ticks = 120
    g = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(4))
    w = World(cfg, iface, Brain(g), torch.tensor([[0, 1], [1, 0]]), run_seed=2, combat_stage=1)
    # Random brains in a full-size arena rarely meet, so the swarms are put nose to nose: the
    # metric is what is under test, not whether unevolved weys can find each other.
    centre = w.side / 2
    gen = torch.Generator().manual_seed(5)
    w.pos[:] = centre + (torch.rand(w.pos.shape, generator=gen) - 0.5) * 4.0
    w.heading[:] = torch.rand(w.heading.shape, generator=gen) * 6.28
    w._points = None
    w._update_body_field()
    w.run()
    rep = tactics_from_world(w)
    assert float(w.damage_by_point.sum()) > 0, "no damage happened; the metric is untested"
    assert rep.flank_share + rep.head_share == pytest.approx(1.0, abs=1e-6)
    assert 0.0 <= rep.turn_toward_rate <= 1.0
    assert rep.turn_events > 0, "no wey was ever bitten asymmetrically while turning"


def test_tactics_report_is_empty_rather_than_undefined_without_a_fight(parts):
    con, iface, spec = parts
    from wormwars.world import World

    cfg = Config()
    cfg.world.n_swarms = 2
    cfg.world.max_ticks = 20
    g = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(6))
    w = World(cfg, iface, Brain(g), torch.tensor([[0, 1]]), run_seed=2, combat_stage=0)
    w.run()
    rep = tactics_from_world(w)
    assert rep.flank_share == 0.0 and rep.head_share == 0.0 and rep.turn_events == 0
