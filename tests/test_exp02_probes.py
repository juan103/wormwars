"""Probes: the valence symmetry is exact without gap junctions; the others return sane numbers."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.exp02 import probes
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def small_cfg():
    c = Config()
    c.world.max_ticks = 60
    return c


def champ(spec, cfg, seed=0):
    return Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(seed))


def test_valence_symmetry_is_exact_without_gap_junctions(parts):
    con, iface, spec = parts
    r = probes.valence_check(spec, small_cfg(), con, iface, 4, np.arange(2), 3, "cpu", gaps=False)
    assert r["max_abs_score_diff"] <= 1e-5


def test_valence_with_gap_junctions_reports_a_discrepancy(parts):
    con, iface, spec = parts
    r = probes.valence_check(spec, small_cfg(), con, iface, 4, np.arange(2), 3, "cpu", gaps=True)
    assert np.isfinite(r["mean_abs_score_diff"])


def test_channel_dependence_returns_per_world_scores_for_every_variant(parts):
    """Astra's decision review, point 10: per-world real and intervention scores, with the world
    ids and the probe seed, so each champion's use of a capability has its own paired interval."""
    con, iface, spec = parts
    d = probes.channel_dependence(small_cfg(), iface, champ(spec, Config()), np.arange(3), 3, "cpu",
                                  with_pheromone=True)
    assert d["world_ids"] == [0, 1, 2] and d["probe_seed"] == 3
    assert set(d["scores"]) == {"real", "food_constant", "food_mirrored", "collision_off", "pheromone_off",
                                "jitter1", "jitter3", "mono", "food_mean", "food_swapped"}
    assert all(len(v) == 3 and np.isfinite(v).all() for v in d["scores"].values())


def test_capability_probes_follow_the_task(parts):
    """History sensitivity (jitter) is probed on every champion; the stereo ablations only where
    the task is stereo, since a mono champion has no left-right difference to lose."""
    con, iface, spec = parts
    mono_cfg = small_cfg()
    mono_cfg.world.food_sensing = "mono"
    d = probes.channel_dependence(mono_cfg, iface, champ(spec, Config()), np.arange(2), 3, "cpu",
                                  with_pheromone=False)["scores"]
    assert not {"mono", "food_mean", "food_swapped"} & set(d) and {"jitter1", "jitter3"} <= set(d)


def test_integrator_rescore_returns_paired_per_world_scores(parts):
    """Plan review F2: the report recomputes the interaction from these, so they must be per world."""
    con, iface, spec = parts
    r = probes.integrator_rescore(small_cfg(), iface, champ(spec, Config()), np.arange(3), 3, "cpu")
    assert set(r) == {"s32", "s128", "s32_bias_perturbed"}
    assert all(len(v) == 3 and np.isfinite(v).all() for v in r.values())


def test_gen0_scores_are_finite_for_every_magnitude_mode(parts):
    con, iface, spec = parts
    cfg = small_cfg()
    for mode in ("anatomical", "uniform", "permuted"):
        c = cfg.copy()
        c.brain.init_chem_magnitude = c.brain.init_gap_magnitude = mode
        assert np.isfinite(probes.gen0_scores(spec, c, iface, 4, np.arange(2), 3, "cpu"))


def test_input_response_reports_raw_and_motor_signed_and_absolute(parts):
    con, iface, spec = parts
    r = probes.input_response(spec, Config(), iface, 4, "cpu", ticks=10)
    assert set(r) == {f"{m}_{k}_{s}" for m in ("common", "directional") for k in ("forward", "turn")
                      for s in ("raw", "motor")} | {f"directional_turn_signed_{s}" for s in ("raw", "motor")}
    assert all(len(v) == 10 and np.isfinite(v).all() for v in r.values())


def test_directional_response_holds_the_common_mode_fixed(parts):
    """Astra's decision review, point 3: the old probe compared (0.5, 0) with (0, 0), which also
    changed the total. Now (b+d, b-d) is compared with (b-d, b+d); with d = 0 they are identical."""
    con, iface, spec = parts
    r = probes.input_response(spec, Config(), iface, 4, "cpu", ticks=10, diff=0.0)
    for k, v in r.items():
        if k.startswith("directional"):
            assert np.allclose(v, 0.0), k
    assert max(r["common_turn_raw"]) > 0


def test_motor_response_is_bounded_by_the_clip(parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.world.turn_gain = cfg.world.forward_gain = 1e6
    r = probes.input_response(spec, cfg, iface, 4, "cpu", ticks=10)
    assert max(r["directional_turn_motor"]) <= 1.0 + 1e-6 and max(r["common_turn_motor"]) <= 2.0 + 1e-6


def test_behaviour_is_finite_even_if_all_die(parts):
    con, iface, spec = parts
    cfg = small_cfg()
    cfg.world.metabolic_drain = 5.0  # everyone dies on the first tick
    b = probes.behaviour(cfg, iface, champ(spec, cfg), np.arange(2), 3, "cpu")
    assert all(np.isfinite(v) for v in b.values())
