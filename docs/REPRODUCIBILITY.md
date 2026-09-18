# Reproducibility: what is claimed and what is not

## Two different things called "replay"

**Replay means playback of recorded trajectories.** `wormwars.recorder.Recorder` is switched on for
chosen worlds and stores positions, headings, energies, pump values, the alive mask, the fields, and
optionally neuron activity, per tick. `wormwars.viewer` draws it back. A replay is exact because it
is a recording: nothing is recomputed.

**Re-simulation from a run bundle is a separate, best-effort thing.** Given a bundle you can rebuild
the same configuration, the same genomes and the same world seeds, and run the simulation again. How
close the result comes depends on where you run it.

## What is exactly reproducible

- **Map generation, spawn positions and hazard placement.** Derived per world from
  `world_seed(run_seed, world_id)` (splitmix64), using numpy on the CPU. A world's map depends only
  on `(run_seed, world_id)` -- never on the batch it was simulated in, how many worlds shared the
  GPU, or the chunk size. There is a test for this.
- **Which training seeds a generation used.** Drawn from `default_rng([run_seed, generation,
  0xC0FFEE])`, so a run's schedule is reproducible without being stored.
- **Held-out seeds.** A fixed range disjoint from the training range.
- **Chunking.** Splitting a rollout to fit memory does not change *which world a strain plays* or
  *how it is generated*, so it is a memory strategy and not an approximation. On the CPU the scores
  are bit-identical (measured: max |score difference| exactly 0). On CUDA the residual
  `index_add_` nondeterminism applies as below, and the same comparison over 8 strains x 8 worlds
  measured max |score difference| = **5.96e-08** on scores of order 1.4 -- rounding, not a
  different simulation.
- **Everything on the CPU.** CPU rollouts with the same seeds reproduce bit for bit.

## What is not exactly reproducible by default, and why

Grid splatting uses `index_add_`, which on CUDA accumulates in **nondeterministic order**. Floating
point addition is not associative, so two runs of the same GPU rollout can differ in the last bits
of a field value. The simulation is a closed-loop recurrent system, so those last bits grow: after a
few hundred ticks two runs can differ visibly, the same way two runs of any chaotic system do.

This is a property of the hardware and of the algorithm, not a bug, and it is not hidden.

## The one mode where exact reproduction *is* claimed

```python
from wormwars.evo.bundle import replay_mode

with replay_mode():
    ...  # re-simulate here
```

`replay_mode()` sets `torch.use_deterministic_algorithms(True)` and
`CUBLAS_WORKSPACE_CONFIG=:4096:8`. Under **the pinned environment in `requirements.txt`, on the same
GPU**, results inside that context are reproducible.

Outside it, expect **approximate** trajectory agreement: the same strategies, similar scores, and
positions that diverge over a long match. Aggregate results across many worlds are stable either
way; a single trajectory is not.

Deterministic mode is slower, so it is not the default for evolution.

## What a run bundle contains

`runs/<name>/bundle.json`, written by `wormwars.evo.bundle.write_bundle`:

- the full config, every section, as it was actually used
- the connectome: label, `weight_kind`, neuron count, the **sha256 of the published source file**
  and of the parsed cache
- for experiments, one entry per graph (`SH1`, `RD3`, ...) with its edge counts and degree spread
- the seed derivation scheme, spelled out in prose
- the environment: Python, OS, torch and CUDA versions, package versions, GPU name and compute
  capability, the git commit, and whether the working tree was dirty at the time

Genomes are saved next to it as `.npz` with their own metadata (graph label, edge counts, brain
config, sha256 of the genome, nickname). Loading a genome against a different graph is refused
rather than reshaped.

## Honest limits

- A bundle records the git commit but not the diff. A dirty working tree is flagged, not captured.
- The raw connectome spreadsheet is not committed (4 MB binary); `scripts/fetch_connectome.py`
  re-downloads it and refuses to continue if the sha256 has changed upstream.
- Wall-clock and per-GPU-hour numbers depend on what else is using the GPU.
