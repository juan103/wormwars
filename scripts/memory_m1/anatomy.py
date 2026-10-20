"""M1, part C (docs/memory/M1-PLAN.md, draft 8): M3's anatomy predictors, frozen in the plan before any were computed.
K is the turn read-out with its one-step chemical in-neighbours (the two-step versions are secondary). C1 the density
inside K, C1' the same over a stub-model reference, C2 write-read walks from the food sensors, C3 the anatomy core.
Within-ensemble Spearman correlations against 03mc's outcomes (runs/memory-m1/accounting.json, written by part A), and
the inspection of the top 5 graphs per ensemble. Writes runs/memory-m1/anatomy.json."""
import json

import numpy as np
from scipy.stats import spearmanr

from common import (ENSEMBLES, FOOD_SENSORS, NAMES, OUT, READOUT, ROOT, S, adjacency, anatomy_core, dump, ensemble_of,
                    measurements, neighbourhood)

OUTCOMES = ("share30", "q75_r30", "cohort", "growth_frac30")
PREDICTORS = ("K_size", "C1", "C1p", "C2", "K2_size", "C1_2", "C1p_2")


def density(A, K):
    k = int(K.sum())
    inside = int(A[np.ix_(K, K)].sum())
    kout, kin, E = A.sum(1), A.sum(0), A.sum()
    expected = (np.outer(kout[K], kin[K]).sum() - (kout[K] * kin[K]).sum()) / E
    return k, inside / (k * (k - 1)), float(inside / expected)


def predictors(A):
    k1, c1, c1p = density(A, neighbourhood(A, 1))
    k2, c12, c1p2 = density(A, neighbourhood(A, 2))
    s = np.zeros(len(A))
    s[FOOD_SENSORS] = 1
    rr = np.zeros(len(A))
    rr[READOUT] = 1
    A2 = A @ A
    w, r = s @ (A + A2), (A + A2) @ rr
    return {"K_size": k1, "C1": c1, "C1p": c1p, "C2": float(np.log((w * r).sum())),
            "K2_size": k2, "C1_2": c12, "C1p_2": c1p2}


def kept_inside(A, A0, idx):
    m = np.zeros(len(A), bool)
    m[idx] = True
    inside0 = A0[np.ix_(m, m)]
    return float((A[np.ix_(m, m)] & inside0).sum() / inside0.sum())


u = measurements()
graphs = sorted(k.split("/")[1] for k in u if k.startswith("graph/") and k.endswith("/long"))
acc = json.load(open(OUT / "accounting.json"))
A0 = adjacency(S.CON.chem).astype(bool)
core = anatomy_core(S.CON.chem)
b7 = json.load(open(ROOT / "runs" / "memory-spikes" / "batch7.json"))["sets"]
top30_start = json.load(open(ROOT / "runs" / "memory-spikes" / "batch6.json"))["lists"]["top30_start"]
out = {"N2": predictors(A0.astype(np.int64)), "core30_anatomy": core,
       "core_overlap_batch7_hubs": len(set(core) & set(b7["hubs"])),
       "core_overlap_top30_start": len(set(core) & set(top30_start)), "ensembles": {}}
pred, adj = {}, {}
for name in graphs:
    z = np.load(ROOT / "runs" / "p4mc" / "graphs" / f"{name}.npz", allow_pickle=False)
    adj[name] = adjacency(z["chem"])
    pred[name] = predictors(adj[name])
idx_start = [NAMES.index(x) for x in top30_start]
idx_core = [NAMES.index(x) for x in core]
for e in ENSEMBLES:
    gs = [n for n in graphs if ensemble_of(n) == e]
    half = np.array([int(n.rsplit("-", 1)[1]) % 2 for n in gs])
    rec = {}
    for p in PREDICTORS:
        x = np.array([pred[n][p] for n in gs])
        rec[p] = {"N2_percentile": float((x < out["N2"][p]).mean()), "median": float(np.median(x))}
        for o in OUTCOMES:
            y = np.array([acc["graphs"][n][o] for n in gs])
            rec[p][o] = {"all": float(spearmanr(x, y).correlation),
                         "even": float(spearmanr(x[half == 0], y[half == 0]).correlation),
                         "odd": float(spearmanr(x[half == 1], y[half == 1]).correlation)}
    inspect = {}
    for o in ("share30", "cohort"):
        top = sorted(gs, key=lambda n: -acc["graphs"][n][o])[:5]
        inspect[o] = [{"graph": n, o: acc["graphs"][n][o], **pred[n],
                       "kept_top30_start_edges": kept_inside(adj[n].astype(bool), A0, idx_start),
                       "kept_core30_anatomy_edges": kept_inside(adj[n].astype(bool), A0, idx_core)} for n in top]
    rec["inspection"] = inspect
    rec["kept_median_all"] = {"top30_start": float(np.median([kept_inside(adj[n].astype(bool), A0, idx_start) for n in gs])),
                              "core30_anatomy": float(np.median([kept_inside(adj[n].astype(bool), A0, idx_core) for n in gs]))}
    out["ensembles"][e] = rec
out["graphs"] = pred
dump(out, "anatomy.json")
print("N2", out["N2"], "\ncore30_anatomy", core, "overlaps", out["core_overlap_batch7_hubs"], out["core_overlap_top30_start"])
for e in ENSEMBLES:
    for p in ("C1", "C1p", "C2"):
        r = out["ensembles"][e][p]
        print(e, p, "N2 pct", round(r["N2_percentile"], 2), {o: round(r[o]["all"], 2) for o in OUTCOMES})
