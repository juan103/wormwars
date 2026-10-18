"""03a's exploratory summary (scripts/e03a_summary.py): the committed summary.json is exactly what the committed
records give, so RESULTS.md's numbers trace to them (AGENTS.md rule 5)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location("e03a_summary_test", ROOT / "scripts" / "e03a_summary.py")
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

    def changed(stage):
        d = real(stage)
        if stage == "baseline":
            d["mip_intact_mean"] += 0.01
        return d

    monkeypatch.setattr(M, "rec", changed)
    committed = json.loads((M.EXP / "summary.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(M.build())) != committed
