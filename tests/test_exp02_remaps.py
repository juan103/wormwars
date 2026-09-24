"""Remap selection: matched to the food neurons on degree and routing, by a fixed rule."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.connectome import load_connectome
from wormwars.exp02 import remaps
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con)


def test_hops_follow_the_direction_of_the_synapse():
    adj = np.zeros((3, 3), dtype=bool)
    adj[0, 1] = adj[1, 2] = True  # 0 -> 1 -> 2
    assert remaps.hops_to(adj, 0, {2}) == 2
    assert remaps.hops_to(adj, 2, {0}) == 99


def test_candidates_are_bilateral_sensory_pairs_outside_the_interface(parts):
    con, iface = parts
    cands = remaps.candidate_pairs(con, iface)
    mapped = {con.names[i] for i in iface.mapped_neurons}
    assert cands == sorted(cands) and len(cands) >= 9
    for base in cands:
        for side in "LR":
            n = base + side
            assert n in con.index_of and n not in mapped
            assert con.classes[con.index(n)] == "sensory"


def test_motivated_pairs_are_the_food_neurons(parts):
    assert remaps.motivated_pairs(*parts) == ["AWA", "AWC", "ASE"]


def test_matched_sets_are_disjoint_triples_and_deterministic(parts):
    con, iface = parts
    a = remaps.choose_matched(con, iface)
    b = remaps.choose_matched(con, iface)
    assert a == b and len(a) == 2
    assert all(len(s) == 3 for s in a)
    assert not set(a[0]) & set(a[1])


def test_every_matched_pair_meets_the_routing_tolerances_on_its_own(parts):
    """Averaging let shortcut pairs in twice: a triple-mean rule admitted URX (direct read-out
    weight 13, one hop) behind a weakly connected partner, and a std-scaled pairwise rule admitted
    BAG, OLQD and OLQV (12-20), because the extreme shortcuts (FLP 174) inflate the scale. Routing
    is therefore a hard per-pair tolerance: no remap pair may be closer to the read-out than the
    food neurons are."""
    con, iface = parts
    for s in remaps.choose_matched(con, iface):
        for b in s:
            f = remaps.pair_features(con, iface, b)
            assert f["hops_forward"] >= remaps.ROUTING_TOLERANCE["hops_forward"], (b, f)
            assert f["hops_turn"] >= remaps.ROUTING_TOLERANCE["hops_turn"], (b, f)
            assert f["direct_weight"] <= remaps.ROUTING_TOLERANCE["direct_weight"], (b, f)


def test_the_food_neurons_themselves_meet_the_tolerances(parts):
    con, iface = parts
    for b in remaps.motivated_pairs(con, iface):
        f = remaps.pair_features(con, iface, b)
        assert remaps.within_routing_tolerance(f), (b, f)


def test_shortcut_pairs_have_more_direct_read_out_weight(parts):
    con, iface = parts
    matched = remaps.choose_matched(con, iface)
    short = remaps.choose_shortcut(con, iface, exclude={p for s in matched for p in s})
    dw = lambda b: remaps.pair_features(con, iface, b)["direct_weight"]  # noqa: E731
    assert min(dw(b) for b in short) > max(dw(b) for s in matched for b in s)


def test_record_is_json_ready_and_carries_no_edges(parts):
    import json

    rec = remaps.remap_record(*parts)
    text = json.dumps(rec)
    assert set(rec["sets"]) == {"M0", "R1", "R2", "MS"}
    assert rec["sets"]["M0"] == [["AWAL", "AWAR"], ["AWCL", "AWCR"], ["ASEL", "ASER"]]
    # no edges or matrices: every per-pair entry is exactly the six scalar summary features
    for base, feats in rec["pair_features"].items():
        assert set(feats) == set(remaps.FEATURES), base
        assert all(isinstance(v, float) for v in feats.values()), base
    assert "[[" not in text.replace('[["', "")  # the only nested lists are the name pairs
