"""M6, option 0's readings (docs/memory/M6-0-PLAN.md): the consistency check against 02b, the audit, the classes with
unresolved bounds, the two comparisons by cluster bootstrap over the 30 graph-and-run blocks, the beside-02b table and
the fixed wordings. Reads runs/memory-m6-0/ and experiments/02b-champion-analysis/history.json; writes reading.json.

Usage: python scripts/memory_m6/m6_0_read.py
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("MEMORY_M6_OUT", ROOT / "runs" / "memory-m6-0"))
HISTORY = ROOT / "experiments" / "02b-champion-analysis" / "history.json"
BANKS = ("own", "03mc")
SWITCH = ("separate states", "separate states, read-out silent")
FADING, UNRESOLVED = "fading", "unresolved"
MIN_SWITCHES = 5
RESAMPLES, BOOT_SEED = 10_000, 20261131
REL_TOL, ABS_TOL = 0.02, 1e-3
SEEN = {f"T1-M0-N2-run{r:02d}/{t}" for r in range(8) for t in ("g00", "g39")}  # the spike's 16, on 03mc's bank


def load(name, out=None):
    return json.loads(((out or OUT) / name).read_text(encoding="utf-8"))


def close(x, y):
    return abs(x - y) <= max(REL_TOL * abs(y), ABS_TOL)


# ------------------------------------------------------------------------------------------------------------ records
def merged(first, second):
    """Per genome (in the first pass's order): the class after the second pass where it ran, else the first pass's;
    and the audit failures (a first-pass-fading audited genome that is a switch after the second)."""
    rows = [dict(x) for x in first["rows"]]
    for i, rec in second["records"].items():
        rows[int(i)]["first_class"] = rows[int(i)]["class"]
        rows[int(i)]["class"] = rec["class"]
    fails = [i for i in second["audit"] if first["rows"][i]["class"] == FADING and rows[i]["class"] in SWITCH]
    return rows, fails


def annotate(rows, genomes):
    meta = {(g["key"], g["label"]): g for g in genomes}
    for x in rows:
        g = meta[(x["key"], x["label"])]
        x.update(block=g["block"], mapping=g["mapping"], family=g["family"], graph=g["graph"])
    return rows


def consistency(rows, banks, history):
    """On the own bank, for the T1-M0 N2 and SH runs 02b measured: a against |raw_turn final|, d(5) against |raw_turn
    after| (g00 and g39), and the bank's food level against typical_food."""
    by = {(x["key"], x["label"]): x for x in rows}
    checks, failed = [], []
    for key, h in sorted(history.items()):
        if not key.startswith("T1-"):
            continue
        b = banks["own"][key]
        food = (b["food_left"] + b["food_right"]) / 2
        items = [("typical_food", food, h["typical_food"])]
        for tag in ("g00", "g39"):
            x = by[(key, tag)]
            items += [(f"{tag} a", x["a"], abs(h[tag]["raw_turn"]["final"])),
                      (f"{tag} d5", x["d5"], abs(h[tag]["raw_turn"]["after"]))]
        for what, got, want in items:
            ok = close(got, want)
            checks.append({"key": key, "what": what, "got": got, "want": want, "ok": ok})
            if not ok:
                failed.append(f"{key} {what}: {got:.6g} against 02b's {want:.6g}")
    return {"checks": len(checks), "runs": len({c["key"] for c in checks}), "failed": failed, "passes": not failed,
            "max_rel": max(abs(c["got"] - c["want"]) / max(abs(c["want"]), 1e-12) for c in checks) if checks else None}


def counts(rows, keys):
    """Classes by the given row fields, with the switch bounds S/n to (S + U)/n."""
    out = defaultdict(lambda: defaultdict(int))
    for x in rows:
        g = " / ".join(str(x[k]) for k in keys)
        out[g][x["class"]] += 1
        out[g]["n"] += 1
    res = {}
    for g, cnt in sorted(out.items()):
        s = sum(cnt[k] for k in SWITCH)
        res[g] = {**dict(cnt), "switch": s, "bounds": [s / cnt["n"], (s + cnt[UNRESOLVED]) / cnt["n"]]}
    return res


# -------------------------------------------------------------------------------------------------------- comparisons
def boot(block_values, seed=BOOT_SEED, resamples=RESAMPLES):
    """The mean over blocks and its 95% percentile interval, resampling whole blocks."""
    v = np.asarray(list(block_values), float)
    if len(v) == 0:
        return {"blocks": 0, "mean": None, "interval": None}
    idx = np.random.default_rng(seed).integers(0, len(v), size=(resamples, len(v)))
    m = v[idx].mean(1)
    return {"blocks": int(len(v)), "mean": float(v.mean()), "interval": [float(np.quantile(m, 0.025)),
                                                                         float(np.quantile(m, 0.975))]}


def by_block(per_run):
    """{block: [run values]} -> the blocks' means."""
    return [float(np.mean(v)) for _, v in sorted(per_run.items()) if v]


def switch_value(x, unresolved_as):
    return 1.0 if x["class"] in SWITCH else (unresolved_as if x["class"] == UNRESOLVED else 0.0)


def runs_of(rows):
    out = defaultdict(dict)
    for x in rows:
        out[x["key"]][x["label"]] = x
    return out


def compare_switches(rows, against, unresolved_as):
    """Per run, g39's switch indicator minus the comparator's (drift: the share of its four replicates; g00: its
    own); unresolved counted as unresolved_as (0, the lower bound; 1, the upper)."""
    per = defaultdict(list)
    for key, r in sorted(runs_of(rows).items()):
        g39 = switch_value(r["g39"], unresolved_as)
        if against == "drift":
            ref = np.mean([switch_value(v, unresolved_as) for k, v in r.items() if k.startswith("drift")])
        else:
            ref = switch_value(r["g00"], unresolved_as)
        per[r["g39"]["block"]].append(g39 - ref)
    return boot(by_block(per))


def exceeds(t, u):
    """1 if tau t exceeds u, a half if tied (both censored included), 0 otherwise; None (censored) ranks highest."""
    t, u = (np.inf if t is None else t), (np.inf if u is None else u)
    return 1.0 if t > u else 0.5 if t == u else 0.0


def compare_persistence(rows, against):
    """Per run, the share of the comparator's eligible genomes whose tau_stay g39's exceeds, minus a half; a run counts
    if g39 and at least one comparator pass the start floor."""
    per, skipped = defaultdict(list), 0
    for key, r in sorted(runs_of(rows).items()):
        g = r["g39"]
        refs = [v for k, v in r.items() if (k.startswith("drift") if against == "drift" else k == "g00")
                and v["eligible"]]
        if not g["eligible"] or not refs:
            skipped += 1
            continue
        per[g["block"]].append(np.mean([exceeds(g["tau_stay"], v["tau_stay"]) for v in refs]) - 0.5)
    return {**boot(by_block(per)), "runs_skipped": skipped}


def restricted_medians(rows, cap=2000):
    out = {}
    for tag in ("g00", "g39", "g79", "drift"):
        for fam in sorted({x["family"] for x in rows}):
            v = [min(cap, cap if x["tau_stay"] is None else x["tau_stay"]) for x in rows
                 if x["tag"] == tag and x["family"] == fam and x["eligible"]]
            c = sum(1 for x in rows if x["tag"] == tag and x["family"] == fam and x["eligible"]
                    and x["tau_stay"] is None)
            out[f"{tag} / {fam}"] = {"eligible": len(v), "median": float(np.median(v)) if v else None,
                                     "censored": c,
                                     "below_floor": sum(1 for x in rows if x["tag"] == tag and x["family"] == fam
                                                        and not x["eligible"])}
    return out


def fading_profile(rows):
    """After the data (results review, Astra and Fable): per tag, over the genomes above the start floor, the medians
    of a, d(t)/a and the absolute d(t) = a * d(t)/a, and how many return above 0.1 a after first crossing it."""
    out = {}
    for tag in ("g00", "g39", "g79", "drift"):
        el = [x for x in rows if x["tag"] == tag and x["eligible"]]
        med = lambda v: float(np.median(v)) if v else None  # noqa: E731
        out[tag] = {"eligible": len(el), "a": med([x["a"] for x in el]),
                    **{f"r{t}": med([x[f"r{t}"] for x in el]) for t in (5, 30, 100)},
                    **{f"d{t}": med([x["a"] * x[f"r{t}"] for x in el]) for t in (30, 100)},
                    "returns": sum(1 for x in el if x["returns"])}
    return out


def fading_only(rows):
    """After the data (Fable): the persistence comparison with every genome not fading set below the floor, so a
    censored switch or unresolved drift replicate no longer ranks above every fading champion."""
    return {against: compare_persistence([{**x, "eligible": x["eligible"] and x["class"] == FADING} for x in rows],
                                         against) for against in ("drift", "g00")}


def bank_reading(rows):
    """The enrichment criterion at both unresolved bounds, and the persistence comparison, for one bank."""
    g39 = [x for x in rows if x["tag"] == "g39"]
    s = sum(x["class"] in SWITCH for x in g39)
    u = sum(x["class"] == UNRESOLVED for x in g39)
    lo, hi = compare_switches(rows, "drift", 0.0), compare_switches(rows, "drift", 1.0)
    holds = [s >= MIN_SWITCHES and lo["interval"][0] > 0, s + u >= MIN_SWITCHES and hi["interval"][0] > 0]
    pers = compare_persistence(rows, "drift")
    if pers["interval"] is None:
        p = "not computable"
    elif pers["interval"][0] > 0:
        p = "lengthened"
    elif pers["interval"][1] < 0:
        p = "shortened"
    else:
        p = "not distinguishable from drift"
    return {"g39_switches": s, "g39_unresolved": u, "switch_vs_drift": {"lower": lo, "upper": hi},
            "switch_vs_g00": {"lower": compare_switches(rows, "g00", 0.0), "upper": compare_switches(rows, "g00", 1.0)},
            "enrichment_at_bounds": holds, "persistence_vs_drift": pers,
            "persistence_vs_g00": compare_persistence(rows, "g00"), "persistence": p,
            "classes_g39": counts(g39, ["class"])}


def words(primary, secondary, incomplete, consistency_ok, audit_failures):
    """The plan's fixed wordings, in their order of precedence."""
    why = []
    if incomplete:
        why.append("the run is incomplete")
    if not consistency_ok:
        why.append("the consistency check against 02b failed")
    if audit_failures:
        why.append("an audited first-pass-fading genome was a switch after the second pass")
    a, b = primary["enrichment_at_bounds"]
    if a != b:
        why.append("the unresolved bounds straddle the enrichment criterion")
    out = {}
    if why:
        out["switches"] = "inconclusive: " + "; ".join(why)
    elif a:
        out["switches"] = ("enrichment: g39 champions are switches more often than the mutation-only control "
                           f"({primary['g39_switches']} switch champions); options 5 and 2 are next to consider")
    else:
        out["switches"] = ("We did not detect enrichment of probe-defined switches in g39 champions relative to the "
                           f"mutation-only control; {primary['g39_switches']} were found")
    if not why:
        out["persistence"] = {"lengthened": "selection lengthened the history effect's persistence beyond drift",
                              "shortened": "selection shortened the history effect's persistence against drift",
                              "not distinguishable from drift": "the history effect's persistence is not "
                                                                "distinguishable from drift's",
                              "not computable": "persistence not computable"}[primary["persistence"]]
    s_a = secondary["enrichment_at_bounds"][0] if secondary else False
    if secondary and (s_a and not a or secondary["persistence"] != primary["persistence"]):
        out["input"] = ("a dependence on input: the secondary bank (03mc's) reads differently "
                        f"(enrichment {s_a}, persistence {secondary['persistence']})")
    return out


def beside_02b(rows, history):
    by = {(x["key"], x["label"]): x for x in rows}
    out = []
    for key, h in sorted(history.items()):
        if not key.startswith("T1-"):
            continue
        row = {"key": key}
        for tag in ("g00", "g39"):
            x = by[(key, tag)]
            row[tag] = {"class": x["class"], "a": x["a"], "d5": x["d5"], "tau_stay": x.get("tau_stay"),
                        "02b_final": abs(h[tag]["raw_turn"]["final"]), "02b_after": abs(h[tag]["raw_turn"]["after"])}
        row["drift_new"] = [{"a": by[(key, f"drift{k}")]["a"], "d5": by[(key, f"drift{k}")]["d5"]} for k in range(4)]
        row["drift_02b"] = [{"final": abs(d["raw_turn"]["final"]), "after": abs(d["raw_turn"]["after"])}
                            for d in h["drift"]]
        out.append(row)
    return out


def read(out=None):
    out = out or OUT
    genomes = load("genomes.json", out)
    banks = load("banks.json", out)
    history = json.loads(HISTORY.read_text(encoding="utf-8"))
    incomplete = not all((out / f"{f}-{b}.json").exists() for f in ("first", "second") for b in BANKS)
    if not (out / "first-own.json").exists() or not (out / "second-own.json").exists():
        return {"incomplete": True, "words": {"switches": "inconclusive: the run is incomplete"}}
    per_bank, audits = {}, {}
    for b in BANKS:
        if not (out / f"second-{b}.json").exists():
            continue
        rows, fails = merged(load(f"first-{b}.json", out), load(f"second-{b}.json", out))
        per_bank[b] = annotate(rows, genomes["genomes"])
        audits[b] = fails
    own = per_bank["own"]
    for x in per_bank.get("03mc", []):
        x["seen"] = f"{x['key']}/{x['label']}" in SEEN
    cons = consistency(own, banks, history)
    primary = bank_reading(own)
    secondary = bank_reading(per_bank["03mc"]) if "03mc" in per_bank else None
    res = {"incomplete": incomplete, "consistency": cons, "audit_failures": audits,
           "genomes": {k: genomes[k] for k in ("counts", "blocks", "distinct_g00")},
           "primary": primary, "secondary": secondary,
           "classes": {b: {"by tag, family": counts(r, ["tag", "family"]),
                           "by tag, mapping, family": counts(r, ["tag", "mapping", "family"])}
                       for b, r in per_bank.items()},
           "persistence_medians": {b: restricted_medians(r) for b, r in per_bank.items()},
           "g79": [{k: x[k] for k in ("key", "class", "tau_stay", "a")} | {
               "g39_class": next(y["class"] for y in own if y["key"] == x["key"] and y["tag"] == "g39"),
               "g39_tau_stay": next(y.get("tau_stay") for y in own if y["key"] == x["key"] and y["tag"] == "g39")}
               for x in own if x["tag"] == "g79"],
           "beside_02b": beside_02b(own, history),
           "after_the_data": {b: {"fading_profile": fading_profile(r), "persistence_fading_only": fading_only(r)}
                              for b, r in per_bank.items()},
           "seen_before_plan": sorted(SEEN)}
    res["words"] = words(primary, secondary, incomplete, cons["passes"], any(audits.values()))
    return res


def main():
    res = read()
    (OUT / "reading.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res["words"], indent=1))


if __name__ == "__main__":
    sys.exit(main())
