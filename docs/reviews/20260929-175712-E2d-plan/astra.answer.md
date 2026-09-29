**revise**. The probes are useful, but several proposed conclusions exceed what this design can establish.

Must-fix items:

1. **Part A — qualify the ranking estimate and correct one count.** The table is consistent with **half credit for ties**. For the smallest gap at eight worlds, I calculate 0.621 with half credit, **0.541 strictly correct**, and 0.160 tied. State that convention and commit the analysis script, including bin boundaries and generation-0 exclusion. Shared-world resampling correctly reflects within-generation pairing; champion pairs do not represent GA parent–offspring comparisons, ES antithetic pairs, or random sampling’s nominations across generations. Training and hold-out IDs use the same world generator; their different finite samples do not establish a distribution shift. Call the SE a hold-out-based proxy, and remove “where most candidates sit.” Also change **all eight ES champions** to **seven**: run 7 is 0.2686 below M-avg.

2. **Part B — change the interpretation, complete the probes.** In [world.py](/D:/Claude/random/wormWars/wormwars/world.py:671), `mean` preserves the instantaneous bilateral average; it does not preserve the original temporal history once trajectories diverge. Both positive contrasts support **a large performance benefit from intact bilateral inputs**, not a particular comparison mechanism. Failing the 0.5 rule does not establish absence of stereo use or a temporal strategy. Report continuous effects; use upper bounds/equivalence margins if claiming negligible effects. Remove the pooled “at most 2 of 48” inference and report groups separately: formal ES and extensions are dependent, and extension run 6 is literally the same genome as formal run 6. **Add `swapped` for C’s champions** if applying B’s rule.

3. **C1 — separate evaluation precision from budget allocation.** This changes worlds, generations and checkpoint opportunities. Its total selection work is **258,816 episodes/run**, versus **266,496** for E2’s GA, including validation. Match checkpoint opportunities at approximately equal fractions of training work, or explicitly retain an allocation comparison with unresolved checkpoint effects. Fewer checkpoints do not necessarily hurt hold-out performance: they also change selection optimism. A positive result supports spending more work per evaluation; a negative result cannot rule out noisy selection.

4. **C3 — it changes two settings.** σ halves, and Adam’s learning rate halves. Hold the rate at 0.15 to isolate σ, or label this a joint perturbation/step-size change and interpret it accordingly. **No new pilot is necessary** for a fixed exploratory setting. Compare its training cost with E2’s formal ES, without presenting it as another equal-total-work optimizer contest.

5. **Part C — make uncertainty and “breaking the plateau” explicit.** Eight runs and a 0.3 practical threshold are reasonable for screening, but “differences under about 0.3 are not resolved” is not a general property of eight runs. E2’s between-run SDs are 0.496 for GA and 0.115 for ES. Define inconclusive and harmful outcomes, including gains above 0.3 whose intervals cross zero. Report individual runs, medians and failure frequency. A gain over the GA’s mean can reflect avoiding its failed run; it need not exceed the successful runs’ plateau. Historical comparisons support exploratory leads, not clean causal attribution.

6. **Decision guidance — remove “the optimizer is not the bottleneck.”** That conclusion is wrong. Failure of these changes leaves search, representation, budget and interactions unresolved. Likewise, C1 does not establish that E3 needs *at least* 32 worlds, and C2/C3 identify promising settings rather than proving the original operator was mis-set. Add an explicit **paired formal-versus-extended ES comparison on B’s fresh worlds**, with cumulative-work learning curves. This costs no additional champion evaluations and addresses budget directly; it still does not establish a ceiling.

7. **Seeds, guards and budget — finish the specification.** Replace “1,130,000 and up” with exact arm/replicate mappings and a declared pairing policy; explicitly retain world seed 1,100,001. Specify smoke/projection allocations, binding inputs including this plan, control-check tolerances, incomplete-arm handling, and evaluation reserves. Benchmark C1’s new **(256, 32, 1)** training composition before accepting its time estimate. Equal episode counts do not guarantee equal throughput or memory use.

Suggestions:

- Within five hours, I would **replace C3 with eight fresh default-GA runs**, paired with C1/C2 through initialization and training-world streams. The nominal total becomes roughly **4.2 hours**, subject to C1’s projection. This strengthens the two GA comparisons.
- Use remaining capacity for fixed-genome local mutations and ES antithetic pairs on independent world blocks: measure ties, rank stability and GA parent-selection agreement. This diagnoses selection noise more directly than unrelated champion pairs. An ES more-worlds arm should follow that evidence; I would not add both it and another full budget arm now.

What I checked and found correct:

- Recomputed SD **0.6046–1.0794**, implying the stated eight-world SE proxy **0.2137–0.3816**; pair-bin counts **80/122/110**.
- Excluding generation 0, the **320 nominees per method** give random sampling **1.1457 → 0.8132**, correlation **0.6387**; GA **1.8125 → 1.6260**, correlation **0.8468**.
- Late GA best/mean/zero share: **1.9216 / 0.5415 / 23.97%**. ES mean/zero share: **1.2793 / 3.795%**. ES endpoint validation: **2.0220 → 2.3101**.
- `mean` and `swapped` implement the stated instantaneous transformations. S-const and M-avg are appropriate positive and invariance checks. The corrected 04a behavioral comparison is accurately described.
- The proposed world ranges are disjoint from the earlier ranges I checked.

Read-only review; no files changed or GPU experiments run.