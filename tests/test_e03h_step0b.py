"""03h's step 0b (scripts/e03h_step0b.py; D330): at smoke size on the CPU, the five specified read-outs are reported
per graph and summarised (the CPU genomes are not 03's, so the numbers mean nothing)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.slow


def test_step0b_reports_the_five_specified_readouts():
    spec = importlib.util.spec_from_file_location("e03h_step0b_test", ROOT / "scripts" / "e03h_step0b.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    out = m.run(smoke=True)
    assert set(out["summary"]) == set(m.READOUTS) and len(out["graphs"]) == 2
    for r in out["graphs"].values():
        assert set(r) == set(m.READOUTS) and all(-1 <= x <= 1 for x in r.values())
