"""E3b-0, after the redesign review (exploratory diagnosis 4; D179).

    python scripts/e3b0_diagnose4.py --part seeds --device cuda      # counted in E3b-0's compute (runs/e3b0)
    python scripts/e3b0_diagnose4.py --part follower --device cpu    # counted apart (runs/e3b0-diagnose)

Both reviewers (docs/reviews/20261003-E3b-0-redesign/) asked for diagnosis before any redesign:
- **seeds** (Fable's decisive test): do the seeds themselves gain from linear trails? E and S3r3, each with
  W0, W1 and W2, on the 256 selection mazes, shared trails at Stage B's highest-rate setting (μ 0.005,
  λ 0.02, δ 0.05, d₀ 0.571) and at a medium one (μ 0.01, λ 0.04, δ 0.05, d₀ 0.571), against no trail;
  with their own nose levels. Writes development-records/diagnosis-4-seeds.json.
- **follower** (both): what produces the follower's trail effect, on mazes 0-63 at the highest-rate
  setting: its branch occupancy and pair differences; a gain-0 variant (the policy switch alone); an
  occlusion-symmetric variant (a blocked nose ignored); gain 128 at d₀/4; each against its own no-trail
  run. Writes development-records/diagnosis-4-follower.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.brain import Brain  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a.evolve import moved  # noqa: E402
from wormwars.e3 import maze_controls as MC  # noqa: E402
from wormwars.e3 import maze_measures as MM  # noqa: E402
from wormwars.e3 import maze_organisms as MO  # noqa: E402
from wormwars.e3 import maze_runs as MR  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

REC = ROOT / "experiments" / "E3-ab-organism" / "E3b-0" / "development-records"
SEED, C, H = 1_180_000, 5, 2400
BEST = dict(mu=0.005, lam=0.02, delta=0.05, d0=0.571)
MEDIUM = dict(mu=0.01, lam=0.04, delta=0.05, d0=0.571)


def rates(ev):
    return MM.later_leg_rate(ev["visit_tick"], H)[0]


def brief(ev):
    r = rates(ev)
    return {"later_leg_rate": float(r.mean()), "visits": float(MM.colony_mean(ev["visits"]).mean()),
            "legs_median": float(np.median(MM.colony_mean(MM.legs(ev["visit_tick"]))))}


def seeds(device: str) -> dict:
    ids = np.arange(256)
    con, l1 = load_connectome(), A.load_l1()
    out = {"maze_ids": [0, 256], "settings": {"best": BEST, "medium": MEDIUM}, "rows": []}
    for sname in ("E", "S3r3"):
        for variant in ("W0", "W1", "W2"):
            cfg0 = MW.maze_config(c=C, horizon=H, colony=8, **BEST)
            org = MO.maze_organism(con, MO.seed(sname, l1, cfg0.brain, con=con), variant, cfg0.brain)
            g = moved(org.genome, device)
            none = MR.play(cfg0, org.iface, lambda: Brain(g), ids, SEED, device, access="none")
            row = {"seed": sname, "variant": variant, "none": brief(none)}
            for label, s in (("best", BEST), ("medium", MEDIUM)):
                cfg = MW.maze_config(c=C, horizon=H, colony=8, **s)
                ev = MR.play(cfg, org.iface, lambda: Brain(g), ids, SEED, device, access="shared", nose_range=True)
                nr = ev["nose_range"]
                row[label] = {**brief(ev), "trail_effect": MM.world_ci(rates(ev), rates(none)),
                              "above_0.35": nr["above_high_share_qualified"],
                              "quantiles": nr["quantiles_unoccluded_positive"],
                              "steering_share_on_route": nr["steering_share_on_route"]}
            out["rows"].append(row)
            print(json.dumps(row, default=float)[:700], flush=True)
    return out


def follower(device: str) -> dict:
    iface = load_interface(load_connectome())
    ids = np.arange(64)
    out = {"maze_ids": [0, 64], "setting": BEST, "variants": {}}
    variants = {"k32": (dict(), 1.0), "k0": (dict(k=0.0), 1.0), "symmetric": (dict(symmetric_occlusion=True), 1.0),
                "k128_d0_quarter": (dict(k=128.0), 0.25)}
    for name, (kw, scale) in variants.items():
        cfg = MW.maze_config(c=C, horizon=H, colony=8, **{**BEST, "d0": BEST["d0"] * scale})
        make = lambda: MC.WorldScripted(iface, cfg, MC.TrailFollower(**kw), device=device)  # noqa: E731
        none = MR.play(cfg, iface, make, ids, SEED, device, access="none", nose_range=True)
        shared = MR.play(cfg, iface, make, ids, SEED, device, access="shared", nose_range=True)
        nr, nn = shared["nose_range"], none["nose_range"]
        row = {"policy": kw, "d0": cfg.world.maze_trail_d0, "shared": brief(shared), "none": brief(none),
               "trail_effect": MM.world_ci(rates(shared), rates(none)),
               "steering_share_on_route": {"shared": nr["steering_share_on_route"], "none": nn["steering_share_on_route"]},
               "steering_share_all": {"shared": nr["steering_share_all"], "none": nn["steering_share_all"]},
               "pairs_turn_relevant_share": nr["pairs_turn_relevant_share"],
               "pair_abs_difference_quantiles": nr["pair_abs_difference_quantiles"],
               "level_quantiles": nr["quantiles_unoccluded_positive"], "occluded_share": nr["occluded"] / max(nr["on_route_noses"], 1)}
        out["variants"][name] = row
        print(name, json.dumps(row, default=float)[:700], flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=("seeds", "follower"), required=True)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out")
    a = ap.parse_args()
    doc = seeds(a.device) if a.part == "seeds" else follower(a.device)
    doc["note"] = __doc__.split("\n\n")[1]
    doc["device"] = a.device
    REC.mkdir(parents=True, exist_ok=True)
    (REC / f"diagnosis-4-{a.part}.json").write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8",
                                                     newline="\n")


if __name__ == "__main__":
    from wormwars.accounting import run_script
    part_seeds = "seeds" in sys.argv
    run_script(main, out_default=str(ROOT / "runs" / ("e3b0" if part_seeds else "e3b0-diagnose")), default="measure",
               name="e3b0_diagnose4")
