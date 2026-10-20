"""Batch 1 of the selection round's spikes: one fresh CPU panel per condition, 1024 genomes, follow 100 ticks."""
import json
import sys
import time

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import spikes as S  # noqa: E402

N, FOLLOW, SEED = 1024, 100, 7100
NULLS = ["SH-2010000", "SH-2010001", "SH-route-2020000", "SH-class-2030000", "SH-mirror-2040000", "SH-recip-2050000"]
OUT = S.ROOT / "runs" / "memory-spikes"
OUT.mkdir(parents=True, exist_ok=True)
res = {}
names = list(S.CON.names)
TURN = [names.index(x) for x in ("RMDDL", "RMDDR", "RMDVL", "RMDVR", "SMDDL", "SMDDR", "SMDVL", "SMDVR")]


def run(key, con, cfg_kw=None, probe_kw=None, ref=None):
    t = time.time()
    g, cfg = S.genomes(con, N, SEED, **(cfg_kw or {}))
    h = S.probe(g, cfg, follow=FOLLOW, **(probe_kw or {}))
    res[key] = S.summary(h, ref)
    res[key]["seconds"] = round(time.time() - t, 1)
    print(key, {k: round(v, 3) for k, v in res[key].items() if v is not None}, flush=True)
    json.dump(res, open(OUT / "batch1.json", "w"), indent=1)
    return h


def zero_among(con, idx, tag):
    chem = con.chem.copy()
    for a in idx:
        for b in idx:
            chem[a, b] = 0
    return S.masks(chem, con.gap, tag)


h_n2 = run("N2", S.CON)
nulls = {n: S.graph(n) for n in NULLS}
h_null = {}
for n, c in nulls.items():
    h_null[n] = run(n, c)
# numerical integrator (Fable's new idea 1; ChatGPT M0)
for k in (16, 32):
    run(f"N2/substeps{k}", S.CON, {"substeps": k})
    run(f"SH-2010000/substeps{k}", nulls["SH-2010000"], {"substeps": k})
# reversal (Claude 8)
run("N2-rev", S.graph("N2-rev"))
# the read-out as the store (Fable 11, Astra 15)
run("N2/turn-edges-zeroed", zero_among(S.CON, TURN, "N2-noturn"))
run("SH-2010000/turn-edges-zeroed", zero_among(nulls["SH-2010000"], TURN, "SH-noturn"))
run("N2/erase-turn", S.CON, probe_kw={"erase": TURN}, ref=h_n2["diff"][0])
rng = np.random.default_rng(1)
other = [i for i in range(len(names)) if i not in TURN]
ctrl = list(rng.choice(other, 8, replace=False))
run("N2/erase-random8", S.CON, probe_kw={"erase": ctrl}, ref=h_n2["diff"][0])
run("SH-2010000/erase-turn", nulls["SH-2010000"], probe_kw={"erase": TURN}, ref=h_null["SH-2010000"]["diff"][0])
# the two layers (Astra 3, Fable's development)
sh = nulls["SH-2010000"]
run("N2chem+SHgap", S.masks(S.CON.chem, sh.gap, "x1"))
run("SHchem+N2gap", S.masks(sh.chem, S.CON.gap, "x2"))
run("N2/gaps-off", S.masks(S.CON.chem, np.zeros_like(S.CON.gap), "x3"))
run("SH-2010000/gaps-off", S.masks(sh.chem, np.zeros_like(sh.gap), "x4"))
# preparation and operating point (Claude 6, Astra 16, Fable 15, Astra 12)
for w in (25, 400):
    run(f"N2/warm{w}", S.CON, probe_kw={"warm": w})
    run(f"SH-2010000/warm{w}", sh, probe_kw={"warm": w})
for f in (0.5, 2.0):
    run(f"N2/food{f}", S.CON, probe_kw={"food_scale": f})
    run(f"SH-2010000/food{f}", sh, probe_kw={"food_scale": f})
print("done")
