"""E3b-0's candidate organisms (docs/E3/E3b-0-PLAN.md §2a, §2c).

The maze-ready additions, grafted beside a seed's modules: W1, a symmetric wall reflex (two neurons on
the front collision sensors, bias −0.5, outputs ±3 onto the turn neurons, away from their side); W2, a
one-sided reflex (the right output at ±1.5) with a resting turn of +0.4; M, a two-neuron oscillator
(self 1.5, cross ±1, τ 4 or 8) driving the turn neurons at ±0.5. The seeds: E, and S3r3 rebuilt from
E3a's committed champion record and checked against its sha256.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars import graft as G
from wormwars.brain import Brain
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e3 import maze_organisms as MO
from wormwars.e3 import organism as O
from wormwars.e3.task import shuttle_config
from wormwars.e4s import arms as A
from wormwars.e4s import comparator as C
from wormwars.evo.genomes import genome_hash


@pytest.fixture(scope="module")
def con():
    return load_connectome()


@pytest.fixture(scope="module")
def l1():
    return A.load_l1()


@pytest.fixture(scope="module")
def seeds(l1):
    cfg = shuttle_config()
    return {"E": MO.seed("E", l1, cfg.brain), "S3r3": MO.seed("S3r3", l1, cfg.brain)}


def edges(m):
    return {(a, b): w for a, b, w in m.synapses}


def settle(brain, n, current=None, ticks=80):
    v = brain.initial_state(1)
    cur = torch.zeros(1, 1, n) if current is None else current
    for _ in range(ticks):
        v = brain.step(v, cur)
    return v


def test_the_variants_in_order_of_engineering():
    assert MO.VARIANTS == ("W0", "W1", "W1+M40", "W1+M80", "W2", "W2+M40", "W2+M80")


@pytest.mark.parametrize("variant,right", [("W1", 3.0), ("W2", 1.5)])
def test_the_reflex_neurons(variant, right):
    (m,) = [x for x in MO.additions(variant) if "WL" in " ".join(x.neurons)]
    e = edges(m)
    assert set(m.neurons) == {"E3B_WL", "E3B_WR"}
    assert m.noses == {"E3B_WL": ("collision_front_left", 1.0), "E3B_WR": ("collision_front_right", 1.0)}
    assert m.bias == {"E3B_WL": -0.5, "E3B_WR": -0.5} and m.tau == {"E3B_WL": 0.5, "E3B_WR": 0.5}
    for d in C.TURN_DORSAL:  # a left wall turns the wey right (away), a right wall left
        assert e[("E3B_WL", d)] == -3.0 and e[("E3B_WR", d)] == right
    for v in C.TURN_VENTRAL:
        assert e[("E3B_WL", v)] == 3.0 and e[("E3B_WR", v)] == -right
    assert len(e) == 16


@pytest.mark.parametrize("tau", [4.0, 8.0])
def test_the_oscillator_module(tau):
    (m,) = MO.additions(f"W1+M{int(tau * 10)}")[1:]
    e = edges(m)
    assert e[("E3B_M1", "E3B_M1")] == 1.5 and e[("E3B_M2", "E3B_M2")] == 1.5
    assert e[("E3B_M1", "E3B_M2")] == 1.0 and e[("E3B_M2", "E3B_M1")] == -1.0
    assert m.tau == {"E3B_M1": tau, "E3B_M2": tau} and m.bias == {"E3B_M1": 0.0, "E3B_M2": 0.0}
    for d in C.TURN_DORSAL:
        assert e[("E3B_M1", d)] == 0.5
    for v in C.TURN_VENTRAL:
        assert e[("E3B_M1", v)] == -0.5
    assert not m.noses


def test_e_and_s3r3_rebuild_from_their_records(seeds):
    e, s = seeds["E"], seeds["S3r3"]
    assert genome_hash(s.genome, 0) == MO.S3R3_SHA256
    assert genome_hash(s.genome, 0) != genome_hash(e.genome, 0)
    assert s.module.name == e.module.name == "e3-organism-E"


@pytest.mark.parametrize("variant,rest", [("W0", 0.2), ("W1", 0.2), ("W2", 0.4)])
def test_the_resting_turn(con, seeds, variant, rest):
    cfg = shuttle_config()
    org = MO.maze_organism(con, seeds["E"], variant, cfg.brain)
    v = settle(Brain(org.genome), org.ext.n)
    _, turn = C.motor_commands(v, org.iface, cfg)
    assert float(turn) == pytest.approx(rest, abs=2e-3)


@pytest.mark.parametrize("variant", ["W1", "W2"])
def test_a_wall_on_the_left_turns_the_wey_right_and_on_the_right_left(con, seeds, variant):
    cfg = shuttle_config()
    org = MO.maze_organism(con, seeds["E"], variant, cfg.brain)
    brain = Brain(org.genome)
    _, rest = C.motor_commands(settle(brain, org.ext.n), org.iface, cfg)
    for nose, sign in (("E3B_WL", -1), ("E3B_WR", 1)):
        cur = torch.zeros(1, 1, org.ext.n)
        cur[..., org.ext.index(nose)] = 2.0  # a wall cell under the nose: 1 x sense_scale_collision 2
        _, turn = C.motor_commands(settle(brain, org.ext.n, cur), org.iface, cfg)
        assert sign * float(turn - rest) > 0.3


def test_the_seeds_grafted_values_survive_the_additions(con, seeds):
    cfg = shuttle_config()
    s = seeds["S3r3"]
    org = MO.maze_organism(con, s, "W1", cfg.brain)
    for name in s.module.neurons + ("E3B_WL",):
        k = org.ext.index(name)
        src = s.module if name in s.module.neurons else None
        if src is not None:
            j = s.ext.index(name)
            assert float(org.genome.bias[0, k]) == float(s.genome.bias[0, j])
            assert float(org.genome.tau[0, k]) == float(s.genome.tau[0, j])
        else:
            assert float(org.genome.bias[0, k]) == -0.5
    sw, ow = MO.named_edges(s.genome, s.ext), MO.named_edges(org.genome, org.ext)
    for key, val in sw.items():
        assert ow[key] == val
    assert ow[("E3B_WL", "SMDDL")] == -3.0


def test_the_interface_routes_the_wall_sensors_to_the_reflex(con, seeds):
    org = MO.maze_organism(con, seeds["E"], "W2", shuttle_config().brain)
    names = list(org.iface.signal_names)
    hits = [i for i, s in enumerate(names) if s == "collision_front_left"
            and int(org.iface.sensor_neuron[i]) == org.ext.index("E3B_WL")]
    assert len(hits) == 1 and float(org.iface.sensor_gain[hits[0]]) == 1.0


def _m1_trace(con, seeds, variant, ticks):
    cfg = shuttle_config()
    org = MO.maze_organism(con, seeds["E"], variant, cfg.brain)
    brain = Brain(org.genome)
    v = brain.initial_state(1)
    k = org.ext.index("E3B_M1")
    v[0, 0, k] = 0.1  # off the unstable rest
    out, turns = [], []
    cur = torch.zeros(1, 1, org.ext.n)
    for _ in range(ticks):
        v = brain.step(v, cur)
        out.append(float(torch.tanh(v[0, 0, k])))
        turns.append(float(C.motor_commands(v, org.iface, cfg)[1]))
    return np.array(out), np.array(turns)


@pytest.mark.parametrize("variant,tau", [("W1+M40", 4.0), ("W1+M80", 8.0)])
def test_the_oscillator_period_and_swing(con, seeds, variant, tau):
    x, turns = _m1_trace(con, seeds, variant, 1200)
    late = x[600:]
    up = np.flatnonzero((late[:-1] < 0) & (late[1:] >= 0))
    period = float(np.mean(np.diff(up)))
    assert period == pytest.approx(9.9 * tau, rel=0.1)
    assert late.max() == pytest.approx(0.92, abs=0.05) and late.min() == pytest.approx(-0.92, abs=0.05)
    assert float(np.mean(turns[600:])) == pytest.approx(0.2, abs=0.05)  # it swings about the carrier's turn
    assert float(np.ptp(turns[600:])) > 0.3


def test_the_maze_modules_are_registered(con, seeds):
    org = MO.maze_organism(con, seeds["S3r3"], "W2+M80", shuttle_config().brain)
    assert G.MODULES[org.module.name] == org.module
    assert org.module.name == "e3b-e3-organism-E-W2+M80"
