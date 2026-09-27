"""T0 item 2: compute accounting (docs/foundations/T0.md v2.1, section 1; D068).

Worlds are counted where they are built (`World.__init__`), world-ticks where they are simulated
(`World.tick`), and neural updates where brains are stepped (`Brain.step`, S x B x substeps).
Categories come from a context manager; nesting resolves to the innermost category."""

from __future__ import annotations

import importlib

import numpy as np
import pytest
import torch

from wormwars import accounting as A
from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo import rollout
from wormwars.interface import load_interface
from wormwars.world import World

E = importlib.import_module("wormwars.evo.evolve")


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


@pytest.fixture(autouse=True)
def fresh_ledger():
    A.LEDGER.reset()
    yield
    A.LEDGER.reset()


def weys_per_world(cfg, iface, spec) -> int:
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(0))
    return World(cfg, iface, Brain(g), torch.zeros(1, 1, dtype=torch.long), run_seed=0).n_weys


def test_a_rollout_is_counted_exactly(parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 20
    g = Genome.random(spec, cfg.brain, 3, generator=torch.Generator().manual_seed(1))
    B = weys_per_world(cfg, iface, spec)
    A.LEDGER.reset()
    with A.category("probe"):
        rollout(cfg, iface, g, np.array([1, 2]), run_seed=5)
    c = A.LEDGER.counts["probe"]
    assert c.worlds_built == 6
    assert c.world_ticks == 6 * 20
    assert c.neural_updates == 6 * 20 * B * cfg.brain.substeps


def test_a_small_evolve_is_counted_by_hand_and_nothing_lands_in_other(parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 15
    cfg.evo.population, cfg.evo.generations, cfg.evo.worlds_per_strain = 4, 2, 2
    cfg.evo.holdout_worlds, cfg.evo.elites, cfg.evo.truncation = 3, 1, 2
    B = weys_per_world(cfg, iface, spec)
    A.LEDGER.reset()
    r = E.evolve(cfg, iface, spec, run=0, run_seed=7, verbose=False, holdout_every=1, snapshots=(1,))
    k = cfg.brain.substeps
    sel = r.compute["selection"]
    assert sel["worlds_built"] == 2 * 4 * 2 and sel["world_ticks"] == 2 * 4 * 2 * 15
    assert sel["neural_updates"] == 2 * 4 * 2 * 15 * B * k
    # a holdout at generation 0; generation 1 is both a holdout and a snapshot: counted once
    assert r.compute["holdout"]["worlds_built"] == 3
    assert r.compute["snapshot"]["worlds_built"] == 3
    assert "other" not in r.compute and "final" not in r.compute
    assert all(v["seconds"] >= 0 for v in r.compute.values())


def test_accounting_is_pure_measurement(parts):
    """Scores are bit-identical with the ledger on and off, and it draws no random numbers."""
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 25
    g = Genome.random(spec, cfg.brain, 3, generator=torch.Generator().manual_seed(2))
    ids = np.array([3, 4])
    torch.manual_seed(123)
    state = torch.random.get_rng_state()
    with A.category("probe"):
        on = rollout(cfg, iface, g, ids, run_seed=9).score
    assert torch.equal(torch.random.get_rng_state(), state)
    A.LEDGER.reset()
    A.LEDGER.enabled = False
    try:
        off = rollout(cfg, iface, g, ids, run_seed=9).score
        assert A.LEDGER.counts == {}
    finally:
        A.LEDGER.enabled = True
    np.testing.assert_array_equal(on, off)


def test_nesting_counts_the_innermost_category_once(parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 5
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(3))
    with A.category("selection"):
        with A.category("calibration"):
            rollout(cfg, iface, g, np.array([1]), run_seed=1)
        rollout(cfg, iface, g, np.array([1, 2]), run_seed=1)
    assert A.LEDGER.counts["calibration"].worlds_built == 1
    assert A.LEDGER.counts["selection"].worlds_built == 2
    total = sum(c.worlds_built for c in A.LEDGER.counts.values())
    assert total == 3


def test_the_category_is_restored_after_an_exception():
    with pytest.raises(RuntimeError):
        with A.category("probe"):
            raise RuntimeError("boom")
    assert A.LEDGER.current() == "other"


def test_unknown_categories_are_refused():
    with pytest.raises(ValueError):
        with A.category("selectoin"):
            pass


def test_calibration_and_probes_record_under_their_own_categories(parts):
    from wormwars import calibration as calib
    from wormwars.exp02 import grid
    from wormwars.exp02 import probes as P
    from wormwars.exp03 import measures as M
    con, iface, spec = parts
    cfg = grid.task_config(Config(), "T1")
    g = Genome.random(spec, cfg.brain, 4, generator=torch.Generator().manual_seed(4))
    calib.achieved_drive(con, cfg, iface, n_strains=4, ticks=10, seed=0)
    assert A.LEDGER.counts["calibration"].world_ticks > 0
    P.input_response(spec, cfg, iface, None, "cpu", genome=g, per_genome=True)
    assert A.LEDGER.counts["probe"].neural_updates > 0
    before = A.LEDGER.counts["probe"].neural_updates
    bank = {k: 0.1 for k in iface.signal_names}
    M.history(g, cfg, iface, bank, warm=5, span=3, after=2)
    assert A.LEDGER.counts["probe"].neural_updates > before
    assert "other" not in A.LEDGER.counts


def test_the_ledger_writes_an_experiment_level_json(tmp_path, parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 5
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(5))
    with A.category("probe"):
        rollout(cfg, iface, g, np.array([1]), run_seed=1)
    path = A.LEDGER.write(tmp_path / "compute.json", extra={"experiment": "test"})
    import json
    d = json.loads(path.read_text(encoding="utf-8"))
    assert d["experiment"] == "test" and d["categories"]["probe"]["worlds_built"] == 1
    assert d["time_unit"].startswith("synchronised wall")


def test_coverage_and_the_behaviour_probe_record_under_their_categories(parts):
    from wormwars.exp02 import probes as P
    from wormwars.exp03 import measures as M
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 8
    g = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(6))
    M.coverage(M.task_c_config(cfg), iface, g, np.array([1]), 3, "cpu")
    assert A.LEDGER.counts["measure"].world_ticks > 0
    P.behaviour(cfg, iface, g.select([0]), np.array([1, 2]), 3, "cpu")
    assert A.LEDGER.counts["probe"].world_ticks > 0
    assert "other" not in A.LEDGER.counts
