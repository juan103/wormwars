"""03h's summary (experiments/03h-history-use/RESULTS.md): the numbers the results page quotes, read from the committed
records, so each one is traceable to a file and a field (AGENTS.md rule 5).

    python scripts/e03h_summary.py        # writes experiments/03h-history-use/summary.json

No simulation; CPU only.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "03h-history-use"
PILOT, DEV = EXP / "pilot", EXP / "development-records"
STAGES = ["bind", "gate", "sham-rates", "gate-sham", "pilot"]


def rec(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def r(x, n=4):
    return None if x is None else round(float(x), n)


def rl(xs, n=4):
    return [r(x, n) for x in xs]


def ci(d: dict, n=4) -> dict:
    return {"mean": r(d["mean"], n), "interval": [r(d["lo"], n), r(d["hi"], n)]}


def build() -> dict:
    """The summary, from the committed records."""
    st = {s: rec(PILOT / f"{s}.json") for s in STAGES}
    for s, d in st.items():
        if d["status"] != "completed" or d["smoke"]:
            raise SystemExit(f"{s} is not a completed full-size record")
    s0, s0b, amp, bp = (rec(DEV / f) for f in ("step0.json", "step0b.json", "amplitude-check.json", "b-power.json"))
    if amp["status"] != "completed" or amp["smoke"]:
        raise SystemExit("the amplitude check is not a completed full-size record")
    out = {"source": "experiments/03h-history-use/pilot/*.json and development-records/*.json, read by "
                     "scripts/e03h_summary.py"}

    out["stages"] = {s: {"commit": d["provenance"]["git_commit"][:7], "seconds_wall": r(d.get("seconds", 0), 1)}
                     for s, d in st.items()}
    out["stages"]["bind"]["bound_commit"] = st["bind"]["bound_commit"][:7]
    for name, d in (("step0", s0), ("step0b", s0b), ("amplitude-check", amp)):
        out["stages"][name] = {"commit": d["provenance"]["git_commit"][:7], "seconds_wall": r(d["seconds"], 1)}

    h = {k: rec(p)["totals"]["seconds_timed"] / 3600 for k, p in (
        ("step0_and_0b", DEV / "step0-compute.json"), ("pilot", PILOT / "compute.json"),
        ("amplitude_check", DEV / "amplitude-check-compute.json"))}
    out["compute"] = {**{k: r(v, 4) for k, v in h.items()}, "total": r(sum(h.values()), 4),
                      "cap_before_preregistration": st["pilot"]["config"]["cap_hours"],
                      "formal_cap": st["pilot"]["config"]["formal"]["cap_hours"],
                      "note": "GPU-hours by T0's accounting; the formal run did not take place"}

    out["rule7"] = {f: rec(DEV / f"equivalence-{f}.json")["bit_equal"] for f in ("cpu", "cuda")}
    v = s0["verification"]
    out["step0"] = {"verification_bit_equal": {m: bool(v[m]["fitness"]["bit_equal"] and v[m]["history"]["bit_equal"])
                                               for m in ("default", "replay")},
                    "graphs": s0["summary"]["graphs"], "mean_rho_level": r(s0["summary"]["mean_rho_level"], 5),
                    "between_graph_sd": r(s0["summary"]["between_graph_sd_rho_level"]),
                    "positive": s0["summary"]["positive"]}
    out["step0b"] = {k: {"mean": r(x["mean"], 5), "between_graph_sd": r(x["between_graph_sd"]),
                         "positive": x["positive"], "graphs": x["graphs"]} for k, x in s0b["summary"].items()}

    g = st["gate"]
    cm = g["check_means"]
    out["gate"] = {
        "families": {k: {"kind": f["kind"], "params": f["params"], "tuning": r(f["tuning_score"]),
                         "check": r(cm[k]), "edges": f["edges"]} for k, f in g["families"].items()},
        "level": {"estimate": r(g["verdicts"]["level"]["estimate"]), "lower_95": r(g["verdicts"]["level"]["lo"]),
                  "criterion": ">= 0.5", "pass": g["verdicts"]["level"]["pass"]},
        "relief": {"estimate": r(g["verdicts"]["relief"]["estimate"]),
                   "interval_90": [r(g["verdicts"]["relief"]["lo"]), r(g["verdicts"]["relief"]["hi"])],
                   "criterion": "inside +-0.3", "pass": g["verdicts"]["relief"]["pass"]},
        "recovered_share": {"estimate": r(g["verdicts"]["recovered_share"]["estimate"]),
                            "interval": [r(g["verdicts"]["recovered_share"]["lo"]),
                                         r(g["verdicts"]["recovered_share"]["hi"])]},
        "scripted_bit_gain_check": r(cm["memoryless+bit"] - cm["memoryless"]),
        "passed": g["passed"]}
    g2 = st["gate-sham"]
    out["gate_sham"] = {"estimate": r(g2["verdict"]["estimate"]),
                        "interval_90": [r(g2["verdict"]["lo"]), r(g2["verdict"]["hi"])],
                        "memoryless_plus_bit_kind": g2["families"]["memoryless+bit"]["kind"],
                        "pass": g2["verdict"]["pass"]}
    s1 = st["sham-rates"]
    out["sham_rates"] = {"graphs": [x["name"] for x in s1["graphs"]], "failures": len(s1["failures"]),
                         "counts": s1["counts"], "rates": rl(s1["rates"]),
                         "stationary_occupancy": r(s1["stationary_occupancy"]),
                         "seconds_cpu": {k: r(x, 1) for k, x in s1["seconds_s1"].items()}}

    p = st["pilot"]
    pr = p["readings"]
    out["pilot"] = {
        "amplitude": p["amplitude"], "action": p["action"],
        "reliability_level": r(pr["reliability_level_mean"]), "W": pr["W"],
        "decile_shift": {"per_graph": rl(pr["manipulation"]["decile_shift"]["per_graph"], 5),
                         **ci(pr["manipulation"]["decile_shift"])},
        "decile_test_means": {c: rl(v) for c, v in pr["B"]["T"].items()},
        "U": rl(pr["B"]["U"]), "U_between_graph_sd": r(pr["B"]["U_between_graph_sd"]),
        "U_mean_shared_world_se": r(pr["B"]["U_mean_shared_world_se"]),
        "turn_response_mean_abs": [float(f"{x:.2g}") for x in pr["manipulation"]["turn_response_mean_abs"]],
        "A_secondary": {"rho": {c: rl([x["rho"][c] for x in p["per_graph"]]) for c in ("level", "relief", "sham")},
                        "D": rl(pr["A_secondary"]["D"], 5), "D_mean": r(pr["A_secondary"]["D_mean"]),
                        "rho_H_dir_level": rl([x["rho_H_dir_level"] for x in p["per_graph"]]),
                        "quartile_difference_level": rl([x["quartile_difference_level"] for x in p["per_graph"]]),
                        "power_A2": r(pr["power_A2_reported"]["power"], 3)},
        "projection": {"plan": pr["projection"]["plan"],
                       "hours": {k: {kk: r(vv, 2) for kk, vv in x.items()} for k, x in pr["projection"]["hours"].items()}}}

    pass_u0 = {reading: {k: r(t[k]["N2 gains nothing"], 3) for k in ("point", "lower_90", "upper_90")}
               for reading, t in bp["pass_rate"].items()}
    out["b_power"] = {"null_mean_U": r(bp["model"]["null_mean_U"]),
                      "null_sd_U": {k: r(x) for k, x in bp["model"]["null_sd_U"].items()},
                      "pass_rate_if_N2_gains_nothing": pass_u0,
                      "u_for_80pct_power_point": {k: r(t["point"]) for k, t in bp["u_for_80pct_power"].items()},
                      "selection_bank_relief_minus_sham_all_genomes": rl(
                          [x["all_genomes_mean"] for x in bp["selection_bank_relief_minus_sham"]["per_graph"].values()])}

    def amp_part(x: dict) -> dict:
        sb = x["selection_bank"]
        return {"decile_shift": {"per_graph": rl(x["decile_shift"]["per_graph"], 5), **ci(x["decile_shift"])},
                "between_graph_sd": r(x["between_graph_sd"]),
                "ratio": {k: r(v, 2) for k, v in x["ratio_mean_to_sd"].items()},
                "all_genomes": {k: ci(sb[f"{k}_all_genomes"], 5) for k in ("relief_minus_sham", "relief_minus_level",
                                                                          "sham_minus_level")},
                "turn_response_mean_abs": [float(f"{t:.2g}") for t in x["turn_response_mean_abs"]]}

    out["amplitude_check"] = {"0.25": amp_part(amp["at_0.25"]),
                              **{k: amp_part(x) for k, x in amp["readings"].items()},
                              "guide": amp["guide"]}
    return out


def main() -> None:
    (EXP / "summary.json").write_text(json.dumps(build(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
                                      newline="\n")
    print(f"wrote {EXP / 'summary.json'}")


if __name__ == "__main__":
    main()
