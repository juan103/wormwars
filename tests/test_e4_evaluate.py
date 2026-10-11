"""E4's evaluation harness (docs/E4/E4-DESIGN.md v3 §2-§4): the named link subsets, each champion's condition
genomes, batched play under a trail condition, and the cut path's sabotage check (a hand-built champion with a known
cross-link effect shows it)."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.connectome import load_connectome
from wormwars.e3 import maze_world as MW
from wormwars.e4 import arms as AR
from wormwars.e4 import evaluate as EVL
from wormwars.e4s import arms as A

IDS = np.array([42_000, 42_001])


@pytest.fixture(scope="module")
def setup():
    cfg = MW.maze_config(c=6, horizon=1800, colony=8, mu=0.01, lam=0.02, delta=0.05, d0=1.142, access="shared",
                         family="islands", k_r=0)
    return cfg, AR.context(load_connectome(), A.load_l1(), cfg.brain)


def _pre_post(cx, k):
    spec, ext = cx["spec"], cx["org"].ext
    return ext.names[int(spec.chem_i[k])], ext.names[int(spec.chem_j[k])]


def test_the_link_subsets(setup):
    _, cx = setup
    s = EVL.link_sets(cx)
    allk = set(AR.slot_indices(cx).tolist())
    assert set(s["all"].tolist()) == allk and len(s["all"]) == 32
    assert len(s["into_A"]) == len(s["into_B"]) == len(s["sensory"]) == len(s["comparator"]) == 16
    assert set(s["into_A"].tolist()) | set(s["into_B"].tolist()) == allk
    assert set(s["sensory"].tolist()) | set(s["comparator"].tolist()) == allk
    for k in s["into_A"].tolist():
        pre, post = _pre_post(cx, k)
        assert pre.startswith("E3_B_") and post.startswith("E3_A_")
    for k in s["sensory"].tolist():
        assert _pre_post(cx, k)[0].endswith(("_NL", "_NR"))
    sources = [n for n in s if n.startswith("from_")]
    assert len(sources) == 8 and all(len(s[n]) == 4 for n in sources)


def test_the_conditions_apply_their_edits(setup):
    _, cx = setup
    g = cx["org"].genome.select([0])
    slots = AR.slot_indices(cx)
    w = g.w.clone()
    w[:, slots] = 1.5
    g = g.with_params(w=w)
    means = torch.full((cx["org"].ext.n,), 0.2)
    conds = EVL.conditions(g, cx, means=means, names=("intact", "cut_all", "meansub_all", "cut_into_A"))
    assert list(conds) == ["intact", "cut_all", "meansub_all", "cut_into_A"]
    assert torch.equal(conds["intact"].w, g.w)
    assert torch.all(conds["cut_all"].w[:, slots] == 0)
    into_a = EVL.link_sets(cx)["into_A"]
    assert torch.all(conds["cut_into_A"].w[:, into_a] == 0)
    assert torch.all(conds["cut_into_A"].w[:, EVL.link_sets(cx)["into_B"]] == 1.5)
    assert not torch.equal(conds["meansub_all"].bias, g.bias)


def test_meansub_needs_means(setup):
    _, cx = setup
    with pytest.raises(ValueError):
        EVL.conditions(cx["org"].genome.select([0]), cx, names=("meansub_all",))


def test_play_returns_per_maze_visits_per_genome(setup):
    cfg, cx = setup
    g = cx["org"].genome.select([0])
    out = EVL.play(cfg, cx["org"], {"a": g, "b": g}, IDS, 1_192_000, "cpu", access="shared", ticks=200)
    assert set(out) == {"a", "b"}
    assert out["a"]["visits"].shape == (len(IDS),) and np.array_equal(out["a"]["visits"], out["b"]["visits"])
    assert out["a"]["legs"].shape == (len(IDS),)


def test_a_known_cross_link_effect_is_seen(setup):
    """Rule 9's sabotage of the cut path: strong links from B's noses into A's comparators disturb A's steering
    in mode A; cutting them must change the visits."""
    cfg, cx = setup
    g = cx["org"].genome.select([0])
    w = g.w.clone()
    s = EVL.link_sets(cx)
    w[:, s["into_A"]] = torch.where(torch.arange(len(s["into_A"])) % 2 == 0, 3.0, -3.0)
    g = g.with_params(w=w)
    conds = EVL.conditions(g, cx, names=("intact", "cut_all"))
    out = EVL.play(cfg, cx["org"], conds, IDS, 1_192_000, "cpu", access="shared", ticks=600)
    assert not np.array_equal(out["intact"]["visits"], out["cut_all"]["visits"])


def test_q_flips_counts_sign_changes_per_wey():
    f = EVL.QFlips(q=1)
    f(torch.tensor([[[0.0, 0.5], [0.0, -0.5]]]))  # [S=1, B=2, N=2]; the start is q = 0, mode A (q >= 0)
    f(torch.tensor([[[0.0, -0.1], [0.0, -0.4]]]))
    f(torch.tensor([[[0.0, 0.2], [0.0, 0.3]]]))
    assert f.flips.tolist() == [[2, 2]]  # wey 0: A, A, B, A; wey 1: A, B, B, A


def test_play_reports_latch_switches(setup):
    cfg, cx = setup
    g = cx["org"].genome.select([0])
    out = EVL.play(cfg, cx["org"], {"a": g}, IDS, 1_192_000, "cpu", access="shared", ticks=600, q_flips=True)
    sw = out["a"]["switches"]
    assert sw["flips"].shape == (len(IDS), 8) and sw["visits"].shape == (len(IDS), 8)
    assert 0.0 <= sw["match_share"] <= 1.0


def _strong_b(cx):
    org = cx["org"]
    g = org.genome.select([0])
    w = g.w.clone()
    spec = g.spec
    for pre, post in AR.O.motor_edges(org.module, "B"):
        k = int(((spec.chem_i == org.ext.index(pre)) & (spec.chem_j == org.ext.index(post))).nonzero()[0, 0])
        w[0, k] = 3.0
    return g.with_params(w=w)


def test_play_is_gated(setup):
    """Sabotage of the evaluation wrapper: `play` equals a hand-gated play and differs from an ungated one."""
    import dataclasses as dc
    from wormwars.brain import Brain
    from wormwars.e3 import maze_runs as MR
    cfg, cx = setup
    org = cx["org"]
    g = _strong_b(cx)
    got = EVL.play(cfg, org, {"g": g}, IDS, 1_192_000, "cpu", access="shared", ticks=600)["g"]["visits"]
    gated = MR.play_batch(cfg, org.iface, Brain(g).gate_outputs(org.gate), np.arange(1), IDS, 1_192_000, "cpu",
                          ticks=600)["visits"][0].mean(-1)
    plain = MR.play_batch(cfg, org.iface, Brain(g), np.arange(1), IDS, 1_192_000, "cpu", ticks=600)["visits"][0].mean(-1)
    assert np.array_equal(got, gated) and not np.array_equal(got, plain)
    ungated_org = dc.replace(org, gate=None)
    with pytest.raises((TypeError, KeyError, ValueError)):
        EVL.play(cfg, ungated_org, {"g": g}, IDS, 1_192_000, "cpu", ticks=10)


def test_the_x0_sham_is_exact_in_one_batch(setup):
    """Fable: X0's intact and cut_all, played in one batch, are bitwise equal."""
    cfg, cx = setup
    g = cx["org"].genome.select([0])
    conds = EVL.conditions(g, cx, names=("intact", "cut_all"))
    out = EVL.play(cfg, cx["org"], conds, IDS, 1_192_000, "cpu", access="shared", ticks=300, q_flips=True)
    assert np.array_equal(out["intact"]["visits"], out["cut_all"]["visits"])
    assert np.array_equal(out["intact"]["switches"]["flips"], out["cut_all"]["switches"]["flips"])


def test_q_flips_count_crossings_within_a_tick():
    """The gate acts per substep, so a crossing and a recrossing inside one tick are two mode changes."""
    f = EVL.QFlips(q=0, substeps=4)
    for q in (0.1, -0.2, 0.3, 0.4):  # one tick of four substeps: A, B, A, A
        f(torch.tensor([[[q]]]))
    assert f.flips.tolist() == [[2]] and f.ticks_of_flips() == [[[0, 0]]]


def test_switch_latency(setup):
    """Each visit's latch switch, matched in order: E-G's switch within a few ticks of its visits."""
    cfg, cx = setup
    out = EVL.play(cfg, cx["org"], {"eg": cx["org"].genome.select([0])}, IDS, 1_192_000, "cpu", ticks=900, q_flips=True)
    sw = out["eg"]["switches"]
    assert sw["aligned_share"] == 1.0 and 0 <= sw["latency_max"] <= EVL.SWITCH_TOLERANCE
