The selector conclusion is supported. The attribution supports strong interactions between the sensing and gating **parameter groups**, but the draft overstates their mechanistic interpretation and understates the output allocation for T-A. There are also several factual errors to fix.

I independently recomputed the attribution estimates, intervals, lesion costs and latch summaries from all 70 committed chunks. They agree with [summary.json](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-2/summary.json). The functional-attribution, side-attribution, trail-split and lesion tables reproduce correctly at their displayed precision. I found no calculation defect requiring another simulation run.

1. **Keep the selector conclusion, with precise limits.**

   The two complementary observations support the plan’s §6 reading: switching survives tuning, and holding q at either stable state severely harms performance. Switching is driven by visit relays by design, so its occurrence alone establishes retained circuit operation, not usefulness. The clamps supply the behavioral evidence.

   “Nearly all” is defensible, but reporting the actual proportion is clearer: the clamps remove approximately **85–87% of the T schedules’ intact shared-trail visits**. Mean performance falls from 6.361 to 0.960/0.798 visits per wey for T-A, and from 8.284 to 1.170/1.103 for T-F, below W2’s 1.648.

   This supports useful dynamic selection under the prespecified diagnostic. It does **not** establish that the tuned comparators retain the seed’s computational function, that modular assembly is advantageous, or that information transfer explains the gain. Keep the proposed next-step reading explicitly at that level.

2. **Correct the latch reporting.**

   The [headline and latch section](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-2/RESULTS.md:45) need these changes:

   - **“Within 1–2 ticks” is wrong.** T-F run 0’s mean latency toward B is **3.000543 ticks**. The recorded latency is a mean over crossings, not a maximum or an event-level range. Label the table accordingly.
   - **“After every visit” needs the denominator.** Across all 21 organisms there are **294,084 visit-triggered legs, 293,905 crossings, 179 censored legs and zero pre-aligned legs**. Every non-censored leg crossed, in both directions. The censored fraction is small, but the plan expressly requires reporting it.
   - **“Undecided ticks number about one per leg” is false as a general description.** Several organisms have zero middle-third undecided ticks; the ratios vary from zero to approximately one. The aggregate is 161,395 undecided ticks across 294,084 legs.
   - Report the sensitivity reading: **middle-half decided-tick agreement is 1.000 for every organism**, with different undecided counts. Specify whether the displayed agreement range spans organisms and goals; retain separate A/B and equal-weight readings in the supporting table.

   These corrections do not weaken the central selector conclusion materially.

3. **Correct the hybrid count and narrow the causal wording.**

   In both places saying seven champions have all eight mismatched hybrids below W2, replace **seven with six**: T-A 7 and T-F 1, 2, 5, 6 and 7. The other claims check out: 15/16 have at least four below W2 under shared trails, at least three under none, and none of the functional hybrids retaining both or neither group falls below W2.

   The phrases [“The cause” and “Neither works with the other’s seed values”](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-2/RESULTS.md:96) are too strong.

   These interventions exchange whole groups. Sensing includes nose biases and time constants; gating includes both comparator biases and latch-input weights. They do not isolate “input weights need their tuned biases.” There are also individual exceptions: transplanting T-A run 2’s gating into the seed gives **+0.011805**, rather than a loss.

   A supported formulation is:

   > Under the specified seed–champion substitutions, mixing sensing and gating groups often causes severe performance losses, indicating strong interaction between these parameter groups.

   The existing evolutionary-path caveat is useful but incomplete. Add that the allocation depends on the **baseline, partition and substitution table**, and does not distinguish sensory computation from altered tonic output or response timing. The large positive pair dividend partly reflects recovery from very poor singleton hybrids; it is not that much additional performance delivered by a separately identified mechanism. Shapley allocations incorporate singleton effects and other interaction terms as well.

4. **Do not describe output tuning as carrying little of T-A’s gain.**

   [The “rest” claim](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-2/RESULTS.md:61) is materially misleading across schedules:

   | Shared-trail allocation | T-A | T-F |
   |---|---:|---:|
   | Output, seed-mean units | +0.040883 | +0.011703 |
   | Output, visits per wey | +0.233363 | +0.066803 |
   | Output / summed net gain | 35.7% | 2.6% |
   | Sensing + gating / summed net gain | 56.8% | 95.4% |

   These are the plan’s permitted schedule-level shares. Output is small relative to the seed’s performance, but substantial relative to **T-A’s gain**. Also, “≤0.04” is literally incorrect.

   Distinguish the schedules prominently: sensing and gating dominate T-F’s allocation; T-A has a negative sensing allocation, a larger positive gating allocation, and a substantial output allocation. The shared-trail latch-parameter allocations are small in both.

5. **The lesion numbers and trail split are correct; several interpretations need qualification.**

   “Nose inputs removed” correctly describes removal of **trail and path-distance scent together**. The implementation preserves nose biases and time constants. This tests the net contribution of those inputs in the tested condition; it does not isolate stereo comparison or trail following.

   Qualify “the noses matter … not to N’s.” Under shared trails, all four N champions have nonnegative point effects from removal, averaging **+0.081480**, with the displayed run interval including zero. Under their trained **none** condition, removal costs **−0.153315**. That condition dependence belongs beside the headline, rather than leaving an impression of general sensory dispensability.

   **“With trails off, the costs keep the same order” is wrong.** For example, in T-F, gate cutting costs more than A-output silencing under shared trails, but less under none: **−0.499 versus −0.545**. Replace this with the narrower observation that both clamps and reflex removal remain strongly harmful.

   The trail decomposition and its bootstrap intervals check out. Its totals are **−0.057218 for T-A** and **+0.360458 for T-F**, exactly the shared-minus-none gain differences. Say T-F’s increase is allocated **primarily** to sensing and gating: output and latch also receive positive allocations. Keep the own-versus-peer limitation.

6. **Make the planned supporting readings accessible, and include the main secondary-outcome distinction.**

   The records contain most of what §5 requires, but the write-up presents only a selection without adequately indexing the remainder. A linked appendix can satisfy this without putting every hybrid in the main text. It should expose:

   - Per-champion endpoints and allocations, raw visit allocations, both interval types, full dividends, side transplants and schedule shares.
   - Absolute hybrid performance beside seed/W2 references and below-W2 flags.
   - The other outcomes and their lesion effects.
   - Per-goal latch counts, occupancy, eligible weys, censoring, both bands and uncertainty.

   State that run-level t intervals are conditional on this maze block; maze-bootstrap intervals address a different source of variation.

   One substantive omission matters for the next design: with shared trails, **T-A’s later-leg rate is 2.822 versus the seed’s 2.760**, whereas T-F reaches **3.826**. T-A also has lower unvisited share, **0.034 versus 0.097**, and higher round-trip share, **0.862 versus 0.665**. These descriptive readings distinguish the performance changes that the visit totals combine.

   Keep units explicit: normalized differences apply to visits; the other lesion differences are raw. The first-B measure is specifically the later-discoverer statistic, excluding the earliest arrival.

7. **Scope the checks accurately and clean up the deviations section.**

   I verified bitwise equality across **all six saved per-maze outcome arrays** for the stated seed comparisons and lesion-intact versus attribution endpoints. Describe those arrays as identical; the records do not establish equality of full trajectories or neural states.

   The resting-turn comparison has maximum difference **0** against the earlier probe records. Replication means are correct; **0.985707** is the pooled correlation across the 16 champions. Label it pooled.

   Compute is also correct: **10,789.54 accounted seconds = 2.9971 hours**, rounding to 3.00, with no failed attempts or drops. The ledger defines this as synchronized wall time, not GPU kernel time.

   Finally, benchmark IDs **7300–7555 already appear in draft 3**. They are not a deviation from that plan. The nose-lesion rename clarifies the already planned intervention; it is not an implementation departure.

**Verdict: fix then publish**—correct the hybrid count and latch statements; narrow the mechanism claims; distinguish T-A’s output allocation; qualify the lesion interpretations; expose the planned supporting readings; and scope the exactness and deviation statements accurately.