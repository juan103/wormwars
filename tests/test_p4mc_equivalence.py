"""03mc's pre-run check (`scripts/p4mc_equivalence.py`): its judgement of labels and tolerances, on the CPU."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def q():
    spec = importlib.util.spec_from_file_location("p4mc_equivalence_test", ROOT / "scripts" / "p4mc_equivalence.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_label_gate_counts_every_genome_with_any_changed_label(q):
    """Astra (review v2.1): two genomes changing "settled" and two others changing "remaining" are four genomes,
    above the limit of two, though each label alone changes only two."""
    n = 10
    a = {"settled": np.zeros(n, bool), "remaining": np.zeros(n, bool)}
    b = {"settled": np.zeros(n, bool), "remaining": np.zeros(n, bool)}
    b["settled"][[0, 1]] = True
    b["remaining"][[2, 3]] = True
    a["both"], b["both"] = a["settled"] & a["remaining"], b["settled"] & b["remaining"]
    ch = q.label_changes(a, b)
    assert ch["any"] == 4 and ch["settled"] == 2 and ch["remaining"] == 2
    row = q.judge({"deviation": {}, "label_changes": ch})
    assert not row["passed"] and "labels.any" in row["failed"]
    b["remaining"][[2, 3]] = False
    ok = q.judge({"deviation": {}, "label_changes": q.label_changes(a, b)})
    assert ok["passed"]


def test_a_deviation_above_its_tolerance_fails(q):
    row = q.judge({"deviation": {"terms": 2e-5, "curve": 1e-3}, "label_changes": {"any": 0}})
    assert row["failed"] == ["terms"] and not row["passed"]
