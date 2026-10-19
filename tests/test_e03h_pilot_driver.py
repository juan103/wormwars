"""03h's pilot driver (scripts/e03h.py; PILOT.md), at smoke size on the CPU. It checks that:
- every stage completes in order and writes its registered readings;
- a stage refuses without the one before, on a changed PILOT.md, on a stale upstream record, and on an exhausted cap;
- a calibration failure takes the next seed, and P rebuilds S1's accepted seeds;
- smoke and registered ranges are disjoint;
- the amplitude rule's branches, its single escalation, and the budget's precedence hold (Astra, Fable)."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.slow


def _module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "e03h.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _into(M, tmp):
    M.out_dir = lambda: tmp / "pilot"
    M.rec_dir = lambda: tmp / "pilot" / "records"
    return M


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("e03h")
    M = _into(_module("e03h_driver_test"), tmp)
    docs = {s: M.main([s, "--smoke"]) for s in M.STAGES}
    return M, tmp, docs


def test_every_stage_completes_with_its_readings(run):
    M, _, docs = run
    assert all(d["status"] == "completed" for d in docs.values())
    g1 = docs["gate"]
    assert set(g1["verdicts"]) == {"level", "relief", "recovered_share"}
    assert set(g1["families"]) >= {"memoryless", "memoryless+bit", "memory", "memory+bit"}
    assert all("edges" in f for f in g1["families"].values())
    s1 = docs["sham-rates"]
    assert len(s1["rates"]) == 2 and all(0 <= r <= 1 for r in s1["rates"]) and sum(s1["counts"]) > 0
    assert all("genome_sha256" in r for r in s1["graphs"])
    g2 = docs["gate-sham"]
    assert g2["families"]["memoryless"] == g1["families"]["memoryless"]  # reused, not re-tuned (Fable)
    p = docs["pilot"]
    r = p["readings"]
    assert r["W"] in (16, 32) and "power_A2_reported" in r and "decile_shift" in r["manipulation"]
    assert len(p["per_graph"]) == len(s1["graphs"]) and p["action"]
    assert all("quartile_difference_level" in g and g["realised_food_fell_counts"]["sham"] for g in p["per_graph"])
    assert p["arrays_npz_sha256"] and r["projection"]["hours"]
    assert p["upstream"].keys() == {"gate-sham", "sham-rates", "gate"}


def test_smoke_and_registered_ranges_are_disjoint():
    M = _module("e03h_driver_test_ranges")

    def spans(c):
        g = c["gate"]
        return [tuple(g["tuning"]), tuple(g["check"]), tuple(c["selection"]), tuple(c["test"])]

    reg = {i for a, n in spans(M.CFG) for i in range(a, a + n)}
    smk = {i for a, n in spans({**M.CFG, **M.SMOKE_CFG}) for i in range(a, a + n)}
    assert not reg & smk
    seeds = lambda c: set(c["gate"]["seeds"]) | set(c["run_seeds"]) | set(c["boot_seeds"]) | {  # noqa: E731
        c["calibration"]["seed"], c["graphs"]["first_seed"]}
    assert not seeds(M.CFG) & seeds({**M.CFG, **M.SMOKE_CFG})


def test_a_stage_without_its_predecessor_is_refused(tmp_path):
    M = _into(_module("e03h_driver_test_b"), tmp_path)
    M.main(["bind", "--smoke"])
    with pytest.raises(SystemExit):
        M.main(["sham-rates", "--smoke"])


def test_a_changed_pilot_md_is_refused(run):
    M, tmp, _ = run
    p = tmp / "pilot" / "records" / "bind.json"
    original = p.read_bytes()
    doc = json.loads(original)
    doc["pilot_md_sha256"] = "0" * 64
    p.write_text(json.dumps(doc), encoding="utf-8")
    try:
        with pytest.raises(SystemExit, match="bound"):
            M.main(["gate", "--smoke", "--rerun", "--reason", "test"])
    finally:
        p.write_bytes(original)  # byte for byte, so downstream records stay fresh


def test_a_stale_upstream_record_is_refused(run, tmp_path):
    M, tmp, _ = run
    work = tmp_path / "copy"
    shutil.copytree(tmp / "pilot", work / "pilot")
    M2 = _into(_module("e03h_driver_test_stale"), work)
    p = work / "pilot" / "records" / "sham-rates.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    doc["rates"] = [0.5, 0.5]  # S1 changed after G2 read it
    p.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(SystemExit, match="stale"):
        M2.main(["pilot", "--smoke", "--rerun", "--reason", "test"])


def test_an_exhausted_cap_refuses_a_stage(run, tmp_path, monkeypatch):
    M, tmp, _ = run
    work = tmp_path / "copy"
    shutil.copytree(tmp / "pilot", work / "pilot")
    M2 = _into(_module("e03h_driver_test_cap"), work)
    monkeypatch.setattr(M2.Clock, "spent_hours", lambda self: 5.0)
    with pytest.raises(M2.reg.CapReached):
        M2.main(["gate", "--smoke", "--rerun", "--reason", "test"])


def test_a_failed_calibration_takes_the_next_seed(run, tmp_path, monkeypatch):
    M, tmp, _ = run
    work = tmp_path / "copy"
    shutil.copytree(tmp / "pilot", work / "pilot")
    M2 = _into(_module("e03h_driver_test_cal"), work)
    real, calls = M2.calib.calibrate_in_world, {"n": 0}

    def fail_first(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("no convergence (test)")
        return real(*a, **k)

    monkeypatch.setattr(M2.calib, "calibrate_in_world", fail_first)
    s1 = M2.main(["sham-rates", "--smoke", "--rerun", "--reason", "test"])
    first = M2.cfg()["graphs"]["first_seed"]
    assert s1["failures"][0] == {"seed": first, "failed": "calibration", "error": "no convergence (test)"}
    assert [r["seed"] for r in s1["graphs"]] == [first + 1, first + 2]
    M2.main(["gate-sham", "--smoke", "--rerun", "--reason", "test"])
    p = M2.main(["pilot", "--smoke", "--rerun", "--reason", "test"])  # P rebuilds S1's accepted seeds
    assert [g["name"] for g in p["per_graph"]] == [r["name"] for r in s1["graphs"]]


def test_the_amplitude_branches_and_the_single_escalation(run, tmp_path, monkeypatch):
    M, tmp, _ = run
    work = tmp_path / "copy"
    shutil.copytree(tmp / "pilot", work / "pilot")
    M2 = _into(_module("e03h_driver_test_amp"), work)
    real = M2.PL.b_readings

    def still(*a, **k):
        r = real(*a, **k)
        r["decile_shift"] = {**r["decile_shift"], "moves": False, "lo": -0.01}
        return r

    monkeypatch.setattr(M2.PL, "b_readings", still)
    monkeypatch.setattr(M2, "_projection", lambda *a: {"fits": True, "plan": {"W_t": 64, "SH": False}})
    p = M2.main(["pilot", "--smoke", "--rerun", "--reason", "test: no shift"])
    assert p["action"].startswith("rerun as P'")
    p2 = M2.main(["pilot", "--smoke", "--amplitude", "0.5", "--rerun", "--reason", "test: P'"])
    assert p2["amplitude"] == 0.5 and p2["action"].startswith("stop: redesign")
    with pytest.raises(SystemExit, match="already raised"):
        M2.main(["pilot", "--smoke", "--amplitude", "0.5", "--rerun", "--reason", "test: twice"])


def test_p_prime_is_refused_after_a_moving_p(run, tmp_path, monkeypatch):
    M, tmp, _ = run
    work = tmp_path / "copy"
    shutil.copytree(tmp / "pilot", work / "pilot")
    M2 = _into(_module("e03h_driver_test_amp2"), work)
    real = M2.PL.b_readings

    def moving(*a, **k):
        r = real(*a, **k)
        r["decile_shift"] = {**r["decile_shift"], "moves": True, "lo": 0.01}
        return r

    monkeypatch.setattr(M2.PL, "b_readings", moving)
    monkeypatch.setattr(M2, "_projection", lambda *a: {"fits": True, "plan": {"W_t": 64, "SH": False}})
    p = M2.main(["pilot", "--smoke", "--rerun", "--reason", "test: shift"])
    assert p["action"] == "proceed to the pre-registration"
    with pytest.raises(SystemExit, match="only after"):
        M2.main(["pilot", "--smoke", "--amplitude", "0.5", "--rerun", "--reason", "test"])


def test_the_budget_takes_precedence_over_the_amplitude_rule(run, tmp_path, monkeypatch):
    M, tmp, _ = run
    work = tmp_path / "copy"
    shutil.copytree(tmp / "pilot", work / "pilot")
    M2 = _into(_module("e03h_driver_test_budget"), work)
    real = M2.PL.b_readings
    monkeypatch.setattr(M2.PL, "b_readings",
                        lambda *a, **k: {**real(*a, **k), "decile_shift": {"moves": False, "lo": -1, "hi": 0,
                                                                           "mean": 0, "per_graph": []}})
    monkeypatch.setattr(M2, "_projection", lambda *a: {"fits": False, "plan": None})
    p = M2.main(["pilot", "--smoke", "--rerun", "--reason", "test: budget"])
    assert p["action"].startswith("stop: redesign (no formal plan fits")


def _still(M2, monkeypatch):
    real = M2.PL.b_readings

    def still(*a, **k):
        r = real(*a, **k)
        r["decile_shift"] = {**r["decile_shift"], "moves": False, "lo": -0.01}
        return r

    monkeypatch.setattr(M2.PL, "b_readings", still)
    monkeypatch.setattr(M2, "_projection", lambda *a: {"fits": True, "plan": {"W_t": 64, "SH": False}})


def test_a_failed_p_prime_may_be_retried(run, tmp_path, monkeypatch):
    M, tmp, _ = run
    work = tmp_path / "copy"
    shutil.copytree(tmp / "pilot", work / "pilot")
    M2 = _into(_module("e03h_driver_test_retry"), work)
    _still(M2, monkeypatch)
    M2.main(["pilot", "--smoke", "--rerun", "--reason", "test: no shift"])
    real = M2.history

    def broken(*a, **k):
        raise RuntimeError("interrupted (test)")

    monkeypatch.setattr(M2, "history", broken)
    with pytest.raises(RuntimeError, match="interrupted"):
        M2.main(["pilot", "--smoke", "--amplitude", "0.5", "--rerun", "--reason", "test: P' fails"])
    monkeypatch.setattr(M2, "history", real)
    p2 = M2.main(["pilot", "--smoke", "--amplitude", "0.5", "--rerun", "--reason", "test: P' retried"])
    assert p2["status"] == "completed" and p2["amplitude"] == 0.5


def test_p_prime_needs_a_p_on_the_current_chain(run, tmp_path, monkeypatch):
    """A qualifying P on G1, S1 and G2 records since replaced does not authorise P' (Astra, round 2)."""
    M, tmp, _ = run
    work = tmp_path / "copy"
    shutil.copytree(tmp / "pilot", work / "pilot")
    M2 = _into(_module("e03h_driver_test_chain"), work)
    _still(M2, monkeypatch)
    M2.main(["pilot", "--smoke", "--rerun", "--reason", "test: no shift"])
    g2 = work / "pilot" / "records" / "gate-sham.json"
    doc = json.loads(g2.read_text(encoding="utf-8"))
    doc["rerun_reason"] = "a new G2 record (test)"  # G2 replaced after P: P's chain is no longer the current one
    g2.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(SystemExit, match="current"):
        M2.main(["pilot", "--smoke", "--amplitude", "0.5", "--rerun", "--reason", "test"])


def test_a_refused_rerun_leaves_the_record_in_place(run, tmp_path, monkeypatch):
    """Eligibility and the cap are checked before a rerun moves the old record aside (Fable, round 2)."""
    M, tmp, _ = run
    work = tmp_path / "copy"
    shutil.copytree(tmp / "pilot", work / "pilot")
    M2 = _into(_module("e03h_driver_test_refused"), work)
    rec = work / "pilot" / "records"
    before = (rec / "pilot.json").read_bytes()
    with pytest.raises(SystemExit):  # the smoke P moved, so P' is not eligible
        M2.main(["pilot", "--smoke", "--amplitude", "0.5", "--rerun", "--reason", "test"])
    monkeypatch.setattr(M2.Clock, "spent_hours", lambda self: 5.0)
    with pytest.raises(M2.reg.CapReached):
        M2.main(["pilot", "--smoke", "--rerun", "--reason", "test"])
    assert (rec / "pilot.json").read_bytes() == before and not list(rec.glob("pilot.attempt*.json"))


def test_the_end_of_stage_cap_counts_the_attempt_once(tmp_path):
    """After the aggregate holds an attempt, its time is not added again (Fable, Astra, round 2)."""
    M = _module("e03h_driver_test_clock")
    path = tmp_path / "compute.json"
    path.write_text(json.dumps({"totals": {"seconds_timed": 3600 * 0.6}}), encoding="utf-8")
    ck = M.Clock(1.0, path)
    ck.t_start -= 3600 * 0.6  # this attempt's 0.6 h, already in the aggregate
    assert not ck.over_at_end()
    path.write_text(json.dumps({"totals": {"seconds_timed": 3600 * 1.1}}), encoding="utf-8")
    assert ck.over_at_end()


def test_s1_times_the_sampler_apart_and_the_projection_leaves_it_out(run):
    """DESIGN §8 counts GPU work only: the sampler's CPU seconds are reported but not projected (Astra, round 2)."""
    M, _, docs = run
    s = docs["sham-rates"]["seconds_s1"]
    assert s["sampler_cpu"] > 0 and s["calibration"] > 0
    timing = [{"selection_relief": 1.0, "selection_sham": 1.0, "test_level": 1.0, "test_relief": 1.0,
               "test_sham": 1.0, "history_and_probe": 0.0}]
    a = M._projection(timing, {"seconds_s1": {"sampler_cpu": 0.0, "calibration": 10.0}}, 16)
    b = M._projection(timing, {"seconds_s1": {"sampler_cpu": 1000.0, "calibration": 10.0}}, 16)
    assert a["per_graph_seconds"] == b["per_graph_seconds"]
    assert b["sampler_cpu_seconds_per_graph_not_counted"] == 1000.0


def test_binding_fixes_the_implementation(run):
    """bind records its commit; afterwards the implementation (CODE) may not change (Astra, round 2)."""
    M, _, docs = run
    assert docs["bind"]["bound_commit"] == M.reg.git("rev-parse", "HEAD")
    assert "experiments/03h-history-use/pilot/bind.json" not in M.CODE and "wormwars" in M.CODE
    with pytest.raises(SystemExit, match="changed since"):
        M.reg.require_same_code("4fae0d1", M.CODE)  # scripts/e03h.py changed after D332
    M.reg.require_same_code(M.reg.git("rev-parse", "HEAD"), M.CODE)


def test_a_cap_during_s1_keeps_the_failure_trail(run, tmp_path, monkeypatch):
    """S1's failures are recorded as they happen, so a stop part-way keeps them (Astra, round 2)."""
    M, tmp, _ = run
    work = tmp_path / "copy"
    shutil.copytree(tmp / "pilot", work / "pilot")
    M2 = _into(_module("e03h_driver_test_trail"), work)
    calls = {"n": 0}

    def fail(*a, **k):
        calls["n"] += 1
        raise RuntimeError("no convergence (test)")

    monkeypatch.setattr(M2.calib, "calibrate_in_world", fail)
    with pytest.raises(RuntimeError, match="too many"):
        M2.main(["sham-rates", "--smoke", "--rerun", "--reason", "test"])
    doc = json.loads((work / "pilot" / "records" / "sham-rates.json").read_text(encoding="utf-8"))
    assert doc["status"] == "failed" and len(doc["failures"]) == calls["n"] > 0
