"""03mc's own census of settled genomes with separation left (committed measurements.json): where N2's 26 falls among
the 640 null graphs, per ensemble, and whether a graph's settled count tracks its tick-30 share (Fable, in the first
review of the roadmap; the roadmap's settling finding must be read against it)."""
import collections
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
m = json.load(open(ROOT / "experiments" / "03mc-p4-confirm" / "measurements.json"))
units = m["units"] if isinstance(m, dict) and "units" in m else m
items = units.items() if isinstance(units, dict) else [(u.get("id"), u) for u in units]
by = collections.defaultdict(list)
n2 = None
for k, u in items:
    if not isinstance(u, dict) or "settled_and_remaining" not in u:
        continue
    if k == "N2/long":
        n2 = u
    else:
        by[k.split("/")[1].rsplit("-", 1)[0]].append(u)
out = {"N2": {"settled_and_remaining": n2["settled_and_remaining"], "eligible": n2["eligible"],
              "share30": n2["share"]["30"]}}
for e, rows in by.items():
    s = np.array([u["settled_and_remaining"] for u in rows])
    sh = np.array([u["share"]["30"] if u["share"]["30"] is not None else np.nan for u in rows])
    ok = ~np.isnan(sh)
    out[e] = {"graphs": len(s), "median": float(np.median(s)), "graphs_at_or_above_N2": int((s >= n2["settled_and_remaining"]).sum()),
              "graphs_with_any": int((s > 0).sum()), "max": int(s.max()),
              "spearman_settled_vs_share30": float(spearmanr(s[ok], sh[ok]).correlation)}
print(json.dumps(out, indent=1))
json.dump(out, open(ROOT / "runs" / "memory-spikes" / "settled_census.json", "w"), indent=1)
