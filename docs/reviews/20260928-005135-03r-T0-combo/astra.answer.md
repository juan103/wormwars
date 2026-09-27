I checked `c91a93d` read-only. All six registered input hashes match, and the binding-worktree and HEAD reports have identical hashes. I verified the P4/P3 counts and P3 SE comparison. The local remeasurement record reports zero differences for both graphs; I did not independently rerun the GPU measurements.

For **A**, the earlier substantive findings are resolved. The registered verdict remains correct. The README now includes the fixed outcome sentence, probe caveat, D063 disclosure amendment, and D059 contributions. RESULTS supplies both runs under both rules.

**Must fix**

- **Correct the README’s opening claim.** “[More than any of five null wirings](D:/Claude/random/wormWars/README.md:23)” turns an ensemble-level result into an apparent blanket superiority claim. One null graph exceeds N2 in each run. Use the already-supported wording: **“N2’s random brains again showed unusually high normalised history dependence relative to all five reference ensembles.”** The subsequent counts are correct, but the lead should be equally precise.

**Should fix**

- In the [README’s P3 paragraph](D:/Claude/random/wormWars/README.md:53), say **“the estimated mean score was slightly lower”** and explicitly label the approximately 0.08 calculation **exploratory**, as RESULTS already does. Otherwise readers can mistake it for the registered analysis.
- The [RESULTS noise caveat](D:/Claude/random/wormWars/experiments/03r-replication/RESULTS.md:140) is directionally justified, but “its rank p is too small here” is stronger than the variance comparison establishes. Say unequal measurement noise **undermines exchangeability and can make the rank test anti-conservative**. Document the approximation behind the exploratory calculation.

**Minor**

- [README line 49](D:/Claude/random/wormWars/README.md:49): 0.931 and 0.924 are **N2’s P4 values**, not the N2-minus-ensemble effect sizes. Rename that bullet.
- Specify **“one additional SH-class graph”** in the replication’s fragility sentence. With unequal ensemble sizes, an additional exceedance in an arbitrary ensemble does not necessarily change the verdict.

The validity correction, disclosure addendum, provenance qualification, stale-status corrections, rounding fixes and one-graph-margin explanation address the earlier review. No further experiment is needed to publish the qualified 03r findings.

For **B**, the recorded historical-score matches, three-generation regression and identity checks are supported. I checked the historical scores against the actual nine champion files and the regression against the original log. **T0 does not yet pass its written gate.** The default-CUDA tolerance exceedance is an allowed finding; other requirements remain unmet.

**Must fix**

1. **Explicitly address the failed replay-mode chunking contract.** All six cases in [T0_gpu.json](D:/Claude/random/wormWars/docs/foundations/T0_gpu.json:9) have `replay_mode_chunking_identical: false`. Differences reach **0.0273757 at 200 ticks** and **0.1531775 in the stress test**. These are also replay-mode failures, whereas D081 foregrounds a default-CUDA exceedance.

   [T0 §2](D:/Claude/random/wormWars/docs/foundations/T0.md:78) promises identical full score arrays across chunkings under the execution mode’s terms; §4 makes replay mode exact. The default-mode exceedance allowance does not discharge that requirement.

   Either fix and regression-test chunk invariance, or explicitly amend the contract and record the failed original requirement. Calling padding “a T1 option” alone does not close T0 as written.

2. **Run the declared champion comparison.** [The script](D:/Claude/random/wormWars/scripts/t0_gpu_checks.py:60) loads eight **01b** N2 champions, while [the plan](D:/Claude/random/wormWars/docs/foundations/T0.md:146) specifies **02’s** champions. Moreover, `gcfg.brain = g.cfg` retains their **8 substeps**, rather than the task’s **32 substeps**. I verified the stored champion configuration.

   Thus the rows labelled “02-T0 / champions” and “02-T1 / champions” use hybrid settings. Keep these findings, label them accurately, and run the specified cohort/configuration with the unchanged bound.

**Should fix**

- **Preserve the targeted follow-up as reproducible evidence.** The committed script tests chunk sizes 4096 and 16. Neither it nor its JSON records the 64/256/1024 sweep or direct default-versus-replay comparisons. Save the follow-up code and results, separating repeat differences from chunk differences, with counts exceeding 1e-4 and effective configurations.
- **Narrow the interpretation.** [REPRODUCIBILITY.md](D:/Claude/random/wormWars/docs/REPRODUCIBILITY.md:29) promotes a *likely* different kernel path into a stated cause, and measured agreement into general guarantees. Say **“in the tested configurations”** and **“consistent with a different kernel path.”** The evidence does not establish that every multi-strain chunk is invariant or that default CUDA always repeats exactly.
- **Disclose the historical-code deviation.** The plan requires original-code comparisons; this script imports current code. The nine exact matches remain useful compatibility evidence. However, the original [01b bundle](D:/Claude/random/wormWars/runs/exp01b-direction-corrected/bundle.json:389) records `git_dirty: true`, so checking out its recorded commit alone would not establish the original executed source. Reconcile this explicitly instead of saying everything ran “as declared.”

**Minor**

- D081’s “published evolution path unchanged” should say **the checked generations 0–2 match in best score, mean score and best nickname**.
- The CUDA identity check establishes that enabling ledger tracking leaves scores unchanged. It does **not** check the CUDA ledger residual against 1e-5 or every-tick numerical finiteness; retain the distinction from the previously accepted CPU checks.

Before closing T0 and proceeding through its gate to T1: resolve the replay/chunking contract, complete the declared champion checks, and reconcile the evidence and documentation. **Do not widen the 1e-4 bound.**

03r results: not yet  
T0: not yet