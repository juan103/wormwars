"""E3a's samplers and mutation masks (PREREGISTRATION §7; tests 12, 13, 21).

- The selector's 13 parameters, in a fixed order; the GA's and random sampling's distributions, tied
  per module in the draw only.
- B-task's mask (121 internal edges among the 11 neurons, 32 output edges) and its draw, with the full
  within-pair blocks, so generation 0 adds no turn at zero nose difference.
- The mutation masks: Stage 2 (the 13 at 1), Stage 3 (the grafted neurons' existing edges, τ and biases
  except the relays' τ and bias, at 0.25), B-task (its 153 edges and 9 non-relay neurons at 1).
"""

from __future__ import annotations

import numpy as np
import pytest
import torch

from wormwars import graft as G
from wormwars.brain import Brain
from wormwars.connectome import load_connectome
from wormwars.e3 import organism as O
from wormwars.e3 import samplers as S
from wormwars.e3.task import shuttle_config
from wormwars.e4s import comparator as C
from wormwars.e4s.arms import load_l1
from wormwars.interface import load_interface  # noqa: F401


@pytest.fixture(scope="module")
def ctx():
    con, l1, cfg = load_connectome(), load_l1(), shuttle_config()
    e = O.engineered(l1)
    ext = G.graft_connectome(con, e)
    return {"con": con, "l1": l1, "cfg": cfg, "e": e, "ext": ext, "iface": G.graft_interface(ext, e),
            "base": C.carrier_genome(ext, e, cfg.brain, forward=1.0, turn=0.2)}


def _turn_at_equal_noses(genome, ext, iface, cfg, m=0.1, ticks=60):
    noses = [ext.index(n) for n in ext.names if n.endswith(("_NL", "_NR"))]
    brain = Brain(genome)
    v = brain.initial_state(1)
    cur = torch.zeros(genome.n_strains, 1, ext.n)
    cur[..., noses] = m
    for _ in range(ticks):
        v = brain.step(v, cur)
    _, u = C.motor_commands(v, iface, cfg)
    return u.reshape(-1)


def test_the_ga_draw_is_tied_per_module_and_in_range():
    p = S.ga_draw(np.random.default_rng(1_172_000), 500)
    assert p.shape == (500, 13)
    i = S.SELECTOR_INDEX
    for a, b in (("gate_A_CL", "gate_A_CR"), ("gate_B_CL", "gate_B_CR"), ("bias_A_CL", "bias_A_CR"), ("bias_B_CL", "bias_B_CR")):
        assert np.array_equal(p[:, i[a]], p[:, i[b]])
    for k in ("w_qq", "w_aq", "w_bq", "gate_A_CL", "gate_B_CL"):
        assert np.all(np.abs(p[:, i[k]]) <= 0.5)
    for k in ("b_q", "bias_A_CL", "bias_B_CL"):
        assert np.all(np.abs(p[:, i[k]]) <= 2.0)
    assert np.all((p[:, i["tau_q"]] >= 0.5) & (p[:, i["tau_q"]] <= 20.0))
    assert np.array_equal(p, S.ga_draw(np.random.default_rng(1_172_000), 500))


def test_the_random_sampling_draw_spans_the_bounds():
    p = S.rs_draw(np.random.default_rng(1_173_000), 4000)
    i = S.SELECTOR_INDEX
    assert np.array_equal(p[:, i["gate_A_CL"]], p[:, i["gate_A_CR"]])
    assert np.abs(p[:, i["w_qq"]]).max() > 2.9 and np.abs(p[:, i["w_qq"]]).max() <= 3.0
    assert np.abs(p[:, i["bias_B_CL"]]).max() > 1.9 and np.abs(p[:, i["bias_B_CL"]]).max() <= 2.0


def test_selector_parameters_round_trip_and_leave_the_rest_of_e(ctx):
    p = S.ga_draw(np.random.default_rng(5), 4)
    g = S.with_selector(ctx["base"], ctx["ext"], p)
    assert g.n_strains == 4
    assert np.allclose(S.read_selector(g, ctx["ext"]), p, atol=1e-6)
    e = S.read_selector(ctx["base"], ctx["ext"])[0]
    assert e[S.SELECTOR_INDEX["w_qq"]] == 2.0 and e[S.SELECTOR_INDEX["bias_A_CL"]] == pytest.approx(-1.914)
    mask = S.selector_masks(ctx["ext"])
    for key, base, new in (("w", ctx["base"].w[0], g.w[3]), ("tau", ctx["base"].tau[0], g.tau[3]), ("bias", ctx["base"].bias[0], g.bias[3])):
        assert torch.equal(base[~mask[key]], new[~mask[key]])


def test_generation_zero_adds_no_turn_at_equal_noses(ctx):
    p = S.ga_draw(np.random.default_rng(9), 16)
    g = S.with_selector(ctx["base"], ctx["ext"], p)
    u = _turn_at_equal_noses(g, ctx["ext"], ctx["iface"], ctx["cfg"])
    assert torch.allclose(u, torch.full_like(u, 0.2), atol=1e-5)  # the carrier's turn only


def test_the_stage_two_mask_mutates_only_the_selector(ctx):
    sc = S.stage2_scales(ctx["ext"])
    m = S.selector_masks(ctx["ext"])
    assert int((sc["w"] != 0).sum()) == 7 and int((sc["bias"] != 0).sum()) == 5 and int((sc["tau"] != 0).sum()) == 1
    for k in ("w", "tau", "bias"):
        assert torch.equal(sc[k] != 0, m[k]) and torch.all(sc[k][m[k]] == 1.0)
    assert torch.all(sc["g"] == 0)


def test_the_stage_three_mask(ctx):
    ext = ctx["ext"]
    sc = S.stage3_scales(ext)
    n0 = int(ext.meta["worm_neurons"])
    assert torch.all(sc["tau"][:n0] == 0) and torch.all(sc["bias"][:n0] == 0)
    for r in O.RELAYS:
        assert sc["tau"][ext.index(r)] == 0 and sc["bias"][ext.index(r)] == 0
    assert sc["tau"][ext.index("E3_Q")] == 0.25 and sc["bias"][ext.index("E3_A_NL")] == 0.25
    from wormwars.brain import BrainSpec
    spec = BrainSpec.from_connectome(ext)
    grafted = (spec.chem_i >= n0) | (spec.chem_j >= n0)
    assert torch.all(sc["w"][grafted] == 0.25) and torch.all(sc["w"][~grafted] == 0)
    assert int(grafted.sum()) == 47


def test_b_task_has_the_full_mask(ctx):
    m = S.b_task_module(ctx["l1"])
    ext = G.graft_connectome(ctx["con"], m)
    n0 = int(ext.meta["worm_neurons"])
    grafted = [ext.index(n) for n in m.neurons]
    internal = sum(int(ext.chem[i, j]) for i in grafted for j in grafted)
    outputs = sum(int(ext.chem[i, j]) for i in grafted for j in range(n0))
    assert internal == 121 and outputs == 32


def test_b_task_draws_keep_the_pairs_symmetric_and_add_no_turn(ctx):
    m = S.b_task_module(ctx["l1"])
    ext = G.graft_connectome(ctx["con"], m)
    iface = G.graft_interface(ext, m)
    g = S.b_task_draw(np.random.default_rng(1_175_000), ext, m, ctx["cfg"].brain, 8)
    idx = ext.index
    w = {}
    from wormwars.brain import BrainSpec
    spec = BrainSpec.from_connectome(ext)
    for p, (i, j) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist())):
        w[(ext.names[i], ext.names[j])] = g.w[:, p]
    for mod in ("A", "B"):
        nl, nr, cl, cr = (f"E3_{mod}_{s}" for s in ("NL", "NR", "CL", "CR"))
        assert torch.equal(g.tau[:, idx(nl)], g.tau[:, idx(nr)]) and torch.equal(g.bias[:, idx(cl)], g.bias[:, idx(cr)])
        assert torch.equal(w[(nl, nl)], w[(nr, nr)]) and torch.equal(w[(nl, nr)], w[(nr, nl)])
        assert torch.equal(w[(cl, cl)], w[(cr, cr)]) and torch.equal(w[(cl, cr)], w[(cr, cl)])
        assert torch.equal(w[(nl, cl)], -w[(nl, cr)]) and torch.equal(w[(nl, cl)], -w[(nr, cl)])
        assert torch.equal(w[("E3_Q", nl)], w[("E3_Q", nr)]) and torch.equal(w[("E3_Q", cl)], w[("E3_Q", cr)])
        assert torch.equal(w[(cl, "SMDDL")], -w[(cr, "SMDDL")])
    for r in O.RELAYS:
        assert torch.all(g.tau[:, idx(r)] == 0.5) and torch.all(g.bias[:, idx(r)] == 0.0)
    u = _turn_at_equal_noses(g, ext, iface, ctx["cfg"])
    assert torch.allclose(u, torch.full_like(u, 0.2), atol=1e-5)


def test_b_task_scales(ctx):
    m = S.b_task_module(ctx["l1"])
    ext = G.graft_connectome(ctx["con"], m)
    sc = S.b_task_scales(ext)
    assert int((sc["w"] != 0).sum()) == 153
    assert int((sc["tau"] != 0).sum()) == 9 and int((sc["bias"] != 0).sum()) == 9
    for r in O.RELAYS:
        assert sc["tau"][ext.index(r)] == 0
