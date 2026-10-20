"""M1, part A (docs/memory/M1-PLAN.md, draft 8): accounting on 03mc's per-genome arrays (runs/p4mc/arrays, local).
A1 the decomposition eligible share = E[r] + Cov(a, r)/E[a], overall and per stratum; A2 amplitude standardisation on
12 pooled strata with common support; A3 the overlap of tick-30 and tick-300 contributors; A4 trimming; A5 the
settling cohort's contribution. Writes runs/memory-m1/accounting.json."""
import json

import numpy as np

from common import ENSEMBLES, REMAIN, ROOT, SETTLE_TOL, START_FLOOR, dump, ensemble_of, measurements

ARR = ROOT / "runs" / "p4mc" / "arrays"
TICKS = json.load(open(ROOT / "experiments" / "03mc-p4-confirm" / "report.json"))["descriptive"]["curves"]["ticks"]
I30, I100, I300 = TICKS.index(30), TICKS.index(100), TICKS.index(300)
MIN_PER_STRATUM = 10


def load(name):
    z = np.load(ARR / name, allow_pickle=False)
    return np.abs(z["diff"]).astype(np.float64), z["end_state_range"].astype(np.float64)


def share(d, t, keep=None):
    keep = np.ones(d.shape[1], bool) if keep is None else keep
    return float(d[t, keep].mean() / d[0, keep].mean())


def decompose(a, n):  # eligible share = E[r] + Cov(a, r)/E[a], population covariance
    r = n / a
    return {"share": float(n.sum() / a.sum()), "mean_r": float(r.mean()),
            "cov_term": float(((a - a.mean()) * (r - r.mean())).mean() / a.mean())}


def per_graph(d, rng_):
    a = d[0]
    ok = a >= START_FLOOR
    # 03mc's committed units are all valid with many eligible genomes; a file that is not would be a different input
    assert ok.sum() >= 10 and a.mean() >= 1e-4, "an 03mc array without an eligible population"
    r = d[I30, ok] / a[ok]
    remaining = ok & (d[I300] > REMAIN * a)
    cohort = (rng_ < SETTLE_TOL) & remaining
    A1 = decompose(a[ok], d[I30, ok])
    out = {"share30": share(d, I30), "share100": share(d, I100), "share300": share(d, I300),
           "eligible_share30": A1["share"], "eligible_share300": float(d[I300, ok].sum() / a[ok].sum()),
           "mean_r30": A1["mean_r"], "cov_term30": A1["cov_term"],
           "ineligible_numerator_frac30": float(d[I30, ~ok].sum() / d[I30].sum()),
           "ineligible_denominator_frac": float(a[~ok].sum() / a.sum()),
           "q75_r30": float(np.quantile(r, 0.75)), "growth_frac30": float((r > 1).mean()),
           # A5: the settling cohort (settled and remaining)
           "cohort": int(cohort.sum()),
           "cohort_C30": float(d[I30, cohort].sum() / a[ok].sum()),
           "cohort_C300": float(d[I300, cohort].sum() / a[ok].sum()),
           "share30_without_cohort": share(d, I30, ~cohort), "share300_without_cohort": share(d, I300, ~cohort)}
    k = int(0.1 * ok.sum())  # A3
    idx = np.where(ok)[0]
    top30 = set(idx[np.argsort(-d[I30, ok])[:k]])
    top300 = set(idx[np.argsort(-d[I300, ok])[:k]])
    out["overlap_top10_300_in_30"] = len(top30 & top300) / k
    order = np.argsort(-d[I30])  # A4
    for p in (2, 5):
        keep = np.ones(d.shape[1], bool)
        keep[order[:int(p / 100 * d.shape[1])]] = False
        out[f"share30_trim{p}"] = share(d, I30, keep)
    return out, a[ok], d[I30, ok]


def strata_edges(pooled):
    q = np.quantile(pooled, [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99])
    return q  # 12 strata: np.digitize(a, q) in 0..11


def standardise(amps, nums, names):
    """A2 for one comparison set (N2 first, then one ensemble's graphs): its own pooled strata, common support,
    pooled proportions, standardised and baseline shares, coverage and balance for N2, per-stratum decomposition."""
    edges = strata_edges(np.concatenate([amps[n] for n in names]))
    K = len(edges) + 1
    b = {n: np.digitize(amps[n], edges) for n in names}
    counts = np.array([[int((b[n] == k).sum()) for k in range(K)] for n in names])
    used = (counts >= MIN_PER_STRATUM).all(0)
    pooled = counts.sum(0)
    pi = pooled * used / (pooled * used).sum()
    res = {"edges": [float(x) for x in edges], "used_strata": [int(k) for k in np.where(used)[0]],
           "pi": [float(x) for x in pi], "graphs": {}}
    for i, n in enumerate(names):
        num = np.array([nums[n][b[n] == k].mean() if counts[i, k] else np.nan for k in range(K)])
        den = np.array([amps[n][b[n] == k].mean() if counts[i, k] else np.nan for k in range(K)])
        inside = used[b[n]]
        res["graphs"][n] = {
            "std_share": float((pi[used] * num[used]).sum() / (pi[used] * den[used]).sum()) if used.any() else None,
            "baseline_share": float(nums[n][inside].sum() / amps[n][inside].sum()) if inside.any() else None,
            "dropped_numerator_frac": float(nums[n][~inside].sum() / nums[n].sum()),
            "dropped_denominator_frac": float(amps[n][~inside].sum() / amps[n].sum()),
            "stratum_share": [float(x) for x in num / den], "stratum_mean_a": [float(x) for x in den],
            "stratum_counts": [int(x) for x in counts[i]],
            "stratum_numerator_frac": [float(nums[n][b[n] == k].sum() / nums[n].sum()) for k in range(K)],
            "stratum_decomposition": [decompose(amps[n][b[n] == k], nums[n][b[n] == k]) if counts[i, k] else None
                                      for k in range(K)]}
    g = res["graphs"]
    N2, others = g[names[0]], [g[n] for n in names[1:]]
    if not used.any():  # no common support at all: nothing to standardise
        res["N2_check"] = {"supported": False, "f": None, "baseline_lead_ratio": None, "note": "no stratum in common support"}
        return res
    med_a = [float(np.nanmedian([o["stratum_mean_a"][k] for o in others])) for k in range(K)]
    heavy = [k for k in res["used_strata"] if N2["stratum_numerator_frac"][k] >= 0.10]
    mb0 = float(np.median([o["baseline_share"] for o in others]))
    res["N2_check"] = {
        "baseline_lead_ratio": N2["baseline_share"] / mb0 if mb0 > 0 else None,
        "dropped_numerator_frac": N2["dropped_numerator_frac"], "dropped_denominator_frac": N2["dropped_denominator_frac"],
        "stratum_counts": N2["stratum_counts"], "median_graph_stratum_mean_a": med_a,
        "balance_worst": max([abs(N2["stratum_mean_a"][k] / med_a[k] - 1) for k in heavy], default=0.0)}
    c = res["N2_check"]
    c["supported"] = bool(c["baseline_lead_ratio"] is not None and c["baseline_lead_ratio"] >= 1.1
                          and c["dropped_numerator_frac"] <= 0.25
                          and c["dropped_denominator_frac"] <= 0.25 and c["balance_worst"] <= 0.25)
    ms = float(np.median([o["std_share"] for o in others]))
    mb = float(np.median([o["baseline_share"] for o in others]))
    c["f"] = float((N2["std_share"] - ms) / (N2["baseline_share"] - mb)) if (mb > 0 and N2["baseline_share"] > mb) else None
    if c["f"] is None:  # no positive baseline lead: f is undefined and the ensemble is unsupported
        c["supported"] = False
    others_std = [o["std_share"] for o in others]
    c.update({"N2_std_share": N2["std_share"], "median_std_share": ms, "min_std_share": float(min(others_std)),
              "max_std_share": float(max(others_std)), "graphs_at_or_above_N2_std": int(sum(x >= N2["std_share"] for x in others_std)),
              "N2_baseline_share": N2["baseline_share"], "median_baseline_share": mb})
    return res


def test_standardise():
    """The guarded paths: a zero reference baseline, no common support, and an ordinary case."""
    rng = np.random.default_rng(0)
    a = {n: rng.uniform(0.01, 1, 200) for n in ("N2", "g1", "g2")}
    zero = {"N2": a["N2"] * 0.5, "g1": a["g1"] * 0, "g2": a["g2"] * 0}
    c = standardise(a, zero, ["N2", "g1", "g2"])["N2_check"]
    assert c["baseline_lead_ratio"] is None and c["f"] is None and not c["supported"]
    far = {"N2": a["N2"] + 100, "g1": a["g1"], "g2": a["g2"]}  # N2 alone in the top strata: little or no support
    assert standardise(far, {n: x * 0.3 for n, x in far.items()}, ["N2", "g1", "g2"])["N2_check"]["supported"] is False
    c = standardise(a, {"N2": a["N2"] * 0.5, "g1": a["g1"] * 0.3, "g2": a["g2"] * 0.3}, ["N2", "g1", "g2"])["N2_check"]
    assert c["supported"] and abs(c["f"] - 1) < 0.2  # retention unrelated to amplitude: standardising keeps the lead


if __name__ == "__main__":
    test_standardise()
    u = measurements()
    names = ["N2"] + sorted(k.split("/")[1] for k in u if k.startswith("graph/") and k.endswith("/long"))
    rows, amps, nums = {}, {}, {}
    for name in names:
        d, rng_ = load("N2__long.npz" if name == "N2" else f"graph__{name}__long.npz")
        rows[name], amps[name], nums[name] = per_graph(d, rng_)
        ref = u["N2/long" if name == "N2" else f"graph/{name}/long"]
        assert abs(rows[name]["share30"] - ref["share"]["30"]) < 1e-6, name  # the arrays reproduce 03mc's record
        assert rows[name]["cohort"] == ref["settled_and_remaining"], name
    A2 = {e: standardise(amps, nums, ["N2"] + [n for n in names[1:] if ensemble_of(n) == e]) for e in ENSEMBLES}
    for e in ENSEMBLES:
        for n in names[1:]:
            if ensemble_of(n) == e:
                rows[n].update({k: v for k, v in A2[e]["graphs"][n].items() if k in ("std_share", "baseline_share")})
    KEYS = [k for k, v in rows["N2"].items() if isinstance(v, (int, float))]
    summary = {"N2": rows["N2"], "A2": {e: {"edges": A2[e]["edges"], "used_strata": A2[e]["used_strata"], "pi": A2[e]["pi"],
                                            "N2_check": A2[e]["N2_check"], "N2_std_share": A2[e]["graphs"]["N2"]["std_share"],
                                            "N2_baseline_share": A2[e]["graphs"]["N2"]["baseline_share"],
                                            "N2_strata": {k: v for k, v in A2[e]["graphs"]["N2"].items() if k.startswith("stratum")}}
                                        for e in ENSEMBLES}, "ensembles": {}}
    for e in ENSEMBLES:
        g = [n for n in names[1:] if ensemble_of(n) == e]
        summary["ensembles"][e] = {
            "graphs": len(g),
            **{k: {"median": float(np.median([rows[n][k] for n in g])), "min": float(min(rows[n][k] for n in g)),
                   "max": float(max(rows[n][k] for n in g)),
                   "graphs_at_or_above_N2": int(sum(rows[n][k] >= rows["N2"][k] for n in g))} for k in KEYS},
            "stratum_share_median": [float(np.nanmedian([A2[e]["graphs"][n]["stratum_share"][k] for n in g])) for k in range(12)],
            "stratum_mean_a_median": [float(np.nanmedian([A2[e]["graphs"][n]["stratum_mean_a"][k] for n in g])) for k in range(12)],
            "stratum_mean_r_median": [float(np.nanmedian([x["mean_r"] if x else np.nan for x in [A2[e]["graphs"][n]["stratum_decomposition"][k]
                                                                                              for n in g]])) for k in range(12)],
            "stratum_cov_term_median": [float(np.nanmedian([x["cov_term"] if x else np.nan for x in [A2[e]["graphs"][n]["stratum_decomposition"][k]
                                                                                                  for n in g]])) for k in range(12)]}
    summary["graphs"] = {n: {k: rows[n][k] for k in KEYS} for n in names[1:]}
    dump(summary, "accounting.json")
    for k in KEYS:
        print(f"{k:30s} N2 {rows['N2'][k]:8.3f} | " + " ".join(
            f"{e} {summary['ensembles'][e][k]['median']:.3f} ({summary['ensembles'][e][k]['graphs_at_or_above_N2']})"
            for e in ENSEMBLES))
