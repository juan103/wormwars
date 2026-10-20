"""M1, part B on the fresh panels (docs/memory/M1-PLAN.md, draft 8): B1 persistence against alignment, B2 the settling
cohort, B3 the amplitude arm, and three of B4's cheap kills (complement erasure, the gap dissipation ratio, the
left-right antisymmetric share). The arms at the ramp's end run as extra row pairs in one batch (30 ticks); the intact
pair runs again alone for 300 ticks, and the two runs must agree. Per graph: runs/memory-m1/panels/<graph>__<seed>.json
(committed) and .npz (per-genome arrays for the bootstrap, local). Compute is recorded in runs/memory-m1/compute.json.
Usage: python scripts/memory_m1/panels.py"""
import json
import sys
import time

import numpy as np
import torch

from common import (C, GENOMES, MIN_ELIGIBLE, NAMES, OUT, PAIRS, RECORD, REMAIN, SEED, SEED2, SETTLE_TOL, START_FLOOR, S,
                    anatomy_core, erased, follow, nan_ratio, panel, panel_valid, ramp, scaled)
from wormwars import accounting as acct

torch.set_grad_enabled(False)
SCALES = (0.25, 0.5, 2.0)
DIR = OUT / "panels"
DIR.mkdir(exist_ok=True)
CORE_RESULT = [NAMES.index(x) for x in json.load(open(S.ROOT / "runs" / "memory-spikes" / "batch6.json"))["lists"]["top30_start"]]
CORE_ANAT = [NAMES.index(x) for x in anatomy_core(S.CON.chem)]
L_IDX, R_IDX = [p[0] for p in PAIRS], [p[1] for p in PAIRS]


def outside(idx):
    return [j for j in range(S.CON.n) if j not in set(idx)]


ARMS = [("intact", lambda v: v)] + [(f"scale{k}", lambda v, k=k: scaled(v, k)) for k in SCALES] + [
    ("complement_result", lambda v: erased(v, outside(CORE_RESULT))), ("erase_result", lambda v: erased(v, CORE_RESULT)),
    ("complement_anatomy", lambda v: erased(v, outside(CORE_ANAT))), ("erase_anatomy", lambda v: erased(v, CORE_ANAT))]


def gap_ratios(brain, dv):
    """dv [S, N]: the geometric ratio dv'L dv / dv'dv, and the dynamical one dv'T^-1 L dv / dv'dv (the gap term's part of
    the Euclidean relative decay rate, T = diag(tau); Astra, round 2)."""
    G, g_row, tau = brain.G.double(), brain.g_row.double(), brain.tau.double()

    def quad(x, y):  # x' L y
        return (g_row * x * y).sum(1) - torch.einsum("si,sij,sj->s", x, G, y)

    den = (dv ** 2).sum(1).numpy()
    return nan_ratio(quad(dv, dv).numpy(), den), nan_ratio(quad(dv / tau, dv).numpy(), den)  # NaN where dv = 0


def antisym(dv):  # [S, N]: the antisymmetric share over mirror pairs, the antisymmetric norm, the paired norm
    anti = ((dv[:, L_IDX] - dv[:, R_IDX]) ** 2).sum(1) / 2
    paired = (dv[:, L_IDX] ** 2 + dv[:, R_IDX] ** 2).sum(1)
    return nan_ratio(anti.numpy(), paired.numpy()), anti.sqrt().numpy(), paired.sqrt().numpy()


def wmean(x, w):
    """The weighted mean over the defined values; None if none is defined (Astra, round 5)."""
    d = np.isfinite(x)
    return float((x[d] * w[d]).sum() / w[d].sum()) if d.any() and w[d].sum() > 0 else None


def nmedian(x):
    d = np.isfinite(x)
    return float(np.median(x[d])) if d.any() else None


BATCH_TOLERANCE, BATCH_STOP, BATCH_STOP_FRACTION = 1e-5, 1e-3, 0.01


def run(gname, seed, n):
    t0 = time.time()
    con = S.graph(gname)
    g, cfg = S.genomes(con, n, seed)
    brain, v, food, steady = ramp(g, cfg, with_steady=True)
    arm, _, _ = follow(brain, cfg, torch.cat([f(v) for _, f in ARMS], 1), food, 30, record=(0, 30))
    rec, srange, _ = follow(brain, cfg, v, food, 300, window=10)
    # the intact pair inside the arm batch against the intact pair alone. The row compositions differ, and T1 section 3
    # claims no equality across compositions; an unstable genome can amplify a last-bit difference, so the policy is per
    # genome: the run stops for investigation only if more than 1% of genomes differ by more than BATCH_STOP (Fable,
    # Astra, round 5). Neither outcome is read as establishing its cause.
    gaps = np.max([(arm[t]["dy"][:, 0] - rec[t]["dy"][:, 0]).abs().numpy() for t in (0, 30)], 0)
    gap, over = float(gaps.max()), float((gaps > BATCH_STOP).mean())
    if over > BATCH_STOP_FRACTION:  # keep the per-genome gaps for the investigation (Fable, round 6)
        np.savez_compressed(DIR / f"{gname}__{seed}__batch_gap.npz", batch_gap=gaps)
        raise RuntimeError(f"{gname}: {over:.1%} of genomes differ by more than {BATCH_STOP} between the batched and lone runs")
    dy = {t: rec[t]["dy"][:, 0].numpy() for t in RECORD}
    a = np.abs(dy[0])
    ok = a >= START_FLOOR
    res = {"graph": gname, "seed": seed, "genomes": n, "eligible": int(ok.sum()),
           "valid": panel_valid(a, steady, int(ok.sum())), "steady_contrast_mean": float(np.abs(steady).mean()),
           "batch_gap": gap, "batch_gap_above_tolerance": bool(gap > BATCH_TOLERANCE), "batch_gap_frac_above_stop": over}
    if not res["valid"]:  # reported and excluded; nothing else is computed on it
        json.dump(res, open(DIR / f"{gname}__{seed}.json", "w"), indent=1)
        print(gname, seed, "not valid", flush=True)
        return res
    ae = a[ok]
    res.update({f"share{t}": float(np.abs(dy[t]).mean() / a.mean()) for t in RECORD[1:]})
    res.update({f"eligible_share{t}": float(np.abs(dy[t])[ok].sum() / ae.sum()) for t in RECORD[1:]})
    res["ineligible_numerator_frac30"] = float(np.abs(dy[30])[~ok].sum() / max(np.abs(dy[30]).sum(), 1e-300))
    res["ineligible_denominator_frac"] = float(a[~ok].sum() / a.sum())
    arrays = {"a": a, "ok": ok, "settle_range": srange, "d30": np.abs(dy[30]), "d100": np.abs(dy[100]), "batch_gap": gaps}
    # B1: |dy| = |c| |da| |cos|; N = alignment frozen at tick 0, A' = activity norm frozen at tick 0
    cn = float(C.norm())
    da0 = rec[0]["da"][:, 0]
    nrm0 = da0.norm(dim=1).numpy()
    cos0 = ((da0 @ C).abs().numpy() / np.maximum(cn * nrm0, 1e-300))
    for t in (30, 100):
        dat = rec[t]["da"][:, 0]
        assert np.allclose((dat @ C).abs().numpy(), np.abs(dy[t]), atol=1e-6), "the read-out is not c'da"
        nrmt = dat.norm(dim=1).numpy()
        cost = (dat @ C).abs().numpy() / np.maximum(cn * nrmt, 1e-300)
        numN = cn * nrmt * cos0  # per genome: |dy| had the alignment stayed as at tick 0
        numA = cn * nrm0 * cost  # per genome: |dy| had the norm stayed as at tick 0 (cos taken as 0 where da(t) = 0)
        zero = ok & (nrmt == 0)
        res[f"zero_da_t{t}"] = int(zero.sum())
        numA_alt = np.where(zero, cn * nrm0 * cos0, numA)  # the other convention: cos(t) taken as cos(0)
        top = ok & (a >= np.quantile(ae, 0.75))
        res[f"B1_t{t}"] = {"s": float(np.abs(dy[t])[ok].sum() / ae.sum()), "N": float(numN[ok].sum() / ae.sum()),
                           "Ap": float(numA[ok].sum() / ae.sum()), "Ap_alt_zero": float(numA_alt[ok].sum() / ae.sum()),
                           "s_top25": float(np.abs(dy[t])[top].sum() / a[top].sum()),
                           "N_top25": float(numN[top].sum() / a[top].sum()), "Ap_top25": float(numA[top].sum() / a[top].sum()),
                           "median_norm_ratio": float(np.median(nrmt[ok] / np.maximum(nrm0[ok], 1e-300))),
                           "median_alignment_ratio": float(np.median(cost[ok] / np.maximum(cos0[ok], 1e-300)))}
        arrays[f"numN{t}"], arrays[f"numA{t}"] = numN, numA
    # B2: the settling cohort (settled and remaining)
    remaining = ok & (np.abs(dy[300]) > REMAIN * a)
    cohort = (srange < SETTLE_TOL) & remaining
    res["B2"] = {"cohort": int(cohort.sum()), "settled_any": int((srange < SETTLE_TOL).sum()), "remaining": int(remaining.sum()),
                 "C30": float(np.abs(dy[30])[cohort].sum() / ae.sum()), "C300": float(np.abs(dy[300])[cohort].sum() / ae.sum())}
    arrays["cohort"] = cohort
    # B3 and the erasures, all within the arm batch: the erasures against the batched intact arm's start and
    # eligibility, so that no share mixes the two row compositions
    a_b = np.abs(arm[0]["dy"][:, 0].numpy())
    ok_b = a_b >= START_FLOOR
    for p, (name, _) in enumerate(ARMS):
        arrays[f"a_{name}"] = np.abs(arm[0]["dy"][:, p].numpy())
        arrays[f"d30_{name}"] = np.abs(arm[30]["dy"][:, p].numpy())
        arrays[f"da0_{name}"] = arm[0]["da"][:, p].norm(dim=1).numpy()
        arrays[f"dv0_{name}"] = arm[0]["dv"][:, p].norm(dim=1).numpy()
    scales = ("intact", "scale0.25", "scale0.5", "scale2.0")
    elig = np.all([arrays[f"a_{x}"] >= START_FLOOR for x in scales], 0)  # B3's population: eligible at every k
    res["B3_eligible_every_k"] = int(elig.sum())
    res["B3_ok"] = bool(elig.sum() >= MIN_ELIGIBLE)
    res["arms"] = {}
    for name, _ in ARMS:
        a_k, d30 = arrays[f"a_{name}"], arrays[f"d30_{name}"]
        rec_ = {"eligible_share30_vs_intact_start": float(d30[ok_b].sum() / max(a_b[ok_b].sum(), 1e-300))}
        if name in scales and res["B3_ok"]:  # B3's per-k numbers, on the population eligible at every k
            rec_.update({"B3_share30_vs_own_start": float(d30[elig].sum() / a_k[elig].sum()),
                         "B3_mean_a": float(a_k[elig].mean()), "B3_median_dv0": float(np.median(arrays[f"dv0_{name}"][elig])),
                         "B3_median_da0": float(np.median(arrays[f"da0_{name}"][elig]))})
        res["arms"][name] = rec_
    if res["B3_ok"]:
        lo, hi = arrays["a_scale0.5"], arrays["a_scale2.0"]
        r2r05 = nan_ratio(arrays["d30_scale2.0"][elig] / hi[elig], arrays["d30_scale0.5"][elig] / lo[elig])
        res["B3_median_r2_over_r05"] = nmedian(r2r05)  # undefined where r(0.5) = 0 (Astra, round 6)
        res["B3_r2_over_r05_undefined"] = int((~np.isfinite(r2r05)).sum())
    # B4: gap dissipation (geometric and dynamical) and the antisymmetric share, on eligible genomes, a-weighted
    w = ae / ae.sum()
    dv0, dv30 = rec[0]["dv"][:, 0], rec[30]["dv"][:, 0]
    p0, t0w = gap_ratios(brain, dv0)
    p30, t30w = gap_ratios(brain, dv30)
    s0, an0, pa0 = antisym(dv0)
    s30, an30, pa30 = antisym(dv30)
    res["B4"] = {"gap0_median": nmedian(p0[ok]), "gap30_median": nmedian(p30[ok]),
                 "gap0_wmean": wmean(p0[ok], w), "gap30_wmean": wmean(p30[ok], w),
                 "gap_dyn0_median": nmedian(t0w[ok]), "gap_dyn30_median": nmedian(t30w[ok]),
                 "gap_dyn0_wmean": wmean(t0w[ok], w), "gap_dyn30_wmean": wmean(t30w[ok], w),
                 "antisym0_wmean": wmean(s0[ok], w), "antisym30_wmean": wmean(s30[ok], w),
                 "antisym30_median": nmedian(s30[ok]),
                 "antisym_retention30_wmean": wmean(nan_ratio(an30[ok], an0[ok]), w),
                 "paired_retention30_wmean": wmean(nan_ratio(pa30[ok], pa0[ok]), w),
                 "undefined_counts": {"gap30": int((~np.isfinite(p30[ok])).sum()), "antisym30": int((~np.isfinite(s30[ok])).sum()),
                                      "antisym_retention30": int((~np.isfinite(nan_ratio(an30[ok], an0[ok]))).sum())}}
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(DIR / f"{gname}__{seed}.json", "w"), indent=1)
    np.savez_compressed(DIR / f"{gname}__{seed}.npz", **arrays)
    print(gname, seed, res["seconds"], "s", flush=True)
    return res


def jobs():
    random_, selected = panel()
    json.dump({"random": random_, "selected": selected}, open(OUT / "panel.json", "w"), indent=1)
    seen, out = set(), []
    for job in [("N2", SEED), ("N2", SEED2)] + [(x, SEED) for x in random_] + \
               [(x, SEED) for e in selected.values() for x in e.values()]:
        if job not in seen:
            seen.add(job)
            out.append(job)
    return out


if __name__ == "__main__":
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M1",
                       script="panels.py", argv=sys.argv[1:]):
        for gname, seed in jobs():
            if not (DIR / f"{gname}__{seed}.json").exists():
                run(gname, seed, GENOMES)
    print("done")
