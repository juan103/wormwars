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
    (EXP / "summary.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for a, s in out["arms"].items():
        print(a, {k: (round(v["mean"], 2) if isinstance(v, dict) and "mean" in v else v)
                  for k, v in s.items() if k not in ("Mc_carrier_share_at_F",)})
    print(json.dumps(out["along_training"])[:1500])
    print(out["final_populations_M"])


if __name__ == "__main__":
    main()
