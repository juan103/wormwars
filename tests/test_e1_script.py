"""The registered rules in `scripts/e1.py` (experiments/E1-navigation/PREREGISTRATION.md): the σ
choice, the one-sided bootstrap bound, the grids, and the secondary measures."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def e1():
    spec = importlib.util.spec_from_file_location("e1_script", ROOT / "scripts" / "e1.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _row(sigma, share):
    return {"sigma": sigma, "share_above_floor": share}


def test_sigma_is_the_smallest_candidate_meeting_the_share(e1):
    rows = [_row(2.0, 0.1), _row(3.0, 0.95), _row(4.0, 0.99), _row(6.0, 1.0)]
    assert e1.choose_sigma(rows) == (3.0, False)


def test_sigma_falls_back_to_the_largest_candidate_flagged(e1):
    rows = [_row(2.0, 0.0), _row(3.0, 0.0), _row(4.0, 0.3), _row(6.0, 0.875)]
    assert e1.choose_sigma(rows) == (6.0, True)


def test_the_share_boundary_is_inclusive(e1):
    assert e1.choose_sigma([_row(2.0, 0.90), _row(6.0, 1.0)]) == (2.0, False)


def test_the_lower_bound_is_below_the_mean_and_reproducible(e1):
    d = np.random.default_rng(1).normal(1.0, 1.0, 500)
    lb = e1.lower_bound(d)
    assert lb < d.mean() and lb == e1.lower_bound(d)
    assert e1.lower_bound(np.full(50, 2.0)) == 2.0


def test_the_wall_follower_thresholds_sit_above_the_own_body_level(e1):
    g = e1.grid_for("wall-follower", 0.3)
    assert "threshold_above_own_body" not in g
    assert min(g["threshold"]) > 0.3


def test_the_small_gain_grid_stops_at_32(e1):
    assert max(e1.grid_for("S-const", 0.0, 32)["k"]) == 32
    assert max(e1.grid_for("S-const", 0.0)["k"]) == 8192


def test_secondary_measures_count_failures_at_the_horizon(e1):
    nan = float("nan")
    ev = {"activation_tick": np.array([[[0, 11, -1], [0, -1, -1]]]),
          "reach_tick": np.array([[[10, -1, -1], [-1, -1, -1]]]),
          "path_length": np.array([[[5.0, 2.0, 0.0], [30.0, 0.0, 0.0]]]),
          "target_x": np.array([[[5.0, 5.0, 5.0], [5.0, 5.0, 5.0]]]),
          "target_y": np.array([[[5.0, 9.0, 13.0], [5.0, 9.0, 13.0]]]),
          "start_x": np.array([[[1.0, 5.0, nan], [1.0, nan, nan]]]),
          "start_y": np.array([[[1.0, 4.0, nan], [1.0, nan, nan]]]),
          "end_x": np.array([[[5.0, nan, nan], [nan, nan, nan]]]),
          "end_y": np.array([[[4.0, nan, nan], [nan, nan, nan]]])}
    s = e1.secondary(ev, horizon=300)
    assert s["first_arrival_share"] == 0.5
    assert s["latency_mean"] == (11 + 300) / 2
    assert s["finished_leg_time_median"] == 11
    assert s["finished_leg_path_efficiency_median"] == pytest.approx(5.0 / 5.0)  # displacement 5 over path 5


# ------------------------------------------------------------------ the guards (D095)

def _freeze(e1, own=0.3):
    """A freeze consistent with the registered rules, with made-up measurements."""
    R = e1.REGISTERED
    cov = [{"sigma": s, "share_above_floor": v} for s, v in zip(R["sigma_rule"]["candidates"], (0.0, 0.0, 0.3, 0.88))]
    tuned = {}
    for name in (*e1.CONTROLS, "S-const k<=32"):
        base = "S-const" if name == "S-const k<=32" else name
        grid = e1.grid_for(base, own, R["tuning"]["s_small_gain_max_k"] if name == "S-const k<=32" else None)
        keys, combos = e1.combos_of(grid)
        means = [float((i * 7) % 11) / 10 for i in range(len(combos))]
        i = int(np.argmax(means))
        tuned[name] = {"keys": keys, "grid": grid, "means": means, "winner_index": i,
                       "params": dict(zip(keys, [float(x) for x in combos[i]])), "tuned_mean": means[i]}
    tuned["oracle"] = {"params": dict(R["oracle"]), "tuned_mean": 5.0}
    import json as _json
    return _json.loads(_json.dumps({"registered": R, "coverage": cov, "sigma": 6.0, "sigma_flagged": True,
                                    "own_body": {"own_body_max_current": own}, "tuned": tuned,
                                    "navigator": e1.navigator_of(tuned)}))


def test_a_consistent_freeze_is_accepted(e1):
    e1.validate_freeze(_freeze(e1))


@pytest.mark.parametrize("tamper", ["sigma", "winner", "navigator", "registered", "grid", "oracle"])
def test_a_freeze_whose_choices_do_not_follow_from_its_rows_is_refused(e1, tamper):
    f = _freeze(e1)
    if tamper == "sigma":
        f["sigma"] = 4.0
    elif tamper == "winner":
        f["tuned"]["constant"]["params"]["speed"] = 0.123
    elif tamper == "navigator":
        f["navigator"] = "M-avg" if f["navigator"] == "S-const" else "S-const"
    elif tamper == "registered":
        f["registered"]["gate"]["baseline_margin"] = 0.1
    elif tamper == "grid":
        f["tuned"]["K"]["means"] = f["tuned"]["K"]["means"][:-1]
    elif tamper == "oracle":
        f["tuned"]["oracle"]["params"]["k"] = 9.0
    with pytest.raises(SystemExit):
        e1.validate_freeze(f)


def test_a_stage_marker_is_exclusive(e1, tmp_path, monkeypatch):
    monkeypatch.setattr(e1, "EXP", tmp_path)
    e1.start_marker("gate", {"git_commit": "x"})
    with pytest.raises(SystemExit):
        e1.start_marker("gate", {"git_commit": "x"})


def test_json_is_written_with_lf_and_hashed_normalised(e1, tmp_path):
    p = tmp_path / "f.json"
    e1.write_json(p, {"a": [1, 2]})
    raw = p.read_bytes()
    assert b"\r\n" not in raw
    h = e1.file_sha256(p)
    p.write_bytes(raw.replace(b"\n", b"\r\n"))  # as a Windows checkout may present it
    assert e1.file_sha256(p) == h


def test_formal_stages_refuse_the_cpu(e1):
    with pytest.raises(SystemExit):
        e1.require_formal("cpu", {"dirty": False, "branch": "roadmap"})


def test_the_cap_raises_before_it_is_exceeded(e1, monkeypatch):
    monkeypatch.setattr(e1, "spent_hours", lambda: e1.REGISTERED["cap_gpu_hours"] + 0.01)
    with pytest.raises(e1.CapReached):
        e1.check_cap(__import__("time").perf_counter())


def test_stage_ids_skip_the_touched_worlds_and_avoid_smoke_ids(e1):
    off = e1.REGISTERED["id_offset"]
    assert off >= 32
    for stage in ("pilot", "tuning", "gate"):
        ids = e1.ids_for(stage, 256)
        assert len(ids) == 256 and not set(ids.tolist()) & set(e1.SMOKE_IDS.tolist())
    assert e1.ids_for("pilot", 1)[0] == e1.PILOT_IDS[off]


def test_the_cue_rule_bootstraps_the_proportional_contrast(e1):
    """Astra's counter-example (D095): real alternating 2 and 6, mirrored = real - 2. The drop is
    half the mean, but 0.5 x real - mirrored is negative on some worlds, and its bound is below 0."""
    real = np.tile([2.0, 6.0], 512)
    counts = {"navigator": real, "navigator mirrored": real - 2}
    counts.update({b: np.zeros_like(real) for b in e1.REGISTERED["gate"]["baselines"]})
    rules = e1.gate_rules(counts)
    assert rules["cue"]["lower_95"] < 0 and not rules["cue"]["passed"]


def test_reliability_counts_episodes_with_two_arrivals(e1):
    real = np.array([2.0] * 820 + [1.0] * 204)
    counts = {"navigator": real, "navigator mirrored": np.zeros_like(real)}
    counts.update({b: np.zeros_like(real) for b in e1.REGISTERED["gate"]["baselines"]})
    r = e1.gate_rules(counts)["reliability"]
    assert r["episodes_with_at_least_2"] == 820 and r["passed"]
    counts["navigator"] = np.array([2.0] * 819 + [1.0] * 205)
    assert not e1.gate_rules(counts)["reliability"]["passed"]
