**Verdict: revise.** I accept the two-arm contrast and the revised primary estimand. The pilot needs a few concrete fixes before running; the audit policy remains consequential for the power calculation.

I checked both round-one reviews, the construction and classification code, and M4e’s panel records. The records confirm 33 unresolved T genomes and 37 K genomes, zero shared separate-state genomes between T and K, and 10.479 CPU hours for those two arms. I changed no files.

1. **K\* = Rr: accepted, with one wording clarification.**

   [M4d’s implementation](/D:/Claude/random/wormWars/scripts/memory_m4/m4d.py:196) does preserve the labelled degrees, each source’s anatomical outgoing weight collection, the exact diagonal, and the total reciprocal-pair count. Rr already includes N2’s autapses.

   Say **“anatomical weight magnitudes”** when describing preserved outgoing weights. Genome signs are assigned by labelled source–target position in [paired_genome](/D:/Claude/random/wormWars/scripts/memory_m4/m4d.py:370); they do not travel with rewired edges. Consequently, each genome’s signed outgoing weight collection and signed out-strength are not preserved.

   With that clarification, I accept the proposed estimand wording and T/Rr as the only formal arms. The algorithm-defined null is defensible. Comparing 5,200 and 10,400 accepted swaps using structural summaries is useful sensitivity analysis; it does not establish mixing or outcome-level invariance.

2. **Primary and secondaries: accepted; the qualifier needs correction.**

   “Fraction of all sampled genomes confirmed as separate states by this protocol” is a coherent primary. Accept the proposed secondaries, but call the composite **“not classified as fading”**: unresolved genomes contribute by definition, without demonstrating persistent dynamics.

   The unresolved-rate-difference qualifier does **not** establish when hidden control switches could explain the advantage. Let \(c_a\) denote confirmed share and \(u_a\) unresolved share. Conditional on the other classifications being correct, the underlying separate-state contrast lies in
   \[
   [\,c_T-c_{Rr}-u_{Rr},\quad c_T-c_{Rr}+u_T\,].
   \]
   For example, a confirmed advantage of 0.002 and unresolved shares of 0.003 in **both** arms permit an underlying contrast from −0.001 to +0.005. Your proposed excess-unresolved trigger would not fire.

   Keep an excess-unresolved flag if useful, but label it descriptively. Use the envelope to assess whether unresolved genomes could reverse the broader interpretation. An untriggered flag must not license a claim about underlying separate states beyond the protocol.

   I also reject **“0.002 is roughly the smallest effect this classifier can resolve”** as justification for this primary. Classification uncertainty limits inference about underlying states; it does not impose a universal 0.002 resolution floor on a fixed protocol’s confirmation rate. “Two additional confirmations per thousand would justify the experiment” is sufficient rationale.

3. **Audit: explicit nonvalidation is better than fallback, but I prefer a prespecified completion branch if affordable.**

   The proposed failure branch is interpretable and preferable to reverting globally to the shorter pass. However, its power consequences are much stronger at the enlarged audit size.

   Under independent audited transitions:

   | Transition probability | Probability of zero transitions |
   |---|---:|
   | 0.0005, one arm with 3,000 audits | 22.3% |
   | 0.0005 in each arm, 6,000 audits total | 5.0% |
   | 0.0001 in each arm, 6,000 audits total | 54.9% |

   If any transition prevents a conclusive reading, these are upper bounds on unconditional success, irrespective of host count. **A transition rate below the proposed 0.001 error budget can nevertheless make 80% power impossible.** The pilot’s zero-transition result cannot safely be fitted as a transition probability of zero.

   My preference is to cost a branch that, after any triggering transition, continues **all remaining first-pass fading genomes in both primary arms** to the specified horizon. Applying complete ascertainment to both arms avoids introducing an asymmetric classification effort. If that branch exceeds a fixed cap, report classification incomplete and give descriptive results. An affected-arm-only completion is possible, but its residual asymmetry needs explicit simulation and interpretation.

   This branch can be selected after the exploratory pilot and before formal registration. Retaining nonvalidation is also acceptable if the report openly shows scenarios where no allocation qualifies.

   Three details must be explicit:

   - **Trigger:** [M4e’s predicate](/D:/Claude/random/wormWars/scripts/memory_m4/m4e.py:526) detects first-pass fading → separate states, not every class change. Define the primary trigger and report all transitions, including those affecting “not classified as fading.”
   - **Confidence:** zero among 3,000 gives an individual one-sided 95% upper bound of 0.000998. Simultaneous 95% bounds below 0.001 for both arms require **3,688 per arm** using Bonferroni. Choose individual or simultaneous assurance explicitly.
   - **Denominator:** the audit bounds transitions among first-pass fading genomes. Their contribution to an all-genome rate also depends on the fading fraction. These bounds do not automatically turn the primary interval into a confidence interval for latent states.

4. **Pilot: keep (a), (b), and (c), with these fixes before execution.**

   **Replay is necessary.** M4e’s panel files contain classifications and timings, but no tick-22,000 checkpoints. The [second-pass output](/D:/Claude/random/wormWars/scripts/memory_m4/m4e.py:435) discards endpoint states, and I found no checkpoint artifacts in its run directory. Specify deterministic reconstruction from the original genomes, signs, and numerical settings; reproduce the relevant stored classifications before extending them. Include replay in the cost estimate. For new Rr panels, retain the required states locally.

   **Define the audit population precisely.** Sample from **first-pass fading** genomes, not merged fading genomes. The latter includes unresolved genomes already resolved by the second pass and is a different population. State whether 1,500 means additional audits or total unique audits. I recommend additional, previously unaudited genomes, sampled without replacement, with overlap checks. Existing T and K audits contain 783 and 786 fading genomes respectively.

   **Freeze the pilot’s reporting branch.** “Classified exactly as M4e” imports its global fallback unless explicitly overridden. Save and report first-pass classes, mechanically merged second-pass classes, audit transitions, and audit status separately. A new Rr audit failure must not change the historical T/K classifications used for the pilot comparison or M4e’s published reading.

   **Fix the seed families.** They are not entirely new. M4e uses `20261601 + 100(2h+d) + arm` for audits:
   - proposed Rr seeds **20261701** and **20261801** already occur in that family;
   - proposed large-audit seeds beginning **20261801** also overlap it;
   - **20261801** occurs in both proposed pilot families if the audit arm index starts at zero.

   This does not prove consequential dependence, but it is avoidable. Freeze distinct streams by experiment, phase, arm, host, and draw.

   **Record enough for the later model.** Add the full paired outcome tables and transition tables by host/draw, not only shared switch IDs. For construction diagnostics, record attempts/acceptance and weighted similarity as well as support overlap and S3. Specify whether the longer chain continues the shorter chain; I prefer that paired comparison.

   Finally, the 100,000-tick pilot assesses continuation of **22,000-tick unresolved genomes**. It does not validate every classification at 100,000 ticks. If M5 adopts a generally longer classification horizon, its audit must address that horizon too. Fix an exploratory compute cap and incomplete-output rule; the Rr unresolved workload is not yet known.

5. **Power calculation: broadly accepted, with several remaining specifications.**

   - **Separate protocol truth from latent-state truth.** Control-enriched unresolved outcomes can create a real difference in confirmation rates when latent separate-state rates are equal. Under the new primary, that is not automatically a statistical false “raises.” Simulate zero *protocol* contrast for type-I error, and separately report misleading interpretations of latent-state contrasts.

   - **Measure unconditional success.** Audit failure, cap exhaustion, invalid runs, and any other no-reading branch must remain in the denominator. Report probabilities of unqualified “raises,” qualified “raises,” nonvalidation, and exclusion separately. State which event the 80% requirement concerns.

   - **Specify the stratified interval and deletion rule.** Define the Student-t component’s standard error and degrees of freedom. After leaving out a host, retain the five ensembles’ fixed one-fifth weights; ordinary pooling would change the estimand. The exclusion should explicitly concern the mean protocol contrast. Leave-one-host-out stability does not exclude substantial effects in rare host subpopulations.

   - **Carry parameter uncertainty beyond the historical point estimates.** The range across historical fitted host variances is a scenario range, not a confidence bound on M5’s variance. Include uncertainty within those sources, boundary estimates, and plausible nonzero audit-transition rates. Zero observed paired switches likewise does not establish exactly independent outcomes.

   - **Complete the scalable-envelope specification.** “Largest achievable spread” still needs an algorithm. A safe, simple alternative is an explicit variance upper bound: for any fixed centre \(c\), a host vector with \(d_i\in[l_i,u_i]\) satisfies
     \[
     s^2(d)\le
     \frac{\sum_i\max\{(l_i-c)^2,(u_i-c)^2\}}{H-1}.
     \]
     Combining this bound with the all-low and all-high means gives conservative t endpoints for the existing pooled-t construction. Adapt it if using stratified variance, and check containment against exhaustive small examples.

   - **Account for selecting among simulated cells.** Pointwise 95% Monte Carlo lower bounds do not provide simultaneous assurance after searching the grid. Use simultaneous bounds or an independent, prespecified confirmation simulation for the selected allocation. Specify the analogous rule for 90% power.

   - **Calibration is not sabotage.** Reproducing M4e’s observed half-width—**0.0039104**, confirmed in its [reading](/D:/Claude/random/wormWars/runs/memory-m4e/readings.json)—is a useful fitted-model check. It does not independently validate coverage. Add deliberate failures of pairing, audit branching, stratum weights, and marginal-effect calibration, plus null rejection checks and exclusion-boundary checks at ±0.002.

The immediate revision is to make the pilot’s replay, audit sampling, reporting branches, seeds, and cap concrete. The formal audit completion policy and final interval implementation can then be settled using the pilot before producing the power recommendation.