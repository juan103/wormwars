**Recommendation: first test whether the existing history effects contribute to performance; keep a revised temporal-assistance experiment as a gated pilot, not yet a full evolutionary run.**

1. **The proposed manipulation is useful to explore, but it does not isolate memory demand.**

   There is a concrete error in the candidate: **a derivative-only controller cannot generally act as KTM does.** KTM uses the current level to choose speed and baseline turning, then the previous level to detect a fall. Replacing level with change removes information KTM needs. A scalar mixture \(a\,level+b\,change\) generally does not preserve both quantities either. This follows directly from [KT/KTM’s implementation](D:/Claude/random/wormWars/wormwars/e03a/probe.py:68).

   The physical world and neuron addresses can remain fixed, but the **observation interface changes**. Calling this “holding the interface fixed” would obscure the intervention.

   Its main confounds are:

   - **Signal distribution:** positive levels become signed, often small differences, with different means, variance, autocorrelation, clipping and neural operating points.
   - **Sensitivity and routing:** N2 already responds unusually strongly to food input. Scaling a derivative could produce a graph-by-sensing interaction through responsiveness alone.
   - **Information removed or added:** derivative-only removes absolute level; supplying level and derivative gives the controller an externally computed temporal feature.
   - **Target relocation:** Task N’s target jumps after capture. Differencing successive readings includes this discontinuity. Resetting the derivative using hidden target identity would introduce additional privileged information.
   - **Search difficulty:** assisted sensing could improve every graph’s optimisation landscape, compress performance differences, or change which strategies evolution discovers.
   - **Timescale mismatch:** P4 concerns persistent history dependence. Supplying a one-tick difference need not remove the benefit of the longer history implicated by P4.

   I would replace “level versus change” with an explicitly named **temporal-assistance contrast**. Preserve level and provide either previous level or change as a separately recoverable quantity. A relatively clean candidate is two channels carrying **current/current** versus **current/previous** level: this preserves approximate marginal signal distributions better than raw differentiation. Counterbalance channel assignment because the receiving neurons are not interchangeable. It still changes cross-channel statistics and requires new implementation.

   Alternatively, level plus an explicit derivative is easier to interpret computationally, provided the mapping and scaling are fixed before seeing graph performance. Neither is a clean “memory versus no memory” experiment.

   There is **no ready-made, demonstrably memory-free comparison in this repository**. Stereo is solvable without memory, but that solution’s availability has not made the evolved controllers memoryless. Likewise, KT’s 1.20 is the performance of one searched family, not an upper bound on memoryless navigation; [03a’s design explicitly makes that distinction](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:97).

2. **The question remains worth investigating, but the evidence supports a pilot rather than an expected positive result.**

   I checked the branch and commit: `roadmap`, `72c1a76`. The quoted numerical results largely check out. Three qualifications matter:

   **First, 03 does not establish “no fitness head start” generally.** Its population mean is ordinary, as stated. But the next row reports a **top-decile mean of 1.69 for N2 versus the SH median of 1.51**, with SH’s graph range extending above N2. That is descriptive, not a demonstrated separation, but it makes the population mean insufficient to dismiss an advantage among selectable genomes. [03 results](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:165)

   **Second, “what changes is the shuffles, not N2” concerns preference for M0 over remapped interfaces.** It is not a decomposition proving that memory explains the declining direct N2–SH fitness difference. The significant generation-0 mapping interactions also need distinguishing from the unseparated direct head starts. [02 results](D:/Claude/random/wormWars/experiments/02-screening/RESULTS.md:175)

   **Third, 02b establishes selected history dependence, not its usefulness or convergence between groups.** On the quoted T0 measure, the absolute N2–SH gap actually grows from 0.065 to 0.341. That does not refute the roadmap hypothesis, because responsiveness and aggregation matter, but it does not demonstrate the proposed catch-up mechanism. The results explicitly say whether this history helps foraging was not tested. [02b results](D:/Claude/random/wormWars/experiments/02b-champion-analysis/RESULTS.md:92)

   The P4 values check out. However, 03mc also narrows the localisation claim: RIA/AIY deletion largely reduces response and history-signal amplitude together while preserving their ratio. That locates dependencies in signal transmission; it does not identify memory stores. [03mc results](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md:86)

   **Power from 02 gives a scale, not a reliable forecast.** Its generation-0 direct-advantage intervals imply approximate standard errors of 0.036–0.038. At nominal two-sided 5% significance and 80% power, the corresponding detectable effect is roughly **0.10–0.11 normalised units**. Its tightly paired task contrast implies approximately **0.032**, but that statistic subtracts mapping interactions across tasks. The new sensing contrast cannot assume the same cancellation.

   The saved within-graph variances, 0.002389 and 0.001097, are variances of **mapping contrasts**, not fitness or the proposed sensing contrast. Their between-graph estimates being near zero is weak evidence with eight graphs and two runs each. [Variance implementation](D:/Claude/random/wormWars/wormwars/exp02/analysis.py:146), [saved estimates](D:/Claude/random/wormWars/runs/exp02-screening/analysis.json:65)

   With four times the effective replication and similar variance, detectable direct effects might fall to about **0.05 normalised units**. A difference between two such effects could require about **0.07–0.08** without useful pairing. These are planning approximations, not predictions.

   For the actual task, use raw targets reached and estimate the variance of the **paired sensing difference** in a pilot. For one ensemble, approximately:

   \[
   SE^2(\widehat\Delta)=
   \frac{\sigma^2_{N2}}{R_{N2}}+
   \frac{\sigma^2_{\mathrm{graph}}}{G}+
   \frac{\sigma^2_{\mathrm{run}}}{GR},
   \]

   where every variance concerns that paired difference. Under hypothetical run SD 0.30 targets and graph SD 0.10, the allocation below detects roughly **0.20 targets**; with SDs 0.50 and 0.20, roughly **0.33 targets**. Those SDs are illustrations, not repository estimates. A reliable sample-size choice needs the pilot.

3. **If the manipulation passes that pilot, these are my provisional design choices.**

   | Choice | Recommendation |
   |---|---|
   | Ensembles | **SH-mirror primary; ordinary SH secondary.** SH-mirror already includes SH-route’s routing constraints. Add SH-route only if separating routing from symmetry is itself a question. |
   | Graphs and runs | Provisionally **16 graphs per ensemble × 4 runs per graph**, and **32 independent N2 runs**, each in both sensing conditions. Revise from pilot variance before registration. |
   | Pairing | Reuse each graph, initial population, training-world schedule and random-stream scheme across sensing modes. Pair evaluation worlds too. |
   | Generations | Score **0, 5, 10, 25, 50, 100, 250**. Starting at 25 could miss the entire transient. |
   | Primary score | **Untouched test score of the validation-selected incumbent available by that generation.** Validation selects; a separate test set estimates performance. |
   | “Head start” | Define it as **generation 0**. Report early learning separately, for example a fixed 0–25 learning-curve summary. |
   | Initial allocation | Population 32 and eight training worlds are a defensible continuity choice; freeze optimiser, shaping and tie handling. |
   | Evaluation | Start with 256 validation and 512 test worlds, then check whether world noise is small relative to run variability. |

   I would not use the maximum observed training fitness as the outcome. Nor would I choose between best-of-population and top quantile after looking at their separation. A population upper-tail measure is useful as a secondary generation-0 diagnostic.

   The ensemble definitions above follow [the sampler](D:/Claude/random/wormWars/wormwars/exp03/samplers.py:1). These sample sizes support **mean contrasts**, not 03’s rank-distinctiveness claim: with 16 null graphs, the smallest usual rank p-value is \(1/17\), above 0.05. N2 remains one fixed connectome; additional evolutionary runs do not replicate anatomy.

   For controls, require separately tuned and independently evaluated memoryless and stateful families in both modes: KT, an assisted memoryless implementation of KTM, KTM, several KTS timescales, and blind navigation controls. Use nested search spaces and comparable tuning effort. Demonstrate that assistance removes the intended benefit **within those families**, using an equivalence margin rather than a nonsignificant difference. This remains a feasibility check, not proof that no better memory strategy exists. The neural optimiser must also be able to exploit the assisted signal; E2d shows why a successful scripted controller alone is insufficient.

   Calibrate motor gains once per graph on a declared reference condition and freeze them across sensing modes. Report achieved drive and clipping in each mode. Separately recalibrating each mode would change the motor intervention too. Fix input scaling using independent calibration data, not N2’s advantage.

   **Keep bounded-history replay secondary.** The existing implementation retains roughly L–2L inputs between resets, leaves body history intact, and cannot detect KTM’s one-tick dependence at the registered windows. It can disrupt filters and autonomous rhythms. The new evidence is already substantial: 03a’s shuffled MIP brain falls from 1.95 to 0.00 at L=5, while KTM is unchanged. That is strong state dependence, not a calibrated measure of useful sensory memory. [03a probe results](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:96)

   Use L=5, 10, 20, 50, full-replay controls, prescribed-input checks, and raw performance differences. Add a sensory-history-specific intervention if memory is to carry a causal interpretation.

   Also, **the old P4 ramp cannot be transferred naively to derivative sensing**: equal final levels can still have opposite current derivatives. Match the complete presented input vector before attributing an output difference to retained history. Report numerator and denominator separately.

4. **I prefer closing the usefulness gap before testing the full evolutionary explanation.**

   My ordering would be:

   **First: frozen-controller diagnostics on existing champions.** Use existing N2 and shuffled champions, including earlier snapshots where available. Combine bounded-history replay with controlled sensory-history replay: hold the recent input suffix fixed while changing older food history, preserving collision input and evaluating from the same physical checkpoint. Include matched sham conditions and inspect both motor changes and subsequent score. This needs validation, and artificial histories can themselves disrupt dynamics, but it targets the missing causal link more directly than another learning curve.

   **Second: a temporal-assistance pilot**, if that diagnostic suggests a useful history signal worth explaining. The pilot should decide feasibility, variance and interpretation—not select graphs or settings because N2 wins.

   **Prediction (2) alone** is cheaper and easier to interpret statistically, but weaker scientifically. A shrinking performance gap could reflect generic optimisation, motor calibration or approach to a common strategy. Without an initial positive advantage and a useful-history measurement, it does little to establish the memory explanation.

   **Prediction (3) in evolved brains** becomes attractive once useful sensory history has been demonstrated. Plain deletions are inadequate by themselves: they can remove sensory transmission or motor drive. Test whether an intervention selectively removes dependence on older sensory information while preserving current-input responsiveness and basic movement.

   **Wiring N2 into the shuttle** is a larger project. The cited exclusion is real: E3a explicitly keeps its task signals out of worm neurons. Restoring N2 introduces choices about gating, routing and readout that could dominate the result. [E3a registration](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/PREREGISTRATION.md:121)

   If a **logically necessary memory task** is the priority, I would prefer designing a small delayed-cue assay before rebuilding the shuttle: randomise an earlier cue, make current observations identical at decision time, and require different responses according to that cue. Compare against a condition where the cue remains available. It would sacrifice navigational relevance but make the memory requirement much clearer. It is new work, not an existing validated task.

5. **Budget and registration should reflect those stages.**

   The single-graph-per-batch limitation is real. Throughput depends strongly on batch size: E1 measured **110 episodes/s for one run, 336 for four, and 438 for eight**, so using four runs per graph cannot automatically inherit the largest-batch rate. [E1 throughput](D:/Claude/random/wormWars/experiments/E1-navigation/RESULTS.md:79)

   For the provisional full design:

   - Two modes × \((32\text{ N2 runs}+2×16×4\text{ null runs})\) = **320 runs**.
   - Generations 0–250, population 32, eight worlds = **20,561,920 training episodes**.
   - At 200–420 episodes/s: **13.6–28.6 GPU-hours for training alone**.
   - Allow roughly **20–45 GPU-hours overall**, conditional on measured validation and probe costs. Repeated full-history replay is more expensive than bounded replay and needs separate accounting.

   I would initially propose a **four-GPU-hour exploratory cap**, with scripted checks first and only a small evolution component if those pass. Four graphs per ensemble, four paired runs each, and 16 paired N2 runs through generation 50 would use about 1.25 million training episodes. That is enough to expose gross failures and inform allocation, not establish a small interaction.

   Before a formal run, pre-register:

   - The exact encoding, neuron assignment, scaling, clipping, initial previous value and target-jump handling.
   - What “reduced memory demand” means, its calibrators, equivalence margins and failure consequences.
   - Graph sampling, exclusions, pairing, optimiser settings, calibration and evaluation splits.
   - One primary ensemble and the exact generation-0 interaction; the direct temporal-change contrast and multiplicity procedure.
   - A smallest effect worth detecting and pilot-based power assumptions.
   - Probe interpretation, controls, compute cap, stopping rules and outcome wording.

   **An interaction alone is insufficient:** it could be positive because N2 is disadvantaged by assistance. Report both component advantages. Likewise, “significant early, nonsignificant late” does not establish fading; test the change directly. Distinguish catch-up, reversal and unresolved differences.

   Commit and push the registration before the formal run. GPU stages still need the owner’s word under D318. I only inspected files for this review; I did not modify files or execute experiments or tests.