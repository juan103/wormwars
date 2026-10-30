"""M1's shared pieces (docs/memory/M1-PLAN.md): 03mc's registered constants, the fresh-panel probe with in-batch arms
at the ramp's end, and the graph panel. Exploratory; CPU."""
from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "memory_spikes"))
import spikes as S  # noqa: E402
from wormwars.brain import Brain  # noqa: E402
from wormwars.exp03.twin import _Range  # noqa: E402

OUT = Path(os.environ.get("MEMORY_M1_OUT", ROOT / "runs" / "memory-m1"))  # a smoke test points it elsewhere
OUT.mkdir(parents=True, exist_ok=True)
REG = S.P.REGISTERED
START_FLOOR, SETTLE_TOL, REMAIN = REG["start_floor"], REG["settle_tolerance"], REG["remaining_fraction"]
ENSEMBLES = ("SH", "SH-route", "SH-class", "SH-mirror", "SH-recip")
NAMES = list(S.CON.names)
TURN_PLUS, TURN_MINUS = list(S.IFACE.turn_plus), list(S.IFACE.turn_minus)
READOUT = TURN_PLUS + TURN_MINUS
C = torch.zeros(S.CON.n, dtype=torch.float64)
C[TURN_PLUS] = 0.25
C[TURN_MINUS] = -0.25
FOOD_SENSORS = [NAMES.index(x) for x in ("AWAL", "AWAR", "AWCL", "AWCR", "ASEL", "ASER")]
PAIRS = [(i, NAMES.index(x[:-1] + "R")) for i, x in enumerate(NAMES) if x.endswith("L") and x[:-1] + "R" in NAMES]
assert len(PAIRS) == 99, "the plan's 99 mirror pairs"
RECORD = (0, 10, 30, 100, 300)
GENOMES, SEED, SEED2 = int(os.environ.get("MEMORY_M1_GENOMES", 1024)), 7600, 7700


def adjacency(chem):
    A = (np.asarray(chem) > 0).astype(np.int64)
    np.fill_diagonal(A, 0)
    return A


def neighbourhood(A, steps=1):
    """C1's K: the turn read-out with its chemical in-neighbours (A[i, j] = 1 for i -> j). Draft 2 uses one step:
    N2's two-step neighbourhood holds 207 of 302 neurons, past Fable's half-the-graph fallback."""
    K = np.zeros(len(A), bool)
    K[READOUT] = True
    for _ in range(steps):
        K = K | (A[:, K].sum(1) > 0)
    return K


def anatomy_core(chem):
    """C3: K ranked by degree inside K (in plus out), the top 30, ties broken by name."""
    A = adjacency(chem)
    K = np.where(neighbourhood(A))[0]
    sub = A[np.ix_(K, K)]
    deg = sub.sum(0) + sub.sum(1)
    order = sorted(range(len(K)), key=lambda i: (-deg[i], NAMES[K[i]]))
    return [NAMES[K[i]] for i in order[:30]]


def dump(obj, name):
    json.dump(obj, open(OUT / name, "w"), indent=1)


def measurements():
    m = json.load(open(ROOT / "experiments" / "03mc-p4-confirm" / "measurements.json"))
    return m["units"] if "units" in m else m


def ensemble_of(name):
    return name.rsplit("-", 1)[0]


def panel():
    """Draft 2: 6 graphs per ensemble at random from all 128; the selected graphs (top 03mc share, top settling
    cohort) listed apart; a graph in both roles is simulated once."""
    u = measurements()
    rng = np.random.default_rng(20261020)
    random_, selected = [], {}
    for e in ENSEMBLES:
        rows = sorted((k.split("/")[1], v) for k, v in u.items()
                      if k.startswith("graph/") and k.endswith("/long") and ensemble_of(k.split("/")[1]) == e)
        top_share = max(rows, key=lambda r: (r[1]["share"]["30"] or -1))[0]
        by_cohort = sorted(rows, key=lambda r: -r[1]["settled_and_remaining"])
        top_cohort = next(r[0] for r in by_cohort if r[0] != top_share)
        selected[e] = {"top_share": top_share, "top_cohort": top_cohort}
        random_ += [rows[i][0] for i in sorted(rng.choice(len(rows), 6, replace=False))]
    return random_, selected


MIN_ELIGIBLE = 10


def panel_valid(a, steady, eligible):
    """03mc's validity (p4mc.py terms and share_ok: finite terms, steady-contrast mean and start mean >= 1e-4), and at
    least MIN_ELIGIBLE eligible genomes, without which no eligible share exists."""
    return bool(np.isfinite(a).all() and np.isfinite(steady).all() and np.abs(steady).mean() >= 1e-4
                and a.mean() >= 1e-4 and eligible >= MIN_ELIGIBLE)


def nan_ratio(num, den):
    """num/den where den > 0, NaN elsewhere: an undefined ratio stays undefined (Astra, round 5)."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    out = np.full(np.broadcast(num, den).shape, np.nan)
    np.divide(num, den, out=out, where=den > 0)
    return out


def diagnostic_available(a, steady, d30):
    """The grower diagnostic's own draw: valid as a panel, and a positive tick-30 numerator over eligible genomes."""
    ok = a >= START_FLOOR
    return panel_valid(a, steady, int(ok.sum())) and float(d30[ok].sum()) > 0


def finite(v, where):
    """A non-finite state anywhere stops the run (M1-PLAN, definitions)."""
    if not torch.isfinite(v).all():
        raise RuntimeError(f"non-finite state {where}")
    return v


_INPUT = {"iface": S.IFACE, "bank": S.BANK}  # the probe's input: M0's interface and 03mc's bank unless probe_input


@contextmanager
def probe_input(iface, bank):
    """M6 option 0 (M6-0-PLAN.md): the probe's input built through another food mapping's interface and another
    stimulus bank, for every path that builds it (at, final_food: the probe, the follow-ups, the oscillation check's
    rerun and M4e's second pass). It does not nest. The read-out must be M0's, since the classifier's c' (C) is.
    Restored on exit."""
    for k in ("turn_plus", "turn_minus", "forward_plus", "forward_minus"):
        if list(getattr(iface, k)) != list(getattr(S.IFACE, k)):
            raise ValueError(f"the interface's {k} is not M0's: the classifier's read-out would be wrong")
    if _INPUT.get("active"):
        raise RuntimeError("probe_input does not nest")
    saved = dict(_INPUT)
    _INPUT.update(iface=iface, bank=bank, active=True)
    try:
        yield
    finally:
        _INPUT.clear()
        _INPUT.update(saved)


def final_food():
    """The probe's final food level: the bank's mean food."""
    b = _INPUT["bank"]
    return (b["food_left"] + b["food_right"]) / 2


def at(cfg, n, s, levels):
    b = _INPUT["bank"]
    return torch.cat([S._current(_INPUT["iface"], cfg, dict(b, food_left=lv, food_right=lv), n, s, "cpu")
                      for lv in levels], 1)


def raw(cfg, v):  # [S, rows]: 03's raw turn, row by row
    return torch.stack([S._readout(_INPUT["iface"], cfg, v[:, r:r + 1])[:, 1] for r in range(v.shape[1])], 1)


def ramp(g, cfg, warm=100, span=10, with_steady=False):
    """03mc's warm-up and ramp; returns the brain, the ramp-end state [S, 2, N] and the final food level, and with
    with_steady also the steady contrast (falling-start minus rising-start raw turn at the warm-up's end, [S])."""
    brain = Brain(g)
    s, n = g.n_strains, g.spec.n
    food = final_food()
    starts = (0.25 * food, 1.75 * food)
    v = brain.initial_state(2)
    cur = at(cfg, n, s, starts)
    for t in range(warm):
        v = finite(brain.step(v, cur), f"in the warm-up, tick {t + 1}")
    steady = raw(cfg, v)
    for t in range(span):
        v = finite(brain.step(v, at(cfg, n, s, [a + (food - a) * (t + 1) / span for a in starts])), f"in the ramp, tick {t + 1}")
    if with_steady:
        return brain, v, food, (steady[:, 1] - steady[:, 0]).double().numpy()
    return brain, v, food


def follow(brain, cfg, v, food, ticks, record=RECORD, window=None):
    """Continue the row pairs of v [S, 2P, N] under the final input. Returns, per recorded tick, the signed read-out
    difference [S, P] and the state differences dv [S, P, N]; with window, the settling range of rows 0 and 1 over
    the last window ticks (03mc's _Range)."""
    s, rows, n = v.shape
    cur = at(cfg, n, s, [food] * rows)
    out = {}

    def rec(t, v):
        r, a = raw(cfg, v), torch.tanh(v)
        out[t] = {"dy": (r[:, 0::2] - r[:, 1::2]).double(), "dv": (v[:, 0::2] - v[:, 1::2]).double(),
                  "da": (a[:, 0::2] - a[:, 1::2]).double()}

    rec(0, finite(v, "at the follow-up's start"))
    end = _Range()
    for t in range(1, ticks + 1):
        v = finite(brain.step(v, cur), f"in the follow-up, tick {t}")
        if t in record:
            rec(t, v)
        if window and t > ticks - window:
            end.add(v[:, :2])
    return out, (end.value() if window else None), v


def scaled(v, k):
    m = v.mean(1, keepdim=True)
    return m + k * (v - m)


def erased(v, idx):
    v = v.clone()
    v[:, :, idx] = v[:, :, idx].mean(1, keepdim=True)
    return v
