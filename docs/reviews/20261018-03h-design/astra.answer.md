**revise.**

I checked `roadmap` at `de22cc4`, the cited results and records, and the relevant implementations. I changed nothing and ran no code or tests.

A can test a **conditional predictive association**; B can test whether N2 has an unusual **graph-by-assistance interaction**. The draft’s stronger readings are not yet supported, and several statistical choices materially affect what would count as success.

1. **Major — §§1, 4, 7: A’s success criterion does not establish its stated link.**

   \(D=\rho_L-\rho_R>0\) does not imply that history predicts *better* performance under level. For example, \(\rho_L=-0.10,\rho_R=-0.30\) passes the interaction while history predicts worse performance in both conditions.

   Require both a positive level association and a positive interaction for the proposed reading. Even then, replace “history … helps them forage” with “probe-measured history predicts fitness positively under level, more strongly than under assistance.” §7 acknowledges this limitation, but §4 contradicts it.

   Controlling response magnitude does not remove all genome-level differences in dynamics, responsiveness, locomotion or saturation. Nor would positive A and B together establish that history *mediates* N2’s advantage. Conversely, a null A does not break the memory hypothesis generally: useful history could have an optimal timescale, depend on response direction, or be missed by this probe.

2. **Major — §§2–3: ASK is a reasonable receiving pair, but the proposed routing control does not cover it.**

   I support **ASKL/ASKR**, with identical bilateral injection. Their existing pheromone **input** is zero in Task N; the neurons themselves need not be inactive. This follows from [the interface mapping](D:/Claude/random/wormWars/configs/interface.yaml:30) and [Task N’s explicit pheromone settings](D:/Claude/random/wormWars/wormwars/e1/task.py:23).

   However, [`constrained_neurons()`](D:/Claude/random/wormWars/wormwars/exp03/samplers.py:53) constrains only the food neurons in M0, R1 and R2. **ASK is absent.** Neither existing SH-route nor SH-mirror controls direct routing from the new relief input. Different access from ASK to the readout could therefore produce B.

   Extend the constrained sampler to include ASK’s chemical/gap direct-edge counts and weight caps, and identify the resulting ensemble as a modified sampler. Otherwise explicitly retain this routing confound.

   I would reject AWC for the primary design: injection there sums the bit with an existing food input, adding another change to food-input processing. A non-sensory pair offers no clear advantage.

3. **Major for a memory explanation; acceptable limitation for a narrowly stated assay — §2: zero versus live bit changes neural drive as well as temporal information.**

   Identical addresses and gains do not equalise input distributions. Live relief changes mean current, variability, temporal structure and neural operating points. A can change because high-history genomes respond differently to this extra drive; B can change because N2 processes ASK input differently.

   The scripted gate demonstrates an available assisted strategy. It does **not** demonstrate that random networks exploit that strategy or experience reduced effective memory demand.

   For a mechanistic interpretation, add a predeclared sham bit on the same neurons, independent of the current food trend, with specified matching of its statistics. Without it, retain the two-condition design but describe the outcome strictly as an **association/interference under temporal assistance**.

   Also freeze numerical gain and clipping conventions. “At the collision scale” is insufficient. Compute the bit from the level actually available to the controller, or establish that scaling/clipping cannot change the comparison. The no-reset rule at target relocation is correct: it avoids an extra target-identity cue. Say “no information beyond the **observed level history**,” not “no information the level does not [carry].”

4. **Major — §4A: my recommended statistic is partial Spearman on raw turn, with a conjunctive success rule.**

   Use:
   \[
   H_i=|\text{raw-turn final history difference}_i|,\qquad
   S_i=|\text{raw-turn steady contrast}_i|.
   \]

   Define partial Spearman explicitly as the correlation between residuals after separately regressing the ranks of \(H\) and fitness on the ranks of \(S\), with an intercept. Use average ranks for ties. Forward and signed-history analyses should be secondary.

   For aggregation, use a prespecified equal-weight mixture of the **two sampled null ensembles**, and report N2 separately. N2 is one fixed connectome, not another random draw from that mixture. Report ensemble-specific results too; a positive pooled mean does not establish the link within every graph or ensemble.

   **Smallest effect:** I would retain **0.05 in the correlation difference** as a provisional screening threshold. It is a judgment, not a repository-supported threshold for biologically or behaviourally meaningful benefit. For a “meaningful positive link” reading, require evidence that the mean \(D\) exceeds 0.05 **and** that the corresponding mean \(\rho_L\) exceeds zero. Distinguish that from merely testing \(D>0\) and observing a point estimate above 0.05.

5. **Major — §§3–4: eight shared worlds do not support the proposed unrestricted uncertainty statements.**

   Pairing worlds is useful. But all graphs share the same eight worlds, so a graph-only test conditions on those worlds; it does not account for uncertainty over Task N environments. A genome-only bootstrap for N2 has the same limitation.

   Choose between:
   
   - an explicitly **fixed-eight-world assay**, with conclusions conditional on that bank; or
   - inference over Task N worlds, using a crossed resampling scheme: one shared world resample across every graph and condition, paired genome resampling within graphs, and graph resampling within ensembles.

   Eight worlds give little information about world-sampling uncertainty. More genomes cannot repair that. World count needs a precision justification before the formal design is frozen.

   Register constant-score and degenerate-residual handling. With count fitness, ties and potentially unscoreable correlations are foreseeable; silently dropping those graphs would select the analysis population.

6. **Major — §4B: choose one upper-tail estimand and separate selection from evaluation.**

   As written, both candidate statistics describe the upper tail of **eight-world measured scores**. They do not estimate the upper tail of genomes’ expected performance on new worlds. Taking an expected maximum over many sampled genomes reduces genome-sampling noise; it does not remove favourable world noise or selection optimism.

   My choice is **held-out performance of the selected top decile**, with expected-best-of-32 secondary. Select the decile separately in each condition using the selection bank, then evaluate those selected genomes on an independent shared test bank. Freeze the cutoff and tie rule—for example, 103 selected genomes with ties resolved independently of test scores. Call this “test performance of the selected decile,” not the true population top decile.

   Define \(T_{g,c}\) accordingly and report
   \[
   \Delta_e=(T_{N2,L}-\overline T_{e,L})
             -(T_{N2,R}-\overline T_{e,R}),
   \]
   alongside both component advantages and the rank statistic.

   Ranking \(U_{N2}=T_{N2,L}-T_{N2,R}\) against null-graph \(U_g\) has the correct direction for interaction distinctiveness. But **a positive interaction alone is not a head start**. Require a positive level advantage for that label; otherwise report an interaction without an established initial advantage.

7. **Major — §§3–4, 7: resolve ensembles, multiplicity and rank-test interpretation together.**

   My preference remains **SH plus SH-mirror**, with the ASK routing extension above. SH-mirror also controls the mirror-symmetric topology share, which can affect a bilateral input/readout system. It does not preserve all anatomical structure or make a rejection memory-specific. SH-route is defensible if isolating the earlier routing explanation is the priority; I would not add a third ensemble at this budget.

   **64 graphs per ensemble are adequate for a coarse distinctiveness screen, not demonstrated adequate power for a small interaction.** Prioritise world-score precision before automatically doubling graph counts.

   If B’s claim requires success against **both** ensembles, use the maximum of their p-values as an intersection–union test. Then control multiplicity across A and B, for example with Holm. If either ensemble can independently trigger a positive claim, a different correction is required. Do not leave both tail statistics as interchangeable primaries.

   The stated minimum \(1/65\) is correct. “Top three” applies at unadjusted 0.05; at Holm’s first threshold of 0.025, N2 must exceed every null graph.

   Finally, 03’s own [results explain](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:56) that these are **approximate reference-ensemble tests**, not established exact randomisation tests. Carry that qualification forward. Specify whether “03’s rank rule” also imports its effect-margin gate.

8. **Major — §2: the scripted gate needs an actual selection and inference protocol.**

   Freeze each controller using tuning worlds, including selection among memory timescales, before opening check-world results. Do not choose the “best” controller again on the check bank.

   Require a paired confidence bound for the level gain and a genuine equivalence/noninferiority procedure for relief. For example, a paired 90% interval wholly inside ±0.3 implements two-sided equivalence at 5%. If the question is only whether memory adds less than 0.3, specify the corresponding one-sided noninferiority criterion instead.

   Explicitly implement the nesting: the memory families must contain the assisted memoryless policies, including settings that ignore internal history. Existing KT/KTM code does not supply that new interface automatically.

   The exact KTM-emulation claim is otherwise supported by [its implementation](D:/Claude/random/wormWars/wormwars/e03a/probe.py:68): level sets baseline behaviour, and a strict fall replaces turning, before collision avoidance. Preserve the first-tick and collision-precedence conventions.

9. **Major implementation contract / moderate interpretation issue — §3: the history measurement is underspecified.**

   [`history()` requires a stimulus bank](D:/Claude/random/wormWars/wormwars/exp03/measures.py:92); naming the function does not define the assay. Freeze its bank, brain configuration, warm-up, ramp length and measurement tick.

   To test the *existing P4 signature*, I would retain 03’s bank as primary and label its transfer to Task N explicitly. That [bank](D:/Claude/random/wormWars/experiments/03-generation0/pilot.json:2) includes nonzero hazard inputs and collision levels from the older task. A Task N-specific bank would be a separately declared sensitivity analysis.

   **Use exactly the same genome objects for history and both fitness conditions.** The existing [03 driver](D:/Claude/random/wormWars/scripts/exp03.py:447) draws fitness and probe genomes separately. Reusing its orchestration would not produce the required per-genome linkage.

   Also distinguish A from P4: P4 is the **ratio of population means**, whereas A uses per-genome history magnitude conditional on response magnitude. They are related but different estimands.

10. **Recommendation — §8.5: include the frozen-champion check alongside A, as a separate diagnostic.**

    Do not gate it on A. Random-genome association and useful history in selected controllers are different questions; either can exist without the other.

    Keep its outcome separate from A/B’s confirmatory family unless a combined claim is explicitly registered. The useful version is controlled sensory-history replay from matched physical checkpoints, with a fixed recent input suffix, preserved non-food inputs, sham interventions, and both action and subsequent-score measurements.

    Simply adding the existing bounded-history reset probe would not close the causal gap. Its disruption can include filtering and autonomous dynamics. The new diagnostic needs its own protocol and cost estimate.

11. **Fact check — §§1–2: mostly correct, with two qualifications and one small numerical correction.**

    The committed reports confirm N2 P4 values **0.930856**, **0.924325**, and **0.926128**: [03](D:/Claude/random/wormWars/experiments/03-generation0/report.json:1540), [03r](D:/Claude/random/wormWars/experiments/03r-replication/report.json:1796), [03mc](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/report.json:146).

    The quoted ensemble range should extend to approximately **0.85**, not 0.84: 03mc SH-mirror is 0.849.

    [02b](D:/Claude/random/wormWars/experiments/02b-champion-analysis/RESULTS.md:92) supports selected **turn-history dependence in the four studied task/group combinations**, relative to generation 0 and mutation-only controls. It does not establish useful memory, all individual graphs, or convergence between N2 and shuffles. Its explicit “whether it helps foraging is not tested” statement is accurately represented.

    The [scripted check record](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/memoryless-check.json) gives KT **1.19921875**, KTM **2.841796875**, difference **1.642578125**. Those citations are correct. They establish a gain within the searched families, not a general memoryless ceiling.

    I found no existing per-genome history–fitness analysis in the cited 03/02b analysis machinery.

12. **Moderate — §6: the original budget is plausible; the revised formal budget is not yet established.**

    The episode count is correct: **2,113,536**. At 892/s, evaluation takes approximately **0.658 hours**. Calibration at 25 seconds and history at 13 seconds per graph add approximately **0.896** and **0.466 hours**, respectively: about **2.02 hours before controls and overhead**.

    The [03a report](D:/Claude/random/wormWars/experiments/03a-self-consistency/pilot-dev/report.json:157) records 892.02 episodes/s and 25.31 seconds for calibration. The [03 pilot](D:/Claude/random/wormWars/experiments/03-generation0/pilot.json:40686) records history timings around 12.6–13.9 seconds, but for **2,048 genomes**, not the proposed 1,024. These support rough planning, not a measured throughput guarantee for the new composition.

    **My cap recommendation:** retain four GPU-hours as an initial feasibility ceiling. Do not call it a validated formal budget until held-out scoring, any sham condition, controls and replay diagnostics are costed. Set the final allocation and stopping rules before formal measurement; a cap-induced incomplete run must not silently become a smaller successful experiment.

13. **Before pre-registration, settle the following—not just §8’s six questions.**

    Freeze the scientific claim and success wording; ASK encoding and modified sampler; stimulus bank and identical-genome linkage; graph/genome/calibration/world seed schemes; selection/check/test splits and world counts; controller grids and gate inference; A’s weighting, effect threshold and uncertainty procedure; B’s single primary tail statistic, tie rule and component requirements; multiplicity; handling of failed samplers, calibration failures and undefined statistics; and cumulative accounting, interruption and incomplete-run rules.

    Define precisely which A/B outcome opens C. C can receive its own later pre-registration, but generation-0 variance alone will not identify evolutionary-run variance. A null outcome should close this particular screening route, not be worded as evidence that useful history is absent.