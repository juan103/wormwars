"""E3c's power analysis, simulated as the readings will be computed (`wormwars/e3/e3c_stats.py`). On the CPU.

    python scripts/e3c_power.py      # writes experiments/E3-ab-organism/E3c/power.json

**What it simulates:** Q1 (S-mod − S-dense) and Q2 (P-joint − S-mod), jointly, so that one S-mod sample enters
both contrasts as it will. Each contrast is a Welch test with Holm, labelled by the dual margin; Q1 has its
floor guard. The inputs are from the pilot and E3b-1, per both reviewers (D204):
- **The S arms:**
  - normal around 6.7 visits per wey, block-independent: coverers score alike on every block (PILOT.md);
  - run-to-run SD 0.06 (the pilot's), 0.2 or 0.4 (three runs bound it weakly);
  - a failure mixture: each run stays near the floor with probability 0, 1/8 or 2/8, at N(2.3, 0.3²), P-sel's
    failed level. The pilot saw 0 of 6.
- **P-joint:**
  - E3b-1's T-F cohort, d SD 0.177 around its mean (8 runs; `evaluate.json`);
  - normal, and that cohort's empirical shape;
  - its mean set so that Q2's true difference is −1 to +1 visits.
- **The seed's mean on the test block:** 5.0 (between the pilot block's 4.82 and E3b-1's 5.84), with 4.82
  and 5.84 as sensitivity checks. It fixes the d unit and the relative margin.
- **The run counts:** 8 per arm, and 6 (the last cut).

**Also:** P-sel's chance of k working selectors in 4 runs, for success rates of 1/8 (E3a) and 1/3 (the
pilot). 2 000 trials per scenario, seed 20 261 005.
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
S_MEAN, FAIL_MEAN, FAIL_SD, W2 = 6.7, 2.3, 0.3, 1.72
TRIALS, SEED = 2000, 20_261_005


def s_arm(rng, n, mean, sd, p_fail):
    x = mean + sd * rng.standard_normal(n)
    fail = rng.random(n) < p_fail
    x[fail] = FAIL_MEAN + FAIL_SD * rng.standard_normal(int(fail.sum()))
    return x


def p_joint(rng, n, mean_visits, seed_mean, shape):
    z = rng.standard_normal(n) if shape == "normal" else rng.choice(TF_Z, size=n, replace=True)
    d = (mean_visits - seed_mean) / seed_mean + TF_SD * z
    return seed_mean * (1 + d)


def scenario(rng, *, n, sd, p_fail, delta1, delta2, shape, seed_mean):
    counts = {"Q1": {}, "Q2": {}}
    for _ in range(TRIALS):
        smod = s_arm(rng, n, S_MEAN, sd, p_fail)
        sdense = s_arm(rng, n, S_MEAN - delta1, sd, p_fail)
        pj = p_joint(rng, n, S_MEAN + delta2, seed_mean, shape)
        d = {k: (v - seed_mean) / seed_mean for k, v in (("s_mod", smod), ("s_dense", sdense), ("p_joint", pj))}
        r = S.readings(d=d, seed_mean=seed_mean, visits={"s_mod": smod.mean(), "s_dense": sdense.mean()}, w2_alone=W2)
        for q in ("Q1", "Q2"):
            counts[q][r[q]["label"]] = counts[q].get(r[q]["label"], 0) + 1
    return {q: {k: v / TRIALS for k, v in sorted(c.items())} for q, c in counts.items()}


def main():
    rng = np.random.default_rng(SEED)
    grid = []
    for n, sd, p_fail, delta1, delta2, shape in itertools.product(
            (8, 6), (0.06, 0.2, 0.4), (0.0, 0.125, 0.25), (0.0, 0.25, 0.5, 1.0), (-1.0, -0.5, 0.0, 0.5, 1.0),
            ("normal", "empirical")):
        if shape == "empirical" and (sd != 0.06 or n != 8):
            continue  # the shape is checked on the base case only
        grid.append({"n": n, "sd": sd, "p_fail": p_fail, "delta1_visits": delta1, "delta2_visits": delta2,
                     "p_joint_shape": shape, "seed_mean": 5.0,
                     **scenario(rng, n=n, sd=sd, p_fail=p_fail, delta1=delta1, delta2=delta2, shape=shape,
                                seed_mean=5.0)})
    sens = []
    for seed_mean in (4.82, 5.84):
        for delta1, delta2 in itertools.product((0.0, 0.5), (-1.0, 0.0, 1.0)):
            sens.append({"n": 8, "sd": 0.06, "p_fail": 0.0, "delta1_visits": delta1, "delta2_visits": delta2,
                         "p_joint_shape": "normal", "seed_mean": seed_mean,
                         **scenario(rng, n=8, sd=0.06, p_fail=0.0, delta1=delta1, delta2=delta2, shape="normal",
                                    seed_mean=seed_mean)})
    p_sel = {f"{p:.3f}": {str(k): float(stats.binom.pmf(k, 4, p)) for k in range(5)} for p in (1 / 8, 1 / 3)}
    doc = {"trials": TRIALS, "seed": SEED, "s_mean": S_MEAN, "fail": [FAIL_MEAN, FAIL_SD], "w2_alone": W2,
           "tf_d": TF_D.tolist(), "tf_sd": TF_SD, "margins_at_seed_5": dict(zip(("m_lo", "m_hi"), S.margins(5.0))),
           "grid": grid, "seed_sensitivity": sens, "p_sel_working_of_4": p_sel}
    OUT.write_text(json.dumps(doc, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(grid)} scenarios + {len(sens)} sensitivity")


if __name__ == "__main__":
    main()
