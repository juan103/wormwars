"""E5-0's old-against-new engine check, one side (docs/E5/E5-0-PLAN.md §4.1). Run once with the engine before E5's
hooks (a worktree at ab749bb) and once with the working tree; `scripts/e5_0.py equivalence` compares the two files
bit for bit. It imports only the engine at `--root`, so it must not use anything E5 added.

    python scripts/e5_0_reference.py --root <engine root> --out <file.npz>

Task N with E1's frozen S-const, the oracle, E4s-1 run 0's champion and E2's GA run 0 champion on the 512 equivalence
worlds (counts and event tables), per-tick traces of positions, headings, input currents and neural states on the
first 8, and a two-swarm combat world (forage, combat stage 1, two random strains of 6 weys, 100 ticks, 64 worlds).
CPU only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""
MAIN = Path(__file__).resolve().parents[1]  # the working tree: records, genome files and the connectome's cache
RUN_SEED = 1_500_001
IDS_FIRST, IDS_COUNT, TRACE_WORLDS = 991_200_000, 512, 8
NAV = {"k": 8192.0, "speed": 1.0, "turn": 0.0}  # E1's frozen S-const (freeze.json)


class Tap:
    """A brain wrapper recording, per tick, the input current it receives and the state it returns."""

    def __init__(self, brain):
        self._b, self.currents, self.states = brain, [], []

    def __getattr__(self, name):
        return getattr(self._b, name)

    def step(self, v, current):
        out = self._b.step(v, current)
        self.currents.append(current.detach().clone().numpy())
        self.states.append(out.detach().clone().numpy())
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    root = Path(a.root).resolve()
    sys.path.insert(0, str(root))
    import numpy as np
    import torch
    import wormwars
    if Path(wormwars.__file__).resolve().parents[1] != root:
        raise SystemExit(f"imported wormwars from {wormwars.__file__}, not {root}")
    from wormwars import graft as G
    from wormwars.brain import Brain, BrainSpec, Genome
    from wormwars.config import Config
    from wormwars.connectome.loader import load_connectome
    from wormwars.e1 import controllers as C
    from wormwars.e1.task import task_n_config
    from wormwars.e4s import arms as A
    from wormwars.evo.genomes import genome_hash, load_population
    from wormwars.evo.rollout import rollout, rollout_brain
    from wormwars.interface import load_interface
    from wormwars.world import World

    torch.set_grad_enabled(False)
    con = load_connectome(MAIN / "data" / "cache" / "cook2019_herm.npz")
    iface = load_interface(con)
    cfg = task_n_config(sigma=6.0, amplitude=1.0, radius=1.5, separation=8.0, max_separation=0.0, horizon=300)
    cfg.world.target_wall_clearance, cfg.world.sense_scale_food = 3.0, 0.35
    ids = np.arange(IDS_FIRST, IDS_FIRST + IDS_COUNT)
    out = {}

    def keep(label, r):
        out[f"{label}|count"] = r.score[0]
        for k, v in r.events.items():
            out[f"{label}|{k}"] = v[0]

    # the hunters
    l1 = A.load_l1(root / "experiments" / "E4s-stereo-module" / "E4s-0" / "module.json")
    ext = G.graft_connectome(con, l1)
    gi = G.graft_interface(ext, l1, probe="real")
    rec = json.loads((MAIN / "experiments/E4s-stereo-module/E4s-1/train-1.json").read_text(encoding="utf-8"))
    c = rec["records"][0]["champion"]
    g4, _ = load_population(MAIN / "runs/e4s1/genomes/M-run00-candidates.npz", BrainSpec.from_connectome(ext), cfg.brain)
    g4 = g4.select([c["checkpoint"]])
    assert genome_hash(g4, 0) == c["sha256"]
    rec = json.loads((MAIN / "experiments/E2-optimizer-screen/train-ga.json").read_text(encoding="utf-8"))
    c = rec["records"][0]["champion"]
    g2, _ = load_population(MAIN / "runs/e2/genomes/ga-run00-candidates.npz", BrainSpec.from_connectome(con), cfg.brain)
    g2 = g2.select([c["checkpoint"]])
    assert genome_hash(g2, 0) == c["sha256"]

    keep("S-const", rollout_brain(cfg, iface, C.scripted(iface, C.s_const(**NAV), cfg), ids, RUN_SEED))
    keep("oracle", rollout_brain(cfg, iface, C.OracleBrain(iface, 302, cfg.world.forward_gain, cfg.world.turn_gain),
                                 ids, RUN_SEED))
    keep("e4s1 run00", rollout(cfg, gi, g4, ids, RUN_SEED))
    keep("e2 ga run00", rollout(cfg, iface, g2, ids, RUN_SEED))

    # per-tick traces on the first worlds
    for label, (brain, fc) in {"S-const": (C.scripted(iface, C.s_const(**NAV), cfg), iface),
                               "e4s1 run00": (Brain(g4), gi), "e2 ga run00": (Brain(g2), iface)}.items():
        tap = Tap(brain)
        w = World(cfg, fc, tap, torch.zeros(TRACE_WORLDS, 1, dtype=torch.long), run_seed=RUN_SEED,
                  world_ids=ids[:TRACE_WORLDS])
        pos, head = [], []
        while not w.done():
            w.tick()
            pos.append(w.pos.clone().numpy())
            head.append(w.heading.clone().numpy())
        out[f"trace {label}|pos"], out[f"trace {label}|heading"] = np.stack(pos), np.stack(head)
        out[f"trace {label}|current"], out[f"trace {label}|state"] = np.stack(tap.currents), np.stack(tap.states)

    # a two-swarm fight
    fc = Config()
    fc.world.n_swarms, fc.world.weys_per_swarm, fc.world.max_ticks = 2, 6, 100
    g = Genome.random(BrainSpec.from_connectome(con), fc.brain, 2, generator=torch.Generator().manual_seed(3))
    so = torch.tensor([[0, 1]] * 64)
    w = World(fc, iface, [Brain(g), Brain(g)], so, run_seed=RUN_SEED, world_ids=np.arange(IDS_FIRST, IDS_FIRST + 64),
              combat_stage=1)
    w.run()
    out["fight|energy"], out["fight|pos"] = w.energy.numpy(), w.pos.numpy()
    out["fight|alive"], out["fight|damage_points"] = w.alive.numpy(), w.damage_points.numpy()
    for k, v in w.ledger.totals().items():
        out[f"fight|ledger {k}"] = np.array(v)
    # and one placed so that it bites from the first tick (random brains may never meet in 100 ticks)
    fc.world.max_ticks = 20
    b = [C.scripted(iface, C.ConstantMotion(0.3, 0.0), fc), C.scripted(iface, C.ConstantMotion(0.0, 0.0), fc)]
    w = World(fc, iface, b, torch.zeros(1, 2, dtype=torch.long), run_seed=RUN_SEED, combat_stage=1)
    for i in range(6):
        w.pos[0, 0, i] = torch.tensor([8.0, 6.0 + 3 * i])
        w.heading[0, 0, i] = 0.0
        w.pos[0, 1, i] = torch.tensor([10.0, 7.2 + 3 * i])
        w.heading[0, 1, i] = -torch.pi / 2
    w._points = None
    w._update_body_field()
    w.run()
    assert float(w.damage_points.sum()) > 0
    out["placed fight|energy"], out["placed fight|pos"] = w.energy.numpy(), w.pos.numpy()
    out["placed fight|damage_points"] = w.damage_points.numpy()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out, **out)
    print(f"wrote {a.out}: {len(out)} arrays")


if __name__ == "__main__":
    main()
