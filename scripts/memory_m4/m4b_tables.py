"""M4b: tables behind the results write-up, after the data, from the committed panel records and readings.json (no
simulation): the weight balance of the controls, the terciles with counts and contrasts, every outcome by group and
arm, every graph, every dissection arm, and the neurons most often among the own sets per graph.
    py scripts/memory_m4/m4b_tables.py > runs/memory-m4b/tables.txt"""
import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs" / "memory-m4b"
N_CTRL = 5


def main():
    r = json.load(open(OUT / "readings.json"))
    panels = [json.load(open(f)) for f in sorted(OUT.glob("*__7*.json"))]
    groups = list(r["groups"])

    print("== the controls' summed anatomical weight against the own set's, per genome (median ratio; the own set's edge"
          " count range)")
    for grp in groups:
        info = [x for p in panels if p["role"] == grp for x in p["info"]]
        ext = [np.mean(x["sum_anat_ctrl"]) / x["sum_anat_own"] for x in info if x["sum_anat_own"] > 0]
        out = [np.mean(x["sum_anat_out"]) / x["sum_anat_own"] for x in info if x["sum_anat_own"] > 0]
        out_full = [np.mean(x["sum_anat_out"]) / x["sum_anat_own"] for x in info
                    if x["sum_anat_own"] > 0 and x["out_edges"] == x["own_edges"]]
        e = [x["own_edges"] for x in info]
        print(f"  {grp:20s} exterior {np.median(ext):.3f}; outgoing {np.median(out):.3f} (without short sets "
              f"{np.median(out_full):.3f}); own edges {min(e)} to {max(e)}")

    print("\n== by the own set's edge count (terciles within each group)")
    for grp, g in r["groups"].items():
        print(f"  {grp}: tercile bounds {np.round(g['own_edges_terciles'], 1).tolist()}")
        for lab, v in g["by_own_edges_tercile"].items():
            if v:
                print(f"     {lab:4s} {v['genomes']:3d} genomes: own {v['E_own']:.3f}, exterior {v['E_ext']:.3f}, outgoing "
                      f"{v['E_out']:.3f}; D_ext {v['D_ext']:+.3f}, D_out {v['D_out']:+.3f}")

    print("\n== every outcome, by group and arm (genomes; controls pooled over their 5 sets)")
    outs = ("both kept", "erased", "swapped", "other root", "not reached")
    for grp, g in r["groups"].items():
        for arm in ("own", "ctrl", "out"):
            c = g["outcomes"].get(arm, {})
            print(f"  {grp:20s} {arm:5s} " + ", ".join(f"{o} {c.get(o, 0)}" for o in outs))

    print("\n== every graph (N2's two panels together)")
    for k, v in r["per_graph"].items():
        print(f"  {k:22s} {v['role']:20s} {v['genomes']:3d} genomes: own {v['E_own']:.3f}, exterior {v['E_ext']:.3f}, "
              f"outgoing {v['E_out']:.3f}; own edges (median) {v['own_edges_median']}")
    sel = [p for p in panels if p["role"] == "selected"]
    er = {p["graph"]: sum(o == "erased" for o in p["arms"]["own"]) for p in sel}
    print(f"  selected: own-cut erasures {sum(er.values())}, of which SH-class-2030099 {er['SH-class-2030099']} and "
          f"SH-recip-2050040 {er['SH-recip-2050040']}")

    print("\n== every dissection arm (N2, 28 genomes)")
    for arm, d in sorted(r["dissection"].items(), key=lambda kv: (-kv[1]["erased"], kv[0])):
        print(f"  {arm:36s} {d['edges']:3d} edges, erased {d['erased']}")

    print("\n== the neurons most often among a genome's 30 most-differing (share of the graph's switch genomes)")
    by = {}
    for p in panels:
        by.setdefault(p["graph"], []).extend(x["own_neurons"] for x in p["info"])
    for gname, sets in by.items():
        cnt = Counter(n for s in sets for n in s)
        top = ", ".join(f"{n} {cnt[n] / len(sets):.2f}" for n, _ in cnt.most_common(8))
        either = sum(1 for s in sets if "RIAL" in s or "RIAR" in s) / len(sets)  # Astra, round 2: the union
        print(f"  {gname:22s} {len(sets):3d} genomes; RIAL or RIAR among them {either:.3f}; top: {top}")


if __name__ == "__main__":
    main()
