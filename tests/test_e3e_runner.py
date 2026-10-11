"""E3e's thin runner over E3d's (docs/E3/E3e-DESIGN.md v2 §1, §1a, §3): every override, both designs bound, both
runners guarded, the labels, reduction 3's ids, and a calibration failure reported in full."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name, file):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def X():
    return _load("e3e_under_test", "e3e.py")


def test_the_overrides(X):
    D = X.D
    R = D.REGISTERED
    assert (R["c"], R["maze_seed"]) == (7, 1_191_000)
    assert R["blocks"] == {"calibration": [31_000, 31_128], "confirmation": [31_200, 31_456],
                           "tree_reference": [31_200, 31_328], "tangent": [31_200, 31_264]}
    assert D.EXP == ROOT / "experiments" / "E3-ab-organism" / "E3e" and D.OUT == ROOT / "runs" / "e3e"
    assert D.LABEL == "E3e" and X.NAME == "e3e"
    assert D.E.EXP == D.EXP and D.E.OUT == D.OUT and D.E.REGISTERED is R
    assert D.E.OUTCOMES["stopped"].startswith("E3e:") and D.E.OUTCOMES["cap"].startswith("E3e:")
    assert {"docs/E3/E3e-DESIGN.md", "docs/E3/E3d-DESIGN.md"} <= set(D.GUARDED) and set(D.DESIGNS) == {
        "docs/E3/E3e-DESIGN.md", "docs/E3/E3d-DESIGN.md"}
    assert D.RUNNERS == ["scripts/e3e.py", "scripts/e3d.py"]
    assert D.REFERENCES == ROOT / "experiments" / "E3-ab-organism" / "E3d"  # E3d's equivalence references stand


def test_e3d_keeps_its_own_defaults():
    D = _load("e3d_defaults_under_test", "e3d.py")
    assert D.LABEL == "E3d" and D.REGISTERED["c"] == 6 and D.EXP.name == "E3d"
    assert D.REGISTERED["blocks"]["tree_reference"] == [30_200, 30_328]


def test_both_design_hashes_are_pinned_and_current(X):
    D = X.D
    for path, key in D.DESIGNS.items():
        assert D.REGISTERED[key] == D.file_sha256(path), path
    assert D.REGISTERED["parent_design_sha256"] == "37ee0c39868f074446cca43fd0242ce8bf72e9f90127fdafbade60394e4b4147"


def test_the_guard_refuses_a_changed_parent_design(X, monkeypatch):
    D = X.D
    args = types.SimpleNamespace(smoke=False, guarded=False)
    monkeypatch.setitem(D.REGISTERED, "parent_design_sha256", "0" * 64)
    monkeypatch.setitem(D.REGISTERED, "binding_commit", "x")  # bound, so the parent's hash is what refuses
    monkeypatch.setattr(D, "engine_changes", lambda: [])
    monkeypatch.setattr(D, "script_changes", lambda: [])
    with pytest.raises(SystemExit, match="E3d-DESIGN.md"):
        D.require_bound(args)


def test_both_runners_are_guarded(X, monkeypatch):
    D = X.D
    old = 'A = 1\n    "binding_commit": "x",\n'
    files = {"diff": "scripts/e3d.py\nscripts/e3e.py\n", "scripts/e3d.py": old, "scripts/e3e.py": old}
    head = dict(files)

    def git(*a, root=None):
        if a[0] == "diff":
            return files["diff"]
        rev, path = a[1].split(":", 1)
        return head[path] if rev == "HEAD" else files[path]

    monkeypatch.setattr(D.E.reg, "git", git)
    monkeypatch.setitem(D.REGISTERED, "binding_commit", "b")
    head["scripts/e3e.py"] = old.replace('"x"', '"y"')  # only a binding value
    assert D.script_changes() == []
    head["scripts/e3d.py"] = old.replace("A = 1", "A = 2")  # the shared runner changed
    assert D.script_changes() == ["scripts/e3d.py"]


def test_reduction_3_cuts_e3es_own_tree_reference(X):
    D = X.D
    R = D.reduced_registry(3)
    assert R["blocks"]["tree_reference"] == [31_200, 31_264]
    assert R["blocks"]["confirmation"] == [31_200, 31_456]
    assert D.reduced_registry(0)["blocks"]["tree_reference"] == [31_200, 31_328]


def test_the_smoke_folder(X):
    D = _load("e3e_smoke_under_test", "e3e.py").D
    D.use_smoke(types.SimpleNamespace(command="report"))
    assert D.EXP == ROOT / "runs" / "e3e-smoke" and D.E.EXP == D.EXP


def _cond(role, *visits):
    return {"role": role, "strains": [{"visits": list(v), "legs": list(np.maximum(np.asarray(v) - 1, 0)),
                                       "visited_share": [1.0] * len(v), "round_trip_share": [0.0] * len(v),
                                       "no_first_visit_share": [0.0] * len(v), "arrived_a": [1.0] * len(v),
                                       "arrived_b": [1.0] * len(v)} for v in visits]}


def test_a_calibration_failure_is_reported_in_full_and_labelled(X):
    D = X.D
    mazes = [{"scent_reach": [True, True]}] * 3
    cond = {"follower_shared": _cond("navigator", [8.0] * 3), "oracle": _cond("navigator", [20.0] * 3),
            "seed": _cond("organism", [4.0] * 3), "walk": _cond("blind", [3.0] * 3),
            "s_mod_noses": _cond("blind", [0.0] * 3, [3.5] * 3)}
    block = {"conditions": cond, "mazes": mazes, "first_draw_feasible_share": 0.7}
    g = D.GT.gate(block, label=D.LABEL)
    block["gate"] = g
    cal = {"blocks": {"0": block}, "choice": D.GT.choose_k({0: g}, {0: 0.7}, 0.5, label=D.LABEL)}
    r = D.report_from({"calibrate": cal})
    assert r["verdict"] == "E3e: failed at calibration"
    s = r["calibration"]["0"]
    assert s["gate"]["b_max_member"] == "s_mod_noses#1"
    assert s["summary"]["bootstrap"]["b_max"]["point"] == pytest.approx(3.5)
    assert s["summary"]["scent_split"]["goals_flagged"] == 6
    assert s["summary"]["b_max_member_detail"]["round_trip_share"] == 0.0  # the multi-strain member resolved


def test_a_changed_parent_hash_in_the_runner_is_refused(X, monkeypatch):
    """Fable: the parent design's hash is a constant, not a binding value; changing it in a runner must be refused
    by the scripts guard, so that E3d's design cannot be amended under E3e unnoticed."""
    D = X.D
    old = '    "parent_design_sha256": "aaa",\n'
    files = {"old": old, "new": old.replace("aaa", "bbb")}

    def git(*a, root=None):
        if a[0] == "diff":
            return "scripts/e3e.py\n"
        return files["new"] if a[1].startswith("HEAD") else files["old"]

    monkeypatch.setattr(D.E.reg, "git", git)
    monkeypatch.setitem(D.REGISTERED, "binding_commit", "b")
    assert D.script_changes() == ["scripts/e3e.py"]
