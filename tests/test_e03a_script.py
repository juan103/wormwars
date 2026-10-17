"""03a's pilot-dev driver, end to end at smoke size on the CPU (scripts/e03a.py): every stage completes in order, its
implementation checks hold, a stage is never rerun silently, and the pilot graph is checked by hash."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    spec = importlib.util.spec_from_file_location("e03a_script_test", ROOT / "scripts" / "e03a.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    tmp = tmp_path_factory.mktemp("e03a")
    M.out_dir = lambda: tmp / "pilot-dev"
    M.rec_dir = lambda: tmp / "pilot-dev" / "records"
    docs = {s: M.main([s, "--smoke"]) for s in M.STAGES}
    return M, tmp, docs


def test_every_stage_completes(run):
    M, _, docs = run
    assert [d["status"] for d in docs.values()] == ["completed"] * len(M.STAGES)


def test_implementation_checks_hold_in_the_pipeline(run):
    _, _, docs = run
    for r in docs["evolve-nip"]["runs"]:
        assert r["pinned"]
    for tb in docs["baseline"]["target_brains"]:
        assert tb.get("restoration_exact", True) and tb.get("own_equals_deleted", True)
    for row in docs["probe"]["evolved"].values():
        assert row["full_replay_equals_plain"]
    assert len(docs["panel"]["targets"]) == 2
    assert set(docs["tune"]["chosen"]) == {"temperatures", "p_move", "max_moves", "shaping"}
    for rnd in docs["tune"]["rounds"][1:]:  # the previous round's pick is carried, not run again
        assert sum(bool(r.get("reused_from_previous_round")) for r in rnd["results"].values()) == 1
    tb = docs["full"]["target_brains"][0]
    assert {"headroom", "advantage", "functional", "restoration"} <= set(tb["comparisons"])
    assert 0 < tb["enrichment"]["p"] <= 1
    assert len(docs["family2"]["scenarios"]) == 5


def test_compute_is_recorded_in_known_categories(run):
    _, tmp, _ = run
    comp = json.loads((tmp / "pilot-dev" / "compute.json").read_text(encoding="utf-8"))
    assert not comp["uncategorised"]
    assert {"selection", "tuning", "search", "final", "probe"} <= set(comp["categories"])


def test_a_stage_is_not_rerun_without_a_reason(run):
    M, _, _ = run
    with pytest.raises(SystemExit):
        M.main(["panel", "--smoke"])
    with pytest.raises(SystemExit):
        M.main(["panel", "--smoke", "--rerun"])


def test_a_changed_graph_is_refused(run):
    """Sabotage: setup's recorded hash no longer matching the rebuilt graph stops every later stage."""
    M, tmp, _ = run
    p = tmp / "pilot-dev" / "records" / "setup.json"
    doc = json.loads(p.read_text(encoding="utf-8"))
    good = doc["graph"]["sha256"]
    doc["graph"]["sha256"] = "0" * 64
    p.write_text(json.dumps(doc), encoding="utf-8")
    try:
        with pytest.raises(SystemExit):
            M.configured()
    finally:
        doc["graph"]["sha256"] = good
        p.write_text(json.dumps(doc), encoding="utf-8")
