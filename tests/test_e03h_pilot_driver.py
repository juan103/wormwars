"""03h's pilot driver (scripts/e03h.py; PILOT.md) end to end at smoke size on the CPU: every stage completes in order
and writes its registered readings; a stage refuses without the one before; a changed PILOT.md is refused; P' at 0.5
is refused unless a P at 0.25 failed to move the decile shift."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.slow


def _module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "e03h.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    M = _module("e03h_driver_test")
    tmp = tmp_path_factory.mktemp("e03h")
    M.out_dir = lambda: tmp / "pilot"
    M.rec_dir = lambda: tmp / "pilot" / "records"
    docs = {s: M.main([s, "--smoke"]) for s in M.STAGES}
    return M, tmp, docs


def test_every_stage_completes_with_its_readings(run):
    M, _, docs = run
    assert all(d["status"] == "completed" for d in docs.values())
    g1 = docs["gate"]
    assert set(g1["verdicts"]) == {"level", "relief", "recovered_share"}
    assert set(g1["families"]) >= {"memoryless", "memoryless+bit", "memory", "memory+bit"}
    s1 = docs["sham-rates"]
    assert len(s1["rates"]) == 2 and all(0 <= r <= 1 for r in s1["rates"]) and sum(s1["counts"]) > 0
    p = docs["pilot"]
    r = p["readings"]
    assert r["W"] in (16, 32) and "power_A2_reported" in r and "decile_shift" in r["manipulation"]
    assert len(p["per_graph"]) == len(s1["graphs"]) and p["action"]
    assert len(r["B"]["U"]) == len(s1["graphs"])


def test_a_stage_without_its_predecessor_is_refused(tmp_path):
    M = _module("e03h_driver_test_b")
    M.out_dir = lambda: tmp_path / "pilot"
    M.rec_dir = lambda: tmp_path / "pilot" / "records"
    M.main(["bind", "--smoke"])
    with pytest.raises(SystemExit):
        M.main(["sham-rates", "--smoke"])


def test_a_changed_pilot_md_is_refused(run, monkeypatch):
    M, tmp, _ = run
    p = tmp / "pilot" / "records" / "bind.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    good = doc["pilot_md_sha256"]
    doc["pilot_md_sha256"] = "0" * 64
    p.write_text(json.dumps(doc), encoding="utf-8")
    try:
        with pytest.raises(SystemExit, match="bound"):
            M.main(["gate", "--smoke", "--rerun", "--reason", "test"])
    finally:
        doc["pilot_md_sha256"] = good
        p.write_text(json.dumps(doc), encoding="utf-8")


def test_the_amplitude_rule_is_enforced(run):
    M, tmp, docs = run
    if docs["pilot"]["readings"]["manipulation"]["decile_shift"]["moves"]:
        with pytest.raises(SystemExit, match="only after"):
            M.main(["pilot", "--smoke", "--amplitude", "0.5", "--rerun", "--reason", "test"])
    with pytest.raises(SystemExit):
        M.main(["pilot", "--smoke", "--amplitude", "0.3"])
