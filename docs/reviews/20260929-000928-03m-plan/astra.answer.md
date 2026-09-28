**Revise before running.** The core P4 calculation follows 03, but the runner has validity and execution gaps, and several interpretations exceed what these interventions can establish.

This was a static review: I read the requested files and relevant initialization, interface, accounting, and test code. I ran no simulations, tests, or statistical recomputations.

I would require these changes before running:

1. **Validate the deletion batch composition, or keep each deletion at 2,048 strains.**  
   [`history_in_chunks`](/D:/Claude/random/wormWars-p4/scripts/p4m.py:183) correctly concatenates complete genome blocks, repeats each deletion list 2,048 times, and slices the results back into matching blocks. I see no indexing bug. However, its default evaluates eight deletions together at 16,384 strains; the reproduction check evaluates 2,048. D090–D092 specifically document composition dependence with **one row per strain**, which is this probe’s shape. The existing check therefore does not establish numerical comparability for lesions. Check intact copies and representative deletions against separate evaluation, including remainder batches, at a tolerance declared beforehand. Alternatively, use one whole deletion per batch.

2. **Do not turn invalid P4 values into valid-looking percentiles.**  
   [`p4_of`](/D:/Claude/random/wormWars-p4/scripts/p4m.py:116) returns `NaN` below the denominator floor, but [`null_position`](/D:/Claude/random/wormWars-p4/scripts/p4m.py:75) then computes `(a < NaN).mean()`, yielding **0.0**. An unmeasurable response consequently appears below every null graph. Require finite numerator, denominator and ratio; preserve an explicit validity flag and missing P4 percentile; exclude invalid cases from lead selection and permutation summaries. Add a regression check for this case.

3. **Implement the stated execution constraints.**  
   [`main`](/D:/Claude/random/wormWars-p4/scripts/p4m.py:339) leaves `args.device="cuda"` under `--smoke`. The advertised smoke command therefore uses the GPU. Set CPU explicitly. Also, the three-hour cap is absent: [`run_script`](/D:/Claude/random/wormWars-p4/wormwars/accounting.py:323) records compute but does not enforce a budget. Add a cumulative check across commands and attempts, with completed results retained on stopping. The reproduction check also ignores `--genomes`: it can pass at 2,048 while the subsequent analysis uses another population size. Restrict formal outputs to the declared size, or clearly label and record deviations.

4. **Change Q4’s interpretation and persistence eligibility.**  
   “A share that persists points to multiple stable states” is too strong. Recurrent networks can relax much more slowly than their individual neuron time constants; 300 ticks being 15 times `tau_max` does not establish convergence. Oscillation, phase differences and long transients also remain possible. Report **history separation remaining at 300 ticks**. For a fixed-point interpretation, check that each trajectory has settled in full state, not just that their turn outputs remain different. In [`decay_summary`](/D:/Claude/random/wormWars-p4/scripts/p4m.py:277), the `1e-12` divisor floor does not make tiny starting differences informative. Define an absolute eligibility floor, report the excluded share, and require a meaningful endpoint difference.

5. **Recast the deletion “lead” rule.**  
   The joint criterion is legitimate as a screen for deletions reducing *both* quantities, but it is a poor sole definition of a mechanism lead. A deletion that reduces P4 while preserving response would be especially informative—and currently fails the rule. Conversely, general disruption of signal transmission can satisfy it. Report persistence-selective, response-selective, and joint changes separately. Moreover, “below the 95th percentile and below the maximum” means **no longer unusually high**, not “inside the ensembles’ range”; there is no lower bound or joint-distribution test. The code supplies marginal percentiles only.

6. **Correct the factual and causal wording.**  
   In [PLAN.md](/D:/Claude/random/wormWars-p4/experiments/03m-p4-mechanism/PLAN.md:30):
   - “N2 nevertheless has the highest P4” is false. In 03, SH-route-20078 has **0.933697**, above N2’s **0.930856**; 03r reports one SH-class graph above N2.
   - `tradeoff.json` gives response/median ratios **4.699–7.087**, so the stated range should be about **4.7–7.1**, not 7.4.
   - Q5’s “would mean the wiring drives the persistence and weight placement drives the response size” does not follow. Persistence also changes with weight placement, and several variants are ordinary relative to the more constrained ensembles.
   - Deleting AWA, AWC or ASE individually or as a bilateral pair removes only part of the food interface. The other food pairs remain driven. These are input-path lesions, not necessarily response-collapse controls.

On **Q1**, the Spearman calculation and ensemble filtering look correct by inspection. The negative association is a valid descriptive result; calling it a dynamical “trade-off” is premature.

Let \(N\) be the numerator and \(D\) the denominator. Since \(P4=N/D\), sublinear growth of \(N\) with \(D\) produces a declining ratio without demonstrating a trade-off between response and memory. Shared estimation error can contribute too. Neither explanation is established just by identifying the ratio.

The **4.3–6.7 residual-SD figures are not significance scores**. They divide an extrapolated residual by within-sample residual scatter, without accounting for prediction uncertainty or validating the functional form beyond the controls. Keep them as explicitly model-dependent descriptions.

My first checks would be:

- Plot **numerator against denominator**, within each ensemble and instance, with N2 and all six permutations. Examine scaling before fitting the ratio.
- Compare P4 against the separately measured `common_turn_M0`, already in the supplements. This removes the exact shared-denominator construction, although it is not statistically independent.
- Inspect read-out neuron voltages and tanh derivatives at the starting holds and ramp endpoint. Small aggregate turn contrasts do not exclude saturated individual neurons. A voltage read-out on the same trajectories isolates the final read-out nonlinearity; it does not remove recurrent tanh effects.
- Check convergence during the 100-tick starting holds. The denominator is a **finite-time contrast**, not a verified equilibrium contrast.

Those checks are more informative initially than trying additional extrapolation formulas. N2’s unusually large absolute numerator and denominator remain observations even if the ratio correlation has a mechanical component.

For **Q2–Q5**, my additional suggestions are:

- **Q2:** Deletions locate dependencies, not necessarily the site storing history; a transmission bottleneck can be critical. Follow promising neurons with chemical-only and gap-only incident-edge deletions. Forward-only read-out neurons can also be included in this **turn-only** analysis: removing AVA, AVB, AVD, AVE or PVC does not alter the turn read-out formula. Their present exclusion follows the plan but unnecessarily narrows the search.
- **Q3:** Add **chemical-off** and, cheaply, **both-off** controls. Gap-off alone tests dependence on gaps; it does not establish an exclusive gap-versus-chemical mechanism. Repeat type-specific permutations over a small seed panel. One permutation can only describe that particular rearrangement.
- **Q4:** The first 16 graphs per ensemble are a defensible exploratory panel. Save signed per-genome curves, add tick 5 to connect directly to 03, and retain convergence diagnostics. Avoid rounding away small curves before saving.
- **Q5:** Sixty-four permutations improve on six substantially, but compare their distribution with each ensemble’s distribution, not just the numerical band 0.86–0.92. [`probe_genomes`](/D:/Claude/random/wormWars-p4/scripts/p4m.py:94) seeds genomes from `N2perm100`, etc., so these variants have **different signs, biases and time constants from N2**. That is valid for a distributional comparison, but not a paired weight-only intervention. Prefer holding N2’s genome draws fixed while varying permutation seed, or state the independent-draw design explicitly.
- Preserve per-genome probe outputs locally and record sample sizes, seeds, batch composition, resolved configuration and input hashes with each result. This makes uncertainty estimates and diagnostic follow-ups inexpensive.

What I checked in the code:

- **Baseline identity:** instance `"03"`, original pilot bank—including non-food background currents—M0 interface, T1 brain configuration, `_gseed(name)+1`, and 2,048 probe genomes match `measure_graph`.
- **Measurement:** the ratio of mean absolute final differences to mean absolute starting contrasts matches `signals`. Omitting motor calibration is correct because raw turn does not use calibrated gains. NumPy aggregation precision differs slightly from the saved-list calculation, so this is tolerance-based reproduction.
- **Deletions and pairs:** chemical edges in both directions, touching gap junctions and bias are removed. Genome ordering and slices are consistent. Trailing-L/R pairing agrees with the curated naming convention. The exclusion set correctly implements the plan’s turn-plus-forward exclusion; pump neurons need not be excluded from this probe.
- **Q3 pairing:** the same genome seed and population size are used, and magnitude permutations use a private generator. Thus signs, biases and time constants remain paired here.
- **Decay:** the 100-tick holds, ten-step ramp, raw-turn column, difference sign and endpoint timing match `history`; default checkpoints correctly include 0 and 300. `mean_fraction_left_at_end` is a **ratio of means**, not a mean of per-genome fractions.
- **Accounting:** neural updates are counted, including the custom decay loop. Budget enforcement is the missing part. I found no tests targeting `p4m.py` itself.

**03m plan: revise**