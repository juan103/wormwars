"""M4c (docs/memory/M4C-PLAN.md): is RIA's part of N2's switch more than its weight? On fresh N2 panels (seeds 7801 to
7808, classified by M2's census code unchanged), every separate-states genome is started at its two stored roots, and
each RIA side's C3-internal chemical edges are cut for ticks 1 to 30, against 20 exterior sets of as many edges matched
in anatomical weight (X) and 20 sets of other C3-internal edges of the same summed weight (W), with descriptive arms.
Each history is assigned by M2's reaching rule after the intact network runs to tick 330 (M4a's Part 2, via
m4b.outcomes). Writes runs/memory-m4c/; readings by m4c_read.py. CPU only.
Usage: python scripts/memory_m4/m4c.py [stage ...]   (stages: census sets arms; all, in that order, by default)"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
import m4a  # noqa: E402
import m4b  # noqa: E402

census, P, c, E = m4a.census, m4a.P, m4a.c, m4a.E
from wormwars import accounting as acct  # noqa: E402

torch.set_grad_enabled(False)
ROOT = Path(__file__).resolve().parents[2]
REAL = ROOT / "runs" / "memory-m4c"
SMOKE = bool(os.environ.get("MEMORY_M4C_SMOKE"))
OUT = Path(os.environ.get("MEMORY_M4C_OUT", REAL))
OUT.mkdir(parents=True, exist_ok=True)
if SMOKE and OUT.resolve() == REAL.resolve():  # a smoke must not land where the real run reads
    raise SystemExit("a smoke run (MEMORY_M4C_SMOKE) needs MEMORY_M4C_OUT set to another folder")
SEEDS = [7899] if SMOKE else list(range(7801, 7809))
EXTRA_SEEDS = [] if SMOKE else list(range(7809, 7813))
MIN_GENOMES = 60  # fewer separate-states genomes in the eight panels: the four extra panels are classified, once
N_PANEL = 256 if SMOKE else 1024
SIDES = ("RIAR", "RIAL")
N_SETS, TOL, NEAR, TRIES = 20, 0.02, 0.25, 2000
STAR_TOL, STAR_TRIES = 0.05, 500  # the stars are descriptive; at 2% only one qualifies
SEED_X = {"RIAR": 20261121, "RIAL": 20261122}
SEED_W = {"RIAR": 20261123, "RIAL": 20261124}
SEED_STAR = 20261125
SEED_C = {"RIAR": 20261127, "RIAL": 20261128}
C_BURN, C_THIN, DESCENT_CAP = 20000, 5000, 10**6  # the swap chain's burn-in, spacing and start-descent cap
FAMILIES = ("X", "W", "C")


# ------------------------------------------------------------------------------------------------------------ edge sets
def n2_spec():
    return c.S.genomes(census.graph_of("N2"), 1, SEEDS[0])[0].spec


def side_edges(spec, name):
    """One neuron's C3-internal off-diagonal chemical edges, in and out (M4b's dissection arm 'C3:<name>')."""
    internal, _ = m4a.edge_sets(spec, m4a.core())
    i, j = spec.chem_i.numpy(), spec.chem_j.numpy()
    k = c.NAMES.index(name)
    return internal[(i[internal] == k) | (j[internal] == k)]


def touches_ria(spec):
    i, j = spec.chem_i.numpy(), spec.chem_j.numpy()
    ria = [c.NAMES.index(x) for x in SIDES]
    return np.isin(i, ria) | np.isin(j, ria)


def matched_draw(target, pool, key, rng, tol=TOL, tries=TRIES):
    """One set of len(target) pool edges matched in weight to the target edges: the target's edges in random order,
    each paired with an unused pool edge drawn uniformly among those within max(1, NEAR x its weight) of it, else the
    nearest unused one (random tie-break); kept only if the summed weight is within tol of the target's, else redrawn.
    Returns (edges, ratio), or (None, None) after tries."""
    tw, pw = key[target], key[pool]
    total = tw.sum()
    for _ in range(tries):
        free = np.ones(len(pool), bool)
        take = []
        for w in rng.permutation(tw):
            cand = np.where(free & (np.abs(pw - w) <= max(1.0, NEAR * w)))[0]
            if not len(cand):
                fr = np.where(free)[0]
                cand = fr[[np.argmin(np.abs(pw[fr] - w) + rng.random(len(fr)) * 1e-6)]]
            k = int(rng.choice(cand))
            free[k] = False
            take.append(k)
        s = pw[take].sum()
        if abs(s - total) <= tol * total:
            return pool[np.array(take)], float(s / total)
    return None, None


def weight_fill(total, pool, key, rng, tol=TOL):
    """Pool edges of the same summed weight, as many as that takes: a random permutation, each edge added if the sum
    stays at most (1 + tol) x total, stopping once it reaches (1 - tol) x total. Returns (edges, ratio)."""
    take, s = [], 0.0
    for k in rng.permutation(len(pool)):
        w = float(key[pool[k]])
        if s + w <= (1 + tol) * total:
            take.append(k)
            s += w
        if s >= (1 - tol) * total:
            return pool[np.array(take)], s / total
    return None, None


def count_weight_chain(n, total, pool, key, rng, k=N_SETS, tol=TOL, burn=C_BURN, thin=C_THIN):
    """k sets of exactly n pool edges whose summed weight is within tol of total, from a swap chain (Astra, round 1:
    count and total can both be matched inside C3): start from the n heaviest (ties by index), swap one member for one
    non-member while that brings the sum closer until it is within tol (at most DESCENT_CAP tries), then propose
    uniform swaps, accepted whenever the sum stays within tol. The proposal is symmetric, so the stationary distribution
    is uniform over the feasible sets reachable by single swaps; the thinned samples after burn steps approximate it
    (an MCMC approximation; Astra, Fable, round 2). Returns the sets with their weight ratios, and the acceptance rate
    after the burn-in (a mixing diagnostic, Fable)."""
    w = key[pool].astype(float)
    inn = np.zeros(len(pool), bool)
    inn[np.lexsort((pool, -w))[:n]] = True
    s = w[inn].sum()
    tries = 0
    while abs(s - total) > tol * total:
        tries += 1
        if tries > DESCENT_CAP:
            raise SystemExit("the C chain found no start within the tolerance (Fable, round 2)")
        a, b = rng.choice(np.where(inn)[0]), rng.choice(np.where(~inn)[0])
        if abs(s - w[a] + w[b] - total) < abs(s - total):
            inn[a], inn[b], s = False, True, s - w[a] + w[b]
    out, accepted = [], 0
    for t in range(burn + thin * k):
        a, b = rng.choice(np.where(inn)[0]), rng.choice(np.where(~inn)[0])
        if abs(s - w[a] + w[b] - total) <= tol * total:
            inn[a], inn[b], s = False, True, s - w[a] + w[b]
            accepted += t >= burn
        if t >= burn and (t - burn + 1) % thin == 0:
            out.append((pool[inn].copy(), float(w[inn].sum() / total)))
    return out, accepted / (thin * k)


def describe_family(sets_, own, key):
    """A family's match beyond the summed weight: the ratio of squared weights (Astra: equal sums are not equal
    perturbations), each set's heaviest edge, the mean pairwise overlap of its sets, and their edge counts."""
    sq = [float((key[e] ** 2).sum() / (key[own] ** 2).sum()) for e in sets_]
    ov = [len(set(a) & set(b)) / min(len(a), len(b)) for x, a in enumerate(sets_) for b in sets_[x + 1:]]
    return {"squared_ratio": [min(sq), float(np.mean(sq)), max(sq)], "squared_ratio_per_set": sq, "heaviest_edge": [float(key[e].max()) for e in sets_],
            "overlap": float(np.mean(ov)), "edges": [len(e) for e in sets_]}


def build_sets(spec):
    """Every edge set of the plan, from N2's wiring (the same for every genome), as lists of edge indices with their
    weights' sums. Deterministic: rebuilt and compared with the saved sets.json on every run and reading."""
    key = spec.chem_anat.numpy()
    i, j = spec.chem_i.numpy(), spec.chem_j.numpy()
    off = i != j
    c3 = m4a.core()
    internal, external = m4a.edge_sets(spec, c3)
    ria = touches_ria(spec)
    core_pool = internal[~ria[internal]]
    out = {"sides": {}, "descriptive": {}, "dissection": {}}
    for side in SIDES:
        own = side_edges(spec, side)
        rng = np.random.default_rng(SEED_X[side])
        X = [matched_draw(own, external, key, rng) for _ in range(N_SETS)]
        rng = np.random.default_rng(SEED_W[side])
        W = [weight_fill(float(key[own].sum()), core_pool, key, rng) for _ in range(N_SETS)]
        C, C_accept = count_weight_chain(len(own), float(key[own].sum()), core_pool, key,
                                         np.random.default_rng(SEED_C[side]))
        heavy = core_pool[np.lexsort((core_pool, -key[core_pool]))[:len(own)]]
        stars = {}
        for n in range(spec.n):
            if c.NAMES[n] in SIDES:
                continue
            star = np.where(off & ((i == n) | (j == n)) & ~ria)[0]
            if len(star) < len(own):
                continue
            e, r = matched_draw(own, star, key, np.random.default_rng(SEED_STAR + n), tol=STAR_TOL, tries=STAR_TRIES)
            if e is not None:
                stars[c.NAMES[n]] = {"edges": e.tolist(), "ratio": r}
        out["sides"][side] = {"edges": own.tolist(), "weight": float(key[own].sum()),
                              "X": [None if e is None else e.tolist() for e, _ in X], "X_ratio": [r for _, r in X],
                              "W": [None if e is None else e.tolist() for e, _ in W], "W_ratio": [r for _, r in W],
                              "C": [e.tolist() for e, _ in C], "C_ratio": [r for _, r in C], "C_acceptance": C_accept,
                              "match": {f: describe_family([e for e, _ in F], own, key) for f, F in
                                        (("X", X), ("W", W), ("C", C)) if all(e is not None for e, _ in F)},
                              "heaviest": heavy.tolist(), "heaviest_ratio": float(key[heavy].sum() / key[own].sum()),
                              "stars": stars}
        k = c.NAMES.index(side)
        outside = np.setdiff1d(np.where(off & ((i == k) | (j == k)))[0], internal)
        out["descriptive"][f"{side} outside C3"] = outside.tolist()
    out["descriptive"]["RIA both"] = np.union1d(*[out["sides"][s]["edges"] for s in SIDES]).tolist()
    ro = np.zeros(spec.n, bool)
    ro[c.READOUT] = True
    d = out["dissection"]  # M4b's dissection arms, the same edges
    d["C3"] = internal.tolist()
    d["C3:read-out among themselves"] = internal[ro[i[internal]] & ro[j[internal]]].tolist()
    d["C3:read-out with the rest of C3"] = internal[ro[i[internal]] ^ ro[j[internal]]].tolist()
    d["C3:without the read-out"] = internal[~ro[i[internal]] & ~ro[j[internal]]].tolist()
    for k in c3:
        d[f"C3:{c.NAMES[k]}"] = internal[(i[internal] == k) | (j[internal] == k)].tolist()
    return out


def check_sets(sets, spec):
    """The plan's rules on every set; a violation stops the run or the reading."""
    key = spec.chem_anat.numpy()
    i, j = spec.chem_i.numpy(), spec.chem_j.numpy()
    c3 = m4a.core()
    inc = np.zeros(spec.n, bool)
    inc[c3] = True
    ria = touches_ria(spec)
    bad = []
    for side, s in sets["sides"].items():
        own = np.array(s["edges"])
        if own.tolist() != side_edges(spec, side).tolist():
            bad.append(f"{side}: not its C3-internal edges")
        total = key[own].sum()
        for fam in FAMILIES:
            if len(s[fam]) != N_SETS or any(e is None for e in s[fam]):
                bad.append(f"{side} {fam}: fewer than {N_SETS} sets")
                continue
            for n, e in enumerate(s[fam]):
                e = np.array(e)
                if len(set(e.tolist())) != len(e) or (i[e] == j[e]).any() or ria[e].any():
                    bad.append(f"{side} {fam}{n}: repeats, autapses or RIA's edges")
                if abs(key[e].sum() - total) > TOL * total + 1e-9:
                    bad.append(f"{side} {fam}{n}: weight off by more than {TOL}")
                if fam == "X" and (len(e) != len(own) or inc[i[e]].any() or inc[j[e]].any()):
                    bad.append(f"{side} X{n}: not as many edges outside C3")
                if fam in ("W", "C") and not (inc[i[e]] & inc[j[e]]).all():
                    bad.append(f"{side} {fam}{n}: not inside C3")
                if fam == "C" and len(e) != len(own):
                    bad.append(f"{side} C{n}: not as many edges as the side")
        for nm, st in s["stars"].items():
            e = np.array(st["edges"])
            k = c.NAMES.index(nm)
            if len(e) != len(own) or ria[e].any() or not ((i[e] == k) | (j[e] == k)).all() \
                    or abs(key[e].sum() - total) > STAR_TOL * total + 1e-9:
                bad.append(f"{side} star {nm}: not a matched set of its own edges")
    if bad:
        raise SystemExit("sets violate the plan: " + "; ".join(bad[:10]))


def arm_edges(sets):
    """Every arm, in a fixed order: name -> edge list (None for intact)."""
    arms = {"intact": None}
    for side in SIDES:
        arms[side] = sets["sides"][side]["edges"]
    for side in SIDES:
        s = sets["sides"][side]
        for fam in FAMILIES:
            for n, e in enumerate(s[fam]):
                arms[f"{side}:{fam}{n}"] = e
        arms[f"{side}:heaviest core"] = s["heaviest"]
        for nm, st in s["stars"].items():
            arms[f"{side}:star {nm}"] = st["edges"]
    arms.update(sets["descriptive"])
    arms.update(sets["dissection"])
    return arms


def stage_sets():
    spec = n2_spec()
    sets = build_sets(spec)
    check_sets(sets, spec)
    f = OUT / "sets.json"
    if f.exists():
        if json.load(open(f)) != json.loads(json.dumps(sets)):
            raise SystemExit("sets.json differs from the sets the code builds: stop for investigation")
        return sets
    json.dump(sets, open(f, "w"))
    for side in SIDES:
        s = sets["sides"][side]
        print(f"{side}: {len(s['edges'])} edges, weight {s['weight']:.0f}; X ratios {min(s['X_ratio']):.3f} to "
              f"{max(s['X_ratio']):.3f}; W {min(len(e) for e in s['W'])} to {max(len(e) for e in s['W'])} edges; "
              f"C ratios {min(s['C_ratio']):.3f} to {max(s['C_ratio']):.3f}; heaviest core {s['heaviest_ratio']:.2f}; "
              f"stars {sorted(s['stars'])}; match {s['match']}", flush=True)
    return sets


def load_sets():
    """The saved sets, checked against the code's rebuild and the plan's rules."""
    spec = n2_spec()
    f = OUT / "sets.json"
    if not f.exists():
        raise SystemExit("sets.json missing")
    sets = json.load(open(f))
    if sets != json.loads(json.dumps(build_sets(spec))):
        raise SystemExit("sets.json differs from the sets the code builds")
    check_sets(sets, spec)
    return sets


# -------------------------------------------------------------------------------------------------------------- genomes
def classify(seed):
    """One fresh N2 panel through the census's own panel code, written to OUT/census. The census's C1 compares with
    M1's arrays, which fresh seeds do not have: it is skipped here, and only here (restored afterwards)."""
    name = f"N2__{seed}"
    if (OUT / "census" / f"{name}.json").exists():
        return
    saved = census.OUT, census.N_PANEL, census.c1
    census.OUT, census.N_PANEL, census.c1 = OUT / "census", N_PANEL, (lambda *a, **k: None)
    try:
        (OUT / "census").mkdir(parents=True, exist_ok=True)
        core, hubs = census.core_and_hubs()
        census.run_panel(name, "N2", seed, "fresh", core, hubs)
    finally:
        census.OUT, census.N_PANEL, census.c1 = saved


def census_record(seed):
    """A fresh panel's census record, checked before use (Astra, round 1): N2, this seed, the fresh role, the panel
    size, and its arrays aligned with its eligible genomes. Panel validity (M1's rule) is returned, not required: an
    invalid panel is dropped and counted (Fable, round 1; M2 dropped invalid panels)."""
    name = f"N2__{seed}"
    cen = json.load(open(OUT / "census" / f"{name}.json"))
    z = np.load(OUT / "census" / f"{name}.npz", allow_pickle=False)
    elig = [gr["genome"] for gr in cen["genomes"]]
    if (cen.get("panel"), cen.get("graph"), cen.get("seed"), cen.get("role")) != (name, "N2", seed, "fresh") \
            or len(cen["all"]["a"]) != N_PANEL or z["idx"].tolist() != elig or z["roots"].shape[:2] != (len(elig), 2):
        raise SystemExit(f"{name}: the census record is not this fresh panel's, or its arrays do not match")
    return cen


def switch_ids(seed):
    """The panel's separate-states genomes (both subclasses); none if the panel is invalid."""
    cen = census_record(seed)
    if not cen["valid"]:
        return []
    return [gr["genome"] for gr in cen["genomes"] if gr["class"].startswith("separate states")]


def panel_seeds():
    """The eight panels, and the four extra ones if the eight give fewer than MIN_GENOMES (the plan's rule)."""
    n = sum(len(switch_ids(s)) for s in SEEDS)
    return SEEDS + (EXTRA_SEEDS if n < MIN_GENOMES else [])


def stage_census():
    for s in SEEDS:
        classify(s)
    for s in panel_seeds()[len(SEEDS):]:
        classify(s)
    print(f"census: {[(s, len(switch_ids(s)), census_record(s)['valid']) for s in panel_seeds()]}", flush=True)


# ----------------------------------------------------------------------------------------------------------------- arms
def run_panel(seed, sets):
    name = f"N2__{seed}"
    f = OUT / f"{name}.json"
    if f.exists():
        return
    ids = switch_ids(seed)
    rec = {"panel": name, "seed": seed, "genomes": ids, "arms": {}}
    if ids:
        t0 = time.time()
        z = np.load(OUT / "census" / f"{name}.npz", allow_pickle=False)
        row = {int(i): r for r, i in enumerate(z["idx"])}
        roots = torch.from_numpy(np.stack([z["roots"][row[i]] for i in ids])).double()
        g = c.S.genomes(census.graph_of("N2"), N_PANEL, seed)[0].select(ids)
        cfg = c.S.genomes(census.graph_of("N2"), 1, seed)[1]
        food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
        cur = c.at(cfg, g.spec.n, len(ids), [food, food]).double()
        for arm, e in arm_edges(sets).items():
            rec["arms"][arm] = m4b.outcomes(g, roots, cur, None if e is None else m4a.common_mask(g, np.array(e, int)))
        rec["seconds"] = round(time.time() - t0, 1)
    json.dump(rec, open(f, "w"))
    print(f"{name}: {len(ids)} genomes, {len(rec['arms'])} arms, {rec.get('seconds')} s", flush=True)
    validate(rec, ids, sets, name)


def validate(p, ids, sets, name=None):
    """A saved panel is usable only if it is the expected panel, holds exactly the fresh census's separate-states
    genomes, has every arm complete, and its intact arm kept both roots in every genome."""
    if name is not None and p.get("panel") != name:
        raise SystemExit(f"{name}: the record is for {p.get('panel')}")
    if p["genomes"] != ids:
        raise SystemExit(f"{p['panel']}: genome ids differ from the census")
    if not ids:
        return
    want = list(arm_edges(sets))
    missing = [a for a in want if a not in p["arms"]]
    bad = [a for a in want if a in p["arms"] and len(p["arms"][a]) != len(ids)]
    extra = [a for a in p["arms"] if a not in want]
    if missing or bad or extra:
        raise SystemExit(f"{p['panel']}: missing arms {missing[:5]}, incomplete {bad[:5]}, unexpected {extra[:5]}")
    if any(p["arms"][s_] != p["arms"][f"C3:{s_}"] for s_ in SIDES):  # the same edges, run twice (Fable, round 1)
        raise SystemExit(f"{p['panel']}: a side's arm differs from its dissection arm")
    m4a.part2_gate({"panel": p["panel"], "genomes": ids, "arms": {"intact": p["arms"]["intact"]}})


def stage_arms():
    sets = load_sets()
    for s in panel_seeds():
        f = OUT / f"N2__{s}.json"
        if f.exists():
            validate(json.load(open(f)), switch_ids(s), sets, f"N2__{s}")
            continue
        run_panel(s, sets)


STAGES = {"census": stage_census, "sets": stage_sets, "arms": stage_arms}


def main(stages):
    for s in stages:
        STAGES[s]()


if __name__ == "__main__":
    todo = sys.argv[1:] or list(STAGES)
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M4c", script="m4c.py"):
        main(todo)
