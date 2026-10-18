"""03h design (D324): the T1 generation-0 numbers the design quotes, from 03's committed pilot record
(experiments/03-generation0/pilot.json, 16 SH graphs x 256 random genomes x 16 worlds, T1-M0), so each is traceable
(AGENTS.md rule 5). CPU only, no simulation.

The reliability of a genome's mean over W shared worlds is estimated by the crossed decomposition
fitness[g, w] = mu + a_g + b_w + e_gw (genome and world main effects, genome-by-world residual), from the two-way
ANOVA mean squares per graph: var_a = (MS_genome - MS_residual) / W, var_e = MS_residual. Shared worlds make b_w common
to every genome, so it does not affect the ranking; the ranking reliability at W worlds is var_a / (var_a + var_e / W)
(Fable, Astra, round 3).

    python experiments/03h-history-use/development-records/t1_generation0.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "experiments" / "03-generation0" / "pilot.json"
OUT = Path(__file__).with_name("t1-generation0.json")


def decompose(f: np.ndarray) -> dict:
    G, W = f.shape
    gm, wm, mu = f.mean(1), f.mean(0), f.mean()
    ss_g = W * ((gm - mu) ** 2).sum()
    ss_w = G * ((wm - mu) ** 2).sum()
    ss_e = ((f - gm[:, None] - wm[None, :] + mu) ** 2).sum()
    ms_g, ms_w, ms_e = ss_g / (G - 1), ss_w / (W - 1), ss_e / ((G - 1) * (W - 1))
    var_a = max((ms_g - ms_e) / W, 0.0)
    var_b = max((ms_w - ms_e) / G, 0.0)
    rel = {str(w): var_a / (var_a + ms_e / w) if var_a > 0 else 0.0 for w in (8, 16, 32)}
    return {"mean": float(mu), "zero_scores": int((f == 0).sum()), "sd_genome_means": float(gm.std(ddof=1)),
            "var_genome": float(var_a), "var_world": float(var_b), "var_residual": float(ms_e),
            "ranking_reliability": rel}


def main() -> dict:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    rows = {g["name"]: decompose(np.asarray(g["fitness"]["T1-M0"], dtype=np.float64)) for g in d["graphs"]}
    secs = [g["seconds"] for g in d["graphs"]]
    cells = 2 * 256 * 16 + 3 * 64 * 16  # 03's fitness stage: two 256-genome cells and three 64-genome cells
    agg = {k: float(np.mean([r[k] for r in rows.values()])) for k in ("mean", "sd_genome_means", "var_genome",
                                                                       "var_world", "var_residual")}
    agg["mean_range"] = [min(r["mean"] for r in rows.values()), max(r["mean"] for r in rows.values())]
    agg["zero_scores"] = sum(r["zero_scores"] for r in rows.values())
    agg["ranking_reliability"] = {w: float(np.mean([r["ranking_reliability"][w] for r in rows.values()]))
                                  for w in ("8", "16", "32")}
    out = {"source": "experiments/03-generation0/pilot.json, graphs[].fitness['T1-M0'] (256 genomes x 16 worlds)",
           "graphs": len(rows), "per_graph": rows, "pooled": agg,
           "timing": {"fitness_seconds_mean": float(np.mean([s["fitness"] for s in secs])),
                      "calibration_seconds_mean": float(np.mean([s["calibration"] for s in secs])),
                      "history_seconds_mean_2048_genomes": float(np.mean([s["history"] for s in secs])),
                      "fitness_episodes_per_graph": cells,
                      "episodes_per_second": cells / float(np.mean([s["fitness"] for s in secs])),
                      "note": "03's fitness stage mixes five cells (T1-M0 and T1const-M0 at 256 genomes; T1-R1, T1-R2 "
                              "and T0-M0 at 64), all in the 20-wey world; timing.json gives 166.4/s for T1 at "
                              "256 x 16 (Astra)"}}
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    o = main()
    p = o["pooled"]
    print(f"mean {p['mean']:.3f} (range {p['mean_range'][0]:.3f}-{p['mean_range'][1]:.3f}), zeros {p['zero_scores']}, "
          f"sd genome means {p['sd_genome_means']:.3f}, var genome {p['var_genome']:.4f}, world {p['var_world']:.4f}, "
          f"residual {p['var_residual']:.4f}; ranking reliability {p['ranking_reliability']}; "
          f"{o['timing']['episodes_per_second']:.1f} episodes/s")
