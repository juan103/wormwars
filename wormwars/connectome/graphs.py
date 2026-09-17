"""The control conditions: SH (degree-preserving shuffles) and RD (random sparse graphs).

Both keep the same 302 neurons, the same neuron classes, and the same *indices* -- so the sensor
and motor map lands on the same positions in every condition. What changes is only which neuron is
wired to which.

- **SH** preserves each neuron's in-degree and out-degree exactly (chemical), and each neuron's
  degree exactly (gap). Chemical and gap graphs are shuffled independently. The gap graph stays
  symmetric. Anatomical weights are carried along with the edges, so the weight *distribution* is
  identical to N2 and only the topology moves.
- **RD** keeps only the neuron count and the edge count: edges are placed uniformly at random, and
  the anatomical weights of N2 are dealt out to them in random order, so again only the topology
  differs from N2 in distribution.

Self-loops are allowed in both, because N2 has 38 chemical autapses and dropping them in the
controls would make the conditions unmatched (DECISIONS.md D007).
"""

from __future__ import annotations

import numpy as np

from .loader import Connectome


def _swap_chemical(edges: np.ndarray, rng: np.random.Generator, passes: int = 20) -> np.ndarray:
    """Double-edge swap on a directed edge list, preserving in- and out-degree exactly.

    Each swap takes (a->b), (c->d) to (a->d), (c->b). Out-degrees of a and c are untouched, as are
    in-degrees of b and d. A swap is rejected only if it would duplicate an existing edge.
    """
    edges = edges.copy()
    m = len(edges)
    present = {(int(i), int(j)) for i, j in edges}
    target = passes * m
    accepted = 0
    attempts = 0
    while accepted < target and attempts < 40 * target:
        attempts += 1
        e1, e2 = rng.integers(0, m, size=2)
        if e1 == e2:
            continue
        a, b = edges[e1]
        c, d = edges[e2]
        if (a, d) in present or (c, b) in present:
            continue
        present.discard((int(a), int(b)))
        present.discard((int(c), int(d)))
        present.add((int(a), int(d)))
        present.add((int(c), int(b)))
        edges[e1, 1], edges[e2, 1] = d, b
        accepted += 1
    return edges


def _swap_gap(edges: np.ndarray, rng: np.random.Generator, passes: int = 20) -> np.ndarray:
    """Double-edge swap on an undirected edge list (i<j not required), preserving degree exactly."""
    edges = edges.copy()
    m = len(edges)
    present = {frozenset((int(i), int(j))) for i, j in edges}
    target = passes * m
    accepted = 0
    attempts = 0
    while accepted < target and attempts < 40 * target:
        attempts += 1
        e1, e2 = rng.integers(0, m, size=2)
        if e1 == e2:
            continue
        a, b = edges[e1]
        c, d = edges[e2]
        if rng.random() < 0.5:
            c, d = d, c
        new1, new2 = frozenset((int(a), int(d))), frozenset((int(c), int(b)))
        if len(new1) < 2 or len(new2) < 2:  # would make a self gap junction
            continue
        if new1 in present or new2 in present or new1 == new2:
            continue
        present.discard(frozenset((int(a), int(b))))
        present.discard(frozenset((int(c), int(d))))
        present.add(new1)
        present.add(new2)
        edges[e1] = (a, d)
        edges[e2] = (c, b)
        accepted += 1
    return edges


def shuffled(con: Connectome, seed: int, label: str | None = None, passes: int = 20) -> Connectome:
    """SH: a degree-preserving shuffle of `con`."""
    rng = np.random.default_rng(seed)
    n = con.n

    ci, cj = np.nonzero(con.chem > 0)
    cw = con.chem[ci, cj]
    new_c = _swap_chemical(np.stack([ci, cj], axis=1), rng, passes)
    chem = np.zeros((n, n), dtype=np.float32)
    chem[new_c[:, 0], new_c[:, 1]] = rng.permutation(cw)

    gi, gj = np.nonzero(np.triu(con.gap, 1) > 0)
    gw = con.gap[gi, gj]
    new_g = _swap_gap(np.stack([gi, gj], axis=1), rng, passes)
    gap = np.zeros((n, n), dtype=np.float32)
    perm_w = rng.permutation(gw)
    gap[new_g[:, 0], new_g[:, 1]] = perm_w
    gap[new_g[:, 1], new_g[:, 0]] = perm_w

    return con.with_masks(chem, gap, label or f"SH{seed}")


def random_graph(
    con: Connectome, seed: int, label: str | None = None, allow_self: bool = True
) -> Connectome:
    """RD: uniformly random edges, same neuron count and same edge counts as `con`."""
    rng = np.random.default_rng(seed)
    n = con.n

    n_chem = int((con.chem > 0).sum())
    cw = con.chem[con.chem > 0]
    pool = n * n if allow_self else n * n - n
    picks = rng.choice(pool, size=n_chem, replace=False)
    if allow_self:
        ci, cj = np.divmod(picks, n)
    else:  # skip the diagonal
        ci, cj = np.divmod(picks, n - 1)
        cj = cj + (cj >= ci)
    chem = np.zeros((n, n), dtype=np.float32)
    chem[ci, cj] = rng.permutation(cw)

    n_gap = int((np.triu(con.gap, 1) > 0).sum())
    gw = con.gap[np.triu(con.gap, 1) > 0]
    iu = np.triu_indices(n, k=1)
    picks = rng.choice(len(iu[0]), size=n_gap, replace=False)
    gi, gj = iu[0][picks], iu[1][picks]
    gap = np.zeros((n, n), dtype=np.float32)
    perm_w = rng.permutation(gw)
    gap[gi, gj] = perm_w
    gap[gj, gi] = perm_w

    return con.with_masks(chem, gap, label or f"RD{seed}")


def make_graphs(con: Connectome, condition: str, k: int) -> list[Connectome]:
    """K graphs of one condition. N2 is the real graph repeated, since there is only one of it."""
    condition = condition.upper()
    if condition == "N2":
        return [con]
    if condition == "SH":
        return [shuffled(con, seed=i + 1, label=f"SH{i + 1}") for i in range(k)]
    if condition == "RD":
        return [random_graph(con, seed=i + 1, label=f"RD{i + 1}") for i in range(k)]
    raise ValueError(f"unknown condition {condition!r}; expected N2, SH or RD")


def degree_summary(con: Connectome) -> dict:
    return {
        "label": con.label,
        "chem_edges": int((con.chem > 0).sum()),
        "gap_edges": int((con.gap > 0).sum()) // 2,
        "chem_in_degree": np.bincount(np.nonzero(con.chem > 0)[1], minlength=con.n),
        "chem_out_degree": np.bincount(np.nonzero(con.chem > 0)[0], minlength=con.n),
        "gap_degree": (con.gap > 0).sum(axis=1),
        "chem_weight_sum": float(con.chem.sum()),
        "gap_weight_sum": float(con.gap.sum()),
        "self_loops": int((np.diag(con.chem) > 0).sum()),
    }
