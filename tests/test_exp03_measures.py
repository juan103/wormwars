"""Experiment 03's measures (design v3): coverage for task C, per-genome input response, and
the history probe on random genomes with a shared stimulus bank."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.exp02 import probes as P
from wormwars.exp03 import measures as M
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def small(cfg):
    cfg.world.max_ticks = 30
    return cfg


def test_task_c_has_no_food_no_drain_and_no_deaths(parts):
    con, iface, spec = parts
    cfg = small(M.task_c_config(Config()))
    g = Genome.random(spec, cfg.brain, 3, generator=torch.Generator().manual_seed(0))
    out = M.coverage(cfg, iface, g, np.arange(2), 5, "cpu")
    assert out["cells"].shape == (3, 2) and np.all(out["cells"] >= 1)
    assert out["food_left"] == 0.0 and out["deaths"] == 0


def test_coverage_counts_distinct_cells_so_a_still_swarm_covers_few(parts):
    con, iface, spec = parts
    cfg = small(M.task_c_config(Config()))
    cfg.world.forward_gain = cfg.world.turn_gain = 0.0  # nobody moves
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(0))
    still = M.coverage(cfg, iface, g, np.arange(2), 5, "cpu")["cells"]
    assert np.all(still <= 20 * 4)  # at most the cells the 20 spawned weys stand on


def test_input_response_per_genome_averages_to_the_old_output(parts):
    con, iface, spec = parts
    cfg = Config()
    a = P.input_response(spec, cfg, iface, 4, "cpu", ticks=10)
    b = P.input_response(spec, cfg, iface, 4, "cpu", ticks=10, per_genome=True)
    for k in a:
        assert np.asarray(b[k]).shape == (10, 4)
        if "signed" in k:
            np.testing.assert_allclose(np.asarray(b[k]).mean(1), a[k], rtol=1e-5, atol=1e-8)


def test_history_probe_is_zero_for_identical_histories_and_per_genome(parts):
    con, iface, spec = parts
    cfg = Config()
    g = Genome.random(spec, cfg.brain, 3, generator=torch.Generator().manual_seed(0))
    bank = {"food_left": 0.2, "food_right": 0.2}
    h = M.history(g, cfg, iface, bank, rising_start=1.0, falling_start=1.0, warm=20, span=5)
    assert h["raw_turn"]["final"].shape == (3,)
    np.testing.assert_allclose(h["raw_turn"]["final"], 0.0, atol=1e-7)
    h2 = M.history(g, cfg, iface, bank, warm=20, span=5)
    assert np.all(np.isfinite(h2["raw_turn"]["final"])) and np.any(np.abs(h2["raw_turn"]["final"]) > 0)
