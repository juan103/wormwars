**Verdict: revise.** I favour the Welch addition, but the implementation has substantive gaps in rule C, and several claims in the note need correction before the counts go to the owner.

I checked draft 4 against the code, both current JSON outputs, the earlier output and logs, and the archived reviews. I reran the tests: **37 passed**. The archived sabotage log contains 17 assertion-failing cases. Neither covers the failures below. I changed no files.

1. **Rule C does not implement two explicit round-2 requirements. This blocks approval.**

   In [run_c](/D:/Claude/random/wormWars/scripts/memory_m5/m5_power.py:1107), the interim uses all stage-1 hosts, and the constructed `sub` object drops `sim["invalid"]`. Consequently, invalid hosts participate in both the interim and final reading.

   I tested `invalid=1.0`, with the saved nominated allocation and policy, for 100 simulated runs. **Every run was reported complete; 83% succeeded.** All should have stopped as incomplete.

   The promised **stage-1 audit bound is also absent**. `readings()` computes a bound from the final selected hosts; `run_c()` never separately computes stage 1’s bound. Moreover, `summarise_short()` removes the coverage fields from C’s saved confirmations. Thus the output establishes neither the promised stage-1 calculation nor the measured coverage of C’s final pooled bound.

   Fix both, add tests that fail on the current implementation, and report C’s invalid-panel sensitivity and both audit-bound coverages.

   The other main C requirements are present: total raw-contrast variance, the 75% normal-reference inflation, lookup and rounding, balanced attempted extension, nomination before confirmation, **K=2**, conjunction across the three core scenarios, and the cap based on fixed-H cost at H_max.

2. **The mean-calibration repair works, but the host-variance fit needs correction or explicit justification.**

   [fit()](/D:/Claude/random/wormWars/scripts/memory_m5/m5_power.py:154) estimates Rr’s host SD using `fit_sd(..., sd_v=0)`, then adds a separately fitted draw component. That attributes draw variation to the host component before adding it again.

   Numerically, Rr’s fitted SD **0.497115** reproduces its observed count variance **15.4333** without the draw term. Adding the fitted draw term while retaining that SD predicts **16.2192**. Jointly matching the observed variance and draw component gives approximately **host SD 0.47814**, draw SD **0.19199**. Pooling that host variance with T’s gives SD **0.48530**, rather than **0.49474**.

   This is probably a modest numerical change, but the host selections and 20% decision are discrete enough that I would not assume it leaves the recommendation unchanged. Either fit the components jointly or explicitly defend the current construction as an approximation rather than a fitted host component.

   Also, “exact calibration” should refer specifically to the protocol-mean calculation. The host-component solver still averages over 200,000 sampled hosts. Independent quadrature gives **1.51016e−5** at the reported core solution, versus the reported **1.52000e−5**. That discrepancy is small; reporting an independently evaluated value or numerical uncertainty would suffice.

   The broader model does implement the important agreed structure: coherent multinomial counts, host-persistent propensities, Rr-only draw effects, the corrected **1/153** transition path, whole-protocol effect calibration, and the enumerated effect spreads.

3. **Choose remedy (a), adding Welch to the balanced hull. Keep the existing tolerances.**

   The saved per-cell results support this choice: every selected fixed-H allocation fails at least one original gate, whereas every selected Welch allocation passes. The Welch envelope extension is consistent with the reader.

   I would not widen the tolerance simply because the original reading failed it. Making raw “raises” automatically qualified changes the agreed reporting rule without repairing its calibration. A different bootstrap would require another validation exercise.

   However, **the note’s pooled headline is mislabeled**. From the two JSON files:

   | Pool across four selected allocations | As written | Welch |
   |---|---:|---:|
   | All six null rows, raw | **2.2303%** | **2.0807%** |
   | Excluding ensemble-heterogeneous nulls, raw | **2.5645%** | **2.3906%** |
   | Same restricted pool, unqualified | **1.1861%** | **1.1074%** |

   Thus “pooled over every null cell” is wrong. The quoted 2.53–2.60% interval belongs to the restricted pool. **The per-cell failures remain valid**, so correcting this does not remove the problem. Sources: [original output](/D:/Claude/random/wormWars/runs/memory-m5-power/power.json), [Welch output](/D:/Claude/random/wormWars/runs/memory-m5-power-welch/power.json).

   My independent 40,000-run component checks support the qualitative diagnosis, especially the bootstrap’s roughly 4.6% false-raises rate at H=30. Say the t is **approximately calibrated two-sided in these simulations**, rather than declaring nominal two-sided control.

   There is another qualification for the owner: the apparent ten-host Welch cost is amplified by Monte Carlo selection. At H=130, A’s refinement changes from **3277 to 3271 successes out of 4000**; the candidate threshold is **3273**. The Welch search consequently reaches H=140. That follows the agreed rule, but it does not establish that Welch intrinsically requires ten additional hosts. Call these the **smallest confirmed host counts tested**.

4. **The latent-switch result requires explicit separation of claims, rather than necessarily changing the experiment.**

   The original A-cheapest result is verified: **78.875%** success in `latent Rr, core`, with an approximately zero latent contrast. With the selected Welch allocation it is **80.925%**. Welch does not address this identification problem.

   Keeping the design is defensible **if M5’s question is about protocol-confirmed states**. Every positive headline should then say something like:

   > T increases the share confirmed by this protocol; the direction of the underlying separate-state contrast remains unidentified.

   I would avoid a standalone “unqualified raises.” It means only “survives the six specified readings,” and can easily be understood more broadly.

   If the owner’s intended question is whether T increases **underlying** separate states, the agreed caveat is insufficient as a reason to fund this design. Better adjudication of unresolved genomes, or another identification strategy, is needed. More hosts do not repair that ambiguity. This distinction belongs in the budget decision itself.

5. **Keep the unresolved-share measure descriptive. The flag is answering its defined question correctly.**

   “Fires with nothing wrong” and “carries no information” are misleading. The baseline model already contains a real Rr–T unresolved-share difference inherited from the pilot. An interval above zero is evidence of that difference; it is not an 88% false-positive rate.

   Report the arm shares, their difference and interval. Do not present the zero-threshold flag as a diagnostic for latent switches.

   I would not immediately replace zero with the pilot’s estimated difference. That would require accounting for uncertainty in a ten-host pilot and validating a new diagnostic. It still would not identify latent switches.

6. **Several further departures and reporting errors need an explicit checklist of repairs.**

   The six-reading conjunction is correctly implemented, including both T-side checks. The A/B families use **K=24**, their candidate bounds use the family level, and confirmation uses fresh seeds at the candidate and candidate+5. Those round-3 changes went in.

   The remaining discrepancies include:

   - **Unbalanced exclusion is disabled too broadly.** [readings()](/D:/Claude/random/wormWars/scripts/memory_m5/m5_power.py:594) requires `all_valid` before attempting exclusion. Draft 4 permits exclusion after deletion when every leave-one-out reading remains valid. A 20-host, zero-contrast example with one invalid host returns exclusion false, although every required interval is exactly `[0,0]`.
   - **Probability-tail handling differs.** [simulate()](/D:/Claude/random/wormWars/scripts/memory_m5/m5_power.py:336) rescales probabilities exceeding 0.2 instead of rejecting and redrawing. Its `rejected` count never reaches the saved report. Therefore the output cannot establish that this departure was inactive.
   - **Promised diagnostics are missing:** realised host components under effect spreads; simulated first-to-final calibration counts; the 1.25-times-cost exceedance probability; historical-pooled audit bounds; and the specified unbalanced coverage check under unequal ensemble variances.
   - **The invalid-panel scenario uses 1,000 runs**, not the section heading’s blanket R=4,000. Refinement also stops at the first candidate rather than evaluating every near-target cell. These should be disclosed.
   - **Fixed costs omit the timed verification** and charge two draws’ block costs even for D=1. [The timing script](/D:/Claude/random/wormWars/scripts/memory_m5/m5_power_timing.py:57) explicitly says verification is reported but unused. Small financially, but a departure from section 6.
   - **The envelope statement is wrong.** Some saved δ=0.004 cells have crossing frequencies below one. Simulation results also cannot imply the wording applies to *every future M5 outcome*. The quoted **0.0078** is approximately the unexpanded logical-bound width; my baseline calculation gives approximately **0.0116** for the sampling envelope’s mean width. Label the two separately.

   The main allocation table, scenario powers, calibration-check quantiles and savings arithmetic otherwise agree with the files. Preserve the already disclosed test-order exception; sabotage does not retrospectively satisfy “seen failing before implementation.”

7. **What goes to the owner: one amended reading, concrete options, and the identification limitation.**

   After the implementation repairs and updated validation, present A, C and B under the **same chosen Welch reading**, rather than ranges spanning an inadmissible original reading and a proposal.

   The current Welch output supplies these **provisional** options:

   | Rule | Hosts; allocation D/G/A | Expected CPU hours | Interpretation |
   |---|---|---:|---|
   | A | 140; 1/512/80 | 95 | Fixed allocation, confirmed at the core scenario |
   | C | 110 initially, maximum 160; 1/512/40 | 72 central; 92 core | Adaptive; implementation repairs outstanding |
   | B | 110; 1/512/40 | 66 | Approximately 70% power at the core scenario |

   The current savings are correctly **24.7078%**, so **C is the recommendation under the stated rule if corrected validation preserves those results**. Show A alongside it and require explicit acceptance of B’s power loss if B is chosen. Include the operational caps—currently about **143, 144 and 99 CPU hours**, respectively—and the 65-host A alternative at about 173 hours.

   Do not send these as final approved counts yet. The required next step is a corrected, documented implementation and updated results, with the owner told plainly which scientific contrast that expenditure can resolve.