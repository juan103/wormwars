"""M4b's readings (docs/memory/M4B-PLAN.md): per graph group, the fraction of separate-states genomes erased by their
own-location cut and by its 5 weight-stratified external controls (the mean over controls), the contrast with a 90%
bootstrap interval (over graphs where a group has at least 5 graphs, over genomes otherwise), the fixed reading, and
Q1's dissection of N2's core as a description. Writes runs/memory-m4b/readings.json.
Usage: python scripts/memory_m4/m4b_read.py"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("MEMORY_M4B_OUT", ROOT / "runs" / "memory-m4b"))
MARGIN, B, SEED_BOOT, N_CTRL, MIN_CLUSTERS = 0.10, 2000, 20261112, 5, 5
GROUPS = ("N2", "selected", "reference", "core-frozen-shuffle", "hub-frozen-shuffle")


def per_genome(p, kind="ctrl"):
    """Over the genomes whose own set has edges (Fable: an empty own set equals intact and is excluded, counted):
    erased under 'own' (0/1) and the mean over the 5 control sets of the kind ('ctrl', the exterior; 'out', outgoing)
    of erased (0 to 1)."""
    keep = np.array([x["own_edges"] > 0 for x in p["info"]]) if "info" in p else np.ones(len(p["arms"]["own"]), bool)
    own = np.array([o == "erased" for o in p["arms"]["own"]], float)[keep]
    ctrl = np.mean([[o == "erased" for o in p["arms"][f"{kind}{d}"]] for d in range(N_CTRL)], 0)[keep]
    return own, ctrl


def contrast(clusters, rng, b=B, within=False):
    """clusters: a list of (own [n], ctrl [n]) arrays, one per graph. Returns the pooled E_own, E_ctrl,
    D = E_own - E_ctrl and the 90% interval of D. within=False resamples the graphs with replacement; within=True
    keeps the graphs fixed and resamples genomes within each (Astra: for groups of fewer than 5 graphs, conditional on
    those graphs)."""
    own = np.concatenate([c[0] for c in clusters])
    ctrl = np.concatenate([c[1] for c in clusters])
    D = []
    for _ in range(b):
        if within:
            picks = [rng.integers(0, len(c[0]), len(c[0])) for c in clusters]
            o = np.concatenate([c[0][k] for c, k in zip(clusters, picks)])
            c_ = np.concatenate([c[1][k] for c, k in zip(clusters, picks)])
        else:
            pick = rng.integers(0, len(clusters), len(clusters))
            o = np.concatenate([clusters[k][0] for k in pick])
            c_ = np.concatenate([clusters[k][1] for k in pick])
        D.append(o.mean() - c_.mean())
    return float(own.mean()), float(ctrl.mean()), float(own.mean() - ctrl.mean()), \
        [float(np.percentile(D, 5)), float(np.percentile(D, 95))]


def reading(n2_iv, sel_iv, n2_out_iv, sel_out_iv):
    """The fixed reading (draft 2): 'preferential erasure' if lower(D) > the margin against both the exterior and the
    outgoing controls, in N2 and in the selected graphs; 'not shown in the selected graphs' if the selected graphs'
    upper(D) < the margin against the exterior; 'unresolved' otherwise."""
    if min(n2_iv[0], sel_iv[0], n2_out_iv[0], sel_out_iv[0]) > MARGIN:
        return ("preferential erasure: cutting the edges among a genome's most-differing neurons erases its switch more "
                "often than as many exterior or outgoing edges, in N2 and in the selected graphs")
    if sel_iv[1] < MARGIN:
        return "not shown in the selected graphs"
    return "unresolved"


def load_validated():
    """Every expected panel, validated as m4b.py validates it on a restart (Astra, round 1): exact genome ids, complete
    arms, the intact gate, and the match with M4a's Part 2 on N2. A missing or invalid panel stops the reading."""
    import m4b
    exp = m4b.expected()
    panels = []
    for name, (gname, seed, role, ids) in exp.items():
        f = OUT / f"{name}.json"
        if not f.exists():
            raise SystemExit(f"{name}: missing; no reading")
        p = json.load(open(f))
        m4b.validate(p, ids, name, role, gname)
        panels.append(p)
    return panels


def main(panels=None):
    rng = np.random.default_rng(SEED_BOOT)
    panels = load_validated() if panels is None else panels
    res = {"groups": {}, "dissection": {}, "per_graph": {}}
    for grp in GROUPS:
        ps = [p for p in panels if p["role"] == grp]
        if not ps:
            continue
        pg = [per_genome(p) for p in ps]
        po = [per_genome(p, "out") for p in ps]
        graphs = sorted({p["graph"] for p in ps})  # N2's two panels are one graph (Astra, round 3)

        def clusters(per):
            return [tuple(np.concatenate([x[k] for x, p in zip(per, ps) if p["graph"] == gname]) for k in (0, 1))
                    for gname in graphs]
        cg, co_ = clusters(pg), clusters(po)
        within = len(graphs) < MIN_CLUSTERS
        unit = "genomes within the fixed graphs" if within else "graphs"
        E_own, E_ctrl, D, iv = contrast(cg, rng, within=within)
        _, E_out, D_out, iv_out = contrast(co_, rng, within=within)
        by_graph = {}  # N2's two panels are one graph (Astra, round 2)
        for p, (o, c_), (_, co) in zip(ps, pg, po):
            k = p["graph"]
            b = by_graph.setdefault(k, {"own": [], "ext": [], "out": [], "edges": [], "genomes": 0})
            b["own"].append(o), b["ext"].append(c_), b["out"].append(co)
            b["edges"] += [x["own_edges"] for x in p["info"]]
            b["genomes"] += len(p["genomes"])
        for k, b in by_graph.items():
            o, c_, co = (np.concatenate(b[x]) for x in ("own", "ext", "out"))
            res["per_graph"][k] = {"role": grp, "genomes": b["genomes"], "used": int(len(o)),
                                   "E_own": float(o.mean()) if len(o) else None,
                                   "E_ext": float(c_.mean()) if len(o) else None,
                                   "E_out": float(co.mean()) if len(o) else None,
                                   "own_edges_median": float(np.median(b["edges"]))}
        allo = {}
        for p in ps:
            for arm in ("own", "ctrl", "out"):
                outs = p["arms"]["own"] if arm == "own" else sum((p["arms"][f"{arm}{d}"] for d in range(N_CTRL)), [])
                for o in outs:
                    allo.setdefault(arm, {}).setdefault(o, 0)
                    allo[arm][o] += 1
        info = [x for p in ps for x in p["info"]]
        excluded = int(sum(x["own_edges"] == 0 for p in ps for x in p["info"]))
        own_e = np.array([x["own_edges"] for p in ps for x in p["info"] if x["own_edges"] > 0])
        own_er = np.concatenate([o for o, _ in pg])
        ext_er = np.concatenate([c_ for _, c_ in pg])
        out_er = np.concatenate([co for _, co in po])
        terc = np.quantile(own_e, [1 / 3, 2 / 3]) if len(own_e) else [0, 0]
        by_size = {}
        for lab, m in (("low", own_e <= terc[0]), ("mid", (own_e > terc[0]) & (own_e <= terc[1])), ("high", own_e > terc[1])):
            by_size[lab] = None if not m.any() else {
                "genomes": int(m.sum()), "E_own": float(own_er[m].mean()), "E_ext": float(ext_er[m].mean()),
                "E_out": float(out_er[m].mean()), "D_ext": float(own_er[m].mean() - ext_er[m].mean()),
                "D_out": float(own_er[m].mean() - out_er[m].mean())}
        short = np.array([x["out_edges"] < x["own_edges"] for p in ps for x in p["info"] if x["own_edges"] > 0])
        out_full = None
        if short.any():  # the outgoing contrast also without the genomes short of outgoing edges (pre-stated)
            out_full = {"excluded": int(short.sum()),
                        "D_out": float(own_er[~short].mean() - out_er[~short].mean()) if (~short).any() else None}
        res["groups"][grp] = {"graphs": len(graphs), "panels": len(ps), "genomes": int(sum(len(p["genomes"]) for p in ps)), "unit": unit,
                              "excluded_empty_own": excluded, "E_own": E_own, "E_ctrl": E_ctrl, "D": D,
                              "D_interval": iv, "E_out": E_out, "D_out": D_out, "D_out_interval": iv_out,
                              "by_own_edges_tercile": by_size, "D_out_without_short_outgoing": out_full,
                              "own_edges_terciles": [float(x) for x in terc], "outcomes": allo,
                              "own_edges_median": float(np.median([x["own_edges"] for x in info])),
                              "overlap_C3_median": float(np.median([x["overlap_C3"] for x in info])),
                              "location_own_median": float(np.median([x["location_own"] for x in info])),
                              "sum_anat_own_median": float(np.median([x["sum_anat_own"] for x in info])),
                              "sum_anat_ctrl_median": float(np.median([v for x in info for v in x["sum_anat_ctrl"]]))}
    if "N2" in res["groups"] and "selected" in res["groups"]:
        n2_, sel = res["groups"]["N2"], res["groups"]["selected"]
        res["reading"] = reading(n2_["D_interval"], sel["D_interval"], n2_["D_out_interval"], sel["D_out_interval"])
    n2 = [p for p in panels if p["role"] == "N2"]
    for arm in (n2[0]["arms"] if n2 else {}):
        if arm.startswith("C3"):
            outs = sum((p["arms"][arm] for p in n2), [])
            res["dissection"][arm] = {"erased": sum(o == "erased" for o in outs), "of": len(outs),
                                      "edges": n2[0]["arm_edges"][arm]}
    json.dump(res, open(OUT / "readings.json", "w"), indent=1)
    print("reading:", res.get("reading"))
    for grp, g in res["groups"].items():
        print(f"  {grp:20s} {g['genomes']:4d} genomes / {g['graphs']:2d} graphs: own {g['E_own']:.3f}, exterior "
              f"{g['E_ctrl']:.3f} (D {g['D']:+.3f} {np.round(g['D_interval'], 3).tolist()}), outgoing {g['E_out']:.3f} "
              f"(D {g['D_out']:+.3f} {np.round(g['D_out_interval'], 3).tolist()}), by {g['unit']}; own edges "
              f"{g['own_edges_median']:.0f}, overlap with C3 {g['overlap_C3_median']:.0f}, excluded {g['excluded_empty_own']}")
    for arm, d in sorted(res["dissection"].items(), key=lambda kv: -kv[1]["erased"]):
        print(f"  {arm:36s} erased {d['erased']:2d} of {d['of']} ({d['edges']} edges)")


def test_rules():
    """The reading's boundaries and the contrast's arithmetic (rule 9)."""
    ok = [0.11, 0.5]
    assert reading(ok, ok, ok, ok).startswith("preferential erasure")
    assert reading([0.10, 0.5], ok, ok, ok) == "unresolved"  # lower(D) must exceed the margin in N2 too
    assert reading(ok, ok, ok, [0.05, 0.5]) == "unresolved"  # and against the outgoing controls (Fable)
    assert reading(ok, [0.0, 0.09], ok, ok) == "not shown in the selected graphs"
    assert reading(ok, [0.0, 0.2], ok, ok) == "unresolved"
    rng = np.random.default_rng(0)
    E_own, E_ctrl, D, iv = contrast([(np.ones(4), np.zeros(4)), (np.ones(2), 0.5 * np.ones(2))], rng, b=200)
    assert abs(E_own - 1) < 1e-12 and abs(E_ctrl - 1 / 6) < 1e-12 and abs(D - 5 / 6) < 1e-12
    assert iv[0] >= 0.5 - 1e-12 and iv[1] <= 1.0 + 1e-12  # each unit's own contrast is 1 or 0.5
    own, ctrl = per_genome({"arms": {"own": ["erased", "both kept"],
                                     **{f"ctrl{d}": ["erased" if d < 2 else "both kept", "not reached"] for d in range(5)}}})
    assert own.tolist() == [1.0, 0.0] and np.allclose(ctrl, [0.4, 0.0])
    own, ctrl = per_genome({"info": [{"own_edges": 0}, {"own_edges": 3}], "arms": {"own": ["both kept", "erased"],
                            **{f"ctrl{d}": ["both kept", "both kept"] for d in range(5)}}})
    assert own.tolist() == [1.0] and ctrl.tolist() == [0.0]  # the empty own set is excluded
    _, _, _, iv = contrast([(np.ones(3), np.zeros(3)), (np.zeros(3), np.zeros(3))], rng, b=200, within=True)
    assert abs(iv[0] - 0.5) < 1e-12 and abs(iv[1] - 0.5) < 1e-12  # graphs fixed: each keeps its own contrast


if __name__ == "__main__":
    main()
