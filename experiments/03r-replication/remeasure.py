"""Re-measure N2 and the last-measured ensemble graph of 03r with the binding commit's code (the
worktree at 7c146fc), and compare with the saved measurements (Fable, 03r results review)."""
import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np

MAIN = Path(r"D:\Claude\random\wormWars")
BIND = Path(r"D:\Claude\random\wormWars-03r-binding")
sys.path.insert(0, str(BIND))  # the binding commit's wormwars package
spec = importlib.util.spec_from_file_location("exp03_bind", BIND / "scripts" / "exp03.py")
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
e.use_instance("03r")
import wormwars  # noqa: E402
assert Path(wormwars.__file__).resolve().is_relative_to(BIND), wormwars.__file__
from wormwars.connectome import load_connectome  # noqa: E402

measures = MAIN / "runs" / "exp03r" / "measures"
ens = sorted((p for p in measures.glob("*.json") if not p.stem.startswith("N2")), key=os.path.getmtime)
names = ["N2", ens[-1].stem]
bank = json.loads(e.PILOT.read_text(encoding="utf-8"))["bank"]
con = load_connectome()
out = {}


def cmp(a, b, path, diffs):
    """Strict comparison (Astra, Fable): the same structure and keys on both sides, the same lengths,
    exactly equal values, and NaN in the same positions."""
    if isinstance(a, dict) or isinstance(b, dict):
        if not (isinstance(a, dict) and isinstance(b, dict)):
            diffs.append((path, "type")); return
        ka, kb = set(a) - {"seconds", "provenance"}, set(b) - {"seconds", "provenance"}
        if ka != kb:
            diffs.append((path, "keys", sorted(ka ^ kb)))
        for k in ka & kb:
            cmp(a[k], b[k], f"{path}/{k}", diffs)
    elif isinstance(a, list) or isinstance(b, list):
        if not (isinstance(a, list) and isinstance(b, list)) or len(a) != len(b):
            diffs.append((path, "length")); return
        if a and isinstance(a[0], (dict, list)):
            for i, (u, v) in enumerate(zip(a, b)):
                cmp(u, v, f"{path}[{i}]", diffs)
        else:
            x, y = np.asarray(a, float), np.asarray(b, float)
            if x.shape != y.shape or not np.array_equal(x, y, equal_nan=True):
                diffs.append((path, "values"))
    elif not (a == b or (isinstance(a, float) and isinstance(b, float) and np.isnan(a) and np.isnan(b))):
        diffs.append((path, a, b))


for name in names:
    saved = json.loads((measures / f"{name}.json").read_text(encoding="utf-8"))
    fresh = e.measure_graph(con, name, "cuda", bank=bank)
    diffs = []
    cmp(saved, fresh, name, diffs)
    out[name] = {"identical": not diffs, "n_differences": len(diffs), "first": [str(x) for x in diffs[:5]]}
    print(name, out[name], flush=True)
import datetime  # noqa: E402
import subprocess  # noqa: E402
import torch  # noqa: E402
doc = {"what": "N2 and the last ensemble graph measured, re-measured with the binding commit's code and compared "
               "with the saved 03r measurements",
       "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BIND, text=True).strip(),
       "code_dirty": bool(subprocess.check_output(["git", "status", "--porcelain", "--", "wormwars", "scripts"],
                                                  cwd=BIND, text=True).strip()),
       "device": torch.cuda.get_device_name(0), "run_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
       "compared": "every key, list length and value of each saved measurement except 'seconds' and 'provenance'; "
                   "exact equality with NaN in the same positions",
       "results": out}
(MAIN / "experiments" / "03r-replication" / "remeasure.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
