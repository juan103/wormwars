"""Exploratory (03a design round 2, D304): a slow-memory mono family, KTS: KT plus a turn by fall_turn whenever the
level is below its exponential average with time constant T ticks (T = 1 compares with the previous tick, as KTM).
A 162-point grid per T, tuned on 256 tuning worlds (ids 1 481 100 000+); each T's winner re-scored on the 512 check
worlds (1 481 000 000+) under the real scent and the jitter probe at r = 1 and 2. Mono food sensing. Run from the
repository root: py -3.13 <this file> runs/03a-mono-check/slow-memory-check.json"""
import importlib.util, itertools, json, sys, time
from pathlib import Path
import numpy as np, torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
spec_ = importlib.util.spec_from_file_location("e2d", ROOT / "scripts" / "e2d.py")
D = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(D)
from wormwars.connectome import load_connectome
from wormwars.interface import load_interface
from wormwars.exp02.scripted import ScriptedBrain
from wormwars.evo.rollout import rollout_brain
from wormwars import accounting as acct


class KT:
    needs_collision = True

    def __init__(self, threshold, slow, fast, turn_hi, turn_lo, avoid, fall_turn=None):
        self.t, self.slow, self.fast, self.th, self.tl, self.avoid, self.ft = threshold, slow, fast, turn_hi, turn_lo, avoid, fall_turn

    def init(self, s, b):
        return None

    def __call__(self, left, right, state, collision=None):
        level = (left + right) / 2
        one = torch.ones_like(level)
        hi = level > self.t
        fwd = torch.where(hi, self.slow * one, self.fast * one)
        turn = torch.where(hi, self.th * one, self.tl * one)
        if self.ft is not None and state is not None:
            turn = torch.where(level < state, self.ft * one, turn)
        near = torch.maximum(collision["front"], torch.maximum(collision["front_left"], collision["front_right"])) > 0.5023
        turn = torch.where(near & (self.avoid > 0), one, turn)
        return fwd, turn, level.clone()




class KTS(KT):
    """KT plus a slow memory: turn by fall_turn when the level is below its exponential average with time constant T
    (in ticks). T is per strain; with T = 1 the average is the previous tick's level, so KTS(T=1) is KTM."""

    def __init__(self, T, **kw):
        super().__init__(**kw)
        self.T = T

    def __call__(self, left, right, state, collision=None):
        level = (left + right) / 2
        one = torch.ones_like(level)
        hi = level > self.t
        fwd = torch.where(hi, self.slow * one, self.fast * one)
        turn = torch.where(hi, self.th * one, self.tl * one)
        avg = level.clone() if state is None else state
        turn = torch.where(level < avg, self.ft * one, turn)
        near = torch.maximum(collision["front"], torch.maximum(collision["front_left"], collision["front_right"])) > 0.5023
        turn = torch.where(near & (self.avoid > 0), one, turn)
        return fwd, turn, avg + (level - avg) / self.T


out = Path(sys.argv[1])
dev = torch.device("cuda")
con = load_connectome(); iface = load_interface(con)
cfg0 = D.E.task_config(); cfg0.world.food_sensing = "mono"
tune_ids = np.arange(1_481_100_000, 1_481_100_256)
check_ids = np.arange(1_481_000_000, 1_481_000_512)
seed = D.REGISTERED["world_seed"]
grid = {"threshold": [0.05, 0.1, 0.2], "slow": [0.5, 0.8, 1.0], "fast": [1.0], "turn_hi": [0.2, 0.5],
        "turn_lo": [0.0, 0.1, 0.2], "avoid": [0.0], "fall_turn": [0.5, 1.0, -1.0]}
Ts = [1.0, 2.0, 5.0, 10.0, 20.0, 50.0]
keys = sorted(grid)
combos = list(itertools.product(*(grid[k] for k in keys)))


def run(combos, T, ids, cfg, probe="real"):
    n = len(combos)
    p = {k: torch.tensor([c[i] for c in combos], dtype=torch.float32, device=dev).view(n, 1) for i, k in enumerate(keys)}
    pol = KTS(torch.full((n, 1), T, device=dev), **p)
    c = cfg.copy(); c.world.food_probe = probe
    brain = ScriptedBrain(iface, 302, pol, c.world.forward_gain, c.world.turn_gain, n_strains=n, device=dev)
    return np.concatenate([np.asarray(rollout_brain(c, iface, brain, ch, seed, dev).score)
                           for ch in np.array_split(ids, max(1, len(ids) // 64))], axis=1)


res = {"keys": keys, "grid": grid, "T": Ts, "by_T": {}}
with acct.recorded(ROOT / "runs" / "03a-mono-check" / "compute", ROOT / "runs" / "03a-mono-check" / "compute.json", default="tuning"):
    for T in Ts:
        s = run(combos, T, tune_ids, cfg0).mean(1)
        i = int(np.argmax(s))
        row = {"params": dict(zip(keys, combos[i])), "tune": float(s[i]), "check": {}}
        for r in (0.0, 1.0, 2.0):
            cfg = cfg0.copy(); cfg.world.food_probe_radius = r
            x = run([combos[i]], T, check_ids, cfg, "real" if r == 0 else "jitter")[0]
            row["check"][str(r)] = {"mean": float(x.mean()), "se": float(x.std(ddof=1) / np.sqrt(len(x))),
                                    "counts": x.astype(int).tolist()}
        res["by_T"][str(T)] = row
        print(T, row["tune"], {k: round(v["mean"], 3) for k, v in row["check"].items()}, flush=True)
out.write_text(json.dumps(res))
