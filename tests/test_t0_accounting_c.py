"""T0 item 2, re-check (D070): coevolution and the exp03 stimulus bank categorised, scripts
routed by --out, --help not a failure, boundary syncs."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from wormwars import accounting as A
from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.interface import load_interface

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


@pytest.fixture(autouse=True)
def fresh_ledger():
    A.LEDGER.reset()
    yield
    A.LEDGER.reset()


def test_a_coevolution_run_is_categorised(parts):
    from wormwars.evo.coevolve import coevolve
    con, iface, spec = parts
    cfg = Config()
    cfg.world.n_swarms, cfg.world.max_ticks = 2, 8
    cfg.evo.coevo_sizes, cfg.evo.population, cfg.evo.generations = (3, 3), 4, 1
    cfg.evo.coevo_worlds, cfg.evo.suite_size, cfg.evo.suite_worlds = 2, 2, 2
    cfg.evo.opponents_self, cfg.evo.opponents_hof, cfg.evo.elites, cfg.evo.truncation = 2, 1, 1, 2
    coevolve(cfg, iface, spec, run=0, run_seed=3, verbose=False)
    assert A.LEDGER.counts["selection"].world_ticks > 0
    assert A.LEDGER.counts["holdout"].world_ticks > 0
    assert "other" not in A.LEDGER.counts


def test_the_exp03_stimulus_bank_is_a_probe(parts):
    con, iface, spec = parts
    s = importlib.util.spec_from_file_location("exp03_acct", ROOT / "scripts" / "exp03.py")
    exp = importlib.util.module_from_spec(s)
    s.loader.exec_module(exp)
    exp.use_instance("03")
    cfg = Config()
    g = Genome.random(spec, cfg.brain, 16, generator=torch.Generator().manual_seed(1))
    exp._typical_signals(cfg, iface, g, "cpu")
    c = A.LEDGER.counts["probe"]
    assert c.worlds_built == 16 * 4 and c.world_ticks > 0 and "other" not in A.LEDGER.counts


def test_run_script_routes_attempts_by_out_and_aggregates(tmp_path):
    def main():
        with A.category("final"):
            pass
    A.run_script(main, out_default=str(tmp_path / "default"), default="measure", name="t",
                 argv=["--out", str(tmp_path / "chosen")])
    assert len(list((tmp_path / "chosen" / "compute").glob("*.json"))) == 1
    agg = json.loads((tmp_path / "chosen" / "compute.json").read_text(encoding="utf-8"))
    assert agg["attempts"][0]["status"] == "completed"
    assert not (tmp_path / "default").exists()


def test_help_is_not_recorded_and_exit_zero_is_not_a_failure(tmp_path):
    def main():
        raise SystemExit(0)
    with pytest.raises(SystemExit):
        A.run_script(main, out_default=str(tmp_path / "o"), default="measure", name="t", argv=["--help"])
    assert not (tmp_path / "o").exists()
    with pytest.raises(SystemExit):
        A.run_script(main, out_default=str(tmp_path / "o"), default="measure", name="t", argv=[])
    d = json.loads(next((tmp_path / "o" / "compute").glob("*.json")).read_text(encoding="utf-8"))
    assert d["status"] == "completed" and d["default_category"] == "measure"


def test_category_boundaries_synchronise(monkeypatch):
    calls = []
    monkeypatch.setattr(A, "_sync", lambda: calls.append(A.LEDGER.current()))
    with A.category("probe"):
        pass
    assert len(calls) == 2  # once on entry, once on exit, never in between
