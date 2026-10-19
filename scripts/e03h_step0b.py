"""03h's step 0b (DECISIONS.md D330, specified before it ran): exploratory read-outs on step 0's genomes.

    python scripts/e03h_step0b.py            # on CUDA; writes experiments/03h-history-use/development-records/step0b.json
    python scripts/e03h_step0b.py --smoke    # two graphs, few genomes, on the CPU (checks the code)

On 03's 16 pilot SH graphs x 256 fitness genomes, by step 0's verified recipe (`scripts/e03h_step0.py`), inside
`replay_mode()`, and against the committed T1-M0 fitness, five read-outs, all reported:
1. the partial Spearman of H_dir with fitness, given S. H_dir is |motor turn after the falling history| −
   |motor turn after the rising history|, at the final tick;
2. the plain Spearman of H with fitness;
3. the plain Spearman of S with fitness;
4. the partial Spearman of |motor-turn final difference| with fitness, given |motor-turn steady contrast|;
5. the partial Spearman of |raw-forward final difference| with fitness, given |raw-forward steady contrast|.

None of it sets a primary, a threshold or a rule.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.e03h.stats import partial_spearman  # noqa: E402
from wormwars.evo.bundle import replay_mode  # noqa: E402
from wormwars.exp03.measures import history  # noqa: E402

_spec = importlib.util.spec_from_file_location("e03h_step0_for_0b", ROOT / "scripts" / "e03h_step0.py")
S0 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S0)

READOUTS = ("H_dir_partial", "H_plain", "S_plain", "motor_turn_partial", "raw_forward_partial")


def _rho(a, b) -> float:
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return 0.0
    return float(spearmanr(a, b).statistic)


def run(smoke: bool) -> dict:
    pilot, con, iface, records = S0._context()
    device = "cpu" if smoke else "cuda"
    names = sorted(records)[:2] if smoke else sorted(records)
    ctx = contextlib.nullcontext if smoke else replay_mode
    graphs = {}
    for name in names:
        rec = records[name]
        cfg = S0.cfg_t1(name, tuple(rec["gains"]))
        with acct.category("measure"), ctx():
            g = S0.genomes_of(con, name, cfg, 256, device)
            if smoke:
                g = g.select(list(range(S0.SMOKE_GENOMES)))
            h = history(g, cfg, iface, pilot["bank"], per_history=True)
        fit = np.asarray(rec["fitness"]["T1-M0"], dtype=np.float64)[: g.n_strains].mean(axis=1)
        H, S = np.abs(h["raw_turn"]["final"]), np.abs(h["raw_turn"]["steady_contrast"])
        mt = h["motor_turn"]
        h_dir = np.abs(mt["falling"]["final"]) - np.abs(mt["rising"]["final"])
        graphs[name] = {
            "H_dir_partial": partial_spearman(h_dir, fit, S)[0],
            "H_plain": _rho(H, fit),
            "S_plain": _rho(S, fit),
            "motor_turn_partial": partial_spearman(np.abs(mt["final"]), fit, np.abs(mt["steady_contrast"]))[0],
            "raw_forward_partial": partial_spearman(np.abs(h["raw_forward"]["final"]), fit,
                                                    np.abs(h["raw_forward"]["steady_contrast"]))[0],
        }
    summary = {}
    for k in READOUTS:
        v = np.array([r[k] for r in graphs.values()])
        summary[k] = {"mean": float(v.mean()), "between_graph_sd": float(v.std(ddof=1)) if len(v) > 1 else None,
                      "positive": int((v > 0).sum()), "graphs": len(v)}
    return {"exploratory": True, "specified_in": "DECISIONS.md D330, before the run", "device": device,
            "smoke": smoke, "graphs": graphs, "summary": summary,
            "note": "the spreads condition on 03's 16 shared worlds; none of this sets a primary, threshold or rule"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)
    prov = reg.provenance(S0.GUARDED)
    if not args.smoke:
        if prov["dirty"]:
            raise SystemExit("uncommitted changes in the guarded files: commit first")
        reg.require_pins(prov)
        if not torch.cuda.is_available():
            raise SystemExit("step 0b runs on CUDA (03's genomes were drawn by a CUDA generator)")
        step0 = json.loads((S0.EXP / "development-records" / "step0.json").read_text(encoding="utf-8"))
        if not step0.get("verified_by"):
            raise SystemExit("step 0's recipe is not verified (step0.json), so step 0b does not run")
    out_dir = ROOT / "runs" / ("e03h-smoke" if args.smoke else "e03h") / "step0"
    rec = (out_dir / "step0b.json") if args.smoke else (S0.EXP / "development-records" / "step0b.json")
    t0 = time.time()
    with acct.recorded(out_dir / "compute", out_dir / "compute.json", default="measure", experiment="03h",
                       stage="step0b", script="scripts/e03h_step0b.py"):
        doc = run(args.smoke)
    doc.update({"provenance": prov, "seconds": time.time() - t0})
    reg.write_json(rec, doc, atomic=True)
    print(f"step 0b: {json.dumps(doc['summary'])} -> {rec}")
    return doc


if __name__ == "__main__":
    main()
