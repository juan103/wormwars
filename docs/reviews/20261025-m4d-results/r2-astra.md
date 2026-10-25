**Verdict: fix then publish.** The reading remains correct. Most round-one fixes are complete, but the new power interpretation is wrong, and two smaller numerical descriptions need correction.

I independently reran `verify_run` and validated all 70 panels; reproduced the reading, intervals and unresolved envelopes; checked the companion, overlaps, measures and block summary; and reproduced `tables.txt` in memory. The digest mismatch guard works, `MEMORY_M4D_OUT` is honoured, and `coverage.json` matches the file in commit 6553a98. No files were modified.

1. **Correct the power argument and remove the unsupported “out of reach” conclusion.**  
   [Results line 234](/D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:234) treats approximately 5% rejection at δ = m as a ten-host power limitation requiring far more hosts. For a calibrated test requiring **lower(D_TR) > m**, δ = m is the **null boundary**. Its rejection probability should remain around the nominal one-sided 5% as sample size increases. More hosts cannot provide high power to establish δ > m when δ = m.

   The simulation’s numbers are correct; this interpretation is not. I disagree with that part of Fable’s round-one advice.

   Power planning needs a specified alternative **δ > m**, its distance above m, host variability, classifier treatment and a compute budget. The current records do not establish that M5 is computationally “out of reach” at [line 254](/D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:254). The reassignment endpoints also bound these sample results, not the true effect.

   Suggested replacement: “At δ = m, the positive rule fires in at most 4.5% of simulated screens, as expected near the null boundary. Assessing a confirmatory study’s feasibility requires power calculations for specified effects above m and a planned treatment of unresolved classifications.”

2. **The T−P interval’s full width is approximately the whole transplant effect, not half.**  
   At [line 176](/D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:176), the interval width is **0.00594924**, versus D_TI = **0.005859375**. Its **half-width**, 0.00297462, is approximately half the transplant effect. Change “the interval spans about half” to “the interval’s half-width is about half,” or describe its full width correctly.

3. **The two slowest panels do not have the two largest unresolved counts.**  
   [Line 57](/D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:57) overlooks **SH-recip-2051000 P: 13 unresolved, 1652.7 seconds**. The two slowest have 12 and 10. Say they have “among the larger unresolved counts,” or specify that they have the largest counts **within SH-mirror-2041001**. Their counts are consistent with difficult classifications; they do not quantify how much slowdown came from classification versus CPU sharing.

Two additional qualifications would make the interpretation precise:

- At [line 150](/D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:150), identify **T and T+G’s exact weighted block**, rather than merely “exact wiring.” **P also preserves N2’s exact edges**, yet has 46 non-settling cases versus 76 and 70. The pattern does not isolate topology from weight placement.
- At [line 252](/D:/Claude/random/wormWars/docs/memory/M4D-RESULTS.md:252), explicitly condition **R−D being above zero** on counted classifications. Its counted interval is positive, but I calculate an unresolved envelope of approximately **−0.00429 to +0.00904**. Keep that statement distinct from T−I and R−I’s robustness.

The corrected classifier explanation, companion interpretation, provenance wording, reproduction paths and impossibility argument all check out. My recommendation remains **publish the corrected unresolved screen and take the direction decision to the owner**. These findings require reporting changes, not another experimental run.