**revise**

Most v1 blockers are addressed, but v2 is not ready unchanged. The remaining issues concern the outcome definitions, shifter validation, budget, and reporting.

Must-fix items:

1. **Registered outcomes, O1 — the decisions overlap.** The interval concerns the **mean** paired difference, while support also uses the **median**. For example, nine differences of +0.6 and seven of −0.1 give median +0.6 and an exact percentile-bootstrap 90% interval for the mean of approximately **[0.163, 0.425]**. Both “supports” and “does not support” fire. Use one estimand and mutually exclusive decision rules; state whether the sign-flip test affects the decision.

2. **Generation-0 measurement and O2 — “eroded” still overstates the evidence.** No benefit from the module’s nose difference can mean redundancy, failure to integrate, or lost function. The descriptive transplant and lesion probes do not repair an unconditional “eroded” headline. Classify endpoint dependence neutrally, then distinguish retention, acquisition and loss using **each run’s** generation-0 classification. Replace the ambiguous “median run’s generation-0 best” trigger with an explicit rule. A graft that never worked cannot subsequently have eroded. Also specify that “kept” means retaining the stereo criterion, not retaining Stage A’s performance.

3. **M2 / A0 — specify and validate the shifter’s actual computation.** The index direction is correct for a positive-left angular coordinate. But `P⁺ receives E + TC_L` does not automatically implement velocity-gated transport: this engine emits **signed tanh activity**, and opposite additive inputs can change saturation and bump shape rather than produce the intended rotation. Pin all relay/shifter weights, biases and time constants, and test zero-turn stability, both directions, clipping and imposed background turns. High gain is plausible within the bounds through recurrence and mutual inhibition; successful shifting is presently unestablished, not demonstrably impossible.

   The **one-column-per-45° calibration also remains unjustified for the encoded quantity**. Normalised lateral contrast does not rotate like bearing. Mechanical rotation calibration alone does not resolve Astra v1 item 2. Add fixed-source cue-off/reacquisition checks across distances and bearings, or explicitly restrict the claim to a heuristic rotating memory whose usefulness is tested behaviorally.

4. **Stage A tuning / Budget — correct the search size and projection.** With 20 qualifying rings, A1 contains **20 × 3⁷ = 43,740 candidates**. Initial evaluation plus 5% rescoring requires **6,718,464 episodes**. Applying the document’s E2 extrapolation gives roughly **5.2 hours for that A1 work alone**, rather than one hour for all Stage A. Actual throughput may differ, but the current estimate is unsupported. Specify A0’s nose/readout settings before those parameters are tuned in A1, the exact M0 grid, and stage caps.

   Correct the counts too: **M2 adds 32 neurons, giving 334 total; M1 without 16 shifters and two relays adds 14, not 30.** The corresponding dense-work factor is about **1.223**. Thirty hours may still suffice; approximately sixteen hours needs revision.

5. **Gain-probe results / D141 — correct the reversal claim.** The three weak-response cases are:
   
   - `e2 ga run03` at 0.02;
   - `e2 random run06` at 0.08;
   - `04a run03` at 0.25.

   They are **three different genomes**, not one genome at three levels. “Not a latch” is also unsupported: for the latter two, the carried-state negative response differs from the zero-start negative response by approximately **0.0068 and −0.0065**, respectively. That establishes a history effect over the measured horizon, without establishing its mechanism. Add dated corrections and narrow the interpretation.

   Astra’s earlier requests for collision-context probes, individual motor traces and recorded accounting also remain unfulfilled. The script saves aggregate responses and saturation shares, and has no accounting wrapper. The change map should not claim complete adoption.

6. **Engine checks / hygiene — never commit the anatomical sabotage fixture.** The proposed “committed test fixture with an embedded anatomical block” contradicts rule 1. Commit a fixture **generator** and construct the offending artifact locally during testing. When extracting the worm block from an extended genome, use edge identities: turn-copy edges interleave with native chemical edges.

Suggestions and remaining pre-registration pins:

- Define A0’s settling horizon, circular peak/contrast calculation, tie handling, ranking across input levels and perturbation checks. A perfectly symmetric zero-state test is weak evidence against spontaneous bumps.
- Pin G1’s confidence-bound convention, bootstrap settings, candidate-selection rules for F and generation 0, incomplete-pair handling, and run scheduling under the cap.
- Define robustness mutations precisely: keep the carrier fixed if testing module robustness; specify worlds and seeds. Apply any 0.125× fallback consistently to matched arms, while preserving B5’s 1× and B6’s zero scales.
- Pair B6 with B1’s corresponding eight runs. Pin world ranges, batch compositions, reference commits, probe timing and all remaining module parameters.
- Twelve of sixteen gives the stated **one-sided p = 0.038406** against 50%. If both directional aggregate outcomes are presented as significance claims, address that explicitly.

What I checked and found correct:

- **Carrier:** AVB/PVC bias gives the stated steady-state forward command. Symmetric dorsal/ventral biases give `clamp(2 tanh(b_t))` without module drive. Turn-neuron τ = 1 is a valid declared carrier choice, though it retains filtering.
- **Architecture and gates:** removing M2’s direct bypass, requiring component checks, dropping the static-gain gate, and separately gating M0 address the central v1 gate objections. These establish component competence, not that memory improves navigation.
- **Evolution controls:** N2-first initialization and embedding, permanently pinned B3 outputs, explicit bridge ownership, F versus C, fixed-generation measurements, and descriptive B4–B6 are appropriate. B3’s hitchhiking caveat is correct.
- **Engine plan:** default/ones-scale bit identity, pinning sabotage checks, E2 hash reproduction and declared inert-graft tolerances are appropriate planned checks. E2’s committed generation-0–25 hashes exist; their recorded runtime totals approximately **129 seconds**.
- **Probe numbers:** recomputation gives median absolute gain **0.0977963**, maximum **0.681214**; the recorded script hash matches.

By v1 item: Fable **1, 3, 5–10 and 12** are addressed at design level; **2, 4 and 11** need the qualifications above. Astra **1, 3 and 6** are substantially addressed; **2, 4, 5 and 7** remain partial. Astra **8** is substantially covered by planned implementation checks, not completed validation.

I checked the design at `68812ac`, both archived reviews, graft code/tests, engine/interface code and committed records. Concurrent engine edits were excluded. No files were modified and no E4s experiments were run.