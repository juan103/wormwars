"""The panel: six neurons per graph, by a rule (experiments/03a-self-consistency/DESIGN.md v7.1 §4).

- **Eligible:** neither mapped (sensor or motor in the interface) nor pharyngeal, and connected by directed paths both
  from and to the interface in that graph (chemical edges directed, gap junctions both ways).
- **Bilateral pairs** (`configs/mirror_pairs.yaml`): one member of each pair is chosen by a fixed seed before any
  measurement and represents the pair; a pair with one eligible member is represented by it.
- **Relevance:** the drop in score when the neuron is deleted, per selector brain, on the target-selection worlds; a
  neuron's relevance is the three-brain mean, with a 95% interval from a bootstrap over worlds (one shared resample of
  world ids for the three brains) of that mean. p_sel = 5% of the selector brains' mean intact score.
- **Tiers,** in order and without replacement: high, the 3 largest mean drops (flagged "relatively high only" if the
  lower bound does not exceed p_sel); medium, 2 drawn with a fixed seed from the remaining neurons whose interval
  contains p_sel, topped up from the remaining neurons ranked 4-20 (flagged) if fewer exist; low, 1 drawn with a fixed
  seed from the remaining neurons whose interval lies inside ±p_sel, else the remaining neuron with the smallest
  absolute drop (flagged). Ties in mean drop are broken by a fixed seeded order.
"""

from __future__ import annotations

from collections import deque

import numpy as np

from ..connectome.loader import Connectome
from ..exp03.samplers import mirror_map
from .stats import world_resamples

PANEL_STREAM = 0x03A9A


def _reach(adj: np.ndarray, start: set) -> set:
    seen, q = set(start), deque(start)
    while q:
        i = q.popleft()
        for j in np.nonzero(adj[i])[0]:
            j = int(j)
            if j not in seen:
                seen.add(j)
                q.append(j)
    return seen


def eligible(con: Connectome, iface) -> list:
    """Indices of the eligible neurons, ascending."""
    mapped = set(iface.mapped_neurons)
    chem, gap = np.asarray(con.chem) > 0, np.asarray(con.gap) > 0
    fwd = chem | gap | gap.T
    from_iface = _reach(fwd, mapped)  # reachable from the interface
    to_iface = _reach(fwd.T, mapped)  # can reach the interface
    return [i for i in range(con.n) if i not in mapped and con.classes[i] != "pharyngeal"
            and i in from_iface and i in to_iface]


def representatives(con: Connectome, eligible_idx: list, seed: int) -> dict:
    """{representative: its mirror or None}: one member per eligible bilateral pair, by a fixed seed; unpaired and
    singly eligible neurons represent themselves."""
    m = mirror_map(con)
    el = set(eligible_idx)
    rng = np.random.default_rng([int(seed), PANEL_STREAM])
    out, done = {}, set()
    for i in sorted(el):
        if i in done:
            continue
        j = int(m[i])
        if j != i and j in el:
            pick = (i, j)[int(rng.integers(2))]
            out[pick] = j if pick == i else i
            done |= {i, j}
        else:
            out[i] = j if j != i else None
            done.add(i)
    return dict(sorted(out.items()))


def relevance(intact: np.ndarray, deleted: np.ndarray, B: int, seed: int) -> dict:
    """intact [brains, worlds], deleted [neurons, brains, worlds] scores: per neuron the three-brain mean drop, its
    95% interval (world bootstrap, shared across brains), and each brain's drop."""
    intact = np.asarray(intact, dtype=np.float64)
    deleted = np.asarray(deleted, dtype=np.float64)
    drop = intact[None] - deleted  # [neurons, brains, worlds]
    nw = drop.shape[2]
    wi = world_resamples(nw, B, seed)
    times = np.zeros((B, nw))  # how often each world is drawn in each resample
    np.add.at(times, (np.arange(B)[:, None], wi), 1.0)
    boot = drop.mean(axis=1) @ times.T / nw  # [neurons, B], without a [neurons, B, worlds] array (Fable)
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=1)
    return {"mean": drop.mean(axis=(1, 2)), "lo": lo, "hi": hi, "per_brain": drop.mean(axis=2)}


def tiers(neurons: list, rel: dict, p_sel: float, seed: int) -> dict:
    """The panel: {"high": [...], "medium": [...], "low": [...], "flags": {neuron: [flags]}}, neurons by index."""
    neurons = list(neurons)
    mean, lo, hi = (np.asarray(rel[k], dtype=np.float64) for k in ("mean", "lo", "hi"))
    rng = np.random.default_rng([int(seed), PANEL_STREAM + 1])
    tiebreak = rng.permutation(len(neurons))
    order = sorted(range(len(neurons)), key=lambda i: (-mean[i], tiebreak[i]))  # rank 1 first
    rank = {i: r + 1 for r, i in enumerate(order)}
    flags = {}
    high = order[:3]
    for i in high:
        if not lo[i] > p_sel:
            flags.setdefault(neurons[i], []).append("relatively high only")
    left = [i for i in order if i not in high]
    contains = [i for i in left if lo[i] <= p_sel <= hi[i]]
    medium = [contains[k] for k in sorted(rng.choice(len(contains), size=min(2, len(contains)), replace=False))] \
        if contains else []
    if len(medium) < 2:
        pool = [i for i in left if 4 <= rank[i] <= 20 and i not in medium]
        extra = [pool[k] for k in sorted(rng.choice(len(pool), size=2 - len(medium), replace=False))]
        for i in extra:
            flags.setdefault(neurons[i], []).append("medium from ranks 4-20")
        medium += extra
    left = [i for i in left if i not in medium]
    inside = [i for i in left if -p_sel <= lo[i] and hi[i] <= p_sel]
    if inside:
        low = [inside[int(rng.integers(len(inside)))]]
    else:
        low = [min(left, key=lambda i: (abs(mean[i]), tiebreak[i]))]
        flags.setdefault(neurons[low[0]], []).append("low by smallest absolute drop")
    pick = lambda idx: [neurons[i] for i in idx]  # noqa: E731
    return {"high": pick(high), "medium": pick(medium), "low": pick(low), "flags": flags,
            "rank": {neurons[i]: rank[i] for i in high + medium + low}}
