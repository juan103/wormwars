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
  - **Corrected 2026-09-28 (T0, D081, D082): on CUDA, in the tested configurations, that holds
    only while every chunk holds more than one strain.** A chunk of a *single* strain behaves
    consistently with a different GPU kernel path: a direct `torch.bmm` test shows a batch of one
    strain differing by about 5e-5 from the same strain in a larger batch (at 64 and 320 rows per
    strain; none at 16). In the clean rerun (`docs/foundations/T0_gpu.json`, `bcee5a8`),
    single-strain chunks gave these per-world differences, amplified by the chaotic dynamics:
    - at 200 ticks: 3 of 512 worlds (random genomes) and 2-8 of 128 (02's champions) exceeded
      1e-4, with a maximum of 0.027;
    - in the 600-tick stress test: 49 of 512 and 98 of 128 exceeded 1e-4, with maxima of 0.073 and
      0.055.
  - With the same batch composition, results were identical in the tested configurations, even
    in default mode. Chunkings with 2, 3, 4, 16 and 32 strains per chunk all agreed exactly
    (`docs/foundations/T0_gpu.json`). The default-mode nondeterminism described below was not
    observed in these tests, but it is not guaranteed absent.
  - So a genome evaluated alone (a champion's hold-out) can differ slightly from the same genome
    evaluated inside a population batch. Historical replays match exactly because they repeat the
    original single-strain evaluation.
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
GPU, with the same batch composition**, results inside that context are reproducible. A
single-strain chunk is its own composition: see the correction under "Chunking" above (D082). The
T0 checks test repeats directly at one chunking, 4 096 worlds; other chunkings were compared with
that reference, not repeated.

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
