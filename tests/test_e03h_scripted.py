"""03h's scripted gate families (experiments/03h-history-use/DESIGN.md §4): a memoryless controller reading food_fell
is exactly MemoryKinesis's zero-threshold member under relief; the slow-memory family at T = 1 is exactly
MemoryKinesis (any threshold); with memory off and the bit on it is the bit controller; the policies broadcast for
batched tuning."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e03h import interface_03h
from wormwars.e03h.scripted import BitKinesis, SlowMemoryKinesis
from wormwars.exp02 import grid
from wormwars.exp02.scripted import MemoryKinesis, ScriptedBrain, score_policy, tune, tune_batched
from wormwars.interface import load_interface

IDS = np.arange(300, 306)
P = dict(slow=0.3, fast=0.9, threshold=0.05, turn=0.1, fall_turn=0.8)


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), interface_03h(con)


def t1(mode):
    cfg = grid.task_config(Config(), "T1")
    cfg.world.food_fell = mode
    return cfg


def score(cfg, iface, policy):
    return score_policy(cfg, iface, policy, IDS, 5, "cpu")


def test_the_bit_controller_is_memorykinesis_at_threshold_zero_under_relief(parts):
    _, _, v = parts
    cfg = t1("relief")
    a = score(cfg, v, BitKinesis(**P))
    b = score(cfg, v, MemoryKinesis(**P, fall_threshold=0.0))
    assert np.array_equal(a, b)


@pytest.mark.parametrize("thr", [0.0, 0.02])
def test_slow_memory_at_t1_is_memorykinesis(parts, thr):
    _, _, v = parts
    for mode in ("level", "relief"):
        cfg = t1(mode)
        a = score(cfg, v, SlowMemoryKinesis(**P, fall_threshold=thr, T=1.0, use_memory=1.0, use_bit=0.0))
        b = score(cfg, v, MemoryKinesis(**P, fall_threshold=thr))
        assert np.array_equal(a, b)


def test_slow_memory_with_memory_off_and_the_bit_on_is_the_bit_controller(parts):
    _, _, v = parts
    cfg = t1("relief")
    a = score(cfg, v, SlowMemoryKinesis(**P, fall_threshold=0.0, T=5.0, use_memory=0.0, use_bit=1.0))
    assert np.array_equal(a, score(cfg, v, BitKinesis(**P)))


def test_a_longer_average_changes_the_policy(parts):
    _, _, v = parts
    cfg = t1("level")
    a = score(cfg, v, SlowMemoryKinesis(**P, fall_threshold=0.0, T=1.0, use_memory=1.0, use_bit=0.0))
    b = score(cfg, v, SlowMemoryKinesis(**P, fall_threshold=0.0, T=10.0, use_memory=1.0, use_bit=0.0))
    assert not np.array_equal(a, b)


def test_the_policies_broadcast_for_batched_tuning(parts):
    _, _, v = parts
    cfg = t1("relief")
    g = {"slow": [0.3], "fast": [0.9], "threshold": [0.05], "turn": [0.1], "fall_turn": [0.4, 0.8],
         "fall_threshold": [0.0], "T": [1.0, 5.0], "use_memory": [1.0], "use_bit": [0.0, 1.0]}
    seq = tune(lambda **k: SlowMemoryKinesis(**k), g, cfg, v, IDS, 5, "cpu")
    bat = tune_batched(lambda **k: SlowMemoryKinesis(**k), g, cfg, v, IDS, 5, "cpu")
    assert seq[0] == bat[0] and abs(seq[1] - bat[1]) < 1e-6


def test_a_bit_reading_policy_needs_the_channel(parts):
    _, pinned, _ = parts
    with pytest.raises(ValueError):
        ScriptedBrain(pinned, 302, BitKinesis(**P), 1.0, 1.0)


def _seq(policy, levels, fells):
    state, out = None, []
    for lv, fl in zip(levels, fells):
        x = torch.tensor([lv])
        fwd, turn, state = policy(x, x, state, fell=torch.tensor([fl]))
        out.append((float(fwd[0]), float(turn[0]), None if state is None else float(state[0])))
    return out


def test_commands_and_memory_on_prescribed_sequences():
    """Astra: commands and states, not only scores. The bit controller issues MemoryKinesis's commands when the bit is
    the fall; memory and bit combine by OR and each can be switched off; T = 5's average follows its recurrence."""
    lv = [0.5, 0.4, 0.4, 0.6, 0.3, 0.3]
    fell = [False] + [b < a for a, b in zip(lv, lv[1:])]
    mk = MemoryKinesis(**P, fall_threshold=0.0)
    st, mem = None, []
    for x in lv:
        f, t, st = mk(torch.tensor([x]), torch.tensor([x]), st)
        mem.append((float(f[0]), float(t[0])))
    bit = [(f, t) for f, t, _ in _seq(BitKinesis(**P), lv, fell)]
    assert bit == mem
    # memory says falling (0.6 -> 0.3) while the bit says not, and the reverse at another tick
    contra = [False, True, False, False, False, True]
    both = _seq(SlowMemoryKinesis(**P, fall_threshold=0.0, T=1.0, use_memory=1.0, use_bit=1.0), lv, contra)
    only_mem = _seq(SlowMemoryKinesis(**P, fall_threshold=0.0, T=1.0, use_memory=1.0, use_bit=0.0), lv, contra)
    only_bit = _seq(SlowMemoryKinesis(**P, fall_threshold=0.0, T=1.0, use_memory=0.0, use_bit=1.0), lv, contra)
    by_mem = fell
    turns = lambda r: [t for _, t, _ in r]  # noqa: E731
    want = lambda flags: [float(np.float32(P["fall_turn"] if f else P["turn"])) for f in flags]  # noqa: E731
    assert turns(only_mem) == want(by_mem)
    assert turns(only_bit) == want(contra)
    assert turns(both) == want([a or b for a, b in zip(by_mem, contra)])
    # T = 5: compared with the previous average, then m <- m + (x - m) / 5 (float32, as the policy computes it)
    r = _seq(SlowMemoryKinesis(**P, fall_threshold=0.0, T=5.0, use_memory=1.0, use_bit=0.0), lv, [False] * 6)
    m = torch.tensor([lv[0]])
    expect_fall = [False]
    for x in lv[1:]:
        xt = torch.tensor([x])
        expect_fall.append(bool(xt < m))
        m = m + (xt - m) / 5.0
    assert turns(r) == want(expect_fall)
    assert abs(r[-1][2] - float(m[0])) < 1e-7
