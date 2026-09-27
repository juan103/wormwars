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


def test_a_nonzero_exit_is_a_failed_attempt_and_the_aggregate_names_the_script(tmp_path):
    def main():
        raise SystemExit(3)
    with pytest.raises(SystemExit):
        A.run_script(main, out_default=str(tmp_path / "o"), default="measure", name="demo", argv=["--x"])
    agg = json.loads((tmp_path / "o" / "compute.json").read_text(encoding="utf-8"))
    a = agg["attempts"][0]
    assert a["status"] == "failed" and a["script"] == "demo" and a["argv"] == ["--x"]
    assert agg["failed_attempts"] == 1


def test_the_legacy_scripts_refuse_abbreviated_options():
    """Astra: --ou was accepted by argparse, sending results and accounting to different folders."""
    for name in ("evolve_forage", "experiment", "coevolve", "ablate", "tactics"):
        src = (ROOT / "scripts" / f"{name}.py").read_text(encoding="utf-8")
        assert "ArgumentParser(allow_abbrev=False)" in src, name


def test_the_aggregate_is_written_even_when_an_attempt_fails(tmp_path):
    """Astra reproduced 02b's stale aggregate: success then failure reported one attempt, no failure."""
    d, agg = tmp_path / "compute", tmp_path / "compute.json"
    with A.recorded(d, agg, default="probe", stage="ok"):
        pass
    with pytest.raises(RuntimeError):
        with A.recorded(d, agg, default="probe", stage="bad"):
            raise RuntimeError("stage failed")
    doc = json.loads(agg.read_text(encoding="utf-8"))
    assert len(doc["attempts"]) == 2 and doc["failed_attempts"] == 1


def test_scripted_tuning_is_categorised(parts):
    from wormwars.exp02 import grid, scripted
    con, iface, spec = parts
    cfg = grid.task_config(Config(), "T1")
    cfg.world.max_ticks = 6
    scripted.tune_batched(lambda **p: scripted.LevelKinesis(**p),
                          {"slow": [0.2], "fast": [0.8], "threshold": [0.1], "turn": [0.2, 0.4]},
                          cfg, iface, np.array([1]), 3, "cpu")
    assert A.LEDGER.counts["tuning"].world_ticks > 0 and "other" not in A.LEDGER.counts
