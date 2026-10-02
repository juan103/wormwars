"""E3a's probe and component tests (PREREGISTRATION §6; tests 8 and 9).

The probe: open loop on the carrier, from a copy of the state under test, with q, RA and RB held at
their saved values; both modules' noses at m, the probed module's L = m + d/2 and R = m − d/2,
d = ±0.001; 50 ticks, then u averaged over 10 more; K_D = (u(+d) − u(−d)) / 0.002.
"""

from __future__ import annotations

import pytest
import torch

from wormwars import graft as G
from wormwars.connectome import load_connectome
from wormwars.e3 import organism as O
from wormwars.e3 import probe as P
from wormwars.e3.task import shuttle_config
from wormwars.e4s import comparator as C
from wormwars.e4s.arms import load_l1


@pytest.fixture(scope="module")
def ctx():
    con, l1, cfg = load_connectome(), load_l1(), shuttle_config()
    e = O.engineered(l1)
    ext = G.graft_connectome(con, e)
    iface = G.graft_interface(ext, e)
    pc = P.ProbeContext(ext, iface, cfg)
    return {"l1": l1, "cfg": cfg, "ext": ext, "iface": iface, "pc": pc, "con": con,
            "E": C.carrier_genome(ext, e, cfg.brain, forward=1.0, turn=0.2),
            "no_latch": C.carrier_genome(ext, O.no_latch(l1), cfg.brain, forward=1.0, turn=0.2)}


def test_the_probe_holds_q_and_leaves_the_state_under_test_unchanged(ctx):
    pc = ctx["pc"]
    state = pc.latch_state(ctx["E"], 0.5)
    before = state.clone()
    k, final = P.k_d(ctx["E"], pc, "A", 0.05, state, return_final=True)
    assert torch.equal(state, before)
    assert float(final[0, 0, pc.q]) == 0.5 and float(final[0, 0, pc.ra]) == 0.0


def test_e_steers_with_the_module_its_latch_selects(ctx):
    pc = ctx["pc"]
    up, down = pc.latch_state(ctx["E"], O.Q_STAR), pc.latch_state(ctx["E"], -O.Q_STAR)
    ka, kb = P.k_d(ctx["E"], pc, "A", 0.05, up), P.k_d(ctx["E"], pc, "B", 0.05, up)
    assert float(ka) > 30 and abs(float(kb)) < 0.3
    ka, kb = P.k_d(ctx["E"], pc, "A", 0.05, down), P.k_d(ctx["E"], pc, "B", 0.05, down)
    assert float(kb) > 30 and abs(float(ka)) < 0.3


def test_e_passes_every_component_test(ctx):
    res = P.component_tests(ctx["E"], ctx["pc"], states={"A": O.Q_STAR, "B": -O.Q_STAR})
    assert res["passed"], res
    for key in ("active", "inactive", "offset", "switching", "startup"):
        assert res[key]["passed"], key


def test_the_sabotaged_gate_fails_the_inactive_limit(ctx):
    """Test 9's sabotage: with the gate edges (and the bias shift) at 0, both modules steer, so the
    inactive module's K_D far exceeds 0.3."""
    res = P.component_tests(ctx["no_latch"], ctx["pc"], states={"A": O.Q_STAR, "B": -O.Q_STAR})
    assert not res["inactive"]["passed"] and not res["passed"]


def test_the_offset_test_is_two_sided(ctx):
    assert P.offset_passes(0.0, 0.019) and P.offset_passes(0.0, -0.019)
    assert not P.offset_passes(0.0, -0.5) and not P.offset_passes(0.1, -0.1)
