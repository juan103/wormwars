"""T1's profile (docs/foundations/T1.md v2, section 4, T1.1; D086).

    python scripts/t1_profile.py [--device cuda] [--quick]

Writes docs/foundations/T1_profile.json. The code provenance is recorded at the start, and the
script refuses to run from a dirty tree unless `--quick` (as the T0 GPU checks do).

**Timing rules:** synchronised wall-clock time is the authority. Each timing is warmed up at the
same shape and repeated (5 times; 2 with `--quick`), reporting the median and the range, with the
ticks actually executed. Peak allocated and reserved memory are recorded, and so are the TF32 and
deterministic settings.

The workload is 02's task T1 with N2 (302 neurons, 20 weys, 32 substeps, 200 ticks), plus a Task N
proxy: the same with one wey per world and 300 ticks. Task N itself is not built yet (E1).

1. `throughput`: whole rollouts at several chunk sizes, several runs' populations in one batch,
   and single-strain shapes (checkpoints: 1 x 16 worlds; hold-outs: 1 x 64).
2. `concurrency`: 1 to 4 processes at once.
3. `world`: the tick with a scripted controller (no neural work) against the tick with a brain; the
   tick's parts, each timed between synchronisations; the two per-tick host syncs, by removing them
   in a diagnostic copy of the world (never in production); world construction.
4. `short_run`: a 02-style single-island run of 5 generations with checkpoints and a final
   hold-out, by accounting category.
5. `replay_mode_cost`: the same rollout in default mode and in `replay_mode(warn=False)`.
6. `sparsity`, and `levers`: the brain step by each formulation of section 2, against the current
   step, with the maximum difference and whether two identical calls agree. The current step is
   timed again at the end of each row.
7. `profiler`, last: kernel share of the top operations, CPU and kernel time, launches.
"""

from __future__ import annotations

import argparse
import json
import os
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
from wormwars import world as world_mod  # noqa: E402
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.evo import SeedPool, evolve, rollout  # noqa: E402
from wormwars.evo.bundle import replay_mode  # noqa: E402
from wormwars.evo.rollout import rollout_brain  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.exp02.scripted import ScriptedBrain, Straight  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402
from wormwars.world import World  # noqa: E402

REPS = 5


def provenance() -> dict:
    def git(*a):
        return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
    return {"git_commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain", "--", "wormwars", "scripts", "configs"))}


def configs() -> dict:
    t1 = grid.brain_config_for_graph(grid.task_config(Config(), "T1"), "N2")
    proxy = t1.copy()
    proxy.world.weys_per_swarm = 1
    proxy.world.max_ticks = 300
    return {"02-T1": t1, "task-N proxy": proxy}


def _genome(spec, cfg, n, device, seed=0):
    return Genome.random(spec, cfg.brain, n, generator=torch.Generator(device=device).manual_seed(seed),
                         device=device)


def _sync(device):
    if str(device).startswith("cuda"):
        torch.cuda.synchronize()


def _timed(fn, device, reps) -> dict:
    """Warm up once at this shape, then `reps` synchronised timings: median and range, in seconds."""
    fn()
    ts = []
    for _ in range(reps):
        _sync(device)
        t = time.perf_counter()
        fn()
        _sync(device)
        ts.append(time.perf_counter() - t)
    return {"median_s": statistics.median(ts), "min_s": min(ts), "max_s": max(ts), "reps": reps}


def _rate(cfg, iface, g, ids, device, reps, chunk=None, ticks=None) -> dict:
    ran = {}

    def go():
        r = rollout(cfg, iface, g, ids, run_seed=1, device=device, chunk_worlds=chunk, ticks=ticks)
        ran["ticks"] = r.ticks
    t = _timed(go, device, reps)
    n = g.n_strains * len(ids)
    return {"strain_worlds_per_s": n / t["median_s"], "range": [n / t["max_s"], n / t["min_s"]],
            "ticks_executed": ran["ticks"], "strains": g.n_strains, "worlds_per_strain": len(ids),
            "chunk_worlds": chunk or cfg.evo.chunk_worlds, **t}


def _memory(device) -> dict | None:
    if not str(device).startswith("cuda"):
        return None
    return {"peak_allocated_gib": torch.cuda.max_memory_allocated() / 2**30,
            "peak_reserved_gib": torch.cuda.max_memory_reserved() / 2**30}


def _reset_memory(device):
    if str(device).startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()


def throughput(cfgs, iface, spec, device, quick, reps) -> dict:
    ticks = 20 if quick else None
    out = {}
    for name, cfg in cfgs.items():
        row = {"ticks": ticks or cfg.world.max_ticks, "substeps": cfg.brain.substeps,
               "weys": cfg.world.weys_per_swarm}
        g = _genome(spec, cfg, 32, device)
        row["chunk"] = {str(c): _rate(cfg, iface, g, np.arange(64), device, reps, c, ticks)
                        for c in (256, 512, 1024, 2048)}
        row["runs_batched"] = {}
        for r in (1, 2, 4, 8):
            gr = _genome(spec, cfg, 32 * r, device)
            _reset_memory(device)
            row["runs_batched"][str(r)] = {**_rate(cfg, iface, gr, np.arange(8), device, reps, 256 * r, ticks),
                                           "memory": _memory(device)}
        one = _genome(spec, cfg, 1, device)
        row["single_strain"] = {"checkpoint 1 x 16": _rate(cfg, iface, one, np.arange(16), device, reps, None, ticks),
                                "hold-out 1 x 64": _rate(cfg, iface, one, np.arange(64), device, reps, None, ticks)}
        out[name] = row
    return out


def concurrency(device, quick) -> dict:
    """1 to 4 copies of the evolution-sized workload at once; the total rate for each count."""
    out = {}
    for n in (1, 2, 3, 4):
        cmd = [sys.executable, str(Path(__file__)), "--worker", "--device", device] + (["--quick"] if quick else [])
        # each worker counts its own work; the parent merges the counts (D091)
        ledgers = [ROOT / "runs" / "t1-profile" / f"worker-{n}-{i}-ledger.json" for i in range(n)]
        ledgers[0].parent.mkdir(parents=True, exist_ok=True)
        procs = [subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True,
                                  env={**os.environ, acct.CHILD_LEDGER_ENV: str(path)}) for path in ledgers]
        rates = [float(p.communicate()[0].strip().splitlines()[-1]) for p in procs]
        for path in ledgers:
            acct.merge_child_ledger(path)
        out[str(n)] = {"per_process": rates, "total": sum(rates)}
    return out


def worker(device, quick):
    cfg = configs()["02-T1"]
    con = load_connectome()
    iface = load_interface(con)
    g = _genome(BrainSpec.from_connectome(con, device=device), cfg, 32, device)
    rollout(cfg, iface, g, np.arange(8), run_seed=1, device=device, ticks=5)
    reps, ticks = (2, 20) if quick else (6, None)
    _sync(device)
    t = time.perf_counter()
    for i in range(reps):
        rollout(cfg, iface, g, np.arange(8) + 8 * i, run_seed=1, device=device, ticks=ticks)
    _sync(device)
    print(32 * 8 * reps / (time.perf_counter() - t))
    acct.write_child_ledger()


def _scripted(cfg, iface, n, device):
    return ScriptedBrain(iface, n, Straight(), cfg.world.forward_gain, cfg.world.turn_gain,
                         n_strains=32, device=device)


class _Parts:
    """Times named World methods between synchronisations, per tick. Diagnostic: the syncs it adds
    change the overlap it measures, so the parts' sum is reported beside the unwrapped tick."""

    NAMES = ("sample_points", "_sensed_food", "_sensor_signals", "_build_current", "_read_motors",
             "_eat", "_reap", "_update_fields", "done")

    def __init__(self, device):
        self.device, self.t, self.saved = device, {}, {}

    def __enter__(self):
        for name in self.NAMES:
            orig = getattr(World, name)
            self.saved[name] = orig
            setattr(World, name, self._wrap(name, orig))
        orig_dd = world_mod.diffuse_decay
        self.saved["diffuse_decay"] = orig_dd
        world_mod.diffuse_decay = self._wrap("pheromone diffuse_decay (inside _update_fields)", orig_dd)
        return self

    def _wrap(self, name, fn):
        def inner(*a, **k):
            _sync(self.device)
            t = time.perf_counter()
            r = fn(*a, **k)
            _sync(self.device)
            self.t[name] = self.t.get(name, 0.0) + time.perf_counter() - t
            return r
        return inner

    def __exit__(self, *a):
        world_mod.diffuse_decay = self.saved.pop("diffuse_decay")
        for name, orig in self.saved.items():
            setattr(World, name, orig)
        return False


class _NoSync:
    """A diagnostic copy of the world without its two per-tick host syncs: `_reap` runs its body
    unconditionally, and `done` checks only the tick count. With nobody dying the result is the same;
    it is never used in production."""

    def __enter__(self):
        self.saved = {"_reap": World._reap, "done": World.done}

        def reap(w):
            dying = w.alive & (w.energy <= 0)
            mass = torch.full_like(w.energy, w.cfg.world.body_mass) * dying.to(w.dtype)
            world_mod.splat_into(w.fields, w.ch.PELLET, w.pos.reshape(w.n_worlds, -1, 2),
                                 mass.reshape(w.n_worlds, -1))
            w.alive &= ~dying
            w.energy = w.energy * w.alive.to(w.dtype)

        World._reap = reap
        World.done = lambda w: w.tick_count >= w.cfg.world.max_ticks
        return self

    def __exit__(self, *a):
        for k, v in self.saved.items():
            setattr(World, k, v)
        return False


def world_share(cfgs, iface, spec, device, quick, reps) -> dict:
    out = {}
    for name, cfg in cfgs.items():
        ticks = 20 if quick else cfg.world.max_ticks
        ids = np.arange(8)
        g = _genome(spec, cfg, 32, device)
        neural = _timed(lambda: rollout(cfg, iface, g, ids, 1, device, ticks=ticks), device, reps)
        sb = _scripted(cfg, iface, spec.n, device)
        scripted = _timed(lambda: rollout_brain(cfg, iface, sb, ids, 1, device, ticks=ticks), device, reps)
        with _NoSync():
            nosync = _timed(lambda: rollout(cfg, iface, g, ids, 1, device, ticks=ticks), device, reps)
        parts = _Parts(device)
        with parts:
            rollout(cfg, iface, g, ids, 1, device, ticks=ticks)
        build = _timed(lambda: World(cfg, iface, Brain(g),
                                     torch.arange(32, device=device).repeat_interleave(8).reshape(-1, 1),
                                     run_seed=1, world_ids=np.tile(ids, 32), device=device), device, reps)
        out[name] = {
            "batch": "32 strains x 8 worlds", "ticks": ticks,
            "tick_ms_with_brain": neural["median_s"] / ticks * 1e3,
            "tick_ms_scripted": scripted["median_s"] / ticks * 1e3,
            "world_share_estimate": scripted["median_s"] / neural["median_s"],
            "tick_ms_without_host_syncs (diagnostic)": nosync["median_s"] / ticks * 1e3,
            "parts_ms_per_tick (synchronised; diagnostic)": {k: v / ticks * 1e3 for k, v in parts.t.items()},
            "world_construction_ms": build["median_s"] * 1e3,
            "timings": {"with_brain": neural, "scripted": scripted, "without_host_syncs": nosync},
        }
    return out


def short_run(cfg, iface, spec, device, quick) -> dict:
    c = cfg.copy()
    c.evo.generations = 2 if quick else 5
    before = acct.LEDGER.snapshot()
    _sync(device)
    t = time.perf_counter()
    res = evolve(c, iface, spec, 0, 12345, device=device, holdout_every=10,
                 checkpoint_ids=grid.CHECKPOINT_IDS, snapshots=(), verbose=False)
    with acct.category("final"):
        rollout(c, iface, res.champion, SeedPool(c, 12345).holdout, 12345, device)
    _sync(device)
    return {"generations": c.evo.generations, "population": c.evo.population,
            "worlds_per_strain": c.evo.worlds_per_strain, "wall_s": time.perf_counter() - t,
            "by_category": acct.LEDGER.since(before)}


def replay_cost(cfg, iface, spec, device, quick, reps) -> dict:
    ticks = 20 if quick else None
    g = _genome(spec, cfg, 32, device)
    default = _rate(cfg, iface, g, np.arange(8), device, reps, None, ticks)
    with replay_mode(warn=False):
        replay = _rate(cfg, iface, g, np.arange(8), device, reps, None, ticks)
    return {"default": default, "replay_mode(warn=False)": replay,
            "slowdown": default["strain_worlds_per_s"] / replay["strain_worlds_per_s"]}


def profiler(cfg, iface, spec, device, quick) -> dict:
    if not str(device).startswith("cuda"):
        return {}
    from torch.profiler import ProfilerActivity, profile
    ticks = 20 if quick else 100
    g = _genome(spec, cfg, 32, device)
    rollout(cfg, iface, g, np.arange(8), run_seed=1, device=device, ticks=5)
    with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA]) as prof:
        rollout(cfg, iface, g, np.arange(8), run_seed=1, device=device, ticks=ticks)
        _sync(device)
    ev = prof.key_averages()
    # kernels only: an aten op and the kernel it launches both carry the same device time
    kernel_total = sum(e.self_device_time_total for e in ev if e.device_type == torch.autograd.DeviceType.CUDA)
    top = sorted((e for e in ev if e.key.startswith("aten::")), key=lambda e: -e.self_device_time_total)[:10]
    return {"ticks": ticks, "batch": "32 strains x 8 worlds",
            "cpu_self_ms": sum(e.self_cpu_time_total for e in ev) / 1e3, "kernel_ms": kernel_total / 1e3,
            "kernel_launches": sum(e.count for e in ev if e.key == "cudaLaunchKernel"),
            "top_ops": [{"op": e.key, "kernel_share": e.self_device_time_total / kernel_total, "calls": e.count}
                        for e in top],
            "note": "CPU time includes dispatch and waiting; it is not by itself evidence of a CPU limit (D086)"}


def sparsity(cfg, spec, device) -> dict:
    br = Brain(_genome(spec, cfg, 2, device))
    m, gm = br.W_drive[0] != 0, br.G[0] != 0
    return {"n": spec.n, "chem_synapses": int(spec.chem_i.numel()), "chem_density": m.float().mean().item(),
            "gap_density": gm.float().mean().item(), "chem_max_in_degree": int(m.sum(0).max()),
            "gap_max_in_degree": int(gm.sum(0).max())}


def _blockdiag(A, pattern, n):
    """A [S, n, n] with out_c += A[r, c] x_r, as one block-diagonal CSR matrix acting on x [S*n, B]."""
    S = A.shape[0]
    r, c = pattern.nonzero(as_tuple=True)
    rows = torch.cat([c + s * n for s in range(S)])
    cols = torch.cat([r + s * n for s in range(S)])
    return torch.sparse_coo_tensor(torch.stack([rows, cols]), A[:, r, c].reshape(-1),
                                   (S * n, S * n)).coalesce().to_sparse_csr()


def levers(cfg, spec, device, quick, reps) -> dict:
    """One brain tick (all substeps) by each formulation, against the current `Brain.step`."""
    K, n = cfg.brain.substeps, spec.n
    out = {}
    shapes = ((32, 160),) if quick else ((32, 160), (8, 1280), (64, 160))
    for S, B in shapes:
        br = Brain(_genome(spec, cfg, S, device, seed=1))
        gen = torch.Generator(device=device).manual_seed(2)
        v0 = torch.randn(S, B, n, device=device, generator=gen)
        cur = torch.randn(S, B, n, device=device, generator=gen) * 0.5
        base = br.step(v0, cur)
        t_base = _timed(lambda: br.step(v0, cur), device, reps)["median_s"]
        c, den = br.c.unsqueeze(1), br.den.unsqueeze(1)
        drive = br.bias.unsqueeze(1) + cur
        M, G = br.W_drive, br.G
        row = {"current": {"ms": t_base * 1e3, "speedup": 1.0, "max_diff": 0.0,
                           "repeat_identical": bool(torch.equal(base, br.step(v0, cur)))}}

        def record(name, fn):
            a, b = fn(), fn()
            t = _timed(fn, device, reps)["median_s"]
            row[name] = {"ms": t * 1e3, "speedup": t_base / t, "max_diff": (a - base).abs().max().item(),
                         "repeat_identical": bool(torch.equal(a, b))}

        MG = torch.cat([M, G], 1).contiguous()

        def fused():
            v = v0
            for _ in range(K):
                v = (v + c * (drive + torch.bmm(torch.cat([torch.tanh(v), v], -1), MG))) / den
            return v
        record("fused_gemm", fused)

        Mt, Gt = M.transpose(1, 2).contiguous(), G.transpose(1, 2).contiguous()

        def transposed():
            v = v0
            for _ in range(K):
                v = (v + c * (drive + torch.bmm(torch.tanh(v), Mt.transpose(1, 2))
                              + torch.bmm(v, Gt.transpose(1, 2)))) / den
            return v
        record("transposed_storage", transposed)

        if str(device).startswith("cuda"):
            sv = v0.clone()
            s = torch.cuda.Stream()
            s.wait_stream(torch.cuda.current_stream())
            with torch.cuda.stream(s):
                for _ in range(2):
                    br.step(sv, cur)
            torch.cuda.current_stream().wait_stream(s)
            graph = torch.cuda.CUDAGraph()
            with torch.cuda.graph(graph):
                gout = br.step(sv, cur)

            def graphed():
                graph.replay()
                return gout.clone()
            record("cuda_graph", graphed)

            torch.backends.cuda.matmul.allow_tf32 = True
            try:
                record("tf32", lambda: br.step(v0, cur))
            finally:
                torch.backends.cuda.matmul.allow_tf32 = False

        Ms = _blockdiag(M, (M != 0).any(0), n)
        Gs = _blockdiag(G, (G != 0).any(0), n)

        def tr(x):
            return x.transpose(1, 2).reshape(S * n, -1)

        def csr():
            v, cc, dd, dr = tr(v0), tr(c), tr(den), tr(drive)
            for _ in range(K):
                v = (v + cc * (dr + torch.sparse.mm(Ms, torch.tanh(v)) + torch.sparse.mm(Gs, v))) / dd
            return v.reshape(S, n, B).transpose(1, 2)
        record("cusparse_csr", csr)
        try:
            with replay_mode(warn=False):
                a, b = csr(), csr()
            row["cusparse_csr"]["replay_mode(warn=False)"] = {"raised": False, "repeat_identical": bool(torch.equal(a, b))}
        except RuntimeError as e:
            row["cusparse_csr"]["replay_mode(warn=False)"] = {"raised": True, "error": str(e)[:300]}

        for P in (304, 320, 384):
            Mp = torch.zeros(S, P, P, device=device)
            Mp[:, :n, :n] = M
            Gp = torch.zeros(S, P, P, device=device)
            Gp[:, :n, :n] = G

            def padded(Mp=Mp, Gp=Gp, P=P):
                v = torch.zeros(S, B, P, device=device)
                v[:, :, :n] = v0
                cp = torch.ones(S, 1, P, device=device)
                cp[:, :, :n] = c
                dp = torch.ones(S, 1, P, device=device)
                dp[:, :, :n] = den
                dr = torch.zeros(S, B, P, device=device)
                dr[:, :, :n] = drive
                for _ in range(K):
                    v = (v + cp * (dr + torch.bmm(torch.tanh(v), Mp) + torch.bmm(v, Gp))) / dp
                return v[:, :, :n]
            record(f"pad_n_{P}", padded)
        # the current step again, last, so a disturbed first timing shows up as a disagreement
        row["current_retimed"] = {"ms": _timed(lambda: br.step(v0, cur), device, reps)["median_s"] * 1e3}
        out[f"S{S}_B{B}"] = row
    return out


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--quick", action="store_true", help="tiny sizes, for a smoke test")
    ap.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--result", default=str(ROOT / "docs" / "foundations" / "T1_profile.json"))
    args = ap.parse_args()
    if args.worker:
        with acct.category("measure"):  # the worker's counts under "measure" when merged (D091)
            return worker(args.device, args.quick)
    prov = provenance()  # at the start
    if prov["dirty"] and not args.quick:
        raise SystemExit("uncommitted changes in wormwars/, scripts/ or configs/: commit before the real run")
    reps = 2 if args.quick else REPS
    con = load_connectome()
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con, device=args.device)
    cfgs = configs()
    t0 = time.perf_counter()
    res = {"provenance_at_start": prov, "device": args.device,
           "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
           "torch": torch.__version__, "cuda": torch.version.cuda, "quick": args.quick, "repeats": reps,
           "settings": {"allow_tf32_matmul": torch.backends.cuda.matmul.allow_tf32,
                        "allow_tf32_cudnn": torch.backends.cudnn.allow_tf32,
                        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled()},
           "workloads": {k: {"weys": c.world.weys_per_swarm, "ticks": c.world.max_ticks,
                             "substeps": c.brain.substeps} for k, c in cfgs.items()}}
    with acct.category("measure"):
        res["throughput"] = throughput(cfgs, iface, spec, args.device, args.quick, reps)
        res["concurrency"] = concurrency(args.device, args.quick)
        res["world"] = world_share(cfgs, iface, spec, args.device, args.quick, reps)
        res["replay_mode_cost"] = replay_cost(cfgs["02-T1"], iface, spec, args.device, args.quick, reps)
        res["sparsity"] = sparsity(cfgs["02-T1"], spec, args.device)
        res["levers"] = levers(cfgs["02-T1"], spec, args.device, args.quick, reps)
    res["short_run"] = {k: short_run(c, iface, spec, args.device, args.quick) for k, c in cfgs.items()}
    # last: in the first full run (e8faf26) the brain-step timing taken right after the profiler
    # was 4x slower than every other measurement of it, so nothing is timed after it now
    with acct.category("measure"):
        res["profiler"] = profiler(cfgs["02-T1"], iface, spec, args.device, args.quick)
    res["seconds"] = time.perf_counter() - t0
    Path(args.result).parent.mkdir(parents=True, exist_ok=True)
    Path(args.result).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("provenance_at_start", "world", "replay_mode_cost")}, indent=1,
                     default=str)[:5000])


if __name__ == "__main__":
    if "--worker" in sys.argv:
        main()
    else:
        from wormwars.accounting import run_script
        run_script(main, out_default=str(ROOT / "runs" / "t1-profile"), default="measure", name="t1_profile")
