"""E3a's generalised graft (E3a PREREGISTRATION §3 routing, §5 G-E; test 5).

- A nose may read any declared signal, at its own gain: (signal, gain). A plain signal name keeps the
  module's `nose_gain`, so E4s's modules are unchanged.
- The probes act on left/right pairs of any scent (food, A's, B's, the goal's), and may be limited
  to some signals, so one module's noses can be probed alone.
- `combine` merges several modules (and a selector whose synapses reach into them) into one graft.
"""

from __future__ import annotations

import pytest

from wormwars import graft as G
from wormwars.connectome import load_connectome
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def con():
    return load_connectome()


def pair(prefix, left, right):
    return G.Module(
        f"pair-{prefix}", (f"{prefix}_NL", f"{prefix}_NR", f"{prefix}_CL"),
        ((f"{prefix}_NL", f"{prefix}_CL", 3.0), (f"{prefix}_NR", f"{prefix}_CL", -3.0), (f"{prefix}_CL", "SMDDL", 3.0)),
        tau={f"{prefix}_NL": 0.5}, bias={f"{prefix}_CL": -1.0},
        noses={f"{prefix}_NL": left, f"{prefix}_NR": right})


def selector():
    return G.Module("sel", ("T_RA", "T_Q"), (("T_RA", "T_Q", -3.0), ("T_Q", "T_Q", 2.0), ("T_Q", "TA_CL", 2.0)),
                    tau={"T_RA": 0.5}, noses={"T_RA": ("at_a", 3.0)})


def entries(ext, iface, prefix="T"):
    got = {}
    for s, n, g in zip(iface.signal_names, iface.sensor_neuron, iface.sensor_gain):
        name = ext.names[int(n)]
        if name.startswith(prefix):
            got.setdefault(name, {})
            got[name][s] = got[name].get(s, 0.0) + float(g)
    return got


def test_combine_merges_neurons_synapses_and_parameters(con):
    m = G.combine("toy-organism", pair("TA", "a_left", "a_right"), pair("TB", "b_left", "b_right"), selector())
    assert m.neurons == ("TA_NL", "TA_NR", "TA_CL", "TB_NL", "TB_NR", "TB_CL", "T_RA", "T_Q")
    assert ("T_Q", "TA_CL", 2.0) in m.synapses and len(m.synapses) == 9
    assert m.tau["TA_NL"] == 0.5 and m.bias["TB_CL"] == -1.0 and m.tau["T_RA"] == 0.5
    ext = G.graft_connectome(con, m)
    assert ext.chem[ext.index("T_Q"), ext.index("T_Q")] == 1.0
    assert ext.chem[ext.index("T_Q"), ext.index("TA_CL")] == 1.0


def test_combine_refuses_shared_names_and_the_graft_refuses_dangling_synapses(con):
    with pytest.raises(ValueError):
        G.combine("dup", pair("TA", "a_left", "a_right"), pair("TA", "b_left", "b_right"))
    bad = G.Module("bad", ("T_X",), (("T_X", "NOPE_CL", 1.0),))
    with pytest.raises(Exception):
        G.graft_connectome(con, G.combine("dangling", pair("TA", "a_left", "a_right"), bad))


def test_noses_read_any_declared_signal_at_their_own_gain(con):
    m = G.combine("toy-organism", pair("TA", "a_left", "a_right"), pair("TB", "b_left", "b_right"), selector())
    ext = G.graft_connectome(con, m)
    got = entries(ext, G.graft_interface(ext, m))
    assert got == {"TA_NL": {"a_left": 1.0}, "TA_NR": {"a_right": 1.0}, "TB_NL": {"b_left": 1.0},
                   "TB_NR": {"b_right": 1.0}, "T_RA": {"at_a": 3.0}}


def test_a_probe_limited_to_one_pair_leaves_the_others_real(con):
    m = G.combine("toy-organism", pair("TA", "a_left", "a_right"), pair("TB", "b_left", "b_right"), selector())
    ext = G.graft_connectome(con, m)
    got = entries(ext, G.graft_interface(ext, m, probe="mean", probe_on={"a_left", "a_right"}))
    assert got["TA_NL"] == {"a_left": 0.5, "a_right": 0.5} and got["TA_NR"] == {"a_left": 0.5, "a_right": 0.5}
    assert got["TB_NL"] == {"b_left": 1.0} and got["T_RA"] == {"at_a": 3.0}
    got = entries(ext, G.graft_interface(ext, m, probe="swapped"))
    assert got["TB_NL"] == {"b_right": 1.0} and got["TA_NR"] == {"a_left": 1.0}
    assert got["T_RA"] == {"at_a": 3.0}  # a level has no partner: probes leave it alone


def test_an_unknown_nose_signal_is_refused(con):
    m = pair("TA", "a_left", "smell_of_victory")
    ext = G.graft_connectome(con, m)
    with pytest.raises(Exception):
        G.graft_interface(ext, m)


def test_e4s_modules_build_the_same_interface_as_before(con):
    from wormwars.e4s.arms import load_l1
    l1 = load_l1()
    ext = G.graft_connectome(con, l1)
    iface = G.graft_interface(ext, l1)
    base = load_interface(con)
    n = len(base.signal_names)
    assert list(iface.signal_names[n:]) == ["food_left", "food_right"]
    assert [ext.names[int(i)] for i in iface.sensor_neuron[n:]] == ["E4S_NL", "E4S_NR"]
    assert [float(g) for g in iface.sensor_gain[n:]] == [l1.nose_gain, l1.nose_gain]
