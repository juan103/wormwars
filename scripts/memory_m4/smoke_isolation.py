"""Smoke-only diagnostic (not a plan arm): what isolating C3 does, on 64 N2 genomes (other draws than the census)."""
import sys
from pathlib import Path
import numpy as np, torch
sys.path.insert(0, "scripts/memory_m4")
import m4a
from wormwars.brain import Brain
c = m4a.c
torch.set_grad_enabled(False)
for seed in (7600, 7700):
    g, cfg = c.S.genomes(c.S.CON, 64, seed)
    cidx = m4a.core()
    inc = np.zeros(g.spec.n, bool); inc[cidx] = True
    ci, cj = g.spec.chem_i.numpy(), g.spec.chem_j.numpy()
    gi, gj = g.spec.gap_i.numpy(), g.spec.gap_j.numpy()
    internal = np.where(inc[ci] & inc[cj] & (ci != cj))[0]
    inputs = np.where(inc[cj] & (ci != cj))[0]
    gaps = np.where(inc[gi] | inc[gj])[0]
    brain, v0, food = c.ramp(g, cfg)
    intact, _ = m4a.follow_arm(brain, brain, cfg, v0, food, None, 100, cidx)
    def with_cut(chem, gap):
        w = g.w.clone(); w[:, chem] = 0
        gg = g.g.clone(); gg[:, gap] = 0
        return Brain(g.with_params(w=w, g=gg))
    arms = {"internal": with_cut(internal, []), "inputs": with_cut(inputs, []), "gaps_C3": with_cut([], gaps),
            "inputs+gaps_C3": with_cut(inputs, gaps)}
    print(f"seed {seed}: internal {len(internal)}, inputs {len(inputs)}, gaps touching C3 {len(gaps)}")
    for name, b in arms.items():
        r, _ = m4a.follow_arm(brain, b, cfg, v0, food, (1, 30), 100, cidx)
        L60 = 1 - r["nv"][:, 60].sum() / intact["nv"][:, 60].sum()
        coll = r["nc"][:, 30].sum() / intact["nc"][:, 30].sum()
        L60y = 1 - r["dy"][:, 60].sum() / intact["dy"][:, 60].sum()
        print(f"  {name:15s} core at tick 30 (cut/intact) {coll:.3f}; loss at 60: state {L60:+.3f}, read-out {L60y:+.3f}")
