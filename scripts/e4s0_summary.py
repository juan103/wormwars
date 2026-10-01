"""E4s-0: every summary number RESULTS.md uses, derived from the committed stage records (rule 5).

    python scripts/e4s0_summary.py      # writes experiments/E4s-stereo-module/E4s-0/summary.json

No GPU; reads only the records in `experiments/E4s-stereo-module/E4s-0/` and the two references
named below (E1's freeze for its tuned k = 256 score, E2d's Part B for 04a run 2's hold-out score).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
EXP = ROOT / "experiments" / "E4s-stereo-module" / "E4s-0"


def read(name):
    return json.loads((EXP / f"{name}.json").read_text(encoding="utf-8"))


def e2d_rules():
    s = importlib.util.spec_from_file_location("e2d_for_summary", ROOT / "scripts" / "e2d.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def sweep_summary(sw):
    per = sw["per_champion"]
    ks = [k for k in sw["per_world_counts"] if k != "0"]
    first = {lab: v["difference"][str(v["k_star"]) if v["k_star"] is not None else ks[0]]["mean"]
             for lab, v in per.items() if v["k_star"] is not None and v["class"] == "rises early"}
    small = [k for k in ks if float(k) <= 1]
    max_small = {lab: max(v["difference"][k]["mean"] for k in small) for lab, v in per.items()}
    never = sorted(lab for lab, v in per.items() if not v["harmed_at"])
    by_k = {}
    for k in ["0", *ks]:
        s = np.array([v["mean_k0"] + (v["difference"][k]["mean"] if k != "0" else 0.0) for v in per.values()])
        by_k[k] = float(np.median(s))
    return {
        "class_counts": sw["class_counts"],
        "k_star_counts": {str(k): sum(1 for v in per.values() if v["k_star"] == k)
                          for k in sorted({v["k_star"] for v in per.values() if v["k_star"] is not None})},
        "rises_early_gain_at_k_star": sorted(first.values()),
        "harmed_at_larger_k": sum(v["harmed_at_larger_k"] for v in per.values()),
        "harmed_at_counts": {k: sum(float(k) in [float(x) for x in v["harmed_at"]] for v in per.values()) for k in ks},
        "harmed_somewhere": sum(1 for v in per.values() if v["harmed_at"]),
        "never_harmed": never,
        "max_gain_at_k_le_1": {"max": max(max_small.values()), "top": sorted(max_small.items(), key=lambda x: -x[1])[:4]},
        "pointwise_k16": {"upper_below_0": sum(v["difference"]["16"]["hi95"] < 0 for v in per.values()),
                          "lower_above_0": sum(v["difference"]["16"]["lo95"] > 0 for v in per.values())},
        "all_improve_at": [k for k in ks if all(v["difference"][k]["lo95"] > 0 for v in per.values())],
        "median_across_champions_by_k": by_k,
        "k0_range": [min(v["mean_k0"] for v in per.values()), max(v["mean_k0"] for v in per.values())],
        "k256_score_range": [min(v["mean_k0"] + v["difference"]["256"]["mean"] for v in per.values()),
                             max(v["mean_k0"] + v["difference"]["256"]["mean"] for v in per.values())],
    }


GROUPS = {"sensory": ["ASEL", "ASER", "AWAL", "AWAR", "AWCL", "AWCR"],
          "first interneurons": ["AIYL", "AIYR", "AIZL", "AIZR", "AIAL", "AIAR", "AIBL", "AIBR"],
          "RIA": ["RIAL", "RIAR"], "turn motor": ["SMDDL", "SMDDR", "SMDVL", "SMDVR", "RMDDL", "RMDDR", "RMDVL", "RMDVR"]}


def attenuation_summary(at):
    """One value per champion and group (the mean of the group's absolute gains), then the median
    across champions; the ratio K_D / K_C per champion, then its median (Astra, Fable)."""
    out = {}
    for m, per in at["per_level"].items():
        row = {}
        for g, ns in GROUPS.items():
            kd = np.array([np.mean([abs(c["K_D"][n]) for n in ns]) for c in per.values()])
            kc = np.array([np.mean([abs(c["K_C"][n]) for n in ns]) for c in per.values()])
            row[g] = {"K_D": float(np.median(kd)), "K_C": float(np.median(kc)), "ratio": float(np.median(kd / kc))}
        kdt = np.array([abs(c["K_D_turn"]) for c in per.values()])
        kct = np.array([abs(c["K_C_turn"]) for c in per.values()])
        row["turn command"] = {"K_D": float(np.median(kdt)), "K_C": float(np.median(kct)),
                               "ratio": float(np.median(kdt / kct))}
        out[m] = row
    return out


def ladder_summary(ld):
    step = ld["ladder_log"]["steps"][0]
    from itertools import product
    grid = list(product([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [0.5, 2.0], [-0.5, 0.0], [0.5, 1.0], [0.0, 0.1, 0.2]))
    q = ld["qualified"]
    same = {c: [i for i, g in enumerate(grid) if g[:5] == (q["w_n"], q["w_o"], q["tau"], q["bias"], q["forward"])
                and g[5] == c][0] for c in (0.0, 0.1, 0.2)}
    return {"qualified": q, "qualification": ld["attempts"][0]["details"]["mean"],
            "tune_mean_by_turn_command": {str(c): step["tune_means"][i] for c, i in same.items()},
            "c0_in_top5": same[0.0] in step["top"],
            "grid_corner": {"w_n": "max", "w_o": "max", "tau": "min", "bias": "interior (0 of -0.5, 0)",
                            "forward": "max", "turn": "max"},
            "dynamics_t90_convention": "zero-based index of the update after the change: t90 = 3 is the 4th update"}


def populations_summary(po, D2):
    g0 = {p: np.array(v) for p, v in po["g0_per_world_counts"].items()}
    real = g0["real"].mean(axis=1)
    bg = {p: np.array(v) for p, v in po["backgrounds"]["per_world_counts"].items()}
    bgm = {p: v.mean(axis=1) for p, v in bg.items()}
    fw, tu, sa = (np.array(po["backgrounds"][k]) for k in ("forward", "turn", "saturated_share"))
    e = {p: np.array(v) for p, v in po["e04a_run02"]["per_world_counts"].items()}
    sel = np.array(po["selection"]["per_world_counts"]).mean(axis=1).reshape(16, 32)
    return {"g0_real_mean": {"median": float(np.median(real)), "min": float(real.min()), "max": float(real.max())},
            "g0_classes": po["g0_counts"], "selection_population_median_fitness": float(np.median(sel)),
            "backgrounds": {"classes": po["backgrounds"]["classes"],
                            "real_zero": int((bgm["real"] == 0).sum()),
                            "zero_under_all_three": int(((bgm["real"] == 0) & (bgm["mean"] == 0) & (bgm["swapped"] == 0)).sum()),
                            "median_score": float(np.median(bgm["real"])),
                            "forward_below_0_share": float((fw < 0).mean()), "median_forward": float(np.median(fw)),
                            "median_abs_turn": float(np.median(np.abs(tu))), "median_saturated_share": float(np.median(sa))},
            "e04a_run02": {"means": {p: float(v.mean()) for p, v in e.items()},
                           "real_minus_mean": D2.world_ci(e["real"], e["mean"]),
                           "real_minus_swapped": D2.world_ci(e["real"], e["swapped"]),
                           "forward": po["e04a_run02"]["forward"], "turn": po["e04a_run02"]["turn"]}}


def robustness_summary(ro):
    pm = ro["parent_mean"]
    out = {"parent_mean": pm, "fallback": ro["fallback"]}
    for s, v in ro["per_scale"].items():
        m = np.array(v["child_means"])
        out[s] = {"median_share": v["median_share"], "zero": int((m == 0).sum()),
                  "below_0.7": int((m < 0.7).sum()), "keep_half": int((m >= 0.5 * pm).sum()),
                  "above_parent": int((m > pm).sum()), "n": int(m.size),
                  "survivor_range": [float(m[m >= 0.7].min()), float(m[m >= 0.7].max())] if (m >= 0.7).any() else None}
    return out


def attempts_summary():
    comp = json.loads((EXP / "compute-record.json").read_text(encoding="utf-8"))
    att = comp.get("attempts", [])
    return {"attempts": len(att), "note": "every attempt in the accounting, the refused ones included"}


def main():
    D2 = e2d_rules()
    doc = {"sweep": sweep_summary(read("sweep")), "attenuation": attenuation_summary(read("attenuation")),
           "ladder": ladder_summary(read("ladder")), "populations": populations_summary(read("populations"), D2),
           "robustness": robustness_summary(read("robustness")),
           "references": {
               "e1_tuned_k256": "E1's best tuned S-const score at k = 256 (turn bias 0.2), on its 256 tuning worlds:"
                                " experiments/E1-navigation/freeze.json",
               "e2d_04a_run02": "04a run 2 on E2d's hold-out: experiments/E2d-taskn-diagnosis/part-b.json",
               "gain_probe": "the champions' open-loop gain 0.098: development-records/gain-probe.json"}}
    (EXP / "summary.json").write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("ladder", "robustness")}, indent=1, default=float)[:3000])


if __name__ == "__main__":
    main()
