"""M4a (docs/memory/M4A-PLAN.md, draft 4): hold-window cuts of the anatomy core C3's internal chemical edges, against
sampled external cuts of equal size (20 stratified on endpoint degree, 10 on anatomical weight; the primary control),
uniform sets and the whole exterior (descriptive), and draft 2's effect-matched controls (secondary, flagged); Part 2
starts the separate-states genomes from their roots. Each panel writes its own files under runs/memory-m4a/ and is
skipped when they exist. The cost guard projects the run after the first N2 panel. The readings are m4a_read.py's.
JSON outputs are committed; arrays (.npz) stay local. CPU only.
Usage: python scripts/memory_m4/m4a.py [stage ...]   (stages: n2 part2 reference; all, in that order, by default)"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
import census  # noqa: E402

P, c, E = census.P, census.c, census.E
from wormwars import accounting as acct  # noqa: E402
from wormwars.brain import Brain  # noqa: E402

torch.set_grad_enabled(False)
OUT = Path(os.environ.get("MEMORY_M4A_OUT", ROOT / "runs" / "memory-m4a"))
OUT.mkdir(parents=True, exist_ok=True)
CENSUS = ROOT / "runs" / "memory-m2-census"
N_PANEL = int(os.environ.get("MEMORY_M4A_PANEL", 1024))
TICKS = 100
ARMS = {"C3-early-30": (1, 30), "C3-early-10": (1, 10), "C3-late-30": (31, 60)}  # windows, ticks after the ramp's end
READ = {"C3-early-30": 60, "C3-early-10": 60, "C3-late-30": 100, "C3-write": 60, "gaps-off-30": 60}
ORDERS, GRID, BISECT = 3, 16, 8
TOL_REL, TOL_ABS, SMALL, FLOOR = 0.2, 0.01, 0.05, 1e-9
MATCH_TICK = 3  # the window's third tick: nothing later chooses a control (Astra)
SEED_ORDERS = 20261101
GATE = 1e-4  # the intact arm against the census
PART2_TICKS, PART2_CUT = 330, (1, 30)
SAME_ROOT = 1e-6
SMOKE = bool(os.environ.get("MEMORY_M4A_SMOKE"))  # a small panel: the census gate is skipped (other draws)
N_DRAWS, N_WEIGHT_DRAWS, N_UNIFORM, N_PART2_DRAWS, BINS = 20, 10, 5, 5, 5  # the random external cuts (draft 3)
SEED_DRAWS = 20261103


def core():
    """C3, M1's anatomy core (N2's neurons), as indices."""
    return [c.NAMES.index(x) for x in c.anatomy_core(c.S.CON.chem)]


def edge_sets(spec, core_idx):
    """C3's internal off-diagonal chemical edges, and the external ones (both endpoints outside C3), as edge indices.
    Autapses are never cut."""
    i, j = spec.chem_i.numpy(), spec.chem_j.numpy()
    inc = np.zeros(spec.n, bool)
    inc[core_idx] = True
    off = i != j
    return np.where(inc[i] & inc[j] & off)[0], np.where(~inc[i] & ~inc[j] & off)[0]


def degrees(spec):
    """Each neuron's chemical degree (in plus out, autapses excluded) in the graph's own wiring."""
    i, j = spec.chem_i.numpy(), spec.chem_j.numpy()
    off = i != j
    return np.bincount(i[off], minlength=spec.n) + np.bincount(j[off], minlength=spec.n)


def endpoint_degree(spec, edges):
    d = degrees(spec)
    return d[spec.chem_i.numpy()[edges]] + d[spec.chem_j.numpy()[edges]]


def stratified_draws(spec, internal, external, n, seed, key=None):
    """n random sets of len(internal) external edges whose key follows C3's: by default the summed endpoint degree
    (Fable, round 2); with key = the anatomical weight (|w| is proportional to it in Genome.random), the weight. C3's
    edges are binned at the quintiles of their key, and each draw takes as many external edges from each bin as C3
    has there, without replacement; a bin short of external edges is filled with the unused external edges nearest
    its range (random tie-break). The same draws for every genome of a panel."""
    rng = np.random.default_rng(seed)
    if key is None:
        di, de = endpoint_degree(spec, internal), endpoint_degree(spec, external)
    else:
        di, de = key[internal], key[external]
    edges_q = np.quantile(di, np.linspace(0, 1, BINS + 1))
    edges_q[0], edges_q[-1] = -np.inf, np.inf
    bi = np.clip(np.searchsorted(edges_q, di, side="right") - 1, 0, BINS - 1)
    be = np.clip(np.searchsorted(edges_q, de, side="right") - 1, 0, BINS - 1)
    lo_hi = [(di[bi == b].min(), di[bi == b].max()) if (bi == b).any() else (0, 0) for b in range(BINS)]
    out = []
    for _ in range(n):
        free = np.ones(len(external), bool)
        take = []
        for b in range(BINS):
            need = int((bi == b).sum())
            pool = np.where((be == b) & free)[0]
            got = rng.choice(pool, min(need, len(pool)), replace=False) if len(pool) else np.zeros(0, int)
            free[got] = False
            short = need - len(got)
            if short > 0:
                rest = np.where(free)[0]
                lo, hi = lo_hi[b]
                dist = np.maximum(0, np.maximum(lo - de[rest], de[rest] - hi)) + rng.random(len(rest)) * 1e-3
                extra = rest[np.argsort(dist)[:short]]
                free[extra] = False
                got = np.concatenate([got, extra])
            take.append(got)
        out.append(external[np.concatenate(take)])
    return out


def uniform_draws(internal, external, n, seed):
    rng = np.random.default_rng(seed)
    return [rng.choice(external, len(internal), replace=False) for _ in range(n)]


def cut(g, mask):
    """The genome with the chemical weights on mask [S, E_chem] (bool) set to zero; nothing else changes."""
    w = g.w.clone()
    w[torch.as_tensor(mask)] = 0
    return g.with_params(w=w)


def common_mask(g, edges):
    m = np.zeros(tuple(g.w.shape), bool)
    m[:, edges] = True
    return m


def prefix_mask(g, order, k):
    """Per strain s, the first k[s] edges of its own order [S, E_ext] (k = 0: none)."""
    m = np.zeros(tuple(g.w.shape), bool)
    take = np.arange(order.shape[1])[None, :] < np.asarray(k)[:, None]
    rows = np.repeat(np.arange(order.shape[0])[:, None], order.shape[1], 1)
    m[rows[take], order[take]] = True
    return m


def norms(v, core_idx):
    """[S, 2, N] -> the full-state separation and its part on C3, per strain."""
    dv = (v[:, 0] - v[:, 1]).double()
    return dv.norm(dim=1).numpy(), dv[:, core_idx].norm(dim=1).numpy()


def follow_arm(brain, brain_cut, cfg, v0, food, window, ticks, core_idx):
    """From the tick-0 state v0 [S, 2, N] under the final input: the cut brain for the window's ticks, the intact one
    otherwise. Records per tick the separation, its part on C3, and |dy|; returns them [S, ticks + 1] and the state at
    every tick a window may start from."""
    s, rows, n = v0.shape
    cur = c.at(cfg, n, s, [food] * rows)
    rec = {k: np.zeros((s, ticks + 1)) for k in ("nv", "nc", "dy")}
    starts = {}

    def put(t, v):
        rec["nv"][:, t], rec["nc"][:, t] = norms(v, core_idx)
        r = c.raw(cfg, v)
        rec["dy"][:, t] = (r[:, 0] - r[:, 1]).abs().double().numpy()

    v = v0
    put(0, v)
    for t in range(1, ticks + 1):
        b = brain_cut if (window and window[0] <= t <= window[1]) else brain
        v = c.finite(b.step(v, cur), f"tick {t}")
        put(t, v)
        if t in (30,):
            starts[t] = v.clone()
    return rec, starts


def ramp_with(g, g_cut, cfg, warm=100, span=10):
    """M1's warm-up and ramp (common.ramp), with the cut brain during the ramp's ticks only (C3-write)."""
    brain, bcut = Brain(g), Brain(g_cut)
    s, n = g.n_strains, g.spec.n
    food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
    starts = (0.25 * food, 1.75 * food)
    v = brain.initial_state(2)
    cur = c.at(cfg, n, s, starts)
    for t in range(warm):
        v = c.finite(brain.step(v, cur), f"in the warm-up, tick {t + 1}")
    for t in range(span):
        v = c.finite(bcut.step(v, c.at(cfg, n, s, [a + (food - a) * (t + 1) / span for a in starts])), f"ramp {t + 1}")
    return v, food


# ------------------------------------------------------------------------------------------------------------ matching
def tol(mstar):
    return np.where(np.abs(mstar) < SMALL, TOL_ABS, TOL_REL * np.abs(mstar))


def grid(kmax):
    return np.unique(np.round(np.geomspace(1, kmax, GRID)).astype(int))


def match(evalm, kmax, mstar):
    """The per-genome control search for one order (the plan's steps 2 and 3). evalm(k [S]) -> m [S], the three-tick
    attenuation with each strain's first k[s] external edges cut. Every grid value is evaluated (monotonicity is not
    assumed); then, in increasing k, each pair of adjacent grid values whose m brackets m* is bisected, at most BISECT
    steps, while it can still give a k below the best match so far. Returns the smallest matching k per strain (0 if
    none) and every candidate evaluated, as (k, m) lists."""
    S_ = len(mstar)
    ks = grid(kmax)
    cand = [[] for _ in range(S_)]
    ms = np.stack([evalm(np.full(S_, k)) for k in ks], 1)  # [S, G]
    for s_ in range(S_):
        cand[s_] += list(zip(ks.tolist(), ms[s_].tolist()))
    t = tol(mstar)
    with np.errstate(invalid="ignore"):
        ok = (np.abs(ms - mstar[:, None]) <= t[:, None]) & np.isfinite(mstar)[:, None]
    best = np.where(ok.any(1), ks[np.argmax(ok, 1)], 0)
    for j in range(len(ks) - 1):
        lo_m, hi_m = ms[:, j] - mstar, ms[:, j + 1] - mstar
        active = (lo_m * hi_m < 0) & ((best == 0) | (best > ks[j])) & (ks[j + 1] - ks[j] > 1)
        if not active.any():
            continue
        lo, hi, sign_lo = np.full(S_, ks[j]), np.full(S_, ks[j + 1]), np.sign(lo_m)
        for _ in range(BISECT):
            run = active & (hi - lo > 1)
            if not run.any():
                break
            mid = np.where(run, (lo + hi) // 2, 0)
            m = evalm(mid)
            for s_ in np.where(run)[0]:
                cand[s_].append((int(mid[s_]), float(m[s_])))
                if abs(m[s_] - mstar[s_]) <= t[s_] and (best[s_] == 0 or mid[s_] < best[s_]):
                    best[s_] = mid[s_]
            right = np.sign(m - mstar) == sign_lo  # m* lies above mid
            lo = np.where(run & right, mid, lo)
            hi = np.where(run & ~right, mid, hi)
    bad = ~np.isfinite(mstar)
    best[bad] = 0
    return best, cand


def three_ticks(brain, v, cur):
    for _ in range(MATCH_TICK):
        v = brain.step(v, cur)
    return v


def matched_controls(g, v_t0, cur, internal, external, make_brain, sep):
    """The plan's matching for one window start v_t0 [S, 2, N]: m* for C3's cut, then ORDERS orders of external
    edges. sep(v) -> the separation [S]. Returns m*, the chosen k [ORDERS, S], the orders, and the balance quantities
    at the window's third tick for the C3 cut and each chosen control."""
    v_int = three_ticks(make_brain(g), v_t0, cur)
    base = sep(v_int)
    with np.errstate(divide="ignore", invalid="ignore"):
        v_c3 = three_ticks(make_brain(cut(g, common_mask(g, internal))), v_t0, cur)
        mstar = np.where(base > FLOOR, 1 - sep(v_c3) / base, np.nan)
    rng = np.random.default_rng(SEED_ORDERS)
    orders = np.stack([np.stack([rng.permutation(external) for _ in range(g.n_strains)]) for _ in range(ORDERS)])
    ks = np.zeros((ORDERS, g.n_strains), int)
    ncand = np.zeros((ORDERS, g.n_strains), int)
    ends = {"C3": v_c3, "intact": v_int}
    for o in range(ORDERS):
        def evalm(k, o=o):
            with np.errstate(divide="ignore", invalid="ignore"):
                return np.where(base > FLOOR, 1 - sep(three_ticks(make_brain(cut(g, prefix_mask(g, orders[o], k))), v_t0, cur)) / base, np.nan)
        best, cand = match(evalm, len(external), mstar)  # a non-finite m* (zero denominator) matches nothing
        ks[o], ncand[o] = best, [len(x) for x in cand]
        ends[f"ctrl{o}"] = three_ticks(make_brain(cut(g, prefix_mask(g, orders[o], best))), v_t0, cur)
    return mstar, ks, orders, ncand, ends


def balance(cfg, ends, v_int_key="intact"):
    """At the window's third tick: the read-out attenuation and the displacement of the histories' mean state, per
    strain, for the C3 cut and each control, against the intact run."""
    out = {}
    r0 = c.raw(cfg, ends[v_int_key])
    y0 = (r0[:, 0] - r0[:, 1]).abs().double().numpy()
    m0 = ends[v_int_key].mean(1).double()
    for k, v in ends.items():
        if k == v_int_key:
            continue
        r = c.raw(cfg, v)
        with np.errstate(divide="ignore", invalid="ignore"):
            out[k] = {"readout_att": 1 - (r[:, 0] - r[:, 1]).abs().double().numpy() / y0,
                      "mean_disp": (v.mean(1).double() - m0).norm(dim=1).numpy(), "y_intact": y0}
    return out


# --------------------------------------------------------------------------------------------------------------- part 1
def census_record(name):
    r = json.load(open(CENSUS / f"{name}.json"))
    return {gr["genome"]: gr for gr in r["genomes"]}


def run_part1(name, gname, seed, arms, n_draws=N_DRAWS, n_weight=N_WEIGHT_DRAWS, n_uniform=N_UNIFORM, matched=True):
    """One panel: the intact arm; for each maintenance arm, C3's cut, the stratified random external cuts (the primary
    control), uniform random external cuts and the whole exterior (descriptive), and the effect-matched controls
    (secondary, flagged); for N2 the write and gaps arms. Writes <name>.json and <name>.npz."""
    if (OUT / f"{name}.json").exists():
        return
    t0 = time.time()
    g, cfg = c.S.genomes(census.graph_of(gname), N_PANEL, seed)
    cidx = core()
    internal, external = edge_sets(g.spec, cidx)
    strat = stratified_draws(g.spec, internal, external, n_draws, SEED_DRAWS)
    if n_weight:  # weight-stratified draws join the primary control (C3's edges carry about twice the |w|)
        strat += stratified_draws(g.spec, internal, external, n_weight, SEED_DRAWS + 2, key=g.spec.chem_anat.numpy())
    unif = uniform_draws(internal, external, n_uniform, SEED_DRAWS + 1)
    brain, v0, food = c.ramp(g, cfg)
    s_, rows, n = v0.shape
    cur = c.at(cfg, n, s_, [food] * rows)
    absw = g.w.abs().double().mean(0).numpy()  # per edge, the mean |w| over genomes
    rec = {"panel": name, "graph": gname, "seed": seed, "internal_edges": int(len(internal)),
           "external_edges": int(len(external)), "arms": {},
           "cut_sets": {"C3": {"endpoint_degree": float(endpoint_degree(g.spec, internal).mean()),
                               "sum_abs_w": float(absw[internal].sum())},
                        **{f"rand{d}": {"endpoint_degree": float(endpoint_degree(g.spec, e).mean()),
                                        "sum_abs_w": float(absw[e].sum()),
                                        "stratified_on": "degree" if d < n_draws else "weight"} for d, e in enumerate(strat)},
                        **{f"unif{d}": {"endpoint_degree": float(endpoint_degree(g.spec, e).mean()),
                                        "sum_abs_w": float(absw[e].sum())} for d, e in enumerate(unif)},
                        "exterior": {"endpoint_degree": float(endpoint_degree(g.spec, external).mean()),
                                     "sum_abs_w": float(absw[external].sum())}}}
    arrays = {}
    intact, starts = follow_arm(brain, brain, cfg, v0, food, None, TICKS, cidx)
    arrays["intact"] = intact

    # the gate: the intact arm against the census's a and |dy(30)| (eligible genomes)
    cen = census_record(name)
    ids = np.array(sorted(i for i in cen if i < N_PANEL))
    gap_a = np.abs(intact["dy"][ids, 0] - np.array([cen[i]["a"] for i in ids])).max()
    gap_30 = np.abs(intact["dy"][ids, 30] - np.array([cen[i]["d30"] for i in ids])).max()
    rec["gate"] = {"max_gap_a": float(gap_a), "max_gap_d30": float(gap_30), "eligible": int(len(ids))}
    if max(gap_a, gap_30) > GATE and not SMOKE:
        raise SystemExit(f"{name}: the intact arm does not reproduce the census ({gap_a:.2e}, {gap_30:.2e})")

    sep = lambda v: norms(v, cidx)[0]  # noqa: E731
    matches = {}
    if matched:
        for start_key, t_start in (("early", 0), ("late", 30)):
            if not any(a in arms for a in ARMS if (ARMS[a][0] == 1) == (start_key == "early")):
                continue
            v_t0 = v0 if t_start == 0 else starts[30]
            mstar, ks, orders, ncand, ends = matched_controls(g, v_t0, cur, internal, external, Brain, sep)
            matches[start_key] = {"mstar": mstar, "k": ks, "ncand": ncand, "balance": balance(cfg, ends), "orders": orders}
            arrays[f"match_{start_key}_mstar"], arrays[f"match_{start_key}_k"] = mstar, ks
            for k_, v_ in matches[start_key]["balance"].items():
                for q, x in v_.items():
                    arrays[f"balance_{start_key}_{k_}_{q}"] = x

    def run_cut(edges, win):
        return follow_arm(brain, Brain(cut(g, common_mask(g, edges))), cfg, v0, food, win, TICKS, cidx)[0]

    for arm in arms:
        if arm in ARMS:
            win = ARMS[arm]
            arrays[arm] = run_cut(internal, win)
            for d, e in enumerate(strat):
                arrays[f"{arm}_rand{d}"] = run_cut(e, win)
            if arm == "C3-early-30":
                for d, e in enumerate(unif):
                    arrays[f"{arm}_unif{d}"] = run_cut(e, win)
            arrays[f"{arm}_exterior"] = run_cut(external, win)
            if matched:
                mk = matches["early" if win[0] == 1 else "late"]
                for o in range(ORDERS):
                    bo = Brain(cut(g, prefix_mask(g, mk["orders"][o], mk["k"][o])))
                    arrays[f"{arm}_ctrl{o}"], _ = follow_arm(brain, bo, cfg, v0, food, win, TICKS, cidx)
        elif arm == "C3-write":
            vw, _ = ramp_with(g, cut(g, common_mask(g, internal)), cfg)
            arrays[arm], _ = follow_arm(brain, brain, cfg, vw, food, None, TICKS, cidx)
        elif arm == "gaps-off-30":
            bg = Brain(g.with_params(g=torch.zeros_like(g.g)))
            arrays[arm], _ = follow_arm(brain, bg, cfg, v0, food, (1, 30), TICKS, cidx)
        rec["arms"][arm] = {"done": True}
        print(f"  {name} {arm} {time.time() - t0:.0f} s", flush=True)

    flat = {}
    for k, v in arrays.items():
        if isinstance(v, dict):
            for q, x in v.items():
                flat[f"{k}__{q}"] = np.asarray(x, np.float32 if q in ("nv", "nc", "dy") else np.float64)
        else:
            flat[k] = np.asarray(v)
    np.savez_compressed(OUT / f"{name}.npz", **flat)
    rec["match"] = {kk: {"matched_orders": np.asarray((mm["k"] > 0).sum(0)).tolist(),
                         "candidates_median": float(np.median(mm["ncand"])),
                         "mstar": [None if not np.isfinite(x) else float(x) for x in mm["mstar"]]}
                    for kk, mm in matches.items()}
    rec["seconds"] = round(time.time() - t0, 1)
    json.dump(rec, open(OUT / f"{name}.json", "w"))
    print(f"{name} {rec['seconds']} s", flush=True)


STOP_HOURS = 8.0
PART2_ALLOWANCE_HOURS = 1.0
REF_RUNS, N2_RUNS = 11, 113  # 100-tick runs per reference graph and per N2 panel (as run_part1 builds them)


def guard():
    """The cost guard (the plan): after the first N2 panel, project the rest (the second N2 panel at the first's time,
    each reference graph at REF_RUNS / N2_RUNS of it, Part 2 an allowance), keep it in guard.json, and if it exceeds
    STOP_HOURS reduce the reference to one graph per ensemble. Enforced on every call."""
    f = OUT / "guard.json"
    if f.exists():
        return json.load(open(f))
    first = json.load(open(OUT / "N2__7600.json"))["seconds"]
    n_ref = sum(1 for *_, role in census.panels() if role == "reference")
    proj = (2 * first + n_ref * first * REF_RUNS / N2_RUNS) / 3600 + PART2_ALLOWANCE_HOURS
    g = {"first_n2_seconds": first, "projected_hours": proj, "reduced_reference": proj > STOP_HOURS}
    json.dump(g, open(f, "w"))
    print(f"projection after the first N2 panel: about {proj:.1f} h; reference reduced: {g['reduced_reference']}",
          flush=True)
    return g


def stage_n2():
    run_part1("N2__7600", "N2", 7600, list(ARMS) + ["C3-write", "gaps-off-30"])
    guard()
    run_part1("N2__7700", "N2", 7700, list(ARMS) + ["C3-write", "gaps-off-30"])


def stage_reference():
    reduced = guard()["reduced_reference"]
    seen = set()
    for name, gname, seed, role in census.panels():
        if role == "reference":
            e = c.ensemble_of(gname)
            if reduced and e in seen:  # the guard's fallback: one graph per ensemble
                continue
            seen.add(e)
            run_part1(name, gname, seed, ["C3-early-30"], n_draws=5, n_weight=3, n_uniform=0, matched=False)


# --------------------------------------------------------------------------------------------------------------- part 2
def assign(stored, found, reach):
    """Part 2's outcome for one genome: stored [2, N] its two census roots, found [2, N] the roots its histories
    reached (float64), reach the two verdicts. 'both kept', 'erased', 'swapped', 'other root' (a history reached a
    root that is neither of its two; Fable) or 'not reached'."""
    if any(r != "reached" for r in reach):
        return "not reached"
    which = []
    for h in range(2):
        d = np.abs(stored - found[h][None]).max(1)
        which.append(int(np.argmin(d)) if d.min() <= SAME_ROOT else -1)
    if -1 in which:
        return "other root"
    if which == [0, 1]:
        return "both kept"
    if which == [1, 0]:
        return "swapped"
    return "erased"


def part2_gate(out):
    """Every intact-arm genome must keep both roots, or Part 2 stops for investigation (the plan)."""
    bad = [i for i, o in zip(out["genomes"], out["arms"]["intact"]) if o != "both kept"]
    if bad:
        raise SystemExit(f"part 2 {out['panel']}: intact arm not 'both kept' for {bad}: stop for investigation")


def run_part2_graph(name, gname, seed):
    f = OUT / f"part2__{name}.json"
    if f.exists():
        part2_gate(json.load(open(f)))  # a cached failure stops too, on every restart (Astra, round 3)
        return
    t0 = time.time()
    cen = json.load(open(CENSUS / f"{name}.json"))
    sep_ids = [gr["genome"] for gr in cen["genomes"] if gr["class"].startswith("separate states")]
    if not sep_ids:
        return
    z = np.load(CENSUS / f"{name}.npz", allow_pickle=False)
    row = {int(i): r for r, i in enumerate(z["idx"])}
    roots = torch.from_numpy(np.stack([z["roots"][row[i]] for i in sep_ids])).double()  # [S, 2, N]
    g_all, cfg = c.S.genomes(census.graph_of(gname), N_PANEL, seed)
    g = g_all.select(sep_ids)
    cidx = core()
    internal, external = edge_sets(g.spec, cidx)
    food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
    n = g.spec.n
    cur = c.at(cfg, n, len(sep_ids), [food, food]).double()
    strat = stratified_draws(g.spec, internal, external, N_DRAWS, SEED_DRAWS)[:N_PART2_DRAWS]  # Part 1's draws
    b_int = E.brain64(g)
    out = {"panel": name, "genomes": sep_ids, "location_C3": [], "arms": {}}
    d2 = (roots[:, 0] - roots[:, 1]) ** 2
    out["location_C3"] = (d2[:, cidx].sum(1) / d2.sum(1)).numpy().tolist()
    brains = {"intact": None, "C3": E.brain64(cut(g, common_mask(g, internal)))}
    for d, e in enumerate(strat):
        brains[f"rand{d}"] = E.brain64(cut(g, common_mask(g, e)))
    for arm, bc in brains.items():
        v = roots.clone()
        for t in range(1, PART2_TICKS + 1):
            b = bc if (bc is not None and PART2_CUT[0] <= t <= PART2_CUT[1]) else b_int
            v = b.step(v, cur)
        res, found = P.locate_and_reach(b_int, v, cur, compact=True)
        out["arms"][arm] = [assign(roots[s_].numpy(), found[s_].numpy(), [str(res["reach"][s_, h]) for h in range(2)])
                            for s_ in range(len(sep_ids))]
    out["intact_not_kept"] = [i for i, o in zip(sep_ids, out["arms"]["intact"]) if o != "both kept"]
    out["seconds"] = round(time.time() - t0, 1)
    json.dump(out, open(f, "w"))  # saved, failure or not, so it can be inspected; the gate holds on every restart
    print(f"part2 {name}: {len(sep_ids)} genomes, {out['seconds']} s, intact not kept {out['intact_not_kept']}", flush=True)
    part2_gate(out)


def stage_part2():
    for name, gname, seed, role in census.panels():
        if role in ("N2", "reference", "selected"):
            run_part2_graph(name, gname, seed)


STAGES = {"n2": stage_n2, "part2": stage_part2, "reference": stage_reference}

if __name__ == "__main__":
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M4a", script="m4a.py"):
        for st in (sys.argv[1:] or list(STAGES)):
            t0 = time.time()
            STAGES[st]()
            f = OUT / "stages.json"
            rec = json.load(open(f)) if f.exists() else {}
            rec[st] = round(time.time() - t0, 1)
            json.dump(rec, open(f, "w"))
