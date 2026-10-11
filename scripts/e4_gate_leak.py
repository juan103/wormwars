"""E4's gate-leak measurement (CPU only; exploratory; both reviewers of E4's design v1, D243).

The seed E + W2 gates its two comparator modules by saturation (E3a): the inactive module's comparators sit at a
bias near −3.8, but its noses still feed them at ±3 and its motor edges stay live. This measures how much turn
signal the inactive module still sends, on E3f's maze family.

    python scripts/e4_gate_leak.py      # writes docs/E4/gate-leak.json

**The play:** the seed on 16 fresh mazes (ids 42 000-42 015, outside every E3 block), 6 × 6, k_r = 0,
H = 1 800, colonies of 8, shared trails, the maze run seed 1 192 000.

**Per tick and wey:**
- **the mode:** A is active when the latch E3_Q is positive (Q → A's comparators +2, → B's −2);
- **each module's turn signal:** tanh(CL) − tanh(CR), the difference its comparators send to the turn motors at
  ±3, read for the active and the inactive module;
- **the nose drive into the inactive comparators,** for comparison.
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
from wormwars.e3 import maze_organisms as MO  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402

IDS = list(range(42_000, 42_016))
H, SEED = 1800, 1_192_000


def main():
    con, l1 = load_connectome(), A.load_l1()
    cfg = MW.maze_config(c=6, horizon=H, colony=8, mu=0.01, lam=0.02, delta=0.05, d0=1.142, access="shared",
                         family="islands", k_r=0)
    seed = AS.context(con, l1, cfg.brain)["seed"]
    ext = seed.ext
    idx = {n: ext.index(n) for n in ("E3_Q", "E3_A_CL", "E3_A_CR", "E3_B_CL", "E3_B_CR",
                                     "E3_A_NL", "E3_A_NR", "E3_B_NL", "E3_B_NR")}
    w = MW.MazeWorld(cfg, seed.iface, MO.brain(seed, "cpu"), torch.zeros(len(IDS), 1, dtype=torch.long),
                     run_seed=SEED, world_ids=np.asarray(IDS), access="shared")
    rows = {k: [] for k in ("q", "a_turn", "b_turn", "a_nose", "b_nose")}
    for _ in range(H):
        w.tick()
        v = w.assigns[0].from_brain(w.v[0], w.n_worlds, w.n_weys)  # [worlds, weys, N]
        t = torch.tanh(v)
        rows["q"].append(v[..., idx["E3_Q"]].numpy().copy())
        rows["a_turn"].append((t[..., idx["E3_A_CL"]] - t[..., idx["E3_A_CR"]]).numpy().copy())
        rows["b_turn"].append((t[..., idx["E3_B_CL"]] - t[..., idx["E3_B_CR"]]).numpy().copy())
        rows["a_nose"].append((t[..., idx["E3_A_NL"]] - t[..., idx["E3_A_NR"]]).numpy().copy())
        rows["b_nose"].append((t[..., idx["E3_B_NL"]] - t[..., idx["E3_B_NR"]]).numpy().copy())
    R = {k: np.stack(v) for k, v in rows.items()}  # [ticks, worlds, weys]
    a_on = R["q"] > 0
    active = np.where(a_on, R["a_turn"], R["b_turn"])
    inactive = np.where(a_on, R["b_turn"], R["a_turn"])
    inactive_nose = np.where(a_on, R["b_nose"], R["a_nose"])
    q = lambda x, p: float(np.quantile(np.abs(x), p))  # noqa: E731
    out = {
        "ids": IDS, "H": H, "seed": SEED, "ticks_x_weys": int(active.size),
        "share_of_ticks_A_active": float(a_on.mean()),
        "active_turn_signal_abs": {f"q{p}": q(active, p) for p in (0.5, 0.9, 0.99)},
        "inactive_turn_signal_abs": {f"q{p}": q(inactive, p) for p in (0.5, 0.9, 0.99, 0.999)},
        "inactive_over_active_q99": q(inactive, 0.99) / max(q(active, 0.99), 1e-12),
        "share_of_ticks_inactive_signal_above_0.05": float((np.abs(inactive) > 0.05).mean()),
        "share_of_ticks_inactive_signal_above_0.2": float((np.abs(inactive) > 0.2).mean()),
        "inactive_nose_difference_abs": {f"q{p}": q(inactive_nose, p) for p in (0.5, 0.9, 0.99)},
        "visits_per_wey": float(w.task_events()["visits"].mean()),
    }
    path = ROOT / "docs" / "E4" / "gate-leak.json"
    path.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
