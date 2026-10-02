"""E3a's registered readings (experiments/E3-ab-organism/E3a/PREREGISTRATION.md §5, §8).

`world_ci` and `classify` are E2d's, passed in by the script; the run-level interval is the 5th and
95th percentiles of E2d's `_boot_means` (10 000 resamples, seed 20 261 002); `boot_means` here is the
same computation (E4s-1's, tested equal to E2d's).
"""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import beta

from ..e4s.readings import boot_means

SEED, RESAMPLES = 20_261_002, 10_000
R, SPEED, TURN, T = 1.5, 0.35, 0.30, 600
MARGIN = 0.5
S2B_WORDING = ("evolution from a start near the ungated pair, with untied mutation, against a blind search over the whole "
               "range with the comparator pairs permanently tied")
NULL_S2A = ("no working selector was found in 300 generations at 02's sigmas, with untied mutation at 1×, "
            "from this initial distribution")


def interval(d, boot=boot_means) -> dict:
    d = np.asarray(d, dtype=np.float64)
    m = boot(d, RESAMPLES, SEED)
    return {"estimate": float(d.mean()), "lo": float(np.percentile(m, 5)), "hi": float(np.percentile(m, 95)),
            "pairs": int(len(d))}


def straight_run_reference(spawn, a, b) -> np.ndarray:
    spawn, a, b = (np.asarray(x, dtype=np.float64) for x in (spawn, a, b))
    t1 = (np.hypot(*(a - spawn).T) - R) / SPEED
    t_leg = (np.hypot(*(a - b).T) - 2 * R) / SPEED + math.pi / TURN
    out = 1 + np.floor((T - t1) / t_leg)
    return np.where(t1 > T, 0, out).astype(np.int64)


def _lower(x, world_ci) -> float:
    return world_ci(x, np.zeros_like(np.asarray(x, dtype=np.float64)))["lo95"]


def g0(*, oracle, reference, s_8192, s_32, l1_switch, blind: dict, world_ci) -> dict:
    o, ref = float(np.mean(oracle)), float(np.mean(reference))
    l1_lo, l1_mean = _lower(l1_switch, world_ci), float(np.mean(l1_switch))
    res = {
        "oracle": {"mean": o, "reference_mean": ref, "passed": o >= 0.6 * ref},
        "s_shuttle": {"k8192_mean": float(np.mean(s_8192)), "passed": float(np.mean(s_8192)) >= 0.5 * o},
        "l1_switch": {"lower_bound": l1_lo, "mean": l1_mean, "k32_mean": float(np.mean(s_32)),
                      "passed": l1_lo >= 0.5 * float(np.mean(s_32))},
        "blind": {},
    }
    ok = True
    for name, x in blind.items():
        m, p90 = float(np.mean(x)), float(np.percentile(x, 90))
        entry = {"mean": m, "p90": p90, "mean_ok": m <= 0.25 * l1_mean, "p90_ok": p90 <= 0.5 * l1_mean}
        entry["passed"] = entry["mean_ok"] and entry["p90_ok"]
        ok &= entry["passed"]
        res["blind"][name] = entry
    res["blind"]["passed"] = ok
    res["passed"] = all(res[k]["passed"] for k in ("oracle", "s_shuttle", "l1_switch", "blind"))
    return res


def g1(*, e, l1_switch, no_latch, one_module, component: bool, assays: dict, world_ci, classify) -> dict:
    lo = _lower(e, world_ci)
    c1, c2 = world_ci(e, no_latch), world_ci(e, one_module)
    res = {"score": {"lower_bound": lo, "l1_switch_mean": float(np.mean(l1_switch)),
                     "passed": lo >= 0.8 * float(np.mean(l1_switch))},
           "controls": {"no_latch": c1, "one_module": c2, "class": classify(c1, c2)},
           "component": {"passed": bool(component)},
           "assays": {**assays, "passed": all(bool(v) for v in assays.values())}}
    res["controls"]["passed"] = res["controls"]["class"] == "uses"
    res["passed"] = all(res[k]["passed"] for k in ("score", "controls", "component", "assays"))
    return res


def s2a(flags: list) -> dict:
    read = [f for f in flags if f is not None]
    n, k = len(read), sum(bool(f) for f in read)
    of = f"{k} of 8" if n == 8 else f"{k} of {n} read"
    if n == 0:
        wording = "not read"
    elif k == 0:
        wording = NULL_S2A + ("" if n == 8 else f" ({k} of {n} read)")
    elif k >= 7:
        wording = f"evolution found a working selector in {of} runs"
    else:
        wording = f"evolution found a working selector in {of} runs, not reliably"
    return {"working": k, "read": n, "wording": wording}


def _ordered(ci: dict, better: str, worse: str) -> str:
    if ci["lo"] > MARGIN:
        return better
    if ci["hi"] < -MARGIN:
        return worse
    if ci["lo"] >= -MARGIN and ci["hi"] <= MARGIN:
        return "as good"
    return "unclear"


def s2b(d, ga_working: list, rs_working: list, boot=boot_means, *, ga_all: list | None = None,
        rs_all: list | None = None) -> dict:
    """`ga_working`/`rs_working` are the paired runs' flags; rule 1 reads every read champion of
    either arm (`ga_all`, `rs_all`), paired or not."""
    d = np.asarray(d, dtype=np.float64)
    out = {"pairs": int(len(d)), "descriptive": len(d) < 8, "wording": S2B_WORDING}
    every = list(ga_all if ga_all is not None else ga_working) + list(rs_all if rs_all is not None else rs_working)
    if not any(bool(x) for x in every):
        return {**out, "label": "neither found a working selector"}
    ci = interval(d, boot)
    return {**out, **ci, "label": _ordered(ci, "evolution better", "random sampling better")}


def compare(d, boot=boot_means, *, a_working: list | None = None, b_working: list | None = None) -> dict:
    """The descriptive comparisons. Stage 3's against Stage 2's keeps S2-b's rule 1 (pass both arms'
    working flags); B-task's has no working branch (pass none)."""
    if a_working is not None and not any(bool(x) for x in list(a_working) + list(b_working or [])):
        return {"label": "neither found a working selector", "pairs": int(len(d))}
    ci = interval(d, boot)
    return {**ci, "label": _ordered(ci, "better", "worse")}


def s2c(count: int, n: int = 1024, *, unchecked: int = 0, ga_distribution: bool = False) -> dict:
    lo = 0.0 if count == 0 else float(beta.ppf(0.025, count, n - count + 1))
    hi = 1.0 if count == n else float(beta.ppf(0.975, count + 1, n - count))
    if unchecked:  # unchecked qualifiers are not failures: no ordinary interval
        lo = hi = None
        wording = f"at least {count} of {n} draws passed the screen and the full check; {unchecked} qualifiers unchecked"
    elif count == 0:
        wording = f"none of {n} draws passed the screen and the full check; that rate is below {hi:.4f}"
    else:
        wording = f"{count} of {n} draws passed the screen and the full check (95% {lo:.4f}-{hi:.4f})"
    res = {"count": count, "n": n, "lo": lo, "hi": hi, "unchecked": unchecked, "wording": wording,
           "generation_zero": bool(ga_distribution and count >= 10)}
    if res["generation_zero"]:
        res["wording"] += "; Stage 2 is answered at generation 0"
    return res
