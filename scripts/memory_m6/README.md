# M6 (memory roadmap): behaviour

Exploratory. Option 0's genomes, probe, classes, comparisons and readings are fixed in
[`docs/memory/M6-0-PLAN.md`](../../docs/memory/M6-0-PLAN.md), reviewed by Astra and Fable before anything ran
([`docs/reviews/20261030-m6-0-plan/`](../../docs/reviews/20261030-m6-0-plan/)). CPU only.

| Script | What it does | Output |
|---|---|---|
| `m6_0.py` | Option 0: every T1 genome 02 saved (g00, g39, g79) and a new CPU draw of 02b's drift control, classified by M2's frozen classifier inside `probe_input` (each run's mapping), on each run's own bank (02b's typical input) and on 03mc's, with M4e's second pass and an audit; the persistence measures. Hides the GPU when run. Stages `genomes`, `banks`, `first`, `second`. | `runs/memory-m6-0/`: `genomes.json`, `banks.json`, `first-<bank>.json`, `second-<bank>.json`, `m6-0-compute-record.json` (a copy of the local `compute.json`; states `first-<bank>-states.npz` local) |
| `m6_0_read.py` | The consistency check against 02b, the audit, the classes with unresolved bounds, the cluster bootstrap over the 30 graph-and-run blocks, the fixed wordings; *after the data*, the fading profile and the fading-only persistence comparison. No simulation. | `runs/memory-m6-0/reading.json` |

The results are in [`docs/memory/M6-0-RESULTS.md`](../../docs/memory/M6-0-RESULTS.md). Inputs: the connectome,
02's local T1 genomes and records (`runs/exp02-screening/`), and 02b's `history.json`. The tests are in
`tests/test_memory_m6.py`.
