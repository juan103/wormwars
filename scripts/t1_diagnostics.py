"""T1's diagnostics behind D090's explanations (docs/foundations/T1.md §6; D091).

    python scripts/t1_diagnostics.py [--device cuda] [--quick]

Writes docs/foundations/T1_diagnostics.json, with provenance at the start; refuses a dirty tree
unless `--quick`. Every statement in T1.md §6 about why single-strain cases differ rests on this
file or on the equivalence results (`T1_equivalence_*.json`).

1. `bmm_strain_count`: `torch.bmm` for the first S strains of a batch of 32, against the same
   strains inside the batch of 32, for S = 1, 2, 3, 4, 8, 16, at 1, 8, 16, 20, 32, 64, 160, 320 and
   1 280 rows per strain (random inputs; the connectome's size, 302).
2. `world_reduction`: each world's food total, `fields[:, FOOD].sum(dim=(1, 2))`, computed over the
   first n worlds of a batch, against the same worlds inside a batch of 2 048: real starting maps,
   and random fields. `eaten_cause`: whether a single strain's final food fields are bit-identical
   to its fields in a 2 048-world batch, and whether their per-world sums differ.
3. `remainder_chunk`: 256 random genomes x 8 worlds in chunks of 3 (a last chunk of one strain),
   with the switch off and on, against the same genomes in one chunk of 256.
4. `cpu_single_strain`: on the CPU, a brain batch of one against the same strain in a batch of 2
   and of 4, at 1, 5, 8, 16, 20 and 64 rows, with the switch off and on.
5. `padding_cost`: single-strain evaluations with the switch off and on (02-T1 checkpoint and
   hold-out shapes; the Task N proxy's), 5 repeats, median and range.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.evo import rollout  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402
from wormwars.world import World  # noqa: E402

ROWS = (1, 8, 16, 20, 32, 64, 160, 320, 1280)
STRAINS = (1, 2, 3, 4, 8, 16)


def provenance() -> dict:
    def git(*a):
        return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
    return {"git_commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain", "--", "wormwars", "scripts", "configs"))}


def _sync(device):
    if str(device).startswith("cuda"):
        torch.cuda.synchronize()


def _pad(g: Genome, on: bool) -> Genome:
    return g.with_params(cfg=dataclasses.replace(g.cfg, pad_single_strain=on))


def _diff(a: torch.Tensor, b: torch.Tensor) -> dict:
    d = (a - b).abs()
    return {"equal": bool(torch.equal(a, b)), "unequal": int((a != b).sum()), "max_abs_diff": float(d.max())}


def bmm_strain_count(device) -> dict:
    gen = torch.Generator(device="cpu").manual_seed(0)
    out = {}
    for rows in ROWS:
        v = torch.randn(32, rows, 302, generator=gen).to(device)
        m = torch.randn(32, 302, 302, generator=gen).to(device)
        full = torch.bmm(v, m)
        out[str(rows)] = {str(S): _diff(torch.bmm(v[:S], m[:S]), full[:S]) for S in STRAINS}
        out[str(rows)]["repeat_32"] = _diff(torch.bmm(v, m), full)
    return out


def world_reduction(con, iface, spec, device) -> dict:
    """Each world's food total over the first n worlds of a batch, against the same worlds inside a
    batch of 2 048 (the size in which the `eaten` differences appeared): real starting maps, and
    random fields of the same shape."""
    cfg = grid.task_config(Config(), "T1")
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(2))
    g = Genome(g.spec.to(device), g.cfg, **{k: None if v is None else v.to(device) for k, v in g.params().items()})
    world = World(cfg, iface, Brain(g), torch.zeros(2048, 1, dtype=torch.long, device=device), run_seed=3,
                  world_ids=np.arange(2048), device=device)
    maps = world.fields[:, world.ch.FOOD].contiguous()
    rand = torch.rand(maps.shape, generator=torch.Generator().manual_seed(5)).to(device)
    out = {}
    for name, food in (("starting_maps", maps), ("random_fields", rand)):
        full = food.sum(dim=(1, 2))
        out[name] = {str(n): _diff(food[:n].contiguous().sum(dim=(1, 2)), full[:n])
                     for n in (1, 2, 4, 8, 12, 15, 16, 20, 32, 64)}
    return out


def eaten_cause(con, iface, spec, device, quick) -> dict:
    """Where the single-strain `eaten` difference comes from (D091). 256 random genomes x 8 worlds,
    switch on, as one batch (2 048 worlds) and strain 0 alone (8 worlds): are the final food fields
    bit-identical (then only the per-world sum differs), and does each per-world sum depend on the
    batch it is computed in?"""
    t1 = grid.task_config(Config(), "T1")
    n = 16 if quick else 256
    g = Genome.random(spec, t1.brain, n, generator=torch.Generator().manual_seed(1))
    g = _pad(Genome(g.spec.to(device), g.cfg, **{k: None if v is None else v.to(device) for k, v in g.params().items()}), True)
    ids = np.arange(8)

    def final_food(genome):
        strain_of = torch.arange(genome.n_strains, device=device).repeat_interleave(len(ids)).reshape(-1, 1)
        w = World(t1, iface, Brain(genome), strain_of, run_seed=3, world_ids=np.tile(ids, genome.n_strains),
                  device=device)
        w.run(20 if quick else None)
        return w.fields[:, w.ch.FOOD].contiguous().clone()
    batch = final_food(g)[:8]
    alone = final_food(g.select([0]))
    return {"strains_in_batch": n, "worlds_alone": 8,
            "final_food_fields_bit_identical": _diff(alone, batch),
            "sum_alone_vs_sum_in_batch": _diff(alone.sum(dim=(1, 2)), final_food(g).sum(dim=(1, 2))[:8])}


def remainder_chunk(con, iface, spec, device, quick) -> dict:
    t1 = grid.task_config(Config(), "T1")
    n = 16 if quick else 256
    ticks = 20 if quick else None
    base = Genome.random(spec, t1.brain, n, generator=torch.Generator().manual_seed(1))
    base = Genome(base.spec.to(device), base.cfg, **{k: None if v is None else v.to(device) for k, v in base.params().items()})
    out = {"strains": n, "per_chunk": 3, "last_chunk_strains": n % 3}
    for label, on in (("off", False), ("on", True)):
        g = _pad(base, on)
        full = rollout(t1, iface, g, np.arange(8), 3, device, chunk_worlds=n * 8, ticks=ticks)
        by3 = rollout(t1, iface, g, np.arange(8), 3, device, chunk_worlds=3 * 8, ticks=ticks)
        out[label] = {f: _diff(torch.from_numpy(np.asarray(getattr(by3, f))), torch.from_numpy(np.asarray(getattr(full, f))))
                      for f in ("score", "energy", "eaten", "food_start")}
    return out


def cpu_single_strain(spec) -> dict:
    cfg = grid.task_config(Config(), "T1").brain
    gen = torch.Generator().manual_seed(4)
    out = {}
    for on in (False, True):
        g = _pad(Genome.random(spec, cfg, 4, generator=torch.Generator().manual_seed(3)), on)
        rows_out = {}
        for rows in (1, 5, 8, 16, 20, 64):
            cur = [torch.randn(4, rows, spec.n, generator=gen) * 0.5 for _ in range(3)]

            def run(genome, cs):
                br = Brain(genome)
                v = br.initial_state(rows)
                for c in cs:
                    v = br.step(v, c)
                return v
            alone = run(g.select([0]), [c[:1] for c in cur])
            rows_out[str(rows)] = {"vs_batch_2": _diff(alone, run(g.select([0, 1]), [c[:2] for c in cur])[:1]),
                                   "vs_batch_4": _diff(alone, run(g, cur)[:1])}
        out["on" if on else "off"] = rows_out
    return out


def padding_cost(con, iface, spec, device, quick) -> dict:
    reps = 2 if quick else 5
    t1 = grid.task_config(Config(), "T1")
    proxy = t1.copy()
    proxy.world.weys_per_swarm = 1
    proxy.world.max_ticks = 300
    one = Genome.random(spec, t1.brain, 1, generator=torch.Generator().manual_seed(7))
    one = Genome(one.spec.to(device), one.cfg, **{k: None if v is None else v.to(device) for k, v in one.params().items()})
    out = {}
    for name, cfg, worlds in (("02-T1 checkpoint 1 x 16", t1, 16), ("02-T1 hold-out 1 x 64", t1, 64),
                              ("proxy checkpoint 1 x 16", proxy, 16), ("proxy hold-out 1 x 64", proxy, 64)):
        row = {}
        for label, on in (("off", False), ("on", True)):
            g = _pad(one, on)
            ticks = 20 if quick else None
            rollout(cfg, iface, g, np.arange(worlds), 1, device, ticks=5)
            ts = []
            for _ in range(reps):
                _sync(device)
                t = time.perf_counter()
                rollout(cfg, iface, g, np.arange(worlds), 1, device, ticks=ticks)
                _sync(device)
                ts.append(time.perf_counter() - t)
            row[label] = {"median_s": statistics.median(ts), "min_s": min(ts), "max_s": max(ts), "reps": reps}
        row["slowdown"] = row["on"]["median_s"] / row["off"]["median_s"]
        out[name] = row
    return out


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--result", default=str(ROOT / "docs" / "foundations" / "T1_diagnostics.json"))
    args = ap.parse_args()
    prov = provenance()
    if prov["dirty"] and not args.quick:
        raise SystemExit("uncommitted changes in wormwars/, scripts/ or configs/: commit before the real run")
    con = load_connectome()
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con)
    t0 = time.perf_counter()
    res = {"provenance_at_start": prov, "device": args.device, "torch": torch.__version__,
           "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None, "quick": args.quick}
    with acct.category("measure"):
        res["bmm_strain_count"] = bmm_strain_count(args.device)
        res["world_reduction"] = world_reduction(con, iface, spec, args.device)
        res["eaten_cause"] = eaten_cause(con, iface, spec, args.device, args.quick)
        res["remainder_chunk"] = remainder_chunk(con, iface, spec, args.device, args.quick)
        res["cpu_single_strain"] = cpu_single_strain(spec)
        res["padding_cost"] = padding_cost(con, iface, spec, args.device, args.quick)
    res["seconds"] = time.perf_counter() - t0
    Path(args.result).parent.mkdir(parents=True, exist_ok=True)
    Path(args.result).write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("provenance_at_start", "remainder_chunk", "padding_cost")}, indent=1)[:4000])


if __name__ == "__main__":
    from wormwars.accounting import run_script
    run_script(main, out_default=str(ROOT / "runs" / "t1-diagnostics"), default="measure", name="t1_diagnostics")
