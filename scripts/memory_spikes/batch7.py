"""Batch 7: the head core. Batch 5's sham (triangle counts held) kept N2's retention, but it also kept 58% of the
internal edges of the 30-neuron head core (batch 6's top30_start), against 27-36% under free rewiring. Which matters?
- core-dissolved: each weight-carrying double-edge swap pairs one core-internal edge with one edge outside the core
  (a->b in the core, c->d outside give a->d and c->b, both crossing), until the core keeps 30% of its internal edges
  (the free level); degrees are kept, about 140 swaps; (swaps among edges touching the core cannot lower the count)
- periphery-scrambled: the same number of swaps among edges with no endpoint in the core;
- core-frozen shuffle: every edge free to swap except the core's internal edges, to 73% moved (batch 5's size);
- hub-frozen control: the same, freezing the internal edges of the 30 highest-degree neurons outside the core.
Same panels as batches 1, 2 and 5 (seed 7100), plus the held-out panel (seed 7400) for every arm."""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import spikes as S  # noqa: E402
from tri_sampler import describe  # noqa: E402

OUT = S.ROOT / "runs" / "memory-spikes"
names = list(S.CON.names)
CORE = [names.index(x) for x in json.load(open(OUT / "batch6.json"))["lists"]["top30_start"]]
res = {}
A0 = S.CON.chem > 0
np.fill_diagonal(A0, False)


def rewire(chem, seed, pick, freeze, stop):
    """pick(a, b) says whether edge a->b may be chosen; freeze is a mask of edges that never move; stop(A, acc) ends."""
    rng = np.random.default_rng(seed)
    A = (chem > 0)
    np.fill_diagonal(A, False)
    W = chem.astype(np.float64).copy()
    diag = np.diag(chem).copy()
    edges = [tuple(e) for e in np.argwhere(A) if pick(*e) and not freeze[e[0], e[1]]]
    acc = att = 0
    while not stop(A, acc):
        att += 1
        if att > 5_000_000:
            raise RuntimeError("rewire did not reach its target")
        i, j = rng.integers(0, len(edges), 2)
        if i == j:
            continue
        (a, b), (c, d) = edges[i], edges[j]
        if a == d or c == b or A[a, d] or A[c, b]:
            continue
        A[a, b] = A[c, d] = False
        A[a, d] = A[c, b] = True
        W[a, d], W[c, b] = W[a, b], W[c, d]
        W[a, b] = W[c, d] = 0
        edges[i], edges[j] = (a, d), (c, b)
        acc += 1
    out = np.where(A, W, 0.0)
    np.fill_diagonal(out, diag)
    return out.astype(np.float32), acc


def dissolve(chem, seed, frac):
    rng = np.random.default_rng(seed)
    A = chem > 0
    np.fill_diagonal(A, False)
    W = chem.astype(np.float64).copy()
    diag = np.diag(chem).copy()
    ins = [tuple(e) for e in np.argwhere(A) if incore[e[0]] and incore[e[1]]]
    outs = [tuple(e) for e in np.argwhere(A) if not incore[e[0]] and not incore[e[1]]]
    goal = int(frac * len(ins))
    acc = 0
    while len(ins) > goal:
        i, j = rng.integers(0, len(ins)), rng.integers(0, len(outs))
        (a, b), (c, d) = ins[i], outs[j]
        if A[a, d] or A[c, b]:
            continue
        A[a, b] = A[c, d] = False
        A[a, d] = A[c, b] = True
        W[a, d], W[c, b] = W[a, b], W[c, d]
        W[a, b] = W[c, d] = 0
        ins.pop(i)
        outs.pop(j)
        acc += 1
    out = np.where(A, W, 0.0)
    np.fill_diagonal(out, diag)
    return out.astype(np.float32), acc


def internal(A, idx):
    m = np.zeros(S.CON.n, bool)
    m[idx] = True
    return A[np.ix_(m, m)] & A0[np.ix_(m, m)]


def kept(A):
    return float((A & A0).sum() / A0.sum())


def run(key, chem, info):
    for seed in (7100, 7400):
        t = time.time()
        con = S.masks(chem, S.CON.gap, key)
        g, cfg = S.genomes(con, 1024, seed)
        h = S.probe(g, cfg, follow=100)
        B = chem > 0
        np.fill_diagonal(B, False)
        res[f"{key}/{seed}"] = {**S.summary(h), "structure": describe(chem), "kept_all": kept(B),
                                "kept_core_internal": float(internal(B, CORE).sum() / internal(A0, CORE).sum()),
                                "info": info, "seconds": round(time.time() - t, 1)}
        print(key, seed, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res[f"{key}/{seed}"].items()
                          if k != "structure"}, flush=True)
        json.dump(res, open(OUT / "batch7.json", "w"), indent=1)


incore = np.zeros(S.CON.n, bool)
incore[CORE] = True
deg = A0.sum(0) + A0.sum(1)
HUBS = [j for j in np.argsort(-deg) if not incore[j]][:30]
inhub = np.zeros(S.CON.n, bool)
inhub[HUBS] = True
res["sets"] = {"core": [names[j] for j in CORE], "hubs": [names[j] for j in HUBS],
               "core_internal_edges": int(internal(A0, CORE).sum()), "hub_internal_edges": int(internal(A0, HUBS).sum()),
               "core_mean_degree": float(deg[CORE].mean()), "hub_mean_degree": float(deg[HUBS].mean())}
print(res["sets"], flush=True)
none = np.zeros_like(A0)
for k in range(3):
    chem, acc = dissolve(S.CON.chem, 500 + k, 0.30)
    run(f"N2/core-dissolved{k}", chem, {"accepted": acc})
    chem, acc2 = rewire(S.CON.chem, 600 + k, lambda a, b: not (incore[a] or incore[b]), none,
                        lambda A, a2, n=acc: a2 >= n)
    run(f"N2/periphery-scrambled{k}", chem, {"accepted": acc2})
    fz = np.zeros_like(A0)
    fz[np.ix_(incore, incore)] = A0[np.ix_(incore, incore)]
    chem, acc3 = rewire(S.CON.chem, 700 + k, lambda a, b: True, fz,
                        lambda A, acc: acc % 50 == 0 and kept(A) <= 0.273)
    run(f"N2/core-frozen-shuffle{k}", chem, {"accepted": acc3})
    fz = np.zeros_like(A0)
    fz[np.ix_(inhub, inhub)] = A0[np.ix_(inhub, inhub)]
    chem, acc4 = rewire(S.CON.chem, 800 + k, lambda a, b: True, fz,
                        lambda A, acc: acc % 50 == 0 and kept(A) <= 0.273)
    run(f"N2/hub-frozen-shuffle{k}", chem, {"accepted": acc4})
print("done")
