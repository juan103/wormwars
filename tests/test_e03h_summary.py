"""03h's summary (scripts/e03h_summary.py): the committed summary.json is exactly what the committed records give, so
RESULTS.md's numbers trace to them (AGENTS.md rule 5)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location("e03h_summary_test", ROOT / "scripts" / "e03h_summary.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    return M


def test_the_committed_summary_is_what_the_records_give():
    M = _module()
    committed = json.loads((M.EXP / "summary.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(M.build())) == committed


def test_a_changed_record_changes_the_summary(monkeypatch):
    """Sabotage: the comparison above can fail."""
    M = _module()
    real = M.rec

    def changed(path):
        d = real(path)
        if path.name == "amplitude-check.json":
            d["readings"]["1.0"]["decile_shift"]["mean"] += 0.01
        return d

    monkeypatch.setattr(M, "rec", changed)
    committed = json.loads((M.EXP / "summary.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(M.build())) != committed


def test_the_power_rerun_without_arrays_leaves_the_committed_record(tmp_path, monkeypatch):
    """Without the pilot's local arrays, b_power.py writes elsewhere, so the summary's input stays as committed (the
    review of RESULTS.md: Fable 7, Astra 8)."""
    spec = importlib.util.spec_from_file_location(
        "b_power_test", ROOT / "experiments" / "03h-history-use" / "development-records" / "b_power.py")
    B = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(B)
    committed = B.OUT.read_bytes()
    monkeypatch.setattr(B, "ARRAYS", tmp_path / "missing")
    monkeypatch.setattr(B, "OUT_WITHOUT_ARRAYS", tmp_path / "b-power-without-arrays.json")
    monkeypatch.setattr(B, "SIMS", 200)
    out = B.main()
    assert out["selection_bank_relief_minus_sham"] is None
    assert B.OUT.read_bytes() == committed
    assert json.loads((tmp_path / "b-power-without-arrays.json").read_text(encoding="utf-8"))["pass_rate"]
