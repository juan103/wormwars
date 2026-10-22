"""M4a: tables behind the results write-up, after the data, from the committed records and the local arrays (no
simulation): the sampled sets' full ranges, each class's share of the intact separation, the secondary arms' beside-
the-reading numbers, Part 2's complete outcomes with each graph's edge count inside C3, and each reference graph.
    py scripts/memory_m4/m4a_tables.py > runs/memory-m4a/tables.txt"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
OUT = ROOT / "runs" / "memory-m4a"
CENSUS = ROOT / "runs" / "memory-m2-census"


def main():
    import m4a
    r = json.load(open(OUT / "readings.json"))
    print("== the sampled sets (N2__7600's record; the same sets on both panels)")
    cs = json.load(open(OUT / "N2__7600.json"))["cut_sets"]
    for fam in ("degree", "weight"):
        sets = [v for k, v in cs.items() if k.startswith("rand") and v["stratified_on"] == fam]
        print(f"  {fam}: {len(sets)} sets; endpoint degree {min(x['endpoint_degree'] for x in sets):.2f} to "
              f"{max(x['endpoint_degree'] for x in sets):.2f}; sum|w| {min(x['sum_abs_w'] for x in sets):.2f} to "
              f"{max(x['sum_abs_w'] for x in sets):.2f}")
    print(f"  C3: endpoint degree {cs['C3']['endpoint_degree']:.2f}; sum|w| {cs['C3']['sum_abs_w']:.2f}")

    print("\n== each class's share of the intact full-state separation (sum ||dv||), ticks 0 and 60")
    for name in ("N2__7600", "N2__7700"):
        z = np.load(OUT / f"{name}.npz", allow_pickle=False)
        cen = {g["genome"]: g for g in json.load(open(CENSUS / f"{name}.json"))["genomes"]}
        E = np.array(sorted(cen))
        nv = z["intact__nv"].astype(np.float64)
        for t in (0, 60):
            tot = nv[E, t].sum()
            parts = {cls: nv[[i for i in E if cen[i]["class"].startswith(cls)], t].sum() / tot
                     for cls in ("separate states", "fading", "persistent oscillation", "unresolved")}
            print(f"  {name} tick {t}: " + ", ".join(f"{k} {v:.4f}" for k, v in parts.items()))
        sep = [i for i in E if cen[i]["class"].startswith("separate states")]
        cut_loss = nv[sep, 60].sum() - z["C3-early-30__nv"][sep, 60].astype(np.float64).sum()
        all_loss = nv[E, 60].sum() - z["C3-early-30__nv"][E, 60].astype(np.float64).sum()
        print(f"  {name}: the separate-states genomes' share of C3's early-30 loss at tick 60: {cut_loss / all_loss:.4f}")

    print("\n== beside each reading (all arms)")
    for name, p in r["panels"].items():
        for arm, a in p["arms"].items():
            if a.get("description_only"):
                print(f"  {name} {arm}: L {a['L']:.3f}, read-out {a['readout_L']:.3f}")
                continue
            print(f"  {name} {arm}: tick-3 C3 {a['L_tick3']:.3f} vs max {max(a['L_tick3_draws']):.3f}; read-out L "
                  f"{a['readout']['L']:.3f} vs max {max(a['readout']['L_draws']):.3f}; exterior {a['exterior_L']:.3f}; "
                  f"uniform {[round(x, 3) for x in a['uniform_L']]}; effect-matched "
                  f"{a['effect_matched']['matched']}/{a['effect_matched']['of']} L {a['effect_matched']['L']:.3f} "
                  f"ctrl {a['effect_matched']['L_ctrl']:.3f}")

    print("\n== per class, every maintenance arm: C3's loss against the sampled sets' median (and the core's collapse)")
    for name, p in r["panels"].items():
        for arm, a in p["arms"].items():
            for cls, b in a.get("by_class", {}).items():
                print(f"  {name} {arm} {cls}: {b['genomes']} genomes; L {b['L']:.3f} vs median {b['L_draws_median']:.3f}; "
                      f"collapse {b['collapse']:.3f}")

    print("\n== Part 2: every outcome, per group (counts; the sampled sets pooled over 5 sets each)")
    outcomes = ("both kept", "erased", "swapped", "other root", "not reached")
    for role, g in r["part2"].items():
        for arm in ("intact", "C3", "random"):
            c = g["counts"].get(arm, {})
            print(f"  {role:9s} {arm:7s} " + ", ".join(f"{o} {c.get(o, 0)}" for o in outcomes))
    print("\n== Part 2: per graph, edges inside C3's neuron set (cut by 'C3'), genomes, erased by C3, location median")
    import census
    selected = {n for n, _, _, role in census.panels() if role == "selected"}
    pooled = {}
    for f in sorted(OUT.glob("part2__*.json")):
        p = json.load(open(f))
        gname = p["panel"].split("__")[0]
        spec = m4a.c.S.genomes(census.graph_of(gname), 1, 7600)[0].spec
        internal, _ = m4a.edge_sets(spec, m4a.core())
        er = sum(o == "erased" for o in p["arms"]["C3"])
        grp = "N2" if p["panel"].startswith("N2") else ("selected" if p["panel"] in selected else "reference")
        pooled.setdefault(grp, []).extend(p["location_C3"])
        print(f"  {p['panel']:28s} internal edges {len(internal):4d}; genomes {len(p['genomes']):3d}; erased by C3 {er:3d}; "
              f"location on C3 median {np.median(p['location_C3']):.3f}")

    print("  pooled location-on-C3 medians: " + ", ".join(f"{k} {np.median(v):.3f} ({len(v)} genomes)"
                                                     for k, v in pooled.items()))

    print("\n== the reference, per graph (early-30, tick 60)")
    for name, v in r["reference"].items():
        print(f"  {name}: internal edges {v['internal_edges']}; C3 loss {v['L']:.3f}; its 8 sets {min(v['L_draws']):.3f} "
              f"to {max(v['L_draws']):.3f}")
    print(f"  N2's lead over the five graphs' mean v(60), N2 seed 7600: {r['n2_lead_over_reference']}")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
    main()
