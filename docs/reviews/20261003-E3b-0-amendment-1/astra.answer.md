**Verdict: confirm with fixes. No further review round needed for the changes below; do not run the draft unchanged.**

I checked amendment commit `85bdffc` and the subsequent working-tree edits. All 24 Stage B arrays match their summaries. I reproduced the best-setting synthetic away/toward results, nose quantiles, and both seeds’ high-level K_D values exactly. The three targeted regression tests pass. I changed no files.

1. **The diagnosis’s numbers hold; its impossibility claims do not.** On the synthetic slope at the best setting, away-facing arrivals rise from **9.375% at 2× to 42.1875% at 4×**; the polarity contrasts are only **0.015625 and 0.03125**. This establishes failure of the tested gate, not inability to turn around. Moreover, the synthetic field subsequently diffuses and evaporates, with scents and wall reflexes still operating.

   The **0.234375 ceiling** follows from `1 − 0.765625`, but applies only to the **corrected toward-facing condition on these 64 mazes**. It does not establish that the registered away-facing 0.3 threshold was mathematically unreachable. Age also matters: the pilot’s toward-facing contrast changes from **−0.078125 aged to +0.125 fresh**. Correct these claims in the [amendment](/D:/Claude/random/wormWars/docs/E3/E3b-0-PLAN.md:478).

   The arrival-time quartiles need repair: `np.quantile` interpolates infinities into `NaN`. Report censoring explicitly and preserve per-maze arrival times and deadlines.

2. **Keep the 5% cap, but scope its justification correctly.** Excluding occluded and zero inputs avoids diluting the high-level fraction. The recorder correctly evaluates trail existence for the current goal at sensing time; “exists” means **anywhere in that maze**, and measured inputs include scent.

   At the diagnosed winner, the new denominator gives **39.86% above 0.35**, substantially worse than the old 31% figure. The cap is therefore meaningful. However, **5% is an engineering allowance, not a demonstrated harmless fraction**, and 0.35 is not a universal qualification certificate: S3r3 already fails K_D ≥ 30 there.

   Crucially, **a follower-based cap does not bound the seed’s distribution**. Enforce the same cap on the chosen seed’s selection-maze run before opening report mazes, with a frozen failure branch. Remove “by the cap they are at most 5%” unless that seed check passes. Reject an empty denominator rather than treating it as zero exceedance.

3. **The positive trail-effect condition is reasonable for exploratory selection.** Pin it explicitly to `world_ci`: paired maze bootstrap, 10,000 resamples, seed 0, lower endpoint of the two-sided 95% interval above zero. Keep shared-rate ranking and the original report-maze criterion 3. Selection intervals do not independently validate the selected winner.

4. **Including d₀ in the widening is defensible, but make its consequences explicit.** With two d₀ values, **every winner is on a d₀ edge**, so widening becomes automatic whenever an initial setting qualifies. “All combinations” can add **54 settings**, not merely one neighbouring setting. Freeze the generated grid, deduplication, complete tie-breaking, and the stop after one widening. State explicitly that no initial qualifier means no widening.

   Also reconcile the old failure table: its criterion-3 fallback and later widening/rescaling branches remain inconsistent with “no fallback” and a single bounded search.

5. **Criterion 4 still needs work.** Use the chosen seed’s inputs, as proposed, but add low-tail coverage and the 99th percentile; retain a boundary check at 0.35 when claiming qualification through that boundary. Report high-tail failures explicitly rather than implying complete qualification.

   There is a concrete implementation problem: [the probe](/D:/Claude/random/wormWars/wormwars/e3/probe.py:58) uses `m ± 0.0005`. Measured low quantiles can be smaller, producing **negative nose inputs**. Freeze a numerically checked, nonnegative perturbation protocol. Also specify executable `(0, q)` and `(q, 0)` response checks; merely counting asymmetric occlusion does not qualify those responses. Label histogram quantiles as approximate bin bounds.

6. **Replace the fixed wording.** “This follower uses it only when already facing the source” asserts both a mechanism and exclusivity that the evidence does not establish. Use:

   > “Stage B failed the registered behavioural polarity criterion. Gradient-sign qualification does not establish directional trail use; the amended stage reports behavioural polarity separately.”

   Keep the restriction on E3b-1’s directional claims.

7. **Before GPU execution, finish the provenance transition and validation.** The current `require_earlier()` calls [reject changed guarded code or plan text](/D:/Claude/random/wormWars/scripts/e2.py:410), so they will reject the historical Stage A/B records. Add a narrowly specified transition verifying their pinned records, hashes and environment, with equivalence evidence supporting reuse. Preserve normal guards afterward.

   Commit/push the final amendment, implementation, reviews and decision entry—**D178 is referenced but absent from `DECISIONS.md`**. Record effective per-setting configurations, test the new qualification/failure paths, and remove the vacuous `assert … or True`.

   Accounting confirms **0.7356 hours used, 2.2644 remaining**. Project the maximum widening plus diagnostics, recheck and downstream work against that remainder before starting.