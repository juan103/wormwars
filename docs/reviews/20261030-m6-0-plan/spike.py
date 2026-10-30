"""Throwaway (M6 option 0's plan): the first-pass classifier on 02's T1-M0-N2 champions, g00 and g39, on the CPU.
How long does it take, and how many would need the 22,000-tick second pass? Not a result."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(r"D:\Claude\random\wormWars")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m1"))
import pilot as P  # noqa: E402
import common as c  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.evo import load_genome  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402

torch.set_grad_enabled(False)
RUNS = ROOT / "runs" / "exp02-screening"
CAL = json.loads((grid.EXP02_DIR / "calibration.json").read_text(encoding="utf-8"))
graph = grid.graph_for(c.S.CON, "N2")
spec = BrainSpec.from_connectome(graph, device="cpu")
cfg = grid.brain_config_for_graph(grid.task_config(Config(), "T1"), "N2")
cfg.world.forward_gain, cfg.world.turn_gain = CAL["N2"]["forward_gain"], CAL["N2"]["turn_gain"]
_, cfg_probe = c.S.genomes(c.S.CON, 1, 1)
print("probe cfg brain == champion cfg brain:", cfg.brain == cfg_probe.brain)
for tag in ("g00", "g39"):
    gs = [load_genome(RUNS / f"T1-M0-N2-run{r:02d}-{tag}.npz", spec, None, device="cpu")[0] for r in range(8)]
    g = Genome.cat(gs)
    t0 = time.perf_counter()
    run = P.probe_states(g, cfg)
    sub = {"end": run["end"], "cur": run["cur"], "y": run["y"], "tail": run["tail"]}
    recs, _ = P.full_classify(g, cfg, sub, compact=True)
    dt = time.perf_counter() - t0
    print(tag, f"{dt:.1f} s for 8 genomes")
    for r in recs:
        print("  ", r["class"], "|", r["reason"], "| a", f"{r['a']:.4f}", "d30", f"{r['d30']:.4f}", "d300", f"{r['d300']:.4f}",
              "rootdist", f"{r['root_distance']:.2e}")
