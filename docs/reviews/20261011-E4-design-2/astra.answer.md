**Verdict: revise.** I verified HEAD is `b43be86d173782547e67ba136e696c9bd4265501`, on `roadmap`. This review was read-only; I used no GPU and did not rerun the maze rollouts.

The required changes were **substantially, but not completely, taken**. Dropping the clamp, using one shared 32-slot connectome, pairing runs, retaining failed runs, removing the matched-cut requirement, crossing interventions with trails, and separating E4-D are correct. The reported leak figures match [gate-leak.json](D:/Claude/random/wormWars/docs/E4/gate-leak.json), and its script measures the stated comparator-output differences.

**The output gate, ungated comparators and frozen selector are sound choices**, subject to the proposed equivalence checks and E-G requalification. The leak’s small average magnitude does not establish isolation; the output gate addresses that directly. Freezing the selector is appropriate for this experiment’s narrower question.

Two implementation details need explicit treatment in the pre-registration: the current brain starts Q at zero, so `q > 0` does not initially select A without a specified initialization or startup convention; and existing `T.assert_frozen` checks T-F’s original mask, so it will need the E4-specific frozen mask. See [brain initialization](D:/Claude/random/wormWars/wormwars/brain.py:402) and [assert_frozen](D:/Claude/random/wormWars/wormwars/e3/tuning.py:59).

My remaining required revisions are limited to issues that could produce a wrong or uninterpretable result:

1. **Mean substitution is a useful primary intervention, but its interpretation is overstated.**

   [§2](D:/Claude/random/wormWars/docs/E4/E4-DESIGN.md:90) says intact minus mean-substituted “isolates the informational part.” It does not. Removing time-varying recurrent currents also changes feedback, variability, synchronization and attractor dynamics. A useful autonomous oscillation could fail this intervention without conveying information about the task’s sensory state. Mean-substituted minus cut likewise measures the effect of that particular constant replacement, not a uniquely identified tonic component of intact behaviour.

   Keep the intervention, but describe its direct conclusion as **dependence on state-dependent cross-link currents beyond a validation-estimated constant replacement**. For the stronger claim about task-relevant information, add an appropriately controlled disruption of signal–task alignment, or narrow the claim.

   Also, a positive P1-info can occur when mean substitution is harmful but cutting is harmless or beneficial. The decision system must retain P1-cut’s direction and handle that case explicitly.

   Validation is an appropriate source for the means. Specify
   \[
   b'_j=b_j+\sum_{i\to j}w_{ij}\,\overline{\tanh(v_i)},
   \]
   measured from intact validation trajectories, with the averaging window, substep sampling, maze/wey weighting and trail-condition treatment fixed. Do not silently clip the replacement biases to evolutionary bounds. Include a constant-source check where substitution reproduces the original current.

2. **The joint table still turns insufficient evidence into absence, and weight magnitude cannot establish recruitment.**

   [The table](D:/Claude/random/wormWars/docs/E4/E4-DESIGN.md:120) needs separate states for positive, negative, practically equivalent, inconclusive and not evaluable. P1 currently has no specified equivalence rule. Consequently, “none / none / positive control works → no useful transfer evolved” is unsupported.

   Require an appropriate upper bound on a meaningful acute benefit, together with competence and assay validity, before making a bounded negative statement. Even then, say **no practically relevant benefit detected by the registered interventions**, rather than excluding every possible use of transfer.

   [Branch A](D:/Claude/random/wormWars/docs/E4/E4-DESIGN.md:100) is also wrong as a functional classification: useful combinations of small weights can remain inside a neutral-drift band, while large neutral weights can have no useful effect. Rename this observation “no detected departure from the neutral weight distribution.” It must not override a positive intervention effect or establish that search failed.

   Finally, failure of a separate E4-D task must not automatically erase valid positive P1 or P2 evidence. Distinguish failure of the diagnostic from demonstrated failure of the main assay.

3. **State the sign-flip null correctly and align inference with the claimed effect.**

   Exact enumeration is exact under the relevant sign symmetry or within-pair exchangeability null—not under an arbitrary zero-mean null. Pairing seeds does not establish that assumption. This distinction is also explicit in [SciPy’s paired-permutation documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html).

   A concrete counterexample: independent run differences of +1 with probability 0.9 and −9 with probability 0.1 have mean zero. With eight runs, all differences are positive with probability **0.4305**, and that sample receives two-sided sign-flip **p = 0.0078125**. Thus the test cannot support distribution-free mean-benefit claims under the skewed failures contemplated here.

   Specify the null and estimand, distinguish exact distributional inference from model-based mean and margin inference, and include zero-mean asymmetric cases in calibration. Merely simulating skewed alternatives is insufficient.

   The quoted **1.26-visit MDE** also uses two-sided α = 0.05. At the proposed α = 0.025, the same unpaired normal approximation gives **1.39 visits**, before small-sample adjustments. The R ≥ 7 arithmetic is correct; it establishes attainable significance, not adequate power.

4. **The scale rule is not yet a reproducible rule.**

   [§1](D:/Claude/random/wormWars/docs/E4/E4-DESIGN.md:78) says to choose the smallest factor at which a neutral random walk reaches |w| ≥ 1 within G generations. A stochastic walk needs a specified probability or quantile. Any positive Gaussian scale has some crossing probability.

   Define the candidate factors, whether the criterion concerns one slot or any of 32, the crossing probability, and the neutral lineage process—including mutation opportunities and clipping. Resolve G and scale jointly before the formal run.

   Generation-1 asymmetry is useful evidence, but neither bounds later mutation load nor supplies an acceptance threshold by itself. Specify that threshold or remove the implied guarantee.

5. **E4-D’s ordering is correct; the swapped-noses necessity claim is not.**

   Running the CPU feasibility check before the main formal run is appropriate. I prefer the randomized B-mode choice in [§7](D:/Claude/random/wormWars/docs/E4/E4-DESIGN.md:201), with timely completion required and cue reversal/shuffling plus cross-link removal as controls.

   “X0 cannot navigate” does not follow from swapping noses. The active module still has the other source’s scent, wall sensing, movement history and potentially trails; those can support indirect strategies. E3f explicitly [does not establish that all blind strategies fail](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3f/RESULTS.md:159). Nor would an X+ success establish that only nose-origin links carried the relevant signal: comparator-origin links can transmit processed scent information.

   Drop that necessity claim unless demonstrated under a controlled task. A hand-configured success establishes architectural feasibility, not evolutionary discoverability, and cannot by itself make an imprecise main-task null informative.

6. **Whole-rollout leg durations do not establish direct mode-specific dependence.**

   [§4](D:/Claude/random/wormWars/docs/E4/E4-DESIGN.md:139) has an unresolved ambiguity. If X0 receives cross-link bundle cuts, those weights are already zero: this is a sham/equivalence check, not a measurement of leakage. If X0 instead receives neuron deletions, earlier movement, trails and residual motor states can change later-mode behaviour despite perfectly gated output edges.

   Switching from leg counts to durations does not remove those paths, and completed-leg durations introduce selection when interventions prevent completion. Either use matched saved states for direct mode-specific attribution, or retain whole-rollout interventions and explicitly limit them to total episode effects, with failed and censored legs handled in advance.

   Similarly, a larger cut cost without trails is **consistent with substitution**; the interaction alone does not uniquely establish that mechanism.

These revisions concern the claims and decision rules. The proposed gated organism and the choice to make acute dependence primary can remain.