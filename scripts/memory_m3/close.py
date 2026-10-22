"""M3's close (docs/memory/MEMORY-ROADMAP.md, M3; the direction agreed in docs/reviews/20261022-m3-m4-direction/).

M1's part C froze M3's anatomy predictors (C1, C1', C2 and the anatomy core C3, defined from N2's anatomy) and tested
them within ensembles on 03mc's 640 graphs. This adds, as description and without simulation, the same frozen
predictors against M2's census measures, on the census's graphs: the 30 reference graphs, the 10 selected graphs and
batch 7's six arms (Fable: the only contrast where the predictors can earn or lose credit). One new quantity, labelled
so: the fraction of N2's chemical edges inside C3 that a graph keeps (N2-relative, not a per-graph anatomy rule).
density() and predictors() are copied from scripts/memory_m1/anatomy.py, which runs on import.

    py scripts/memory_m3/close.py      # seconds; writes runs/memory-m3/close.json and prints the table
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m1"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
from common import FOOD_SENSORS, NAMES, READOUT, S, adjacency, anatomy_core, ensemble_of, neighbourhood  # noqa: E402
import census  # noqa: E402

OUT = ROOT / "runs" / "memory-m3"
CENSUS = ROOT / "runs" / "memory-m2-census"
PRED = ("K_size", "C1", "C1p", "C2", "C3_kept")
MEASURES = ("S_frac", "S30", "rhoF30", "s30")


def density(A, K):  # copied from scripts/memory_m1/anatomy.py
    k = int(K.sum())
    inside = int(A[np.ix_(K, K)].sum())
    kout, kin, E = A.sum(1), A.sum(0), A.sum()
    expected = (np.outer(kout[K], kin[K]).sum() - (kout[K] * kin[K]).sum()) / E
    return k, inside / (k * (k - 1)), float(inside / expected)


def predictors(A, A0, core):  # anatomy.py's one-step predictors, and C3's kept fraction (new)
    k1, c1, c1p = density(A, neighbourhood(A, 1))
    s = np.zeros(len(A))
    s[FOOD_SENSORS] = 1
    rr = np.zeros(len(A))
    rr[READOUT] = 1
    A2 = A @ A
    w, r = s @ (A + A2), (A + A2) @ rr
    m = np.zeros(len(A), bool)
    m[core] = True
    inside0 = A0[np.ix_(m, m)].astype(bool)
    kept = float((A[np.ix_(m, m)].astype(bool) & inside0).sum() / inside0.sum())
    return {"K_size": k1, "C1": c1, "C1p": c1p, "C2": float(np.log((w * r).sum())), "C3_kept": kept}


def measures(panel):
    """From the census's committed panel record: separate-states fraction of eligible genomes, S(30), rho_F(30), s(30)."""
    r = json.load(open(CENSUS / f"{panel}.json"))
    gs = r["genomes"]
    den = sum(g["a"] for g in gs)
    sep = [g for g in gs if g["class"].startswith("separate states")]
    fad = [g for g in gs if g["class"] == "fading"]
    return {"S_frac": len(sep) / len(gs), "S30": sum(g["d30"] for g in sep) / den,
            "rhoF30": sum(g["d30"] for g in fad) / sum(g["a"] for g in fad), "s30": r["eligible_share"]["30"]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    A0 = adjacency(S.CON.chem)
    core = [NAMES.index(x) for x in anatomy_core(S.CON.chem)]
    rows = {"N2": {"role": "N2", **predictors(A0, A0, core), **measures("N2__7600"),
                   "measures_7700": measures("N2__7700")}}
    for name, gname, seed, role in census.panels():
        if role == "N2":
            continue
        if role in ("core-frozen-shuffle", "hub-frozen-shuffle"):
            chem = census.batch7_graph(role, int(gname[len(role):]))[0].chem
        else:
            chem = np.load(ROOT / "runs" / "p4mc" / "graphs" / f"{gname}.npz", allow_pickle=False)["chem"]
        rows[gname] = {"role": role, **predictors(adjacency(chem), A0, core), **measures(name)}

    ref = [g for g, v in rows.items() if v["role"] == "reference"]
    corr = {}
    for p in PRED:
        corr[p] = {}
        for m in MEASURES:
            x, y = np.array([rows[g][p] for g in ref]), np.array([rows[g][m] for g in ref])
            corr[p][m] = None if np.ptp(x) == 0 or np.ptp(y) == 0 else float(spearmanr(x, y).correlation)
    rank = {p: {"N2_above_reference": int(sum(rows[g][p] < rows["N2"][p] for g in ref)),
                "N2_below_reference": int(sum(rows[g][p] > rows["N2"][p] for g in ref))} for p in PRED}
    json.dump({"rows": rows, "spearman_reference": corr, "N2_rank_reference": rank,
               "core30_anatomy": anatomy_core(S.CON.chem)}, open(OUT / "close.json", "w"), indent=1)

    print("graph                          role                 " + " ".join(f"{p:>8s}" for p in PRED) + " | "
          + " ".join(f"{m:>7s}" for m in MEASURES))
    for g, v in rows.items():
        print(f"{g:30s} {v['role']:20s} " + " ".join(f"{v[p]:8.3f}" for p in PRED) + " | "
              + " ".join(f"{v[m]:7.3f}" for m in MEASURES))
    print("\nSpearman over the 30 reference graphs (predictor x measure):")
    for p in PRED:
        print(f"  {p:8s} " + "  ".join(f"{m} {'n/a' if corr[p][m] is None else f'{corr[p][m]:+.2f}'}" for m in MEASURES))
    print("\nN2 against the 30 reference graphs (graphs below / above N2):")
    for p in PRED:
        print(f"  {p:8s} below N2 {rank[p]['N2_above_reference']}, above N2 {rank[p]['N2_below_reference']}")
    for role in ("selected", "core-frozen-shuffle", "hub-frozen-shuffle"):
        gs = [g for g, v in rows.items() if v["role"] == role]
        print(f"\n{role}: " + "; ".join(f"{p} {min(rows[g][p] for g in gs):.3f} to {max(rows[g][p] for g in gs):.3f}"
                                     for p in PRED))
    print(f"reference medians: " + "; ".join(f"{p} {np.median([rows[g][p] for g in ref]):.3f}" for p in PRED))
    print(f"ensembles of the reference: {sorted(set(ensemble_of(g) for g in ref))}")


if __name__ == "__main__":
    main()
