"""Two-swarm coevolution.

    python scripts/coevolve.py --runs 2 --generations 20 --stage 1 --out runs/m7

Absolute progress is the score against the versioned frozen opponent suite on held-out world ids;
the within-generation score is relative and will drift on its own as opponents improve.
"""

from __future__ import annotations

import argparse
import json
import sys as _sys
import time
from pathlib import Path as _Path

import numpy as np
import torch

_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from wormwars.brain import BrainSpec
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import make_graphs
from wormwars.evo.bundle import write_bundle
from wormwars.evo.coevolve import coevolve
from wormwars.interface import load_interface


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--generations", type=int, default=20)
    ap.add_argument("--population", type=int, default=16)
    ap.add_argument("--size", type=int, default=40, help="weys per swarm")
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--worlds", type=int, default=2, help="map seeds per generation")
    ap.add_argument("--stage", type=int, default=1, choices=(1, 2))
    ap.add_argument("--lopsided", action="store_true")
    ap.add_argument(
        "--vary-sizes", action="store_true",
        help="draw headcounts per generation from --size-range instead of using --size, including "
             "lopsided matchups (each played with the headcounts swapped as well)",
    )
    ap.add_argument("--size-range", type=int, nargs=2, default=(50, 200))
    ap.add_argument("--size-pairs", type=int, default=2)
    ap.add_argument("--graph", default="N2")
    ap.add_argument("--out", default="runs/m7")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--base-seed", type=int, default=30000)
    args = ap.parse_args()

    cfg = Config()
    cfg.world.n_swarms = 2
    cfg.world.max_ticks = args.ticks
    cfg.evo.generations = args.generations
    cfg.evo.population = args.population
    cfg.evo.coevo_worlds = args.worlds
    cfg.evo.coevo_sizes = (args.size, args.size)
    cfg.evo.coevo_lopsided = args.lopsided
    cfg.evo.coevo_vary_sizes = args.vary_sizes
    cfg.evo.coevo_size_range = tuple(args.size_range)
    cfg.evo.coevo_size_pairs = args.size_pairs

    con = load_connectome()
    iface = load_interface(con)
    graph = make_graphs(con, args.graph, 1)[0] if args.graph != "N2" else con
    spec = BrainSpec.from_connectome(graph, device=args.device)
    out = _Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_bundle(out, cfg, con, extra={"script": "coevolve.py", "args": vars(args)})

    print(con.summary())
    print(
        f"coevolution stage {args.stage}: {args.runs} runs x {args.generations} generations, "
        f"population {args.population}, "
        + (f"sizes {args.size_range[0]}-{args.size_range[1]} ({args.size_pairs} pairs/generation, "
           f"lopsided included), " if args.vary_sizes else f"{args.size}v{args.size}, ")
        + f"{args.ticks} ticks, "
        f"{args.worlds} map seeds/generation on {args.device}"
    )

    rows = []
    for run in range(args.runs):
        seed = args.base_seed + run
        t0 = time.perf_counter()
        pop, hof, log, suite_meta = coevolve(
            cfg, iface, spec, run=run, run_seed=seed, device=args.device,
            combat_stage=args.stage, out_dir=out,
        )
        suite_points = [(x.generation, x.suite_best) for x in log if x.suite_best is not None]
        rows.append({
            "run": run,
            "run_seed": seed,
            "suite_first": suite_points[0][1],
            "suite_last": suite_points[-1][1],
            "suite_curve": suite_points,
            "flank_share_first": log[0].flank_share,
            "flank_share_last": log[-1].flank_share,
            "hall_of_fame": [n for _, _, n in hof.entries],
            "suite_version": suite_meta["suite_version"],
            "seconds": time.perf_counter() - t0,
        })
        print(
            f"  run {run}: frozen suite {rows[-1]['suite_first']:+.3f} -> "
            f"{rows[-1]['suite_last']:+.3f}   flank share "
            f"{rows[-1]['flank_share_first']:.2f} -> {rows[-1]['flank_share_last']:.2f}   "
            f"{rows[-1]['seconds']:.0f}s"
        )

    (out / "summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    first = np.array([r["suite_first"] for r in rows])
    last = np.array([r["suite_last"] for r in rows])
    print("\n=== frozen opponent suite, held-out seeds ===")
    print(f"start  {first.mean():+.3f} +- {first.std():.3f}")
    print(f"end    {last.mean():+.3f} +- {last.std():.3f}")
    print(f"gain   {(last - first).mean():+.3f}  (improved in {int((last > first).sum())}/{len(rows)} runs)")
    fs = np.array([r["flank_share_last"] for r in rows])
    print(f"share of damage landed on mid/tail rather than head, final generation: {fs.mean():.3f}")
    print(f"total GPU-hours: {sum(r['seconds'] for r in rows) / 3600:.3f}")


if __name__ == "__main__":
    main()
