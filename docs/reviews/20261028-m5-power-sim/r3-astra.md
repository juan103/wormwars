**Verdict: revise, narrowly.** Most round-2 objections are answered. Two items need correction before coding: the success predicate still omits an agreed sensitivity, and the scope supporting **K = 26** remains unspecified. The first requires correcting my own round-2 recommendation.

I compared both reviews and drafts, checked the pilot report and panel records, and ran numerical checks in memory. No files changed; no neural experiments ran.

1. **Q2 — The envelope is correct; the four-reading success event remains incomplete.**

   Draft 3 correctly implements my request to restore the standalone Rr-unresolved check. But my request overlooked the consequence of the non-monotonicity we had already identified: **adding T-side confirmations can also remove “raises” by widening the interval.**

   The [earlier agreement explicitly requires both one-arm sensitivities](D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:262). The [current predicate](D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:94) checks only Rr’s.

   A concrete, count-compatible example:

   - H = 15, three hosts per ensemble; D = 2, G = 512.
   - Fourteen hosts have confirmed-count contrast 1; one has contrast 14.
   - No audited transitions and no Rr unresolved genomes.
   - T has five unresolved genomes, all in the host with contrast 14.

   All four current readings equal the raw reading:

   | Reading | Hull’s lower endpoint |
   |---|---:|
   | Raw—and all four current checks | +0.0000076675 |
   | T-side unresolved sensitivity | −0.0000017606 |

   The bootstrap lower endpoints remain positive; the t component causes the reversal. Thus the current event calls this unqualified although the agreed T-side sensitivity qualifies it.

   **Repair:** include the T-side standalone sensitivity. My recommendation is to specify six checks explicitly: raw, audit-only, each one-arm unresolved adjustment, and each one-arm unresolved adjustment combined with the audit adjustment. Add this example as a test. I have not measured how frequently this affects power; the example establishes that the predicates differ.

   The **unbalanced envelope repair is valid**. Writing \(a_e=w_e^2s_e^2/n_e\), Welch’s degrees of freedom satisfy
   \[
   \nu=\frac{(\sum_e a_e)^2}{\sum_e a_e^2/(n_e-1)}
   \geq \min_e(n_e-1).
   \]
   Together with the per-stratum variance bounds, this establishes the stated containment. I checked a 16,384-corner example with sizes `(2,3,3,3,3)` and reproduced the earlier half-widths, 0.002265 versus 0.025412. Making exclusion unavailable when an ensemble has only two valid hosts also answers round 2.

2. **Q4 — Accept the candidate threshold and null tolerances; finish the confirmation-family definition.**

   [K = 26](D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:293) counts 24 fixed-H candidates and two C candidates. That can work, but the document does not specify:

   - **Which scenario constitutes that fixed-H family.** A and B select H under different scenarios, and the report supplies selections across the host-variance range.
   - **Which single allocation supplies C’s two candidates.** Section 5 supplies a lookup for each allocation but no rule nominating one allocation before C’s confirmation.

   This is the remaining part of my round-2 request to define K’s scope.

   A straightforward repair is to declare separate scenario families and nominate exactly one C allocation using exploration results before its fresh confirmation. Then allocate its two confirmations explicitly to the relevant family. If instead all 12 C allocations receive two confirmation attempts, they contribute **24**, giving **K = 48** alongside the 24 fixed-H candidates in that family.

   C’s three core scenarios need not introduce another factor of three **if acceptance is one conjunction requiring all three to pass**. That supports a joint “passes throughout the core” decision; it does not provide simultaneous coverage for every reported numerical bound. State which claim is intended.

   The revised numerical rules otherwise check:

   | Check | Required count |
   |---|---:|
   | 80% candidate, R = 4,000, K = 26 | At least 3,273 successes |
   | 80% confirmation, R = 10,000, K = 26 | At least 8,116 successes |
   | Null upper bound ≤ 0.0275, R = 40,000 | At most 1,045 false raises |
   | Null upper bound ≤ 0.030, R = 40,000 | At most 1,143 false raises |

   Separate 90% and 80% families are acceptable. Restore the explicit instruction that the 90% column substitutes **0.90** for the currently hard-coded 0.80 criterion.

   The 0.0275/0.030 tolerances, their interpretation as 10%/20% permitted inflation, and reporting point estimates beside passes answer both reviews.

3. **Q3 — Rule C’s substantive round-2 repairs are acceptable, subject to point 2.**

   The [revised specification](D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:332) answers the outstanding requests:

   - The lookup names its nuisance settings and indexes total raw variance at δ = 0.002.
   - H_max exploration ends before fresh confirmation, with an explicit failure outcome.
   - Invalid interim hosts have a defined treatment and minimum surviving stratum size.
   - The cap is **1.5 times fixed-H mean cost at H_max**, under a named reference scenario, frozen in seconds. This fixes Fable’s cap objection.
   - The inflation is correctly described as a normal-reference rule.
   - Power above the core range is measured rather than asserted.
   - The cost comparison uses matching components.

   The [stage-1-only audit bound](D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:271) answers my stopping objection under the common-rate model. The final pooled bound remains diagnostic, with its coverage measured. The distinctions between probability coverage, expected hidden contribution and realised hidden count are now explicit. The revised inclusion-probability explanation is also correct.

   Two wording corrections remain, neither requiring a new mechanism: stage 2 preserves balance in **attempted** hosts, not necessarily valid hosts; and a lower cap **can reduce power**—it does not necessarily force power below 80%.

4. **Q1 — The variance construction is now consistent, with small exactness corrections.**

   Fixing baseline logit variance, defining the scenarios at 0.0058, integrating over Rr’s draw effect, and enumerating the base-rate sensitivities answer the main round-2 objection.

   My quadrature check with σ = 0.49 and the reported draw component gives:

   - Minimum host component: **1.448 × 10⁻¹²**.
   - Ceiling at ρ = 0: **1.7914 × 10⁻⁵**.
   - ρ for 7.6 × 10⁻⁶: **0.6037**.
   - ρ for 1.52 × 10⁻⁵: **0.1673**.

   These support the revised scenario labels. Numerical calibration should govern the script; the quoted scaling factor “about 1.54” is approximate—this particular calculation gives about **1.57**.

   Change “at equal rates the two arms’ count-scale variances are equal” to qualified wording. With Rr’s draw term, even the draw-averaged host variances differ slightly; total count variances additionally contain Rr’s draw contribution.

   I verified the corrected inputs directly: first-pass unresolved totals **42/51/60**, T/Rr ranges **0–7/0–12**, oscillation totals **30/24**, and K’s single unresolved-to-separate transition, giving **1/153**. The pilot count variances, correlation and contrast SD also reproduce. The fitted-rate calibration check and plain-reader reproduction mode address Fable’s corresponding corrections.

   Finally, the new [audit-noise paragraph](D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:305) overstates equality. Equal τ in both arms does not make latent and protocol contrasts exactly equal when fading shares differ. The expected additional contrast from unaudited fading transitions is
   \[
   \tau\bigl(f_T^{un}-f_{Rr}^{un}\bigr).
   \]
   Retain the raw-only and τ = 0 comparisons, but describe audit noise as the contribution to quantify, rather than declaring every qualification false.

A short amendment settling points 1 and 2, plus those wording corrections, is sufficient before the script is written.