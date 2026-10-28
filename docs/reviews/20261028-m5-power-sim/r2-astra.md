**Verdict: revise.** The fixed audit and the independent confirmation rule answer major round-1 objections. The remaining problems affect the model being simulated, the success event, and rule C’s specification.

I checked both reviews, draft 2, the pilot report and panel records, and M4e’s audit, merging and interval code. I reproduced the main pilot quantities: confirmations 75/59, host count variances 22.500/15.433, correlation 0.70061, and contrast SD 0.00335776. No files changed and no neural experiments ran.

Below are my answers to the five questions, ranked by importance.

1. **Q2 — The model still contains incompatible variance specifications and two incorrect calibration inputs.**

   [Section 2](D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:107) alternates between holding **logit-scale host variance** fixed and holding the pilot’s **probability/count-scale host variances** fixed. Those are different models once the marginal rates change.

   Your formula fixes logit variance near \(0.49^2\). Under that formula, setting both marginal rates to 0.0058 at zero effect does not preserve T’s pilot count-scale host variance of 15.1. Its host variance becomes approximately Rr’s.

   I checked the permitted zero-draw scenario by logistic-normal quadrature:

   | Common marginal rate | Maximum contrast host variance at \(\rho=0,\ \sigma=0.49\) |
   |---|---:|
   | 0.0031 | \(5.164\times10^{-6}\) |
   | 0.0058 | \(1.792\times10^{-5}\) |
   | 0.0090 | \(4.271\times10^{-5}\) |

   Consequently:

   - At 0.0031, neither \(7.6\times10^{-6}\) nor \(1.52\times10^{-5}\) is attainable by lowering a nonnegative correlation.
   - At 0.0090, reaching \(3.0\times10^{-5}\) from \(\rho=0\) requires scaling variance **down**, contrary to the stated construction.
   - At 0.0058, the correlation producing \(1.52\times10^{-5}\) is approximately **0.168**, not 0.36, in this zero-draw case. The 0.36 calculation uses the unequal pilot probability-scale variances.

   If you instead preserve those unequal pilot variances, zero contrast variance is impossible: its minimum is
   \[
   (\sqrt{15.1}-\sqrt{9.5})^2/1024^2 \approx 6.16\times10^{-7}.
   \]

   **Required repair:** choose which variance scale is fixed, specify the scenario combinations, and define what happens whenever a target is unattainable. If baseline-rate sensitivities are not crossed with the variance scenarios, enumerate that explicitly. Holding logit variance fixed is a reasonable choice; describing it as preserving each arm’s pilot probability variance is wrong.

   The nonlinear draw-effect issue is now acknowledged correctly, but that also means \(\rho=1\) does not give *exactly* zero contrast variance. With the fitted draw component, my calculation gives a residual around \(1.45\times10^{-12}\): practically negligible, but an exact zero-solving requirement is impossible. Label the central scenario as the minimum attainable variance or change the construction.

   Two record-based corrections are also needed:

   - First-pass unresolved panel ranges are **T: 0–7; Rr: 0–12**. The stated 0–6 and 0–10 are the final ranges.
   - The pooled first-pass unresolved→separate transition is **1/153**, if pooling T, K and Rr: their first-pass unresolved totals are 42, 51 and 60. **1/139 is wrong.** First-pass oscillation totals are T 30 and Rr 24; Rr’s 25 includes an unresolved→oscillation transition.

   The multinomial construction, first-to-final tables, whole-protocol calibration, constant-*increment* interpretation, host-persistent unresolved propensities, and added draw scenario answer the corresponding round-1 points. For the ± null, specify independent Bernoulli assignments per host; “half the hosts” could otherwise impose artificial exact balance.

2. **Q3 — The interval change is defensible, but the success predicate drops a required check and the envelope needs updating.**

   [The new success event](D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:75) requires raw, audit-adjusted and jointly adjusted “raises.” It omits the **standalone Rr-unresolved sensitivity** that draft 1 required.

   Joint success does not imply standalone unresolved success: the audit adjustment can favour T and compensate for the unresolved adjustment. A translation-invariant example suffices:

   | Reading | Lower endpoint |
   |---|---:|
   | Raw | +0.00005 |
   | Audit adjustment of +0.00020 | +0.00025 |
   | Unresolved adjustment of −0.00010 | −0.00005 |
   | Both adjustments | +0.00015 |

   Your current event accepts this as unqualified even though the unresolved sensitivity qualifies it.

   **Require all four:** raw, audit alone, unresolved alone, and joint. Adding the joint check should not remove either individual check.

   I accept the balanced pooled-t component with the stated “conservative in expectation” limitation. I also accept within-stratum variances and Welch–Satterthwaite degrees of freedom after imbalance, subject to the promised heterogeneous-variance simulations. Using different formulas in the two cases is a design choice, not inherently an error.

   However, [the envelope](D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:84) still supplies only the old pooled-variance bound. It does not specify a bound for the new Welch intervals, whose degrees of freedom vary with the corner.

   This matters even with permitted stratum sizes. For sizes \((2,3,3,3,3)\), contrasts \((-0.01,+0.01)\) in the first stratum and zero elsewhere, the ordinary pooled-t half-width is **0.002265**, whereas the Welch half-width is **0.025412**. Taking a box with identical lower and upper endpoints already exposes the missing extension.

   A sufficient conservative repair is to bound each stratum’s variance separately, combine those bounds using \(w_e^2/n_e\), and use \(t_{0.975,\min_e(n_e-1)}\). Test containment against the **new unbalanced reader**, not only M4e’s reader.

   Dropping invalid hosts while retaining fixed ensemble weights answers the round-1 denominator objection. But define the exclusion guard when an ensemble has exactly two valid hosts: its leave-one-out calculation would leave one. The exclusion should be unavailable in that case. The proposed singleton sabotage should also be supplemented by a permitted-size example that actually reaches the interval calculation.

3. **Q1 — Accept the fixed audit, with a remaining qualification for rule C’s bound.**

   [Fixed \(A\in\{40,80,160\}\)](D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:202), selected as part of the allocation, is acceptable. It removes the trigger, retroactive continuation and second-tranche scheduling problems. Sampling IDs from the entire panel matches `audit_ids`; replacing audited first-pass classifications matches `merged_classes`; adjusting only unaudited fading genomes avoids double counting. The changed D371 choice is disclosed.

   But “Clopper–Pearson is valid now because audit size does not depend on its outcome” is established only for **fixed H** under the common-rate model.

   Under C, final H depends on interim raw contrasts, which include audited transitions. Total audit sample size therefore remains outcome-dependent. Fixing A per panel does not establish fixed-sample coverage for the final pooled bound. I have not established the magnitude or direction of the resulting coverage error under your eventual C mapping.

   **Specify a remedy before coding:** for example, use the fixed-stage-1 audit for the guaranteed common-rate bound, use a stopping-valid construction, or explicitly validate and repair the final bound’s coverage under C. Power and false-“raises” validation do not establish audit-bound coverage.

   Two further distinctions:

   - A confidence bound on the common transition probability bounds the **expected hidden contribution** after multiplying by the unaudited share. It is not automatically a prediction bound on the realised hidden count. State which coverage the simulation checks.
   - The pooling explanation partly carries over an objection to the old “40 fading genomes” design. With fixed A sampled from G IDs, every genome has the same inclusion probability \(A/G\); fading-rich panels contribute more audited fading genomes in expectation. Thus the pooled denominator already supplies fading-count weighting. Indeed, \((G/A-1)\) times total audited transitions is a design-unbiased estimator of the total hidden transitions for fixed panels. Your pooled-rate sensitivity can remain, but its justification should reflect the revised sampling mechanism.

4. **Q4 — A remains my default. C’s mapping is closer, but it is not fully specified.**

   [The 75% inflation formula](D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:278) is the normal-theory upper-limit formula; at H1=25 its multiplier is approximately **1.261**. Treat it here as a **normal-reference inflation rule**, not a demonstrated 75% confidence limit for sparse, heterogeneous host contrasts. Its adequacy comes from validating the complete adaptive procedure. The underlying chi-square variance formula is documented by [NIST](https://www.itl.nist.gov/div898/handbook/eda/section3/eda358.htm).

   Four specifications remain:

   - **Freeze the lookup’s nuisance settings.** Total raw contrast variance does not uniquely determine unqualified power. Different audit noise, unresolved distributions and effect heterogeneity can have the same raw variance. Name the reference model generating each allocation’s lookup, including the effect at which its variance is indexed. This was explicitly requested in round 1.
   - **Separate H_max discovery from confirmation.** Explore candidate caps, freeze the proposed policy, then use the limited independent confirmation procedure. Do not repeatedly search for the next “confirmed” H_max. Allow “C not confirmed/no feasible cap.”
   - **Define interim invalid-host handling.** The stated H1−1 factor and balanced extension assume all stage-1 hosts survive. Specify the action when they do not.
   - **Define “H_max’s cost.”** Mean cost or a specified quantile must produce a fixed cap in seconds before validation. It cannot mean the realised cost.

   Simulating C itself to determine its cap addresses the earlier mistaken transfer of A’s power guarantee. Requiring validation throughout the core scenarios is right. The **20% central-scenario saving** is an acceptable prespecified threshold for recommending C, provided A and C are compared using the same cost components.

   Delete “at \(3.0\times10^{-5}\)…less than 80% by construction.” With H_max newly determined by adaptive-policy simulation, that conclusion is no longer guaranteed. Measure and report it.

   One correction to my own round-1 review: the cited Coffey–Kairalla–Muller paper was published in **2007**; 2013 is its PMC availability date. Its warning about ordinary testing after internal-pilot adaptation remains applicable. [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC3867302/)

5. **Q5 — Accept the confirmation repair and precision budget; qualify the error tolerance and freeze the cost cap’s reference scenario.**

   [One independent confirmation batch at H and H+5](D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:244), Bonferroni adjustment over the candidate allocations and two host counts, and “not confirmed” without further searching correctly answer the round-1 selection objection. Define the scope of K explicitly for the 80% and 90% columns and C policies. Call the result the **smallest confirmed host count tested**, rather than claiming the true minimum.

   The null gate is precise enough to enforce the proposed tolerance. At R=40,000, a one-sided 95% Clopper–Pearson upper bound ≤0.030 requires **at most 1,143 false raises**, an observed rate ≤0.028575.

   I accept 0.030 as an explicitly chosen exploratory acceptance tolerance. It permits **20% relative inflation** over nominal 0.025; it does not certify nominal control. For perspective, a procedure whose true false-“raises” rate is 0.0275 passes this gate about **90.8%** of the time. Keep that distinction in the eventual report.

   The cost–difficulty coupling, whole-host residual resampling, separation of G-dependent and A-dependent costs, and overhead sensitivity answer my round-1 cost points. The orientation of approximately 1.17 hours per host and another 0.48 hours for A=160 at D=2 is consistent with the records.

   One ambiguity remains: **which scenario’s mean fixes A/B’s cap?** Choose a reference scenario and freeze its cap in seconds across subsequent sensitivities. Recomputing “1.5 times mean cost” separately under each simulated difficulty scenario would change the operational policy while ostensibly evaluating it.

The other round-1 corrections are answered: protocol versus latent truth is distinguished; the unresolved-share flag is defined; concentrated audit scenarios and the alternative host-variance parametrisation are included; favourable point-estimate movement is no longer confused with interval monotonicity; and the two ineffective sabotages have been replaced.

**I would not approve writing the script against this draft unchanged.** Resolve the variance specification, restore the standalone unresolved check, extend the envelope, and finish C’s lookup and audit-bound rules first.