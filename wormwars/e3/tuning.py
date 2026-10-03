"""E3b-1's tuning pieces and registered statistics (experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md §3, §7).

- `start_organism`: the seed E + W2, or arm R's degraded start (E's no-latch variant + W2, on E's mask).
- `scales`: the mutation factors. Every chemical edge with a grafted end, and every grafted neuron's τ and
  bias, at 0.25; frozen (0): the relays' τ and bias (as in E3a's Stage 3), W2's two neurons (τ, bias) and
  their 16 output edges, the worm block, and every gap junction.
- `assert_frozen`: the end-of-run assertion, every frozen parameter bitwise equal to the start's.
- `gate`: the stratified one-sided Welch test on the two schedules' differences, with its labels, zero
  spread, "not read" below 4 runs per schedule, and "better, but concentrated".
- `sign_flip`: the exact sign-flip test on the estimand itself.
- `paired`: S-gen's one-sided paired t-test. `holm`: Holm over a fixed family, an unread test at p = 1.
- `normalised`: a reading over a denominator, None ("not read") when the denominator is 0.
"""

from __future__ import annotations

import itertools
import math

import numpy as np
import torch
from scipy import stats

from .. import graft as G
from ..brain import BrainSpec, Genome
from ..e4s import comparator as C
from . import maze_organisms as MO
from . import organism as O
from .samplers import _grafted, _scales

FACTOR = 0.25
W2_NEURONS = ("E3B_WL", "E3B_WR")
MIN_RUNS = 4
ALPHA = 0.05


def start_organism(kind: str, con, l1, bcfg) -> MO.Organism:
    """"seed": E + W2 (the frozen seed). "degraded": E's no-latch variant + W2, on E's mask (arm R)."""
    if kind == "seed":
        return MO.maze_organism(con, MO.seed("E", l1, bcfg, con=con), "W2", bcfg)
    if kind != "degraded":
        raise ValueError("the start organisms are 'seed' and 'degraded'")
    module = O.no_latch(l1)
    ext = G.graft_connectome(con, module)
    genome = C.carrier_genome(ext, module, bcfg, forward=MO.CARRIER_FORWARD, turn=MO.REST_TURN["W0"])
    return MO.maze_organism(con, MO.Seed("E-no-latch", module, ext, genome), "W2", bcfg)


def scales(ext) -> dict:
    spec, edges, nodes = _grafted(ext)
    w2 = torch.tensor([ext.index(n) for n in W2_NEURONS])
    edges = edges & ~torch.isin(spec.chem_i, w2)
    nodes = nodes.clone()
    nodes[w2] = False
    return _scales(spec, edges, nodes, nodes, FACTOR)


def assert_frozen(start: Genome, final: Genome, ext) -> None:
    """Every frozen parameter of every strain of `final` equals strain 0 of `start`, bitwise."""
    sc = scales(ext)
    for name, key in (("w", "w"), ("tau", "tau"), ("bias", "bias"), ("g", "g")):
        frozen = sc[key] == 0
        a = getattr(start, name)[0].cpu()[frozen]
        b = getattr(final, name).cpu()[:, frozen]
        if not torch.equal(b, a.unsqueeze(0).expand_as(b)):
            raise AssertionError(f"a frozen parameter changed ({name})")


def _labels(p_greater, p_less):
    if p_greater <= ALPHA:
        return "better"
    if p_less <= ALPHA:
        return "worse"
    return "unclear"


def gate(d_a, d_f, *, alternative: str = "greater", legs_medians=None, min_runs: int = MIN_RUNS) -> dict:
    """The stratified estimand Δ = (mean d_A + mean d_F) / 2 and its one-sided Welch test (§7)."""
    a, f = np.asarray(d_a, dtype=np.float64), np.asarray(d_f, dtype=np.float64)
    n_a, n_f = len(a), len(f)
    if n_a < min_runs or n_f < min_runs:
        return {"label": "not read", "n_a": n_a, "n_f": n_f, "p": 1.0}
    est = (a.mean() + f.mean()) / 2
    va, vf = a.var(ddof=1) / n_a, f.var(ddof=1) / n_f
    se = math.sqrt(va + vf) / 2
    if se == 0:
        df = None
        p_greater = 0.0 if est > 0 else 1.0
        p_less = 0.0 if est < 0 else 1.0
        lower = est
    else:
        df = (va + vf) ** 2 / (va ** 2 / (n_a - 1) + vf ** 2 / (n_f - 1))
        t = est / se
        p_greater, p_less = float(stats.t.sf(t, df)), float(stats.t.cdf(t, df))
        lower = est - float(stats.t.ppf(0.95, df)) * se
    label = _labels(p_greater, p_less)
    if label == "better" and legs_medians is not None:
        legs = np.asarray(legs_medians, dtype=np.float64)
        if (legs >= 2).sum() < math.ceil(len(legs) / 2):
            label = "better, but concentrated"
    return {"label": label, "estimate": float(est), "se": float(se), "df": df, "p_greater": p_greater,
            "p_less": p_less, "p": p_greater if alternative == "greater" else p_less, "lower_bound_95": float(lower),
            "n_a": n_a, "n_f": n_f, "spread": float(math.sqrt((a.var(ddof=1) + f.var(ddof=1)) / 2))}


def sign_flip(d_a, d_f) -> float:
    """One-sided ("greater") exact sign-flip p over 2^(n_A + n_F) patterns, on the estimand."""
    a, f = np.asarray(d_a, dtype=np.float64), np.asarray(d_f, dtype=np.float64)
    n_a = len(a)
    d = np.concatenate([a, f])
    w = np.concatenate([np.full(n_a, 0.5 / n_a), np.full(len(f), 0.5 / len(f))])
    obs = float((d * w).sum())
    signs = np.array(list(itertools.product((1.0, -1.0), repeat=len(d))))
    null = signs @ (d * w)
    return float(np.mean(null >= obs - 1e-12))


def paired(diffs, *, min_runs: int = MIN_RUNS) -> dict:
    """S-gen: a one-sided paired t-test, alternative "greater"."""
    d = np.asarray(diffs, dtype=np.float64)
    if len(d) < min_runs:
        return {"label": "not read", "n": len(d), "p": 1.0}
    m, se = d.mean(), d.std(ddof=1) / math.sqrt(len(d))
    if se == 0:
        p = 0.0 if m > 0 else 1.0
    else:
        p = float(stats.t.sf(m / se, len(d) - 1))
    return {"label": "read", "n": len(d), "mean": float(m), "se": float(se), "p": p}


def holm(pvalues: dict, alpha: float = ALPHA) -> dict:
    """Holm's step-down over the whole family; a test that is not read (None) enters with p = 1."""
    names = list(pvalues)
    ps = {k: (1.0 if v is None else float(v)) for k, v in pvalues.items()}
    order = sorted(names, key=lambda k: ps[k])
    m, running, out = len(names), 0.0, {}
    for i, k in enumerate(order):
        running = max(running, min(1.0, (m - i) * ps[k]))
        out[k] = {"p": ps[k], "p_holm": running, "rejected": running <= alpha, "read": pvalues[k] is not None}
    return out


def normalised(x, denominator: float):
    if denominator == 0:
        return None
    return np.asarray(x, dtype=np.float64) / denominator
