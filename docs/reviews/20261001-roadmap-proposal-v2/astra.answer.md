**Verdict: adopt with changes.** I checked `fdddee4` on `roadmap`, both v1 reviews, the relevant code and committed results. Nothing was modified; no experiments were run.

At roadmap level, **Astra 1–4, 6–7 and Fable 1–5, 8–10 are resolved**, subject to the implementation details below. **Astra 5/Fable 7 remain unresolved; Fable 6 is only partly resolved.**

1. **The outcome table is exclusive but misclassifies acquisition.** [Row 2](/D:/Claude/random/wormWars/docs/E4s/ROADMAP-PROPOSAL.md:211) labels every run without G0 dependence “never used,” including one that becomes dependent at F. Restore an **acquired** branch; reserve “never used” for neither endpoint meeting the criterion. Preserve the explicit unclear handling.

   Also, H at F alone establishes host competence, **not acquisition**: acquisition requires comparison with H at G0. And the statement that N’s and R’s outputs never reached the motors is false—**R remains connected**. M versus N can support graft-assisted host acquisition; M versus R tests the contribution of designed initialization. Neither alone demonstrates transfer of a particular computation.

2. **The comparator arithmetic checks out, with qualifications.** From `brain.py` and [`_read_motors`](/D:/Claude/random/wormWars/wormwars/world.py:742), the zero-bias L1 carrier has small-signal, steady-state gain
   \[
   K_D=4w_ow_n\,\mathrm{sech}^2(m).
   \]
   Thus 36 is correct near zero common input; at \(m=0.35\), it is approximately 31.93. Comparator and motor biases add attenuation, and dynamics introduce delay. This assumes outputs reach **all eight named turn neurons**. The cited E1 scores check out, but they do not predict the graft’s closed-loop score.

   The ladder is reasonable. However, mutual inhibition of −2 or −3 can create **bistability and hysteresis**, not simply increased gain with slower response. Keep the controlled reversal measurements and describe these candidates accordingly.

3. **The residual classes need narrower wording.** [“No benefit”](/D:/Claude/random/wormWars/docs/E4s/ROADMAP-PROPOSAL.md:95) means only **“no detected benefit on the tested grid.”** Broad intervals satisfy it. Define “dips first” only when an improving k exists; otherwise its reference point is undefined. The counts and selected best k are exploratory results from scanning multiple pointwise intervals.

   The sensory-gain assertion also remains wrong: the probe injects \(m+d/2\) and \(m-d/2\). Individual injected-current derivatives are **+½ and −½**; their difference has derivative 1. Sensory-neuron voltage or activity gain is not fixed by construction in a recurrent brain.

4. **M, N and R now answer identifiable questions.** The comparisons, parameter ownership and permanently pinned N cut resolve the earlier arm objections. Pin R’s exact randomization: per-edge preserved magnitudes versus resampling, which weights are randomized, treatment of τ/bias, and whether draws vary across individuals or runs.

5. **E3’s fallback contradiction is resolved.** One selection detail remains: [“chosen by validation mean”](/D:/Claude/random/wormWars/docs/E4s/ROADMAP-PROPOSAL.md:254) must mean **among individually retained F genomes**. A 12-of-16 majority does not make the highest-scoring remaining genome retained. Replacement should also require passing E3’s own positive control.

Before execution, E4s-0’s script should pin exact L1–L5 adjacency and neuron counts, whether L3 retains L2 self-excitation, L5’s relay wiring, command-to-bias conversion, candidate ranking and ties, gate reuse/stopping rules, response horizons, world ranges and cap handling. Verify that the residual is inserted **before** clamping and that k=0 reproduces the original policy. Restore the robustness measurement needed by the inherited mutation-scale fallback. The pending GPU and equivalence gates are correctly preserved.