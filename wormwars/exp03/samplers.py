"""Experiment 03's control ensembles (design v3, D050-D051). Every sampler is a double-edge-swap
chain that preserves each neuron's chemical in- and out-degree and gap degree. It returns its
accepted and attempted counts, and raises `SamplerFailure` instead of returning a half-mixed graph.

- "SH": ordinary shuffles. It reproduces `connectome.graphs.shuffled` exactly, including the
  random-number stream, with counters added. That sampler, used by 01b and 02, is left untouched.
- "SH-route": the six food pairs of M0, R1 and R2 keep at most N2's number of direct edges onto the
  motor read-out. Edges can be removed and recreated within that bound, so the moves are
  reversible. After weights are permuted, each such neuron's direct read-out weight *sum* is
  capped at N2's, by swapping weights with unconstrained edges.
- "SH-class": a swap needs both targets in one neuron class and both sources in one class, so
  each neuron keeps its in- and out-degree per partner class.
- "SH-mirror": moves stay within mirror-orbit categories (paired, self-mirrored, unpaired) under
  the curated left-right map, so the symmetric share equals N2's exactly. Routing-matched as
  SH-route. Self-mirrored gap junctions between left-right homologs cannot move.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..interface import load_interface

ROOT = Path(__file__).resolve().parents[2]
KINDS = ("SH", "SH-route", "SH-class", "SH-mirror")


class SamplerFailure(RuntimeError):
    """A chain did not reach its accepted-swap target within its attempt cap."""


# ----------------------------------------------------------------------------- annotations

def mirror_map(con) -> np.ndarray:
    """The curated left-right map (configs/mirror_pairs.yaml) as a permutation of indices."""
    text = (ROOT / "configs" / "mirror_pairs.yaml").read_text(encoding="utf-8")
    m = np.arange(con.n)
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("- [") and line.endswith("]"):
            a, b = (x.strip() for x in line[3:-1].split(","))
            i, j = con.index(a), con.index(b)
            m[i], m[j] = j, i
    return m


def constrained_neurons(con) -> list[str]:
    """The food neurons of every mapping used for fitness: M0, R1 and R2."""
    sets = json.loads((ROOT / "experiments" / "02-screening" / "remaps.json").read_text(encoding="utf-8"))["sets"]
    return [n for mapping in ("M0", "R1", "R2") for pair in sets[mapping] for n in pair]


def readout_indices(con) -> np.ndarray:
    iface = load_interface(con)
    return np.array(sorted({int(i) for i in np.concatenate([iface.forward_plus, iface.forward_minus,
                                                            iface.turn_plus, iface.turn_minus])}))


def direct_readout(con, k: int, mat: str) -> dict:
    r = readout_indices(con)
    row = getattr(con, mat)[k, r]
    return {"count": int((row > 0).sum()), "weight": float(row.sum())}


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    return float((a & b).sum() / max((a | b).sum(), 1))


def mirror_share(mask: np.ndarray, m: np.ndarray) -> float:
    return float((mask & mask[np.ix_(m, m)]).sum() / max(mask.sum(), 1))


def class_profile(con) -> np.ndarray:
    """Per neuron: chemical out-degree, chemical in-degree and gap degree, by partner class."""
    classes = sorted(set(con.classes))
    cls = np.array([classes.index(c) for c in con.classes])
    onehot = np.eye(len(classes))[cls]
    ch, gp = (con.chem > 0).astype(float), (con.gap > 0).astype(float)
    return np.concatenate([ch @ onehot, ch.T @ onehot, gp @ onehot], axis=1).astype(int)


# ----------------------------------------------------------------------------- chains

def _chem_chain(edges, rng, target, cap, ok):
    """The published chemical swap (connectome.graphs._swap_chemical), with an acceptance hook
    `ok(old1, old2, new1, new2)` and counters. With ok=None it consumes the same random
    numbers and returns the same graph."""
    edges = edges.copy()
    m = len(edges)
    present = {(int(i), int(j)) for i, j in edges}
    accepted = attempts = 0
    while accepted < target and attempts < cap:
        attempts += 1
        e1, e2 = rng.integers(0, m, size=2)
        if e1 == e2:
            continue
        a, b = (int(x) for x in edges[e1])
        c, d = (int(x) for x in edges[e2])
        if (a, d) in present or (c, b) in present:
            continue
        if ok is not None and not ok((a, b), (c, d), (a, d), (c, b), present):
            continue
        present.discard((a, b))
        present.discard((c, d))
        present.add((a, d))
        present.add((c, b))
        edges[e1, 1], edges[e2, 1] = d, b
        accepted += 1
    return edges, accepted, attempts


def _gap_chain(edges, rng, target, cap, ok):
    """The published undirected swap (connectome.graphs._swap_gap), with a hook and counters."""
    edges = edges.copy()
    m = len(edges)
    present = {frozenset((int(i), int(j))) for i, j in edges}
    accepted = attempts = 0
    while accepted < target and attempts < cap:
        attempts += 1
        e1, e2 = rng.integers(0, m, size=2)
        if e1 == e2:
            continue
        a, b = (int(x) for x in edges[e1])
        c, d = (int(x) for x in edges[e2])
        if rng.random() < 0.5:
            c, d = d, c
        new1, new2 = frozenset((a, d)), frozenset((c, b))
        if len(new1) < 2 or len(new2) < 2:
            continue
        if new1 in present or new2 in present or new1 == new2:
            continue
        if ok is not None and not ok(frozenset((a, b)), frozenset((c, d)), new1, new2, present):
            continue
        present.discard(frozenset((a, b)))
        present.discard(frozenset((c, d)))
        present.add(new1)
        present.add(new2)
        edges[e1] = (a, d)
        edges[e2] = (c, b)
        accepted += 1
    return edges, accepted, attempts


def _mirror_chain(edges, rng, target, cap, m, directed, route_ok):
    """Swaps within mirror-orbit categories. Paired edges move with their images, in one atomic
    step of four edges. Self-mirrored and unpaired edges are swapped within their own category.
    Every category is recomputed from the complete edge set the move would produce."""
    key = (lambda a, b: (a, b)) if directed else (lambda a, b: frozenset((a, b)))

    def image(e):
        a, b = tuple(e) if directed else sorted(e)
        return key(int(m[a]), int(m[b]))

    def cat(e, pres):
        im = image(e)
        if im == e:
            return "self"
        return "paired" if im in pres else "unpaired"

    present = {key(int(a), int(b)) for a, b in edges}
    elist = list(present)
    accepted = attempts = 0
    while accepted < target and attempts < cap:
        attempts += 1
        i1, i2 = rng.integers(0, len(elist), size=2)
        if i1 == i2:
            continue
        e1, e2 = elist[i1], elist[i2]
        c1, c2 = cat(e1, present), cat(e2, present)
        if c1 != c2:
            continue
        (a, b), (c, d) = (e1, e2) if directed else (tuple(sorted(e1)), tuple(sorted(e2)))
        if not directed and rng.random() < 0.5:
            c, d = d, c
        new = [key(a, d), key(c, b)]
        if any((not directed and len(e) < 2) or (directed and e[0] == e[1]) for e in new):
            continue  # degenerate before its image is taken
        old = [e1, e2]
        if c1 == "paired":
            old += [image(e1), image(e2)]
            new += [image(new[0]), image(new[1])]
        if len(set(old)) != len(old) or len(set(new)) != len(new):
            continue
        if any((not directed and len(e) < 2) or (directed and e[0] == e[1]) for e in new):
            continue
        after = (present - set(old)) | set(new)
        if len(after) != len(present) or any(e in present and e not in old for e in new):
            continue
        # categories unchanged: the new edges fall in the old category, and no other edge's
        # category changes (only images of old or new edges can change, so check those)
        touched = {image(e) for e in old + new} & after
        if any(cat(e, after) != c1 for e in new):
            continue
        if any(cat(e, after) != cat(e, present) for e in touched if e in present and e not in old):
            continue
        if route_ok is not None and not route_ok(old, new, after):
            continue
        present = after
        idx = {e: i for i, e in enumerate(elist)}
        for o, n in zip(old, new):
            elist[idx[o]] = n
        accepted += 1
    arr = np.array([tuple(e) if directed else tuple(sorted(e)) for e in elist], dtype=np.int64)
    return arr, accepted, attempts


# ----------------------------------------------------------------------------- building

def _route_checker(con, directed):
    """A count-level check: each constrained neuron keeps at most N2's number of direct edges to
    the read-out. Removal and recreation are both allowed."""
    read = set(int(r) for r in readout_indices(con))
    cons = [con.index(n) for n in constrained_neurons(con)]
    mat = con.chem if directed else con.gap
    caps = {k: int((mat[k, sorted(read)] > 0).sum()) for k in cons}
    cons = set(cons)

    def count(edges, k):
        if directed:
            return sum(1 for (a, b) in edges if a == k and b in read)
        return sum(1 for e in edges if k in e and (set(e) - {k}) & read)

    def ok_swap(o1, o2, n1, n2, present):
        touched = {x for e in (o1, o2, n1, n2) for x in e} & cons
        if not touched:
            return True
        after = (present - {o1, o2}) | {n1, n2}
        return all(count(after, k) <= caps[k] for k in touched)

    def ok_mirror(old, new, after):
        touched = {x for e in old + new for x in e} & cons
        return all(count(after, k) <= caps[k] for k in touched)

    return ok_swap, ok_mirror


def _cap_weights(con, mat_new: np.ndarray, rng, directed: bool) -> np.ndarray:
    """Swap weights between each constrained neuron's direct read-out edges and unconstrained
    edges until that neuron's direct read-out weight sum is at most N2's. The multiset of weights
    is unchanged."""
    read = readout_indices(con)
    cons = [con.index(n) for n in constrained_neurons(con)]
    old = con.chem if directed else con.gap
    w = mat_new.copy()
    constrained_slots = set()
    for k in cons:
        for r in read:
            if w[k, r] > 0:
                constrained_slots.add((k, int(r)))
                if not directed:
                    constrained_slots.add((int(r), k))
    free = [(int(i), int(j)) for i, j in zip(*np.nonzero(w)) if (int(i), int(j)) not in constrained_slots
            and (directed or i < j)]
    for k in cons:
        cap = float(old[k, read].sum())
        heavy = [int(r) for r in read if w[k, r] > 0]
        if not heavy or w[k, read].sum() <= cap + 1e-9:
            continue
        # an even split: each direct edge may carry at most cap / count. The count is at most
        # N2's, so the split is at least N2's mean direct weight, and the pool holds such values.
        budget = cap / len(heavy)
        for r in heavy:
            if w[k, r] <= budget + 1e-9:
                continue
            cands = [e for e in free if 0 < w[e] <= budget + 1e-9]
            if not cands:
                raise SamplerFailure(f"cannot cap the direct read-out weight of {con.names[k]}")
            i, j = cands[int(rng.integers(0, len(cands)))]
            w[k, r], w[i, j] = w[i, j], w[k, r]
            if not directed:
                w[r, k], w[j, i] = w[k, r], w[i, j]
        if w[k, read].sum() > cap + 1e-9:
            raise SamplerFailure(f"weight cap failed for {con.names[k]}")
    return w


def build(con, kind: str, seed: int, passes: int = 20, attempt_factor: float = 40.0):
    """One graph of ensemble `kind`. Returns (connectome, info with the counts per chain)."""
    if kind not in KINDS:
        raise ValueError(f"unknown ensemble {kind!r}")
    rng = np.random.default_rng(seed)
    n = con.n
    m = mirror_map(con)
    classes = np.array(con.classes)
    route = kind in ("SH-route", "SH-mirror")
    ok_chem = ok_gap = None
    route_chem = route_gap = (None, None)
    if route:
        route_chem, route_gap = _route_checker(con, True), _route_checker(con, False)
    if kind == "SH-route":
        ok_chem, ok_gap = route_chem[0], route_gap[0]
    elif kind == "SH-class":
        def ok_chem(o1, o2, n1, n2, present):
            (a, b), (c, d) = o1, o2
            return classes[b] == classes[d] and classes[a] == classes[c]

        def ok_gap(o1, o2, n1, n2, present):
            # {a,b},{c,d} -> {a,d},{c,b}: recover the orientation from the shared endpoints. Each
            # endpoint keeps its partner-class profile iff class(b) = class(d) and class(a) = class(c).
            (a,) = tuple(n1 & o1)
            (b,) = tuple(o1 - {a})
            (d,) = tuple(n1 - {a})
            (c,) = tuple(n2 - {b})
            return classes[b] == classes[d] and classes[a] == classes[c]

    info = {}
    ci, cj = np.nonzero(con.chem > 0)
    cw = con.chem[ci, cj]
    target_c = passes * len(ci)
    if kind == "SH-mirror":
        new_c, acc, att = _mirror_chain(np.stack([ci, cj], 1), rng, target_c, int(attempt_factor * target_c), m, True,
                                        route_chem[1])
    else:
        new_c, acc, att = _chem_chain(np.stack([ci, cj], 1), rng, target_c, int(attempt_factor * target_c), ok_chem)
    info["chem"] = {"accepted": acc, "attempted": att, "target": target_c}
    if acc < target_c:
        raise SamplerFailure(f"{kind} seed {seed}: chemical chain reached {acc} of {target_c} swaps")
    chem = np.zeros((n, n), dtype=np.float32)
    chem[new_c[:, 0], new_c[:, 1]] = rng.permutation(cw)

    gi, gj = np.nonzero(np.triu(con.gap, 1) > 0)
    gw = con.gap[gi, gj]
    target_g = passes * len(gi)
    if kind == "SH-mirror":
        new_g, acc, att = _mirror_chain(np.stack([gi, gj], 1), rng, target_g, int(attempt_factor * target_g), m, False,
                                        route_gap[1])
    else:
        new_g, acc, att = _gap_chain(np.stack([gi, gj], 1), rng, target_g, int(attempt_factor * target_g), ok_gap)
    info["gap"] = {"accepted": acc, "attempted": att, "target": target_g}
    if acc < target_g:
        raise SamplerFailure(f"{kind} seed {seed}: gap chain reached {acc} of {target_g} swaps")
    gap = np.zeros((n, n), dtype=np.float32)
    perm = rng.permutation(gw)
    gap[new_g[:, 0], new_g[:, 1]] = perm
    gap[new_g[:, 1], new_g[:, 0]] = perm
    if route:
        chem = _cap_weights(con, chem, rng, True)
        gap = _cap_weights(con, gap, rng, False)
    return con.with_masks(chem, gap, f"{kind}-{seed}"), info
