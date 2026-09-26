"""Per-graph quantities behind the P4 decomposition: exploratory in 03 (§11), a registered
descriptive secondary in 03r (its pre-registration §5, D060).

Extracts, per graph, from the local measurements (`runs/exp03*/measures/`, git-ignored), so the
tables can be checked without them:
- P4's numerator and denominator (raw turn), and the same ratio on the raw forward read-out;
- the mean common-mode turn response at M0;
- the calibrated gains, the calibration target, and the independent calibration validation.

Missing measurements (a budget stop) and calibration failures are listed and counted, never
fatal. A ratio whose denominator mean is below 10^-4, or is not finite, is masked (None), the
same floor as the report's. Every measurement read must share one provenance.

Usage: py -3.13 experiments/03-generation0/supplement.py [--instance 03r]
→ writes supplement.json in that instance's experiment directory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[2]
INSTANCES = {"03": (ROOT / "experiments" / "03-generation0", ROOT / "runs" / "exp03" / "measures",
                    ("N2", "N2-rev", "N2perm1", "N2perm2", "N2perm3"),
                    "Exploratory (03 §11). Per-graph quantities behind RESULTS.md's exploratory tables."),
             "03r": (ROOT / "experiments" / "03r-replication", ROOT / "runs" / "exp03r" / "measures",
                     ("N2", "N2-rev", "N2perm4", "N2perm5", "N2perm6"),
                     "Registered descriptive secondary (03r pre-registration §5). No verdicts.")}
FLOOR = 1e-4
SUMMARISED = ("P4_turn_numerator", "P4_turn_denominator", "P4_turn", "P4_forward", "common_turn_M0",
              "forward_gain", "turn_gain", "validation_max_rel_deviation")


def per_graph(m: dict) -> dict:
    h, r, cal = m["history"], m["response"]["M0"], m["calibration"]

    def ratio(x):
        num, den = np.mean(np.abs(x["final"])), np.mean(np.abs(x["steady_contrast"]))
        ok = np.isfinite(num) and np.isfinite(den) and den >= FLOOR
        return float(num), float(den), float(num / den) if ok else None

    t_num, t_den, t_ratio = ratio(h["raw_turn"])
    f_num, f_den, f_ratio = ratio(h["raw_forward"])
    val = m.get("calibration_validation") or None
    target = cal["target"]
    return {"P4_turn_numerator": t_num, "P4_turn_denominator": t_den, "P4_turn": t_ratio,
            "P4_forward_numerator": f_num, "P4_forward_denominator": f_den, "P4_forward": f_ratio,
            "common_turn_M0": float(np.mean(np.abs(r["common_turn_raw"]))),
            "forward_gain": m["gains"][0], "turn_gain": m["gains"][1],
            "calibration_target": target,
            "calibration_achieved": [cal["achieved"]["forward"], cal["achieved"]["turn"]],
            "calibration_validation": [val["forward"], val["turn"]] if val else None,
            "validation_max_rel_deviation": max(abs(val["forward"] - target[0]) / target[0],
                                                abs(val["turn"] - target[1]) / target[1]) if val else None}


def _quantiles(v) -> dict:
    v = np.array([x for x in v if x is not None], float)
    v = v[np.isfinite(v)]  # non-finite values are not observations (Astra, D061)
    if not len(v):
        return {"n": 0}
    return {"n": int(len(v)), "q05": float(np.quantile(v, 0.05)), "median": float(np.median(v)),
            "q95": float(np.quantile(v, 0.95)), "max": float(v.max())}


def summarise(rows: dict, names: list, variants) -> dict:
    names = [n for n in names if n in rows]
    out = {k: _quantiles([rows[n][k] for n in names]) for k in SUMMARISED}
    fwd = np.array([rows[n]["P4_forward"] for n in names if rows[n]["P4_forward"] is not None], float)
    out["graphs_at_or_above_on_P4_forward"] = {v: int((fwd >= rows[v]["P4_forward"]).sum())
                                               for v in variants if v in rows and rows[v]["P4_forward"] is not None}
    return out


def build_supplement(exp_dir: Path, measures: Path, variants, note: str = "") -> dict:
    ens = json.loads((exp_dir / "ensembles.json").read_text(encoding="utf-8"))
    by_kind: dict[str, list] = {}
    for g in ens["graphs"]:
        by_kind.setdefault(g["kind"], []).append(g["name"])
    rows, missing, failed, provs = {}, [], [], set()
    for name in [*variants, *(n for names in by_kind.values() for n in names)]:
        path = measures / f"{name}.json"
        if not path.exists():
            missing.append(name)
            continue
        m = json.loads(path.read_text(encoding="utf-8"))
        if "provenance" not in m:
            raise ValueError(f"{name}: measurement has no provenance")
        provs.add(json.dumps(m["provenance"], sort_keys=True))
        if "calibration_failed" in m:
            failed.append(name)
            continue
        rows[name] = per_graph(m)
    if len(provs) > 1:
        raise ValueError(f"measurements come from {len(provs)} different provenances")
    return {"note": note, "floor": FLOOR, "missing": missing, "calibration_failed": failed,
            "summary": {k: summarise(rows, names, variants) for k, names in by_kind.items()},
            "per_graph": rows}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", choices=sorted(INSTANCES), default="03")
    exp_dir, measures, variants, note = INSTANCES[ap.parse_args().instance]
    out = build_supplement(exp_dir, measures, variants, note)
    (exp_dir / "supplement.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("missing", out["missing"], "calibration failed", out["calibration_failed"])
    print({k: {kk: vv.get("median") for kk, vv in s.items() if isinstance(vv, dict) and "n" in vv}
           for k, s in out["summary"].items()})


if __name__ == "__main__":
    main()
