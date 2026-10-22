"""M4a's readings (docs/memory/M4A-PLAN.md, draft 4, "The readings"), from m4a.py's records: over all eligible genomes,
C3's loss against the 30 sampled external cuts (20 stratified on endpoint degree, 10 on anatomical weight; the primary
control; the reading is conditional on these sampled sets; 90% intervals, the 5th and 95th percentiles), the core's collapse and the actual-loss condition, per N2 panel and combined over both; the
uniform cuts, the whole exterior and the effect-matched controls (flagged) as descriptions; Part 2's outcome fractions;
the reference as a description. Writes runs/memory-m4a/readings.json (or the MEMORY_M4A_OUT folder).
Usage: python scripts/memory_m4/m4a_read.py"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("MEMORY_M4A_OUT", ROOT / "runs" / "memory-m4a"))
CENSUS = ROOT / "runs" / "memory-m2-census"
SMOKE = bool(os.environ.get("MEMORY_M4A_SMOKE"))
ARMS = {"C3-early-30": (1, 30, 60, "early"), "C3-early-10": (1, 10, 60, "early"), "C3-late-30": (31, 60, 100, "late")}
MARGIN, COLLAPSE, ELIGIBLE = 0.10, 0.5, 1e-3
B, SEED_BOOT = 2000, 20261102
ORDERS = 3


def loss(num_x, num_int):
    """1 - sum(x) / sum(intact) over the same genomes."""
    return 1 - num_x.sum(-1) / num_int.sum(-1)


def boot_max(x_int, x_c3, X_draws, rng, b=B):
    """Genomes resampled together for every cut; in each resample C3's loss, every draw's loss and
    D = L_C3 - max over draws (Fable, Astra, round 2). Returns the 90% intervals of L_C3 and D."""
    n = len(x_int)
    idx = rng.integers(0, n, (b, n))
    si = x_int[idx].sum(1)
    Lc = 1 - x_c3[idx].sum(1) / si
    Ld = 1 - np.stack([x[idx].sum(1) for x in X_draws]) / si  # [D, b]
    q = lambda a: [float(np.percentile(a, 5)), float(np.percentile(a, 95))]  # noqa: E731
    return q(Lc), q(Lc - Ld.max(0))


def panel_reading(L_lo, D_lo, D_hi, collapse):
    """One panel's verdict for one arm: 'positive', 'null' or 'unresolved' (with the reason)."""
    if collapse > COLLAPSE:
        return "unresolved", "no collapse"
    if D_lo > MARGIN and L_lo > 0:
        return "positive", None
    if D_hi < MARGIN:
        return "null", None
    return "unresolved", "interval across the margin" if D_lo <= MARGIN else "no actual loss"


def combine(r1, r2):
    """Both panels must agree."""
    if r1 == r2 == "positive":
        return ("cutting C3's internal edges for the window costs more separation at the reading than any of the "
                "sampled degree- or weight-matched external cuts of equal size")
    if r1 == r2 == "null":
        return "not demonstrated"
    return "unresolved"


def control_mean(z, arm, key, k):
    """Effect-matched controls (secondary): per genome, the mean over its matched orders (k > 0); NaN if none."""
    tr = np.stack([z[f"{arm}_ctrl{o}__{key}"] for o in range(ORDERS)]).astype(np.float64)
    w = (k > 0)[:, :, None]
    with np.errstate(invalid="ignore"):
        return (tr * w).sum(0) / w.sum(0)


def eligible(name, z):
    """The census's eligible genomes and classes; in a smoke run (other draws) eligibility from its own intact start,
    and no classes (Astra, round 2)."""
    if SMOKE:
        a = z["intact__dy"][:, 0]
        return np.where(a >= ELIGIBLE)[0], None
    cen = {g["genome"]: g for g in json.load(open(CENSUS / f"{name}.json"))["genomes"]}
    return np.array(sorted(cen)), cen


def draws(z, arm, key, prefix="rand"):
    out, d = [], 0
    while f"{arm}_{prefix}{d}__{key}" in z.files:
        out.append(z[f"{arm}_{prefix}{d}__{key}"].astype(np.float64))
        d += 1
    return out


def read_panel(name, rng):
    z = np.load(OUT / f"{name}.npz", allow_pickle=False)
    E, cen = eligible(name, z)
    nv = z["intact__nv"].astype(np.float64)
    out = {"eligible": int(len(E)), "arms": {}}
    for arm, (w0, w1, t, start) in ARMS.items():
        if f"{arm}__nv" not in z.files:
            continue
        x_int, x_c3 = nv[E, t], z[f"{arm}__nv"][E, t].astype(np.float64)
        R = [x[E, t] for x in draws(z, arm, "nv")]
        L_iv, D_iv = boot_max(x_int, x_c3, R, rng)
        Ld = [float(loss(x, x_int)) for x in R]
        collapse = float(z[f"{arm}__nc"][E, w1].sum() / z["intact__nc"][E, w1].sum())
        verdict, why = panel_reading(L_iv[0], D_iv[0], D_iv[1], collapse)
        y_int = z["intact__dy"][E, t].astype(np.float64)
        rec = {"reading_tick": t, "L": float(loss(x_c3, x_int)), "L_draws": Ld, "L_draws_max": max(Ld),
               "D": float(loss(x_c3, x_int)) - max(Ld), "L_interval": L_iv, "D_interval": D_iv, "collapse": collapse,
               "verdict": verdict, "why": why,
               "L_tick3": float(loss(z[f"{arm}__nv"][E, w0 + 2], nv[E, w0 + 2])),
               "L_tick3_draws": [float(loss(x[E, w0 + 2], nv[E, w0 + 2])) for x in draws(z, arm, "nv")],
               "readout": {"L": float(loss(z[f"{arm}__dy"][E, t], y_int)),
                           "L_draws": [float(loss(x[E, t], y_int)) for x in draws(z, arm, "dy")]},
               "exterior_L": float(loss(z[f"{arm}_exterior__nv"][E, t], x_int)),
               "v": {"intact": float(x_int.sum() / nv[E, 0].sum()), "C3": float(x_c3.sum() / nv[E, 0].sum())},
               "v_draws": [float(x.sum() / nv[E, 0].sum()) for x in R],
               "s_draws": [float(x[E, t].sum() / z["intact__dy"][E, 0].sum()) for x in draws(z, arm, "dy")],
               "s": {"intact": float(y_int.sum() / z["intact__dy"][E, 0].sum()),
                     "C3": float(z[f"{arm}__dy"][E, t].sum() / z["intact__dy"][E, 0].sum())},
               "uniform_L": [float(loss(x[E, t], x_int)) for x in draws(z, arm, "nv", "unif")]}
        if f"match_{start}_k" in z.files:  # effect-matched, secondary and flagged: biased toward weakly hit genomes
            k = z[f"match_{start}_k"]
            M = E[(k[:, E] > 0).any(0)]
            ctrl = control_mean(z, arm, "nv", k)
            rec["effect_matched"] = {"matched": int(len(M)), "of": int(len(E)),
                                     "L": float(loss(z[f"{arm}__nv"][M, t], nv[M, t])) if len(M) else None,
                                     "L_ctrl": float(loss(ctrl[M, t], nv[M, t])) if len(M) else None,
                                     "unmatched_share_30": float(nv[np.setdiff1d(E, M), 30].sum() / nv[E, 30].sum())}
        if cen is not None:
            by = {}
            for cls in ("separate states", "fading"):
                sel = np.array([cen[i]["class"].startswith(cls) for i in E])
                if sel.any():
                    by[cls] = {"genomes": int(sel.sum()), "L": float(loss(x_c3[sel], x_int[sel])),
                               "L_draws_median": float(np.median([loss(x[sel], x_int[sel]) for x in R])),
                               "v_intact": float(x_int[sel].sum() / nv[E[sel], 0].sum()),
                               "s_intact": float(y_int[sel].sum() / z["intact__dy"][E[sel], 0].sum()),
                               "L_readout": float(loss(z[f"{arm}__dy"][E[sel], t], y_int[sel])),
                               "v_C3": float(x_c3[sel].sum() / nv[E[sel], 0].sum()),
                               "s_C3": float(z[f"{arm}__dy"][E[sel], t].sum() / z["intact__dy"][E[sel], 0].sum()),
                               "collapse": float(z[f"{arm}__nc"][E[sel], w1].sum() / z["intact__nc"][E[sel], w1].sum())}
            rec["by_class"] = by
        out["arms"][arm] = rec
    for arm in ("C3-write", "gaps-off-30"):
        if f"{arm}__nv" in z.files:
            out["arms"][arm] = {"reading_tick": 60, "L": float(loss(z[f"{arm}__nv"][E, 60], nv[E, 60])),
                                "readout_L": float(loss(z[f"{arm}__dy"][E, 60], z["intact__dy"][E, 60])),
                                "v": float(z[f"{arm}__nv"][E, 60].sum() / nv[E, 0].sum()),
                                "s": float(z[f"{arm}__dy"][E, 60].sum() / z["intact__dy"][E, 0].sum()),
                                "description_only": True}
    return out


def part2_summary(files, selected):
    """Per group and arm, the fraction of genomes with each outcome; the random draws averaged over draws, each draw
    normalised by its own genome count (Astra, round 2)."""
    res = {}
    for f in files:
        p = json.load(open(f))
        role = "N2" if p["panel"].startswith("N2") else ("selected" if p["panel"] in selected else "reference")
        grp = res.setdefault(role, {"genomes": 0, "location_C3": [], "counts": {}})
        grp["genomes"] += len(p["genomes"])
        grp["location_C3"] += p["location_C3"]
        for arm, outs in p["arms"].items():
            a = "random" if arm.startswith("rand") else arm
            c = grp["counts"].setdefault(a, {})
            for o in outs:
                c[o] = c.get(o, 0) + 1
    for role, grp in res.items():
        grp["fractions"] = {}
        for a, c in grp["counts"].items():
            tot = sum(c.values())
            grp["fractions"][a] = {o: v / tot for o, v in c.items()}  # pooled over draws: each draw has every genome
        loc = grp.pop("location_C3")
        grp["location_C3_median"] = float(np.median(loc)) if loc else None
    return res


def main(selected=frozenset()):
    rng = np.random.default_rng(SEED_BOOT)
    res = {"panels": {}, "readings": {}}
    for name in ("N2__7600", "N2__7700"):
        if (OUT / f"{name}.npz").exists():
            res["panels"][name] = read_panel(name, rng)
    for arm in ARMS:
        v = [res["panels"][n]["arms"][arm]["verdict"] for n in res["panels"] if arm in res["panels"][n]["arms"]]
        if len(v) == 2:
            res["readings"][arm] = combine(*v)
    res["part2"] = part2_summary(sorted(OUT.glob("part2__*.json")), selected)
    ref = {}
    for f in sorted(OUT.glob("SH-*.json")):
        name = f.stem
        z = np.load(OUT / f"{name}.npz", allow_pickle=False)
        E, _ = eligible(name, z)
        x_int = z["intact__nv"][E, 60].astype(np.float64)
        ref[name] = {"internal_edges": json.load(open(f))["internal_edges"], "eligible": int(len(E)),
                     "v60_intact": float(x_int.sum() / z["intact__nv"][E, 0].sum()),
                     "v60_cut": float(z["C3-early-30__nv"][E, 60].sum() / z["intact__nv"][E, 0].sum()),
                     "L": float(loss(z["C3-early-30__nv"][E, 60], x_int)),
                     "L_draws": [float(loss(x[E, 60], x_int)) for x in draws(z, "C3-early-30", "nv")]}
    res["reference"] = ref
    if ref and "N2__7600" in res["panels"]:  # N2's lead over the reference mean at tick 60, intact and under the cut
        z = np.load(OUT / "N2__7600.npz", allow_pickle=False)
        E, _ = eligible("N2__7600", z)
        n2 = {"intact": float(z["intact__nv"][E, 60].sum() / z["intact__nv"][E, 0].sum()),
              "cut": float(z["C3-early-30__nv"][E, 60].sum() / z["intact__nv"][E, 0].sum())}
        res["n2_lead_over_reference"] = {k: n2[k] - float(np.mean([r[f"v60_{k}"] for r in ref.values()]))
                                         for k in ("intact", "cut")}
    json.dump(res, open(OUT / "readings.json", "w"), indent=1)
    for arm, r in res["readings"].items():
        print(arm, "->", r)
        for n in res["panels"]:
            a = res["panels"][n]["arms"][arm]
            print(f"   {n}: L {a['L']:.3f} (tick 3 {a['L_tick3']:.3f}); draws max {a['L_draws_max']:.3f}; "
                  f"D {a['D']:+.3f} {np.round(a['D_interval'], 3).tolist()}; collapse {a['collapse']:.3f}; "
                  f"{a['verdict']} {a['why'] or ''}")


def test_rules():
    """The readings' boundaries (rule 9): margin, actual loss and collapse; the combination; the bootstrap."""
    assert panel_reading(0.05, 0.11, 0.3, 0.4) == ("positive", None)
    assert panel_reading(0.05, 0.10, 0.3, 0.4)[0] == "unresolved"  # lower(D) must exceed the margin
    assert panel_reading(-0.01, 0.11, 0.3, 0.4) == ("unresolved", "no actual loss")
    assert panel_reading(0.05, 0.11, 0.3, 0.51) == ("unresolved", "no collapse")
    assert panel_reading(0.05, -0.2, 0.09, 0.5) == ("null", None)
    assert panel_reading(0.05, -0.2, 0.09, 0.6) == ("unresolved", "no collapse")
    assert combine("positive", "positive").startswith("cutting C3")
    assert combine("null", "null") == "not demonstrated"
    assert combine("positive", "null") == "unresolved" and combine("positive", "unresolved") == "unresolved"
    rng = np.random.default_rng(0)
    x = np.ones(50)
    L_iv, D_iv = boot_max(x, 0.5 * x, [0.8 * x, 0.7 * x, 0.9 * x], rng, b=200)
    assert abs(L_iv[0] - 0.5) < 1e-12 and abs(D_iv[0] - 0.2) < 1e-12  # D against the largest draw loss (0.3)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
    import census  # noqa: E402
    main(frozenset(name for name, _, _, role in census.panels() if role == "selected"))
