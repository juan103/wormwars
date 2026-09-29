"""03m's exploratory runner (`scripts/p4m.py`): its building blocks on the CPU, with a few genomes."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def p():
    spec = importlib.util.spec_from_file_location("p4m_script", ROOT / "scripts" / "p4m.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def parts(p):
    con, bank, iface = p.setup("cpu")
    g, cfg = p.probe_genomes(con, "N2", "cpu", n=4)
    return con, bank, iface, g, cfg


def test_pairs_join_left_and_right_names_only(p):
    assert p.pairs(["RIAL", "RIAR", "AVL", "PVR", "RMDL", "RMDR", "RMDDL", "RMDDR"]) == {
        "RIA": [0, 1], "RMD": [4, 5], "RMDD": [6, 7]}


def test_ensemble_membership_is_exact(p):
    """Review v2 (both): `SH-` also prefixes every other ensemble's names."""
    names = ["SH-10000", "SH-route-20000", "SH-class-30000", "SH-mirror-40000", "SH-recip-50000", "N2", "N2perm1"]
    assert [n for n in names if p.in_ensemble(n, "SH")] == ["SH-10000"]
    assert [n for n in names if p.in_ensemble(n, "SH-route")] == ["SH-route-20000"]


def test_the_lesion_order_puts_the_empty_deletion_then_the_pre_named_targets_first(p, parts):
    con, bank, iface, g, cfg = parts
    names = list(con.names)
    turn = set(iface.turn_plus) | set(iface.turn_minus)
    e = p.lesion_entries(names, turn)
    assert e[0] == ("intact", [])
    assert [lbl for lbl, _ in e[1:4]] == ["pair RIA", "pair AIZ", "pair AIY"]
    assert not any(set(d) & turn for _, d in e)
    labels = [lbl for lbl, _ in e]
    assert len(labels) == len(set(labels))


def test_an_empty_deletion_reproduces_the_intact_brain(p, parts):
    con, bank, iface, g, cfg = parts
    whole = p.p4_of(p.M.history(g, cfg, iface, bank))
    res = p.history_in_chunks(g, cfg, iface, bank, [[], [5]], per_chunk=g.n_strains)
    assert (res[0]["numerator"], res[0]["denominator"]) == (whole["numerator"], whole["denominator"])
    assert res[1]["numerator"] != whole["numerator"]


def test_chunked_deletions_match_one_at_a_time_on_the_cpu(p, parts):
    con, bank, iface, g, cfg = parts
    dels = [[], [3], [7, 8]]
    one = p.history_in_chunks(g, cfg, iface, bank, dels, per_chunk=g.n_strains)
    many = p.history_in_chunks(g, cfg, iface, bank, dels, per_chunk=3 * g.n_strains)
    for a, b in zip(one, many):
        assert a["numerator"] == pytest.approx(b["numerator"], rel=1e-6)


def test_the_long_window_starts_at_03s_measurement(p, parts):
    con, bank, iface, g, cfg = parts
    h = p.M.history(g, cfg, iface, bank)["raw_turn"]
    full = p.history_full(g, cfg, iface, bank, after=20, every=10)
    assert full["ticks"] == [0, 5, 10, 20]
    np.testing.assert_allclose(full["diff"][0], h["final"], rtol=1e-6, atol=1e-9)
    np.testing.assert_allclose(full["diff"][1], h["after"], rtol=1e-6, atol=1e-9)
    np.testing.assert_allclose(full["steady_contrast"], h["steady_contrast"], rtol=1e-6, atol=1e-9)
    assert full["end_state_range"].shape == (4,) and (full["end_state_range"] >= 0).all()


def test_the_window_range_sees_an_oscillation_that_returns_to_its_start(p):
    """Review v2 (Astra): comparing only the window's two ends would call this settled."""
    w = p.WindowRange()
    for x in (0.0, 1.0, -1.0, 0.0):
        w.add(torch.full((2, 1, 3), x))
    assert w.value().tolist() == [2.0, 2.0]
    still = p.WindowRange()
    for _ in range(4):
        still.add(torch.zeros(2, 1, 3))
    assert still.value().tolist() == [0.0, 0.0]


def test_the_decay_summary_leaves_empty_shares_missing(p):
    n = 5
    h = {"ticks": [0, 10], "diff": np.zeros((2, n), np.float32), "steady_contrast": np.ones(n, np.float32),
         "hold_state_range": np.zeros(n), "hold_turn_range": np.zeros(n), "end_state_range": np.zeros(n),
         "end_turn_range": np.zeros(n), "slope_hold": np.ones(n), "slope_ramp": np.ones(n)}
    s = p.decay_summary(h)
    assert s["eligible"] == {"share": 0.0, "count": 0, "of": 5}
    assert s["separation_remaining_among_eligible"] == {"share": None, "count": 0, "of": 0}
    assert s["ratio_of_means_at_end"] is None
    json.dumps(s, allow_nan=False)


def test_the_tail_statistics(p):
    f = np.array([10.0] + [1.0] * 19)
    s = np.ones(20)
    t = p.tail_stats(f, s)
    assert t["top5pct_share_of_numerator"] == pytest.approx(10 / 29)
    assert t["P4_without_top5pct_by_numerator"] == pytest.approx(1.0)
    assert t["P4"] == pytest.approx(29 / 20)


def test_an_invalid_measurement_is_never_placed_among_the_nulls(p):
    for final, steady in ((np.zeros(4), np.zeros(4)), (np.full(4, np.nan), np.ones(4)), (np.ones(4), np.full(4, np.inf))):
        r = p.p4_of({"raw_turn": {"final": final, "steady_contrast": steady}})
        assert r["valid"] is False and r["P4"] is None
        pg = p.supplement("03")
        assert p.null_position(r, pg) is None and p.lead_class(r, pg) is None
        json.dumps(r, allow_nan=False)  # standard JSON: no NaN


def test_edge_deletions_touch_one_synapse_type(p, parts):
    con, bank, iface, g, cfg = parts
    k = 10
    chem = p.delete_edges(g, [[k]] * g.n_strains, "chemical")
    gap = p.delete_edges(g, [[k]] * g.n_strains, "gap")
    touch_c = torch.isin(g.spec.chem_i, torch.tensor([k])) | torch.isin(g.spec.chem_j, torch.tensor([k]))
    touch_g = torch.isin(g.spec.gap_i, torch.tensor([k])) | torch.isin(g.spec.gap_j, torch.tensor([k]))
    assert (chem.w[:, touch_c] == 0).all() and torch.equal(chem.g, g.g)
    assert (gap.g[:, touch_g] == 0).all() and torch.equal(gap.w, g.w)
    assert torch.equal(chem.bias, g.bias)


def test_formal_runs_refuse_another_genome_count(p):
    from types import SimpleNamespace
    with pytest.raises(SystemExit):
        p.formal_guard(SimpleNamespace(genomes=512, device="cuda"))


@pytest.mark.parametrize("fails", [False, True])
def test_the_compute_record_includes_the_attempt_that_writes_it(p, tmp_path, fails):
    """Review v2 (both): the export runs after the accounting has written the current attempt."""
    out, exp = tmp_path / "runs", tmp_path / "exp"

    def main():
        if fails:
            raise p.reg.CapReached("cap")

    try:
        p.acct.run_script(main, out_default=str(out), default="probe", name="p4m-test", argv=[])
    except p.reg.CapReached:
        pass
    p.export_compute_record(out, exp)
    rec = json.loads((exp / "compute-record.json").read_text())
    assert len(rec["attempts"]) == 1 and rec["attempts"][0]["status"] == ("failed" if fails else "completed")


# ------------------------------------------------------------------ retention on a cap stop (review v3)

@pytest.fixture
def smoke(p, tmp_path, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(p, "SMOKE", True)
    monkeypatch.setattr(p, "EXP", tmp_path)
    monkeypatch.setattr(p, "OUT", tmp_path)
    calls = {"n": 0, "stop_at": None}

    def check(self):
        calls["n"] += 1
        if calls["stop_at"] is not None and calls["n"] >= calls["stop_at"]:
            raise p.reg.CapReached("cap")

    monkeypatch.setattr(p.reg.CapClock, "check", check)
    return SimpleNamespace(device="cpu", genomes=8, per_chunk=8), calls, tmp_path


def test_weights_keep_every_finished_condition_on_a_stop(p, smoke):
    args, calls, d = smoke
    calls["stop_at"] = 3  # the command's first check, the independent condition, then the paired one
    with pytest.raises(p.reg.CapReached):
        p.cmd_weights(args)
    part = json.loads((d / "weights-partial.json").read_text())
    assert list(part["permutations"]["independent"]) == ["N2perm100"] and part["permutations"]["paired"] == {}
    assert "independent|N2perm100|final" in np.load(d / "weights-per-genome.npz", allow_pickle=False).files


def test_decay_keeps_the_long_history_when_the_gaps_off_check_stops(p, smoke, monkeypatch):
    args, calls, d = smoke
    monkeypatch.setattr(p, "ensure_graphs", lambda names: {"rebuilt": 0})  # never writes outside tmp_path
    calls["stop_at"] = 3  # the command's check, N2's long history, then N2's gaps-off
    with pytest.raises(p.reg.CapReached):
        p.cmd_decay(args)
    part = json.loads((d / "decay-partial.json").read_text())
    assert list(part["graphs"]) == ["N2"] and "gaps_off" not in part["graphs"]["N2"]
    assert "N2|diff" in np.load(d / "decay-per-genome.npz", allow_pickle=False).files


def test_the_lesion_follow_up_keeps_its_finished_deletions_on_a_stop(p, smoke, tmp_path, monkeypatch):
    """Review v4 (both): the follow-up by synapse type, stopped at its very last check (inside the gap
    pass), keeps the finished chemical pass: its partial summary and its per-genome arrays."""
    args, calls, d = smoke
    p.cmd_lesions(args)  # a full smoke run, to count the checks
    full = json.loads((d / "lesions.json").read_text())
    top = [r["deleted"] for r in full["follow_up_by_synapse_type"]["chemical"]]
    assert top, "the smoke run must reach the follow-up"
    total = calls["n"]
    run2 = tmp_path / "second"
    monkeypatch.setattr(p, "EXP", run2)
    monkeypatch.setattr(p, "OUT", run2)
    calls["n"], calls["stop_at"] = 0, total  # the last check: the last gap-pass deletion
    with pytest.raises(p.reg.CapReached):
        p.cmd_lesions(args)
    part = json.loads((run2 / "lesions-partial.json").read_text())
    assert [r["deleted"] for r in part["follow_up_by_synapse_type"]["chemical"]] == top
    assert len(part["follow_up_by_synapse_type"].get("gap", [])) == len(top) - 1
    arr = np.load(run2 / "lesions-follow-up-per-genome.npz", allow_pickle=False).files
    assert all(f"chemical|{lbl}|{k}" in arr for lbl in top for k in ("final", "steady"))
    assert all(f"gap|{lbl}|{k}" in arr for lbl in top[:-1] for k in ("final", "steady"))


def test_lesions_flush_every_finished_deletion_on_a_stop(p, smoke):
    args, calls, d = smoke
    calls["stop_at"] = 4  # the command's check, then one check per deletion batch: two done, the third stops
    with pytest.raises(p.reg.CapReached):
        p.cmd_lesions(args)
    arr = np.load(d / "lesions-per-genome.npz", allow_pickle=False)
    assert arr["labels"].tolist() == ["intact", "pair RIA"] and arr["final"].shape == (2, 8)
    part = json.loads((d / "lesions-partial.json").read_text())
    assert [r["deleted"] for r in part["rows"]] == ["intact", "pair RIA"]


def test_graph_rebuilding_stops_at_the_cap(p, smoke, monkeypatch):
    args, calls, d = smoke
    built = []
    monkeypatch.setattr(p, "ensure_graphs", lambda names: built.append(names) or {"rebuilt": 1})
    calls["stop_at"] = 3
    with pytest.raises(p.reg.CapReached):
        p.cmd_graphs(args)
    assert len(built) == 2
