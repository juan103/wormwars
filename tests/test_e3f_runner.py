"""E3f's thin runner over E3d's (docs/E3/E3f-DESIGN.md v1 §1, §3): H = 1 800, k_r = 0 only, a fresh seed and fresh
blocks, the label, both designs bound, both runners guarded, reduction 3's ids."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name, file):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def X():
    return _load("e3f_under_test", "e3f.py")


def test_the_overrides(X):
    D = X.D
    R = D.REGISTERED
    assert (R["c"], R["H"], R["k_r"], R["maze_seed"]) == (6, 1800, [0], 1_192_000)
    assert R["blocks"] == {"calibration": [32_000, 32_128], "confirmation": [32_200, 32_456],
                           "tree_reference": [32_200, 32_328], "tangent": [32_200, 32_264]}
    assert D.EXP == ROOT / "experiments" / "E3-ab-organism" / "E3f" and D.OUT == ROOT / "runs" / "e3f"
    assert D.SMOKE_DIR == ROOT / "runs" / "e3f-smoke" and D.LABEL == "E3f" and X.NAME == "e3f"
    assert D.E.OUTCOMES["stopped"].startswith("E3f:")
    assert set(D.DESIGNS) == {"docs/E3/E3f-DESIGN.md", "docs/E3/E3d-DESIGN.md"}
    assert {"docs/E3/E3f-DESIGN.md", "docs/E3/E3d-DESIGN.md"} <= set(D.GUARDED)
    assert D.RUNNERS == ["scripts/e3f.py", "scripts/e3d.py"]
    assert D.REGISTERED["parent_design_sha256"] == "37ee0c39868f074446cca43fd0242ce8bf72e9f90127fdafbade60394e4b4147"
    assert D.cfg_for("islands", 0, "shared").world.max_ticks == 1800


def test_reduction_3_cuts_e3fs_own_tree_reference(X):
    assert X.D.reduced_registry(3)["blocks"]["tree_reference"] == [32_200, 32_264]


def test_the_designs_are_pinned_and_current(X):
    D = X.D
    for path, key in D.DESIGNS.items():
        assert D.REGISTERED[key] == D.file_sha256(path), path


def test_every_calibration_id_builds_at_k_r_0():
    from wormwars.e3 import islands as I
    for mid in range(32_000, 32_128):
        im = I.islands_for(run_seed=1_192_000, maze_id=mid, c=6, k_r=0)
        assert I.failed_check(im.maze, im.a, im.b) is None


def test_the_calibration_choice_with_one_k_r(X):
    """With k_r = 0 only, calibration passes or fails on its one block (E3f §1)."""
    GT = X.D.GT
    ok = {"failed": [], "precondition": True}
    bad = {"failed": ["G2a"], "precondition": True}
    assert GT.choose_k({0: ok}, {0: 0.8}, 0.5, label="E3f")["k_r"] == 0
    assert GT.choose_k({0: bad}, {0: 0.8}, 0.5, label="E3f")["verdict"] == "E3f: failed at calibration"
