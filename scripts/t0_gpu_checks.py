"""T0's GPU checks, v2 (docs/foundations/T0.md v2.1 sections 1, 2, 4 and 6; D079, D081, D082).

    python scripts/t0_gpu_checks.py [--device cuda] [--quick]

Writes docs/foundations/T0_gpu.json. The code provenance (commit, and whether the tree is dirty)
is recorded at the **start**, and the script refuses to run from a dirty tree unless `--quick`.

1. **Batch composition, separated from repeats** (the D081 review):
   - `repeat`: the same genomes, worlds and chunking, run 3 times, in default CUDA and in
     `replay_mode`;
   - `chunking`: the same set under chunkings giving 1, 2, 3, 4, 16 and 32 strains per chunk, plus
     a remainder chunk of one strain;
   - for each: the maximum per-world |d score|, and the number of worlds exceeding the declared
     1e-4.
   It is run at 02-T0 and 02-T1 settings (200 ticks), for random genomes and **02's** evolved
   champions (8 N2 runs per cell, at their own brain configuration with 32 substeps), plus a
   labelled 600-tick stress test.
2. **The cause:** `torch.bmm` for a batch of one strain against the same strain inside larger
   batches, at the row counts the world uses.
3. **Identity:** scores are identical with per-tick ledger tracking on and off, and with
   accounting on and off.
4. **The CUDA ledger bound and finiteness:** N2, SH and RD, 8 worlds, 02-T0 and 02-T1, with
   per-tick tracking. The relative error must be below 1e-5, and scores and energies finite.
5. **Historical replay:** 01b champions against their stored `holdout_score`. **Deviation from the
   plan:** it runs at current code, not the original code version, and 01b's bundle records
   `git_dirty: true`, so the original executed source cannot be checked out exactly.
6. **Single-island regression:** 01b's N2-run00, generations 0-2 at current code, against its log.
"""

from __future__ import annotations

import argparse
import json
import subprocess
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
RUN02 = ROOT / "runs" / "exp02-screening"
DECLARED_TOL = 1e-4
STRAINS_PER_CHUNK = (1, 2, 3, 4, 16, 32)


def provenance() -> dict:
    def git(*a):
        return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
    return {"git_commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain", "--", "wormwars", "scripts", "configs"))}


class _Null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _to(g: Genome, device) -> Genome:
    return Genome(g.spec.to(device), g.cfg, **{k: None if v is None else v.to(device) for k, v in g.params().items()})


def _scores(cfg, iface, g, ids, seed, device, chunk):
    return rollout(cfg, iface, g, ids, run_seed=seed, device=device, chunk_worlds=chunk).score


def _cohort(kind, task, spec, n):
    """Random genomes at the task's brain configuration, or 02's N2 champions for the task (their
    own configuration and gains)."""
    cfg = grid.task_config(Config(), task)
    if kind == "random":
        return Genome.random(spec, cfg.brain, n, generator=torch.Generator().manual_seed(1)), cfg
    files = sorted(RUN02.glob(f"{task}-M0-N2-run*-g39.npz"))[:n]
    gs, metas = zip(*[load_genome(f, spec) for f in files])
    cfg, _ = apply_world_meta(cfg, metas[0])
    cfg.brain = gs[0].cfg
    assert cfg.brain.substeps == 32, cfg.brain.substeps
    return Genome.cat(list(gs)), cfg


def _diffs(ref, other):
    d = np.abs(other - ref)
    return {"max_abs_diff": float(d.max()), "worlds_over_1e-4": int((d > DECLARED_TOL).sum()),
            "worlds": int(d.size)}


def check_composition(con, iface, device, quick):
    spec = BrainSpec.from_connectome(con)
    n_strains, n_worlds = (4, 4) if quick else (32, 16)
    out = {}
    for task, ticks, label in (("T0", 200, "02-T0"), ("T1", 200, "02-T1"), ("T1", 600, "02-T1 600-tick stress")):
        for kind in ("random", "02-champions"):
            g, cfg = _cohort("random" if kind == "random" else "champions", task, spec,
                             n_strains if kind == "random" else (4 if quick else 8))
            cfg.world.max_ticks = ticks
            g = _to(g, device)
            ids = np.arange(n_worlds)
            row = {"strains": g.n_strains, "worlds_per_strain": n_worlds, "ticks": ticks,
                   "substeps": cfg.brain.substeps}
            refs = {}
            for mode in ("default", "replay_mode"):
                with (replay_mode(warn=True) if mode == "replay_mode" else _Null()):
                    ref = refs[mode] = _scores(cfg, iface, g, ids, 3, device, 4096)
                    row[f"{mode} repeat"] = max((_diffs(ref, _scores(cfg, iface, g, ids, 3, device, 4096))
                                                 for _ in range(2)), key=lambda x: x["max_abs_diff"])
                    for k in STRAINS_PER_CHUNK:
                        if k <= g.n_strains:
                            row[f"{mode} chunking {k} strain(s) per chunk"] = _diffs(
                                ref, _scores(cfg, iface, g, ids, 3, device, k * n_worlds))
                    if g.n_strains > 2:  # the last chunk holds a single strain
                        k = g.n_strains - 1
                        row[f"{mode} chunking {k} + remainder of 1"] = _diffs(
                            ref, _scores(cfg, iface, g, ids, 3, device, k * n_worlds))
            row["replay vs default, same chunking"] = _diffs(refs["default"], refs["replay_mode"])
            out[f"{label} / {kind}"] = row
    return out


def check_bmm(device):
    torch.manual_seed(0)
    out = {}
    for rows in (16, 64, 320):  # worlds x weys per strain, as the world batches them
        v = torch.randn(4, rows, 302, device=device)
        m = torch.randn(4, 302, 302, device=device)
        full = torch.bmm(v, m)
        out[f"{rows} rows"] = {
            "single strain vs batch of 4": float((torch.bmm(v[:1], m[:1]) - full[:1]).abs().max()),
            "batch of 2 vs batch of 4": float((torch.bmm(v[:2], m[:2]) - full[:2]).abs().max())}
    return out


def check_identity(con, iface, device):
    cfg = grid.task_config(Config(), "T1")
    g = _to(Genome.random(BrainSpec.from_connectome(con), cfg.brain, 4, generator=torch.Generator().manual_seed(2)), device)
    ids = np.arange(8)
    with replay_mode(warn=True):
        off = _scores(cfg, iface, g, ids, 4, device, 4096)
        on_cfg = cfg.copy()
        on_cfg.world.check_ledger_every_tick = True
        on = _scores(on_cfg, iface, g, ids, 4, device, 4096)
        acct.LEDGER.enabled = False
        try:
            no_acct = _scores(cfg, iface, g, ids, 4, device, 4096)
        finally:
            acct.LEDGER.enabled = True
    return {"ledger_tracking_identical": bool(np.array_equal(off, on)),
            "accounting_identical": bool(np.array_equal(off, no_acct))}


def check_ledger_cuda(con, device):
    out = {}
    for name, graph in (("N2", con), ("SH", shuffled(con, seed=11)), ("RD", random_graph(con, seed=12))):
        for task in ("T0", "T1"):
            cfg = grid.task_config(Config(), task)
            cfg.world.check_ledger_every_tick = True
            g = _to(Genome.random(BrainSpec.from_connectome(graph), cfg.brain, 1,
                                  generator=torch.Generator().manual_seed(3)), device)
            r = rollout(cfg, load_interface(graph), g, np.arange(8), run_seed=4, device=device)
            out[f"{name} {task}"] = {"ledger_rel_error_per_tick_max": r.ledger_rel_error,
                                     "below_1e-5": bool(r.ledger_rel_error < 1e-5),
                                     "finite": bool(np.isfinite(r.score).all() and np.isfinite(r.energy).all())}
    return out


def check_historical(con, device, quick):
    bundle = json.loads((RUN01B / "bundle.json").read_text(encoding="utf-8"))
    base = Config.from_dict(bundle["config"])
    graphs = {"N2": con, "SH1": shuffled(con, seed=1, label="SH1"), "RD1": random_graph(con, seed=1, label="RD1")}
    out = {"_note": "at current code, not 01b's; 01b's bundle records git_dirty: true (deviation)"}
    for fam, graph in graphs.items():
        spec, iface = BrainSpec.from_connectome(graph, device=device), load_interface(graph)
        for run in (("run00",) if quick else ("run00", "run01", "run02")):
            champ, meta = load_genome(RUN01B / f"champion-{fam}-{run}.npz", spec, device=device)
            cfg, _ = apply_world_meta(base, meta)
            cfg.brain = champ.cfg
            ids = SeedPool(cfg, meta["run_seed"]).holdout
            got = float(rollout(cfg, iface, champ, ids, meta["run_seed"], device).per_strain()[0])
            out[f"{fam}-{run}"] = {"replayed": got, "stored": meta["holdout_score"],
                                   "exact": got == meta["holdout_score"]}
    sh2 = shuffled(con, seed=2, label="SH1")  # the wrong graph under SH1's label: a control
    champ, meta = load_genome(RUN01B / "champion-SH1-run00.npz", BrainSpec.from_connectome(sh2, device=device), device=device)
    cfg, _ = apply_world_meta(base, meta)
    cfg.brain = champ.cfg
    out["control: SH1 champion on the SH2 graph"] = {
        "replayed": float(rollout(cfg, load_interface(sh2), champ, SeedPool(cfg, meta["run_seed"]).holdout,
                                  meta["run_seed"], device).per_strain()[0]),
        "stored": meta["holdout_score"]}
    return out


def check_regression(con, device, quick):
    bundle = json.loads((RUN01B / "bundle.json").read_text(encoding="utf-8"))
    cfg = Config.from_dict(bundle["config"])
    meta = json.loads(str(np.load(RUN01B / "champion-N2-run00.npz", allow_pickle=False)["meta"]))
    cfg, _ = apply_world_meta(cfg, meta)
    cfg.brain.chem_direction = meta["brain_config"].get("chem_direction", cfg.brain.chem_direction)
    cfg.evo.generations = 2 if quick else 3
    log = json.loads((RUN01B / "N2-run00-log.json").read_text(encoding="utf-8"))
    r = evolve(cfg, load_interface(con), BrainSpec.from_connectome(con, device=device), run=0,
               run_seed=meta["run_seed"], device=device, verbose=False,
               holdout_every=max(1, bundle["extra"]["args"]["generations"] // 5))
    rows = [{"generation": g.generation, "best": g.best, "stored_best": log[g.generation]["best"],
             "mean": g.mean, "stored_mean": log[g.generation]["mean"],
             "same_best_nickname": g.best_nickname == log[g.generation]["best_nickname"]} for g in r.log]
    return {"generations": rows,
            "pass": all(x["best"] == x["stored_best"] and x["mean"] == x["stored_mean"] and x["same_best_nickname"]
                        for x in rows)}


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--quick", action="store_true", help="tiny sizes, for a smoke test")
    ap.add_argument("--result", default=str(ROOT / "docs" / "foundations" / "T0_gpu.json"))
    args = ap.parse_args()
    prov = provenance()  # at the start (D082)
    if prov["dirty"] and not args.quick:
        raise SystemExit("uncommitted changes in wormwars/, scripts/ or configs/: commit before the real run")
    con = load_connectome()
    iface = load_interface(con)
    t0 = time.perf_counter()
    res = {"provenance_at_start": prov, "device": args.device,
           "cuda": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
           "torch": torch.__version__, "quick": args.quick, "declared_tolerance": DECLARED_TOL}
    with acct.category("measure"):
        res["composition"] = check_composition(con, iface, args.device, args.quick)
        res["bmm_cause"] = check_bmm(args.device)
        res["identity"] = check_identity(con, iface, args.device)
        res["ledger_cuda"] = check_ledger_cuda(con, args.device)
        res["historical"] = check_historical(con, args.device, args.quick)
        res["single_island_regression"] = check_regression(con, args.device, args.quick)
    res["seconds"] = time.perf_counter() - t0
    Path(args.result).parent.mkdir(parents=True, exist_ok=True)
    Path(args.result).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "composition"}, indent=1)[:4000])


if __name__ == "__main__":
    from wormwars.accounting import run_script
    run_script(main, out_default=str(ROOT / "runs" / "t0-gpu"), default="measure", name="t0_gpu_checks")
