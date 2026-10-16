"""Exploratory (03a design round, D303): 04a's 16 champions and E1's frozen M-avg and K, under stereo and mono
food sensing, and under mono with the reading held for h ticks. World ids 1 481 000 000 + 0..511, outside every
registered range. Writes JSON to the path given."""
import importlib.util, json, sys, time
from pathlib import Path
import numpy as np, torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
spec_ = importlib.util.spec_from_file_location("e2d", ROOT / "scripts" / "e2d.py")
D = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(D)
from wormwars.brain import BrainSpec, Genome
from wormwars.connectome import load_connectome
from wormwars.interface import load_interface
from wormwars import accounting as acct

class Cap:
    def check(self): pass

out = Path(sys.argv[1]); n = int(sys.argv[2]) if len(sys.argv) > 2 else 512
dev = torch.device("cuda")
con = load_connectome(); iface = load_interface(con)
spec, cfg = BrainSpec.from_connectome(con), D.E.task_config()
champs = D.e04a_champions(spec, cfg)
refs = D.references()
wids = np.arange(1_481_000_000, 1_481_000_000 + n)
conds = [("stereo", "real", 1), ("mono", "real", 1), ("mono", "hold", 2), ("mono", "hold", 5), ("mono", "hold", 10), ("mono", "hold", 20), ("mono", "constant", 1)]
res = {"worlds": [int(wids[0]), int(wids[-1])], "conditions": [list(c) for c in conds], "champions": {}, "scripted": {}}
t0 = time.time()
with acct.recorded(ROOT / "runs" / "03a-mono-check" / "compute", ROOT / "runs" / "03a-mono-check" / "compute.json", default="final"):
    for sensing, probe, h in conds:
        c = cfg.copy(); c.world.food_sensing = sensing; c.world.food_probe_hold = h
        key = f"{sensing}/{probe}/{h}"
        labs = list(champs)
        r = D.neural(c, iface, Genome.cat([champs[l][0] for l in labs]), wids, probe, dev, Cap())
        assert r.shape == (len(labs), len(wids)), r.shape
        for i, lab in enumerate(labs):
            res["champions"].setdefault(lab, {})[key] = r[i].astype(int).tolist()
        for name in ("M-avg", "S-const"):
            maker, params = refs[name]
            r = D.scripted(c, iface, maker, params, wids, probe, dev, Cap())
            res["scripted"].setdefault(name, {})[key] = r.astype(int).tolist()
        K = json.loads(D.E.E1_FREEZE.read_text(encoding="utf-8"))["tuned"]["K"]["params"]
        r = D.scripted(c, iface, "K", K, wids, probe, dev, Cap())
        res["scripted"].setdefault("K", {})[key] = r.astype(int).tolist()
        print(key, round(time.time() - t0), "s", flush=True)
res["seconds"] = time.time() - t0
out.write_text(json.dumps(res))
