"""M5's pilot report (docs/memory/M5-PILOT-PLAN.md, "Outputs"): Rr's counts on M4e's hosts, T − Rr per host with
its hull interval and variance split (paired genome part, the independent one as a sensitivity), the paired class
tables, (b)'s longer horizon with s and r pooled and per arm and the horizon rule, the contrasts again at the 100,000
-tick classes, (c)'s audit with its bounds pooled with the panels' own audits, the denominators and the costs. Every
input is checked first (m4e.verify_run, then each record's own rules). A stage the cap stopped is reported with its
finished and missing panels, and no rule is applied to it. Descriptive: design inputs, not readings.

Usage: python scripts/memory_m5/m5_pilot_read.py     # writes runs/memory-m5-pilot/report.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
import m5_pilot as MP  # noqa: E402

m4e = MP.m4e
import m4e_read as RD  # noqa: E402

SEED_READ = 20264301  # the host bootstrap's generator (above M4e's families and the pilot's)
SETTLE_RULE = 0.5  # the plan: s >= 0.5 means M5 continues its unresolved genomes to 100,000 ticks


def cp_upper(x, n, level=0.95):
    """One-sided Clopper-Pearson upper bound for x events in n."""
    if n == 0:
        return 1.0
    return 1.0 if x >= n else float(stats.beta.ppf(level, x + 1, n - x))


def horizon_rule(s):
    return "continue to 100,000 ticks" if s >= SETTLE_RULE else "keep 22,000 ticks"


def variance_split(d, pa, pb, n, p11=None):
    """Method of moments on per-host-draw differences d [H, D] (shares of n genomes). The genome part is analytic:
    paired, (pa(1 − pa) + pb(1 − pb) − 2 (p11 − pa pb)) / n with p11 the share confirmed in both arms (Astra, round
    3), or, with p11 None, two independent binomials (the sensitivity). The draw part is the within-host spread above
    it, the host part the host means' spread above the draw and genome parts."""
    H, D = d.shape
    cov = 0.0 if p11 is None else p11 - pa * pb
    genome = (pa * (1 - pa) + pb * (1 - pb) - 2 * cov) / n
    within = float(d.var(axis=1, ddof=1).mean()) if D > 1 else float("nan")
    draw = max(within - genome, 0.0) if D > 1 else float("nan")
    host_means = d.mean(1)
    host = max(float(host_means.var(ddof=1)) - (within if D > 1 else genome) / D, 0.0)
    per_host = host + ((draw if D > 1 else 0.0) + genome) / D
    share = (lambda x: x / per_host) if per_host > 0 else (lambda x: None)  # noqa: E731
    return {"host": host, "draw": draw, "genome": genome, "within_host": within, "paired": p11 is not None,
            "shares_of_host_contrast_variance": {"host": share(host), "draw": share(draw / D) if D > 1 else None,
                                                 "genome": share(genome / D)},
            "sd_of_host_contrasts": float(host_means.std(ddof=1))}


def classes(rec, longer=None):
    """The merged classes at 22,000 ticks, or with (b)'s 100,000-tick classes in place of the unresolved ones."""
    m = m4e.merged_classes(rec)
    if longer is not None:
        for i, x in zip(longer["ids"], longer["class_100000"]):
            m[i] = x
    return m


def counts(rec, longer=None):
    m = classes(rec, longer)
    return {"separate": sum(x in MP.SEPARATE for x in m),
            "separate_first_pass": sum(x in MP.SEPARATE for x in rec["class"]),
            "unresolved": m.count(MP.UNRESOLVED), "not_classified_fading": sum(x != MP.FADING for x in m),
            "first_pass_fading": rec["class"].count(MP.FADING), "valid": rec.get("valid"),
            "eligible": rec.get("eligible"), "second_pass_genomes": len(rec["second"]["ids"]),
            "second_pass_seconds": rec["second"]["seconds"], "panel_seconds": rec["seconds"]}


def contrast(panels, a, b, n, hosts):
    """T − control per host-draw and per host on the confirmed shares; hull interval over hosts; the variance split
    with the paired genome part and the independent one beside it. panels[(host, draw, arm)] = classes."""
    d = np.array([[(sum(x in MP.SEPARATE for x in panels[(h, dr, a)]) - sum(x in MP.SEPARATE for x in
                                                                           panels[(h, dr, b)])) / n
                   for dr in (0, 1)] for h in hosts])
    sa = np.array([[x in MP.SEPARATE for x in panels[(h, dr, a)]] for h in hosts for dr in (0, 1)])
    sb = np.array([[x in MP.SEPARATE for x in panels[(h, dr, b)]] for h in hosts for dr in (0, 1)])
    pa, pb, p11 = float(sa.mean()), float(sb.mean()), float((sa & sb).mean())
    idx = np.random.default_rng(SEED_READ).integers(0, len(d), (RD.B, len(d)))
    m = d.mean(1)
    return {"mean": float(m.mean()), "interval": list(RD.hull(m, idx)), "per_host": m.tolist(),
            "per_host_draw": d.tolist(), "hosts_above_zero": int((m > 0).sum()), "rates": [pa, pb],
            "confirmed_in_both": int((sa & sb).sum()), "variance": variance_split(d, pa, pb, n, p11),
            "variance_independent": variance_split(d, pa, pb, n)}


def paired_table(ma, mb):
    """5 x 5 table of classes, a's rows against b's columns, on the same genomes."""
    t = np.zeros((len(MP.CODES), len(MP.CODES)), int)
    for x, y in zip(ma, mb):
        t[x, y] += 1
    return t.tolist()


def stage_files(verified, stage, cols, recs):
    """{(host, draw, arm): stage output validated against its source record (MP.check_out), and the panels missing."""
    got, missing = {}, []
    for p, v in enumerate(verified):
        for a in MP.PILOT_ARMS:
            f = MP.OUT / stage / f"{v['rec']['name']}__d{v['draw']}__{a}.json"
            if not f.exists():
                missing.append(f.name)
                continue
            out = json.load(open(f))
            want = (MP.longer_targets(recs[a][p]) if stage == "longer" else [i for q, i in AUDIT[a] if q == p])
            MP.check_out(out, want, cols, f.name, (v["rec"]["name"], v["draw"], a), recs[a][p])
            got[(v["rec"]["host"], v["draw"], a)] = out
    return got, missing


def replay_summary(got):
    """The registered check's record: the largest root-field deviation and the fallbacks, per arm."""
    out = {}
    for (_, _, a), o in got.items():
        s = out.setdefault(a, {"max_root_deviation": 0.0, "fallbacks": 0})
        s["max_root_deviation"] = max(s["max_root_deviation"], o["max_root_deviation"])
        s["fallbacks"] += len(o["fallbacks"])
    return out


AUDIT = {}


def reason_table(reasons):
    t = {}
    for r in reasons:
        for part in (r or "").split("; "):
            if part:
                t[part] = t.get(part, 0) + 1
    return dict(sorted(t.items(), key=lambda kv: -kv[1]))


def longer_report(longer, missing):
    rows = {a: {"genomes": 0, "class_100000": {k: 0 for k in MP.CODES}, "reasons_22000": [], "reasons_100000": []}
            for a in MP.PILOT_ARMS}
    for (_, _, a), out in longer.items():
        rows[a]["genomes"] += len(out["ids"])
        for x in out["class_100000"]:
            rows[a]["class_100000"][MP.CODES[x]] += 1
        rows[a]["reasons_22000"] += [x["reason"] for x in out["recorded_22000"]]
        rows[a]["reasons_100000"] += out["reason_100000"]

    def sr(rs):
        n = sum(r["genomes"] for r in rs)
        resolved = sum(r["genomes"] - r["class_100000"]["unresolved"] for r in rs)
        sep = sum(r["class_100000"]["separate states"] + r["class_100000"]["separate states, read-out silent"]
                  for r in rs)
        return {"genomes": n, "s": resolved / n if n else None, "r": sep / n if n else None, "separate": sep,
                "r_upper_95": cp_upper(sep, n)}

    for a, r in rows.items():
        r.update(sr([r]))
        r["reasons_22000"], r["reasons_100000"] = reason_table(r["reasons_22000"]), reason_table(r["reasons_100000"])
    pooled = sr(list(rows.values()))
    out = {"complete": not missing, "missing": missing, "by_arm": rows, "pooled": pooled}
    # the rule is applied only to the whole population (the plan: a stage the cap stopped gets no rule)
    out["horizon_rule"] = horizon_rule(pooled["s"]) if not missing and pooled["genomes"] else (
        "not applied: incomplete" if missing else "no genomes")
    return out


def audit_report(audit, missing, recs):
    out = {}
    for a in MP.PILOT_ARMS:
        n = trig = moved = 0
        changes, by_panel = {}, {}
        for (h, dr, arm), r in audit.items():
            if arm != a:
                continue
            n += len(r["ids"])
            t = sum(x in MP.SEPARATE for x in r["class_22000"])
            trig += t
            moved += sum(x != MP.FADING for x in r["class_22000"])
            for x in r["class_22000"]:
                if x != MP.FADING:
                    changes[MP.CODES[x]] = changes.get(MP.CODES[x], 0) + 1
            by_panel[f"{h} d{dr}"] = {"audited": len(r["ids"]), "fading_to_separate": t}
        n0 = t0 = 0  # the panels' own audits (M4e's for T and K, (a)'s for Rr)
        for rec in recs[a]:
            second = dict(zip(rec["second"]["ids"], rec["second"]["class"]))
            for i in rec["audit"]:
                if rec["class"][i] == MP.FADING:
                    n0 += 1
                    t0 += second[i] in MP.SEPARATE
        out[a] = {"audited": n, "fading_to_separate": trig, "any_change": moved, "changes": changes,
                  "upper_95": cp_upper(trig, n), "by_panel": by_panel,
                  "panel_audits": {"audited": n0, "fading_to_separate": t0},
                  "pooled": {"audited": n + n0, "fading_to_separate": trig + t0, "upper_95": cp_upper(trig + t0,
                                                                                                    n + n0)}}
    return {"complete": not missing, "missing": missing, "by_arm": out}


def main():
    verified = m4e.verify_run()
    n = m4e.N_DRAW
    rep = {"note": "design inputs for M5's power calculation; descriptive, not a reading"}
    have = [v for v in verified if MP.rr_file(v["rec"], v["draw"]).exists()]
    rep["rr_missing"] = [f"{v['rec']['name']} d{v['draw']}" for v in verified if v not in have]
    recs = {a: [MP.panel_record(v, a) for v in have] for a in MP.PILOT_ARMS}
    key = lambda v: (v["rec"]["host"], v["draw"])  # noqa: E731
    rep["counts"] = {a: {f"{v['rec']['name']} d{v['draw']}": counts(rec) for v, rec in zip(have, recs[a])}
                     for a in MP.PILOT_ARMS}
    rep["paired_T_by_Rr"] = {f"{v['rec']['name']} d{v['draw']}": paired_table(m4e.merged_classes(t),
                                                                              m4e.merged_classes(r))
                             for v, t, r in zip(have, recs["T"], recs["Rr"])}
    rep["Rr_audit_failed_panels"] = [f"{v['rec']['name']} d{v['draw']}" for v, r in zip(have, recs["Rr"])
                                     if m4e.audit_failed(r)]
    rep["rr_blocks"] = json.load(open(MP.OUT / "rr-summary.json")) if (MP.OUT / "rr-summary.json").exists() else None
    hosts = sorted({v["rec"]["host"] for v in have if all((v["rec"]["host"], d) in {key(w) for w in have}
                                                         for d in (0, 1))})
    panels22 = {(*key(v), a): m4e.merged_classes(rec) for a in MP.PILOT_ARMS for v, rec in zip(have, recs[a])}
    rep["at_22000"] = {"T_minus_Rr": contrast(panels22, "T", "Rr", n, hosts) if len(hosts) > 1 else None,
                       "T_minus_K": contrast(panels22, "T", "K", n, hosts) if len(hosts) > 1 else None,
                       "hosts": len(hosts)}
    if not rep["rr_missing"]:
        AUDIT.update({a: MP.audit_sample(recs[a], a) for a in MP.PILOT_ARMS})
        cf = MP.OUT / "composition-check.json"
        if cf.exists():
            MP.check_composition_file(json.load(open(cf)), verified, recs)
            rep["composition_check"] = json.load(open(cf))
        longer, lmiss = stage_files(verified, "longer", MP.LONGER_COLS, recs)
        if longer and not cf.exists():
            raise MP.Stop("longer outputs exist without their composition check")
        rep["longer_replay"] = replay_summary(longer)
        rep["longer"] = longer_report(longer, lmiss)
        if not lmiss:
            p100 = {(*key(v), a): classes(rec, longer[(*key(v), a)]) for a in MP.PILOT_ARMS
                    for v, rec in zip(have, recs[a])}
            rep["at_100000"] = {"T_minus_Rr": contrast(p100, "T", "Rr", n, hosts),
                                "T_minus_K": contrast(p100, "T", "K", n, hosts),
                                "paired_T_by_Rr": {f"{v['rec']['name']} d{v['draw']}": paired_table(
                                    p100[(*key(v), "T")], p100[(*key(v), "Rr")]) for v in have},
                                "counts": {a: {f"{v['rec']['name']} d{v['draw']}": counts(rec, longer[(*key(v), a)])
                                               for v, rec in zip(have, recs[a])} for a in MP.PILOT_ARMS}}
        audit, amiss = stage_files(verified, "audit", MP.AUDIT_COLS, recs)
        rep["audit"] = audit_report(audit, amiss, recs)
        rep["audit_replay"] = replay_summary(audit)
        rep["seconds"] = {stage: {f"{h} d{d} {a}": o["seconds"] for (h, d, a), o in got.items()}
                          for stage, got in (("longer", longer), ("audit", audit))}
    (MP.OUT / "report.json").write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8", newline="\n")
    t = rep["at_22000"]["T_minus_Rr"]
    if t:
        print(f"T - Rr {t['mean']:+.4f} {t['interval']}; hosts above 0 {t['hosts_above_zero']}; "
              f"SD {t['variance']['sd_of_host_contrasts']:.4f}")
    if "longer" in rep:
        p = rep["longer"]["pooled"]
        print(f"longer: s {p['s']}, r {p['r']} (upper {p['r_upper_95']:.3f}); {rep['longer']['horizon_rule']}")


if __name__ == "__main__":
    main()
