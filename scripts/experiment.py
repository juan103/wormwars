"""The N2 / SH / RD comparison.

    python scripts/experiment.py --k 3 --runs 2 --generations 20 --out runs/m5

Design, as specified:
  * K independent SH graphs and K independent RD graphs; N2 has one graph and gets K*R runs, so
    every condition has the same number of runs.
  * Identical initialisation distributions, mutation settings, population sizes and evaluation
    budgets across conditions.
  * The unit of analysis is the run. Confidence intervals come from a hierarchical bootstrap over
    graphs and runs.
  * Reported on held-out world ids that were never used for selection, per evaluation and per
    GPU-hour.
"""

from __future__ import annotations

import argparse
import json
import sys as _sys
import time
from collections import defaultdict
from pathlib import Path as _Path

import numpy as np
import torch

_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from wormwars.analysis import area_under_curve, compare, hierarchical_bootstrap, per_graph_table
from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import degree_summary, make_graphs
from wormwars.evo import SeedPool, evolve, rollout, save_genome
from wormwars.evo.bundle import write_bundle
from wormwars.interface import load_interface

CONDITIONS = ("N2", "SH", "RD")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=3, help="independent SH and RD graphs")
    ap.add_argument("--runs", type=int, default=2, help="runs per graph")
    ap.add_argument("--generations", type=int, default=20)
    ap.add_argument("--population", type=int, default=32)
    ap.add_argument("--worlds", type=int, default=8)
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--holdout", type=int, default=32)
    ap.add_argument("--out", default="runs/m5")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--base-seed", type=int, default=20000)
    ap.add_argument("--conditions", default=",".join(CONDITIONS))
    args = ap.parse_args()

    cfg = Config()
    cfg.world.max_ticks = args.ticks
    cfg.evo.generations = args.generations
    cfg.evo.population = args.population
    cfg.evo.worlds_per_strain = args.worlds
    cfg.evo.holdout_worlds = args.holdout

    con = load_connectome()
    iface = load_interface(con)
    out = _Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    conditions = [c.strip().upper() for c in args.conditions.split(",")]
    graphs: dict[str, list] = {}
    for cond in conditions:
        graphs[cond] = make_graphs(con, cond, args.k)
    # N2 has one graph but must end up with the same number of runs as the others
    runs_per_graph = {c: (args.k * args.runs if c == "N2" else args.runs) for c in conditions}

    graph_meta = {}
    for cond, gl in graphs.items():
        for g in gl:
            d = degree_summary(g)
            graph_meta[g.label] = {
                "condition": cond,
                "chem_edges": d["chem_edges"],
                "gap_edges": d["gap_edges"],
                "chem_weight_sum": d["chem_weight_sum"],
                "self_loops": d["self_loops"],
                "chem_in_degree_sd": float(d["chem_in_degree"].std()),
            }
    write_bundle(out, cfg, con, graphs=graph_meta,
                 extra={"script": "experiment.py", "args": vars(args)})

    total_runs = sum(runs_per_graph[c] * len(graphs[c]) for c in conditions)
    print(con.summary())
    print(
        f"{len(conditions)} conditions, K={args.k}, "
        f"{total_runs} runs of {args.generations} generations x {args.population} strains "
        f"x {args.worlds} worlds x {args.ticks} ticks on {args.device}"
    )

    records = []
    seed_counter = args.base_seed
    t_all = time.perf_counter()
    for cond in conditions:
        for graph in graphs[cond]:
            spec = BrainSpec.from_connectome(graph, device=args.device)
            for r in range(runs_per_graph[cond]):
                seed_counter += 1
                t0 = time.perf_counter()
                res = evolve(
                    cfg, iface, spec, run=r, run_seed=seed_counter, device=args.device,
                    out_dir=out, holdout_every=max(1, args.generations // 5), verbose=False,
                )
                pool = SeedPool(cfg, seed_counter)
                held = rollout(cfg, iface, res.champion, pool.holdout, seed_counter, args.device)
                hist = res.history()
                rec = {
                    "condition": cond,
                    "graph": graph.label,
                    "run": r,
                    "run_seed": seed_counter,
                    "holdout": float(held.per_strain()[0]),
                    "holdout_alive": float(held.alive.mean()),
                    "train_best_final": float(hist["best"][-1]),
                    "auc": area_under_curve(hist["best"]),
                    "evaluations": res.evaluations,
                    "seconds": time.perf_counter() - t0,
                }
                records.append(rec)
                save_genome(
                    out / f"champion-{graph.label}-run{r:02d}.npz", res.champion, 0,
                    strain_id=res.champion_id, run_seed=seed_counter,
                    holdout_score=rec["holdout"],
                )
                print(
                    f"  {cond:<3} {graph.label:<5} run{r} holdout {rec['holdout']:6.3f}  "
                    f"auc {rec['auc']:6.3f}  {rec['seconds']:5.0f}s"
                )

    (out / "records.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    report(records, out, time.perf_counter() - t_all)


def report(records, out: _Path, wall: float) -> None:
    by_cond: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    auc_cond: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    per_hour: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        by_cond[r["condition"]][r["graph"]].append(r["holdout"])
        auc_cond[r["condition"]][r["graph"]].append(r["auc"])
        per_hour[r["condition"]][r["graph"]].append(r["holdout"] / (r["seconds"] / 3600))

    lines = ["# N2 / SH / RD comparison", ""]
    lines.append(f"Total wall time {wall / 3600:.3f} h over {len(records)} runs.")
    lines.append("")
    lines.append("Scores are held-out foraging score (surviving swarm energy / starting energy),")
    lines.append("on world ids never used for selection. The unit of analysis is the run.")
    lines.append("")

    for title, data in (
        ("Final held-out score", by_cond),
        ("Area under the fitness curve (speed of improvement)", auc_cond),
        ("Held-out score per GPU-hour", per_hour),
    ):
        lines += [f"## {title}", "", "```"]
        for cond in ("N2", "SH", "RD"):
            if cond not in data:
                continue
            b = hierarchical_bootstrap(dict(data[cond]), n_boot=20000)
            lines.append(f"{cond:<4} {b}")
        lines.append("```")
        lines.append("")
        lines.append("Per graph:")
        lines.append("")
        lines.append("```")
        for cond in ("N2", "SH", "RD"):
            if cond in data:
                lines.append(per_graph_table(dict(data[cond])))
        lines.append("```")
        lines.append("")
        lines.append("Contrasts (bootstrap of the difference, 95% interval):")
        lines.append("")
        lines.append("```")
        for a, b in (("N2", "SH"), ("N2", "RD"), ("SH", "RD")):
            if a in data and b in data:
                c = compare(dict(data[a]), dict(data[b]), a, b, n_boot=20000)
                lines.append(f"{c}   -> {c.verdict()}")
        lines.append("```")
        lines.append("")

    lines += [
        "## Reading this",
        "",
        "N2 has one graph, so its interval carries run-to-run variation only. SH and RD have K",
        "graphs each, so their intervals also carry graph-to-graph variation and are wider by",
        "construction. The question is whether N2 sits outside the SH/RD distribution over graphs,",
        "not whether two equally-estimated means differ.",
        "",
        "This measures wiring **plus this specific sensor/motor interface** on **this game**. It is",
        "not a test of whether biological wiring is better in general.",
    ]
    text = "\n".join(lines)
    (out / "REPORT.md").write_text(text, encoding="utf-8")
    print("\n" + text)


if __name__ == "__main__":
    main()
