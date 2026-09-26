"""Exploratory supplement to 03's RESULTS.md (not registered, §11).

Extracts, per graph, the quantities behind RESULTS.md's exploratory tables from the local
measurements (`runs/exp03/measures/`, git-ignored), so the tables can be checked without them:
- P4's numerator and denominator (raw turn), and the same ratio on the raw forward read-out;
- the mean common-mode turn response at M0;
- the calibrated gains, the calibration target, and the independent calibration validation.

Usage: py -3.13 experiments/03-generation0/supplement.py [--instance 03r]
→ writes supplement.json in that instance's experiment directory (03r registers it as a
secondary, descriptive output).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import argparse

ROOT = Path(__file__).parents[2]
INSTANCES = {"03": (ROOT / "experiments" / "03-generation0", ROOT / "runs" / "exp03" / "measures",
                    ("N2", "N2-rev", "N2perm1", "N2perm2", "N2perm3")),
             "03r": (ROOT / "experiments" / "03r-replication", ROOT / "runs" / "exp03r" / "measures",
                     ("N2", "N2-rev", "N2perm4", "N2perm5", "N2perm6"))}
EXP, MEASURES, N2_AND_VARIANTS = INSTANCES["03"]


def per_graph(m: dict) -> dict:
    h, r, cal = m["history"], m["response"]["M0"], m["calibration"]

    def ratio(x):
        num, den = np.mean(np.abs(x["final"])), np.mean(np.abs(x["steady_contrast"]))
        return float(num), float(den), float(num / den) if den > 0 else None

    t_num, t_den, t_ratio = ratio(h["raw_turn"])
    f_num, f_den, f_ratio = ratio(h["raw_forward"])
    return {"P4_turn_numerator": t_num, "P4_turn_denominator": t_den, "P4_turn": t_ratio,
            "P4_forward_numerator": f_num, "P4_forward_denominator": f_den, "P4_forward": f_ratio,
            "common_turn_M0": float(np.mean(np.abs(r["common_turn_raw"]))),
            "forward_gain": m["gains"][0], "turn_gain": m["gains"][1],
            "calibration_target": cal["target"],
            "calibration_achieved": [cal["achieved"]["forward"], cal["achieved"]["turn"]],
            "calibration_validation": [m["calibration_validation"]["forward"],
                                       m["calibration_validation"]["turn"]]
            if "calibration_validation" in m and m["calibration_validation"] else None}


def summarise(rows: dict, names: list) -> dict:
    out = {}
    for k in ("P4_turn_numerator", "P4_turn_denominator", "common_turn_M0", "P4_forward", "turn_gain"):
        v = np.array([rows[n][k] for n in names], float)
        out[k] = {"q05": float(np.quantile(v, 0.05)), "median": float(np.median(v)),
                  "q95": float(np.quantile(v, 0.95)), "max": float(v.max())}
    for n2 in N2_AND_VARIANTS:
        v = np.array([rows[n]["P4_forward"] for n in names], float)
        out.setdefault("graphs_at_or_above_on_P4_forward", {})[n2] = int((v >= rows[n2]["P4_forward"]).sum())
    return out


def main() -> None:
    global EXP, MEASURES, N2_AND_VARIANTS
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", choices=sorted(INSTANCES), default="03")
    EXP, MEASURES, N2_AND_VARIANTS = INSTANCES[ap.parse_args().instance]
    ens = json.loads((EXP / "ensembles.json").read_text(encoding="utf-8"))
    by_kind: dict[str, list] = {}
    for g in ens["graphs"]:
        by_kind.setdefault(g["kind"], []).append(g["name"])
    rows = {}
    for name in [*N2_AND_VARIANTS, *(n for names in by_kind.values() for n in names)]:
        rows[name] = per_graph(json.loads((MEASURES / f"{name}.json").read_text(encoding="utf-8")))
    validated = {n: r for n, r in rows.items() if r["calibration_validation"] is not None}
    dev = [max(abs(a - t) / t for a, t in zip(r["calibration_validation"], r["calibration_target"]))
           for r in validated.values()]
    out = {"note": "Exploratory (§11). Per-graph quantities behind RESULTS.md's exploratory tables.",
           "summary": {k: summarise(rows, names) for k, names in by_kind.items()},
           "calibration_validation": {"graphs_validated": sorted(validated),
                                      "max_relative_deviation_from_target": float(max(dev))},
           "per_graph": rows}
    (EXP / "supplement.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out["calibration_validation"], indent=1))
    print(json.dumps({k: {kk: vv["median"] if isinstance(vv, dict) and "median" in vv else vv
                          for kk, vv in s.items()} for k, s in out["summary"].items()}, indent=1))
    print({n: {k: rows[n][k] for k in ("P4_turn_numerator", "P4_turn_denominator", "P4_forward", "common_turn_M0")}
           for n in N2_AND_VARIANTS})


if __name__ == "__main__":
    main()
