"""The evolutionary E4-D's power analysis (docs/E4/E4-D-EVO-DESIGN.md v2.1 §4; Astra), simulated as the registered rule
reads. On the CPU.

    python scripts/e4d_evo_power.py                 # writes experiments/E4-two-minds/E4-D-evo/power.json
    python scripts/e4d_evo_power.py --from-record   # the same, from the calibration recorded in power.json

**What it simulates, per run, the whole rule** (Astra: final-population selection, finite blocks, heterogeneous
success):
- **a final population** of 32 strains, strain i's real-first probability 0.5 + g_r m_i: g_r the run's top gain (drawn
  by the scenario), m_i resampled from the pilot's profile (below);
- **its validation block** (64 mazes × 2 assignments; every strain); **the champion** is the best real-first share,
  exact ties at random (the registered rule breaks them by the final fitness, then the norm);
- **its own test block** (64 fresh mazes × 2); the run's gain is the champion's share − 0.5;
- **the maze effect:** a strain's probability on a maze is logistic(logit p + σ z), z normal per strain and maze, both
  assignments of a maze sharing it; σ = 0 (the pilot's champions show no overdispersion, below) and σ = 1. A maze's
  pair count then has an exact distribution (Gauss-Hermite over z), and a block's counts are multinomial over mazes;
- **the arm's reading** by the registered rule (`wormwars.e4.evo_stats.states`, δ = 0.15, one-sided 95% t bounds) on R
  runs drawn from a pool of simulated runs.

**The pilot's calibration** (exploratory, D270): the runs that match the formal arms, L at factor 0.25 (4) and F (4).
- **The profile:** m_i = (v_i − 0.5) / (v_c − 0.5), clipped to [−1, 1]; v the final population's validation shares, c
  the champion (256 values; validation noise included, which does not make it conservative: Astra, D272).
- **The success level:** the top gain at which the homogeneous scenario's mean champion test gain equals the 8 pilot
  champions' mean assessment gain.
- **The overdispersion:** the champions' per-maze pair shares against two independent trials.

**The scenarios,** each placed by bisection so that the mean champion test gain (the estimand's expectation) is μ:
- **H (homogeneous):** g_r normal around θ, SD 0.03, clipped to [0, 0.5];
- **M (mixture):** a run succeeds at the pilot's level with probability q, else g_r = 0 (no transfer);
- **U (spread):** g_r uniform on [0, 2θ], clipped to 0.5;
- **P (pilot):** the 8 pilot champions' assessment gains resampled (only at their own mean);
- **μ** from 0 to the pilot's level; μ = 0 is g_r = 0 for every run.

**Its approximations** (Astra, D272), each with a sensitivity case (`sensitivity` in the record):
- the champion's exact ties are broken at random, not by the final fitness and the norm. **Ties bounded** (Astra,
  D273): among the tied validation winners, the lowest and the highest true probability, at the main grid's θ for
  μ = 0.25 (σ = 0);
- the main grid draws each strain's profile independently and gives each strain its own maze effects, while a real
  population shares its mazes and its members are related (the pilot's within-population correlation of per-maze
  scores is recorded). **Structured:** whole pilot populations' profiles, a maze effect shared by every strain of a
  population (σ_s 1 and 1.5, bracketing the pilot's correlation), at μ = 0.25;
- failures sit at a gain of 0 and successes at the pilot's level. **Champion-level mixtures:** two-point mixtures of
  champion gains ((0, 0.5), (−0.10, 0.383), (0, 0.383)) at μ = 0.25, with a 128-trial test block;
- the logistic σ = 1 changes the marginal means and the mixture proportions too; it is not only added maze variance.

**The proposal it supports** (for the pre-registration, reviewed by both): the smallest R in the grid whose probability
of "practically relevant transfer found" is at least 0.80 at μ = δ + 0.10 = 0.25 in every scenario at σ = 0 and σ = 1
(Astra's spacing of 0.10 above the margin). μ = 0.20 (Astra's number, set against δ = 0.10) is reported beside. The
false rate of "practically relevant" at μ = δ is reported for every scenario (the t bound is approximate; M is
skewed). The GPU-hours of each R are projected from the pilot's timing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.e4 import evo_stats as ES  # noqa: E402

EXP = ROOT / "experiments" / "E4-two-minds" / "E4-D-evo"
PILOT = ROOT / "runs" / "e4d-evo" / "pilot"
OUT = EXP / "power.json"

SEED = 1_430_000
POP, MAZES = 32, 64
SIGMAS = (0.0, 1.0)
RS = (4, 6, 8, 12, 16, 20, 24, 32, 40, 48)
MUS = (0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35)
POOL = 40_000          # simulated runs per (scenario, μ, σ)
ARMS = 20_000          # simulated arms per (scenario, μ, σ, R)
BISECT_POOL = 20_000
H_SD = 0.03
TARGET, TARGET_ASTRA = 0.25, 0.20
SHARED = (1.0, 1.5)    # the structured sensitivity's shared maze effect: within-population correlations 0.23 and 0.40 bracket the pilot's 0.26-0.39
MIXTURES = ((0.0, 0.5), (-0.10, None), (0.0, None))  # None: the pilot's level
POWER = 0.80
G = 100


def calibration() -> dict:
    s = json.loads((EXP / "screen.json").read_text(encoding="utf-8"))
    f = json.loads((EXP / "f.json").read_text(encoding="utf-8"))
    pre = json.loads((EXP / "precheck.json").read_text(encoding="utf-8"))
    chosen = float(s["factor"])
    runs = [("L", r) for r in s["runs"] if float(r["factor"]) == chosen] + [("F", r) for r in f["runs"]]
    profile, per_run, pair, corr = [], [], [], []
    for arm, r in runs:
        z = np.load(PILOT / f"{arm}-run{int(r['run']):03d}-assessment.npz", allow_pickle=False)
        v = z["validation"].mean(1)
        c = int(r["champion_index"])
        if not np.isclose(z["assessment"][0].mean(), r["assessment"]["real_first_all"]):
            raise ValueError(f"{arm} run {r['run']}: the assessment file disagrees with the record")
        profile += np.clip((v - 0.5) / (v[c] - 0.5), -1, 1).tolist()
        corr.append(_within_correlation(z["validation"]))
        pair.append(z["assessment"][0].tolist())
        per_run.append({"arm": arm, "run": int(r["run"]), "champion_validation": float(v[c]),
                        "population_validation_mean": float(v.mean()),
                        "champion_assessment": float(r["assessment"]["real_first_all"])})
    pair = np.asarray(pair)
    p = pair.mean(1, keepdims=True)
    observed = float(((pair - p) ** 2).mean())
    binomial = float((p * (1 - p) / 2).mean())
    return {"source": "the pilot (D270): L at factor %g and F; validation and assessment per maze" % chosen,
            "runs": per_run, "profile": [round(x, 6) for x in profile],
            "champion_pair_shares": pair.tolist(),
            "overdispersion": {"observed_variance": observed, "two_independent_trials": binomial,
                               "ratio": observed / binomial},
            "pilot_mean_gain": float(np.mean([r["champion_assessment"] for r in per_run]) - 0.5),
            "within_population_correlation": corr,
            "precheck_timing": {"seconds_per_generation_W8": float(pre["timing"]["8"]["seconds_per_generation"]),
                                "runs": int(pre["timing"]["8"]["composition"][0]) // int(s["registered"]["ga"]["population"])},
            "timing": {"screen_runs": len(s["runs"]), "screen_training_seconds": float(s["training_seconds"]),
                       "screen_seconds": float(s["seconds"]), "f_runs": len(f["runs"]),
                       "f_training_seconds": float(f["training_seconds"]), "f_seconds": float(f["seconds"]),
                       "generations": int(s["registered"]["screen"]["G"])}}


def _within_correlation(V) -> float:
    """The mean Pearson correlation of per-maze scores between pairs of a population's strains (constant rows
    skipped)."""
    V = np.asarray(V, dtype=np.float64)
    V = V[V.std(1) > 0]
    if len(V) < 2:
        return float("nan")
    C = np.corrcoef(V)
    return float(C[np.triu_indices(len(V), 1)].mean())


def shares(p, sigma, rng):
    """Real-first shares over MAZES mazes × 2 assignments, for probabilities p [..]."""
    if sigma == 0:
        return rng.binomial(2 * MAZES, p) / (2 * MAZES)
    # a maze's pair count (0, 1 or 2 real-first) has an exact distribution given p and σ (Gauss-Hermite over z);
    # the block's counts are multinomial over its mazes
    z, w = np.polynomial.hermite_e.hermegauss(48)
    w = w / w.sum()
    pc = np.clip(p, 1e-9, 1 - 1e-9)
    q = 1 / (1 + np.exp(-((np.log(pc) - np.log1p(-pc))[..., None] + sigma * z)))
    probs = np.stack([((1 - q) ** 2) @ w, (2 * q * (1 - q)) @ w, (q ** 2) @ w], -1)
    n = rng.multinomial(MAZES, probs / probs.sum(-1, keepdims=True))
    return (n[..., 1] + 2 * n[..., 2]) / (2 * MAZES)


def simulate_runs(g, profile, sigma, rng, chunk=4000, ties="random"):
    """The champions' test gains for runs with top gains g; the validation winners' exact ties at random, or to the
    lowest ("worst") or highest ("best") true probability."""
    out = np.empty(len(g))
    for lo in range(0, len(g), chunk):
        gg = g[lo:lo + chunk]
        p = 0.5 + gg[:, None] * rng.choice(profile, size=(len(gg), POP))
        v = shares(p, sigma, rng)
        if ties == "random":
            c = np.argmax(v + rng.random(v.shape) * 1e-9, axis=1)
        else:
            top = v == v.max(axis=1, keepdims=True)
            c = (np.argmin(np.where(top, p, np.inf), axis=1) if ties == "worst"
                 else np.argmax(np.where(top, p, -np.inf), axis=1))
        out[lo:lo + chunk] = shares(p[np.arange(len(gg)), c], sigma, rng) - 0.5
    return out


def tops(kind, theta, rng, n, success):
    if kind == "H":
        return np.clip(theta + H_SD * rng.standard_normal(n), 0, 0.5)
    if kind == "M":
        return np.where(rng.random(n) < theta, success, 0.0)
    if kind == "U":
        return np.clip(rng.uniform(0, 2 * theta, n), 0, 0.5)
    raise ValueError(kind)


def mean_gain(kind, theta, profile, sigma, success, seed):
    rng = np.random.default_rng(seed)
    return float(simulate_runs(tops(kind, theta, rng, BISECT_POOL, success), profile, sigma, rng).mean())


def place(kind, mu, profile, sigma, success, seed):
    """θ whose mean champion test gain is μ (common random numbers across the bisection)."""
    lo, hi = (0.0, 1.0) if kind == "M" else (0.0, 0.5)
    if mean_gain(kind, hi, profile, sigma, success, seed) < mu:
        return None
    for _ in range(30):
        mid = (lo + hi) / 2
        if mean_gain(kind, mid, profile, sigma, success, seed) < mu:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def arm_rates(pool, rng):
    rates = {}
    for R in RS:
        D = pool[rng.integers(0, len(pool), size=(ARMS, R))]
        st = ES.states(D)
        p = np.bincount(st, minlength=len(ES.STATES)) / ARMS
        rates[str(R)] = {ES.STATES[i]: float(p[i]) for i in range(len(ES.STATES))}
        rates[str(R)]["mc_se_max"] = float(np.sqrt(0.25 / ARMS))
    return rates


def hours(n_runs, cal, *, conservative):
    """GPU-hours for n_runs batched over G generations, plus their evaluation."""
    t = cal["timing"]
    if conservative:  # the precheck's measured per-run rate (16 runs at W = 8), no intercept, times 1.5
        pc = cal["precheck_timing"]
        per_gen = 1.5 * pc["seconds_per_generation_W8"] / pc["runs"] * n_runs
    else:  # a line through the pilot's two batches (16 runs, 4 runs)
        b = (t["screen_training_seconds"] - t["f_training_seconds"]) / t["generations"] / (t["screen_runs"] - t["f_runs"])
        a = t["f_training_seconds"] / t["generations"] - b * t["f_runs"]
        per_gen = a + b * n_runs
    evaluation = max((t["screen_seconds"] - t["screen_training_seconds"]) / t["screen_runs"],
                     (t["f_seconds"] - t["f_training_seconds"]) / t["f_runs"]) * 2  # the formal controls double it
    return (per_gen * G + evaluation * n_runs) / 3600


def simulate_structured(g, profiles, shared, rng, chunk=2000):
    """As `simulate_runs`, with whole populations' profiles and a maze effect shared by a population's strains on its
    validation block; also the realised within-population correlation."""
    out, corr = np.empty(len(g)), []
    for lo in range(0, len(g), chunk):
        gg = g[lo:lo + chunk]
        n = len(gg)
        m = profiles[rng.integers(0, len(profiles), n)]
        p = np.clip(0.5 + gg[:, None] * m, 1e-9, 1 - 1e-9)
        lp = np.log(p) - np.log1p(-p)
        q = 1 / (1 + np.exp(-(lp[..., None] + shared * rng.standard_normal((n, 1, MAZES)))))
        y = rng.binomial(2, q) / 2  # [n, POP, MAZES] per-maze pair shares
        v = y.mean(-1)
        c = np.argmax(v + rng.random(v.shape) * 1e-9, axis=1)
        if lo == 0:
            corr = [_within_correlation(y[i]) for i in range(min(200, n))]
        pc = lp[np.arange(n), c]
        qt = 1 / (1 + np.exp(-(pc[:, None] + shared * rng.standard_normal((n, MAZES)))))
        out[lo:lo + chunk] = rng.binomial(2, qt).sum(-1) / (2 * MAZES) - 0.5
    return out, float(np.nanmean(corr))


def sensitivity(cal, profile, success, rng, results) -> dict:
    out = {"structured": [], "mixtures": [], "ties": []}
    for kind in ("H", "M", "U"):
        theta = next(r["theta"] for r in results if r["scenario"] == kind and r["sigma"] == 0.0
                     and r["mu_target"] == TARGET and r["feasible"])
        for ties in ("worst", "best"):
            g = tops(kind, theta, rng, POOL, success)
            pool = simulate_runs(g, np.asarray(profile), 0.0, rng, ties=ties)
            out["ties"].append({"scenario": kind, "ties": ties, "theta": theta, "mu_realised": float(pool.mean()),
                                "run_sd": float(pool.std()), "rates": arm_rates(pool, rng)})
            print(f"ties {ties} {kind} realised {pool.mean():.4f} R=32 "
                  f"{out['ties'][-1]['rates']['32'][ES.STATES[0]]:.3f}", flush=True)
    profiles = np.asarray(profile).reshape(-1, POP)
    for shared in SHARED:
        for kind in ("H", "M", "U"):
            seed = SEED + 9000 + int(10 * shared) * 10 + "HMU".index(kind)
            lo, hi = 0.0, (1.0 if kind == "M" else 0.5)
            for _ in range(20):
                mid = (lo + hi) / 2
                r = np.random.default_rng(seed)
                m = simulate_structured(tops(kind, mid, r, 4000, success), profiles, shared, r)[0].mean()
                lo, hi = (mid, hi) if m < TARGET else (lo, mid)
            theta = (lo + hi) / 2
            pool, corr = simulate_structured(tops(kind, theta, rng, POOL // 2, success), profiles, shared, rng)
            out["structured"].append({"scenario": kind, "shared_sigma": shared, "theta": theta,
                                      "mu_realised": float(pool.mean()), "run_sd": float(pool.std()),
                                      "within_population_correlation": corr, "rates": arm_rates(pool, rng)})
            print(f"structured {kind} shared {shared} realised {pool.mean():.4f} corr {corr:.3f} R=32 "
                  f"{out['structured'][-1]['rates']['32'][ES.STATES[0]]:.3f}", flush=True)
    for a, b in MIXTURES:
        b = cal["pilot_mean_gain"] if b is None else b
        q = (TARGET - a) / (b - a)
        truth = np.where(rng.random(POOL) < q, b, a)
        pool = rng.binomial(2 * MAZES, 0.5 + truth) / (2 * MAZES) - 0.5
        out["mixtures"].append({"failure_gain": a, "success_gain": b, "success_share": q,
                                "mu_realised": float(pool.mean()), "rates": arm_rates(pool, rng)})
        print(f"mixture ({a}, {b:.3f}) q {q:.3f} R=32 {out['mixtures'][-1]['rates']['32'][ES.STATES[0]]:.3f}",
              flush=True)
    return out


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--from-record", action="store_true")
    a = ap.parse_args()
    cal = json.loads(OUT.read_text(encoding="utf-8"))["calibration"] if a.from_record else calibration()
    profile = np.asarray(cal["profile"])
    target = cal["pilot_mean_gain"]
    # the success level: the homogeneous top gain (SD 0) whose champions' mean test gain is the pilot's
    lo, hi = 0.0, 0.5
    for _ in range(30):
        mid = (lo + hi) / 2
        rng = np.random.default_rng(SEED)
        m = float(simulate_runs(np.full(BISECT_POOL, mid), profile, 0.0, rng).mean())
        lo, hi = (mid, hi) if m < target else (lo, mid)
    success = (lo + hi) / 2

    rng = np.random.default_rng(SEED + 1)
    results = []
    for sigma in SIGMAS:
        for kind in ("H", "M", "U"):
            for k, mu in enumerate(MUS):
                seed = SEED + 1000 * (1 + SIGMAS.index(sigma)) + 100 * "HMU".index(kind) + k
                theta = 0.0 if mu == 0 else place(kind, mu, profile, sigma, success, seed)
                if theta is None:
                    results.append({"scenario": kind, "sigma": sigma, "mu_target": mu, "feasible": False})
                    continue
                g = np.zeros(POOL) if mu == 0 else tops(kind, theta, rng, POOL, success)
                pool = simulate_runs(g, profile, sigma, rng)
                results.append({"scenario": kind, "sigma": sigma, "mu_target": mu, "feasible": True, "theta": theta,
                                "mu_realised": float(pool.mean()), "run_sd": float(pool.std()),
                                "rates": arm_rates(pool, rng)})
                print(f"sigma {sigma} {kind} mu {mu:.2f} theta {theta:.4f} realised {pool.mean():.4f} "
                      f"P(practical) R=16 {results[-1]['rates']['16'][ES.STATES[0]]:.3f}", flush=True)
        # P: the pilot's own champions, resampled
        pool = np.asarray([r["champion_assessment"] - 0.5 for r in cal["runs"]])
        results.append({"scenario": "P", "sigma": None, "mu_target": float(pool.mean()), "feasible": True,
                        "mu_realised": float(pool.mean()), "run_sd": float(pool.std()),
                        "rates": arm_rates(pool, rng)}) if sigma == SIGMAS[0] else None

    def practical(scen, sigma, mu, R):
        for r in results:
            if r["scenario"] == scen and r["sigma"] == sigma and r["mu_target"] == mu and r["feasible"]:
                return r["rates"][str(R)][ES.STATES[0]]
        return None

    table = {}
    for R in RS:
        row = {}
        for sigma in SIGMAS:
            for kind in ("H", "M", "U"):
                row[f"{kind} sigma={sigma:g}"] = {"mu=0.25": practical(kind, sigma, TARGET, R),
                                                  "mu=0.20": practical(kind, sigma, TARGET_ASTRA, R),
                                                  "false at mu=delta": practical(kind, sigma, ES.DELTA, R)}
        row["hours_L_plus_F4"] = hours(R + 4, cal, conservative=False)
        row["hours_L_plus_F4_conservative"] = hours(R + 4, cal, conservative=True)
        row["hours_S"] = hours(R, cal, conservative=False)
        row["hours_S_conservative"] = hours(R, cal, conservative=True)
        table[str(R)] = row
    sens = sensitivity(cal, profile, success, np.random.default_rng(SEED + 2), results)
    ok = [R for R in RS if all(v["mu=0.25"] is not None and v["mu=0.25"] >= POWER
                               for k, v in table[str(R)].items() if isinstance(v, dict))]
    doc = {"what": "the evolutionary E4-D's power analysis (design v2.1 §4); exploratory input to the pre-registration",
           "script": "scripts/e4d_evo_power.py", "seed": SEED, "rule": "wormwars.e4.evo_stats (delta %g, one-sided "
           "%g t bounds)" % (ES.DELTA, ES.ALPHA), "population": POP, "mazes_per_block": MAZES, "pool": POOL,
           "arms": ARMS, "h_sd": H_SD, "G": G, "success_top_gain": success, "calibration": cal,
           "results": results, "summary": table, "sensitivity": sens,
           "proposal": {"rule": "the smallest R with P(practically relevant) >= %g at mu = %g in every scenario at "
                                "sigma 0 and 1" % (POWER, TARGET), "R": ok[0] if ok else None}}
    OUT.write_text(json.dumps(doc, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({R: {k: v for k, v in row.items()} for R, row in table.items()}, indent=1))
    print("proposal R =", ok[0] if ok else None)


if __name__ == "__main__":
    main()
