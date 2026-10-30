"""M6, step 2's readings (docs/memory/M6-STEP2-PLAN.md, draft 2): the champions' mean within-champion relative score
change at k = 0.25 (primary), each control's comparison, the other k, the interior-only arm, T0 against T1 (matched by
mapping), the association with the history effect and with tau, absolute changes and baselines, the probe validation
with its individual failures, the consistency check against 02b, a sensitivity reading without the switch champion,
and fixed wordings, every interpretive sentence gated on the checks. Averaging: worlds within a genome, paired changes
within a run, runs within a graph-and-run block, blocks weighted equally; a cluster bootstrap over blocks. Reads
runs/memory-m6-step2/ and M6-0's and 02b's committed records; writes reading.json.

Usage: python scripts/memory_m6/step2_read.py
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("MEMORY_M6_STEP2_OUT", ROOT / "runs" / "memory-m6-step2"))
M6_0 = ROOT / "runs" / "memory-m6-0"
CRIT = ROOT / "experiments" / "02b-champion-analysis" / "criticality.json"
RESAMPLES, SEED = 10_000, 20261201
FLOOR = 0.05          # a genome's intact mean score below this is not used in a ratio (reported)
REL_TOL = 0.02        # consistency against 02b's intact scores (GPU) for the 24 T1-M0 champions
A_FLOOR = 1e-3        # the probe validation's start floor (M6-0's)
VALID_MEDIAN, VALID_SHARE = 0.5, 0.9
N_WORLDS = 32
SWITCH_CHAMPION = "T1-MS-N2-run07"  # M6-0's one switch champion (own bank)
INTERIOR, ALONE = "interior 0.25", "1 alone"
T1_ARMS = {"g39": ["0.25", "0.5", "1", "2", "4", INTERIOR, ALONE], "g00": ["0.25", "1", "4"],
           "drift0": ["0.25", "1", "4"]}
T0_ARMS = {"g39": ["0.25", "0.5", "1", "2", "4"]}
PROBE_ARMS = ["0.25", "0.5", "1", "2", "4", INTERIOR]
PROBE_FIELDS = ("a_written_at_1", "continued_integral", "a_full", "full_integral")
CAVEAT = ("This tests the champions' dependence on neural time scale; it does not establish that the probe-defined "
          "fading history effect mediates any benefit, because faster neurons also respond faster.")
NAMES = {"g00": "the generation-0 champions", "drift0": "the drift genomes"}


def load(name, out=None):
    return json.loads(((out or OUT) / name).read_text(encoding="utf-8"))


def boot(values, seed=SEED, resamples=RESAMPLES):
    """Mean over blocks with a 95% percentile interval, resampling blocks."""
    v = np.asarray([x for x in values if x is not None], float)
    if len(v) == 0:
        return {"blocks": 0, "mean": None, "interval": None}
    rng = np.random.default_rng(seed)
    means = v[rng.integers(0, len(v), (resamples, len(v)))].mean(1)
    return {"blocks": int(len(v)), "mean": float(v.mean()),
            "interval": [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]}


def by_block(per_run, block):
    acc = defaultdict(list)
    for key, v in per_run.items():
        if v is not None:
            acc[block[key]].append(v)
    return {b: float(np.mean(v)) for b, v in sorted(acc.items())}


def bb(per_run, block):
    return boot(list(by_block(per_run, block).values()))


def base_arm(arm):
    """k = 1 in the same batch composition (Astra): three strains for 0.25 and 4, one strain otherwise."""
    return "1" if arm in ("0.25", "4") else ALONE


def ratio(scores, key, label, arm):
    s = scores[key][label]
    base = s[base_arm(arm) if label == "g39" and key.startswith("T1") else "1"]["mean"]
    return None if base < FLOOR else s[arm]["mean"] / base - 1


def absolute(scores, key, label, arm):
    s = scores[key][label]
    return s[arm]["mean"] - s[base_arm(arm) if label == "g39" and key.startswith("T1") else "1"]["mean"]


def direction(iv):
    if iv is None:
        return "not computable"
    return "reduced" if iv[1] < 0 else "increased" if iv[0] > 0 else "none detected"


def primary_words(res):
    m, iv = res["mean"], res["interval"]
    if iv is None:
        return "not computable"
    tail = f"(mean within-champion change {m:+.1%}, 95% interval {iv[0]:+.1%} to {iv[1]:+.1%})"
    d = direction(iv)
    if d == "reduced":
        return f"Making every neuron four times faster reduced the champions' T1 foraging score {tail}."
    if d == "increased":
        return f"Making every neuron four times faster increased the champions' T1 foraging score {tail}."
    return ("No reliable mean reduction of the champions' T1 foraging score was detected when every neuron was made "
            f"four times faster {tail}.")


def control_words(primary_dir, cmp, name):
    """The plan's three cases when the primary is a reduction; otherwise the comparison's direction only."""
    d = direction(cmp["interval"])
    if primary_dir == "reduced":
        if d == "reduced":
            return f"The reduction exceeded that of {name}."
        if d == "increased":
            return f"The reduction was smaller than that of {name}."
        return f"A champion reduction with no detected excess over {name}."
    return f"The champions' change compared with {name}: {d} (champion minus control)."


def spearman(x, y):
    """Spearman with average ranks for ties (scipy); None where undefined (constant input or fewer than 3)."""
    if len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return None
    r = spearmanr(x, y).statistic
    return None if not np.isfinite(r) else float(r)


def association(per_champ, block, seed=SEED, resamples=RESAMPLES):
    """Spearman over champions of (x, y) pairs, with an interval from resampling blocks."""
    keys = [k for k, v in per_champ.items() if v is not None]
    rho = spearman([per_champ[k][0] for k in keys], [per_champ[k][1] for k in keys])
    if rho is None:
        return {"n": len(keys), "rho": None, "interval": None, "undefined_draws": None}
    blocks = sorted({block[k] for k in keys})
    members = {b: [k for k in keys if block[k] == b] for b in blocks}
    rng = np.random.default_rng(seed)
    draws, undefined = [], 0
    for _ in range(resamples):
        ks = [k for b in rng.choice(blocks, len(blocks)) for k in members[b]]
        r = spearman([per_champ[k][0] for k in ks], [per_champ[k][1] for k in ks])
        if r is None:
            undefined += 1
        else:
            draws.append(r)
    return {"n": len(keys), "rho": rho, "interval": [float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))],
            "undefined_draws": undefined}


def completeness(genomes, scores, probe):
    """Every required genome, label, arm and field present, with N_WORLDS finite world scores whose mean is the
    recorded mean (Astra). Returns the list of problems (empty when complete)."""
    bad = []
    for x in genomes:
        arms = (T1_ARMS if x["task"] == "T1" else T0_ARMS).get(x["label"], [])
        s = scores.get(x["key"], {}).get(x["label"])
        if s is None:
            bad.append(f"{x['key']} {x['label']}: no scores")
            continue
        for a in arms:
            v = s.get(a)
            if v is None:
                bad.append(f"{x['key']} {x['label']} {a}: missing")
                continue
            w = v.get("worlds", [])
            if len(w) != N_WORLDS or not all(math.isfinite(t) for t in w) or abs(np.mean(w) - v["mean"]) > 1e-6:
                bad.append(f"{x['key']} {x['label']} {a}: world scores incomplete or inconsistent")
        if x["task"] == "T1" and x["label"] == "g39":
            p = probe.get(x["key"], {}).get("g39")
            for a in PROBE_ARMS:
                if p is None or a not in p or any(f not in p[a] for f in PROBE_FIELDS):
                    bad.append(f"{x['key']} probe {a}: missing")
    return bad


def validation(probe):
    """The continuation's integrated read-out difference at each arm against k = 1, over champions above the floor;
    individual failures listed, zero denominators reported (Astra, Fable)."""
    out, eligible, zero = {}, [], []
    for key, labs in probe.items():
        p = labs["g39"]
        if p["1"]["a_written_at_1"] < A_FLOOR:
            continue
        if p["1"]["continued_integral"] <= 0:
            zero.append(key)
            continue
        eligible.append(key)
    for arm in ("0.25", "0.5", "2", "4", INTERIOR):
        rs = {k: probe[k]["g39"][arm]["continued_integral"] / probe[k]["g39"]["1"]["continued_integral"]
              for k in eligible}
        fr = {k: probe[k]["g39"][arm]["full_integral"] / probe[k]["g39"]["1"]["full_integral"]
              for k in eligible if probe[k]["g39"]["1"]["full_integral"] > 0}
        out[arm] = {"n": len(rs), "median": float(np.median(list(rs.values()))) if rs else None,
                    "share_below_1": float(np.mean([r < 1 for r in rs.values()])) if rs else None,
                    "full_probe_median": float(np.median(list(fr.values()))) if fr else None,
                    "not_below_1" if arm != "4" else "not_above_1":
                        sorted(k for k, r in rs.items() if (r >= 1 if arm != "4" else r <= 1))}
    v = out["0.25"]
    passes = (v["median"] is not None and v["median"] < VALID_MEDIAN and v["share_below_1"] >= VALID_SHARE
              and out["4"]["median"] is not None and out["4"]["median"] > 1)
    sw = probe.get(SWITCH_CHAMPION, {}).get("g39")
    return {"by_arm": out, "passes": bool(passes), "zero_denominators": zero,
            "switch_champion": {a: sw[a] for a in sw} if sw else None}


def consistency(scores):
    crit = json.loads(CRIT.read_text(encoding="utf-8"))
    rows = []
    for key, v in crit.items():
        got = scores[key]["g39"]["1"]["mean"]
        rows.append({"key": key, "got": got, "02b": v["intact"],
                     "ok": abs(got - v["intact"]) <= REL_TOL * abs(v["intact"])})
    return {"checks": len(rows), "failed": [r for r in rows if not r["ok"]], "passes": all(r["ok"] for r in rows),
            "max_rel": max(abs(r["got"] - r["02b"]) / abs(r["02b"]) for r in rows)}


def read(out=None):
    out = out or OUT
    for f in ("genomes.json", "scores.json", "probe.json"):
        if not (out / f).exists():
            return {"inconclusive": f"the run is incomplete ({f} missing)"}
    genomes = load("genomes.json", out)["genomes"]
    scores = load("scores.json", out)["scores"]
    probe = load("probe.json", out)["probe"]
    missing = completeness(genomes, scores, probe)
    if missing:
        return {"inconclusive": "the run is incomplete (required measurements missing)", "missing": missing[:50],
                "n_missing": len(missing)}
    keys = {x["key"] for x in genomes}
    block = {x["key"]: x["block"] for x in genomes}
    mapping = {x["key"]: x["mapping"] for x in genomes}
    t1 = sorted(k for k in keys if k.startswith("T1-"))
    t0 = sorted(k for k in keys if k.startswith("T0-"))
    cons, val = consistency(scores), validation(probe)
    floored = sorted({(k, lb) for k in keys for lb in scores[k] if scores[k][lb]["1"]["mean"] < FLOOR})
    res = {"consistency": cons, "validation": val, "below_floor": [list(x) for x in floored]}

    prim = bb({k: ratio(scores, k, "g39", "0.25") for k in t1}, block)
    res["primary"] = {**prim, "direction": direction(prim["interval"]),
                      "absolute": bb({k: absolute(scores, k, "g39", "0.25") for k in t1}, block),
                      "intact": bb({k: scores[k]["g39"]["1"]["mean"] for k in t1}, block),
                      "without_switch_champion": bb({k: ratio(scores, k, "g39", "0.25") for k in t1
                                                     if k != SWITCH_CHAMPION}, block)}
    res["k"] = {a: {"relative": bb({k: ratio(scores, k, "g39", a) for k in t1}, block),
                    "absolute": bb({k: absolute(scores, k, "g39", a) for k in t1}, block)} for a in ("0.5", "2", "4")}
    res["composition_check"] = bb({k: scores[k]["g39"][ALONE]["mean"] - scores[k]["g39"]["1"]["mean"] for k in t1},
                                  block)
    res["controls"] = {}
    for lb in ("g00", "drift0"):
        cmp = {}
        for a in ("0.25", "4"):
            per = {}
            for k in t1:
                base = scores[k]["g39"]["1"]["mean"]
                per[k] = None if base < FLOOR else (absolute(scores, k, "g39", a) - absolute(scores, k, lb, a)) / base
            cmp[a] = bb(per, block)
        res["controls"][lb] = {"difference_over_champion_intact": cmp,
                               "own_relative_0.25": bb({k: ratio(scores, k, lb, "0.25") for k in t1}, block),
                               "own_absolute_0.25": bb({k: absolute(scores, k, lb, "0.25") for k in t1}, block),
                               "intact": bb({k: scores[k][lb]["1"]["mean"] for k in t1}, block)}
    res["interior"] = {"relative": bb({k: ratio(scores, k, "g39", INTERIOR) for k in t1}, block),
                       "minus_full": bb({k: (None if ratio(scores, k, "g39", INTERIOR) is None
                                             or ratio(scores, k, "g39", "0.25") is None
                                             else ratio(scores, k, "g39", INTERIOR) - ratio(scores, k, "g39", "0.25"))
                                         for k in t1}, block)}
    # T1 minus T0, matched by graph, run and mapping (M0, R1, R2), then averaged within blocks (Astra)
    t0_by = {(block[k], mapping[k]): k for k in t0}
    paired = {}
    for k in t1:
        k0 = t0_by.get((block[k], mapping[k]))  # T0 has M0, R1 and R2 only, so MS is never paired
        if k0 is not None:
            r1, r0 = ratio(scores, k, "g39", "0.25"), ratio(scores, k0, "g39", "0.25")
            paired[k] = None if r1 is None or r0 is None else r1 - r0
    res["T0"] = {"relative_0.25": bb({k: ratio(scores, k, "g39", "0.25") for k in t0}, block),
                 "k": {a: bb({k: ratio(scores, k, "g39", a) for k in t0}, block) for a in ("0.5", "2", "4")},
                 "intact": bb({k: scores[k]["g39"]["1"]["mean"] for k in t0}, block),
                 "T1_minus_T0_0.25_matched": bb(paired, block),
                 "matched_runs": sum(v is not None for v in paired.values())}
    first = {(x["key"], x["label"]): x for x in load("first-own.json", M6_0)["rows"]}
    tau = {(x["key"], x["label"]): x["tau"]["median"] for x in genomes}
    res["association"] = {
        "with_a": association({k: (None if ratio(scores, k, "g39", "0.25") is None else
                                   (first[(k, "g39")]["a"], ratio(scores, k, "g39", "0.25"))) for k in t1}, block),
        "with_median_tau": association({k: (None if ratio(scores, k, "g39", "0.25") is None else
                                            (tau[(k, "g39")], ratio(scores, k, "g39", "0.25"))) for k in t1}, block)}
    res["tau_profiles"] = {f"{task} {lb}": {s: float(np.median([x["tau"][s] for x in genomes
                                                                 if x["task"] == task and x["label"] == lb]))
                                            for s in ("median", "at_min", "at_max")}
                           for task, lb in (("T1", "g39"), ("T1", "g00"), ("T1", "drift0"), ("T0", "g39"))}
    why = [w for w, bad in (("the consistency check against 02b failed", not cons["passes"]),
                            ("the probe validation failed", not val["passes"])) if bad]
    if why:  # every interpretive sentence is gated (Astra, Fable); the numbers above stay
        res["words"] = {"reading": f"inconclusive: {'; '.join(why)}"}
    else:
        pd = res["primary"]["direction"]
        res["words"] = {"primary": primary_words(prim), "caveat": CAVEAT,
                        **{lb: control_words(pd, res["controls"][lb]["difference_over_champion_intact"]["0.25"],
                                             NAMES[lb]) for lb in ("g00", "drift0")}}
    return res


def main():
    res = read()
    (OUT / "reading.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps(res.get("words", res), indent=1))


if __name__ == "__main__":
    sys.exit(main())
