"""Batch 2: triangle surgery, both directions (the owner's loops and transplanting; Claude's and Fable's triangle
leads). Degree-preserving, weight-carrying rewiring of the chemical layer only; the gap layer is the parent's."""
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import spikes as S  # noqa: E402
from tri_sampler import describe, rewire  # noqa: E402

N, FOLLOW, SEED = 1024, 100, 7100  # the same genome seed as batch 1, so parents match batch 1's panels
OUT = S.ROOT / "runs" / "memory-spikes"
res = {}
N2_C3, N2_FF = 2470, 12553
NULL_C3, NULL_FF = 1346, 4900  # null medians (check_structure.py: cycles3 1346; ff about 4.5-6.4k, median ~4.9k)


def run(key, con, info):
    t = time.time()
    g, cfg = S.genomes(con, N, SEED)
    h = S.probe(g, cfg, follow=FOLLOW)
    res[key] = {**S.summary(h), "structure": describe(con.chem), "rewire": info, "seconds": round(time.time() - t, 1)}
    print(key, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res[key].items()}, flush=True)
    json.dump(res, open(OUT / "batch2.json", "w"), indent=1)


for i, parent in enumerate(["SH-2010000", "SH-2010001", "SH-2010002"]):
    pc = S.graph(parent)
    if parent == "SH-2010002":
        run(parent, pc, None)
    for tag, target, metric in (("tri", N2_C3, "cycles3"), ("fft", N2_FF, "ff")):
        chem, info = rewire(pc.chem, target, 100 + i, metric=metric)
        run(f"{parent}/{tag}", S.masks(chem, pc.gap, f"{parent}-{tag}"), info)
for i in range(3):
    for tag, target, metric in (("detri", NULL_C3, "cycles3"), ("deff", NULL_FF, "ff")):
        chem, info = rewire(S.CON.chem, target, 200 + i, metric=metric)
        run(f"N2/{tag}{i}", S.masks(chem, S.CON.gap, f"N2-{tag}{i}"), info)
print("done")
