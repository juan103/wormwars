"""M1, amendment 1 (docs/memory/M1-PLAN.md): D1's targeted replication with smaller k on N2 only. Reruns N2's two
panels with M1's four amplitude arms (k = 1, 0.25, 0.5, 2) and four new ones (k = 1/8, 1/16, 1/32, 1/64), checks that
the rerun reproduces M1's arrays, then reads D1 on M1's population, strata, used strata and weights, with N2's new
observations added and the balance condition replaced. Reads runs/memory-m1/{summary,panel}.json and panels/*.npz
(local); writes runs/memory-m1/d1_small_k.json and d1_small_k/N2__<seed>.npz (local).
Usage: python scripts/memory_m1/d1_small_k.py"""
import json
import sys

import numpy as np
import torch

from common import ENSEMBLES, GENOMES, OUT, SEED, SEED2, START_FLOOR, S, dump, ensemble_of, follow, ramp, scaled
from summarise import B, MAX_BAD, d1_reading, interval, ratio, ref_median
from wormwars import accounting as acct

torch.set_grad_enabled(False)
OLD = ("intact", "scale0.25", "scale0.5", "scale2.0")
OLD_K = (1.0, 0.25, 0.5, 2.0)
NEW_K = (1 / 8, 1 / 16, 1 / 32, 1 / 64)
NEW = tuple(f"scale1/{round(1 / k)}" for k in NEW_K)
DIR = OUT / "d1_small_k"
REPRO_TOLERANCE, REPRO_STOP, REPRO_STOP_FRACTION = 1e-5, 1e-3, 0.01  # M1's batch policy
BALANCE = 0.25  # the replaced balance condition: every used stratum within 25% (Astra, Fable, round 1)
SCALE_BAND = (0.8, 1.25)  # a median within-genome ratio outside it annotates the reading (Fable, round 1); no gate


def rerun(seed, n):
    """N2's panel with the old and the new arms in one batch of 8 row pairs, 30 ticks. Returns {arm: {a, d30, da0}}."""
    g, cfg = S.genomes(S.CON, n, seed)
    brain, v, food = ramp(g, cfg)
    ks = OLD_K + NEW_K  # k = 1 is the ramp-end state itself, as in M1, not m + 1.0 (v - m) (Fable, round 1)
    arm, _, _ = follow(brain, cfg, torch.cat([v if k == 1.0 else scaled(v, k) for k in ks], 1), food, 30, record=(0, 30))
    return {x: {"a": np.abs(arm[0]["dy"][:, p].numpy()), "d30": np.abs(arm[30]["dy"][:, p].numpy()),
                "da0": arm[0]["da"][:, p].norm(dim=1).numpy()} for p, x in enumerate(OLD + NEW)}


def reproduction_gaps(new, m1):
    """Per genome, the largest gap between the rerun's old arms and M1's arrays, over a and |dy(30)|."""
    return np.max([np.abs(new[x][q] - m1[f"{q}_{x}"]) for x in OLD for q in ("a", "d30")], 0)


def observations(z, var, extra=None):
    """A panel's B3 observations: M1's four arms from its arrays z, and for N2 the new arms (extra), each entering only
    where its own a is at or above the floor. Returns the population (eligible at every old k) and a list of
    (stratum variable, |dy(30)|, a, mask) per arm."""
    elig = np.all([z[f"a_{x}"] >= START_FLOOR for x in OLD], 0)
    obs = [(z[f"{var}_{x}"], z[f"d30_{x}"], z[f"a_{x}"], elig) for x in OLD]
    for x in (extra or {}):
        e = extra[x]
        obs.append((e[var], e["d30"], e["a"], elig & (e["a"] >= START_FLOOR)))
    return elig, obs


def stratum_sums(obs, edges, W):
    """Per stratum: resampled (W [B, n]) and point sums of |dy(30)|, a and the observation count; the distinct genomes
    with an observation; and the counts and the |dy(30)| sums per arm."""
    K = len(edges) + 1
    num, den, cnt = np.zeros((len(W), K)), np.zeros((len(W), K)), np.zeros((len(W), K))
    num0, den0, cnt0 = np.zeros(K), np.zeros(K), np.zeros(K)
    per_arm, per_arm_num, anyarm = [], [], np.zeros((len(obs[0][1]), K), bool)
    for var, d, a, mask in obs:
        oh = np.eye(K)[np.digitize(var, edges)] * mask[:, None]
        num += W @ (oh * d[:, None])
        den += W @ (oh * a[:, None])
        cnt += W @ oh
        num0 += oh.T @ d
        den0 += oh.T @ a
        cnt0 += oh.sum(0)
        per_arm.append(oh.sum(0))
        per_arm_num.append(oh.T @ d)
        anyarm |= oh > 0
    return {"bs": (num, den, cnt), "pt": (num0, den0, cnt0), "genomes": anyarm.sum(0), "per_arm": per_arm,
            "per_arm_num": per_arm_num}


def std_base(num, den, cnt, used, pi):
    m_num, m_den = ratio(num[..., used], cnt[..., used]), ratio(den[..., used], cnt[..., used])
    return ratio((pi[used] * m_num).sum(-1), (pi[used] * m_den).sum(-1)), ratio(num[..., used].sum(-1), den[..., used].sum(-1))


def coverage(elig, obs, edges, used, d_int, a_int):
    """Against the original population: a genome is covered if any of its arms above the floor lies in a used
    stratum; the covered genomes' share of the intact-arm numerator and denominator over the whole population."""
    covered = elig & np.any([mask & used[np.digitize(var, edges)] for var, _, _, mask in obs], 0)
    return (float(d_int[covered].sum() / max(d_int[elig].sum(), 1e-300)),
            float(a_int[covered].sum() / max(a_int[elig].sum(), 1e-300)))


def balance(num0, mean_a, med_a, used):
    """The replaced condition: over every used stratum, the worst |E[a | k]_N2 / median_ref - 1| (a gate on N2's pooled
    numerator would not match the pi-weighted standardisation; Astra, Fable, round 1); and the numerator-weighted
    mean imbalance. An undefined ratio counts as out of balance."""
    idx = np.where(used)[0]
    frac = num0[idx] / max(num0[idx].sum(), 1e-300)
    dev = np.abs(mean_a[idx] / med_a[idx] - 1)
    return (float(np.max(np.where(np.isfinite(dev), dev, np.inf))) if len(idx) else 0.0, float(np.nansum(frac * dev)),
            {int(i): {"numerator_frac_used": float(f), "mean_a_ratio": float(m / r)} for i, f, m, r in
             zip(idx, frac, mean_a[idx], med_a[idx])})


def read(var, Z, extra, edges, used, pi, W, by_e, gpick, keys, n2keys):
    """D1 on one basis. Z: M1's arrays per panel; extra: the new arms per N2 panel (empty for the reproduction)."""
    sums, elig, obs = {}, {}, {}
    for k in keys:
        elig[k], obs[k] = observations(Z[k], var, extra.get(k))
        sums[k] = stratum_sums(obs[k], edges, W[k])
    refs = [k for k in keys if k not in n2keys]
    P0 = {k: std_base(*sums[k]["pt"], used, pi) for k in keys}
    PB = {k: std_base(*sums[k]["bs"], used, pi) for k in keys}
    rs, rb = float(np.median([P0[k][0] for k in refs])), float(np.median([P0[k][1] for k in refs]))
    rsb = ref_median({k: PB[k][0] for k in refs}, by_e, gpick, len(W[refs[0]]))
    rbb = ref_median({k: PB[k][1] for k in refs}, by_e, gpick, len(W[refs[0]]))
    mean_a = {k: ratio(sums[k]["pt"][1], sums[k]["pt"][2]) for k in keys}
    med_a = np.nanmedian(np.stack([mean_a[k] for k in refs]), 0)
    out = {}
    for n2 in n2keys:
        cov_num, cov_den = coverage(elig[n2], obs[n2], edges, used, Z[n2]["d30_intact"], Z[n2]["a_intact"])
        worst, wmean, per_stratum = balance(sums[n2]["pt"][0], mean_a[n2], med_a, used)
        lead_ok = bool(np.isfinite(P0[n2][1]) and rb > 0 and P0[n2][1] >= 1.1 * rb)
        f = float((P0[n2][0] - rs) / (P0[n2][1] - rb)) if (np.isfinite(P0[n2][1]) and P0[n2][1] > rb) else None
        fi, bad = interval(ratio(PB[n2][0] - rsb, PB[n2][1] - rbb))
        num0 = sums[n2]["pt"][0]
        arms = OLD + tuple(extra.get(n2, {}))
        by_arm = [float(pn[used].sum()) for pn in sums[n2]["per_arm_num"]]
        out[f"seed{n2[1]}"] = {
            "std": float(P0[n2][0]), "baseline": float(P0[n2][1]), "ref_std": rs, "ref_baseline": rb, "f": f,
            "f_interval": fi, "bad": bad, "baseline_lead_ratio": float(P0[n2][1] / rb) if rb > 0 else None,
            "coverage_numerator": cov_num, "coverage_denominator": cov_den,
            "balance_worst": worst, "balance_weighted_mean": wmean, "balance_per_used_stratum": per_stratum,
            "conditions": bool(lead_ok and cov_num >= 0.75 and cov_den >= 0.75 and worst <= BALANCE),
            "f_above_0.75": bool(f is not None and f > 0.75), "std_lead": float(P0[n2][0] - rs),
            "genomes_per_used_stratum": [int(sums[n2]["genomes"][i]) for i in np.where(used)[0]],
            "k_composition": {x: [int(c) for c in pa] for x, pa in zip(arms, sums[n2]["per_arm"])},
            "used_numerator_frac_by_arm": dict(zip(arms, [b / max(sum(by_arm), 1e-300) for b in by_arm])),
            "dropped_numerator_frac": float(num0[~used].sum() / max(num0.sum(), 1e-300))}
    return out


def inputs():
    s = json.load(open(OUT / "summary.json"))
    panel = json.load(open(OUT / "panel.json"))
    P = OUT / "panels"
    meta = {g: json.load(open(P / f"{g}__{SEED}.json")) for g in panel["random"]}
    refs = [(g, SEED) for g in panel["random"] if meta[g]["valid"] and meta[g].get("B3_ok")]  # as summarise.py
    n2keys = [("N2", SEED), ("N2", SEED2)]
    keys = n2keys + refs
    Z = {k: dict(np.load(P / f"{k[0]}__{k[1]}.npz", allow_pickle=False)) for k in keys}
    return s, Z, keys, n2keys, refs


def weights(rng, keys, n2keys, refs, n, nres=B):
    draw = lambda: np.stack([np.bincount(rng.integers(0, n, n), minlength=n) for _ in range(nres)]).astype(np.float64)  # noqa: E731
    w7600, w7700 = draw(), draw()
    W = {k: (w7700 if k == n2keys[1] else w7600) for k in keys}
    by_e = {e: [k for k in refs if ensemble_of(k[0]) == e] for e in ENSEMBLES}
    gpick = {e: (rng.integers(0, len(by_e[e]), (nres, len(by_e[e]))) if by_e[e] else np.zeros((nres, 0), int)) for e in ENSEMBLES}
    return W, by_e, gpick


def basis(s, var):
    rec = s["D1_B3_a" if var == "a" else "D1_B3_da"]
    edges = np.array(rec["edges"])
    used = np.zeros(len(edges) + 1, bool)
    used[rec["used_strata"]] = True
    return rec, edges, used, np.array(rec["pi"])


def check_reproduces_m1(s, Z, keys, n2keys, refs):
    """With the new arms left out, M1's point values on both bases and both panels (the plan's check that can fail)."""
    W, by_e, gpick = weights(np.random.default_rng(0), keys, n2keys, refs, len(Z[keys[0]]["a"]), nres=4)
    for var in ("a", "da0"):
        rec, edges, used, pi = basis(s, var)
        got = read(var, Z, {}, edges, used, pi, W, by_e, gpick, keys, n2keys)
        for tag, g in got.items():
            for q in ("std", "baseline", "ref_std", "ref_baseline", "f", "coverage_numerator", "coverage_denominator"):
                assert (g[q] is None and rec[tag][q] is None) or (None not in (g[q], rec[tag][q]) and abs(g[q] - rec[tag][q]) < 1e-9),                     (var, tag, q, g[q], rec[tag][q])


def test_rules():
    """The floor and the new balance rule on constructed data (they must be able to fail)."""
    edges = np.array([0.01, 0.1])
    z = {f"{q}_{x}": np.full(3, 0.05) for x in OLD for q in ("a", "d30", "da0")}
    extra = {"scale1/64": {"a": np.array([0.0005, 0.05, 0.05]), "d30": np.ones(3), "da0": np.ones(3)}}
    elig, obs = observations(z, "a", extra)
    assert elig.all() and list(obs[-1][3]) == [False, True, True]  # below the floor: dropped, not in stratum 0
    sums = stratum_sums(obs, edges, np.ones((1, 3)))
    assert sums["pt"][2][0] == 0 and sums["pt"][2][1] == 4 * 3 + 2
    used = np.array([True, True, False])
    worst, _, _ = balance(np.array([3.0, 1.0, 96.0]), np.array([0.02, 0.05, 0.3]), np.array([0.01, 0.05, 0.12]), used)
    assert worst == 1.0  # a used stratum at twice the reference's mean a fails, though 3% of the whole numerator (M1's case)
    worst, _, _ = balance(np.array([0.01, 10.0, 50.0]), np.array([0.02, 0.05, 0.3]), np.array([0.01, 0.05, 0.12]), used)
    assert worst == 1.0  # and so does one holding 0.1% of the used numerator: every used stratum counts
    worst, _, _ = balance(np.array([1.0, 1.0, 50.0]), np.array([0.011, 0.05, 0.3]), np.array([0.01, 0.05, 0.12]), used)
    assert abs(worst - 0.1) < 1e-12  # the unused stratum's imbalance does not count
    worst, _, _ = balance(np.array([1.0, 1.0, 50.0]), np.array([np.nan, 0.05, 0.3]), np.array([0.01, 0.05, 0.12]), used)
    assert worst == np.inf  # an undefined ratio is out of balance
    assert coverage(elig, obs, edges, np.array([False, False, True]), np.ones(3), np.ones(3)) == (0.0, 0.0)
    assert coverage(elig, obs, edges, np.array([False, True, False]), np.array([1.0, 2.0, 1.0]), np.ones(3)) == (1.0, 1.0)
    obs_b = [(np.array([0.05, 0.5, 0.5]), np.ones(3), np.ones(3), elig)]  # genome 0 in stratum 1, the others in 2
    assert coverage(elig, obs_b, edges, np.array([False, True, False]), np.array([1.0, 2.0, 1.0]), np.ones(3)) == (0.25, 1 / 3)


def main():
    test_rules()
    s, Z, keys, n2keys, refs = inputs()
    check_reproduces_m1(s, Z, keys, n2keys, refs)
    DIR.mkdir(exist_ok=True)
    extra, repro = {}, {}
    with acct.recorded(DIR / "compute", DIR / "compute.json", default="probe", experiment="memory-M1",
                       script="d1_small_k.py", argv=sys.argv[1:]):
        for k in n2keys:
            f = DIR / f"N2__{k[1]}.npz"
            if not f.exists():
                new = rerun(k[1], GENOMES)
                gaps = reproduction_gaps(new, Z[k])
                np.savez_compressed(f, gaps=gaps, **{f"{q}_{x}": new[x][q] for x in OLD + NEW for q in ("a", "d30", "da0")})
            z = np.load(f, allow_pickle=False)
            gaps = z["gaps"]
            repro[f"seed{k[1]}"] = {"max_gap": float(gaps.max()), "above_tolerance": bool(gaps.max() > REPRO_TOLERANCE),
                                    "frac_above_stop": float((gaps > REPRO_STOP).mean())}
            if repro[f"seed{k[1]}"]["frac_above_stop"] > REPRO_STOP_FRACTION:
                raise RuntimeError(f"N2 seed {k[1]}: the rerun does not reproduce M1's arrays ({repro})")
            extra[k] = {x: {q: z[f"{q}_{x}"] for q in ("a", "d30", "da0")} for x in NEW}
    W, by_e, gpick = weights(np.random.default_rng(20261022), keys, n2keys, refs, len(Z[keys[0]]["a"]))
    out = {"reproduction": repro, "new_k": list(NEW), "reference_graphs": len(refs)}
    for var, tag in (("a", "D1_a"), ("da0", "D1_da")):
        rec, edges, used, pi = basis(s, var)
        out[tag] = read(var, Z, extra, edges, used, pi, W, by_e, gpick, keys, n2keys)
    out["D1_reading"] = d1_reading([{q: out["D1_a"][t][q] for q in ("conditions", "f_interval", "bad")}
                                    for t in ("seed7600", "seed7700")], [])  # A2 cannot intervene (all unsupported)
    e30 = s["eligible_share30"]
    out["M1_intact_eligible_lead"] = {"seed7600": e30["N2"] - e30["random_median"], "seed7700": e30["N2_seed2"] - e30["random_median"]}
    for b in ("D1_a", "D1_da"):  # descriptive (Astra, rounds 1 and 2): the standardised lead against the intact lead
        for tag in ("seed7600", "seed7700"):
            out[b][tag]["std_lead_over_intact_lead"] = out[b][tag]["std_lead"] / out["M1_intact_eligible_lead"][tag]
    desc = {}
    for k in n2keys:
        elig = np.all([Z[k][f"a_{x}"] >= START_FLOOR for x in OLD], 0)
        arm = lambda x: extra[k][x] if x in NEW else {q: Z[k][f"{q}_{x}"] for q in ("a", "d30")}  # noqa: E731
        d = {}
        for x in NEW:
            m = elig & (arm(x)["a"] >= START_FLOOR)
            d[x] = {"genomes_above_floor": int(m.sum()), "share30_vs_own_start": float(arm(x)["d30"][m].sum() / arm(x)["a"][m].sum()),
                    "mean_a": float(arm(x)["a"][m].mean())}
        for hi, lo in (("scale1/64", "scale1/32"), ("scale1/8", "scale0.25")):
            m = elig & (arm(hi)["a"] >= START_FLOOR) & (arm(lo)["a"] >= START_FLOOR)
            r = ratio(arm(hi)["d30"][m] / arm(hi)["a"][m], arm(lo)["d30"][m] / arm(lo)["a"][m])
            d[f"median_r_{hi}_over_r_{lo}"] = float(np.nanmedian(r)) if np.isfinite(r).any() else None
        d["outside_scale_band"] = [x for x in d if x.startswith("median_r_") and d[x] is not None
                                   and not SCALE_BAND[0] <= d[x] <= SCALE_BAND[1]]
        desc[f"seed{k[1]}"] = d
    out["N2_new_arms"] = desc
    out["annotation"] = ("N2's retention depends on scale at small k" if any(desc[t]["outside_scale_band"] for t in desc) else None)
    out["bad_limit"] = MAX_BAD
    dump(out, "d1_small_k.json")
    print("D1 (amendment 1):", out["D1_reading"], {t: (out["D1_a"][t]["f"], out["D1_a"][t]["f_interval"],
                                                       out["D1_a"][t]["coverage_numerator"])
                                                   for t in ("seed7600", "seed7700")})  # f may be None (Astra, round 2)


if __name__ == "__main__":
    main()
