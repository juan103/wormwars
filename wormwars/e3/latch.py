"""E3a's latch: the fixed points of q with the relays at rest, and its equilibrium structure
(experiments/E3-ab-organism/E3a/PREREGISTRATION.md §6, "The fixed points").

f(q) = −q + w·tanh q + b. If w > 1, f's stationary points ±acosh(√w) split the line into three
monotone intervals; otherwise it is one. Each interval, bounded by |q| ≤ |w| + |b| + 1, holds at most
one root, found by bisection to 1e-12 when its ends differ in sign or one is exactly 0. A stationary
point where |f| < 1e-12 is a tangent root. A root is stable if f′ = −1 + w·sech²q < −1e-6.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

STABLE = -1e-6
TANGENT = 1e-12
TOL = 1e-12
MIN_SEPARATION = 0.1


def f(q: float, w: float, b: float) -> float:
    return -q + w * math.tanh(q) + b


def fprime(q: float, w: float) -> float:
    return -1.0 + w / math.cosh(q) ** 2


def _bisect(lo: float, hi: float, w: float, b: float) -> float:
    flo = f(lo, w, b)
    while hi - lo > TOL:
        mid = (lo + hi) / 2
        fm = f(mid, w, b)
        if fm == 0.0:
            return mid
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def roots(w: float, b: float) -> list[tuple[float, float]]:
    """Every root, ascending, as (q, f′(q))."""
    w, b = float(w), float(b)
    bound = abs(w) + abs(b) + 1.0
    edges = [-bound, bound]
    stationary = []
    if w > 1.0:
        s = math.acosh(math.sqrt(w))
        stationary = [-s, s]
        edges = [-bound, -s, s, bound]
    found: list[float] = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        flo, fhi = f(lo, w, b), f(hi, w, b)
        if flo == 0.0:
            found.append(lo)
        elif fhi == 0.0:
            found.append(hi)
        elif (flo > 0) != (fhi > 0):
            found.append(_bisect(lo, hi, w, b))
    for s in stationary:  # tangent roots
        if abs(f(s, w, b)) < TANGENT:
            found.append(s)
    found.sort()
    out: list[float] = []
    for q in found:
        if not out or abs(q - out[-1]) > 1e-9:
            out.append(q)
    return [(q, fprime(q, w)) for q in out]


def stable_roots(w: float, b: float) -> list[float]:
    return [q for q, d in roots(w, b) if d < STABLE]


@dataclass(frozen=True)
class Structure:
    kind: str  # "bistable" or "monostable"
    states: tuple[float, ...]  # the two stable roots if bistable, else ()


def structure(w: float, b: float) -> Structure:
    st = stable_roots(w, b)
    if len(st) == 2 and st[1] - st[0] >= MIN_SEPARATION:
        return Structure("bistable", (st[0], st[1]))
    return Structure("monostable", ())


def release_start(w: float, b: float) -> float:
    """A monostable q's release-test start: the root with the most negative f′, ties to the lower q.
    Defined whether or not any root meets the stability threshold."""
    rs = roots(w, b)
    best = min(d for _, d in rs)
    return min(q for q, d in rs if d == best)
