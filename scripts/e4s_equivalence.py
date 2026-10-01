"""E4s engine check (AGENTS.md rule 7; docs/E4s/DESIGN.md v2, "Engine changes" 3):

    python scripts/e4s_equivalence.py     # writes experiments/E4s-stereo-module/development-records/equivalence-ga.json

`Genome.mutate` gained optional per-parameter scales and 04a's `evolve_batch` gained the `initial`
and `mutation_scales` hooks. With the defaults, E2's GA must be unchanged: this reruns E2's formal GA
batch (its 8 run seeds, its training and validation worlds, its composition of 8 runs × 32 strains × 8
worlds, on the GPU) for generations 0-25, three ways (the defaults, hooks restating the defaults, and
scale vectors of ones), and compares every generation's best-genome hash with E2's committed
`train-ga.json`.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import BrainSpec  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

OUT = ROOT / "experiments" / "E4s-stereo-module" / "development-records" / "equivalence-ga.json"
E2_TRAIN = ROOT / "experiments" / "E2-optimizer-screen" / "train-ga.json"
GENERATIONS = 26


def load_e2():
    s = importlib.util.spec_from_file_location("e2_for_equivalence", ROOT / "scripts" / "e2.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    E = load_e2()
    cfg = E.task_config()
    con = load_connectome()
    iface, spec = load_interface(con), BrainSpec.from_connectome(con)
    committed = json.loads(E2_TRAIN.read_text(encoding="utf-8"))
    runs = [EV.RunSpec(**r["spec"]) for r in committed["records"]]
    assert [r.run_seed for r in runs] == [r.run_seed for r in E.run_specs()]
    want = [[g["best_sha256"] for g in r["log"][:GENERATIONS]] for r in committed["records"]]
    ids = E.REGISTERED["ids"]["train"]
    ones = {"w": torch.ones(spec.n_chem), "g": torch.ones(spec.n_gap), "tau": torch.ones(spec.n),
            "bias": torch.ones(spec.n)}
    variants = {
        "defaults": {},
        "hooks restating the defaults": {
            "initial": lambda r: EV.initial_population(spec, cfg.brain, r.run_seed, cfg.evo.population, "cpu")},
        "scale vectors of ones": {"mutation_scales": lambda r: ones},
    }
    out = {}
    for name, hooks in variants.items():
        t0 = time.perf_counter()
        recs = EV.evolve_batch(cfg, iface, spec, runs, generations=GENERATIONS,
                               checkpoint_every=E.REGISTERED["checkpoint_every"], validation_ids=E.validation_ids(),
                               world_seed=E.REGISTERED["world_seed"], id_base=ids["base"], id_span=ids["span"],
                               device="cuda", **hooks)
        got = [[g["best_sha256"] for g in r.log] for r in recs]
        match = [[a == b for a, b in zip(gr, wr)] for gr, wr in zip(got, want)]
        out[name] = {"all_match": all(all(m) for m in match),
                     "matching_generations_per_run": [sum(m) for m in match],
                     "first_mismatch_per_run": [m.index(False) if False in m else None for m in match],
                     "seconds": time.perf_counter() - t0}
        print(name, out[name])
    doc = {"what": "E4s engine check: E2's GA, generations 0-25, with the E4s hooks at their defaults",
           "generations": GENERATIONS, "composition": {"training": [len(runs) * cfg.evo.population,
                                                                    cfg.evo.worlds_per_strain, 1]},
           "device": torch.cuda.get_device_name(0), "torch": torch.__version__, "results": out,
           "provenance": {"git_commit": reg.git("rev-parse", "HEAD"), "script_sha256": reg.file_sha256(Path(__file__)),
                          "dirty": bool(subprocess.run(["git", "status", "--porcelain", "--", "scripts", "wormwars"],
                                                       cwd=ROOT, capture_output=True, text=True).stdout.strip())}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
