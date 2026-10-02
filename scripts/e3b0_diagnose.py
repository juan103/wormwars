"""E3b-0, after Stage B chose no setting (exploratory diagnosis; D178). On the CPU, outside the GPU cap.

    python scripts/e3b0_diagnose.py     # writes experiments/E3-ab-organism/E3b-0/development-records/stage-b-diagnosis.json

Stage B (c 5, H 2 400) failed every setting on polarity (real − max(none, permuted) at most +0.02, against
0.3) and on the nose range (in range at most 0.46, against 0.9), while the gradient share passed (0.80-0.94).
Three questions, on selection mazes 0-63, at the pilot constants and at Stage B's highest-rate setting:
1. Do trails help the scripted follower at all? Its later-leg rate with shared, own and no trails.
2. Is the polarity failure the start's heading? The polarity test facing away from A (as registered), facing
   toward A, and at a uniform heading.
3. How much of the range failure is occlusion? The range with occluded noses counted apart.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e3 import maze_controls as MC  # noqa: E402
from wormwars.e3 import maze_measures as MM  # noqa: E402
from wormwars.e3 import maze_runs as MR  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

OUT = ROOT / "experiments" / "E3-ab-organism" / "E3b-0" / "development-records" / "stage-b-diagnosis.json"
SEED, C, H = 1_180_000, 5, 2400
IDS = np.arange(64)
SETTINGS = {"pilot": dict(mu=0.01, lam=0.03, delta=0.15, d0=0.571),
            "stage_b_best_rate": dict(mu=0.005, lam=0.02, delta=0.05, d0=0.571)}


def main():
    iface = load_interface(load_connectome())
    out = {"note": __doc__.split("\n\n")[1], "maze_ids": [0, 64], "c": C, "H": H, "run_seed": SEED, "settings": {}}
    for name, s in SETTINGS.items():
        cfg = MW.maze_config(c=C, horizon=H, colony=8, **s)
        one = MW.maze_config(c=C, horizon=H, colony=1, **s)
        row = {"constants": s}
        rates = {}
        for mode in ("shared", "own", "none"):
            ev = MR.play(cfg, iface, lambda: MC.follower(iface, cfg), IDS, SEED, access=mode, nose_range=(mode == "shared"))
            rates[mode] = MM.later_leg_rate(ev["visit_tick"], H)[0]
            row[f"follower_{mode}"] = {"later_leg_rate": float(rates[mode].mean()),
                                       "visits": float(MM.colony_mean(ev["visits"]).mean())}
            if mode == "shared":
                row["nose_range"] = ev["nose_range"]
        row["shared_minus_none"] = MM.world_ci(rates["shared"], rates["none"])
        row["own_minus_none"] = MM.world_ci(rates["own"], rates["none"])
        row["shared_minus_own"] = MM.world_ci(rates["shared"], rates["own"])
        for facing in ("away", "toward", "random"):
            p = MR.polarity(one, iface, IDS, SEED, facing=facing)
            ok = p["single_pass"].astype(bool)
            row[f"polarity_{facing}"] = {k: float(p[f"pass_{k}"][ok].mean()) for k in ("real", "none", "permuted")}
            row[f"polarity_{facing}"]["single_pass_mazes"] = int(ok.sum())
        out["settings"][name] = row
        print(name, json.dumps(row, default=float)[:900], flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    from wormwars.accounting import run_script
    run_script(main, out_default=str(ROOT / "runs" / "e3b0-diagnose"), default="measure", name="e3b0_diagnose")
