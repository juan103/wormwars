"""04a's engine-equivalence check (AGENTS.md rule 7; D104): the rollout before 04a's changes
(`5eaf339`) against the rollout after them, on smoke ids (outside every E1 and 04a range).

    python scripts/e04a_equivalence.py run --root ../wormWars-e04a-ref --device cpu --out ref-cpu.npz
    python scripts/e04a_equivalence.py run --root . --device cpu --out new-cpu.npz
    python scripts/e04a_equivalence.py compare ref-cpu.npz new-cpu.npz

**Declared before running:** with shared world ids ([worlds], the only form the old engine takes)
and the same composition, the new engine must reproduce the old one **exactly** on the CPU: every
score, and every entry of the event table. On CUDA the same comparison is reported, and exactness
is expected but not required (CUDA default mode, docs/REPRODUCIBILITY.md).

The arms: E1's navigator (S-const at its frozen parameters) and the oracle, each one strain on 64
worlds; and 4 random N2 genomes together on 16 worlds, the neural path. Task N at σ = 6, 300 ticks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

TOLERANCE = {"cpu": "exact", "cuda": "reported; exact expected, not required"}
KEYS = ("activation_tick", "reach_tick", "path_length", "target_x", "target_y", "start_x", "start_y", "end_x", "end_y")


def run(args):
    root = Path(args.root).resolve()
    sys.path.insert(0, str(root))
    import torch

    from wormwars.brain import BrainSpec, Genome
    from wormwars.connectome import load_connectome
    from wormwars.e1 import controllers as C
    from wormwars.e1.task import task_n_config
    from wormwars.evo.rollout import rollout, rollout_brain
    from wormwars.interface import load_interface

    import wormwars
    assert Path(wormwars.__file__).resolve().is_relative_to(root), "imported the library from the wrong tree"
    cfg = task_n_config(sigma=6.0, amplitude=1.0, radius=1.5, separation=8.0, max_separation=0.0, horizon=300)
    cfg.world.target_wall_clearance, cfg.world.sense_scale_food = 3.0, 0.35
    con = load_connectome()
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con)
    tuned = json.loads((Path(__file__).resolve().parents[1] / "experiments" / "E1-navigation" / "freeze.json")
                       .read_text(encoding="utf-8"))["tuned"]
    ids64, ids16 = np.arange(64), np.arange(100, 116)
    out = {}
    nav = C.scripted(iface, C.s_const(**tuned["S-const"]["params"]), cfg, device=args.device)
    orc = C.OracleBrain(iface, 302, cfg.world.forward_gain, cfg.world.turn_gain, device=args.device,
                        **tuned["oracle"]["params"])
    for name, brain in (("navigator", nav), ("oracle", orc)):
        r = rollout_brain(cfg, iface, brain, ids64, 1_100_001, args.device)
        out[f"{name}|score"] = r.score
        out.update({f"{name}|{k}": r.events[k] for k in KEYS})
    g = Genome.random(spec, cfg.brain, 4, generator=torch.Generator().manual_seed(12))
    g = g.with_params(spec=g.spec.to(args.device), **{k: v.to(args.device) for k, v in g.params().items()
                                                     if v is not None})
    r = rollout(cfg, iface, g, ids16, 1_100_001, args.device, chunk_worlds=64)
    out["neural|score"] = r.score
    out.update({f"neural|{k}": r.events[k] for k in KEYS})
    np.savez_compressed(args.out, **out)
    print(f"wrote {args.out}: " + ", ".join(f"{k.split('|')[0]} mean {v.mean():.3f}" for k, v in out.items()
                                            if k.endswith("|score")))


def compare(args):
    a, b = np.load(args.a, allow_pickle=False), np.load(args.b, allow_pickle=False)
    if set(a.files) != set(b.files):
        raise SystemExit(f"different arrays: {sorted(set(a.files) ^ set(b.files))}")
    rows = {}
    for k in sorted(a.files):
        x, y = a[k], b[k]
        same = bool(np.array_equal(x, y, equal_nan=True))
        rows[k] = {"identical": same, "max_abs_difference": float(np.nanmax(np.abs(x.astype(float) - y.astype(float))))
                   if x.size else 0.0}
    ok = all(r["identical"] for r in rows.values())
    doc = {"tolerance": TOLERANCE, "a": Path(args.a).name, "b": Path(args.b).name, "reference_commit": "5eaf339", "all_identical": ok, "arrays": rows}
    if args.json:
        Path(args.json).write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("all identical" if ok else "DIFFERENT: " + ", ".join(k for k, r in rows.items() if not r["identical"]))
    if not ok:
        raise SystemExit(1)  # a failed exact comparison fails the command (Astra, review v2)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--root", required=True)
    r.add_argument("--device", default="cpu")
    r.add_argument("--out", required=True)
    c = sub.add_parser("compare")
    c.add_argument("a")
    c.add_argument("b")
    c.add_argument("--json")
    args = ap.parse_args()
    {"run": run, "compare": compare}[args.cmd](args)


if __name__ == "__main__":
    main()
