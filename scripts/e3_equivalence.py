"""E3a's engine check, the CPU leg (experiments/E3-ab-organism/E3a/PREREGISTRATION.md §5, G-E; rule 7).

    python scripts/e3_equivalence.py --save-reference --root <a worktree at 989da99> --out runs/e3-equivalence/reference.json
    python scripts/e3_equivalence.py --compare --reference runs/e3-equivalence/reference.json --out <record>

The previous engine is the bound commit 989da99, the last before E3a's code. With `--root`, the
package is imported from that worktree, so the same script drives either engine; it uses only APIs
both have. The connectome is read from one cache file for both (`--cache`).

Cases, every per-tick state hashed (positions, headings, energies, alive flags, brain states) and the
final scores and Task N's events compared, tolerance zero:
- Task N: 300 ticks on smoke ids 0-15 (world seed 1 179 500), for 4 random N2 genomes
  (`initial_population`, run seed 1 179 500), and for E4s-1's M run 0 generation-0 genome (L1 on random
  N2, `embedded_population` with run seed 1 160 000, strain 0);
- foraging: 300 ticks on the same ids under the default configuration, for the same 4 random genomes.
The graft: E4s-1's grafted genome (that M genome) rebuilt bit-identically, and its `MODULES` entry
unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SEED = 1_179_500
IDS = list(range(16))
TICKS = 300


def _import(root: Path):
    sys.path.insert(0, str(root))
    import numpy as np  # noqa: F401
    import torch  # noqa: F401
    from wormwars import graft as G
    from wormwars.brain import Brain, BrainSpec
    from wormwars.config import Config
    from wormwars.connectome import load_connectome
    from wormwars.e04a import evolve as EV
    from wormwars.e1.task import task_n_config
    from wormwars.e4s import arms as A
    from wormwars.e4s import comparator as C
    from wormwars.interface import load_interface
    from wormwars.world import World
    return dict(G=G, Brain=Brain, BrainSpec=BrainSpec, Config=Config, load_connectome=load_connectome, EV=EV,
                task_n_config=task_n_config, A=A, C=C, load_interface=load_interface, World=World)


def _h(*arrays) -> str:
    h = hashlib.sha256()
    for a in arrays:
        h.update(a.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def _trace(M, cfg, iface, genome) -> dict:
    import numpy as np
    import torch
    S = genome.n_strains
    strain_of = torch.arange(S).repeat_interleave(len(IDS)).reshape(-1, 1)
    world = M["World"](cfg, iface, M["Brain"](genome), strain_of, run_seed=SEED, world_ids=np.tile(IDS, S))
    ticks = []
    for _ in range(TICKS):
        world.tick()
        ticks.append(_h(world.pos, world.heading, world.energy, world.alive.to(torch.uint8), *world.v))
    out = {"ticks": ticks, "final": _h(world.pos, world.heading, world.energy, *world.v)}
    if getattr(world, "navigate", False):
        out["targets_reached"] = world.targets_reached.tolist()
        out["events"] = {k: hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest()
                         for k, v in world.target_events().items()}
    return out


def run(root: Path, cache: Path) -> dict:
    M = _import(root)
    con = M["load_connectome"](cache)
    iface = M["load_interface"](con)
    spec = M["BrainSpec"].from_connectome(con)
    taskn = M["task_n_config"](sigma=6.0, amplitude=1.0, radius=1.5, separation=8.0, horizon=TICKS)
    forage = M["Config"]()
    forage.world.max_ticks = TICKS
    g4 = M["EV"].initial_population(spec, taskn.brain, SEED, 4, "cpu")
    l1 = M["A"].load_l1()
    ext = M["G"].graft_connectome(con, l1)
    gm = M["C"].embedded_population(con, ext, l1, taskn.brain, run_seed=1_160_000, population=32).select([0])
    iface_m = M["G"].graft_interface(ext, l1)
    entry = M["G"].MODULES.get(l1.name)
    import subprocess
    import wormwars
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    return {
        "engine": {"package": str(Path(wormwars.__file__).resolve()), "commit": commit},
        "task_n_random": _trace(M, taskn, iface, g4),
        "task_n_e4s1_m0": _trace(M, taskn, iface_m, gm),
        "forage_random": _trace(M, forage, iface, g4),
        "graft": {"w": _h(gm.w), "tau": _h(gm.tau), "bias": _h(gm.bias), "g": _h(gm.g),
                  "module_entry": hashlib.sha256(repr(entry).encode()).hexdigest()},
        "configs": {"task_n": hashlib.sha256(json.dumps(taskn.to_dict(), sort_keys=True).encode()).hexdigest(),
                    "forage": hashlib.sha256(json.dumps(forage.to_dict(), sort_keys=True).encode()).hexdigest()},
    }


def compare(ref: dict, new: dict) -> dict:
    diffs = {}
    for case in ("task_n_random", "task_n_e4s1_m0", "forage_random"):
        a, b = ref[case], new[case]
        first = next((t for t, (x, y) in enumerate(zip(a["ticks"], b["ticks"])) if x != y), None)
        diffs[case] = {"identical": a == b, "first_differing_tick": first}
    diffs["graft"] = {"identical": ref["graft"] == new["graft"]}
    diffs["configs"] = {"identical": ref["configs"] == new["configs"]}
    return {"cases": diffs, "passed": all(d["identical"] for d in diffs.values())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save-reference", action="store_true")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--root", default=str(HERE))
    ap.add_argument("--cache", default=str(HERE / "data" / "cache" / "cook2019_herm.npz"))
    ap.add_argument("--reference")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    doc = run(Path(a.root), Path(a.cache))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.save_reference:
        out.write_text(json.dumps(doc) + "\n", encoding="utf-8", newline="\n")
        print("reference saved", hashlib.sha256(out.read_bytes()).hexdigest())
        return
    ref_path = Path(a.reference)
    ref = json.loads(ref_path.read_text(encoding="utf-8"))
    res = compare(ref, doc)
    res["engines"] = {"reference": ref.get("engine"), "compared": doc["engine"]}
    res["reference_sha256"] = hashlib.sha256(ref_path.read_bytes()).hexdigest()
    out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(res, indent=1))
    if not res["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
