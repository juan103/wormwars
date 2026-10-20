"""Spike: do simple structural features of a graph predict its retention, across 640 null graphs? Where is N2?
(Fable 2 autapses, Fable 3 heavy reciprocal loops, Fable 5 / Astra 2 gap junctions, Fable 8 modules, owner's loops.)"""
import glob
import json
import os
import re
import sys

import numpy as np
from scipy import stats as st

ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
sys.path.insert(0, ROOT)
from wormwars.connectome.loader import load_connectome  # noqa: E402

rep = json.load(open(f"{ROOT}/experiments/03mc-p4-confirm/report.json"))
ticks = rep["descriptive"]["curves"]["ticks"]
t30 = ticks.index(30)
m = json.load(open(f"{ROOT}/experiments/03mc-p4-confirm/measurements.json"))["units"]


def features(chem, gap):
    c = chem / chem[chem > 0].mean()
    g = gap / gap[gap > 0].mean()
    off = c.copy()
    np.fill_diagonal(off, 0)
    recip = (off > 0) & (off.T > 0)
    b = (off > 0).astype(float)
    return {
        "autapses": int((np.diag(c) > 0).sum()),
        "autapse_weight": float(np.diag(c).sum()),
        "recip_pairs": int(recip.sum() // 2),
        "recip_weight_product": float((off * off.T).sum() / 2),
        "cycles3": float(np.trace(b @ b @ b) / 3),
        "weighted_cycles3": float(np.trace(off @ off @ off) / 3),
        "gap_chem_overlap": float((g * ((off + off.T) > 0)).sum() / g.sum()),
        "top_edge_share": float(np.sort(off[off > 0])[::-1][: int(0.05 * (off > 0).sum())].sum() / off.sum()),
    }


def tail(path):
    d = np.abs(np.load(path, allow_pickle=False)["diff"]).astype(float)
    ok = d[0] >= 1e-3
    per = d[t30, ok] / d[0, ok]
    return {"share30": d[t30].mean() / d[0].mean(), "q75": float(np.quantile(per, 0.75)),
            "grow": float((per > 1).mean()), "median": float(np.median(per)),
            "corr": float(np.corrcoef(np.log(d[0, ok]), per)[0, 1])}


con = load_connectome()
n2f = features(np.asarray(con.chem, float), np.asarray(con.gap, float))
n2t = tail(f"{ROOT}/runs/p4mc/arrays/N2__long.npz")
rows = []
for p in sorted(glob.glob(f"{ROOT}/runs/p4mc/graphs/*.npz")):
    name = os.path.basename(p)[:-4]
    a = f"{ROOT}/runs/p4mc/arrays/graph__{name}__long.npz"
    if not os.path.exists(a):
        continue
    z = np.load(p, allow_pickle=False)
    rows.append({"name": name, "ens": re.sub(r"-\d+$", "", name), **features(z["chem"].astype(float), z["gap"].astype(float)),
                 **tail(a)})
print("graphs", len(rows))
F = list(n2f)
T = ["share30", "q75", "grow", "median", "corr"]
print("feature: N2 value | null median [min,max] | Spearman with share30, q75, grow, corr (pooled 640)")
for f in F:
    x = np.array([r[f] for r in rows])
    rho = [st.spearmanr(x, [r[t] for r in rows]).correlation for t in ("share30", "q75", "grow", "corr")]
    print(f"{f:22s} N2 {n2f[f]:10.3f} | {np.median(x):10.3f} [{x.min():.3f}, {x.max():.3f}] | "
          + " ".join(f"{v:+.2f}" for v in rho))
# within-ensemble correlations for the strongest candidates
for f in F:
    out = []
    for e in ("SH", "SH-route", "SH-class", "SH-mirror", "SH-recip"):
        sub = [r for r in rows if r["ens"] == e]
        out.append(st.spearmanr([r[f] for r in sub], [r["share30"] for r in sub]).correlation)
    print(f"within-ensemble rho(share30) {f:22s}", " ".join(f"{v:+.2f}" for v in out))
print("N2 tail", {k: round(v, 3) for k, v in n2t.items()})

# extrapolation: fit share30 and grow on each feature (and a few together) across the nulls, predict N2
y = {t: np.array([r[t] for r in rows]) for t in ("share30", "grow", "q75")}
sets = [["cycles3"], ["weighted_cycles3"], ["autapse_weight"], ["recip_weight_product"], ["gap_chem_overlap"],
        ["weighted_cycles3", "autapse_weight", "recip_weight_product", "gap_chem_overlap"]]
for s in sets:
    X = np.column_stack([np.ones(len(rows))] + [[r[f] for r in rows] for f in s])
    x0 = np.array([1.0] + [n2f[f] for f in s])
    out = []
    for t in y:
        beta, *_ = np.linalg.lstsq(X, y[t], rcond=None)
        r2 = 1 - ((y[t] - X @ beta) ** 2).sum() / ((y[t] - y[t].mean()) ** 2).sum()
        out.append(f"{t}: R2 {r2:.2f} pred N2 {x0 @ beta:.3f} (obs {n2t[t]:.3f}, null med {np.median(y[t]):.3f})")
    print("+".join(s), "|", "; ".join(out))

# bootstrap interval of the extrapolated prediction, and other walk/loop measures
def more(chem):
    c = chem / chem[chem > 0].mean()
    off = c.copy(); np.fill_diagonal(off, 0)
    b = (off > 0).astype(float)
    und = ((b + b.T) > 0).astype(float)
    deg = und.sum(1)
    tri_und = np.trace(und @ und @ und) / 6
    trans = 3 * tri_und / ((deg * (deg - 1)).sum() / 2)
    ev = np.abs(np.linalg.eigvals(b)).max()
    return {"walks4": float(np.trace(np.linalg.matrix_power(b, 4))), "transitivity": float(trans),
            "spectral_radius_binary": float(ev),
            "ff_triangles": float(((b @ b) * b).sum())}  # a->b->c with a->c
n2m = more(np.asarray(con.chem, float))
for r in rows:
    z = np.load(f"{ROOT}/runs/p4mc/graphs/{r['name']}.npz", allow_pickle=False); r.update(more(z["chem"].astype(float)))
rng = np.random.default_rng(0)
for f in ["cycles3", "walks4", "transitivity", "spectral_radius_binary", "ff_triangles"]:
    x = np.array([r[f] for r in rows]); v = n2f.get(f, n2m.get(f))
    X = np.column_stack([np.ones(len(x)), x]); yy = y["share30"]
    preds = []
    for _ in range(2000):
        i = rng.integers(0, len(x), len(x)); beta, *_ = np.linalg.lstsq(X[i], yy[i], rcond=None); preds.append(beta[0] + beta[1] * v)
    beta, *_ = np.linalg.lstsq(X, yy, rcond=None)
    print(f"{f:24s} N2 {v:9.3f} nulls [{x.min():.3f},{x.max():.3f}] rho {st.spearmanr(x, yy).correlation:+.2f} "
          f"pred {beta[0]+beta[1]*v:.3f} 95% [{np.quantile(preds,.025):.3f},{np.quantile(preds,.975):.3f}]")
