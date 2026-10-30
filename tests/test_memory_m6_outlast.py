"""M6, step 1 (docs/memory/M6-OUTLAST-PLAN.md): the changed inputs, the phases' wiring (B from A's end inside the
changed input, C from B's end outside it, the oscillation rerun from the same start), the rebuild against the
census's stored roots, the genome list, the root match, the outcomes and the reader's wordings and guards."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m6"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m1"))

import common as c  # noqa: E402
import pilot as P  # noqa: E402
from wormwars.brain import Brain  # noqa: E402

CENSUS_NPZ = ROOT / "runs" / "memory-m2-census" / "N2__7600.npz"


@pytest.fixture(scope="module")
def O(tmp_path_factory):
    os.environ["MEMORY_M6_OUTLAST_OUT"] = str(tmp_path_factory.mktemp("outlast"))
    import outlast
    yield outlast
    os.environ.pop("MEMORY_M6_OUTLAST_OUT", None)


@pytest.fixture
def R(tmp_path, monkeypatch):
    import outlast_read
    monkeypatch.setattr(outlast_read, "OUT", tmp_path)
    return outlast_read


@pytest.fixture(scope="module")
def panel():
    return c.S.genomes(c.S.CON, 3, 4343)


def test_the_changed_inputs(O, panel):
    g, cfg = panel
    n, s = g.spec.n, g.n_strains
    base = c.S._current(c.S.IFACE, cfg, c.S.BANK, n, s, "cpu")
    f0 = c.S._current(c.S.IFACE, cfg, O.bank_for("F0"), n, s, "cpu")
    z = c.S._current(c.S.IFACE, cfg, O.bank_for("Z"), n, s, "cpu")
    food = c.FOOD_SENSORS
    other = [j for j in range(n) if j not in food]
    assert base[..., food].abs().sum() > 0 and f0[..., food].abs().sum() == 0
    assert torch.equal(f0[..., other], base[..., other]) and base[..., other].abs().sum() > 0
    assert z.abs().sum() == 0


def test_phase_b_continues_from_phase_as_end_states_under_the_changed_input(O, panel):
    g, cfg = panel
    run = P.probe_states(g, cfg, ticks=20, record=False)
    start = run["end"].float()
    with c.probe_input(c.S.IFACE, O.bank_for("F0")):
        out = P.follow_from(g, cfg, start, ticks=1, record=False)
        cur = c.at(cfg, g.spec.n, g.n_strains, [0.0, 0.0])
    assert torch.allclose(out["end"].float(), Brain(g).step(start, cur), atol=0, rtol=0)


def test_phase_from_wires_the_context_the_start_and_the_initial_states(O, monkeypatch):
    """With fakes: B runs from A's end inside the changed input, C from B's end under 03mc's bank, and the classifier's
    oscillation rerun gets the same start (Astra)."""
    calls = []

    def fake_follow(g, cfg, start, **k):
        calls.append(("follow", start.clone(), c.final_food(), c._INPUT["bank"]["collision_front"]))
        return {"end": start.double() + 1.0, "cur": torch.zeros(1), "y": None, "tail": None}

    def fake_classify(g, cfg, run, compact=True, initial=None, **k):
        calls.append(("classify", initial.clone()))
        return [], torch.zeros(1)

    monkeypatch.setattr(O.P, "follow_from", fake_follow)
    monkeypatch.setattr(O.P, "full_classify", fake_classify)
    a_end = torch.zeros(2, 2, 3, dtype=torch.float64)
    (run_b, _, _), _ = O.arm_phases(None, None, a_end, "Z")
    (_, sb, food_b, coll_b), (_, ib), (_, sc, food_c, coll_c), (_, ic) = calls
    assert torch.equal(sb, a_end.float()) and torch.equal(ib, a_end.float())
    assert food_b == 0 and coll_b == 0
    assert torch.equal(sc, run_b["end"].float()) and torch.equal(ic, run_b["end"].float())
    assert food_c == c.final_food() > 0 and coll_c == c.S.BANK["collision_front"] > 0


@pytest.mark.skipif(not CENSUS_NPZ.exists(), reason="the census's state arrays are local, not in git")
def test_the_rebuild_reproduces_the_census_roots(O):
    rows = [r for r in O.genome_list() if r["seed"] == 7600][:2]
    ids = [r["genome"] for r in rows]
    g, cfg = O.build(7600, ids)
    _, recs, roots = O.phase_a(g, cfg)
    assert [x["class"] for x in recs] == [r["census_class"] for r in rows]
    assert float((roots - O.census_roots(7600, ids)).abs().max()) < 1e-6


def test_the_genome_list_is_the_census_switches(O):
    rows = O.genome_list()
    assert len(rows) == O.EXPECT == 169
    for _, seed, path in O.PANELS:
        rec = json.loads(path.read_text(encoding="utf-8"))
        want = [g["genome"] for g in rec["genomes"] if g["class"].startswith("separate states")]
        assert [r["genome"] for r in rows if r["seed"] == seed] == want
    assert sum(r["seen_before_plan"] for r in rows) == 4
    assert all(r["seed"] == 7700 for r in rows if r["seen_before_plan"])
    assert O.N_PANEL == 1024 and O.TOL == 1e-6


def test_the_root_match(O):
    a = torch.zeros(6, 2, 3, dtype=torch.float64)
    a[:, 1] = 1.0
    cc = a.clone()
    cc[1] = a[1].flip(0)                      # swapped
    cc[2, 1] = a[2, 0]                         # both at the rising-start root
    cc[3, 0] = a[3, 1]                         # both at the falling-start root
    cc[4] = 0.5                                # new
    cc[0, 0, 0] += 5e-7                        # within the distinctness level
    a[5, 1] = 1e-6                             # A's roots closer than twice the tolerance
    cc[5] = a[5]
    assert O.match(a, cc) == ["same", "swapped", "both at 0", "both at 1", "new", "ambiguous"]


def test_the_outcome_and_held(O):
    s = "separate states"
    assert O.outcome(s, "same") == "recovered"
    assert O.outcome("separate states, read-out silent", "same") == "recovered"
    assert O.outcome(s, "swapped") == "other"
    assert O.outcome("fading", "both at 0") == "merged"
    assert O.outcome("unresolved", "same") == "unresolved"
    assert O.outcome("persistent oscillation", "new") == "other"
    assert [O.held(x) for x in (s, "separate states, read-out silent", "fading", "unresolved")] == \
        ["held", "held", "not held", "unresolved"]


def _write(path, outcomes, held=None, stopped=False, complete=True, drop=0, inconsistent=0):
    rows, man = [], []
    for i, o in enumerate(outcomes):
        h = (held or ["not held"] * len(outcomes))[i]
        man.append({"seed": 7801, "genome": i, "census_class": "separate states"})
        rows.append({"seed": 7801, "genome": i, "census_class": "separate states", "seen_before_plan": False,
                     "A": {"class": "fading" if i < inconsistent else "separate states"}, "census_root_diff": None,
                     **{arm: {"outcome": o, "held": h, "match": "same", "B": {"class": "x"}, "C": {"class": "y"},
                              "separation_B": {k: 1.0 for k in ("0", "10", "30", "100", "300", "2000")}}
                        for arm in ("F0", "Z")}})
    (path / "genomes.json").write_text(json.dumps({"genomes": man}))
    (path / "run.json").write_text(json.dumps({"rows": rows[:len(rows) - drop], "inconsistent": inconsistent,
                                               "stopped": stopped, "complete": complete}))


def test_reader_count_wordings_name_the_gap(R, tmp_path):
    _write(tmp_path, ["merged"] * 30 + ["recovered"] * 10, held=["not held"] * 35 + ["unresolved"] * 5)
    res = R.read(tmp_path)
    assert res["F0"]["words"]["recovered"] == \
        "10 of 40 switches returned to their original states after a 2000-tick removal of the food input"
    assert res["Z"]["words"]["held"] == \
        "0 of 40 switches held two states during a 2000-tick removal of all sensory input (5 unresolved)"
    assert res["F0"]["held"]["share_bounds"] == [0.0, 0.125]


def test_reader_guards(R, tmp_path):
    assert R.read(tmp_path)["inconclusive"] == "the run is incomplete"
    _write(tmp_path, ["merged"] * 10, stopped=True)
    assert R.read(tmp_path)["inconclusive"].startswith("the consistency check stopped the run")
    _write(tmp_path, ["merged"] * 10, drop=1)
    assert "differ from genomes.json" in R.read(tmp_path)["inconclusive"]
    _write(tmp_path, ["merged"] * 10, complete=False)
    assert "differ from genomes.json" in R.read(tmp_path)["inconclusive"]
    _write(tmp_path, ["merged"] * 40, inconsistent=3)
    assert R.read(tmp_path)["inconclusive"].startswith("the consistency check fails")
    _write(tmp_path, ["merged"] * 40, inconsistent=1)
    res = R.read(tmp_path)
    assert res["consistent"] == 39 and res["F0"]["recovered"]["n"] == 39 and len(res["excluded"]) == 1


def test_wilson_matches_a_known_value(R):
    lo, hi = R.wilson(20, 40)
    assert abs(lo - 0.3519) < 1e-3 and abs(hi - 0.6481) < 1e-3


def test_separation_reads_the_recorded_ticks(O):
    dense = np.zeros((1, 301, 2, 4), np.float32)
    for t in O.SEP_TICKS:
        dense[0, t, 0, 0] = t + 1.0
    end = torch.zeros(1, 2, 4, dtype=torch.float64)
    end[0, 1, 2] = 7.0
    assert O.separation({"dense": dense, "end": end}).tolist() == [[1.0, 11.0, 31.0, 101.0, 301.0, 7.0]]
