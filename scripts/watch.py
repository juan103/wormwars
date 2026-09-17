"""Run one foraging world and look at it.

    python scripts/watch.py --out runs/look --ticks 400

Writes a contact sheet, a field panel and an energy plot. With --gif it also writes an animation.
"""

from __future__ import annotations

import argparse
import sys as _sys
from pathlib import Path as _Path

import torch

_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo.genomes import load_genome
from wormwars.interface import load_interface
from wormwars.recorder import Recorder, Replay
from wormwars.viewer import contact_sheet, energy_plot, gif, panel
from wormwars.world import World


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/look")
    ap.add_argument("--ticks", type=int, default=400)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--weys", type=int, default=20)
    ap.add_argument("--swarms", type=int, default=1)
    ap.add_argument("--worlds", type=int, default=1)
    ap.add_argument("--genome", default=None, help="path to a saved genome bundle")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--gif", action="store_true")
    ap.add_argument("--stage", type=int, default=0, help="combat stage")
    args = ap.parse_args()

    cfg = Config()
    cfg.world.weys_per_swarm = args.weys
    cfg.world.n_swarms = args.swarms
    cfg.world.max_ticks = args.ticks
    con = load_connectome()
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con, device=args.device)

    if args.genome:
        genome, meta = load_genome(args.genome, spec, cfg.brain, device=args.device)
        print(f"loaded {meta.get('strain_id', args.genome)}")
    else:
        g = torch.Generator().manual_seed(args.seed)
        genome = Genome.random(spec, cfg.brain, 1, generator=g, device=args.device)
        print("random-weight genome")

    brain = Brain(genome)
    strain_of = torch.zeros(args.worlds, args.swarms, dtype=torch.long)
    world = World(cfg, iface, brain, strain_of, run_seed=args.seed, device=args.device,
                  combat_stage=args.stage)
    rec = Recorder(worlds=(0,), field_every=2).attach(world)
    world.run()

    out = _Path(args.out)
    rec.save(out / "replay.npz")
    replay = Replay.load(out / "replay.npz")
    print("contact sheet:", contact_sheet(replay, out / "sheet.png"))
    print("field panel  :", panel(replay, out / "panel.png"))
    print("energy plot  :", energy_plot(replay, out / "energy.png"))
    if args.gif:
        print("gif          :", gif(replay, out / "match.gif"))

    e = world.swarm_energy()
    print(f"ticks {world.tick_count}  alive {world.n_alive().tolist()}  energy {e.tolist()}")
    print(f"ledger error {world.energy_ledger_error().abs().max().item():.3e}")
    print(f"ledger {world.ledger.totals()}")


if __name__ == "__main__":
    main()
