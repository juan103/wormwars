"""M1's summary over the fresh panels, the decision rules D1 and D2, and the readings of the cheap kills
(docs/memory/M1-PLAN.md, draft 8). Reads runs/memory-m1/{accounting,panel,tau,growers}.json and panels/*.json|npz;
writes runs/memory-m1/summary.json.
Uncertainty: 2000 resamples. The seed-7600 panels share their genome draws index by index (one seed, one edge count),
so in each resample one set of genome indices is drawn for all of them, and another for N2's seed-7700 panel; each
ensemble's random graphs are resampled too; 90% percentile intervals. Every reading, and the calculation paths that can
meet an undefined case, are functions tested by test_rules() before the summary runs."""
import json

import numpy as np

from common import ENSEMBLES, OUT, SEED, SEED2, START_FLOOR, dump, ensemble_of

B, MIN_PER_STRATUM = 2000, 10
MAX_BAD = int(0.05 * B)  # resamples with a denominator at or below zero; more than this and the rule is inconclusive
ARMS = ("intact", "scale0.25", "scale0.5", "scale2.0")


def interval(x):
    """The 90% interval of the finite resamples, and the integer count of the others (a denominator at or below zero, or
    a resample that empties a used stratum)."""
    x = np.asarray(x, float)
    good = x[np.isfinite(x)]
    return ([float(np.percentile(good, 5)), float(np.percentile(good, 95))] if len(good) else [None, None]), int(len(x) - len(good))


def ratio(num, den):
    num, den = np.asarray(num, float), np.asarray(den, float)
    out = np.full(np.broadcast(num, den).shape, np.nan)
    np.divide(num, den, out=out, where=den > 0)
    return out


def safe_log(x):
    x = np.asarray(x, float)
    out = np.full(x.shape, np.nan)
    np.log(x, out=out, where=x > 0)
    return out


def ref_median(stat, by_e, gpick, nres):
    """{key: [B]} -> [B]: per resample, the median over its resampled reference graphs; an ensemble with no graph is
    skipped, and with none at all the result is NaN."""
    cols = [np.stack([stat[k] for k in by_e[e]], 1)[np.arange(nres)[:, None], gpick[e]] for e in by_e if by_e[e]]
    return np.median(np.concatenate(cols, 1), 1) if cols else np.full(nres, np.nan)


def support_and_pi(obs_counts, genome_counts, minimum=MIN_PER_STRATUM):
    """B3's common support and weights: a stratum is used if every panel has at least `minimum` distinct genomes in it
    (Fable, round 5); pi is the pooled proportion of observations over the used strata (the plan; Astra, round 6).
    Both arguments are [panels, strata]."""
    used = (np.asarray(genome_counts) >= minimum).all(0)
    pooled = np.asarray(obs_counts, float).sum(0) * used
    return used, (pooled / pooled.sum() if pooled.sum() > 0 else pooled)


def d2_panel(x, ref_pt, st_n2, ref_bs):
    """D2 for one N2 panel. x and ref_pt: point values {"s", "N", "Ap"}; st_n2 and ref_bs: their resamples. Returns the
    record and the input to d2_reading; a zero term or a non-positive contrast leaves the conditions unmet."""
    if not (min(x["s"], x["N"], x["Ap"], *ref_pt.values()) > 0):
        return {"available": False, "note": "a zero term"}, {"conditions": False, "P1": [None, None], "P2": [None, None], "bad": 0}
    T = float(np.log(x["s"] / ref_pt["s"]))
    P1 = float(np.log(x["s"] / x["N"]) - np.log(ref_pt["s"] / ref_pt["N"]))
    P2 = float(np.log(x["Ap"] / ref_pt["Ap"]))
    Tb = safe_log(ratio(st_n2["s"], ref_bs["s"]))
    P1b = safe_log(ratio(st_n2["s"], st_n2["N"])) - safe_log(ratio(ref_bs["s"], ref_bs["N"]))
    P2b = safe_log(ratio(st_n2["Ap"], ref_bs["Ap"]))
    Ti, badT = interval(Tb)
    P1i, bad1 = interval(ratio(P1b, Tb))
    P2i, bad2 = interval(ratio(P2b, Tb))
    cond = bool(T >= np.log(1.2) and Ti[0] is not None and Ti[0] > 0)
    rec = {"available": True, "T": T, "T_interval": Ti, "P1_over_T": P1 / T if T > 0 else None,
           "P2_over_T": P2 / T if T > 0 else None, "P1_over_T_interval": P1i, "P2_over_T_interval": P2i,
           "bad": max(badT, bad1, bad2), "conditions": cond}
    return rec, {"conditions": cond, "P1": P1i, "P2": P2i, "bad": rec["bad"]}


def d1_reading(b3, a2_checks):
    """b3: per N2 panel {"conditions": bool, "f_interval": [lo, hi], "bad": int}; a2_checks: per ensemble
    {"supported": bool, "f": float or None}."""
    if not all(p["conditions"] and p["bad"] <= MAX_BAD and p["f_interval"][0] is not None for p in b3):
        return "inconclusive (conditions)"
    if all(p["f_interval"][1] < 0.25 for p in b3):
        reading = "fires"
    elif all(p["f_interval"][0] > 0.25 for p in b3):
        reading = "does not fire"
    else:
        return "inconclusive"
    for c in a2_checks:  # A2 is a check: a supported ensemble on the other side of 0.25 makes D1 inconclusive
        if c["supported"] and c["f"] is not None and ((reading == "fires" and c["f"] >= 0.25)
                                                      or (reading == "does not fire" and c["f"] <= 0.25)):
            return "inconclusive (A2 disagrees)"
    return reading


def d2_reading(panels):
    """panels: per N2 panel {"conditions": bool, "P1": [lo, hi], "P2": [lo, hi], "bad": int}, P the intervals of P/T."""
    if not all(p["conditions"] and p["bad"] <= MAX_BAD and p["P1"][0] is not None and p["P2"][0] is not None
               for p in panels):
        return "inconclusive (conditions)"
    if all(p["P1"][0] > 0.5 and p["P2"][0] > 0.5 for p in panels):
        return "fires"
    if all(p["P1"][1] < 0.5 or p["P2"][1] < 0.5 for p in panels):
        return "does not fire"
    return "inconclusive"


def gap_reading(n2_geo, ref_geo, n2_dyn, ref_dyn):
    """Fable's test on the a-weighted means at tick 30: N2 below the null median under both ratios, one, or neither."""
    if None in (n2_geo, ref_geo, n2_dyn, ref_dyn):
        return "unavailable"
    below = (n2_geo < ref_geo) + (n2_dyn < ref_dyn)
    return {2: "support", 1: "partial", 0: "no support"}[int(below)]


def antisym_reading(n2_share, n2_ret, ref_ret):
    if None in (n2_share, n2_ret, ref_ret):
        return "unavailable"
    return "no support" if (n2_share < 0.10 and n2_ret <= ref_ret) else "not rejected"


def tau_reading(summary):
    if not summary.get("reading_available"):
        return "unavailable"
    if summary["intact_lead"] <= 0:
        return "no intact lead"
    return "survives" if summary["equal_lead"] >= 0.5 * summary["intact_lead"] else "does not survive"


def growers_reading(rec):
    if not rec.get("available"):
        return "unavailable"
    return ("no support" if (rec["frac_state_grow10_rho_lt1"] < 0.02 and rec["numerator30_state_grow10_rho_lt1"] < 0.10)
            else "not rejected")


def test_rules():
    ok = {"conditions": True, "bad": 0}
    assert d1_reading([{**ok, "f_interval": [0.0, 0.2]}] * 2, []) == "fires"
    assert d1_reading([{**ok, "f_interval": [0.0, 0.3]}] * 2, []) == "inconclusive"
    assert d1_reading([{**ok, "f_interval": [0.3, 0.9]}] * 2, []) == "does not fire"
    assert d1_reading([{**ok, "f_interval": [0.0, 0.2]}, {**ok, "f_interval": [0.3, 0.9]}], []) == "inconclusive"
    assert d1_reading([{**ok, "f_interval": [0.0, 0.2]}] * 2, [{"supported": True, "f": 0.6}]).startswith("inconclusive")
    assert d1_reading([{**ok, "f_interval": [0.0, 0.2]}] * 2, [{"supported": False, "f": 0.6}]) == "fires"
    assert d1_reading([{**ok, "f_interval": [0.0, 0.2]}] * 2, [{"supported": False, "f": None}]) == "fires"
    assert d1_reading([{**ok, "conditions": False, "f_interval": [0.0, 0.2]}] * 2, []).startswith("inconclusive")
    assert d1_reading([{**ok, "bad": MAX_BAD, "f_interval": [0.0, 0.2]}] * 2, []) == "fires"  # exactly 5% is allowed
    assert d1_reading([{**ok, "bad": MAX_BAD + 1, "f_interval": [0.0, 0.2]}] * 2, []).startswith("inconclusive")
    assert d1_reading([{**ok, "f_interval": [None, None]}] * 2, []).startswith("inconclusive")
    assert d2_reading([{**ok, "P1": [0.6, 0.9], "P2": [0.55, 0.8]}] * 2) == "fires"
    assert d2_reading([{**ok, "P1": [0.6, 0.9], "P2": [0.45, 0.8]}] * 2) == "inconclusive"
    assert d2_reading([{**ok, "P1": [0.6, 0.9], "P2": [0.1, 0.4]}] * 2) == "does not fire"
    assert d2_reading([{**ok, "P1": [0.6, 0.9], "P2": [0.1, 0.4]}, {**ok, "P1": [0.6, 0.9], "P2": [0.6, 0.8]}]) == "inconclusive"
    assert d2_reading([{**ok, "conditions": False, "P1": [0.6, 0.9], "P2": [0.6, 0.9]}] * 2).startswith("inconclusive")
    assert d2_reading([{**ok, "P1": [None, None], "P2": [0.6, 0.9]}] * 2).startswith("inconclusive")
    assert np.isnan(ratio(1.0, 0.0)) and np.isnan(ratio(1.0, -1.0)) and ratio(1.0, 2.0) == 0.5
    assert np.isnan(safe_log(0.0)) and safe_log(1.0) == 0.0
    assert interval(np.r_[np.full(MAX_BAD, np.nan), np.zeros(B - MAX_BAD)])[1] == MAX_BAD
    assert gap_reading(1, 2, 1, 2) == "support" and gap_reading(1, 2, 3, 2) == "partial" and gap_reading(3, 2, 3, 2) == "no support"
    assert antisym_reading(0.05, 0.3, 0.4) == "no support" and antisym_reading(0.15, 0.3, 0.4) == "not rejected"
    assert antisym_reading(0.05, 0.5, 0.4) == "not rejected"
    assert gap_reading(None, 2, 1, 2) == "unavailable" and antisym_reading(0.05, None, 0.4) == "unavailable"
    t = {"reading_available": True, "intact_lead": 0.1}
    assert tau_reading({**t, "equal_lead": 0.06}) == "survives" and tau_reading({**t, "equal_lead": 0.04}) == "does not survive"
    assert tau_reading({**t, "intact_lead": 0, "equal_lead": 1}) == "no intact lead" and tau_reading({}) == "unavailable"
    g = {"available": True, "frac_state_grow10_rho_lt1": 0.01, "numerator30_state_grow10_rho_lt1": 0.05}
    assert growers_reading(g) == "no support" and growers_reading({**g, "numerator30_state_grow10_rho_lt1": 0.2}) == "not rejected"
    assert growers_reading({**g, "frac_state_grow10_rho_lt1": 0.03}) == "not rejected" and growers_reading({}) == "unavailable"
    # the calculation paths (Astra, round 4): equal shares, a zero term, an empty ensemble
    one = np.ones(B)
    pt = {"s": 0.3, "N": 0.25, "Ap": 0.35}
    res = lambda p: {q: one * v for q, v in p.items()}  # noqa: E731
    rec, inp = d2_panel(pt, dict(pt), res(pt), res(pt))
    assert rec["T"] == 0 and rec["P1_over_T"] is None and not rec["conditions"] and d2_reading([inp] * 2).startswith("inconclusive")
    rec, inp = d2_panel({**pt, "N": 0.0}, pt, res(pt), res(pt))
    assert rec["available"] is False and d2_reading([inp] * 2).startswith("inconclusive")
    big = {"s": 0.6, "N": 0.3, "Ap": 0.6}  # N2 twice the reference
    rec, inp = d2_panel(big, pt, res(big), res(pt))
    assert rec["conditions"] and rec["P1_over_T"] > 0.5
    k = ("g", 1)
    assert np.allclose(ref_median({k: one * 2}, {"A": [k], "B": []}, {"A": np.zeros((B, 1), int), "B": np.zeros((B, 0), int)}, B), 2)
    assert np.isnan(ref_median({}, {"A": []}, {"A": np.zeros((B, 0), int)}, B)).all()
    # B3's weights come from observations, its support from distinct genomes (Astra, round 6): one genome with all four
    # arms in stratum 0 gives 4 observations but 1 genome
    obs = np.array([[40, 10, 10], [40, 10, 10]])
    gen = np.array([[10, 10, 10], [10, 10, 9]])
    used, pi = support_and_pi(obs, gen)
    assert list(used) == [True, True, False] and np.allclose(pi, [0.8, 0.2, 0.0])


def main():
    P = OUT / "panels"
    panel = json.load(open(OUT / "panel.json"))
    rand = panel["random"]
    sel = sorted({x for e in panel["selected"].values() for x in e.values()})
    N2A, N2B = ("N2", SEED), ("N2", SEED2)
    J = {k: json.load(open(P / f"{k[0]}__{k[1]}.json")) for k in [N2A, N2B] + [(g, SEED) for g in rand + sel]}
    invalid = sorted(f"{k[0]}__{k[1]}" for k, r in J.items() if not r["valid"])
    if not (J[N2A]["valid"] and J[N2B]["valid"]):  # D1 and D2 inconclusive; nothing else is summarised
        dump({"invalid_panels": invalid, "n2_valid": False, "D1_reading": "inconclusive (an N2 panel is not valid)",
              "D2": {"reading": "inconclusive (an N2 panel is not valid)"}}, "summary.json")
        print("an N2 panel is not valid")
        return
    rand = [g for g in rand if J[(g, SEED)]["valid"]]  # an invalid panel is excluded from the reference and reported
    sel = [g for g in sel if J[(g, SEED)]["valid"]]
    KEYS = [N2A, N2B] + [(g, SEED) for g in rand]
    REF = KEYS[2:]
    Z = {k: dict(np.load(P / f"{k[0]}__{k[1]}.npz", allow_pickle=False)) for k in KEYS}
    rng = np.random.default_rng(20261021)
    out = {"invalid_panels": invalid, "n2_valid": True, "reference_graphs": len(REF),
           "batch_gap_max": max(r["batch_gap"] for r in J.values()),
           "batch_gap_above_tolerance": sorted(f"{k[0]}__{k[1]}" for k, r in J.items() if r["batch_gap_above_tolerance"])}
    if not REF:
        out.update({"D1_reading": "inconclusive (no valid reference graph)", "D2": {"reading": "inconclusive (no valid reference graph)"}})
        dump(out, "summary.json")
        return

    def spread(fn):  # a value of None (undefined) is left out of the reference and counted
        vals = {g: fn(J[(g, SEED)]) for g in rand}
        undefined = sum(v is None for v in vals.values())
        vals = {g: v for g, v in vals.items() if v is not None}
        n2v = fn(J[N2A])
        med = lambda xs: float(np.median(xs)) if xs else None  # noqa: E731
        return {"N2": n2v, "N2_seed2": fn(J[N2B]), "random_median": med(list(vals.values())),
                "random_min": float(min(vals.values())) if vals else None, "random_max": float(max(vals.values())) if vals else None,
                "random_at_or_above_N2": int(sum(v >= n2v for v in vals.values())) if n2v is not None else None,
                "random_undefined": undefined,
                "by_ensemble_median": {e: med([v for g, v in vals.items() if ensemble_of(g) == e]) for e in ENSEMBLES},
                "selected": {g: fn(J[(g, SEED)]) for g in sel}}

    for t in (30, 100, 300):
        out[f"eligible_share{t}"] = spread(lambda r, t=t: r[f"eligible_share{t}"])
    out["ineligible_denominator_frac"] = spread(lambda r: r["ineligible_denominator_frac"])
    out["ineligible_numerator_frac30"] = spread(lambda r: r["ineligible_numerator_frac30"])
    for t in (30, 100):
        for k in ("s", "N", "Ap", "Ap_alt_zero", "s_top25", "N_top25", "Ap_top25", "median_norm_ratio", "median_alignment_ratio"):
            out[f"B1_t{t}_{k}"] = spread(lambda r, t=t, k=k: r[f"B1_t{t}"][k])
        out[f"zero_da_t{t}"] = spread(lambda r, t=t: float(r[f"zero_da_t{t}"]))
    for k in ("cohort", "C30", "C300"):
        out[f"B2_{k}"] = spread(lambda r, k=k: float(r["B2"][k]))
    for arm in J[N2A]["arms"]:
        out[f"arm_{arm}_eligible_share30_vs_intact_start"] = spread(lambda r, arm=arm: r["arms"][arm]["eligible_share30_vs_intact_start"])
    out["B3_eligible_every_k"] = spread(lambda r: float(r["B3_eligible_every_k"]))
    b3_ok = [g for g in rand if J[(g, SEED)]["B3_ok"]]
    b3_ready = bool(J[N2A]["B3_ok"] and J[N2B]["B3_ok"] and b3_ok)
    if b3_ready:
        for x in ARMS:
            for k in ("B3_share30_vs_own_start", "B3_mean_a", "B3_median_dv0", "B3_median_da0"):
                out[f"{k}_{x}"] = {"N2": J[N2A]["arms"][x][k], "N2_seed2": J[N2B]["arms"][x][k],
                                   "random_median": float(np.median([J[(g, SEED)]["arms"][x][k] for g in b3_ok]))}
        vals = [J[(g, SEED)]["B3_median_r2_over_r05"] for g in b3_ok if J[(g, SEED)]["B3_median_r2_over_r05"] is not None]
        out["B3_median_r2_over_r05"] = {"N2": J[N2A]["B3_median_r2_over_r05"], "N2_seed2": J[N2B]["B3_median_r2_over_r05"],
                                        "random_median": float(np.median(vals)) if vals else None,
                                        "undefined_genomes": {f"{k[0]}__{k[1]}": J[k]["B3_r2_over_r05_undefined"]
                                                              for k in [N2A, N2B] + [(g, SEED) for g in b3_ok]}}
    for k in J[N2A]["B4"]:
        if k == "undefined_counts":
            out["B4_undefined_counts"] = {f"{x[0]}__{x[1]}": J[x]["B4"][k] for x in KEYS}
            continue
        out[f"B4_{k}"] = spread(lambda r, k=k: r["B4"][k])
    out["between_graph_sd_eligible_share30"] = {e: (float(np.std(v, ddof=1)) if len(v) > 1 else None) for e, v in
                                                {e: [J[(g, SEED)]["eligible_share30"] for g in rand if ensemble_of(g) == e]
                                                 for e in ENSEMBLES}.items()}

    # resampling weights, [B, n]: one draw of genome indices shared by every seed-7600 panel, another for seed 7700
    n = len(Z[N2A]["a"])
    assert all(len(Z[k]["a"]) == n for k in KEYS)
    draw = lambda: np.stack([np.bincount(rng.integers(0, n, n), minlength=n) for _ in range(B)]).astype(np.float64)  # noqa: E731
    W7600, W7700 = draw(), draw()
    W = {k: (W7700 if k == N2B else W7600) for k in KEYS}
    by_e = {e: [(g, SEED) for g in rand if ensemble_of(g) == e] for e in ENSEMBLES}
    pick = lambda m: rng.integers(0, m, (B, m)) if m else np.zeros((B, 0), int)  # noqa: E731  (an empty ensemble)
    gpick = {e: pick(len(by_e[e])) for e in ENSEMBLES}
    sub_e = {e: [(g, SEED) for g in b3_ok if ensemble_of(g) == e] for e in ENSEMBLES}
    sub_pick = {e: pick(len(sub_e[e])) for e in ENSEMBLES}

    # D2 at tick 30
    st, pt = {}, {}
    for k in KEYS:
        z, ok = Z[k], Z[k]["ok"].astype(float)
        den = W[k] @ (z["a"] * ok)
        st[k] = {"s": ratio(W[k] @ (z["d30"] * ok), den), "N": ratio(W[k] @ (z["numN30"] * ok), den),
                 "Ap": ratio(W[k] @ (z["numA30"] * ok), den)}
        pt[k] = J[k]["B1_t30"]
    ref_pt = {q: float(np.median([pt[k][q] for k in REF])) for q in ("s", "N", "Ap")}
    ref_bs = {q: ref_median({k: st[k][q] for k in REF}, by_e, gpick, B) for q in ("s", "N", "Ap")}
    out["D2"] = {}
    d2_in = []
    for n2, tag in ((N2A, "seed7600"), (N2B, "seed7700")):
        rec, inp = d2_panel(pt[n2], ref_pt, st[n2], ref_bs)
        out["D2"][tag] = rec
        d2_in.append(inp)
    out["D2"]["reading"] = d2_reading(d2_in)
    out["D2_by_ensemble"] = {}
    for e in ENSEMBLES:
        if not by_e[e]:
            out["D2_by_ensemble"][e] = {"T": None, "note": "no valid graph"}
            continue
        r = {q: float(np.median([pt[k][q] for k in by_e[e]])) for q in ("s", "N", "Ap")}
        if min(*r.values(), pt[N2A]["s"], pt[N2A]["N"], pt[N2A]["Ap"]) > 0 and pt[N2A]["s"] > r["s"]:
            T = np.log(pt[N2A]["s"] / r["s"])
            out["D2_by_ensemble"][e] = {"T": float(T),
                                        "P1_over_T": float((np.log(pt[N2A]["s"] / pt[N2A]["N"]) - np.log(r["s"] / r["N"])) / T),
                                        "P2_over_T": float(np.log(pt[N2A]["Ap"] / r["Ap"]) / T)}
        else:
            out["D2_by_ensemble"][e] = {"T": None, "note": "no positive contrast, or a zero term"}

    # D1 on B3: genomes eligible at every k, each counted once per k; strata on a (decides) and on |da(0)| (beside it).
    # Only panels with at least 10 such genomes take part; the reference is resampled among them.
    KB = [N2A, N2B] + [(g, SEED) for g in b3_ok]
    RB = KB[2:]

    def b3(var):
        elig = {k: np.all([Z[k][f"a_{x}"] >= START_FLOOR for x in ARMS], 0) for k in KB}
        pooled = np.concatenate([np.concatenate([Z[k][f"{var}_{x}"][elig[k]] for x in ARMS]) for k in KB])
        edges = np.quantile(pooled, [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99])
        K = len(edges) + 1
        sums, strat = {}, {}
        for k in KB:
            num, den, cnt = np.zeros((B, K)), np.zeros((B, K)), np.zeros((B, K))
            num0, den0, cnt0 = np.zeros(K), np.zeros(K), np.zeros(K)
            kcomp = np.zeros((len(ARMS), K))
            anyarm = np.zeros((len(Z[k]["a"]), K), bool)
            strat[k] = {}
            for j, x in enumerate(ARMS):
                s_ = np.digitize(Z[k][f"{var}_{x}"], edges)
                strat[k][x] = s_
                oh = np.eye(K)[s_] * elig[k][:, None]
                d, a = Z[k][f"d30_{x}"], Z[k][f"a_{x}"]
                num += W[k] @ (oh * d[:, None])
                den += W[k] @ (oh * a[:, None])
                cnt += W[k] @ oh
                num0 += oh.T @ d
                den0 += oh.T @ a
                cnt0 += oh.sum(0)
                kcomp[j] = oh.sum(0)
                anyarm |= oh > 0
            sums[k] = (num, den, cnt, num0, den0, cnt0, kcomp, anyarm.sum(0))
        used, pi = support_and_pi(np.stack([sums[k][5] for k in KB]), np.stack([sums[k][7] for k in KB]))
        res = {"edges": [float(x) for x in edges], "used_strata": [int(i) for i in np.where(used)[0]]}
        if not used.any():
            return {**res, **{t: {"conditions": False, "f_interval": [None, None], "bad": 0, "note": "no common support"}
                              for t in ("seed7600", "seed7700")}}
        res["pi"] = [float(x) for x in pi]

        def std_base(num, den, cnt):
            m_num, m_den = ratio(num[..., used], cnt[..., used]), ratio(den[..., used], cnt[..., used])
            return ratio((pi[used] * m_num).sum(-1), (pi[used] * m_den).sum(-1)), ratio(num[..., used].sum(-1), den[..., used].sum(-1))

        P0 = {k: std_base(*sums[k][3:6]) for k in KB}
        PB = {k: std_base(*sums[k][:3]) for k in KB}
        rs, rb = float(np.median([P0[k][0] for k in RB])), float(np.median([P0[k][1] for k in RB]))
        rsb = ref_median({k: PB[k][0] for k in RB}, sub_e, sub_pick, B)
        rbb = ref_median({k: PB[k][1] for k in RB}, sub_e, sub_pick, B)
        mean_a = {k: ratio(sums[k][4], sums[k][5]) for k in KB}  # NaN where a panel has no observation
        med_a = np.nanmedian(np.stack([mean_a[k] for k in RB]), 0)
        res["per_graph"] = {f"{k[0]}__{k[1]}": {"counts": [int(c) for c in sums[k][5]], "genomes": [int(c) for c in sums[k][7]],
                                                "mean_a": [None if np.isnan(m) else float(m) for m in mean_a[k]],
                                                "k_composition": {x: [int(c) for c in sums[k][6][j]] for j, x in enumerate(ARMS)}}
                            for k in KB}
        for n2, tag in ((N2A, "seed7600"), (N2B, "seed7700")):
            num0, den0, cnt0 = sums[n2][3], sums[n2][4], sums[n2][5]
            # coverage per genome: an N2 genome is covered if any of its four arms lies in a used stratum; the covered
            # genomes' share of N2's intact-arm numerator and denominator (over the genomes eligible at every k)
            covered = elig[n2] & np.any([used[strat[n2][x]] for x in ARMS], 0)
            d_int, a_int = Z[n2]["d30_intact"], Z[n2]["a_intact"]
            cov_num = float(d_int[covered].sum() / max(d_int[elig[n2]].sum(), 1e-300))
            cov_den = float(a_int[covered].sum() / max(a_int[elig[n2]].sum(), 1e-300))
            heavy = [i for i in np.where(used)[0] if num0[i] / max(num0.sum(), 1e-300) >= 0.10]  # of the whole numerator, as A2
            balance = max([abs(mean_a[n2][i] / med_a[i] - 1) for i in heavy], default=0.0)
            lead_ok = bool(np.isfinite(P0[n2][1]) and rb > 0 and P0[n2][1] >= 1.1 * rb)
            f = float((P0[n2][0] - rs) / (P0[n2][1] - rb)) if (np.isfinite(P0[n2][1]) and P0[n2][1] > rb) else None
            fi, bad = interval(ratio(PB[n2][0] - rsb, PB[n2][1] - rbb))
            cond = bool(lead_ok and cov_num >= 0.75 and cov_den >= 0.75 and balance <= 0.25)
            res[tag] = {"std": float(P0[n2][0]), "baseline": float(P0[n2][1]), "ref_std": rs, "ref_baseline": rb, "f": f,
                        "f_interval": fi, "bad": bad, "baseline_lead_ratio": float(P0[n2][1] / rb) if rb > 0 else None,
                        "coverage_numerator": cov_num, "coverage_denominator": cov_den, "balance_worst": float(balance),
                        "dropped_pooled_numerator_frac": float(num0[~used].sum() / max(num0.sum(), 1e-300)),
                        "conditions": cond, "f_above_0.75": bool(f is not None and f > 0.75)}
        return res

    if b3_ready:
        out["D1_B3_a"] = b3("a")
        out["D1_B3_da"] = b3("da0")
    else:
        out["D1_B3_a"] = {t: {"conditions": False, "f_interval": [None, None], "bad": 0, "note": "too few genomes eligible at every k"}
                          for t in ("seed7600", "seed7700")}
    acc = json.load(open(OUT / "accounting.json"))
    out["D1_A2"] = {e: acc["A2"][e]["N2_check"] for e in ENSEMBLES}
    b3in = [{"conditions": out["D1_B3_a"][t]["conditions"], "f_interval": out["D1_B3_a"][t]["f_interval"],
             "bad": out["D1_B3_a"][t]["bad"]} for t in ("seed7600", "seed7700")]
    out["D1_reading"] = d1_reading(b3in, list(out["D1_A2"].values()))

    # the cheap kills' readings (each on its own diagnostic only)
    def b4(k):  # N2's value and the reference median over the graphs where it is defined
        vals = [J[(g, SEED)]["B4"][k] for g in rand if J[(g, SEED)]["B4"][k] is not None]
        return J[N2A]["B4"][k], (float(np.median(vals)) if vals else None)
    out["kills"] = {"gap": gap_reading(*b4("gap30_wmean"), *b4("gap_dyn30_wmean")),
                    "antisym": antisym_reading(J[N2A]["B4"]["antisym30_wmean"], *b4("antisym_retention30_wmean")),
                    "equal_tau": tau_reading(json.load(open(OUT / "tau.json"))["summary"]),
                    "growers": growers_reading(json.load(open(OUT / "growers.json")).get("N2", {}))}
    out["kills"]["complement_erasure"] = {k: {"N2": J[N2A]["arms"][k]["eligible_share30_vs_intact_start"],
                                              "random_median": float(np.median([J[(g, SEED)]["arms"][k]["eligible_share30_vs_intact_start"]
                                                                                for g in rand]))}
                                          for k in ("intact", "complement_result", "erase_result", "complement_anatomy", "erase_anatomy")}

    # for M2: the settling cohort's fraction of the mean lead, from pairwise contrasts on 03mc's arrays (A5)
    G = acc["graphs"]
    out["M2_handoff"] = {}
    for e in ENSEMBLES:
        gs = [x for x in G if ensemble_of(x) == e]
        out["M2_handoff"][e] = {}
        for t in (30, 300):
            lead = float(np.mean([acc["N2"][f"eligible_share{t}"] - G[x][f"eligible_share{t}"] for x in gs]))
            part = float(np.mean([acc["N2"][f"cohort_C{t}"] - G[x][f"cohort_C{t}"] for x in gs]))
            out["M2_handoff"][e][f"t{t}"] = {"mean_lead": lead, "mean_cohort_contrast": part,
                                             "fraction": part / lead if lead > 0 else None}
    dump(out, "summary.json")
    print("D1", out["D1_reading"], "D2", out["D2"]["reading"], "kills", {k: v for k, v in out["kills"].items() if isinstance(v, str)})


if __name__ == "__main__":
    test_rules()
    main()
