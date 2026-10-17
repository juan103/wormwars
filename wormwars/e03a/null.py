"""The recovery statistic and its stratified permutation null (experiments/03a-self-consistency/DESIGN.md v7.1 §6).

**Ranking:** per target-brain and connection type, a candidate's score is the mean absolute final weight (or
conductance) of its connection to X over the free searches, 0 if not connected; ties get the average rank.

**Recovery statistic:** the ROC AUC of that ranking against the true partners, averaged with equal weight over the
connection types X has (a type with no true partner, or with every candidate a partner, is unscoreable and left out),
then over the arm's brains.

**Strata:** a candidate's kind (its interface role, mapped sensor then mapped motor, otherwise pharyngeal, otherwise
other; MCL and MCR are pharyngeal and mapped pump motors, so "motor") crossed with its degree bin: tertiles of total
degree (chemical in + chemical out + gap, self-connections not counted) in the graph with X deleted, computed within
each kind, boundaries after ranks ⌊n/3⌋ and ⌊2n/3⌋ by ascending degree; a group of tied degrees is never split and goes
wholly to the lower bin; a bin with fewer than 3 candidates is merged into the bin below it of the same kind (the
lowest bin into the one above). Nothing here reads X's partners.

**The null:** one draw is one permutation of candidate identities within strata. It relabels every connection type's
truth at once and is applied to every brain, search and arm of the target. p = (1 + #{null >= observed}) / (B + 1),
ties counted: the observed value is computed by the same arithmetic as the null's (the identity permutation), so a tie
is exact.
"""

from __future__ import annotations

from math import comb, log10

import numpy as np
from scipy.stats import rankdata

from ..connectome.loader import Connectome
from .reinsert import TYPES, candidates

KINDS = ("sensor", "motor", "pharyngeal", "other")
NULL_STREAM = 0x03A0B


def kinds(con: Connectome, iface) -> np.ndarray:
    """[n] each neuron's kind index into KINDS."""
    sensors = {int(i) for i in iface.sensor_neuron}
    motors = {int(i) for part in (iface.forward_plus, iface.forward_minus, iface.turn_plus, iface.turn_minus,
                                  iface.pump_neurons) for i in part}
    out = np.empty(con.n, dtype=np.int64)
    for i in range(con.n):
        out[i] = (0 if i in sensors else 1 if i in motors else 2 if con.classes[i] == "pharyngeal" else 3)
    return out


def degrees_without(con: Connectome, x: int) -> np.ndarray:
    """[n] total degree with X deleted: chemical in + chemical out + gap partners, self-connections not counted."""
    chem = (np.asarray(con.chem) > 0).copy()
    gap = (np.asarray(con.gap) > 0).copy()
    chem[x, :] = chem[:, x] = False
    gap[x, :] = gap[:, x] = False
    np.fill_diagonal(chem, False)
    np.fill_diagonal(gap, False)
    return chem.sum(0) + chem.sum(1) + gap.sum(1)


def tertile_bins(deg: np.ndarray, min_size: int = 3) -> np.ndarray:
    """Degree bins for one kind's candidates (the rule in the module docstring); bins numbered from 0, ascending."""
    deg = np.asarray(deg)
    n = len(deg)
    if n == 0:
        return np.zeros(0, dtype=np.int64)
    order = np.argsort(deg, kind="stable")
    by_rank = np.empty(n, dtype=np.int64)
    cut1, cut2 = n // 3, (2 * n) // 3
    for r, i in enumerate(order):
        by_rank[i] = 0 if r < cut1 else 1 if r < cut2 else 2
    # a tied group goes wholly to the bin of its lowest rank
    first = {}
    for r, i in enumerate(order):
        first.setdefault(int(deg[i]), by_rank[i])
    raw = np.array([first[int(d)] for d in deg], dtype=np.int64)
    bins = sorted(set(raw.tolist()))
    groups = [set(np.nonzero(raw == b)[0].tolist()) for b in bins]
    while len(groups) > 1 and min(len(g) for g in groups) < min_size:
        i = next(k for k, g in enumerate(groups) if len(g) < min_size)
        j = 1 if i == 0 else i - 1
        groups[j] |= groups[i]
        del groups[i]
    out = np.empty(n, dtype=np.int64)
    for b, g in enumerate(groups):
        out[list(g)] = b
    return out


def strata(con: Connectome, iface, x: int) -> np.ndarray:
    """[K] each candidate's stratum id (kind x degree bin), over `candidates(con.n, x)`."""
    c = candidates(con.n, x)
    kd, dg = kinds(con, iface)[c], degrees_without(con, x)[c]
    out = np.empty(len(c), dtype=np.int64)
    for k in range(len(KINDS)):
        sel = np.nonzero(kd == k)[0]
        out[sel] = 10 * k + tertile_bins(dg[sel])
    return out


def permutations(strat: np.ndarray, B: int, seed: int) -> np.ndarray:
    """[B, K]: perm[b, k] is the candidate whose labels candidate k takes in draw b, always in k's stratum."""
    strat = np.asarray(strat)
    K = len(strat)
    rng = np.random.default_rng([int(seed), NULL_STREAM])
    base = np.argsort(strat, kind="stable")  # positions grouped by stratum
    keys = strat[None, :] + rng.random((B, K)) * 0.5  # strata are integers; the key stays inside its stratum
    order = np.argsort(keys, axis=1, kind="stable")
    perm = np.empty((B, K), dtype=np.int64)
    rows = np.arange(B)[:, None]
    perm[rows, base[None, :]] = order
    return perm


def ranks(score: np.ndarray) -> np.ndarray:
    """Average ranks (1-based) of a candidate score vector, ties averaged."""
    return rankdata(np.asarray(score, dtype=np.float64), method="average")


def scoreable(labels: np.ndarray) -> bool:
    n1 = int(np.asarray(labels).sum())
    return 0 < n1 < len(labels)


def auc_from_ranks(r: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """AUC for ranks r [..., K] against labels [B, K] (boolean), by the Mann-Whitney sum: [B, ...]."""
    labels = np.asarray(labels, dtype=np.float64)
    n1 = labels.sum(axis=-1)
    n0 = labels.shape[-1] - n1
    r = np.asarray(r, dtype=np.float64)
    s = labels @ r.reshape(-1, r.shape[-1]).T  # [B, prod(...)]
    s = s.reshape(labels.shape[0], *r.shape[:-1])
    shape = (labels.shape[0],) + (1,) * (r.ndim - 1)
    return (s - (n1 * (n1 + 1) / 2).reshape(shape)) / (n1 * n0).reshape(shape)


def recovery(rankings: dict, truth: dict, perm: np.ndarray | None = None) -> dict:
    """The recovery statistic and its per-type parts.

    `rankings[type]` is [brains, K] candidate scores (one row per brain), `truth[type]` the true partners [K].
    `perm` [B, K] gives the null draws; None gives the observed value through the identity permutation.
    Returns {"stat": [B] (mean over brains of the mean over scoreable types), "per_type": {type: [B, brains]},
    "types": the scoreable types, "per_brain": [B, brains]}."""
    K = len(next(iter(truth.values())))
    perm = np.arange(K)[None, :] if perm is None else np.asarray(perm)
    types = [t for t in TYPES if scoreable(truth[t])]
    if not types:
        raise ValueError("no scoreable connection type")
    per_type = {}
    for t in types:
        lab = np.asarray(truth[t], dtype=bool)[perm]  # candidate k takes candidate perm[k]'s label
        rk = np.stack([ranks(row) for row in np.atleast_2d(rankings[t])])
        per_type[t] = auc_from_ranks(rk, lab)  # [B, brains]
    per_brain = np.mean([per_type[t] for t in types], axis=0)
    return {"stat": per_brain.mean(axis=1), "per_type": per_type, "types": types, "per_brain": per_brain}


def p_value(null: np.ndarray, observed: float) -> float:
    null = np.asarray(null)
    return float((1 + int((null >= observed).sum())) / (len(null) + 1))


def test(rankings: dict, truth: dict, strat: np.ndarray, B: int, seed: int) -> dict:
    """The stratified enrichment test of one target-arm: observed statistic, null mean, p (one-sided)."""
    obs = recovery(rankings, truth)
    null = recovery(rankings, truth, permutations(strat, B, seed))
    o = float(obs["stat"][0])
    return {"observed": o, "null_mean": float(null["stat"].mean()), "p": p_value(null["stat"], o), "B": int(B),
            "types": obs["types"], "per_type": {t: obs["per_type"][t][0].tolist() for t in obs["types"]},
            "per_brain": obs["per_brain"][0].tolist()}


def support(truth: dict, strat: np.ndarray) -> dict:
    """How many distinct joint truth patterns (over the types together) the within-strata permutations can produce:
    the product over strata of the multinomial of the label vectors inside it (Astra)."""
    strat = np.asarray(strat)
    lab = np.stack([np.asarray(truth[t], dtype=np.int64) for t in TYPES], axis=1)
    code = lab @ np.array([1, 2, 4])
    total = 1
    for s in np.unique(strat):
        inside = code[strat == s]
        n = len(inside)
        k = 1
        left = n
        for c in np.unique(inside):
            m = int((inside == c).sum())
            k *= comb(left, m)
            left -= m
        total *= k
    return {"patterns": total, "log10": log10(total) if total > 0 else float("-inf")}


def strata_report(truth: dict, strat: np.ndarray) -> dict:
    strat = np.asarray(strat)
    out = {}
    for s in np.unique(strat):
        sel = strat == s
        out[f"{KINDS[int(s) // 10]}/{int(s) % 10}"] = {"size": int(sel.sum()),
                                                       **{t: int(np.asarray(truth[t])[sel].sum()) for t in TYPES}}
    return out


def precision_at_k(score: np.ndarray, labels_b: np.ndarray) -> np.ndarray:
    """[B] precision among the top k candidates (k = the number of true partners), ties at the k-th place shared
    in proportion (the expected precision over random tie-breaking)."""
    score = np.asarray(score, dtype=np.float64)
    labels_b = np.atleast_2d(np.asarray(labels_b, dtype=np.float64))
    k = int(labels_b[0].sum())
    if k == 0:
        return np.full(labels_b.shape[0], np.nan)
    srt = np.sort(score)[::-1]
    kth = srt[k - 1]
    above = score > kth
    tied = score == kth
    w = above.astype(np.float64) + tied * ((k - above.sum()) / tied.sum())
    return labels_b @ w / k


def average_precision(score: np.ndarray, labels_b: np.ndarray) -> np.ndarray:
    """[B] area under the precision-recall curve (average precision), tied scores treated as one threshold."""
    score = np.asarray(score, dtype=np.float64)
    labels_b = np.atleast_2d(np.asarray(labels_b, dtype=np.float64))
    levels = np.unique(score)[::-1]
    out = np.zeros(labels_b.shape[0])
    n1 = labels_b.sum(axis=1)
    tp_prev = np.zeros(labels_b.shape[0])
    seen = 0
    for lv in levels:
        sel = score == lv
        seen += int(sel.sum())
        tp = tp_prev + labels_b[:, sel].sum(axis=1)
        out += (tp - tp_prev) / np.maximum(n1, 1) * (tp / seen)
        tp_prev = tp
    return out
