"""M1's scripts (scripts/memory_m1, docs/memory/M1-PLAN.md): the decision rules' boundaries, part A's guarded paths,
and the non-finite stop in the shared probe loops (a sabotage check: a NaN planted in one arm's row must stop the run)."""
import os
import sys
import tempfile
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MEMORY_M1_OUT", tempfile.mkdtemp(prefix="memory-m1-test-"))  # nothing is written into runs/
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
