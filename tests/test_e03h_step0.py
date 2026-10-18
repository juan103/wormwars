"""03h's step 0 (scripts/e03h_step0.py; DESIGN.md §7.2) at smoke size on the CPU: its verification and per-graph
records are written in the registered shape. (The CPU genomes are not 03's CUDA genomes, so smoke numbers mean
nothing; the formal step 0 runs on CUDA and drops itself if the replay is not bit-equal.)"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_step0_smoke_writes_the_registered_shape():
    spec = importlib.util.spec_from_file_location("e03h_step0_test", ROOT / "scripts" / "e03h_step0.py")
    M = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(M)
    out = M.run(smoke=True)
    v = out["verification"]
    assert v["graph"] == "pilotSH101" and set(v) >= {"unequal_values", "max_difference", "bit_equal"}
    assert len(out["graphs"]) == 2 and out["exploratory"] is True
    for r in out["graphs"].values():
        assert -1 <= r["rho_level"] <= 1 and isinstance(r["degenerate"], bool)
    assert out["summary"]["graphs"] == 2
