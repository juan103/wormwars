"""The memory thread's summary (scripts/memory_summary.py): the committed summary.json is exactly what the committed
records give, so SYNTHESIS.md's numbers trace to them (AGENTS.md rule 5)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location("memory_summary_test", ROOT / "scripts" / "memory_summary.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    return M


def test_the_committed_summary_is_what_the_records_give():
    M = _module()
    committed = json.loads(M.OUT.read_text(encoding="utf-8"))
    assert json.loads(json.dumps(M.build())) == committed


def test_a_changed_record_changes_the_summary(monkeypatch):
    """Sabotage: the comparison above can fail."""
    M = _module()
    real = M.rec

    def changed(path):
        d = real(path)
        if path.parent.name == "memory-m4d" and path.name == "readings.json":
            d["counts"]["separate"]["T"][0] += 1
        return d

    monkeypatch.setattr(M, "rec", changed)
    committed = json.loads(M.OUT.read_text(encoding="utf-8"))
    assert json.loads(json.dumps(M.build())) != committed


def test_a_failed_attempt_stops_the_summary(monkeypatch):
    M = _module()
    real = M.rec

    def failed(path):
        d = real(path)
        if path.name == "m4b-compute-record.json":
            d["failed_attempts"] = 1
        return d

    monkeypatch.setattr(M, "rec", failed)
    try:
        M.build()
    except SystemExit:
        return
    raise AssertionError("a failed attempt did not stop the summary")


def test_a_pilot_check_without_its_verdict_stops_the_summary(monkeypatch):
    """A renamed or missing verdict must not pass silently (Fable, synthesis review round 1)."""
    M = _module()
    real = M.rec

    def renamed(path):
        d = real(path)
        if path.parent.name == "memory-m2" and path.name == "summary.json":
            d["checks"]["R2"]["passed"] = d["checks"]["R2"].pop("passes")
        return d

    monkeypatch.setattr(M, "rec", renamed)
    try:
        M.build()
    except SystemExit:
        return
    raise AssertionError("a missing verdict did not stop the summary")


def test_a_changed_m4e_or_m5_record_changes_the_summary(monkeypatch):
    """Sabotage for the M4e and M5 parts added with the synthesis's draft 4."""
    M = _module()
    real = M.rec
    committed = json.loads(M.OUT.read_text(encoding="utf-8"))
    for folder, name, change in (
            ("memory-m4e", "readings.json", lambda d: d["counts"]["separate"]["T"].__setitem__(0, 99)),
            ("memory-m5-pilot", "report.json", lambda d: d["audit"]["by_arm"]["Rr"].__setitem__("fading_to_separate", 1)),
            ("memory-m5-power-welch", "power.json", lambda d: d["answer"]["choice"].__setitem__("recommend", "A"))):
        def changed(path, folder=folder, name=name, change=change):
            d = real(path)
            if path.parent.name == folder and path.name == name:
                change(d)
            return d

        monkeypatch.setattr(M, "rec", changed)
        assert json.loads(json.dumps(M.build())) != committed, folder


def test_a_changed_m6_0_record_changes_the_summary(monkeypatch):
    """Sabotage for M6's option 0 (D377): its reading and its compute record reach the summary (against a fresh
    build, not the committed file, so a script that ignores them fails)."""
    M = _module()
    real = M.rec
    unchanged = json.loads(json.dumps(M.build()))
    for name, change in (
            ("reading.json", lambda d: d["primary"].__setitem__("g39_switches", 5)),
            ("reading.json", lambda d: d["secondary"].__setitem__("persistence", "lengthened")),
            ("m6-0-compute-record.json", lambda d: d["totals"].__setitem__("seconds_timed", 1.0))):
        def changed(path, name=name, change=change):
            d = real(path)
            if path.parent.name == "memory-m6-0" and path.name == name:
                change(d)
            return d

        monkeypatch.setattr(M, "rec", changed)
        assert json.loads(json.dumps(M.build())) != unchanged, name


def test_a_changed_m6_outlast_record_changes_the_summary(monkeypatch):
    """Sabotage for M6's step 1 (D381): its reading and compute record reach the summary (against a fresh build)."""
    M = _module()
    real = M.rec
    unchanged = json.loads(json.dumps(M.build()))
    for name, change in (
            ("reading.json", lambda d: d["Z"]["held"].__setitem__("held", 0)),
            ("outlast-compute-record.json", lambda d: d["totals"].__setitem__("seconds_timed", 1.0))):
        def changed(path, name=name, change=change):
            d = real(path)
            if path.parent.name == "memory-m6-outlast" and path.name == name:
                change(d)
            return d

        monkeypatch.setattr(M, "rec", changed)
        assert json.loads(json.dumps(M.build())) != unchanged, name


def test_a_changed_m6_step2_record_changes_the_summary(monkeypatch):
    """Sabotage for M6's step 2 (D383): its reading and compute record reach the summary (against a fresh build)."""
    M = _module()
    real = M.rec
    unchanged = json.loads(json.dumps(M.build()))
    for name, change in (
            ("reading.json", lambda d: d["primary"].__setitem__("mean", 0.0)),
            ("reading.json", lambda d: d["T0"]["T1_minus_T0_0.25_matched"].__setitem__("mean", 0.0)),
            ("step2-compute-record.json", lambda d: d["totals"].__setitem__("seconds_timed", 1.0))):
        def changed(path, name=name, change=change):
            d = real(path)
            if path.parent.name == "memory-m6-step2" and path.name == name:
                change(d)
            return d

        monkeypatch.setattr(M, "rec", changed)
        assert json.loads(json.dumps(M.build())) != unchanged, name
