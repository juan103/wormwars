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
