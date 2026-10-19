"""03h's exploratory amplitude check (scripts/e03h_amplitude.py; D338), at smoke size on the CPU. It checks that:
- the check completes after the pilot driver's smoke stages, with readings at both amplitudes and at 0.25;
- its cap counts the pilot's recorded time; its own budget, a missing pilot and a missing ledger each refuse before a
  record moves; a failed attempt is kept beside the retry;
- the guide's branches, an undefined ratio, its flags, and discordance replacing the branch (Astra, Fable);
- the real run's code guard excludes only this script (Fable, Astra, round 2);
- under level the amplitude changes nothing (the bit is 0), so level need not be rerun."""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.slow


def _module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _into(M, tmp):
    M.out_dir = lambda: tmp / "pilot"
    M.rec_dir = lambda: tmp / "pilot" / "records"
    return M


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("e03h-amp")
    D = _into(_module("e03h_amp_driver", "e03h.py"), tmp)
    for s in D.STAGES:
        D.main([s, "--smoke"])
    A = _module("e03h_amp_check", "e03h_amplitude.py")
    _into(A.P, tmp)
    doc = A.main(["--smoke"])
    return A, tmp, doc


def test_the_check_completes_with_both_amplitudes(run):
    A, tmp, doc = run
    assert doc["status"] == "completed" and doc["amplitudes"] == [0.5, 1.0]
    s1 = json.loads((tmp / "pilot" / "records" / "sham-rates.json").read_text(encoding="utf-8"))
    n = len(s1["graphs"])
    for amp in ("0.5", "1.0"):
        r = doc["readings"][amp]
        assert len(r["decile_shift"]["per_graph"]) == n and len(r["graphs"]) == n
        assert r["decile_shift"]["lo"] <= r["decile_shift"]["mean"] <= r["decile_shift"]["hi"]
        sb = r["selection_bank"]
        for k in ("relief_minus_sham_all_genomes", "relief_minus_level_all_genomes", "sham_minus_level_all_genomes"):
            assert len(sb[k]["per_graph"]) == n and sb[k]["lo"] <= sb[k]["mean"] <= sb[k]["hi"]
        assert len(r["realised_food_fell_counts"]) == n and set(r["realised_food_fell_counts"][0]) == {"relief", "sham"}
        assert len(r["turn_response_mean_abs"]) == n
        rr = r["ratio_mean_to_sd"]
        assert rr["ratio"] is None or rr["lo"] <= rr["ratio"] <= rr["hi"]
    assert doc["at_0.25"]["decile_shift"] and doc["at_0.25"]["pilot_recorded_decile_shift"]
    assert doc["guide"]["branch"] and isinstance(doc["guide"]["flags"], list)
    assert doc["upstream"]["sham-rates"] == A.P.sha(tmp / "pilot" / "records" / "sham-rates.json")
    assert doc["upstream"]["pilot"] == A.P.sha(tmp / "pilot" / "records" / "pilot.json")
    assert doc["over_cap_at_end"] is False and "over_own_budget_at_end" in doc


def test_the_cap_counts_the_pilots_time(run):
    A, tmp, _ = run
    pilot = json.loads((tmp / "pilot" / "compute.json").read_text(encoding="utf-8"))["totals"]["seconds_timed"] / 3600
    assert pilot > 0
    ck = A.clock()
    assert ck.spent_hours() >= pilot + A.reg.CapClock.spent_hours(ck)


def _record(tmp):
    return tmp / "amplitude" / "records" / "amplitude-check.json"


def test_its_own_budget_refuses_before_the_record_moves(run, monkeypatch):
    A, tmp, _ = run
    before = _record(tmp).read_text(encoding="utf-8")
    monkeypatch.setattr(A, "OWN_CAP_HOURS", 0.0)
    with pytest.raises(SystemExit, match="own budget"):
        A.main(["--smoke"])
    assert _record(tmp).read_text(encoding="utf-8") == before  # refused: the record stays in place


def test_a_missing_pilot_or_ledger_refuses_before_any_work(run):
    A, tmp, _ = run
    before = _record(tmp).read_text(encoding="utf-8")
    rec = tmp / "pilot" / "records" / "pilot.json"
    shutil.move(rec, rec.with_suffix(".away"))
    try:
        with pytest.raises(SystemExit, match="pilot has not run"):
            A.main(["--smoke"])
    finally:
        shutil.move(rec.with_suffix(".away"), rec)
    moved = [tmp / "pilot" / "compute.json", tmp / "pilot" / "compute"]  # the pilot's ledger and its attempts
    for p in moved:
        shutil.move(p, p.with_name(p.name + ".away"))
    try:
        with pytest.raises(SystemExit, match="ledger"):
            A.main(["--smoke"])
    finally:
        for p in moved:
            shutil.move(p.with_name(p.name + ".away"), p)
    assert _record(tmp).read_text(encoding="utf-8") == before


def test_a_failed_attempt_is_kept_beside_the_retry(run, monkeypatch):
    A, tmp, _ = run
    rec = tmp / "amplitude" / "records"

    def boom(dv, ck, pilot):
        raise RuntimeError("sabotage")

    monkeypatch.setattr(A, "run", boom)
    with pytest.raises(RuntimeError):
        A.main(["--smoke"])
    assert json.loads((rec / "amplitude-check.json").read_text(encoding="utf-8"))["status"] == "failed"
    k = max(int(f.stem.split("attempt")[1]) for f in rec.glob("amplitude-check.attempt*.json"))
    assert json.loads((rec / f"amplitude-check.attempt{k}.json").read_text(encoding="utf-8"))["status"] == "completed"
    monkeypatch.undo()
    assert A.main(["--smoke"])["status"] == "completed"
    assert json.loads((rec / f"amplitude-check.attempt{k + 1}.json").read_text(encoding="utf-8"))["status"] == "failed"


def _r(ratio, mean=0.01, sd=0.01, sham_level_hi=0.01, rs_lo=-0.01, lo=None):
    return {"ratio_mean_to_sd": {"ratio": ratio}, "decile_shift": {"mean": mean, "lo": mean / 2 if lo is None else lo},
            "between_graph_sd": sd,
            "selection_bank": {"sham_minus_level_all_genomes": {"hi": sham_level_hi},
                               "relief_minus_sham_all_genomes": {"lo": rs_lo}}}


def test_the_guides_branches_and_an_undefined_ratio():
    A = _module("e03h_amp_guide", "e03h_amplitude.py")
    assert "not supported" in A.guide({"0.5": _r(0.4), "1.0": _r(0.9)})["branch"]
    assert "redesign" in A.guide({"0.5": _r(0.8), "1.0": _r(2.1)})["branch"]
    assert "in between" in A.guide({"0.5": _r(0.8), "1.0": _r(1.4)})["branch"]
    assert "undefined" in A.guide({"0.5": _r(0.4), "1.0": _r(None)})["branch"]  # not "not supported" (Astra)
    assert A.ratio_range(0.01, 0.0, 3)["ratio"] is None


def test_the_guides_flags_and_discordance_replaces_the_branch():
    A = _module("e03h_amp_flags", "e03h_amplitude.py")
    g = A.guide({"0.5": _r(0.5, sham_level_hi=-0.001)})
    assert g["discordant"] and "sham damage" in g["flags"][0] and "discordant" in g["branch"]  # Astra, round 2
    g = A.guide({"0.5": _r(0.5, rs_lo=0.001)})
    assert g["discordant"] and "all-genome" in g["flags"][0] and "discordant" in g["branch"]
    base = {"decile_shift": {"mean": 0.0077}, "between_graph_sd": 0.0102}  # the pilot at 0.25: ratio 0.76
    # consistent fakes (Fable, round 2): each ratio is its mean over its SD
    ok = _r(0.05 / 0.02, mean=0.05, sd=0.02, lo=0.03)
    assert not A.guide({"1.0": ok}, base)["discordant"] and "redesign" in A.guide({"1.0": ok}, base)["branch"]
    near = _r(0.025 / 0.012, mean=0.025, sd=0.012, lo=0.007)  # its interval includes the 0.25 mean
    g = A.guide({"1.0": near}, base)
    assert g["discordant"] and "not corroborated" in g["flags"][0]
    shrunk = _r(0.02 / 0.008, mean=0.02, sd=0.008, lo=0.015)  # the SD shrank from 0.25
    assert A.guide({"1.0": shrunk}, base)["discordant"]


def test_a_negative_mean_gives_an_ordered_range():
    A = _module("e03h_amp_neg", "e03h_amplitude.py")
    rr = A.ratio_range(-0.005, 0.01, 3)
    assert rr["ratio"] < 0 and rr["lo"] <= rr["ratio"] <= rr["hi"]


def test_the_code_guard_excludes_only_this_script(tmp_path):
    """The real run's guard (smoke skips it): the pilot's code paths unchanged, this new script excluded (Fable,
    Astra, round 2). In a scratch repository, adding the script passes and any other change under scripts refuses."""
    import subprocess
    A = _module("e03h_amp_guard", "e03h_amplitude.py")

    def git(*a):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "test")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "e03h.py").write_text("x = 1\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-q", "-m", "bound")
    bound = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True).stdout.strip()
    (tmp_path / "scripts" / "e03h_amplitude.py").write_text("y = 2\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-q", "-m", "the check")
    A.reg.require_same_code(bound, A.CODE, root=tmp_path)
    with pytest.raises(SystemExit):
        A.reg.require_same_code(bound, A.P.CODE, root=tmp_path)  # without the exclusion it refuses (sabotage)
    (tmp_path / "scripts" / "e03h.py").write_text("x = 3\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-q", "-m", "a driver change")
    with pytest.raises(SystemExit):
        A.reg.require_same_code(bound, A.CODE, root=tmp_path)


def test_the_ratio_range_matches_b_power():
    A = _module("e03h_amp_range", "e03h_amplitude.py")
    rr = A.ratio_range(0.0077402972, 0.0101681801, 3)  # the pilot at 0.25 (D337: 0.17 to 1.3)
    assert abs(rr["ratio"] - 0.7612) < 1e-3 and abs(rr["lo"] - 0.1724) < 1e-3 and abs(rr["hi"] - 1.3175) < 1e-3


def test_under_level_the_amplitude_changes_nothing():
    import torch
    from wormwars.brain import BrainSpec, Genome
    from wormwars.connectome import load_connectome
    from wormwars.e03h import interface_03h
    D = _module("e03h_amp_level", "e03h.py")
    D.SMOKE, D.SMOKE_DEVICE = True, "cpu"  # the CPU path, as in CI
    con = load_connectome()
    c = D.t1("level", None)
    g = Genome.random(BrainSpec.from_connectome(con), c.brain, 3, generator=torch.Generator().manual_seed(7))
    ids = np.arange(3_699_000, 3_699_002)  # outside every registered and smoke range
    a, _ = D._scores(c, interface_03h(con, 0.25), g, ids, 3_699_100, "cpu")
    b, _ = D._scores(c, interface_03h(con, 1.0), g, ids, 3_699_100, "cpu")
    assert np.array_equal(a, b)
    r, _ = D._scores(D.t1("relief", None), interface_03h(con, 1.0), g, ids, 3_699_100, "cpu")
    assert not np.array_equal(a, r)  # the check can fail: the live bit at 1.0 changes the scores


def test_the_final_line_prints_on_a_cp1252_console(monkeypatch):
    """The check's last line crashed on a Windows console after its record was written (D339)."""
    import io
    import sys
    A = _module("e03h_amp_say", "e03h_amplitude.py")
    out = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", out)
    A._say("  flag: 1.0: the all-genome relief \u2212 sham is above 0")
    out.flush()
    assert b"relief ? sham" in out.buffer.getvalue()
