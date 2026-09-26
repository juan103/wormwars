The registered verdicts are correct, but I would not publish this wording unchanged.

I checked commit `f5ab9d9`, the registration, reporting code, decision history, and cited results. I independently recomputed all 15 signal-by-ensemble rank tests, means, latent SDs, margins, central ranges, and verdict classifications from `report.json`; they agree. The reporting code and binding registration were unchanged after `132acae`. I found no evidence of a rule selected after seeing these results. I could not independently recompute the raw-data bootstraps, decomposition table, calibration validation, or elapsed GPU time.

**Must fix before publishing**

1. **Restore the qualification on “exact” tests.**  
   [RESULTS.md:40](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:40) calls these “one-sided exact rank” p-values without the qualification in registration §2. These are approximate reference-ensemble tests; exactness requires exchangeability that the finite swap chains and greedy weight repair do not establish. This matters particularly for a result barely below 0.05.

   Explain the calculation explicitly: maximum p across five ensembles, then Holm across three signals. That IUT logic is correct for the conjunction claim; an additional fivefold correction is unnecessary. Also retain the registered disclosure that the opposite-direction tests form a separate family, giving up to 10% combined error across both directions.

2. **The headline and “none … reproduces” exceed the result.**  
   [RESULTS.md:3](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:3) and [RESULTS.md:218](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:218): the registered label **“distinctive relative to every ensemble” is warranted**, but “none of the five null ensembles reproduces” the property is misleading. `SH-route-20078` has P4 **0.933697**, exceeding N2’s **0.930856**. Every ensemble also exhibits substantial history dependence.

   A defensible headline is: “Under the registered matched-input probe, N2 has unusually high normalized history dependence relative to all five reference ensembles.” “Carry more of their recent input” is acceptable shorthand only with that operational qualification. P4 does not measure information capacity, useful memory, or a property of every individual random brain.

3. **The explanation for passing despite low simulated power is wrong.**  
   [RESULTS.md:62](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:62) and [DECISIONS.md:1338](D:/Claude/random/wormWars/DECISIONS.md:1338): smaller estimated latent SDs do **not** explain the rank-test success. Those estimates determine the effect margins and reported z values, not the ranks. At a specified z, a smaller absolute Gaussian SD is not itself an explanation for greater extremeness.

   The effect-margin gates passed comfortably: P4’s lower effect bounds are **0.077–0.170**, versus margins **0.018–0.037**. Even using the pilot’s margin, approximately **0.0372**, would leave all five gates satisfied. The borderline component is the rank gate.

   The quoted power-table entries match the registration, but they describe Gaussian ensembles sharing pilot parameters, not these observed distributions. Their exact simulated values were **0.002 at z = 2** and **0.326 at z = 2.5**. Say the observed tail counts passed despite modest power under that planning model; do not assert an established explanation. Different distribution shapes and sampling variation are relevant possibilities.

4. **P1’s “inconclusive” explanation misstates the registered rule.**  
   [RESULTS.md:80](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:80): small effect margins do not cause these labels. Under §6, consistency requires N2’s **whole measurement interval** to lie inside the ensemble’s central range.

   N2’s interval is **[−0.029727, 0.037700]**. SH-route’s central range, for example, is **[−0.024972, 0.027979]**. N2’s point estimate lies inside it, but its interval does not. The same containment failure occurs for SH-class and SH-mirror. Replace the margin explanation with this.

5. **P4 has no established ceiling at 1.**  
   [RESULTS.md:187](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:187), and the inherited claim in registration §7: bounded read-outs do not make their ratio bounded by 1. The implementation imposes no inequality requiring the final history difference to remain below the starting-level contrast. Overshoot, cancellation in the read-out, or nonlinear trajectories can violate that interpretation.

   Consequently, delete “That would tend to understate, not create, a difference at the top.” A compression mechanism and its direction of bias have not been demonstrated. Correct the registration’s mistaken explanatory statement through an explicit annotation, preserving its historical version.

   The available evidence does support **numerical stability for N2 in this sample**: the reported denominator is approximately **0.129**, far above the exclusion floor, and its bootstrap SE is **0.00618**. That is different from proving a bounded retention fraction or ruling out normalization effects generally.

6. **The stated example of an untested constraint combination was already tested.**  
   [RESULTS.md:220](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:220): SH-mirror includes **both mirror constraints and the routing cap**, as registration §3 states and `samplers.py` implements. Thus “each ensemble adds one constraint” and “mirror symmetry together with routing” as an untested combination are false.

   The broader limitation is valid: these ensembles do not jointly match every relevant property. Use an actually untested combination, such as class preservation plus reciprocity. Also repeat the registered limitation that the comparison changes **topology and weight placement**, so rejection does not isolate topology alone.

7. **The variants table mixes empirical shares with corrected rank p-values.**  
   [RESULTS.md:125](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:125) labels the entries “share,” then says they are `(r + 1)/129`. They cannot be both. For example, zero exceedances means an empirical share of zero but a rank p of **0.007752**.

   If reporting the registered rank quantities, the corrected table is:

   | Graph | SH | SH-route | SH-class | SH-mirror | SH-recip |
   |---|---:|---:|---:|---:|---:|
   | N2 | .008 | .016 | .008 | .008 | .008 |
   | N2perm1 | .256 | .876 | .837 | .876 | .333 |
   | N2perm2 | .008 | .016 | .008 | .008 | .008 |
   | N2perm3 | .016 | .225 | .163 | .225 | .054 |
   | N2-rev | .008 | .070 | .023 | .062 | .023 |

   If retaining empirical shares instead, use `r/128` consistently. In that case N2perm1’s route and mirror entries round to **0.88**, and N2-rev’s mirror entry rounds to **0.05**.

8. **“P2 is zero” is an unsupported null conclusion.**  
   [RESULTS.md:115](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:115): intervals containing zero establish neither exact zero nor equivalence. Replace this with “Every ensemble’s mean-P2 interval includes zero.” These are **95%** t-intervals, which should be stated.

   The corresponding claim at line 207 should say “not distinguishable from zero.” This is also an interpretation placed inside a section promising registered secondary **values, no verdicts**.

**Should fix**

9. **The 02b comparison misidentifies the aggregation and omits a major stimulus difference.**  
   [RESULTS.md:178](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:178): **0.931** is a ratio of means, but **0.881** is a **median of per-genome decay ratios**, as [report.py:102](D:/Claude/random/wormWars/wormwars/exp03/report.py:102) shows. Therefore “already average 0.93 and 0.88” and “03’s are ratios of means” are inaccurate.

   Also, 02b used a different stimulus bank for each run, obtained from its evolved champion; 03 uses one common pilot bank. The quoted 02b numbers are correct, but the comparison cannot establish equal persistence before and after selection. The **0.095 versus 0.030** generation-0 comparison concerns absolute history differences, not normalized P4, and could reflect responsiveness.

10. **Separate raw responsiveness, calibrated motor drive, and mechanism.**  
    [RESULTS.md:155](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:155) through line 195: the responsiveness result concerns the **raw food-evoked read-out under these probes**. It does not establish stronger motor drive in the calibrated world.

    I checked the calibration path: motor gains are applied after the raw read-out; the P4 calculation uses `raw_turn`. A simple multiplicative motor-gain artefact therefore does **not** explain P4. Matching world drive also does not match neural operating points or response dynamics.

    Alternative readings worth naming are slow relaxation, hysteresis or multistability, nonlinear saturation, and a starting-level contrast measured after a finite 100-tick warm-up rather than verified equilibrium. Common-mode responsiveness is measured under a different stimulus protocol, so the variants do not settle these alternatives. N2-rev’s tiny **P1/common-mode** denominator is not its P4 denominator.

    “Topology contributes” is reasonable as an explicitly exploratory suggestion. Note that reversal preserves some structural features but changes directed topology; three weight permutations do not isolate a causal structural feature.

11. **The corrections to 02 should distinguish different estimands from failed replication.**  
    [RESULTS.md:197](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:197): the directional numbers check out. The reconstructed signed response here is **0.0001178**, and the absolute response is **0.0150123**. “Sampling variation is a plausible explanation” is better supported than “most likely sampling noise,” given the missing uncertainty from 02.

    The mapping-preference comparison is not a replication of 02’s best-of-32 result. Experiment 02 already explicitly identified those brains as champions. Experiment 03 addresses unselected population means. It blocks generalizing the champion finding to average random brains; it does not overturn the original champion result.

12. **Make the exploratory decomposition and calibration checks reviewable.**  
    [RESULTS.md:147](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:147): I found no numerical inconsistency in the decomposition. In particular, **0.120/0.129 ≈ 0.930**, compatible with P4 after rounding. But `report.json` does not contain the per-graph numerator and denominator means or common-mode maxima, so I cannot verify those extremes independently.

    Before owner approval, provide a small reproducible supplementary table and extraction script, including these quantities and the saved independent calibration-validation results. “Calibration converged” does not demonstrate that its independent validation matched target drive. Publishing all 640 MB is unnecessary for this check.

13. **Replication should test robustness, not become a condition for reporting this result.**  
    [RESULTS.md:68](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:68) and line 229: I recommend a separately registered replication with fresh graph draws **and independent genome draws for N2 and controls** before presenting the biological interpretation as established. Reusing N2’s present measurement tests only part of the uncertainty.

    I would **not** require successful replication before publishing an honestly qualified report of this completed registered experiment. Preserve and report either replication outcome; do not rerun until the threshold passes. Before asking the owner to publish, fix the issues above and make the supporting exploratory calculations auditable.

**Minor**

14. **Additional numerical corrections.**

    | Location in RESULTS.md | Written | Correct |
    |---|---|---|
    | Line 52, SH P4 z | 2.5 | **2.6** when rounding 2.554685 to one decimal |
    | Line 62, observed z range | 2.2–2.5 | **2.2–2.6** at that precision |
    | Lines 73 and 81, P1 SE | 0.021 | **0.0205**, or 0.020 at three decimals |
    | Line 109, other ensembles’ top-decile medians | 1.50–1.53 | **1.49–1.53**; SH-recip is 1.488439 |

    The other primary-table quantities, secondary values, variant signal values, and cited historical numbers checked out apart from the issues listed above.

15. **Clarify what is fragile.**  
    [RESULTS.md:59](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:59): “One graph decides the margin” should say “One additional exceedance would lose significance.” The counterfactual **0.06977** is correct. The registered effect margins are not borderline. Conversely, failure to cross 0.05 in a replication would not by itself refute the underlying difference.

16. **The machine report contains nonstandard JSON `NaN` values.**  
    These represent invalid N2-rev P1 measurements. Strict JSON readers reject them. A publication export should use `null` while retaining the validity flags.

Overall, this is a correctly classified pre-registered experiment with a largely accurate numerical report, but the present write-up is not yet sufficiently precise for publication. The P4 verdict survives this review; I found no evidence of post-data rule selection. The problems are explanatory: overstated exactness and generality, incorrect accounts of the decision rules and power, and several misleading descriptions of ratios, controls, and secondary results. After those corrections and a small auditable supplement, it can honestly report an initial, borderline reference-ensemble finding. It does not yet establish a distinctive memory mechanism or a functional advantage at birth.