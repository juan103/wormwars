"""M2 census: the tables of the results, from the committed records only (split.json, the panel records, c1 to c5).

Written after the data, to make the numbers of M2-CENSUS-RESULTS.md traceable (rule 5). No simulation.

    py scripts/memory_m2/census_tables.py > runs/memory-m2-census/tables.txt
"""
import json
import pathlib

import numpy as np

OUT = pathlib.Path("runs/memory-m2-census")
CLS = ["S", "F", "O", "U"]


def load(f):
    return json.load(open(OUT / f))


def main():
    sp = load("split.json")
    roles = {}
    silent, s_ratio, chunks = {}, {}, []
    for f in sorted(OUT.glob("*__7*.json")):
        if f.name.startswith("c1__") or f.name.endswith(".skipped.json"):
            continue
        r = json.load(open(f))
        roles[r["panel"]] = (r["role"], r["graph"], r["seconds"], r["ineligible_numerator_frac30"],
                             r["ineligible_denominator_frac"], r["valid"])
        chunks += r["chunk_seconds"]
        k = sum(g["class"] == "separate states, read-out silent" for g in r["genomes"])
        if k:
            silent[r["panel"]] = (k, r["role"])
        s_ratio[r["panel"]] = [g["d30"] / g["a"] for g in r["genomes"] if g["class"].startswith("separate states")]
    print(f"panels {len(roles)}, valid {sum(v[5] for v in roles.values())}")
    print(f"panel seconds: total {sum(v[2] for v in roles.values()):.0f}, "
          f"median {np.median([v[2] for v in roles.values()]):.0f}, max {max(v[2] for v in roles.values()):.0f}")
    print(f"chunk seconds: {len(chunks)} chunks, {min(chunks):.1f} to {max(chunks):.1f}, median {np.median(chunks):.1f}")
    print(f"separate states, read-out silent (inside the S counts below): {silent}, total {sum(v[0] for v in silent.values())}")
    for n in ["N2__7600", "N2__7700"]:
        print(f"   {n}: separate-states genomes' own |dy(30)|/a, {min(s_ratio[n]):.3f} to {max(s_ratio[n]):.3f}")
    print("stages (stage seconds; the panel seconds above are the panel records')", load("stages.json"), "guard", load("guard.json")["projected_hours"])
    top = max(roles, key=lambda n: roles[n][3])
    print(f"ineligible numerator(30) fraction, max over panels {roles[top][3]:.4f} ({top}); N2 "
          f"{roles['N2__7600'][3]:.4f}, {roles['N2__7700'][3]:.4f}; denominator, max {max(v[4] for v in roles.values()):.5f}")

    print("\n== C1")
    worst = {"a": 0.0, "d30": 0.0, "d100": 0.0}
    elig, coh, frac, shares = [], [], [], []
    for f in sorted(OUT.glob("c1__*.json")):
        c = json.load(open(f))
        for k in worst:
            worst[k] = max(worst[k], c["gap_max"][k])
        frac.append(c["frac_above"])
        elig += [(c["panel"], g) for g in c["eligibility_changed"]["genomes"]]
        coh += [(c["panel"], g) for g in c["cohort_changed"]["genomes"]]
        for pairs in (c["eligible_share"], c["cohort_C"]):  # a missing value (None) is printed, not compared
            shares += [abs(x - y) if x is not None and y is not None else float("nan") for x, y in pairs.values()]
    print(f"panels {len(frac)}; largest gaps {worst}; largest fraction above 1e-3 {max(frac)}")
    print(f"eligibility changes {elig}; cohort changes {coh}; largest share/C gap {np.nanmax(shares):.2e}, missing {int(np.isnan(shares).sum())}")
    c3 = load("c3.json")
    print(f"\n== C3 {len(c3['checks'])} roots, max {max(x['max_abs_diff'] for x in c3['checks']):.2e}, passes {c3['passes']}")
    c5 = load("c5.json")
    print(f"== C5 genomes {c5['genomes']}, agreement {c5['agreement']}, basin changes {c5['basin_changes']}, "
          f"passes {c5['passes']}")
    c2 = load("c2.json")
    print(f"== C2 {sum(v['correct'] for v in c2['cases'].values())}/{len(c2['cases'])} named correctly")

    print("\n== C4 and classes per panel (counts S F O U; unresolved fraction of eligible and of numerator 30)")
    for name, p in sp["panels"].items():
        role = roles[name][0]
        c = p["counts"]
        print(f"{name:32s} {role:20s} elig {p['eligible']:5d}  S {c['S']:3d} F {c['F']:4d} O {c['O']} U {c['U']}"
              f"  Ufrac {p['unresolved_frac']:.4f} Unum {p['unresolved_numerator30_frac']:.4f}"
              f"{'  C4 FLAG' if p['C4_flagged'] else ''}")

    print("\n== totals by role (genomes, S, F, O, U; graphs with any S)")
    for role in ["N2", "reference", "selected", "core-frozen-shuffle", "hub-frozen-shuffle"]:
        ps = [n for n in sp["panels"] if roles[n][0] == role]
        tot = {k: sum(sp["panels"][n]["counts"][k] for n in ps) for k in CLS}
        el = sum(sp["panels"][n]["eligible"] for n in ps)
        anyS = sum(sp["panels"][n]["counts"]["S"] > 0 for n in ps)
        print(f"{role:20s} panels {len(ps):2d} eligible {el:6d} {tot} graphs with S {anyS}")

    print("\n== unresolved reasons and oscillation periods (in ticks)")
    for name, p in sp["panels"].items():
        if p["unresolved_reasons"] or p["oscillation_periods"]:
            per = [[round(x / 32, 2) for x in h if x is not None] for h in p["oscillation_periods"]]
            print(f"{name}: {p['unresolved_reasons']} periods {per}")

    print("\n== N2's unresolved and oscillating genomes: |dy(t)| / denominator / Lambda(t), at ticks 30 and 300")
    for n in ["N2__7600", "N2__7700"]:
        r = load(f"{n}.json")
        lam = {t: sp[f"t{t}"]["panels"][n]["point"]["Lambda"] for t in (30, 300)}
        for g in r["genomes"]:
            if g["class"] in ("unresolved", "persistent oscillation"):
                print(f"   {n} genome {g['genome']} {g['class']}: " + ", ".join(
                    f"t{t} |dy| {g[f'd{t}']:.4f}, /den/Lambda {g[f'd{t}'] / r['denominator'] / lam[t]:.4f}" for t in (30, 300)))

    for t in ("t30", "t300"):
        print(f"\n== split at {t}: reading {sp[t]['reading']} {sp[t]['readings']} branch {sp[t]['branch']}")
        for name, p in sp[t]["panels"].items():
            pt, iv = p["point"], p["intervals"]
            print(f"{name}: Lambda {pt['Lambda']:.4f} [{iv['Lambda'][0]:.4f}, {iv['Lambda'][1]:.4f}], "
                  f"median-definition lead {p['lead_median_definition']:.4f}, resamples Lambda<=0 "
                  f"{p['resamples_lambda_not_positive']}")
            for k in ["phi_S", "phi_S_lo", "phi_S_hi", "phi_F", "phi_F_lo", "phi_F_hi", "phi_O", "phi_U"]:
                print(f"   {k:9s} {pt[k]:+.3f} [{iv[k][0]:+.3f}, {iv[k][1]:+.3f}]")
            print("   by ensemble phi_S / phi_F: " + ", ".join(
                f"{e} {v['phi_S']:.2f}/{v['phi_F']:.2f}" for e, v in p["by_ensemble"].items()))
            for X, cr in p["composition_retention"].items():
                print(f"   {X}: w_N2 {cr['w_N2']:.4f} rho_N2 {cr['rho_N2']:.3f} w_ref {cr['w_ref_mean']:.4f} | "
                      f"composition {cr['composition']:+.4f} retention {cr['retention']:+.4f} presence "
                      f"{cr['presence']:+.4f} ({cr['presence_pairs']} pairs)")
        con = sp[t]["contributions"]
        ref = [n for n in con if roles[n][0] == "reference"]
        print("   reference mean: " + ", ".join(f"{k} {np.mean([con[n][k] for n in ref]):.4f}" for k in ["s"] + CLS))
        print(f"   reference s range: {min(con[n]['s'] for n in ref):.4f} to {max(con[n]['s'] for n in ref):.4f}")
        for role in ["N2", "selected", "core-frozen-shuffle", "hub-frozen-shuffle"]:
            for n in [n for n in con if roles[n][0] == role]:
                print(f"   {n:32s} " + ", ".join(f"{k} {con[n][k]:.4f}" for k in ["s"] + CLS))

    print("\n== contributions over time: N2 and the reference mean (S, F)")
    ot = sp["over_time"]
    ticks = ot["ticks"]
    for tk in [0, 10, 30, 100, 300, 1000, 2000]:
        i = ticks.index(tk)
        print(f"t {tk:5d}: " + " | ".join(f"{n} S {ot['contributions'][n]['S'][i]:.4f} F {ot['contributions'][n]['F'][i]:.4f}"
                                         for n in ["N2__7600", "N2__7700", "reference_mean"]))
    print("phi over time (point estimates, from the same contributions):")
    con = ot["contributions"]
    for tk in [10, 30, 50, 100, 200, 300, 1000, 2000]:  # at tick 0 every share is 1, so Lambda is 0
        i = ticks.index(tk)
        row = []
        for n in ["N2__7600", "N2__7700"]:
            lam = {X: con[n][X][i] - con["reference_mean"][X][i] for X in CLS}
            tot = sum(lam.values())
            if tot <= 0:
                row.append(f"{n} Lambda {tot:.4f} (not positive: no phi)")
                continue
            row.append(f"{n} Lambda {tot:.4f} phi_S {lam['S'] / tot:.3f} phi_F {lam['F'] / tot:.3f}")
        print(f"t {tk:5d}: " + " | ".join(row))

    print("\n== where the two states differ (fractions of |v1-v2|^2, weighted by |dy(30)|), and fading's slow rate")
    for name, p in sp["panels"].items():
        w = p["where_separation"]
        ws = "" if not w or w.get("core") is None else (f"core {w['core']:.3f} hubs {w['hubs']:.3f} rest {w['rest']:.3f} "
                                                       f"readout {w['readout']:.3f}")
        print(f"{name:32s} {roles[name][0]:20s} S {p['counts']['S']:3d} {ws:55s} slow rate {p['fading_slow_rate_wmedian']:.4f}")

    print("\n== M1's cohort against separate states (genomes; numerator 30 / 300), summed by role")
    for role in ["N2", "reference", "selected", "core-frozen-shuffle", "hub-frozen-shuffle"]:
        ps = [n for n in sp["panels"] if roles[n][0] == role]
        cells = {}
        for n in ps:
            for k, v in sp["panels"][n]["cohort_by_separate"].items():
                c = cells.setdefault(k, [0, 0.0, 0.0])
                c[0] += v["genomes"]; c[1] += v["numerator30"]; c[2] += v["numerator300"]
        notsep = {}
        for n in ps:
            for k, v in sp["panels"][n]["cohort_not_separate_classes"].items():
                notsep[k] = notsep.get(k, 0) + v
        print(f"{role:20s} " + "; ".join(f"{k} {c[0]} ({c[1]:.2f} / {c[2]:.2f})" for k, c in cells.items())
              + f"; cohort not separate: {notsep}")
    for n in ["N2__7600", "N2__7700"]:
        print(f"   {n}: " + "; ".join(f"{k} {v['genomes']} ({v['numerator30']:.2f} / {v['numerator300']:.2f})"
                                     for k, v in sp["panels"][n]["cohort_by_separate"].items()))

    print("\n== the cheap rule against the full verdict, every history")
    tot = {}
    for p in sp["panels"].values():
        for k, v in p["cheap_rule"].items():
            tot[k] = tot.get(k, 0) + v
    print(tot)

    print("\n== the locating-radius sensitivity")
    rs = sp["radius_sensitivity"]
    print(f"histories {rs['histories']}; genomes changing class {rs['genomes_changing_class']}; phi_S(30) {rs['phi_S_t30']}")
    for name, p in sp["panels"].items():
        for g in p["radius"]:
            print(f"   {name} genome {g['genome']}: {g['class_now']} -> {g['class']}; "
                  + "; ".join(f"h{h['history']} {h['dist_end_root']:.2e} {h['reach']}" for h in g["histories"]))

    print("\n== fading's own retention per panel: w_F = sum_F a / sum_E a, rho_F(t) = sum_F |dy(t)| / sum_F a "
          "(from the panel records)")
    by = {}
    for name in sp["panels"]:
        gs = json.load(open(OUT / f"{name}.json"))["genomes"]
        den = sum(g["a"] for g in gs)
        fa = sum(g["a"] for g in gs if g["class"] == "fading")
        f30 = sum(g["d30"] for g in gs if g["class"] == "fading")
        f300 = sum(g["d300"] for g in gs if g["class"] == "fading")
        by.setdefault(roles[name][0], []).append((name, fa / den, f30 / fa, f300 / fa))
    for role, rows in by.items():
        r30 = [x[2] for x in rows]
        print(f"{role:20s} rho_F(30) median {np.median(r30):.3f} range [{min(r30):.3f}, {max(r30):.3f}]")
        if role != "reference":
            for x in rows:
                print(f"   {x[0]:32s} w_F {x[1]:.3f} rho_F(30) {x[2]:.3f} rho_F(300) {x[3]:.4f}")
    ref30 = [x[2] for x in by["reference"]]
    for x in by["N2"]:
        print(f"   {x[0]} rho_F(30) {x[2]:.3f}: above {sum(v < x[2] for v in ref30)} of {len(ref30)} reference graphs")

    rates = {n: sp["panels"][n]["fading_slow_rate_wmedian"] for n in sp["panels"]}
    ref_rates = [rates[n] for n in rates if roles[n][0] == "reference"]
    print(f"fading's slow rate, reference median {np.median(ref_rates):.4f} range [{min(ref_rates):.4f}, {max(ref_rates):.4f}]")
    for n in ["N2__7600", "N2__7700"]:
        print(f"   {n} {rates[n]:.4f}: slower than {sum(v < rates[n] for v in ref_rates)} of {len(ref_rates)}")

    print("\n== settling and share (Spearman, the 30 reference graphs)")
    print(json.dumps(sp["settling_and_share"]))


if __name__ == "__main__":
    main()
