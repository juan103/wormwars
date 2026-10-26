"""M4e's readings (docs/memory/M4E-PLAN.md): per host and arm, the share of its 1024 genomes (two draws of 512)
classified separate states by the merged classes (the second pass's where it ran, unless the audit fails); the two
primary contrasts with 95% intervals (the hull of the host bootstrap and the Student-t interval), each read in two
fields, direction and size, with the single-host guard and the conservative envelope over the still-unresolved
genomes; the secondary contrasts, the dose model and the descriptions. Every input is checked through m4e.verify_run
first. The stage `coverage` simulates the intervals before the run.

Writes runs/memory-m4e/readings.json (or coverage.json).
Usage: python scripts/memory_m4/m4e_read.py [coverage]
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
ROOT = Path(__file__).resolve().parents[2]
B, SEED_BOOT, LEVEL = 2000, 20261541, 0.95  # 95% each; Bonferroni over the two primaries gives 90% jointly
BENCH, MARGIN, HOST_GUARD = 0.001, 0.004, 0.01
SEED_COVERAGE, SCREENS, MIN_COVERAGE = 20261542, 1000, 0.90
SEED_DOSE = 20261543
MIN_HOSTS = 10
SEPARATE, OSCILLATION, UNRESOLVED, FADING = (0, 1), 3, 4, 2
LIMIT = ", as a mean across these ten hosts (a response confined to a minority of host graphs may be missed)"
PRIMARY = {"weight": ("U_HH", "U_HL"), "count": ("U_HH", "U_LH")}
SECONDARY = (("U_LH", "U_LL"), ("U_HL", "U_LL"), ("U_LL", "I"), ("U_HX", "U_HH"), ("W", "U_HH"), ("K", "W"),
             ("T", "K"), ("T", "I"))
BY_UNRESOLVED = "unresolved (the unresolved genomes decide it)"
SINGLE_HOST = "size unresolved (a single host responds)"


# ------------------------------------------------------------------------------------------------------------ intervals
def boot_interval(d, idx, level=LEVEL):
    m = d[idx].mean(1)
    q = 100 * (1 - level) / 2
    return float(np.percentile(m, q)), float(np.percentile(m, 100 - q))


def t_interval(d, level=LEVEL):
    n = len(d)
    half = stats.t.ppf(0.5 + level / 2, n - 1) * d.std(ddof=1) / np.sqrt(n)
    return float(d.mean() - half), float(d.mean() + half)


def hull(d, idx, level=LEVEL):
    lo, hi = boot_interval(d, idx, level)
    tl, th = t_interval(d, level)
    return min(lo, tl), max(hi, th)


def envelope(lo_d, hi_d, idx, level=LEVEL):
    """The conservative hull over every assignment of the unresolved genomes (M4d's): the bootstrap at the box's two
    ends, the Student-t interval at all its corners."""
    lo, _ = boot_interval(lo_d, idx, level)
    _, hi = boot_interval(hi_d, idx, level)
    for corner in itertools.product(*zip(lo_d, hi_d)):
        tl, th = t_interval(np.array(corner), level)
        lo, hi = min(lo, tl), max(hi, th)
    return lo, hi


# ------------------------------------------------------------------------------------------------------------- fields
def direction(iv):
    lo, hi = iv
    if lo > 0:
        return "raises"
    if hi < 0:
        return "lowers"
    return "direction unresolved"


def size(iv, host_absmax, exclusions_ok=True):
    """'at least 0.001' (either sign), or the exclusion at 0.004 (guarded, and only if the coverage allows it), or
    'size unresolved'. Both can hold; the result lists every field that holds."""
    lo, hi = iv
    out = []
    if lo > BENCH or hi < -BENCH:
        out.append("at least 0.001")
    if -MARGIN < lo and hi < MARGIN and exclusions_ok:
        out.append(SINGLE_HOST if host_absmax >= HOST_GUARD else "no effect of 0.004 or more" + LIMIT)
    return out or ["size unresolved"]


def diffs(sep, unres, n, a, b, where="main"):
    """Each host's p_a - p_b; 'low' counts every unresolved genome against a (in b only), 'high' for it (in a only)."""
    sa, sb = np.asarray(sep[a], float), np.asarray(sep[b], float)
    if where == "low":
        sb = sb + np.asarray(unres[b])
    elif where == "high":
        sa = sa + np.asarray(unres[a])
    return (sa - sb) / n


def contrast(sep, unres, n, idx, a, b, exclusions_ok=True):
    """One contrast: its mean, hull interval, fields, envelope and the envelope's fields."""
    d = diffs(sep, unres, n, a, b)
    iv = hull(d, idx)
    lo_d, hi_d = diffs(sep, unres, n, a, b, "low"), diffs(sep, unres, n, a, b, "high")
    env = envelope(lo_d, hi_d, idx)
    absmax = float(np.abs(d).max())
    env_absmax = float(max(np.abs(lo_d).max(), np.abs(hi_d).max()))
    f_dir, f_size = direction(iv), size(iv, absmax, exclusions_ok)
    e_dir, e_size = direction(env), size(env, env_absmax, exclusions_ok)
    both = [x for x in f_size if x in e_size and x != "size unresolved"]  # a size sub-field holding on both stands
    return {"D": float(d.mean()), "interval": list(iv), "per_host": d.tolist(), "host_absmax": absmax,
            "envelope": list(env), "direction": f_dir if e_dir == f_dir else BY_UNRESOLVED,
            "size": f_size if e_size == f_size else (both or [BY_UNRESOLVED]), "direction_before_bounds": f_dir,
            "size_before_bounds": f_size, "envelope_direction": e_dir, "envelope_size": e_size}


# ------------------------------------------------------------------------------------------------------------ the dose
def poisson_slope(counts, n, x, iters=100):
    """MLE of log mu = alpha + beta x + log n for counts out of n (Newton's method). None when it does not exist or is
    not found: no switch at all, or every switch at the largest x or every one at the smallest (the slope then
    diverges; a single switching arm at an interior x has a finite slope, Astra, round 2), a singular step, a
    non-finite value, or no convergence."""
    y, x = np.asarray(counts, float), np.asarray(x, float)
    pos = x[y > 0]
    if len(pos) == 0 or np.all(pos == x.max()) or np.all(pos == x.min()):
        return None
    X = np.stack([np.ones_like(x), x], 1)
    beta = np.array([np.log(y.sum() / (n * len(y))), 0.0])
    for _ in range(iters):
        mu = n * np.exp(X @ beta)
        grad = X.T @ (y - mu)
        hess = X.T @ (X * mu[:, None])
        try:
            step = np.linalg.solve(hess, grad)
        except np.linalg.LinAlgError:
            return None
        beta = beta + step
        if not np.all(np.isfinite(beta)):
            return None
        if np.abs(step).max() < 1e-10:
            return beta
    return None


def dose_model(sep, n, s2, u_arms, others):
    """Per host, the Poisson slope of the U arms' counts on log S2; the mean slope with its hull interval; then each
    other arm's deviation from its host's curve at its own S2 (observed minus predicted share), averaged over hosts."""
    slopes, dev = [], {a: [] for a in others}
    skipped, outside = [], {a: 0 for a in others}
    for h in range(len(sep["I"])):
        beta = poisson_slope([sep[a][h] for a in u_arms], n, [np.log(s2[a][h]) for a in u_arms])
        if beta is None:
            skipped.append(h)
            continue
        slopes.append(beta[1])
        lo, hi = min(s2[a][h] for a in u_arms), max(s2[a][h] for a in u_arms)
        for a in others:
            dev[a].append(sep[a][h] / n - float(np.exp(beta[0] + beta[1] * np.log(s2[a][h]))))
            outside[a] += not (lo <= s2[a][h] <= hi)
    out = {"hosts_without_a_slope": skipped, "slopes": [float(s) for s in slopes],
           "hosts_where_the_arm_lies_outside_the_U_range": outside}
    if len(slopes) >= 2:
        sl = np.array(slopes)
        ix = np.random.default_rng(SEED_DOSE).integers(0, len(sl), (B, len(sl)))
        out["mean_slope"] = float(sl.mean())
        out["slope_interval"] = list(hull(sl, ix))
        out["deviation"] = {a: {"mean": float(np.mean(v)), "interval": list(hull(np.array(v), ix))} for a, v in dev.items()}
    return out


# ------------------------------------------------------------------------------------------------------------ coverage
def m4d_rates():
    """M4d's per-host block-arm shares (D, R, Rr, P, T) as plausible base rates, from its committed readings."""
    r = json.load(open(ROOT / "runs" / "memory-m4d" / "readings.json"))
    n = r["counts"]["n"]
    return np.array([x / n for a in ("D", "R", "Rr", "P", "T") for x in r["counts"]["separate"][a]])


SCENARIOS = ("fixed", "uniform", "sparse", "ensemble", "raised base")


def shifts(kind, delta, rng, hosts=10):
    if kind in ("fixed", "raised base"):
        return np.full(hosts, delta)
    if kind == "uniform":
        return rng.uniform(0, 2 * delta, hosts)
    if kind == "sparse":
        return np.where(rng.random(hosts) < 0.1, 10 * delta, 0.0)
    if kind == "ensemble":
        ens = np.repeat(np.arange(hosts // 2), 2)
        return np.where(np.isin(ens, rng.choice(hosts // 2, 2, replace=False)), 2.5 * delta, 0.0)
    raise ValueError(kind)


def draw_counts(rate, n, pairing, other, rng):
    """Counts for one draw of n genomes at `rate` given the paired arm's `other` rate: independent, or as disjoint or
    nested as the rates allow (returns this arm's count and the other's)."""
    if pairing == "independent":
        return rng.binomial(n, rate), rng.binomial(n, other)
    both = max(0.0, rate + other - 1) if pairing == "disjoint" else min(rate, other)
    q = np.array([both, rate - both, other - both, 1 - rate - other + both])
    c = rng.multinomial(n, q / q.sum())
    return c[0] + c[1], c[0] + c[2]


def simulate(rates, kind, delta, rng, screens=SCREENS, n=512, draws=2, hosts=10, pairing="independent", sigma=0.5):
    """Simulated screens: host base rates from `rates`, two draws per host whose rates scatter log-normally (sigma)
    around the host's in each arm independently, the treated arm shifted by the scenario's host shift. Returns the
    hull's coverage of delta, and the shares reading 'raises', 'at least 0.001' and the exclusion."""
    hit = raises = big = excl = 0
    for _ in range(screens):
        base = rng.choice(rates, hosts) + (0.01 if kind == "raised base" else 0.0)
        sh = shifts(kind, delta, rng, hosts)
        d = np.zeros(hosts)
        for h in range(hosts):
            ct = cb = 0
            for _ in range(draws):
                rb = np.clip(base[h] * rng.lognormal(0, sigma), 0, 1) if base[h] > 0 else 0.0
                rt = np.clip(base[h] * rng.lognormal(0, sigma) + sh[h], 0, 1) if base[h] > 0 else min(sh[h], 1)
                x, y = draw_counts(rt, n, pairing, rb, rng)
                ct, cb = ct + x, cb + y
            d[h] = (ct - cb) / (n * draws)
        idx = rng.integers(0, hosts, (B, hosts))
        lo, hi = hull(d, idx)
        hit += lo <= delta <= hi
        raises += lo > 0
        big += lo > BENCH
        excl += -MARGIN < lo and hi < MARGIN and np.abs(d).max() < HOST_GUARD
    return {"scenario": kind, "delta": delta, "pairing": pairing, "coverage": hit / screens,
            "raises": raises / screens, "at_least_bench": big / screens, "excluding": excl / screens}


def stage_coverage(out):
    rng = np.random.default_rng(SEED_COVERAGE)
    rates = m4d_rates()
    res = [simulate(rates, kind, dl, rng) for dl in (0.002, MARGIN) for kind in SCENARIOS]
    res += [simulate(rates, "fixed", 0.0, rng)]
    res += [simulate(rates, kind, MARGIN, rng, pairing=pr) for kind in ("fixed", "raised base")
            for pr in ("disjoint", "nested")]
    ok = all(r["coverage"] >= MIN_COVERAGE for r in res if r["delta"] > 0 and r["scenario"] != "sparse")
    rec = {"scenarios": res, "min_coverage": MIN_COVERAGE, "exclusions_ok": ok, "host_guard": HOST_GUARD,
           "base_rates": rates.tolist()}
    json.dump(rec, open(out / "coverage.json", "w"), indent=1)
    for r in res:
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    print(f"exclusions read: {ok}")
    return rec


# ------------------------------------------------------------------------------------------------------------ the run
def load_counts(verified, arms):
    """Per arm, each host's merged separate-states and still-unresolved counts over its draws; the audit and the
    transitions."""
    import m4e
    hosts = []
    per = {}
    for v in verified:
        r = v["rec"]
        if r["name"] not in hosts:
            hosts.append(r["name"])
        for a in arms:
            f = m4e.panel_file(r, v["draw"], a)
            if not f.exists():
                raise SystemExit(f"missing panel {f.name}: the run is incomplete and is not read")
            p = json.load(open(f))
            m4e.validate(p, r, v["draw"], a, v["arms"][a][1])
            per[(r["name"], v["draw"], a)] = p
    failed = [k for k, p in per.items() if m4e.audit_failed(p)]
    use_second = not failed
    sep = {a: [] for a in arms}
    unres = {a: [] for a in arms}
    first = {a: [] for a in arms}
    first_unres = {a: [] for a in arms}
    for name in hosts:
        for a in arms:
            ps = [p for (h, _, a_), p in per.items() if h == name and a_ == a]
            cls = [m4e.merged_classes(p) if use_second else p["class"] for p in ps]
            sep[a].append(sum(x in SEPARATE for cl in cls for x in cl))
            unres[a].append(sum(x == UNRESOLVED for cl in cls for x in cl))
            first[a].append(sum(x in SEPARATE for p in ps for x in p["class"]))
            first_unres[a].append(sum(x == UNRESOLVED for p in ps for x in p["class"]))
    audited = {a: sum(p["class"][i] == FADING for (_, _, a_), p in per.items() if a_ == a for i in p["audit"])
               for a in arms}  # the audit's actual fading denominators (Astra, round 2)
    trans = {}
    for (_, _, a), p in per.items():
        t = trans.setdefault(a, {})
        for i, x in zip(p["second"]["ids"], p["second"]["class"]):
            key = f"{m4e.CODES[p['class'][i]]} -> {m4e.CODES[x]}"
            t[key] = t.get(key, 0) + 1
    return {"hosts": hosts, "sep": sep, "unres": unres, "first": first, "first_unres": first_unres,
            "use_second": use_second, "audited_fading": audited,
            "audit_failed": [list(k) for k in failed], "transitions": trans, "panels": per}


def classes(counts, key):
    """The classes the reading uses for one panel: the merged ones, or the first pass's if the audit failed anywhere
    (the global fallback; the tables use the same choice, Astra, round 2)."""
    import m4e
    p = counts["panels"][key]
    return m4e.merged_classes(p) if counts["use_second"] else list(p["class"])


def read(counts, n, exclusions_ok, seed=SEED_BOOT):
    sep, unres = counts["sep"], counts["unres"]
    h = len(sep["I"])
    if h < MIN_HOSTS:
        raise SystemExit(f"{h} hosts: fewer than {MIN_HOSTS} are never read")
    idx = np.random.default_rng(seed).integers(0, h, (B, h))
    out = {"primary": {k: contrast(sep, unres, n, idx, a, b, exclusions_ok) for k, (a, b) in PRIMARY.items()},
           "secondary": {f"{a} - {b}": contrast(sep, unres, n, idx, a, b, exclusions_ok)
                         for a, b in SECONDARY if a in sep and b in sep}}
    s = {a: np.asarray(sep[a], float) for a in ("U_HH", "U_HL", "U_LH", "U_LL")}
    u = {a: np.asarray(unres[a], float) for a in s}
    inter = (s["U_HH"] - s["U_HL"] - s["U_LH"] + s["U_LL"]) / n
    lo_d = (s["U_HH"] - s["U_HL"] - u["U_HL"] - s["U_LH"] - u["U_LH"] + s["U_LL"]) / n
    hi_d = (s["U_HH"] + u["U_HH"] - s["U_HL"] - s["U_LH"] + s["U_LL"] + u["U_LL"]) / n
    out["interaction"] = {"D": float(inter.mean()), "interval": list(hull(inter, idx)),
                          "envelope": list(envelope(lo_d, hi_d, idx))}
    return out


def describe(counts, arms):
    """Not-settled counts (persistent oscillation plus unresolved, merged classes) per arm, per host and draw counts."""
    import m4e
    out = {}
    for a in arms:
        ps = [(k, p) for k, p in counts["panels"].items() if k[2] == a]
        cls = {k: (m4e.merged_classes(p) if counts["use_second"] else p["class"]) for k, p in ps}
        out[a] = {"not_settled": sum(x in (OSCILLATION, UNRESOLVED) for c_ in cls.values() for x in c_),
                  "per_draw_separate": {f"{k[0]} d{k[1]}": sum(x in SEPARATE for x in c_) for k, c_ in cls.items()},
                  "invalid_panels": [f"{k[0]} d{k[1]}" for k, p in ps if not p["valid"]]}
    return out


def block_s2(verified, arms):
    """S2 of every arm's block per host (the paired construction's magnitudes; the same for both draws of the U, W and
    K arms by construction), averaged over the draws."""
    import m4e
    k = m4e.m4d.core_idx()
    out = {a: [] for a in arms}
    names = []
    for v in verified:
        if v["rec"]["name"] not in names:
            names.append(v["rec"]["name"])
    for name in names:
        vs = [v for v in verified if v["rec"]["name"] == name]
        for a in arms:
            vals = []
            for v in vs:
                g = v["g"]
                scale = g.cfg.init_w_scale / float(g.spec.chem_anat.mean())
                Bk = v["arms"][a][0].chem[np.ix_(k, k)].astype(np.float64) * scale
                off = ~np.eye(len(Bk), dtype=bool)
                vals.append(float((Bk[off] ** 2).sum()))
            out[a].append(float(np.mean(vals)))
    return out


def main():
    import m4e
    out = m4e.OUT
    verified = m4e.verify_run()  # every input checked first
    arms = m4e.arms()
    counts = load_counts(verified, arms)
    n = m4e.N_DRAW * m4e.DRAWS
    base = {"counts": {"separate": counts["sep"], "unresolved": counts["unres"], "separate_first_pass": counts["first"],
                       "hosts": counts["hosts"], "n": n},
            "second_pass_used": counts["use_second"], "audit_failed": counts["audit_failed"],
            "audited_fading_per_arm": counts["audited_fading"],
            "transitions": counts["transitions"]}
    if m4e.SMOKE or len(counts["hosts"]) < MIN_HOSTS:
        json.dump({"reading": "not read (a smoke, or fewer than ten hosts)", **base}, open(out / "readings.json", "w"),
                  indent=1)
        print(f"not read: {len(counts['hosts'])} host(s); every check passed; {base['counts']}")
        return
    cov = json.load(open(out / "coverage.json"))
    res = read(counts, n, cov["exclusions_ok"])
    res["first_pass_reading"] = read({"sep": counts["first"], "unres": counts["first_unres"]}, n,
                                     cov["exclusions_ok"])["primary"]  # beside it, on the 2000-tick classes (Astra)
    res.update(base)
    res["not_settled"] = describe(counts, arms)
    json.dump(res, open(out / "readings.json", "w"), indent=1)  # the readings first: the dose model cannot stop them
    u = [a for a in ("U_LL", "U_LH", "U_HL", "U_HH", "U_HX") if a in arms]
    res["dose"] = dose_model(counts["sep"], n, block_s2(verified, arms), u, [a for a in ("W", "K") if a in arms])
    json.dump(res, open(out / "readings.json", "w"), indent=1)
    for k, v in res["primary"].items():
        print(f"Δ_{k} {v['D']:+.4f} {v['interval']}: {v['direction']}; {v['size']}")


if __name__ == "__main__":
    if sys.argv[1:] == ["coverage"]:
        import m4e
        m4e.OUT.mkdir(parents=True, exist_ok=True)
        stage_coverage(m4e.OUT)
    else:
        main()
