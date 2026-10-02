"""E3b-0, after the reviews of Stage B (exploratory diagnosis 2; D178). On the CPU, outside the GPU cap.

    python scripts/e3b0_diagnose2.py    # writes experiments/E3-ab-organism/E3b-0/development-records/stage-b-diagnosis-2.json

Both reviewers (docs/reviews/20261002-E3b-0-stage-b/) asked to separate the polarity test's competing
explanations before blaming the controller, and to qualify the nose levels actually met:
1. Polarity, on selection mazes 0-63, at the pilot constants and at Stage B's highest-rate setting: the start
   facing away from A (registered), toward A (the route's previous cell, corrected) and at a uniform heading;
   the trail aged 1 leg (registered) or 0; passes within 2× (registered) and 4× the oracle's time from one
   run each; the follower's arrival time over the oracle's.
2. A synthetic trail with a known slope, exp(−d / 8) on the route cells (d the free distance from A), at each
   heading: can this follower use a clean longitudinal slope at all?
3. The levels met: quantiles of the unoccluded, positive, on-route goal-channel nose inputs once the goal's
   trail exists, for the follower's shared colony.
4. The seeds' active K_D (E3a's probe) at levels above the registered 0.35.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e3 import latch as L  # noqa: E402
from wormwars.e3 import maze_controls as MC  # noqa: E402
from wormwars.e3 import maze_organisms as MO  # noqa: E402
from wormwars.e3 import maze_runs as MR  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e3 import organism as O  # noqa: E402
from wormwars.e3 import probe as P  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

OUT = ROOT / "experiments" / "E3-ab-organism" / "E3b-0" / "development-records" / "stage-b-diagnosis-2.json"
SEED, C, H = 1_180_000, 5, 2400
IDS = np.arange(64)
SETTINGS = {"pilot": dict(mu=0.01, lam=0.03, delta=0.15, d0=0.571),
            "stage_b_best_rate": dict(mu=0.005, lam=0.02, delta=0.05, d0=0.571)}
HIGH_LEVELS = [0.35, 0.5, 0.7, 1.0, 1.5, 2.0]


def readings(p: dict) -> dict:
    ok = p["single_pass"].astype(bool)
    t = p["oracle_ticks"].astype(np.float64)
    out = {"single_pass_mazes": int(ok.sum())}
    for name in ("real", "none", "permuted"):
        first = p[f"first_tick_{name}"]
        arrived = first >= 0
        for f in (2, 4):
            out[f"{name}_within_{f}x"] = float(((arrived & (first + 1 <= np.ceil(f * t)))[ok]).mean())
        ratio = np.where(arrived, (first + 1) / t, np.inf)[ok]
        out[f"{name}_time_over_oracle_quartiles"] = [float(x) for x in np.quantile(ratio, [0.25, 0.5, 0.75])]
    for f in (2, 4):
        out[f"reading_{f}x"] = out[f"real_within_{f}x"] - max(out[f"none_within_{f}x"], out[f"permuted_within_{f}x"])
    return out


def main():
    iface = load_interface(load_connectome())
    out = {"note": __doc__.split("\n\n")[1], "maze_ids": [0, 64], "c": C, "H": H, "run_seed": SEED, "settings": {}}
    for name, s in SETTINGS.items():
        cfg = MW.maze_config(c=C, horizon=H, colony=8, **s)
        one = MW.maze_config(c=C, horizon=H, colony=1, **s)
        row = {"constants": s}
        for facing in ("away", "toward", "random"):
            for age in (1.0, 0.0):
                p = MR.polarity(one, iface, IDS, SEED, facing=facing, limit_factor=4.0, age_legs=age)
                row[f"polarity_{facing}_age{int(age)}"] = readings(p)
        for facing in ("away", "toward", "random"):
            p = MR.polarity(one, iface, IDS, SEED, facing=facing, limit_factor=4.0,
                            synthetic=lambda mz, pl, route: np.where(route, np.exp(-np.where(np.isfinite(
                                mz.free_distance(pl.a)), mz.free_distance(pl.a), 0.0) / 8.0), 0.0))
            row[f"synthetic_{facing}"] = readings(p)
        ev = MR.play(cfg, iface, lambda: MC.follower(iface, cfg), IDS, SEED, access="shared", nose_range=True)
        row["nose_range"] = ev["nose_range"]
        out["settings"][name] = row
        print(name, json.dumps({k: v for k, v in row.items() if k.startswith(("polarity_toward_age1", "synthetic_"))},
                               default=float)[:1200], flush=True)
    # 4. the seeds' active K_D at high levels
    cfg = MW.maze_config(c=C, horizon=H, colony=8, **SETTINGS["pilot"])
    con, l1 = load_connectome(), A.load_l1()
    kd = {}
    for sname in ("E", "S3r3"):
        org = MO.maze_organism(con, MO.seed(sname, l1, cfg.brain, con=con), "W0", cfg.brain)
        w = MO.named_edges(org.genome, org.ext)[(O.Q, O.Q)]
        b = float(org.genome.bias[0, org.ext.index(O.Q)])
        r = L.stable_roots(w, b)
        states = {"A": max(r), "B": min(r)}
        pc = P.ProbeContext(org.ext, org.iface, cfg)
        kd[sname] = {"latch_states": states,
                     "active": {f"{g}@{m}": float(P.k_d(org.genome, pc, g, m, pc.latch_state(org.genome, q)))
                                for g, q in states.items() for m in HIGH_LEVELS}}
        print(sname, kd[sname], flush=True)
    out["active_k_d_high_levels"] = kd
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    from wormwars.accounting import run_script
    run_script(main, out_default=str(ROOT / "runs" / "e3b0-diagnose"), default="measure", name="e3b0_diagnose2")
