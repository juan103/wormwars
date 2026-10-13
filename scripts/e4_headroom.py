"""E4's headroom on stage A's block A (exploratory; D259, Fable's question in D257): E-G against the oracle and the
scripted follower (shared trails and none), on the same 16 mazes.

    python scripts/e4_headroom.py      # CPU; writes experiments/E4-two-minds/headroom.json
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import registration as reg  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e3 import assembly as AS  # noqa: E402
from wormwars.e3 import maze_measures as MM  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e4 import arms as AR  # noqa: E402
from wormwars.e4.train import gated_brain  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402


def _load(name, file):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


P4 = _load("e4_for_headroom", "e4.py")
OUT = ROOT / "experiments" / "E4-two-minds" / "headroom.json"
IDS, SEED = np.arange(40_800, 40_816), 1_400_000


def play(cfg, iface, brain, access):
    w = MW.MazeWorld(cfg, iface, brain, torch.zeros(len(IDS), 1, dtype=torch.long), run_seed=SEED, world_ids=IDS,
                     access=access)
    w.run()
    v = MM.colony_mean(w.task_events()["visits"])
    return {"mean": float(v.mean()), "per_maze": np.round(v, 4).tolist()}


def main():
    con, l1 = load_connectome(), A.load_l1()
    cfg = P4.cfg_for("shared")
    cx = AR.context(con, l1, cfg.brain)
    org = cx["org"]
    out = {"ids": IDS.tolist(), "provenance": reg.provenance(P4.GUARDED + ["scripts/e4_headroom.py"]),
           "eg": play(cfg, org.iface, gated_brain(org.genome.select([0]), org.gate), "shared")}
    cx3 = AS.context(con, l1, cfg.brain)
    for name, sp, access in (("oracle", {"kind": "oracle"}, "shared"),
                             ("follower_shared", {"kind": "follower", "access": "shared"}, "shared"),
                             ("follower_none", {"kind": "follower", "access": "none"}, "none")):
        c = P4.cfg_for(access)
        iface, brain, _, _ = P4.D.build(sp, c, con, l1, cx3, {}, "cpu")
        out[name] = play(c, iface, brain, access)
    out["eg_over_oracle"] = out["eg"]["mean"] / out["oracle"]["mean"]
    reg.write_json(OUT, out, atomic=True)
    print({k: round(v["mean"], 3) for k, v in out.items() if isinstance(v, dict) and "mean" in v}, round(out["eg_over_oracle"], 3))


if __name__ == "__main__":
    main()
