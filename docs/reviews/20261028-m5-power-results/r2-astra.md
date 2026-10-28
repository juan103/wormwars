**Verdict: revise, narrowly.** I agree with adopting the Welch addition and recommending C under the stated rule. But invalid-host handling remains incomplete, and two explanations in the note need correction.

I checked both JSON files, their round-1 versions, logs, code, tests and sabotage record. **44 tests passed**; I excluded the test that writes a temporary output file. The archived sabotage log contains 17 assertion-failing cases. I changed no files.

1. **Invalid hosts still affect the final audit-adjusted reading. This needs fixing.**

   The interim now excludes invalid hosts correctly, and an all-invalid C run stops incomplete. I independently reproduced that repair.

   However, [`contrasts()`](/D:/Claude/random/wormWars/scripts/memory_m5/m5_power.py:558) pools audit transitions and denominators over **all hosts**, before `readings()` applies the valid-host mask. Thus an invalid host still changes the audit adjustment applied to valid hosts. This affects both fixed-H runs and `run_c()`.

   A deterministic counterexample: 20 hosts, one invalid, every valid host having a raw contrast of `1/512`. Changing only the invalid Rr host from zero to two audited transitions changes the valid hosts’ adjusted contrast from **0.001953125 to −0.000400641**. Raw “raises” remains true; six-reading success changes from true to false.

   The final audit coverage calculations likewise include invalid hosts. Stage 1 masks its audit counts correctly, but its hidden-count coverage comparison includes invalid final hosts.

   Apply the same validity rule to the pooled audit estimator, audit bounds and hidden-count comparisons, while retaining the costs of attempted hosts. Add a regression test where changing an invalid host’s audit data cannot change the valid-host reading. Then rerun the affected invalid-panel sensitivities. The baseline selections use no invalid hosts, so this finding does **not** directly invalidate their A/C comparison.

2. **Keep the identification limit; qualify what continuation can establish.**

   Agreed: report unresolved shares, their difference and interval descriptively, without a flag. Agreed: put the 100,000-tick continuation sample into M5’s plan, rather than expanding this calculation.

   But “that would bound the hazard directly” is too broad. It bounds **additional protocol confirmations by 100,000 ticks**, under the sampling assumptions. It does not bound all underlying separate states or eventual switches.

   The pilot JSON confirms zero resolutions among Rr’s 47 unresolved genomes. Its documented root-search and classification limitations remain relevant. I therefore disagree with round 1’s assertion that the remaining hazard must consist only of switches occurring **after** 100,000 ticks: underlying states can remain unconfirmed by the classifier at that horizon too. [The pilot note already makes this distinction.](/D:/Claude/random/wormWars/docs/memory/M5-PILOT-RESULTS.md:155)

   The owner must accept a question about **protocol-confirmed states**. If they want the direction of the underlying-state contrast, this design does not establish it.

3. **Yes to Welch; revise the gate’s explanation.**

   Nothing in the revised as-written results persuades me to reverse that recommendation. They do show that the original reading is close to nominal in these simulations; they do not establish gross miscalibration. Nevertheless, adding Welch to the existing balanced hull is defensible, passes the retained tolerances, and is being chosen before M5’s observations.

   Be explicit that this is the **additional Welch component**, retaining the bootstrap and plain-s² t—not a replacement reading.

   The new “three of 32” argument needs more careful wording. Recomputing its exact binomial calculation:

   - A cell passes with at most **1,045/40,000 = 2.6125%** observed raw raises.
   - At the restricted pooled rate, **2.5230208%**, a cell fails that gate with probability **12.40%**.
   - Across the **24 non-ensemble-null cells**, that gives about **2.97 expected failures**, if their true rates were equal.
   - Applying that same rate to all 32 would give **3.97**, not three. The eight ensemble-null cells have much lower rates.

   Thus roughly three failures across this grid is a reasonable illustrative calculation when those eight cells are treated separately. It does **not** identify how much of the observed six failures came from Monte Carlo variation versus differing true cell rates or directional asymmetry. Replace the causal decomposition with that qualification.

   In M5’s pre-registration, report the **chosen policy’s** simulated rates and scenario range. For nominated Welch C, excluding the two ensemble-null rows, the averages are **2.443% raw and 1.064% six-reading success**; the largest raw cell is **2.630%**, with upper bound **2.765%**. These are model-conditional estimates, not a guarantee of nominal control.

4. **“No run exceeded 1.25 times the mean cost” is false for C’s own mean.**

   [`over_125`](/D:/Claude/random/wormWars/scripts/memory_m5/m5_power.py:595) uses `cap × 1.25 / 1.5`. For C, that is 1.25 times the **fixed-H reference mean at H_max**, not C’s adaptive mean.

   I replayed both central confirmations with their saved seeds and reproduced their success rates and costs:

   | Reading | C’s mean CPU h | Runs above 1.25 × C’s mean |
   |---|---:|---:|
   | As written | 71.2044 | **143/10,000** |
   | Welch | 72.0309 | **62/10,000** |

   Either label the existing statistic precisely or report the additional adaptive-mean statistic. The operational caps and savings calculation are unaffected.

5. **The main remaining round-1 repairs are present and numerically correct, with a few reporting omissions.**

   The joint fit checks out independently:

   - Rr host SD **0.478144194**; draw SD **0.191990523**.
   - Predicted count variance **15.4333333333332**, matching the observed **15.4333333333333**.
   - Independently evaluated draw component **1.5306472778301e−6**, matching the input **1.5306472778320e−6**.

   The quadrature host-component calculation, stage-1 audit coverage calculation, exclusion after invalid-host deletion, per-draw fixed costs, verification cost and `c_sens` stage are present. The principal allocation table, confirmation counts, calibration quantiles and **23.0045% / 22.1108%** savings agree with the JSON.

   Smaller corrections:

   - “Each target to within `1e-12`” is literally wrong: the half and above targets miss by approximately **4.32e−12** and **2.79e−12**. Numerically immaterial; say within `5e-12`.
   - “Three in all / two” probability rescalings describes the **scenario rows**, not the full pipelines. Family searches and confirmations contain additional events.
   - C still discards the rescaling count: its saved `capped_draws` fields are `null`. Preserve that diagnostic or disclose its absence.
   - The timing script and `fixed-costs.json` explanatory text still say verification is “reported, not used,” although the power calculation now uses it.

6. **The owner table is supported, subject to the repairs above.**

   Under Welch, the saved results support:

   | Rule | Allocation D/G/A | Hosts | Mean CPU h | Cap h | Power: central / core / above |
   |---|---|---|---|---:|---|
   | **C, recommended** | 1/512/40 | 110 initially; maximum 160 | 72.0 / 90.7 central/core | 145.4 | 0.841 / 0.808 / 0.747 |
   | A | 1/512/80 | 135 | 92.5 | 138.9 | 0.929 / 0.827 / 0.719 |
   | B | 1/512/40 | 110 | 66.7 | 99.9 | 0.806 / 0.692 / 0.597 |

   Sources: [Welch output](/D:/Claude/random/wormWars/runs/memory-m5-power-welch/power.json), [as-written output](/D:/Claude/random/wormWars/runs/memory-m5-power/power.json).

   Beside it, state that **C’s 22.1% saving is conditional on the central scenario; at the core it saves only about 1.9%**. Its core confirmation passes narrowly: lower bound **0.800547**. Those facts do not overturn the specified choice rule, but they matter to the budget decision.

   Retain the identification limit, planning effect of 0.002, fewest-host alternative, 90% option and qualifier-cost comparison. Describe these as the smallest confirmed counts tested and conditional simulation results. After the invalid-audit repair and corrected diagnostics, I see no reason here to reopen the baseline A/C selection.