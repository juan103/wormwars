"""M1's scripts (scripts/memory_m1, docs/memory/M1-PLAN.md): the decision rules' boundaries, part A's guarded paths,
and the non-finite stop in the shared probe loops (a sabotage check: a NaN planted in one arm's row must stop the run)."""
import os
import sys
import tempfile
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
os.environ["MEMORY_M1_OUT"] = tempfile.mkdtemp(prefix="memory-m1-test-")  # always a scratch folder: nothing is written into runs/
sys.path.insert(0, str(ROOT / "scripts" / "memory_m1"))


def test_the_decision_rules_and_the_guarded_summary_paths():
    import summarise
    summarise.test_rules()


def test_part_a_guards_a_zero_baseline_and_missing_support():
    import accounting
    accounting.test_standardise()


def test_a_zero_state_difference_leaves_the_kills_unavailable():
    """A zero difference must not become a substantive reading (Astra, rounds 5 and 6): through the gap and antisymmetry
    ratios and their aggregates to the readings, and the grower diagnostic's zero numerator."""
    import numpy as np
    import common as c
    import panels
    import summarise
    from wormwars.brain import Brain
    torch.set_grad_enabled(False)
    g, _ = c.S.genomes(c.S.CON, 3, 1)
    brain = Brain(g)
    dv = torch.zeros(3, c.S.CON.n, dtype=torch.float64)
    geo, dyn = panels.gap_ratios(brain, dv)
    share, anti, paired = panels.antisym(dv)
    assert np.isnan(geo).all() and np.isnan(dyn).all() and np.isnan(share).all()
    w = np.full(3, 1 / 3)
    assert panels.wmean(geo, w) is None and panels.nmedian(dyn) is None
    assert summarise.gap_reading(panels.wmean(geo, w), 0.1, panels.wmean(dyn, w), 0.1) == "unavailable"
    assert summarise.antisym_reading(panels.wmean(share, w), 0.3, 0.4) == "unavailable"
    a = np.full(20, 0.05)
    steady = np.full(20, 0.05)
    assert c.diagnostic_available(a, steady, np.full(20, 0.01))
    assert not c.diagnostic_available(a, steady, np.zeros(20))  # zero follow-up differences
    assert not c.diagnostic_available(np.full(20, 2e-5), steady, np.full(20, 0.01))  # below the start floors


@pytest.mark.slow
def test_the_summary_runs_with_a_reference_panel_below_b3s_minimum(monkeypatch):
    """Astra, rounds 7 and 8: a valid reference panel with fewer than 10 genomes eligible at every k (written by
    panels.py without its B3 fields) must leave B3 to the other panels, not crash the summary. Real panels on N2's wiring
    stand in for the null graphs, whose files are local; parts A, the tau control and the growers are stubbed."""
    import json
    import common as c
    import panels
    import summarise
    monkeypatch.setattr(c.S, "graph", lambda name: c.S.CON)
    refs = ["SH-2010000", "SH-route-2020000", "SH-class-2030000"]
    json.dump({"random": refs, "selected": {}}, open(c.OUT / "panel.json", "w"))
    for name, seed in [("N2", c.SEED), ("N2", c.SEED2)] + [(r, c.SEED) for r in refs]:
        assert panels.run(name, seed, 48)["valid"]
    f = panels.DIR / f"{refs[2]}__{c.SEED}.json"  # rewrite one reference as panels.py writes a panel below B3's minimum
    r = json.load(open(f))
    r["B3_ok"] = False
    r.pop("B3_median_r2_over_r05", None)
    r.pop("B3_r2_over_r05_undefined", None)
    for arm in r["arms"].values():
        for k in [k for k in arm if k.startswith("B3_")]:
            arm.pop(k)
    json.dump(r, open(f, "w"))
    check = {"supported": False, "f": None}
    graphs = {g: {"eligible_share30": 0.3, "eligible_share300": 0.05, "cohort_C30": 0.0, "cohort_C300": 0.0} for g in refs}
    json.dump({"A2": {e: {"N2_check": check} for e in c.ENSEMBLES}, "graphs": graphs,
               "N2": {"eligible_share30": 0.4, "eligible_share300": 0.08, "cohort_C30": 0.01, "cohort_C300": 0.005}},
              open(c.OUT / "accounting.json", "w"))
    json.dump({"summary": {"reading_available": False}}, open(c.OUT / "tau.json", "w"))
    json.dump({"N2": {"available": False}}, open(c.OUT / "growers.json", "w"))
    summarise.main()
    s = json.load(open(c.OUT / "summary.json"))
    assert s["reference_graphs"] == 3
    assert f"{refs[2]}__{c.SEED}" not in s["B3_median_r2_over_r05"]["undefined_genomes"]
    assert f"{refs[2]}__{c.SEED}" not in s["D1_B3_a"].get("per_graph", {})
    assert isinstance(s["D1_reading"], str) and isinstance(s["D2"]["reading"], str)


def test_a_non_finite_arm_stops_the_probe():
    import common as c
    torch.set_grad_enabled(False)
    g, cfg = c.S.genomes(c.S.CON, 4, 1)
    brain, v, food = c.ramp(g, cfg)
    rows = torch.cat([v, c.scaled(v, 2.0)], 1)
    rows[1, 3, 5] = float("nan")  # one neuron of one row of the scaled arm, in one genome
    with pytest.raises(RuntimeError, match="non-finite"):
        c.follow(brain, cfg, rows, food, 3, record=(0, 3))
    c.follow(brain, cfg, torch.cat([v, c.scaled(v, 2.0)], 1), food, 3, record=(0, 3))  # the clean batch runs
