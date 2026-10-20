"""M2 pilot (docs/memory/M2-PILOT-PLAN.md): the classifier's rules as pure functions of recorded quantities, so that each
can be tested on constructed inputs. The trajectories, Newton and P live in pilot.py and equilibria.py. Exploratory."""
from __future__ import annotations

import numpy as np

LOCATE_NEAR = 1e-3        # a located root within this max-norm distance of the tick-2000 state
ACCURACY = 1e-9           # the error bound above which a root's identity is uncertain
DISTINCT = 1e-6           # two roots farther apart than this are distinct
FORECAST_FACTOR = 10.0    # the continuation may sit up to 10x above the forecast at the same tick
FLOOR = 1e-12
WINDOW = 100              # the last ticks of the continuation compared tick by tick
SLOW_AT_CAP = 0.1         # forecast still above this fraction of d0 at the cap: too slow to test
REMAIN = 0.1              # 03mc's remaining fraction of a, for the read-out difference between two roots
CANDIDATE_RANGE = 1e-4    # a settling range above this in both late windows makes an oscillation candidate
PERSIST = 0.9             # the range kept over the long continuation
RETURN_TOL, RETURNS = 0.01, 3
REFINE = 20              # integer-lag minima refined to fractional lags


def reached(dist, forecast, d0, near, capped, error=0.0):
    """dist, forecast: [T] max-norm distance of the float64 continuation from the root and of the linear forecast
    (P^32)^t x0, at matching ticks 1..T. near: the root within LOCATE_NEAR of the tick-2000 state. capped: T hit the cap.
    error: the located root's error bound; the continuation converges to the true root, which may sit that far from the
    located one, so the floor is max(FLOOR, 10 error) (Fable, round 4). Returns 'reached', 'slow', 'forecast failure',
    or 'not approaching'."""
    dist, forecast = np.asarray(dist, float), np.asarray(forecast, float)
    if not near:
        return "not approaching"
    if capped and forecast[-1] > SLOW_AT_CAP * d0:
        return "slow"
    w = slice(-WINDOW, None)
    floor = max(FLOOR, 10 * error)
    within = bool(np.all(dist[w] <= np.maximum(floor, FORECAST_FACTOR * forecast[w])))
    if d0 <= floor:  # already at the root (a float64 run ends on it): reached if it stays within the floor
        return "reached" if within else "not approaching"
    contracted = bool(dist[-1] <= d0 / 2)
    if within and contracted:
        return "reached"
    return "forecast failure" if dist[-1] < d0 else "not approaching"


def _shift_dev(x, L, need):
    """The largest deviation, over the last `need` periods sample by sample, between x(t) and x(t - L), with x(t - L)
    linearly interpolated for a fractional L; and the range of the stretch compared (the last need + 1 periods)."""
    n = len(x)
    span = int(np.ceil((need + 1) * L)) + 1
    if span > n:
        return np.inf, 0.0
    t = np.arange(n - int(np.floor(need * L)), n)
    src = t - L
    lo = np.floor(src).astype(int)
    w = (src - lo)[:, None]
    back = x[lo] * (1 - w) + x[np.minimum(lo + 1, n - 1)] * w
    tail = x[n - span:]
    return float(np.abs(x[t] - back).max()), float((tail.max(0) - tail.min(0)).max())


def returns(x, max_lag, tol=RETURN_TOL, need=RETURNS):
    """x: [T, D] a recorded stretch (substeps or ticks). The smallest period L, 2 <= L <= max_lag samples, possibly
    fractional, at which the whole of the last `need` periods repeats the period before it, sample by sample, within tol
    of the compared stretch's range (its last need + 1 periods), or None. Comparing whole periods, not isolated
    endpoints, rejects a tail whose excursions differ between returns (Astra, round 5); a fractional L, found by
    refining around the integer lags' local minima in ascending order, lets a cycle whose period is not a whole number
    of samples pass, and finds the fundamental period before its multiples (Fable, round 5). The interpolation needs
    fine sampling: at 32 substeps a tick (64 samples a period for a cycle of 2 ticks) it is far inside the tolerance. A finite tolerance cannot exclude a
    quasi-periodic orbit that repeats closely."""
    x = np.asarray(x, float)
    devs = []
    for L in range(2, max_lag + 1):
        d, rng = _shift_dev(x, L, need)
        if not np.isfinite(d):
            break
        if rng <= 0:
            return None
        devs.append(d / rng)
    if not devs:
        return None
    rel = np.array(devs)
    lags = np.arange(2, 2 + len(rel))
    minima = [k for k in range(len(rel)) if (k == 0 or rel[k] <= rel[k - 1]) and (k == len(rel) - 1 or rel[k] <= rel[k + 1])]
    minima = sorted(sorted(minima, key=lambda k: rel[k])[:REFINE])  # the deepest minima only, bounding the cost on noise
    for k in minima:  # ascending lag, so the fundamental period is found before its multiples
        if rel[k] <= tol:
            return float(lags[k])
        for Lf in np.arange(lags[k] - 1, lags[k] + 1.0001, 0.02):
            if Lf < 2:
                continue
            d, rng = _shift_dev(x, Lf, need)
            if np.isfinite(d) and rng > 0 and d <= tol * rng:
                return float(Lf)
    return None


def oscillation(candidate, period, range_late, range_ref, roots_from_orbit):
    """A candidate history: confirmed if a period was found, the long continuation kept PERSIST of the range, at least
    one root was located from the orbit, and none of those is stable or marginal under P (roots_from_orbit: their
    verdicts). The root condition is a conservative veto, not a contradiction: a stable cycle can coexist with a stable
    root, so it can exclude genuine cycles (Astra, Fable, round 4). Returns 'persistent oscillation', 'candidate around
    a stable root', 'no root located from the orbit', or 'unconfirmed candidate'."""
    if not candidate:
        return None
    if not roots_from_orbit:
        return "no root located from the orbit"
    if any(v in ("stable", "marginal") for v in roots_from_orbit):
        return "candidate around a stable root"
    if period is not None and range_late >= PERSIST * range_ref:
        return "persistent oscillation"
    return "unconfirmed candidate"


def classify(h0, h1, root_distance, readout_difference, a, osc0=None, osc1=None, distinct=DISTINCT):
    """Per genome, in the plan's order of precedence. h0, h1: per history a dict with 'located' (bool), 'error'
    (the error bound), 'stability' ('stable'|'unstable'|'marginal'), 'reach' (the result of reached()). root_distance:
    max-norm distance between the two histories' roots; readout_difference: |c'(tanh r1 - tanh r0)|; a: the genome's
    start difference. osc0, osc1: the result of oscillation() for each history (None if not a candidate). distinct: the
    distinct-root threshold (the plan's sensitivity check varies it)."""
    hs = (h0, h1)
    good = [h["located"] and h["error"] <= ACCURACY and h["reach"] == "reached" and h["stability"] == "stable" for h in hs]
    if all(good):
        if root_distance <= distinct:
            return "fading", None
        if readout_difference >= REMAIN * a:
            return "separate states", None
        return "separate states, read-out silent", None
    osc = [o for o in (osc0, osc1) if o is not None]
    if "persistent oscillation" in osc:  # ahead of every unresolved verdict (Fable, round 5)
        return "persistent oscillation", None
    reasons = []
    for h in hs:
        if not h["located"]:
            reasons.append("Newton failure")
        elif h["error"] > ACCURACY:
            reasons.append("ill-conditioned")
        elif h["stability"] != "stable":
            reasons.append("unstable or marginal root")
        elif h["reach"] == "slow":
            reasons.append("slow")
        elif h["reach"] != "reached":
            reasons.append("located root not reached")
    reasons += [o for o in osc if o != "persistent oscillation"]
    return "unresolved", "; ".join(sorted(set(reasons))) or "unspecified"


def test_rules():
    d0 = 1e-4
    t = np.arange(1, 301)
    fc = d0 * 0.95 ** t
    assert reached(fc, fc, d0, True, False) == "reached"  # exact exponential convergence passes (draft 3 failed it)
    assert reached(fc * 5, fc, d0, True, False) == "reached"
    assert reached(fc * 50, fc, d0, True, False) == "forecast failure"
    assert reached(np.full(300, d0), fc, d0, True, False) == "not approaching"
    assert reached(fc, fc, d0, False, False) == "not approaching"
    assert reached(np.full(300, 1e-15), np.zeros(300), 0.0, True, False, error=1e-13) == "reached"  # starts on its root
    assert reached(np.full(300, 1e-6), np.zeros(300), 0.0, True, False, error=1e-13) == "not approaching"  # and leaves it
    slow = d0 * (1 - 1e-6) ** t
    assert reached(slow, slow, d0, True, True) == "slow"
    grow = d0 * (1.0 + 0.5 * np.sin(t / 30.0)) * 0.97 ** t  # non-normal hump that the forecast carries
    assert reached(grow, grow, d0, True, False) == "reached"
    # returns: a period-12 sine is found at 12; a damped one with fast decay is not; a constant has no range
    s = np.sin(2 * np.pi * np.arange(600) / 12.0)[:, None]
    assert returns(s, 50) == 12
    # a period that is not a whole number of samples, sampled as finely as the candidates are (at 32 substeps a tick a
    # cycle of 2 ticks or more has at least 64 samples a period; this one has 153.6; linear interpolation is then far
    # inside the 1% tolerance)
    s5 = np.sin(2 * np.pi * np.arange(800) / 153.6)[:, None]
    L = returns(s5, 200)
    assert L is not None and abs(L - 153.6) <= 0.5, L  # within half a sample of the period
    sharp = np.tanh(4 * np.sin(2 * np.pi * np.arange(800) / 153.6))[:, None]  # a sharper waveform, same period
    assert returns(sharp, 200) is not None
    assert returns(s * np.exp(-0.01 * np.arange(600))[:, None], 50) is None
    assert returns(np.ones((600, 1)), 50) is None
    irregular = np.array([0, 1, 0, 2, 0, 3, 0, 4, 0], float)[:, None]  # Astra, round 5: endpoints return, excursions differ
    assert returns(irregular, 4) is None
    assert returns(np.tile(irregular[:-1], (6, 1)), 20) == 8.0  # the same excursions, repeated, are a period
    assert oscillation(True, 12, 1.0, 1.0, ["unstable"]) == "persistent oscillation"
    assert oscillation(True, 12, 1.0, 1.0, ["marginal"]) == "candidate around a stable root"  # the slow spiral
    assert oscillation(True, 12, 0.5, 1.0, ["unstable"]) == "unconfirmed candidate"
    assert oscillation(True, 12, 1.0, 1.0, []) == "no root located from the orbit"  # not confirmed vacuously
    assert reached(fc, fc, d0, True, False, error=0.0) == "reached"
    assert reached(fc + 5e-10, fc, d0, True, False, error=0.0) == "forecast failure"  # 5e-10 above the 1e-12 floor
    assert reached(fc + 5e-10, fc, d0, True, False, error=1e-10) == "reached"  # within 10x the root's error bound
    assert oscillation(False, 12, 1.0, 1.0, []) is None
    ok = {"located": True, "error": 1e-14, "stability": "stable", "reach": "reached"}
    assert classify(ok, ok, 0.0, 0.0, 0.1) == ("fading", None)
    assert classify(ok, ok, 1.0, 0.5, 0.1) == ("separate states", None)
    assert classify(ok, ok, 1.0, 0.001, 0.1) == ("separate states, read-out silent", None)
    assert classify(ok, {**ok, "error": 1e-6}, 1.0, 0.5, 0.1) == ("unresolved", "ill-conditioned")
    assert classify(ok, {**ok, "stability": "marginal"}, 1.0, 0.5, 0.1)[0] == "unresolved"
    assert classify(ok, {**ok, "reach": "slow"}, 1.0, 0.5, 0.1) == ("unresolved", "slow")
    no = {"located": False, "error": np.inf, "stability": None, "reach": None}
    assert classify(ok, no, 1.0, 0.5, 0.1, None, "persistent oscillation") == ("persistent oscillation", None)
    ill = {**ok, "error": 1e-6}
    assert classify(ill, no, 1.0, 0.5, 0.1, None, "persistent oscillation") == ("persistent oscillation", None)
    assert classify(ill, ok, 1.0, 0.5, 0.1, None, None) == ("unresolved", "ill-conditioned")
    assert classify(ok, no, 1.0, 0.5, 0.1, None, "candidate around a stable root") == \
        ("unresolved", "Newton failure; candidate around a stable root")
