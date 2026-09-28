"""03m's exploratory runner (`scripts/p4m.py`): its building blocks on the CPU, with a few genomes."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).parents[1]


@pytest.fixture(scope="module")
def p():
    spec = importlib.util.spec_from_file_location("p4m_script", ROOT / "scripts" / "p4m.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def parts(p):
    con, bank, iface = p.setup("cpu")
    g, cfg = p.probe_genomes(con, "N2", "cpu", n=4)
    return con, bank, iface, g, cfg


def test_pairs_join_left_and_right_names_only(p):
    assert p.pairs(["RIAL", "RIAR", "AVL", "PVR", "RMDL", "RMDR", "RMDDL", "RMDDR"]) == {
        "RIA": [0, 1], "RMD": [4, 5], "RMDD": [6, 7]}


def test_an_empty_deletion_reproduces_the_intact_brain(p, parts):
    con, bank, iface, g, cfg = parts
    whole = p.p4_of(p.M.history(g, cfg, iface, bank))
    res = p.history_in_chunks(g, cfg, iface, bank, [[], [5]], per_chunk=g.n_strains)
    assert (res[0]["numerator"], res[0]["denominator"]) == (whole["numerator"], whole["denominator"])
    assert res[1]["numerator"] != whole["numerator"]


def test_chunked_deletions_match_one_at_a_time_on_the_cpu(p, parts):
    con, bank, iface, g, cfg = parts
    dels = [[], [3], [7, 8]]
    one = p.history_in_chunks(g, cfg, iface, bank, dels, per_chunk=g.n_strains)
    many = p.history_in_chunks(g, cfg, iface, bank, dels, per_chunk=3 * g.n_strains)
    for a, b in zip(one, many):
        assert a["numerator"] == pytest.approx(b["numerator"], rel=1e-6)


def test_the_long_window_starts_at_03s_measurement(p, parts):
    con, bank, iface, g, cfg = parts
    h = p.M.history(g, cfg, iface, bank)["raw_turn"]
    full = p.history_full(g, cfg, iface, bank, after=20, every=10)
    assert full["ticks"] == [0, 5, 10, 20]
    np.testing.assert_allclose(full["diff"][0], h["final"], rtol=1e-6, atol=1e-9)
    np.testing.assert_allclose(full["diff"][1], h["after"], rtol=1e-6, atol=1e-9)
    np.testing.assert_allclose(full["steady_contrast"], h["steady_contrast"], rtol=1e-6, atol=1e-9)


def test_an_invalid_measurement_is_never_placed_among_the_nulls(p):
    r = p.p4_of({"raw_turn": {"final": np.zeros(4), "steady_contrast": np.zeros(4)}})
    assert r == {"numerator": 0.0, "denominator": 0.0, "P4": None, "valid": False}
    pg = p.supplement("03")
    assert p.null_position(r, pg) is None and p.lead_class(r, pg) is None
    json.dumps(r)  # standard JSON: no NaN


def test_edge_deletions_touch_one_synapse_type(p, parts):
    con, bank, iface, g, cfg = parts
    k = 10
    chem = p.delete_edges(g, [[k]] * g.n_strains, "chemical")
    gap = p.delete_edges(g, [[k]] * g.n_strains, "gap")
    touch_c = torch.isin(g.spec.chem_i, torch.tensor([k])) | torch.isin(g.spec.chem_j, torch.tensor([k]))
    touch_g = torch.isin(g.spec.gap_i, torch.tensor([k])) | torch.isin(g.spec.gap_j, torch.tensor([k]))
    assert (chem.w[:, touch_c] == 0).all() and torch.equal(chem.g, g.g)
    assert (gap.g[:, touch_g] == 0).all() and torch.equal(gap.w, g.w)
    assert torch.equal(chem.bias, g.bias)


def test_formal_runs_refuse_another_genome_count(p):
    from types import SimpleNamespace
    with pytest.raises(SystemExit):
        p.require_formal_size(SimpleNamespace(genomes=512))
