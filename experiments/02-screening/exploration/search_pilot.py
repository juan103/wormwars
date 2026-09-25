"""Is the limit the evolutionary search? T0 on the discarded shuffle SH101, 40 generations:
E1 = 32 training worlds per strain (4x less selection noise), E2 = population 128.
Measure: held-out score, and the loss when reduced to one nose (stereo use)."""

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


for name, worlds, pop, elites, trunc in (("E1 32 worlds/strain", 32, 32, 3, 8), ("E2 population 128", 8, 128, 12, 32)):
    cfg = grid.task_config(Config(), "T0")
    cfg.world.forward_gain, cfg.world.turn_gain = cal.forward_gain, cal.turn_gain
    cfg.evo.worlds_per_strain, cfg.evo.population = worlds, pop
    cfg.evo.elites, cfg.evo.truncation = elites, trunc
    seed = 31_700
    t = time.perf_counter()
    res = evolve(cfg, iface, spec, 0, seed, device=dev, holdout_every=40, checkpoint_ids=grid.CHECKPOINT_IDS,
                 snapshots=(39,), verbose=False)
    ids = SeedPool(cfg, seed).holdout
    champ = res.snapshots[39]
    real = rollout(cfg, iface, champ, ids, seed, dev).score[0]
    mono = cfg.copy()
    mono.world.food_sensing = "mono"
    lost = pb(real, rollout(mono, iface, champ, ids, seed, dev).score[0])
    print(f"{name}: {time.perf_counter() - t:.0f}s, held-out {real.mean():.3f}, loss when one-nosed {lost}", flush=True)
