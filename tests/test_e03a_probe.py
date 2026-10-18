"""03a's bounded-history replay probe (DESIGN.md v7.1 §8): the full-replay control reproduces the unperturbed episode
bitwise on the CPU; the first action that can differ is at 2L + 1; the rebuild equals a fresh run over the window; and
the prescribed-sequence validation on the scripted calibrators (KT and KTM unaffected, KTS's average changed)."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.connectome import load_connectome
from wormwars.e03a.probe import KT, KTS, ReplayBrain
from wormwars.e1.task import task_n_config
from wormwars.evo.rollout import rollout_brain
from wormwars.exp02.scripted import ScriptedBrain
from wormwars.interface import load_interface
from wormwars.world import World


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    iface = load_interface(con)
    cfg = task_n_config(sigma=6.0, amplitude=1.0, radius=1.5, separation=8.0, horizon=60)
    cfg.world.food_sensing = "mono"
    cfg.brain.substeps = 8  # a cheaper brain for the test; the probe does not depend on it
    return con, iface, cfg


def _genome(con, cfg, n=3, seed=0):
    return Genome.random(BrainSpec.from_connectome(con), cfg.brain, n, generator=torch.Generator().manual_seed(seed))


def _episode(cfg, iface, brain, n_strains, worlds=2, seed=7):
    ids = np.arange(worlds)
    strain_of = torch.arange(n_strains).repeat_interleave(worlds).reshape(-1, 1)
    w = World(cfg, iface, brain, strain_of, run_seed=seed, world_ids=np.tile(ids, n_strains))
    fwd, turn = [], []
    while not w.done():
        w.tick()
        fwd.append(w.last_forward.clone())
        turn.append(w.last_turn.clone())
    return torch.stack(fwd), torch.stack(turn), w.pos.clone(), w.targets_reached.clone()


def test_full_replay_reproduces_the_unperturbed_episode_bitwise(parts):
    con, iface, cfg = parts
    g = _genome(con, cfg)
    a = _episode(cfg, iface, Brain(g), g.n_strains)
    rb = ReplayBrain(Brain(g), L=10, window=None)
    b = _episode(cfg, iface, rb, g.n_strains)
    assert rb.resets == 5
    for x, y in zip(a, b):
        assert torch.equal(x, y)


def test_the_first_action_that_can_differ_is_at_2L_plus_1(parts):
    con, iface, cfg = parts
    g = _genome(con, cfg, n=4, seed=1)
    L = 5
    a = _episode(cfg, iface, Brain(g), g.n_strains)
    b = _episode(cfg, iface, ReplayBrain(Brain(g), L=L), g.n_strains)
    # ticks 1..2L (indices 0..2L-1) are unperturbed
    assert torch.equal(a[0][:2 * L], b[0][:2 * L]) and torch.equal(a[1][:2 * L], b[1][:2 * L])
    # and the probe does act afterwards (sabotage: a probe that never resets would pass the line above too)
    assert not (torch.equal(a[0], b[0]) and torch.equal(a[1], b[1]))


def test_the_rebuild_is_a_fresh_run_over_the_last_L_inputs(parts):
    con, _, cfg = parts
    g = _genome(con, cfg, n=2, seed=2)
    L = 4
    rng = torch.Generator().manual_seed(3)
    inputs = [torch.randn(2, 3, con.n, generator=rng) * 0.5 for _ in range(13)]
    inner = Brain(g)
    rb = ReplayBrain(inner, L=L)
    v = rb.initial_state(3)
    for t, cur in enumerate(inputs):
        v = rb.step(v, cur)
        if t + 1 >= L and (t + 1) % L == 0 and t + 1 < len(inputs):
            # what the next step will rebuild from: the last L inputs, from zeros
            ref = inner.initial_state(3)
            for c in inputs[t + 1 - L:t + 1]:
                ref = inner.step(ref, c)
            assert torch.equal(rb.rebuild(v), ref)


def _scripted(iface, policy, n=1):
    return ScriptedBrain(iface, 302, policy, forward_gain=1.0, turn_gain=1.0, n_strains=n)


def _levels(iface, seq):
    names = list(iface.signal_names)
    left = int(iface.sensor_neuron[names.index("food_left")])
    right = int(iface.sensor_neuron[names.index("food_right")])
    out = []
    for lv in seq:
        cur = torch.zeros(1, 1, 302)
        cur[..., left] = cur[..., right] = float(lv)
        out.append(cur)
    return out


def _actions(brain, inputs):
    v = brain.initial_state(1)
    acts = []
    for cur in inputs:
        v = brain.step(v, cur)
        acts.append(v.clone())
    return torch.stack(acts)


KT_PARAMS = dict(threshold=0.5, slow=0.5, fast=1.0, turn_hi=0.2, turn_lo=0.1, avoid=0.0)


def test_prescribed_sequence_where_the_discarded_history_changes_a_slow_controllers_action(parts):
    _, iface, _ = parts
    seq = [1.0] * 30 + [0.6] * 20  # after the drop, the T = 20 average stays above 0.6 for many ticks
    inputs = _levels(iface, seq)
    make = lambda: _scripted(iface, KTS(20.0, fall_turn=-1.0, **KT_PARAMS))  # noqa: E731
    plain, probed = _actions(make(), inputs), _actions(ReplayBrain(make(), L=5), inputs)
    assert torch.equal(plain[:31], probed[:31])  # until the window holds only post-drop levels
    assert not torch.equal(plain[35:], probed[35:])  # by tick 36 the rebuilt average is 0.6: no fall turn


def test_memoryless_and_one_tick_controllers_are_unaffected_by_the_probe(parts):
    _, iface, _ = parts
    rng = np.random.default_rng(0)
    inputs = _levels(iface, rng.random(60))
    for policy in (KT(**KT_PARAMS), KT(fall_turn=-1.0, **KT_PARAMS)):
        for L in (5, 10, 20, 50):
            plain = _actions(_scripted(iface, policy), inputs)
            probed = _actions(ReplayBrain(_scripted(iface, policy), L=L), inputs)
            assert torch.equal(plain, probed)


def test_the_calibrators_closed_loop_kt_and_ktm_unchanged_kts_changed(parts):
    """In the world: KT and KTM score exactly the same under the probe; KTS at T = 20 does not always."""
    con, iface, cfg = parts
    c = cfg.copy()
    ids = np.arange(16)

    def score(policy, L=None):
        b = ScriptedBrain(iface, con.n, policy, c.world.forward_gain, c.world.turn_gain)
        brain = b if L is None else ReplayBrain(b, L=L)
        r = rollout_brain(c, iface, brain, ids, 3)
        return np.asarray(r.score), np.asarray(r.final_head)

    for policy in (KT(**KT_PARAMS), KT(fall_turn=-1.0, **KT_PARAMS)):
        a, b = score(policy), score(policy, L=5)
        np.testing.assert_array_equal(a[0], b[0])
        np.testing.assert_array_equal(a[1], b[1])
    k = KTS(20.0, fall_turn=-1.0, **KT_PARAMS)
    a, b = score(k), score(k, L=5)
    assert not np.array_equal(a[1], b[1])


@pytest.mark.parametrize("L", [5, 10, 20])
def test_the_first_difference_is_exactly_at_action_2L_plus_1(parts, L):
    """Astra and Fable: a probe resetting one period late would pass the world test above. Here the history before
    tick L + 1 decides KTS's action at 2L + 1: the unperturbed average still remembers the high level, the rebuilt one
    holds only the low level since tick L + 1."""
    _, iface, _ = parts
    seq = [1.0] * L + [0.6] * (2 * L + 5)
    inputs = _levels(iface, seq)
    make = lambda: _scripted(iface, KTS(20.0, fall_turn=-1.0, **KT_PARAMS))  # noqa: E731
    plain, probed = _actions(make(), inputs), _actions(ReplayBrain(make(), L=L), inputs)
    assert torch.equal(plain[:2 * L], probed[:2 * L])
    assert not torch.equal(plain[2 * L], probed[2 * L])  # index 2L is action 2L + 1
