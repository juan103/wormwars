"""Does longer evolution make champions use the capabilities the tasks were designed around?
Discarded shuffle SH101 only. T1: sensitivity to jitter (history). T0: loss when reduced to one nose."""

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from wormwars import calibration as calib
from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import shuffled
from wormwars.evo import SeedPool, rollout
from wormwars.evo.evolve import evolve
from wormwars.exp02 import grid
from wormwars.interface import load_interface

dev = "cuda"
con = load_connectome()
iface = load_interface(con)
graph = shuffled(con, 101, "SH101")
spec = BrainSpec.from_connectome(graph, device=dev)
cal = calib.calibrate_in_world(graph, grid.task_config(Config(), "T0"), iface, grid.TARGET_DRIVE,
                               n_strains=grid.CALIBRATION_STRAINS, device=dev)


def pb(a, b, n=20000):
    d = np.asarray(a) - np.asarray(b)
    rng = np.random.default_rng(0)
    m = d[rng.integers(0, len(d), (n, len(d)))].mean(1)
    return f"{d.mean():+.3f} [{np.quantile(m, .025):+.3f}, {np.quantile(m, .975):+.3f}]"


for task in ("T1", "T0"):
    cfg = grid.task_config(Config(), task)
    cfg.world.forward_gain, cfg.world.turn_gain = cal.forward_gain, cal.turn_gain
    cfg.evo.generations = 120
    seed = 31_500
    t = time.perf_counter()
    res = evolve(cfg, iface, spec, 0, seed, device=dev, holdout_every=40, checkpoint_ids=grid.CHECKPOINT_IDS,
                 snapshots=(39, 79, 119), verbose=False)
    ids = SeedPool(cfg, seed).holdout
    print(f"{task}: 120 generations in {time.perf_counter() - t:.0f}s", flush=True)
    for g in (39, 79, 119):
        champ = res.snapshots[g]
        real = rollout(cfg, iface, champ, ids, seed, dev).score[0]
        line = f"   gen {g + 1:3d}: held-out {real.mean():.3f}"
        for name, kw in (("jitter1", {"food_probe": "jitter", "food_probe_radius": 1.0}),
                         ("jitter3", {"food_probe": "jitter", "food_probe_radius": 3.0}),
                         ("constant", {"food_probe": "constant"}),
                         ("mono", {"food_sensing": "mono"})):
            if name == "mono" and task == "T1":
                continue
            c = cfg.copy()
            for k, v in kw.items():
                setattr(c.world, k, v)
            line += f" | -{name} {pb(real, rollout(c, iface, champ, ids, seed, dev).score[0])}"
        print(line, flush=True)
