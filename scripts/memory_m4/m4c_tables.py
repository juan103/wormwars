"""M4c: tables behind the results write-up, after the data, from the committed panel records, sets.json and
readings.json (no simulation): every outcome by arm (each family pooled over its 20 sets), every panel, the spread of
each family's sets and whether their weight concentration tracks their erasures, the two sides per genome, the
descriptive arms per unit of weight, and the dissection against M4b's.
    py scripts/memory_m4/m4c_tables.py > runs/memory-m4c/tables.txt"""
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs" / "memory-m4c"
SIDES, FAMILIES, N_SETS = ("RIAR", "RIAL"), ("X", "W", "C"), 20
OUTS = ("both kept", "erased", "swapped", "other root", "not reached")


def main():
    r = json.load(open(OUT / "readings.json"))
    sets = json.load(open(OUT / "sets.json"))
    panels = [json.load(open(OUT / f"{name}.json")) for name, n, valid in r["panels"] if valid and n]
    arms = {a: sum((p["arms"][a] for p in panels), []) for a in panels[0]["arms"]}
    n = len(arms["intact"])
    print(f"{n} genomes in {len(panels)} panels; reading: {r['reading']}")

    print("\n== every outcome by arm (genomes; each family pooled over its 20 sets, so its counts sum to 20 x genomes)")
    rows = ["intact", "RIAR", "RIAL"] + [f"{s}:{f}" for s in SIDES for f in FAMILIES]
    for a in rows:
        outs = arms[a] if a in arms else sum((arms[f"{a}{k}"] for k in range(N_SETS)), [])
        c = Counter(outs)
        print(f"  {a:8s} " + " / ".join(str(c.get(o, 0)) for o in OUTS) + f"  (of {len(outs)})")
    print("  (order: " + " / ".join(OUTS) + ")")

    print("\n== every panel: genomes, erased by each side and the mean over each family's sets")
    for p in panels:
        g = len(p["genomes"])
        line = []
        for s in SIDES:
            e = sum(o == "erased" for o in p["arms"][s]) / g
            fam = [np.mean([sum(o == "erased" for o in p["arms"][f"{s}:{f}{k}"]) / g for k in range(N_SETS)])
                   for f in FAMILIES]
            line.append(f"{s} {e:.2f} (X {fam[0]:.2f}, W {fam[1]:.2f}, C {fam[2]:.2f})")
        print(f"  {p['panel']} {g:3d}: " + "; ".join(line))

    print("\n== each family's 20 sets: erased fraction (min / median / max), and Spearman of a set's erased fraction"
          " with its squared-weight ratio and with its heaviest edge")
    for s in SIDES:
        for f in FAMILIES:
            x = r["sides"][s][f]
            per = np.array(x["per_set"])
            m = x["match"]
            rho_sq = spearmanr(per, m["squared_ratio_per_set"]).statistic
            heavy = m["heaviest_edge"]
            rho_h = spearmanr(per, heavy).statistic if len(set(heavy)) > 1 else float("nan")
            print(f"  {s} {f}: {per.min():.3f} / {np.median(per):.3f} / {per.max():.3f}; side {r['sides'][s]['E']:.3f};"
                  f" rho(squared ratio) {rho_sq:+.2f}, rho(heaviest edge) {rho_h:+.2f}")

    print("\n== the two sides per genome (RIAR erased x RIAL erased)")
    a = np.array([o == "erased" for o in arms["RIAR"]])
    b = np.array([o == "erased" for o in arms["RIAL"]])
    both = np.array([o == "erased" for o in arms["RIA both"]])
    print(f"  both {int((a & b).sum())}, RIAR only {int((a & ~b).sum())}, RIAL only {int((~a & b).sum())}, "
          f"neither {int((~a & ~b).sum())}; RIA both sides cut together erased {int(both.sum())}, of which "
          f"{int((both & ~a & ~b).sum())} erased by neither side alone; not erased by both sides together but by one "
          f"alone {int((~both & (a | b)).sum())}")

    print("\n== descriptive arms: erased, edges, weight, erased per 100 of weight")
    desc = [k for k in r["arms"] if k not in ("intact",) and not any(f":{f}" in k for f in FAMILIES)
            and not (k.startswith("C3:") and k[3:].isupper() and len(k) <= 8)]
    for k in desc:
        v = r["arms"][k]
        print(f"  {k:34s} {v['erased']:3d} / {n}  {v['edges']:3d} edges, weight {v['weight']:6.0f}, "
              f"{100 * v['erased'] / v['weight']:.1f}")

    print("\n== how concentrated each descriptive set's weight is: summed squared weights and heaviest edge, against the"
          " side's (needs the local connectome)")
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import m4c
    key = m4c.n2_spec().chem_anat.numpy()
    for s in SIDES:
        own = sets["sides"][s]["edges"]
        other = [f"{s}:heaviest core"] + [f"{s}:star {nm}" for nm in sets["sides"][s]["stars"]] + [f"{s} outside C3"]
        for k in [s] + other:
            e = m4c.arm_edges(sets)[k]
            print(f"  {k:22s} squared ratio {(key[e] ** 2).sum() / (key[own] ** 2).sum():.2f}, heaviest edge "
                  f"{key[e].max():.0f} (side's {key[own].max():.0f})")
    spec = m4c.n2_spec()
    i, j = spec.chem_i.numpy(), spec.chem_j.numpy()
    ria = [m4c.c.NAMES.index(x) for x in SIDES]
    for nm in sorted({nm for s in SIDES for nm in sets["sides"][s]["stars"]}):
        k = m4c.c.NAMES.index(nm)
        pool = ((i == k) | (j == k)) & (i != j) & ~np.isin(i, ria) & ~np.isin(j, ria)
        print(f"  {nm}'s pool for the star sets: {int(pool.sum())} off-diagonal chemical edges not touching RIA")

    print("\n== the dissection: each C3 neuron's internal edges alone, fresh genomes (M4c) against M4b's 28")
    old = json.load(open(ROOT / "runs" / "memory-m4b" / "readings.json"))["dissection"]
    neu = [(k, v) for k, v in r["arms"].items() if k.startswith("C3:") and k in old and k[3:].isupper()]
    neu = [(k, v) for k, v in neu if " " not in k]
    neu.sort(key=lambda kv: (-kv[1]["erased"], kv[0]))
    for k, v in neu:
        print(f"  {k[3:]:6s} {v['edges']:2d} edges, weight {v['weight']:4.0f}: M4c {v['erased']:3d} / {n} "
              f"({v['erased'] / n:.3f}); M4b {old[k]['erased']:2d} / {old[k]['of']} ({old[k]['erased'] / old[k]['of']:.3f})")
    rho = spearmanr([v["erased"] for _, v in neu], [old[k]["erased"] for k, _ in neu]).statistic
    rho_w = spearmanr([v["weight"] for _, v in neu], [v["erased"] for _, v in neu]).statistic
    no_ria = [(k, v) for k, v in neu if k not in ("C3:RIAR", "C3:RIAL")]
    rho_w2 = spearmanr([v["weight"] for _, v in no_ria], [v["erased"] for _, v in no_ria]).statistic
    print(f"  {len(neu)} neurons; Spearman M4c against M4b {rho:+.2f}; weight against M4c's erased {rho_w:+.2f} "
          f"(without the two RIAs {rho_w2:+.2f})")
    for k in ("C3", "C3:read-out among themselves", "C3:read-out with the rest of C3", "C3:without the read-out"):
        v = r["arms"][k]
        print(f"  {k:34s} M4c {v['erased']:3d} / {n} ({v['erased'] / n:.3f}); M4b {old[k]['erased']} / {old[k]['of']}")

    print("\n== the sides against M4b (E with its 90% genome-bootstrap interval)")
    for s in SIDES:
        x = r["sides"][s]
        print(f"  {s}: {x['erased']} / {n} = {x['E']:.3f} [{x['E_interval'][0]:.3f}, {x['E_interval'][1]:.3f}]; "
              f"M4b {old['C3:' + s]['erased']} / 28 = {old['C3:' + s]['erased'] / 28:.3f}")
    print(f"\nsets.json sides: " + ", ".join(f"{s} {len(sets['sides'][s]['edges'])} edges" for s in SIDES))


if __name__ == "__main__":
    main()
