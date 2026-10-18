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
- Each endpoint must have the reference's exact shape, and every value must be finite and equal (Astra: an absolute
  difference would pass NaNs and broadcast shapes).
- The reference's provenance is recorded beside it and carried into the comparison record (Fable, Astra):
  - the worktree's commit and dirty state;
  - the reference file's sha256;
  - torch, CUDA and the GPU.
- `--root` is required for a reference, and the expected commit is checked.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parents[1]
GENOME_SEED, RUN_SEED, FIRST_ID, WORLDS = 3_600_001, 3_600_002, 3_600_100, 16
ENDPOINTS = ("score", "energy", "alive", "eaten", "pellet_eaten", "food_start")
REFERENCE_COMMIT = "6facc3d"  # the commit before 03h's code (D326)


def compare_endpoints(got: dict, ref: dict) -> dict:
    """Per endpoint: equal shapes, finite values and exact equality; anything else is unequal (no broadcasting)."""
    per = {}
    for k in ENDPOINTS:
        a, b = np.asarray(got[k]), np.asarray(ref[k])
        if a.shape != b.shape:
            per[k] = {"shape_match": False, "shape": list(a.shape), "reference_shape": list(b.shape),
                      "unequal_values": None, "max_difference": None}
            continue
        a64, b64 = a.astype(np.float64), b.astype(np.float64)
        bad = ~(np.isfinite(a64) & np.isfinite(b64)) | (a64 != b64)
        d = np.where(bad & np.isfinite(a64) & np.isfinite(b64), np.abs(a64 - b64), 0.0)
        per[k] = {"shape_match": True, "shape": list(a.shape), "unequal_values": int(bad.sum()),
                  "non_finite": int((~(np.isfinite(a64) & np.isfinite(b64))).sum()), "max_difference": float(d.max())}
    ok = all(v["shape_match"] and v["unequal_values"] == 0 for v in per.values())
    return {"endpoints": per, "bit_equal": bool(ok)}


def _git(root: Path, *args) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


def _environment() -> dict:
    import torch
    return {"torch": torch.__version__, "cuda": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "python": sys.version.split()[0]}


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
    ap.add_argument("--root", type=Path, help="with --save-reference: a worktree at the reference commit (required)")
    ap.add_argument("--device", choices=["cpu", "cuda"], required=True)
    ap.add_argument("--reference", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    if a.save_reference == a.compare:
        raise SystemExit("one of --save-reference or --compare")
    if a.save_reference:
        if a.root is None:
            raise SystemExit("--save-reference needs --root, a worktree at the reference commit")
        root = a.root.resolve()
        head, dirty = _git(root, "rev-parse", "HEAD"), bool(_git(root, "status", "--porcelain", "--untracked-files=no"))
        if not head.startswith(REFERENCE_COMMIT):
            raise SystemExit(f"the worktree is at {head[:7]}, not the reference commit {REFERENCE_COMMIT}")
        if dirty:
            raise SystemExit("the reference worktree has uncommitted changes")
        mods = _modules(root)
        out = _play(mods, a.device, None)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        np.savez(a.out, **out)
        prov = {"commit": head, "dirty": dirty, "root": str(root), "device": a.device,
                "sha256": hashlib.sha256(a.out.read_bytes()).hexdigest(), **_environment()}
        a.out.with_suffix(".json").write_text(json.dumps(prov, indent=1) + "\n", encoding="utf-8")
        print(f"reference ({a.device}) from {root} at {head[:7]} -> {a.out}")
        return out
    mods = _modules(HERE)
    ref_prov = json.loads(a.reference.with_suffix(".json").read_text(encoding="utf-8"))
    if hashlib.sha256(a.reference.read_bytes()).hexdigest() != ref_prov["sha256"]:
        raise SystemExit("the reference file does not match its recorded sha256")
    if ref_prov["device"] != a.device:
        raise SystemExit("the reference was saved on another device (T1.md: each device separately)")
    with np.load(a.reference, allow_pickle=False) as z:
        ref = {k: z[k] for k in ENDPOINTS}
    sys.path.insert(0, str(HERE))
    from wormwars import registration as reg
    rec = {"device": a.device, "reference": {"file": a.reference.name, **ref_prov},
           "current": {"provenance": reg.provenance(["wormwars", "scripts", "configs"]), **_environment()},
           "endpoints": list(ENDPOINTS), "comparisons": {}}
    for label, variant in (("pinned interface, food_fell unset", None), ("03h variant, level", "level")):
        rec["comparisons"][label] = compare_endpoints(_play(mods, a.device, variant), ref)
    rec["bit_equal"] = all(c["bit_equal"] for c in rec["comparisons"].values())
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    print(f"{a.device}: bit-equal {rec['bit_equal']} -> {a.out}")
    if not rec["bit_equal"]:
        raise SystemExit(1)
    return rec


if __name__ == "__main__":
    main()
