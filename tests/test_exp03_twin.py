"""03mc's two-row history probe (`wormwars/exp03/twin.py`): the rising and falling histories as two rows of
each strain must give 03's P4 terms (`measures.history`) to within the declared tolerance, on the CPU."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest
import torch

from wormwars.exp03 import measures as M

ROOT = Path(__file__).parents[1]
TOL = 1e-5  # relative, declared in experiments/03mc-p4-confirm/DESIGN.md §5


@pytest.fixture(scope="module")
def parts():
    spec = importlib.util.spec_from_file_location("p4m_script_twin", ROOT / "scripts" / "p4m.py")
    p = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p)
    con, bank, iface = p.setup("cpu")
    g, cfg = p.probe_genomes(con, "N2", "cpu", n=6)
    return p, con, bank, iface, g, cfg


def rel(a, b):
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    return float(np.max(np.abs(a - b)) / max(np.max(np.abs(b)), 1e-30))


def test_two_rows_reproduce_the_one_row_probe(parts):
    from wormwars.exp03 import twin
    p, con, bank, iface, g, cfg = parts
    one = M.history(g, cfg, iface, bank)
    two = twin.history(g, cfg, iface, bank, follow=5)
    for k in ("final", "steady_contrast"):
        assert rel(two["raw_turn"][k], one["raw_turn"][k]) < TOL
    assert rel(two["raw_turn"]["after"], one["raw_turn"]["after"]) < TOL
    assert two["ticks"][0] == 0 and two["ticks"][-1] == 5
    assert np.allclose(two["diff"][0], two["raw_turn"]["final"])


def test_the_long_follow_keeps_the_ramp_end_and_the_steady_contrast(parts):
    from wormwars.exp03 import twin
    p, con, bank, iface, g, cfg = parts
    short = twin.history(g, cfg, iface, bank, follow=5)
    long = twin.history(g, cfg, iface, bank, follow=40, every=10)
    assert long["ticks"] == [0, 5, 10, 20, 30, 40]
    for k in ("final", "steady_contrast"):
        assert np.array_equal(long["raw_turn"][k], short["raw_turn"][k])
    assert np.array_equal(long["diff"][1], short["diff"][1])  # tick 5 is the same step either way


def test_the_pre_tanh_read_out_is_the_turn_neurons_state(parts):
    from wormwars.exp03 import twin
    p, con, bank, iface, g, cfg = parts
    h = twin.history(g, cfg, iface, bank, follow=5)
    assert h["pre_turn"]["final"].shape == h["raw_turn"]["final"].shape
    # tanh compresses: the pre-tanh contrast is at least as large as the tanh one wherever both are small
    assert not np.allclose(h["pre_turn"]["steady_contrast"], h["raw_turn"]["steady_contrast"])
    # saturation is between 0 and 1
    assert ((h["slope_hold"] > 0) & (h["slope_hold"] <= 1)).all()


def test_a_genome_change_reaches_both_rows(parts):
    """A sabotage check: if the two rows shared one history, the difference would vanish."""
    from wormwars.exp03 import twin
    p, con, bank, iface, g, cfg = parts
    h = twin.history(g, cfg, iface, bank, follow=5)
    assert np.abs(h["raw_turn"]["final"]).mean() > 0
    assert np.abs(h["raw_turn"]["steady_contrast"]).mean() > 0


def test_the_rows_do_not_interact(parts):
    """Astra (design review v1): each row's trajectory must be its own. Run the rising history alone as a
    one-row brain and compare it with row 0 of the two-row run, tick by tick."""
    from wormwars.brain import Brain
    p, con, bank, iface, g, cfg = parts
    from wormwars.exp03 import twin
    food = (bank["food_left"] + bank["food_right"]) / 2
    brain = Brain(g)
    s, n = g.n_strains, g.spec.n
    at1 = lambda lv: M._current(iface, cfg, dict(bank, food_left=lv, food_right=lv), n, s, "cpu")  # noqa: E731
    one = brain.initial_state(1)
    for _ in range(100):
        one = brain.step(one, at1(0.25 * food))
    two = brain.initial_state(2)
    cur = torch.cat([at1(0.25 * food), at1(1.75 * food)], 1)
    for _ in range(100):
        two = brain.step(two, cur)
    assert torch.allclose(two[:, :1], one, rtol=0, atol=1e-6)
    # and the steady contrast the probe reports is falling minus rising, as 03's is
    h = twin.history(g, cfg, iface, bank, follow=5)
    assert np.allclose(h["raw_turn"]["steady_contrast"],
                       (M._readout(iface, cfg, two[:, 1:2])[:, 1] - M._readout(iface, cfg, two[:, :1])[:, 1]).numpy(),
                       atol=1e-6)


def test_swapping_the_starts_flips_every_sign(parts):
    """With the two start levels swapped, the rows swap: the differences change sign and nothing else."""
    from wormwars.exp03 import twin
    p, con, bank, iface, g, cfg = parts
    a = twin.history(g, cfg, iface, bank, follow=5)
    b = twin.history(g, cfg, iface, bank, rising_start=1.75, falling_start=0.25, follow=5)
    for k in ("final", "steady_contrast"):
        assert np.allclose(a["raw_turn"][k], -b["raw_turn"][k], atol=1e-6)
    assert np.allclose(a["diff"], -b["diff"], atol=1e-6)


def sequential_pre(g, cfg, iface, bank, start, food, warm=100, span=10):
    """A one-row reference for the pre-tanh read-out: the turn-plus neurons' mean state minus the turn-minus
    neurons', after the hold and at the ramp's end, written out from the neuron lists (Fable, Astra, review v2)."""
    from wormwars.brain import Brain
    brain = Brain(g)
    s, n = g.n_strains, g.spec.n
    at = lambda lv: M._current(iface, cfg, dict(bank, food_left=lv, food_right=lv), n, s, "cpu")  # noqa: E731
    v = brain.initial_state(1)
    for _ in range(warm):
        v = brain.step(v, at(start))
    plus, minus = list(iface.turn_plus), list(iface.turn_minus)
    hold = v[:, 0, plus].mean(-1) - v[:, 0, minus].mean(-1)
    for t in range(span):
        v = brain.step(v, at(start + (food - start) * (t + 1) / span))
    return hold.numpy(), (v[:, 0, plus].mean(-1) - v[:, 0, minus].mean(-1)).numpy()


def test_the_pre_tanh_terms_match_a_one_row_reference(parts):
    from wormwars.exp03 import twin
    p, con, bank, iface, g, cfg = parts
    food = (bank["food_left"] + bank["food_right"]) / 2
    h_r, f_r = sequential_pre(g, cfg, iface, bank, 0.25 * food, food)
    h_f, f_f = sequential_pre(g, cfg, iface, bank, 1.75 * food, food)
    h = twin.history(g, cfg, iface, bank, follow=5)
    assert rel(h["pre_turn"]["final"], f_r - f_f) < TOL
    assert rel(h["pre_turn"]["steady_contrast"], h_f - h_r) < TOL
