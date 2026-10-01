"""E4s-0's building blocks (`wormwars/e4s/comparator.py`; docs/E4s/E4s-0-PLAN.md): the comparator
ladder's wiring, the carrier's commands, the sign of the turn, the residual stereo term in the motor
read-out, and generation-0 populations drawn on N2 and embedded."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest
import torch

from wormwars import graft as G
from wormwars.brain import Brain, BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e04a import evolve as EV
from wormwars.e4s import comparator as C
from wormwars.evo.rollout import rollout
from wormwars.world import World


@pytest.fixture(scope="module")
def con():
    return load_connectome()


def edges(m):
    return {(a, b): w for a, b, w in m.synapses}


def test_l1_has_twenty_edges_with_the_planned_signs():
    m = C.comparator("L1", w_n=2.0, w_o=3.0, tau=0.5, bias=0.0)
    e = edges(m)
    assert len(e) == 20 and set(m.neurons) == {"E4S_NL", "E4S_NR", "E4S_CL", "E4S_CR"}
    assert e[("E4S_NL", "E4S_CL")] == 2.0 and e[("E4S_NL", "E4S_CR")] == -2.0
    assert e[("E4S_NR", "E4S_CR")] == 2.0 and e[("E4S_NR", "E4S_CL")] == -2.0
    for d in C.TURN_DORSAL:
        assert e[("E4S_CL", d)] == 3.0 and e[("E4S_CR", d)] == -3.0
    for v in C.TURN_VENTRAL:
        assert e[("E4S_CL", v)] == -3.0 and e[("E4S_CR", v)] == 3.0
    assert m.noses == {"E4S_NL": "food_left", "E4S_NR": "food_right"} and m.nose_gain == 1.0
    assert m.tau["E4S_NL"] == 0.5 and m.tau["E4S_CL"] == 0.5 and m.bias.get("E4S_NL", 0.0) == 0.0


def test_l2_l3_and_l4_add_what_the_plan_says():
    l2 = edges(C.comparator("L2", w_n=1, w_o=1, tau=2.0, bias=-0.5, w_s=0.8))
    assert l2[("E4S_CL", "E4S_CL")] == 0.8 and l2[("E4S_CR", "E4S_CR")] == 0.8 and len(l2) == 22
    l3 = edges(C.comparator("L3", w_n=1, w_o=1, tau=2.0, bias=-0.5, w_m=-0.95))
    assert l3[("E4S_CL", "E4S_CR")] == -0.95 and l3[("E4S_CR", "E4S_CL")] == -0.95 and len(l3) == 22
    for P in (2, 4):
        m = C.comparator("L4", w_n=1, w_o=1, tau=2.0, bias=0.0, w_m=-0.5, pairs=P)
        assert len(m.neurons) == 2 + 2 * P and len(m.synapses) == 22 * P
    with pytest.raises(ValueError):
        C.comparator("L3", w_n=1, w_o=1, tau=1, bias=0, w_s=0.5, w_m=-0.6)  # w_s + |w_m| >= 1: a latch


def settle(brain, n, current=None, ticks=60):
    v = brain.initial_state(1)
    cur = torch.zeros(1, 1, n) if current is None else current
    for _ in range(ticks):
        v = brain.step(v, cur)
    return v


def test_the_carrier_gives_the_declared_commands(con):
    m = C.comparator("L1", w_n=3, w_o=3, tau=0.5, bias=0.0)
    ext = G.graft_connectome(con, m)
    iface = G.graft_interface(ext, m)
    for f, c in ((0.5, 0.0), (1.0, 0.2), (0.75, -0.1)):
        gen = C.carrier_genome(ext, m, Config().brain, forward=f, turn=c)
        v = settle(Brain(gen), ext.n)
        fwd, turn = C.motor_commands(v, iface, Config())
        assert float(fwd) == pytest.approx(f, abs=1e-6) and float(turn) == pytest.approx(c, abs=1e-6)


def test_a_stronger_left_nose_turns_the_wey_left(con):
    m = C.comparator("L1", w_n=3, w_o=3, tau=0.5, bias=0.0)
    ext = G.graft_connectome(con, m)
    iface = G.graft_interface(ext, m)
    brain = Brain(C.carrier_genome(ext, m, Config().brain, forward=1.0, turn=0.0))
    cur = torch.zeros(1, 1, ext.n)
    cur[..., ext.index("E4S_NL")], cur[..., ext.index("E4S_NR")] = 0.11, 0.10
    _, turn = C.motor_commands(settle(brain, ext.n, cur), iface, Config())
    assert float(turn) > 0.05  # left; about 4 * 3 * 3 * 0.01 = 0.36 before saturation and sech^2
    cur[..., ext.index("E4S_NL")], cur[..., ext.index("E4S_NR")] = 0.10, 0.11
    _, turn = C.motor_commands(settle(brain, ext.n, cur), iface, Config())
    assert float(turn) < -0.05


def fake_world(turn_pre, left, right):
    """A stand-in with what `_read_motors` reads: motor indices, gains and the tick's signals."""
    n = 6
    cfg = Config()
    w = SimpleNamespace(_m_fwd_p=torch.tensor([0]), _m_fwd_m=torch.tensor([1]), _m_turn_p=torch.tensor([2]),
                        _m_turn_m=torch.tensor([3]), _m_pump=torch.tensor([4]), iface=SimpleNamespace(pump_gain=4.0),
                        cfg=cfg, last_signals={"food_left": torch.tensor([left]), "food_right": torch.tensor([right])})
    v = torch.zeros(1, n)
    v[0, 2] = float(np.arctanh(turn_pre))  # one dorsal neuron at tanh = turn_pre; turn = 1 x turn_pre
    return w, v


def test_the_residual_adds_k_times_the_difference_before_the_clamp():
    w, v = fake_world(0.3, 0.12, 0.10)
    base = World._read_motors(w, v)
    with C.residual_turn(0.0):
        same = World._read_motors(w, v)
    assert all(torch.equal(a, b) for a, b in zip(base, same))
    with C.residual_turn(10.0):
        _, turn, _ = World._read_motors(w, v)
    assert float(turn) == pytest.approx(0.3 + 10.0 * 0.02, abs=1e-6)
    with C.residual_turn(100.0):
        _, turn, _ = World._read_motors(w, v)
    assert float(turn) == 1.0  # clamped after the addition
    _, after, _ = World._read_motors(w, v)
    assert torch.equal(after, base[1])  # the patch is undone


def test_the_residual_at_zero_reproduces_whole_episodes(con):
    cfg = Config()
    cfg.world.max_ticks = 40
    from wormwars.interface import load_interface
    iface, spec = load_interface(con), BrainSpec.from_connectome(con)
    gen = EV.initial_population(spec, cfg.brain, 5, 2, "cpu")
    a = rollout(cfg, iface, gen, np.arange(4), run_seed=3)
    with C.residual_turn(0.0):
        b = rollout(cfg, iface, gen, np.arange(4), run_seed=3)
    np.testing.assert_array_equal(a.score, b.score)
    np.testing.assert_array_equal(a.final_head, b.final_head)


def test_an_embedded_population_keeps_the_n2_draw_exactly(con):
    cfg = Config()
    m = C.comparator("L1", w_n=3, w_o=3, tau=0.5, bias=0.0)
    ext = G.graft_connectome(con, m)
    pop = C.embedded_population(con, ext, m, cfg.brain, run_seed=1_150_000, population=3)
    ref = EV.initial_population(BrainSpec.from_connectome(con), cfg.brain, 1_150_000, 3, "cpu")
    w, g = G.worm_parameters(ext, pop.w.numpy(), pop.g.numpy())
    np.testing.assert_array_equal(w, ref.w.numpy())
    np.testing.assert_array_equal(g, ref.g.numpy())
    torch.testing.assert_close(pop.tau[:, :con.n], ref.tau, rtol=0, atol=0)
    torch.testing.assert_close(pop.bias[:, :con.n], ref.bias, rtol=0, atol=0)


def fake_world2(dorsal, ventral, left, right):
    w, _ = fake_world(0.1, left, right)
    v = torch.zeros(1, 6)
    v[0, 2], v[0, 3] = float(np.arctanh(dorsal)), float(np.arctanh(ventral))
    v[0, 0], v[0, 4] = 0.3, 0.2  # some forward drive and pump
    return w, v


def test_the_residual_goes_in_before_the_clamp_not_after():
    """Raw turn 1.5 (dorsal 0.75, ventral -0.75) plus a residual of -0.75 is 0.75; clamping the raw
    turn first would give 0.25 (Astra, Fable)."""
    w, v = fake_world2(0.75, -0.75, 0.100, 0.175)
    with C.residual_turn(10.0):
        fwd, turn, pump = World._read_motors(w, v)
    assert float(turn) == pytest.approx(0.75, abs=1e-6)
    f0, _, p0 = World._read_motors(w, v)
    assert torch.equal(fwd, f0) and torch.equal(pump, p0)


def test_a_positive_k_with_a_stronger_left_signal_turns_more_left():
    w, v = fake_world2(0.1, 0.0, 0.12, 0.10)
    _, t0, _ = World._read_motors(w, v)
    with C.residual_turn(2.0):
        _, t1, _ = World._read_motors(w, v)
    assert float(t1) > float(t0)


def test_the_patch_is_removed_after_an_error():
    original = World._read_motors
    with pytest.raises(RuntimeError):
        with C.residual_turn(5.0):
            raise RuntimeError("boom")
    assert World._read_motors is original
