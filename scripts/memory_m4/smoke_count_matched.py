"""M4a smoke diagnostic (not a plan arm; 64 N2 genomes per seed, other draws than the census): C3's internal cut for
ticks 1 to 30 against every external edge cut, and against three random sets of external edges of the same count.
Output: runs/memory-m4a-smoke/count_matched.txt.  Usage: python scripts/memory_m4/smoke_count_matched.py"""
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
import m4a  # noqa: E402
from wormwars.brain import Brain  # noqa: E402

c = m4a.c
torch.set_grad_enabled(False)
for seed in (7600, 7700):
    g, cfg = c.S.genomes(c.S.CON, 64, seed)
    cidx = m4a.core()
    internal, external = m4a.edge_sets(g.spec, cidx)
    brain, v0, food = c.ramp(g, cfg)
    intact, _ = m4a.follow_arm(brain, brain, cfg, v0, food, None, 100, cidx)
    rng = np.random.default_rng(1)
    sets = {"internal (260)": internal, "external, all": external}
    for d in range(3):
        sets[f"external, random 260 #{d}"] = rng.choice(external, len(internal), replace=False)
    print(f"seed {seed}")
    for name, e in sets.items():
        w = g.w.clone()
        w[:, e] = 0
        r, _ = m4a.follow_arm(brain, Brain(g.with_params(w=w)), cfg, v0, food, (1, 30), 100, cidx)

        def L(t, k="nv"):
            return 1 - r[k][:, t].sum() / intact[k][:, t].sum()
        print(f"  {name:26s} tick 3 {L(3):+.3f}; tick 30 {L(30):+.3f}; core at 30 "
              f"{r['nc'][:, 30].sum() / intact['nc'][:, 30].sum():.3f}; tick 60 {L(60):+.3f}; tick 100 {L(100):+.3f}; "
              f"read-out 60 {L(60, 'dy'):+.3f}")
