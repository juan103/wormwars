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
    if isinstance(a, dict):
        for k in a:
            if k in ("seconds", "provenance"):
                continue
            cmp(a[k], b[k], f"{path}/{k}", diffs)
    elif isinstance(a, list) and a and isinstance(a[0], (dict, list)) and not isinstance(a[0], (int, float)):
        for i, (u, v) in enumerate(zip(a, b)):
            cmp(u, v, f"{path}[{i}]", diffs)
    elif isinstance(a, list):
        x, y = np.asarray(a, float), np.asarray(b, float)
        d = float(np.nanmax(np.abs(x - y))) if x.size else 0.0
        if d > 0 or x.shape != y.shape:
            diffs.append((path, d))
    elif a != b and not (isinstance(a, float) and np.isnan(a) and np.isnan(b)):
        diffs.append((path, a, b))


for name in names:
    saved = json.loads((measures / f"{name}.json").read_text(encoding="utf-8"))
    fresh = e.measure_graph(con, name, "cuda", bank=bank)
    diffs = []
    cmp(saved, fresh, name, diffs)
    out[name] = {"identical": not diffs, "n_differences": len(diffs), "first": [str(x) for x in diffs[:5]]}
    print(name, out[name], flush=True)
(MAIN / "runs" / "remeasure-03r.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
