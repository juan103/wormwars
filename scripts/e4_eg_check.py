"""E4: a CPU look at E-G's competence against the seed (exploratory; docs/E4/E4-DESIGN.md v3 §1). Not the
re-qualification, which plays the blind family on E4's blocks; this only shows whether E-G navigates at all.

    python scripts/e4_eg_check.py      # writes docs/E4/eg-check.json

The seed and E-G, each on 16 fresh mazes (ids 42 000-42 015, as the leak measurement), 6 × 6, k_r = 0,
H = 1 800, colonies of 8, shared trails, the maze run seed 1 192 000; and the random walk as a blind reference.
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
from wormwars.e3 import assembly as AS  # noqa: E402
from wormwars.e3 import maze_controls as MC  # noqa: E402
from wormwars.e3 import maze_measures as MM  # noqa: E402
from wormwars.e3 import maze_organisms as MO  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e4 import organism as E4O  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

IDS = list(range(42_000, 42_016))


def play(cfg, iface, brain):
    w = MW.MazeWorld(cfg, iface, brain, torch.zeros(len(IDS), 1, dtype=torch.long), run_seed=1_192_000,
                     world_ids=np.asarray(IDS), access="shared")
    w.run()
    ev = w.task_events()
    legs = MM.legs(ev["visit_tick"])
    return {"visits": float(ev["visits"].mean()), "median_colony_legs": float(np.median(legs.mean(-1))),
            "per_maze_visits": np.round(ev["visits"].mean(-1), 4).tolist()}


def main():
    con, l1 = load_connectome(), A.load_l1()
    cfg = MW.maze_config(c=6, horizon=1800, colony=8, mu=0.01, lam=0.02, delta=0.05, d0=1.142, access="shared",
                         family="islands", k_r=0)
    seed = AS.context(con, l1, cfg.brain)["seed"]
    eg = E4O.eg(con, l1, cfg.brain)
    plain = load_interface(con)
    out = {"ids": IDS,
           "seed": play(cfg, seed.iface, MO.brain(seed, "cpu")),
           "E-G": play(cfg, eg.iface, MO.brain(eg, "cpu")),
           "walk": play(cfg, plain, MC.WorldScripted(plain, cfg, MC.ReflexWalk(1.0, 2.0, 0.5, seed=0)))}
    path = ROOT / "docs" / "E4" / "eg-check.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print({k: (v["visits"], v["median_colony_legs"]) for k, v in out.items() if k != "ids"})


if __name__ == "__main__":
    main()
