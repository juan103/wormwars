"""M2 census (docs/memory/M2-CENSUS-PLAN.md): every eligible genome of 48 panels classified by the pilot's frozen
classifier at 2000 ticks, with the checks C1 to C5. Each panel writes its own files under runs/memory-m2-census/ and is
skipped when they exist, so a stopped run resumes. The split and its readings are computed by split.py. JSON outputs
are committed; arrays (.npz) stay local. CPU only.
Usage: python scripts/memory_m2/census.py [stage ...]   (stages: c2 panels c3 c5; all by default)"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import pilot as P  # noqa: E402

c, K, E = P.c, P.K, P.E
from wormwars import accounting as acct  # noqa: E402
from tri_sampler import describe  # noqa: E402  (scripts/memory_spikes, on the path through common)

torch.set_grad_enabled(False)
OUT = Path(os.environ.get("MEMORY_M2_CENSUS_OUT", ROOT / "runs" / "memory-m2-census"))
OUT.mkdir(parents=True, exist_ok=True)
M1 = ROOT / "runs" / "memory-m1"
SPIKES = ROOT / "runs" / "memory-spikes"
N_PANEL = int(os.environ.get("MEMORY_M2_CENSUS_PANEL", 1024))
CHUNK = 128
SEED, SEED2 = 7600, 7700
STOP_HOURS = 16.0
SERIES = list(range(0, 301)) + list(range(400, 2001, 100))  # the ticks of the class contributions over time
RADIUS_FAR = 1e-2  # the locating-radius sensitivity: stable, accurate roots between LOCATE_NEAR and this
C1_GAP, C1_FRACTION = 1e-3, 0.01  # M1's reproduction rule
C3_ROOTS = 20
GUARD_ALLOWANCE_HOURS = 0.25  # C3 and C5, which take minutes, in the projection (Astra, Fable, round 4)
CODES = ["separate states", "separate states, read-out silent", "fading", "persistent oscillation", "unresolved"]


def dump(obj, name):
    json.dump(obj, open(OUT / name, "w"), default=lambda x: x.item() if hasattr(x, "item") else str(x))


def g7(x):
    return None if x is None else float(f"{float(x):.7g}")


# --------------------------------------------------------------------------------------------------------------- graphs
class Batch7Mismatch(RuntimeError):
    """Batch 7's shuffle could not be regenerated as recorded: that arm is skipped, the rest run."""


def batch7_graph(arm, k):
    """Batch 7's core-frozen (seed 700 + k) or hub-frozen (800 + k) shuffle of N2's chemical layer, regenerated with
    batch 7's own rewiring (copied from scripts/memory_spikes/batch7.py) and checked against batch7.json."""
    S = c.S
    names = list(S.CON.names)
    core = [names.index(x) for x in json.load(open(SPIKES / "batch6.json"))["lists"]["top30_start"]]
    A0 = S.CON.chem > 0
    np.fill_diagonal(A0, False)
    incore = np.zeros(S.CON.n, bool)
    incore[core] = True
    deg = A0.sum(0) + A0.sum(1)
    hubs = [j for j in np.argsort(-deg) if not incore[j]][:30]
    inhub = np.zeros(S.CON.n, bool)
    inhub[hubs] = True

    def kept(A):
        return float((A & A0).sum() / A0.sum())

    def rewire(chem, seed, freeze, stop):  # batch 7's rewire() with pick = always
        rng = np.random.default_rng(seed)
        A = (chem > 0)
        np.fill_diagonal(A, False)
        W = chem.astype(np.float64).copy()
        diag = np.diag(chem).copy()
        edges = [tuple(e) for e in np.argwhere(A) if not freeze[e[0], e[1]]]
        acc = att = 0
        while not stop(A, acc):
            att += 1
            if att > 5_000_000:
                raise Batch7Mismatch("rewire did not reach its target")
            i, j = rng.integers(0, len(edges), 2)
            if i == j:
                continue
            (a, b), (cc, d) = edges[i], edges[j]
            if a == d or cc == b or A[a, d] or A[cc, b]:
                continue
            A[a, b] = A[cc, d] = False
            A[a, d] = A[cc, b] = True
            W[a, d], W[cc, b] = W[a, b], W[cc, d]
            W[a, b] = W[cc, d] = 0
            edges[i], edges[j] = (a, d), (cc, b)
            acc += 1
        out = np.where(A, W, 0.0)
        np.fill_diagonal(out, diag)
        return out.astype(np.float32), acc

    m = incore if arm == "core-frozen-shuffle" else inhub
    fz = np.zeros_like(A0)
    fz[np.ix_(m, m)] = A0[np.ix_(m, m)]
    chem, acc = rewire(S.CON.chem, (700 if arm == "core-frozen-shuffle" else 800) + k, fz,
                       lambda A, acc: acc % 50 == 0 and kept(A) <= 0.273)
    B = chem > 0
    np.fill_diagonal(B, False)
    ref = json.load(open(SPIKES / "batch7.json"))[f"N2/{arm}{k}/7100"]
    internal = lambda A, mk: (A[np.ix_(mk, mk)] & A0[np.ix_(mk, mk)]).sum()  # noqa: E731
    got = {"structure": describe(chem), "kept_all": kept(B), "kept_core_internal": float(internal(B, incore) / internal(A0, incore)),
           "accepted": acc}
    want = {"structure": ref["structure"], "kept_all": ref["kept_all"], "kept_core_internal": ref["kept_core_internal"],
            "accepted": ref["info"]["accepted"]}
    got, want = json.loads(json.dumps(got, default=int)), json.loads(json.dumps(want))
    if got != want:
        raise Batch7Mismatch(f"batch 7's {arm}{k} does not regenerate: {got} against {want}")
    return S.masks(chem, S.CON.gap, f"N2/{arm}{k}"), {"core": core, "hubs": hubs}


def core_and_hubs():
    S = c.S
    names = list(S.CON.names)
    sets = json.load(open(SPIKES / "batch7.json"))["sets"]
    return [names.index(x) for x in sets["core"]], [names.index(x) for x in sets["hubs"]]


def panels():
    """The census's 48 panels, in the plan's order: N2 (7600), the reference one per ensemble in turn, N2 (7700), the
    selected graphs, batch 7's shuffles. Each is (name, graph, seed, role)."""
    panel = json.load(open(M1 / "panel.json"))
    by_e = {e: [g for g in panel["random"] if c.ensemble_of(g) == e] for e in c.ENSEMBLES}
    ref = [by_e[e][i] for i in range(max(len(v) for v in by_e.values())) for e in c.ENSEMBLES if i < len(by_e[e])]
    sel = [x for e in c.ENSEMBLES for x in (panel["selected"][e]["top_share"], panel["selected"][e]["top_cohort"])]
    out = [("N2__7600", "N2", SEED, "N2")] + [(f"{g}__{SEED}", g, SEED, "reference") for g in ref]
    out += [("N2__7700", "N2", SEED2, "N2")] + [(f"{g}__{SEED}", g, SEED, "selected") for g in sel]
    out += [(f"{arm}{k}__{SEED}", f"{arm}{k}", SEED, arm) for arm in ("core-frozen-shuffle", "hub-frozen-shuffle")
            for k in range(3)]
    return out


def graph_of(gname):
    for arm in ("core-frozen-shuffle", "hub-frozen-shuffle"):
        if gname.startswith(arm):
            return batch7_graph(arm, int(gname[len(arm):]))[0]
    return c.S.graph(gname)


# ---------------------------------------------------------------------------------------------------------------- panel
def extras(gs, cfg, run, recs, roots, core, hubs):
    """Per classified genome: the cheaper rule per history; for separate states, where the two roots differ (core,
    hubs, rest); for fading, the slowest discrete rate of P^32 at the common root; and the locating-radius
    sensitivity."""
    b64 = E.brain64(gs)
    cur = run["cur"].double()
    sysm = E.System(b64, cur[:, :1])
    n = gs.spec.n
    rest = np.setdiff1d(np.arange(n), np.union1d(core, hubs))
    out = [{} for _ in recs]
    for j, r in enumerate(recs):
        out[j]["cheap"] = [bool(h["located"] and h["error"] <= K.ACCURACY and h["dist_end_root"] <= K.LOCATE_NEAR)
                           for h in r["histories"]]
        if r["class"].startswith("separate states"):
            d2 = ((roots[j, 0] - roots[j, 1]) ** 2).numpy()
            tot = d2.sum()
            out[j]["where"] = {"core": float(d2[core].sum() / tot), "hubs": float(d2[hubs].sum() / tot),
                               "rest": float(d2[rest].sum() / tot), "readout": float(d2[c.READOUT].sum() / tot)}
    fad = [j for j, r in enumerate(recs) if r["class"] == "fading"]
    for lo in range(0, len(fad), 32):
        jj = fad[lo:lo + 32]
        sub = E.System(E.brain64(gs.select(jj)), cur[jj, :1])
        P32 = torch.linalg.matrix_power(sub.P(roots[jj, 0], P.SUBSTEPS), P.SUBSTEPS)
        mu = torch.linalg.eigvals(P32).abs().amax(1).numpy()
        for k_, j in enumerate(jj):
            out[j]["slow_rate"] = float(np.log(mu[k_]))
    # the locating radius (the plan's sensitivity): "not approaching" with a located, accurate, stable root farther
    # than LOCATE_NEAR but within RADIUS_FAR gets the continuation anyway
    far = [(j, h) for j, r in enumerate(recs) for h, hh in enumerate(r["histories"])
           if hh["reach"] == "not approaching" and hh["located"] and hh["error"] <= K.ACCURACY and hh["stability"] == "stable"
           and K.LOCATE_NEAR < hh["dist_end_root"] <= RADIUS_FAR]
    if far:  # one batched continuation, one strain per qualifying history
        js, hs_ = [j for j, _ in far], [h for _, h in far]
        b_far = E.brain64(gs.select(js))
        sub = E.System(b_far, cur[js, :1])
        rt = torch.stack([roots[j, h] for j, h in far]).unsqueeze(1)
        P32 = torch.linalg.matrix_power(sub.P(rt[:, 0], P.SUBSTEPS), P.SUBSTEPS)
        st = torch.stack([run["end"][j, h].double() for j, h in far]).unsqueeze(1)
        d0, T, capped, wd, wf, _ = P.continuation_compact(b_far, st, rt, P32, cur[js, :1], P.CAP, P.SUBSTEPS)
        verdicts = {}
        for m, (j, h) in enumerate(far):
            verdicts.setdefault(j, {})[h] = (K.reached(wd[m, 0], wf[m, 0], d0[m, 0], True, bool(capped[m, 0]),
                                                       recs[j]["histories"][h]["error"]), int(T[m, 0]))
        for j, vh in verdicts.items():
            out[j]["radius"] = joint_radius(recs[j], vh)
        del hs_
    del sysm, n
    return out


def joint_radius(rec, vh):
    """The locating-radius sensitivity for one genome: every qualifying history's new reaching verdict applied
    together, then the genome classified once (Fable, Astra, round 3). vh {history: (verdict, T)}."""
    hs = [dict(x) for x in rec["histories"]]
    for h, (v, _) in vh.items():
        hs[h]["reach"] = v
    cls, why = K.classify(hs[0], hs[1], rec["root_distance"], rec["readout_difference"], rec["a"],
                          *[None if o is None else o["verdict"] for o in rec["oscillation"]])
    return {"histories": [{"history": h, "dist_end_root": rec["histories"][h]["dist_end_root"], "reach": v, "T": t_}
                          for h, (v, t_) in vh.items()], "class": cls, "reason": why}


def run_panel(name, gname, seed, role, core, hubs):
    t0 = time.time()
    g, cfg = c.S.genomes(graph_of(gname), N_PANEL, seed)  # the whole panel first, then sliced (Astra)
    allg = {k: [] for k in ("a", "d30", "d100", "d300", "steady", "settled300", "eligible", "cohort")}
    series = {k: np.zeros(len(SERIES)) for k in CODES}
    genomes, dy_all, roots_all, idx_all = [], [], [], []
    chunk_seconds = []
    for lo in range(0, N_PANEL, CHUNK):
        tc = time.time()
        idx = list(range(lo, min(lo + CHUNK, N_PANEL)))
        gs = g.select(idx)
        steady = c.ramp(gs, cfg, with_steady=True)[3]
        run = P.probe_states(gs, cfg)
        y = run["y"]
        dy = np.abs(y[:, :, 0] - y[:, :, 1])  # [S, 2001]
        a = dy[:, 0]
        elig = a >= c.START_FLOOR
        dense = run["dense"]
        settled = ((dense[:, 291:301].max(1) - dense[:, 291:301].min(1)).max(-1) < c.SETTLE_TOL).all(1)
        cohort = elig & settled & (dy[:, 300] > c.REMAIN * a)
        for k, v in (("a", a), ("d30", dy[:, 30]), ("d100", dy[:, 100]), ("d300", dy[:, 300]), ("steady", steady),
                     ("settled300", settled), ("eligible", elig), ("cohort", cohort)):
            allg[k].append(v)
        e = np.where(elig)[0]
        if len(e):
            ge = gs.select([int(i) for i in e])
            sub = {"end": run["end"][e], "cur": run["cur"][e], "y": y[e], "tail": run["tail"][e]}
            recs, roots = P.full_classify(ge, cfg, sub, compact=True)
            ex = extras(ge, cfg, sub, recs, roots, core, hubs)
            for j, (i, r) in enumerate(zip(e, recs)):
                genomes.append({"genome": lo + int(i), **r, **ex[j], "cohort": bool(cohort[i]), "settled300": bool(settled[i])})
                series[r["class"]] += dy[i, SERIES]
            dy_all.append(dy[e].astype(np.float32))
            roots_all.append(roots.numpy())
            idx_all.append(lo + e)
        chunk_seconds.append(round(time.time() - tc, 1))
        print(f"  {name} chunk {lo // CHUNK + 1}/{(N_PANEL + CHUNK - 1) // CHUNK} {chunk_seconds[-1]} s", flush=True)
    allg = {k: np.concatenate(v) for k, v in allg.items()}
    el = allg["eligible"]
    den = float(allg["a"][el].sum())
    valid = c.panel_valid(allg["a"], allg["steady"], int(el.sum()))
    rec = {"panel": name, "graph": gname, "seed": seed, "role": role, "valid": valid, "eligible": int(el.sum()),
           "steady_contrast_mean": float(np.abs(allg["steady"]).mean()),
           "ineligible_numerator_frac30": float(allg["d30"][~el].sum() / max(allg["d30"].sum(), 1e-300)),
           "ineligible_denominator_frac": float(allg["a"][~el].sum() / max(allg["a"].sum(), 1e-300)),
           "eligible_share": {str(t): float(allg[f"d{t}"][el].sum() / den) if den > 0 else None for t in (30, 100, 300)},
           "denominator": den,
           "all": {k: [g7(x) if v.dtype.kind == "f" else bool(x) for x in v] for k, v in allg.items() if k != "steady"},
           "series_ticks": SERIES, "series": {k: [g7(x) for x in v] for k, v in series.items()},
           "genomes": [compact_record(r) for r in genomes],
           "seconds": round(time.time() - t0, 1), "chunk_seconds": chunk_seconds}
    c1(name, gname, seed, role, rec)  # before the record is saved, so a failed C1 is never skipped on a restart
    np.savez_compressed(OUT / f"{name}.npz", idx=np.concatenate(idx_all) if idx_all else np.zeros(0, int),
                        dy=np.concatenate(dy_all) if dy_all else np.zeros((0, 2001), np.float32),
                        roots=np.concatenate(roots_all) if roots_all else np.zeros((0, 2, g.spec.n)))
    dump(rec, f"{name}.json")
    counts = {k: sum(r["class"] == k for r in genomes) for k in CODES}
    print(f"{name} {rec['seconds']} s, valid {valid}, eligible {rec['eligible']}, {counts}", flush=True)
    return rec


def compact_record(r):
    """The committed per-genome record: the class and what it rests on, without the pilot's full history records."""
    hs = r["histories"]
    out = {"genome": r["genome"], "class": r["class"], "reason": r["reason"], "a": g7(r["a"]), "d30": g7(r["d30"]),
           "d300": g7(r["d300"]), "root_distance": g7(r["root_distance"]), "readout_difference": g7(r["readout_difference"]),
           "cohort": r["cohort"], "settled300": r["settled300"], "candidate": r["candidate"],
           "located": [h["located"] for h in hs], "reach": [h["reach"] for h in hs], "stability": [h["stability"] for h in hs],
           "error": [g7(h["error"]) for h in hs], "dist_end_root": [g7(h["dist_end_root"]) for h in hs],
           "rho_substep": [g7(h["rho_substep"]) for h in hs], "cont_max_re": [g7(h["cont_max_re"]) for h in hs],
           "T": [h["T"] for h in hs], "cheap": r["cheap"]}
    for k in ("where", "slow_rate", "radius"):
        if k in r:
            out[k] = r[k]
    if any(o is not None for o in r["oscillation"]):
        out["oscillation"] = r["oscillation"]
    return out


def require(name):
    """A check's record must exist and pass before anything that depends on it runs (Astra, round 3)."""
    f = OUT / name
    if not f.exists() or not json.load(open(f)).get("passes"):
        raise SystemExit(f"{name} is missing or did not pass; nothing that depends on it runs")


def stage_panels():
    require("c2.json")
    core, hubs = core_and_hubs()
    todo = panels()
    guard(todo)  # a stop already projected holds on a restart (Fable, Astra, round 4)
    for name, gname, seed, role in todo:
        if (OUT / f"{name}.json").exists() or (OUT / f"{name}.skipped.json").exists():
            continue
        try:
            run_panel(name, gname, seed, role, core, hubs)
        except Batch7Mismatch as err:  # the plan: that arm only
            dump({"panel": name, "reason": str(err)}, f"{name}.skipped.json")
            print(f"{name} skipped: {err}", flush=True)
            continue
        guard(todo)


def guard(todo):
    """The cost guard, on the plan's first two panels (N2's first and the first reference graph): C2's time, those two
    panels' and the rest at their mean, plus an allowance for C3 and C5. The measurements are read from the saved panel
    records, so an interruption between saving a panel and measuring it loses nothing, and the projection is kept in
    guard.json and enforced on every call, so a restart cannot run past it (Astra, round 4)."""
    f = OUT / "guard.json"
    g = json.load(open(f)) if f.exists() else {}
    first = [todo[0][0], todo[1][0]]
    if "projected_hours" not in g and all((OUT / f"{x}.json").exists() for x in first):
        measured = {x: json.load(open(OUT / f"{x}.json"))["seconds"] for x in first}
        c2s = json.load(open(OUT / "stages.json")).get("c2", 0.0) if (OUT / "stages.json").exists() else 0.0
        g = {"measured": measured, "c2_seconds": c2s,
             "projected_hours": (c2s + float(np.mean(list(measured.values()))) * len(todo)) / 3600 + GUARD_ALLOWANCE_HOURS}
        dump(g, "guard.json")
        print(f"projection after two panels: about {g['projected_hours']:.1f} h", flush=True)
    if g.get("projected_hours", 0.0) > STOP_HOURS:
        raise SystemExit(f"projected {g['projected_hours']:.1f} h exceeds {STOP_HOURS} h: the plan is to be revisited")


# ------------------------------------------------------------------------------------------------------------------- C1
def c1(name, gname, seed, role, rec):
    """C1: on M1's panels, a, |dy(30)| and |dy(100)|, eligibility and cohort genome by genome against M1's arrays, and the
    eligible shares and cohort contributions against M1's records. Stops for investigation under M1's rule, after
    saving the gaps."""
    f = M1 / "panels" / f"{gname}__{seed}.npz"
    if role in ("core-frozen-shuffle", "hub-frozen-shuffle") or N_PANEL != 1024:  # batch 7's arms; a smoke panel
        return
    if not f.exists():
        raise RuntimeError(f"C1: M1's arrays for {gname}__{seed} are missing; the reproduction check cannot run")
    z = np.load(f, allow_pickle=False)
    j = json.load(open(M1 / "panels" / f"{gname}__{seed}.json"))
    al = {k: np.array([np.nan if x is None else x for x in v], float) for k, v in rec["all"].items()}
    gaps = {k: np.abs(al[k] - z[k]) for k in ("a", "d30", "d100")}
    worst = np.maximum(gaps["a"], gaps["d30"])
    el_m1, co_m1 = z["ok"].astype(bool), z["cohort"].astype(bool)
    el, co = al["eligible"].astype(bool), al["cohort"].astype(bool)
    d300 = al["d300"]
    changed = lambda m: {"genomes": [int(i) for i in np.where(m)[0]],  # noqa: E731
                         "numerator30": float(al["d30"][m].sum()), "numerator300": float(d300[m].sum())}
    den = rec["denominator"]
    out = {"panel": name, "gap_max": {k: float(v.max()) for k, v in gaps.items()},
           "frac_above": float((worst > C1_GAP).mean()), "eligibility_changed": changed(el != el_m1),
           "cohort_changed": changed(co != co_m1),
           "eligible_share": {t: [rec["eligible_share"][t], j[f"eligible_share{t}"]] for t in ("30", "100", "300")},
           "cohort_C": {t: [float(al[f"d{t}"][co].sum() / den), j["B2"][f"C{t}"]] for t in ("30", "300")},
           "gaps": {k: [g7(x) for x in v] for k, v in gaps.items()}}
    dump(out, f"c1__{name}.json")
    if out["frac_above"] > C1_FRACTION:
        raise RuntimeError(f"C1: {out['frac_above']:.1%} of {name}'s genomes differ from M1's by more than {C1_GAP}")


# ------------------------------------------------------------------------------------------------------------------- C2
def stage_c2():
    if (OUT / "c2.json").exists():
        require("c2.json")  # a cached failure stops the census as a fresh one would (Astra, round 3)
        return
    out = P.planted_check(compact=True)
    dump(out, "c2.json")
    if not out["passes"]:
        raise SystemExit("C2: a planted genome is misclassified by the census path; nothing runs")


# ------------------------------------------------------------------------------------------------------------------- C3
def c3_valid(rec):
    return bool(rec.get("passes") and len(rec.get("checks", [])) == C3_ROOTS and rec.get("panels_complete"))


def missing_panels():
    """The panels with neither a record nor a recorded batch-7 skip."""
    return [name for name, *_ in panels() if not (OUT / f"{name}.json").exists() and not (OUT / f"{name}.skipped.json").exists()]


def stage_c3():
    """C3 runs only on the complete census, and a cached record counts only if it checked C3_ROOTS roots on it (Astra,
    round 4: an early call would otherwise save an empty pass)."""
    if (OUT / "c3.json").exists() and c3_valid(json.load(open(OUT / "c3.json"))):
        return
    miss = missing_panels()
    if miss:
        raise SystemExit(f"C3 needs the whole census; missing: {miss}")
    pool = []
    for name, gname, seed, role in panels():
        if not (OUT / f"{name}.json").exists():  # a recorded batch-7 skip
            continue
        rec = json.load(open(OUT / f"{name}.json"))
        for j, r in enumerate(rec["genomes"]):
            for h in range(2):
                if r["located"][h] and r["error"][h] <= K.ACCURACY:
                    pool.append((name, gname, seed, j, h))
    rng = np.random.default_rng(20261029)
    pick = [pool[i] for i in sorted(rng.choice(len(pool), min(20, len(pool)), replace=False))]
    out = []
    for name, gname, seed, j, h in pick:
        z = np.load(OUT / f"{name}.npz", allow_pickle=False)
        g, cfg = c.S.genomes(graph_of(gname), N_PANEL, seed)
        gs = g.select([int(z["idx"][j])])
        root = torch.from_numpy(z["roots"][j, h]).unsqueeze(0)
        b64 = E.brain64(gs)
        food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
        cur = c.at(cfg, g.spec.n, 1, [food]).double()
        P32 = torch.linalg.matrix_power(E.System(b64, cur).P(root, P.SUBSTEPS), P.SUBSTEPS)
        D = E.tick_autograd(b64, root, cur)
        out.append({"panel": name, "genome": int(z["idx"][j]), "history": h, "max_abs_diff": float((P32 - D).abs().max())})
    dump({"checks": out, "panels_complete": True,
          "passes": len(out) == C3_ROOTS and all(x["max_abs_diff"] <= 1e-8 for x in out)}, "c3.json")


# ------------------------------------------------------------------------------------------------------------------- C5
def c5_compare(pilot, proots, census, croots):
    """C5 on one graph: pilot {genome: record}, proots {genome: [2, N]}, census {genome: compact record}, croots
    {genome: [2, N]}. Returns (rows, agreeing, compared, basin changes). A pilot genome the census does not classify
    (lost to eligibility) disagrees, and if it had separate states its roots are not reached: a basin change (Astra,
    round 3)."""
    rows, same, n, switched = [], 0, 0, []
    for i, r in pilot.items():
        n += 1
        if i not in census:
            rows.append({"genome": i, "pilot": r["class"], "census": "not eligible"})
            if r["class"].startswith("separate states"):
                switched.append({"genome": i, "census": "not eligible"})
            continue
        q = census[i]
        dist = np.abs(croots[i] - proots[i]).max(-1)
        ok_roots = [bool(q["reach"][h] == "reached" and q["stability"][h] == "stable" and q["error"][h] <= K.ACCURACY
                         and dist[h] <= K.DISTINCT) for h in range(2)]
        lost = r["class"].startswith("separate states") and not all(ok_roots)
        if lost:
            switched.append({"genome": i})
        same += r["class"] == q["class"]
        if r["class"] != q["class"] or lost:
            rows.append({"genome": i, "pilot": r["class"], "census": q["class"], "census_reason": q["reason"],
                         "root_distance_to_pilot": [float(x) for x in dist], "same_root": ok_roots})
    return rows, same, n, switched


def stage_c5():
    """C5: the pilot's 467 genomes, reclassified here, against the pilot's classes and roots at R3's thresholds."""
    if (OUT / "c5.json").exists():
        return
    pm = ROOT / "runs" / "memory-m2"
    out, same, n, switched = {"graphs": {}}, 0, 0, []
    for gname in P.GRAPHS:
        pc = {r["genome"]: r for r in json.load(open(pm / f"classes__{gname}.json"))["genomes"]}
        pz = np.load(pm / f"roots__{gname}.npz", allow_pickle=False)
        cz = np.load(OUT / f"{gname}__{SEED}.npz", allow_pickle=False)
        rec = json.load(open(OUT / f"{gname}__{SEED}.json"))
        rows, s_, n_, sw = c5_compare(pc, {int(i): pz["roots"][k] for k, i in enumerate(pz["idx"])},
                                      {r["genome"]: r for r in rec["genomes"]},
                                      {int(i): cz["roots"][k] for k, i in enumerate(cz["idx"])})
        out["graphs"][gname] = rows
        same, n = same + s_, n + n_
        switched += [dict(x, graph=gname) for x in sw]
    out.update({"genomes": n, "agreement": same / n if n else None, "basin_changes": switched,
                "passes": bool(n and same / n >= 0.95 and not switched)})
    dump(out, "c5.json")


STAGES = {"c2": stage_c2, "panels": stage_panels, "c3": stage_c3, "c5": stage_c5}

if __name__ == "__main__":
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M2-census",
                       script="census.py"):
        for st in (sys.argv[1:] or list(STAGES)):
            t0 = time.time()
            STAGES[st]()
            f = OUT / "stages.json"
            rec = json.load(open(f)) if f.exists() else {}
            rec[st] = round(rec.get(st, 0.0) + time.time() - t0, 1)
            dump(rec, "stages.json")
            print("stage", st, round(time.time() - t0, 1), "s", flush=True)
