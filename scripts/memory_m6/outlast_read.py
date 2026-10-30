"""M6, step 1's readings (docs/memory/M6-OUTLAST-PLAN.md, draft 2): per arm, how many switches held two states during
the 2000-tick removal (B) and how many returned to their original states after restoration (C), each with its own
unresolved bounds and 95% Wilson intervals (sampling uncertainty for the genome-draw population), the merged roots,
B's separations, the counts by panel and subclass, and count wordings that name the gap. Inconclusive if the run is
incomplete, its rows differ from genomes.json, or its consistency check stopped it. Reads runs/memory-m6-outlast/;
writes reading.json. No simulation.

Usage: python scripts/memory_m6/outlast_read.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("MEMORY_M6_OUTLAST_OUT", ROOT / "runs" / "memory-m6-outlast"))
ARMS = ("F0", "Z")
Z95 = 1.959963984540054
STOP_FRACTION = 0.05
WORDS = {"F0": "the food input", "Z": "all sensory input"}
GAP = 2000


def wilson(k, n, z=Z95):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, centre - half), min(1.0, centre + half)]


def bounded(values, yes):
    """A count with its unresolved bounds: k yes, u unresolved, of n; Wilson intervals at k and k + u."""
    n, k, u = len(values), values.count(yes), values.count("unresolved")
    return {"n": n, yes: k, "unresolved": u, "share_bounds": [k / n if n else None, (k + u) / n if n else None],
            "interval_low": wilson(k, n), "interval_high": wilson(k + u, n)}


def unres(u):
    return f" ({u} unresolved)" if u else ""


def arm_reading(rows, arm):
    h = bounded([r[arm]["held"] for r in rows], "held")
    rc = bounded([r[arm]["outcome"] for r in rows], "recovered")
    sep = np.array([[r[arm]["separation_B"][k] for k in ("0", "10", "30", "100", "300", "2000")] for r in rows])
    w = WORDS[arm]
    words = {"held": f"{h['held']} of {h['n']} switches held two states during a {GAP}-tick removal of {w}"
                     f"{unres(h['unresolved'])}",
             "recovered": f"{rc['recovered']} of {rc['n']} switches returned to their original states after a "
                          f"{GAP}-tick removal of {w}{unres(rc['unresolved'])}"}
    return {"held": h, "recovered": rc, "words": words,
            "outcomes": dict(Counter(r[arm]["outcome"] for r in rows)),
            "match": dict(Counter(r[arm]["match"] for r in rows)),
            "B_classes": dict(Counter(r[arm]["B"]["class"] for r in rows)),
            "C_classes": dict(Counter(r[arm]["C"]["class"] for r in rows)),
            "separation_B_median": dict(zip(("0", "10", "30", "100", "300", "2000"),
                                            np.median(sep, 0).tolist() if len(sep) else [None] * 6)),
            "separation_B_max": dict(zip(("0", "10", "30", "100", "300", "2000"),
                                         sep.max(0).tolist() if len(sep) else [None] * 6)),
            "by_panel": {str(s): dict(Counter(r[arm]["outcome"] for r in rows if r["seed"] == s))
                         for s in sorted({r["seed"] for r in rows})},
            "by_subclass": {cl: dict(Counter(r[arm]["outcome"] for r in rows if r["census_class"] == cl))
                            for cl in sorted({r["census_class"] for r in rows})},
            "seen_before_plan": dict(Counter(r[arm]["outcome"] for r in rows if r.get("seen_before_plan")))}


def read(out=None):
    out = out or OUT
    f = out / "run.json"
    if not f.exists():
        return {"inconclusive": "the run is incomplete"}
    run = json.loads(f.read_text(encoding="utf-8"))
    if run.get("stopped"):
        return {"inconclusive": f"the consistency check stopped the run ({run['inconsistent']} genomes)"}
    manifest = json.loads((out / "genomes.json").read_text(encoding="utf-8"))["genomes"]
    want = {(r["seed"], r["genome"]) for r in manifest}
    got = [(r["seed"], r["genome"]) for r in run["rows"]]
    if not run.get("complete") or len(got) != len(set(got)) or set(got) != want:
        return {"inconclusive": "the run's rows differ from genomes.json (incomplete or stale)"}
    failed = sum(r["A"]["class"] != r["census_class"] for r in run["rows"])
    if failed > int(STOP_FRACTION * len(want)):
        return {"inconclusive": f"the consistency check fails ({failed} genomes)"}
    rows = [r for r in run["rows"] if r["A"]["class"] == r["census_class"]]
    diffs = [r["census_root_diff"] for r in rows if r.get("census_root_diff") is not None]
    res = {"genomes": len(run["rows"]), "consistent": len(rows), "inconsistent": failed,
           "excluded": [[r["seed"], r["genome"], r["census_class"], r["A"]["class"]] for r in run["rows"]
                        if r["A"]["class"] != r["census_class"]],
           "census_roots_compared": len(diffs), "census_roots_within_1e-6": sum(d < 1e-6 for d in diffs),
           "census_root_diff_max": max(diffs) if diffs else None}
    for arm in ARMS:
        res[arm] = arm_reading(rows, arm)
    return res


def main():
    res = read()
    (OUT / "reading.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: (v["words"] if isinstance(v, dict) and "words" in v else v) for k, v in res.items()
                      if k in ARMS or k == "inconclusive"}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
