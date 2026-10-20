"""M1, a check written after the data (docs/memory/M1-RESULTS.md): why B3's balance condition reads 0. The condition
looks only at used strata holding at least 10% of N2's pooled tick-30 numerator (summarise.py, `heavy`); this prints,
for each N2 panel and each basis (a and ||da(0)||), the largest such fraction among the used strata. Reads
runs/memory-m1/summary.json and the panels' local .npz arrays; writes runs/memory-m1/check_b3_balance.json."""
import json

import numpy as np

from common import OUT, START_FLOOR, dump

ARMS = ["intact", "scale0.25", "scale0.5", "scale2.0"]


def main():
    s = json.load(open(OUT / "summary.json"))
    res = {}
    for panel in ("N2__7600", "N2__7700"):
        z = np.load(OUT / "panels" / f"{panel}.npz", allow_pickle=False)
        elig = np.all([z[f"a_{x}"] >= START_FLOOR for x in ARMS], 0)
        for var, key in (("a", "D1_B3_a"), ("da0", "D1_B3_da")):
            edges, used = np.array(s[key]["edges"]), s[key]["used_strata"]
            num = np.zeros(len(edges) + 1)
            for x in ARMS:
                np.add.at(num, np.digitize(z[f"{var}_{x}"][elig], edges), z[f"d30_{x}"][elig])
            frac = num / num.sum()
            res[f"{panel}__{var}"] = {"numerator_frac_per_stratum": [float(f) for f in frac],
                                      "largest_used": float(max(frac[i] for i in used)),
                                      "heavy_used_strata": [int(i) for i in used if frac[i] >= 0.10]}
    dump(res, "check_b3_balance.json")
    print({k: (round(v["largest_used"], 3), v["heavy_used_strata"]) for k, v in res.items()})


if __name__ == "__main__":
    main()
