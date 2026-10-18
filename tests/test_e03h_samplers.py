"""03h's routing control (experiments/03h-history-use/DESIGN.md §3): SH-mirror-ASK and SH-route-ASK add ASKL and ASKR
to 03's routing cap, and the existing ensembles are unchanged."""

from __future__ import annotations

import hashlib

import numpy as np
import pytest

from wormwars.connectome import load_connectome
from wormwars.exp03 import samplers as S


@pytest.fixture(scope="module")
def con():
    return load_connectome()


def sha(c) -> str:
    h = hashlib.sha256()
    for a in (c.chem, c.gap):
        h.update(np.ascontiguousarray(a, dtype=np.float32).tobytes())
    return h.hexdigest()


def caps_hold(con, g, names) -> bool:
    for n in names:
        k = con.index(n)
        for mat in ("chem", "gap"):
            mine, n2 = S.direct_readout(g, k, mat), S.direct_readout(con, k, mat)
            if mine["count"] > n2["count"] or mine["weight"] > n2["weight"] + 1e-6:
                return False
    return True


def test_the_existing_ensembles_are_unchanged(con):
    """03a's pilot graph (SH-mirror, seed 3 403 000, 20 passes) by its committed hash (pilot-dev/setup.json)."""
    g, _ = S.build(con, "SH-mirror", 3_403_000, passes=20)
    assert sha(g) == "dcf0cb24aba7682105f58ee3c7de646eeeaec7b84413d680adf0eccd1042937d"
    assert "SH-mirror-ASK" not in S.KINDS and set(S.ASK_KINDS) == {"SH-mirror-ASK", "SH-route-ASK"}


@pytest.mark.parametrize("kind", ["SH-mirror-ASK", "SH-route-ASK"])
def test_the_ask_ensembles_cap_ask_and_the_food_neurons(con, kind):
    g, info = S.build(con, kind, 3_500_001, passes=4)
    assert caps_hold(con, g, ["ASKL", "ASKR"] + S.constrained_neurons(con))
    assert np.array_equal((g.chem > 0).sum(0), (con.chem > 0).sum(0))  # degrees kept
    assert np.array_equal((g.chem > 0).sum(1), (con.chem > 0).sum(1))
    assert np.array_equal((g.gap > 0).sum(1), (con.gap > 0).sum(1))
    assert g.label == f"{kind}-3500001"


def test_without_the_ask_cap_ask_reaches_the_readout(con):
    """Sabotage for the test above: the plain ensemble lets ASK's direct read-out edges through, so the cap is not
    vacuous (N2's ASK has none)."""
    seen = []
    for seed in range(3_500_010, 3_500_014):
        g, _ = S.build(con, "SH-mirror", seed, passes=4)
        seen.append(caps_hold(con, g, ["ASKL", "ASKR"]))
    assert not all(seen)
