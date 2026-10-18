"""03a's registered statistics (experiments/03a-self-consistency/DESIGN.md v7.1 §6, §7).

- **Holm** step-down at α (both families).
- **Family 2, per target:** the mean of the five MIP brains' recovery statistics minus the five NIP brains'; the exact
  one-sided permutation of arm labels over the 252 splits of the ten distinct brains (p = the share of splits at least
  as extreme, the observed one included); Holm over the five high and medium targets; a target counts only if it is
  rejected and its observed difference is at least the 0.05 AUC floor; a withheld target keeps its place with p = 1.
- **Family 2's validation** by simulation: under the sharp null, independent targets and a shared MIP-brain effect
  (intraclass correlation ρ) that leaves each target's arms exchangeable, the family-wise rejection rate must be at
  most 0.0531 over 20 000 datasets; unequal arm variances (outside the null) are reported.
- **Three-state comparisons:** a paired difference with a 95% bootstrap interval over worlds (one shared resample of
  world ids for every brain and state compared) and over brains; equivalent inside ±p, above entirely above +p, below
  entirely below −p, otherwise undetermined.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np

FLOOR = 0.05
ALPHA = 0.05
ACCEPT = 0.0531  # 0.05 plus two Monte Carlo standard errors at 20 000 datasets
BOOT_STREAM = 0x03AB00


def holm(p, alpha: float = ALPHA) -> np.ndarray:
    """Holm's step-down: rejections, in the input order."""
    p = np.asarray(p, dtype=np.float64)
    m = len(p)
    order = np.argsort(p, kind="stable")
    rej = np.zeros(m, dtype=bool)
    for i, j in enumerate(order):
        if p[j] <= alpha / (m - i):
            rej[j] = True
        else:
            break
    return rej


SPLITS = np.array([[i in c for i in range(10)] for c in combinations(range(10), 5)])  # [252, 10], True = "MIP"


def exact_p(mip, nip) -> tuple[float, float]:
    """(observed MIP − NIP difference of means, exact one-sided p over the 252 label splits)."""
    mip, nip = np.asarray(mip, dtype=np.float64), np.asarray(nip, dtype=np.float64)
    if mip.shape != (5,) or nip.shape != (5,):
        raise ValueError("family 2 compares five MIP brains with five NIP brains")
    x = np.concatenate([mip, nip])
    d = (SPLITS @ x - (~SPLITS) @ x) / 5.0
    obs = (mip.sum() - nip.sum()) / 5.0
    # the observed split is one of the 252, computed the same way; compare with a tolerance far below any real gap
    return float(obs), float((d >= obs - 1e-12).mean())


def exact_p_batch(mip: np.ndarray, nip: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Vectorised `exact_p` over leading axes: mip, nip [..., 5]."""
    x = np.concatenate([mip, nip], axis=-1)
    tot = x.sum(axis=-1, keepdims=True)
    msum = x @ SPLITS.T.astype(np.float64)  # [..., 252]
    d = (2 * msum - tot) / 5.0
    obs = (mip.sum(axis=-1) - nip.sum(axis=-1)) / 5.0
    return obs, (d >= obs[..., None] - 1e-12).mean(axis=-1)


def family2(mip: dict, nip: dict, targets: list, floor: float = FLOOR, alpha: float = ALPHA) -> dict:
    """Family 2 over a fixed list of targets. `mip[t]` and `nip[t]` are five per-brain recovery statistics, or None
    when a registered brain is missing; a missing or non-finite value withholds the target with p = 1."""
    rows, ps = [], []
    for t in targets:
        m, n = mip.get(t), nip.get(t)
        if (m is None or n is None or len(m) != 5 or len(n) != 5
                or not np.isfinite(np.asarray(m, dtype=np.float64)).all()
                or not np.isfinite(np.asarray(n, dtype=np.float64)).all()):
            # a missing or non-finite brain value withholds the target (Astra: a NaN would otherwise give p = 0)
            rows.append({"target": t, "withheld": True, "difference": None, "p": 1.0})
            ps.append(1.0)
            continue
        d, p = exact_p(mip[t], nip[t])
        rows.append({"target": t, "withheld": False, "difference": d, "p": p})
        ps.append(p)
    rej = holm(ps, alpha)
    for r, k in zip(rows, rej):
        r["holm_rejected"] = bool(k)
        r["counts"] = bool(k and r["difference"] is not None and r["difference"] >= floor)
    return {"targets": rows, "any": any(r["counts"] for r in rows), "alpha": alpha, "floor": floor}


def simulate_family2(n_datasets: int, seed: int, *, icc: float = 0.0, nip_sd: float = 1.0, targets: int = 5,
                     floor: float | None = None, alpha: float = ALPHA, chunk: int = 2000) -> dict:
    """The family-wise rejection rate of family 2 on simulated datasets.

    Each MIP brain b has one effect u_b shared by every target; a target's MIP value is √ρ u_b + √(1−ρ) e and its NIP
    value √ρ v + √(1−ρ) e' with v drawn per NIP brain (each target has its own), times `nip_sd`. With nip_sd = 1 every
    target's ten values are exchangeable (the sharp null) and the targets are dependent through u when ρ > 0.
    `floor` None counts Holm rejections alone; a number also requires the observed difference to reach it."""
    rng = np.random.default_rng([int(seed), 0x03AF2])
    a, b = np.sqrt(icc), np.sqrt(1.0 - icc)
    hits = 0
    done = 0
    while done < n_datasets:
        n = min(chunk, n_datasets - done)
        u = rng.standard_normal((n, 1, 5))
        mip = a * u + b * rng.standard_normal((n, targets, 5))
        nip = nip_sd * (a * rng.standard_normal((n, targets, 5)) + b * rng.standard_normal((n, targets, 5)))
        obs, p = exact_p_batch(mip, nip)  # [n, targets]
        order = np.sort(p, axis=1)
        thresh = alpha / (targets - np.arange(targets))
        passed = np.cumprod(order <= thresh, axis=1).astype(bool)  # Holm's step-down
        n_rej = passed.sum(axis=1)
        if floor is None:
            hits += int((n_rej > 0).sum())
        else:
            # the rejected targets are those with the n_rej smallest p values (ties at the threshold included)
            cut = np.where(n_rej > 0, order[np.arange(n), np.maximum(n_rej - 1, 0)], -1.0)
            rejected = p <= cut[:, None]
            hits += int((rejected & (obs >= floor)).any(axis=1).sum())
        done += n
    rate = hits / n_datasets
    return {"datasets": n_datasets, "rate": rate, "se": float(np.sqrt(rate * (1 - rate) / n_datasets)),
            "icc": icc, "nip_sd": nip_sd, "floor": floor}


VALIDATION_SCENARIOS = (
    {"name": "independent", "icc": 0.0, "nip_sd": 1.0, "null": True},
    {"name": "shared MIP effect, icc 0.3", "icc": 0.3, "nip_sd": 1.0, "null": True},
    {"name": "shared MIP effect, icc 0.5", "icc": 0.5, "nip_sd": 1.0, "null": True},
    {"name": "unequal variances (NIP sd 2)", "icc": 0.0, "nip_sd": 2.0, "null": False},
    {"name": "unequal variances (NIP sd 0.5)", "icc": 0.0, "nip_sd": 0.5, "null": False},
)


def validate_family2(n_datasets: int = 20_000, seed: int = 0) -> dict:
    """§7's validation: every null scenario at most ACCEPT; the others reported."""
    rows = []
    for i, sc in enumerate(VALIDATION_SCENARIOS):
        r = simulate_family2(n_datasets, seed + i, icc=sc["icc"], nip_sd=sc["nip_sd"])
        rows.append({**sc, **r, "passes": (r["rate"] <= ACCEPT) if sc["null"] else None})
    return {"scenarios": rows, "accept": ACCEPT, "passes": all(r["passes"] for r in rows if r["null"])}


# ------------------------------------------------------------------ three-state comparisons

def world_resamples(n_worlds: int, B: int, seed: int) -> np.ndarray:
    """[B, n_worlds] world indices: one shared resample, the same for every comparison made with this seed."""
    rng = np.random.default_rng([int(seed), BOOT_STREAM, int(n_worlds)])
    return rng.integers(0, n_worlds, size=(B, n_worlds))


def brain_resamples(n_brains: int, B: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng([int(seed), BOOT_STREAM + 1, int(n_brains)])
    return rng.integers(0, n_brains, size=(B, n_brains))


def compare(a: np.ndarray, b: np.ndarray, margin: float, *, B: int = 10_000, seed: int = 0,
            over_brains: bool = True) -> dict:
    """a − b for two states scored on the same worlds: a, b are [brains, worlds] (or [worlds] for one brain).

    The difference of means, its 95% percentile interval from a bootstrap over worlds (shared across brains and
    states) and, if `over_brains` and there is more than one brain, over brains; and the verdict at ±margin."""
    a, b = np.atleast_2d(np.asarray(a, dtype=np.float64)), np.atleast_2d(np.asarray(b, dtype=np.float64))
    if a.shape != b.shape:
        raise ValueError("compared states must share brains and worlds")
    d = a - b  # [brains, worlds]
    nb, nw = d.shape
    wi = world_resamples(nw, B, seed)
    per_brain = d[:, wi].mean(axis=2)  # [brains, B]
    if over_brains and nb > 1:
        bi = brain_resamples(nb, B, seed)
        boot = per_brain[bi, np.arange(B)[:, None]].mean(axis=1)
    else:
        boot = per_brain.mean(axis=0)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    est = float(d.mean())
    return {"difference": est, "lo": float(lo), "hi": float(hi), "half_width": float((hi - lo) / 2),
            "verdict": verdict(lo, hi, margin), "margin": float(margin)}


def verdict(lo: float, hi: float, margin: float) -> str:
    if lo > margin:
        return "above"
    if hi < -margin:
        return "below"
    if lo >= -margin and hi <= margin:
        return "equivalent"
    return "undetermined"


# ------------------------------------------------------------------ attributes and outcomes

def reliable_brain(refit_means, delta_search: float, restoration: dict | None = None) -> bool:
    """A target-brain's reference is reliable if its refits' SD (over their final-evaluation means) is at most
    2 δ_search and, in MIP, the reference is equivalent to or above exact restoration (`restoration` the comparison
    reference − restoration; undetermined does not qualify)."""
    sd = float(np.std(np.asarray(refit_means, dtype=np.float64), ddof=1))
    ok = sd <= 2 * delta_search
    if restoration is not None:
        ok = ok and restoration["verdict"] in ("equivalent", "above")
    return bool(ok)


def functional(comparison: dict) -> str:
    """Mean free search − reference: reached if equivalent, exceeded if above, failed if below, else undetermined."""
    return {"equivalent": "reached", "above": "exceeded", "below": "failed"}.get(comparison["verdict"], "undetermined")


def outcome(reliable: bool, functional_success: str, enrichment: bool) -> str:
    """§6's outcome summary for one target-arm."""
    if not reliable:
        return "excluded"
    if functional_success in ("reached", "exceeded"):
        return "anatomical recovery" if enrichment else "functional success, anatomy undetermined"
    if functional_success == "failed":
        return "search failure"
    return "inconclusive"


def separates(outcomes: list) -> bool:
    """'The proof of concept separates the outcomes': at least two of the three substantive outcomes occur."""
    subst = {"anatomical recovery", "functional success, anatomy undetermined", "search failure"}
    return len(subst & set(outcomes)) >= 2


def pooled_rms(values) -> float:
    v = np.asarray(list(values), dtype=np.float64)
    return float(np.sqrt(np.mean(v ** 2))) if len(v) else float("nan")
