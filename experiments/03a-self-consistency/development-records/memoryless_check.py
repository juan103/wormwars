"""Exploratory (03a design round, D303): can a richer memoryless mono controller reach the evolved navigators' level?
KT: speed AND turn depend on the current level (one threshold), optional collision avoidance. KTM: KT plus one tick
of memory (turn by fall_turn when the level fell), nested: fall_turn = None is KT. Tuned on 256 tuning worlds
(ids 1 481 100 000+), winners re-scored on the 512 check worlds (1 481 000 000+). Mono food sensing."""
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


out = Path(sys.argv[1])
dev = torch.device("cuda")
con = load_connectome(); iface = load_interface(con)
cfg = D.E.task_config(); cfg.world.food_sensing = "mono"
tune_ids = np.arange(1_481_100_000, 1_481_100_256)
check_ids = np.arange(1_481_000_000, 1_481_000_512)
seed = D.REGISTERED["world_seed"]
grid = {"threshold": [0.01, 0.02, 0.05, 0.1, 0.2], "slow": [0.2, 0.5, 0.8, 1.0], "fast": [0.5, 0.8, 1.0],
        "turn_hi": [0.0, 0.2, 0.5, 1.0], "turn_lo": [0.0, 0.1, 0.2, 0.5], "avoid": [0.0, 1.0]}
fall = [0.5, 1.0, -1.0]


def run(combos, keys, ids, fall_turn=None):
    n = len(combos)
    p = {k: torch.tensor([c[i] for c in combos], dtype=torch.float32, device=dev).view(n, 1) for i, k in enumerate(keys)}
    pol = KT(**p, fall_turn=None if fall_turn is None else torch.full((n, 1), float(fall_turn), device=dev))
    brain = ScriptedBrain(iface, 302, pol, cfg.world.forward_gain, cfg.world.turn_gain, n_strains=n, device=dev)
    sc = []
    for ch in np.array_split(ids, max(1, len(ids) // 64)):
        sc.append(np.asarray(rollout_brain(cfg, iface, brain, ch, seed, dev).score))
    return np.concatenate(sc, axis=1)


keys = sorted(grid)
combos = list(itertools.product(*(grid[k] for k in keys)))
res = {"keys": keys, "n_combos": len(combos)}
t0 = time.time()
with acct.recorded(ROOT / "runs" / "03a-mono-check" / "compute", ROOT / "runs" / "03a-mono-check" / "compute.json", default="tuning"):
    base = run(combos, keys, tune_ids).mean(1)
    order = np.argsort(-base, kind="stable")
    res["KT_top"] = [{"params": dict(zip(keys, combos[i])), "tune": float(base[i])} for i in order[:5]]
    print("KT tuned", res["KT_top"][0], round(time.time() - t0), flush=True)
    best = {"KT": (None, combos[order[0]])}
    bm, bmc = -1, None
    for f in fall:
        s = run(combos, keys, tune_ids, fall_turn=f).mean(1)
        i = int(np.argmax(s))
        res.setdefault("KTM_by_fall", {})[str(f)] = {"params": dict(zip(keys, combos[i])), "tune": float(s[i])}
        if s[i] > bm:
            bm, bmc = s[i], (f, combos[i])
        print("KTM fall", f, float(s[i]), round(time.time() - t0), flush=True)
    best["KTM"] = bmc
    for name, (f, c) in best.items():
        s = run([c], keys, check_ids, fall_turn=f)[0]
        res[f"{name}_check"] = {"params": dict(zip(keys, c)), "fall_turn": f, "mean": float(s.mean()),
                                "se": float(s.std(ddof=1) / np.sqrt(len(s))), "counts": s.astype(int).tolist()}
        print(name, "check", s.mean(), flush=True)
res["seconds"] = time.time() - t0
out.write_text(json.dumps(res))
