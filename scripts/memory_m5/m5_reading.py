"""M5's reading (docs/memory/M5-POWER-DESIGN.md, section 1), shared by the power simulation and, later, M5's reader.

Per host, d_h = T's minus Rr's confirmed share. The estimate is the mean of the five ensembles' host means (fixed
strata, 1/5 each). The interval is the hull of a host bootstrap (stratified within ensembles; a plain mode resamples
all hosts as M4e's reader does) and a Student-t: the plain-s² t when every ensemble has the same number of hosts, the
stratum-aware Welch t otherwise. The envelope over the unresolved genomes uses a variance bound that holds for every
assignment, so it scales to any number of hosts. Success is an unqualified "raises": all six readings (raw,
audit-adjusted, each one-arm unresolved sensitivity, and each of those combined with the audit adjustment) read
"raises".
"""

from __future__ import annotations

import numpy as np
from scipy import stats

LEVEL, B = 0.95, 2000
SEED_BOOT = 20264401  # the bootstrap's resampling, one fixed matrix per composition (above the pilot's families)
R_BOUND = 0.0253  # r's one-sided 95% upper bound from the pilot's longer horizon, the unresolved sensitivity's rate
N_ENS = 5
# D372 (both reviewers, power results round 2): the balanced hull also holds the stratum-aware Welch t, beside the
# bootstrap and the plain-s^2 t, so one t formula serves the balanced and the unbalanced case. A constant, not a flag
# (Fable); only the power calculation's comparison run turns it off.
WELCH_TOO = True
READINGS = ("raw", "audit", "unres_T", "unres_Rr", "audit_unres_T", "audit_unres_Rr")
QUALIFIERS = (("audit", "the audit"), ("unres_T", "the T-side unresolved sensitivity"),
              ("unres_Rr", "the Rr-side unresolved sensitivity"))


def _groups(ens):
    ens = np.asarray(ens)
    groups = [np.flatnonzero(ens == e) for e in range(N_ENS)]
    if any(len(g) < 2 for g in groups):
        raise ValueError("every ensemble needs at least 2 hosts")
    return groups


def balanced(ens):
    return len({len(g) for g in _groups(ens)}) == 1


def estimate(d, ens):
    d = np.asarray(d, float)
    return float(sum(d[g].mean() for g in _groups(ens)) / N_ENS)


# ----------------------------------------------------------------------------------------------------- the bootstrap
def resample_weights(ens, b=B, seed=0, stratified=True, return_idx=False):
    """A (b, n) matrix W with W @ d the b bootstrap estimates. Stratified: each resample draws each ensemble's n_e
    hosts with replacement within it, weighted 1/(5 n_e). Plain: M4e's `default_rng(seed).integers(0, n, (b, n))`,
    weighted 1/n."""
    ens = np.asarray(ens)
    n = len(ens)
    rng = np.random.default_rng(seed)
    if stratified:
        groups = _groups(ens)
        idx = np.concatenate([g[rng.integers(0, len(g), (b, len(g)))] for g in groups], axis=1)
        w = np.concatenate([np.full(len(g), 1.0 / (N_ENS * len(g))) for g in groups])
    else:
        idx = rng.integers(0, n, (b, n))
        w = np.full(n, 1.0 / n)
    W = np.zeros((b, n))
    np.add.at(W, (np.repeat(np.arange(b), n), idx.ravel()), np.tile(w, b))
    return (W, idx) if return_idx else W


def boot_interval(d, W, level=LEVEL):
    m = W @ np.asarray(d, float)
    q = 100 * (1 - level) / 2
    return float(np.percentile(m, q)), float(np.percentile(m, 100 - q))


# ----------------------------------------------------------------------------------------------------------- the t
def welch_df(d, ens):
    d = np.asarray(d, float)
    groups = _groups(ens)
    a = np.array([d[g].var(ddof=1) / (N_ENS ** 2 * len(g)) for g in groups])
    k = np.array([len(g) for g in groups])
    if a.sum() == 0:
        return float(k.min() - 1)
    return float(a.sum() ** 2 / (a ** 2 / (k - 1)).sum())


def t_interval(d, ens, level=LEVEL):
    """Balanced: m ± t(n − 1) s sqrt(Σ_e (1/5)² / n_e), s² the plain sample variance (M4e's t at equal allocation).
    Unbalanced: SE² = Σ_e (1/5)² s_e² / n_e with Welch–Satterthwaite degrees of freedom."""
    d = np.asarray(d, float)
    groups = _groups(ens)
    m = estimate(d, ens)
    if balanced(ens):
        se = np.sqrt(d.var(ddof=1) * sum(1.0 / (N_ENS ** 2 * len(g)) for g in groups))
        df = len(d) - 1
    else:
        se = np.sqrt(sum(d[g].var(ddof=1) / (N_ENS ** 2 * len(g)) for g in groups))
        df = welch_df(d, ens)
    half = stats.t.ppf(0.5 + level / 2, df) * se if se > 0 else 0.0
    return float(m - half), float(m + half)


def welch_interval(d, ens, level=LEVEL):
    """The stratum-aware t: SE^2 = sum_e (1/5)^2 s_e^2 / n_e, Welch-Satterthwaite degrees of freedom."""
    d = np.asarray(d, float)
    groups = _groups(ens)
    m = estimate(d, ens)
    se = np.sqrt(sum(d[g].var(ddof=1) / (N_ENS ** 2 * len(g)) for g in groups))
    half = stats.t.ppf(0.5 + level / 2, welch_df(d, ens)) * se if se > 0 else 0.0
    return float(m - half), float(m + half)


def interval(d, ens, W, level=LEVEL):
    lo, hi = boot_interval(d, W, level)
    tl, th = t_interval(d, ens, level)
    lo, hi = min(lo, tl), max(hi, th)
    if WELCH_TOO and balanced(ens):
        wl, wh = welch_interval(d, ens, level)
        lo, hi = min(lo, wl), max(hi, wh)
    return lo, hi


# ------------------------------------------------------------------------------------------------------ the envelope
def envelope(lo_d, hi_d, ens, W, level=LEVEL):
    """A hull containing the interval of every assignment d with lo_d <= d <= hi_d: the bootstrap at the two ends
    (each resample's estimate is increasing in d), and a t with a variance bound valid for every corner. Balanced:
    s² <= Σ_i max{(lo_i − c)², (hi_i − c)²} / (n − 1) for any fixed c. Unbalanced: the same bound per ensemble,
    combined with (1/5)² / n_e, at t(min_e(n_e − 1)), which is at least every corner's Welch t."""
    lo_d, hi_d = np.asarray(lo_d, float), np.asarray(hi_d, float)
    groups = _groups(ens)
    blo, _ = boot_interval(lo_d, W, level)
    _, bhi = boot_interval(hi_d, W, level)
    mlo, mhi = estimate(lo_d, ens), estimate(hi_d, ens)
    halves = []
    if balanced(ens):
        c = (mlo + mhi) / 2
        bound = np.maximum((lo_d - c) ** 2, (hi_d - c) ** 2).sum() / (len(lo_d) - 1)
        se = np.sqrt(bound * sum(1.0 / (N_ENS ** 2 * len(g)) for g in groups))
        halves.append(stats.t.ppf(0.5 + level / 2, len(lo_d) - 1) * se)
    if not balanced(ens) or WELCH_TOO:
        var = 0.0
        for g in groups:
            c = (lo_d[g].mean() + hi_d[g].mean()) / 2
            var += np.maximum((lo_d[g] - c) ** 2, (hi_d[g] - c) ** 2).sum() / (len(g) - 1) / (N_ENS ** 2 * len(g))
        halves.append(stats.t.ppf(0.5 + level / 2, min(len(g) for g in groups) - 1) * np.sqrt(var))
    half = max(halves)
    return min(blo, mlo - half), max(bhi, mhi + half)


# -------------------------------------------------------------------------------------------------------- the fields
def direction(iv):
    lo, hi = iv
    if lo > 0:
        return "raises"
    if hi < 0:
        return "lowers"
    return "direction unresolved"


def qualification(ivs):
    """ivs: the interval of each of READINGS. Returns the raw direction when it is not "raises"; otherwise "raises",
    or which single adjustment removes it, or "qualified only in a combination" when only a combined one does."""
    raw = direction(ivs["raw"])
    if raw != "raises":
        return raw
    failing = [name for key, name in QUALIFIERS if direction(ivs[key]) != "raises"]
    if failing:
        return "raises, qualified by " + " and ".join(failing)
    if any(direction(ivs[k]) != "raises" for k in ("audit_unres_T", "audit_unres_Rr")):
        return "raises, qualified only in a combination"
    return "raises"


def unqualified_raises(ivs):
    return qualification(ivs) == "raises"
