"""E4s-0's script (`scripts/e4s0.py`; docs/E4s/E4s-0-PLAN.md v2): its world ranges, the ladder's
search and grids, its stage frame and imported rules, the module probes, and the projection's
shrink order."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from wormwars import graft as G
from wormwars.connectome import load_connectome
from wormwars.e1 import task as T
from wormwars.e4s import comparator as C
from wormwars.exp02 import grid as GRID

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def mod():
    s = importlib.util.spec_from_file_location("e4s0_under_test", ROOT / "scripts" / "e4s0.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def test_the_formal_ranges_are_disjoint_from_each_other_and_every_earlier_range(mod):
    earlier = [(0, 10_000), (900_000_000, 901_000_000),  # smoke; the default hold-out seeds
               (950_000_000, 951_000_000), (960_000_000, 961_000_000), (970_000_000, 971_000_000),
               (980_000_000, 981_000_000),  # 02's checkpoint, ..., gate and probe ids
               (990_000_000, 991_000_000),  # 03's timing ids (E2's code review)
               (992_700_000, 993_000_000), (993_000_000, 995_000_000)]
    earlier += [(995_000_000, 996_000_000), (996_000_000, 1_000_000_000)]  # E2's ranges; E1's, 04a's and above
    earlier += [(int(r[0]), int(r[-1]) + 1) for r in
                                                  (T.PILOT_IDS, T.TUNING_IDS, T.GATE_IDS, T.HOLDOUT_04A_IDS)]
    earlier += [(int(GRID.CHECKPOINT_IDS[0]), int(GRID.CHECKPOINT_IDS[-1]) + 1),
                (int(GRID.GATE_IDS[0]), int(GRID.GATE_IDS[-1]) + 1), (int(GRID.PROBE_IDS[0]), int(GRID.PROBE_IDS[-1]) + 1)]
    mine = list(mod.formal_ranges().values())
    spans = sorted(mine)
    for (a0, a1), (b0, b1) in zip(spans, spans[1:]):
        assert a1 <= b0, ("overlap within E4s-0", a0, a1, b0, b1)
    for m0, m1 in mine:
        for e0, e1 in earlier:
            assert m1 <= e0 or e1 <= m0, ((m0, m1), (e0, e1))
    sel = [mod.selection_ids(i) for i in range(16)]
    assert len(set(np.concatenate(sel).tolist())) == 16 * 8


def test_the_ladder_grids_and_their_order(mod):
    sizes = {s: len(mod.ladder_grid(s, {"step": "L3", "w_m": -0.8})) for s in mod.LADDER_STEPS}
    assert sizes == {"L1": 216, "L2": 648, "L3": 648, "L4x2": 216, "L4x4": 216}
    g = mod.ladder_grid("L2")
    assert g[0]["w_s"] == 0.5 and g[-1]["w_s"] == 0.95 and g[0]["w_n"] == 1.0 and g[1]["turn"] == 0.1
    l4 = mod.ladder_grid("L4x2", {"step": "L3", "w_m": -0.8, "w_n": 9})
    assert all(c["w_m"] == -0.8 and c["base"] == "L3" for c in l4) and {c["w_n"] for c in l4} == {1.0, 2.0, 3.0}
    assert mod.take_best([1.0, 3.0, 3.0, 2.0], 2) == [1, 2]  # ties to the first in grid order
    m = mod.module_of(l4[0])
    assert len(m.neurons) == 6


def test_the_ladder_stops_at_the_first_qualifying_step_and_each_step_reads_its_own_worlds(mod):
    seen, calls = [], {"base": 0}

    def evaluate(s, step, cands):
        seen.append((s, step, tuple(mod.ladder_ids(s, "tune")[:2])))
        return {**cands[0], "tag": step}

    def base_select(finalists):
        calls["base"] += 1
        assert [f["tag"] for f in finalists] == ["L1", "L2", "L3"]
        return finalists[1]

    out = mod.ladder_search(evaluate, lambda s, c: (c["tag"] == "L2", {}), base_select)
    assert out["qualified"]["tag"] == "L2" and [a["step"] for a in out["attempts"]] == ["L1", "L2"]
    out = mod.ladder_search(evaluate, lambda s, c: (c["tag"] == "L4x4", {}), base_select)
    assert [a["step"] for a in out["attempts"]] == mod.LADDER_STEPS and calls["base"] == 1
    assert out["attempts"][4]["base"]["tag"] == "L2"
    out = mod.ladder_search(evaluate, lambda s, c: (False, {}), base_select)
    assert out["qualified"] is None
    ids = {(s, w): tuple(mod.ladder_ids(s, w)) for s in range(5) for w in ("tune", "rescore", "qual")}
    flat = [i for v in ids.values() for i in v]
    assert len(flat) == len(set(flat))


def test_the_stage_frame_is_e4s0s_and_the_rules_are_e2ds(mod):
    assert mod.E.EXP == mod.EXP and mod.E.OUT == mod.OUT and mod.E.REGISTERED is mod.REGISTERED
    assert mod.E.record_path("sweep").parent == mod.EXP
    assert mod.D2.E is not mod.E and mod.D2.E.EXP == mod.D2.EXP != mod.EXP
    assert mod.D2.REGISTERED["analysis"]["resamples"] == 10_000 and mod.D2.REGISTERED["analysis"]["seed"] == 0
    assert mod.REGISTERED["cap_gpu_hours"] == 2.0 and mod.E.clock().cap_hours == 2.0


def test_the_module_probes_change_only_the_noses_currents():
    con = load_connectome()
    m = C.comparator("L1", w_n=1, w_o=1, tau=0.5, bias=0.0)
    ext = G.graft_connectome(con, m)
    sig = {"food_left": 0.3, "food_right": 0.1}

    def current(probe):
        iface = G.graft_interface(ext, m, probe=probe)
        cur = np.zeros(ext.n)
        for s, n, g in zip(iface.signal_names, iface.sensor_neuron, iface.sensor_gain):
            cur[int(n)] += sig.get(s, 0.0) * float(g)
        return cur

    real, mean, swapped = current("real"), current("mean"), current("swapped")
    np.testing.assert_array_equal(real[:con.n], mean[:con.n])
    np.testing.assert_array_equal(real[:con.n], swapped[:con.n])
    nl, nr = ext.index("E4S_NL"), ext.index("E4S_NR")
    assert (real[nl], real[nr]) == (0.3, 0.1)
    assert mean[nl] == pytest.approx(0.2) and mean[nr] == pytest.approx(0.2)
    assert (swapped[nl], swapped[nr]) == (0.1, 0.3)


def test_the_projection_shrinks_in_order_and_never_grows(mod):
    fast = {s: 1e9 for s in ("sweep", "sweep_small", "tuning", "tuning_small", "rescore", "base_rescore",
                             "qualification", "selection", "g0", "backgrounds", "backgrounds_small", "robustness",
                             "robustness_parent")}
    sizes, hours, within = mod.freeze_sizes(fast, 0.0)
    assert within and sizes == {"populations.bg_worlds": 64, "ladder.tune_worlds": 128, "sweep.worlds": 512}
    # the non-rollout work counts: an hour of it alone forces every shrink and still does not fit
    sizes, _, within = mod.freeze_sizes(fast, 0.0, lambda R: {"ladder": 7000.0})
    assert not within and sizes["sweep.worlds"] == 256
    # a shrunk size is priced at its own measured composition
    R = mod.copy.deepcopy(mod.REGISTERED)
    R["sweep"]["worlds"] = 256
    assert "sweep_small" in mod.stage_episodes(R)["sweep"] and "sweep" not in mod.stage_episodes(R)["sweep"]
    eps = mod.stage_episodes(mod.REGISTERED)
    total = sum(sum(v.values()) for v in eps.values())
    assert 0.75e6 < total < 0.9e6  # the plan's about 0.82 M
    # slow enough that only the first shrink is needed
    rate = sum(sum(v.values()) for v in eps.values()) / (1.79 * 3600)
    slow = {k: rate for k in fast}
    sizes, _, within = mod.freeze_sizes(slow, 0.02)
    assert within and sizes["populations.bg_worlds"] == 32 and sizes["ladder.tune_worlds"] == 128
    sizes, _, within = mod.freeze_sizes({k: 1.0 for k in fast}, 0.0)
    assert not within and sizes == {"populations.bg_worlds": 32, "ladder.tune_worlds": 64, "sweep.worlds": 256}


def test_rescore_ties_go_to_the_first_in_grid_order(mod):
    """`top` is in screening order; a tie on the re-score goes to the lower grid index (Astra)."""
    assert mod.rescore_choice([1, 0], [5.0, 5.0]) == 0
    assert mod.rescore_choice([3, 7, 2], [4.0, 6.0, 6.0]) == 2
    assert mod.rescore_choice([3, 7, 2], [9.0, 6.0, 6.0]) == 3


def test_generation0_selection_reads_the_selection_worlds(mod):
    """Scores that depend on the world: on selection worlds strain 1 of each population wins, on any
    other world strain 0 does. The production routing must pick strain 1."""
    sel_all = set(np.concatenate([mod.selection_ids(i) for i in range(16)]).tolist())

    def fake_play(ids2d):
        ids2d = np.asarray(ids2d)
        score = np.zeros(ids2d.shape)
        on_sel = np.isin(ids2d, list(sel_all))
        strain = np.arange(ids2d.shape[0])[:, None] % 4
        score[(strain == 1) & on_sel] = 3.0
        score[(strain == 0) & ~on_sel] = 5.0
        return score

    ids = mod.population_selection_ids(3, 4)
    assert ids.shape == (12, 8)
    for s in range(12):
        np.testing.assert_array_equal(ids[s], mod.selection_ids(s // 4))
    np.testing.assert_array_equal(mod.pick_g0(fake_play, 3, 4), [1, 1, 1])


def test_mutants_are_paired_across_scales_and_differ_across_j(mod):
    con = load_connectome()
    m = C.comparator("L1", w_n=1.5, w_o=1.5, tau=2.0, bias=0.0)
    ext = G.graft_connectome(con, m)
    from wormwars.config import Config
    cfg = Config()
    parent = C.carrier_genome(ext, m, cfg.brain, forward=1.0, turn=0.1)
    a = mod.mutants(parent, ext, cfg.mutation, 0.25, 3, 1_151_000)
    b = mod.mutants(parent, ext, cfg.mutation, 1.0, 3, 1_151_000)
    i, j = ext.index("E4S_NL"), ext.index("E4S_CL")
    W0, _ = parent.dense()
    Wa, _ = a.dense()
    Wb, _ = b.dense()
    da, db = Wa[:, i, j] - W0[0, i, j], Wb[:, i, j] - W0[0, i, j]
    np.testing.assert_allclose(da.numpy(), 0.25 * db.numpy(), rtol=1e-4, atol=1e-6)  # the same draws
    assert len({float(x) for x in db}) == 3  # mutant j's draws differ across j


def test_the_robustness_reading(mod):
    assert mod.robustness_reading(0.0, 0.9, 0.9)["fallback"] == "undefined (the parent scores 0)"
    assert mod.robustness_reading(5.0, 0.6, 0.4)["fallback"] == "0.125x"
    assert mod.robustness_reading(5.0, 0.6, 0.7)["fallback"] == "0.25x"
    assert mod.robustness_reading(5.0, 0.3, 0.2)["fallback"] == "neither scale keeps half: not drawn"
    assert mod.robustness_shares(np.array([[1.0, 2.0]]), 0.0) is None


def test_parameters_on_the_genomes_bounds_are_named(mod):
    from wormwars.config import Config
    b = mod.on_bounds({"w_n": 3.0, "w_o": 2.0, "tau": 0.5, "bias": 0.0, "w_m": -0.8}, Config().brain)
    assert set(b) == {"w_n", "tau"}
