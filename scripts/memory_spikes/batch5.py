"""Batch 5: the control batch 2 lacked. Removing N2's triangles cut its retention, but any rewiring of that size might.
Sham arms move the same fraction of N2's chemical edges while holding both triangle counts (3-cycles and
feed-forward) within 0.5%; free arms move the same fraction with no constraint. Same panels as batches 1-2."""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import spikes as S  # noqa: E402
from tri_sampler import _ff_through, _through, cycles3, describe, fft, rewire  # noqa: E402

N, FOLLOW, SEED = 1024, 100, 7100
OUT = S.ROOT / "runs" / "memory-spikes"
res = {}


def moved(a, b):
    A, B = a > 0, b > 0
    np.fill_diagonal(A, False)
    np.fill_diagonal(B, False)
    return float(1 - (A & B).sum() / A.sum())


def swaps(chem, frac, seed, hold, tol=0.005):
    """Weight-carrying double-edge swaps until `frac` of the off-diagonal edges have moved; with `hold`, each swap must
    keep both triangle counts within `tol` of the start."""
    rng = np.random.default_rng(seed)
    A = (chem > 0).astype(np.int64)
    np.fill_diagonal(A, 0)
    A0 = A.copy()
    W = chem.astype(np.float64).copy()
    diag = np.diag(chem).copy()
    edges = np.argwhere(A > 0)
    c0, f0 = cycles3(A), fft(A)
    c, f = c0, f0
    att = acc = 0
    while True:
        att += 1
        e1, e2 = rng.integers(0, len(edges), 2)
        if e1 == e2:
            continue
        a, b = edges[e1]
        cc, d = edges[e2]
        if a == d or cc == b or A[a, d] or A[cc, b]:
            continue
        A[a, b] = 0; dc = -_through(A, a, b); df = -_ff_through(A, a, b)  # noqa: E702
        A[cc, d] = 0; dc -= _through(A, cc, d); df -= _ff_through(A, cc, d)  # noqa: E702
        A[a, d] = 1; dc += _through(A, a, d); df += _ff_through(A, a, d)  # noqa: E702
        A[cc, b] = 1; dc += _through(A, cc, b); df += _ff_through(A, cc, b)  # noqa: E702
        if hold and (abs(c + dc - c0) > tol * c0 or abs(f + df - f0) > tol * f0):
            A[a, d] = 0; A[cc, b] = 0; A[a, b] = 1; A[cc, d] = 1  # noqa: E702
            continue
        W[a, d], W[cc, b] = W[a, b], W[cc, d]
        W[a, b] = W[cc, d] = 0
        edges[e1] = (a, d)
        edges[e2] = (cc, b)
        c, f = c + dc, f + df
        acc += 1
        if acc % 50 == 0 and 1 - (A & A0).sum() / A0.sum() >= frac:
            break
    out = np.where(A > 0, W, 0.0)
    np.fill_diagonal(out, diag)
    return out.astype(np.float32), {"attempts": att, "accepted": acc, "cycles3": int(c), "ff": int(f)}


def run(key, chem, info):
    t = time.time()
    con = S.masks(chem, S.CON.gap, key)
    g, cfg = S.genomes(con, N, SEED)
    h = S.probe(g, cfg, follow=FOLLOW)
    res[key] = {**S.summary(h), "structure": describe(chem), "moved": moved(S.CON.chem, chem), "info": info,
                "seconds": round(time.time() - t, 1)}
    print(key, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res[key].items()}, flush=True)
    json.dump(res, open(OUT / "batch5.json", "w"), indent=1)


fr = []
for i in range(3):
    for metric, target in (("cycles3", 1346), ("ff", 4900)):  # batch 2's surgery, regenerated (same seeds)
        chem, _ = rewire(S.CON.chem, target, 200 + i, metric=metric)
        fr.append(moved(S.CON.chem, chem))
frac = float(np.mean(fr))
res["surgery_moved_fractions"] = fr
print("surgery moved", [round(x, 3) for x in fr], "target", round(frac, 3), flush=True)
for i in range(3):
    chem, info = swaps(S.CON.chem, frac, 300 + i, hold=True)
    run(f"N2/sham{i}", chem, info)
    chem, info = swaps(S.CON.chem, frac, 400 + i, hold=False)
    run(f"N2/free{i}", chem, info)
print("done")
