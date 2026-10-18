**revise.**

T1 is a defensible choice for generation 0. The remaining problems concern its implementation contract, the scripted gate, and the registered readings—not a need to choose another task.

I checked the files on `roadmap` at `e0efdd8`, including both archived reviews and D322. I made no changes and ran no experiments or tests.

1. **§§1–9 — Round-1 audit; severity as indicated below.**

   “Resolved” here means resolved in the design, not verified in an implementation. These are the numbered findings in [Astra’s round-1 review](/D:/Claude/random/wormWars/docs/reviews/20261018-03h-design/astra.answer.md).

   | R1 finding | Status | Assessment |
   |---|---|---|
   | 1. A’s success criterion and interpretation | **Partly** | Positive A1 and the association-only interpretation are adopted. The new sham contrast no longer supports §1’s unqualified level-versus-relief wording; see finding 6 below. |
   | 2. ASK routing | **Resolved** | The new sampler names and ASK extension address the design objection. Validate both chemical/gap counts and weight caps. |
   | 3. Added drive versus information | **Partly** | Sham is added, but matching is limited and the pre-clamp observation issue remains. |
   | 4. Partial Spearman and effect threshold | **Partly** | H, S, ranks and residuals are defined. Ensemble aggregation and evidence for exceeding δ remain unspecified. |
   | 5. Shared-world uncertainty | **Partly** | Crossed resampling is adopted. Precision rules and handling of undefined statistics remain promises. |
   | 6. B’s upper-tail estimand | **Partly** | Independent selection/test banks and the initial-advantage requirement resolve the main objections. The interval procedure and decile rounding remain open. |
   | 7. Ensembles, multiplicity, rank interpretation | **Partly** | One primary ensemble and Holm resolve the main choices. Define exactly what “03’s rank rule” imports and constrain budget-driven graph cuts. |
   | 8. Scripted gate | **Partly** | Tuning/check separation and equivalence intervals are adopted. T1 introduces substantive family and emulation problems. |
   | 9. History measurement | **Partly** | Identical genomes and the primary bank are specified. Correct the bank’s provenance and freeze the probe parameters. |
   | 10. Frozen-champion diagnostic | **Resolved** | Separate, exploratory and not gated on A is acceptable. |
   | 11. Cited facts | **Resolved** | The earlier numerical, quotation and scope corrections are incorporated. New T1 inaccuracies are identified below. |
   | 12. Budget | **Partly** | Pilot timing and incomplete-run reporting are adopted. The borrowed throughput does not establish T1 feasibility. |
   | 13. Registration decisions | **Partly** | C’s gate and several operational rules are settled; important pilot and formal choices remain open. |

2. **§§2, 4–6 — Major: T1’s outcome is specified incorrectly, and its experimental unit changes.**

   T1 does **not** score target counts. [`foraging_score()`](/D:/Claude/random/wormWars/wormwars/evo/rollout.py:54) returns surviving swarm energy divided by starting swarm energy. Consequently, “T1’s mean count,” “0.5 targets,” and expressing δ in “targets” are wrong. The cited +0.942 is a difference in this energy-ratio score.

   Register that score explicitly, and decide whether 0.5 and ±0.3 are defensible margins **in those units**. Food consumption can be a separate diagnostic; it is not interchangeable with fitness. A zero fitness score means the whole swarm died, not that it reached no food.

   T1 retains **one swarm of 20 weys**, with shared food, crowding, hazards, energy expenditure and corpse pellets. A genome is therefore evaluated through a group’s performance. The weys are interacting components, not 20 independent replicates. Keep worlds as the resampling unit; define the relief state separately for each wey. Food decline can reflect consumption by neighbours as well as movement down a gradient.

   This is still suitable for the proposed association screen. It changes the interpretation to history versus **swarm foraging performance**, including survival and movement costs.

3. **§§2–4 — Minor correction / no task blocker: the bank already comes from T1; pheromone silence is correctly limited to sensing.**

   The bank provenance is better than v2 suggests. [`scripts/exp03.py:498`](/D:/Claude/random/wormWars/scripts/exp03.py:498) explicitly collects it with `cfg_for("T1")`. This is not a transfer from a different task to T1. Its nonzero hazard and collision inputs are appropriate to this world. The archived assertion that it was T0’s bank should be corrected.

   Retain the committed bank as primary. A newly collected bank would be a **new sampling/calibration sensitivity analysis**, requiring its own construction rule. Freeze the existing probe’s 100-tick warm-up, 10-tick ramp, 0.25/1.75 start multipliers and final-tick measurement explicitly. The bank values are already scaled signal values; do not apply the world’s food scale again.

   Pheromone sensing really is zero in T1. However, deposition remains enabled: [`task_config()`](/D:/Claude/random/wormWars/wormwars/exp02/grid.py:49) zeros the sensing scale, while the world still deposits and updates pheromone. Thus ASK’s pheromone **input** is silent; neither the neurons nor the field are absent. V2’s wording on this distinction is correct.

4. **§3 — Major: the scripted gate’s equivalence and nesting claims are not yet valid.**

   [`MemoryKinesis`](/D:/Claude/random/wormWars/wormwars/exp02/scripted.py:148) tests:

   `level < previous_level - fall_threshold`

   The proposed bit only encodes a strict fall. It can reproduce the **zero-threshold** member, not the whole family. The original tuning grid includes nonzero thresholds. The saved T1 winner does have threshold zero, so the narrow emulation claim is supported; the unrestricted claim is not.

   There are three further problems:

   - `MemoryKinesis` contains `LevelKinesis`, but not generally `GradedKinesis`. Include the graded policies in the memory-capable family, for example through a registered union with an ignore-history option.
   - Only one-tick memory is actually named. That cannot test the stated claim about gains “beyond one tick.” Either add defined longer-history families or narrow the gate’s interpretation.
   - Scripted policies read **clamped injected currents**, whereas the bit is specified before gain and clamp. Two saturated readings can look identical to the controller while the pre-clamp bit reports a fall. Compute the comparison from the available food observation, or establish that clipping cannot alter it.

   The tuning/check split and paired equivalence procedure are sound choices. They do not repair these policy-definition problems.

5. **§§3, 6 — Major: the gate/pilot order is circular; sham matching is overstated.**

   The complete scripted gate must run “before any neural run,” but its sham transition rates come from a neural pilot. Those instructions cannot both be followed.

   A workable registered sequence is: level/relief scripted checks → restricted level-only null pilot to estimate sham rates → freeze sham → sham scripted check → remaining pilot measurements. Alternatively, explicitly place the complete gate after the pilot and before formal measurement. Choose one before registering the pilot.

   Also freeze the Markov initial state, transition estimator, pooling weights and treatment of dead weys. Matching two transition probabilities under **pilot level trajectories** does not ensure equal drive under formal relief trajectories or on N2. Independent per-wey sham streams also need not reproduce cross-wey correlations in live falls. Report realised bit occupancy and transitions by condition, and replace “changes the input equally” with the narrower matching claim.

   An exogenous random bit supplies no external food observation, but it can still improve a policy by randomising its actions. The sham gate tests performance neutrality within the chosen families; it does not establish that random stimulation can never be useful.

6. **§§1, 5 — Major: A’s revised tests do not imply its stated contrast.**

   A1 requires \(\rho_L>0\); A2 requires \(\rho_S-\rho_R>0\). Neither requires \(\rho_L>\rho_R\).

   For example, \(\rho_L=0.10,\rho_S=0.30,\rho_R=0.20\) satisfies both, although prediction is stronger under relief than under level.

   Keep the proposed tests, but state their conclusion precisely: **“History predicts fitness positively under level, and its association is stronger under sham than under relief.”**

   Likewise, “meaningful” should require inferential evidence that the ensemble contrast exceeds δ, not merely significance against zero plus a point estimate above δ. A top-versus-bottom H-quartile score difference is a useful additional effect description; it is not a conversion of a correlation difference into fitness units.

   Finally, replace “the relief was not exploited” after a nonsignificant manipulation check with **“no improvement was detected.”** Distinguish an adverse effect from an imprecise estimate.

7. **§§4–7 — Moderate, but required before formal registration: complete the statistical contract.**

   The remaining choices include:

   - Equal graph weighting for A, the bootstrap-to-p-value procedure, and the conjunctive p-value supplied to Holm—for example, `max(p_A1, p_A2)`.
   - A concrete rule for constant scores and degenerate residuals. Saying they are “kept” does not define a statistic.
   - B’s selected count, interval level and resampling procedure. If inference includes selection uncertainty, resample the selection and test banks separately and repeat selection within each resample.
   - Whether “03’s rank rule” means only its rank formula or also its effect-margin gate.
   - The unequal genome allocation: §4 suggests G per graph, while §7 gives N2 twice as many. This changes finite-sample precision and potentially selected-tail behaviour; match the primary comparison or justify the asymmetry.
   - Explicit calibration-failure and seed-disjointness rules. §9 claims disjoint world ranges more broadly than the body specifies.

   Keep the approximate reference-ensemble qualification attached to **03h’s** B test. Graph cuts also need a minimum tied to Holm’s attainable thresholds; cutting the primary ensemble to 32 would prevent B from passing Holm’s first 0.025 threshold.

8. **§§2, 7 — Moderate: six hours is an acceptable ceiling, not an established budget.**

   The roughly 13-million-world count is consistent with evaluating all genomes on both banks. The 892-worlds/s reference does not validate its runtime: T1 has 20 neural agents per world and food, hazard and crowding dynamics. This is a task/workload change as well as a batch-composition change.

   Time the actual T1 workload, calibration and probe before fixing allocations. Record the actual chunk composition: [`rollout()`](/D:/Claude/random/wormWars/wormwars/evo/rollout.py:159) chunks populations, so 512–1,024 total genomes does not imply that many strains in every neural batch. Padding relevance depends on those chunks, including any selected-decile evaluation.

9. **§9 “Merged” / D322 — Decisions on the four points.**

   | Point | Decision | Reason |
   |---|---|---|
   | H primary, H_dir key secondary | **Accept** | This directly screens the existing P4 numerator while retaining the directional hypothesis as a declared secondary. |
   | SH-mirror-ASK primary, SH secondary | **Accept** | This addresses the identified direct-routing problem and keeps one primary reference ensemble. |
   | Separate frozen-champion check after binding, not gated on A | **Accept** | It preserves the independent question without delaying or contaminating 03h’s confirmatory family. |
   | At most six GPU-hours, set from pilot | **Accept** | This is defensible as an allocation ceiling, conditional on actual T1 timing and a registered infeasibility rule. |

10. **§§3–7 — Readiness.**

   **Not yet ready for the pilot’s registration without substantive corrections.** Settle the score and margin units, scripted families, observation/clipping convention, and gate–pilot ordering first. Then the pilot registration must specify its exact graph allocation, sham estimator, precision targets, G/W/W_t selection rules, permissible budget cuts and stop conditions.

   **The formal pre-registration must follow the pilot**, with those outputs fixed and finding 7’s statistical choices completed. The task switch itself is acceptable; no further task search is needed to resolve these issues.