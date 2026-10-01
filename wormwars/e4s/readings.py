"""E4s-1's registered outcome rules (experiments/E4s-stereo-module/E4s-1/PREREGISTRATION.md §6, D150).

`boot_means` is the same computation as E2d's `_boot_means` (a test checks they agree); the script
passes E2d's own function, imported unchanged.
"""

from __future__ import annotations

from collections import Counter

import numpy as np

O1_SEED, O1_RESAMPLES, MIN_PAIRS = 20_261_001, 10_000, 12
USES, NEGLIGIBLE = 0.5, 0.25
O1_LABELS = ("reversed: M is worse", "supports", "positive; estimate below 0.5",
             "does not support an effect of at least 0.5", "inconclusive")


def boot_means(x, resamples: int, seed: int) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(resamples, len(x)))
    return x[idx].mean(axis=1)


def o1_label(lo: float, hi: float, est: float) -> str:
    if hi < 0:
        return O1_LABELS[0]
    if lo > 0 and est >= 0.5:
        return O1_LABELS[1]
    if lo > 0:
        return O1_LABELS[2]
    if hi < 0.5:
        return O1_LABELS[3]
    return O1_LABELS[4]


def interval(d, boot=boot_means) -> dict:
    m = boot(np.asarray(d, dtype=np.float64), O1_RESAMPLES, O1_SEED)
    return {"lo": float(np.percentile(m, 5)), "hi": float(np.percentile(m, 95)), "estimate": float(np.mean(d))}


def o1(d, boot=boot_means, min_pairs: int = MIN_PAIRS) -> dict:
    d = np.asarray(d, dtype=np.float64)
    if not np.isfinite(d).all():
        raise ValueError("a non-finite paired difference: the run is not read, not a pair")
    if len(d) < min_pairs:
        return {"label": "not read", "pairs": int(len(d))}
    ci = interval(d, boot)
    return {**ci, "label": o1_label(ci["lo"], ci["hi"], ci["estimate"]), "pairs": int(len(d))}


def o1_companion(label: str, climb_lo: float, climb_hi: float):
    if label == "supports" and climb_lo <= 0 <= climb_hi:
        return "N ended lower; M did not improve"
    return None


def o1b_companion(label: str, r_minus_n: float):
    if label == "supports" and r_minus_n < 0:
        return "random signs were worse than no graft"
    return None


_O2 = {("uses", "uses"): "uses at both endpoints", ("uses", "unclear"): "uses at G0; F unclear",
       ("uses", "no material benefit"): "uses at G0 only", ("unclear", "uses"): "uses at F; G0 unclear",
       ("unclear", "unclear"): "unclear at both endpoints", ("unclear", "no material benefit"): "no use at F; G0 unclear",
       ("no material benefit", "uses"): "uses at F only", ("no material benefit", "unclear"): "no use at G0; F unclear",
       ("no material benefit", "no material benefit"): "uses at neither endpoint"}


def o2_label(g0: str, f: str) -> str:
    return _O2[(g0, f)]


def arm_reading(labels, threshold: int, denominator: int) -> dict:
    """The arm's descriptive reading: a label named if at least `threshold` of a fixed `denominator`
    runs carry it; otherwise "no label named". "not read" runs never reach a threshold."""
    counts = Counter(labels)
    named = [k for k, v in counts.items() if k != "not read" and v >= threshold]
    return {"reading": named[0] if named else "no label named", "counts": dict(counts), "denominator": denominator}


def retention(g0_classes, f_classes):
    """Among the runs that use at G0 and whose F was read (not None), the share that also use at F."""
    known = {"uses", "unclear", "no material benefit"}
    if any(g not in known for g in g0_classes) or any(f is not None and f not in known for f in f_classes):
        raise ValueError("classes must be E2d's three states, or None for an unread F")
    pairs = [(g, f) for g, f in zip(g0_classes, f_classes) if g == "uses" and f is not None]
    if not pairs:
        return "not applicable"
    return sum(f == "uses" for _, f in pairs) / len(pairs)


def c2_reading(mean_ci: dict, swap_ci: dict) -> str:
    """C2's ordered reading from the module's signed contrasts (real - module mean, real - swapped)."""
    if mean_ci["lo95"] > USES and swap_ci["lo95"] > USES:
        return "uses"
    if mean_ci["hi95"] < -NEGLIGIBLE:
        return "harmful"
    inside = lambda c: c["lo95"] > -NEGLIGIBLE and c["hi95"] < NEGLIGIBLE  # noqa: E731
    if inside(mean_ci) and inside(swap_ci):
        return "neutral"
    return "unclear"


def o3_split(abs_offsets) -> tuple[list[int], list[int]]:
    """M's 16 runs split 8 against 8 by rank of |u(0.08, 0)|, ties to the lower run index."""
    x = np.asarray(abs_offsets, dtype=np.float64)
    order = sorted(range(len(x)), key=lambda i: (x[i], i))
    half = len(x) // 2
    return sorted(order[:half]), sorted(order[half:])
