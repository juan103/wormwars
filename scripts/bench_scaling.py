"""Scaling benchmark: wey-ticks per second and peak VRAM against worlds and swarm size.

    python scripts/bench_scaling.py --out runs/scaling.md

"Thousands of worlds" is a target to be measured, not assumed. This script measures it, and also
checks that chunking a rollout leaves the scores bit-identical, which is what makes chunking a
memory strategy rather than an approximation.
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

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo import rollout
from wormwars.interface import load_interface
from wormwars.world import World, arena_side


def measure(cfg, iface, spec, n_worlds, n_swarms, size, ticks, device, stage):
    cfg.world.n_swarms = n_swarms
    cfg.world.weys_per_swarm = size
    n_strains = min(8, n_worlds)
    gen = torch.Generator(device=device).manual_seed(0)
    genome = Genome.random(spec, cfg.brain, n_strains, generator=gen, device=device)
    brain = Brain(genome)
    strain_of = (
        torch.arange(n_strains, device=device)
        .repeat_interleave(n_worlds * n_swarms // n_strains)
        .reshape(n_worlds, n_swarms)
    )
    if device == "cuda":
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
    world = World(cfg, iface, brain, strain_of, run_seed=1, device=device, combat_stage=stage)
    for _ in range(3):
        world.tick()
    if device == "cuda":
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(ticks):
        world.tick()
    if device == "cuda":
        torch.cuda.synchronize()
    dt = (time.perf_counter() - t0) / ticks
    weys = n_worlds * n_swarms * size
    vram = torch.cuda.max_memory_allocated() / 2**20 if device == "cuda" else 0.0
    side = world.side
    del world, brain, genome
    return {
        "worlds": n_worlds,
        "swarms": n_swarms,
        "size": size,
        "weys": weys,
        "arena": side,
        "ms_per_tick": dt * 1e3,
        "wey_ticks_per_s": weys / dt,
        "peak_vram_mb": vram,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=60)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--out", default="runs/scaling.md")
    ap.add_argument("--stage", type=int, default=1)
    ap.add_argument("--showcase", action="store_true", help="also try one huge world")
    args = ap.parse_args()

    con = load_connectome()
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con, device=args.device)

    rows = []
    print(f"{'worlds':>7} {'swarms':>7} {'size':>6} {'weys':>9} {'arena':>6} "
          f"{'ms/tick':>9} {'wey-ticks/s':>14} {'VRAM MB':>9}")

    # sweep worlds at the development size, then swarm size at fixed worlds
    for n_worlds in (8, 32, 128, 512, 2048):
        try:
            r = measure(Config(), iface, spec, n_worlds, 1, 20, args.ticks, args.device, 0)
        except torch.cuda.OutOfMemoryError:
            print(f"{n_worlds:>7}  out of memory")
            break
        rows.append(r)
        _print(r)

    for size in (20, 50, 100, 200):
        for n_worlds in (16, 64):
            try:
                r = measure(Config(), iface, spec, n_worlds, 2, size, args.ticks, args.device,
                            args.stage)
            except torch.cuda.OutOfMemoryError:
                print(f"{n_worlds:>7} {2:>7} {size:>6}  out of memory")
                continue
            rows.append(r)
            _print(r)

    if args.showcase:
        # Showcase mode: one big world, for spectacle and as a generalisation test. Never used for
        # selection.
        for size in (500, 1000, 2000):
            try:
                r = measure(Config(), iface, spec, 1, 2, size, max(args.ticks // 3, 10),
                            args.device, args.stage)
            except torch.cuda.OutOfMemoryError:
                print(f"showcase {size}v{size}: out of memory")
                break
            r["showcase"] = True
            rows.append(r)
            _print(r)

    # chunking must not change a single score
    cfg = Config()
    cfg.world.max_ticks = 120
    gen = torch.Generator(device=args.device).manual_seed(0)
    genome = Genome.random(spec, cfg.brain, 8, generator=gen, device=args.device)
    ids = np.arange(200, 208)
    a = rollout(cfg, iface, genome, ids, run_seed=5, device=args.device, chunk_worlds=1024)
    b = rollout(cfg, iface, genome, ids, run_seed=5, device=args.device, chunk_worlds=8)
    diff = float(np.abs(a.score - b.score).max())
    print(f"\nchunked rollout agreement: max |score difference| = {diff:.3e} "
          f"({'identical' if diff == 0 else 'NOT identical'})")

    out = _Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Scaling", "", f"Device: {args.device}", ""]
    if args.device == "cuda":
        p = torch.cuda.get_device_properties(0)
        lines.append(f"GPU: {p.name}, {p.total_memory / 2**30:.1f} GiB, "
                     f"sm_{torch.cuda.get_device_capability(0)[0]}"
                     f"{torch.cuda.get_device_capability(0)[1]}")
        lines.append("")
    lines += [
        "| worlds | swarms | weys/swarm | total weys | arena | ms/tick | wey-ticks/s | peak VRAM MB |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        tag = " (showcase)" if r.get("showcase") else ""
        lines.append(
            f"| {r['worlds']}{tag} | {r['swarms']} | {r['size']} | {r['weys']:,} | "
            f"{r['arena']} | {r['ms_per_tick']:.2f} | {r['wey_ticks_per_s']:,.0f} | "
            f"{r['peak_vram_mb']:.0f} |"
        )
    lines += ["", f"Chunked rollout agreement: max |score difference| = {diff:.3e}.", ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    (out.with_suffix(".json")).write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"wrote {out}")


def _print(r):
    print(f"{r['worlds']:>7} {r['swarms']:>7} {r['size']:>6} {r['weys']:>9,} {r['arena']:>6} "
          f"{r['ms_per_tick']:>9.2f} {r['wey_ticks_per_s']:>14,.0f} {r['peak_vram_mb']:>9.0f}")


if __name__ == "__main__":
    main()
