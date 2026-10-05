"""E3c's power analysis (draft 3; both reviewers of drafts 1 and 2, D207-D208), simulated as the readings are
computed. On the CPU.

    python scripts/e3c_power.py      # writes experiments/E3-ab-organism/E3c/power.json

**What it simulates:** Q1 (S-mod − S-dense) and Q2 (P-joint − S-mod), jointly. One S-mod sample enters both, as
it will.
- **The confirmatory decision:** an exact two-sided permutation test per contrast, at 0.025, over every split of
  the pooled runs.
- **The approximate margin labels:** fixed 97.5% Welch intervals with the dual margin.
- **Also applied:** Q1's floor guard and the failed-run counts.
- **How:** the decisions are vectorized. Every run checks the margin labels and the exact labels against the
  registered `wormwars.e3.e3c_stats.readings`, label for label, on random trials from every scenario.

**The scenarios, centred on the true arm means:**
- **S-mod's mean** is 6.7 (1 − p_mod) + f p_mod: S-mod's successes at 6.7 visits per wey, failures at level f.
- **S-dense's mean** is S-mod's − Δ₁, and P-joint's is S-mod's + Δ₂. S-dense's successful component is placed
  so that its mixture has exactly that mean, so it is not 6.7 when the failure rates differ.
- **Δ₁ and Δ₂:** −1, −0.5, 0, 0.5, 1 visit.
- **The failure probabilities** (S-mod, S-dense): (0, 0), (1/8, 1/8), (1/4, 1/4), (1/8, 0), (0, 1/8).
- **The failure level:** f = N(2.3, 0.3²), P-sel's failed level, of which about 8% lies above W2 alone + 1.
  N(1.8, 0.2²) is a sensitivity case.
- **The S arms' spread:** 0.06 visits (the pilot's), with 0.4 as a sensitivity case.
- **P-joint:**
  - E3b-1's T-F d SD (0.177), times 1, 0.75 or 1.5;
  - normal, or T-F's empirical shape (8 atoms; ties; a sensitivity case only);
  - always 8 runs.
- **The S arms' run count:** 8, or 6 (the last cut).
- **P-fixed's test mean:** 5.0, with 4.82 and 5.84 as sensitivity cases.

**For each scenario:**
- **the exact test:** its rejection rate; its false rejections where the two arms' distributions are identical
  (Q1 with Δ₁ = 0 and equal failure rates); its wrong-direction rejections;
- **the margin labels:** each label's rate, and the joint rate of any false label assertion over both
  contrasts (Astra). That counts a wrong-direction or null rejection, a false "beyond", a false "within" and a
  false "no relevant difference";
- **the joint coverage** of the two 97.5% intervals;
- **the analytic arm means;**
- **Monte Carlo standard errors.**

5 000 trials per scenario, seed 20 261 009. P-sel's binomial chances are given beside.
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.e3 import e3c_stats as S  # noqa: E402

OUT = ROOT / "experiments" / "E3-ab-organism" / "E3c" / "power.json"
TF_D = np.array([0.38528428093645484, 0.29774247491638794, 0.43010033444816054, 0.4919732441471572,
                 0.11304347826086956, 0.5493311036789298, 0.6110367892976588, 0.1710702341137124])  # E3b-1 G/d/tf
TF_Z = (TF_D - TF_D.mean()) / TF_D.std(ddof=0)
TF_SD = float(TF_D.std(ddof=1))
S_SUCCESS, W2, PJ_N = 6.7, 1.72, 8
TRIALS, SEED, CHECKS = 5000, 20_261_009, 40
APPROX = "approximate (model-based): "


def mixture(rng, trials, n, mean, sd, p, f_mean, f_sd):
    """[trials, n] draws from successes N(mu, sd) and failures N(f_mean, f_sd) with probability p, mu set so the
    mixture's mean is `mean`."""
    mu = (mean - p * f_mean) / (1 - p) if p < 1 else mean
    x = mu + sd * rng.standard_normal((trials, n))
    if p > 0:
        fail = rng.random((trials, n)) < p
        x[fail] = f_mean + f_sd * rng.standard_normal(int(fail.sum()))
    return x


def vwelch(x, y, level):
    nx, ny = x.shape[1], y.shape[1]
    vx, vy = x.var(1, ddof=1) / nx, y.var(1, ddof=1) / ny
    se = np.sqrt(vx + vy)
    df = (vx + vy) ** 2 / (vx ** 2 / (nx - 1) + vy ** 2 / (ny - 1))
    est = x.mean(1) - y.mean(1)
    q = stats.t.ppf(1 - (1 - level) / 2, df)
    return est, est - q * se, est + q * se


_SPLITS = {}


def splits(n, nx):
    """The 0/1 assignment matrix of every split of n pooled runs into nx and n − nx."""
    if (n, nx) not in _SPLITS:
        idx = np.array(list(itertools.combinations(range(n), nx)))
        a = np.zeros((len(idx), n), dtype=np.float64)
        a[np.arange(len(idx))[:, None], idx] = 1.0
        _SPLITS[(n, nx)] = a
    return _SPLITS[(n, nx)]


def vpermutation_p(x, y, chunk=400):
    """The exact two-sided permutation p-value per trial, as `e3c_stats.permutation_p`."""
    nx, ny = x.shape[1], y.shape[1]
    pooled = np.concatenate([x, y], 1)
    a = splits(nx + ny, nx)
    obs = np.abs(x.mean(1) - y.mean(1))
    out = np.empty(len(x))
    for i in range(0, len(x), chunk):
        sx = a @ pooled[i:i + chunk].T  # [splits, chunk]
        tot = pooled[i:i + chunk].sum(1)
        diffs = sx / nx - (tot - sx) / ny
        out[i:i + chunk] = (np.abs(diffs) >= obs[i:i + chunk] - 1e-12).mean(0)
    return out


def vlabels(est, lo, hi, m_lo, m_hi, a, b):
    rej = (lo > 0) | (hi < 0)
    pos = est > 0
    l = np.where(pos, lo, -hi)
    h = np.where(pos, hi, -lo)
    side = np.where(pos, a, b)
    out = np.where(l > m_hi, np.char.add(side, " better, beyond the margin"),
                   np.where(h < m_lo, np.char.add(side, " better, within the margin"),
                            np.char.add(side, " better, margin unresolved")))
    out = np.where(rej, out, np.where((lo > -m_lo) & (hi < m_lo), "no relevant difference", "unclear"))
    return out.astype(object), rej


def simulate(rng, *, n_s, sd_s, p_mod, p_dense, f, d1, d2, pj_sd_mult, shape, seed_mean, trials=TRIALS):
    f_mean, f_sd = f
    m_mod = S_SUCCESS * (1 - p_mod) + f_mean * p_mod
    smod = mixture(rng, trials, n_s, m_mod, sd_s, p_mod, f_mean, f_sd)
    sdense = mixture(rng, trials, n_s, m_mod - d1, sd_s, p_dense, f_mean, f_sd)
    z = rng.standard_normal((trials, PJ_N)) if shape == "normal" else rng.choice(TF_Z, size=(trials, PJ_N))
    pj = seed_mean * (1 + (m_mod + d2 - seed_mean) / seed_mean + TF_SD * pj_sd_mult * z)
    dd = {k: (v - seed_mean) / seed_mean for k, v in (("s_mod", smod), ("s_dense", sdense), ("p_joint", pj))}
    m_lo, m_hi = S.margins(seed_mean)
    fails = {k: (v <= W2 + S.FLOOR_MARGIN).sum(1) for k, v in (("s_mod", smod), ("s_dense", sdense), ("p_joint", pj))}
    q1_read = np.maximum(smod.mean(1), sdense.mean(1)) > W2 + S.FLOOR_MARGIN
    res = {}
    for q, (x, y, arms) in {"Q1": (dd["s_mod"], dd["s_dense"], ("s_mod", "s_dense")),
                            "Q2": (dd["p_joint"], dd["s_mod"], ("p_joint", "s_mod"))}.items():
        est, lo, hi = vwelch(x, y, S.LEVEL)
        lab, rej = vlabels(est, lo, hi, m_lo, m_hi, *S.NAMES[q])
        lab = np.char.add(APPROX, lab.astype(str)).astype(object)
        a, b = S.NAMES[q]
        exact = vpermutation_p(x, y) <= S.ALPHA / 2
        exact_lab = np.where(exact, np.where(x.mean(1) > y.mean(1), f"distributions differ (exact test); observed mean higher for {a}",
                                              f"distributions differ (exact test); observed mean higher for {b}"),
                             "no difference detected (exact)").astype(object)
        read = q1_read if q == "Q1" else np.ones(trials, dtype=bool)
        lab = np.where(read, lab, "not read: both at the floor").astype(object)
        exact_lab = np.where(read, exact_lab, "not read").astype(object)
        res[q] = {"label": lab, "rejected": rej & read, "est": est, "lo": lo, "hi": hi, "read": read,
                  "exact": exact & read, "exact_label": exact_lab,
                  "failed_present": (fails[arms[0]] + fails[arms[1]]) > 0}
    return res, (smod, sdense, pj, dd)


def arm_means(sc) -> dict:
    """The analytic arm means of a scenario (visits per wey)."""
    m_mod = S_SUCCESS * (1 - sc["p_mod"]) + sc["f"][0] * sc["p_mod"]
    return {"s_mod": m_mod, "s_dense": m_mod - sc["d1"], "p_joint": m_mod + sc["d2"]}


def false_assertion(label, true, m_lo, m_hi) -> bool:
    """Whether one approximate margin label asserts something false about the true contrast (in d)."""
    lab = label.replace(APPROX, "")
    if lab.startswith("not read") or lab == "unclear":
        return False
    if lab == "no relevant difference":
        return abs(true) >= m_lo
    sign = 1 if lab.split(" better")[0] in (S.NAMES["Q1"][0], S.NAMES["Q2"][0]) else -1
    if true == 0 or np.sign(true) != sign:
        return True
    if lab.endswith("beyond the margin"):
        return abs(true) <= m_hi
    if lab.endswith("within the margin"):
        return abs(true) >= m_lo
    return False


def _rate(m):
    m = np.asarray(m, dtype=bool)
    r = float(m.mean())
    return {"rate": r, "mc_se": float(np.sqrt(r * (1 - r) / len(m)))}


def summarise(res, d1, d2, seed_mean, identical_q1: bool) -> dict:
    m_lo, m_hi = S.margins(seed_mean)
    n = len(res["Q1"]["label"])
    out, joint_false, covered = {}, np.zeros(n, dtype=bool), np.ones(n, dtype=bool)
    for q, true in (("Q1", d1 / seed_mean), ("Q2", d2 / seed_mean)):
        r = res[q]
        lab = r["label"].astype(str)
        labs, counts = np.unique(lab, return_counts=True)
        fa = np.array([false_assertion(x, true, m_lo, m_hi) for x in lab])
        joint_false |= fa
        covered &= ~r["read"] | ((r["lo"] <= true) & (true <= r["hi"]))
        ex = {"rejection": _rate(r["exact"]),
              "wrong_direction": _rate(r["exact"] & (true != 0) & (np.sign(r["est"]) != np.sign(true)))}
        if q == "Q1" and identical_q1:
            ex["false_rejection_identical_distributions"] = _rate(r["exact"])
        out[q] = {"labels": {k: float(c / n) for k, c in zip(labs, counts)}, "welch_rejection": _rate(r["rejected"]),
                  "false_label_assertion": _rate(fa), "exact": ex, "failed_runs_present": _rate(r["failed_present"])}
    out["joint_false_label_assertion"] = _rate(joint_false)
    out["joint_interval_coverage"] = _rate(covered)
    return out


def check_against_registered(res, draws, seed_mean, k, rng) -> int:
    smod, sdense, pj, dd = draws
    idx = rng.choice(len(smod), size=k, replace=False)
    for i in idx:
        r = S.readings(d={a: dd[a][i] for a in dd}, seed_mean=seed_mean,
                       run_visits={"s_mod": smod[i], "s_dense": sdense[i], "p_joint": pj[i]}, w2_alone=W2)
        for q in ("Q1", "Q2"):
            if r[q]["label"] != res[q]["label"][i]:
                raise AssertionError(f"vectorized {res[q]['label'][i]!r} != registered {r[q]['label']!r} ({q}, trial {i})")
            if r[q]["exact"]["label"] != res[q]["exact_label"][i]:
                raise AssertionError(f"vectorized {res[q]['exact_label'][i]!r} != registered "
                                     f"{r[q]['exact']['label']!r} ({q}, trial {i})")
    return len(idx)


def plan() -> list:
    base = dict(sd_s=0.06, f=(2.3, 0.3), pj_sd_mult=1.0, shape="normal", seed_mean=5.0)
    out = []
    for n_s, (p_mod, p_dense), d1, d2 in itertools.product(
            (8, 6), ((0, 0), (0.125, 0.125), (0.25, 0.25), (0.125, 0), (0, 0.125)), (-1.0, -0.5, 0.0, 0.5, 1.0),
            (-1.0, -0.5, 0.0, 0.5, 1.0)):
        out.append({**base, "case": "base", "n_s": n_s, "p_mod": p_mod, "p_dense": p_dense, "d1": d1, "d2": d2})
    for kind, change in (("s_spread_0.4", {"sd_s": 0.4}), ("failure_level_1.8", {"f": (1.8, 0.2)}),
                         ("p_joint_sd_x0.75", {"pj_sd_mult": 0.75}), ("p_joint_sd_x1.5", {"pj_sd_mult": 1.5}),
                         ("p_joint_empirical", {"shape": "empirical"}), ("seed_4.82", {"seed_mean": 4.82}),
                         ("seed_5.84", {"seed_mean": 5.84})):
        for (p_mod, p_dense), d1, d2 in itertools.product(((0, 0), (0.125, 0.125), (0.25, 0.25)), (0.0, 1.0),
                                                          (-1.0, 0.0, 1.0)):
            out.append({**base, **change, "case": kind, "n_s": 8, "p_mod": p_mod, "p_dense": p_dense,
                        "d1": d1, "d2": d2})
    return out


def main():
    rng = np.random.default_rng(SEED)
    checked, rows = 0, []
    for sc in plan():
        kw = {k: v for k, v in sc.items() if k != "case"}
        res, draws = simulate(rng, **kw)
        checked += check_against_registered(res, draws, sc["seed_mean"], CHECKS, rng)
        identical = sc["d1"] == 0 and sc["p_mod"] == sc["p_dense"]
        rows.append({**{k: (list(v) if isinstance(v, tuple) else v) for k, v in sc.items()}, "arm_means": arm_means(sc),
                     **summarise(res, sc["d1"], sc["d2"], sc["seed_mean"], identical)})
    p_sel = {f"{p:.3f}": {str(k): float(stats.binom.pmf(k, 4, p)) for k in range(5)} for p in (1 / 8, 1 / 3)}
    doc = {"trials": TRIALS, "seed": SEED, "s_success": S_SUCCESS, "w2_alone": W2, "p_joint_runs": PJ_N,
           "tf_d": TF_D.tolist(), "tf_sd": TF_SD, "margins_at_seed_5": dict(zip(("m_lo", "m_hi"), S.margins(5.0))),
           "checked_against_registered_readings": checked, "scenarios": rows, "p_sel_working_of_4": p_sel}
    OUT.write_text(json.dumps(doc, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} scenarios; {checked} trials matched the registered readings")


if __name__ == "__main__":
    main()
