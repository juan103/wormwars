"""E4s-1: the descriptive numbers RESULTS.md uses beyond the registered readings (rule 5; no GPU).

    python scripts/e4s1_summary.py     # writes experiments/E4s-stereo-module/E4s-1/summary.json

Reads only E4s-1's committed records: eval-endpoints.json, eval-training.json, report.json, and the
per-world counts in eval-endpoints-counts.npz (to re-derive F's scores independently of the summaries).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "E4s-stereo-module" / "E4s-1"


def stats(x) -> dict:
    x = np.asarray(x, dtype=np.float64)
    return {"mean": float(x.mean()), "min": float(x.min()), "max": float(x.max()), "n": int(x.size)}


def main():
    ev = json.loads((EXP / "eval-endpoints.json").read_text(encoding="utf-8"))
    tr = json.loads((EXP / "eval-training.json").read_text(encoding="utf-8"))
    counts = np.load(EXP / "eval-endpoints-counts.npz", allow_pickle=False)
    runs = ev["runs"]
    arms = sorted({v["arm"] for v in runs.values()})
    out = {"references": {k: v["score"] for k, v in ev["references"].items()}, "arms": {}}
    l1 = ev["references"]["L1 carrier turn 0.2"]["score"]
    for a in arms:
        rr = {v["run"]: v for v in runs.values() if v["arm"] == a}
        s = {"F": stats([v["F"]["score"] for v in rr.values()]), "C": stats([v["C"]["score"] for v in rr.values()]),
             "G0": stats([v["G0"]["score"] for v in rr.values()]),
             "climb": stats([v["F"]["score"] - v["G0"]["score"] for v in rr.values()]),
             "F_from_counts": stats([counts[f"{a} run{i:02d}|F|1"].mean() for i in rr]),
             "H_at_F": dict(Counter(v["F"]["H"]["class"] for v in rr.values())),
             "H_at_G0": dict(Counter(v["G0"]["H"]["class"] for v in rr.values())),
             "closed_loop_real_turn_at_F": stats([v["F"]["closed_loop_real"]["turn"] for v in rr.values()]),
             "open_loop_K_D_0.08_at_F": stats([v["F"]["open_loop"]["0.08"]["K_D"][0] for v in rr.values()]),
             "open_loop_K_D_0.08_at_G0": stats([v["G0"]["open_loop"]["0.08"]["K_D"][0] for v in rr.values()])}
        if a != "N":
            s["D_at_F"] = dict(Counter(v["F"]["D"]["class"] for v in rr.values()))
            s["D_at_G0"] = dict(Counter(v["G0"]["D"]["class"] for v in rr.values()))
            s["Mc_holds_at_F"] = sum(v["F"]["Mc"]["holds"] for v in rr.values())
            s["Mc_carrier_share_at_F"] = {t: stats([v["F"]["Mc"]["per_turn"][t]["score"] / ev["references"][f"L1 carrier turn {t}"]["score"]
                                                    for v in rr.values()]) for t in ("0.2", "-0.2")}
            s["lesion_cost_at_F"] = stats([v["F"]["lesion_cost"] for v in rr.values()])
            s["lesioned_score_at_F"] = stats([v["F"]["score"] - v["F"]["lesion_cost"] for v in rr.values()])
            s["reset_at_F"] = stats([v["F"]["reset"] for v in rr.values()])
            s["rescue_at_F"] = stats([v["F"]["rescue"] for v in rr.values()])
            w_f = np.array([[e["weight"] for e in v["F"]["module_parameters"]["edges"]] for v in rr.values()])
            w_0 = np.array([[e["weight"] for e in v["G0"]["module_parameters"]["edges"]] for v in rr.values()])
            s["module_abs_weight_at_F"] = stats(np.abs(w_f))
            s["module_sign_flips_G0_to_F"] = int((np.sign(w_f) != np.sign(w_0)).sum())
            s["O2b_share"] = stats([v["F"]["score"] / l1 for v in rr.values()])
        if a in ("M", "R"):
            s["g0_population_users"] = stats([v["g0_population_users"] for v in rr.values()])
        kd_f = [v["F"]["open_loop"]["0.08"]["K_D"][0] for v in rr.values()]
        kd_0 = [v["G0"]["open_loop"]["0.08"]["K_D"][0] for v in rr.values()]
        s["open_loop_K_D_0.08_median"] = {"G0": float(np.median(kd_0)), "F": float(np.median(kd_f)),
                                          "F_range": [float(min(kd_f)), float(max(kd_f))]}
        s["C_scores"] = stats([v["C"]["score"] for v in rr.values()])
        if a != "N":
            # the score with the module's noses on the mean (no stereo cue reaches the module), per run
            blind = {str(i): v["F"]["score"] - v["F"]["D"]["contrast_mean"]["mean"] for i, v in rr.items()}
            s["blind_module_score_at_F"] = {"per_run": blind, **stats(list(blind.values())),
                                            "near_zero_runs_below_0.35": sorted(int(i) for i, x in blind.items() if x < 0.35)}
            s["Mc_carrier_scores_at_F"] = {str(i): {t_: v["F"]["Mc"]["per_turn"][t_]["score"] for t_ in ("0.2", "-0.2")}
                                           for i, v in rr.items()}
            s["Mc_runs_above_L1_on_a_carrier"] = sum(
                any(v["F"]["Mc"]["per_turn"][t_]["score"] > ev["references"][f"L1 carrier turn {t_}"]["score"] for t_ in ("0.2", "-0.2"))
                for v in rr.values())
            s["Mc_runs_zero_on_both_carriers"] = sum(all(v["F"]["Mc"]["per_turn"][t_]["score"] == 0 for t_ in ("0.2", "-0.2"))
                                                     for v in rr.values())
            s["reset_range_at_F"] = [float(min(v["F"]["reset"] for v in rr.values())), float(max(v["F"]["reset"] for v in rr.values()))]
            s["module_abs_weight_shrink_share"] = float(1 - s["module_abs_weight_at_F"]["mean"] / 3.0)
            tau_d = [abs(v["F"]["module_parameters"]["tau"][n] - v["G0"]["module_parameters"]["tau"][n])
                     for v in rr.values() for n in v["F"]["module_parameters"]["tau"]]
            bias_d = [abs(v["F"]["module_parameters"]["bias"][n] - v["G0"]["module_parameters"]["bias"][n])
                      for v in rr.values() for n in v["F"]["module_parameters"]["bias"]]
            s["module_tau_abs_change"] = stats(tau_d)
            s["module_bias_abs_change"] = stats(bias_d)
        if a == "R":
            s["R_draw_alone_K_D_0.08_at_G0"] = stats([v["R_draw_open_loop_g0"]["0.08"]["K_D"][0] for v in rr.values()])
            s["R_draw_alone_K_C_0.08_at_G0"] = stats([v["R_draw_open_loop_g0"]["0.08"]["K_C"][0] for v in rr.values()])
            fw = np.array([[e["weight"] for e in v["R_final_module"]["edges"]] for v in rr.values()])
            s["R_final_edges"] = {"min_abs_weight": float(np.abs(fw).min()), "mean_abs_weight": float(np.abs(fw).mean())}
        out["arms"][a] = s
    # along training: the share of runs whose best uses the module, and the mean score, per generation
    along = {}
    for key, gens in tr["along"].items():
        a = key.split()[0]
        for g, v in gens.items():
            along.setdefault(a, {}).setdefault(g, []).append((v["D"]["class"], v["score"]))
    out["along_training"] = {a: {g: {"uses": sum(c == "uses" for c, _ in xs), "n": len(xs),
                                     "mean_score": float(np.mean([s for _, s in xs]))}
                                 for g, xs in sorted(gs.items(), key=lambda kv: int(kv[0]))} for a, gs in along.items()}
    fp = tr["final_populations_M"]
    out["final_populations_M"] = {"strains_with_contrast_lower_bound_above_0.5": sum(c["lo95"] > 0.5 for v in fp.values() for c in v),
                                  "strains": sum(len(v) for v in fp.values())}
    out["report"] = json.loads((EXP / "report.json").read_text(encoding="utf-8"))
    # the three genomes that share M's maximum total (7 722 targets): distinct per-world vectors?
    tie = [counts[k] for k in ("M run10|F|1", "S run00|F|1", "M run03|C|1")]
    out["max_total_coincidence"] = {"totals": [int(x.sum()) for x in tie],
                                    "pairwise_identical": [bool(np.array_equal(tie[i], tie[j])) for i, j in ((0, 1), (0, 2), (1, 2))]}
    # the recording defect: per-world motor arrays were cast to int16 (D154)
    motor_keys = [k for k in counts.files if "|motor" in k]
    out["motor_arrays"] = {"stored": len(motor_keys), "dtype": str(counts[motor_keys[0]].dtype) if motor_keys else None,
                           "all_zero": sum(int(not counts[k].any()) for k in motor_keys)}
    (EXP / "summary.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for a, s in out["arms"].items():
        print(a, {k: (round(v["mean"], 2) if isinstance(v, dict) and "mean" in v else v)
                  for k, v in s.items() if k not in ("Mc_carrier_share_at_F",)})
    print(json.dumps(out["along_training"])[:1500])
    print(out["final_populations_M"])


if __name__ == "__main__":
    main()
