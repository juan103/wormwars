"""E4's pilot runner (scripts/e4.py; docs/E4/E4-DESIGN.md v3 §6): its configuration, its folders, the pairing of run
seeds across arms, the frame's kill reconciliation (Astra, code review), and the blocks' disjointness."""

from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def X():
    s = importlib.util.spec_from_file_location("e4_under_test", ROOT / "scripts" / "e4.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_the_configuration(X):
    cfg = X.cfg_for("shared")
    assert cfg.world.max_ticks == 1800 and (cfg.evo.population, cfg.evo.elites, cfg.evo.truncation) == (32, 3, 8)
    assert cfg.mutation.w_sigma == 0.08 and X.REGISTERED["pilot"]["checkpoint_every"] == 10
    assert X.E.EXP == ROOT / "experiments" / "E4-two-minds" and X.E.OUT == ROOT / "runs" / "e4"


def test_runs_are_paired_by_seed(X):
    runs = X.pilot_runs()
    by_arm = {a: [r for r in runs if r["arm"] == a] for a in X.ARMS}
    assert [r["seed"] for r in by_arm["x0"]] == [r["seed"] for r in by_arm["x_plus"]]
    assert len({r["run"] for r in runs}) == len(runs)


def test_the_blocks_are_disjoint(X):
    ids = [set(X.block(b).tolist()) for b in X.REGISTERED["pilot"]["blocks"]]
    assert sum(len(s) for s in ids) == len(set().union(*ids))


def test_a_killed_attempt_is_reconciled(X, tmp_path, monkeypatch):
    """A start marker without a record: the frame charges the attempt plus the registered tail."""
    monkeypatch.setattr(X.E, "OUT", tmp_path)
    marker = tmp_path / "pilot-started.json"
    marker.write_text(json.dumps({"started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}), encoding="utf-8")
    got = X.E.reconcile_kill("pilot", [tmp_path / "pilot.json", marker])
    doc = json.loads((tmp_path / "compute" / got["file"]).read_text(encoding="utf-8"))
    assert doc["tail_seconds"] == X.REGISTERED["rerun_kill_tail_seconds"] and got["seconds"] >= doc["tail_seconds"]


def test_without_the_tail_the_reconciliation_fails(X, tmp_path, monkeypatch):
    """The sabotage: E2's frame reads the registered tail, so a registry without it cannot reconcile a kill."""
    monkeypatch.setattr(X.E, "OUT", tmp_path)
    monkeypatch.delitem(X.REGISTERED, "rerun_kill_tail_seconds")
    marker = tmp_path / "pilot-started.json"
    marker.write_text(json.dumps({"started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}), encoding="utf-8")
    with pytest.raises(KeyError):
        X.E.reconcile_kill("pilot", [tmp_path / "pilot.json", marker])
