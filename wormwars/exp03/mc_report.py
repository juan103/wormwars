"""03mc's report (PREREGISTRATION.md; DESIGN.md §4, §6): a function of the committed measurements and the local
per-genome arrays, so it can be tested on synthetic records and smoke-run before any formal measurement.

`build(doc, names, load, registered, minimum)`: `doc` is `measurements.json`; `names` the ensembles' graph names;
`load(unit_id)` returns a unit's arrays (the runner's loader checks each against its recorded hash). Every question
reports its planned, measured and valid counts, its components, N2's estimate with an interval, and its fixed
wording; the four primaries go through Holm with missing questions at p = 1 (`mc.holm`)."""

from __future__ import annotations

import numpy as np

from . import mc
from . import report as R03
from . import verdict as V

P4_KEYS = {"P4": ("final", "steady", ""), "pre": ("pre_final", "pre_steady", "pre_")}
MISSING = "missing"  # a planned unit not measured, kept apart from a measured but invalid one (Fable, Astra)


def _ens_rows(names, units, suffix):
    return {e: [(g, units.get(f"graph/{g}/{suffix}")) for g in names[e]] for e in mc.ENSEMBLES}


def single_signal(n2_unit, names, units, load, which: str, suffix: str, minimum: int, effect_boot: int) -> dict:
    """03r's single-signal rule (`report.single_signal`) on P4 or the pre-tanh P4 of the `suffix` units, with
    03's per-ensemble records (kept in full: Astra, prereg review): SEs by bootstrap over genomes, the latent SD and
    its margin, the effect interval, both rank directions. Withheld, with the gates, when N2 is invalid or an
    ensemble has too few valid graphs."""
    fk, sk, pre = P4_KEYS[which]
    vkey = f"{pre}valid"
    counts0 = {e: {"planned": len(rows), "measured": sum(u is not None for _, u in rows),
                   "valid": sum(1 for _, u in rows if u is not None and u.get(vkey))}
               for e, rows in _ens_rows(names, units, suffix).items()}
    if n2_unit is None or not n2_unit["unit"].get(vkey):
        return {"overall": "withheld", "reason": "N2 invalid or not measured", "counts": counts0}
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
                "gates": R03.gates({e: r for e, r in res.items()}, "P4"), "per_ensemble": res}
    out = R03.single_signal(res, "P4")
    out.update(counts=counts, n2=n2v, n2_se=n2se, per_ensemble=res)
    return out


def failing_gates(sig: dict) -> list[str]:
    return [f"{e}: {', '.join(k for k in ('rank_gate', 'margin_gate') if not g.get(k, False))}"
            for e, g in sig.get("gates", {}).items() if not (g.get("rank_gate") and g.get("margin_gate"))]


def signal_wording(kind: str, sig: dict) -> str:
    """03r's outcomes (distinctive, reversed, not distinctive, withheld) in this study's registered words."""
    o = sig.get("overall")
    if o == "withheld":
        return "withheld: " + sig.get("reason", "")
    if kind == "Q-E":
        if o == "distinctive relative to every ensemble":
            return "P4's distinctiveness persists on the pre-tanh read-out"
        if o == "reversed against every ensemble":
            return "reversed against every ensemble on the pre-tanh read-out"
        return "pre-tanh distinctiveness was not established (failing gates: " + "; ".join(failing_gates(sig)) + ")"
    if o == "distinctive relative to every ensemble":
        return f"{kind}: distinctive relative to every ensemble"
    if o == "reversed against every ensemble":
        return f"{kind}: reversed against every ensemble"
    return f"{kind}: not distinctive (failing gates: " + "; ".join(failing_gates(sig)) + ")"


def rank_question(n2_value, values_by_ensemble: dict, at_or_below: bool, minimum: int) -> dict:
    """A rank question: per ensemble, the planned, measured and valid counts, r and the rank p; the question's p by
    intersection-union. Entries are a value, None (measured, invalid) or MISSING (not measured). Withheld (p = None)
    if N2 is invalid or any ensemble has fewer than `minimum` valid graphs."""
    per = {}
    for e, vals in values_by_ensemble.items():
        measured = [v for v in vals if v is not MISSING]
        r = mc.rank_p(np.array([np.nan if v is None else v for v in measured], float), n2_value, at_or_below)
        per[e] = {**r, "planned": len(vals), "measured": len(measured)}
    complete = n2_value is not None and np.isfinite(n2_value) and all(r["n"] >= minimum for r in per.values())
    return {"n2": n2_value, "per_ensemble": per, "complete": bool(complete),
            "p": mc.intersection_union(per) if complete else None}


def genome_ci(arrays: list, stat, seed: int, resamples: int) -> list | None:
    """A 95% percentile interval of N2's statistic over its genomes, resampled once and shared by every array."""
    n = arrays[0].shape[-1]  # genomes are the last axis (the curve is [ticks, genomes])
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(resamples):
        i = rng.integers(0, n, n)
        v = stat(*[a[..., i] for a in arrays])
        if v is not None and np.isfinite(v):
            vals.append(v)
    return [float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))] if vals else None


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
    """Q-B: RIA and AIY pooled over the batches; the double deletion is descriptive, and its absence does not
    withhold Q-B (PREREGISTRATION §6)."""
    B = registered["bootstrap"]
    out, comps, complete = {}, [], True
    intact = [b for b in range(batches) if f"qb/{b}/intact" in units]
    for cond in ("RIA", "AIY", "both"):
        present = sum(f"qb/{b}/{cond}" in units for b in range(batches))
        valid = sum(1 for b in range(batches) if units.get(f"qb/{b}/{cond}", {}).get("valid"))
        paired = [b for b in intact if f"qb/{b}/{cond}" in units]
        counts = {"batches_planned": batches, "batches_measured": present, "batches_valid": valid,
                  "intact_batches_measured": len(intact), "paired_batches": len(paired)}
        arr = _qb_arrays(units, load, batches, cond)
        if arr is None:
            desc = None
            if paired:  # Astra (review of draft 3): a descriptive estimate from the complete pairs, never a test
                a = [np.concatenate([load(f"qb/{b}/{k}")[q] for b in paired]).astype(np.float64)
                     for k, q in (("intact", "final"), ("intact", "steady"), (cond, "final"), (cond, "steady"))]
                d = mc.paired_bootstrap(*a, resamples=B["resamples"], seed=B["genomes_seed"])
                desc = {"note": "descriptive, from the batches measured in both conditions; the question is withheld",
                        "batches": paired, **d}
            out[cond] = {"complete": False, **counts, "descriptive_available_batches": desc}
            complete = complete and cond == "both"
            continue
        bt = mc.paired_bootstrap(*arr, resamples=B["resamples"], seed=B["genomes_seed"])
        if not bt["valid"] or bt["dropped"] > 0.01 * B["resamples"]:
            out[cond] = {"complete": False, "bootstrap": bt, **counts}
            complete = complete and cond == "both"
            continue
        t = mc.qb_tests(bt["cut"], bt["cut_se"], bt["dP4"], bt["dP4_se"])
        out[cond] = {"complete": True, "bootstrap": bt, "tests": t, **counts}
        if cond != "both":
            comps += [t["p_cut"], t["p_eq"]]
    p = max(comps) if complete and len(comps) == 4 else None
    return {"per_deletion": out, "complete": p is not None, "p": p,
            "reason": None if p is not None else "a batch or a deletion is missing, or its bootstrap is invalid"}


def lead_change(units, names) -> dict | None:
    """Q-A's second sentence (Fable, prereg review): N2's lead over each ensemble's median P4, intact and with gap
    junctions off, and its change. Computed, never asserted."""
    n2l, n2g = units.get("N2/long"), units.get("N2/gaps")
    if not (n2l and n2g and n2l["valid"] and n2g["valid"]):
        return None
    out = {}
    for e in mc.ENSEMBLES:
        li = [u["P4"] for g in names[e] if (u := units.get(f"graph/{g}/long")) and u["valid"]]
        lg = [u["P4"] for g in names[e] if (u := units.get(f"graph/{g}/gaps")) and u["valid"]]
        if not li or not lg:
            return None
        intact, gaps = n2l["P4"] - float(np.median(li)), n2g["P4"] - float(np.median(lg))
        out[e] = {"lead_intact": intact, "lead_gaps_off": gaps, "change": gaps - intact}
    return out


def wording(q: str, res: dict, holm: dict, replicated: bool) -> str:
    h = holm[q]
    if res.get("p") is None:
        return "withheld: " + (res.get("reason") or "the question's measurements are incomplete")
    if q == "B":
        pd = res["per_deletion"]
        if h["passed"]:
            return ("Deleting the RIA pair, or the AIY pair, cuts N2's response by more than 40% while P4 stays within "
                    "0.02: the history signal falls approximately in proportion.")
        parts = []
        thr = h.get("threshold", 0.05)  # a part is named if it misses the question's Holm threshold (Fable)
        for cond in ("RIA", "AIY"):
            t, b = pd[cond]["tests"], pd[cond]["bootstrap"]
            if t["p_cut"] > thr:
                parts.append(f"{cond}'s cut was not shown to exceed 40% ({b['cut']:.3f}, 90% interval "
                             f"{b['cut_q05_q95'][0]:.3f} to {b['cut_q05_q95'][1]:.3f})")
            if t["p_eq"] > thr:
                parts.append(f"{cond}'s change in P4 was not shown to be within 0.02 ({b['dP4']:+.4f}, 90% interval "
                             f"{b['dP4_q05_q95'][0]:+.4f} to {b['dP4_q05_q95'][1]:+.4f})")
        base = "the registered criterion was not met: " + (
            "; ".join(parts) if parts else "each component met its test; Holm's step-down stopped at an earlier question")
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
            lead = res.get("lead")
            if replicated and lead:
                changes = "; ".join(f"{e} {v['change']:+.3f}" for e, v in lead.items())
                if all(v["lead_gaps_off"] < v["lead_intact"] for v in lead.values()):
                    text += f" N2's P4 lead over each ensemble's median narrows without gap junctions, by: {changes}."
                else:
                    text += f" N2's lead over the ensemble median did not narrow in every ensemble: {changes}."
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
    """Holm's step-down rule: a question whose own p met α but which Holm did not reach or pass (PREREGISTRATION §6
    notes that an earlier failure, not only its own threshold, can stop it)."""
    if h["alone_at_alpha"] and not h["passed"]:
        return ("met α = 0.05 alone, but not its Holm threshold: not confirmed under the registered familywise rule ("
                + text + ")")
    return text


def _boot_ci(values, seed, resamples=10_000, transform=None, stat="mean"):
    """95% percentile interval over units of the mean or the median (`stat`), or of `transform` of the median; the
    transform is applied to each bootstrap sample before the quantiles (Astra, prereg review)."""
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)], float)
    if len(v) < 2:
        return None
    rng = np.random.default_rng(seed)
    if transform is not None:
        stat = "median"
    f = np.median if stat == "median" else np.mean
    m = [float(f(v[rng.integers(0, len(v), len(v))])) for _ in range(resamples)]
    if transform is not None:
        m = [transform(x) for x in m]
    return [float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))]


def _value(u, key):
    """A unit's value for a rank question: MISSING if not measured, None if invalid."""
    if u is None:
        return MISSING
    return u.get(key) if u.get("valid") else None


def build(doc: dict, names: dict, load, registered: dict, minimum: dict, effect_boot: int = 1000) -> dict:
    units = doc["units"]
    plan = {u["id"]: u for u in doc["plan"]}
    floor = registered["denominator_floor"]
    B = registered["bootstrap"]
    get = lambda uid: {"id": uid, "unit": units[uid]} if uid in units else None  # noqa: E731
    n2_long = units.get("N2/long")
    batches = sum(1 for k in plan if k.startswith("qb/") and k.endswith("/intact"))
    perms = sorted(int(k.split("/")[1]) for k in plan if k.startswith("perm/"))
    tick = str(registered["tick"])

    # the third replication, Q-E, and the gaps-off levels: 03r's single-signal rule
    replication = single_signal(get("N2/long"), names, units, load, "P4", "long", minimum["graphs"], effect_boot)
    q_e = single_signal(get("N2/long"), names, units, load, "pre", "long", minimum["graphs"], effect_boot)
    gaps_level = single_signal(get("N2/gaps"), names, units, load, "P4", "gaps", minimum["graphs"], effect_boot)
    replicated = replication.get("overall") == "distinctive relative to every ensemble"

    # Q-A
    def dp4(long_u, gaps_u):
        if long_u is None or gaps_u is None:
            return MISSING
        if not (long_u["valid"] and gaps_u["valid"]):
            return None
        return gaps_u["P4"] - long_u["P4"]
    n2_dA = dp4(units.get("N2/long"), units.get("N2/gaps"))
    n2_dA = None if n2_dA is MISSING else n2_dA
    q_a = rank_question(n2_dA, {e: [dp4(units.get(f"graph/{g}/long"), units.get(f"graph/{g}/gaps")) for g in names[e]]
                                for e in mc.ENSEMBLES}, at_or_below=True, minimum=minimum["graphs"])
    q_a["lead"] = lead_change(units, names)
    if n2_dA is not None:
        al, ag = load("N2/long"), load("N2/gaps")
        q_a["n2_interval_95"] = genome_ci(
            [np.abs(al["final"]).astype(float), np.abs(al["steady"]).astype(float), np.abs(ag["final"]).astype(float),
             np.abs(ag["steady"]).astype(float)],
            lambda fl, sl, fg, sg: (fg.mean() / sg.mean() - fl.mean() / sl.mean())
            if min(sl.mean(), sg.mean()) >= floor else None, B["genomes_seed"], B["resamples"])
    q_a["ensemble_median_change"] = {e: (float(np.median(v)) if (v := [x for x in [dp4(units.get(f"graph/{g}/long"),
                                                                                      units.get(f"graph/{g}/gaps"))
                                                                                  for g in names[e]]
                                                                     if x is not MISSING and x is not None]) else None)
                                     for e in mc.ENSEMBLES}

    # Q-B
    q_b = question_b(units, load, registered, batches)

    # Q-C: N2's batch-0 intact response; a valid permutation is one whose P4 is valid
    ref = units.get("qb/0/intact")
    pv = [units.get(f"perm/{s}") for s in perms]
    pv_valid = [u for u in pv if u is not None and u["valid"]]
    q_c = {"planned": len(perms), "measured": sum(u is not None for u in pv), "valid": len(pv_valid)}
    if ref is not None and ref["valid"]:  # the estimates are reported whether or not the question is complete
        a0 = load("qb/0/intact")
        q_c.update({"n2_response": ref["denominator"],
                    "n2_response_interval_95": genome_ci([np.abs(a0["steady"]).astype(float)], lambda s: s.mean(),
                                                         B["genomes_seed"], B["resamples"])})
    if pv_valid:
        q_c["permutations_response_median"] = float(np.median([u["denominator"] for u in pv_valid]))
    if ref is not None and ref["valid"] and len(pv_valid) >= minimum["permutations"]:
        r_c = mc.rank_p(np.array([u["denominator"] for u in pv_valid]), ref["denominator"], at_or_below=False)
        q_c.update({"per": r_c, "complete": True, "p": r_c["p"]})
    else:
        q_c.update({"complete": False, "p": None, "reason": "N2's reference invalid or fewer than the minimum of "
                                                             "valid permutations"})

    # Q-D
    def share(u, t=tick):
        if u is None:
            return MISSING
        return u.get("share", {}).get(t)
    n2_share = share(n2_long)
    n2_share = None if n2_share is MISSING else n2_share
    q_d = rank_question(n2_share, {e: [share(units.get(f"graph/{g}/long")) for g in names[e]] for e in mc.ENSEMBLES},
                        at_or_below=False, minimum=minimum["graphs"])
    if n2_share is not None:
        d = np.abs(load("N2/long")["diff"]).astype(float)
        ti = n2_long["ticks"].index(int(tick))
        q_d["n2_interval_95"] = genome_ci([d], lambda x: x[ti].mean() / x[0].mean() if x[0].mean() >= floor else None,
                                          B["genomes_seed"], B["resamples"])

    ps = {"A": q_a["p"], "B": q_b["p"], "C": q_c["p"], "D": q_d["p"]}
    holm = mc.holm(ps)
    results = {"A": q_a, "B": q_b, "C": q_c, "D": q_d}
    words = {q: wording(q, results[q], holm, replicated) for q in "ABCD"}

    # secondaries with tests (outside the family)
    sec = {}
    if q_c.get("complete"):
        sec["Q-C P4 rank"] = mc.rank_p(np.array([u["P4"] for u in pv_valid]), ref["P4"], False)
    sec["Q-D other ticks"] = {}
    for t in registered["secondary_ticks"]:
        n2t = share(n2_long, str(t))
        sec["Q-D other ticks"][str(t)] = rank_question(None if n2t is MISSING else n2t,
                                                       {e: [share(units.get(f"graph/{g}/long"), str(t)) for g in names[e]]
                                                        for e in mc.ENSEMBLES}, False, minimum["graphs"])
    controls = {}
    i0 = units.get("qb/0/intact")
    if i0 is not None and i0["valid"]:
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
    if i0 is not None and i0["valid"]:
        a0 = load("qb/0/intact")
        screen = {}
        for uid in [k for k in units if k.startswith("pair/")] + [f"qb/0/{c}" for c in ("RIA", "AIY", "both")
                                                                  if f"qb/0/{c}" in units]:
            ad = load(uid)
            bt = mc.paired_bootstrap(a0["final"], a0["steady"], ad["final"], ad["steady"], resamples=B["resamples"],
                                     seed=B["genomes_seed"])
            key = uid.split("/")[-1]
            screen[key] = ({"cut": bt["cut"], "cut_95": bt["cut_q025_q975"], "numerator_cut": bt["numerator_cut"],
                            "numerator_cut_95": bt["numerator_cut_q025_q975"], "dP4": bt["dP4"],
                            "dP4_95": bt["dP4_q025_q975"]} if bt["valid"] else {"valid": False})
        order = sorted((k for k in screen if k != "both" and "cut" in screen[k]), key=lambda k: -screen[k]["cut"])
        desc["pair screen, batch 0"] = {"per_pair": screen, "pairs": len(order),
                                        "rank_by_cut": {t: order.index(t) + 1 for t in ("RIA", "AIY") if t in order}}
        fac = {}
        for cond in ("RIA", "AIY", "both"):
            if f"qb/0/{cond}" not in units:
                continue
            n2_cut = 1 - units[f"qb/0/{cond}"]["denominator"] / i0["denominator"]
            cuts = [1 - units[f"fact/{s}/{cond}"]["denominator"] / units[f"perm/{s}"]["denominator"]
                    for s in perms[:registered["factorial_permutations"]]
                    if f"fact/{s}/{cond}" in units and f"perm/{s}" in units and units[f"perm/{s}"]["valid"]]
            if cuts:
                ci = _boot_ci(cuts, B["permutations_seed"], B["resamples"])
                fac[cond] = {"N2_cut": n2_cut, "permutations_mean_cut": float(np.mean(cuts)), "permutations": len(cuts),
                             "permutation_cuts": cuts, "contrast": n2_cut - float(np.mean(cuts)),
                             "contrast_95": None if ci is None else [n2_cut - ci[1], n2_cut - ci[0]]}
        desc["factorial"] = fac
    nulls = {}
    for cond in ("RIA", "AIY", "both"):
        per_e = {}
        n2c = None
        if i0 is not None and i0["valid"] and f"qb/0/{cond}" in units:
            n2c = 1 - units[f"qb/0/{cond}"]["denominator"] / i0["denominator"]
        for e in mc.ENSEMBLES:
            cuts = {}
            for g in names[e][:registered["null_deletion_graphs_per_ensemble"]]:
                u, base = units.get(f"null/{g}/{cond}"), units.get(f"graph/{g}/long")
                if u is not None and base is not None and base["valid"]:
                    cuts[g] = 1 - u["denominator"] / base["denominator"]
            v = list(cuts.values())
            per_e[e] = {"graphs": len(v), "cuts": cuts, "median_cut": float(np.median(v)) if v else None,
                        "median_cut_95": _boot_ci(v, B["graphs_seed"], B["resamples"], stat="median"), "N2_cut": n2c,
                        "graphs_at_or_above_N2": None if n2c is None else int(sum(c >= n2c for c in v))}
        nulls[cond] = per_e
    desc["null-graph deletions"] = nulls
    if q_c.get("complete") and n2_long is not None and n2_long["valid"]:
        pooled = [u["P4"] for e in mc.ENSEMBLES for g in names[e] if (u := units.get(f"graph/{g}/long")) and u["valid"]]
        med = float(np.median(pooled)) if pooled else None
        perm_p4 = [u["P4"] for u in pv_valid]
        if med is not None and perm_p4 and n2_long["P4"] != med:
            kept = lambda m: (m - med) / (n2_long["P4"] - med)  # noqa: E731
            desc["Q-C kept share of N2's excess P4"] = {
                "pooled_null_median_P4": med, "permutations_median_P4": float(np.median(perm_p4)),
                "N2_excess": n2_long["P4"] - med, "kept": kept(float(np.median(perm_p4))),
                "kept_95": _boot_ci(perm_p4, B["permutations_seed"], B["resamples"], transform=kept)}
    curves = {}
    for e in mc.ENSEMBLES:
        rows = [u for g in names[e] if (u := units.get(f"graph/{g}/long")) and u.get("valid")
                and u["mean_abs_difference"][0] >= floor]
        if rows:
            r = np.asarray([u["mean_abs_difference"] for u in rows])
            frac = [u["remaining"] / u["eligible"] for u in rows if u["eligible"]]
            curves[e] = {"graphs": len(rows), "median_share": (np.median(r / r[:, :1], axis=0)).tolist(),
                         "eligible_fraction_median": float(np.median([u["eligible"] for u in rows])) / doc["registered"]["genomes"]
                         if doc.get("registered") else None,
                         "remaining_among_eligible_median": float(np.median(frac)) if frac else None,
                         "settled_and_remaining_median_max": [float(np.median([u["settled_and_remaining"] for u in rows])),
                                                              int(max(u["settled_and_remaining"] for u in rows))]}
    if n2_long is not None and n2_long["valid"] and n2_long["mean_abs_difference"][0] >= floor:
        m = np.asarray(n2_long["mean_abs_difference"])
        curves["N2"] = {"share": (m / m[0]).tolist(), "eligible": n2_long["eligible"], "remaining": n2_long["remaining"],
                        "remaining_among_eligible": n2_long["remaining"] / n2_long["eligible"] if n2_long["eligible"] else None,
                        "settled_and_remaining": n2_long["settled_and_remaining"]}
        curves["ticks"] = n2_long["ticks"]
    desc["curves"] = curves
    slopes = {}
    for key in ("slope_hold", "slope_ramp"):
        n2s = (n2_long or {}).get(key)
        per = {}
        for e in mc.ENSEMBLES:
            v = [u[key] for g in names[e] if (u := units.get(f"graph/{g}/long")) and u.get("valid")]
            per[e] = None if not v else {"median": float(np.median(v)),
                                         "share_below_N2": None if n2s is None else float(np.mean(np.asarray(v) < n2s))}
        slopes[key] = {"N2": n2s, "ensembles": per}
    desc["turn read-out tanh slopes"] = slopes

    counts = {"planned_units": len(plan), "completed_units": len(units),
              "invalid_units": sorted(k for k, u in units.items() if not u["valid"]),
              "attempts": [{k: a.get(k) for k in ("started_utc", "ended_utc", "outcome", "owner_word",
                                                  "replaced_orphan_arrays")} for a in doc["attempts"]]}
    headline = {"third replication of P4": signal_wording("third replication of P4", replication),
                **{f"Q-{q}": {"p": holm[q]["p"], "holm_adjusted_p": holm[q]["adjusted_p"], "passed": holm[q]["passed"],
                              "wording": words[q]} for q in "ABCD"},
                "Q-E (pre-tanh P4)": signal_wording("Q-E", q_e),
                "gaps-off P4 levels": signal_wording("N2's gaps-off P4", gaps_level)}
    return {"what": "03mc's registered statistics", "smoke": doc.get("smoke"), "headline": headline,
            "holm": holm, "replication": replication, "Q-A": q_a, "Q-B": q_b, "Q-C": q_c, "Q-D": q_d, "Q-E": q_e,
            "gaps_off_levels": gaps_level, "secondary_tests": sec, "descriptive": desc, "counts": counts}
