"""The evolutionary E4-D's trial rollout for `evolve_batch` (design v2.1 §3): per strain and maze, the real-first share
over the maze's two assignments; zero progress; the integrity check on link-free strains; qualifying ids."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import Genome
from wormwars.connectome import load_connectome
from wormwars.e4 import arms as AR
from wormwars.e4 import evo_trial as ET
from wormwars.e4 import trial as TL
from wormwars.e4.train import gated_brain
from wormwars.e4s import arms as A

SEED = 1_420_000
IDS = np.array([52_000, 52_001, 52_002])


@pytest.fixture(scope="module")
def setup():
    cfg = TL.trial_config(sigma=6.0, horizon=300)
    cx = AR.context(load_connectome(), A.load_l1(), cfg.brain)
    return cfg, cx


def test_scores_progress_and_shapes(setup):
    cfg, cx = setup
    org = cx["org"]
    eg = org.genome.select([0])
    ctl = TL.control_genome(eg, cx, "comparator", 3.0)
    fn = ET.trial_rollout(cx)
    res = fn(cfg, org.iface, Genome.cat([eg, ctl, eg]), IDS, SEED, "cpu")
    assert res.score.shape == (3, len(IDS)) and np.all(res.progress == 0)
    assert set(np.unique(res.score[0])) <= {0.0, 0.5}  # a link-free strain enters the same candidate under both
    assert np.array_equal(res.score[0], res.score[2])  # one genome, one score, wherever it sits in the batch


def test_a_strain_alone_matches_the_trial_world(setup):
    cfg, cx = setup
    org = cx["org"]
    ctl = TL.control_genome(org.genome.select([0]), cx, "comparator", 3.0)
    res = ET.trial_rollout(cx)(cfg, org.iface, ctl, IDS, SEED, "cpu")
    w = TL.TrialWorld(cfg, org.iface, gated_brain(ctl, org.gate), torch.zeros(2 * len(IDS), 1, dtype=torch.long),
                      run_seed=SEED, world_ids=np.repeat(ET.qualifying(IDS, SEED), 2), assign=np.tile([0, 1], len(IDS)),
                      q_index=org.gate["q"])
    w.run(cfg.world.max_ticks)
    rf = w.trial_events()["real_first"][:, 0].reshape(len(IDS), 2).mean(axis=1)
    assert np.array_equal(res.score[0], rf)


def test_per_strain_ids(setup):
    cfg, cx = setup
    org = cx["org"]
    eg = org.genome.select([0])
    res = ET.trial_rollout(cx)(cfg, org.iface, Genome.cat([eg, eg]), np.stack([IDS, IDS[::-1]]), SEED, "cpu")
    assert np.array_equal(res.score[0], res.score[1][::-1])


def test_the_integrity_check_can_fail(setup):
    """A link-free strain whose B smells the real candidate (the oracle's mapping) breaks the check."""
    cfg, cx = setup
    org = cx["org"]
    with pytest.raises(RuntimeError):
        ET.trial_rollout(cx, b_source="real")(cfg, org.iface, org.genome.select([0]), IDS, SEED, "cpu")


def test_qualifying_ids_are_deterministic_and_qualify():
    q = ET.qualifying(np.arange(52_000, 52_040), SEED)
    assert np.array_equal(q, ET.qualifying(np.arange(52_000, 52_040), SEED))
    assert all(ET.qualifies(int(i), SEED) for i in q) and np.all(q >= np.arange(52_000, 52_040))


def test_the_champion_rule_and_its_ties():
    """The best validation share; ties to the higher final fitness, then the smaller link norm, then the lowest index."""
    val = np.array([0.6, 0.7, 0.7, 0.7, 0.5])
    fit = np.array([0.9, 0.5, 0.6, 0.6, 0.9])
    norm = np.array([0.0, 1.0, 2.0, 1.5, 0.0])
    assert ET.champion(val, fit, norm) == 3  # 1, 2, 3 tie on validation; 2 and 3 on fitness; 3 has the smaller norm
    assert ET.champion(np.array([0.5, 0.5]), np.array([0.5, 0.5]), np.array([1.0, 1.0])) == 0


def test_the_oracle_skips_the_check(setup):
    cfg, cx = setup
    org = cx["org"]
    res = ET.trial_rollout(cx, b_source="real", check=False)(cfg, org.iface, org.genome.select([0]), IDS, SEED, "cpu")
    assert res.score.shape == (1, len(IDS))


def test_the_capture_keeps_entry_counts(setup):
    from wormwars.e4 import lineage as LI
    cfg, cx = setup
    org = cx["org"]
    cap = LI.Capture(ET.trial_rollout(cx))
    cap(cfg, org.iface, Genome.cat([org.genome.select([0])] * 2), np.stack([IDS, IDS]), SEED, "cpu")
    s = cap.selections[0]
    assert s["neither"].shape == (2,) and s["real_first"].shape == (2,)


def test_qualifying_ids_stay_distinct_within_a_row(monkeypatch):
    """Astra: a rejected id must not map onto a neighbour already in the row."""
    monkeypatch.setattr(ET, "qualifies", lambda mid, seed, c=6: mid % 3 != 1)  # every id ≡ 1 (mod 3) is rejected
    row = np.array([10, 11, 12, 13])  # 11 → 12 would collide with 12
    q = ET.qualifying(row, SEED)
    assert len(set(q.tolist())) == 4 and all(m % 3 != 1 for m in q)
    q2 = ET.qualifying(np.stack([row, row]), SEED)
    assert np.array_equal(q2[0], q2[1]) and len(set(q2[0].tolist())) == 4


def test_the_integrity_check_is_per_maze(setup):
    """Equal totals can hide per-maze differences; the check compares every maze pair (Fable)."""
    rf = np.array([[[1, 0], [0, 1]]])  # one strain, two mazes: real-first on (assign 0, maze 0) and (assign 1, maze 1)
    df = np.array([[[0, 1], [1, 0]]])
    assert ET.distinguishes(rf, df).tolist() == [False]
    assert ET.distinguishes(np.array([[[1, 0], [0, 0]]]), np.array([[[0, 0], [1, 0]]])).tolist() == [True]


def test_the_per_maze_counts_are_additive_and_agree(setup):
    """The formal stages' per-maze, per-assignment counts (pre-registration §0.3, authorized in advance; D273): the
    existing fields are unchanged and the new arrays sum to them."""
    cfg, cx = setup
    org = cx["org"]
    eg = org.genome.select([0])
    ctl = TL.control_genome(eg, cx, "comparator", 3.0)
    res = ET.trial_rollout(cx)(cfg, org.iface, Genome.cat([eg, ctl]), IDS, SEED, "cpu")
    S, W = 2, len(IDS)
    for k in ("real_first_maze", "decoy_first_maze", "neither_maze"):
        assert getattr(res, k).shape == (S, W, 2)
    assert np.array_equal(res.real_first_maze.sum(axis=(1, 2)), res.real_first)
    assert np.array_equal(res.decoy_first_maze.sum(axis=(1, 2)), res.decoy_first)
    assert np.array_equal(res.neither_maze.sum(axis=(1, 2)), res.neither)
    assert np.array_equal(res.real_first_maze.mean(axis=2), res.score)
    assert np.all(res.real_first_maze + res.decoy_first_maze + res.neither_maze == 1)
