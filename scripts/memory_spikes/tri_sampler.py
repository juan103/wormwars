"""Spike: degree-preserving rewiring that moves a graph's directed 3-cycle count to a target, carrying each edge's
weight with it; the gap layer is untouched. SH-tri raises a shuffle to N2's count; N2-detri lowers N2 to a shuffle's.
In- and out-degrees are kept exactly (the samplers' double-edge swap a->b, c->d => a->d, c->b)."""
import numpy as np


def cycles3(A):
    return int(np.trace(A @ A @ A) // 3)


def _through(A, x, y):  # directed 3-cycles that would use edge x->y: y->z->x
    return int((A[y, :] & A[:, x]).sum())


def _ff_through(A, x, y):  # feed-forward triangles using edge x->y in any of its three roles
    return int((A[x, :] & A[:, y]).sum() + (A[y, :] & A[x, :]).sum() + (A[:, x] & A[:, y]).sum())


def fft(A):
    return int(((A @ A) * A).sum())


def rewire(chem, target, seed, max_attempts=4_000_000, tol=0.005, extra_swaps=2000, metric="cycles3"):
    rng = np.random.default_rng(seed)
    A = (chem > 0).astype(np.int64)
    W = chem.astype(np.float64).copy()
    np.fill_diagonal(A, 0)  # autapses kept as they are, outside the chain
    diag = np.diag(chem).copy()
    edges = np.argwhere(A > 0)
    through = _through if metric == "cycles3" else _ff_through
    count = cycles3(A) if metric == "cycles3" else fft(A)
    up = target > count
    hit = None
    for att in range(max_attempts):
        e1, e2 = rng.integers(0, len(edges), 2)
        if e1 == e2:
            continue
        a, b = edges[e1]
        c, d = edges[e2]
        if a == d or c == b or A[a, d] or A[c, b]:
            continue
        delta = 0
        A[a, b] = 0; delta -= through(A, a, b)  # noqa: E702
        A[c, d] = 0; delta -= through(A, c, d)  # noqa: E702
        A[a, d] = 1; delta += through(A, a, d)  # noqa: E702
        A[c, b] = 1; delta += through(A, c, b)  # noqa: E702
        new = count + delta
        if hit is None:
            good = (delta > 0) if up else (delta < 0)
        else:  # at the target: keep mixing within the tolerance
            good = abs(new - target) <= tol * target
        if not good:
            A[a, d] = 0; A[c, b] = 0; A[a, b] = 1; A[c, d] = 1  # noqa: E702
            continue
        W[a, d], W[c, b] = W[a, b], W[c, d]
        W[a, b] = W[c, d] = 0
        edges[e1] = (a, d)
        edges[e2] = (c, b)
        count = new
        if hit is None and ((up and count >= target) or (not up and count <= target)):
            hit = att
            mixed = 0
        if hit is not None:
            mixed += 1
            if mixed >= extra_swaps:
                break
    out = np.where(A > 0, W, 0.0)
    np.fill_diagonal(out, diag)
    return out.astype(np.float32), {"metric": metric, "value": count, "attempts": att + 1, "hit_at": hit}


def describe(chem):
    A = (chem > 0).astype(np.int64)
    off = A.copy(); np.fill_diagonal(off, 0)  # noqa: E702
    return {"cycles3": cycles3(off), "recip_pairs": int(((off > 0) & (off.T > 0)).sum() // 2),
            "ff_triangles": int(((off @ off) * off).sum()), "edges": int(off.sum()),
            "in": off.sum(0).tolist()[:3], "out": off.sum(1).tolist()[:3]}
