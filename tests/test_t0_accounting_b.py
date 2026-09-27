"""T0 item 2, after Astra's and Fable's review (D069): exact counts for calibration and the
probes, early termination, the substeps override, scripted brains, timing, exception safety,
attempts and aggregation."""

from __future__ import annotations

import json

import numpy as np
import pytest
import torch

from wormwars import accounting as A
from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.interface import load_interface
from wormwars.world import World


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


@pytest.fixture(autouse=True)
def fresh_ledger():
    A.LEDGER.reset()
    yield
    A.LEDGER.reset()


def n_weys(cfg, iface, spec):
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(0))
    return World(cfg, iface, Brain(g), torch.zeros(1, 1, dtype=torch.long), run_seed=0).n_weys


def test_calibration_is_counted_exactly(parts):
    from wormwars import calibration as calib
    from wormwars.exp02 import grid
    con, iface, spec = parts
    cfg = grid.task_config(Config(), "T1")
    B = n_weys(cfg, iface, spec)
    A.LEDGER.reset()
    calib.achieved_drive(con, cfg, iface, n_strains=4, ticks=10, seed=0)
    c = A.LEDGER.counts["calibration"]
    assert (c.worlds_built, c.world_ticks, c.neural_updates) == (4, 4 * 10, 4 * B * cfg.brain.substeps * 10)


def test_the_input_response_probe_is_counted_exactly(parts):
    from wormwars.exp02 import grid
    from wormwars.exp02 import probes as P
    con, iface, spec = parts
    cfg = grid.task_config(Config(), "T1")
    g = Genome.random(spec, cfg.brain, 3, generator=torch.Generator().manual_seed(1))
    P.input_response(spec, cfg, iface, None, "cpu", ticks=7, genome=g, per_genome=True)
    c = A.LEDGER.counts["probe"]
    # four traces (zero, both, toward left, toward right), each 3 strains x 1 batch x k x 7 ticks
    assert (c.worlds_built, c.world_ticks, c.neural_updates) == (0, 0, 4 * 3 * 1 * cfg.brain.substeps * 7)


def test_the_history_probe_is_counted_exactly(parts):
    from wormwars.exp03 import measures as M
    con, iface, spec = parts
    cfg = Config()
    g = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(2))
    M.history(g, cfg, iface, {k: 0.1 for k in iface.signal_names}, warm=5, span=3, after=2)
    # two histories (rising, falling), each warm + span + after steps of 2 strains x 1 x k
    assert A.LEDGER.counts["probe"].neural_updates == 2 * (5 + 3 + 2) * 2 * cfg.brain.substeps


def test_early_termination_counts_only_the_ticks_simulated(parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 200
    cfg.world.start_energy, cfg.world.metabolic_drain = 0.05, 1.0  # everyone starves at once
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(3))
    w = World(cfg, iface, Brain(g), torch.zeros(2, 1, dtype=torch.long), run_seed=0)
    with A.category("probe"):
        w.run()
    assert w.tick_count < 200
    assert A.LEDGER.counts["probe"].world_ticks == 2 * w.tick_count


def test_the_substeps_override_is_counted(parts):
    con, iface, spec = parts
    cfg = Config()
    g = Genome.random(spec, cfg.brain, 3, generator=torch.Generator().manual_seed(4))
    b = Brain(g)
    v = b.initial_state(5)
    with A.category("probe"):
        b.step(v, torch.zeros_like(v), substeps=3)
    assert A.LEDGER.counts["probe"].neural_updates == 3 * 5 * 3


def test_scripted_brains_count_ticks_but_no_neural_updates(parts):
    from wormwars.exp02 import grid, scripted
    con, iface, spec = parts
    cfg = grid.task_config(Config(), "T1")
    cfg.world.max_ticks = 12
    b = scripted.ScriptedBrain(iface, 302, scripted.LevelKinesis(slow=0.2, fast=0.8, threshold=0.1, turn=0.3), cfg.world.forward_gain,
                               cfg.world.turn_gain)
    with A.category("measure"):
        scripted.rollout_brain(cfg, iface, b, np.array([1, 2]), 3, "cpu")
    c = A.LEDGER.counts["measure"]
    assert c.world_ticks == 2 * 12 and c.neural_updates == 0


def test_nested_time_is_exclusive_on_a_fake_clock(monkeypatch):
    clock = iter([0.0, 2.0, 5.0, 9.0]).__next__
    monkeypatch.setattr(A.time, "perf_counter", clock)
    with A.category("selection"):        # t = 0
        with A.category("calibration"):  # t = 2: selection gets 2
            pass                         # t = 5: calibration gets 3, selection resumes
    #                                      t = 9: selection gets 4 more
    assert A.LEDGER.counts["selection"].seconds == 6.0
    assert A.LEDGER.counts["calibration"].seconds == 3.0


def test_a_snapshot_inside_a_category_times_correctly(monkeypatch):
    """Astra: open at 0, snapshot at 5, close at 10 used to give 10 instead of 5."""
    clock = iter([0.0, 5.0, 10.0, 10.0]).__next__
    monkeypatch.setattr(A.time, "perf_counter", clock)
    with A.category("probe"):
        before = A.LEDGER.snapshot()
    assert A.LEDGER.since(before)["probe"]["seconds"] == 5.0


def test_a_failing_sync_still_restores_the_category(monkeypatch):
    calls = {"n": 0}

    def sync():
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("device-side assert")

    monkeypatch.setattr(A, "_sync", sync)
    with pytest.raises(RuntimeError, match="device-side"):
        with A.category("probe"):
            pass
    assert A.LEDGER.current() == "other"


def test_untimed_other_is_null_and_flagged(tmp_path, parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 3
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(5))
    with A.attempt(tmp_path, command="t"):
        World(cfg, iface, Brain(g), torch.zeros(1, 1, dtype=torch.long), run_seed=0).run()
    d = json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8"))
    assert d["uncategorised"] and d["categories"]["other"]["seconds"] is None


def test_an_attempt_is_written_even_when_it_fails_and_aggregation_sums_attempts(tmp_path, parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 4
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(6))
    with A.attempt(tmp_path, default="measure", command="ok"):
        World(cfg, iface, Brain(g), torch.zeros(2, 1, dtype=torch.long), run_seed=0).run()
    with pytest.raises(RuntimeError):
        with A.attempt(tmp_path, default="calibration", command="bad"):
            World(cfg, iface, Brain(g), torch.zeros(3, 1, dtype=torch.long), run_seed=0).run()
            raise RuntimeError("calibration did not converge")
    files = sorted(tmp_path.glob("*.json"))
    assert len(files) == 2 and len({f.name for f in files}) == 2
    agg = A.aggregate(tmp_path)
    assert agg["failed_attempts"] == 1 and not agg["uncategorised"]
    assert agg["categories"]["measure"]["world_ticks"] == 2 * 4
    assert agg["categories"]["calibration"]["world_ticks"] == 3 * 4
    assert agg["totals"]["worlds_built"] == 5


def test_geometry_work_is_categorised(parts):
    from wormwars.analysis import geometry
    con, iface, spec = parts
    geometry.duel(con, Config(), pose="head_on", gap=1.0)
    assert A.LEDGER.counts["probe"].worlds_built > 0 and "other" not in A.LEDGER.counts
