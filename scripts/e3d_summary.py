"""E3d's results summary: the calibration block's numbers RESULTS.md quotes, derived from the committed records
(rule 5). Additive analyses the report stage does not compute when calibration fails (both reviewers of the
draft, D231): every gate quantity's bootstrap interval (design §5: 2 000 resamples, seed 20 261 011, B_max
recomputed in each), the scent-reach split (§2), and exact visit and leg counts for the noses-removed champions.

    python scripts/e3d_summary.py                  # writes experiments/E3-ab-organism/E3d/summary.json
    python scripts/e3d_summary.py --exp E3e        # E3e's, from its records (D235)
"""

from __future__ import annotations

import json
from pathlib import Path

import importlib.util
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.e3 import e3d_gate as GT  # noqa: E402
EXP = ROOT / "experiments" / "E3-ab-organism" / "E3d"
if "--exp" in sys.argv:
    EXP = ROOT / "experiments" / "E3-ab-organism" / sys.argv[sys.argv.index("--exp") + 1]


def mean(x):
    return float(np.mean(x))


def _runner():
    s = importlib.util.spec_from_file_location("e3d_for_summary", ROOT / "scripts" / "e3d.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    D = _runner()
    cal = json.loads((EXP / "calibrate.json").read_text(encoding="utf-8"))
    rep = json.loads((EXP / "report.json").read_text(encoding="utf-8"))
    comp = json.loads((EXP / "compute-record.json").read_text(encoding="utf-8"))
    R = {"resamples": 2000, "seed": 20_261_011}  # design §5
    out = {"verdict": rep["verdict"], "bootstrap_settings": R, "choice": cal["choice"], "gpu_hours": comp["totals"]["seconds_timed"] / 3600,
           "k_r": {}}
    def block_summary(b):
        """One block's summary (a calibration k_r, or the confirmation block when it was played; D239)."""
        g, c = b["gate"], b["conditions"]
        arms = {}
        for name, cond in c.items():
            if cond["role"] != "blind" or len(cond["strains"]) == 1:
                continue
            v = [mean(s["visits"]) for s in cond["strains"]]
            arms[name] = {"min": min(v), "max": max(v), "mean": mean(v)}
        single = {name: mean(cond["strains"][0]["visits"]) for name, cond in c.items() if len(cond["strains"]) == 1}
        top = g["b_max_member"]
        w = D.member_strain(b, top)  # "name#strain" resolves to its strain (D233)
        rows = b["mazes"]
        colony = 8
        counts = {}
        for name in ("s_mod_noses", "s_dense_noses", "p_sel_noses", "p_joint_noses", "wall_left", "wall_right"):
            cond = c[name]
            counts[name] = [{"total_visits": int(round(sum(st["visits"]) * colony)),
                             "max_colony_mean_legs": max(st["legs"]),
                             "round_trip_share": mean(st["round_trip_share"])} for st in cond["strains"]]
        return {
            "bootstrap": GT.bootstrap(b, R["resamples"], R["seed"]),
            "scent_split": D.scent_split(b),
            "exact_counts": counts,
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
            "navigators": {name: {
                "later_leg_rate": mean(c[name]["strains"][0]["later_leg_rate"]),
                **{f"first_entry_median_{g}": {
                    # a maze's colony median of first-entry ticks is censored when at most half its weys arrived
                    # (E3c's censored median); the median over mazes is over the uncensored ones (D241, Astra)
                    "median_over_uncensored_mazes": (float(np.median([x for x in c[name]["strains"][0][f"first_entry_median_{g}"]
                                                                       if x is not None]))
                                                     if any(x is not None for x in c[name]["strains"][0][f"first_entry_median_{g}"])
                                                     else None),
                    "mazes_median_censored": sum(x is None for x in c[name]["strains"][0][f"first_entry_median_{g}"]),
                    "mazes_with_no_arrival": sum(x == 0 for x in c[name]["strains"][0][f"arrived_{g}"])}
                   for g in "ab"},
                "arrived_a": mean(c[name]["strains"][0]["arrived_a"]), "arrived_b": mean(c[name]["strains"][0]["arrived_b"])}
                for name in ("follower_shared", "seed", "oracle")},  # D236: the records E3e's G2a reading names
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
    for k, b in cal["blocks"].items():
        out["k_r"][k] = block_summary(b)
    conf_path = EXP / "confirm.json"
    if conf_path.exists():  # the confirmation block, summarised as calibration is (Fable, D239)
        conf = json.loads(conf_path.read_text(encoding="utf-8"))
        out["confirmation"] = {"k_r": conf.get("k_r"), **block_summary(conf["blocks"]["confirmation"])}
        # the intact champions on both blocks and the tree reference's single-strain means (D241, both reviewers)
        def arms(b):
            return {name: {"mean": mean([mean(st["visits"]) for st in cond["strains"]]),
                           "total_visits_per_champion": [int(round(sum(st["visits"]) * 8)) for st in cond["strains"]]}
                    for name, cond in b["conditions"].items() if name.endswith("_intact")}
        tree = conf["blocks"]["tree_reference"]
        out["intact_champions"] = {"confirmation": arms(conf["blocks"]["confirmation"]), "tree_reference": arms(tree)}
        out["tree_reference"] = {
            "single_strain_means": {name: mean(cond["strains"][0]["visits"]) for name, cond in tree["conditions"].items()
                                    if len(cond["strains"]) == 1},
            "quantities": {k: v for k, v in GT.quantities(tree).items() if k != "blind_means"},
            "follower_over_oracle": GT.quantities(tree)["follower"] / GT.quantities(tree)["oracle"],
            "wall_follower_switch_rate": {n: mean(tree["conditions"][n]["strains"][0]["switch_rate"])
                                          for n in ("wall_left", "wall_right")}}
        if "tangent" in conf["blocks"]:
            out["tangent"] = {"moved_share": {n: c_["tangent_moved_share"] for n, c_ in conf["blocks"]["tangent"]["conditions"].items()
                                              if "tangent_moved_share" in c_}}
    path = EXP / "summary.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("wrote", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
