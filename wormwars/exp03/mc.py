"""03mc's statistics and rules (experiments/03mc-p4-confirm/DESIGN.md §4, §6): rank tests, intersection-union over
the five ensembles, Holm over the four primary questions with missing questions kept at p = 1, Q-B's paired
bootstrap and its normal-theory tests, and the degree-matched controls."""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm

ENSEMBLES = ("SH", "SH-route", "SH-class", "SH-mirror", "SH-recip")
PRIMARY = ("A", "B", "C", "D")
ALPHA = 0.05
MARGIN_CUT = 0.40  # Q-B: the response must fall by more than this share
MARGIN_P4 = 0.02  # Q-B: |change in P4| must be below this


def rank_p(values, n2: float, at_or_below: bool) -> dict:
    """The rank p of N2 against one reference set: r counts the valid references at or below N2's value
    (`at_or_below`, Q-A) or at or above it (Q-C, Q-D, the single-signal rule); p = (r + 1)/(n + 1), with n the
    number of valid references. Non-finite values are invalid and leave n. A non-finite N2 gives p = 1: with both
    comparisons false, r = 0 would otherwise read as a pass (Fable, review v2.1)."""
    v = np.asarray(values, dtype=np.float64)
    ok = np.isfinite(v)
    v = v[ok]
    if n2 is None or not math.isfinite(float(n2)):
        return {"r": None, "n": int(len(v)), "invalid": int((~ok).sum()), "p": 1.0, "n2_valid": False}
    r = int((v <= n2).sum() if at_or_below else (v >= n2).sum())
    return {"r": r, "n": int(len(v)), "invalid": int((~ok).sum()), "p": (r + 1) / (len(v) + 1), "n2_valid": True}


def intersection_union(per_ensemble: dict) -> float:
    """The largest p over the five ensembles; 1 if any ensemble is missing, so an incomplete set cannot pass."""
    if any(e not in per_ensemble or per_ensemble[e] is None or per_ensemble[e].get("p") is None for e in ENSEMBLES):
        return 1.0
    return max(float(per_ensemble[e]["p"]) for e in ENSEMBLES)


def holm(ps: dict, alpha: float = ALPHA) -> dict:
    """Holm over the four primary questions. A question that is withheld or not measured (None) enters with
    p = 1, so the family keeps four members (DESIGN §6). Reports each question's p, its Holm threshold, whether
    it passed, the Holm-adjusted p, and whether it would have met `alpha` alone (the "Holm stops" wording)."""
    p = {q: (1.0 if ps.get(q) is None or not math.isfinite(float(ps[q])) else float(ps[q])) for q in PRIMARY}
    order = sorted(PRIMARY, key=lambda q: (p[q], q))
    m = len(order)
    out, going, running = {}, True, 0.0
    for i, q in enumerate(order):
        thr = alpha / (m - i)
        running = max(running, min(1.0, (m - i) * p[q]))
        passed = going and p[q] <= thr
        going = passed
        out[q] = {"p": p[q], "missing": ps.get(q) is None, "threshold": thr,
                  "rank": i + 1, "passed": passed, "adjusted_p": running, "alone_at_alpha": p[q] <= alpha}
    return out


def ratio_terms(f, s, idx=None):
    f = np.asarray(f, dtype=np.float64)
    s = np.asarray(s, dtype=np.float64)
    if idx is not None:
        f, s = f[idx], s[idx]
    return float(np.abs(f).mean()), float(np.abs(s).mean())


def paired_bootstrap(f_int, s_int, f_del, s_del, resamples: int = 10_000, seed: int = 20261016,
                     floor: float = 1e-4) -> dict:
    """Q-B's estimates and their bootstrap SEs (DESIGN §4): the response cut 1 - den_del/den_int, the numerator's
    cut, and the change in P4, all as ratios of means over genomes. The resamples draw genome indices once and use
    them for both conditions (paired). A resample with either denominator below `floor` is dropped and counted."""
    n = len(f_int)
    for a in (s_int, f_del, s_del):
        if len(a) != n:
            raise ValueError("paired arrays must have one value per genome in each condition")
    ni, di = ratio_terms(f_int, s_int)
    nd, dd = ratio_terms(f_del, s_del)
    valid = bool(all(math.isfinite(x) for x in (ni, di, nd, dd)) and di >= floor and dd >= floor)
    if not valid:  # the full-sample estimate is held to the floor too (Fable, review v2.1)
        return {"valid": False, "genomes": n, "numerator_intact": ni, "denominator_intact": di,
                "numerator_deleted": nd, "denominator_deleted": dd}
    est = {"valid": True, "cut": 1 - dd / di, "numerator_cut": 1 - nd / ni, "dP4": nd / dd - ni / di,
           "P4_intact": ni / di, "P4_deleted": nd / dd, "genomes": n}
    af, as_, bf, bs = (np.abs(np.asarray(x, dtype=np.float64)) for x in (f_int, s_int, f_del, s_del))
    rng = np.random.default_rng(seed)
    cuts, ncuts, dps, dropped = [], [], [], 0
    for _ in range(resamples):
        i = rng.integers(0, n, n)
        a_n, a_d, b_n, b_d = af[i].mean(), as_[i].mean(), bf[i].mean(), bs[i].mean()
        if a_d < floor or b_d < floor:
            dropped += 1
            continue
        cuts.append(1 - b_d / a_d)
        ncuts.append(1 - b_n / a_n)
        dps.append(b_n / b_d - a_n / a_d)
    q = lambda x, lo, hi: [float(np.quantile(x, lo)), float(np.quantile(x, hi))] if len(x) else [None, None]  # noqa: E731
    est.update(cut_se=float(np.std(cuts)), numerator_cut_se=float(np.std(ncuts)), dP4_se=float(np.std(dps)),
               cut_q05_q95=q(cuts, 0.05, 0.95), dP4_q05_q95=q(dps, 0.05, 0.95),
               cut_q025_q975=q(cuts, 0.025, 0.975), numerator_cut_q025_q975=q(ncuts, 0.025, 0.975),
               dP4_q025_q975=q(dps, 0.025, 0.975), resamples=resamples, dropped=dropped, seed=seed)
    return est


def cut_difference(s_int, s_a, s_b, resamples: int = 10_000, seed: int = 20261016) -> dict:
    """The paired difference of two deletions' response cuts on the same genomes, cut_a - cut_b =
    (den_b - den_a) / den_int, with its bootstrap SE and the one-sided p for cut_a > cut_b (DESIGN §4, the
    degree-matched controls). A zero SE gives 0 or 1 exactly."""
    i0, a, b = (np.abs(np.asarray(x, dtype=np.float64)) for x in (s_int, s_a, s_b))
    diff = float((b.mean() - a.mean()) / i0.mean())
    rng = np.random.default_rng(seed)
    n = len(i0)
    ds = []
    for _ in range(resamples):
        i = rng.integers(0, n, n)
        ds.append((b[i].mean() - a[i].mean()) / i0[i].mean())
    se = float(np.std(ds))
    p = (0.0 if diff > 0 else 1.0) if se <= 0 else _sf(diff / se)
    return {"difference": diff, "se": se, "p": p, "resamples": resamples, "seed": seed}


def _sf(z: float) -> float:
    return float(norm.sf(z))


def qb_tests(cut: float, cut_se: float, dP4: float, dP4_se: float, margin_cut: float = MARGIN_CUT,
             margin_p4: float = MARGIN_P4) -> dict:
    """Q-B's normal-theory tests with the bootstrap SE (DESIGN §4): one-sided p for cut > margin_cut, and the
    two one-sided tests for |dP4| < margin_p4 (p_eq is the larger). A zero SE gives 0 or 1 exactly."""
    def one(dist, se):
        if se <= 0:
            return 0.0 if dist > 0 else 1.0
        return _sf(dist / se)
    p_cut = one(cut - margin_cut, cut_se)
    p_eq = max(one(dP4 + margin_p4, dP4_se), one(margin_p4 - dP4, dP4_se))
    return {"p_cut": p_cut, "p_eq": p_eq, "p": max(p_cut, p_eq)}


def matched_controls(total_degree: dict, targets, exclude=(), k: int = 4) -> dict:
    """For each target pair, the `k` pairs nearest in total degree, ties broken alphabetically; the targets and
    `exclude` (the turn read-out pairs) are never controls."""
    banned = set(targets) | set(exclude)
    pool = sorted(p for p in total_degree if p not in banned)
    return {t: sorted(pool, key=lambda p: (abs(total_degree[p] - total_degree[t]), p))[:k] for t in targets}


def pair_total_degrees(con, turn_pairs=()) -> dict:
    """Total degree of every bilateral pair (XXXL with XXXR): chemical in + out + gap, summed over both neurons."""
    chem = np.asarray(con.chem) != 0
    gap = np.asarray(con.gap) != 0
    names = list(con.names)
    idx = {n: i for i, n in enumerate(names)}

    def deg(i):
        return int(chem[:, i].sum() + chem[i, :].sum() + gap[i, :].sum())

    return {n[:-1]: deg(i) + deg(idx[n[:-1] + "R"]) for n, i in idx.items()
            if n.endswith("L") and n[:-1] + "R" in idx}


def _derived(salt: str, name: str) -> set:
    """Every generator seed a graph name reaches in 03's code: the calibration draw `_gseed`, the probe genomes
    `_gseed + 1`, and 03r's secondary permutation `_gseed + 2`."""
    from .measures import genome_seed
    g = genome_seed(name, salt)
    return {g, g + 1, g + 2}


def freshness_audit(new: dict, old: dict, new_perm_seeds, old_perm_seeds) -> dict:
    """DESIGN §3: the new study's derived seeds must be distinct from each other and from every earlier study's;
    new salts must be new; permutation seeds are compared as the generator seeds `brain._apply_magnitude_mode`
    uses (2 * seed + 0 for chemical, + 1 for gap)."""
    reused_salts = sorted(set(new) & set(old))
    new_seeds: dict[int, str] = {}
    repeated = []
    for salt, names in new.items():
        for n in names:
            for s in _derived(salt, n):
                if s in new_seeds and new_seeds[s] != f"{salt}{n}":
                    repeated.append([new_seeds[s], f"{salt}{n}"])
                elif s in new_seeds:
                    repeated.append([f"{salt}{n}", "listed twice"])
                new_seeds[s] = f"{salt}{n}"
    old_seeds = {}
    for salt, names in old.items():
        for n in names:
            for s in _derived(salt, n):
                old_seeds[s] = f"{salt}{n}"
    with_old = sorted({(new_seeds[s], old_seeds[s]) for s in set(new_seeds) & set(old_seeds)})
    gen = lambda seeds: {2 * int(s) + t: int(s) for s in seeds for t in (0, 1)}  # noqa: E731
    gn, go = gen(new_perm_seeds), gen(old_perm_seeds)
    perm = sorted({gn[s] for s in set(gn) & set(go)})
    repeated_perm = sorted({int(s) for s in new_perm_seeds if list(new_perm_seeds).count(s) > 1})
    out = {"reused_salts": reused_salts, "repeated_new_seeds": repeated, "genome_seed_collisions_with_old":
           [list(x) for x in with_old], "permutation_collisions": perm, "repeated_permutation_seeds": repeated_perm,
           "new_genome_seeds": len(new_seeds), "old_genome_seeds": len(old_seeds)}
    out["ok"] = not (reused_salts or repeated or with_old or perm or repeated_perm)
    return out


def content_check(new_hashes: dict, old_hashes) -> dict:
    """DESIGN §3: every new graph's array content must differ from every other new graph's and from every earlier
    graph's (03's and 03r's content manifests)."""
    by_hash: dict[str, list] = {}
    for n, h in sorted(new_hashes.items()):
        by_hash.setdefault(h, []).append(n)
    within = [v for v in by_hash.values() if len(v) > 1]
    old = set(old_hashes)
    against = sorted(n for n, h in new_hashes.items() if h in old)
    return {"within_new": within, "against_old": against, "ok": not within and not against,
            "new": len(new_hashes), "old": len(old)}
