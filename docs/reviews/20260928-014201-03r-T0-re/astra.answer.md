At `9b65eb9`, **the prior blockers are resolved. T0 passes under the amended, configuration-specific contract.** D082’s claim that *every* point is addressed is slightly too strong.

For **03r**, the lead, registered P3 label, exploratory caveat, both-rules comparison, named fragile ensembles and §9 disclosure now address the review. I verified the P3/P4 counts, all six registered input hashes, and identical binding-worktree/HEAD report hashes. No new problem changes the registered verdict.

For **T0**, I verified that the selected champion files are 02’s, with 32 substeps and matching gains. The rerun records clean code provenance at `bcee5a8`; its script is unchanged at HEAD. The JSON supports:

- Exact recorded repeats and all tested chunkings without singleton chunks.
- Nine historical matches, checked against the champion metadata.
- Generations 0–2 matching the original log.
- CUDA ledger residuals below 1e-5; the largest is **1.405×10⁻⁷**.

The amendment explicitly acknowledges the failed original contract. Accepting that amendment closes the chunking objection without changing the numerical bound.

There are still **nonblocking corrections**:

- **The remeasurement comparator can falsely report identity.** In [remeasure.py:41](D:/Claude/random/wormWars/experiments/03r-replication/remeasure.py:41), `nanmax` ignores finite-to-NaN changes: `[1, 2]` versus `[NaN, 2]` passes. Nested-list `zip` also ignores unmatched trailing entries. Require matching structures and exact values with matching NaN positions. This is a checker defect, not evidence that the recorded measurements differ; the saved measurements contain no NaNs.

- **The reproducibility summary still quotes old evidence.** [REPRODUCIBILITY.md:32](D:/Claude/random/wormWars/docs/REPRODUCIBILITY.md:32) should say **three worlds exceeded 1e-4**, not that only three differed. Its **0.15** stress-test maximum belongs to the earlier cohort, absent from the linked replacement JSON. The new maxima are **0.07325** for random genomes and **0.05497** for champions; respectively **49/512** and **98/128** exceed the bound. Likewise, the amendment’s “a few worlds” needs a 200-tick qualification.

- **Keep the exactness claims scoped.** Add “same batch composition” directly to the [replay-mode guarantee](D:/Claude/random/wormWars/docs/REPRODUCIBILITY.md:63). Also, [the script](D:/Claude/random/wormWars/scripts/t0_gpu_checks.py:121) directly tests repeats and default-versus-replay equality at `chunk_worlds=4096`; it does not directly repeat-test every chunking.

- **“Everything finite” overstates the CUDA check.** [Its `finite` field](D:/Claude/random/wormWars/scripts/t0_gpu_checks.py:178) checks final scores and swarm energies. Every-tick brain-state coverage remains in the previously accepted CPU tests.

I did not independently rerun the GPU measurements or test suite. The engine and tests are unchanged since the accepted CPU revision.

03r results: ready to publish  
T0: close