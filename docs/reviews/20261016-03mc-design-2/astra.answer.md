**Revise.** The main statistical corrections are sound, but v1’s requests for joint power modelling and complete probe validation are only partly resolved.

1. **The equivalence check still omits two promised outputs.**  
   [p4mc_equivalence.py:78](/D:/Claude/random/wormWars/scripts/p4mc_equivalence.py:78), [test_exp03_twin.py:60](/D:/Claude/random/wormWars/tests/test_exp03_twin.py:60), [DESIGN.md:314](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:314).

   The script measures per-genome tick-30 differences, but **never computes the error in the aggregate retained share**. It also contains **no pre-tanh comparison**. The pre-tanh test checks shape and inequality from the tanh result; a wrongly scaled or sign-reversed pre-tanh result could pass.

   I found no corresponding formula error in `twin.py`. Its raw-turn extraction correctly handles both rows; its range and slope calculations match `history_full` mathematically. Independent checks gave:

   - All six existing test functions passed when invoked directly.
   - A six-genome CPU comparison against `history_full` gave whole-curve relative error \(4.16\times10^{-5}\).
   - An independent sequential-state calculation gave pre-tanh errors below \(4.8\times10^{-7}\).
   - GPU tick-30 retained-share errors on N2, SH-mirror-40010 and SH-mirror-40015 were \(1.16\times10^{-8}\), \(3.40\times10^{-7}\) and \(3.63\times10^{-7}\).

   These support the implementation and proposed tolerances, but do not replace executable checks in the repository.

   **Fix:** add direct sequential-reference tests for both pre-tanh terms, including a sabotage check; record aggregate retention errors in `equivalence.json`; explicitly include pre-tanh outputs in the formal equivalence contract.

2. **The settling evidence names the wrong worst-case graph, and the tolerance margins are overstated.**  
   [DESIGN.md:309](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:309), [equivalence.json:977](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/equivalence.json:977).

   The largest end-range error, **0.329738**, belongs to **SH-mirror-40015**, not SH-recip-50015. The latter’s error is about 0.030.

   I reran the actual worst graph on the old inputs: no settled or remaining-separation labels changed, and the settled-with-separation count remained zero. N2 likewise retained its count of 26. Thus I found a reporting error, not evidence of a changed scientific classification.

   Two numerical qualifications also need correction:

   - \(10^{-4}/2.65636\times10^{-5}=3.76\), so the hold-range tolerance is **not “at least 4.5 times”** the measured maximum.
   - “50 times the worst measured” is supported approximately for the original P4 terms, **not for retained share**, which the committed report does not measure. My three-graph check already gives a smaller margin.

   **Fix:** correct the graph and margins; commit the label-comparison calculation and results. Include the actual worst graph in the pre-run settling checks. Checking only an aggregate count on N2 can miss offsetting label changes.

3. **`power.json` is exactly reproducible, but the simulation still does not implement the joint uncertainty requested in v1.**  
   [power.py:124](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/power.py:124), [power.py:145](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/power.py:145), [DESIGN.md:367](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:367).

   I executed `main()` with its file write intercepted in memory. **The entire generated JSON matched the committed JSON exactly**, including the three local-array hashes. The reported Holm probabilities—A 0.9724, B 0.76755, C 1, D 0.7846, all four 0.6387—are what this code computes. The Holm loop and fixed-sequence calculation are correct.

   However, independence is imposed both **between questions and within Q-B**. My 6,000 paired bootstrap draws from the local arrays gave approximate correlations:

   - RIA ΔP4 versus AIY ΔP4: **0.44**;
   - RIA cut versus AIY cut: **0.47**;
   - Q-A’s N2 change versus RIA ΔP4: **0.40**.

   Also, Q-C is hard-coded to \(p=1/257\). Its reported power of 1.00 is an assumption, not an estimated probability. Consequently, “N2’s sampling uncertainty enters every question” is false.

   **Fix:** add a joint-bootstrap or covariance-preserving sensitivity calculation. Preserve shared N2 uncertainty and account for Q-B sharing only batch 0 with the other questions. Label Q-C’s result explicitly as conditional on assuming zero exceedances, and assess a nonzero-exceedance scenario. These omissions affect prospective probabilities; they do **not** invalidate Holm’s error control.

4. **Q-A’s regression and Q-D’s posterior draws are implemented coherently, but their modelling limits need fuller treatment.**  
   [power.py:76](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/power.py:76), [power.py:128](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/power.py:128), [power.py:135](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/power.py:135).

   **Q-A:** the ensemble intercepts, common slope, residual degrees of freedom and historical intact-P4 pools are correct. I independently recovered slope **−0.256257**, residual SD **0.0143491**, and conventional slope SE **0.03007**. The extrapolation genuinely reaches beyond the fitted panel—for example, SH-route’s panel maximum is 0.89095 versus 0.93370 in its historical pool.

   But the code fixes the fitted coefficients and residual SD. It propagates residual variation, **not regression-fit uncertainty**. A common linear slope and Gaussian residual tail are consequential assumptions for an extreme-rank endpoint.

   **Q-D:** the inverse-chi-square variance draw followed by the conditional normal mean draw is correct under the normal model with reference prior \(p(\mu,\sigma^2)\propto1/\sigma^2\). Drawing those parameters once per ensemble per simulated study correctly propagates fit uncertainty. The `sqrt(2)` N2 SD combines old-estimate and equally sized fresh-sample uncertainty under the stated normal approximation; that is not accidental double-counting.

   **Fix:** name Q-D’s prior; add Q-A coefficient/variance uncertainty and sensitivity to graph-tail assumptions. Describe these as **model-based predictive pass probabilities**, conditional on the chosen models—not established operating characteristics.

5. **Q-B’s two-stage draw and primary tests are acceptable approximations; its secondary tests remain underspecified.**  
   [power.py:142](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/power.py:142), [DESIGN.md:160](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:160), [DESIGN.md:193](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:193).

   The two-stage draw is mathematically consistent: marginal variance is \(s_{2048}^{2}(1+2048/n)\). The old-data uncertainty therefore remains even as the fresh sample grows. This is predictive assurance, rather than power conditional on a fixed true effect.

   **Answer to §10.2:** at 65,536 genomes, the proposed normal-theory tests with paired bootstrap SEs are reasonable for these ratios of means, assuming valid denominators. The TOST signs and maximum-p conjunction are correct. I do not require replacing them with bootstrap-tail p-values; a bootstrap tail is not automatically better calibrated.

   **Answer to §10.3:** I reproduced both control lists and their degrees. Total degree is a defensible coarse match, and four prespecified controls per target is acceptable. It does not match chemical/gap composition, direction, weight strength or functional position, so conclusions should remain about these named controls.

   However, “one-sided bootstrap tests” for the controls repeats v1’s ambiguity. Several descriptive “bootstrap intervals” also lack a method and confidence level.

   **Fix:** specify the control contrast and p-value formula—paired cut difference divided by its bootstrap SE would be consistent with the primary analysis—and specify interval methods, levels, resampling units and seeds.

6. **The claimed tick-selection comparison is not supplied by the committed calculation.**  
   [DESIGN.md:240](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:240), [power.py:40](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/power.py:40).

   The design says tick 30 has the highest simulated pass probability among ticks 10–50. `power.py` fixes `TICK = 30`, and `power.json` contains only that endpoint. I could not verify the comparative claim.

   **Fix:** commit the endpoint-comparison calculation and table, or remove that claim while preserving the disclosure that tick 30 was selected after inspecting 03m. Tick 30 itself remains a legitimate confirmatory endpoint on fresh data.

7. **Disposition of the v1 findings: mostly fixed, not all fixed.**  
   [DESIGN.md:457](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:457), [DECISIONS.md:8782](/D:/Claude/random/wormWars/DECISIONS.md:8782).

   Against the twelve findings in the local Astra v1 review:

   - **1–3, 5–7 and 9:** resolved at the design level—larger Q-B sample, explicit primary tests, corrected rank denominator/family handling, narrower interpretations, and corrected permutation count.
   - **4 and 8:** only partly resolved, for the power and equivalence reasons above.
   - **10:** control selection and factorial contrast resolved; secondary test construction still needs precision.
   - **11–12:** substantially addressed in the design, but enforcement remains future code. The cap’s “under a minute” overrun also needs qualification or a bound covering build and analysis units, not just probes.

   **Fix:** replace D286’s blanket “every finding … taken” disposition with these qualifications. Complete the specified algorithms and validation contract before freezing the pre-registration; retain the planned implementation review before any formal run.

I did not modify files. I reproduced the power calculation, executed the six tests directly, and ran the additional CPU and three-graph GPU checks described above. The GPU checks consumed **84.2 seconds and 161,218,560 neural updates**, counted in memory. I did not rerun the full 81-graph equivalence panel, verify the historical sabotage runs, or validate the future driver. An external edit to `scripts/exp03.py` appeared during this review; it adds new instance definitions and was outside this review of commit `1673ad5`.