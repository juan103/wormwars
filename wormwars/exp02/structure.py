"""Graph covariates for the primary outcome (Fable 5.1's pre-registration review, points 1 and 7).

A degree-preserving shuffle keeps every neuron's degrees but not the left-right pairing of its
targets, while the turn read-out is bilateral. Any mirror-symmetric graph gets a left-minus-right
comparison almost for free, so a stereo advantage for N2 may be a symmetry effect rather than
anything specific to its wiring. These scalars are reported per graph next to the capability
results. They carry no edges."""

from __future__ import annotations

import numpy as np

from .remaps import pair_features

FOOD_PAIRS = ("AWA", "AWC", "ASE")


def mirror_index(con) -> np.ndarray:
    """The left-right relabelling as a permutation: XL <-> XR where both exist, else identity."""
    m = np.arange(con.n)
    idx = con.index_of
    for i, name in enumerate(con.names):
        if name.endswith("L") and name[:-1] + "R" in idx:
            j = idx[name[:-1] + "R"]
            m[i], m[j] = j, i
    return m


def mirror_symmetry(con) -> dict[str, float]:
    """chem_edges_mirrored: share of chemical edges i -> j whose mirror image m(i) -> m(j) is also
    an edge. gap_edges_mirrored: the same for gap junctions. food_out_jaccard: mean over the food
    pairs of the Jaccard overlap between the mirrored out-neighbourhood of the left neuron and
    the out-neighbourhood of the right one."""
    m = mirror_index(con)
    chem, gap = con.chem > 0, con.gap > 0
    out = {"chem_edges_mirrored": float((chem & chem[np.ix_(m, m)]).sum() / max(chem.sum(), 1)),
           "gap_edges_mirrored": float((gap & gap[np.ix_(m, m)]).sum() / max(gap.sum(), 1))}
    jac = []
    for base in FOOD_PAIRS:
        left, right = con.index(base + "L"), con.index(base + "R")
        a = {int(m[j]) for j in np.nonzero(chem[left] | gap[left])[0]}
        b = {int(j) for j in np.nonzero(chem[right] | gap[right])[0]}
        jac.append(len(a & b) / max(len(a | b), 1))
    out["food_out_jaccard"] = float(np.mean(jac))
    return out


def covariates(con, iface) -> dict:
    return {"mirror": mirror_symmetry(con),
            "food_routing": {b: pair_features(con, iface, b) for b in FOOD_PAIRS}}
