"""Experiment 03's report end to end on the shuffle-only pilot data, with one pilot shuffle
standing in for N2 (both reviewers: prove the analysis before any N2 run)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from wormwars.exp03 import report as R

PILOT = Path(__file__).parents[1] / "experiments" / "03-generation0" / "pilot.json"


@pytest.fixture(scope="module")
def pilot():
    return json.loads(PILOT.read_text(encoding="utf-8"))


def test_report_runs_on_pilot_data_with_a_stand_in(pilot):
    measures = {m["name"]: m for m in pilot["graphs"]}
    names = sorted(measures)
    n2, rest = names[0], names[1:]
    out = R.build(measures, n2, {"A": rest[:8], "B": rest[8:]}, n_boot=100, min_graphs=1)
    json.dumps(out)
    for s in R.PRIMARY:
        summ = out["signals"][s + "_summary"]
        assert summ["overall"] in {"distinctive relative to every ensemble", "reversed against every ensemble",
                                   "not distinctive"}
        for e in ("A", "B"):
            r = out["signals"][s][e]
            assert np.isfinite(r["n2"]) and r["n2_se"] > 0 and r["graphs"] > 0
            assert r["verdict"] in {"distinctive", "reversed", "consistent", "inconclusive"}


def test_a_stand_in_from_the_same_ensemble_is_never_distinctive_with_eight_graphs(pilot):
    """With 8 graphs the smallest rank p is 1/9, above every Holm threshold: nothing can be
    distinctive, which is the right answer for an exchangeable stand-in."""
    measures = {m["name"]: m for m in pilot["graphs"]}
    names = sorted(measures)
    out = R.build(measures, names[0], {"A": names[1:9]}, n_boot=50, min_graphs=1)
    assert all(out["signals"][s + "_summary"]["overall"] == "not distinctive" for s in R.PRIMARY)
