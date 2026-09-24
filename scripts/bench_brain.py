"""Measurements that justify the brain's configuration.

1. Timestep refinement: how far the state at `substeps` is from a 32x-refined reference.
   This is what picks `BrainConfig.substeps` -- accuracy, not just stability.
2. Dense vs sparse: which formulation of the two matmuls is actually faster on this GPU.
3. Throughput: wey-ticks per second and peak VRAM.
"""

from __future__ import annotations

import argparse
import time

import torch

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import BrainConfig
from wormwars.connectome import load_connectome


def make(spec, cfg, kind, S=2, seed=11):
    gen = torch.Generator(device="cpu").manual_seed(seed)
    if kind == "extreme":
        return Genome(
            spec,
            cfg,
            w=torch.full((S, spec.n_chem), cfg.w_max),
            g=torch.full((S, spec.n_gap), cfg.g_max),
            tau=torch.full((S, spec.n), cfg.tau_min),
            bias=torch.full((S, spec.n), cfg.b_max),
        )
    genome = Genome.random(spec, cfg, S, generator=gen, device="cpu")
    if kind == "fast_tau":
        genome.tau.fill_(cfg.tau_min)
        genome.g.fill_(cfg.g_max)
    return genome


def refinement(spec, cfg, ticks=40):
    print(f"\n== timestep refinement ({ticks} ticks, reference = 32x the finest tested) ==")
    print(f"{'genome':<10} {'substeps':>8} {'dt':>7} {'max|dv|':>12} {'relative':>10}")
    for kind in ("random", "extreme", "fast_tau"):
        genome = make(spec, cfg, kind)
        brain = Brain(genome)
        S = genome.n_strains
        gen = torch.Generator().manual_seed(13)
        v0 = torch.randn(S, 4, spec.n, generator=gen) * 0.5
        cur = torch.randn(S, 4, spec.n, generator=gen)

        def run(sub):
            v = v0.clone()
            for _ in range(ticks):
                v = brain.step(v, cur, substeps=sub)
            return v

        ref = run(32 * 16)
        scale = max(ref.abs().max().item(), 1.0)
        for sub in (1, 2, 4, 8, 16):
            err = (run(sub) - ref).abs().max().item()
            print(f"{kind:<10} {sub:>8} {1 / sub:>7.3f} {err:>12.5f} {err / scale:>10.5f}")


class SparseBrain:
    """Sparse-CSR formulation of the same two matmuls, for the benchmark only."""

    def __init__(self, brain: Brain):
        s = 0
        # the oriented matrix the dense brain actually multiplies by, so both formulations
        # compute the same thing in either synapse direction (D031)
        self.W = brain.W_drive[s].t().contiguous().to_sparse_csr()
        self.G = brain.G[s].to_sparse_csr()
        self.c = brain.c[s]
        self.den = brain.den[s]
        self.bias = brain.bias[s]
        self.k = brain.cfg.substeps

    def step(self, v, cur):
        # v: [B, N]; sparse mm wants [N, B]
        drive = self.bias + cur
        for _ in range(self.k):
            # self.W holds W_drive^T, so this is (tanh v) @ W_drive, as in Brain.step
            chem = torch.sparse.mm(self.W, torch.tanh(v).t()).t()
            gap = torch.sparse.mm(self.G, v.t()).t()
            v = (v + self.c * (drive + chem + gap)) / self.den
        return v


def throughput(spec, cfg, device, strains, weys, ticks=200):
    print(f"\n== throughput on {device} ==")
    print(f"{'strains':>8} {'weys/str':>9} {'total weys':>11} {'ms/tick':>9} {'wey-ticks/s':>14} {'VRAM MB':>9}")
    for S in strains:
        for B in weys:
            torch.cuda.empty_cache() if device == "cuda" else None
            if device == "cuda":
                torch.cuda.reset_peak_memory_stats()
            gen = torch.Generator(device="cpu").manual_seed(0)
            genome = Genome.random(spec.to(device), cfg, S, generator=gen, device="cpu")
            genome = Genome(
                spec.to(device), cfg,
                genome.w.to(device), genome.g.to(device),
                genome.tau.to(device), genome.bias.to(device),
            )
            brain = Brain(genome)
            v = brain.initial_state(B)
            cur = torch.randn_like(v) * 0.2
            for _ in range(5):
                v = brain.step(v, cur)
            if device == "cuda":
                torch.cuda.synchronize()
            t0 = time.perf_counter()
            for _ in range(ticks):
                v = brain.step(v, cur)
            if device == "cuda":
                torch.cuda.synchronize()
            dt = (time.perf_counter() - t0) / ticks
            vram = torch.cuda.max_memory_allocated() / 2**20 if device == "cuda" else 0.0
            print(f"{S:>8} {B:>9} {S * B:>11} {dt * 1e3:>9.3f} {S * B / dt:>14,.0f} {vram:>9.1f}")
            del brain, genome, v, cur


def dense_vs_sparse(spec, cfg, device, weys=4096, ticks=100):
    print(f"\n== dense vs sparse, one strain, {weys} weys, {device} ==")
    gen = torch.Generator(device="cpu").manual_seed(0)
    genome = Genome.random(spec, cfg, 1, generator=gen, device="cpu")
    genome = Genome(spec.to(device), cfg, genome.w.to(device), genome.g.to(device),
                    genome.tau.to(device), genome.bias.to(device))
    brain = Brain(genome)
    v = brain.initial_state(weys)
    cur = torch.randn_like(v) * 0.2

    def timeit(fn, *a):
        for _ in range(5):
            fn(*a)
        if device == "cuda":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(ticks):
            fn(*a)
        if device == "cuda":
            torch.cuda.synchronize()
        return (time.perf_counter() - t0) / ticks

    dense_t = timeit(lambda: brain.step(v, cur))
    sp = SparseBrain(brain)
    v2, cur2 = v[0], cur[0]
    try:
        sparse_t = timeit(lambda: sp.step(v2, cur2))
    except RuntimeError as exc:
        print(f"sparse formulation failed: {exc}")
        return
    density = (spec.n_chem + 2 * spec.n_gap) / spec.n**2
    print(f"mask density      : {density:.3%}")
    print(f"dense  ms/tick    : {dense_t * 1e3:.3f}")
    print(f"sparse ms/tick    : {sparse_t * 1e3:.3f}")
    print(f"winner            : {'dense' if dense_t < sparse_t else 'sparse'} "
          f"({max(dense_t, sparse_t) / min(dense_t, sparse_t):.2f}x)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--skip-refinement", action="store_true")
    args = ap.parse_args()

    con = load_connectome()
    cfg = BrainConfig()
    spec = BrainSpec.from_connectome(con)
    print(con.summary())
    print(f"genome size: {spec.n_params} parameters "
          f"({spec.n_chem} W + {spec.n_gap} G + {spec.n} tau + {spec.n} bias)")
    print(f"config: substeps={cfg.substeps} dt={cfg.dt} tau in [{cfg.tau_min}, {cfg.tau_max}] "
          f"w_max={cfg.w_max} g_max={cfg.g_max} b_max={cfg.b_max}")

    if not args.skip_refinement:
        refinement(spec, cfg)
    dense_vs_sparse(spec, cfg, args.device)
    throughput(spec, cfg, args.device, strains=[1, 16, 64], weys=[256, 2048])


if __name__ == "__main__":
    main()
