"""E3d's full-rollout rule-7 leg (docs/E3/E3d-DESIGN.md v2.2 §7): tree-family maze rollouts, the engine before
E3d's code (40bd50f) against the current one, tolerance zero.

    python scripts/e3d_equivalence.py --save-reference --root <a worktree at 40bd50f> --device cpu --out <ref.json>
    python scripts/e3d_equivalence.py --save-reference --root <a worktree at 40bd50f> --device cuda --out <ref.json>
    python scripts/e3d_equivalence.py --compare --reference <ref.json> --device cpu --out <record.json>

With `--root`, the package is imported from that worktree, so one script drives either engine; it uses only
APIs both have (`maze_world.maze_config` without a family, `maze_controls.follower`, `assembly.context`, E3c's
`base_config`).

**Pinned:** the scripted follower and the seed E + W2; maze run seed 1 190 000; maze ids 30 000-30 007;
episode 0; c = 5 and c = 6; H = 2 400; colonies of 8; the 8 mazes in one chunk (8 worlds); shared trails;
float32. On CUDA, inside `replay_mode()`.

**Hashed every tick:** positions, headings, goals and visits; **at the end:** the visit ticks, the raw entries
and the first-B ticks.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SEED, IDS, H, COLONY = 1_190_000, list(range(30_000, 30_008)), 2400, 8
TRAIL = dict(mu=0.01, lam=0.02, delta=0.05, d0=1.142)
SIZES = (5, 6)


def _h(*arrays) -> str:
    h = hashlib.sha256()
    for a in arrays:
        h.update(a.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def _hn(a) -> str:
    import numpy as np
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def _modules(root: Path):
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location("e3c_for_e3d_eq", root / "scripts" / "e3c.py")
    e3c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(e3c)  # inserts `root` on sys.path itself; the package resolves from `root`
    from wormwars.connectome import load_connectome
    from wormwars.e3 import assembly as AS
    from wormwars.e3 import maze_controls as MC
    from wormwars.e3 import maze_organisms as MO
    from wormwars.e3 import maze_world as MW
    from wormwars.e4s import arms as A
    from wormwars.evo.bundle import replay_mode
    from wormwars.interface import load_interface
    return dict(e3c=e3c, load_connectome=load_connectome, load_interface=load_interface, AS=AS, MC=MC, MO=MO, MW=MW, A=A, replay_mode=replay_mode)


def _trace(M, cfg, iface, brain, device) -> dict:
    import numpy as np
    import torch
    strain_of = torch.zeros(len(IDS), 1, dtype=torch.long, device=device)
    world = M["MW"].MazeWorld(cfg, iface, brain, strain_of, run_seed=SEED, world_ids=np.asarray(IDS), device=device,
                              access="shared")
    ticks = []
    for _ in range(H):
        world.tick()
        ticks.append(_h(world.pos, world.heading, world.goal, world.visits))
    ev = world.task_events()
    return {"ticks": ticks, "final": ticks[-1],
            "events": {k: _hn(ev[k]) for k in ("visit_tick", "entries", "first_b_tick", "visits")},
            "visits_total": int(ev["visits"].sum())}


def run(root: Path, device: str, cache: Path) -> dict:
    import contextlib
    import torch
    M = _modules(root)
    con = M["load_connectome"](cache)  # one cache file for both engines
    base = M["e3c"].base_config()
    l1 = M["A"].load_l1()
    out = {}
    ctx = M["replay_mode"]() if device.startswith("cuda") else contextlib.nullcontext()
    with ctx:
        for c in SIZES:
            cfg = M["MW"].maze_config(base.copy(), c=c, horizon=H, colony=COLONY, access="shared", spawns=4, **TRAIL)
            seed = M["AS"].context(con, l1, cfg.brain)["seed"]
            iface = M["load_interface"](con)  # the scripted follower on the plain worm, as E3b-0 played it
            out[f"follower_c{c}"] = _trace(M, cfg, iface, M["MC"].follower(iface, cfg, device=device), device)
            out[f"seed_c{c}"] = _trace(M, cfg, seed.iface, M["MO"].brain(seed, device), device)
            out[f"config_c{c}"] = hashlib.sha256(json.dumps(cfg.to_dict(), sort_keys=True).encode()).hexdigest()
    import wormwars
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", "wormwars", "scripts", "configs"],
                           capture_output=True, text=True).stdout.strip()
    return {"engine": {"package": str(Path(wormwars.__file__).resolve()), "commit": commit, "dirty": bool(dirty)},
            "device": device, "torch": torch.__version__,
            "gpu": torch.cuda.get_device_name(0) if device.startswith("cuda") else None,
            "pins": {"seed": SEED, "ids": IDS, "episode": 0, "sizes": list(SIZES), "H": H, "colony": COLONY,
                     "worlds_per_chunk": len(IDS), "access": "shared", "dtype": "float32", "trail": TRAIL},
            "cases": out}


def compare(ref: dict, new: dict) -> dict:
    """Every case identical, tick by tick, and the events and configurations identical."""
    diffs = {}
    for k, a in ref["cases"].items():
        b = new["cases"].get(k)
        if b is None:
            diffs[k] = {"identical": False, "missing": True}
        elif isinstance(a, str):
            diffs[k] = {"identical": a == b}
        else:
            first = next((t for t, (x, y) in enumerate(zip(a["ticks"], b["ticks"])) if x != y), None)
            same = first is None and len(a["ticks"]) == len(b["ticks"]) and a["events"] == b["events"]
            diffs[k] = {"identical": same, "first_differing_tick": first, "visits_total": [a["visits_total"], b["visits_total"]]}
    return {"identical": all(d["identical"] for d in diffs.values()) and ref["pins"] == new["pins"]
            and ref["device"] == new["device"], "cases": diffs,
            "engines": {"reference": ref["engine"], "compared": new["engine"]}}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--save-reference", action="store_true")
    g.add_argument("--compare", action="store_true")
    ap.add_argument("--root", type=Path, default=HERE)
    ap.add_argument("--reference", type=Path)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--cache", type=Path, default=HERE / "data" / "cache" / "cook2019_herm.npz")
    a = ap.parse_args()
    new = run(a.root.resolve(), a.device, a.cache.resolve())
    if a.save_reference:
        if new["engine"]["dirty"]:
            raise SystemExit("the reference engine's worktree has local changes: refusing")
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(new, indent=1), encoding="utf-8", newline="\n")
        print("wrote", a.out)
    else:
        rec = compare(json.loads(a.reference.read_text(encoding="utf-8")), new)
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(rec, indent=1), encoding="utf-8", newline="\n")
        print("identical" if rec["identical"] else "DIFFERENT", a.out)
        sys.exit(0 if rec["identical"] else 1)


if __name__ == "__main__":
    main()
