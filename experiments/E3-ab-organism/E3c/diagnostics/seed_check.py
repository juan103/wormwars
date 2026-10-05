"""Diagnostic (not a stage): the seed played the pilot's way (MR.play on the started organism) and E3b-1's way
(play_batch on the seed genome), on E3b-1's test block and on the pilot block."""
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from wormwars.brain import Brain  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e3 import assembly as AS  # noqa: E402
from wormwars.e3 import maze_organisms as MO  # noqa: E402
from wormwars.e3 import maze_runs as MR  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402

s = importlib.util.spec_from_file_location("e3c", ROOT / "scripts" / "e3c.py")
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
dev = "cuda"
cfg = m.cfg_for("shared", 8)
cx = AS.context(load_connectome(), A.load_l1(), cfg.brain)
seed = cx["seed"]
H = int(cfg.world.max_ticks)
out = {}
for block, ids in (("e3b1_test", np.arange(6000, 6256)), ("pilot", np.arange(7600, 7728))):
    t = time.time()
    ev = MR.play(cfg, seed.iface, lambda: MO.brain(seed, dev), ids, m.seed(), dev, access="shared")
    ev1 = {k: (v[None] if isinstance(v, np.ndarray) and v.shape[:1] == (len(ids),) else v) for k, v in ev.items()}
    a = float(m.outcomes(ev1, H)["visits"].mean())
    g = seed.genome if dev == "cpu" else m.EV.moved(seed.genome, dev)
    ev = MR.play_batch(cfg, seed.iface, Brain(g), np.arange(1), ids, m.seed(), dev, access="shared")
    b = float(m.outcomes(ev, H)["visits"].mean())
    out[block] = {"play_started_organism": a, "play_batch_genome": b, "seconds": time.time() - t}
    print(block, out[block], flush=True)
(Path(__file__).parent / "seed-check.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
