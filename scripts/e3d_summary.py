"""E3d's results summary: every number RESULTS.md quotes, derived from the committed records (rule 5).

    python scripts/e3d_summary.py      # writes experiments/E3-ab-organism/E3d/summary.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "E3-ab-organism" / "E3d"


def mean(x):
    return float(np.mean(x))


def main():
    cal = json.loads((EXP / "calibrate.json").read_text(encoding="utf-8"))
    rep = json.loads((EXP / "report.json").read_text(encoding="utf-8"))
    comp = json.loads((EXP / "compute-record.json").read_text(encoding="utf-8"))
    out = {"verdict": rep["verdict"], "choice": cal["choice"], "gpu_hours": comp["totals"]["seconds_timed"] / 3600,
           "k_r": {}}
    for k, b in cal["blocks"].items():
        g, c = b["gate"], b["conditions"]
        arms = {}
        for name, cond in c.items():
            if cond["role"] != "blind" or len(cond["strains"]) == 1:
                continue
            v = [mean(s["visits"]) for s in cond["strains"]]
            arms[name] = {"min": min(v), "max": max(v), "mean": mean(v)}
        single = {name: mean(cond["strains"][0]["visits"]) for name, cond in c.items() if len(cond["strains"]) == 1}
        top = g["b_max_member"]
        w = c[top]["strains"][0]
        rows = b["mazes"]
        out["k_r"][k] = {
            "gate": {x: g[x] for x in ("follower", "oracle", "oracle_visited_share", "seed", "seed_median_legs", "b_max",
                                       "b_max_member", "failed", "verdict", "precondition")},
            "ratios": {"b_max_over_follower": g["b_max"] / g["follower"], "follower_over_oracle": g["follower"] / g["oracle"],
                       "seed_minus_b_max": g["seed"] - g["b_max"]},
            "first_draw_feasible_share": b["first_draw_feasible_share"],
            "single_strain_means": single, "multi_strain_blind": arms,
            "w2_turn_best": max(((n, v) for n, v in single.items() if n.startswith("w2_turn_")), key=lambda t: t[1]),
            "b_max_member_detail": {"round_trip_share": mean(w["round_trip_share"]), "coverage": mean(w["coverage"]),
                                    "visited_share": mean(w["visited_share"]),
                                    **{f"contact_{x}": mean(w[f"contact_{x}"]) for x in ("perimeter", "ring_a", "ring_b", "other")},
                                    "switch_rate": mean(w["switch_rate"]), "at_visit": w["at_visit"]},
            "round_trip_share_blind_top5": sorted(((n, mean(cond["strains"][0]["round_trip_share"])) for n, cond in c.items()
                                                   if cond["role"] == "blind" and len(cond["strains"]) == 1),
                                                  key=lambda t: -t[1])[:5],
            "follower_shared_detail": {"round_trip_share": mean(c["follower_shared"]["strains"][0]["round_trip_share"]),
                                       "no_first_visit_share": mean(c["follower_shared"]["strains"][0]["no_first_visit_share"])},
            "seed_detail": {"round_trip_share": mean(c["seed"]["strains"][0]["round_trip_share"]),
                            "no_first_visit_share": mean(c["seed"]["strains"][0]["no_first_visit_share"])},
            "mazes": {"open_share": mean([r["open_share"] for r in rows]), "junctions": mean([r["junctions"] for r in rows]),
                      "dead_ends": mean([r["dead_ends"] for r in rows]), "detour": mean([r["detour"] for r in rows]),
                      "line_of_sight_share": mean([r["line_of_sight_share"] for r in rows]),
                      "entrances": mean([e for r in rows for e in r["entrances"]]),
                      "spawn_candidates": mean([r["spawn_candidates"] for r in rows]),
                      "redrawn_share": mean([r["redraw"] > 0 for r in rows]),
                      "scent_reach_share": mean([x for r in rows for x in r["scent_reach"]])},
        }
    path = EXP / "summary.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
