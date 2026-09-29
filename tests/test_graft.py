"""Grafting extra neurons onto a connectome (`wormwars/graft.py`, E4s): the extended connectome keeps
every existing neuron and edge, the seeded genome carries the background's and the module's
parameters to the right places, the interface feeds the module's noses (and the module-only
probes), and an inert graft does not change the worm's own trajectories."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars import graft as G
from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.loader import ConnectomeError
from wormwars.interface import load_interface


@pytest.fixture(scope="module")
def con():
    return load_connectome()


def toy(outputs=True) -> G.Module:
    syn = [("E4S_NL", "E4S_TL", 1.5), ("E4S_NR", "E4S_TR", 1.5), ("E4S_TL", "E4S_TR", -0.5),
           ("E4S_TR", "E4S_TL", -0.5),
           ("SMDDL", "E4S_TL", 0.3)]  # worm -> module (a turn copy): its edge sits among the worm's
    if outputs:
        syn += [("E4S_TL", "SMDDL", 1.2), ("E4S_TL", "SMDVL", -1.2), ("E4S_TR", "SMDVL", 1.2),
                ("E4S_TR", "SMDDL", -1.2)]
    return G.Module(name="toy", neurons=("E4S_NL", "E4S_NR", "E4S_TL", "E4S_TR"),
                    synapses=tuple(syn), tau={"E4S_NL": 0.7, "E4S_NR": 0.7, "E4S_TL": 1.0, "E4S_TR": 1.0},
                    bias={"E4S_TL": 0.1}, noses={"E4S_NL": "food_left", "E4S_NR": "food_right"},
                    nose_gain=2.5)


def test_the_extended_connectome_appends_and_keeps_every_worm_neuron_and_edge(con):
    ext = G.graft_connectome(con, toy())
    assert ext.n == con.n + 4 and ext.names[:con.n] == con.names and ext.names[con.n:] == toy().neurons
    np.testing.assert_array_equal(ext.chem[:con.n, :con.n], con.chem)
    np.testing.assert_array_equal(ext.gap[:con.n, :con.n], con.gap)
    assert ext.chem[ext.index("E4S_TL"), ext.index("SMDDL")] > 0
    assert (ext.gap[con.n:, :] == 0).all() and ext.label == "N2+toy"


def test_a_module_may_not_rewrite_the_worms_own_wiring(con):
    bad = G.Module(name="bad", neurons=("E4S_X",), synapses=(("AWAL", "AIYL", 1.0),), tau={}, bias={},
                   noses={}, nose_gain=1.0)
    with pytest.raises(ValueError, match="worm"):
        G.graft_connectome(con, bad)
    unknown = G.Module(name="u", neurons=("E4S_X",), synapses=(("E4S_X", "NOPE", 1.0),), tau={}, bias={},
                       noses={}, nose_gain=1.0)
    with pytest.raises(ConnectomeError):
        G.graft_connectome(con, unknown)


def test_the_seeded_genome_places_the_background_and_the_module(con):
    cfg = Config()
    spec = BrainSpec.from_connectome(con)
    base = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(1))
    m = toy()
    ext = G.graft_connectome(con, m)
    gen = G.seeded_genome(ext, m, cfg.brain, base=base)
    espec = gen.spec
    assert gen.n_strains == 2 and espec.n == con.n + 4
    W, _ = gen.dense()
    Wb, Gb = base.dense()
    torch.testing.assert_close(W[:, :con.n, :con.n], Wb)
    torch.testing.assert_close(gen.dense()[1][:, :con.n, :con.n], Gb)
    torch.testing.assert_close(gen.tau[:, :con.n], base.tau)
    torch.testing.assert_close(gen.bias[:, :con.n], base.bias)
    i, j = ext.index("E4S_TL"), ext.index("SMDDL")
    assert float(W[0, i, j]) == pytest.approx(1.2) and float(gen.tau[0, ext.index("E4S_NL")]) == pytest.approx(0.7)
    assert float(gen.bias[1, ext.index("E4S_TL")]) == pytest.approx(0.1)


def test_a_silent_background_has_no_worm_drive(con):
    m = toy()
    gen = G.seeded_genome(G.graft_connectome(con, m), m, Config().brain, base=None, n_strains=1)
    W, Gm = gen.dense()
    assert float(W[0, :con.n, :con.n].abs().max()) == 0 and float(Gm.abs().max()) == 0
    assert float(gen.bias[0, :con.n].abs().max()) == 0


@pytest.mark.parametrize("probe,want", [("real", {"E4S_NL": {"food_left": 1.0}, "E4S_NR": {"food_right": 1.0}}),
                                        ("mean", {"E4S_NL": {"food_left": 0.5, "food_right": 0.5},
                                                  "E4S_NR": {"food_left": 0.5, "food_right": 0.5}}),
                                        ("swapped", {"E4S_NL": {"food_right": 1.0}, "E4S_NR": {"food_left": 1.0}})])
def test_the_interface_feeds_the_noses_and_the_module_only_probes(con, probe, want):
    m = toy()
    ext = G.graft_connectome(con, m)
    iface = G.graft_interface(ext, m, probe=probe)
    got = {}
    for s, n, g in zip(iface.signal_names, iface.sensor_neuron, iface.sensor_gain):
        name = ext.names[int(n)]
        if name.startswith("E4S_"):
            got.setdefault(name, {})[s] = got.get(name, {}).get(s, 0.0) + float(g) / m.nose_gain
    assert got == want
    base = load_interface(con)  # the worm's own entries are unchanged
    assert list(iface.signal_names[:len(base.signal_names)]) == list(base.signal_names)
    assert list(iface.sensor_neuron[:len(base.sensor_neuron)]) == list(base.sensor_neuron)


def test_an_inert_graft_leaves_the_worms_trajectories_unchanged(con):
    """The module has no synapse onto the worm, so the 302 neurons evolve as without it, up to
    rounding: adding rows and columns regroups the floating-point sums, so it is not bit-exact
    (measured: at most about 1.4e-6 over 300 ticks with a 30-neuron module, three seeds; E4s design
    note, D140). The declared tolerance is 1e-5 over 100 ticks, on the CPU."""
    cfg = Config()
    spec = BrainSpec.from_connectome(con)
    base = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(2))
    m = toy(outputs=False)
    gen = G.seeded_genome(G.graft_connectome(con, m), m, cfg.brain, base=base)
    b0, b1 = Brain(base), Brain(gen)
    v0, v1 = b0.initial_state(3), b1.initial_state(3)
    rng = torch.Generator().manual_seed(3)
    worst = 0.0
    for _ in range(100):
        cur = torch.rand(2, 3, con.n, generator=rng) * 0.3
        cur1 = torch.cat([cur, torch.zeros(2, 3, 4)], dim=2)
        v0, v1 = b0.step(v0, cur), b1.step(v1, cur1)
        worst = max(worst, float((v0 - v1[..., :con.n]).abs().max()))
    assert 0 <= worst <= 1e-5, worst
