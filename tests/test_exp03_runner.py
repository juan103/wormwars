"""Experiment 03's runner (D054): N2 is measured last, the time cap is cumulative across
restarts, graph files are checked against the committed manifest, and every measurement records
its provenance."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def exp():
    spec = importlib.util.spec_from_file_location("exp03_script", ROOT / "scripts" / "exp03.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_n2_and_its_variants_are_measured_last(exp):
    order = exp.run_order()
    assert order[-5:] == ["N2", "N2-rev", "N2perm1", "N2perm2", "N2perm3"]
    assert len(order) == 645 and len(set(order)) == 645


def test_a_graph_file_that_does_not_match_the_manifest_is_refused(exp, tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "GRAPHS", tmp_path)
    name = "SH-10000"
    np.savez_compressed(tmp_path / f"{name}.npz", chem=np.zeros((2, 2)), gap=np.zeros((2, 2)))
    from wormwars.connectome import load_connectome
    with pytest.raises(exp.ProvenanceError):
        exp._load_graph(load_connectome(), name)


def test_the_time_cap_counts_every_saved_measurement(exp, tmp_path, monkeypatch):
    monkeypatch.setattr(exp, "MEASURES", tmp_path)
    for i, s in enumerate((1800.0, 1800.0)):
        (tmp_path / f"g{i}.json").write_text(json.dumps({"seconds": {"a": s}}), encoding="utf-8")
    assert exp.spent_hours() == pytest.approx(1.0)


def test_provenance_is_recorded_and_checked(exp):
    p = exp.provenance("cpu")
    assert {"git_commit", "inputs", "device"} <= set(p)
    assert set(p["inputs"]) >= {"ensembles.json", "graphs_manifest.json", "pilot.json", "mirror_pairs.yaml", "remaps.json"}
    exp.check_provenance([{"provenance": p}, {"provenance": p}])
    q = dict(p, git_commit="different")
    with pytest.raises(exp.ProvenanceError):
        exp.check_provenance([{"provenance": p}, {"provenance": q}])
