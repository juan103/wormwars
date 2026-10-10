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
                                       "no_first_visit_share": [0.0] * len(v), "arrived_a": [1.0] * len(v),
                                       "arrived_b": [1.0] * len(v)} for v in visits]}


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


def test_the_registered_design_hash_is_the_designs(D):
    """A design edit without re-binding fails here, before any stage would refuse it (Fable)."""
    assert D.REGISTERED["design_sha256"] == D.design_sha256()


def test_the_guard_refuses_engine_or_script_changes(D, monkeypatch):
    args = types.SimpleNamespace(smoke=False, guarded=False)
    monkeypatch.setitem(D.REGISTERED, "design_sha256", D.design_sha256())
    monkeypatch.setattr(D, "engine_changes", lambda: ["M\twormwars/e3/islands.py"])
    with pytest.raises(SystemExit, match="engine changed"):
        D.require_bound(args)
    monkeypatch.setattr(D, "engine_changes", lambda: [])
    monkeypatch.setattr(D, "script_changes", lambda: ["scripts/e2.py"])
    with pytest.raises(SystemExit, match="scripts changed"):
        D.require_bound(args)


def test_script_changes_ignore_only_the_binding_lines(D, monkeypatch):
    old = 'A = 1\n    "binding_commit": "x",\n    "design_sha256": "y",\nB = 2\n'
    files = {"diff": "scripts/e3d.py\n", "old": old, "new": old.replace('"x"', '"z"').replace('"y"', '"w"')}

    def git(*a, root=None):
        if a[0] == "diff":
            return files["diff"]
        return files["old"] if a[1].endswith(":scripts/e3d.py") and not a[1].startswith("HEAD") else files["new"]

    monkeypatch.setattr(D.E.reg, "git", git)
    monkeypatch.setitem(D.REGISTERED, "binding_commit", "b")
    assert D.script_changes() == []
    files["new"] = files["new"].replace("B = 2", "B = 3")
    assert D.script_changes() == ["scripts/e3d.py"]
    files["diff"] = "scripts/e3d.py\nscripts/e2.py\n"
    assert set(D.script_changes()) == {"scripts/e3d.py", "scripts/e2.py"}


def test_the_rollout_leg_needs_a_fresh_successful_comparison(D, monkeypatch, tmp_path):
    """Astra: a stale identical record and a failing subprocess must not pass."""
    import json
    monkeypatch.setattr(D, "OUT", tmp_path)
    rec = tmp_path / "equivalence-cpu.json"

    def fake(write, rc):
        def run(cmd, **kw):
            if write is not None:
                rec.write_text(json.dumps({"identical": write}), encoding="utf-8")
            return types.SimpleNamespace(returncode=rc, stderr="boom" if rc else "")
        return run

    rec.write_text(json.dumps({"identical": True}), encoding="utf-8")  # stale
    assert D.rollout_leg("cpu", "cpu", run=fake(None, 1))["identical"] is False
    rec.write_text(json.dumps({"identical": True}), encoding="utf-8")  # stale again; a run that writes nothing
    assert D.rollout_leg("cpu", "cpu", run=fake(None, 0))["identical"] is False
    assert D.rollout_leg("cpu", "cpu", run=fake(True, 1))["identical"] is False
    assert D.rollout_leg("cpu", "cpu", run=fake(False, 0))["identical"] is False
    assert D.rollout_leg("cpu", "cpu", run=fake(True, 0))["identical"] is True


def test_the_projection_reserves_spent_hours(D):
    free = D.projection({"scripted": 0.1, "neural": 0.1, "arm": 0.1, "records": 0.0}, CH)
    h = free["tried"][0]["hours"]
    assert free["admitted"] and free["reductions"] == 0
    tight = D.projection({"scripted": 0.1, "neural": 0.1, "arm": 0.1, "records": 0.0}, CH, reserved_hours=3.0 - h / 2)
    assert tight["reductions"] >= 1 or not tight["admitted"]


def test_the_scent_reach_is_read_per_goal(D):
    st = lambda a, b: {"visits": [1.0] * 4, "no_first_visit_share": [0.0] * 4, "arrived_a": a, "arrived_b": b}  # noqa: E731
    block = {"mazes": [{"scent_reach": f} for f in ([True, False], [True, True], [False, False], [False, True])],
             "conditions": {"follower_shared": {"strains": [st([1.0, 1.0, 0.0, 0.0], [0.0, 1.0, 0.0, 1.0])]},
                            "seed": {"strains": [st([0.5] * 4, [0.5] * 4)]}}}
    s = D.scent_split(block)
    f = s["per_goal"]["follower_shared"]
    assert s["goals_flagged"] == 4 and s["goals_other"] == 4
    assert f["arrived_flagged"] == 1.0 and f["arrived_other"] == 0.0
    assert f["arrived_a_flagged"] == 1.0 and f["arrived_b_other"] == 0.0


def test_summarise_maps_worlds_to_strains_and_mazes(D):
    """Two strains on two mazes: world w = strain · n + maze (play's layout); each strain's per-maze visits are
    its own worlds' (Fable: the mapping was exercised only by smoke)."""
    from wormwars.e3 import islands as I
    ids = [30_000, 30_001]
    built = [I.maze_for(run_seed=1_190_000, maze_id=m, episode=0, c=6, k_r=0) for m in ids]
    mazes, pls = [b[0] for b in built] * 2, [b[1] for b in built] * 2
    H, B = 20, 2
    vt = np.full((4, B, 4), -1)
    for w, k in enumerate([1, 2, 3, 4]):  # world w gives each wey k visits
        vt[w, :, :k] = np.arange(k)
    paths = np.zeros((4, B, H, 2), dtype=np.float32)
    for w, pl in enumerate(pls):
        paths[w] = np.array([2.5 + 4 * pl.spawns[0][1], 2.5 + 4 * pl.spawns[0][0]])
    tables = {m: D.RC.contact_tables(b[0].wall, b[1].a, b[1].b) for m, b in zip(ids, built)}
    strains, arrays = D.summarise({"visit_tick": vt}, paths, mazes, pls, ids, 2, tables, H, 6)
    assert [s["visits"] for s in strains] == [[1.0, 2.0], [3.0, 4.0]]
    assert arrays["world_ids"].tolist() == ids * 2 and arrays["strain_of_world"].tolist() == [0, 0, 1, 1]
    assert arrays["visits_contact"].shape == (2 * (1 + 2 + 3 + 4), 6)


def test_script_changes_refuse_edits_hidden_on_binding_lines(D, monkeypatch):
    """Astra: moving a binding line and appending an entry to it is an executable change; only the two binding
    values may differ."""
    old = 'R = {\n    "binding_commit": "x",\n    "design_sha256": "y",\n    "H": 2400,\n}\n'
    hidden = 'R = {\n    "design_sha256": "y",\n    "H": 2400,\n    "binding_commit": "x", "H": 60,\n}\n'
    files = {"old": old, "new": hidden}

    def git(*a, root=None):
        if a[0] == "diff":
            return "scripts/e3d.py\n"
        return files["new"] if a[1].startswith("HEAD") else files["old"]

    monkeypatch.setattr(D.E.reg, "git", git)
    monkeypatch.setitem(D.REGISTERED, "binding_commit", "b")
    assert D.script_changes() == ["scripts/e3d.py"]
    files["new"] = old.replace('"x"', '"0123abcd"').replace('"y"', '"' + "f" * 64 + '"')
    assert D.script_changes() == []


def test_the_reserve_counts_the_current_stage(D):
    """Astra: the admission reserves earlier attempts, this stage's own elapsed time and g-e's allowance."""
    clock = types.SimpleNamespace(spent_hours=lambda: 0.5, t_start=0.0)
    assert D.reserved_hours(clock, now=360.0) == pytest.approx(0.5 + 0.1 + D.REGISTERED["ge_allowance_hours"])
