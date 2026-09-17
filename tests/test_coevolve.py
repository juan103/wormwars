"""Milestone 7: paired evaluation, match scoring, hall of fame, frozen suite.

The point of these tests is fairness. A coevolution result is worthless if the schedule quietly
favours somebody, so the schedule's balance and the score's antisymmetry are checked directly.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import shuffled
from wormwars.evo.coevolve import (
    HallOfFame,
    Match,
    build_schedule,
    candidate_scores,
    make_frozen_suite,
    play,
)
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def small_cfg(size=12, ticks=60):
    cfg = Config()
    cfg.world.n_swarms = 2
    cfg.world.max_ticks = ticks
    cfg.evo.coevo_sizes = (size, size)
    return cfg


# --------------------------------------------------------------- scheduling


def test_every_candidate_gets_an_identical_schedule():
    rng = np.random.default_rng(0)
    ms = build_schedule(5, 3, np.array([7, 8, 9]), rng, sizes=(50, 50))
    per_candidate = Counter(m.a for m in ms)
    assert len(set(per_candidate.values())) == 1
    for a in range(5):
        mine = [m for m in ms if m.a == a]
        assert Counter(m.b for m in mine) == Counter({b: 6 for b in range(3)})
        assert Counter(m.world_id for m in mine) == Counter({7: 6, 8: 6, 9: 6})
        assert Counter(m.swap_sides for m in mine) == Counter({False: 9, True: 9})


def test_every_pairing_is_played_from_both_sides():
    rng = np.random.default_rng(1)
    ms = build_schedule(2, 2, np.array([3]), rng)
    seen = {(m.a, m.b, m.world_id, m.swap_sides) for m in ms}
    for a in range(2):
        for b in range(2):
            assert (a, b, 3, False) in seen and (a, b, 3, True) in seen


def test_lopsided_matchups_are_played_with_headcounts_swapped():
    rng = np.random.default_rng(2)
    ms = build_schedule(2, 1, np.array([4]), rng, sizes=(50, 200), lopsided=True)
    assert Counter((m.size_a, m.size_b) for m in ms) == Counter({(50, 200): 4, (200, 50): 4})


def test_equal_headcounts_are_not_duplicated_by_lopsided():
    rng = np.random.default_rng(3)
    ms = build_schedule(2, 1, np.array([4]), rng, sizes=(60, 60), lopsided=True)
    assert all(m.size_a == m.size_b == 60 for m in ms)
    assert len(ms) == 4


def test_candidate_scores_average_over_the_schedule():
    ms = [Match(0, 0, 1, False, 10, 10), Match(0, 0, 2, False, 10, 10), Match(1, 0, 1, False, 10, 10)]
    out = candidate_scores(ms, np.array([1.0, -1.0, 0.5]), 2)
    assert out.tolist() == [0.0, 0.5]


# ------------------------------------------------------- paired evaluation


def test_swapping_sides_is_an_exact_relabelling(parts):
    """A at side 0 vs B at side 1 must be the *same fight* however the swarms are indexed.

    Played as (A=swarm0, B=swarm1, swap=False) and as (B=swarm0, A=swarm1, swap=True), the two
    swarms occupy the same two spawn clouds on the same map. The scores must be exact negatives.
    """
    con, iface, spec = parts
    cfg = small_cfg()
    ga = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(1))
    gb = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(2))
    ms = [Match(0, 0, 55, False, 12, 12)]
    forward = play(cfg, iface, ga, gb, ms, run_seed=9, combat_stage=1)
    ms_swapped = [Match(0, 0, 55, True, 12, 12)]
    backward = play(cfg, iface, gb, ga, ms_swapped, run_seed=9, combat_stage=1)
    assert forward.score[0] == pytest.approx(-backward.score[0], abs=1e-5)
    assert forward.energy_a[0] == pytest.approx(backward.energy_b[0], rel=1e-4)


def test_match_score_is_comparable_across_swarm_sizes(parts):
    """The score is normalised by total starting energy, so it stays in [-1, 1] at any headcount."""
    con, iface, spec = parts
    cfg = small_cfg(ticks=40)
    ga = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(3))
    gb = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(4))
    for sa, sb in ((10, 10), (5, 20), (20, 5)):
        res = play(cfg, iface, ga, gb, [Match(0, 0, 3, False, sa, sb)], run_seed=2, combat_stage=1)
        assert -1.0 <= res.score[0] <= 1.0


def test_two_different_graphs_can_fight(parts):
    """N2 and a shuffle have different masks, so they must be separate brains in one world."""
    con, iface, _ = parts
    cfg = small_cfg(ticks=40)
    spec_n2 = BrainSpec.from_connectome(con)
    spec_sh = BrainSpec.from_connectome(shuffled(con, seed=1))
    assert spec_n2.n_chem == spec_sh.n_chem
    ga = Genome.random(spec_n2, cfg.brain, 1, generator=torch.Generator().manual_seed(5))
    gb = Genome.random(spec_sh, cfg.brain, 1, generator=torch.Generator().manual_seed(6))
    res = play(cfg, iface, ga, gb, [Match(0, 0, 1, False, 10, 10)], run_seed=1, combat_stage=1)
    assert np.isfinite(res.score).all()


def test_ledger_balances_across_a_batch_of_matches(parts):
    con, iface, spec = parts
    cfg = small_cfg(ticks=80)
    ga = Genome.random(spec, cfg.brain, 3, generator=torch.Generator().manual_seed(7))
    gb = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(8))
    ms = build_schedule(3, 2, np.array([1, 2]), np.random.default_rng(0), sizes=(12, 12))
    res = play(cfg, iface, ga, gb, ms, run_seed=4, combat_stage=1)
    assert res.ledger_error / (12 * 2 * cfg.world.start_energy) < 1e-4
    assert len(res.score) == len(ms)


# ---------------------------------------------------- hall of fame + suite


def test_hall_of_fame_keeps_oldest_and_newest(parts):
    con, iface, spec = parts
    cfg = Config()
    pop = Genome.random(spec, cfg.brain, 4, generator=torch.Generator().manual_seed(9))
    hof = HallOfFame(capacity=4)
    for g in range(10):
        hof.add(pop, g % 4, g)
    gens = [g for g, _, _ in hof.entries]
    assert len(hof.entries) == 4
    assert gens[0] == 0, "the oldest champion was dropped"
    assert gens[-1] == 9, "the newest champion was dropped"


def test_hall_of_fame_sample_is_a_genome(parts):
    con, iface, spec = parts
    cfg = Config()
    pop = Genome.random(spec, cfg.brain, 4, generator=torch.Generator().manual_seed(10))
    hof = HallOfFame(capacity=5)
    for g in range(3):
        hof.add(pop, g, g)
    entries = hof.sample(2, np.random.default_rng(0))
    genome = hof.as_genome(entries)
    assert genome.n_strains == 2


def test_frozen_suite_is_diverse_and_versioned(parts):
    con, iface, spec = parts
    cfg = Config()
    suite, meta = make_frozen_suite(spec, cfg, n=6)
    assert suite.n_strains == 6
    assert meta["suite_version"] >= 1 and meta["graph"] == "N2"
    assert len(set(meta["nicknames"])) == 6
    # a single baseline is exploitable; these must actually differ from each other
    spread = suite.flat().std(dim=0).mean().item()
    assert spread > 0.05, f"suite members are nearly identical (spread {spread:.4f})"


def test_frozen_suite_is_reproducible(parts):
    con, iface, spec = parts
    cfg = Config()
    a, _ = make_frozen_suite(spec, cfg, n=4)
    b, _ = make_frozen_suite(spec, cfg, n=4)
    assert torch.equal(a.flat(), b.flat())


def test_suite_respects_the_parameter_bounds(parts):
    con, iface, spec = parts
    cfg = Config()
    suite, _ = make_frozen_suite(spec, cfg, n=6)
    assert suite.w.abs().max() <= cfg.brain.w_max + 1e-6
    assert suite.bias.abs().max() <= cfg.brain.b_max + 1e-6
    assert suite.tau.min() >= cfg.brain.tau_min - 1e-6


def test_a_saved_population_round_trips(parts, tmp_path):
    con, iface, spec = parts
    from wormwars.evo.genomes import load_genome, save_population

    cfg = Config()
    pop = Genome.random(spec, cfg.brain, 5, generator=torch.Generator().manual_seed(11))
    path = save_population(tmp_path / "pop.npz", pop, run=0)
    back, meta = load_genome(path, spec, cfg.brain)
    assert back.n_strains == 5 and meta["n_strains"] == 5
    torch.testing.assert_close(back.w, pop.w, rtol=0, atol=0)
    one, _ = load_genome(path, spec, cfg.brain, strain=3)
    assert one.n_strains == 1
    torch.testing.assert_close(one.w[0], pop.w[3], rtol=0, atol=0)


def test_loading_a_genome_onto_the_wrong_graph_is_refused(parts, tmp_path):
    con, iface, spec = parts
    from wormwars.evo.genomes import load_genome, save_genome

    cfg = Config()
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(12))
    path = save_genome(tmp_path / "g.npz", g)
    sh_spec = BrainSpec.from_connectome(shuffled(con, seed=9))
    with pytest.raises(ValueError, match="not transferable"):
        load_genome(path, sh_spec, cfg.brain)


def test_arena_density_is_constant_across_headcounts(parts):
    """Arena area scales with headcount, so starting density must not depend on swarm size."""
    con, iface, spec = parts
    from wormwars.world import arena_side

    cfg = Config()
    for total in (40, 100, 200, 400, 2000):
        side = arena_side(cfg, total)
        interior = (side - 2) ** 2
        density = total / interior
        expected = 1.0 / cfg.world.cells_per_wey
        assert density == pytest.approx(expected, rel=0.12), (
            f"{total} weys -> {density:.4f} weys/cell, wanted {expected:.4f}"
        )


def test_mixed_headcount_batches_do_not_share_one_arena(parts):
    """A 50v50 batched with a 200v200 must not be handed the big arena.

    Matches are grouped by total headcount before chunking; this checks the outcome, by playing a
    small match alone and then inside a mixed batch and requiring the same result.
    """
    con, iface, spec = parts
    cfg = small_cfg(ticks=50)
    ga = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(21))
    gb = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(22))
    small = Match(0, 0, 31, False, 8, 8)
    big = Match(0, 0, 31, False, 30, 30)
    alone = play(cfg, iface, ga, gb, [small], run_seed=6, combat_stage=1)
    mixed = play(cfg, iface, ga, gb, [big, small, big], run_seed=6, combat_stage=1)
    assert mixed.score[1] == pytest.approx(alone.score[0], abs=1e-5)


def test_results_come_back_in_the_order_they_were_asked_for(parts):
    con, iface, spec = parts
    cfg = small_cfg(ticks=30)
    ga = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(23))
    gb = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(24))
    ms = [
        Match(0, 0, 1, False, 20, 20),
        Match(0, 0, 2, False, 6, 6),
        Match(0, 0, 3, False, 20, 20),
    ]
    res = play(cfg, iface, ga, gb, ms, run_seed=7, combat_stage=1)
    per_match = [play(cfg, iface, ga, gb, [m], run_seed=7, combat_stage=1).score[0] for m in ms]
    np.testing.assert_allclose(res.score, per_match, atol=1e-5)


def test_sampled_sizes_stay_in_range_and_include_lopsided():
    from wormwars.evo.coevolve import sample_sizes

    rng = np.random.default_rng(0)
    pairs = sample_sizes(rng, 200, size_range=(50, 200), lopsided_fraction=0.5)
    assert all(50 <= a <= 200 and 50 <= b <= 200 for a, b in pairs)
    assert any(a != b for a, b in pairs), "no lopsided matchups were generated"
    assert any(a == b for a, b in pairs), "no even matchups were generated"
