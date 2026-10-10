"""E3d's runner (scripts/e3d.py; docs/E3/E3d-DESIGN.md v2.2 §3-§8): the conditions per block, W2-turn's bound,
the projection's reductions, the binding guard and the report."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def D():
    s = importlib.util.spec_from_file_location("e3d_under_test", ROOT / "scripts" / "e3d.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


CH = {"s_mod": [{"run": r} for r in range(8)], "s_dense": [{"run": r} for r in range(10, 18)],
      "p_sel": [{"run": r} for r in range(20, 24)], "p_joint": [{"run": r} for r in range(8)]}


def test_who_plays_where(D):
    cal, conf, tree = (D.specs(b, CH) for b in ("calibration", "confirmation", "tree_reference"))
    names = lambda sp: [s["name"] for s in sp]  # noqa: E731
    blind = [s for s in cal if s["role"] == "blind"]
    # 2 wall-followers, W2, 13 W2-turn points, 2 oscillators, 9 walks, the seed and 4 arms with noses removed
    assert len(blind) == 2 + 1 + 13 + 2 + 9 + 1 + 4
    assert {"oracle", "follower_shared", "follower_none", "seed"} <= set(names(cal))
    assert not any(n.endswith("_intact") for n in names(cal))
    assert {f"{a}_intact" for a in CH} <= set(names(conf)) and {f"{a}_intact" for a in CH} <= set(names(tree))
    assert names(conf) == names(tree)
    assert all(s["noses"] is False for s in blind if s["kind"] in ("seed", "arm"))


def test_w2_turn_bound(D):
    from wormwars.connectome import load_connectome
    from wormwars.e3.task import shuttle_config
    con, bcfg = load_connectome(), shuttle_config().brain
    assert D.w2_turn(con, bcfg, 1.95).name == "W2+turn1.95"
    for r in (2.0, -2.0, 2.5):
        with pytest.raises(ValueError, match="outside"):
            D.w2_turn(con, bcfg, r)


def test_the_projection_applies_the_reductions_in_order(D):
    one = D.projection({"scripted": 0.0, "neural": 0.0, "arm": 0.0, "records": 0.0}, CH)
    assert one["admitted"] and one["reductions"] == 0
    # cost per world chosen so the full plan is over 3 h, the walk reduction alone is not enough, the W2-turn one is
    full = sum(1 for _ in D.specs("calibration", CH))
    big = D.projection({"scripted": 2.0, "neural": 2.0, "arm": 2.0, "records": 0.0}, CH)
    hours = [t["hours"] for t in big["tried"]]
    assert hours == sorted(hours, reverse=True) and len(hours) >= 2
    huge = D.projection({"scripted": 100.0, "neural": 100.0, "arm": 100.0, "records": 0.0}, CH)
    assert not huge["admitted"] and huge["plan"] is None and len(huge["tried"]) == 4
    assert D.REGISTERED["turn_grid"][-1] == 1.95 and len(D.REGISTERED["turn_grid"]) == 13  # restored
    assert full > 0


def test_the_binding_guard(D, monkeypatch):
    args = types.SimpleNamespace(smoke=False, guarded=False)
    monkeypatch.setitem(D.REGISTERED, "binding_commit", None)
    with pytest.raises(SystemExit, match="not bound"):
        D.require_bound(args)
    monkeypatch.setitem(D.REGISTERED, "binding_commit", "HEAD")
    monkeypatch.setitem(D.REGISTERED, "design_sha256", "0" * 64)
    with pytest.raises(SystemExit, match="differs from the bound text"):
        D.require_bound(args)
    monkeypatch.setitem(D.REGISTERED, "design_sha256", D.design_sha256())
    D.require_bound(args)  # HEAD against HEAD: no engine change
    D.require_bound(types.SimpleNamespace(smoke=True, guarded=False))  # smoke: unguarded


def _cond(role, *visits):
    return {"role": role, "strains": [{"visits": list(v), "legs": list(np.maximum(np.asarray(v) - 1, 0)),
                                       "visited_share": [1.0] * len(v), "round_trip_share": [0.0] * len(v),
                                       "no_first_visit_share": [0.0] * len(v)} for v in visits]}


MAZES = [{"open_share": 0.7, "junctions": 10, "dead_ends": 6, "detour": 1.5, "line_of_sight_share": 0.25,
          "spawn_candidates": 12, "entrances": [1, 2], "redraw": r, "scent_reach": [True, f]}
         for r, f in ((0, True), (1, False), (0, True))]


def test_the_report(D):
    good = {"follower_shared": _cond("navigator", [8.0] * 3), "oracle": _cond("navigator", [20.0] * 3),
            "seed": _cond("organism", [4.0] * 3), "walk": _cond("blind", [1.0] * 3),
            "s_mod_intact": _cond("organism", [2.0] * 3), "p_joint_intact": _cond("organism", [4.0] * 3)}
    tree = {**good, "s_mod_intact": _cond("organism", [6.0] * 3), "p_joint_intact": _cond("organism", [5.0] * 3)}
    from wormwars.e3 import e3d_gate as GT
    cal = {"blocks": {"0": {"gate": GT.gate({"conditions": good}), "first_draw_feasible_share": 0.7}},
           "choice": {"k_r": 0, "verdict": "chosen", "failures": {}}}
    conf = {"blocks": {"confirmation": {"conditions": good, "mazes": MAZES},
                       "tree_reference": {"conditions": tree, "mazes": MAZES},
                       "tangent": {"conditions": {"walk": _cond("blind", [0.5] * 3)}, "mazes": MAZES}}}
    r = D.report_from({"calibrate": cal, "confirm": conf})
    assert r["verdict"] == "E3d: passed"
    assert r["predictions"]["s_mod"]["holds"] and r["predictions"]["p_joint"]["holds"]
    assert r["bootstrap"]["b_max"]["point"] == 1.0
    assert r["maze_summary"]["confirmation"]["redrawn_share"] == pytest.approx(1 / 3)
    assert r["maze_summary"]["confirmation"]["entrances"] == pytest.approx(1.5)
    assert r["scent_reach_split"]["mazes_both_flagged"] == 2 and r["scent_reach_split"]["mazes_other"] == 1
    assert r["tangent_blind_means"] == {"walk": 0.5}
    failed = D.report_from({"calibrate": {**cal, "choice": {"k_r": None, "verdict": "E3d: failed at calibration",
                                                           "failures": {0: ["G1a"]}}}})
    assert failed["verdict"] == "E3d: failed at calibration"
