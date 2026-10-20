"""M2 census: the split of N2's mean lead into class contributions, its unresolved band, the bootstrap and the readings,
and the census's descriptions (docs/memory/M2-CENSUS-PLAN.md). Reads the panel records written by census.py and
writes runs/memory-m2-census/split.json. Exploratory; CPU, seconds.
Usage: python scripts/memory_m2/split.py"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("MEMORY_M2_CENSUS_OUT", ROOT / "runs" / "memory-m2-census"))
ENSEMBLES = ("SH", "SH-route", "SH-class", "SH-mirror", "SH-recip")
B, MAX_BAD = 2000, 100
GROUPS = {"S": ("separate states", "separate states, read-out silent"), "F": ("fading",),
          "O": ("persistent oscillation",), "U": ("unresolved",)}
MOST, LITTLE = 0.5, 0.25


def ensemble_of(name):
    return name.rsplit("-", 1)[0]


def interval(x):
    x = np.asarray(x, float)
    good = x[np.isfinite(x)]
    return [float(np.percentile(good, 5)), float(np.percentile(good, 95))] if len(good) else [None, None]


# ---------------------------------------------------------------------------------------------------- the panel vectors
def vectors(rec):
    """Per panel, length-N vectors over all genomes: a, |dy(30)|, |dy(300)| on the eligible genomes (zero elsewhere), and
    one 0/1 vector per class group."""
    al = rec["all"]
    el = np.array(al["eligible"], bool)
    v = {"a": np.where(el, np.array(al["a"], float), 0.0)}
    for t in (30, 300):
        v[f"d{t}"] = np.where(el, np.array(al[f"d{t}"], float), 0.0)
    cls = np.array([""] * len(el), dtype=object)
    for r in rec["genomes"]:
        cls[r["genome"]] = r["class"]
    for k, names in GROUPS.items():
        v[k] = np.isin(cls, names).astype(float)
    return v


def contributions(v, W, t):
    """For multiplicity weights W [b, N] (rows of genome counts): the eligible share s and the class contributions X,
    each [b]. A resample with no eligible denominator gives NaN."""
    den = W @ v["a"]
    with np.errstate(invalid="ignore", divide="ignore"):
        out = {"s": np.where(den > 0, (W @ v[f"d{t}"]) / den, np.nan)}
        for k in GROUPS:
            out[k] = np.where(den > 0, (W @ (v[f"d{t}"] * v[k])) / den, np.nan)
    return out


def split_from(n2, refs):
    """n2: {quantity: [b]}; refs: list of {quantity: [b]} (the resampled reference panels, already picked). Returns the
    mean contrasts Lambda and Lambda_X, the parts phi_X and the band's ends for S and F, each [b]."""
    mean = {k: np.mean([r[k] for r in refs], 0) for k in n2}
    lam = n2["s"] - mean["s"]
    out = {"Lambda": lam}
    with np.errstate(invalid="ignore", divide="ignore"):
        for k in GROUPS:
            out[f"Lambda_{k}"] = n2[k] - mean[k]
            out[f"phi_{k}"] = np.where(lam > 0, out[f"Lambda_{k}"] / lam, np.nan)
        for k in ("S", "F"):
            out[f"phi_{k}_lo"] = np.where(lam > 0, (n2[k] - (mean[k] + mean["U"])) / lam, np.nan)
            out[f"phi_{k}_hi"] = np.where(lam > 0, (n2[k] + n2["U"] - mean[k]) / lam, np.nan)
    return out


def reading(lo_int, hi_int, bad, lam_point):
    """One panel's reading from the 90% intervals of the band's two ends, lower(phi_S-) = lo_int[0] and
    upper(phi_S+) = hi_int[1]. The roadmap's branch is decided apart, after the panels are combined (branch())."""
    if lam_point is None or not lam_point > 0 or bad > MAX_BAD or None in (lo_int[0], hi_int[1]):
        return "inconclusive (the lead's denominator)"
    if lo_int[0] > MOST:
        return "most"
    if hi_int[1] < LITTLE:
        return "little"
    if lo_int[0] > LITTLE and hi_int[1] < MOST:
        return "a part, between a quarter and a half"
    return "inconclusive"


def branch(combined, f_lo_ints):
    """The roadmap's branch: only on a combined "little", and only if lower(phi_F-) > 0.5 on both panels (Fable,
    Astra, round 3: the branch is not part of the reading)."""
    if combined != "little":
        return None
    if all(x[0] is not None and x[0] > MOST for x in f_lo_ints):
        return "little: the graded part becomes the main target"
    return "little; the remainder not attributed to fading"


def multiplicities(idx, n):
    W = np.zeros((idx.shape[0], n))
    for b in range(idx.shape[0]):
        W[b] = np.bincount(idx[b], minlength=n)
    return W


def bootstrap(V, ref_names, n2_names, rng, t, b=B):
    """M1's bootstrap: one set of genome indices for every seed-7600 panel, an independent one for N2's seed-7700 panel,
    the reference graphs resampled within ensembles. Returns {N2 panel: split arrays [b]} and the picks."""
    n = len(V[ref_names[0]]["a"])
    W1 = multiplicities(rng.integers(0, n, (b, n)), n)
    W2 = multiplicities(rng.integers(0, n, (b, n)), n)
    by_e = {e: [g for g in ref_names if ensemble_of(g.split("__")[0]) == e] for e in ENSEMBLES}
    picks = {e: rng.integers(0, len(by_e[e]), (b, len(by_e[e]))) for e in ENSEMBLES if by_e[e]}
    C = {g: contributions(V[g], W1, t) for g in ref_names}
    refs = []
    for e, pk in picks.items():
        for col in range(pk.shape[1]):  # each resampled slot: per resample, the picked graph's contributions
            refs.append({k: np.choose(pk[:, col], [C[g][k] for g in by_e[e]]) for k in C[ref_names[0]]})
    out = {}
    for name in n2_names:
        W = W1 if name.endswith("__7600") else W2
        out[name] = split_from(contributions(V[name], W, t), refs)
    return out


# ------------------------------------------------------------------------------------------------------- descriptions
def wr(v, k, t):
    """A class's share of the eligible denominator and its own retention (None where the class is empty)."""
    sa = (v["a"] * v[k]).sum()
    return sa / v["a"].sum(), ((v[f"d{t}"] * v[k]).sum() / sa if sa > 0 else None)


def composition_retention(V, n2, refs, t):
    """X = w_X rho_X. Lambda_X, the mean over the pairs (N2, g) of X_N2 - X_g, in three parts, each a mean over all
    pairs: where both graphs have the class, composition (w_N2 - w_g)(rho_N2 + rho_g)/2 and retention
    (rho_N2 - rho_g)(w_N2 + w_g)/2, which add up exactly; where one lacks it (rho is 0/0 there), the pair's whole
    difference as presence (the plan, draft 3; Fable, Astra)."""
    out = {}
    for k in ("S", "F"):
        wn, rn = wr(V[n2], k, t)
        comp, ret, pres = [], [], []
        for g in refs:
            wg, rg = wr(V[g], k, t)
            if rn is not None and rg is not None:
                comp.append((wn - wg) * (rn + rg) / 2)
                ret.append((rn - rg) * (wn + wg) / 2)
                pres.append(0.0)
            else:
                comp.append(0.0)
                ret.append(0.0)
                pres.append((wn * rn if rn is not None else 0.0) - (wg * rg if rg is not None else 0.0))
        out[k] = {"w_N2": wn, "rho_N2": rn, "w_ref_mean": float(np.mean([wr(V[g], k, t)[0] for g in refs])),
                  "composition": float(np.mean(comp)), "retention": float(np.mean(ret)), "presence": float(np.mean(pres)),
                  "presence_pairs": int(sum(1 for g in refs if rn is None or wr(V[g], k, t)[1] is None))}
    return out


def combine(r1, r2):
    """The plan's combination of the two N2 panels' readings, in its order."""
    den = "inconclusive (the lead's denominator)"
    if den in (r1, r2):
        return den
    if r1 == r2:
        return r1
    if "inconclusive" in (r1, r2):
        return f"{r1 if r2 == 'inconclusive' else r2} on one panel, inconclusive on the other"
    return "not replicated"


def wmedian(x, w):
    x, w = np.asarray(x, float), np.asarray(w, float)
    if len(x) == 0 or w.sum() <= 0:
        return None
    o = np.argsort(x)
    cw = np.cumsum(w[o])
    return float(x[o][np.searchsorted(cw, cw[-1] / 2)])


def describe_panel(rec):
    g = rec["genomes"]
    counts = {k: sum(r["class"] in names for r in g) for k, names in GROUPS.items()}
    sep = [r for r in g if r["class"].startswith("separate states")]
    fad = [r for r in g if r["class"] == "fading"]
    where = {k: (float(np.average([r["where"][k] for r in sep], weights=[max(r["d30"], 1e-300) for r in sep]))
                 if sep else None) for k in ("core", "hubs", "rest", "readout")}
    co = np.array([r["cohort"] for r in g], bool)
    ss = np.array([r["class"].startswith("separate states") for r in g], bool)
    d30 = np.array([r["d30"] for r in g], float)
    d300 = np.array([r["d300"] for r in g], float)
    cell = lambda m: {"genomes": int(m.sum()), "numerator30": float(d30[m].sum()), "numerator300": float(d300[m].sum())}  # noqa: E731
    cheap = {"both_yes": 0, "cheap_only": 0, "full_only": 0, "both_no": 0}
    for r in g:
        for h in range(2):
            ch, fu = r["cheap"][h], r["reach"][h] == "reached"
            cheap[{(True, True): "both_yes", (True, False): "cheap_only", (False, True): "full_only",
                   (False, False): "both_no"}[(ch, fu)]] += 1
    radius = [dict(r["radius"], genome=r["genome"], class_now=r["class"]) for r in g if "radius" in r]
    unres = {}
    for r in g:
        if r["class"] == "unresolved":
            unres[r["reason"]] = unres.get(r["reason"], 0) + 1
    el_num = float(np.sum(d30))
    return {"counts": counts, "eligible": rec["eligible"],
            "unresolved_frac": counts["U"] / max(rec["eligible"], 1),
            "unresolved_numerator30_frac": float(d30[[r["class"] == "unresolved" for r in g]].sum() / el_num) if el_num > 0 else None,
            "C4_flagged": bool(counts["U"] / max(rec["eligible"], 1) > 0.05 or
                               (el_num > 0 and d30[[r["class"] == "unresolved" for r in g]].sum() / el_num > 0.10)),
            "unresolved_reasons": unres,
            "oscillation_periods": [[o["period_substeps"] for o in r["oscillation"] if o] for r in g
                                    if r["class"] == "persistent oscillation"],
            "where_separation": where,
            "fading_slow_rate_wmedian": wmedian([r["slow_rate"] for r in fad], [r["d30"] for r in fad]),
            "cohort_by_separate": {"cohort_and_separate": cell(co & ss), "cohort_only": cell(co & ~ss),
                                   "separate_only": cell(~co & ss), "neither": cell(~co & ~ss)},
            "cohort_not_separate_classes": {k: sum(1 for r in g if r["cohort"] and r["class"] == k)
                                            for k in sorted({r["class"] for r in g if r["cohort"]}) if not k.startswith("separate")},
            "cheap_rule": cheap, "radius": radius,
            "eligible_share": rec["eligible_share"], "valid": rec["valid"]}


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return None
    return float(spearmanr(x, y)[0])


# ---------------------------------------------------------------------------------------------------------------- main
def main():
    sys.path.insert(0, str(Path(__file__).parent))
    import census
    order = census.panels()
    R = {name: json.load(open(OUT / f"{name}.json")) for name, *_ in order if (OUT / f"{name}.json").exists()}
    missing = [name for name, *_ in order if name not in R]
    roles = {name: role for name, _, _, role in order}
    ref = [n for n in R if roles[n] == "reference" and R[n]["valid"]]
    n2 = [n for n in ("N2__7600", "N2__7700") if n in R]
    checks = {}
    for ck in ("c2", "c3", "c5"):
        f = OUT / f"{ck}.json"
        checks[ck] = (census.c3_valid(json.load(open(f))) if ck == "c3" else bool(json.load(open(f)).get("passes")))             if f.exists() else None
    out = {"missing_panels": missing, "invalid_panels": sorted(n for n in R if not R[n]["valid"]),
           "reference_graphs": len(ref), "checks": checks}
    ref_missing = [n for n, *_ in order if roles[n] == "reference" and n not in R]
    withheld = None
    if not all(checks.values()):  # the plan: a failed check is investigated before the split is read (Astra, round 3)
        withheld = f"withheld: a check failed or is missing ({checks})"
    elif ref_missing:
        withheld = f"withheld: reference panels missing ({ref_missing})"
    elif len(n2) < 2 or not all(R[n]["valid"] for n in n2) or not ref:
        withheld = "inconclusive (an N2 panel or the reference is missing or not valid)"
    if withheld and not os.environ.get("MEMORY_M2_CENSUS_SMOKE"):
        out["reading"] = withheld
        json.dump(out, open(OUT / "split.json", "w"), indent=1)
        json.dump({"reading": withheld, "checks": checks}, open(OUT / "summary.json", "w"), indent=1)
        print(withheld)
        return
    out["smoke"] = bool(withheld)
    V = {n: vectors(R[n]) for n in R}
    rng = np.random.default_rng(20261028)
    for t in (30, 300):
        pts = {}
        ones = {n: contributions(V[n], np.ones((1, len(V[n]["a"]))), t) for n in R}
        for name in n2:
            pts[name] = {k: float(v[0]) for k, v in split_from(ones[name], [ones[g] for g in ref]).items()}
        bs = bootstrap(V, ref, n2, rng, t)
        res = {}
        for name in n2:
            b = bs[name]
            bad = int((~(b["Lambda"] > 0)).sum())
            ints = {k: interval(v) for k, v in b.items()}
            res[name] = {"point": pts[name], "intervals": ints, "resamples_lambda_not_positive": bad,
                         "lead_median_definition": float(ones[name]["s"][0] - np.median([ones[g]["s"][0] for g in ref])),
                         "reading": reading(ints["phi_S_lo"], ints["phi_S_hi"], bad, pts[name]["Lambda"])}
            res[name]["by_ensemble"] = {}
            for e in ENSEMBLES:
                eg = [g for g in ref if ensemble_of(g.split("__")[0]) == e]
                if eg:
                    res[name]["by_ensemble"][e] = {k: float(v[0]) for k, v in split_from(ones[name], [ones[g] for g in eg]).items()}
            res[name]["composition_retention"] = composition_retention(V, name, ref, t)
        rd = [res[n]["reading"] for n in n2]
        cmb = combine(*rd)
        out[f"t{t}"] = {"panels": res, "reading": cmb, "readings": rd,
                        "branch": branch(cmb, [res[n]["intervals"]["phi_F_lo"] for n in n2])}
        out[f"t{t}"]["contributions"] = {n: {k: float(v[0]) for k, v in ones[n].items()} for n in R}
    out["reading"] = out["t30"]["reading"]
    out["panels"] = {n: describe_panel(R[n]) for n in R}
    # settling and share, across the reference graphs (counts as fractions of the eligible, not S; Astra)
    s30 = [out["t30"]["contributions"][g]["s"] for g in ref]
    fr = lambda g, key: out["panels"][g][key] / max(R[g]["eligible"], 1)  # noqa: E731
    cohort_frac = [sum(r["cohort"] for r in R[g]["genomes"]) / max(R[g]["eligible"], 1) for g in ref]
    sep_frac = [out["panels"][g]["counts"]["S"] / max(R[g]["eligible"], 1) for g in ref]
    out["settling_and_share"] = {
        "pooled": {"cohort_fraction": spearman(cohort_frac, s30), "separate_fraction": spearman(sep_frac, s30)},
        "by_ensemble": {e: {"cohort_fraction": spearman([x for x, g in zip(cohort_frac, ref) if ensemble_of(g.split("__")[0]) == e],
                                                        [x for x, g in zip(s30, ref) if ensemble_of(g.split("__")[0]) == e]),
                            "separate_fraction": spearman([x for x, g in zip(sep_frac, ref) if ensemble_of(g.split("__")[0]) == e],
                                                          [x for x, g in zip(s30, ref) if ensemble_of(g.split("__")[0]) == e])}
                        for e in ENSEMBLES}}
    del fr
    # the class contributions over time: N2's panels and the reference mean
    ticks = R[n2[0]]["series_ticks"]
    over = {}
    for n in n2 + ["reference_mean"]:
        src = [n] if n != "reference_mean" else ref
        over[n] = {k: list(np.mean([[(sum(R[g]["series"][c][i] for c in names) / R[g]["denominator"]) for i in range(len(ticks))]
                                     for g in src], 0)) for k, names in GROUPS.items()}
    out["over_time"] = {"ticks": ticks, "contributions": over}
    # the locating-radius sensitivity: phi_S at tick 30 with the changed classes
    out["radius_sensitivity"] = radius_sensitivity(R, V, n2, ref)
    json.dump(out, open(OUT / "split.json", "w"), indent=1)
    summ = {"reading_t30": out["t30"]["reading"], "readings_t30": out["t30"]["readings"], "branch": out["t30"]["branch"],
            "reading_t300": out["t300"]["reading"], "checks": checks, "missing_panels": missing,
            "invalid_panels": out["invalid_panels"], "reference_graphs": len(ref),
            "phi": {f"t{t}": {n: {k: {"point": out[f"t{t}"]["panels"][n]["point"][k],
                                       "interval": out[f"t{t}"]["panels"][n]["intervals"][k]}
                                   for k in ("phi_S", "phi_S_lo", "phi_S_hi", "phi_F", "phi_F_lo", "phi_F_hi", "phi_O",
                                             "phi_U", "Lambda")} for n in n2} for t in (30, 300)}}
    json.dump(summ, open(OUT / "summary.json", "w"), indent=1)
    print("reading at tick 30:", out["reading"], {n: out["t30"]["panels"][n]["point"]["phi_S"] for n in n2})


def radius_sensitivity(R, V, n2, ref):
    changed = {}
    for n in R:
        for r in R[n]["genomes"]:
            if "radius" in r:  # both qualifying histories already changed together (census.extras)
                changed.setdefault(n, {})[r["genome"]] = r["radius"]["class"]
    if not changed:
        return {"histories": 0}
    V2 = {}
    for n in R:
        rec = json.loads(json.dumps(R[n]))
        for r in rec["genomes"]:
            if r["genome"] in changed.get(n, {}):
                r["class"] = changed[n][r["genome"]]
        V2[n] = vectors(rec)
    ones = {n: contributions(V2[n], np.ones((1, len(V2[n]["a"]))), 30) for n in R}
    return {"histories": sum(len(r["radius"]["histories"]) for n in R for r in R[n]["genomes"] if "radius" in r),
            "genomes_changing_class": {n: sum(1 for r in R[n]["genomes"] if r["genome"] in changed.get(n, {})
                                              and changed[n][r["genome"]] != r["class"]) for n in changed},
            "phi_S_t30": {n: float(split_from(ones[n], [ones[g] for g in ref])["phi_S"][0]) for n in n2}}


def test_rules():
    """The split's arithmetic, the band and the readings on toy panels."""
    def panel(a, d, cls):
        n = len(a)
        rec = {"all": {"eligible": [True] * n, "a": a, "d30": d, "d300": d},
               "genomes": [{"genome": i, "class": c} for i, c in enumerate(cls)]}
        return vectors(rec)
    n2 = panel([1, 1, 1, 1], [0.8, 0.4, 0.2, 0.2], ["separate states", "fading", "unresolved", "fading"])
    rf = panel([1, 1, 1, 1], [0.1, 0.1, 0.1, 0.3], ["fading", "unresolved", "fading", "separate states"])
    one = np.ones((1, 4))
    cn, cr = contributions(n2, one, 30), contributions(rf, one, 30)
    sp = {k: float(v[0]) for k, v in split_from(cn, [cr]).items()}
    assert abs(sp["Lambda"] - (0.4 - 0.15)) < 1e-12
    assert abs(sum(sp[f"Lambda_{k}"] for k in GROUPS) - sp["Lambda"]) < 1e-12  # the parts add up
    assert abs(sp["phi_S"] - (0.2 - 0.075) / 0.25) < 1e-12
    assert sp["phi_S_lo"] <= sp["phi_S"] <= sp["phi_S_hi"]  # the band brackets phi_S
    assert abs(sp["phi_S_hi"] - (0.2 + 0.05 - 0.075) / 0.25) < 1e-12
    assert abs(sp["phi_S_lo"] - (0.2 - (0.075 + 0.025)) / 0.25) < 1e-12  # the reference's unresolved (Fable, Astra)
    assert reading([0.6, 0.9], [0.7, 0.95], 0, 0.2) == "most"
    assert reading([0.05, 0.1], [0.1, 0.2], 0, 0.2) == "little"
    assert branch("little", [[0.6, 0.9], [0.55, 0.8]]) == "little: the graded part becomes the main target"
    assert branch("little", [[0.6, 0.9], [0.4, 0.8]]) == "little; the remainder not attributed to fading"
    assert branch("most", [[0.6, 0.9], [0.6, 0.9]]) is None
    assert branch("little on one panel, inconclusive on the other", [[0.6, 0.9], [0.6, 0.9]]) is None
    assert reading([0.3, 0.4], [0.35, 0.45], 0, 0.2) == "a part, between a quarter and a half"
    assert reading([0.2, 0.4], [0.35, 0.55], 0, 0.2) == "inconclusive"
    assert reading([0.6, 0.9], [0.7, 0.95], 101, 0.2) == "inconclusive (the lead's denominator)"
    assert reading([0.6, 0.9], [0.7, 0.95], 0, -0.1) == "inconclusive (the lead's denominator)"
    # the combination of the two panels (Fable, Astra, round 2)
    den = "inconclusive (the lead's denominator)"
    assert combine(den, "most") == den and combine("most", den) == den
    assert combine("most", "most") == "most"
    assert combine("most", "inconclusive") == "most on one panel, inconclusive on the other"
    assert combine("inconclusive", "a part, between a quarter and a half").startswith("a part")
    assert combine("most", "a part, between a quarter and a half") == "not replicated"
    assert combine("little", "little") == "little"  # the branch is decided apart (Fable, Astra, round 3)
    # composition, retention and presence add up to Lambda_X, with an empty class on either side
    V = {"n2": n2, "r1": rf, "r2": panel([1, 1, 1, 1], [0.1, 0.2, 0.1, 0.1], ["fading"] * 4)}
    cr_ = composition_retention(V, "n2", ["r1", "r2"], 30)
    lam_s = float(split_from(cn, [cr, contributions(V["r2"], one, 30)])["Lambda_S"][0])
    assert abs(cr_["S"]["composition"] + cr_["S"]["retention"] + cr_["S"]["presence"] - lam_s) < 1e-12
    assert cr_["S"]["presence_pairs"] == 1
    V["n0"] = panel([1, 1], [0.3, 0.1], ["fading", "fading"])  # N2 itself without separate states
    cr0 = composition_retention(V, "n0", ["r1", "r2"], 30)
    assert cr0["S"]["presence_pairs"] == 2 and abs(cr0["S"]["presence"] - (0 - 0.075) / 2) < 1e-12
    # the bootstrap's genome indices: rows of multiplicities sum to N
    W = multiplicities(np.random.default_rng(0).integers(0, 4, (3, 4)), 4)
    assert (W.sum(1) == 4).all()
    # the bootstrap's sharing (Fable, Astra, round 3). (i) Graphs are resampled within ensembles: with a constant
    # ratio |dy|/a in each panel, s does not depend on the genomes drawn, and the reference mean stays at the
    # ensembles' average only if every resample keeps each ensemble's count of graphs.
    flat = lambda r, cl: panel([1.0, 2.0, 0.5, 1.5], [r * 1.0, r * 2.0, r * 0.5, r * 1.5], [cl] * 4)  # noqa: E731
    V = {"N2__7600": flat(0.5, "fading"), "N2__7700": flat(0.5, "fading"),
         "SH-1__7600": flat(0.2, "fading"), "SH-2__7600": flat(0.2, "fading"),
         "SH-route-1__7600": flat(0.6, "fading"), "SH-route-2__7600": flat(0.6, "fading")}
    bs = bootstrap(V, ["SH-1__7600", "SH-2__7600", "SH-route-1__7600", "SH-route-2__7600"], ["N2__7600", "N2__7700"],
                   np.random.default_rng(1), 30, b=50)
    assert np.allclose(bs["N2__7600"]["Lambda"], 0.1) and np.allclose(bs["N2__7700"]["Lambda"], 0.1)
    # (ii) one set of genome indices for every seed-7600 panel, an independent one for seed 7700: with N2's panels
    # equal to the one reference graph, Lambda is zero in every resample at seed 7600 and not at seed 7700
    het = panel([1.0, 2.0, 0.5, 1.5], [0.9, 0.2, 0.4, 0.1], ["fading"] * 4)
    V = {"N2__7600": het, "N2__7700": het, "SH-1__7600": het}
    bs = bootstrap(V, ["SH-1__7600"], ["N2__7600", "N2__7700"], np.random.default_rng(2), 30, b=50)
    assert np.allclose(bs["N2__7600"]["Lambda"], 0.0) and not np.allclose(bs["N2__7700"]["Lambda"], 0.0)


if __name__ == "__main__":
    test_rules()
    main()
