"""E3a's memory assays and classes (PREREGISTRATION §6; test 11).

Constructed organisms land in their classes:
- E: bistable, settable both ways, holds: "latch";
- E with w_aq = w_bq = 0: bistable, but the stimulus cannot switch it: "bistable, not a latch";
- a slow monostable trace (τ_q 20, w_qq 0.95, biases −1.55): passes the release test: "slow trace";
- E with w_qq 0 and τ_q 0.5: monostable, forgets at once: "no memory".
The clamp assays and the reset run in the world.
"""

from __future__ import annotations

import numpy as np
import pytest

from wormwars import graft as G
from wormwars.connectome import load_connectome
from wormwars.e3 import assays as A
from wormwars.e3 import organism as O
from wormwars.e3 import probe as P
from wormwars.e3 import samplers as S
from wormwars.e3.task import shuttle_config
from wormwars.e4s import comparator as C
from wormwars.e4s.arms import load_l1

# smoke ids and seed only: the registered blocks are read only by the formal stages (D166)
SMOKE_SEED = 1_179_000


@pytest.fixture(scope="module")
def ctx():
    con, l1, cfg = load_connectome(), load_l1(), shuttle_config()
    e = O.engineered(l1)
    ext = G.graft_connectome(con, e)
    iface = G.graft_interface(ext, e)
    base = C.carrier_genome(ext, e, cfg.brain, forward=1.0, turn=0.2)
    return {"cfg": cfg, "ext": ext, "iface": iface, "pc": P.ProbeContext(ext, iface, cfg), "E": base}


def _variant(ctx, **kw):
    p = S.read_selector(ctx["E"], ctx["ext"])
    for k, v in kw.items():
        if k in ("gate", "bias"):
            for mod in ("A", "B"):
                for side in ("CL", "CR"):
                    name = f"{k}_{mod}_{side}"
                    p[0, S.SELECTOR_INDEX[name]] = (v if mod == "A" else -v) if k == "gate" else v
        else:
            p[0, S.SELECTOR_INDEX[k]] = v
    return S.with_selector(ctx["E"], ctx["ext"], p)


def _classify(ctx, genome, stim=2, D=60):
    sel = S.read_selector(genome, ctx["ext"])[0]
    return A.memory_assays(genome, ctx["pc"], w_qq=sel[S.SELECTOR_INDEX["w_qq"]], b_q=sel[S.SELECTOR_INDEX["b_q"]],
                           tau_q=sel[S.SELECTOR_INDEX["tau_q"]], stim=stim, D=D, assignment=None)


def test_e_is_a_latch(ctx):
    r = _classify(ctx, ctx["E"])
    assert r["structure"] == "bistable" and r["settable"] and r["hold"] and r["class"] == "latch"


def test_a_latch_without_drive_is_bistable_but_not_a_latch(ctx):
    g = _variant(ctx, w_aq=0.0, w_bq=0.0)
    r = _classify(ctx, g)
    assert r["structure"] == "bistable" and not r["settable"] and r["class"] == "bistable, not a latch"
    assert "release" in r  # run descriptively on bistable non-latches


def test_a_slow_trace(ctx):
    g = _variant(ctx, tau_q=20.0, w_qq=0.95, gate=2.0, bias=-1.55)
    r = _classify(ctx, g, stim=8, D=60)
    assert r["structure"] == "monostable" and r["release"] and r["class"] == "slow trace"


def test_no_memory(ctx):
    g = _variant(ctx, tau_q=0.5, w_qq=0.0)
    r = _classify(ctx, g)
    assert r["structure"] == "monostable" and not r["release"] and r["class"] == "no memory"


def test_the_window_scales_with_tau():
    assert A.window(1.0) == 20 and A.window(4.0) == 40 and A.window(2.05) == 21


# ------------------------------------------------------------------ in the world

def test_es_clamp_assays_and_its_assignment(ctx):
    ids = np.arange(0, 16)
    r = A.clamp_assays(ctx["E"], ctx["ext"], ctx["iface"], ctx["cfg"], states=(-O.Q_STAR, O.Q_STAR),
                       world_ids=ids, run_seed=SMOKE_SEED)
    assert r["assignment"] == {"A": O.Q_STAR, "B": -O.Q_STAR}
    assert r["share"]["A"] >= 0.9 and r["share"]["B"] >= 0.9 and r["passed"]


def test_the_assignment_rule():
    # both assignments cannot pass; the passing one wins
    assert A.assign((-1.0, 1.0), {(-1.0, "A"): 0.1, (-1.0, "B"): 0.95, (1.0, "A"): 0.92, (1.0, "B"): 0.05}) == \
        ({"A": 1.0, "B": -1.0}, True)
    # mirrored polarity
    assert A.assign((-1.0, 1.0), {(-1.0, "A"): 0.97, (-1.0, "B"): 0.0, (1.0, "A"): 0.0, (1.0, "B"): 0.96}) == \
        ({"A": -1.0, "B": 1.0}, True)
    # neither passes: the larger summed share; a tie gives the higher state to A
    assert A.assign((-1.0, 1.0), {(-1.0, "A"): 0.5, (-1.0, "B"): 0.5, (1.0, "A"): 0.5, (1.0, "B"): 0.5}) == \
        ({"A": 1.0, "B": -1.0}, False)


def test_not_applicable_clamp_assays_do_not_pass():
    assert A.working(lower_bound=9.0, e_mean=5.0, clamp={"applicable": False, "passed": False}) is False
    assert A.working(lower_bound=4.0, e_mean=5.0, clamp={"applicable": True, "passed": True}) is True
    assert A.working(lower_bound=3.9, e_mean=5.0, clamp={"applicable": True, "passed": True}) is False


def test_es_reset(ctx):
    ids = np.arange(0, 16)
    r = A.reset_test(ctx["E"], ctx["ext"], ctx["iface"], ctx["cfg"], go_to_a=O.Q_STAR, world_ids=ids,
                     run_seed=SMOKE_SEED)
    assert r["eligible"] >= 8 and r["passed"]
    # a world where the write never happens fails: a q pinned at "go to B" cannot be reset
    assert set(r["per_world"]) <= {"passed", "failed", "unwritten", "not eligible"}


def test_calibration_medians_and_stimulus_duration(ctx):
    ids = np.arange(100, 108)
    cal = A.calibrate(ctx["E"], ctx["ext"], ctx["iface"], ctx["cfg"], world_ids=ids, run_seed=SMOKE_SEED)[0]
    assert cal["median_q"]["A"] > 1.5 and cal["median_q"]["B"] < -1.5
    assert cal["stimulus"] >= 1 and cal["pool"] > 0
    assert A.stimulus_from([], fallback=2) == 2
    assert A.stimulus_from([3, 4, 6], fallback=2) == 4 and A.stimulus_from([3, 4], fallback=2) == 4  # half up


def test_the_window_includes_the_stimulus_last_tick(ctx, monkeypatch):
    """§6: W starts at the stimulus's last tick, so a settable run lasts stim + W − 1 ticks."""
    seen = []
    real = A.P._free_run

    def spy(genome, pc, state, ticks, relay, stim, m=0.05):
        seen.append((ticks, stim))
        return real(genome, pc, state, ticks, relay, stim, m)

    monkeypatch.setattr(A.P, "_free_run", spy)
    A.memory_assays(ctx["E"], ctx["pc"], w_qq=2.0, b_q=0.0, tau_q=1.0, stim=3, D=10, assignment=None)
    assert (3 + 20 - 1, 3) in seen  # settable
    assert (3 + 20 - 1 + 580, 3) in seen  # the hold


def test_latches_also_report_the_release_test(ctx):
    r = _classify(ctx, ctx["E"])
    assert r["class"] == "latch" and "release_detail" in r


def test_calibration_runs_strains_together_and_matches_one_by_one(ctx):
    from wormwars.brain import Genome
    ids = np.arange(200, 204)
    two = Genome.cat([ctx["E"], _variant(ctx, tau_q=0.5, w_qq=0.0)])
    both = A.calibrate(two, ctx["ext"], ctx["iface"], ctx["cfg"], world_ids=ids, run_seed=SMOKE_SEED)
    one = A.calibrate(ctx["E"], ctx["ext"], ctx["iface"], ctx["cfg"], world_ids=ids, run_seed=SMOKE_SEED)
    assert len(both) == 2 and both[0]["median_q"] == pytest.approx(one[0]["median_q"], abs=1e-5)
    assert both[0]["durations"] == one[0]["durations"]


def test_the_hysteresis_sweep_switches_e_both_ways(ctx):
    h = A.hysteresis(ctx["E"], ctx["pc"], w_qq=2.0, b_q=0.0)
    assert h["q_after_a_ramp"] > 1.5 and h["q_after_b_ramp"] < -1.5
    assert h["a_crossing_drive"] is not None and h["b_crossing_drive"] is not None


def test_the_per_tick_traces(ctx):
    from wormwars.brain import Genome
    ids = np.arange(300, 303)
    tr = A.traces(Genome.cat([ctx["E"], ctx["E"]]), ctx["ext"], ctx["iface"], ctx["cfg"], world_ids=ids,
                  run_seed=SMOKE_SEED, ticks=40)
    assert set(tr) == {"q", "ra", "rb", "u", "contribution_A", "contribution_B"}
    assert tr["q"].shape == (2, 3, 40) and tr["q"].dtype == np.float32
    assert np.array_equal(tr["q"][0], tr["q"][1])
    assert tr["rb"][0, :, 2].min() > 0.5  # the cue drives RB in the first ticks
    # E's two modules never push together: one is saturated, so one contribution is near 0
    small = np.minimum(np.abs(tr["contribution_A"]), np.abs(tr["contribution_B"]))
    assert float(small[:, :, 20:].max()) < 0.1
