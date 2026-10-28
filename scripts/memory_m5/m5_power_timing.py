"""The fixed costs per host for M5's power calculation (docs/memory/M5-POWER-DESIGN.md, section 6): building a fresh
host of each ensemble (03's samplers, as M4e builds them), drawing an Rr block with its chain continued once (the
reference chain's order of cost), and checking it. Timed on the CPU; no panel is run. M4e's verification is timed
once, as the per-run part.

Writes runs/memory-m5-power/fixed-costs.json.
Usage: python scripts/memory_m5/m5_power_timing.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import m5_pilot as MP  # noqa: E402

m4d, m4e = MP.m4d, MP.m4e
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs" / "memory-m5-power"
SEED_TIMING = 9_700_000  # host seeds for timing only, far from every experiment's hosts; nothing here is read as data


def main():
    out = {"hosts": [], "rr_blocks": []}
    for i, kind in enumerate(m4e.ENSEMBLES):
        t0 = time.process_time()
        seed, tries = m4e.SEED_BASE[kind] + SEED_TIMING, 0
        while True:
            tries += 1
            try:
                m4d.build_host(kind, seed)
                break
            except MP.m4e.SM.SamplerFailure:
                seed += 1
        out["hosts"].append({"ensemble": kind, "tries": tries, "cpu_seconds": round(time.process_time() - t0, 2)})
        print(out["hosts"][-1], flush=True)
    for hd in range(5):
        t0 = time.process_time()
        Bn = m4d.n2_block()
        rng = np.random.default_rng(SEED_TIMING + hd)
        B1, _ = m4d.rewire(Bn, rng, keep_recip=True)
        m4d.rewire(B1, rng, keep_recip=True)
        MP.check_rr(B1.astype(np.float32))
        out["rr_blocks"].append({"cpu_seconds": round(time.process_time() - t0, 2)})
        print(out["rr_blocks"][-1], flush=True)
    t0 = time.process_time()
    m4e.verify_run()
    out["m4e_verify_run_cpu_seconds"] = round(time.process_time() - t0, 2)
    hosts = [h["cpu_seconds"] for h in out["hosts"]]
    rr = [b["cpu_seconds"] for b in out["rr_blocks"]]
    out["per_host_seconds"] = round(float(np.mean(hosts)) + 2 * float(np.mean(rr)), 2)  # a host and two draws' blocks
    out["note"] = ("process CPU seconds on the machine that runs M5; the power calculation charges per host one host "
                   "build, one Rr block (with its continued chains) per draw, and a tenth of M4e's verify_run, which "
                   "covers ten hosts (results round 1); per_host_seconds is the earlier sum, a host and two blocks")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "fixed-costs.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(out["per_host_seconds"], out["m4e_verify_run_cpu_seconds"])


if __name__ == "__main__":
    main()
