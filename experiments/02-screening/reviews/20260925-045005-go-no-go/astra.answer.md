1. **MAJOR — Conditional GO for B+, but NO-GO on the current interpretation and pipeline.** I would keep the D034 tasks and run a 40-generation screening after fixing the issues below. The scripted results establish that these capabilities can pay; they do not establish that evolution must discover them. More replication is useful for estimating success under this particular search budget. It cannot establish that shuffles *cannot* acquire a capability.

   I would redesign the probes before redesigning evolution or the tasks. If the required outcome is an identified test of temporal computation, T1 is not ready for that claim.

2. **MAJOR — Seeing N2’s response does not invalidate future comparisons, but B+ is an informed redesign.** Disclose the value, exactly how it was measured, when it was seen, and which choices it influenced—including replacing the failed shuffle feasibility gate with capability use as an outcome. Label the resulting prediction as motivated by preliminary N2 evidence.

   Fresh evolutionary runs can test that prediction prospectively. They cannot make its origin independent of N2. Preserve the failed gate and the alternatives considered; do not retrospectively describe B+ as the original plan. The existing design already calls the interaction exploratory, which remains appropriate.

3. **MAJOR — Point 4 does not yet establish the proposed structural cause.** The implemented [input-response probe](D:/Claude/random/wormWars/wormwars/exp02/probes.py:74) computes its “differential” response as:

   `abs(trace(0.5, 0.0) - trace(0.0, 0.0))`

   This changes both common-mode food level and left–right difference. A controller responding only to total food could score strongly. It also measures absolute raw motor read-out, without the world’s calibrated gains and clipping; it does not measure steering in the correct direction.

   Before calling this a stereo-routing bottleneck, specify a fixed-common-mode comparison: `(b+d, b-d)` versus `(b-d, b+d)`, with signed and absolute responses reported separately. Report both raw read-out and actual motor commands. Keep common-mode responsiveness separate. Moreover, a spatial input-response difference supplies no direct evidence about temporal computation.

4. **MAJOR — Neither jitter probe currently identifies “uses history.”** Jitter-1 selectively disrupted **one particular scripted memory strategy** while sparing the tested `LevelKinesis`. That is useful validation, but its sensitivity and specificity do not transfer automatically to evolved controllers. A memoryless nonlinear policy can be harmed by altered instantaneous readings; a controller integrating over several ticks can average out the jitter.

   The saved diagnostics make jitter-3 particularly unconvincing: it reduces the memoryless controller’s score by **0.057 [0.046, 0.069]**, larger than the reported **0.039** champion loss. That champion result is not evidence of history use.

   Also, [the validation rule](D:/Claude/random/wormWars/scripts/exp02.py:160) accepts a confidence interval containing zero as evidence that the memoryless controller is unchanged. Use an equivalence margin instead. Its second condition requires reduced memory advantage, not necessarily removal of that advantage.

   **Pre-register jitter-1 and jitter-3 as sensitivity outcomes. Neither alone should trigger a generic “uses history” classification.** For stronger identification, add matched-current replay: vary preceding food histories while holding the current complete input and non-food history identical, across declared timescales. That can establish food-history-dependent output. Demonstrating that this dependence improves foraging needs an additional validated behavioral intervention; replay alone does not establish benefit. If that work is deferred, defer the stronger claim too.

5. **MAJOR — The stereo ablation also needs a cleaner primary contrast.** The current [mono implementation](D:/Claude/random/wormWars/wormwars/world.py:508) replaces two lateral samples with a centre sample. It changes sampling geometry and common-mode concentration as well as removing left–right information.

   Keep that as a useful physical intervention, but make the primary differential-information ablation feed `(L+R)/2` into both sides, with clipping order explicitly fixed. Add left–right swapping as supporting evidence for directional steering. Validate against controllers using only the bilateral mean and against the scripted stereo controller.

   The existing real-minus-mono difference should be called **sensitivity to single-nose substitution**, not automatically proof of stereo comparison.

6. **MAJOR — Register explicit estimands, including acquisition versus starting advantage.** For each frozen champion, task, mapping and probe \(p\), define:

   \[
   U_p = E_{\text{world, probe randomness}}
   [Y_{\mathrm{real}}-Y_p].
   \]

   Keep signed values; negative values mean the intervention helped. Specify the actual constant used for food replacement—the implementation uses each world’s initial spatial mean food—and interpret this as dependence on the varying food signal.

   Define N2’s mean over runs, SH’s mean over **equally weighted graph means**, and the direct contrast \(\Delta_p=\mu_{N2,p}-\mu_{SH,p}\). If mapping specificity matters, register the capability-use interaction:
   \[
   \Delta_p(M0)-\tfrac12[\Delta_p(R1)+\Delta_p(R2)].
   \]

   State which outcomes are primary; my choice would be T0–M0 differential-information dependence as primary, with the unvalidated history proxies secondary. Keep the fitness interactions separately.

   Probe generation-0 champions as well as generation-39 champions, at least for the principal mechanistic cells. Otherwise, greater capability use at generation 39 cannot distinguish an initial advantage from acquisition during evolution.

7. **MAJOR — Thresholds must separate meaningful use, negligible use and uncertainty.** A defensible starting choice is **0.10 raw score units** for meaningful behavioral dependence—roughly a tenth of the scripted capability gains—and **±0.02** for acceptable effects on negative-control policies. These are proposed design choices, not thresholds established by the present evidence. Freeze and justify them before N2 results.

   For a validated assay, classify meaningful use only when the interval lies above the use threshold; classify negligible dependence only when the interval lies inside a declared equivalence region. Everything else is inconclusive. A nonsignificant SH result is not evidence of absence, and “significant for N2, nonsignificant for SH” is not a between-group comparison.

   Specify the multiplicity treatment for any decision-making labels. Reporting many exploratory intervals is acceptable; selecting whichever probe, mapping or radius supports the narrative is not.

8. **MAJOR — Replace “N2 uses what shuffles cannot” with a falsifiable, budget-limited prediction.** Suitable wording is: “Under the registered 40-generation procedure, N2 champions show greater meaningful dependence on bilateral food information than champions from the sampled shuffle distribution.”

   Its proposed explanation would be challenged by:

   - N2 dependence being tightly below the meaningful-use threshold.
   - A direct N2–SH contrast tightly at zero or reversed.
   - Reproducible capability use in SH champions, which directly contradicts categorical “cannot.”
   - Similar N2 advantages under the remaps, which weakens the M0-specific explanation.
   - The difference already being present at generation 0, which weakens an acquisition claim.

   Wide intervals are inconclusive. Failure under jitter-1 does not falsify general history use. Eight graphs also cannot establish a rare capability’s absence: even an ideal independent binary test with zero successes in eight graphs has a one-sided 95% upper success-rate bound of about 31%.

9. **MAJOR — There are concrete implementation blockers before running.**

   [The analysis code](D:/Claude/random/wormWars/wormwars/exp02/analysis.py:153) expects diagnostic keys `one_step_memory` and `level_kinesis`; the actual JSON contains `M` and `K`. The report will encounter a `KeyError`. Its nearby `temporal_check()` still treats losses under constant and mirrored food as temporal evidence, contrary to D037, and pools T1 champions across graphs and mappings.

   [The schedule](D:/Claude/random/wormWars/wormwars/exp02/grid.py:35) still specifies four N2 runs and six SH graphs. Calibration contains SH1–SH6 only; diagnostic reference scores cover the old run seeds. Increasing the counts requires extending those inputs too.

   Fix these and run a report smoke test using the actual diagnostic schema and synthetic champion records before generating N2 fitness data. Update the design’s stale “no code/data exists” statement and freeze the revised protocol.

10. **MAJOR — Save enough probe data to support the proposed inference.** [Capability probes currently return only means](D:/Claude/random/wormWars/wormwars/exp02/probes.py:47), and [the caller uses just 16 checkpoint worlds](D:/Claude/random/wormWars/scripts/exp02.py:365). This cannot support a paired world-level uncertainty estimate for each champion after the fact.

    Save per-world real and intervention scores, world identifiers, and probe-randomness seeds. Use multiple independently seeded jitter realizations if averaging over jitter is part of the estimand. Prefer a frozen final probe suite, separate from convergence monitoring.

    Preserve whole vectors of cells and probes when resampling runs; resample SH graphs with runs nested within them. Report individual graph/run results alongside group means. Worlds and worms are not additional independent evolutionary replicates. Extend numerical verification to capability contrasts themselves if those become substantive outcomes.

11. **MINOR — Recheck cost and preserve the missing pilot evidence.** The committed pilot timings precede the commit adding jitter-1, jitter-3 and mono to every champion’s probes. Those timings therefore do not measure the present battery. They also do not include the generation-0 probe sweep. Retiming should include the revised suite, the 400-tick anchor, and any generation-0 capability measurements. The runner’s cap applies to evolution, not the subsequent probe command, so reserve that budget explicitly.

    Keep the planned continuations. The current convergence fit pools graph families within each task/mapping, which can conceal different learning curves; analyze them separately before claiming saturation.

    I verified the scripted gate and the failed 40-generation pilot against the specified JSON files. Those files do not contain the 80/120-generation results, population/world sweeps, graded-controller result, or eight-shuffle response table; archive those with their commands and seeds before freezing. This was a static review: the available Python launcher could not access an interpreter, so I did not execute tests or generate additional N2 measurements.