"""Experiment 03's report (design v3.2, D053), as a pure function of the saved per-graph measures,
so it can be smoke-tested on pilot data with a stand-in for N2 before any N2 run.

For each primary signal (P1, P3, P4) and each ensemble:
- the per-graph value and its measurement SE (P1, P4: bootstrap over genomes of a ratio of
  means; P3: crossed genome x world variance components after removing the world profile
  shared by every graph);
- the ensemble's latent SD, sqrt(var(values) - mean SE^2), and margin 0.5 latent SD;
- N2's one-sided exact rank p in the expected and in the opposite direction;
- the 90% joint-bootstrap interval of N2 minus the ensemble mean, and N2's own 90% interval;
- the verdict per ensemble.
Across ensembles: the maximum p, then Holm across the three signals.
"""

from __future__ import annotations

import numpy as np

from . import verdict as V

PRIMARY = ("P1", "P3", "P4")
EXPECTED = {"P1": "above", "P3": "above", "P4": "above"}


def _ratio(num, den):
    return float(np.mean(num) / np.mean(den))


def per_genome(m: dict) -> dict:
    """The raw per-genome (and per-world) arrays each primary signal is built from."""
    f = m["fitness"]
    h = m["history"]["raw_turn"]
    r = m["response"]["M0"]
    return {"P1": {"num": np.asarray(r["directional_turn_signed_raw"], float),
                   "den": np.asarray(r["common_turn_raw"], float)},
            "P3": np.asarray(f["T1-M0"], float) - np.asarray(f["T1const-M0"], float),
            "P4": {"num": np.abs(np.asarray(h["final"], float)),
                   "den": np.abs(np.asarray(h["steady_contrast"], float))}}


def value(signal: str, data) -> float:
    if signal == "P3":
        return float(np.mean(data))
    return _ratio(data["num"], data["den"])


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


def ratio_se(num, den, n_boot=1000, seed=0) -> float:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(num), (n_boot, len(num)))
    return float(np.std(num[idx].mean(1) / den[idx].mean(1), ddof=1))


def build(measures: dict, n2: str, ensembles: dict, n_boot: int = 1000) -> dict:
    """`measures`: {graph name: saved measures}. `ensembles`: {ensemble: [graph names]}."""
    data = {name: per_genome(m) for name, m in measures.items()}
    common = np.mean([np.asarray(d["P3"]).mean(0) for d in data.values()], axis=0)
    se = {name: {"P1": ratio_se(d["P1"]["num"], d["P1"]["den"]), "P3": crossed_se(d["P3"], common),
                 "P4": ratio_se(d["P4"]["num"], d["P4"]["den"])} for name, d in data.items()}
    vals = {name: {s: value(s, d[s]) for s in PRIMARY} for name, d in data.items()}
    out = {"n2": n2, "signals": {}}
    pvals, pvals_opp = {}, {}
    for s in PRIMARY:
        direction = EXPECTED[s]
        opposite = "below" if direction == "above" else "above"
        res = {}
        for e, names in ensembles.items():
            ev = np.array([vals[n][s] for n in names if np.isfinite(vals[n][s])])
            mse = float(np.mean([se[n][s] ** 2 for n in names]))
            latent = float(np.sqrt(max(np.var(ev, ddof=1) - mse, 0.0)))
            lo, hi = V.effect_interval(data[n2][s], [data[n][s] for n in names], _stat(s), n_boot=n_boot, seed=1)
            # N2's own 90% measurement interval: its value +- 1.645 SE
            n2_int = (vals[n2][s] - 1.645 * se[n2][s], vals[n2][s] + 1.645 * se[n2][s])
            res[e] = {"n2": vals[n2][s], "n2_se": se[n2][s], "ensemble_mean": float(ev.mean()),
                      "ensemble_latent_sd": latent, "margin": 0.5 * latent, "graphs": int(len(ev)),
                      "p": V.rank_p(vals[n2][s], ev, direction), "p_opposite": V.rank_p(vals[n2][s], ev, opposite),
                      "effect_interval": [lo, hi], "n2_interval": list(n2_int),
                      "ensemble_q05_q95": [float(np.quantile(ev, 0.05)), float(np.quantile(ev, 0.95))]}
        out["signals"][s] = res
        pvals[s] = {e: r["p"] for e, r in res.items()}
        pvals_opp[s] = {e: r["p_opposite"] for e, r in res.items()}
    holm, holm_opp = V.iut_holm(pvals), V.iut_holm(pvals_opp)
    for s in PRIMARY:
        verdicts = {}
        for e, r in out["signals"][s].items():
            r["verdict"] = V.classify(holm[s]["p_holm"], holm_opp[s]["p_holm"], tuple(r["effect_interval"]),
                                      {"effect": r["margin"]}, EXPECTED[s], tuple(r["n2_interval"]),
                                      [vals[n][s] for n in ensembles[e]])
            verdicts[e] = r["verdict"]
        v = set(verdicts.values())
        overall = ("distinctive relative to every ensemble" if v == {"distinctive"} else
                   "reversed against every ensemble" if v == {"reversed"} else "not distinctive")
        out["signals"][s + "_summary"] = {"p_max": holm[s]["p_max"], "p_holm": holm[s]["p_holm"],
                                          "p_holm_opposite": holm_opp[s]["p_holm"], "verdicts": verdicts,
                                          "overall": overall}
    out["per_graph"] = {n: {"values": vals[n], "se": se[n]} for n in measures}
    return out
