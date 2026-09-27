The registered verdict is correct. The publication package is **not yet ready**: the README obligations are unmet, and several statements need correction.

I checked `roadmap` at `43f6faa`, without reading the raw measurements or modifying files. I independently recomputed ranks, Holm adjustments, latent-SD margins, classifications and supplement summaries from the exported values. They agree. The report in the binding worktree and the HEAD report also have identical SHA-256 hashes.

**Must fix**

1. **Complete the promised README publication text.** [README.md:3](/D:/Claude/random/wormWars/README.md:3) still says 03r is running; its latest-result section remains experiment 02. Consequently, [03r RESULTS.md:172](/D:/Claude/random/wormWars/experiments/03r-replication/RESULTS.md:172) incorrectly says “the README says” the amended text.

   Before merging, include everything required by §10 and D059/D063:

   - The exact successful-outcome sentence already used in RESULTS.
   - The same-probe, stimulus-bank and code caveat.
   - Replication completed before the combined main-branch presentation, while explicitly acknowledging that 03 was publicly readable on `roadmap` from September 27.
   - Why replication was requested: **one additional** graph would have changed 03’s verdict.
   - The distinct contributions of Fable, Astra, Claude Opus and the owner. The attribution in 03r RESULTS agrees with D059; carry it into the README.

   Also make §10’s “side by side, each with both decision rules” explicit. Both runs have P4 maximum rank p **0.0155039** and Holm-adjusted p **0.0465116**. Identify P4-alone as registered primary only for **03r**.

2. **Correct the blanket validity claim.** [RESULTS.md:41](/D:/Claude/random/wormWars/experiments/03r-replication/RESULTS.md:41) says every signal was valid on every graph. That is false: **N2-rev’s P1 is invalid**, with `NaN` value/SE and `valid.P1 = false`. Its common-mode denominator is approximately **0.00008955**, below the registered threshold.

   Say: “All three signals were valid for N2 and every ensemble graph; N2-rev’s descriptive P1 was invalid.” This does **not** affect completeness or either primary verdict.

**Should fix**

3. **Correct the discrete-p explanation.** [RESULTS.md:71](/D:/Claude/random/wormWars/experiments/03r-replication/RESULTS.md:71) calls 0.0465 the “second attainable value.” That was true for 03’s equal-sized ensembles, but is false for 03r. With SH-route at 256, smaller attainable Holm values include **0.0232558, 0.0233463 and 0.0350195**.

   Replace the ordinal claim with the concrete fragility: **one additional SH-class graph at or above N2 would raise the adjusted p to 0.06977**, failing the three-signal rank gate.

4. **Keep P3, but sharpen its interpretation.** Its registered classification is correct:

   - Counts at or below N2: **0, 0, 0, 0, 1**, with denominators **128, 256, 128, 128, 128**.
   - Maximum opposite-direction p: **2/129 = 0.0155039**.
   - Opposite-direction Holm-adjusted p: **0.0465116**.
   - Every effect interval clears its negative margin, including SH-route’s registered zero margin.

   “Registered secondary, unpredicted direction” is the right status. It is **not an unregistered analysis**, and “reversed” means opposite the prediction—not a reversal of 03’s observed sign. The existing text largely gets this right.

   Add two qualifications beside the finding: the rank result is borderline—one additional SH-recip graph below N2 would give **0.06977**—and these are approximate reference-ensemble tests, with nominal error control conditional on exchangeability. The nulls move weights as well as wiring. Describe the score reduction as the **observed mean contrast under this intervention**, without generalising to biological food sensing.

   **No new experiment is required before publishing this qualified secondary.** A mechanistic explanation or stronger general claim would need further testing. P3’s changed label does not invalidate the successful P4 outcome row.

5. **Make the disclosure’s historical scope unmistakable.** [DISCLOSURE.md:10](/D:/Claude/random/wormWars/experiments/03r-replication/DISCLOSURE.md:10) supplies a command claimed to show only one comment edit. That accurately describes the first-push commit `ff17f00`; it does **not** describe HEAD, where the command shows changes across 24 files.

   Preserve the dated notice, but add a dated clarification or pin its comparison to `ff17f00`. Explain the later development separately, referencing D069’s loaded-process/binding-worktree arrangement and D080’s identical reports. Similarly, scope “no signal value … inspected since binding” to the disclosure time.

   I found no demonstrated analysis-rule deviation here. The binding pre-registration and statistical report/verdict modules are unchanged. However, exported reports cannot independently establish every measurement’s provenance or the absence of interim inspection.

6. **Remove stale current-status statements.** The new pointer atop 03’s RESULTS is substantially correct, but [its later paragraph still says 03r is running](/D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:331). [ROADMAP.md:21](/D:/Claude/random/wormWars/ROADMAP.md:21) does too. Update or explicitly date those statements.

**Minor**

7. Three displayed values are misrounded:

   | Location in 03r RESULTS | Written | Correct rounding |
   |---|---:|---:|
   | Line 66: 03 SH-recip interval lower bound | 0.159 | **0.158**, from 0.1584990568 |
   | Line 125: N2 calibration deviation | 2.8% | **2.7%**, or preferably **2.75%**, from 2.7493725% |
   | Line 135: N2perm5 common mode | 0.008 | **0.007**, or preferably **0.00745** |

8. [Line 24](/D:/Claude/random/wormWars/experiments/03r-replication/RESULTS.md:24) needs “a single **additional** routing-matched graph.” One already exceeded N2 in 03.

9. The “roughly 2.6%” calculation is reasonable as a scale comparison, but identify the approximately 0.9 reference score. The exported 03r report supplies **T0** mean fitness, whereas P3 compares **T1** conditions; it does not supply the two T1 means needed to establish an actual percentage reduction.

10. Document that `report.json` contains nonstandard `NaN` values for invalid descriptive quantities, as 03’s RESULTS already does. Preserve the registered report artifact.

Apart from those exceptions, the numerical summaries match the exports or cited records. The P4 gate table is correct, completeness passes, and §10’s **first outcome row and exact fixed wording are correctly selected**. The AI attribution, preflight disclosure and D063 publication-plan amendment are accurately represented in RESULTS; the remaining work is making the publication files consistent with them.

not yet