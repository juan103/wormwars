"""E3c's power analysis (draft 2; both reviewers of draft 1, D207), simulated as the readings are computed. On the
CPU.

    python scripts/e3c_power.py      # writes experiments/E3-ab-organism/E3c/power.json

**What it simulates:** Q1 (S-mod − S-dense) and Q2 (P-joint − S-mod) jointly. One S-mod sample enters both, as
it will.
- **The labels:** both contrasts from fixed 97.5% Welch intervals, with the dual margin, Q1's floor guard and
  the failed-run rule ("approximate").
- **How:** the decisions are vectorized for speed. Every run checks them, label for label, against the
  registered `wormwars.e3.e3c_stats.readings` on random trials from every scenario (Astra's check, kept).

**The scenarios, centred on the true arm means** (Astra: draft 1's failure mixtures shifted the means):
- **S-mod's mean** is 6.7 (1 − p_mod) + f p_mod: successes at 6.7 visits per wey, failures at level f.
- **S-dense's mean** is S-mod's − Δ₁, and P-joint's is S-mod's + Δ₂. Each arm's successful component is
  placed so that its mixture has exactly that mean.
- **Δ₁ and Δ₂:** −1, −0.5, 0, 0.5, 1 visit.
- **The failure probabilities** (S-mod, S-dense): (0, 0), (1/8, 1/8), (1/4, 1/4), (1/8, 0), (0, 1/8).
- **The failure level:** f = N(2.3, 0.3²), P-sel's failed level. N(1.8, 0.2²) is a sensitivity case.
- **The S arms' spread:** 0.06 visits (the pilot's), with 0.4 as a sensitivity case.
- **P-joint:**
  - E3b-1's T-F d SD (0.177), times 1, 0.75 or 1.5;
  - normal, or T-F's empirical shape. Resampling 8 atoms gives ties, so that case is anti-conservative and is
    a sensitivity case only (Fable).
- **The run counts:** S arms 8 or 6 (the last cut), P-joint always 8.
- **P-fixed's test mean:** 5.0, with 4.82 and 5.84 as sensitivity cases.

**For each scenario:**
- each label's rate;
- the confirmatory rates: rejected and not approximate;
- the joint false-claim rate: any wrong-direction or null rejection over both contrasts, confirmatory only;
- false margin classifications;
- Monte Carlo standard errors.

5 000 trials per scenario, seed 20 261 006. P-sel's binomial chances are given beside.
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
TRIALS, SEED, CHECKS = 5000, 20_261_006, 40


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
        approx = (fails[arms[0]] + fails[arms[1]]) > 0
        lab = np.where(approx, np.char.add("approximate: ", lab.astype(str)), lab.astype(str)).astype(object)
        if q == "Q1":
            lab = np.where(q1_read, lab, "not read: both at the floor").astype(object)
            rej = rej & q1_read
            approx = approx & q1_read
        res[q] = {"label": lab, "rejected": rej, "approximate": approx, "est": est}
    return res, (smod, sdense, pj, dd)


def summarise(res, d1, d2, seed_mean):
    m_lo, m_hi = S.margins(seed_mean)
    out, joint_false = {}, np.zeros(len(res["Q1"]["label"]), dtype=bool)
    for q, true in (("Q1", d1 / seed_mean), ("Q2", d2 / seed_mean)):
        r = res[q]
        labs, counts = np.unique(r["label"].astype(str), return_counts=True)
        conf = r["rejected"] & ~r["approximate"]
        wrong = conf & ((true == 0) | (np.sign(r["est"]) != np.sign(true)))
        joint_false |= wrong
        lab = r["label"].astype(str)
        unq = np.char.replace(lab, "approximate: ", "")
        false_beyond = np.char.endswith(unq, "beyond the margin") & (abs(true) <= m_hi) & ~r["approximate"]
        false_nrd = (lab == "no relevant difference") & (abs(true) >= m_lo)
        rate = lambda m: {"rate": float(m.mean()), "mc_se": float(np.sqrt(m.mean() * (1 - m.mean()) / len(m)))}  # noqa: E731
        out[q] = {"labels": {k: float(c / len(lab)) for k, c in zip(labs, counts)},
                  "confirmatory_rejection": rate(conf), "any_rejection": rate(r["rejected"]),
                  "approximate": rate(r["approximate"]), "false_confirmatory_claim": rate(wrong),
                  "false_beyond_the_margin": rate(false_beyond), "false_no_relevant_difference": rate(false_nrd)}
    out["joint_false_confirmatory_claim"] = {"rate": float(joint_false.mean()),
                                             "mc_se": float(np.sqrt(joint_false.mean() * (1 - joint_false.mean()) / len(joint_false)))}
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
    return len(idx)


def main():
    rng = np.random.default_rng(SEED)
    checked, rows = 0, []
    base = dict(sd_s=0.06, f=(2.3, 0.3), pj_sd_mult=1.0, shape="normal", seed_mean=5.0)
    plan = []
    for n_s, (p_mod, p_dense), d1, d2 in itertools.product(
            (8, 6), ((0, 0), (0.125, 0.125), (0.25, 0.25), (0.125, 0), (0, 0.125)), (-1.0, -0.5, 0.0, 0.5, 1.0),
            (-1.0, -0.5, 0.0, 0.5, 1.0)):
        plan.append({**base, "case": "base", "n_s": n_s, "p_mod": p_mod, "p_dense": p_dense, "d1": d1, "d2": d2})
    for kind, change in (("s_spread_0.4", {"sd_s": 0.4}), ("failure_level_1.8", {"f": (1.8, 0.2)}),
                         ("p_joint_sd_x0.75", {"pj_sd_mult": 0.75}), ("p_joint_sd_x1.5", {"pj_sd_mult": 1.5}),
                         ("p_joint_empirical", {"shape": "empirical"}), ("seed_4.82", {"seed_mean": 4.82}),
                         ("seed_5.84", {"seed_mean": 5.84})):
        for (p_mod, p_dense), d1, d2 in itertools.product(((0, 0), (0.125, 0.125), (0.25, 0.25)), (0.0, 1.0),
                                                          (-1.0, 0.0, 1.0)):
            plan.append({**base, **change, "case": kind, "n_s": 8, "p_mod": p_mod, "p_dense": p_dense,
                         "d1": d1, "d2": d2})
    for sc in plan:
        kw = {k: v for k, v in sc.items() if k != "case"}
        res, draws = simulate(rng, **kw)
        checked += check_against_registered(res, draws, sc["seed_mean"], CHECKS, rng)
        rows.append({**{k: (list(v) if isinstance(v, tuple) else v) for k, v in sc.items()},
                     **summarise(res, sc["d1"], sc["d2"], sc["seed_mean"])})
    p_sel = {f"{p:.3f}": {str(k): float(stats.binom.pmf(k, 4, p)) for k in range(5)} for p in (1 / 8, 1 / 3)}
    doc = {"trials": TRIALS, "seed": SEED, "s_success": S_SUCCESS, "w2_alone": W2, "p_joint_runs": PJ_N,
           "tf_d": TF_D.tolist(), "tf_sd": TF_SD, "margins_at_seed_5": dict(zip(("m_lo", "m_hi"), S.margins(5.0))),
           "checked_against_registered_readings": checked, "scenarios": rows, "p_sel_working_of_4": p_sel}
    OUT.write_text(json.dumps(doc, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} scenarios; {checked} trials matched the registered readings")


if __name__ == "__main__":
    main()
