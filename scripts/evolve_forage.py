"""Evolve foragers and measure them against random-weight weys on held-out seeds.

    python scripts/evolve_forage.py --runs 3 --generations 25 --out runs/m4

Held-out world ids are never used for selection, so the comparison is not a training score.
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

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo import SeedPool, evolve, rollout, save_genome
from wormwars.evo.bundle import write_bundle
from wormwars.interface import load_interface


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--generations", type=int, default=25)
    ap.add_argument("--population", type=int, default=32)
    ap.add_argument("--worlds", type=int, default=6, help="evaluation worlds per strain")
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--holdout", type=int, default=32)
    ap.add_argument("--islands", type=int, default=1)
    ap.add_argument("--out", default="runs/m4")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--base-seed", type=int, default=1000)
    ap.add_argument(
        "--stage", type=int, default=0, choices=(0, 2),
        help="0: eating is automatic. 2: eating demand is gated on pump intensity and pumping costs "
             "energy, so a forager must learn to open its mouth as well as find food.",
    )
    args = ap.parse_args()

    cfg = Config()
    cfg.world.max_ticks = args.ticks
    cfg.evo.generations = args.generations
    cfg.evo.population = args.population
    cfg.evo.worlds_per_strain = args.worlds
    cfg.evo.holdout_worlds = args.holdout
    cfg.evo.islands = args.islands

    con = load_connectome()
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con, device=args.device)
    out = _Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_bundle(out, cfg, con, extra={"script": "evolve_forage.py", "args": vars(args)})

    print(con.summary())
    print(
        f"stage {args.stage}, population {cfg.evo.population}, {cfg.evo.generations} generations, "
        f"{cfg.evo.worlds_per_strain} worlds/strain, {cfg.world.max_ticks} ticks, "
        f"device {args.device}"
    )

    rows = []
    for run in range(args.runs):
        run_seed = args.base_seed + run
        t0 = time.perf_counter()
        res = evolve(cfg, iface, spec, run=run, run_seed=run_seed, device=args.device,
                     combat_stage=args.stage, out_dir=out,
                     holdout_every=max(1, args.generations // 6))
        pool = SeedPool(cfg, run_seed)

        # --- the comparison: champion vs random-weight weys, same held-out worlds ---
        gen_r = torch.Generator(device=args.device).manual_seed(run_seed + 777)
        baseline = Genome.random(
            spec, cfg.brain, cfg.evo.population, generator=gen_r, device=args.device
        )
        champ = rollout(cfg, iface, res.champion, pool.holdout, run_seed, args.device,
                        combat_stage=args.stage)
        base = rollout(cfg, iface, baseline, pool.holdout, run_seed, args.device,
                       combat_stage=args.stage)
        base_per_strain = base.per_strain()

        row = {
            "run": run,
            "run_seed": run_seed,
            "champion_holdout": float(champ.per_strain()[0]),
            "random_holdout_mean": float(base_per_strain.mean()),
            "random_holdout_best_of_pop": float(base_per_strain.max()),
            "random_holdout_std": float(base_per_strain.std()),
            "champion_alive": float(champ.alive.mean()),
            "random_alive": float(base.alive.mean()),
            "champion_eaten": float(champ.eaten.mean()),
            "random_eaten": float(base.eaten.mean()),
            "wall_seconds": time.perf_counter() - t0,
            "evaluations": res.evaluations,
            "champion_id": res.champion_id,
            "nickname": res.log[-1].best_nickname,
        }
        rows.append(row)
        save_genome(
            out / f"champion-run{run:02d}.npz", res.champion, 0,
            strain_id=res.champion_id, run_seed=run_seed,
            holdout_score=row["champion_holdout"],
        )
        print(
            f"  run {run}: champion {row['champion_holdout']:.3f} vs random "
            f"{row['random_holdout_mean']:.3f} (best of {cfg.evo.population}: "
            f"{row['random_holdout_best_of_pop']:.3f})  {row['wall_seconds']:.0f}s"
        )

    (out / "summary.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    champ = np.array([r["champion_holdout"] for r in rows])
    rand = np.array([r["random_holdout_mean"] for r in rows])
    rand_best = np.array([r["random_holdout_best_of_pop"] for r in rows])
    print("\n=== held-out seeds, never used for selection ===")
    print(f"{'run':>4} {'champion':>10} {'random mean':>12} {'random best':>12} {'ratio':>8}")
    for r in rows:
        print(
            f"{r['run']:>4} {r['champion_holdout']:>10.3f} {r['random_holdout_mean']:>12.3f} "
            f"{r['random_holdout_best_of_pop']:>12.3f} "
            f"{r['champion_holdout'] / max(r['random_holdout_mean'], 1e-9):>8.2f}x"
        )
    print(
        f"\nchampion {champ.mean():.3f} +- {champ.std():.3f}  |  "
        f"random {rand.mean():.3f} +- {rand.std():.3f}  |  "
        f"best-of-population random {rand_best.mean():.3f}"
    )
    print(f"every run improved on the best random strain: {bool((champ > rand_best).all())}")
    print(f"total GPU-hours: {sum(r['wall_seconds'] for r in rows) / 3600:.3f}")


if __name__ == "__main__":
    main()
