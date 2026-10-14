"""The evolutionary E4-D's formal summary: every number the results cite, derived from the committed records in
`experiments/E4-two-minds/E4-D-evo/formal/` (rule 5). CPU, no GPU; the connectome is loaded only to name the 32
cross-link slots.

    python scripts/e4d_evo_summary.py        # writes experiments/E4-two-minds/E4-D-evo/summary.json

Registered readings (§7.1, §7.2) are copied from the report records, not recomputed. Everything else is descriptive
(§7.3, §7.4). The slot contrasts ("copy" and "nose") were chosen after seeing L's data and are labelled so.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.e3 import organism as O  # noqa: E402

EXP = ROOT / "experiments" / "E4-two-minds" / "E4-D-evo"
FORMAL = EXP / "formal"
OUT = EXP / "summary.json"
CONDITIONS = ("intact", "reversed", "removed", "fixed", "cut", "eg")
HAND_BUILT = {("E3_A_CL", "E3_B_CL"): 3.0, ("E3_A_CR", "E3_B_CR"): 3.0}  # the check's control (w = 3)


def load(name: str):
    p = FORMAL / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def spread(x) -> dict:
    a = np.asarray(x, dtype=np.float64)
    return {"n": int(a.size), "mean": float(a.mean()), "sd": float(a.std(ddof=1)) if a.size > 1 else None,
            "min": float(a.min()), "median": float(np.median(a)), "max": float(a.max())}


def slot_names() -> list:
    from wormwars.connectome import load_connectome
    from wormwars.e4 import arms as AR
    from wormwars.e4s import arms as A
    from wormwars.config import BrainConfig

    cx = AR.context(load_connectome(), A.load_l1(), BrainConfig())
    return [list(p) for p in O.cross_links(cx["org"].module)]


def wiring(runs: list, names: list) -> dict:
    """§7.4: each slot's weight across the champions, by class; and two contrasts chosen after seeing L's data."""
    W = np.asarray([r["slot_weights"] for r in runs], dtype=np.float64)  # [champions, 32]
    idx = {tuple(n): k for k, n in enumerate(names)}

    def cls(pre, post):
        into = "into_B" if post.startswith("E3_B_") else "into_A"
        origin = "comparator" if pre in O.COMPARATORS else "nose"
        return f"{into}.{origin}"

    classes = {}
    for k, (pre, post) in enumerate(names):
        classes.setdefault(cls(pre, post), []).append(k)
    by_class = {c: {"slots": len(ks), "mean_abs_weight": spread(np.abs(W[:, ks]).mean(axis=1)),
                    "sum_abs_weight": spread(np.abs(W[:, ks]).sum(axis=1))} for c, ks in sorted(classes.items())}

    def w(pre, post):
        return W[:, idx[(pre, post)]]

    copy = (w("E3_A_CL", "E3_B_CL") + w("E3_A_CR", "E3_B_CR") - w("E3_A_CL", "E3_B_CR") - w("E3_A_CR", "E3_B_CL")) / 2
    nose = (w("E3_A_NL", "E3_B_CL") + w("E3_A_NR", "E3_B_CR") - w("E3_A_NL", "E3_B_CR") - w("E3_A_NR", "E3_B_CL")) / 2
    to_nose = (w("E3_A_CL", "E3_B_NL") + w("E3_A_CR", "E3_B_NR") - w("E3_A_CL", "E3_B_NR") - w("E3_A_CR", "E3_B_NL")) / 2
    nose_nose = (w("E3_A_NL", "E3_B_NL") + w("E3_A_NR", "E3_B_NR") - w("E3_A_NL", "E3_B_NR") - w("E3_A_NR", "E3_B_NL")) / 2
    per_slot = [{"pre": pre, "post": post, "class": cls(pre, post), "weights": spread(W[:, k]),
                 "positive": int((W[:, k] > 0).sum()), "hand_built": HAND_BUILT.get((pre, post), 0.0)}
                for k, (pre, post) in enumerate(names)]

    def contrast(definition, x):
        return {"definition": definition, "values": spread(x), "positive": int((x > 0).sum())}

    return {"by_class": by_class, "per_slot": per_slot,
            "contrasts_after_data": {
                "label": "exploratory: chosen after seeing L's data",
                "comparator_to_comparator": contrast(
                    "(A_CL→B_CL + A_CR→B_CR − A_CL→B_CR − A_CR→B_CL) / 2; the hand-built control's 3.0", copy),
                "nose_to_comparator": contrast(
                    "(A_NL→B_CL + A_NR→B_CR − A_NL→B_CR − A_NR→B_CL) / 2; the hand-built control's 0", nose),
                "comparator_to_nose": contrast(
                    "(A_CL→B_NL + A_CR→B_NR − A_CL→B_NR − A_CR→B_NL) / 2; the hand-built control's 0", to_nose),
                "nose_to_nose": contrast(
                    "(A_NL→B_NL + A_NR→B_NR − A_NL→B_NR − A_NR→B_NL) / 2; the hand-built control's 0", nose_nose)}}


def controls(runs: list) -> dict:
    """§7.3: per condition, the champions' shares of real-first, decoy-first and neither, and entry."""
    out = {}
    for c in CONDITIONS:
        t = [r["test"][c] for r in runs]
        n = np.asarray([x["trials"] for x in t], dtype=np.float64)
        out[c] = {k: spread(np.asarray([x[k] for x in t]) / n) for k in ("real_first", "decoy_first", "neither")}
        out[c]["decoy_first_exceeds_real_first"] = int(sum(x["decoy_first"] > x["real_first"] for x in t))
        balanced = [np.array_equal(np.asarray(x["per_maze"]["real_first"]).sum(1),
                                   np.asarray(x["per_maze"]["decoy_first"]).sum(1)) for x in t]
        out[c]["balanced_per_maze"] = int(sum(balanced))
    intact = np.asarray([r["test"]["intact"]["real_first"] for r in runs], dtype=np.float64)
    for c in ("removed", "fixed"):
        rf = np.asarray([r["test"][c]["real_first"] for r in runs], dtype=np.float64)
        out[c]["real_first_over_intact"] = spread(rf / intact)
    return out


def checkpoints(train: dict) -> dict:
    """§7.4: the checkpoint block's real-first share (8 mazes, 16 trials; noisy) by generation, across runs."""
    by_gen = {}
    for recs in train["checkpoints"].values():
        for c in recs:
            by_gen.setdefault(int(c["generation"]), []).append(c["validation_mean"])
    return {str(g): spread(v) for g, v in sorted(by_gen.items())}


def arm(key: str, names: list) -> dict | None:
    report, evaluate, train = load(f"report-{key}.json"), load(f"evaluate-{key}.json"), load(f"train-{key}.json")
    if report is None or evaluate is None or train is None:
        return None
    runs = evaluate["runs"]
    champ = np.asarray([r["test"]["intact"]["real_first_all"] for r in runs])
    val = np.asarray([max(r["validation_shares"]) for r in runs])
    return {"reading": report["reading"], "label": report["label"], "outcome": report["outcome"],
            "runs": [{"run": r["run"], "seed": r["seed"], "champion_index": r["champion_index"],
                      "test_real_first": r["test"]["intact"]["real_first"],
                      "test_decoy_first": r["test"]["intact"]["decoy_first"],
                      "test_neither": r["test"]["intact"]["neither"], "gain": g, "minus_eg": m,
                      "champion_validation_share": float(max(r["validation_shares"])),
                      "lineage_mutations": r["lineage_mutations"]}
                     for r, g, m in zip(runs, report["gains"], report["minus_eg"])],
            "champion_test_share": spread(champ), "champion_validation_share": spread(val),
            "validation_minus_test": spread(val - champ),
            "gain": spread(report["gains"]), "minus_eg": spread(report["minus_eg"]),
            "controls": controls(runs), "wiring": wiring(runs, names), "checkpoints": checkpoints(train),
            "tie_share": spread([np.mean(r["tie_shares"]) for r in runs]),
            "turnover": spread([np.mean(r["turnover"]) for r in runs]),
            "lineage_mutations": spread([r["lineage_mutations"] for r in runs]),
            "training_seconds": train["training_seconds"], "evaluate_seconds": evaluate["seconds"]}


def compute() -> dict:
    out = {}
    for key in ("l", "f", "s"):
        rec = load(f"compute-record-{key}.json")
        if rec is not None:
            out[key] = {k: v for k, v in rec.items() if k != "attempts"}
            out[key]["attempts"] = [{k: a[k] for k in ("argv", "status", "git_commit")} for a in rec["attempts"]]
    return out


def main() -> None:
    check = load("check.json")
    names = slot_names()
    doc = {"source": "experiments/E4-two-minds/E4-D-evo/formal/ (the committed records); scripts/e4d_evo_summary.py",
           "check": {k: check[k] for k in check if k in ("outcome", "positive_control", "evaluation_path", "timing", "replay")},
           "L": arm("l", names), "F": arm("f", names), "S": arm("s", names), "compute": compute()}
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
