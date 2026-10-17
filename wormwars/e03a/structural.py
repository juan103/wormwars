"""The structural comparators (experiments/03a-self-consistency/DESIGN.md v7.1 §6; DRAFT.md "Structural baselines").

Each is a candidate ranking per connection type, computed only from the graph with X deleted, and scored against the
same truth as the task ranking; none costs any simulation.
- **Mirror** (paired targets): a candidate c's score is the weight of the mirror-image connection of X's bilateral
  partner X': in, chem[m(c), X']; out, chem[X', m(c)]; gap, gap[X', m(c)]. Where that would need a connection to or
  from X itself (c = X', whose mirror is X), the class-model score is used.
- **Class model:** the connection probability between X's neuron class and the candidate's class, estimated with X
  removed: the share of ordered pairs (a, b), a ≠ b, neither X, with a of the presynaptic class and b of the
  postsynaptic class, that have the edge (unordered for gap junctions). Classes are the dataset's.
- **Degree:** the candidate's degree of the matching kind with X deleted: out-degree for in-partners, in-degree for
  out-partners, gap degree for gap partners (self-connections not counted).
- **Composite:** mirror for paired targets, class model for unpaired ones, by rule.
"""

from __future__ import annotations

import numpy as np

from ..connectome.loader import Connectome
from .reinsert import candidates


def _without(con: Connectome, x: int):
    chem = np.array(con.chem, dtype=np.float64, copy=True)
    gap = np.array(con.gap, dtype=np.float64, copy=True)
    chem[x, :] = chem[:, x] = 0
    gap[x, :] = gap[:, x] = 0
    return chem, gap


def class_model(con: Connectome, x: int) -> dict:
    chem, gap = _without(con, x)
    cls = np.array(con.classes)
    keep = np.array([i != x for i in range(con.n)])
    labels = sorted(set(cls[keep]))
    ce, ge = chem > 0, gap > 0
    np.fill_diagonal(ce, False)
    np.fill_diagonal(ge, False)
    prob_c, prob_g = {}, {}
    for a in labels:
        ia = keep & (cls == a)
        for b in labels:
            ib = keep & (cls == b)
            pairs = ia.sum() * ib.sum() - (ia & ib).sum()
            prob_c[(a, b)] = ce[np.ix_(ia, ib)].sum() / pairs if pairs else 0.0
            prob_g[(a, b)] = ge[np.ix_(ia, ib)].sum() / pairs if pairs else 0.0
    c = candidates(con.n, x)
    cx = cls[x]
    return {"in": np.array([prob_c[(cls[k], cx)] for k in c]),
            "out": np.array([prob_c[(cx, cls[k])] for k in c]),
            "gap": np.array([prob_g[(cx, cls[k])] for k in c])}


def degree(con: Connectome, x: int) -> dict:
    chem, gap = _without(con, x)
    ce, ge = chem > 0, gap > 0
    np.fill_diagonal(ce, False)
    np.fill_diagonal(ge, False)
    c = candidates(con.n, x)
    return {"in": ce.sum(1)[c].astype(float), "out": ce.sum(0)[c].astype(float), "gap": ge.sum(1)[c].astype(float)}


def mirror(con: Connectome, x: int, m: np.ndarray) -> dict | None:
    """None for an unpaired target."""
    xp = int(m[x])
    if xp == x:
        return None
    chem, gap = _without(con, x)
    cm = class_model(con, x)
    c = candidates(con.n, x)
    out = {"in": np.empty(len(c)), "out": np.empty(len(c)), "gap": np.empty(len(c))}
    for k, cand in enumerate(c):
        mc = int(m[cand])
        if mc == x:  # c = X': its mirror connection would be X's own
            for t in out:
                out[t][k] = cm[t][k]
            continue
        out["in"][k] = chem[mc, xp]
        out["out"][k] = chem[xp, mc]
        out["gap"][k] = gap[xp, mc]
    return out


def composite(con: Connectome, x: int, m: np.ndarray) -> tuple[str, dict]:
    mr = mirror(con, x, m)
    return ("mirror", mr) if mr is not None else ("class model", class_model(con, x))
