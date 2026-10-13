**Keep the 32 independent cross-links. Reduce only module-bias mutation, using a declared calibration rule; retain inherited weight and τ factors at 0.25. Do not freeze biases or impose mirror tying yet. Run one bounded follow-up pilot before fixing formal training.**

1. **Reading 1 is substantially supported; its wording is too absolute.** The [diagnostics](D:/Claude/random/wormWars/experiments/E4-two-minds/diagnostics.json) identify biases as the dominant generation-1 load at this setting. They do not establish “biases alone” across training, or exclude interactions. Likewise, zero-scale breeding excludes a mutation-independent breeding defect, not every possible defect.

   The [comparator equations](D:/Claude/random/wormWars/wormwars/e4s/comparator.py:36) support the proposed mechanism: unequal nose biases shift the sensory difference; unequal comparator biases introduce steering asymmetry. Equal offsets can instead change gain through saturation. The effect does not require the hard gate or the 6 × 6 arena; its magnitude can still depend on both.

   A cheap CPU check: sweep equal and opposite versus equal left/right bias perturbations, separately on noses and comparators, under fixed scent inputs. Measure the steering zero-crossing and gain.

2. **Reading 2 is a hypothesis, not a consequence of reading 1.** The identity is exact:
   \[
   w\tanh(v_i(t))=wm_i+w[\tanh(v_i(t))-m_i],
   \qquad m_i=\operatorname{mean}\tanh(v_i).
   \]
   But neither tonic dominance nor “evolution can only recruit cancelling combinations” follows. Small offsets may be tolerable or useful; inherited weights and biases can compensate; changing currents and feedback can also cause the cost. D250 measures cross-links added to already heavily mutated modules.

   **Direct check:** on identical inherited genotypes, compare four conditions for random cross-links:

   - links cut;
   - intact;
   - cut plus target-bias offsets \(c_j=\sum_iw_{ij}m_i\);
   - intact minus those same target-bias offsets.

   Estimate means on a calibration block; evaluate on separate paired mazes. Use 16–32 children at factors 0.25 and 1.0, initially with inherited parameters fixed. Existing [mean substitution](D:/Claude/random/wormWars/wormwars/e4/arms.py:104) supplies the third condition. Tonic-only reproducing the loss **and** centering rescuing it would support the mechanism. Report nose-origin and comparator-origin currents separately. This is an intervention diagnostic, not an additive causal decomposition.

3. **Endorse (a), with nonzero biases; endorse (b), with a conservative bound.** My proposed calibration:

   - Keep `p_mutate=1`, inherited weights and τ at **0.25**.
   - Screen bias factors **0.005, 0.01, 0.02, 0.05**, plus zero as a diagnostic reference. Factors 0.01–0.02 mean actual bias σ **0.0005–0.001**.
   - On **16 fresh mazes × four paired mutation seeds**, choose the largest factor whose children retain **≥95% of unmutated E-G’s mean**. Evaluate the combined mutation mask, not biases alone.
   - Check the selected setting once on another fresh 16-maze block; report paired uncertainty. If it fails, reconsider explicitly rather than repeatedly searching blocks.

   For cross-links, require children’s mean loss versus the newly calibrated X0 children to be **≤min(0.25 visits, 5% of X0’s mean)**. These are proposed engineering tolerances, not data-derived truths. I would not grant 20–25% additional damage merely to admit larger factors. Reapply the existing reach rule to passing candidates; report reach deficiency without equating small weights with absent functional recruitment.

4. **Mirror tying changes the search space materially, and the cancellation claim is wrong as stated.** Equal weights on A_NL→B_CL and A_NR→B_CR give differential tonic drive \(w(m_{NL}-m_{NR})\), which need not vanish. Even equal common drive can change comparator gain; inherited mutations also break symmetry.

   Retaining all slots with correlated mutations is therefore an engineered symmetry constraint, not merely an implementation detail. Treat it as a separately named alternative requiring the owner’s scientific choice.

   Freezing **only biases** also restricts coadaptation, but it does **not** freeze the modules: weights and τ remain evolvable, and P2 does not collapse into P1-cut. Prefer smaller nonzero steps because they preserve compensation routes.

5. **Next pilot: at most 2.5 additional GPU-hours, including calibration and assays.** After calibration, run **four paired runs per arm, P=32, W=8, G=50**. Training projects to **1.56 hours** at the observed throughput. Save populations, RNG states, selection records and validation scores every ten generations.

   Measure offspring retention, candidate performance against E-G on common mazes, competence, and intact/cut/mean-substitution effects. Flat X0 performance alone is not a stopping criterion.

   Taking **3.7 hours spent**, this leaves **23.8 hours**. Eight runs per arm × 300 generations project to **18.7 training hours**, leaving about **5.1 hours** for formal evaluation and contingencies. Verify that allocation with measured assay costs.

   **Owner decision:** approve expanding the cumulative pilot allowance beyond 4.5 hours. Bias scaling is a pilot-informed optimizer amendment; mirror tying or freezing biases should be explicit scientific choices. Preserve the failed attempt, and commit and push the revised specification before formal work.