"""The memory thread's summary (docs/memory/SYNTHESIS.md): the numbers the synthesis quotes, read from the committed
records of M1 to M4e and of M5's pilot and power calculation, so each one is traceable to a file and a field (AGENTS.md rule 5).

    python scripts/memory_summary.py        # writes docs/memory/summary.json

No simulation; CPU only; seconds.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
OUT = ROOT / "docs" / "memory" / "summary.json"

COMPUTE = {
    "M1": ["memory-m1/compute-record.json", "memory-m1/d1_small_k-compute-record.json"],
    "M2 pilot": ["memory-m2/pilot-compute-record.json"],
    "M2 census": ["memory-m2-census/census-compute-record.json"],
    "M4a": ["memory-m4a/m4a-compute-record.json"],
    "M4b": ["memory-m4b/m4b-compute-record.json"],
    "M4c": ["memory-m4c/m4c-compute-record.json"],
    "M4d": ["memory-m4d/m4d-compute-record.json"],
    "M4e": ["memory-m4e/m4e-compute-record.json"],
    "M5 pilot": ["memory-m5-pilot/m5-pilot-compute-record.json"],
}


def rec(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def r(x, n=4):
    return None if x is None else round(float(x), n)


def rl(xs, n=4):
    return [r(x, n) for x in xs]


def pilot_checks(checks: dict) -> bool:
    """Every pilot check with a verdict passed (R5 is descriptive; M2-PILOT-RESULTS)."""
    verdicts = {k: v["passes"] for k, v in checks.items() if isinstance(v, dict) and "passes" in v}
    if set(verdicts) != {"R1", "R2", "R3", "R4", "R4p", "R6"}:
        raise SystemExit(f"unexpected pilot checks with a verdict: {sorted(verdicts)}")
    return all(verdicts.values())


def genomes_per_arm(hosts: list) -> dict:
    """Genomes per arm, summed over the hosts' panel records."""
    arms = ("I", "D", "R", "Rr", "P", "T", "T+G")
    arms_dir = RUNS / "memory-m4d" / "arms"
    return {a: sum(rec(arms_dir / f"{h}__{a.replace('+', 'p')}.json")["n"] for h in hosts) for a in arms}


def build() -> dict:
    """The summary, from the committed records."""
    out = {"source": "runs/memory-*/ committed records, read by scripts/memory_summary.py"}

    comp, total_s, total_u = {}, 0.0, 0
    for stage, files in COMPUTE.items():
        s = u = 0
        for f in files:
            d = rec(RUNS / f)
            if d["failed_attempts"]:
                raise SystemExit(f"{f} has failed attempts")
            s += d["totals"]["seconds_timed"]
            u += d["totals"]["neural_updates"]
        comp[stage] = {"cpu_hours": r(s / 3600, 2), "neural_updates": u}
        total_s, total_u = total_s + s, total_u + u
    out["compute"] = {**comp, "total": {"cpu_hours": r(total_s / 3600, 2), "neural_updates": total_u},
                      "note": "recorded wall-clock hours on the CPU (T0's accounting, category probe); the total is "
                              "summed before rounding; no GPU"}

    m1, acc, sk = (rec(RUNS / "memory-m1" / f) for f in ("summary.json", "accounting.json", "d1_small_k.json"))
    es = m1["eligible_share30"]
    ens = acc["ensembles"].values()
    out["M1"] = {
        "fresh_eligible_share30": {"N2": [r(es["N2"], 3), r(es["N2_seed2"], 3)],
                                   "reference_median": r(es["random_median"], 3),
                                   "reference_range": [r(es["random_min"], 3), r(es["random_max"], 3)],
                                   "reference_at_or_above_N2": es["random_at_or_above_N2"]},
        "mean_r30": {"N2": r(acc["N2"]["mean_r30"], 3),
                     "ensemble_medians": [r(min(e["mean_r30"]["median"] for e in ens), 3),
                                          r(max(e["mean_r30"]["median"] for e in ens), 3)],
                     "graphs_at_or_above_N2": sum(e["mean_r30"]["graphs_at_or_above_N2"] for e in ens)},
        "cov_term30": {"N2": r(acc["N2"]["cov_term30"], 3),
                       "ensemble_medians": [r(min(e["cov_term30"]["median"] for e in ens), 3),
                                            r(max(e["cov_term30"]["median"] for e in ens), 3)]},
        "share30_trim5": {"N2": r(acc["N2"]["share30_trim5"], 3),
                          "graphs_at_or_above_N2": [e["share30_trim5"]["graphs_at_or_above_N2"] for e in ens]},
        "D1_reading": m1["D1_reading"],
        "D1_replication": {"reading": sk["D1_reading"],
                           "f": {s: [r(sk["D1_a"][s]["f"], 2), rl(sk["D1_a"][s]["f_interval"], 2)]
                                 for s in ("seed7600", "seed7700")}},
        "D2": {s: {"P1_over_T": r(m1["D2"][s]["P1_over_T"], 2), "interval": rl(m1["D2"][s]["P1_over_T_interval"], 2)}
               for s in ("seed7600", "seed7700")},
        "kills": {k: v for k, v in m1["kills"].items() if isinstance(v, str)},
    }

    cs, sp = rec(RUNS / "memory-m2-census" / "summary.json"), rec(RUNS / "memory-m2-census" / "split.json")
    n2 = ("N2__7600", "N2__7700")
    out["M2"] = {
        "pilot_checks_pass": pilot_checks(rec(RUNS / "memory-m2" / "summary.json")["checks"]),
        "census_checks": cs["checks"],
        "N2_counts": {p: sp["panels"][p]["counts"] for p in n2},
        "N2_eligible": {p: sp["panels"][p]["eligible"] for p in n2},
        "reading_t30": cs["readings_t30"],
        "phi_S_t30": {p: [r(cs["phi"]["t30"][p]["phi_S"]["point"], 2), rl(cs["phi"]["t30"][p]["phi_S"]["interval"], 2)]
                      for p in n2},
        "phi_F_t30": {p: [r(cs["phi"]["t30"][p]["phi_F"]["point"], 2), rl(cs["phi"]["t30"][p]["phi_F"]["interval"], 2)]
                      for p in n2},
        "phi_S_t300": {p: r(sp["t300"]["panels"][p]["point"]["phi_S"], 2) for p in n2},
        "reading_t300": cs["reading_t300"],
    }

    m4a = rec(RUNS / "memory-m4a" / "readings.json")
    p2 = m4a["part2"]
    out["M4a"] = {
        "readings": m4a["readings"],
        "primary_D": {p: r(m4a["panels"][p]["arms"]["C3-early-30"].get("D"), 3) for p in n2},
        "part2": {g: {"genomes": p2[g]["genomes"], "C3_erased": p2[g]["counts"]["C3"].get("erased", 0),
                      "sampled_erased_fraction": r(p2[g]["fractions"]["random"].get("erased", 0), 3)}
                  for g in ("N2", "selected", "reference")},
    }

    m4b = rec(RUNS / "memory-m4b" / "readings.json")
    g = m4b["groups"]
    out["M4b"] = {
        "reading": m4b["reading"],
        "groups": {k: {"genomes": g[k]["genomes"], "E_own": r(g[k]["E_own"], 3), "E_ext": r(g[k]["E_ctrl"], 3),
                       "E_out": r(g[k]["E_out"], 3), "D_ext": [r(g[k]["D"], 3), rl(g[k]["D_interval"], 3)],
                       "D_out": [r(g[k]["D_out"], 3), rl(g[k]["D_out_interval"], 3)]}
                   for k in ("N2", "selected")},
        "dissection": {k.split(":", 1)[-1]: m4b["dissection"][k]["erased"]
                       for k in ("C3", "C3:RIAR", "C3:RIAL", "C3:SMDVL", "C3:SMDVR")},
        "dissection_of": m4b["dissection"]["C3"]["of"],
    }

    m4c = rec(RUNS / "memory-m4c" / "readings.json")
    out["M4c"] = {
        "reading": m4c["reading"],
        "genomes": m4c["genomes"],
        "sides": {s: {"E": r(v["E"], 3), "erased": v["erased"],
                      "families": {f: {"E": r(v[f]["E"], 3), "D": r(v[f]["D"], 3),
                                       "D_interval": rl(v[f]["D_interval"], 3), "set_max": r(v[f]["set_max"], 3),
                                       "sets_reaching_E_side": v[f]["sets_reaching_E_side"]}
                                   for f in ("X", "W", "C")}}
                  for s, v in m4c["sides"].items()},
    }

    m4d = rec(RUNS / "memory-m4d" / "readings.json")
    c = m4d["counts"]
    out["M4d"] = {
        "reading": m4d["reading"],
        "reading_on_counted_genomes": m4d["reading_before_bounds"],
        "D_TI": [r(m4d["D_TI"]["D"]), rl(m4d["D_TI"]["interval"])],
        "D_TR": [r(m4d["D_TR"]["D"]), rl(m4d["D_TR"]["interval"])],
        "envelope": {k: rl(v) for k, v in m4d["envelope"].items()},
        "hosts_T_over_I": m4d["hosts_T_over_I"],
        "hosts_T_over_R": m4d["hosts_T_over_R"],
        "separate_states": {a: sum(v) for a, v in c["separate"].items()},
        "unresolved": {a: sum(v) for a, v in c["unresolved"].items()},
        "genomes_per_arm": genomes_per_arm(c["hosts"]),
    }

    m4e = rec(RUNS / "memory-m4e" / "readings.json")

    def contrast(v):
        return {"D": r(v["D"]), "interval": rl(v["interval"]), "envelope": rl(v["envelope"]),
                "hosts_below_at_above": [sum(x < 0 for x in v["per_host"]), sum(x == 0 for x in v["per_host"]),
                                         sum(x > 0 for x in v["per_host"])],
                "direction": v["direction"], "size": v["size"]}

    ce = m4e["counts"]
    out["M4e"] = {
        "primary": {k: contrast(v) for k, v in m4e["primary"].items()},
        "first_pass_direction": {k: v["direction"] for k, v in m4e["first_pass_reading"].items()},
        "descriptive": {k: contrast(v) for k, v in m4e["secondary"].items()},
        "interaction": {"D": r(m4e["interaction"]["D"]), "interval": rl(m4e["interaction"]["interval"]),
                        "envelope": rl(m4e["interaction"]["envelope"])},
        "separate_states": {a: sum(v) for a, v in ce["separate"].items()},
        "unresolved": {a: sum(v) for a, v in ce["unresolved"].items()},
        "genomes_per_arm": ce["n"] * len(ce["hosts"]),
        "second_pass_used": m4e["second_pass_used"],
        "audited_fading_per_arm": m4e["audited_fading_per_arm"],
        "audit_fading_to_separate": sum(v.get("fading -> separate states", 0) for v in m4e["transitions"].values()),
    }

    pil = rec(RUNS / "memory-m5-pilot" / "report.json")
    tr = pil["at_22000"]["T_minus_Rr"]
    pw = rec(RUNS / "memory-m5-power-welch" / "power.json")["answer"]

    def policy(v, rows):
        return {k: {"power": r(v[k]["success"]), "cpu_hours": r(v[k]["cpu_hours"]["mean"], 1)} for k in rows}

    out["M5"] = {
        "pilot": {
            "T_minus_Rr": {"mean": r(tr["mean"]), "interval": rl(tr["interval"]), "hosts_above_zero": tr["hosts_above_zero"],
                           "sd_of_host_contrasts": r(tr["variance"]["sd_of_host_contrasts"]),
                           "genome_share": r(tr["variance"]["shares_of_host_contrast_variance"]["genome"], 2)},
            "unresolved_at_22000_resolved_by_100000": {a: [v["genomes"], v["genomes"] - v["class_100000"]["unresolved"]]
                                                       for a, v in pil["longer"]["by_arm"].items()},
            "audit": {a: [v["audited"], v["fading_to_separate"]] for a, v in pil["audit"]["by_arm"].items()},
        },
        "power": {
            "C": {"allocation": pw["C"]["allocation"], "h1": pw["C"]["h1"], "hmax": pw["C"]["hmax"],
                  **policy(pw["C"], ("central", "core", "above"))},
            "A": {"allocation": pw["A"]["cheapest"]["allocation"], "H": pw["A"]["cheapest"]["H"],
                  "power_central": r(pw["A"]["cheapest"]["power, base, central"]),
                  "power_core": r(pw["A"]["cheapest"]["power, base, core"]),
                  "cpu_hours_central": r(pw["A"]["cheapest"]["cpu_hours, base, central"], 1)},
            "B": {"allocation": pw["B"]["cheapest"]["allocation"], "H": pw["B"]["cheapest"]["H"],
                  "power_central": r(pw["B"]["cheapest"]["power, base, central"]),
                  "power_core": r(pw["B"]["cheapest"]["power, base, core"]),
                  "cpu_hours_central": r(pw["B"]["cheapest"]["cpu_hours, base, central"], 1)},
            "recommend": pw["choice"]["recommend"], "C_saving_central": r(pw["choice"]["saving"], 3),
        },
    }
    return out


def main() -> None:
    OUT.write_text(json.dumps(build(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
