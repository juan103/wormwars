"""03h's step 0 (experiments/03h-history-use/DESIGN.md §7.2): exploratory and disclosed, on 03's committed T1 fitness.

    python scripts/e03h_step0.py            # on CUDA; writes experiments/03h-history-use/development-records/step0.json
    python scripts/e03h_step0.py --smoke    # two graphs, 16 genomes, on the CPU, to runs/e03h-smoke/ (checks the code)

03's pilot (experiments/03-generation0/pilot.json) holds T1-M0 fitness for 256 random genomes x 16 worlds on each of 16
SH graphs, but measured history on a separate genome draw. Step 0 rebuilds those graphs and genomes by 03's recipe
(`scripts/exp03.py`: graphs `pilotSH101`-`pilotSH116`, SH with that seed and 20 passes; genomes from one CUDA
`Genome.random(..., 256, ...)` call seeded by `genome_seed(name, "")`, without the probe population's +1), verifies by
replaying one graph's T1-M0 fitness bit-equal per world (T1's class-E contract, tolerance zero), and only then measures
H and S (`history()` on 03's bank) on the same genomes and relates them to the committed fitness, under level only.
If the replay is not bit-equal, step 0 is dropped and the record says so. It sets nothing by itself.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e03h.stats import partial_spearman  # noqa: E402
from wormwars.evo.rollout import rollout  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.exp03.measures import history  # noqa: E402

_spec = importlib.util.spec_from_file_location("exp03_for_e03h", ROOT / "scripts" / "exp03.py")
X3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(X3)  # 03's driver, instance "03" (its import-time default): seeds, worlds, graphs

EXP = ROOT / "experiments" / "03h-history-use"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", "experiments/03h-history-use/DESIGN.md"]
VERIFY = "pilotSH101"


def cfg_t1(name, gains):
    c = grid.brain_config_for_graph(grid.task_config(Config(), "T1"), name)
    c.world.forward_gain, c.world.turn_gain = gains
    return c


def genomes_of(con, name, cfg, n, device):
    graph = X3._load_graph(con, name)
    spec = BrainSpec.from_connectome(graph, device=device)
    gen = torch.Generator(device=device).manual_seed(X3._gseed(name))
    return Genome.random(spec, cfg.brain, n, generator=gen, device=device)


def run(smoke: bool) -> dict:
    X3.use_instance("03")
    device = "cpu" if smoke else "cuda"
    pilot = json.loads(X3.PILOT.read_text(encoding="utf-8"))
    remap = json.loads(X3.INPUT_FILES["remaps.json"].read_text(encoding="utf-8"))["sets"]
    con = load_connectome()
    iface = grid.interface_for(con, "M0", remap)
    bank = pilot["bank"]
    records = {g["name"]: g for g in pilot["graphs"]}
    names = sorted(records)[:2] if smoke else sorted(records)
    n_genomes = 16 if smoke else 256
    out = {"exploratory": True, "device": device, "smoke": smoke, "graphs": {}, "verification": None}

    # 1. the verification replay: one graph's T1-M0 fitness, bit-equal per world
    rec = records[VERIFY]
    cfg = cfg_t1(VERIFY, tuple(rec["gains"]))
    with acct.category("measure"):
        big = genomes_of(con, VERIFY, cfg, 256, device)
        if smoke:
            big = big.select(list(range(n_genomes)))
        score = np.asarray(rollout(cfg, iface, big, X3.WORLDS, X3.RUN_SEED, device, chunk_worlds=4096).score)
    committed = np.asarray(rec["fitness"]["T1-M0"], dtype=np.float32)[: big.n_strains]
    diff = np.abs(score.astype(np.float64) - committed.astype(np.float64))
    out["verification"] = {"graph": VERIFY, "genomes": int(big.n_strains), "unequal_values": int((diff > 0).sum()),
                           "max_difference": float(diff.max()), "bit_equal": bool((diff == 0).all())}
    if not out["verification"]["bit_equal"] and not smoke:
        out["dropped"] = "the replay is not bit-equal to pilot.json, so step 0 is dropped (DESIGN.md §7.2)"
        return out

    # 2. H and S on the same genomes, against the committed fitness, under level
    for name in names:
        rec = records[name]
        cfg = cfg_t1(name, tuple(rec["gains"]))
        with acct.category("measure"):
            g = genomes_of(con, name, cfg, 256, device)
            if smoke:
                g = g.select(list(range(n_genomes)))
            hist = history(g, cfg, iface, bank)
        fit = np.asarray(rec["fitness"]["T1-M0"], dtype=np.float64)[: g.n_strains].mean(axis=1)
        H = np.abs(hist["raw_turn"]["final"])
        S = np.abs(hist["raw_turn"]["steady_contrast"])
        rho, flag = partial_spearman(H, fit, S)
        q = np.argsort(H, kind="stable")
        k = max(1, len(q) // 4)
        out["graphs"][name] = {"rho_level": rho, "degenerate": flag,
                               "top_minus_bottom_quartile_fitness": float(fit[q[-k:]].mean() - fit[q[:k]].mean()),
                               "H_mean": float(H.mean()), "S_mean": float(S.mean()), "fitness_mean": float(fit.mean())}
    rhos = np.array([r["rho_level"] for r in out["graphs"].values()])
    out["summary"] = {"graphs": len(rhos), "mean_rho_level": float(rhos.mean()),
                      "between_graph_sd_rho_level": float(rhos.std(ddof=1)) if len(rhos) > 1 else None,
                      "positive": int((rhos > 0).sum())}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)
    prov = reg.provenance(GUARDED)
    if not args.smoke:
        if prov["dirty"]:
            raise SystemExit("uncommitted changes in the guarded files: commit first")
        reg.require_pins(prov)
        if not torch.cuda.is_available():
            raise SystemExit("step 0 runs on CUDA (03's genomes were drawn by a CUDA generator)")
    out_dir = ROOT / "runs" / ("e03h-smoke" if args.smoke else "e03h") / "step0"
    rec = (out_dir / "step0.json") if args.smoke else (EXP / "development-records" / "step0.json")
    t0 = time.time()
    with acct.recorded(out_dir / "compute", out_dir / "compute.json", default="measure", experiment="03h",
                       stage="step0", script="scripts/e03h_step0.py"):
        doc = run(args.smoke)
    doc.update({"provenance": prov, "seconds": time.time() - t0})
    reg.write_json(rec, doc, atomic=True)
    print(f"step 0: {json.dumps(doc.get('summary', doc.get('dropped')))} -> {rec}")
    return doc


if __name__ == "__main__":
    main()
