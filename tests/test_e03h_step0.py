"""03h's step 0 (scripts/e03h_step0.py; DESIGN.md §7.2, annotated 2026-10-19), on the CPU at smoke size:
- its records have the registered shape;
- when no verification check is bit-equal, step 0 is dropped before any measurement;
- a bit-equal fitness replay, or a bit-equal world-free history check, in any mode, lets it proceed;
- the formal path refuses a dirty tree;
- the inputs are guarded.

The CPU genomes are not 03's CUDA genomes, so smoke numbers mean nothing; the formal step 0 runs on CUDA."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.slow  # each call rebuilds SH graphs and rolls out on the CPU (Fable)


@pytest.fixture()
def M():
    spec = importlib.util.spec_from_file_location("e03h_step0_test", ROOT / "scripts" / "e03h_step0.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _v(fit: bool, hist: bool, mode="replay"):
    return {"mode": mode, "graph": "pilotSH101", "fitness": {"bit_equal": fit}, "history": {"bit_equal": hist}}


def test_step0_smoke_writes_the_registered_shape(M):
    out = M.run(smoke=True)
    v = out["verification"]["cpu"]
    assert v["graph"] == "pilotSH101" and set(v["fitness"]) >= {"bit_equal", "unequal_values", "genomes"}
    assert set(v["history"]["parts"]) == {f"{k}.{p}" for k in ("raw_turn", "raw_forward")
                                          for p in ("final", "after", "steady_contrast")}
    assert len(out["graphs"]) == 2 and out["exploratory"] is True and out["summary"]["graphs"] == 2
    for r in out["graphs"].values():
        assert -1 <= r["rho_level"] <= 1 and isinstance(r["degenerate"], bool)
    assert set(out["inputs"]) == {"experiments/03-generation0/pilot.json", "experiments/02-screening/remaps.json"}


def test_no_bit_equal_check_drops_step0_before_measuring(M, monkeypatch):
    monkeypatch.setattr(M, "measure", lambda smoke: pytest.fail("measured after a failed verification"))
    out = M.run(smoke=True, enforce=True, verifications={"default": _v(False, False, "default"),
                                                         "replay": _v(False, False)})
    assert "dropped" in out and not out["graphs"] and out["verified_by"] == []


@pytest.mark.parametrize("fit,hist", [(True, False), (False, True)])
def test_one_bit_equal_check_in_one_mode_lets_step0_proceed(M, monkeypatch, fit, hist):
    monkeypatch.setattr(M, "measure", lambda smoke: {"g": {"rho_level": 0.1, "degenerate": False}})
    out = M.run(smoke=True, enforce=True, verifications={"default": _v(fit, hist, "default"),
                                                         "replay": _v(False, False)})
    assert "dropped" not in out and out["verified_by"] == ["default"] and out["graphs"]


def test_the_formal_path_refuses_a_dirty_tree(M, monkeypatch):
    monkeypatch.setattr(M.reg, "provenance", lambda guarded: {"dirty": True})
    with pytest.raises(SystemExit, match="uncommitted"):
        M.main([])


def test_the_inputs_are_guarded(M):
    assert {"experiments/03-generation0/pilot.json", "experiments/02-screening/remaps.json"} <= set(M.GUARDED)
