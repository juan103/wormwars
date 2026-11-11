"""E5-1a step 1's old-against-new Task H check, one side (docs/E5/E5-1-DESIGN.md §7.1). Run once with E5-0's engine
(a worktree at 7d25460, the commit E5-0's formal stages ran on) and once with the working tree; `scripts/e5_1a.py
equivalence` compares the two files bit for bit. It uses only what E5-0's Task H had: `play` with shared world ids and
one pin, `PreyBrain` of one kind, `PursuitBrain`, `HuntWorld`.

    python scripts/e5_1_reference.py --root <engine root> --out <file.npz> [--first ID --count N --ticks T]

Every E5-0 setting (19, H1-ghost and H1-reach included) with three hunters (the pursuit reference, E4s-1 run 0's validation champion C, L1 on its
carrier) on 64 worlds: captures, the event tables (activation and capture ticks, so respawns and skipped sequence
entries, paths, contact, damage, bearings), bite energy, pin pushes, the prey's wall-limited moves and the ledger's
terms; and per-tick traces (both bodies' positions and headings, and the life index) on the first 8 worlds of every
setting under the pursuit, which captures often. CPU only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = ""
MAIN = Path(__file__).resolve().parents[1]  # the working tree: records, genome files and the connectome's cache
WORLD_SEED = 1_520_001
IDS_FIRST, IDS_COUNT, TRACE_WORLDS = 985_800_000, 64, 8  # the first ids of E5-1's check block
E_PREY = 1.3750000298023224  # E5-0's calibration.json
ROUTE = {"gain": 2.0, "spacing": 6.0, "reach": 1.0}
WALK = {"rate": 0.4, "persistence": 0.9}


def settings():
    S = [("H1-ghost", "ghost", "stationary", 0.0, True), ("H1-reach", "reach", "stationary", 0.0, True),
         ("H1-bite", "bite", "stationary", 0.0, True)]
    for s in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        S.append((f"H2-{s:g}", "bite", "route", s, False))
    for kind, label in (("random_walk", "walk"), ("wall_follower", "wall")):
        for s in (0.25, 0.5, 0.75):
            S.append((f"H2b-{label}-{s:g}", "bite", kind, s, False))
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--first", type=int, default=IDS_FIRST, help="the first world id (a smoke passes its own)")
    ap.add_argument("--count", type=int, default=IDS_COUNT)
    ap.add_argument("--ticks", type=int, default=None, help="the horizon (a smoke shortens it)")
    ap.add_argument("--budget-seconds", type=float, default=float("inf"),
                    help="what is left of the caller's cap: checked before every play and trace")
    a = ap.parse_args()
    import time
    t_end = time.perf_counter() + a.budget_seconds

    def budget():
        if time.perf_counter() > t_end:
            raise SystemExit("the caller's cap is reached")
    root = Path(a.root).resolve()
    sys.path.insert(0, str(root))
    import numpy as np
    import torch
    import wormwars
    if Path(wormwars.__file__).resolve().parents[1] != root:
        raise SystemExit(f"imported wormwars from {wormwars.__file__}, not {root}")
    from wormwars import graft as G
    from wormwars.brain import Brain, BrainSpec
    from wormwars.connectome.loader import load_connectome
    from wormwars.e4s import arms as A
    from wormwars.e4s import comparator as CMP
    from wormwars.e5.hunt import HuntWorld, hunt_config
    from wormwars.e5.play import play
    from wormwars.e5.prey import PreyBrain, PursuitBrain
    from wormwars.evo.genomes import genome_hash, load_population
    from wormwars.interface import load_interface

    torch.set_grad_enabled(False)
    con = load_connectome(MAIN / "data" / "cache" / "cook2019_herm.npz")
    iface = load_interface(con)
    cfg = hunt_config()
    if a.ticks is not None:
        cfg.world.max_ticks = int(a.ticks)
    l1 = A.load_l1(root / "experiments" / "E4s-stereo-module" / "E4s-0" / "module.json")
    ext = G.graft_connectome(con, l1)
    gi = G.graft_interface(ext, l1, probe="real")
    rec = json.loads((MAIN / "experiments/E4s-stereo-module/E4s-1/train-1.json").read_text(encoding="utf-8"))
    c = rec["records"][0]["champion"]
    g4, _ = load_population(MAIN / "runs/e4s1/genomes/M-run00-candidates.npz", BrainSpec.from_connectome(ext),
                            cfg.brain)
    g4 = g4.select([c["checkpoint"]])
    assert genome_hash(g4, 0) == c["sha256"]
    carrier = CMP.carrier_genome(ext, l1, cfg.brain, forward=1.0, turn=0.2)
    wf = json.loads((MAIN / "experiments/E1-navigation/freeze.json").read_text(encoding="utf-8"))
    wf = wf["tuned"]["wall-follower"]["params"]
    wall = {k: wf[k] for k in ("seek_turn", "avoid_turn", "threshold")}
    ids = np.arange(a.first, a.first + a.count)

    def prey(kind, speed, n):
        return PreyBrain(iface, n, cfg.world.forward_gain, cfg.world.turn_gain, kind, speed=speed, wall=wall,
                         **ROUTE, **WALK)

    def pursuit():
        return PursuitBrain(iface, 302, cfg.world.forward_gain, cfg.world.turn_gain, k=2.0, speed=1.0)

    hunters = {"pursuit": (pursuit, iface, 302), "e4s1 M run00 C": (lambda: Brain(g4), gi, 306),
               "L1 carrier": (lambda: Brain(carrier), gi, 306)}
    out = {}
    for name, rule, kind, speed, pinned in settings():
        for label, (make, fc, n) in hunters.items():
            budget()
            r = play(cfg, fc, make(), prey(kind, speed, n), ids, WORLD_SEED, rule=rule, prey_energy=E_PREY,
                     pinned=pinned)
            key = f"{name}|{label}"
            out[f"{key}|captures"] = r.captures[0]
            out[f"{key}|bite_energy"] = r.bite_energy[0]
            out[f"{key}|pin_push"] = r.pin_push[0]
            out[f"{key}|prey_wall_limited"] = r.prey_wall_limited[0]
            out[f"{key}|ledger_rel"] = np.array(r.ledger_rel_error)
            for k, v in r.events.items():
                out[f"{key}|ev {k}"] = v[0]
        # traces under the pursuit
        budget()
        so = torch.zeros(TRACE_WORLDS, 2, dtype=torch.long)
        w = HuntWorld(cfg, iface, [pursuit(), prey(kind, speed, 302)], so, run_seed=WORLD_SEED,
                      world_ids=ids[:TRACE_WORLDS], rule=rule, prey_energy=E_PREY, pinned=pinned)
        pos, head, life = [], [], []
        while not w.done():
            w.tick()
            pos.append(w.pos.clone().numpy())
            head.append(w.heading.clone().numpy())
            life.append(w.life.clone().numpy())
        out[f"trace {name}|pos"], out[f"trace {name}|heading"] = np.stack(pos), np.stack(head)
        out[f"trace {name}|life"] = np.stack(life)
        for k, v in w.ledger.totals().items():
            out[f"trace {name}|ledger {k}"] = np.array(v)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.out, **out)
    print(f"wrote {a.out}: {len(out)} arrays")


if __name__ == "__main__":
    _root = Path(sys.argv[sys.argv.index("--root") + 1]).resolve()
    sys.path.insert(0, str(_root))
    from wormwars import accounting as acct
    with acct.child_ledger(), acct.category("measure"):
        main()
