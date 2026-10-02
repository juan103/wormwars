"""E3a's summary: every number RESULTS.md cites, read from the committed stage records (no GPU).

    python scripts/e3a_summary.py      # writes experiments/E3-ab-organism/E3a/summary.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
EXP = ROOT / "experiments" / "E3-ab-organism" / "E3a"


def rec(name: str) -> dict:
    return json.loads((EXP / f"{name}.json").read_text(encoding="utf-8"))


def main():
    from wormwars.e3.samplers import SELECTOR
    out = {}
    p = rec("project")
    out["projection"] = {"planned_total_hours": p["plan"]["planned_total_hours"], "steps": p["plan"]["steps"],
                         "seconds_per_generation": p["timing"]["training"]["seconds_per_generation"]}
    ge = rec("g-e")
    out["g-e"] = {"passed": ge["passed"], "cpu_cases": {k: v["identical"] for k, v in ge["cpu"]["cases"].items()},
                  "gpu": ge["gpu"]}
    g0 = rec("g0")["reading"]
    out["g0"] = {"passed": g0["passed"], "oracle_mean": g0["oracle"]["mean"], "reference_mean": g0["oracle"]["reference_mean"],
                 "s8192_mean": g0["s_shuttle"]["k8192_mean"], "s32_mean": g0["l1_switch"]["k32_mean"],
                 "l1_switch_mean": g0["l1_switch"]["mean"], "l1_switch_lower": g0["l1_switch"]["lower_bound"],
                 "blind": {k: {"mean": v["mean"], "p90": v["p90"]} for k, v in g0["blind"].items() if isinstance(v, dict)}}
    g1 = rec("g1")
    r = g1["reading"]
    comp = g1["component_tests"]
    act = list(comp["active"]["values"].values())
    ina = [abs(x) for x in comp["inactive"]["values"].values()]
    out["g1"] = {"passed": g1["passed"], "e_lower": r["score"]["lower_bound"], "no_latch": r["controls"]["no_latch"],
                 "one_module": r["controls"]["one_module"], "class": r["controls"]["class"],
                 "active_kd": [min(act), max(act)], "inactive_kd": [min(ina), max(ina)],
                 "clamp_share": g1["clamp"]["share"], "reset": [g1["reset"]["passed_worlds"], g1["reset"]["eligible"]],
                 "assays": r["assays"]}
    ce = rec("calibrate-e")
    out["calibrate-e"] = {"D": ce["D"], "e_measured_stimulus": ce["e_measured_stimulus"], "median_q": ce["median_q"],
                          "release_passed": all(v["passed"] for d in ce["e_release_reported"].values() for v in d.values())}
    cen = rec("census")
    c = np.load(EXP / "census-counts.npz", allow_pickle=False)
    g0o = cen["ga"]["generation0_first64"]
    out["census"] = {"e_mean": cen["e_census_mean"], "screen": 0.8 * cen["e_census_mean"],
                     **{k: {"qualifiers": cen[k]["qualifiers"], "mean": float(c[f"{k}_means"].mean()),
                            "max": float(c[f"{k}_means"].max())} for k in ("ga", "rs")},
                     "gen0_max_abs_offset": max(abs(x) for x in g0o["turn_offset"]),
                     "gen0_kd_range": [min(g0o["K_D_A_at_q0"]), max(g0o["K_D_A_at_q0"])]}
    out["training"] = {}
    for b, arm in ((1, "ga"), (3, "stage3"), (4, "btask")):
        t = rec(f"train-{b}")
        out["training"][arm] = {"hours": t["seconds"] / 3600, "assertions_failed": t["assertions_failed"],
                                "final_checkpoint": [r["checkpoints"][-1]["validation_mean"] for r in t["records"]],
                                "first_checkpoint": [r["checkpoints"][0]["validation_mean"] for r in t["records"]]}
    t2 = rec("train-2")
    out["training"]["rs"] = {"hours": t2["seconds"] / 3600, "assertions_failed": t2["assertions_failed"],
                             "best_selection": [t2["top32"][str(i)][0]["selection_mean"] for i in t2["runs"]]}
    ch2, ch3 = rec("champions-2"), rec("champions-3")
    out["champions"] = {arm: [{"run": x["run"], "validation_mean": x["validation_mean"]} for x in src[arm]["champions"]]
                        for arm, src in (("ga", ch2), ("rs", ch2), ("stage3", ch3), ("btask", ch3))}
    ev = rec("evaluate")
    orgs = []
    for o in ev["organisms"]:
        mem = o["memory"]
        hold = mem.get("hold_detail", {})
        orgs.append({"arm": o["arm"], "run": o["run"], "test_mean": o["test_mean"], "test_lower": o["test_lower_bound"],
                     "structure": o["structure"], "class": o["class"], "working": o["working"],
                     "clamp_share": o["clamp"].get("share"), "clamp_passed": o["clamp"].get("passed"),
                     "tau_q": o["selector"][SELECTOR.index("tau_q")], "w_qq": o["selector"][SELECTOR.index("w_qq")],
                     "settable": mem.get("settable"), "hold": mem.get("hold"), "release": mem.get("release"),
                     "hold_inactive_ratio": ({g: abs(v["other"]) / v["K_D"] for g, v in hold.items()} if hold else None),
                     "hold_q_kept": ({g: v["q"] for g, v in hold.items()} if hold else None),
                     "mean_nose": o["mean_nose"], "module_skill": o["module_skill"], "hysteresis": o["hysteresis"],
                     "stimulus": mem.get("stimulus")})
    out["evaluate"] = {"e_test_mean": ev["e_test_mean"], "D": ev["D"], "readings": ev["readings"], "organisms": orgs,
                       "btask_means": ev["btask_means"],
                       "e_contrasts": {k: v for k, v in ev["descriptive"]["E"].items() if k != "mean"},
                       "b_shared_mean": ev["descriptive"]["b_shared_mean"], "l1_switch_mean": ev["descriptive"]["l1_switch_mean"],
                       "b_shared_component_passed": ev["descriptive"]["b_shared_component_tests"]["passed"],
                       "b_shared_memory_class": ev["descriptive"]["b_shared_memory"]["class"],
                       "checkpoint_offsets_max_abs": {k: max(abs(x) for x in v) for k, v in ev["descriptive"]["checkpoint_offsets"].items()}}
    comp_rec = json.loads((EXP / "compute-record.json").read_text(encoding="utf-8"))
    out["compute"] = comp_rec.get("totals", comp_rec)
    (EXP / "summary.json").write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print("written", len(json.dumps(out)))


if __name__ == "__main__":
    main()
