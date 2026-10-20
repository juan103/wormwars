"""Spike: is N2's slow retention typical of its genomes, or carried by a minority? (Fable 1, Astra 8)."""
import glob
import json
import os
import re

import numpy as np

ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[2])
rep = json.load(open(f"{ROOT}/experiments/03mc-p4-confirm/report.json"))
ticks = rep["descriptive"]["curves"]["ticks"]
t30 = ticks.index(30)
FLOOR = 1e-3


def stats(path):
    d = np.abs(np.load(path, allow_pickle=False)["diff"]).astype(float)  # [ticks, genomes]
    ok = d[0] >= FLOOR
    ratio_of_means = d[t30].mean() / d[0].mean()
    per = d[t30, ok] / d[0, ok]
    # drop the genomes with the largest late contribution until N2-sized trims
    late = d[t30]
    order = np.argsort(-late)
    trims = {}
    for k in (0, 20, 43, 100, 200):
        keep = np.ones(d.shape[1], bool)
        keep[order[:k]] = False
        trims[k] = d[t30, keep].mean() / d[0, keep].mean()
    # contribution of the top 5% of genomes to the tick-30 mean
    top = late[order[: int(0.05 * len(late))]].sum() / late.sum()
    return {"ratio_of_means": ratio_of_means, "median_per_genome": float(np.median(per)),
            "q25": float(np.quantile(per, 0.25)), "q75": float(np.quantile(per, 0.75)),
            "mean_per_genome": float(per.mean()), "trims": trims, "top5_share_t30": top,
            "grow_frac": float((per > 1).mean()), "half_frac": float((per > 0.5).mean()),
            "corr_amp_retention": float(np.corrcoef(np.log(d[0, ok]), per)[0, 1])}


n2 = stats(f"{ROOT}/runs/p4mc/arrays/N2__long.npz")
print("N2", {k: (round(v, 3) if isinstance(v, float) else {a: round(b, 3) for a, b in v.items()}) for k, v in n2.items()})
for e in ("SH", "SH-route", "SH-class", "SH-mirror", "SH-recip"):
    rows = [stats(p) for p in sorted([q for q in glob.glob(f"{ROOT}/runs/p4mc/arrays/graph__{e}-*__long.npz") if re.fullmatch(rf"graph__{e}-\d+__long\.npz", os.path.basename(q))])]
    med = lambda k: float(np.median([r[k] for r in rows]))  # noqa: E731
    above = lambda k: sum(r[k] >= n2[k] for r in rows)  # noqa: E731
    print(e, len(rows), {k: (round(med(k), 3), above(k)) for k in
                         ("ratio_of_means", "median_per_genome", "q25", "q75", "half_frac", "grow_frac", "top5_share_t30", "corr_amp_retention")},
          "trim43", round(float(np.median([r["trims"][43] for r in rows])), 3))
