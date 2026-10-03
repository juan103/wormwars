"""E3b-0: why S3r3 fails the maze (exploratory diagnosis 5; the results review, D180). On the CPU.

    python scripts/e3b0_diagnose5.py    # writes experiments/E3-ab-organism/E3b-0/development-records/diagnosis-5-turning.json

S3r3 failed Stage C with every variant. This records, for S3r3 + W2 and E + W2 on 4 smoke mazes (ids
9000-9003, outside every formal block) for 600 ticks at the chosen trail setting: the mean turn command, its
mean absolute value, the forward command, the diagonal of each wey's path's bounding box, visits per wey and
raw entries into A and B. It replaces an uncommitted look reported in D179.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e3 import maze_organisms as MO  # noqa: E402
from wormwars.e3 import maze_runs as MR  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402

OUT = ROOT / "experiments" / "E3-ab-organism" / "E3b-0" / "development-records" / "diagnosis-5-turning.json"
SETTING = dict(mu=0.01, lam=0.02, delta=0.05, d0=1.142)


def main():
    con, l1 = load_connectome(), A.load_l1()
    cfg = MW.maze_config(c=5, horizon=600, colony=8, **SETTING)
    out = {"note": __doc__.split("\n\n")[1], "maze_ids": [9000, 9004], "ticks": 600, "setting": SETTING, "rows": {}}
    for sname in ("S3r3", "E"):
        org = MO.maze_organism(con, MO.seed(sname, l1, cfg.brain, con=con), "W2", cfg.brain)
        w = MR.world(cfg, org.iface, MO.brain(org), np.arange(9000, 9004), 1_180_000, access="shared")
        pos, turn, fwd = [], [], []
        while w.tick_count < 600:
            w.tick()
            pos.append(w.pos[:, 0].clone())
            turn.append(w.last_turn[:, 0].clone())
            fwd.append(w.last_forward[:, 0].clone())
        P, T, F = torch.stack(pos), torch.stack(turn), torch.stack(fwd)
        ev = w.task_events()
        out["rows"][f"{sname}+W2"] = {"mean_turn": float(T.mean()), "mean_abs_turn": float(T.abs().mean()),
                                      "mean_forward": float(F.mean()),
                                      "path_bbox_diagonal": float((P.amax(0) - P.amin(0)).norm(dim=-1).mean()),
                                      "visits_per_wey": float(ev["visits"].mean()),
                                      "entries_a_b": [int(x) for x in ev["entries"].sum((0, 1))]}
        print(sname, out["rows"][f"{sname}+W2"], flush=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    from wormwars.accounting import run_script
    run_script(main, out_default=str(ROOT / "runs" / "e3b0-diagnose"), default="measure", name="e3b0_diagnose5")
