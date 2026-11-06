"""E5-0's summary (experiments/E5-hunter/E5-0/RESULTS.md): the numbers the results page quotes, read from the committed
records (all but the exploratory phases, which are in phases.json), so each one is traceable to a file and a field
(AGENTS.md rule 5). It also writes the per-genome table the plan asks for before any family summary (§6).

    python scripts/e5_0_summary.py        # writes summary.json and genomes.md in experiments/E5-hunter/E5-0/

No simulation; CPU only.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "E5-hunter" / "E5-0"
STAGES = ["bench", "equivalence", "calibration", "evaluation", "probes", "reading"]
FAMILIES = ["e4s1", "L1 carrier", "e2d", "generation0"]
SERIES = {"H2": "H2-", "H2b walk": "H2b-walk", "H2b wall": "H2b-wall"}
CODES = {"qualifies": "Q", "uncertain": "U", "fails cue dependence": "C",
         "capture criteria met; cue dependence untested": "T"}


def rec(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def r(x, n=6):
    return None if x is None else round(float(x), n)


def rl(xs, n=6):
    return [r(x, n) for x in xs]


def family(label: str) -> str:
    if label.startswith("e4s1"):
        return "e4s1"
    if label.startswith("generation0"):
        return "generation0"
    if label == "L1 carrier":
        return label
    if label.startswith("e2 ") or label.startswith("04a "):
        return "e2d"
    raise ValueError(f"no family for {label}")


def code(reading: str) -> str:
    if reading in CODES:
        return CODES[reading]
    if reading.startswith("demonstrated failure: "):
        return "F" + "".join(x.strip()[0] for x in reading.split(": ", 1)[1].split(","))
    raise ValueError(f"unknown reading {reading}")


def spread(xs: list[float]) -> dict:
    return {"n": len(xs), "mean": r(sum(xs) / len(xs)), "min": r(min(xs)), "max": r(max(xs))}


def contrast(rows: dict) -> dict:
    """A family's paired contrasts: the spread of the means, and how many lower bounds are above 0 and upper bounds
    below 0."""
    out = {}
    for f in FAMILIES:
        hs = [v for k, v in rows.items() if k in LABELS and family(k) == f]
        if hs:
            out[f] = {**spread([h["mean"] for h in hs]), "lower_above_0": sum(h["bounds"][0] > 0 for h in hs),
                      "upper_below_0": sum(h["bounds"][1] < 0 for h in hs)}
    return out


LABELS: set[str] = set()


def build() -> dict:
    """The summary, from the committed records."""
    d = {s: rec(EXP / f"{s}.json") for s in STAGES}
    for s in ("calibration", "evaluation", "probes"):
        if d[s].get("complete") is not True:
            raise SystemExit(f"{s}.json is not complete")
    if d["equivalence"].get("passed") is not True or d["bench"].get("fits") is not True:
        raise SystemExit("equivalence or bench did not pass")
    commits = {rec(EXP / f"{s}-started.json")["provenance"]["git_commit"]
               for s in ("bench", "equivalence", "calibrate", "evaluate", "probe")}
    if len(commits) != 1:
        raise SystemExit(f"the stages ran on more than one commit: {commits}")
    rd, cal, eq, ev = d["reading"], d["calibration"], d["equivalence"], d["evaluation"]
    LABELS.clear()
    LABELS.update(rd["settings"]["H1-bite"]["hunters"])

    cr = rec(EXP / "compute-record.json")
    compute = {"attempts": len(cr["attempts"]), "failed_attempts": cr["failed_attempts"],
               "hours": {k: r(v["seconds"] / 3600, 3) for k, v in cr["categories"].items()},
               "hours_total": r(cr["totals"]["seconds_timed"] / 3600, 3),
               "cap_hours": cal["registered"]["cap_hours"],
               "bench_projected_hours": {k: r(v, 3) for k, v in d["bench"]["projected_hours"].items()},
               "bench_seconds_per_episode": {k: r(v) for k, v in d["bench"]["seconds"].items()},
               "cuts": d["bench"]["cuts"], "untested_under_the_cap": d["probes"]["untested_under_the_cap"]}

    ep = cal["e_prey"]
    calibration = {
        "e_prey": r(ep["e_prey"]), "held_damage_per_tick": {k: r(ep["held"][k]) for k in ("median", "min", "max")},
        "held_start_clamped": ep["held"]["start_clamped"],
        "largest_single_tick_damage": r(ep["largest_single_tick_damage"]),
        "approaches": {k: {x: v[x] for x in ("aim", "worlds", "start_clamped", "captured_first_life",
                                               "kill_ticks_median", "kill_ticks_min", "kill_ticks_max")}
                       for k, v in ep["approaches"].items()},
        "route": cal["route"], "route_checks": len(cal["route_checks"]),
        "route_rows": [{k: (r(v) if isinstance(v, float) else v) for k, v in row.items()}
                       for row in cal["route_checks"][-1]["rows"]],
        "tuned": {s: {c: {"params": {k: r(v) for k, v in t["params"].items()}, "tuned_mean": r(t["tuned_mean"])}
                      for c, t in row.items()} for s, row in cal["tuned"].items()}}

    equivalence = {"old_against_new": eq["old_against_new"],
                   "ghost_against_task_n": {k: v for k, v in eq["ghost_against_task_n"].items()
                                            if not isinstance(v, (dict, list))},
                   "cuda_gap": {k: (r(v) if isinstance(v, float) else v) for k, v in eq["cuda_gap"].items()}}

    settings = {}
    for name, row in rd["settings"].items():
        e = ev["settings"][name]
        evals = len(e["per_world_counts"])
        moves = evals * len(ev["worlds"]) * 300
        prey = {"pin_push_total": e["pin_push_total"],
                "wall_limited_share_all_evaluations": r(e["prey_wall_limited_total"] / moves),
                "speed_with_stationary_hunter": {k: r(v) for k, v in e["prey_speed_with_stationary_hunter"].items()},
                "ledger_rel_error_max": e["ledger_rel_error_max"]}
        if row.get("bridge"):
            settings[name] = {"setting": row["setting"], "bridge": True, "prey": prey,
                              "means": {k: r(v) for k, v in row["means"].items()}}
            continue
        pc = row["positive_control"]
        best = max(row["baseline_means"].items(), key=lambda kv: kv[1])
        fams = {}
        for f in FAMILIES:
            hs = {k: v for k, v in row["hunters"].items() if family(k) == f}
            fams[f] = {**spread([h["mean"] for h in hs.values()]),
                       "readings": dict(sorted(Counter(h["reading"] for h in hs.values()).items()))}
        s = {"setting": row["setting"], "solvable": row["solvable"],
             "positive_control": {"mean": r(pc["mean"]), "share_at_least_1": r(pc["share_at_least_1"]),
                                  "reliability_bounds": rl(pc["reliability"]),
                                  "advantage_bounds": rl(pc["advantage_over_best_baseline"])},
             "pursuit_mean": r(row["pursuit_mean"]),
             "best_baseline": {"name": best[0], "mean": r(best[1])},
             "baseline_means": {k: r(v) for k, v in row["baseline_means"].items()},
             "e1_frozen_means": {k: r(v) for k, v in row["e1_frozen_means"].items()},
             "too_easy": {"ratio": r(row["too_easy"]["ratio"]), "bounds": rl(row["too_easy"]["bounds"]),
                          "flag": row["too_easy"]["flag"], "reading": row["too_easy"]["reading"]},
             "families": fams, "prey": prey}
        if "attack_disabled" in row:
            s["attack_disabled"] = row["attack_disabled"]
        settings[name] = s

    falls = {}
    for f in FAMILIES:
        falls[f] = {}
        for sname in SERIES:
            c = Counter(v[sname]["first_not_qualifying"] for k, v in rd["falls_off"].items() if family(k) == f)
            falls[f][sname] = {str(k): n for k, n in sorted(c.items(), key=lambda kv: str(kv[0]))}
    recoveries = {}
    for k, v in rd["falls_off"].items():
        for sname, x in v.items():
            q = list(x["readings"].values())
            if x["first_not_qualifying"] is not None:
                i = list(x["readings"]).index(x["first_not_qualifying"])
                later = [n for n, rr in list(x["readings"].items())[i + 1:] if rr == "qualifies"]
                if later:
                    recoveries.setdefault(k, {})[sname] = later

    return {"stages_commit": commits.pop(), "compute": compute, "equivalence": equivalence,
            "calibration": calibration, "rules": rd["rules"], "bootstrap": rd["bootstrap"], "settings": settings,
            "falls_off": falls, "recoveries_after_falling_off": recoveries,
            "ghost_minus_reach": {"scripted": {k: {"mean": r(v["mean"]), "bounds": rl(v["bounds"])}
                                               for k, v in rd["ghost_minus_reach"].items() if k not in LABELS},
                                  "families": contrast(rd["ghost_minus_reach"])},
            "intact_minus_probe": {k: contrast(v) for k, v in rd["intact_minus_probe"].items()}}


def genomes_table() -> str:
    """Each genome on its own (§6): its mean captures and reading code at every setting."""
    rd = rec(EXP / "reading.json")
    names = [n for n, v in rd["settings"].items() if not v.get("bridge")]
    labels = list(rd["settings"]["H1-bite"]["hunters"])
    head = ["genome", "H1-ghost"] + names
    lines = ["# E5-0: every reused hunter, one by one",
             "",
             "*Generated by `scripts/e5_0_summary.py` from `reading.json`. Each cell is the genome's mean captures per "
             "300-tick episode over the 512 evaluation worlds, then its reading: **Q** qualifies; **U** uncertain; "
             "**F** demonstrated failure of (r) reliability and/or (a) the advantage over the best baseline; **C** fails "
             "cue dependence; **T** capture criteria met, cue dependence untested. H1-ghost is the bridge to Task N: "
             "no rule is read there. Rules: `docs/E5/E5-0-PLAN.md` §6.*",
             "",
             "| " + " | ".join(head) + " |",
             "|" + "---|" * len(head)]
    for lab in labels:
        cells = [lab, f"{rd['settings']['H1-ghost']['means'][lab]:.2f}"]
        for n in names:
            h = rd["settings"][n]["hunters"][lab]
            cells.append(f"{h['mean']:.2f} {code(h['reading'])}")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main():
    out = build()
    (EXP / "summary.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    (EXP / "genomes.md").write_text(genomes_table(), encoding="utf-8")
    print(f"wrote {EXP / 'summary.json'} and genomes.md")


if __name__ == "__main__":
    main()
