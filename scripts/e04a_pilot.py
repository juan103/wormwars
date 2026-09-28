"""04a's development pilot (D104; Fable, review v1): batch A's shape at full size for a few hundred
generations on smoke ids (training 0-4 999, validation 5 000-5 255; outside every E1 and 04a range),
before the registration is bound. It shows whether this optimizer makes progress on Task N at all.
Descriptive only; never a result.

    python scripts/e04a_pilot.py --generations 200 --device cuda
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
_spec = importlib.util.spec_from_file_location("e04a_script", ROOT / "scripts" / "e04a.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

from wormwars import accounting as acct  # noqa: E402
from wormwars.brain import BrainSpec  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generations", type=int, default=200)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    prov = M.reg.provenance(M.GUARDED)
    con, iface = M.preflight(args.device)
    spec = BrainSpec.from_connectome(con)
    cfg = M.task_config()
    val, base, span = M.projection_ids()
    t0 = time.perf_counter()
    with acct.category("measure"):
        # the seeds it ran with: v1's formal seeds, since moved (D105), so the record stays reproducible
        recs = M.EV.evolve_batch(cfg, iface, spec, M.run_specs("A", 1_104_000), generations=args.generations,
                                 checkpoint_every=25, validation_ids=val, world_seed=M.REGISTERED["world_seed"],
                                 id_base=base, id_span=span, device=args.device, rollout_fn=M.rollout_mod.rollout)
    doc = {"what": "development pilot on smoke ids, before binding; descriptive only (D104)",
           "provenance": prov, "device": args.device, "generations": args.generations,
           "ids": {"training": [base, base + span - 1], "validation": M.id_record(val)},
           "seconds": time.perf_counter() - t0,
           "runs": [{"spec": vars(r.spec) if hasattr(r.spec, "__dict__") else str(r.spec),
                     "checkpoints": [{k: c[k] for k in ("generation", "validation_mean")} for c in r.checkpoints],
                     "best_count_every_10": [x["best_count"] for x in r.log[::10]],
                     "mean_count_every_10": [x["mean_count"] for x in r.log[::10]],
                     "best_fitness_every_10": [x["best_fitness"] for x in r.log[::10]]} for r in recs]}
    out = ROOT / "experiments" / "04a-navigation-primitive" / "development-records" / "pilot-evolution.json"
    M.reg.write_json(out, doc)
    for r in doc["runs"]:
        print(r["spec"]["run"], [round(c["validation_mean"], 2) for c in r["checkpoints"]])


if __name__ == "__main__":
    from wormwars.accounting import run_script
    run_script(main, out_default=str(ROOT / "runs" / "e04a-pilot"), default="measure", name="e04a-pilot")
