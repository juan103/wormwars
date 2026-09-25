"""Why does the pilot T1 champion beat kinesis without being hurt by the 1-cell jitter?
(a) a better memoryless strategy (graded kinesis) or (b) history integrated over many ticks.
Scripted controllers and the discarded SH101 pilot champions only."""

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import shuffled
from wormwars.evo import SeedPool, load_genome, rollout
from wormwars.exp02 import grid, scripted
from wormwars.interface import load_interface
from wormwars import calibration as calib

dev = "cuda"
con = load_connectome()
iface = load_interface(con)
cal = json.load(open(ROOT / "experiments/02-screening/calibration.json", encoding="utf-8"))["N2"]
diag = json.load(open(ROOT / "experiments/02-screening/diagnostics.json", encoding="utf-8"))


def pb(a, b, n=20000):
    d = np.asarray(a) - np.asarray(b)
    rng = np.random.default_rng(0)
    m = d[rng.integers(0, len(d), (n, len(d)))].mean(1)
    return f"{d.mean():+.3f} [{np.quantile(m, .025):+.3f}, {np.quantile(m, .975):+.3f}]"


# (a) graded kinesis, tuned wide, against the memory controller on the gate worlds
c1 = grid.task_config(Config(), "T1")
c1.world.forward_gain, c1.world.turn_gain = cal["forward_gain"], cal["turn_gain"]
G = {"slow": [0.0, 0.1, 0.25, 0.5, 0.75], "fast": [0.75, 1.0], "scale": [0.3, 0.6, 1.0, 1.5, 2.0, 3.0, 5.0],
     "turn": [0.0, 0.1, 0.2, 0.3, 0.4]}
gp, gs = scripted.tune_batched(lambda **p: scripted.GradedKinesis(**p), G, c1, iface, grid.TUNING_IDS, grid.TUNING_SEED, dev)


def val(pol):
    b = scripted.ScriptedBrain(iface, 302, pol, c1.world.forward_gain, c1.world.turn_gain, device=dev)
    return scripted.rollout_brain(c1, iface, b, grid.GATE_IDS, grid.GATE_SEED, dev).score[0]


K = val(scripted.LevelKinesis(**diag["T1"]["tuned"]["K"]["params"]))
M = val(scripted.MemoryKinesis(**diag["T1"]["tuned"]["M"]["params"]))
GK = val(scripted.GradedKinesis(**gp))
st = val(scripted.Straight())
print(f"graded kinesis tuned: {gp}")
print(f"gate worlds: straight {st.mean():.3f}  K {K.mean():.3f}  graded {GK.mean():.3f}  M {M.mean():.3f}")
print(f"   memory over GRADED kinesis: {pb(M, GK)};  share of best over straight: "
      f"{(M.mean() - GK.mean()) / (M.mean() - st.mean()):.2f}")

# (b) the pilot champions under harsher and different ablations
graph = shuffled(con, 101, "SH101")
spec = BrainSpec.from_connectome(graph, device=dev)
gains = calib.calibrate_in_world(graph, grid.task_config(Config(), "T0"), iface, grid.TARGET_DRIVE,
                                 n_strains=grid.CALIBRATION_STRAINS, device=dev)
out = ROOT / "runs/exp02-screening/pilot"
for task in ("T1", "T0"):
    cfg = grid.task_config(Config(), task)
    cfg.world.forward_gain, cfg.world.turn_gain = gains.forward_gain, gains.turn_gain
    champ, _ = load_genome(out / f"{task}-M0-SH101-run00-g39.npz", spec, None, device=dev)
    ids, seed = SeedPool(cfg, 31_000).holdout, 31_000
    real = rollout(cfg, iface, champ, ids, seed, dev).score[0]
    print(f"\n{task} pilot champion, held-out mean {real.mean():.3f}; real minus ablated:")
    variants = [("food constant", {"food_probe": "constant"}), ("food mirrored", {"food_probe": "mirrored"}),
                ("jitter 1", {"food_probe": "jitter", "food_probe_radius": 1.0}),
                ("jitter 2", {"food_probe": "jitter", "food_probe_radius": 2.0}),
                ("jitter 3", {"food_probe": "jitter", "food_probe_radius": 3.0}),
                ("collision off", {"sense_scale_collision": 0.0})]
    if task == "T0":
        variants.append(("mono (one nose)", {"food_sensing": "mono"}))
    for name, kw in variants:
        c = cfg.copy()
        for k, v in kw.items():
            setattr(c.world, k, v)
        print(f"   {name:16} {pb(real, rollout(c, iface, champ, ids, seed, dev).score[0])}")
