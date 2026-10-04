"""E3b-2's runner (scripts/e3b2.py): its fixed rules, checked without a formal stage (docs/E3/E3b-2-PLAN.md draft 2)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def m():
    s = importlib.util.spec_from_file_location("e3b2_under_test", ROOT / "scripts" / "e3b2.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


def test_the_fresh_block_and_the_benchmark_block_are_disjoint_from_every_earlier_block(m):
    fresh = set(range(*m.REGISTERED["ids"]["fresh"]))
    bench = set(range(*m.REGISTERED["ids"]["benchmark"]))
    smoke = set(range(*m.REGISTERED["ids"]["smoke"]))
    assert len(fresh) == 256 and len(bench) == 256 and smoke == set(range(9800, 9900))
    earlier = set()
    for lo, hi in ((0, 256), (1000, 1256), (2000, 2256), (4000, 4128), (4500, 4628), (5000, 5256), (6000, 6256),
                   (9000, 9100), (9100, 9106), (9200, 9206), (9300, 9334), (9400, 9406), (9500, 9756), (9900, 9903)):
        earlier |= set(range(lo, hi))
    for block in (fresh, bench, smoke):
        assert not block & earlier
    assert not fresh & bench and not fresh & smoke and not bench & smoke
    assert all(x < 10_000_000 for x in fresh | bench)  # below every training id
    assert m.REGISTERED["maze_seed"] == 1_180_000


def test_every_output_path_lies_outside_e3b0_and_e3b1(m):
    e3 = ROOT / "experiments" / "E3-ab-organism"
    forbidden = [e3 / "E3b-0", e3 / "E3b-1", ROOT / "runs" / "e3b0", ROOT / "runs" / "e3b1"]
    for p in m.output_paths():
        p = Path(p).resolve()
        assert not any(f.resolve() == p or f.resolve() in p.parents for f in forbidden), p
    assert m.E.EXP == m.EXP and m.E.OUT == m.OUT and m.EXP.name == "E3b-2"


def test_a_changed_champion_genome_is_refused(m, tmp_path):
    from wormwars.brain import Genome
    cx = m.context(m.cfg_for("shared"))
    g = cx["seed"].genome
    want = m.genome_hash(g, 0)
    m.check_genome(g, want, "seed")
    bad = g.with_params(bias=g.bias + 1e-6)
    with pytest.raises(SystemExit, match="does not match"):
        m.check_genome(bad, want, "seed")


def test_a_chunk_resumes_only_on_its_full_specification(m, tmp_path):
    calls = []

    def play():
        calls.append(1)
        return {"visits": np.ones((2, 3))}

    spec = {"mazes": [7000, 7003], "condition": "shared", "organisms": ["a#h1", "b#h2"], "composition": [2, 3, 8]}
    path = tmp_path / "c.npz"
    m.run_chunk(path, spec, play)
    m.run_chunk(path, spec, play)
    assert calls == [1]
    for key, val in (("condition", "none"), ("organisms", ["a#h1", "b#hX"]), ("composition", [2, 3, 1])):
        with pytest.raises(SystemExit, match="specification"):
            m.run_chunk(path, {**spec, key: val}, play)


def test_the_chunk_plans_hold_what_the_plan_says(m):
    plan = m.default_plan()
    a = [c for c in m.attribution_chunks(plan) if c["analysis"] == "A"]
    b = [c for c in m.attribution_chunks(plan) if c["analysis"] == "B"]
    assert len(a) == 32 and all(len(c["variants"]) == 16 for c in a)
    assert {c["condition"] for c in a} == {"shared", "none"}
    assert all(c["variants"][0][1] == ("hybrid", "functional", ()) for c in a)  # the all-seed hybrid first
    assert len(b) == 8 and all(len(c["variants"]) == 16 for c in b)
    les = m.lesion_chunks(plan)
    kinds = {v[1][0] for c in les for v in c["variants"]}
    assert kinds == {"intact", "clamp_a", "clamp_b", "edge", "reflex", "scent", "w2_reference"}
    assert all(len({v[1][0] == "scent" for v in c["variants"]}) == 1 for c in les)  # scent chunks hold only scent
    orgs = {v[0] for c in les for v in c["variants"]}
    assert len(orgs) == 21 + 1  # 16 T, 4 N, the seed, and the W2 reference
    lat = m.latch_chunks(plan)
    assert sum(len(c["variants"]) for c in lat) == 21


def test_the_drop_order(m):
    t = {"chunk": 150.0, "clamp_chunk": 150.0, "recorder_chunk": 170.0, "scent_chunk": 150.0}
    p = m.apply_drops(t, spent=0.0)
    assert p["drops"] == [] and p["fits"]
    # by hand at x1.6, with the 1.25 reserve: all 5.86 h > 5; without N 5.52; without B too 4.86 <= 5
    t2 = {k: v * 1.6 for k, v in t.items()}
    p2 = m.apply_drops(t2, spent=0.0)
    assert p2["drops"] == ["n champions", "side attribution"] and p2["fits"]
    assert m.apply_drops({k: v * 10 for k, v in t.items()}, spent=0.0)["fits"] is False


def test_the_attribution_reading_on_synthetic_tables(m):
    rng = np.random.default_rng(0)
    players = m.AT.FUNCTIONAL
    coal = m.AT.coalitions(players)
    base = rng.normal(5.0, 0.5, 64)
    eff = {"sensing": 0.1, "gating": 0.0, "output": 0.6, "latch": 0.2}
    X = np.stack([base + sum(eff[g] for g in S) + rng.normal(0, 0.01, 64) for S in coal])
    r = m.read_table(X, players, seed_shared=X[0])
    assert r["gain"] == pytest.approx(sum(eff.values()) / X[0].mean(), rel=0.05)
    assert sum(r["shapley"].values()) == pytest.approx(r["gain"], abs=1e-12)
    assert r["shapley"]["output"] == pytest.approx(0.6 / X[0].mean(), rel=0.1)


def test_the_maze_paired_bootstrap_resamples_jointly(m):
    idx = m.bootstrap_indices(n_mazes=8, resamples=5, seed=0)
    assert idx.shape == (5, 8) and np.array_equal(idx, m.bootstrap_indices(n_mazes=8, resamples=5, seed=0))


@pytest.mark.slow
def test_a_smoke_of_every_stage(m):
    for stage in m.STAGES:
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "e3b2.py"), stage, "--smoke", "--device", "cpu"],
                           cwd=ROOT, capture_output=True, text=True, timeout=3600)
        assert r.returncode == 0, (stage, r.stdout[-2000:], r.stderr[-4000:])
    rep = json.loads((ROOT / "runs" / "e3b2-smoke" / "report.json").read_text(encoding="utf-8"))
    assert rep["outcome"] == "completed" and "attribution" in rep["summary"]
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "e3b2.py"), "summary", "--smoke", "--device", "cpu"],
                       cwd=ROOT, capture_output=True, text=True, timeout=1800)
    assert r.returncode == 0, r.stderr[-3000:]


def test_a_ratio_interval_over_mazes(m):
    num, den = np.array([1, 2, 3, 0]), np.array([2, 2, 4, 0])
    r = m.ratio_interval(num, den, m.bootstrap_indices(4, 2000, 0))
    assert r["value"] == pytest.approx(6 / 8) and r["ci95"][0] <= 0.75 <= r["ci95"][1]
    assert m.ratio_interval(np.zeros(3), np.zeros(3), m.bootstrap_indices(3, 10, 0))["value"] is None


def test_every_variant_reports_every_outcome(m):
    z = {"visits": np.array([[1.0, 3.0], [2.0, 2.0]]), "legs": np.array([[1.0, 4.0], [2.0, 3.0]]),
         "later_leg_rate": np.ones((2, 2)), "unvisited_share": np.zeros((2, 2)), "round_trip_share": np.ones((2, 2)),
         "later_first_b": np.ones((2, 2))}
    out = m.variant_outcomes(z, [("ta:0", ("intact",)), ("seed", ("intact",))])
    assert out[0]["visits"] == 2.0 and out[0]["median_legs"] == 2.5 and out[1]["median_legs"] == 2.5
    assert set(out[0]) >= {"organism", "variant", "visits", "later_leg_rate", "unvisited_share", "round_trip_share",
                           "median_legs"}


# ------------------------------------------------------------------ the code review's findings (D195)

def test_out_is_refused_before_any_accounting(m, tmp_path):
    for args in (["--out", str(tmp_path / "x")], [f"--out={tmp_path / 'y'}"]):
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "e3b2.py"), "report", "--smoke", "--device", "cpu", *args],
                           cwd=ROOT, capture_output=True, text=True, timeout=600)
        assert r.returncode != 0 and "--out" in (r.stderr + r.stdout)
    assert not (tmp_path / "x").exists() and not (tmp_path / "y").exists()


def test_every_fixed_input_is_pinned(m, monkeypatch):
    assert all(v is not None and len(v) == 64 for v in m.FIXED.values())
    m.check_inputs()
    bad = dict(m.FIXED)
    bad[next(iter(bad))] = "0" * 64
    monkeypatch.setattr(m, "FIXED", bad)
    with pytest.raises(SystemExit, match="has changed"):
        m.check_inputs()


def test_a_chunk_specification_holds_every_maze_id(m):
    cfg = m.cfg_for("shared")
    cx = m.context(cfg)
    orgs = {"seed": cx["seed"].genome}
    chunk = {"analysis": "C", "condition": "shared", "key": "x", "variants": [("seed", ("intact",))]}
    a = m.chunk_spec(chunk, orgs, cx, np.array([7000, 7001, 7003]), "sha")
    b = m.chunk_spec(chunk, orgs, cx, np.array([7000, 7002, 7003]), "sha")
    assert a["mazes"] == [7000, 7001, 7003] and a != b


def test_the_trail_dependence_split_on_synthetic_tables(m):
    rng = np.random.default_rng(1)
    players = m.AT.FUNCTIONAL
    coal = m.AT.coalitions(players)
    base = rng.normal(5.0, 0.3, 64)
    seed_shared = base.copy()
    def X(extra_output):
        return np.stack([base + sum({"sensing": 0.1, "gating": 0.0, "output": 0.5 + extra_output, "latch": 0.2}[g] for g in S)
                         for S in coal])
    shared, none = {"ta:0": X(0.4)}, {"ta:0": X(0.0)}
    out = m.trail_split(shared, none, seed_shared, players, m.bootstrap_indices(64, 200, 0))
    d = out["per_champion"]["ta:0"]
    assert d["output"] == pytest.approx(0.4 / base.mean()) and abs(d["sensing"]) < 1e-12
    b = out["schedules"]["ta"]["output"]["bootstrap95"]
    assert b[0] <= d["output"] <= b[1]


def test_the_latch_summary_definitions(m):
    z = {f"latch_{k}": np.array([[v, 0]]) for k, v in {
        "legs_to_b": 4, "pre_to_b": 1, "crossed_to_b": 2, "lat_to_b": 10, "censored_to_b": 1,
        "legs_to_a": 3, "pre_to_a": 0, "crossed_to_a": 0, "lat_to_a": 0, "censored_to_a": 0,
        "third_decided_A": 10, "third_agree_A": 6, "third_undecided_A": 2, "third_decided_B": 8, "third_agree_B": 8,
        "third_undecided_B": 0, "half_decided_A": 9, "half_agree_A": 5, "half_undecided_A": 3, "half_decided_B": 8,
        "half_agree_B": 8, "half_undecided_B": 0, "occupancy_A": 12, "occupancy_B": 8, "eligible_weys": 7}.items()}
    r = m.latch_summary(z, 0, m.bootstrap_indices(2, 50, 0))
    assert r["switched_to_b"]["value"] == pytest.approx(2 / (4 - 1 - 1))  # crossed / (legs − pre-aligned − censored)
    assert r["pre_aligned_to_b"] == pytest.approx(1 / 4) and r["latency_to_b"]["value"] == pytest.approx(5.0)
    assert r["switched_to_a"]["value"] == 0.0
    assert r["third"]["agreement_A"]["value"] == pytest.approx(0.6) and r["third"]["opposite_A"] == 4
    assert r["third"]["agreement_equal_weight"]["value"] == pytest.approx((0.6 + 1.0) / 2)
    assert r["half"]["agreement_A"]["value"] == pytest.approx(5 / 9)
    assert r["occupancy"] == {"A": 12, "B": 8} and r["eligible_weys"] == 7


def test_the_resting_turn_matches_the_seeds_probe_record(m):
    cfg = m.cfg_for("shared")
    out = m.resting_turn_check({"seed": m.genome_report({"t": [], "n": []}, cfg)["seed"]})
    assert out["max_abs_difference"] < 1e-6


def test_the_report_survives_a_missing_chunk(m, tmp_path, monkeypatch):
    monkeypatch.setattr(m, "EXP", tmp_path)
    assert m.load_chunk("A-shared-ta0") is None


# ------------------------------------------------------------------ the confirmation pass (D196)

def test_the_trail_split_keeps_both_intervals(m):
    players = m.AT.FUNCTIONAL
    coal = m.AT.coalitions(players)
    base = np.full(32, 5.0)
    def X(out_shared):
        return np.stack([base + sum({"sensing": 0.0, "gating": 0.0, "output": out_shared, "latch": 0.0}[g] for g in S)
                         for S in coal])
    shared = {"ta:0": X(1.0), "ta:1": X(3.0)}
    none = {"ta:0": X(0.0), "ta:1": X(0.0)}
    out = m.trail_split(shared, none, base, players, m.bootstrap_indices(32, 100, 0))["schedules"]["ta"]["output"]
    assert out["ci95"][0] < 0.2 and out["ci95"][1] > 0.6  # the run-level t interval, wide over runs 0.2 and 0.6
    assert out["bootstrap95"] == pytest.approx([0.4, 0.4])  # the maze bootstrap, no maze noise here


def test_the_equal_weight_bootstrap_excludes_draws_missing_a_goal(m):
    z = {f"latch_{k}": np.array([v]) for k, v in {
        "third_decided_A": [5, 0], "third_agree_A": [5, 0], "third_decided_B": [0, 5], "third_agree_B": [0, 5],
        "third_undecided_A": [0, 0], "third_undecided_B": [0, 0], "half_decided_A": [5, 0], "half_agree_A": [5, 0],
        "half_decided_B": [0, 5], "half_agree_B": [0, 5], "half_undecided_A": [0, 0], "half_undecided_B": [0, 0],
        **{f"{k}_{d}": [0, 0] for k in ("legs", "pre", "crossed", "lat", "censored") for d in ("to_a", "to_b")},
        "occupancy_A": [5, 0], "occupancy_B": [0, 5], "eligible_weys": [1, 1]}.items()}
    r = m.latch_summary(z, 0, m.bootstrap_indices(2, 400, 0))["third"]["agreement_equal_weight"]
    assert r["value"] == 1.0 and r["ci95"] == [1.0, 1.0]


def test_the_summary_runs_outside_the_stage_frame(m):
    assert "summary" in m.COMMANDS and "summary" not in m.STAGES
