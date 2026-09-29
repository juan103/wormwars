"""E2d, Part A (`scripts/e2d_records.py`): the record-only analysis, pinned against E2's committed
records. Written after the script (a pin, D129); each pin was sabotage-checked."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def doc(tmp_path_factory):
    spec = importlib.util.spec_from_file_location("e2d_records", ROOT / "scripts" / "e2d_records.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.OUT = tmp_path_factory.mktemp("e2d") / "part-a.json"  # never the committed file
    return mod.main()


def test_a_genome_in_two_sets_is_counted_once(doc):
    assert doc["shared_genomes"] == ["es run06 = extension run06"]
    assert [r["pairs"] for r in doc["ranking"]["rows"]] == [74, 113, 106]


def test_ranking_rates_add_up_and_rise_with_worlds(doc):
    for row in doc["ranking"]["rows"]:
        for k in ("k8", "k32", "k128"):
            r = row[k]
            assert r["ties_half"] == pytest.approx(r["strict"] + r["tied"] / 2)
        assert row["k8"]["ties_half"] < row["k32"]["ties_half"] < row["k128"]["ties_half"] + 1e-12
    first = doc["ranking"]["rows"][0]["k8"]  # the smallest gaps, at E2's 8 training worlds
    assert (round(first["strict"], 3), round(first["tied"], 3), round(first["ties_half"], 3)) == (0.543, 0.156, 0.621)


def test_the_nominations_and_the_plateau_match_the_records(doc):
    n = doc["nomination"]
    assert n["random"]["nominees"] == n["ga"]["nominees"] == 320  # 8 runs x 40 checkpoints after generation 0
    assert n["random"]["training_mean"] == pytest.approx(1.1457, abs=1e-3)
    assert n["ga"]["validation_mean"] == pytest.approx(1.6260, abs=1e-3)
    p = doc["plateau"]
    assert p["within_0.25_of_m_avg"] == {"ga": 7, "es": 7, "random": 0, "extension": 7}
    assert p["above_m_avg"]["extension"] == 6
