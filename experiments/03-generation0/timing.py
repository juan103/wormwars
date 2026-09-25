"""Throughput of generation-0 fitness at wide batches, on a pilot shuffle (SH101), never N2.
Random genomes are scored on a few worlds each; the question is genome-world evaluations per
second as the batch widens. Writes timing.json next to this file."""

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.connectome.graphs import shuffled  # noqa: E402
from wormwars.evo import rollout  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.exp02 import probes as P  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

dev = "cuda"
con = load_connectome()
iface = load_interface(con)
graph = shuffled(con, 101, "SH101")
spec = BrainSpec.from_connectome(graph, device=dev)
out = {"fitness": [], "input_response": {}}
for task in ("T1", "T0"):
    cfg = grid.task_config(Config(), task)
    for strains, worlds in ((64, 4), (256, 4), (512, 4), (1024, 4), (256, 8)):
        g = Genome.random(spec, cfg.brain, strains, generator=torch.Generator(device=dev).manual_seed(0), device=dev)
        ids = np.arange(990_000_000, 990_000_000 + worlds)
        torch.cuda.synchronize()
        t = time.perf_counter()
        try:
            rollout(cfg, iface, g, ids, 5, dev)
            torch.cuda.synchronize()
            dt = time.perf_counter() - t
            row = {"task": task, "strains": strains, "worlds": worlds, "seconds": dt,
                   "genome_worlds_per_s": strains * worlds / dt}
        except RuntimeError as e:  # out of memory at this width
            row = {"task": task, "strains": strains, "worlds": worlds, "error": str(e)[:120]}
            torch.cuda.empty_cache()
        out["fitness"].append(row)
        print(row, flush=True)
cfg = grid.task_config(Config(), "T1")
for n in (256, 2048):
    torch.cuda.synchronize()
    t = time.perf_counter()
    P.input_response(spec, cfg, iface, n, dev)
    torch.cuda.synchronize()
    out["input_response"][n] = time.perf_counter() - t
    print("input response", n, out["input_response"][n], flush=True)
(Path(__file__).parent / "timing.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
