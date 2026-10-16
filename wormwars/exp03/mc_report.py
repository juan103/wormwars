"""03mc's report (PREREGISTRATION.md; DESIGN.md §4, §6): a function of the committed measurements and the local
per-genome arrays, so it can be tested on synthetic records and smoke-run before any formal measurement.

`build(doc, names, load, registered, minimum)`: `doc` is `measurements.json`; `names` the ensembles' graph names;
`load(unit_id)` returns a unit's arrays. Every question reports its counts, its components and its fixed wording;
the four primaries go through Holm with missing questions at p = 1 (`mc.holm`)."""

from __future__ import annotations

import numpy as np

from . import mc
from . import report as R03
from . import verdict as V

P4_KEYS = {"P4": ("final", "steady", ""), "pre": ("pre_final", "pre_steady", "pre_")}


def _ens_rows(names, units, suffix):
    return {e: [(g, units.get(f"graph/{g}/{suffix}")) for g in names[e]] for e in mc.ENSEMBLES}


def single_signal(n2_unit, names, units, load, which: str, suffix: str, minimum: int, effect_boot: int) -> dict:
    """03r's single-signal rule (`report.single_signal`) on P4 or the pre-tanh P4 of the `suffix` units, with
    03's per-ensemble records: SEs by bootstrap over genomes, the latent SD and its margin, the effect interval,
    both rank directions. Withheld, with the gates, when N2 is invalid or an ensemble has too few valid graphs."""
    fk, sk, pre = P4_KEYS[which]
    vkey = f"{pre}valid"
    if n2_unit is None or not n2_unit["unit"].get(vkey):
        return {"overall": "withheld", "reason": "N2 invalid or not measured"}
    a = load(n2_unit["id"])
    n2 = {"num": np.abs(a[fk].astype(float)), "den": np.abs(a[sk].astype(float))}
    n2v = float(n2["num"].mean() / n2["den"].mean())
    n2se = R03.ratio_se(n2["num"], n2["den"])
    res, counts = {}, {}
    for e, rows in _ens_rows(names, units, suffix).items():
        ok = [(g, u) for g, u in rows if u is not None and u.get(vkey)]
        counts[e] = {"planned": len(rows), "measured": sum(u is not None for _, u in rows), "valid": len(ok)}
        if len(ok) < 2:
            res[e] = {"n2": n2v, "graphs": len(ok), "values": [], "at_or_above": 0, "unavailable": "fewer than 2"}
            continue
        data = []
        for g, u in ok:
            arr = load(f"graph/{g}/{suffix}")
            data.append({"num": np.abs(arr[fk].astype(float)), "den": np.abs(arr[sk].astype(float))})
        ev = np.array([d["num"].mean() / d["den"].mean() for d in data])
        mse = float(np.mean([R03.ratio_se(d["num"], d["den"]) ** 2 for d in data]))
        latent = float(np.sqrt(max(np.var(ev, ddof=1) - mse, 0.0)))
        lo, hi = V.effect_interval(n2, data, lambda d: float(np.mean(d["num"]) / np.mean(d["den"])),
                                   n_boot=effect_boot, seed=R03.EFFECT_SEED)
        res[e] = {"n2": n2v, "n2_se": n2se, "ensemble_mean": float(ev.mean()), "ensemble_latent_sd": latent,
                  "margin": 0.5 * latent, "graphs": int(len(ev)), "p": V.rank_p(n2v, ev, "above"),
                  "p_opposite": V.rank_p(n2v, ev, "below"), "effect_interval": [lo, hi],
                  "n2_interval": [n2v - 1.645 * n2se, n2v + 1.645 * n2se],
                  "ensemble_q05_q95": [float(np.quantile(ev, 0.05)), float(np.quantile(ev, 0.95))], "values": ev.tolist()}
    complete = all(c["valid"] >= minimum for c in counts.values())
    if not complete:
        return {"overall": "withheld", "reason": "too few valid graphs in an ensemble", "counts": counts,
                "gates": R03.gates({e: r for e, r in res.items()}, "P4")}
    out = R03.single_signal(res, "P4")
    out.update(counts=counts, n2=n2v, n2_se=n2se)
    return out


def rank_question(n2_value, values_by_ensemble: dict, at_or_below: bool, minimum: int) -> dict:
    """A primary rank question: per ensemble, r and the rank p; the question's p by intersection-union. Withheld
    (p = None) if N2 is invalid or any ensemble has fewer than `minimum` valid graphs."""
    per = {e: mc.rank_p(np.array([np.nan if v is None else v for v in vals], float), n2_value, at_or_below)
           for e, vals in values_by_ensemble.items()}
    complete = n2_value is not None and np.isfinite(n2_value) and all(r["n"] >= minimum for r in per.values())
    return {"n2": n2_value, "per_ensemble": per, "complete": bool(complete),
            "p": mc.intersection_union(per) if complete else None}


def _qb_arrays(units, load, batches, cond):
    f_i, s_i, f_d, s_d = [], [], [], []
    for b in range(batches):
        it, de = units.get(f"qb/{b}/intact"), units.get(f"qb/{b}/{cond}")
        if it is None or de is None:
            return None
        ai, ad = load(f"qb/{b}/intact"), load(f"qb/{b}/{cond}")
        f_i.append(ai["final"]), s_i.append(ai["steady"]), f_d.append(ad["final"]), s_d.append(ad["steady"])
    return [np.concatenate(x).astype(np.float64) for x in (f_i, s_i, f_d, s_d)]


def question_b(units, load, registered, batches) -> dict:
    B = registered["bootstrap"]
    out, comps, complete = {}, [], True
    for cond in ("RIA", "AIY", "both"):
        arr = _qb_arrays(units, load, batches, cond)
        if arr is None:
            out[cond] = {"complete": False}
            complete = complete and cond == "both"
            continue
        bt = mc.paired_bootstrap(*arr, resamples=B["resamples"], seed=B["genomes_seed"])
        if not bt["valid"] or bt["dropped"] > 0.01 * B["resamples"]:
            out[cond] = {"complete": False, "bootstrap": bt}
            complete = complete and cond == "both"
            continue
        t = mc.qb_tests(bt["cut"], bt["cut_se"], bt["dP4"], bt["dP4_se"])
        out[cond] = {"complete": True, "bootstrap": bt, "tests": t}
        if cond != "both":
            comps += [t["p_cut"], t["p_eq"]]
    p = max(comps) if complete and len(comps) == 4 else None
    return {"per_deletion": out, "complete": p is not None, "p": p}


def wording(q: str, res: dict, holm: dict, replicated: bool) -> str:
    h = holm[q]
    if res.get("p") is None:
        return "withheld: " + res.get("reason", "the question's measurements are incomplete")
    if q == "B":
        pd = res["per_deletion"]
        if h["passed"]:
            return ("Deleting the RIA pair, or the AIY pair, cuts N2's response by more than 40% while P4 stays within "
                    "0.02: the history signal falls approximately in proportion.")
        parts = []
        for cond in ("RIA", "AIY"):
            t, b = pd[cond]["tests"], pd[cond]["bootstrap"]
            if t["p_cut"] > 0.05:
                parts.append(f"{cond}'s cut was not shown to exceed 40% ({b['cut']:.3f}, 90% interval "
                             f"{b['cut_q05_q95'][0]:.3f} to {b['cut_q05_q95'][1]:.3f})")
            if t["p_eq"] > 0.05:
                parts.append(f"{cond}'s change in P4 was not shown to be within 0.02 ({b['dP4']:+.4f}, 90% interval "
                             f"{b['dP4_q05_q95'][0]:+.4f} to {b['dP4_q05_q95'][1]:+.4f})")
        base = "the registered criterion was not met: " + ("; ".join(parts) if parts else "see the components")
        return _holm_stop(base, h)
    if q == "C":
        r = res["per"]
        text = (f"N2's response is unusually high relative to permutations of its weight magnitudes: {r['r']} of "
                f"{r['n']} permutations reached it.") if h["passed"] else (
            f"the registered criterion was not met: {r['r']} of {r['n']} permutations reached N2's response")
        return text if h["passed"] else _holm_stop(text, h)
    counts = "; ".join(f"{e} {r['r']} of {r['n']}" for e, r in res["per_ensemble"].items())
    if q == "A":
        if h["passed"]:
            text = (f"N2's P4 changed unusually little when gap junctions were switched off, relative to each ensemble: "
                    f"graphs per ensemble that changed as little or less: {counts}.")
            if replicated:
                text += " N2's P4 lead over each ensemble narrows without gap junctions."
            return text
        return _holm_stop(f"the registered criterion was not met: graphs per ensemble that changed as little as N2 or "
                          f"less: {counts}", h)
    if q == "D":
        if h["passed"]:
            return (f"N2 retained an unusually large share of its history difference 30 ticks after the ramp, relative "
                    f"to each ensemble: graphs per ensemble that retained as much or more: {counts}.")
        return _holm_stop(f"the registered criterion was not met: graphs per ensemble that retained as much as N2 or "
                          f"more: {counts}", h)
    raise ValueError(q)


def _holm_stop(text: str, h: dict) -> str:
    if h["alone_at_alpha"] and not h["passed"]:
        return ("met α = 0.05 alone, but not its Holm threshold: not confirmed under the registered familywise rule ("
                + text + ")")
    return text


def _boot_ci(values, seed, resamples=10_000):
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)], float)
    if len(v) < 2:
        return None
    rng = np.random.default_rng(seed)
    m = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(resamples)]
    return [float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))]


def build(doc: dict, names: dict, load, registered: dict, minimum: dict, effect_boot: int = 1000) -> dict:
    units = doc["units"]
    plan = {u["id"]: u for u in doc["plan"]}
    floor = registered["denominator_floor"]
    B = registered["bootstrap"]
    get = lambda uid: {"id": uid, "unit": units[uid]} if uid in units else None  # noqa: E731
    n2_long = units.get("N2/long")
    batches = sum(1 for k in plan if k.startswith("qb/") and k.endswith("/intact"))
    perms = sorted(int(k.split("/")[1]) for k in plan if k.startswith("perm/"))

    # the third replication, Q-E, and the gaps-off levels: 03r's single-signal rule
    replication = single_signal(get("N2/long"), names, units, load, "P4", "long", minimum["graphs"], effect_boot)
    q_e = single_signal(get("N2/long"), names, units, load, "pre", "long", minimum["graphs"], effect_boot)
    gaps_level = single_signal(get("N2/gaps"), names, units, load, "P4", "gaps", minimum["graphs"], effect_boot)
    replicated = replication.get("overall") == "distinctive relative to every ensemble"

    # Q-A
    def dp4(long_u, gaps_u):
        if long_u is None or gaps_u is None or not (long_u["valid"] and gaps_u["valid"]):
            return None
        return gaps_u["P4"] - long_u["P4"]
    n2_dA = dp4(units.get("N2/long"), units.get("N2/gaps"))
    vals_A = {e: [dp4(units.get(f"graph/{g}/long"), units.get(f"graph/{g}/gaps")) for g in names[e]] for e in mc.ENSEMBLES}
    q_a = rank_question(n2_dA, vals_A, at_or_below=True, minimum=minimum["graphs"])
    q_a["levels"] = {"N2": [n2_long and n2_long["P4"], units.get("N2/gaps", {}).get("P4")],
                     "ensemble_medians": {e: [float(np.nanmedian([np.nan if (u := units.get(f"graph/{g}/{s}")) is None
                                                                  or u["P4"] is None else u["P4"] for g in names[e]]))
                                              for s in ("long", "gaps")] for e in mc.ENSEMBLES}}

    # Q-B
    q_b = question_b(units, load, registered, batches)

    # Q-C
    ref = units.get("qb/0/intact")
    pv = [units.get(f"perm/{s}") for s in perms]
    pv_valid = [u for u in pv if u is not None and u["valid"]]
    if ref is not None and ref["valid"] and len(pv_valid) >= minimum["permutations"]:
        r_c = mc.rank_p(np.array([u["denominator"] for u in pv_valid]), ref["denominator"], at_or_below=False)
        q_c = {"per": r_c, "complete": True, "p": r_c["p"], "n2_response": ref["denominator"]}
    else:
        q_c = {"complete": False, "p": None, "valid_permutations": len(pv_valid)}

    # Q-D
    tick = str(registered["tick"])
    share = lambda u: None if u is None else u.get("share", {}).get(tick)  # noqa: E731
    q_d = rank_question(share(n2_long), {e: [share(units.get(f"graph/{g}/long")) for g in names[e]]
                                         for e in mc.ENSEMBLES}, at_or_below=False, minimum=minimum["graphs"])

    ps = {"A": q_a["p"], "B": q_b["p"], "C": q_c["p"], "D": q_d["p"]}
    holm = mc.holm(ps)
    results = {"A": q_a, "B": q_b, "C": q_c, "D": q_d}
    words = {q: wording(q, results[q], holm, replicated) for q in "ABCD"}

    # secondaries with tests (outside the family)
    sec = {}
    if q_c["complete"]:
        sec["Q-C P4 rank"] = mc.rank_p(np.array([u["P4"] for u in pv_valid if u["P4"] is not None]), ref["P4"], False)
    sec["Q-D other ticks"] = {}
    for t in registered["secondary_ticks"]:
        st = lambda u, t=str(t): None if u is None else u.get("share", {}).get(t)  # noqa: E731
        sec["Q-D other ticks"][str(t)] = rank_question(st(n2_long), {e: [st(units.get(f"graph/{g}/long"))
                                                                         for g in names[e]] for e in mc.ENSEMBLES},
                                                       False, minimum["graphs"])
    controls = {}
    if units.get("qb/0/intact"):
        a0 = load("qb/0/intact")["steady"]
        for t, ks in registered["controls"].items():
            if f"qb/0/{t}" not in units or any(f"pair/{k}" not in units for k in ks):
                controls[t] = {"complete": False}
                continue
            at = load(f"qb/0/{t}")["steady"]
            per = {k: mc.cut_difference(a0, at, load(f"pair/{k}")["steady"], resamples=B["resamples"],
                                        seed=B["genomes_seed"]) for k in ks}
            p = max(v["p"] for v in per.values())
            controls[t] = {"complete": True, "per_control": per, "p": p, "passed": bool(p <= 0.05)}
    sec["degree-matched controls"] = controls

    # descriptive
    desc = {}
    if units.get("qb/0/intact"):
        d0 = units["qb/0/intact"]["denominator"]
        screen = {k.split("/", 1)[1]: 1 - u["denominator"] / d0 for k, u in units.items() if k.startswith("pair/")}
        for t in ("RIA", "AIY", "both"):
            if f"qb/0/{t}" in units:
                screen[t] = 1 - units[f"qb/0/{t}"]["denominator"] / d0
        order = sorted((k for k in screen if k != "both"), key=lambda k: -screen[k])
        desc["pair screen, batch 0"] = {"cuts": screen, "rank_by_cut": {t: order.index(t) + 1 for t in ("RIA", "AIY")
                                                                        if t in order}, "pairs": len(order)}
        fac = {}
        for cond in ("RIA", "AIY", "both"):
            if f"qb/0/{cond}" not in units:
                continue
            n2_cut = 1 - units[f"qb/0/{cond}"]["denominator"] / d0
            cuts = [1 - units[f"fact/{s}/{cond}"]["denominator"] / units[f"perm/{s}"]["denominator"]
                    for s in perms[:registered["factorial_permutations"]]
                    if f"fact/{s}/{cond}" in units and f"perm/{s}" in units]
            if cuts:
                ci = _boot_ci(cuts, B["permutations_seed"])
                fac[cond] = {"N2_cut": n2_cut, "permutations_mean_cut": float(np.mean(cuts)), "permutations": len(cuts),
                             "contrast": n2_cut - float(np.mean(cuts)),
                             "contrast_95": None if ci is None else [n2_cut - ci[1], n2_cut - ci[0]]}
        desc["factorial"] = fac
    nulls = {}
    for cond in ("RIA", "AIY", "both"):
        per_e = {}
        for e in mc.ENSEMBLES:
            cuts = []
            for g in names[e][:registered["null_deletion_graphs_per_ensemble"]]:
                u, base = units.get(f"null/{g}/{cond}"), units.get(f"graph/{g}/long")
                if u is not None and base is not None and base["denominator"] >= floor:
                    cuts.append(1 - u["denominator"] / base["denominator"])
            n2c = None
            if units.get("qb/0/intact") and f"qb/0/{cond}" in units:
                n2c = 1 - units[f"qb/0/{cond}"]["denominator"] / units["qb/0/intact"]["denominator"]
            per_e[e] = {"graphs": len(cuts), "median_cut": float(np.median(cuts)) if cuts else None,
                        "mean_cut_95": _boot_ci(cuts, B["graphs_seed"]),
                        "N2_cut": n2c, "graphs_at_or_above_N2": None if n2c is None else int(sum(c >= n2c for c in cuts))}
        nulls[cond] = per_e
    desc["null-graph deletions"] = nulls
    if q_c["complete"] and n2_long is not None and n2_long["valid"]:
        pooled = [u["P4"] for e in mc.ENSEMBLES for g in names[e] if (u := units.get(f"graph/{g}/long")) and u["valid"]]
        med = float(np.median(pooled)) if pooled else None
        perm_p4 = [u["P4"] for u in pv_valid if u["P4"] is not None]
        if med is not None and perm_p4 and n2_long["P4"] != med:
            rng = np.random.default_rng(B["permutations_seed"])
            boots = [np.median(np.asarray(perm_p4)[rng.integers(0, len(perm_p4), len(perm_p4))]) for _ in range(B["resamples"])]
            kept = lambda m: (m - med) / (n2_long["P4"] - med)  # noqa: E731
            desc["Q-C kept share of N2's excess P4"] = {
                "pooled_null_median_P4": med, "permutations_median_P4": float(np.median(perm_p4)),
                "kept": kept(float(np.median(perm_p4))),
                "kept_95": [kept(float(np.quantile(boots, 0.025))), kept(float(np.quantile(boots, 0.975)))]}
    curves = {}
    for e in mc.ENSEMBLES:
        rows = [u["mean_abs_difference"] for g in names[e] if (u := units.get(f"graph/{g}/long")) and u.get("valid")]
        if rows:
            r = np.asarray(rows)
            curves[e] = {"median_share": (np.median(r / r[:, :1], axis=0)).tolist()}
    if n2_long is not None:
        m = np.asarray(n2_long["mean_abs_difference"])
        curves["N2"] = {"share": (m / m[0]).tolist(), "eligible": n2_long["eligible"],
                        "remaining": n2_long["remaining"], "settled_and_remaining": n2_long["settled_and_remaining"]}
        curves["ticks"] = n2_long["ticks"]
    sar = {e: [u["settled_and_remaining"] for g in names[e] if (u := units.get(f"graph/{g}/long"))] for e in mc.ENSEMBLES}
    desc["curves"] = curves
    desc["settled with separation left, per ensemble (median, max)"] = {
        e: [float(np.median(v)), int(max(v))] if v else None for e, v in sar.items()}
    desc["turn read-out tanh slope at the holds' end"] = {
        "N2": n2_long and n2_long.get("slope_hold"),
        **{e: (lambda v: [float(np.median(v)), float(np.mean(np.asarray(v) < (n2_long or {}).get("slope_hold", np.inf)))]
               if v else None)([u["slope_hold"] for g in names[e] if (u := units.get(f"graph/{g}/long"))])
           for e in mc.ENSEMBLES}}

    counts = {"planned_units": len(plan), "completed_units": len(units),
              "invalid_units": sorted(k for k, u in units.items() if not u["valid"]),
              "attempts": [{k: a.get(k) for k in ("started_utc", "ended_utc", "outcome", "owner_word")}
                           for a in doc["attempts"]]}
    headline = {"third replication of P4": replication.get("overall"),
                **{f"Q-{q}": {"p": holm[q]["p"], "holm_adjusted_p": holm[q]["adjusted_p"], "passed": holm[q]["passed"],
                              "wording": words[q]} for q in "ABCD"},
                "Q-E (pre-tanh P4)": q_e.get("overall")}
    return {"what": "03mc's registered statistics", "smoke": doc.get("smoke"), "headline": headline,
            "holm": holm, "replication": replication, "Q-A": q_a, "Q-B": q_b, "Q-C": q_c, "Q-D": q_d, "Q-E": q_e,
            "gaps_off_levels": gaps_level, "secondary_tests": sec, "descriptive": desc, "counts": counts}
