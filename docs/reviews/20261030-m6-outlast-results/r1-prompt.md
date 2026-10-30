# M6 step 1: the results (round 1)

The plan is `docs/memory/M6-OUTLAST-PLAN.md` (draft 2, committed and pushed in D380, 7e3e5e7, before the run). The
results draft is `docs/memory/M6-OUTLAST-RESULTS.md` (draft 1, also `draft1.md` here). The records are in
`runs/memory-m6-outlast/`: `genomes.json`, `run.json` (per genome: A, B and C classes, the root match, B's
separations, C's root distances), `reading.json` (from `scripts/memory_m6/outlast_read.py`), the logs and
`outlast-compute-record.json` (a copy of the local `compute.json`). `roots.npz` is local.

Read-only; one round planned; proportionate:
1. Does every number in the draft match the records? Re-derive what you can, especially the held/recovered
   cross-tabulation, the merged-root counts and the separation table.
2. Did the reader apply the plan's measures and wordings? Is anything read beyond them?
3. The interpretation (after the data): about a third of the switches are multistable without input, two thirds
   need their input; this refines M6-3's "attractors of a known kind". Fair? Overstated? Anything missing (for
   example what "held under Z" does and does not establish about the network's attractors)?
4. Verdict: agree, fix then publish (list), or revise.
