**Verdict: fix.** The registered conclusions stand. I checked commit `f70c949`, the runner, and committed records, and independently recomputed the score contrasts, bootstrap intervals, working flags, census bound, and champion selections. No files were changed.

The five readings follow the registered rules and wording:

| Reading | Verified result |
|---|---|
| S2-a | **1/8**, GA run 4: “evolution found a working selector in 1 of 8 runs, not reliably.” All eight memory classes match. |
| S2-b | **Unclear**: −1.48975, 90% interval [−2.97998, +0.24268]. Neither superiority threshold nor equivalence applies. |
| S2-c | Both censuses have **zero screen qualifiers**. The 95% Clopper–Pearson interval is [0, 0.00359594]; the required zero-count wording is correct. This bounds passing **screen and full check**, not working-selector prevalence generally. |
| Stage 3 | **Better**: +2.36230 [1.31543, 3.51758]; lower bound exceeds +0.5. “Joint tuning” is identified. |
| B-task | **Worse**: −3.72998 [−5.95850, −1.55176]; upper bound is below −0.5. Stage 3 is the correct comparator, and the capacity caveat is present. |

These agree with [evaluate.json](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/evaluate.json).

The numerical fixes are:

- **[G0 table, line 38](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/RESULTS.md:38):** the blind controls’ 90th-percentile threshold is **0.5 × L1-switch’s mean = 6.82324 visits**, not 0.5 visits. The controls correctly passed.
- **[Inactive gain range, line 52](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/RESULTS.md:52):** `g1.json` gives **0.05947798–0.06750971**, approximately **0.059–0.068**, not 0.060–0.067.
- Two rounded values are incorrectly expressed as strict upper bounds: maximum nose τ is **2.8230958**, exceeding “≤ 2.82”; maximum generation-zero offset is **2.1010637 × 10⁻⁶**, exceeding “at most 2.1 × 10⁻⁶”. Use approximate maxima or round bounds outward.
- The τ values are traceable to committed `champions-3.json`, but **absent from `summary.json`**. Correct the opening assertion that every number is collected there.

I found committed sources for the remaining quantitative claims and no other numerical discrepancy.

The descriptive interpretations need these qualifications:

- **“Bistable, not a latch”: supported for these four champions.** Each passes settable, retains q during the 580-tick hold, and fails only the leakage condition. Maximum inactive/active ratios are 0.1772, 0.2203, 0.4848 and 0.3358. Say active gain is **essentially unchanged**, rather than exactly unchanged.
- **“Memory-less” overstates the evidence**, despite the later operational caveat. GA runs 2 and 3 and Stage 3 run 2 also fail release because of excessive inactive gain; active gain passes. For Stage 3 run 2, leakage ratios are approximately **0.45 and 0.67**. This does not establish that q lost its history dependence. Replace “where else its memory might live” with language leaving both q-based transients and behavioral mechanisms open.
- **Mean-nose results support dependence on both modules’ stereo inputs among the 24 tested selector champions.** “Every champion” wrongly includes untested B-task champions. Stage 3 run 7 is exceptional in residual performance, not exempt from the dependence: 14.50 still falls to 4.14/5.80. Clarify that “0.5 to 0.7 elsewhere” refers to its other two noses; other Stage 3 champions have noses up to 1.113.
- **GA versus random sampling is appropriately qualified.** The 1/8 versus 7/8 working counts do not isolate an optimizer effect; the draft correctly acknowledges different distributions and permanent ties.

The deviations are candid about the registered-world exposure, Amendment 1, and **running without confirmation after substantial fixes**. I found no additional material deviation in the checked execution path. “Fix then run” was conditional approval, not independent verification of the rewritten runner; retain that distinction. The missing confirmation alone does not justify discarding or rerunning these results.

Record the corrections with a dated entry under rule 4.