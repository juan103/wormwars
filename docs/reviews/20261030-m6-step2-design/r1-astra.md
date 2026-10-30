**Proceed to a plan with fixes—but describe this as a test of neural timescale dependence, not an identification of useful probe-defined memory.** The intervention is informative within the budget. The proposed primary reading and validation rule need correction.

I checked the design against the brain update, rollout score, probe implementation, M6 records, and D379/D381. The two draft copies are identical. I did not modify files or run simulations.

1. **The intervention is defensible; its mathematical description overstates what is preserved.**

   The fixed-point equations are unchanged. However, “every transient is k times as long” is not true of the implemented experiment.

   That statement holds for the continuous dynamics under constant input, from the same initial state. During foraging, inputs change on the unchanged world clock. The probe also keeps its warm-up and ramp durations unchanged.

   Furthermore, [Brain.step](/D:/Claude/random/wormWars/wormwars/brain.py:434) uses a semi-implicit update. Writing its right-hand-side dynamics as \(F_j\), one substep satisfies
   \[
   v_j^{+}-v_j=\frac{hF_j(v,I)}{k\tau_j+h(1+g_j)}.
   \]
   Thus scaling tau does not simply rescale the discrete trajectory’s time uniformly. Fixed points remain fixed, but transient distortion depends on the neuron’s gap conductance.

   Required changes:

   - Say “preserves the fixed-point equations; changes temporal responses, with history suppression measured empirically.”
   - Add a small, predetermined numerical sensitivity check at higher substep counts, including \(k=1\) and \(0.25\), with acceptance criteria fixed beforehand.
   - Scale copied parameters without subsequently calling `Genome.clamp_()`: that would clip tau back to its evolutionary bounds and change the intervention.
   - Preserve each run’s interface, gains, configuration, seed and batch composition. Check the \(k=1\) intervention path against the intact path.

   Even after these fixes, faster sensory responses, collision responses, motor transients and adaptation to changing inputs remain inseparable from shorter history dependence. The controls cannot remove that limitation.

2. **Keep the controls, but weaken their interpretation and repair probe validation.**

   **g00 and drift:** useful comparisons, but they do not estimate a universal “generic cost.” They have different performance, weights and operating regimes. Small probe history effects do not make them memoryless controls. Show comparisons against each separately; their average can conceal disagreement. One drift replicate per run is acceptable for this budget if its identity is fixed in advance—reuse a named M6 replicate and its [recorded seed/hash](/D:/Claude/random/wormWars/scripts/memory_m6/m6_0.py:90).

   **\(k=2\):** keep it, but call it a slowing arm. It is reciprocal to \(0.5\), not \(0.25\). Losses in both directions are compatible with useful memory having a preferred timescale; they do not establish a local optimum or count against memory use. Conversely, asymmetric losses do not eliminate ordinary timescale tuning. I would not add \(k=4\) merely to obtain symmetry.

   **Across-champion association:** worth reporting cheaply, but it is not a causal dose-response. The actual intervention doses are the different k values within genomes. Across genomes, baseline history amplitude can covary with gain, mapping, baseline performance and other evolved properties. Prespecify the correlation and block handling; treat it as supporting association.

   **Probe validation needs substantial revision.** Requiring every genome’s \(a\), \(d(5)/a\), and \(\tau_{\mathrm{stay}}\) to shrink is unjustified. The existing records contain one switch champion, unresolved controls and controls below the amplitude floor. Changing tau also changes the states produced by the fixed-duration ramp. Normalized decay can behave differently from absolute history magnitude.

   I would:

   - Freeze the existing own banks across arms.
   - Choose one primary manipulation measure, such as integrated absolute read-out separation over a fixed, task-relevant horizon.
   - Report amplitude and normalized persistence as supporting measures, with explicit floor and censoring rules.
   - Define a population-level validation criterion and report individual failures without selecting them out after seeing scores.
   - Keep the known switch identified separately, with a prespecified fading-only sensitivity analysis.

   A cheap additional check would generate the two ramp-end states at \(k=1\), then continue those **same states** under each k and common input. That separates changes in writing the history from changes in its subsequent decay. The existing [probe code](/D:/Claude/random/wormWars/scripts/memory_m2/pilot.py:47) makes this distinction concrete.

   I would not require an “outside the read-out only” arm. It still changes sensory-to-motor processing and does not supply the missing specificity.

3. **The proposed primary contrast does not support its proposed wording.**

   There is a decisive logical problem: champions could change by **0%**, controls improve by **10%**, and the primary contrast would be **−10%**. Its interval could lie below zero without any champion impairment.

   My preference is:

   - **Primary:** within-champion score change at \(k=0.25\).
   - **Secondary:** the difference between that change and each control’s change, separately.

   If you retain the interaction as primary, any “depends on” reading must additionally require an actual champion reduction. A negative interaction alone means a less favorable intervention response.

   Absolute score changes are suitable here: [the score already normalizes surviving energy by starting energy](/D:/Claude/random/wormWars/wormwars/evo/rollout.py:57). Relative changes are also defensible, but specify **ratio of the 32-world mean scores**, check denominators, and report absolute changes alongside them. Relative normalization does not make the control groups otherwise comparable.

   Suitable positive wording:

   > Reducing all neural time constants to one quarter reduced the champions’ mean T1 foraging score. The reduction exceeded that observed in [named control].

   Then:

   > Together with reduced probe history effects, this supports a contribution of neural temporal dynamics to performance. It does not establish that the probe-defined fading history effect mediates the benefit.

   For an interval spanning zero, say “no reliable mean reduction detected,” and report the interval. If champions decline but the control interaction spans zero, report **a champion decline with no detected excess over that control**. That is materially different from no effect.

   Fix the averaging explicitly: worlds within genome, paired changes within run, mappings within graph/run block, then equal weighting of the 30 blocks. Also fix bootstrap settings, incomplete-run handling and the distinction between exploratory work and a confirmatory pre-registration.

4. **The cost is plausible; the precision claim is unsupported.**

   The rollout arithmetic checks: \(306\times4\times3.5\) seconds is **71.4 minutes**. That leaves about 19 minutes within the 1.5-hour estimate for rebuilding controls, validation and numerical checks. The three-hour cap looks reasonable, but the full workflow needs a representative timing check. Archive the disclosed timing command, configuration and raw output.

   Do not rerun long switch classification just to validate suppression. Short curves over a fixed horizon should suffice; if retaining M6’s \(\tau_{\mathrm{stay}}\), retain its actual observation horizon and cost it accordingly.

   Delete the claim that approximately 10% should be detectable “if the spread is like M6-0’s.” M6-0’s rank and switch statistics do not establish the variance of this score interaction. A smaller effect is not automatically indistinguishable. Either provide a justified precision calculation or leave precision unknown.

   I see no clearly superior, equally cheap selective intervention established here. However, the alternatives paragraph is wrong to say resetting toward equilibrium preserves latency: it bypasses ordinary temporal responses and can jump motor output. The “100 times” cost also needs evidence or qualification.

The fixes can remain within the proposed scope. **Advance to a plan for the bounded timescale experiment. If the promised deliverable remains “establish whether this particular measured history effect helps foraging,” revise that promise: this design cannot establish it.**