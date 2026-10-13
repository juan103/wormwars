"""E4-D's runner (scripts/e4d.py; design v2.3): the freeze is enforced between stages (Astra, D260)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def X(tmp_path, monkeypatch):
    s = importlib.util.spec_from_file_location("e4d_under_test", ROOT / "scripts" / "e4d.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    monkeypatch.setattr(m, "EXP", tmp_path)
    monkeypatch.setattr(m, "provenance", lambda: {"git_commit": head, "dirty": False})
    return m, head


def _scout(m, head, **over):
    rec = {"registered": json.loads(json.dumps(m.REGISTERED)), "provenance": {"git_commit": head, "dirty": False}, **over}
    (m.EXP / "scout.json").write_text(json.dumps(rec), encoding="utf-8")


def test_a_later_stage_runs_after_a_matching_earlier_record(X):
    m, head = X
    _scout(m, head)
    m.guard("calibrate", after=("scout",))


def test_a_changed_registration_is_refused(X):
    m, head = X
    reg = json.loads(json.dumps(m.REGISTERED))
    reg["H_t"] = 601
    _scout(m, head, registered=reg)
    with pytest.raises(SystemExit):
        m.guard("calibrate", after=("scout",))


def test_a_missing_earlier_record_is_refused(X):
    m, _ = X
    with pytest.raises(SystemExit):
        m.guard("calibrate", after=("scout",))
