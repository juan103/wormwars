"""E3a's fixed-point finder and equilibrium structure (PREREGISTRATION §6 "The fixed points"; test 10).

Roots of f(q) = −q + w tanh q + b, bracketed by f's stationary points ±acosh(√w) when w > 1, each
monotone interval bisected to 1e-12. A root is stable if f′ < −1e-6; a tangent root is not.
Bistable: two stable roots at least 0.1 apart.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from wormwars.e3 import latch as L


def test_es_latch_has_two_stable_roots_and_an_unstable_zero():
    roots = L.roots(2.0, 0.0)
    assert [round(q, 5) for q, _ in roots] == [-1.91501, 0.0, 1.91501]  # 0 is an exact zero
    s = L.structure(2.0, 0.0)
    assert s.kind == "bistable" and s.states == pytest.approx((-1.915008, 1.915008), abs=1e-6)


def test_astras_missed_root_case_is_found():
    """The design's 100 001-point grid finds one root here; bracketing finds all three (D164)."""
    w, b = 1.0119999647140503, 0.0008732174756005406
    g = np.linspace(-(w + b + 1), w + b + 1, 100_001)
    f = -g + w * np.tanh(g) + b
    assert int((np.sign(f[:-1]) * np.sign(f[1:]) < 0).sum()) == 1  # the grid's failure
    roots = L.roots(w, b)
    assert len(roots) == 3
    stable = L.stable_roots(w, b)
    assert [round(q, 5) for q in stable] == [-0.10934, 0.21970]
    assert L.structure(w, b).kind == "bistable"


def test_a_tangent_root_is_not_stable():
    w = 2.0
    s = math.acosh(math.sqrt(w))
    b = s - w * math.tanh(s)  # f(s) = 0 and f'(s) = 0
    roots = L.roots(w, b)
    assert any(abs(q - s) < 1e-6 for q, _ in roots)
    assert all(abs(q - s) > 1e-6 for q in L.stable_roots(w, b))
    assert L.structure(w, b).kind == "monostable"


def test_close_stable_roots_are_monostable_and_the_start_breaks_the_tie_low():
    """Astra: w 1.0001, b 0 has stable roots ±0.0173, too close to count as bistable (D165)."""
    w = 1.000100016593933
    stable = L.stable_roots(w, 0.0)
    assert len(stable) == 2 and stable[1] - stable[0] < 0.1
    assert L.structure(w, 0.0).kind == "monostable"
    assert L.release_start(w, 0.0) == pytest.approx(stable[0])


def test_a_monostable_q_has_one_root_and_starts_there():
    assert len(L.roots(0.5, 0.3)) == 1
    q = L.release_start(0.5, 0.3)
    assert -q + 0.5 * math.tanh(q) + 0.3 == pytest.approx(0.0, abs=1e-10)
    assert L.structure(0.5, 0.3).kind == "monostable"


def test_negative_self_weights_are_monostable():
    assert L.structure(-3.0, 1.0).kind == "monostable"
    assert len(L.roots(-3.0, 1.0)) == 1


def test_a_near_tangent_within_the_tolerance_counts_as_a_tangent_root():
    """|f| < 1e-12 at a stationary point is a tangent root by the registered rule, even where f never
    changes sign there; bisection alone would miss it."""
    w = 2.0
    s = math.acosh(math.sqrt(w))
    b = s - w * math.tanh(s) - 5e-13
    assert L.f(s, w, b) < 0
    roots = L.roots(w, b)
    assert any(abs(q - s) < 1e-9 for q, _ in roots)
    assert all(abs(q - s) > 1e-6 for q in L.stable_roots(w, b))
