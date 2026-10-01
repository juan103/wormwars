"""E4s-1's script (`scripts/e4s1.py`) against its bound pre-registration (D150): world ranges, the batch
plan, the arms' generation 0, G2's inputs and current, the end-of-run assertions, and the stage frame."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from wormwars import graft as G
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.e1 import task as T
from wormwars.e4s import arms as A
from wormwars.exp02 import grid as GRID

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def mod():
    s = importlib.util.spec_from_file_location("e4s1_under_test", ROOT / "scripts" / "e4s1.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_the_world_ranges_are_disjoint_from_each_other_and_every_earlier_range(mod):
    e4s0 = importlib.util.spec_from_file_location("e4s0_ranges", ROOT / "scripts" / "e4s0.py")
    m0 = importlib.util.module_from_spec(e4s0)
    e4s0.loader.exec_module(m0)
    earlier = [(0, 10_000), (900_000_000, 901_000_000), (950_000_000, 951_000_000), (960_000_000, 961_000_000),
               (970_000_000, 971_000_000), (980_000_000, 981_000_000), (990_000_000, 991_000_000),
               (992_700_000, 993_000_000), (993_000_000, 995_000_000), (995_000_000, 996_000_000),
               (996_000_000, 1_000_000_000)]
    earlier += [(int(r[0]), int(r[-1]) + 1) for r in (T.PILOT_IDS, T.TUNING_IDS, T.GATE_IDS, T.HOLDOUT_04A_IDS,
                                                       GRID.CHECKPOINT_IDS, GRID.GATE_IDS, GRID.PROBE_IDS)]
    earlier += list(m0.formal_ranges().values())
    mine = list(mod.formal_ranges().values())
    s = sorted(mine)
    for (a0, a1), (b0, b1) in zip(s, s[1:]):
        assert a1 <= b0, (a0, a1, b0, b1)
    for m0_, m1_ in mine:
        for e0, e1 in earlier:
            assert m1_ <= e0 or e1 <= m0_, ((m0_, m1_), (e0, e1))


def test_the_batch_plan_is_the_registered_one(mod):
    assert [a for a, _ in mod.BATCHES] == ["M", "N", "R", "M", "N", "R", "F0", "U", "S", "C2"]
    assert mod.BATCHES[0][1] == list(range(8)) and mod.BATCHES[3][1] == list(range(8, 16))
    assert mod.run_seed("M", 3) == mod.run_seed("N", 3) == mod.run_seed("R", 3) == 1_160_003
    assert mod.run_seed("C2", 3) == 1_166_003
    assert mod.STAGES[:5] == ["project", "gate-1", "gate-2", "gate-3", "r-draws"] and mod.STAGES[-2:] == [
        "eval-endpoints", "eval-training"]


def test_the_arms_generation0_share_the_background_and_differ_only_in_the_module(mod):
    cfg = Config()
    cx = mod.context(cfg)
    m = mod.initial("M", 2, cx, cfg, 4)
    n = mod.initial("N", 2, cx, cfg, 4)
    r = mod.initial("R", 2, cx, cfg, 4)
    _, _, me, _, mn = A._masks(cx["ext"])
    for other in (n, r):
        assert torch.equal(m.w[:, ~me], other.w[:, ~me]) and torch.equal(m.tau[:, ~mn], other.tau[:, ~mn])
    out = A.output_edge_mask(cx["ext"], cx["l1"])
    assert float(n.w[:, out].abs().max()) == 0.0 and float(m.w[:, out].abs().min()) == 3.0
    assert not torch.equal(m.w[:, me], r.w[:, me])


def test_g2_inputs_are_seeded_shared_and_injected_as_the_world_does(mod):
    con = load_connectome()
    from wormwars.interface import load_interface
    iface = load_interface(con)
    order, X = mod.g2_inputs(iface)
    assert X.shape == (300, len(order)) and order == list(dict.fromkeys(iface.signal_names))
    np.testing.assert_array_equal(X, np.random.default_rng(1_168_000).uniform(0, 0.35, size=X.shape))
    bcfg = Config().brain
    cur = mod.g2_current(iface, X[0], con.n, bcfg, "cpu")
    for s, n, g in zip(iface.signal_names, iface.sensor_neuron, iface.sensor_gain):
        if s == "food_left":
            assert float(cur[int(n)]) == pytest.approx(min(float(X[0][order.index(s)]) * float(g) * bcfg.input_gain,
                                                            bcfg.input_max), abs=1e-6)


def test_the_end_of_run_assertions_flag_what_they_should(mod):
    cfg = Config()
    cx = mod.context(cfg)
    ext, l1 = cx["ext"], cx["l1"]
    n0 = mod.initial("N", 0, cx, cfg, 3)
    rec = SimpleNamespace(final=n0, candidates=[n0.select([0])])
    assert mod.check_assertions("N", rec, ext, l1) == []
    bad = n0.clone()
    out = A.output_edge_mask(ext, l1)
    w = bad.w.clone()
    w[1, out.nonzero()[0]] = 0.01
    rec_bad = SimpleNamespace(final=bad.with_params(w=w), candidates=[n0.select([0])])
    assert mod.check_assertions("N", rec_bad, ext, l1)
    f0 = mod.initial("F0", 0, cx, cfg, 3)
    assert mod.check_assertions("F0", SimpleNamespace(final=f0, candidates=[f0.select([1])]), ext, l1) == []
    drift = f0.with_params(tau=f0.tau.clone())
    drift.tau[0, ext.index("E4S_CL")] = 0.6
    assert mod.check_assertions("F0", SimpleNamespace(final=drift, candidates=[]), ext, l1)


def test_the_stage_frame_is_e4s1s(mod):
    assert mod.E.EXP == mod.EXP and mod.E.OUT == mod.OUT and mod.E.REGISTERED is mod.REGISTERED
    assert mod.E.record_path("gate-1").parent == mod.EXP and mod.E.clock().cap_hours == 24.0
    assert mod.D2.E is not mod.E
    assert G.MODULES.get("comparator-L1") is not None or A.load_l1()
