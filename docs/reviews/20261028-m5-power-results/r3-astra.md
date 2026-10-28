**Verdict: revise, narrowly.** The round-2 statistical repair is complete and correct, and draft 3 fixes the material wording objections. I found one new execution-default bug; it does not invalidate the saved results or the recommendation of C.

1. **Fix the default output directory.** In [m5_power.py:37](/D:/Claude/random/wormWars/scripts/memory_m5/m5_power.py:37), Welch now defaults on, but `OUT` still defaults to `runs/memory-m5-power`, which contains the original-reading results.

   I verified this with both environment variables unset. This matters because [stage_c:1321](/D:/Claude/random/wormWars/scripts/memory_m5/m5_power.py:1321) reuses existing exploration entries. A default invocation can therefore combine Welch confirmations with the original reading’s cached allocation search and overwrite the comparison file.

   Make the default directory depend on the selected reading, while preserving an explicit `M5_POWER_OUT` override. Add a regression check for both default Welch and `M5_WELCH_TOO=0`. The documented explicit-directory command is correct; the bare default is not.

2. **The invalid-host repair checks out.** Audit-rate pooling, final bounds, hidden-count comparisons, and stage-1 bounds consistently use valid hosts. Attempted-host costs remain charged. I also exercised `run_c` with invalid hosts in both stages: changing their transitions and hidden counts left the readings and coverage unchanged. Only the intentionally all-host latent diagnostic changed.

   The saved diagnostics correctly contain **143/10,000** and **62/10,000** central runs exceeding C’s own mean by 25%, along with caps and rescaling counts.

3. **Draft 3 answers my substantive wording points.** It correctly distinguishes protocol confirmations from underlying states, retains all three balanced-hull components, qualifies the gate calculation as illustrative, and distinguishes the two cost references.

   One small correction remains at [line 246](/D:/Claude/random/wormWars/docs/memory/M5-POWER-RESULTS.md:246): “the eight ensemble-null cells cannot fail” is literally false. Say their contribution to expected failures is negligible at their simulated rates. The revised arithmetic—12.4% failure probability and approximately three expected failures among 24 cells—is correct.

4. **Section 5’s recommendation remains supported.** The Welch records give C:

   - **72.03 / 90.68 / 96.15 CPU hours**, central/core/above;
   - **0.8409 / 0.8084 / 0.7467 power**;
   - **145.36-hour cap**;
   - **22.11% central saving**, approximately **1.9% at the core**;
   - core confirmation lower bound **0.800547**.

   The owner-facing qualifications now describe the relevant tradeoffs. These findings require no new power simulation or reconsideration of C.

I ran **48 tests successfully**, excluding the single test that writes a temporary output file. The archived draft matches the live note. No files changed.