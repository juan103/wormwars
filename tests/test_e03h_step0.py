"""03h's step 0 (scripts/e03h_step0.py; DESIGN.md §7.2) at smoke size on the CPU: its records have the registered
shape; a replay that is not bit-equal drops step 0 before any history is measured, and a bit-equal one lets it
proceed (Astra); its provenance guards and hashes the inputs it reads. (The CPU genomes are not 03's CUDA genomes, so
smoke numbers mean nothing; the formal step 0 runs on CUDA.)"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def M():
    spec = importlib.util.spec_from_file_location("e03h_step0_test", ROOT / "scripts" / "e03h_step0.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def committed(n):
    p = json.loads((ROOT / "experiments" / "03-generation0" / "pilot.json").read_text(encoding="utf-8"))
    rec = next(g for g in p["graphs"] if g["name"] == "pilotSH101")
    return np.asarray(rec["fitness"]["T1-M0"], dtype=np.float32)[:n]


class Fake:
    def __init__(self, score):
        self.score = score


def test_step0_smoke_writes_the_registered_shape(M):
    out = M.run(smoke=True)
    v = out["verification"]
    assert v["graph"] == "pilotSH101" and set(v) >= {"unequal_values", "max_difference", "bit_equal", "mode"}
    assert len(out["graphs"]) == 2 and out["exploratory"] is True
    for r in out["graphs"].values():
        assert -1 <= r["rho_level"] <= 1 and isinstance(r["degenerate"], bool)
    assert out["summary"]["graphs"] == 2
    assert set(out["inputs"]) == {"experiments/03-generation0/pilot.json", "experiments/02-screening/remaps.json"}


def test_a_replay_that_is_not_bit_equal_drops_step0_before_history(M, monkeypatch):
    monkeypatch.setattr(M, "rollout", lambda *a, **k: Fake(committed(16) + np.float32(1e-6)))
    called = []
    monkeypatch.setattr(M, "history", lambda *a, **k: called.append(1))
    out = M.run(smoke=True, enforce=True)
    assert "dropped" in out and not out["graphs"] and not called
    assert out["verification"]["bit_equal"] is False and out["verification"]["unequal_values"] > 0


def test_a_bit_equal_replay_lets_step0_proceed(M, monkeypatch):
    monkeypatch.setattr(M, "rollout", lambda *a, **k: Fake(committed(16)))
    out = M.run(smoke=True, enforce=True)
    assert out["verification"]["bit_equal"] is True and "dropped" not in out and len(out["graphs"]) == 2


def test_the_inputs_are_guarded(M):
    assert {"experiments/03-generation0/pilot.json", "experiments/02-screening/remaps.json"} <= set(M.GUARDED)
