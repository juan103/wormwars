**Verdict: revise, narrowly.** The construction and replay logic largely match the agreed design. The remaining problems are record validation, incomplete-run reporting, and assumptions in the power inputs.

I reproduced the first Rr block’s swap counts and overlap, and the reported variance shares: 0.50851 host, 0.07929 draw, 0.41220 genome. The existing records contain 33 unresolved T genomes and 37 K genomes. I changed no files; executable checks used extracted functions and in-memory inputs, without importing the experiment drivers.

1. **M4e’s outputs are safe under the default invocation, but the isolation claim needs qualification.**

   The pilot calls no M4e writing stage or reading entry point. Its assignments to `m4e.CAP` **and `m4e.STOP_HOURS`** are process-local.

   However, [`MEMORY_M5P_OUT`](/D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot.py:34) accepts an unrestricted directory. Setting it to `runs/memory-m4e` would direct the pilot’s accounting aggregate onto M4e’s `compute.json`. Reject an output directory that aliases a historical experiment’s output directory. With the default path, I found no route that changes M4e’s records or published reading.

2. **The replay implementation is correct; the claim of exact state reconstruction exceeds the evidence.**

   [`replay` and `extend`](/D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot.py:179) use the original probe, retain the first-pass readouts, continue the float32 endpoint, and classify from the final 200-tick tail exactly as M4e’s second pass does. The final extension is correctly 78,000 ticks. The classifier’s float64 investigations do not replace the float32 endpoint being continued.

   Checking both recorded classes is a reasonable exploratory replay check. It establishes classification agreement, not state identity—particularly when both recorded classes are simply “unresolved.”

   The advertised batch-equivalence test actually uses **`ticks=60`**, not 2,000, on an intact SH host ([test](/D:/Claude/random/wormWars/tests/test_memory_m5_pilot.py:138)). It does not establish the docstring’s conclusion that “the states equal the original run’s.” Either narrow that claim or strengthen the test to compare full first-pass endpoints, tails, and readouts for the relevant arm/batch compositions. Preferably include continuation endpoints too.

3. **The saved-record checks need completing before execution and resumption.**

   [`m4e.verify_run()`](/D:/Claude/random/wormWars/scripts/memory_m4/m4e.py:446) reconstructs and checks hosts, blocks, shams, and arm graphs. It **does not validate the saved panel records**. M4e’s reader separately calls `m4e.validate`; the pilot’s [`panel_record`](/D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot.py:203) does not.

   Add that validation for T/K using the reconstructed expected digest. Also complete [`validate_rr`](/D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot.py:117): it omits genome-ID validation and second-pass column-length checks that M4e’s validator performs.

   This is demonstrably consequential. An in-memory Rr record with 40 second-pass IDs and **zero second-pass classes passes `validate_rr`**. Likewise, resumed longer/audit outputs are checked only for matching IDs. The reader accepts missing classification entries: with three IDs and no 100,000-tick classes, it reports `complete: true`, **s = 1**, and selects the longer horizon. Validate identity, IDs, column lengths, class codes, and replay agreement before skipping or reading these files.

4. **The definitions of s and r are correctly implemented, with limits on their interpretation.**

   I accept the fixed, genome-weighted pooling over T, K, and Rr, the inclusive `s ≥ 0.5` boundary, and counting every non-unresolved class—including persistent oscillation—as resolved. “Resolved by the classifier” would be clearer than “settled.”

   The numerator of r correctly includes both separate-state classes. The one-sided Clopper–Pearson calculation is correct.

   But r estimates **confirmation by 100,000 among genomes unresolved at 22,000**. It does not bound eventual switches among those still unresolved at 100,000. If M5 adopts the longer horizon, applying this same r to its remaining unresolved genomes requires an additional extrapolation assumption. Likewise, assigning a common pooled r to both arms is a sensitivity scenario, not protection against control-enriched unresolved switches. Keep those distinctions explicit when choosing the qualifier.

5. **The report needs several corrections before supplying the power calculation.**

   **Incomplete runs:** the promised reporting branch is absent. [`main`](/D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot_read.py:137) opens every Rr panel unconditionally, and `rr-summary.json` is written only after all Rr panels finish. A cap stop during Rr therefore prevents reporting. For later stages, the first missing file produces only `{"complete": false}`, discarding completed-panel summaries. Report completed and missing panels explicitly, retaining descriptive results but withholding s/r decisions until the required population is complete.

   **Paired variance:** [`variance_split`](/D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot_read.py:39) assumes independent binomials despite collecting paired T/Rr outcomes. Agreement with the old T/K decomposition does not validate that assumption for Rr. For paired confirmation indicators, the genome contribution is
   \[
   \frac{p_T(1-p_T)+p_{Rr}(1-p_{Rr})-2(p_{11}-p_Tp_{Rr})}{n}.
   \]
   Estimate it from the paired tables, preferably within panels. Keep the independent-binomial version as a labelled sensitivity. My in-memory check with identical paired outcomes produces positive reported genome variance although every paired difference is zero.

   **Horizon-specific inputs:** if the rule selects 100,000, the power model needs updated confirmation rates, unresolved shares, paired tables, and host/draw contrasts after applying those continuation results. The current contrast always uses the 22,000-tick merged classes. Also expose first-pass fading denominators and transition counts by host/draw for the audit model. The underlying records retain enough information to add these summaries.

   **Cost inputs:** collect separate timings for first-pass replay, continuation to 22,000, and continuation to 100,000. Currently longer/audit files retain only total seconds. A future run retaining endpoints will incur different costs from this replay-based pilot; phase timings are worth adding **before** collection.

One smaller reporting correction: [`weight_share_on_shared_edges`](/D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot.py:100) measures **minimum-weight overlap**, not either graph’s weight share on shared support. For the first block those are respectively 0.24329, 0.44823 for N2, and 0.46442 for Rr. Rename the existing measure or report all three.

The seeds, reciprocal-count constraint, outgoing anatomical magnitudes, continued-chain construction, audit sampling exclusions, and absence of global fallback otherwise match the agreed design. These findings call for local corrections, not a new experimental design.