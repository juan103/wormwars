**Verdict: fix then publish.** The numerical results reproduce. One new explanation is wrong, and several interpretations and M5 statements still need qualification. No change to the primary readings is needed.

I regenerated the 20 host–draw constructions, validated all 160 panels, and reproduced `readings.json`, the predictor tables, block summaries and block-file digest exactly, with writes blocked. I also checked the document’s tables, timings, accounting totals and M4d comparison.

1. **The explanation of why Δ_count’s envelope clears zero is wrong.**

   [“In short”](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:25) attributes this to settling two U_HH genomes. I recomputed the envelope while applying each arm’s second-pass resolutions separately:

   | Unresolved counts used | Envelope upper bound |
   |---|---:|
   | First pass: U_HH = 5, U_LH = 59 | +0.0004600 |
   | Only U_HH resolutions: 3, 59 | +0.0001782 |
   | Only U_LH resolutions: 5, 39 | −0.0001061 |
   | Both: 3, 39 | −0.0004020 |

   Settling the two U_HH cases was **neither sufficient nor necessary** for crossing zero. Settling U_LH’s 20 cases was sufficient. This happens because the conservative envelope includes Student-t intervals over all corners: changing U_LH’s uncertainty can change the upper bound through the spread of host differences.

   Replace the causal sentence with:

   > The second pass settled 20 U_LH and two U_HH unresolved genomes as fading, narrowing the envelope enough to clear zero.

   Keep the thin-clearance warning. This also corrects the mistaken first-round recommendation that the draft followed.

2. **Keep the threshold description, but remove the claims that it establishes shape, mechanism or location.**

   Three passages remain too strong:

   - [“This reads as a property of those hosts’ graphs outside the block”](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:190): the pattern does not locate the cause outside C3. These arms retain host autapses inside C3, and host-specific genome panels also differ. Say it is **consistent with a host-dependent baseline**, without locating its source.
   - [“A log-linear slope is also the wrong shape”](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:236): no comparison establishes that. Sparse switches confined to the largest sampled S2 can also arise from a steep continuous response. The exclusions and limited sampling already justify saying this mean slope is uninformative about the overall response.
   - [“That is why Δ_weight is flat”](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:262): this turns a descriptive pattern into an explanation. Replace it with “This is consistent with Δ_weight’s unresolved direction and small counted difference.”

   “The arm averages look threshold-like” is defensible. A demonstrated threshold, a shared exact floor, or its causal explanation is not.

3. **The S3 matching-cost estimate needs its missing tolerance and uncertainty.**

   [“Matching costs about ten cheap draws per block”](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:287) does not follow from the range 1.26–1.81.

   The files supply a more specific basis: **two of 20 K draws** lie within **0.05 of T’s S3 = 1.7140019**. Thus ten proposals per accepted draw is a rough empirical estimate **for that tolerance and the current construction**.

   Suggested wording:

   > Two of the 20 K draws were within 0.05 of T’s S3, suggesting roughly ten proposals per accepted draw under that tolerance. Acceptance and cost need reassessment for M5’s chosen controls.

   Matching autapses or reciprocity could change this acceptance rate.

4. **M5’s power guidance is substantially improved, but omits explicit first-round requirements.**

   [The M5 paragraph](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:283) now correctly distinguishes the two estimands, identifies the unresolved-outcome problem and qualifies allocation. Add that M5 must:

   - Choose the primary estimand(s) and success criterion before calculating power: detecting a positive effect, establishing an effect above 0.001, and excluding 0.004 are different targets.
   - Account for multiplicity if both contrasts are primary.
   - Assess variance for the new S3-matched control, rather than automatically transferring T − K’s variance.

   Also explicitly call the decomposition a decomposition of **variance in the estimated host contrasts**, not standard deviation or pure host heterogeneity. I reproduced **50.85% host, 7.73% draw and 41.42% genome sampling**. Under that estimate, doubling genomes at fixed draw count multiplies the SD by **0.8904**. The numerical allocation illustration is correct, conditional on that uncertain decomposition.

The other requested fixes check out:

- The revised coupling interpretation and descriptive ladder are appropriately limited.
- The interaction qualification, eigenvalue definition, ≥1.2 band restriction, band medians, 1.0–1.2 rates and 7256-versus-7255 rounding note are correct.
- The boundary-separation wording and “three of four fitted hosts” are correct.
- The strong-arm comparison no longer claims an established conditional arm effect.
- The T − K package description correctly reports eight versus two–four autapses and 75 versus 34–44 reciprocal pairs.
- The identification interval is **[−0.0016602, +0.0051758]**. The SDs, approximate uncertainty factors and orientation-only host counts check out: **237, 61 and 17** for effects 0.001, 0.002 and 0.004 under the stated single-test calculation.
- The audit bounds are **0.003738–0.003819**; **2995** zero-transition audited cases give the stated per-arm 0.001 bound. The envelope limitation and reported-only byte-identity wording are correct.

Two smaller clarifications:

- [“Settled about a third … at about 75 s each”](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:153) should distinguish outcomes from processing cost: **56 of 201 unresolved genomes settled, or 27.9%**. The approximately 75 seconds comes from the smoke estimate per unresolved genome processed, not a measured cost per genome successfully settled.
- At HEAD `46869e7`, the result artifacts are still untracked; the coverage file is committed and matches after line-ending normalization. The draft’s “committed” descriptions therefore depend on the publication commit including those artifacts.

**Δ_count still reads “lowers; size unresolved.” Δ_weight retains its unresolved direction and stipulated 0.004 exclusion.** The required changes concern explanation and planning guidance.