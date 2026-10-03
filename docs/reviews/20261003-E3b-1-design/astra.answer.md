**Verdict: revise.** Keep the owner’s two schedules, but settle the gate and champion rule in another design pass. The budget looks plausible; the claimed power does not yet apply to the proposed gate.

1. **Pooling is defensible for a narrowly defined question.** Define the estimand as the equally weighted mean improvement of the two schedules. A pooled win would establish neither schedule individually. Report their effects separately.

   Prefer a schedule-stratified estimate, \((\bar d_A+\bar d_F)/2\), with uncertainty calculated within schedules and calibrated for eight runs each. Simulate unequal variances, different schedule means and opposite-sign effects whose average is zero.

   **Sign-flip agreement is not a general safeguard against bimodality.** Exhaustive enumeration is exact under the appropriate sign-symmetry/randomization null, not merely because the pooled mean is zero. Use it as sensitivity analysis, or calibrate the actual conjunction of tests. Two mirrored 5% tests also allow approximately 10% probability of *either* directional label under a symmetric null; state whether that is intended.

2. **Correct the power claim and distinguish a margin from an MDE.** At CV 0.282, the committed t-test results are:

   | Runs | Normal MDE, 80% power | Empirical MDE |
   |---:|---:|---:|
   | 8 | 0.28 | 0.26 |
   | 12 | 0.22 | 0.20 |
   | 16 | 0.19 | 0.18 |

   Thus **0.18–0.19**, not 0.17–0.19, applies at the stated CV. More importantly, the 16-run simulations contain **no sign-flip calculation**, no conjunction and no fixed two-schedule design. At a 10% improvement, their t-test power is only about **39–40%**. [Power record](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-0/power.json), [simulation](D:/Claude/random/wormWars/scripts/e3b0_power.py:68)

   I would accept **10% as an explicitly chosen practical target**, approximately 0.58 visits at the old seed mean. Do not choose 22% merely because it was an MDE. If “better” requires rejecting a null of improvement ≤10%, the old model needs roughly **28–29% actual improvement** for 80% power. These remain conditional planning figures.

3. **The champion rule is undefined, and its justification is wrong.** A changing genome does not possess five generations of fitness observations. Averaging population-slot scores would average different genomes; tracking surviving genotypes introduces unequal observation histories.

   E3a validates **one training winner per checkpoint**, then selects its champion from the **final population of 32**. It does not validate every checkpoint’s whole population. [Checkpoint code](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:165), [champion selection](D:/Claude/random/wormWars/scripts/e3a.py:873)

   My recommendation: validate all 32 genomes at each designated selection point. Thirty selections ×32×128 mazes project to **1.13 hours**, versus 0.14 for four candidates—not 12 hours. At 128 mazes, the seed’s marginal mean SE is approximately 6.6%; that alone does not determine ranking accuracy, because paired differences matter. Keep common validation mazes and freeze tie-breaking and generation indexing.

4. **N with `none` access is appropriate.** Under the current mechanics, unsensed deposits have no behavioural effect; this equivalence extends beyond the seed. Verify it with mutated genomes, and explicitly document the substitution for deposit-off. A separate deposit-off evolutionary arm is unnecessary. [Trail sensing](D:/Claude/random/wormWars/wormwars/e3/maze_world.py:275)

   Compare **T-A against N** when discussing training with versus without trails: those schedules match. Pooled T versus N also changes training schedule.

5. **Use visits per wey for S-trail; retain later-leg rate secondarily.** The latter excludes weys without a first visit and uses a behaviour-dependent denominator, so it can improve while discovery deteriorates. [Measure definition](D:/Claude/random/wormWars/wormwars/e3/maze_measures.py:41)

   Report all four tuned/seed × on/off means. A larger on−off contrast can arise through worse off-performance: call it **increased trail dependence**, not automatically improved exploitation. Register secondary testing/multiplicity rules. Re-evaluate the seed’s peer controls on the new test panel; historical E3b-0 values are contextual comparisons.

6. **Restore missing interpretation safeguards before registration.**

   - The parent design required a **minimum repeated-journey criterion**. Specify it, retain raw entries, and report round-trip completion shares; mean visits alone can conceal concentration in a few weys.
   - Pin disjoint training, validation, replay-calibration and test maze blocks, with independent training streams per run. Make the generation-125 check non-adaptive unless an adaptation rule is registered.
   - State whether inference is conditional on the fixed test panel or includes uncertainty over mazes.
   - Include memory assays at **D=141** and a small optimizer recovery control. A null remains about this initialization and affordable training effort.
   - Explicitly exclude W2 from mutation: the existing `stage3_scales` would mutate it when applied unchanged to the extended organism. [Mask](D:/Claude/random/wormWars/wormwars/e3/samplers.py:128)

7. **The training arithmetic checks out.** From `timing.json`: T-A **4.711 h**, T-F **5.653 h**, N **3.533 h**; total **13.896 h**, or **17.371 h** with reserve.

   The complete budget remains provisional. Replay-coefficient pre-passes, assays and initialization/evolution overhead need explicit entries. The existing timing measures 50 ticks after initialization. Benchmark complete generations and evaluation compositions, then apply the fixed budget cuts before training. Complete the owed GPU equivalence leg. [Timing implementation](D:/Claude/random/wormWars/scripts/e3b0.py:990)

I checked the files and recomputed the arithmetic; I did not run simulations.