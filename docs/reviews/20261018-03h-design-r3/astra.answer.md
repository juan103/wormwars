**revise.**

Most round-2 objections are addressed. One new contradiction blocks the proposed implementation: **B evaluates only the original selected decile, but its bootstrap repeats selection and therefore needs test scores for other genomes.** The pilot’s adaptation rules also remain insufficiently specified.

I checked `roadmap` at `0ddf41f`, both review rounds, the committed pilot arrays, and the relevant implementations. No files were changed; no experiments, tests or GPU work were run.

1. **§§5–6, 8 — Major, blocking: B’s data collection cannot support its registered intervals.**

   [§5](/D:/Claude/random/wormWars/experiments/03h-history-use/DESIGN.md:154) evaluates only the selected 26 genomes on the test bank. [§6](/D:/Claude/random/wormWars/experiments/03h-history-use/DESIGN.md:204) resamples selection worlds and repeats selection. A genome originally ranked 27th can enter a bootstrap decile, but its test scores do not exist.

   Choose explicitly between:

   - **Conditional inference:** freeze the originally selected genomes and bootstrap the shared test worlds, with appropriate graph resampling for ensemble averages. State that these intervals condition on the genome draws and selection bank.
   - **Reselection inference:** collect test scores for all genomes that can be selected. Evaluating all 256 is the straightforward complete solution.

   This choice changes the budget:

   | Primary: 64 null graphs + N2 | Episodes | Fitness hours at 171/s |
   |---|---:|---:|
   | Current selected-only design | 1,123,200 | 1.82 |
   | All 256 genomes, 64 test worlds | 3,993,600 | 6.49 |
   | All 256 genomes, 32 test worlds | 2,396,160 | 3.89 |

   Thus the current arithmetic is correct, but it prices a different uncertainty procedure. Testing all genomes on 32 worlds looks provisionally compatible with the six-hour ceiling after dropping SH; actual timing must decide.

   Also specify which scores supply “expected best of 32.” Selection-bank order statistics are computable, but do not estimate held-out expected-best performance without selection optimism.

2. **§§2, 5, 7–8 — Moderate: W = 16 is reasonable provisionally; its reliability and power justification are overstated.**

   From the 16 `T1-M0` matrices in [pilot.json](/D:/Claude/random/wormWars/experiments/03-generation0/pilot.json:120):

   | Quantity | Checked value |
   |---|---:|
   | Genomes × worlds per graph | 256 × 16 |
   | Graph mean fitness range | 0.86468–0.91067 |
   | Zero episode scores | 0 |
   | Mean across graphs of SD of genome means | 0.26082 |
   | Mean within-genome world SD | 0.25460 |
   | Square root of mean within-genome world variance | 0.26078 |

   The reported “0.26” and “0.25” therefore have identifiable support, although the latter averages SDs rather than variances. The minimum mean should be approximately **0.865**, rather than a literal 0.87 lower bound.

   **“Reliability 0.94” is a rough variance-ratio approximation, not a directly demonstrated property of this assay.** Observed genome-mean variance already contains sampling noise, and shared worlds contribute common effects that differ from genome-by-world variation. Using the simple uncorrected ratio graph by graph gives approximately **0.941 at W = 16 and 0.888 at W = 8**.

   More importantly, reliable fitness means do not establish adequate precision for partial Spearman or \(D=\rho_{\mathrm{sham}}-\rho_{\mathrm{relief}}\). Shared-world uncertainty remains relevant across all 64 graphs.

   The timing correction is otherwise supported. The cited **65.8938 seconds and 11.4167 calibration seconds are pilotSH101’s values**; the corresponding averages across 16 graphs are **65.1430 and 10.8374 seconds**. The 11,264 episodes cover five fitness cells, including T0 and T1const, rather than T1 alone. The separate [T1 timing record](/D:/Claude/random/wormWars/experiments/03-generation0/timing.json:20) gives **166.4 episodes/s at 256 × 16**, supporting 171/s as a planning approximation.

3. **§4 — Moderate implementation clarification; the substantive gate objection is resolved.**

   Adding genuinely slower memory removes the structural identity. Including `GradedKinesis` in the memory-family union also repairs the previous nesting problem. The tuning/check split is appropriate.

   The **0.5 lower-bound requirement and ±0.3 equivalence margin are now in the correct energy-ratio units**, and the historical +0.942 and +0.98 comparisons support their scale. They remain chosen screening margins, not empirically established equivalence tolerances. “A third of the level gain” should mean the historical approximately 0.94 gain; 0.3 is 60% of the minimum accepted 0.5 gain.

   Before coding the family, specify its update and decision rules. Existing [KTS](/D:/Claude/random/wormWars/wormwars/e03a/probe.py:102) uses the **previous** exponential average for the comparison, then updates it:
   \[
   m_t=m_{t-1}+(x_t-m_{t-1})/T.
   \]
   Port that memory mechanism into the T1 policy. KTS also contains level-dependent turning and collision avoidance; copying those features would change the policy comparison.

   Specify whether the slow comparator includes `fall_threshold`, and how internal history and the supplied bit combine. Existing KTS corresponds to the **zero-threshold** comparison. If exact T = 1 equivalence is required, directly storing the current level avoids floating-point differences from evaluating `avg + (level - avg)`.

   Nesting does not guarantee held-out sham equivalence: tuning can select a worse policy. Define the sham interval procedure and what a failed sanity check causes.

4. **§3 — Minor: the bit is adequately defined; the sham needs boundary conventions.**

   **The amplitude is defensible.** A 0.25 current at each ASK neuron is about 1.12 times the bank’s 0.22338 food current per receiving neuron, comfortably below the clamp of 5. This compares per-neuron input scales, not total drive or downstream effect.

   **The post-clamp definition resolves the observation mismatch.** First-tick zero, per-wey state, dead-wey masking and no hidden-event reset are appropriate.

   The pooled transition MLE is now a workable estimator. Write its remaining conventions explicitly:
   \[
   \hat p_{01}=N_{01}/(N_{00}+N_{01}),\qquad
   \hat p_{10}=N_{10}/(N_{10}+N_{11}).
   \]
   Count adjacent observations within the same trajectory; specify whether both endpoints must be alive, exclude artificial transitions across boundaries, and define zero-denominator/nonunique-stationary cases.

   The stationary start implies occupancy \(\hat p_{01}/(\hat p_{01}+\hat p_{10})\). This need not exactly equal finite-trajectory empirical occupancy, particularly with forced-zero initial relief bits. Say **approximately matches pooled occupancy and persistence**.

   Also replace unconditional “independent of the food trend” with “generated without observing food.” Sham-driven actions can create subsequent correlations with food through the world.

5. **§7.2 — Minor qualification: step 0 is feasible, and the fitness genomes have a reproducible construction.**

   [The driver](/D:/Claude/random/wormWars/scripts/exp03.py:448) establishes the required recipe:

   - Names are exactly **`pilotSH101` through `pilotSH116`**.
   - Rebuild SH with the corresponding integer seed and 20 passes.
   - Use `genome_seed(name, "")`, **without `+1`**.
   - Make one CUDA `Genome.random(..., 256, ...)` call with the original configuration and tensor shapes.
   - Preserve genome order when joining to the committed `T1-M0` rows.

   The `+1` seed generates the separate 2,048-genome probe population. Generating individual genomes or another population size is not interchangeable with the original 256-genome draw.

   I compared the relevant code with `132acae`: genome generation, the SH sampler and requirements are unchanged; the seed function retains the original unsalted behavior. **Exact regeneration is supported under the original pinned environment and device assumptions, but was not empirically verified in this review.** That does not imply exact reproduction of historical CUDA fitness trajectories.

   Use a narrow helper, not `measure_graph()`, which recalibrates and performs additional work. H and S use raw readouts and need no new calibration; saved gains are available if needed.

   Step 0 can estimate exploratory **level-association** variation. It cannot estimate D’s variance or transfer SH’s variation automatically to SH-mirror-ASK.

6. **§7 — Moderate: the circularity is resolved, but the pilot decision procedure is unfinished.**

   The new dependency order is executable: level/relief gate → restricted level pilot → freeze sham → sham check → remaining pilot. Exploratory step 0 before the gate is acceptable as explicitly labelled.

   Add an explicit **pilot registration, review, binding and push before the registered gate/pilot measurements**. Step 0 can precede that registration as disclosed exploration. The current numbered sequence mentions pilot registration only indirectly.

   The registration must resolve:

   - **W adaptation:** which reliability estimator, which conditions and aggregation, and exactly what happens below 0.85. §7 permits changing W while §8 says W stays at 16.
   - **Detectability:** power target, significance threshold, alternative and treatment of shared-world uncertainty. SD of \(\rho_{\mathrm{level}}\) alone cannot determine detectability of D.
   - **Pilot size:** a fixed count or an outcome-independent rule selecting between two and four graphs.
   - **Gate details:** controller grids, world counts/ranges, interval methods and sham-failure action.
   - **CUDA equivalence:** perform the bitwise Rule 7 check under the repository’s required deterministic replay conditions.

   One further statistical wording correction: assigning degenerate correlations zero is **not generally conservative for A2**. If relief becomes constant while sham retains a positive correlation, that convention creates positive D. Keep the flags and specify how such outcomes constrain interpretation.

7. **§10 — Round-2 finding audit.**

   “Resolved” means resolved at design level, pending implementation checks.

   | Astra R2 finding | Status | Assessment |
   |---|---|---|
   | 1. Round-1 audit | **Partly** | Most inherited issues addressed; remaining items below. |
   | 2. Outcome and experimental unit | **Resolved** | Correct score, swarm interpretation and world resampling unit. |
   | 3. Bank provenance and pheromone distinction | **Resolved** | T1 provenance and frozen probe parameters are correct. |
   | 4. Gate equivalence/nesting | **Resolved** | Structural repair accepted; implementation details in finding 3. |
   | 5. Order and sham | **Partly** | Circularity fixed; estimator boundaries and matching wording remain. |
   | 6. A’s conclusion and effect wording | **Resolved** | Tests and stated conclusion now agree. |
   | 7. Statistical contract | **Partly** | B’s reselection is incompatible with available scores; zero is not universally conservative. |
   | 8. Budget/composition | **Partly** | Correct workload scale; B’s inference choice changes cost. |
   | 9. Four merged decisions | **Partly** | Main choices retained; separate frozen-champion diagnostic is absent from v3. Its omission need not block 03h. |
   | 10. Readiness | **Partly** | Main substantive corrections made; B and pilot rules remain. |

   | Fable R2 finding | Status | Assessment |
   |---|---|---|
   | 1. Throughput/budget | **Partly** | Rate corrected; inferentially complete B needs repricing. |
   | 2. Relief-gate identity | **Resolved** | Slower-memory alternatives remove the identity. |
   | 3. Units | **Resolved** | Correct units and historical scale. |
   | 4. B’s baseline | **Resolved** | Sham is primary. |
   | 5. Circular order | **Resolved** | Dependency order now works. |
   | 6. Bit observation | **Resolved** | Post-clamp comparison. |
   | 7. Graph cuts | **Resolved** | Primary stays at 64; SH cut first. |
   | 8. Rule 7 | **Resolved** | Equivalence criterion included; apply replay requirements. |
   | 9. Bank provenance | **Resolved** | Corrected to T1. |
   | 10. Existing T1 distribution | **Partly** | Data used; reliability interpretation needs correction. |
   | 11. ScriptedBrain extension | **Resolved** | Extension and test explicitly included. |
   | 12. Amplitude | **Resolved** | Numerical amplitude and rationale supplied. |
   | 13. Composition/padding | **Resolved** | Padding off, separate banks and chunk recording specified. |
   | 14. Remaining statistical choices | **Partly** | Most fixed; seed/world allocation and B’s uncertainty contract remain. |

   **The bit, sampler and controller helper code can proceed. Resolve B’s scoring/inference choice before implementing the experiment runner, and make the pilot’s adaptation rules operational before binding its registration.**