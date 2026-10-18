"""03h's food_fell channel (experiments/03h-history-use/DESIGN.md §3): the relief bit is the fall of the injected food
current since the last tick, 0 on the first tick and for dead weys; level injects zeros but counts the would-be bit;
sham is a keyed two-state Markov sequence at registered rates; and under level the interface variant plays exactly as
the pinned interface does (AGENTS.md rule 7)."""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e03h import AMPLITUDE, interface_03h
from wormwars.evo.rollout import rollout
from wormwars.exp02 import grid
from wormwars.interface import load_interface
from wormwars.world import World


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), interface_03h(con), BrainSpec.from_connectome(con)


def t1(mode=None, rates=None):
    cfg = grid.task_config(Config(), "T1")
    cfg.world.food_fell = mode
    cfg.world.food_fell_rates = rates
    return cfg


def build(parts, cfg, iface, n=3, seed=0, ids=None):
    con, _, _, spec = parts
    g = Genome.random(spec, cfg.brain, n, generator=torch.Generator().manual_seed(seed))
    strain_of = torch.arange(n).reshape(n, 1)  # world k is played by strain k
    return World(cfg, iface, Brain(g), strain_of, run_seed=3, world_ids=None if ids is None else np.asarray(ids))


def injected_food(w, iface, cfg):
    names = list(iface.signal_names)
    k = names.index("food_left")
    raw = w.last_signals["food_left"] * float(iface.sensor_gain[k]) * cfg.brain.input_gain
    return raw.clamp(-cfg.brain.input_max, cfg.brain.input_max)


def test_an_unset_food_fell_leaves_the_configuration_hash_unchanged():
    d = Config().to_dict()["world"]
    assert "food_fell" not in d and "food_fell_rates" not in d
    c = Config()
    c.world.food_fell = "relief"
    assert c.to_dict()["world"]["food_fell"] == "relief"


def test_the_interface_variant_maps_food_fell_to_ask_at_the_registered_amplitude(parts):
    con, pinned, v, _ = parts
    names = list(v.signal_names)
    idx = [i for i, n in enumerate(names) if n == "food_fell"]
    assert [con.names[int(v.sensor_neuron[i])] for i in idx] == ["ASKL", "ASKR"]
    assert all(abs(float(v.sensor_gain[i]) - AMPLITUDE) < 1e-7 for i in idx)
    assert names[: len(pinned.signal_names)] == list(pinned.signal_names)  # the pinned channels first, unchanged


def test_relief_is_the_fall_of_the_injected_food_current(parts):
    _, _, v, _ = parts
    cfg = t1("relief")
    w = build(parts, cfg, v)
    prev = None
    for t in range(60):
        alive_before = w.alive.clone()
        w.tick()
        cur = injected_food(w, v, cfg)
        bit = w.last_signals["food_fell"]
        if prev is None:
            assert torch.equal(bit, torch.zeros_like(bit))  # the first tick
        else:
            want = ((cur < prev) & alive_before).to(bit.dtype)
            assert torch.equal(bit, want)
        prev = cur


def test_level_injects_zeros_and_counts_the_would_be_bit(parts):
    _, _, v, _ = parts
    cfg = t1("level")
    w = build(parts, cfg, v)
    shadow, alive = [], []
    prev = None
    for _ in range(60):
        alive.append(w.alive.clone())
        w.tick()
        assert torch.equal(w.last_signals["food_fell"], torch.zeros_like(w.last_signals["food_fell"]))
        cur = injected_food(w, v, cfg)
        shadow.append(torch.zeros_like(cur, dtype=torch.bool) if prev is None else (cur < prev) & alive[-1])
        prev = cur
    counts = np.zeros(4, dtype=np.int64)  # N00, N01, N10, N11 between ticks t - 1 and t, t - 1 >= 1, alive at both
    for t in range(2, len(shadow)):
        both = alive[t - 1] & alive[t]  # alive when sensing at both ends of the step
        a, b = shadow[t - 1][both], shadow[t][both]
        for i, (x, y) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
            counts[i] += int(((a == bool(x)) & (b == bool(y))).sum())
    assert w.food_fell_counts["relief"].tolist() == counts.tolist()
    assert w.food_fell_counts["injected"].tolist() == [int(counts.sum()), 0, 0, 0]


def test_sham_is_keyed_by_world_and_wey_and_follows_its_rates(parts):
    _, _, v, _ = parts
    rates = (0.2, 0.3)
    cfg = t1("sham", rates)
    a = build(parts, cfg, v, n=3, seed=0, ids=[5, 6, 7])
    b = build(parts, cfg, v, n=3, seed=1, ids=[7, 6, 5])  # other genomes, worlds in another batch order
    sa, sb = [], []
    for _ in range(40):
        a.tick()
        b.tick()
        sa.append(a._ff_state.clone())
        sb.append(b._ff_state.clone())
    for x, y in zip(sa, sb):
        assert torch.equal(x, y.flip(0))  # a pure function of (run seed, world id, tick, swarm, wey)
    big = build(parts, cfg, v, n=64, seed=2)
    on = []
    for _ in range(200):
        big.tick()
        on.append(big._ff_state.clone())
    st = torch.stack(on).reshape(len(on), -1)
    p01 = ((~st[:-1]) & st[1:]).sum() / (~st[:-1]).sum()
    p10 = (st[:-1] & (~st[1:])).sum() / st[:-1].sum()
    assert abs(float(p01) - 0.2) < 0.02 and abs(float(p10) - 0.3) < 0.02
    occ = float(st.float().mean())
    assert abs(occ - 0.2 / 0.5) < 0.03  # the stationary start keeps the occupancy at p01 / (p01 + p10)


def test_sham_injects_its_state_only_for_live_weys(parts):
    _, _, v, _ = parts
    cfg = t1("sham", (0.5, 0.5))
    w = build(parts, cfg, v)
    for _ in range(30):
        alive = w.alive.clone()
        w.tick()
        want = (w._ff_state & alive).to(w.last_signals["food_fell"].dtype)
        assert torch.equal(w.last_signals["food_fell"], want)


def test_inconsistent_settings_are_refused(parts):
    _, pinned, v, _ = parts
    with pytest.raises(ValueError):
        build(parts, t1("relief"), pinned)  # the mode without the channel
    with pytest.raises(ValueError):
        build(parts, t1(None), v)  # the channel without a mode
    with pytest.raises(ValueError):
        build(parts, t1("sham"), v)  # sham without rates
    with pytest.raises(ValueError):
        build(parts, t1("change"), v)


def test_under_level_the_variant_plays_exactly_as_the_pinned_interface(parts):
    """The interface comparison on the current engine, on the CPU: with the bit at 0 the variant injects nothing at
    ASK. Rule 7's comparison against the engine before 03h (all class-E endpoints) is scripts/e03h_equivalence.py, with
    its records in experiments/03h-history-use/development-records/ (Astra)."""
    con, pinned, v, spec = parts
    g = Genome.random(spec, t1().brain, 4, generator=torch.Generator().manual_seed(11))
    ids = np.arange(100, 106)
    base = rollout(t1(None), pinned, g, ids, 7, "cpu")
    lvl = rollout(t1("level"), v, g, ids, 7, "cpu")
    assert np.array_equal(np.asarray(base.score), np.asarray(lvl.score))


@pytest.mark.gpu
def test_under_level_the_variant_plays_exactly_as_the_pinned_interface_on_cuda(parts):
    """The interface comparison on the current engine, on CUDA, in one composition (64 x 16), inside replay_mode().
    The pre-change comparison at the planned composition is scripts/e03h_equivalence.py (Astra)."""
    if not torch.cuda.is_available():
        pytest.skip("no CUDA")
    from wormwars.evo.bundle import replay_mode
    con, pinned, v, _ = parts
    spec = BrainSpec.from_connectome(con, device="cuda")
    g = Genome.random(spec, t1().brain, 64, generator=torch.Generator(device="cuda").manual_seed(11), device="cuda")
    ids = np.arange(100, 116)
    with replay_mode():
        base = rollout(t1(None), pinned, g, ids, 7, "cuda", chunk_worlds=1024)
        lvl = rollout(t1("level"), v, g, ids, 7, "cuda", chunk_worlds=1024)
    assert np.array_equal(np.asarray(base.score), np.asarray(lvl.score))


def _crafted(parts, mode, rates=None, n=2):
    _, _, v, _ = parts
    cfg = t1(mode, rates)
    return build(parts, cfg, v, n=n), cfg


def test_the_bit_reads_the_clamped_current_per_wey_and_skips_the_dead(parts):
    """Astra: two unequal readings that clamp equal give 0; a fall below the clamp gives 1; weys are separate; a death
    between two ticks zeroes the bit and removes the step from the counts."""
    w, cfg = _crafted(parts, "relief", n=1)
    B = w.n_weys
    big = cfg.brain.input_max + 2.0  # above the clamp (sensor gain 1, input gain 1 for food_left)
    seq = np.zeros((5, B))
    seq[:, 0] = [big + 1, big, 1.0, 1.0, 0.5]  # clamp-equal (no fall), a fall below the clamp, equal, a fall
    seq[:, 1] = [0.2, 0.3, 0.1, 0.4, 0.3]      # rise, fall, rise, fall
    seq[:, 2] = [0.5, 0.4, 0.3, 0.2, 0.1]      # falls every tick; dies before tick 3
    alive0 = w.alive.clone()
    bits = []
    for t in range(5):
        if t == 3:
            w.alive[0, 0, 2] = False
        bits.append(_feed_one(w, t, seq[t]))
    b = torch.stack(bits)[:, 0, 0, :3].numpy()
    assert b[:, 0].tolist() == [0, 0, 1, 0, 1]
    assert b[:, 1].tolist() == [0, 0, 1, 0, 1]
    assert b[:, 2].tolist() == [0, 1, 1, 0, 0]
    assert bool(alive0[0, 0, :3].all())
    c = w.food_fell_counts["relief"].tolist()  # steps 1->2, 2->3, 3->4 (t - 1 >= 1), weys alive at both ends
    wey0 = [(0, 1), (1, 0), (0, 1)]
    wey1 = [(0, 1), (1, 0), (0, 1)]
    wey2 = [(1, 1)]  # only 1->2: wey 2 is dead at ticks 3 and 4
    others = B - 3  # constant readings 0: no falls, three steps each
    want = [3 * others, 0, 0, 0]
    for x, y in wey0 + wey1 + wey2:
        want[2 * x + y] += 1
    assert c == want


def _feed_one(w, t, row):
    w.tick_count = t
    food = torch.as_tensor(row, dtype=w.dtype).reshape(1, 1, -1)
    return w._food_fell({"food_left": food}).clone()


def test_a_sham_without_a_stationary_start_is_refused(parts):
    _, _, v, _ = parts
    with pytest.raises(ValueError):
        build(parts, t1("sham", (0.0, 0.0)), v)


def test_the_sham_starts_at_its_stationary_occupancy_on_the_first_tick(parts):
    w, _ = _crafted(parts, "sham", (0.2, 0.3), n=64)
    w.tick()
    first = float(w._ff_state.float().mean())  # 64 worlds x 20 weys on tick 0
    assert abs(first - 0.4) < 0.05


def test_the_pinned_prefix_is_identical_in_neurons_and_gains(parts):
    _, pinned, v, _ = parts
    n = len(pinned.signal_names)
    assert np.array_equal(v.sensor_neuron[:n], pinned.sensor_neuron)
    assert np.array_equal(v.sensor_gain[:n], pinned.sensor_gain)
    for f in ("forward_plus", "forward_minus", "turn_plus", "turn_minus", "pump_neurons"):
        assert np.array_equal(getattr(v, f), getattr(pinned, f))


@pytest.mark.parametrize("mode,rates", [("relief", None), ("sham", (0.2, 0.3))])
def test_the_injected_bit_reaches_ask_and_its_counts_are_its_own(parts, mode, rates):
    """The current actually built at ASKL and ASKR is the injected bit times the amplitude (Astra: an integration
    check through _build_current), and the injected counts are the injected bit's transitions."""
    con, _, v, _ = parts
    cfg = t1(mode, rates)
    w = build(parts, cfg, v)
    ask = [con.index("ASKL"), con.index("ASKR")]
    inj, alive = [], []
    for _ in range(40):
        alive.append(w.alive.clone())
        w.tick()
        bit = w.last_signals["food_fell"]
        cur = w._build_current(w.last_signals)
        for k in ask:
            assert torch.allclose(cur[..., k], bit * AMPLITUDE * alive[-1], atol=0, rtol=0)
        inj.append(bit.bool())
    want = np.zeros(4, dtype=np.int64)
    for t in range(2, len(inj)):
        both = alive[t - 1] & alive[t]
        code = (inj[t - 1].long() * 2 + inj[t].long())[both]
        want += np.bincount(code.numpy(), minlength=4)
    assert w.food_fell_counts["injected"].tolist() == want.tolist()
