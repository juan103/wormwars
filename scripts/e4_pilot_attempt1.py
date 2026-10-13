"""E4's pilot, attempt 1 (stopped at its 3-hour cap in X+'s generation 80; D251-D252): what it recorded, summarised.

    python scripts/e4_pilot_attempt1.py      # writes experiments/E4-two-minds/pilot-attempt1-summary.json

Inputs: the stopped attempt's record (`experiments/E4-two-minds/pilot.json`, committed) and X0's selection matrices
and parents (`runs/e4/pilot/selections-x0.npz`, local; its sha256 is recorded). X+'s training was in memory when the
cap stopped it and was not saved.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars.e4 import lineage as LI  # noqa: E402

REC = ROOT / "experiments" / "E4-two-minds" / "pilot.json"
SEL = ROOT / "runs" / "e4" / "pilot" / "selections-x0.npz"
OUT = ROOT / "experiments" / "E4-two-minds" / "pilot-attempt1-summary.json"
P = 32


def main():
    rec = json.loads(REC.read_text(encoding="utf-8"))
    z = np.load(SEL, allow_pickle=False)
    s = z["score"]  # [generations, runs × P, training mazes]: confirmed visits per wey, per strain and maze
    G = s.shape[0]
    runs = []
    for r in range(s.shape[1] // P):
        m = s[:, P * r:P * (r + 1)].mean(axis=2)  # [G, P] each strain's mean over the generation's mazes
        parents = [{"source": z[f"parents_source_run{r:02d}"][g].tolist(), "child": z[f"parents_child_run{r:02d}"][g].tolist()}
                   for g in range(G - 1)]
        k = int(np.argmax(m[-1]))
        child = z[f"parents_child_run{r:02d}"]  # [G - 1, P]: whether strain j of generation g + 1 is a mutated child
        kids = np.where(child, m[1:], np.nan)
        elites = np.where(~child, m[1:], np.nan)
        runs.append({"run": r, "best_by_generation": np.round(m.max(axis=1), 4).tolist(),
                     "children_mean_generations_1_10": float(np.nanmean(kids[:10])),
                     "children_mean_generations_90_99": float(np.nanmean(kids[-10:])),
                     "elites_mean_generations_1_10": float(np.nanmean(elites[:10])),
                     "elites_mean_generations_90_99": float(np.nanmean(elites[-10:])),
                     "population_mean_generations_1_10": float(m[1:11].mean()),
                     "population_mean_by_generation": np.round(m.mean(axis=1), 4).tolist(),
                     "best_mean_generations_0_9": float(m.max(axis=1)[:10].mean()),
                     "best_mean_generations_90_99": float(m.max(axis=1)[90:].mean()),
                     "population_mean_generations_90_99": float(m[90:].mean()),
                     "final_share_at_least_5": float((m[-1] >= 5).mean()),
                     "final_best_lineage_mutations": LI.mutations(parents, k), "breedings": G - 1})
    per_run_gen = s.mean(axis=2).reshape(G, -1, P).mean(axis=2)  # [G, runs]: each run's population mean
    out = {"inputs": {"record": str(REC.relative_to(ROOT)).replace("\\", "/"),
                      "selections": str(SEL.relative_to(ROOT)).replace("\\", "/"),
                      "selections_sha256": hashlib.sha256(SEL.read_bytes()).hexdigest()},
           "outcome": rec["outcome"], "seconds": rec["seconds"], "generation1_load": rec["generation1_load"],
           "pilot_cross_factor": rec["pilot_cross_factor"], "x_plus_reached": rec.get("training_progress"),
           "generation0_population_mean": float(s[0].mean()), "x0_runs": runs,
           "across_runs": {"population_mean_generations_1_10": float(s[1:11].mean()),
                           "population_mean_generations_90_99": float(s[90:].mean()),
                           "single_run_generation_means_after_0": [float(per_run_gen[1:].min()),
                                                                   float(per_run_gen[1:].max())]},
           "seconds_per_generation_note": "about 56 s per generation (4 runs × 32 strains × 8 mazes, H = 1 800) with "
                                          "the CPU idle; 65 s while CPU tests ran beside it (D251)",
           "note": "exploratory; the best of a generation is on its own 8 training mazes, a noisy measure"}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print({r["run"]: (round(r["best_mean_generations_0_9"], 2), round(r["best_mean_generations_90_99"], 2),
                      round(r["population_mean_generations_90_99"], 2)) for r in runs})


if __name__ == "__main__":
    main()
