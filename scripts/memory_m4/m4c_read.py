"""M4c's readings (docs/memory/M4C-PLAN.md): per RIA side, the fraction of the fresh N2 separate-states genomes erased
by the side's C3-internal cut, against its exterior count-and-weight-matched sets (X), its core weight-matched sets of more edges (W) and its
core count-and-weight-matched sets (C), the
contrasts with 90% intervals resampling both the genomes and the sets, the fixed reading, and the descriptive arms.
Writes runs/memory-m4c/readings.json.
Usage: python scripts/memory_m4/m4c_read.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
MARGIN, B, SEED_BOOT = 0.10, 2000, 20261126
FAMILIES = ("X", "W", "C")


def erased(outs):
    return np.array([o == "erased" for o in outs], float)


def side_arrays(arms, side, n_sets):
    """The side's per-genome erasure (0/1) and each family's [genomes, sets] erasure matrix."""
    e = erased(arms[side])
    fam = {f: np.stack([erased(arms[f"{side}:{f}{k}"]) for k in range(n_sets)], 1) for f in FAMILIES}
    return e, fam


def two_way(e, M, rng, b=B):
    """E_s, E_M (the mean over genomes and sets), D = E_s - E_M and its 90% interval; each resample draws the genomes
    with replacement and, independently, the sets with replacement."""
    n, k = M.shape
    D = np.empty(b)
    for r in range(b):
        gi = rng.integers(0, n, n)
        si = rng.integers(0, k, k)
        D[r] = e[gi].mean() - M[np.ix_(gi, si)].mean()
    return float(e.mean()), float(M.mean()), float(e.mean() - M.mean()), \
        [float(np.percentile(D, 5)), float(np.percentile(D, 95))]


def reading(iv):
    """iv[side][family] = the 90% interval of D. The fixed reading (draft 2): positive if every lower bound, both sides
    and all three families, exceeds the margin; an advantage ruled out if, for both sides, some family's upper bound
    is below it, naming those families (Astra, Fable, round 1); 'unresolved' otherwise."""
    if all(iv[s][f][0] > MARGIN for s in iv for f in FAMILIES):
        return "RIA's core edges erase the switch more often than every weight-matched control family"
    below = {s: [f for f in FAMILIES if iv[s][f][1] < MARGIN] for s in iv}
    if all(below.values()):
        return ("an advantage of 0.10 or more ruled out against at least one control family on each side ("
                + "; ".join(f"{s}: {', '.join(v)}" for s, v in below.items()) + ")")
    return "unresolved"


def main():
    import m4c
    sets = m4c.load_sets()
    seeds = m4c.panel_seeds()
    panels = []
    for s in seeds:
        f = m4c.OUT / f"N2__{s}.json"
        if not f.exists():
            raise SystemExit(f"N2__{s}: missing; no reading")
        p = json.load(open(f))
        m4c.validate(p, m4c.switch_ids(s), sets, f"N2__{s}")
        panels.append(p)
    used = [p for p in panels if p["genomes"]]
    arms = {a: sum((p["arms"][a] for p in used), []) for a in m4c.arm_edges(sets)}
    spec = m4c.n2_spec()
    key = spec.chem_anat.numpy()
    rng = np.random.default_rng(SEED_BOOT)
    valid = {s: bool(m4c.census_record(s)["valid"]) for s in seeds}  # Astra, round 2: invalid panels named
    res = {"panels": [(p["panel"], len(p["genomes"]), valid[p["seed"]]) for p in panels],
           "invalid_panels": [f"N2__{s}" for s in seeds if not valid[s]], "genomes": len(arms["intact"]), "sides": {},
           "arms": {}}
    iv = {}
    for side in m4c.SIDES:
        e, fam = side_arrays(arms, side, m4c.N_SETS)
        boot = [e[rng.integers(0, len(e), len(e))].mean() for _ in range(B)]
        r = {"E": float(e.mean()), "E_interval": [float(np.percentile(boot, 5)), float(np.percentile(boot, 95))],
             "erased": int(e.sum())}
        iv[side] = {}
        for f, M in fam.items():
            E_s, E_M, D, ivf = two_way(e, M, rng)
            per_set = M.mean(0)
            r[f] = {"E": E_M, "D": D, "D_interval": ivf, "set_max": float(per_set.max()),
                    "sets_reaching_E_side": int((per_set >= E_s).sum()), "per_set": per_set.tolist(),
                    "match": sets["sides"][side]["match"].get(f)}
            iv[side][f] = ivf
        res["sides"][side] = r
    res["reading"] = reading(iv)
    outs = ("both kept", "erased", "swapped", "other root", "not reached")
    for a, e in m4c.arm_edges(sets).items():
        res["arms"][a] = {"erased": int(sum(o == "erased" for o in arms[a])),
                          "outcomes": {o: int(sum(x == o for x in arms[a])) for o in outs},
                          "edges": None if e is None else len(e), "weight": None if e is None else float(key[e].sum())}
    dis = [(a, v) for a, v in res["arms"].items() if a.startswith("C3:") and a[3:] in m4c.c.NAMES]
    from scipy.stats import spearmanr
    rho = spearmanr([v["weight"] for _, v in dis], [v["erased"] for _, v in dis])
    res["dissection_weight_spearman"] = float(rho.statistic)
    json.dump(res, open(m4c.OUT / "readings.json", "w"), indent=1)
    print(f"reading: {res['reading']}  ({res['genomes']} genomes; panels {res['panels']})")
    for side, r in res["sides"].items():
        print(f"  {side}: erased {r['erased']} of {res['genomes']} = {r['E']:.3f} {np.round(r['E_interval'], 3).tolist()}")
        for f in FAMILIES:
            x = r[f]
            print(f"     {f}: {x['E']:.3f}, D {x['D']:+.3f} {np.round(x['D_interval'], 3).tolist()}; largest set "
                  f"{x['set_max']:.3f}; sets reaching the side {x['sets_reaching_E_side']}; squared-weight ratio "
                  f"{np.round(x['match']['squared_ratio'], 2).tolist()}")
    for a, v in res["arms"].items():
        if any(f":{f}" in a for f in FAMILIES):
            continue
        print(f"  {a:36s} erased {v['erased']:3d}  ({v['edges']} edges, weight {v['weight']})")
    print(f"  dissection: Spearman of weight and erased over C3's 30 neurons {res['dissection_weight_spearman']:+.2f}")


def test_rules():
    """The reading's boundaries and the two-way bootstrap's arithmetic (rule 9)."""
    ok = [0.11, 0.6]
    good = {s: {f: ok for f in FAMILIES} for s in ("RIAR", "RIAL")}
    assert reading(good).startswith("RIA's core edges")
    worse = {**good, "RIAL": {"X": ok, "W": ok, "C": [0.10, 0.6]}}
    assert reading(worse) == "unresolved"  # the margin is strict, and both sides and every family count
    matched = {s: {"X": ok, "W": [-0.2, 0.09], "C": ok} for s in ("RIAR", "RIAL")}
    assert reading(matched) == ("an advantage of 0.10 or more ruled out against at least one control family on each "
                                "side (RIAR: W; RIAL: W)")
    half = {"RIAR": {"X": ok, "W": [-0.2, 0.09], "C": ok}, "RIAL": {"X": ok, "W": [0.0, 0.3], "C": ok}}
    assert reading(half) == "unresolved"  # both sides must be matched
    rng = np.random.default_rng(0)
    e = np.array([1.0, 1.0, 0.0, 0.0])
    M = np.zeros((4, 4))
    M[:, 0] = 1  # one set erases everything, the other three nothing
    E_s, E_M, D, iv = two_way(e, M, rng, b=400)
    assert abs(E_s - 0.5) < 1e-12 and abs(E_M - 0.25) < 1e-12 and abs(D - 0.25) < 1e-12
    assert iv[0] < 0 < iv[1]  # resampling the sets moves E_M between 0 and 1
    _, _, _, iv1 = two_way(np.ones(5), np.zeros((5, 3)), rng, b=50)
    assert iv1 == [1.0, 1.0]
    M = np.zeros((4, 4))
    M[:, 0] = 1
    _, _, D, iv2 = two_way(np.ones(4), M, rng, b=400)  # the genomes agree; only the sets vary
    assert abs(D - 0.75) < 1e-12 and iv2[0] < 0.75 - 1e-9 and iv2[1] <= 1.0


if __name__ == "__main__":
    main()
