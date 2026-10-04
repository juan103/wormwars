"""E3b-2's attribution pieces (docs/E3/E3b-2-PLAN.md draft 2, §4, §5, §8): the parameter partitions, the hybrids,
the Shapley and dividend calculator, the lesions and clamps, and the latch recorder."""

from __future__ import annotations

import itertools
import math

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.connectome import load_connectome
from wormwars.e3 import attribution as AT
from wormwars.e3 import latch as L
from wormwars.e3 import maze_organisms as MO
from wormwars.e3 import organism as O
from wormwars.e3 import tuning as T
from wormwars.e3.task import shuttle_config
from wormwars.e4s import arms as A


@pytest.fixture(scope="module")
def seed():
    return T.start_organism("seed", load_connectome(), A.load_l1(), shuttle_config().brain)


@pytest.fixture(scope="module")
def mutant(seed):
    """A stand-in champion: the seed with every mutable parameter perturbed (the real champions stay local)."""
    cfg = shuttle_config()
    sc = {k: v * 8 for k, v in T.scales(seed.ext).items()}
    return Genome.cat([seed.genome]).mutate(cfg.mutation, generator=torch.Generator().manual_seed(11), scales=sc)


# ------------------------------------------------------------------ §4: the partitions

def _mutable(ext):
    sc = T.scales(ext)
    return {k: (sc[k] > 0) for k in ("w", "tau", "bias")}


@pytest.mark.parametrize("partition, sizes", [("functional", {"sensing": 20, "gating": 8, "output": 32, "latch": 5}),
                                              ("side", {"module_a": 28, "module_b": 28, "selector": 9})])
def test_each_partition_covers_every_mutable_scalar_exactly_once(seed, partition, sizes):
    groups = AT.parameter_groups(seed.ext, partition)
    mut = _mutable(seed.ext)
    assert list(groups) == list(sizes)
    for k in ("w", "tau", "bias"):
        total = sum(g[k].int() for g in groups.values())
        assert torch.equal(total > 0, mut[k]) and int(total.max()) <= 1, k
    assert {name: sum(int(g[k].sum()) for k in ("w", "tau", "bias")) for name, g in groups.items()} == sizes


def test_the_groups_hold_what_the_plan_says(seed):
    ext = seed.ext
    g = AT.parameter_groups(ext, "functional")
    spec = BrainSpec.from_connectome(ext)
    names = lambda mask: {(ext.names[i], ext.names[j]) for p, (i, j) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist())) if mask[p]}  # noqa: E731
    assert names(g["latch"]["w"]) == {(O.Q, O.Q), ("E3_RA", O.Q), ("E3_RB", O.Q)}
    assert names(g["gating"]["w"]) == {(O.Q, c) for c in O.COMPARATORS}
    assert {ext.names[k] for k in range(spec.n) if g["gating"]["bias"][k]} == set(O.COMPARATORS)
    assert {ext.names[k] for k in range(spec.n) if g["latch"]["tau"][k]} == {O.Q}


# ------------------------------------------------------------------ §5A: the hybrids

def test_the_endpoint_hybrids_are_bitwise_the_seed_and_the_champion(seed, mutant):
    groups = AT.parameter_groups(seed.ext, "functional")
    none = AT.hybrid(seed.genome, mutant, groups, set())
    every = AT.hybrid(seed.genome, mutant, groups, set(groups))
    for a, b in ((none, seed.genome), (every, mutant)):
        assert all(torch.equal(x, y) for x, y in zip(a.params().values(), b.params().values()) if x is not None)


def test_a_hybrid_takes_exactly_its_groups_from_the_champion(seed, mutant):
    groups = AT.parameter_groups(seed.ext, "functional")
    h = AT.hybrid(seed.genome, mutant, groups, {"output"})
    out = groups["output"]["w"]
    assert torch.equal(h.w[0, out], mutant.w[0, out]) and torch.equal(h.w[0, ~out], seed.genome.w[0, ~out])
    assert torch.equal(h.tau, seed.genome.tau) and torch.equal(h.bias, seed.genome.bias)


# ------------------------------------------------------------------ the Shapley and dividend calculator

PLAYERS = ("p", "q", "r", "s")


def _table(fn):
    return {frozenset(S): fn(set(S)) for k in range(len(PLAYERS) + 1) for S in itertools.combinations(PLAYERS, k)}


def test_shapley_on_an_additive_game():
    a = {"p": 1.0, "q": -2.0, "r": 0.5, "s": 3.0}
    t = _table(lambda S: sum(a[i] for i in S))
    assert AT.shapley(t, PLAYERS) == pytest.approx(a)
    d = AT.dividends(t, PLAYERS)
    assert all(d[frozenset([i])] == pytest.approx(a[i]) for i in PLAYERS)
    assert all(abs(v) < 1e-12 for S, v in d.items() if len(S) != 1)


def test_shapley_gives_a_dummy_zero_and_splits_a_pure_pair_interaction():
    t = _table(lambda S: 6.0 if {"p", "q"} <= S else 0.0)
    phi = AT.shapley(t, PLAYERS)
    assert phi == pytest.approx({"p": 3.0, "q": 3.0, "r": 0.0, "s": 0.0})
    d = AT.dividends(t, PLAYERS)
    assert d[frozenset({"p", "q"})] == pytest.approx(6.0) and sum(abs(v) for v in d.values()) == pytest.approx(6.0)


def test_shapley_splits_a_higher_order_interaction_and_the_table_is_rebuilt():
    t = _table(lambda S: (9.0 if {"p", "q", "r"} <= S else 0.0) + (2.0 if "s" in S else 0.0) - (1.0 if {"p", "s"} <= S else 0.0))
    phi = AT.shapley(t, PLAYERS)
    assert phi == pytest.approx({"p": 3.0 - 0.5, "q": 3.0, "r": 3.0, "s": 2.0 - 0.5})
    assert sum(phi.values()) == pytest.approx(t[frozenset(PLAYERS)] - t[frozenset()])
    assert AT.rebuild(AT.dividends(t, PLAYERS), PLAYERS) == pytest.approx(t)


def test_reversion_and_transplant():
    t = _table(lambda S: (4.0 if "p" in S else 0.0) + (1.0 if {"p", "q"} <= S else 0.0))
    rev, tra = AT.reversion(t, PLAYERS), AT.transplant(t, PLAYERS)
    assert rev["p"] == pytest.approx(-5.0) and rev["q"] == pytest.approx(-1.0) and rev["r"] == pytest.approx(0.0)
    assert tra["p"] == pytest.approx(4.0) and tra["q"] == pytest.approx(0.0)


# ------------------------------------------------------------------ §5C: lesions and clamps

def test_the_latch_states_come_from_the_organisms_own_self_weight_and_bias(seed, mutant):
    for g in (seed.genome, mutant):
        low, mid, high = AT.latch_states(g, seed.ext)
        w = MO.named_edges(g, seed.ext)[(O.Q, O.Q)]
        b = float(g.bias[0, seed.ext.index(O.Q)])
        roots = [q for q, _ in L.roots(w, b)]
        assert (low, mid, high) == (roots[0], roots[1], roots[2])
    assert AT.latch_states(seed.genome, seed.ext)[1] == pytest.approx(0.0, abs=1e-9)


def test_each_lesion_changes_exactly_its_edges(seed, mutant):
    ext = seed.ext
    spec = BrainSpec.from_connectome(ext)
    for name, pick in AT.EDGE_LESIONS.items():
        g = AT.edge_lesion(mutant, ext, name)
        hit = torch.tensor([pick(ext.names[i], ext.names[j]) for i, j in zip(spec.chem_i.tolist(), spec.chem_j.tolist())])
        assert hit.any(), name
        assert torch.all(g.w[0, hit] == 0) and torch.equal(g.w[0, ~hit], mutant.w[0, ~hit]), name
        assert torch.equal(g.tau, mutant.tau) and torch.equal(g.bias, mutant.bias)
    assert int(sum(AT.EDGE_LESIONS["outputs_both"](ext.names[i], ext.names[j])
                   for i, j in zip(spec.chem_i.tolist(), spec.chem_j.tolist()))) == 32


def test_the_reflex_clamp_and_the_scent_interface(seed):
    ext = seed.ext
    assert AT.reflex_clamp(ext) == {ext.index("E3B_WL"): -0.5, ext.index("E3B_WR"): -0.5}
    iface = AT.without_scent(seed.iface)
    changed = [n for n, a, b in zip(iface.signal_names, iface.sensor_gain, seed.iface.sensor_gain) if a != b]
    assert sorted(set(changed)) == ["a_left", "a_right", "b_left", "b_right"]
    assert all(g == 0 for n, g in zip(iface.signal_names, iface.sensor_gain) if n in AT.SCENT)


def test_a_clamped_latch_holds_from_the_first_tick(seed, mutant):
    from wormwars.e3 import maze_world as MW
    from wormwars.e3.maze_world import maze_config
    cfg = maze_config(shuttle_config(), c=5, horizon=60, mu=0.01, lam=0.02, delta=0.05, d0=1.142)
    pop = Genome.cat([seed.genome, mutant])
    low, _, high = AT.latch_states(mutant, seed.ext)
    q = seed.ext.index(O.Q)
    brain = AT.HeldBrain(pop).clamp([{}, {q: high}])
    w = MW.MazeWorld(cfg, seed.iface, brain, torch.tensor([[0], [1]]), run_seed=1_180_000, world_ids=np.array([9800, 9801]))
    held = torch.tensor(high, dtype=w.v[0].dtype)  # states are float32
    assert torch.equal(w.v[0][1, 0, q], held)  # the initial state is already clamped
    w.run(60)
    v = w.assigns[0].from_brain(w.v[0], 2, w.n_weys)
    assert torch.all(v[1, :, q] == held) and not torch.all(v[0, :, q] == held)


# ------------------------------------------------------------------ §5D: the latch recorder

def test_the_switch_bookkeeping_on_a_scripted_case():
    """Hand-specified (D195). Coding A <-> high, mid 0, stable states ±1.6: undecided is |q| < 0.533 (middle
    third) or |q| < 0.8 (middle half). Each tick: q (computed before the move), the goal before and after the
    tick's switch, and whether the wey had visited before the tick."""
    ticks = [  # q, goal before, goal after, visited before
        (1.5, 0, 0, False),
        (1.4, 0, 1, False),   # visit A at tick 1: a leg to B opens (q on A's side: not pre-aligned)
        (0.3, 1, 1, True),    # not crossed (q > 0); undecided in both bands
        (-1.2, 1, 1, True),   # crossed toward B, latency 3 - 1 = 2
        (-1.5, 1, 0, True),   # visit B at tick 4: a leg to A opens (q on B's side)
        (-1.4, 0, 0, True),   # disagrees with A
        (0.7, 0, 0, True),    # crossed toward A, latency 6 - 4 = 2; decided in the third band, undecided in the half
        (1.5, 0, 1, True),    # visit A on the last tick: a leg to B opens and is censored
    ]
    rec = AT.SwitchTally(mid=0.0, low=-1.6, high=1.6, a_high=True)
    for q, gb, ga, vb in ticks:
        rec.tick(q=q, goal_before=gb, goal_after=ga, visited_before=vb)
    out = rec.result()
    assert out["switches"] == {"to_b": {"legs": 2, "pre_aligned": 0, "crossed": 1, "latency_sum": 2, "censored": 1},
                               "to_a": {"legs": 1, "pre_aligned": 0, "crossed": 1, "latency_sum": 2, "censored": 0}}
    # eligible ticks 2..7: B at 2, 3, 4; A at 5, 6, 7
    assert out["occupancy"] == {"A": 3, "B": 3}
    assert out["third"] == {"decided": {"A": 3, "B": 2}, "agree": {"A": 2, "B": 2}, "undecided": {"A": 0, "B": 1}}
    assert out["half"] == {"decided": {"A": 2, "B": 2}, "agree": {"A": 1, "B": 2}, "undecided": {"A": 1, "B": 1}}


def test_a_stuck_latch_is_pre_aligned_once_and_never_switches_back():
    rec = AT.SwitchTally(mid=0.0, low=-1.6, high=1.6, a_high=True)
    rec.tick(q=-1.5, goal_before=0, goal_after=0, visited_before=False)
    rec.tick(q=-1.5, goal_before=0, goal_after=1, visited_before=False)  # visit A: already on B's side
    for _ in range(20):
        rec.tick(q=-1.5, goal_before=1, goal_after=1, visited_before=True)
    rec.tick(q=-1.5, goal_before=1, goal_after=0, visited_before=True)  # visit B: a leg to A that never crosses
    for _ in range(10):
        rec.tick(q=-1.5, goal_before=0, goal_after=0, visited_before=True)
    out = rec.result()
    assert out["switches"]["to_b"] == {"legs": 1, "pre_aligned": 1, "crossed": 0, "latency_sum": 0, "censored": 0}
    assert out["switches"]["to_a"] == {"legs": 1, "pre_aligned": 0, "crossed": 0, "latency_sum": 0, "censored": 1}
    assert out["third"]["agree"]["B"] == out["third"]["decided"]["B"] == 21 and out["third"]["agree"]["A"] == 0


def test_a_leg_ended_by_the_next_visit_is_not_crossed_and_not_censored():
    rec = AT.SwitchTally(mid=0.0, low=-1.6, high=1.6, a_high=True)
    rec.tick(q=1.5, goal_before=0, goal_after=1, visited_before=False)  # a leg to B
    rec.tick(q=1.5, goal_before=1, goal_after=0, visited_before=True)   # the next visit, before any crossing
    rec.tick(q=1.5, goal_before=0, goal_after=0, visited_before=True)
    out = rec.result()["switches"]
    assert out["to_b"] == {"legs": 1, "pre_aligned": 0, "crossed": 0, "latency_sum": 0, "censored": 0}
    assert out["to_a"] == {"legs": 1, "pre_aligned": 1, "crossed": 0, "latency_sum": 0, "censored": 0}


def test_the_recorder_decodes_weys_and_strains_and_changes_nothing(seed, mutant):
    from wormwars.brain import Brain
    from wormwars.e3 import maze_world as MW
    from wormwars.e3.maze_world import maze_config
    cfg = maze_config(shuttle_config(), c=5, horizon=200, mu=0.01, lam=0.02, delta=0.05, d0=1.142)
    pop = Genome.cat([seed.genome, mutant])
    runs = []
    for with_rec in (False, True):
        w = MW.MazeWorld(cfg, seed.iface, Brain(pop), torch.tensor([[0], [1], [1]]), run_seed=1_180_000,
                         world_ids=np.array([9802, 9803, 9804]))
        rec = None
        if with_rec:
            rec = AT.LatchRecorder(seed.ext, [seed.genome, mutant])
            rec.attach(w)
            w.recorder = rec
        w.run(200)
        runs.append((w.pos.clone(), w.task_events(), rec, w))
    assert torch.equal(runs[0][0], runs[1][0])
    for k in ("visit_tick", "visits"):
        assert np.array_equal(runs[0][1][k], runs[1][1][k])
    rec, w = runs[1][2], runs[1][3]
    q_now = w.assigns[0].from_brain(w.v[0], 3, w.n_weys)[..., seed.ext.index(O.Q)]
    assert torch.equal(rec.last_q, q_now)  # decoded into world and wey order
    res = rec.result()
    assert len(res) == 3 and all(r["strain"] == s for r, s in zip(res, (0, 1, 1)))


def test_the_vectorised_recorder_matches_the_scripted_tally_on_a_real_run(seed, mutant):
    """The recorder's counts per world equal SwitchTally's, fed tick by tick from a trace of the same run."""
    from wormwars.brain import Brain
    from wormwars.e3 import maze_world as MW
    from wormwars.e3.maze_world import maze_config
    cfg = maze_config(shuttle_config(), c=5, horizon=1200, mu=0.01, lam=0.02, delta=0.05, d0=1.142)
    genomes = [seed.genome, mutant]
    q_i = seed.ext.index(O.Q)

    class Both:
        def __init__(self):
            self.rec = AT.LatchRecorder(seed.ext, genomes)
            self.trace = []

        def attach(self, w):
            self.rec.attach(w)
            self.goal0 = w.goal.clone()

        def record(self, w):
            q = w.assigns[0].from_brain(w.v[0], w.n_worlds, w.n_weys)[..., q_i].to(torch.float64)
            self.trace.append((q.clone(), w.goal.clone(), w.has_visited.clone()))
            self.rec.record(w)

    w = MW.MazeWorld(cfg, seed.iface, Brain(Genome.cat(genomes)), torch.tensor([[0], [1]]), run_seed=1_180_000,
                     world_ids=np.array([9805, 9806]))
    both = Both()
    both.attach(w)
    w.recorder = both
    w.run(1200)
    got = both.rec.result()
    for wi, s in enumerate((0, 1)):
        low, mid, high = AT.latch_states(genomes[s], seed.ext)
        totals = None
        for b in range(w.n_weys):
            t = AT.SwitchTally(mid=mid, low=low, high=high, a_high=AT.a_high(genomes[s], seed.ext))
            goal_before, visited_before = int(both.goal0[wi, b]), False
            for q, goal_after, visited_after in both.trace:
                t.tick(q=float(q[wi, b]), goal_before=goal_before, goal_after=int(goal_after[wi, b]),
                       visited_before=visited_before)
                goal_before, visited_before = int(goal_after[wi, b]), bool(visited_after[wi, b])
            r = t.result()
            flat = {f"{band}_{kind}_{g}": r[band][kind][g] for band in ("third", "half")
                    for kind in ("decided", "agree", "undecided") for g in ("A", "B")}
            flat.update({f"occupancy_{g}": r["occupancy"][g] for g in ("A", "B")})
            flat.update({f"{k}_{d}": r["switches"][d][kk] for d in ("to_a", "to_b")
                         for k, kk in (("legs", "legs"), ("pre", "pre_aligned"), ("crossed", "crossed"),
                                       ("lat", "latency_sum"), ("censored", "censored"))})
            totals = flat if totals is None else {k: totals[k] + v for k, v in flat.items()}
        assert {k: got[wi][k] for k in totals} == totals, wi
    assert sum(got[0][k] + got[1][k] for k in ("legs_to_a", "legs_to_b")) > 0  # the run had visits to check


def test_with_both_outputs_silenced_every_organism_plays_as_the_seed(seed, mutant):
    """No tuned parameter reaches the motors once the 32 output edges are 0, so the W2-alone reference is one
    organism (the plan's §5C6), bitwise on the CPU."""
    from wormwars.brain import Brain
    from wormwars.e3 import maze_world as MW
    from wormwars.e3.maze_world import maze_config
    cfg = maze_config(shuttle_config(), c=5, horizon=300, mu=0.01, lam=0.02, delta=0.05, d0=1.142)
    runs = []
    for g in (seed.genome, mutant):
        lesioned = AT.edge_lesion(g, seed.ext, "outputs_both")
        w = MW.MazeWorld(cfg, seed.iface, Brain(lesioned), torch.zeros(2, 1, dtype=torch.long), run_seed=1_180_000,
                         world_ids=np.array([9807, 9808]))
        w.run(300)
        runs.append((w.pos.clone(), w.task_events()))
    assert torch.equal(runs[0][0], runs[1][0])
    for k in ("visit_tick", "visits", "entries"):
        assert np.array_equal(runs[0][1][k], runs[1][1][k])
    intact = []
    for g in (seed.genome, mutant):  # and the test can fail: intact, they differ
        w = MW.MazeWorld(cfg, seed.iface, Brain(g), torch.zeros(2, 1, dtype=torch.long), run_seed=1_180_000,
                         world_ids=np.array([9807, 9808]))
        w.run(300)
        intact.append(w.pos.clone())
    assert not torch.equal(intact[0], intact[1])
