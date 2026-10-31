import json
from collections import defaultdict
import numpy as np

from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
R = str(ROOT / "runs" / "memory-m6-step2") + "/"
s = json.load(open(R + "scores.json"))["scores"]
g = json.load(open(R + "genomes.json"))
rows = g if isinstance(g, list) else g.get("genomes", g)
block = {x["key"]: x["block"] for x in rows}
print("keys", len(s), "blocks", len(set(block.values())))


def bm(f, keys):
    acc = defaultdict(list)
    for k in keys:
        v = f(k)
        if v is not None:
            acc[block[k]].append(v)
    return np.mean([np.mean(v) for v in acc.values()]), len(acc)


t1 = [k for k in s if k.startswith("T1")]
t0 = [k for k in s if k.startswith("T0")]
for lab, arms in (("g39", ["0.25", "0.5", "2", "4", "interior 0.25"]), ("g00", ["0.25", "4"]), ("drift0", ["0.25", "4"])):
    for a in arms:
        print("T1", lab, a, bm(lambda k: s[k][lab][a]["mean"] / s[k][lab]["1"]["mean"] - 1, t1))
    print("T1", lab, "intact", bm(lambda k: s[k][lab]["1"]["mean"], t1))
for a in ["0.25", "0.5", "2", "4"]:
    print("T0 g39", a, bm(lambda k: s[k]["g39"][a]["mean"] / s[k]["g39"]["1"]["mean"] - 1, t0))
# champion counts with drop at 0.25 and at 4
for a in ["0.25", "0.5", "2", "4"]:
    d = [s[k]["g39"][a]["mean"] < s[k]["g39"]["1"]["mean"] for k in t1]
    print("T1 champions lower at", a, sum(d), "of", len(d))
print("1 alone == 1:", all(s[k]["g39"]["1 alone"]["mean"] == s[k]["g39"]["1"]["mean"] for k in t1))
from scipy.stats import spearmanr
first = {(x["key"], x["label"]): x for x in json.load(open(ROOT / "runs" / "memory-m6-0" / "first-own.json"))["rows"]}
a = [first[(k, "g39")]["a"] for k in t1]
r = [s[k]["g39"]["0.25"]["mean"] / s[k]["g39"]["1"]["mean"] - 1 for k in t1]
base = [s[k]["g39"]["1"]["mean"] for k in t1]
print("spearman change@0.25 vs intact", spearmanr(r, base))
print("spearman a vs intact", spearmanr(a, base))
print("spearman change@0.25 vs a", spearmanr(r, a))
# added after review: drift genomes with an individual relative change above 10%; champions whose best arm is not k = 1
for a in ["0.25", "4"]:
    n = sum(abs(s[k]["drift0"][a]["mean"] / s[k]["drift0"]["1"]["mean"] - 1) > 0.10 for k in t1)
    print("drift0 |relative change| > 10% at", a, n, "of", len(t1))
arms5 = ["0.25", "0.5", "1", "2", "4"]
for task, keys in (("T1", t1), ("T0", t0)):
    best = [max(arms5, key=lambda a: s[k]["g39"][a]["mean"]) for k in keys]
    print(task, "champions by best of five k:", {a: best.count(a) for a in arms5})
