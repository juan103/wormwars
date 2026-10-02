"""E3a's organisms (experiments/E3-ab-organism/E3a/PREREGISTRATION.md §4; tests 3, 5, 7).

The engineered organism E: two renamed copies of L1 (A's and B's noses), two relays and the latch q,
with the gate by saturation (comparator biases −1.914, q → A's comparators +2, → B's −2). Its
controls are stated changes to E. B-shared gates one L1's two nose pairs instead.
"""

from __future__ import annotations

import math

import pytest
import torch

from wormwars import graft as G
from wormwars.brain import Brain
from wormwars.connectome import load_connectome
from wormwars.e3 import organism as O
from wormwars.e3.task import shuttle_config
from wormwars.e4s.arms import load_l1


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def l1():
    return load_l1()


def test_e_has_eleven_neurons_and_forty_seven_edges(l1):
    e = O.engineered(l1)
    assert len(e.neurons) == 11 and len(e.synapses) == 47
    assert {n: e.tau[n] for n in ("E3_A_NL", "E3_B_CR", "E3_RA", "E3_Q")} == {"E3_A_NL": 0.5, "E3_B_CR": 0.5, "E3_RA": 0.5, "E3_Q": 1.0}
    for c in O.COMPARATORS:
        assert e.bias[c] == -1.914
    syn = {(a, b): w for a, b, w in e.synapses}
    assert syn[("E3_Q", "E3_Q")] == 2.0 and syn[("E3_RA", "E3_Q")] == -3.0 and syn[("E3_RB", "E3_Q")] == 3.0
    assert syn[("E3_Q", "E3_A_CL")] == 2.0 and syn[("E3_Q", "E3_B_CR")] == -2.0
    # each copy carries L1's 20 edges, renamed
    l1_syn = {(a, b): w for a, b, w in l1.synapses}
    for prefix in ("A", "B"):
        for (a, b), w in l1_syn.items():
            ren = lambda n: n.replace("E4S_", f"E3_{prefix}_")  # noqa: E731
            assert syn[(ren(a), ren(b))] == w


def test_e_routes_each_signal_to_its_neurons_only(con, l1):
    e = O.engineered(l1)
    ext = G.graft_connectome(con, e)
    iface = G.graft_interface(ext, e)
    got = {}
    for s, n, g in zip(iface.signal_names, iface.sensor_neuron, iface.sensor_gain):
        if s in ("a_left", "a_right", "b_left", "b_right", "at_a", "at_b", "goal_left", "goal_right"):
            got[(s, ext.names[int(n)])] = float(g)
    assert got == {("a_left", "E3_A_NL"): 1.0, ("a_right", "E3_A_NR"): 1.0, ("b_left", "E3_B_NL"): 1.0,
                   ("b_right", "E3_B_NR"): 1.0, ("at_a", "E3_RA"): 3.0, ("at_b", "E3_RB"): 3.0}


def test_the_controls_are_stated_changes_to_e(l1):
    e = {(a, b): w for a, b, w in O.engineered(l1).synapses}
    nl = O.no_latch(l1)
    assert all(nl.bias[c] == 0.0 for c in O.COMPARATORS)
    syn = {(a, b): w for a, b, w in nl.synapses}
    assert all(syn[("E3_Q", c)] == 0.0 for c in O.COMPARATORS)
    assert set(syn) == set(e)  # the same mask
    om = O.one_module(l1)
    syn = {(a, b): w for a, b, w in om.synapses}
    assert om.bias["E3_A_CL"] == 0.0 and om.bias["E3_B_CL"] == -1.914
    assert syn[("E3_Q", "E3_A_CL")] == 0.0 and syn[("E3_Q", "E3_B_CL")] == -2.0
    assert all(w == 0.0 for (a, b), w in syn.items() if a.startswith("E3_B_C") and not b.startswith("E3_"))
    assert set(syn) == set(e)


def test_b_shared_gates_its_nose_pairs(con, l1):
    m = O.b_shared(l1)
    assert len(m.neurons) == 9
    syn = {(a, b): w for a, b, w in m.synapses}
    assert syn[("E3_S_AL", "E3_S_CL")] == 3.0 and syn[("E3_S_AL", "E3_S_CR")] == -3.0
    assert syn[("E3_S_BR", "E3_S_CR")] == 3.0 and syn[("E3_S_BR", "E3_S_CL")] == -3.0
    assert syn[("E3_Q", "E3_S_AL")] == 2.0 and syn[("E3_Q", "E3_S_BR")] == -2.0
    assert all(m.bias[n] == -1.914 for n in ("E3_S_AL", "E3_S_AR", "E3_S_BL", "E3_S_BR"))
    ext = G.graft_connectome(con, m)
    iface = G.graft_interface(ext, m)
    routed = {(s, ext.names[int(n)]) for s, n in zip(iface.signal_names, iface.sensor_neuron) if ext.names[int(n)].startswith("E3_")}
    assert routed == {("a_left", "E3_S_AL"), ("a_right", "E3_S_AR"), ("b_left", "E3_S_BL"), ("b_right", "E3_S_BR"),
                      ("at_a", "E3_RA"), ("at_b", "E3_RB")}


def test_l1_switch_reads_the_goals_scent(l1):
    m = O.l1_switch(l1)
    assert {n: G.nose_entry(m, n) for n in m.noses} == {"E4S_NL": ("goal_left", 1.0), "E4S_NR": ("goal_right", 1.0)}


def test_the_modules_are_registered_for_the_publication_guard(l1):
    for m in (O.engineered(l1), O.b_shared(l1), O.l1_switch(l1)):
        assert G.MODULES[m.name] is m or G.MODULES[m.name] == m


# ------------------------------------------------------------------ test 7: the latch in Brain.step

def _latch_run(con, l1, q0, drive_neuron, ticks_on, total):
    cfg = shuttle_config()
    e = O.engineered(l1)
    ext = G.graft_connectome(con, e)
    from wormwars.e4s.comparator import carrier_genome
    brain = Brain(carrier_genome(ext, e, cfg.brain, forward=1.0, turn=0.2))
    n, q, d = ext.n, ext.index("E3_Q"), ext.index(drive_neuron)
    v = torch.zeros(1, 1, n)
    v[0, 0, q] = q0
    out = []
    for t in range(total):
        cur = torch.zeros(1, 1, n)
        if t < ticks_on:
            cur[0, 0, d] = 3.0
        v = brain.step(v, cur)
        out.append(float(v[0, 0, q]))
    return out


def test_a_one_tick_level_switches_the_latch(con, l1):
    q = _latch_run(con, l1, O.Q_STAR, "E3_RA", 1, 40)
    assert q[0] == pytest.approx(-0.2197, abs=1e-3)
    assert q[-1] == pytest.approx(-O.Q_STAR, abs=1e-4)
    q = _latch_run(con, l1, -O.Q_STAR, "E3_RB", 1, 40)
    assert q[0] == pytest.approx(0.2197, abs=1e-3) and q[-1] == pytest.approx(O.Q_STAR, abs=1e-4)


def test_the_cue_and_the_hold(con, l1):
    q = _latch_run(con, l1, 0.0, "E3_RB", 5, 600)
    assert q[4] == pytest.approx(4.937, abs=2e-3)
    assert q[-1] == pytest.approx(O.Q_STAR, abs=1e-4)
    assert O.Q_STAR == pytest.approx(1.91501, abs=1e-5) and math.tanh(O.Q_STAR) == pytest.approx(0.957504, abs=1e-6)


def test_the_controls_do_not_overwrite_es_registration(l1):
    e = O.engineered(l1)
    O.no_latch(l1)
    O.one_module(l1)
    assert G.MODULES[e.name] == e
