"""Experiment 03's report (pre-registration §5-§6, as amended by the team's review, D054), a pure
function of the saved per-graph measures, so it can be tested on synthetic data and smoke-tested
on the pilot before any N2 run.

Rules enforced here:
- **Validity.** One mask per signal, used everywhere: P1 and P4 need a denominator mean of at
  least 1e-4 and a finite value; P3 needs a finite value. Excluded graphs are listed.
- **Completeness.** A signal's verdict needs a valid N2 and at least 120 valid graphs in every
  ensemble; otherwise it is withheld and enters Holm with p = 1, so Holm still divides by three.
- **Registered graphs only.** The P3 world profile is computed from the registered ensemble graphs
  alone, never from N2, its variants, or unregistered files.
- **Fixed resampling:** measurement-SE bootstrap 1 000 draws with seed 0; effect interval 1 000
  draws with seed 1.
"""

from __future__ import annotations

import numpy as np

from . import verdict as V

PRIMARY = ("P1", "P3", "P4")
EXPECTED = {"P1": "above", "P3": "above", "P4": "above"}
RESPONSE_CONDITIONS = ("M0", "R1", "R2", "MS", "M0-gaps-off", "M0-uniform", "M0-permuted")
DESCRIPTIVE = ("N2-rev", "N2perm1", "N2perm2", "N2perm3")
MIN_GRAPHS = 120
DENOMINATOR_FLOOR = 1e-4
SE_BOOT, SE_SEED, EFFECT_BOOT, EFFECT_SEED = 1000, 0, 1000, 1
SHARED_GENOMES = 64


def per_genome(m: dict) -> dict:
    f, h, r = m["fitness"], m["history"]["raw_turn"], m["response"]["M0"]
    return {"P1": {"num": np.asarray(r["directional_turn_signed_raw"], float),
                   "den": np.asarray(r["common_turn_raw"], float)},
            "P3": np.asarray(f["T1-M0"], float) - np.asarray(f["T1const-M0"], float),
            "P4": {"num": np.abs(np.asarray(h["final"], float)),
                   "den": np.abs(np.asarray(h["steady_contrast"], float))}}


def value(signal: str, d) -> float:
    if signal == "P3":
        return float(np.mean(d))
    return float(np.mean(d["num"]) / np.mean(d["den"]))


def valid(signal: str, d) -> bool:
    if signal == "P3":
        return bool(np.all(np.isfinite(d)))
    den = float(np.mean(d["den"]))
    return bool(np.isfinite(den) and den >= DENOMINATOR_FLOOR and np.isfinite(value(signal, d)))


def _stat(signal):
    if signal == "P3":
        return lambda d: float(np.mean(d))
    return lambda d: float(np.mean(d["num"]) / np.mean(d["den"]))


def crossed_se(d, common_world) -> float:
    d = np.asarray(d, float) - common_world[None, :]
    g, w = d.shape
    grand, rm, cm = d.mean(), d.mean(1), d.mean(0)
    ms_g = w * np.sum((rm - grand) ** 2) / (g - 1)
    ms_w = g * np.sum((cm - grand) ** 2) / (w - 1)
    ms_e = np.sum((d - rm[:, None] - cm[None, :] + grand) ** 2) / ((g - 1) * (w - 1))
    s_g, s_w = max((ms_g - ms_e) / w, 0.0), max((ms_w - ms_e) / g, 0.0)
    return float(np.sqrt(s_g / g + s_w / w + ms_e / (g * w)))


def ratio_se(num, den) -> float:
    rng = np.random.default_rng(SE_SEED)
    idx = rng.integers(0, len(num), (SE_BOOT, len(num)))
    return float(np.std(num[idx].mean(1) / den[idx].mean(1), ddof=1))


def _t_interval(x):
    from scipy import stats
    x = np.asarray(x, float)
    se = x.std(ddof=1) / np.sqrt(len(x))
    q = stats.t.ppf(0.975, len(x) - 1)
    return [float(x.mean()), float(x.mean() - q * se), float(x.mean() + q * se)]


def secondary(m: dict) -> dict:
    f = {k: np.asarray(v, float) for k, v in m["fitness"].items()}
    t0 = f["T0-M0"].mean(1)
    top = np.sort(t0)[-max(1, len(t0) // 10):]
    by_cond = {}
    for c in RESPONSE_CONDITIONS:
        if c in m["response"]:
            r = m["response"][c]
            den = float(np.mean(r["common_turn_raw"]))
            by_cond[c] = float(np.mean(r["directional_turn_signed_raw"]) / den) if den >= DENOMINATOR_FLOOR else float("nan")
    h = m["history"]["raw_turn"]
    return {"P2": float(f["T1-M0"][:SHARED_GENOMES].mean() - (f["T1-R1"].mean() + f["T1-R2"].mean()) / 2),
            "T0_mean": float(t0.mean()), "T0_top_decile": float(top.mean()),
            "coverage": float(np.mean(m["coverage"])),
            "abs_directional_M0": float(np.mean(m["response"]["M0"]["directional_turn_raw"])),
            "common_M0": float(np.mean(m["response"]["M0"]["common_turn_raw"])),
            "P1_by_condition": by_cond,
            "P4_decay": float(np.median(np.abs(np.asarray(h["after"])) / np.maximum(np.abs(np.asarray(h["final"])), 1e-12)))}


def gates(sig: dict, signal: str) -> dict:
    """Every ensemble's own gates, so a split (some ensembles passing, one failing) is visible even
    though the maximum-p rule gives every ensemble the same p (Astra, D060). Computed for withheld
    signals too (D061)."""
    sign = 1.0 if EXPECTED[signal] == "above" else -1.0
    out = {}
    for e, r in sig.items():
        vals = np.asarray(r["values"], float)
        if "unavailable" in r:
            out[e] = {"graphs": int(len(vals)), "at_or_above": r["at_or_above"], "unavailable": r["unavailable"]}
            continue
        lo_s = min(sign * r["effect_interval"][0], sign * r["effect_interval"][1])
        out[e] = {"graphs": int(len(vals)),
                  "at_or_above": int((vals >= r["n2"]).sum() if sign > 0 else (vals <= r["n2"]).sum()),
                  "p": r["p"], "rank_gate": bool(r["p"] <= V.ALPHA), "margin_gate": bool(lo_s > r["margin"])}
    return out


def single_signal(sig: dict, signal: str) -> dict:
    """One signal tested alone (03r's registered primary test, D059): the maximum rank p over the
    ensembles against alpha, with the same effect-margin gate and verdict rules as §6 of 03, and
    no Holm across signals. `sig`: {ensemble: the per-ensemble record `build` writes}."""
    p_max = max(r["p"] for r in sig.values())
    p_opp = max(r["p_opposite"] for r in sig.values())
    verdicts = {e: V.classify(p_max, p_opp, tuple(r["effect_interval"]), {"effect": r["margin"]}, EXPECTED[signal],
                              tuple(r["n2_interval"]), r["values"]) for e, r in sig.items()}
    v = set(verdicts.values())
    return {"p_max": p_max, "p_max_opposite": p_opp, "verdicts": verdicts, "gates": gates(sig, signal),
            "overall": ("distinctive relative to every ensemble" if v == {"distinctive"} else
                        "reversed against every ensemble" if v == {"reversed"} else "not distinctive")}


def replication_primary(out: dict, signal: str = "P4") -> dict:
    """03r's registered primary result from a built report: the single-signal test, or an explicit
    withheld record when the signal is incomplete (Fable, Astra, D060)."""
    if not out["signals"].get(signal + "_complete"):
        sig = out["signals"].get(signal) or {}
        return {"overall": "withheld", "reason": "N2 invalid or too few valid graphs",
                "counts": out["counts"].get(signal, {}),
                "gates": gates(sig, signal) if sig else "unavailable: N2 invalid on this signal"}
    return single_signal(out["signals"][signal], signal)


def build(measures: dict, n2: str, ensembles: dict, n_boot: int = EFFECT_BOOT,
          min_graphs: int | dict = MIN_GRAPHS, descriptive: tuple = DESCRIPTIVE) -> dict:
    """`measures`: {graph name: saved measures}; only N2, the registered ensemble graphs in
    `ensembles`, and the descriptive N2 variants are read. `n_boot` and `min_graphs` exist for
    tests on small synthetic or pilot sets; the registered values are EFFECT_BOOT and MIN_GRAPHS.
    `min_graphs` may be a per-ensemble dict (03r: 240 for its 256 SH-route graphs, D060)."""
    floor = min_graphs if isinstance(min_graphs, dict) else {e: min_graphs for e in ensembles}
    registered = {n for names in ensembles.values() for n in names}
    # a graph whose calibration failed is excluded from every signal and counted (registered)
    use = [n for n in [n2, *descriptive, *sorted(registered)]
           if n in measures and "calibration_failed" not in measures[n]]
    data = {n: per_genome(measures[n]) for n in use}
    ok = {n: {s: valid(s, data[n][s]) for s in PRIMARY} for n in use}
    ens_p3 = [n for n in registered if n in data and ok[n]["P3"]]
    # with no valid P3 reference graph there is no world profile; P3 is then withheld below
    common = np.mean([np.asarray(data[n]["P3"]).mean(0) for n in ens_p3], axis=0) if ens_p3 else None
    se = {n: {"P1": ratio_se(data[n]["P1"]["num"], data[n]["P1"]["den"]) if ok[n]["P1"] else float("nan"),
              "P3": crossed_se(data[n]["P3"], common) if ok[n]["P3"] and common is not None else float("nan"),
              "P4": ratio_se(data[n]["P4"]["num"], data[n]["P4"]["den"]) if ok[n]["P4"] else float("nan")}
          for n in use}
    vals = {n: {s: value(s, data[n][s]) if ok[n][s] else float("nan") for s in PRIMARY} for n in use}
    out = {"n2": n2, "signals": {}, "exclusions": {}, "counts": {}}
    pv, pv_opp = {}, {}
    for s in PRIMARY:
        direction = EXPECTED[s]
        opposite = "below" if direction == "above" else "above"
        valid_lists = {e: [n for n in names if n in ok and ok[n][s]] for e, names in ensembles.items()}
        out["exclusions"][s] = {e: [n for n in names if n not in ok or not ok[n][s]] for e, names in ensembles.items()}
        out["counts"][s] = {e: len(v) for e, v in valid_lists.items()}
        # a verdict needs every ensemble's statistics, so at least two valid graphs each
        complete = n2 in ok and ok[n2][s] and all(len(v) >= max(floor[e], 2) for e, v in valid_lists.items())
        res = {}
        # the per-ensemble statistics are descriptive and computed whenever N2 is valid, so a
        # withheld signal still reports them (Astra, D061); only verdicts need completeness
        if n2 in ok and ok[n2][s]:
            for e, names in valid_lists.items():
                if len(names) < 2:  # kept as a row, with what is defined (Astra, D061)
                    ev = [vals[n][s] for n in names]
                    at = sum(v >= vals[n2][s] for v in ev) if direction == "above" else sum(v <= vals[n2][s] for v in ev)
                    res[e] = {"n2": vals[n2][s], "n2_se": se[n2][s], "graphs": len(ev), "values": ev,
                              "at_or_above": int(at), "unavailable": "fewer than 2 valid graphs"}
                    continue
                ev = np.array([vals[n][s] for n in names])
                mse = float(np.mean([se[n][s] ** 2 for n in names]))
                latent = float(np.sqrt(max(np.var(ev, ddof=1) - mse, 0.0)))  # truncated at 0 (registered)
                lo, hi = V.effect_interval(data[n2][s], [data[n][s] for n in names], _stat(s),
                                           n_boot=n_boot, seed=EFFECT_SEED)
                res[e] = {"n2": vals[n2][s], "n2_se": se[n2][s], "ensemble_mean": float(ev.mean()),
                          "ensemble_latent_sd": latent, "margin": 0.5 * latent, "graphs": int(len(ev)),
                          "p": V.rank_p(vals[n2][s], ev, direction), "p_opposite": V.rank_p(vals[n2][s], ev, opposite),
                          "effect_interval": [lo, hi],
                          "n2_interval": [vals[n2][s] - 1.645 * se[n2][s], vals[n2][s] + 1.645 * se[n2][s]],
                          "ensemble_q05_q95": [float(np.quantile(ev, 0.05)), float(np.quantile(ev, 0.95))],
                          "values": ev.tolist()}
        if complete:
            pv[s] = {e: r["p"] for e, r in res.items()}
            pv_opp[s] = {e: r["p_opposite"] for e, r in res.items()}
        else:
            pv[s] = {e: 1.0 for e in ensembles}  # withheld: p = 1 keeps Holm's divisor at three
            pv_opp[s] = {e: 1.0 for e in ensembles}
        out["signals"][s] = res
        out["signals"][s + "_complete"] = complete
    holm, holm_opp = V.iut_holm(pv), V.iut_holm(pv_opp)
    for s in PRIMARY:
        if not out["signals"][s + "_complete"]:
            out["signals"][s + "_summary"] = {"p_max": 1.0, "p_holm": holm[s]["p_holm"], "overall": "withheld",
                                              "verdicts": {}}
            continue
        verdicts = {}
        for e, r in out["signals"][s].items():
            r["verdict"] = V.classify(holm[s]["p_holm"], holm_opp[s]["p_holm"], tuple(r["effect_interval"]),
                                      {"effect": r["margin"]}, EXPECTED[s], tuple(r["n2_interval"]), r["values"])
            verdicts[e] = r["verdict"]
        v = set(verdicts.values())
        out["signals"][s + "_summary"] = {
            "p_max": holm[s]["p_max"], "p_holm": holm[s]["p_holm"], "p_holm_opposite": holm_opp[s]["p_holm"],
            "verdicts": verdicts,
            "overall": ("distinctive relative to every ensemble" if v == {"distinctive"} else
                        "reversed against every ensemble" if v == {"reversed"} else "not distinctive")}
    # descriptive: the N2 variants' ranks against every ensemble, both directions
    out["ranks_descriptive"] = {}
    for d in descriptive:
        if d not in ok:
            continue
        out["ranks_descriptive"][d] = {s: {e: {"above": V.rank_p(vals[d][s], out["signals"][s][e]["values"], "above"),
                                               "below": V.rank_p(vals[d][s], out["signals"][s][e]["values"], "below")}
                                           for e in out["signals"][s]} for s in PRIMARY if ok[d][s] and out["signals"][s]}
    sec = {n: secondary(measures[n]) for n in use}
    out["secondary"] = {n: sec[n] for n in [n2, *descriptive] if n in sec}
    out["secondary"]["ensemble_mean_P2"] = {e: _t_interval([sec[n]["P2"] for n in names if n in sec])
                                            for e, names in ensembles.items()}
    out["secondary"]["ensembles"] = {e: {k: [float(np.nanquantile([sec[n][k] for n in names if n in sec], q))
                                             for q in (0.05, 0.5, 0.95)]
                                         for k in ("P2", "T0_mean", "T0_top_decile", "coverage", "abs_directional_M0",
                                                   "common_M0", "P4_decay")}
                                     for e, names in ensembles.items()}
    for e, names in ensembles.items():
        out["secondary"]["ensembles"][e]["P1_by_condition"] = {
            c: [float(np.nanquantile([sec[n]["P1_by_condition"].get(c, np.nan) for n in names if n in sec], q))
                for q in (0.05, 0.5, 0.95)] for c in RESPONSE_CONDITIONS}
    out["per_graph"] = {n: {"values": vals[n], "se": se[n], "valid": ok[n]} for n in use}
    return out
