**Verdict: revise before formal arms.** The main construction and contrast formulas look consistent with the plan, but I found a reproducible reader failure and several gaps that affect the reading or its verification.

1. **High — the dose fit fails on plausible sparse counts.**  
   [poisson_slope](/D:/Claude/random/wormWars/scripts/memory_m4/m4e_read.py:116) handles all-zero counts but not a non-finite maximum-likelihood estimate. With U-arm counts `[0, 1, 0, 0]` in `(LL, LH, HL, HH)` order, all switches occur at the largest S2; the fitted slope tends to positive infinity.

   Using the smoke block’s S2 values, I reproduced `LinAlgError: Singular matrix`. This is also the U-arm count pattern in the smoke. Other inputs can return an unconverged coefficient after the arbitrary 50 iterations. Because `main()` fits the dose model before writing `readings.json`, this secondary analysis can prevent publication of the primary readings.

   Detect boundary/non-finite fits, check convergence, and prespecify their reporting and treatment in the host average. Do not evaluate W/K against an undefined curve. Also flag when their S2 lies outside the fitted U range. Fitting U only is the correct choice; the numerical failure policy is missing.

2. **High — the fading audit does not validate the mixed-horizon reading at the stated margins.**  
   The [audit specification](/D:/Claude/random/wormWars/docs/memory/M4E-PLAN.md:122) improves on 256 pooled cases, but pooling across arms conceals the relevant uncertainty.

   Even assuming all 160 sampled genomes in an arm are initially fading, zero transitions gives a one-sided 95% binomial upper bound of **1.85%**, versus effects of 0.1% and 0.4%. If one arm has a fading→separate transition rate of 0.004, its audit misses every transition with probability **52.7%**. The actual fading sample can be smaller than 160.

   Unaudited fading genomes remain resolved non-switches and therefore contribute **nothing to the unresolved envelope**. Zero detected transitions cannot establish robustness to this source of error.

   Keep this audit as a diagnostic, but either strengthen validation and account for unaudited fading, or retain the original-horizon envelope as the primary reading and make the mixed-horizon result descriptive. State an explicit tolerated transition rate. Under the simple binomial calculation, ruling out 0.004 with zero transitions requires at least 748 fading cases **per arm**, not pooled.

3. **Medium — validation accepts records that can narrow the envelope incorrectly.**  
   [validate](/D:/Claude/random/wormWars/scripts/memory_m4/m4e.py:444) checks first-pass class codes but only the *length* of second-pass classes. I passed it a record containing second-pass code `-1`. Subsequently:

   - `CODES[-1]` labels the transition “unresolved”;
   - the merged unresolved count tests equality with `4`, so counts none of those genomes.

   Thus malformed records can produce an internally contradictory report and omit uncertainty from the envelope. Missing second-pass reasons, root distances and read-out differences also pass validation. Validate both passes’ complete schemas and class domains before merging.

   Separately, [check_host_list](/D:/Claude/random/wormWars/scripts/memory_m4/m4e.py:125) permits arbitrary jumps along the seed sequence. I confirmed that jumping 50 candidate seeds with an empty `skipped` list passes this check. `load_hosts()` regenerates only the selected host; it never verifies why earlier candidates were rejected. That does not enforce the specified first-available-host rule.

4. **Medium — several promised outputs are absent.**  
   The implementation does not currently produce:

   - the interaction’s unresolved envelope: [read](/D:/Claude/random/wormWars/scripts/memory_m4/m4e_read.py:285) writes only its point estimate and ordinary interval;
   - `blocks-summary.json` and the promised block-file digest;
   - M4e’s per-block S1/S2/S3 and per-genome eigenvalue/AUC outputs.

   `block_s2()` supplies a temporary dose-model input; it does not fulfill the promised summaries. `m4e_stage0.py` analyzes **M4d**, not M4e. Implement these or explicitly amend the plan before running.

5. **Medium — the stated regression evidence exceeds what the tests establish.**  
   The plan claims bitwise preservation of the frozen classifier **on planted genomes**. [The corresponding test](/D:/Claude/random/wormWars/tests/test_memory_m4e.py:162) only inspects parameter defaults. It never compares old and new classifier outputs. Likewise, the checkpoint test uses one genome throughout; it does not test the production transition from a batched continuation to an individual recurrence rerun.

   There is also a false-positive sabotage: [“coverage’s response ignored”](/D:/Claude/random/wormWars/scripts/memory_m4/sabotage_m4e.py:114) installs a lambda accepting `ok`, whereas the test passes `exclusions_ok`. The archived log shows failure from **`TypeError`**, not detection of the disabled coverage response.

   Add the actual classifier regression and batch-to-individual replay tests, and fix that sabotage’s signature. Test the global audit fallback through `load_counts()`, not only the audit predicate.

6. **Lower — the advertised hard cap is not implemented as stated.**  
   Cap checks occur before chunks, outside potentially long classification and continuation calls. The final chunk can finish above 48 hours and still leave a complete, readable run. [CapClock](/D:/Claude/random/wormWars/wormwars/registration.py:129) also measures elapsed wall time, not process CPU time. Enforce the intended cap within long operations, or describe the boundary checks and possible overrun accurately.

On the six implementation choices:

- **Tick-21,800 checkpoint:** agree with the optimization. The windows shift correctly and the additional float64 cap remains 20,000 ticks. I independently obtained bitwise-identical recurrence substeps in short moving-state checks using batches of 3, 8 and 128 genomes followed by individual reruns. Preserve that production-shaped check in the suite; determinism alone does not establish equality across batch compositions.
- **U_HX omitted:** agree. The benchmark supports exclusion under the stated budget rule.
- **Power:** acceptable for a limited exploratory screen; I would not require additional hosts solely to raise power. The reported power is conditional on correct classification and does not repair the audit issue. Keep null conclusions narrow.
- **K matching:** agree. The swaps preserve degrees and weights, the tolerance is implemented, and unmatched fallback is explicit. Describe K−W conditionally on achieved matching.
- **Audit:** revise as above.
- **U-only dose model:** agree conceptually; fix boundary fits before running.

I executed all **18 test functions directly in memory**, avoiding filesystem-writing fixtures, and reproduced **every coverage scenario exactly** from the saved specification. The primary 95% hulls, envelope corner calculation, contrast signs, and global audit-failure fallback match the plan. The checked Stage 0 AUC, bands and correlations match its JSON. Those checks support the implementation’s core, but do not resolve the findings above.