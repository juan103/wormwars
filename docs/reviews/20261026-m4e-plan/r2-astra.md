**Verdict: revise.** The main round-1 reader defects are fixed. I found one new reporting bug, one incorrect statistical justification, and remaining output/documentation gaps.

1. **Medium — the tables ignore the global audit fallback.**  
   [m4e_tables.py:71](/D:/Claude/random/wormWars/scripts/memory_m4/m4e_tables.py:71) always uses `merged_classes()`. It neither applies the reader’s global audit decision nor validates the panel records.

   I reproduced the inconsistency with valid records in memory: an audited fading→separate transition makes `load_counts()` return `use_second=False` and zero switches in both test arms. `predictor()` nevertheless reports one switch in each and computes their AUCs using the rejected second pass.

   Have the tables consume the reader’s validated records and global class selection. Add a regression check covering this fallback.

2. **Medium — “switches in fewer than two arms means no finite MLE” is wrong.**  
   That statement appears in [the plan:222](/D:/Claude/random/wormWars/docs/memory/M4E-PLAN.md:222) and motivates [poisson_slope:123](/D:/Claude/random/wormWars/scripts/memory_m4/m4e_read.py:123). Round 1’s blanket claim was incorrect.

   Using the smoke host’s actual U-arm S2 values, approximately `[2.7816, 69.6586, 1.05915, 26.5239]`, counts `[0, 0, 0, 5]` have a finite MLE: **α = −7.98953, β = 0.464609**, with score residual below `4e-13`. Production returns `None`.

   A singleton positive arm at an **interior dose** can have a finite slope. The smoke’s original extreme-dose case does diverge. Either handle the actual boundary condition, or explicitly retain the two-positive-arm requirement as a deliberate sparsity filter. It changes which hosts contribute; it is not simply protection against nonexistent estimates.

3. **Medium — the promised per-genome predictor output is still missing.**  
   [The plan:227](/D:/Claude/random/wormWars/docs/memory/M4E-PLAN.md:227) promises the predictor for every genome in `tables.json`. [The implementation:80](/D:/Claude/random/wormWars/scripts/memory_m4/m4e_tables.py:80) saves only AUC, median and bands. The individual scores are computed and discarded.

   Save scores with host/draw/arm/genome identifiers and the selected class, or explicitly narrow the promised output. The block summaries and digest check are implemented.

4. **Lower — the audit rationale overstates what the classifier establishes.**  
   [The plan:151](/D:/Claude/random/wormWars/docs/memory/M4E-PLAN.md:151) says later separation would contradict the root verification. That verification uses a finite **float64** continuation and numerical thresholds; M4e subsequently advances the **float32** trajectory. This supports an expectation of stability, not a construction-level guarantee. I have not reproduced a fading→separate counterexample.

   I accept the larger audit as addressing the requested approximately 0.004 sensitivity. Report the actual fading denominator per arm: 800 sampled IDs need not mean 800 fading cases. Even with 800 fading cases and zero transitions, the simple one-sided 95% upper bound is **0.003738**, so it does not validate the 0.001 benchmark. Keep that limitation explicit alongside the first-pass comparison.

5. **Low — two operative seed formulas in the plan remain stale.**  
   [Line 116](/D:/Claude/random/wormWars/docs/memory/M4E-PLAN.md:116) still specifies sign seed `20261311`; production uses `20261511`. [Line 167](/D:/Claude/random/wormWars/docs/memory/M4E-PLAN.md:167) still specifies bootstrap seed `20261341`; production uses `20261541`. The consolidated seed paragraph and code agree with the new values.

The other fixes I checked are present: second-pass schema/class checks, recorded and regenerated host skips, K’s target check, interaction envelope, preservation of robust size sub-fields, and primary readings written before the dose model.

I independently ran **all 24 test functions in memory**, reproduced **all 15 coverage scenarios exactly**, and recomputed Stage 0’s two correlations and nine-host count from its saved blocks. I inspected the 27 sabotage failures, equivalence artifact and M2 test log; I did not rerun the full planted equivalence experiment.

The checkpoint optimization, U_HX exclusion and ten-host/two-draw choice remain acceptable for this exploratory screen. Nothing was modified.