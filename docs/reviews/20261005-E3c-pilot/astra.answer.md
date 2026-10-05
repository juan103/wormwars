**My verdict: one more bounded exploratory step first, then power analysis and registration.** Keep the maze task, training schedule, and mutation factor. The extra step should establish what the nose intervention measures and recover probeable genomes.

I checked both reference arrays and all nine final `per_maze` records. The reported pilot numbers hold. There is, however, a material error in the historical comparison used to discuss Q2.

**1. The branch and mutation factor**

**“Mazes” is correct.** §5 requires *either* S arm to have one qualifying run. Both S arms qualify in every run by generation 25. P-sel’s result does not determine that branch. The exact threshold is 2.7197265625 visits per wey. See [the branch rule](D:/Claude/random/wormWars/docs/E3/E3c-DESIGN.md:177) and [recorded decision](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/pilot.json:18406).

**Keep factor 1.0 for all three new arms.** The pilot provides no reason to change it. That establishes its adequacy for learning here, not its optimality. P-sel’s two unsuccessful runs do not justify a separate tuning search from three observations.

One wording correction: D203 says §5’s fixed rule keeps the factor at 1.0. The branch is fixed; retaining the factor is a supported discretionary decision. [§5 explicitly permits changing it](D:/Claude/random/wormWars/docs/E3/E3c-DESIGN.md:165).

**2. Do the S champions use scent?**

**Unknown. The pattern supports investigating a common traversal strategy; it does not establish scent independence.**

Recomputed sample SDs across the 128 mazes:

| Controller/run | Mean visits | Per-maze SD |
|---|---:|---:|
| W2 alone | 1.720 | 1.373 |
| Seed | 4.824 | 3.675 |
| S-mod 0 | 6.602 | 0.575 |
| S-mod 1 | 6.633 | 0.479 |
| S-mod 2 | 6.700 | 0.497 |
| S-dense 10 | 6.789 | 0.467 |
| S-dense 11 | 6.739 | 0.479 |
| S-dense 12 | 6.649 | 0.516 |
| P-sel 20 | 2.338 | 0.944 |
| P-sel 21 | 2.290 | 0.988 |
| P-sel 22 | 5.218 | 0.878 |

Sources: [references](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/pilot.json:272), final records beginning at [S-mod](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/pilot.json:2799), [S-dense](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/pilot.json:8403), and [P-sel](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/pilot.json:14007).

Three additional observations strengthen and sharpen the interpretation:

- The six S champions’ pairwise maze-score correlations are **0.562–0.901**. Their correlations with the seed are only **0.068–0.222**. They share a pattern of relative difficulty that differs from the seed’s.
- Their round-trip shares are **97.2–99.6%**. This is widespread repeated shuttling, not an average inflated by a few successful weys.
- All mazes are trees on 25 cells, hence have 24 connections. A repeated traversal of the whole tree has a relatively fixed amount of corridor to cover, whereas efficient A–B navigation depends on the particular source separation. That makes **goal-agnostic coverage with wall assistance** a concrete hypothesis. It remains an inference, not an observed mechanism. See [maze construction and placement](D:/Claude/random/wormWars/wormwars/e3/maze.py:3).

“Maze-independent” is too strong: a wall follower responds to maze geometry. “Possibly goal-agnostic traversal” is more precise.

**(a) Register nose removal as a secondary mechanistic reading, not a primary guard.** Apply it to every selected champion, including P-joint and P-sel, with seed and W2 controls. Select champions using the intact validation condition only; use those same genomes for both evaluations.

For each run, report the paired loss
\[
L_r=\operatorname{mean}_{maze}(V_{\mathrm{intact}}-V_{\mathrm{nose\ inputs\ removed}}),
\]
absolute performance in both conditions, uncertainty across runs, and the maze-level differences. Preserve maze pairing in supplemental resampling.

The intervention is appropriate: [`without_scent`](D:/Claude/random/wormWars/wormwars/e3/attribution.py:182) removes the four external A/B nose channels while preserving the neurons’ internal dynamics. That distinction matters especially for recurrent S-dense controllers.

But label it **“nose inputs removed.”** It removes trails and path-distance scent together. It leaves source-occupancy inputs and W2’s collision sensing available. A negligible loss means performance does not materially require those nose inputs under this intervention; it does not prove the intact controller ignores them. A loss establishes a net contribution, not specifically stereo comparison. E3b-2 already states this limitation [explicitly](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-2/RESULTS.md:218).

A nonsignificant loss is insufficient to declare independence. Prespecify a negligible-loss bound and report whether the interval excludes materially harmful removal.

**(b) A scripted wall follower is useful but optional.** It would establish an achievable scent-free reference, not identify the champions’ mechanism merely by matching their score. Use local collision signals, the same movement limits, and a fixed policy; disclose any tuning on exploratory mazes. The existing [random walk and W2 control](D:/Claude/random/wormWars/wormwars/e3/maze_controls.py:7) do not substitute for this.

**(c) Yes to bounded exploratory retraining with saving.** My preferred version is in answer 6.

**(d) Inspect trajectories.** On a fixed small set of pilot mazes, compare intact and nose-removed paths, corridor coverage, and visit timing. If performance survives removal, a separate occupancy-input intervention would distinguish goal-agnostic coverage from navigation still using `at_a`/`at_b`. If removal harms performance, equalising each left/right pair is a useful subsequent diagnostic of bilateral differences. Neither needs to become another primary endpoint.

**3. Would a scent-free solution undermine E3c?**

**It undermines the mechanistic interpretation, not the stated numerical Q1/Q2 comparisons.**

Q1 explicitly compares two masks under one training recipe. Q2 compares engineered initialization plus its tuning recipe against training E’s mask from scratch. Those remain legitimate questions if evolution discovers another strategy. [§1 already narrows the claims this way](D:/Claude/random/wormWars/docs/E3/E3c-DESIGN.md:21).

However, if the S controllers do not depend on nose inputs, E3c cannot describe its result as showing which method better assembles *functioning stereo navigators*. Also, it would not necessarily compare two routes to the same scent-free strategy: P-joint could retain substantial nose dependence while S-mod does not.

**Run the performance comparison as designed.** Do not change fitness, shape rewards, change mazes, or exclude scent-independent champions. Add a dated post-pilot amendment specifying the mechanistic readings and their interpretation. That addition should be disclosed as an amendment, not presented as already authorized by §5’s “only the mutation factor” wording.

If the desired scientific question requires stereo navigation to be necessary, that requires a separate task-design experiment. Retrofitting that requirement into this matched comparison would answer a different question.

**4. Q2’s expectation**

**Keep “P-joint better” as the original pre-pilot prediction, with a dated account of the pilot and current uncertainty. I would not reverse it.**

First correct [PILOT.md’s historical comparison](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PILOT.md:55):

- **+1.316 visits** is E3b-1’s pooled T-A/T-F gain.
- E3c reuses **T-F alone**.
- T-F’s old-block mean was **8.066**, against seed **5.840**: a gain of **2.226 visits**, or \(d=0.3812\).

Those figures follow from [E3b-1’s recorded readings](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/evaluate.json:5253) and [per-controller means](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/evaluate.json:5720).

Thus the argument that S-mod’s approximately 1.82-visit gain already exceeds the relevant tuning gain is wrong. Different blocks, training lengths, and champion selection still prevent a direct comparison.

An honest registration can preserve the original directional prediction while stating that rapid S learning makes the eventual contrast uncertain. The two-sided test already permits either outcome.

**5. Power analysis and practical margins**

**Model Q1 and Q2 separately within one joint simulation.** The S-arm SDs cannot serve as a common variance estimate.

The simulation should include:

- **An optimistic, reliable-learning scenario:** S-mod SD 0.050 and S-dense SD 0.071 visits, with wider-variance sensitivity cases. Three runs are weak evidence about the population spread.
- **Successful/failed-run mixtures for the S arms**, despite their observed 3/3 successes. Vary success probability, failure level, and spread within each component. For illustration, 90% near 6.7 and 10% near 1.7 produces approximately **1.5 visits of SD** from mixture membership alone.
- **P-joint’s own distribution.** T-F’s old-block run SD is **1.032 visits**, far larger than the S spreads. Treat that as historical guidance with sensitivity to reselection and block changes. At eight runs per arm, this alone suggests a Q2 standard error near **0.37 visits**, even with very stable S-mod.
- **Endpoint uncertainty:** these are generation-99 training-best candidates. The formal endpoint is a validation-selected champion after 300 generations. Do not assume identical distributions. Do not use generation-0 draws as though they were terminal failures.
- **The actual two-sided Welch/Holm procedure**, with the same simulated S-mod sample entering both contrasts. Include global and partial nulls, unequal variances, and mixture shapes to check false-positive behaviour as well as power. Include the prescribed floor guard and the eventual practical-effect wording. Examine eight-run and permitted six-run scenarios.

The design already specifies the run as the independent unit and inference conditional on the test block: [§6](D:/Claude/random/wormWars/docs/E3/E3c-DESIGN.md:196). Maze resampling is a supplement; 256 mazes do not become 256 evolutionary replicates.

**P-sel is descriptive.** Its 1/3 split warrants mixture scenarios and explicit uncertainty, not a confident estimate of bimodality or a success probability fixed at one-third. It should not determine Q1/Q2’s sample-size justification.

**My recommended practical margin is 0.5 visits per wey for both Q1 and Q2.** That means four additional confirmed visits per eight-wey colony over the fixed horizon. It is a substantive task improvement and half the established one-visit floor margin. This is a scientific judgment, not something the pilot estimates.

Fix it in absolute units; its normalized equivalent is \(0.5/\bar V_{\mathrm{seed,test}}\), with that conversion specified beforehand. Show power at 0.5 and 1.0 visits, in both directions. Do not shrink the margin toward the pilot’s S-arm difference of only **0.081 visits** because that difference may be statistically detectable.

Finally, distinguish detecting a nonzero difference from establishing a difference beyond the practical margin. A significant Welch result plus a point estimate over 0.5 does not itself establish that the true advantage exceeds 0.5.

**6. The next step, its cost, and its consequences**

**Replay the original three-run S-dense batch once, saving genomes and hashes.** This is preferable to claiming that an isolated rerun recreates a particular pilot champion.

The recorded S-dense `batch_seconds` sum to **3,903.7 seconds, or 1.084 GPU-hours**; those are batch timings, not per-run timings. Its training composition was 96 strains × 8 worlds × 8 weys. See [timings](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/pilot.json:8186) and [composition](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/pilot.json:18421).

Budget **1.5 GPU-hours total** for that replay and bounded probing. Preserve the original recipe and composition, compare recorded hashes, and save final populations plus checkpoint candidates. Hash agreement must be checked; it should not be promised. If hashes differ, describe the resulting organisms as exploratory retraining.

Evaluate all three recovered finals intact and with nose inputs removed on the pilot block, alongside seed/W2 controls, and inspect a fixed small trajectory sample. Do not use the future formal blocks or select replacements based on these probes.

The possible consequences should be fixed now:

- **Performance survives and paths show repeated coverage:** register that mechanism hypothesis, narrow the stereo-assembly language, and retain the formal secondary nose reading.
- **Performance drops substantially:** retain the nose reading, withdraw the scent-free explanation as the leading account, and avoid claiming stereo comparison without a more specific probe.
- **Mixed or ambiguous results:** register heterogeneity/uncertainty and proceed. Do not launch an open-ended search for a cleaner story.

None of those outcomes changes the maze branch, factor, schedule, or primary contrasts.

Before registration, also correct two record issues. The seed diagnostic establishes matching **block means** for the two paths, as recorded in [seed-check.json](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/diagnostics/seed-check.json:1). But SD 3.675 implies a block-mean SE of about **0.325** for 128 independent mazes; it does not by itself justify saying block means typically move by a visit. And its approximately **0.030 GPU-hours**, explicitly omitted in [PILOT.md](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PILOT.md:87), should be charged to E3c’s ledger: usage is approximately **2.85**, not strictly 2.82, before further work.