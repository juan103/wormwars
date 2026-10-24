"""M4d's readings (docs/memory/M4D-PLAN.md): per host and arm, the share of all drawn genomes classified separate states;
D_TI and D_TR with 90% intervals resampling the hosts (genomes are not resampled again), hulled with the Student-t
interval when the coverage simulation says so; the fixed reading with its single-host guard, its conservative
envelope over the unresolved genomes, and the descriptive contrasts and measures. Before reading, every input is
checked through m4d.verify_run. The stage `coverage` simulates the interval's coverage before the run.
Writes runs/memory-m4d/readings.json (or coverage.json).
Usage: python scripts/memory_m4/m4d_read.py [coverage]"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
ROOT = Path(__file__).resolve().parents[2]
MARGIN, B, SEED_BOOT, LEVEL = 0.004, 2000, 20261221, 0.90
HOST_GUARD = 0.01  # an exclusion needs every host's own difference below this (Astra, round 2; 0.01: Fable, round 3)
SEED_COVERAGE, SCREENS, MIN_COVERAGE = 20261222, 2000, 0.85
MIN_HOSTS = 10  # fewer hosts (a smoke) are never read
SEPARATE, UNRESOLVED = (0, 1), 4
LIMIT = (", as a mean across these ten hosts (a response confined to a minority of host graphs may be missed)")
READINGS = ("C3's block carries the switch into fresh hosts beyond rewired copies at its degrees",
            "A transplant benefit; an advantage of C3's wiring of m or more over rewired copies ruled out" + LIMIT,
            "No transplant effect of m or more" + LIMIT,
            "Unresolved")
SINGLE_HOST = "Unresolved (a single host responds)"
BY_UNRESOLVED = "Unresolved (the unresolved genomes decide it)"


def boot_interval(d, idx):
    """The 5th and 95th percentiles of the mean of the host differences d over the resampled host index rows idx."""
    m = d[idx].mean(1)
    return float(np.percentile(m, 5)), float(np.percentile(m, 95))


def t_interval(d):
    n = len(d)
    half = stats.t.ppf(0.5 + LEVEL / 2, n - 1) * d.std(ddof=1) / np.sqrt(n)
    return float(d.mean() - half), float(d.mean() + half)


def interval(d, idx, use_t):
    """The bootstrap interval, or with use_t the hull of it and the Student-t interval."""
    lo, hi = boot_interval(d, idx)
    if use_t:
        tl, th = t_interval(d)
        lo, hi = min(lo, tl), max(hi, th)
    return lo, hi


def reading(ti, tr, m=MARGIN):
    """The plan's reading from the intervals (lower, upper) of D_TI and D_TR."""
    if ti[0] > m and tr[0] > m:
        return READINGS[0]
    if ti[0] > m and tr[1] < m:
        return READINGS[1]
    if ti[1] < m:
        return READINGS[2]
    return READINGS[3]


def guarded(ti, tr, ti_max, tr_max, m=MARGIN, guard=HOST_GUARD):
    """The reading, with an exclusion (the second or third) replaced by SINGLE_HOST when one host's own difference in
    the excluded contrast reaches the guard: ten hosts cannot rule out a response confined to one of them."""
    r = reading(ti, tr, m)
    if (r == READINGS[1] and tr_max >= guard) or (r == READINGS[2] and ti_max >= guard):
        return SINGLE_HOST
    return r


def diffs(sep, unres, n, a, b, where="main"):
    """Each host's p_a - p_b; 'low' and 'high' assign every unresolved genome against a (counted in b only) or for it
    (counted in a only)."""
    sa, sb = np.asarray(sep[a], float), np.asarray(sep[b], float)
    if where == "low":
        sb = sb + np.asarray(unres[b])
    elif where == "high":
        sa = sa + np.asarray(unres[a])
    return (sa - sb) / n


def envelope(lo_d, hi_d, idx, use_t):
    """The conservative interval over every assignment of the unresolved genomes, each host's difference anywhere in
    [lo_d, hi_d]: the bootstrap percentiles rise with every host's difference, so their extremes are at lo_d and hi_d;
    the Student-t lower bound is concave and its upper bound convex in the differences, so their extremes are at
    corners of the box, all of which are checked (Astra, round 2)."""
    lo, _ = boot_interval(lo_d, idx)
    _, hi = boot_interval(hi_d, idx)
    if use_t:
        for corner in itertools.product(*zip(lo_d, hi_d)):
            tl, th = t_interval(np.array(corner))
            lo, hi = min(lo, tl), max(hi, th)
    return lo, hi


def contrast(sep, unres, n, idx, use_t, a, b):
    d = diffs(sep, unres, n, a, b)
    return {"D": float(d.mean()), "interval": list(interval(d, idx, use_t)), "per_host": d.tolist(),
            "host_max": float(d.max())}


def read(sep, unres, n, use_t, seed=SEED_BOOT):
    """The reading and its robustness; sep and unres hold, per arm, each host's counts of separate-states and
    unresolved genomes out of n."""
    h = len(sep["T"])
    if h < MIN_HOSTS:
        raise SystemExit(f"{h} hosts: fewer than {MIN_HOSTS} are never read")
    idx = np.random.default_rng(seed).integers(0, h, (B, h))
    ti = contrast(sep, unres, n, idx, use_t, "T", "I")
    tr = contrast(sep, unres, n, idx, use_t, "T", "R")
    main = guarded(ti["interval"], tr["interval"], ti["host_max"], tr["host_max"])
    env = {}
    for a, b in (("T", "I"), ("T", "R")):
        env[f"D_{a}{b}"] = list(envelope(diffs(sep, unres, n, a, b, "low"), diffs(sep, unres, n, a, b, "high"), idx,
                                         use_t))
    env_reading = guarded(env["D_TI"], env["D_TR"], float(diffs(sep, unres, n, "T", "I", "high").max()),
                          float(diffs(sep, unres, n, "T", "R", "high").max()))
    robust = env_reading == main or main.startswith("Unresolved")
    out = {"D_TI": ti, "D_TR": tr, "reading_before_bounds": main, "envelope": env, "envelope_reading": env_reading,
           "robust": robust, "reading": main if robust else BY_UNRESOLVED, "t_widened": use_t}
    out["descriptive"] = {f"D_{a}{b}": contrast(sep, unres, n, idx, use_t, a, b)
                          for a, b in (("T", "Rr"), ("T", "P"), ("R", "D"), ("D", "I"), ("R", "I"), ("T+G", "T"))
                          if a in sep and b in sep}
    return out


# ------------------------------------------------------------------------------------------------------------ coverage
def reference_rates():
    """M2's 30 reference graphs: separate-states genomes (both subclasses) per 1024 drawn, from the committed records."""
    rates = []
    for f in sorted((ROOT / "runs" / "memory-m2-census").glob("*__7600.json")):
        r = json.load(open(f))
        if r.get("role") == "reference":
            rates.append(sum(g["class"].startswith("separate states") for g in r["genomes"]) / len(r["all"]["a"]))
    if len(rates) != 30:
        raise SystemExit(f"expected M2's 30 reference graphs, found {len(rates)}")
    return np.array(rates)


SCENARIOS = ("fixed", "uniform", "sparse", "ensemble", "raised base")
PAIRINGS = ("independent", "disjoint", "nested")


def shifts(kind, delta, rng, hosts=10):
    """Per-host shifts with population mean delta: the same everywhere; uniform on [0, 2 delta]; 10 delta in each
    host with probability 0.1 (Astra's sparse case); 2.5 delta in the hosts of two of the five ensembles (two hosts
    each); fixed on a base raised by 0.01 in both arms (as a dense block might raise R's); or 10 delta in one host
    chosen at random (Fable's case for the guard, round 3)."""
    if kind in ("fixed", "raised base"):
        return np.full(hosts, delta)
    if kind == "uniform":
        return rng.uniform(0, 2 * delta, hosts)
    if kind == "sparse":
        return np.where(rng.random(hosts) < 0.1, 10 * delta, 0.0)
    if kind == "one host":
        return np.where(np.arange(hosts) == rng.integers(hosts), hosts * delta, 0.0)
    if kind == "ensemble":
        ens = np.repeat(np.arange(hosts // 2), 2)
        return np.where(np.isin(ens, rng.choice(hosts // 2, 2, replace=False)), 2.5 * delta, 0.0)
    raise ValueError(kind)


def paired_counts(pb, pt, pairing, n, rng):
    """Per host, the comparator's and T's counts of n genomes with marginal rates pb and pt: independent binomials, or
    paired genomes whose switches are as disjoint as the rates allow (the largest variance of T - comparator) or
    nested (the smallest) (Astra, round 3: the pairing's covariance is not assumed)."""
    if pairing == "independent":
        return rng.binomial(n, pt), rng.binomial(n, pb)
    both = np.maximum(0.0, pb + pt - 1) if pairing == "disjoint" else np.minimum(pb, pt)
    probs = np.stack([both, pb - both, pt - both, 1 - pb - pt + both], 1)
    c = np.array([rng.multinomial(n, q / q.sum()) for q in probs])
    return c[:, 0] + c[:, 2], c[:, 0] + c[:, 1]


def simulate(rates, kind, delta, rng, screens=SCREENS, n=1024, hosts=10, pairing="independent"):
    """Simulated screens: host base rates drawn from `rates`, the comparator at the base and T at the base plus the
    scenario's shift, paired as `pairing` says. Returns the bootstrap's and the widened interval's coverage of delta, and the shares of screens whose widened
    interval reads an excluding upper bound (< MARGIN) with and without the single-host guard, and a lower bound
    above MARGIN."""
    hit = hit_t = excl = excl_g = pos = 0
    for _ in range(screens):
        base = rng.choice(rates, hosts) + (0.01 if kind == "raised base" else 0.0)
        ct, cb = paired_counts(base, np.clip(base + shifts(kind, delta, rng, hosts), 0, 1), pairing, n, rng)
        d = (ct - cb) / n
        idx = rng.integers(0, hosts, (B, hosts))
        lo, hi = boot_interval(d, idx)
        hit += lo <= delta <= hi
        lo, hi = interval(d, idx, True)
        hit_t += lo <= delta <= hi
        excl += hi < MARGIN
        excl_g += hi < MARGIN and d.max() < HOST_GUARD
        pos += lo > MARGIN
    return {"scenario": kind, "delta": delta, "pairing": pairing, "coverage": hit / screens, "coverage_widened": hit_t / screens,
            "excluding": excl / screens, "excluding_guarded": excl_g / screens, "lower_above_margin": pos / screens}


def stage_coverage(out):
    rng = np.random.default_rng(SEED_COVERAGE)
    rates = reference_rates()
    res = [simulate(rates, kind, dl, rng) for dl in (MARGIN, 0.015) for kind in SCENARIOS]
    res += [simulate(rates, kind, dl, rng) for dl, kind in ((0.0, "fixed"), (2 * MARGIN, "sparse"))]
    res += [simulate(rates, kind, MARGIN, rng, pairing=pr) for kind in ("fixed", "raised base")
            for pr in ("disjoint", "nested")]  # round 3 (Astra)
    res += [simulate(rates, "one host", dl, rng) for dl in (0.0012, 0.0009)]  # one host at 0.012 or 0.009 (Fable)
    res += [simulate(rates, "raised base", 0.0, rng)]  # the guard's false fires on a raised base (Fable, round 4)
    use_t = any(r["coverage"] < MIN_COVERAGE for r in res if r["delta"] > 0)
    rec = {"scenarios": res, "min_coverage": MIN_COVERAGE, "use_t": use_t, "host_guard": HOST_GUARD,
           "reference_rates": rates.tolist()}
    json.dump(rec, open(out / "coverage.json", "w"), indent=1)
    for r in res:
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    print(f"use the Student-t widening: {use_t}")
    return rec


# ------------------------------------------------------------------------------------------------------------ the run
def load_counts(verified, arms, n):
    import m4d
    sep = {a: [] for a in arms}
    unres = {a: [] for a in arms}
    recs = {}
    for v in verified:
        r = v["rec"]
        for a in arms:
            f = m4d.panel_file(r, a)
            if not f.exists():
                raise SystemExit(f"missing panel {f.name}: the run is incomplete and is not read")
            p = json.load(open(f))
            m4d.validate(p, r, a, v["arms"][a][1])
            sep[a].append(sum(x in SEPARATE for x in p["class"]))
            unres[a].append(p["class"].count(UNRESOLVED))
            recs[(r["name"], a)] = p
    return sep, unres, recs


def describe(recs, hosts, arms, floor):
    """Per arm, pooled over hosts: the write and read measures (not read)."""
    out = {}
    for a in arms:
        ps = [recs[(r["name"], a)] for r in hosts]
        wc = [x for p in ps for x in p["write_core"] if x is not None]
        sq = [x for p in ps for x in p["write_sq"]]
        sepro = [rd for p in ps for c_, rd in zip(p["class"], p["readout_difference"]) if c_ in SEPARATE]
        above = [c_ for p in ps for c_, a_ in zip(p["class"], p["a"]) if a_ >= floor and c_ in SEPARATE]
        out[a] = {"write_sq_median": float(np.median(sq)), "write_core_median": float(np.median(wc)) if wc else None,
                  "write_zero": sum(x is None for p in ps for x in p["write_core"]),
                  "readout_difference_separate_median": float(np.median(sepro)) if sepro else None,
                  "silent_share_above_floor": (sum(x == 1 for x in above) / len(above)) if above else None,
                  "invalid_panels": [p["name"] for p in ps if not p["valid"]],
                  "unresolved_over_5pct": [p["name"] for p in ps if p["class"].count(UNRESOLVED) > 0.05 * p["n"]]}
    return out


def main():
    import m4d
    out = m4d.OUT
    verified = m4d.verify_run()  # every input checked first (Fable, Astra, round 2)
    hosts = [v["rec"] for v in verified]
    sep, unres, recs = load_counts(verified, m4d.ARMS, m4d.N_PANEL)
    if m4d.SMOKE or len(hosts) < MIN_HOSTS:  # a smoke is checked, never read (Astra, round 3)
        json.dump({"reading": "not read (a smoke, or fewer than ten hosts)", "counts": {"separate": sep,
                   "unresolved": unres, "hosts": [r["name"] for r in hosts], "n": m4d.N_PANEL}},
                  open(out / "readings.json", "w"), indent=1)
        print(f"not read: {len(hosts)} host(s); every check passed; separate {sep}, unresolved {unres}")
        return
    cov = json.load(open(out / "coverage.json"))
    res = read(sep, unres, m4d.N_PANEL, cov["use_t"])
    res["counts"] = {"separate": sep, "unresolved": unres, "hosts": [r["name"] for r in hosts], "n": m4d.N_PANEL}
    res["hosts_T_over_R"] = int(sum(t > r for t, r in zip(sep["T"], sep["R"])))
    res["hosts_T_over_I"] = int(sum(t > i for t, i in zip(sep["T"], sep["I"])))
    res["by_ensemble"] = {e: {a: sum(s for s, r in zip(sep[a], hosts) if r["ensemble"] == e) for a in m4d.ARMS}
                          for e in m4d.ENSEMBLES}
    res["measures"] = describe(recs, hosts, m4d.ARMS, m4d.c.START_FLOOR)
    json.dump(res, open(out / "readings.json", "w"), indent=1)
    print(f"reading: {res['reading']}")
    print(f"D_TI {res['D_TI']['D']:+.4f} {res['D_TI']['interval']}; D_TR {res['D_TR']['D']:+.4f} {res['D_TR']['interval']}")


def test_rules():
    m = MARGIN
    assert reading((m + 1e-6, 1), (m + 1e-6, 1)) == READINGS[0]
    assert reading((m, 1), (m + 1e-6, 1)) == READINGS[3]  # lower bound must exceed the margin strictly
    assert reading((m + 1e-6, 1), (-1, m - 1e-6)) == READINGS[1]
    assert reading((m + 1e-6, 1), (-1, m)) == READINGS[3]
    assert reading((-1, m - 1e-6), (-1, 1)) == READINGS[2]
    assert reading((-1, m), (-1, 1)) == READINGS[3]
    assert reading((0, 1), (0, 1)) == READINGS[3]
    g = HOST_GUARD
    assert guarded((m + 1e-6, 1), (-1, m - 1e-6), 0.0, g - 1e-6) == READINGS[1]
    assert guarded((m + 1e-6, 1), (-1, m - 1e-6), 0.0, g) == SINGLE_HOST
    assert guarded((-1, m - 1e-6), (-1, 1), g - 1e-6, 1.0) == READINGS[2]
    assert guarded((-1, m - 1e-6), (-1, 1), g, 0.0) == SINGLE_HOST
    assert guarded((m + 1e-6, 1), (m + 1e-6, 1), 1.0, 1.0) == READINGS[0]  # a positive reading is never guarded


if __name__ == "__main__":
    if sys.argv[1:] == ["coverage"]:
        import m4d
        stage_coverage(m4d.OUT)
    else:
        main()
