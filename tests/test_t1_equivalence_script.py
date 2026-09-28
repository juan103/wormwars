"""The class E checker in `scripts/t1_equivalence.py` (T1, D091): strict equality, the classification
of single-strain chunks, and the cross-composition table. A checker that cannot fail proves nothing."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def eq():
    spec = importlib.util.spec_from_file_location("t1_equivalence", ROOT / "scripts" / "t1_equivalence.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_equal_arrays_pass(eq):
    a = np.array([1.0, 2.5], dtype=np.float32)
    assert eq._eq(a, a.copy())["equal"]


@pytest.mark.parametrize("bad", [np.nan, np.inf])
def test_matching_non_finite_values_do_not_pass(eq, bad):
    a = np.array([1.0, bad], dtype=np.float32)
    r = eq._eq(a, a.copy())
    assert not r["equal"] and not r["finite"]


def test_signed_zeros_are_different_bits(eq):
    assert not eq._eq(np.array([0.0], dtype=np.float32), np.array([-0.0], dtype=np.float32))["equal"]


def test_a_dtype_mismatch_does_not_pass(eq):
    assert not eq._eq(np.array([1.0], dtype=np.float32), np.array([1.0], dtype=np.float64))["equal"]


def test_a_last_bit_difference_is_caught(eq):
    a = np.array([1.0], dtype=np.float32)
    b = np.nextafter(a, np.float32(2))
    r = eq._eq(a, b)
    assert not r["equal"] and r["unequal"] == 1


def test_a_single_strain_remainder_is_classified_from_the_counts(eq):
    """The first reference stored no remainder flag; 256 strains in chunks of 3 leave one alone."""
    old_desc = {"T1/random256x8/chunk3": {"strains": 256, "worlds": 8, "per_chunk": 3},
                "T1/random256x8/chunk4": {"strains": 256, "worlds": 8, "per_chunk": 4},
                "T1/random256x8/chunk256": {"strains": 256, "worlds": 8, "per_chunk": 256}}
    keys = [f"{c}/score" for c in old_desc]
    pairs = {p[0]: p for p in eq.single_strain_pairs(keys, old_desc)}
    assert pairs["T1/random256x8/chunk3/score"][1] == "T1/random256x8/chunk256/score"
    assert "T1/random256x8/chunk4/score" not in pairs


def test_an_explicit_batch_reference_is_used(eq):
    desc = {"x/chunk1": {"strains": 4, "per_chunk": 1, "batch_ref": "y/chunk4"},
            "y/chunk4": {"strains": 4, "per_chunk": 4}}
    pairs = eq.single_strain_pairs(["x/chunk1/score", "y/chunk4/score"], desc)
    assert pairs == [("x/chunk1/score", "y/chunk4/score", 4)]


def test_a_single_strain_output_whose_batch_is_missing_is_refused(eq):
    """The guard must be able to fail: a single-strain output with no batch output to compare
    against is an error, not a skipped comparison (Astra, Fable, D092)."""
    desc = {"x/chunk1": {"strains": 4, "per_chunk": 1}}
    with pytest.raises(AssertionError):
        eq.single_strain_pairs(["x/chunk1/score"], desc)


def test_an_output_without_a_case_description_is_refused(eq):
    with pytest.raises(AssertionError):
        eq.single_strain_pairs(["x/chunk1/score"], {})


def _outputs(eq, keys):
    return {k: np.arange(4, dtype=np.float32) for k in keys}


def test_compare_refuses_an_output_missing_from_the_new_run(eq):
    desc = {"c/chunk4": {"strains": 4, "per_chunk": 4}}
    ref = _outputs(eq, ["c/chunk4/score", "c/chunk4/energy"])
    new = _outputs(eq, ["c/chunk4/score"])
    with pytest.raises(AssertionError):
        eq.compare(ref, desc, new, new)


def test_compare_refuses_an_output_the_reference_lacks(eq):
    """An older reference that omits newly added cases must not pass them silently (Astra, D092)."""
    desc = {"c/chunk4": {"strains": 4, "per_chunk": 4}, "d/chunk4": {"strains": 4, "per_chunk": 4}}
    ref = _outputs(eq, ["c/chunk4/score"])
    new = _outputs(eq, ["c/chunk4/score", "d/chunk4/score"])
    with pytest.raises(AssertionError):
        eq.compare(ref, desc, new, new)


def test_compare_refuses_empty_inventories(eq):
    with pytest.raises(AssertionError):
        eq.compare({}, {}, {}, {})


def test_compare_passes_complete_equal_inventories(eq):
    desc = {"c/chunk4": {"strains": 4, "per_chunk": 4}, "c/chunk1": {"strains": 4, "per_chunk": 1}}
    out = _outputs(eq, ["c/chunk4/score", "c/chunk1/score"])
    r = eq.compare(out, desc, out, out)
    assert all(r["passed"].values())


def test_cross_composition_compares_each_chunking_with_the_largest(eq):
    desc = {"c/chunk2": {"strains": 4, "per_chunk": 2}, "c/chunk4": {"strains": 4, "per_chunk": 4},
            "c/chunk1": {"strains": 4, "per_chunk": 1}}
    full = np.arange(4, dtype=np.float32)
    outputs = {f"c/chunk{k}/{f}": full.copy() for k in (1, 2, 4) for f in eq.FIELDS}
    outputs["c/chunk2/score"] = full + np.float32(1)
    table = eq.cross_composition(outputs, desc)
    assert not table["c/chunk2 vs chunk4/score"]["equal"]
    assert table["c/chunk2 vs chunk4/energy"]["equal"]
    assert not any(k.startswith("c/chunk1") for k in table)  # single-strain cases are the other leg
