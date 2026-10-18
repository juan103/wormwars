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


def test_a_failed_restoration_control_fails_the_baseline_stage(tmp_path, monkeypatch):
    """Astra: a failed implementation control must stop the dependent stages, not only be recorded."""
    spec = importlib.util.spec_from_file_location("e03a_script_test_b", ROOT / "scripts" / "e03a.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    M.out_dir = lambda: tmp_path / "pilot-dev"
    M.rec_dir = lambda: tmp_path / "pilot-dev" / "records"
    for s in ("setup", "evolve-intact", "panel", "evolve-nip"):
        M.main([s, "--smoke"])
    real = M.R.Reinsertion.saved_state

    def off_by_a_little(self, intact):
        st = real(self, intact)
        st.bias += 0.5
        return st

    monkeypatch.setattr(M.R.Reinsertion, "saved_state", off_by_a_little)
    with pytest.raises(RuntimeError, match="restoration"):
        M.main(["baseline", "--smoke"])
    doc = json.loads((tmp_path / "pilot-dev" / "records" / "baseline.json").read_text(encoding="utf-8"))
    assert doc["status"] == "failed" and doc["failures"]
    with pytest.raises(SystemExit):
        M.main(["tune", "--smoke"])  # nothing downstream runs on a failed baseline


@pytest.mark.gpu
def test_the_cuda_preflight_runs_every_stage(tmp_path):
    import torch
    if not torch.cuda.is_available():
        pytest.skip("no CUDA")
    spec = importlib.util.spec_from_file_location("e03a_script_test_c", ROOT / "scripts" / "e03a.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    M.out_dir = lambda: tmp_path / "pilot-dev"
    M.rec_dir = lambda: tmp_path / "pilot-dev" / "records"
    for s in M.STAGES:
        assert M.main([s, "--smoke", "--device", "cuda"])["status"] == "completed"


def test_a_stopped_full_keeps_its_finished_target_brains_and_the_report_still_runs(tmp_path, monkeypatch):
    """Astra and Fable, round 2: a cap reached in `full` must leave the finished target-brains, their saved states, and
    a report that names what is missing."""
    spec = importlib.util.spec_from_file_location("e03a_script_test_d", ROOT / "scripts" / "e03a.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    M.out_dir = lambda: tmp_path / "pilot-dev"
    M.rec_dir = lambda: tmp_path / "pilot-dev" / "records"
    for s in ("setup", "evolve-intact", "panel", "evolve-nip", "baseline", "probe", "tune"):
        M.main([s, "--smoke"])
    real, calls = M._final_scores, {"n": 0}

    def stop_on_second(*a, **k):
        calls["n"] += 1
        if calls["n"] == 2:
            raise M.reg.CapReached("the registered cap is reached (test)")
        return real(*a, **k)

    monkeypatch.setattr(M, "_final_scores", stop_on_second)
    with pytest.raises(M.reg.CapReached):
        M.main(["full", "--smoke"])
    doc = json.loads((tmp_path / "pilot-dev" / "records" / "full.json").read_text(encoding="utf-8"))
    assert doc["status"] == "failed" and len(doc["target_brains"]) == 1 and "p" in doc and doc["setting"]
    assert len(doc["searches_finished"]) == 2  # the second target-brain's searches finished before the stop
    saved = sorted(p.name for p in (tmp_path / "pilot-dev" / "states").glob("*.npz"))
    assert len(saved) == 4  # two target-brains, each at the ordinary length and complete
    rep = M.main(["report", "--smoke"])
    assert rep["target_brains_measured"] == 1 and not rep["full_complete"]
    assert any("full did not complete" in m for m in rep["missing"])
    monkeypatch.setattr(M, "_final_scores", real)
    again = M.main(["full", "--smoke", "--rerun", "--reason", "test: after a stop"])
    assert again["status"] == "completed" and again["target_brains"][0].get("carried_from_attempt")
    assert not any(r.get("carried_from_attempt") for r in again["target_brains"][1:])


def test_the_probe_times_the_full_replay_control(run):
    _, _, docs = run
    t = docs["probe"]["timing"]
    assert len(t["full_replay_control"]) == len(docs["probe"]["evolved"]) and t["plain"]


def test_full_writes_the_no_task_control_turnover_from_generation_0_and_attributes(run):
    _, _, docs = run
    tb = docs["full"]["target_brains"][0]
    assert 0 < tb["no_task"]["p"] <= 1 and "attributes" in tb and tb["final_evaluation"] == "complete"
    ps = tb["per_search"][0]
    assert len(ps["turnover_per_10_from_0"]) == max(0, len(ps["q_every_10_from_0"]) - 1)
    assert "paired_diff_sd_mean" in ps
    paired = tb["descriptive"]["composite"]["name"] == "mirror"
    assert ("mirror_zero_subset" in tb["descriptive"]) == paired


def test_turnover_windows_run_from_generation_0_on_a_known_history():
    """Astra, round 3: the smoke searches are too short to test the 10-generation windows."""
    spec = importlib.util.spec_from_file_location("e03a_script_test_e", ROOT / "scripts" / "e03a.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    import numpy as np
    import torch

    def masks(on):
        m = torch.zeros(10, dtype=torch.bool)
        m[list(on)] = True
        return {"in": m, "out": torch.zeros(10, dtype=torch.bool), "gap": torch.zeros(10, dtype=torch.bool)}

    class Fake:
        class trace:
            initial_cold = masks([0, 1, 2, 3])
            # generation g's state at index g - 1: two partners replaced by generation 10, all four by generation 20
            cold_masks = [masks([0, 1, 2, 3])] * 9 + [masks([0, 1, 8, 9])] + [masks([0, 1, 8, 9])] * 9 \
                + [masks([4, 5, 6, 7])]

    assert M._turnover(Fake) == [0.5, 1.0]


def _module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "e03a.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    return M


def test_the_search_check_runs_in_the_pipeline_and_reads_by_its_rule(run):
    """D314: the lesion covers every true edge, the re-evaluation every start and size, three variants in their order,
    one outcome; the records needed to read it afterwards are written."""
    M, _, docs = run
    d = docs["search-check"]
    assert [v["name"] for v in d["variants"]] == ["V4", "V3", "V1"]
    assert d["rule"]["outcome"] in ("i", "ii", "iii")
    tb = next(r for r in docs["baseline"]["target_brains"] if r["label"] == d["target_brain"])
    assert d["lesion"]["n_edges"] == sum(tb["counts"].values())
    assert set(d["reeval"]) == {"refit-0", "free-0"}
    for r in d["reeval"].values():
        assert set(r["by_worlds"]) == {"2", "4"} and len(r["raw"]["selection_world_ids"][0]) == 4
    v4 = d["variants"][0]
    assert v4["confirm_worlds"] > 0
    for ps in v4["per_search"]:  # one confirmation and one acceptance share per generation
        assert len(ps["confirmed"]) == len(ps["cold_score_series"]) == len(ps["accepted_share_series"])
    for v in d["variants"]:
        assert 0 < v["enrichment"]["p"] <= 1 and 0 < v["no_task"]["p"] <= 1 and v["advantage"] is not None
        assert set(v["enrichment_per_type"]) == set(v["enrichment"]["types"])
        assert len(v["final_counts"]) == len(v["states"]) and len(v["restoration_per_refit"]) == len(v["refit_means"])
        assert v["refit_sd_95"][0] <= v["refit_sd"] <= v["refit_sd_95"][1]


def test_lesions_remove_exactly_one_true_edge_each():
    M = _module("e03a_script_test_f")
    import torch
    K = 6
    m_in = torch.tensor([[1, 0, 1, 0, 0, 0]], dtype=torch.bool)
    m_out = torch.tensor([[0, 1, 0, 0, 0, 0]], dtype=torch.bool)
    m_gap = torch.tensor([[0, 0, 0, 1, 1, 0]], dtype=torch.bool)
    w = torch.arange(1, K + 1, dtype=torch.float32).reshape(1, K)
    one = torch.ones(1)
    st = M.R.XState(m_in, m_out, m_gap, w.clone(), w.clone() * 2, w.clone() * 3, one, one * 0, one * 0)
    les, where = M._lesions(st)
    assert les.n == 5 and where == [("in", 0), ("in", 2), ("out", 1), ("gap", 3), ("gap", 4)]
    for i, (t, k) in enumerate(where):
        one_state = les.select([i])
        for tt in M.R.TYPES:
            dm = (one_state.masks()[tt][0] != st.masks()[tt][0]).nonzero().flatten().tolist()
            dw = (one_state.weights()[tt][0] != st.weights()[tt][0]).nonzero().flatten().tolist()
            assert dm == ([k] if tt == t else []) and dw == ([k] if tt == t else [])
        assert not one_state.masks()[t][0, k] and one_state.weights()[t][0, k] == 0


def test_the_check_outcome_rule_at_its_boundaries():
    """PILOT-DEV §7's rule (v3.3): reliability (the lower bound over worlds and refits at least -p, so a variant above
    restoration passes; refit SD at most p) and recovery (enrichment p below 0.05 over the variants), outcome i (lowest
    p, first on ties), ii (some reliable, no single variant both) or iii."""
    M = _module("e03a_script_test_g")
    p = 0.1

    def v(name, lo=-0.05, sd=0.05, ep=0.5):
        return {"name": name, "restoration_over_refits": {"lo": lo}, "refit_sd": sd, "enrichment": {"p": ep}}

    out = M._check_outcome([v("V4"), v("V3", ep=0.0166), v("V1", ep=0.0166)], p, 0.05, 1.0)
    assert out["outcome"] == "i" and out["variant"] == "V3"  # a tie keeps the first listed
    out = M._check_outcome([v("V4"), v("V3"), v("V1", ep=0.0167)], p, 0.05, 1.0)
    assert out["outcome"] == "ii"  # below 0.05 but not below 0.05 / 3: the division over the variants decides
    out = M._check_outcome([v("V4", lo=0.08), v("V3"), v("V1", lo=0.08, ep=0.001)], p, 0.05, 1.0)
    assert out["outcome"] == "i" and out["variant"] == "V1"  # above restoration passes (monotonic; Astra)
    out = M._check_outcome([v("V4", lo=-0.1), v("V3", lo=-0.1001, ep=0.001), v("V1", sd=0.1001, ep=0.001)],
                           p, 0.05, 1.0)
    assert out["outcome"] == "ii" and out["unreliable_but_recovering"] == ["V3", "V1"]  # -p exactly passes
    out = M._check_outcome([v("V4", lo=-0.2), v("V3", sd=0.2), v("V1", lo=-0.11, ep=0.0)], p, 0.05, 1.0)
    assert out["outcome"] == "iii"
