"""03a's exploratory summary (experiments/03a-self-consistency/RESULTS.md): the numbers the results page quotes, read
from pilot-dev's committed records, so each one is traceable to a file and a field (AGENTS.md rule 5).

    python scripts/e03a_summary.py        # writes experiments/03a-self-consistency/summary.json

No simulation; CPU only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "03a-self-consistency"
PD = EXP / "pilot-dev"
STAGES = ["setup", "evolve-intact", "panel", "evolve-nip", "baseline", "probe", "tune", "full", "report",
          "search-check"]


def rec(stage: str) -> dict:
    return json.loads((PD / f"{stage}.json").read_text(encoding="utf-8"))


def r(x, n=4):
    return None if x is None else round(float(x), n)


def cmp_(c: dict) -> dict:
    return {"difference": r(c["difference"]), "interval": [r(c["lo"]), r(c["hi"])], "verdict": c["verdict"]}


def build() -> dict:
    """The summary, from the committed records."""
    docs = {s: rec(s) for s in STAGES}
    for s, d in docs.items():
        if d["status"] != "completed" or d["smoke"]:
            raise SystemExit(f"{s} is not a completed full-size record")
    comp = json.loads((PD / "compute.json").read_text(encoding="utf-8"))
    pre = json.loads((PD / "preflight-compute.json").read_text(encoding="utf-8"))  # the CUDA preflight's aggregate
    out = {"source": "experiments/03a-self-consistency/pilot-dev/*.json, read by scripts/e03a_summary.py"}

    out["stages"] = {s: {"commit": d["provenance"]["git_commit"][:7], "hours_wall": r(d["seconds"] / 3600, 5)}
                     for s, d in docs.items()}
    rep = docs["report"]
    pre_h = pre["totals"]["seconds_timed"] / 3600
    out["compute"] = {"pilot_dev_hours_measured": r(comp["totals"]["seconds_timed"] / 3600, 4),
                      "cuda_preflight_hours": r(pre_h, 4),
                      "pilot_dev_hours_with_preflight": r(comp["totals"]["seconds_timed"] / 3600 + pre_h, 4),
                      "exploratory_checks_hours": docs["setup"]["dev"]["charged_before_hours"],
                      "pilot_dev_cap": docs["setup"]["dev"]["cap_gpu_hours"],
                      "experiment_cap": docs["setup"]["dev"]["experiment_cap_gpu_hours"],
                      "rates_per_second": {k: r(v["per_second"], 1) for k, v in rep["rates"].items()},
                      "note": "pilot_dev_hours_measured includes the bounded check; the CUDA preflight's hours are "
                              "from pilot-dev/preflight-compute.json, a copy of runs/e03a-smoke-cuda's aggregate"}

    ev = {}
    for stage in ("evolve-intact", "evolve-nip"):
        for run in docs[stage]["runs"]:
            name = ({"0": "selector", "1": "MIP"}.get(str(run["spec"]["run"]))
                    or f"NIP/{run.get('target', {}).get('name')}")
            ev[name] = {"generation0_validation": r(run["generation0_baseline"]["validation_mean"]),
                        "champion_validation": r(run["champion"]["validation_mean"]),
                        "champion_generation": run["champion"]["generation"],
                        **({"pinned": run["pinned"]} if "pinned" in run else {})}
    out["evolution"] = ev

    pan = docs["panel"]
    rel = np.asarray(pan["relevance"]["mean"])
    ceiling = float(pan["selector_intact_mean"])
    out["panel"] = {"selector_intact_mean": r(ceiling), "eligible_representatives": len(rel),
                    "deletions_that_zero_the_selector": int(np.sum(np.isclose(rel, ceiling))),
                    "tiers": pan["tier_names"], "targets": pan["target_names"], "flags": pan["flags"]}

    base = docs["baseline"]
    out["baseline"] = {"mip_intact_mean": r(base["mip_intact_mean"]), "p": r(base["p"]),
                       "target_brains": [{k: tb.get(k) for k in ("label", "deletion_deficit", "restoration_exact",
                                                                  "own_equals_deleted", "degree", "counts")}
                                         for tb in base["target_brains"]]}

    pr = docs["probe"]
    mean = lambda v: r(np.mean(v), 4)  # noqa: E731
    out["probe"] = {
        "worlds": pr["worlds"],
        "evolved": {k: {kk: mean(vv) for kk, vv in v.items() if kk.startswith("L=") or kk == "plain"}
                    | {"full_replay_equals_plain": v["full_replay_equals_plain"]} for k, v in pr["evolved"].items()},
        "scripted": {k: {kk: mean(vv) for kk, vv in v.items() if kk.startswith("L=") or kk == "plain"}
                     | ({"unaffected": v["unaffected"]} if "unaffected" in v else {}) for k, v in pr["scripted"].items()}}

    tn = docs["tune"]
    out["tune"] = {"chosen": tn["chosen"],
                   "rounds": [{"round": x["round"], "flag": x["flag"], "chosen": x["chosen"],
                               "mean_final": [r(v["mean_final"]) for v in x["results"].values()],
                               "swap_rate": [r(v["swap_rate"], 3) for v in x["results"].values()]}
                              for x in tn["rounds"]]}

    fu = docs["full"]
    rows = []
    for tb in fu["target_brains"]:
        c = tb["comparisons"]
        frees = [ps for ps in tb["per_search"] if ps["label"].startswith("free")]
        rows.append({"label": tb["label"], "deletion_deficit": r(tb["deletion_deficit"]),
                     **{k: cmp_(v) for k, v in c.items()},
                     "refit_means": [r(x) for x in tb["refit_means"]], "refit_sd": r(tb["refit_sd"]),
                     "enrichment_p": r(tb["enrichment"]["p"]), "no_task_p": r(tb["no_task"]["p"]),
                     "chance_q": r(tb["chance_q"]), "attributes": tb["attributes"],
                     "free_auc": [r(ps["auc"], 3) for ps in frees],
                     "free_q_range": [r(min(min(ps["q_every_10_from_0"]) for ps in frees), 3),
                                      r(max(max(ps["q_every_10_from_0"]) for ps in frees), 3)],
                     "free_paired_diff_mean": [r(ps["paired_diff_mean"], 3) for ps in frees],
                     "longer": tb["longer"]})
    out["full"] = {"setting": fu["setting"], "p": r(fu["p"]), "delta_eval": r(fu["delta_eval"]),
                   "delta_search": r(fu["delta_search"]),
                   "delta_search_fraction_of_p": r(fu["delta_search_fraction_of_p"], 3), "target_brains": rows}
    out["report"] = {"plan_total_hours": r(rep["plan"]["total"], 2),
                     "plan_pilot_check_hours": r(rep["plan"]["hours"]["pilot-check"], 2),
                     "remaining_hours_then": r(rep["remaining_hours"], 2)}

    sc = docs["search-check"]
    les = sc["lesion"]
    out["search_check"] = {
        "rule": sc["rule"], "p": r(sc["p"]),
        "lesion": {k: les[k] for k in ("restored_mean", "n_edges", "n_drop_above_p", "n_drop_lower_bound_above_0",
                                       "sum_drops", "share_of_positive_in_top")}
        | {"largest_drops": [{"type": e["type"], "drop": r(e["drop"], 3)} for e in les["edges"][:5]],
           "edges_above_p_by_type": {t: sum(e["type"] == t and e["drop"] > sc["p"] for e in les["edges"])
                                     for t in ("in", "out", "gap")},
           "edges_by_type": {t: sum(e["type"] == t for e in les["edges"]) for t in ("in", "out", "gap")}},
        "reeval": {st: {"oracle_best_reference_gain": r(v["oracle_best_reference_gain"]),
                        "mean_reference_gain_of_offspring": r(v["mean_reference_gain_of_offspring"]),
                        "by_worlds": {w: {k: r(b[k], 3) for k in ("mean_reference_gain_of_winner",
                                                                  "se_of_that_mean_over_sets", "share_accepted_greedy",
                                                                  "share_of_accepted_that_are_worse",
                                                                  "spearman_selection_reference_mean")}
                                      for w, b in v["by_worlds"].items()}} for st, v in sc["reeval"].items()},
        "variants": [{"name": v["name"], "from": v["from"], "reliable": v["reliable"], "recovers": v["recovers"],
                      "restoration_over_refits": cmp_(v["restoration_over_refits"]),
                      "refit_sd": r(v["refit_sd"]), "refit_sd_95": [r(x) for x in v["refit_sd_95"]],
                      "advantage": cmp_(v["advantage"]), "functional": cmp_(v["functional"]),
                      "enrichment_p": r(v["enrichment"]["p"]),
                      "per_type_p": {t: r(x["p"]) for t, x in v["enrichment_per_type"].items()},
                      "per_type_null_sd": {t: r(x["null_sd"]) for t, x in v["enrichment_per_type"].items()},
                      "no_task_p": r(v["no_task"]["p"]),
                      "free_accepted_share": [r(ps["accepted_share_mean"], 2) for ps in v["per_search"]
                                              if ps["label"].startswith("free")],
                      "free_auc": [r(ps["auc"], 3) for ps in v["per_search"] if ps["label"].startswith("free")]}
                     for v in sc["variants"]]}
    return out


def main() -> dict:
    out = build()
    (EXP / "summary.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    main()
    print(f"wrote {EXP / 'summary.json'}")
    sys.exit(0)
