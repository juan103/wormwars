**Fix then publish.** The registered L/F readings, §7.1 limits, secondary designation and S decision are correct. I found no undisclosed formal-run deviation. D279’s exemption does not materially weaken the connectome guard.

1. **Medium — mechanism overclaimed.** `RESULTS.md:79–82`, experiment `README.md:16`, root `README.md:91`, `DECISIONS.md:8642`. Positive comparator→nose weight contrasts do not establish that this route carries the behavioural effect, or exclude comparator→comparator contributions. The controls cut all links together. **Fix:** say “all champions have a positive comparator→nose contrast, suggesting this route”; explicitly state that route-specific necessity/sufficiency was not tested. The exploratory label is correct but does not justify the stronger causal wording.

2. **Medium — entry conflated with approach.** `RESULTS.md:50–54`. “Need it to approach a candidate at all” exceeds the measurement: neither candidate was entered **within 600 ticks**. Approach, movement and eventual entry were not measured. **Fix:** report reduced entry within the trial horizon; retain “not predicted” and “mechanism unmeasured.” Also identify the hand-built comparison as coming from a different maze block.

3. **Low — three incorrect roundings.** `RESULTS.md:76–77,90`. From the records and matching summary:
   - F nose→comparator: −0.034848 → **−0.03**, not −0.04.
   - F nose→nose: 0.054899 → **0.05**, not 0.06.
   - L generation 10: 0.714844 → **0.71**, not 0.72.

4. **Low — “every number … is in summary.json” is false.** `RESULTS.md:4`, `scripts/e4d_evo_summary.py:128–161`, `DECISIONS.md:8645`. Examples missing from the summary: the **24 champions with ≥100 neither trials**, the **minimum per-generation tie share**, and **check’s 787 seconds**. These are correct in the underlying records. Historical compute is also outside the summary; the 128-second dry run is documented in **D275**, not D278 (`RESULTS.md:117`). **Fix:** add the missing quantities and historical sources, and correct that citation.

5. **Low — rerun instructions incomplete.** `RESULTS.md:135`. A disposable checkout of HEAD still fails the formal code guard: the newly added summary script changes guarded `scripts/` since 5237304. **Fix:** name an execution revision, such as **a2e9ae7**, before formal records were added, alongside the existing local-artifact requirements.

Verification: independently recomputed L gain **0.412109375**, bounds **[0.401370455, 0.422848295]**; F **0.390625**, **[0.357907493, 0.423342507]**. Checked per-maze outcomes, stage order/environment/code consistency and amended blocks. Summary regeneration matched in memory; **35 focused tests passed**. No GPU replay performed.