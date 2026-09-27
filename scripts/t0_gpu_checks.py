"""T0's GPU checks (docs/foundations/T0.md v2.1, sections 1, 4 and 6; D065-D076).

    python scripts/t0_gpu_checks.py [--device cuda] [--quick]

Runs after 03r frees the GPU and writes docs/foundations/T0_gpu.json. The checks, as declared
before measuring in T0.md:
1. **replay_mode exactness:** the same genomes and worlds, run twice under `replay_mode()`, and
   under two chunkings, give identical per-world scores.
2. **Default-CUDA tolerance:** the same comparisons outside `replay_mode`, 3 repeats. Declared
   bound: per-world |d score| <= 1e-4 for random genomes, and provisionally for champions. An
   exceedance is a finding, reported with its distribution, never a silently widened bound. At
   experiment 02's 02-T0 and 02-T1 settings (200 ticks), plus a labelled 600-tick stress test.
3. **CUDA ledger and accounting identity:** scores are identical with per-tick ledger tracking
   on and off, and with the compute ledger enabled and disabled.
4. **Historical replay:** 01b champions (N2, SH1, RD1) replayed on their recorded settings and
   hold-out worlds, against the stored `holdout_score`. 01b ran default CUDA, so the comparison
   uses a tolerance and reports the divergence. It also tests whether the SH1 and RD1 graphs
   rebuilt from their seeds are 01b's (D076): a wrong graph gives a very different score.
5. **Single-island regression:** the first generations of a published 01b run, from its bundle
   configuration and seed, against its stored log (best and mean per generation), with the
   default-CUDA caveat.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.connectome.graphs import random_graph, shuffled  # noqa: E402
from wormwars.evo import SeedPool, evolve, rollout  # noqa: E402
from wormwars.evo.bundle import replay_mode  # noqa: E402
from wormwars.evo.genomes import apply_world_meta, load_genome  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

RUN01B = ROOT / "runs" / "exp01b-direction-corrected"
DECLARED_TOL = 1e-4


def _to(g: Genome, device) -> Genome:
    return Genome(g.spec.to(device), g.cfg, **{k: None if v is None else v.to(device) for k, v in g.params().items()})


def _scores(cfg, iface, genome, ids, seed, device, chunk=None):
    return rollout(cfg, iface, genome, ids, run_seed=seed, device=device, chunk_worlds=chunk).score


def _champions(spec, n, device):
    files = sorted(RUN01B.glob("champion-N2-run*.npz"))[:n]
    return Genome.cat([load_genome(f, spec, device=device)[0] for f in files])


def check_exact_and_tolerance(con, iface, spec, device, quick):
    out = {}
    n_rand, n_champ, n_worlds, repeats = (4, 2, 4, 2) if quick else (32, 8, 16, 3)
    cpu_spec = spec.to("cpu")  # genomes are drawn with a CPU generator, then moved
    rand = Genome.random(cpu_spec, grid.task_config(Config(), "T1").brain, n_rand,
                         generator=torch.Generator().manual_seed(1))
    for task, ticks, label in (("T0", 200, "02-T0"), ("T1", 200, "02-T1"), ("T1", 600, "02-T1 600-tick stress")):
        cfg = grid.task_config(Config(), task)
        cfg.world.max_ticks = ticks
        ids = np.arange(n_worlds)
        for kind, g in (("random", rand.select(list(range(n_rand)))),
                        ("champions", _champions(cpu_spec, n_champ, "cpu"))):
            g = _to(g.with_params(), device)  # a clean copy on the device
            gcfg = cfg.copy()
            gcfg.brain = g.cfg if kind == "champions" else cfg.brain
            with replay_mode(warn=True):
                a = _scores(gcfg, iface, g, ids, 3, device, chunk=4096)
                b = _scores(gcfg, iface, g, ids, 3, device, chunk=4096)
                c = _scores(gcfg, iface, g, ids, 3, device, chunk=max(1, len(ids)))
            default = [_scores(gcfg, iface, g, ids, 3, device, chunk=4096) for _ in range(repeats)]
            default.append(_scores(gcfg, iface, g, ids, 3, device, chunk=max(1, len(ids))))
            dev = np.stack([np.abs(x - default[0]) for x in default[1:]])
            out[f"{label} / {kind}"] = {
                "replay_mode_repeat_identical": bool(np.array_equal(a, b)),
                "replay_mode_chunking_identical": bool(np.array_equal(a, c)),
                "default_cuda_max_abs_diff": float(dev.max()),
                "default_cuda_quantiles_abs_diff": [float(np.quantile(dev, q)) for q in (0.5, 0.9, 0.99, 1.0)],
                "within_declared_1e-4": bool(dev.max() <= DECLARED_TOL),
                "strains": g.n_strains, "worlds": len(ids), "ticks": ticks}
    return out


def check_identity(con, iface, spec, device):
    cfg = grid.task_config(Config(), "T1")
    g = _to(Genome.random(spec.to("cpu"), cfg.brain, 4, generator=torch.Generator().manual_seed(2)), device)
    ids = np.arange(8)
    with replay_mode(warn=True):
        off = _scores(cfg, iface, g, ids, 4, device)
        on_cfg = cfg.copy()
        on_cfg.world.check_ledger_every_tick = True
        on = _scores(on_cfg, iface, g, ids, 4, device)
        acct.LEDGER.enabled = False
        try:
            no_acct = _scores(cfg, iface, g, ids, 4, device)
        finally:
            acct.LEDGER.enabled = True
    return {"ledger_tracking_identical": bool(np.array_equal(off, on)),
            "accounting_identical": bool(np.array_equal(off, no_acct))}


def check_historical(con, device, quick):
    bundle = json.loads((RUN01B / "bundle.json").read_text(encoding="utf-8"))
    base = Config.from_dict(bundle["config"])
    graphs = {"N2": con, "SH1": shuffled(con, seed=1, label="SH1"), "RD1": random_graph(con, seed=1, label="RD1"),
              "SH2": shuffled(con, seed=2, label="SH2")}
    out = {}
    runs = ("run00",) if quick else ("run00", "run01", "run02")
    for fam in ("N2", "SH1", "RD1"):
        graph = graphs[fam]
        spec, iface = BrainSpec.from_connectome(graph, device=device), load_interface(graph)
        for run in runs:
            f = RUN01B / f"champion-{fam}-{run}.npz"
            if not f.exists():
                continue
            champ, meta = load_genome(f, spec, device=device)
            cfg, _ = apply_world_meta(base, meta)
            cfg.brain = champ.cfg
            ids = SeedPool(cfg, meta["run_seed"]).holdout
            rows = {}
            for mode in ("default", "replay_mode"):
                if mode == "replay_mode":
                    with replay_mode(warn=True):
                        got = float(rollout(cfg, iface, champ, ids, meta["run_seed"], device).per_strain()[0])
                else:
                    got = float(rollout(cfg, iface, champ, ids, meta["run_seed"], device).per_strain()[0])
                rows[mode] = {"replayed": got, "stored": meta["holdout_score"],
                              "abs_diff": abs(got - meta["holdout_score"])}
            out[f"{fam}-{run}"] = rows
    # a control for the rebuild question: SH1's champion on the wrong graph (SH2) must differ a lot
    f = RUN01B / "champion-SH1-run00.npz"
    spec2 = BrainSpec.from_connectome(graphs["SH2"], device=device)
    champ, meta = load_genome(f, spec2.__class__.from_connectome(graphs["SH2"].with_masks(
        graphs["SH2"].chem, graphs["SH2"].gap, "SH1"), device=device), device=device)
    cfg, _ = apply_world_meta(base, meta)
    cfg.brain = champ.cfg
    ids = SeedPool(cfg, meta["run_seed"]).holdout
    wrong = float(rollout(cfg, load_interface(graphs["SH2"]), champ, ids, meta["run_seed"], device).per_strain()[0])
    out["control: SH1 champion on the SH2 graph"] = {"replayed": wrong, "stored": meta["holdout_score"],
                                                     "abs_diff": abs(wrong - meta["holdout_score"])}
    return out


def check_single_island_regression(con, device, quick):
    bundle = json.loads((RUN01B / "bundle.json").read_text(encoding="utf-8"))
    cfg = Config.from_dict(bundle["config"])
    meta = json.loads(str(np.load(RUN01B / "champion-N2-run00.npz", allow_pickle=False)["meta"]))
    cfg, _ = apply_world_meta(cfg, meta)
    cfg.brain.chem_direction = meta["brain_config"].get("chem_direction", cfg.brain.chem_direction)
    gens = 2 if quick else 3
    cfg.evo.generations = gens
    log = json.loads((RUN01B / "N2-run00-log.json").read_text(encoding="utf-8"))
    spec = BrainSpec.from_connectome(con, device=device)
    r = evolve(cfg, load_interface(con), spec, run=0, run_seed=meta["run_seed"], device=device, verbose=False,
               holdout_every=max(1, bundle["extra"]["args"]["generations"] // 5))
    return [{"generation": g.generation, "best": g.best, "stored_best": log[g.generation]["best"],
             "mean": g.mean, "stored_mean": log[g.generation]["mean"],
             "best_nickname": g.best_nickname, "stored_best_nickname": log[g.generation]["best_nickname"]}
            for g in r.log]


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--quick", action="store_true", help="tiny sizes, for a smoke test")
    ap.add_argument("--result", default=str(ROOT / "docs" / "foundations" / "T0_gpu.json"))
    args = ap.parse_args()
    con = load_connectome()
    iface, spec = load_interface(con), BrainSpec.from_connectome(con, device=args.device)
    t0 = time.perf_counter()
    res = {"device": args.device, "cuda": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
           "torch": torch.__version__, "quick": args.quick, "declared_tolerance": DECLARED_TOL}
    with acct.category("measure"):
        res["exact_and_tolerance"] = check_exact_and_tolerance(con, iface, spec, args.device, args.quick)
        res["identity"] = check_identity(con, iface, spec, args.device)
        res["historical"] = check_historical(con, args.device, args.quick)
        res["single_island_regression"] = check_single_island_regression(con, args.device, args.quick)
    res["seconds"] = time.perf_counter() - t0
    Path(args.result).parent.mkdir(parents=True, exist_ok=True)
    Path(args.result).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "exact_and_tolerance"}, indent=1)[:3000])


if __name__ == "__main__":
    from wormwars.accounting import run_script
    run_script(main, out_default=str(ROOT / "runs" / "t0-gpu"), default="measure", name="t0_gpu_checks")
