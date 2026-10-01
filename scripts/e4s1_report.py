"""E4s-1's registered readings, applied to the committed evaluation records (§6-§7; no GPU).

    python scripts/e4s1_report.py            # writes experiments/E4s-stereo-module/E4s-1/report.json
    python scripts/e4s1_report.py --smoke    # on runs/e4s1-smoke, with one pair enough (plumbing only)

Rules from `wormwars/e4s/readings.py`; the run-level bootstrap is E2d's `_boot_means` (imported unchanged)
with seed 20 261 001; the sign-flip p is E2d's `sign_flip_p`.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.e4s import readings as RD  # noqa: E402

EXP = ROOT / "experiments" / "E4s-stereo-module" / "E4s-1"


def e2d():
    s = importlib.util.spec_from_file_location("e2d_for_report", ROOT / "scripts" / "e2d.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def runs_of(ev: dict, arm: str) -> dict[int, dict]:
    return {v["run"]: v for k, v in ev["runs"].items() if v["arm"] == arm}


def paired(a: dict, b: dict, f) -> tuple[list[int], np.ndarray]:
    keys = sorted(set(a) & set(b))
    return keys, np.array([f(a[k]) - f(b[k]) for k in keys], dtype=np.float64)


def report(folder: Path, min_pairs: int = RD.MIN_PAIRS) -> dict:
    D2 = e2d()
    boot = D2._boot_means
    ev = json.loads((folder / "eval-endpoints.json").read_text(encoding="utf-8"))
    arms = {a: runs_of(ev, a) for a in ("M", "N", "R", "F0", "U", "S", "C2")}
    score_f = lambda r: r["F"]["score"]  # noqa: E731
    out = {"not_covered": ev.get("not_covered", []), "min_pairs": min_pairs}

    # O1 and O1b
    keys, d = paired(arms["M"], arms["N"], score_f)
    o1 = RD.o1(d, boot, min_pairs) if len(d) else {"label": "not read", "pairs": 0}
    climb = np.array([arms["M"][k]["F"]["score"] - arms["M"][k]["G0"]["score"] for k in sorted(arms["M"])])
    climb_ci = RD.interval(climb, boot) if len(climb) else None
    o1["companion"] = RD.o1_companion(o1["label"], climb_ci["lo"], climb_ci["hi"]) if climb_ci else None
    o1["sign_flip_p"] = D2.sign_flip_p(d) if len(d) else None
    o1["pairs_used"] = keys
    keys_b, db = paired(arms["M"], arms["R"], score_f)
    o1b = RD.o1(db, boot, min_pairs) if len(db) else {"label": "not read", "pairs": 0}
    _, rn = paired(arms["R"], arms["N"], score_f)
    o1b["r_minus_n"] = float(rn.mean()) if len(rn) else None
    o1b["companion"] = RD.o1b_companion(o1b["label"], float(rn.mean())) if len(rn) else None
    o1b["sign_flip_p"] = D2.sign_flip_p(db) if len(db) else None
    o1b["pairs_used"] = keys_b
    out["O1"], out["O1b"] = o1, o1b

    # O1c
    climbs = {a: {k: v["F"]["score"] - v["G0"]["score"] for k, v in r.items()} for a, r in arms.items()}
    o1c = {"climbs": climbs}
    for other in ("N", "R"):
        ks = sorted(set(climbs["M"]) & set(climbs[other]))
        o1c[f"M_minus_{other}_climb"] = float(np.mean([climbs["M"][k] - climbs[other][k] for k in ks])) if ks else None
    ks = sorted(set(arms["M"]) & set(arms["N"]))
    o1c["G0_M_minus_G0_N"] = float(np.mean([arms["M"][k]["G0"]["score"] - arms["N"][k]["G0"]["score"] for k in ks])) if ks else None
    out["O1c"] = o1c

    # O2 and O2b
    l1 = ev["references"]["L1 carrier turn 0.2"]["score"]
    o2 = {}
    for a, thr, den in (("M", 12, 16), ("R", 12, 16), ("F0", 6, 8), ("U", 6, 8), ("S", 6, 8)):
        per, labels, g0c, fc = {}, [], [], []
        for k, v in sorted(arms[a].items()):
            g, f = v["G0"]["D"]["class"], v["F"]["D"]["class"]
            lab = RD.o2_label(g, f)
            per[k] = {"label": lab, "Mc_at_F": v["F"]["Mc"]["holds"], "H_G0": v["G0"]["H"]["class"],
                      "H_F": v["F"]["H"]["class"], "contrasts_G0": {q: v["G0"]["D"][q] for q in ("contrast_mean", "contrast_swapped")},
                      "contrasts_F": {q: v["F"]["D"][q] for q in ("contrast_mean", "contrast_swapped")},
                      "g0_population_users": v.get("g0_population_users"),
                      "O2b": (v["F"]["score"] / l1) if lab == "uses at both endpoints" and l1 > 0 else None}
            labels.append(lab)
            g0c.append(g)
            fc.append(f)
        labels += ["not read"] * max(0, den - len(labels))
        o2[a] = {"per_run": per, **RD.arm_reading(labels, thr, den), "retention_among_G0_users": RD.retention(g0c, fc)}
        bands = [p["O2b"] for p in per.values() if p["O2b"] is not None]
        o2[a]["O2b_bands"] = {"at least 0.9": sum(b >= 0.9 for b in bands), "0.5 to 0.9": sum(0.5 <= b < 0.9 for b in bands),
                              "below 0.5": sum(b < 0.5 for b in bands)}
    out["O2"] = o2

    # C2
    c2 = {}
    for k, v in sorted(arms["C2"].items()):
        c2[k] = {w: {"reading": RD.c2_reading(v[w]["D"]["contrast_mean"], v[w]["D"]["contrast_swapped"]),
                     "real_minus_mean": v[w]["D"]["contrast_mean"]["mean"], "score": v[w]["score"]} for w in ("G0", "F")}
    out["C2"] = {"per_run": c2, "ungrafted_reference": ev["references"].get("04a run02 ungrafted")}

    # O3
    o3 = {}
    for a in ("F0", "U", "S"):
        ks, dd = paired(arms[a], arms["M"], score_f)
        o3[f"{a}_minus_M"] = {"pairs": ks, "mean": float(dd.mean()) if len(dd) else None}
    if arms["M"]:
        mk = sorted(arms["M"])
        off = [abs(arms["M"][k]["G0"]["open_loop"]["0.08"]["u"][0]) for k in mk]
        if len(mk) >= 2:
            low, high = RD.o3_split(off)
            for name, idx in (("low_offset", low), ("high_offset", high)):
                rk = [mk[j] for j in idx]
                diffs = [arms["M"][k]["F"]["score"] - arms["N"][k]["F"]["score"] for k in rk if k in arms["N"]]
                o3[name] = {"runs": rk, "M_minus_N": float(np.mean(diffs)) if diffs else None,
                            "O2_labels": [o2["M"]["per_run"][k]["label"] for k in rk]}
    out["O3"] = o3

    # E3's artefact rule
    both = [k for k, p in o2["M"]["per_run"].items() if p["label"] == "uses at both endpoints"]
    e3 = {"uses_at_both_endpoints": len(both), "eligible": len(both) >= 12}
    if e3["eligible"]:
        tr = {}
        for f in sorted(folder.glob("train-*.json")):
            rec = json.loads(f.read_text(encoding="utf-8"))
            if rec.get("arm") == "M" and rec.get("outcome") == "completed":
                for i, r in zip(rec["runs"], rec["records"]):
                    tr[i] = r["checkpoints"][-1]["validation_mean"]
        best = sorted(both, key=lambda k: (-tr.get(k, -1), k))[0]
        e3.update(chosen_run=best, chosen_O2b=o2["M"]["per_run"][best]["O2b"],
                  passes_score_condition=(o2["M"]["per_run"][best]["O2b"] or 0) >= 0.9,
                  note="E3's own positive control is still required")
    out["E3_rule"] = e3
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    folder = ROOT / "runs" / "e4s1-smoke" if a.smoke else EXP
    doc = report(folder, min_pairs=1 if a.smoke else RD.MIN_PAIRS)
    (folder / "report.json").write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("O1", "O1b")}, indent=1, default=float)[:2000])
    print({a: doc["O2"][a]["reading"] for a in doc["O2"]})


if __name__ == "__main__":
    main()
