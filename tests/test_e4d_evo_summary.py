"""The evolutionary E4-D's summary (`scripts/e4d_evo_summary.py`): the wiring contrasts and the control tallies, on
synthetic records (CPU; no connectome)."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("e4d_evo_summary", ROOT / "scripts" / "e4d_evo_summary.py")
S = importlib.util.module_from_spec(_s)
_s.loader.exec_module(S)

A = ("E3_A_NL", "E3_A_NR", "E3_A_CL", "E3_A_CR")
B = ("E3_B_NL", "E3_B_NR", "E3_B_CL", "E3_B_CR")
NAMES = [[a, b] for a in A for b in B] + [[b, a] for b in B for a in A]


def run_with(weights: dict) -> dict:
    return {"slot_weights": [weights.get(tuple(n), 0.0) for n in NAMES]}


def test_the_hand_built_wiring_is_a_pure_comparator_copy():
    hand = run_with(S.HAND_BUILT)
    c = S.wiring([hand, hand], NAMES)["contrasts_after_data"]
    assert c["comparator_to_comparator"]["values"]["mean"] == 3.0
    for k in ("nose_to_comparator", "comparator_to_nose", "nose_to_nose"):
        assert c[k]["values"]["mean"] == 0.0 and c[k]["positive"] == 0


def test_a_comparator_to_nose_route_is_read_as_such():
    w = {("E3_A_CL", "E3_B_NL"): 0.25, ("E3_A_CL", "E3_B_NR"): -0.25,
         ("E3_A_CR", "E3_B_NL"): -0.25, ("E3_A_CR", "E3_B_NR"): 0.25}
    out = S.wiring([run_with(w)] * 3, NAMES)
    c = out["contrasts_after_data"]
    assert c["comparator_to_nose"]["values"]["mean"] == pytest.approx(0.5) and c["comparator_to_nose"]["positive"] == 3
    assert c["comparator_to_comparator"]["values"]["mean"] == 0.0
    assert out["by_class"]["into_B.from_comparator"]["sum_abs_weight"]["mean"] == pytest.approx(1.0)
    assert out["by_class"]["into_A.from_nose"]["sum_abs_weight"]["mean"] == 0.0


def cond(rf, df, ne, per_maze_rf, per_maze_df):
    return {"real_first": rf, "decoy_first": df, "neither": ne, "trials": rf + df + ne,
            "per_maze": {"real_first": per_maze_rf, "decoy_first": per_maze_df}}


def test_the_control_tallies():
    bal = cond(1, 1, 2, [[1, 0], [0, 0]], [[0, 1], [0, 0]])
    unbal = cond(3, 0, 1, [[1, 1], [1, 0]], [[0, 0], [0, 0]])
    rev = cond(0, 3, 1, [[0, 0], [0, 0]], [[1, 1], [1, 0]])
    run = {"test": {"intact": unbal, "reversed": rev, "removed": bal, "fixed": bal, "cut": bal, "eg": bal}}
    out = S.controls([run, run])
    assert out["intact"]["real_first"]["mean"] == 0.75 and out["intact"]["balanced_per_maze"] == 0
    assert out["reversed"]["decoy_first_exceeds_real_first"] == 2
    assert out["removed"]["balanced_per_maze"] == 2 and out["removed"]["neither"]["mean"] == 0.5
    assert out["fixed"]["real_first_over_intact"]["mean"] == pytest.approx(1 / 3)


def test_a_rounded_share_returns_to_its_whole_trials():
    """The records round validation shares to 6 decimals; 117/128 is stored 0.914062 and must count as 117."""
    assert S.on_grid(0.914062) == 117 and S.on_grid(0.960938) == 123
    with pytest.raises(ValueError):
        S.on_grid(0.9145)
