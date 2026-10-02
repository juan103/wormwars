"""E3b-0, after stage-b2 qualified no setting (exploratory diagnosis 3; D179). On the CPU, outside the GPU cap.

    python scripts/e3b0_diagnose3.py    # writes experiments/E3-ab-organism/E3b-0/development-records/stage-b2-diagnosis.json

Stage B's grid lowered the trail levels only by faster evaporation (higher μ, λ), which also shortens the
trails' reach. It never tried long-lived trails laid lightly. This checks, on selection mazes 0-63, whether
persistent trails (μ 0.005 or 0.01, λ 0.02, δ 0.05) at d₀ scaled down by 4, 8 and 16 from the pilot
(0.571) keep the follower's trail effect while meeting the high-level cap (at most 5% of unoccluded positive
on-route inputs above 0.35), and how the seeds' active K_D behaves at the low levels such trails would bring.
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
from wormwars.e3 import maze_measures as MM  # noqa: E402
from wormwars.e3 import maze_organisms as MO  # noqa: E402
from wormwars.e3 import maze_runs as MR  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e3 import organism as O  # noqa: E402
from wormwars.e3 import probe as P  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

OUT = ROOT / "experiments" / "E3-ab-organism" / "E3b-0" / "development-records" / "stage-b2-diagnosis.json"
SEED, C, H = 1_180_000, 5, 2400
IDS = np.arange(64)
D0 = 0.571
SHAPES = [dict(mu=0.005, lam=0.02, delta=0.05), dict(mu=0.01, lam=0.02, delta=0.05)]
SCALES = [1 / 4, 1 / 8, 1 / 16]
LOW_LEVELS = [0.001, 0.003, 0.005, 0.01, 0.02]


def main():
    iface = load_interface(load_connectome())
    out = {"note": __doc__.split("\n\n")[1], "maze_ids": [0, 64], "c": C, "H": H, "run_seed": SEED, "rows": []}
    base = MW.maze_config(c=C, horizon=H, colony=8, mu=0.01, lam=0.03, delta=0.15, d0=D0)
    none = MR.play(base, iface, lambda: MC.follower(iface, base), IDS, SEED, access="none")
    none_rate = MM.later_leg_rate(none["visit_tick"], H)[0]
    out["follower_none_rate"] = float(none_rate.mean())
    for shape in SHAPES:
        for k in SCALES:
            cfg = MW.maze_config(c=C, horizon=H, colony=8, d0=D0 * k, **shape)
            ev = MR.play(cfg, iface, lambda: MC.follower(iface, cfg), IDS, SEED, access="shared", nose_range=True)
            rate = MM.later_leg_rate(ev["visit_tick"], H)[0]
            nr = ev["nose_range"]
            row = {**shape, "d0": D0 * k, "d0_scale": k, "rate": float(rate.mean()),
                   "trail_effect": MM.world_ci(rate, none_rate), "above_0.35": nr["above_high_share_qualified"],
                   "quantiles": nr["quantiles_unoccluded_positive"], "zero_share": nr["zero"] / max(nr["on_route_noses"], 1)}
            out["rows"].append(row)
            print(json.dumps(row, default=float)[:400], flush=True)
    cfg = MW.maze_config(c=C, horizon=H, colony=8, mu=0.01, lam=0.03, delta=0.15, d0=D0)
    con, l1 = load_connectome(), A.load_l1()
    kd = {}
    for sname in ("E", "S3r3"):
        org = MO.maze_organism(con, MO.seed(sname, l1, cfg.brain, con=con), "W0", cfg.brain)
        w = MO.named_edges(org.genome, org.ext)[(O.Q, O.Q)]
        b = float(org.genome.bias[0, org.ext.index(O.Q)])
        r = L.stable_roots(w, b)
        states = {"A": max(r), "B": min(r)}
        pc = P.ProbeContext(org.ext, org.iface, cfg)
        kd[sname] = {f"{g}@{m}": float(P.k_d(org.genome, pc, g, m, pc.latch_state(org.genome, q)))
                     for g, q in states.items() for m in LOW_LEVELS}
        print(sname, kd[sname], flush=True)
    out["active_k_d_low_levels"] = kd
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    from wormwars.accounting import run_script
    run_script(main, out_default=str(ROOT / "runs" / "e3b0-diagnose"), default="measure", name="e3b0_diagnose3")
