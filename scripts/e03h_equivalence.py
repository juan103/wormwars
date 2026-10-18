"""03h's rule-7 check (experiments/03h-history-use/DESIGN.md §3; docs/foundations/T1.md §3, class E): T1 rollouts on the
engine before 03h's code (6facc3d) against the current one, tolerance zero, on each device separately.

    python scripts/e03h_equivalence.py --save-reference --root <a worktree at 6facc3d> --device cpu --out <ref.npz>
    python scripts/e03h_equivalence.py --compare --reference <ref.npz> --device cpu --out <record.json>

With `--root`, the package is imported from that worktree, so one script drives either engine; the reference uses only
APIs both have (the pinned interface, 02's T1 `task_config`, `rollout`).

**The comparison** is made twice against the one reference, on the current engine:
- the pinned interface with `food_fell` unset;
- 03h's interface variant under "level".

**Pinned:**
- N2;
- random genomes from `Genome.random` with a generator seeded 3_600_001 on the device;
- T1's world ids 3_600_100 onward, run seed 3_600_002;
- motor gains at the task defaults;
- on CUDA, the planned selection composition, 256 strains x 16 worlds x 20 weys, in one 4 096-world chunk, inside
  `replay_mode()`;
- on the CPU, 64 strains x 16 worlds.

**Compared per world:** score, energy, alive, eaten, pellets eaten, starting food (T1.md's class-E endpoints).
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
GENOME_SEED, RUN_SEED, FIRST_ID, WORLDS = 3_600_001, 3_600_002, 3_600_100, 16
ENDPOINTS = ("score", "energy", "alive", "eaten", "pellet_eaten", "food_start")


def _modules(root: Path):
    sys.path.insert(0, str(root))
    for m in [k for k in sys.modules if k == "wormwars" or k.startswith("wormwars.")]:
        del sys.modules[m]
    mods = {name: importlib.import_module(f"wormwars.{name}") for name in
            ("brain", "config", "connectome", "interface", "evo.rollout", "exp02.grid", "evo.bundle")}
    return mods


def _play(mods, device: str, variant: str | None):
    import torch
    B, C, conn, I, R, G, bundle = (mods[k] for k in ("brain", "config", "connectome", "interface", "evo.rollout",
                                                       "exp02.grid", "evo.bundle"))
    con = conn.load_connectome()
    cfg = G.task_config(C.Config(), "T1")
    if variant is None:
        iface = I.load_interface(con)
    else:
        from wormwars.e03h import interface_03h
        iface = interface_03h(con)
        cfg.world.food_fell = variant
    n = 256 if device == "cuda" else 64
    spec = B.BrainSpec.from_connectome(con, device=device)
    g = B.Genome.random(spec, cfg.brain, n, generator=torch.Generator(device=device).manual_seed(GENOME_SEED),
                        device=device)
    ids = np.arange(FIRST_ID, FIRST_ID + WORLDS)
    if device == "cuda":
        with bundle.replay_mode():
            r = R.rollout(cfg, iface, g, ids, RUN_SEED, device, chunk_worlds=n * WORLDS)
    else:
        r = R.rollout(cfg, iface, g, ids, RUN_SEED, device, chunk_worlds=n * WORLDS)
    return {k: np.asarray(getattr(r, k)) for k in ENDPOINTS}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--save-reference", action="store_true")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--root", type=Path, default=HERE)
    ap.add_argument("--device", choices=["cpu", "cuda"], required=True)
    ap.add_argument("--reference", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.save_reference == a.compare:
        raise SystemExit("one of --save-reference or --compare")
    if a.save_reference:
        mods = _modules(a.root.resolve())
        out = _play(mods, a.device, None)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        np.savez(a.out, **out)
        print(f"reference ({a.device}) from {a.root} -> {a.out}")
        return out
    mods = _modules(HERE)
    with np.load(a.reference, allow_pickle=False) as z:
        ref = {k: z[k] for k in ENDPOINTS}
    rec = {"device": a.device, "reference": str(a.reference), "endpoints": list(ENDPOINTS), "comparisons": {}}
    for label, variant in (("pinned interface, food_fell unset", None), ("03h variant, level", "level")):
        got = _play(mods, a.device, variant)
        per = {}
        for k in ENDPOINTS:
            d = np.abs(got[k].astype(np.float64) - ref[k].astype(np.float64))
            per[k] = {"unequal_values": int((d > 0).sum()), "max_difference": float(d.max()), "shape": list(d.shape)}
        rec["comparisons"][label] = {"endpoints": per, "bit_equal": all(v["unequal_values"] == 0 for v in per.values())}
    rec["bit_equal"] = all(c["bit_equal"] for c in rec["comparisons"].values())
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    print(f"{a.device}: bit-equal {rec['bit_equal']} -> {a.out}")
    if not rec["bit_equal"]:
        raise SystemExit(1)
    return rec


if __name__ == "__main__":
    main()
