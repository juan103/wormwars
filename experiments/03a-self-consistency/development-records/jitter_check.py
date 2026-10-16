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



from wormwars.brain import BrainSpec, Genome
out = Path(sys.argv[1])
dev = torch.device("cuda")
con = load_connectome(); iface = load_interface(con)
spec, cfg0 = BrainSpec.from_connectome(con), D.E.task_config()
champs = D.e04a_champions(spec, cfg0)
labs = list(champs); G = Genome.cat([champs[l][0] for l in labs])
ml = json.loads((ROOT / "runs/03a-mono-check/memoryless-check.json").read_text())
ids = np.arange(1_481_000_000, 1_481_000_512)
seed = D.REGISTERED["world_seed"]
class Cap:
    def check(self): pass
res = {"worlds": [int(ids[0]), int(ids[-1])], "champions": {}, "scripted": {}}
with acct.recorded(ROOT / "runs" / "03a-mono-check" / "compute", ROOT / "runs" / "03a-mono-check" / "compute.json", default="final"):
    for r in (0.0, 0.5, 1.0, 2.0):
        cfg = cfg0.copy(); cfg.world.food_sensing = "mono"; cfg.world.food_probe_radius = r
        probe = "real" if r == 0 else "jitter"
        sc = D.neural(cfg, iface, G, ids, probe, dev, Cap())
        for i, l in enumerate(labs):
            res["champions"].setdefault(l, {})[str(r)] = sc[i].astype(int).tolist()
        for name in ("KT", "KTM"):
            p = ml[f"{name}_check"]["params"]; f = ml[f"{name}_check"]["fall_turn"]
            pol = KT(**{k: torch.tensor([[float(v)]], device=dev) for k, v in p.items()},
                     fall_turn=None if f is None else torch.tensor([[float(f)]], device=dev))
            c2 = cfg.copy(); c2.world.food_probe = probe
            b = ScriptedBrain(iface, 302, pol, cfg.world.forward_gain, cfg.world.turn_gain, n_strains=1, device=dev)
            res["scripted"].setdefault(name, {})[str(r)] = np.asarray(rollout_brain(c2, iface, b, ids, seed, dev).score[0]).astype(int).tolist()
        print("radius", r, flush=True)
out.write_text(json.dumps(res))
