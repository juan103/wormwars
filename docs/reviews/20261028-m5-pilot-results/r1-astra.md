**Verdict: fix then publish.** The pilot supports keeping 22,000 ticks. I found no reason to rerun it, but the cost attribution, several interpretations and parts of the report need correction before publication.

I checked all 60 source panels, 60 longer-stage files and 60 audit files; reproduced the audit samples, contrasts, intervals and variance splits; and regenerated both blocks for all 20 Rr chains, matching all 40 hashes. I inspected the fallback evidence and implementation without rerunning neural classifications. No files changed.

1. **Accept the qualifier proposal only as a sensitivity analysis for the stated protocol estimand.**

   The distinction at [results:165](D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:165) needs sharpening. The pooled bound, **0.0252795**, bounds neither arm’s latent switches nor each arm’s confirmation probability separately. Applying it to either arm alone is an assumed sensitivity scenario. The registered plan explicitly says this at [plan:154](D:/Claude/random/wormWars/docs/memory/M5-PILOT-PLAN.md:154).

   Reporting both one-arm adjustments and the unrestricted envelope **does answer my earlier concern**, provided the outcome remains explicitly about protocol confirmations. When the envelope permits a sign reversal, say that the underlying separate-state contrast remains unidentified; passing the calibrated sensitivity must not imply otherwise.

   Delete “would mark every M5 outcome as undetermined.” At the pilot shares, the envelope crosses zero when the confirmed contrast lies between −0.003223 and +0.004590—not for every possible outcome. Its width is **0.0078125**, but width alone does not determine whether it crosses zero. At the observed contrast, its endpoints are **[−0.0030273, +0.0047852]**, before sampling uncertainty.

   The calibrated movements are correctly small: **+0.00008147** for T alone and **−0.00011603** for Rr alone. That is conditional on the calibration assumption, not an empirical upper bound on hidden-state bias.

2. **I accept the sampled-audit branch in principle, but its estimator and decision rule must be specified before coding power.**

   [Results:154](D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:154) leaves consequential choices inside “a rule fixed in the plan.” Before `m5_power.py`, specify:

   - Whether the trigger is fading → separate states or any class change, and whether it operates separately by arm.
   - Both tranche sizes, sampling populations and the rule for combining them.
   - How observed reclassifications and estimated transitions among unaudited fading genomes enter the estimator, without double counting.
   - How audit uncertainty—including zero-event uncertainty—and the data-dependent second tranche enter inference.
   - Which final outcome must achieve 80% unconditional power.

   Adding estimated missed confirmations changes the raw “share actually confirmed” into an audit-adjusted estimator. Either retain the raw primary and label the adjustment separately, or explicitly define the adjusted primary’s estimand.

   Using the **unrounded per-arm pooled upper bounds**, with transitions concentrated in either arm as separate scenarios, is appropriate. Multiply transition probabilities by the applicable first-pass-fading share when translating them into all-genome effects. Include heterogeneous host/panel transition scenarios; a common arm-wide rate is not the only plausible allocation.

   I do **not** require completing every fading genome on the evidence here.

3. **The cross-arm audit number is arithmetically right but must not carry the inferential weight currently placed on it.**

   At [results:131](D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:131), \(1-0.05^{1/6855}=0.000436919\), so **0.00044** is correct as a pooled-binomial calculation. However:

   - These are **6,855 genome-arm evaluations**, covering **5,451 distinct host/draw/genome identities**. The arms share underlying genomes and hosts.
   - The pooled number is not a bound for either primary arm or their differential.
   - The individual per-arm 95% bounds are not simultaneous 95% assurance for both arms.

   Label it a descriptive pooled-binomial calculation with those limitations, or omit the bound and retain the zero-event count. Do not make it the leading justification for the audit branch at [results:157](D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:157).

   The registered per-arm calculation was applied correctly: **0/2283 → 0.00131133** for T; **0/2286 → 0.00130961** for K and Rr. Rr’s earlier 786 audits belong to pilot stage (a), not M4e.

4. **Correct the stage-cost accounting and the audit-completion denominator.**

   [Results:36](D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:36) incorrectly assigns the remaining time to stage (a). The saved amounts are:

   | Component | Seconds |
   |---|---:|
   | Rr panel classifications | 22,579.3 |
   | Recorded longer-stage phases | 32,196.9 |
   | Recorded audit phases | 18,919.6 |
   | Remaining recorded runtime | 10,630.2 |
   | Total | 84,326.0 |

   The longer-stage timers stop at `t4`, **before fallback panel reruns**, and exclude the preliminary composition checks; see [driver:479](D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot.py:479) and [driver:490](D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot.py:490). The remainder therefore includes stage-(b) work, verification, reconstruction and overhead. Label these as phase subtotals and leave the residual unattributed unless another record supports a split.

   Also correct “about 96% of every panel” at [results:158](D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:158). First-pass fading shares are **98.56% T and 98.60% Rr**. After the existing panel audits, about **90.92% and 90.93%** remain unaudited.

   The measured audit costs—about **4.14 s/T genome and 4.31 s/Rr genome**—include first-pass replay. A new run retaining endpoints has a different marginal completion cost. “About triple” can remain a rough replay-based estimate, not an established cost multiplier.

5. **Keep the host-variance range, but stop treating its endpoints as established limits.**

   At [results:142](D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:142), zero to M4e’s T − K host component is a reasonable **core scenario range**, not a confidence interval or demonstrated upper bound.

   Two corrections matter:

   - M4d does **not** establish a zero host component. Its quoted decomposition identifies a combined host-and-draw residual: approximately **1.46×10⁻⁶** for T − R and **1.87×10⁻⁶** for T − Rr. Its one-draw design cannot separate those components.
   - Calling M4e T − K “the outlier” at [results:23](D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:23) suggests it can be discounted. It is a different contrast, and the pilot shares M4e’s hosts and T panels. Say it is the larger historical variance source.

   Include sensitivity above M4e’s fitted host component **1.51952×10⁻⁵**, or an explicit treatment of uncertainty within the source estimates. Similar observed SDs in M4d and this pilot do not tightly identify the true host variance.

   There is also a boundary-estimate detail for the power implementation: the observed pilot SD is **0.00335776**, but the reported nonnegative components imply
   \[
   \sqrt{0+(1.53065\times10^{-6}+2.51722\times10^{-5})/2}
   =0.00365396.
   \]
   Thus the simple normal calculation gives approximately **23 hosts from the observed SD**, versus **27 from the truncated component model**. The orientation paragraph is correctly labelled, but the simulation must not silently equate these quantities.

6. **The seven fallbacks satisfy the registered remedy. Fix the strength of the reproduction claim and freeze composition for M5.**

   The remedy at [plan:105](D:/Claude/random/wormWars/docs/memory/M5-PILOT-PLAN.md:105) imposed an exact original-composition reproduction condition, **not a maximum permitted fallback deviation**. All seven records meet that condition as implemented; their class and reason agree, and write amplitude agrees wherever recorded. The maximum normalized deviation is **0.0010377554**. Its size does not retrospectively invalidate the remedy.

   However, [results:46](D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:46) should say **“the failing genome’s recorded fields for the failing pass reproduced exactly.”** The implementation checks those fields, not equality of the entire rerun panel record; see [driver:393](D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot.py:393).

   For M5, predefine deterministic classifier batching, target order, chunk boundaries and singleton handling, and record actual batch membership. “Chunk size 128” alone is insufficient when target lists change. Preserve original-composition replay for adjudicating discrepancies and record root diagnostics and rerun evidence. The 100,000-tick records currently retain only class and reason.

   Finally, call the deviation **normalized absolute/relative error**, using \(|\Delta|/\max(1,|\mathrm{recorded}|)\), rather than simply “relative.”

7. **Complete the promised machine-readable report. The underlying files contain the needed evidence.**

   Against [plan:187](D:/Claude/random/wormWars/docs/memory/M5-PILOT-PLAN.md:187), these gaps remain:

   - [Reader:121](D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot_read.py:121) reports fallback **counts**, without their identities or values, and `max_root_deviation` excludes the fallback deviations. Report separate nonfallback and overall maxima, plus the fallback details or explicit source references.
   - [Reader:187](D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot_read.py:187) supplies per-panel audit denominators and fading-to-separate counts, but not the promised per-panel bounds or all class-change counts.
   - First-pass reporting at [reader:70](D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot_read.py:70) gives separate and fading counts, not a full first-pass class breakdown. Add first-pass/merged class summaries and explicit per-host totals.
   - Describe timing fields as recorded phase costs, not complete stage costs.

   These are reporting repairs; they require no new experimental observations.

8. **Narrow the structural and dynamical interpretations.**

   At [results:68](D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:68), replace “the chain looks mixed” with **“these overlap summaries changed little after another 5,200 accepted swaps.”** Two chain lengths and a few summaries do not establish mixing.

   Also replace “tests the arrangement of the rest.” Shared support does not mean preserved weighted connections: only **20.2 edges on average** retain the same magnitude. Use the registered weighted-arrangement estimand at [plan:35](D:/Claude/random/wormWars/docs/memory/M5-PILOT-PLAN.md:35). The observed 40% overlap is not itself a fixed construction guarantee.

   At [results:119](D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:119), “held by the root search, not by the horizon” exceeds the evidence even with an exploratory label. The supported statement is: **extending the hold to 100,000 ticks resolved none under the unchanged classifier; root-related reasons remained common.** This does not distinguish numerical search limitations from difficult dynamics.

The remaining headline arithmetic checks out: **75/55/59 confirmations, 33/37/47 unresolved, s = r = 0, the horizon decision, audit zeros, overlap table, mean panel times, paired contrasts and intervals, historical SDs, total compute and normal-approximation orientation.** D370 changed only the documented test scope and annotation, not pilot execution code. The power calculation should retain effect **0.002**, model the chosen audit procedure and cost tail, and keep protocol-confirmation inference separate from claims about underlying states.
