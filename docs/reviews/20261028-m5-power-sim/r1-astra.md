**Verdict: revise.** The script should wait for corrections to the audit bound, the generative model, and rule C’s acceptance criteria. The underlying T-versus-Rr question and protocol primary remain acceptable.

I checked the archived reviews, pilot report and source panels, audit records, and M4e’s classification and interval code. I reproduced these inputs:

| Quantity | Recomputed |
|---|---:|
| T / Rr confirmations | 75 / 59 |
| T / Rr unresolved | 33 / 47 |
| Host count variances, T / Rr | 22.500 / 15.433 |
| Cross-host T–Rr correlation | 0.70061 |
| T–Rr host-contrast SD | 0.00335776 |
| Untruncated host component | −2.07689 × 10⁻⁶ |
| Draw / genome variance components | 1.53065 × 10⁻⁶ / 2.51722 × 10⁻⁵ |
| SD implied by the truncated components | 0.00365396 |
| Mean panel seconds, T / Rr | 978.600 / 1128.965 |

M4e’s published T−K interval also reproduces exactly from its reader functions and records. No files changed; no neural experiments ran.

My answers follow in priority order.

1. **Q3 — The audit estimator is usable as a sensitivity, but its advertised 95% bias limit is wrong under the proposed stopping rule.**

   I accept the fading→separate trigger, its application to both arms, adjustment only of unaudited fading genomes, and omission of an unsupported risk stratum.

   **The adaptive Clopper–Pearson bound fails even under homogeneous independent transitions.** Reading the trigger as global, take a grid cell with H=30, D=2, and the specified Rr-only scenario, τ=0.00131:

   - First tranche: 2,400 fading genomes per arm.
   - If Rr has zero transitions, sampling stops. Its upper bound is **0.00124744**, below the true rate. This happens with probability **0.04302125**.
   - If the second tranche runs, the final Rr sample is 9,600. Cases with at most six total transitions contribute another **0.02569929** probability of undercoverage.
   - Total undercoverage is **0.06872054**: coverage is **93.13%, not 95%**.

   I obtained this by exact binomial summation, not Monte Carlo. Thus “the simulation measures the whole procedure” needs an explicit **bound-coverage check and repair**, not just measurement of power. Use a bound valid for the two-stage sampling rule, stagewise bounds with a prespecified error allocation, or a fixed audit size.

   Pooling also needs qualification. Equal numbers audited per panel estimate an average of panel transition rates; hidden confirmations depend on those rates **weighted by unaudited fading counts**. These differ under heterogeneity. The common pooled estimate can remain a labelled common-rate sensitivity, but it is not automatically a bound on the heterogeneous population. Include arm-specific host concentration and panel concentration, and assess coverage of the actual hidden contribution.

   There are two concrete protocol corrections:

   - **M4e did not sample 40 fading genomes.** [`audit_ids`](D:/Claude/random/wormWars/scripts/memory_m4/m4e.py:353) samples 40 IDs from the entire panel. The historical fading denominators are 783 for T and 786 for Rr across 20 panels. Choosing 40 fading genomes is reasonable, but call it a change and account for its classification composition.
   - After 160 audits in G=512, the pilot Rr fading share leaves approximately **0.67354** unaudited. At τ=0.00131 the expected hidden contribution is **0.0008823**, not 0.0012. The latter approximates the branch with only 40 audits.

   Finally, specify the global trigger and scheduling explicitly, particularly whether later hosts can trigger additional classification of the internal pilot’s earlier hosts.

2. **Q2 — The proposed model does not yet define mutually consistent probabilities and variance scenarios.**

   The shared host effect is supported as a parsimonious working model. The approximate lognormal SDs inferred separately from the two arms’ overdispersion are **0.487 and 0.493**, consistent with “about 0.5.” T needs no additional random block-draw term: the construction code supports that choice.

   But several definitions in [section 2](D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:76) conflict.

   **First, constant host contrast and nonzero contrast host variance cannot both hold.** If
   \[
   p_{T,h}=p_{Rr,h}+\delta
   \]
   in every host, then its host variance is zero. That cannot simultaneously implement the 7.6e−6, 1.52e−5 and 3e−5 scenarios. If “constant” means a constant *increment to an already heterogeneous baseline contrast*, write that instead and provide the construction.

   **Second, define host probabilities after integrating over Rr’s draw effect.** With a nonlinear logit link and a draw term only in Rr, a shared \(u_h\) need not cancel in the conditional host contrast. Therefore “\(w\) alone makes the host component” is not generally true. Calibrate the host variance using the draw-averaged probabilities, and jointly verify the marginal means and draw variance.

   **Third, calibrate δ after the complete protocol.** The current \(p_a\) produces first-pass confirmations, then audited transitions add confirmations to raw S. Thus calibrating \(E(p_T-p_{Rr})=\delta\) does not calibrate the stated primary under asymmetric transitions. This can mislabel real protocol effects as type-I errors. Calibration must include the audit sampling and trigger, potentially separately for each allocation.

   **Fourth, the ±0.004 null needs a valid probability construction.** At the 0.0031 baseline, subtracting 0.004 is already impossible without random effects. Clipping changes the mean: with that constant baseline, clipping equal-probability ±0.004 effects produces a positive mean contrast of **0.00045**. It is no longer a null. Preserve the mean explicitly.

   **Fifth, independent class counts are not an exact categorical model.** Independently drawing separate, unresolved and oscillation counts permits their sum to exceed G. Nor can first-pass fading remain fixed at 98.6% while the other first-pass probabilities change. Use coherent categorical counts and first-to-final transition counts. Count-only simulation is sufficient, provided it preserves those constraints and audit sampling without replacement.

   I would also include host-persistent unresolved propensity and its association with confirmation propensity as sensitivities. Independent per-panel beta-binomials silently impose an important dependence assumption. The pilot is too small to estimate that structure reliably, but it does not justify deleting it.

3. **Q4 — Choose A as the default. C is a candidate to evaluate, not yet the recommended design.**

   A is the clearest commitment to the chosen upper core scenario. It is robust **within that scenario specification**, not a demonstrated bound on the unknown variance. B is defensible only if the owner explicitly accepts its reported loss of power.

   The rationale for C overstates what variance-only adaptation establishes. Independence of the interim mean and variance under an ideal normal model does **not** make the final ordinary t procedure automatically valid after sample-size selection. Internal-pilot methods can produce downward bias in the final variance estimator and inflate type-I error even with Gaussian observations. [Coffey, Kairalla and Muller](https://pmc.ncbi.nlm.nih.gov/articles/PMC3867302/) discuss and address this directly.

   For C, freeze these matters before coding:

   - The lookup maps **observed total host-contrast variance**, including genome and draw sampling, to H—not the latent host component. Specify the nuisance settings, interpolation, out-of-range handling and rounding.
   - Both stages preserve balanced ensemble allocation.
   - Define which audit results enter the interim variance and what happens if a later audit trigger changes earlier hosts’ final counts.
   - Fix the cap before the run and simulate its interaction with the adaptive H.

   C must then demonstrate, in independent validation simulations:

   - Acceptable directional type-I error for **raw raises**, as well as the unqualified event, with a numerical acceptance threshold fixed in advance.
   - The required unconditional power throughout the scenarios claimed to govern the design.
   - The distribution of final H, frequency of hitting H_max, incomplete-run probability, and expected and upper-tail cost.

   **H_max equal to A’s minimum qualifying H does not itself protect C’s power.** At the upper variance scenario, interim underestimation can select smaller samples than A. Simulate the adaptive policy as a whole; fixed-H table qualifications do not transfer to it.

   If C passes these checks and saves meaningful compute, I would reconsider the preference for A.

4. **Q1 — The reading is largely acceptable, but “conservative” and “unqualified” need narrower definitions.**

   For balanced fixed-H sampling, the plain-s² t component is a defensible conservative addition to the stratified bootstrap. Including between-ensemble mean variation makes its variance estimate conservative **in expectation**. That is not a general finite-sample coverage theorem for sparse, heterogeneous host outcomes.

   After a deletion or invalid-panel exclusion, the proposed pooled variance formula is not generally conservative under unequal stratum sizes and unequal variances. For example, with remaining stratum sizes (1,2,2,2,2), equal stratum means, and variance concentrated in the singleton stratum, its expected variance estimate is only **one third** of the estimator’s actual variance.

   Keep the fixed one-fifth weights. Either justify and validate the pooled-t procedure under the relevant heterogeneity, or use a specified stratum-aware variance procedure. Define minimum surviving hosts per ensemble; an empty stratum cannot retain an estimable one-fifth mean.

   I accept the leave-one-host-out exclusion guard with its limited wording. I also accept the scalable envelope variance bound: it holds for **any fixed centre**.

   “Unqualified raises” under the symmetric audit scenario is an acceptable planning event for **protocol confirmations**, with asymmetric scenarios reported as limits. However:

   - The current event requires passing audit and unresolved sensitivities **separately**. Passing both separately does not imply passing their combined adjustment. State whether a joint adjustment is required.
   - Recomputing interval width means a favourable count adjustment need not invariably preserve “raises.” Replace “only Rr’s transitions can remove raises” with a statement about the direction of the **point-estimate** adjustment.
   - Survival of these checks does not identify the underlying-state contrast when the logical envelope permits reversal, as already agreed.

   Reconcile “every panel valid” in the success definition with dropping invalid hosts and reading the remainder. Under independent 1% panel invalidity, H=30, D=2 has probability only **0.2994** that all 120 arm panels are valid. If that is mandatory, it is already an upper bound on unconditional success.

5. **Q5 — The Monte Carlo plan needs a selection correction; the cost model is a baseline rather than a validated cap model.**

   R=4,000 with a one-sided lower bound is reasonable for power refinement. At that R, at least **3,242 successes** are needed for the 80% qualification.

   But independent confirmation followed by “try the next H” reintroduces repeated selection. A succession of pointwise 95% confirmations does not provide 95% assurance for the eventual selected cell. Use prespecified error spending or simultaneous bounds across confirmation attempts, or one independent confirmation followed by an explicit failure outcome. Address selection across allocations too.

   Null-error validation needs a separate precision budget. At a true rate of 0.025, R=4,000 has Monte Carlo SE **0.00247**. That is too imprecise to dismiss modest inflation in C. Specify the acceptable upper error rate and allocate substantially more null replicates near that boundary.

   Whole-host resampling of the four pilot panel times preserves useful arm and draw dependence. I accept it as a baseline. But independent resampling of costs from simulated outcomes loses a material association: pilot panel time correlates with unresolved count at **0.747 in T and 0.845 in Rr**. Include a cost–difficulty coupling sensitivity before interpreting unconditional success or cap tails.

   The second tranche is almost routine under the planning scenario. At H=30, D=2, symmetric τ=0.00131, its trigger probability is **0.99815**. The verified baseline is **1.17087 CPU hours per host**; measured fading-continuation costs make the extra tranche approximately **0.4784 hours per host**. The resulting baseline is about **1.65 hours**, before fixed overhead. That cost belongs prominently in the planning answer.

   Doubling the entire panel time for G=1024 also doubles the historical first-audit cost although the proposed first tranche stays at 40. Separate costs that scale with G from fixed audit and construction costs. Linear scaling remains a labelled sensitivity until benchmarked at the intended composition.

   Finally, specify which cap—1.25 or 1.5 times which expected cost—governs qualification, or produce separate qualifying tables for both.

Two proposed sabotages also need replacing. Subtracting or adding a common mean shift leaves sample variance unchanged; it cannot sabotage s². And a “bad” fixed centre cannot invalidate the stated envelope inequality, only loosen it. Sabotage an actually invalid variance calculation or bound, and test that the check detects it.