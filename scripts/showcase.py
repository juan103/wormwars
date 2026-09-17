"""Showcase mode: one large world, two chosen strains, recorded and rendered.

    python scripts/showcase.py --a runs/m7/champion-a.npz --b runs/m7/champion-b.npz --size 2000

Spectacle, and a generalisation test: the strains were selected at 20-100 weys a side and are asked
here to hold together at a size they have never seen. **Never used for selection.**
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
from wormwars.connectome.graphs import random_graph, shuffled
from wormwars.evo import load_genome
from wormwars.interface import load_interface
from wormwars.recorder import Recorder, Replay
from wormwars.viewer import contact_sheet, energy_plot, gif, panel
from wormwars.world import World


def graph_for(con, label):
    if label == "N2":
        return con
    kind, num = label[:2], int(label[2:])
    return shuffled(con, num, label) if kind == "SH" else random_graph(con, num, label)


def load_side(path, con, cfg, device, seed):
    if path is None:
        spec = BrainSpec.from_connectome(con, device=device)
        g = torch.Generator(device=device).manual_seed(seed)
        return Genome.random(spec, cfg.brain, 1, generator=g, device=device), {
            "nickname": "random", "graph": "N2"
        }
    meta = json.loads(str(np.load(path, allow_pickle=True)["meta"]))
    spec = BrainSpec.from_connectome(graph_for(con, meta["graph"]), device=device)
    genome, meta = load_genome(path, spec, cfg.brain, device=device, strain=0)
    return genome, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default=None, help="genome for swarm A (random if omitted)")
    ap.add_argument("--b", default=None, help="genome for swarm B (random if omitted)")
    ap.add_argument("--size", type=int, default=2000, help="weys per swarm")
    ap.add_argument("--ticks", type=int, default=600)
    ap.add_argument("--stage", type=int, default=1)
    ap.add_argument("--seed", type=int, default=777)
    ap.add_argument("--out", default="runs/showcase")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--gif", action="store_true")
    args = ap.parse_args()

    cfg = Config()
    cfg.world.n_swarms = 2
    cfg.world.weys_per_swarm = args.size
    cfg.world.max_ticks = args.ticks

    con = load_connectome()
    iface = load_interface(con)
    ga, meta_a = load_side(args.a, con, cfg, args.device, args.seed)
    gb, meta_b = load_side(args.b, con, cfg, args.device, args.seed + 1)

    world = World(
        cfg, iface, [Brain(ga), Brain(gb)], torch.zeros(1, 2, dtype=torch.long),
        run_seed=args.seed, device=args.device, combat_stage=args.stage,
    )
    print(
        f"showcase: {meta_a.get('nickname')} ({meta_a['graph']}) vs "
        f"{meta_b.get('nickname')} ({meta_b['graph']})\n"
        f"{args.size} v {args.size} in a {world.side}x{world.side} arena, "
        f"{args.ticks} ticks, stage {args.stage}"
    )
    rec = Recorder(worlds=(0,), field_every=8).attach(world)

    if args.device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    t0 = time.perf_counter()
    world.run()
    dt = time.perf_counter() - t0
    weys = 2 * args.size
    print(
        f"{world.tick_count} ticks in {dt:.1f}s -> "
        f"{weys * world.tick_count / dt:,.0f} wey-ticks/s"
        + (f", peak VRAM {torch.cuda.max_memory_allocated() / 2**20:.0f} MB"
           if args.device == "cuda" else "")
    )
    e = world.swarm_energy()[0]
    alive = world.n_alive()[0]
    start = args.size * cfg.world.start_energy
    print(f"A: {int(alive[0])} alive, energy {e[0]:.0f}   B: {int(alive[1])} alive, energy {e[1]:.0f}")
    print(f"match score (A): {float((e[0] - e[1]) / (2 * start)):+.4f}")
    print(f"ledger error: {world.energy_ledger_error().abs().max().item():.3e}")

    out = _Path(args.out)
    rec.save(out / "replay.npz")
    replay = Replay.load(out / "replay.npz")
    print("contact sheet:", contact_sheet(replay, out / "sheet.png", show="food"))
    print("attack view  :", contact_sheet(replay, out / "attack.png", show="attack"))
    print("field panel  :", panel(replay, out / "panel.png"))
    print("energy plot  :", energy_plot(replay, out / "energy.png"))
    if args.gif:
        print("gif          :", gif(replay, out / "match.gif", stride=6))
    print("\nShowcase results are never used for selection.")


if __name__ == "__main__":
    main()
