"""03h's rule-7 checker (scripts/e03h_equivalence.py): equal shapes, finite values and exact equality, or the check
fails (Astra: an absolute difference passed NaNs and broadcast shapes)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def _m():
    spec = importlib.util.spec_from_file_location("e03h_eq_test", ROOT / "scripts" / "e03h_equivalence.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _ref():
    rng = np.random.default_rng(0)
    return {k: rng.random((4, 16)).astype(np.float32) for k in
            ("score", "energy", "alive", "eaten", "pellet_eaten", "food_start")}


def test_identical_endpoints_pass():
    M, ref = _m(), _ref()
    assert M.compare_endpoints({k: v.copy() for k, v in ref.items()}, ref)["bit_equal"]


def test_a_finite_mismatch_fails():
    M, ref = _m(), _ref()
    got = {k: v.copy() for k, v in ref.items()}
    got["energy"][2, 3] = np.nextafter(got["energy"][2, 3], np.float32(2))
    r = M.compare_endpoints(got, ref)
    assert not r["bit_equal"] and r["endpoints"]["energy"]["unequal_values"] == 1


def test_a_nan_fails():
    M, ref = _m(), _ref()
    got = {k: v.copy() for k, v in ref.items()}
    got["score"][0, 0] = np.nan
    r = M.compare_endpoints(got, ref)
    assert not r["bit_equal"] and r["endpoints"]["score"]["non_finite"] == 1
    both = {k: v.copy() for k, v in ref.items()}
    ref2 = {k: v.copy() for k, v in ref.items()}
    both["score"][0, 0] = ref2["score"][0, 0] = np.nan
    assert not M.compare_endpoints(both, ref2)["bit_equal"]  # NaN never counts as equal


def test_a_broadcastable_shape_mismatch_fails():
    M, ref = _m(), _ref()
    ref["food_start"] = np.tile(ref["food_start"][:1], (4, 1))
    got = {k: v.copy() for k, v in ref.items()}
    got["food_start"] = got["food_start"][:1]  # [1, 16] would broadcast against [4, 16]
    r = M.compare_endpoints(got, ref)
    assert not r["bit_equal"] and r["endpoints"]["food_start"]["shape_match"] is False
