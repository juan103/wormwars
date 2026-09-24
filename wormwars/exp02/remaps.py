"""Choosing the wrong food mappings by a fixed rule, before any fitness is measured.

A remap moves the food signal from AWA/AWC/ASE to three other bilateral sensory pairs outside the
interface. Routing is a hard, per-pair tolerance: a remap pair may be no closer to the motor
read-out than the food neurons are, measured in the direction signal flows (chemical pre -> post,
gap both ways): at least 1.5 hops on average to the forward read-out and to the turn read-out,
and at most 2 units of anatomical weight on direct edges into the read-out (the food pairs have
0-1). Among the pairs that qualify, degree is matched pair by pair: a triple's distance is the
smallest sum, over the six ways of assigning its pairs to AWA, AWC and ASE, of per-pair L1
distances on chemical out-degree, in-degree and gap degree, each scaled by its standard deviation
over the candidate pool. The two best disjoint triples are R1 and R2, each ordered so that position
k replaces food pair k. The shortcut remap MS is the three pairs with the most direct read-out
weight. Only per-pair summaries leave this module, never edges.

Why hard tolerances: averaging let shortcuts in twice during development. A triple-mean rule
admitted URX (direct weight 13, one hop) behind a weakly connected partner, and a std-scaled
six-feature rule admitted BAG, OLQD and OLQV (12-20), because the extreme shortcuts (FLP 174)
inflate the scale of the direct-weight feature until 13 against 0 barely registers.
"""

from __future__ import annotations

import itertools

import numpy as np

FEATURES = ("chem_out", "chem_in", "gap", "hops_forward", "hops_turn", "direct_weight")
DEGREE = ("chem_out", "chem_in", "gap")
ROUTING_TOLERANCE = {"hops_forward": 1.5, "hops_turn": 1.5, "direct_weight": 2.0}


def within_routing_tolerance(f: dict) -> bool:
    t = ROUTING_TOLERANCE
    return (f["hops_forward"] >= t["hops_forward"] and f["hops_turn"] >= t["hops_turn"]
            and f["direct_weight"] <= t["direct_weight"])


def hops_to(adj: np.ndarray, source: int, targets: set[int], limit: int = 99) -> int:
    """Shortest path length from `source` to any of `targets` along `adj[u, v]` (u -> v)."""
    if source in targets:
        return 0
    seen, frontier, d = {source}, [source], 0
    while frontier:
        d += 1
        nxt = []
        for u in frontier:
            for v in np.flatnonzero(adj[u]):
                v = int(v)
                if v in targets:
                    return d
                if v not in seen:
                    seen.add(v)
                    nxt.append(v)
        frontier = nxt
    return limit


def _pair(con, base: str) -> tuple[int, int]:
    return con.index(base + "L"), con.index(base + "R")


def candidate_pairs(con, iface) -> list[str]:
    mapped = set(iface.mapped_neurons)
    out = set()
    for i, n in enumerate(con.names):
        if con.classes[i] != "sensory" or not n.endswith("L"):
            continue
        r = n[:-1] + "R"
        if r not in con.index_of:
            continue
        if i in mapped or con.index(r) in mapped:
            continue
        out.add(n[:-1])
    return sorted(out)


def motivated_pairs(con, iface, prefix: str = "food") -> list[str]:
    left = [con.names[i] for s, i in zip(iface.signal_names, iface.sensor_neuron)
            if s == f"{prefix}_left"]
    return [n[:-1] for n in left]


def _readout(iface) -> tuple[set[int], set[int]]:
    fwd = {int(i) for i in np.concatenate([iface.forward_plus, iface.forward_minus])}
    turn = {int(i) for i in np.concatenate([iface.turn_plus, iface.turn_minus])}
    return fwd, turn


def pair_features(con, iface, base: str) -> dict[str, float]:
    chem, gap = con.chem > 0, con.gap > 0
    adj = chem | gap
    fwd, turn = _readout(iface)
    read = sorted(fwd | turn)
    rows = []
    for i in _pair(con, base):
        rows.append({
            "chem_out": float(chem[i].sum()),
            "chem_in": float(chem[:, i].sum()),
            "gap": float(gap[i].sum()),
            "hops_forward": float(hops_to(adj, i, fwd)),
            "hops_turn": float(hops_to(adj, i, turn)),
            "direct_weight": float(con.chem[i, read].sum() + con.gap[i, read].sum()),
        })
    return {f: float(np.mean([r[f] for r in rows])) for f in FEATURES}


def _table(con, iface, bases):
    return {b: pair_features(con, iface, b) for b in bases}


def _pvec(feats: dict[str, dict], base: str, scale: np.ndarray) -> np.ndarray:
    return np.array([feats[base][f] for f in DEGREE]) / scale


def _assign(feats, triple, target, scale) -> tuple[float, tuple]:
    """Best assignment of the triple's pairs to the target pairs; returns (distance, ordered)."""
    best = None
    for perm in itertools.permutations(triple):
        d = sum(float(np.abs(_pvec(feats, b, scale) - _pvec(feats, t, scale)).sum())
                for b, t in zip(perm, target))
        if best is None or (d, perm) < best:
            best = (d, perm)
    return best


def _scales(feats: dict[str, dict], bases) -> np.ndarray:
    m = np.array([[feats[b][f] for f in DEGREE] for b in bases])
    s = m.std(axis=0)
    return np.where(s > 0, s, 1.0)


def _ranked_triples(con, iface, prefix="food"):
    cands = candidate_pairs(con, iface)
    target = motivated_pairs(con, iface, prefix)
    feats = _table(con, iface, cands + target)
    scale = _scales(feats, cands)
    eligible = [b for b in cands if within_routing_tolerance(feats[b])]
    if len(eligible) < 6:
        raise ValueError(f"only {len(eligible)} candidate pairs meet the routing tolerance: {eligible}")
    scored = [_assign(feats, tr, target, scale) for tr in itertools.combinations(eligible, 3)]
    scored.sort()
    return scored, feats


def choose_matched(con, iface, n_sets: int = 2, prefix: str = "food") -> list[list[str]]:
    scored, _ = _ranked_triples(con, iface, prefix)
    chosen: list[list[str]] = []
    for _, tr in scored:
        if all(not set(tr) & set(c) for c in chosen):
            chosen.append(list(tr))
            if len(chosen) == n_sets:
                break
    return chosen


def choose_shortcut(con, iface, exclude: set[str], k: int = 3) -> list[str]:
    cands = [b for b in candidate_pairs(con, iface) if b not in exclude]
    ranked = sorted(cands, key=lambda b: (-pair_features(con, iface, b)["direct_weight"], b))
    return ranked[:k]


def remap_record(con, iface, prefix: str = "food") -> dict:
    scored, feats = _ranked_triples(con, iface, prefix)
    dist = {tuple(tr): d for d, tr in scored}  # keyed by the ordered triple
    r1, r2 = choose_matched(con, iface, 2, prefix)
    ms = choose_shortcut(con, iface, exclude=set(r1) | set(r2))
    m0 = motivated_pairs(con, iface, prefix)
    as_pairs = lambda bases: [[b + "L", b + "R"] for b in bases]  # noqa: E731
    return {
        "rule": " ".join(__doc__.strip().split("\n\n")[1].split()),
        "routing_tolerance": dict(ROUTING_TOLERANCE),
        "features": list(FEATURES),
        "sets": {"M0": as_pairs(m0), "R1": as_pairs(r1), "R2": as_pairs(r2), "MS": as_pairs(ms)},
        "distance_to_M0": {"R1": dist[tuple(r1)], "R2": dist[tuple(r2)]},
        "pair_features": {b: feats.get(b) or pair_features(con, iface, b)
                          for b in m0 + r1 + r2 + ms},
    }
