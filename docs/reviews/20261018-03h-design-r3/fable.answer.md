**Verdict: ready for code and the pilot's registration, with small fixes.** Nothing left needs a redesign. Three items should be fixed in the text before the pilot's registration is bound: B's one-sided direction is not stated, step 0's "committed seeds" are not committed and need a verification replay, and the pilot's rules are not yet numeric.

## Round-2 findings, per reviewer

**Fable, round 2**

| # | Finding | Status |
|---|---|---|
| 1 | Throughput was Task N's | Resolved. 171/s checks: 11 264 / 65.9 s. `timing.json` corroborates at 166 to 169/s for 4 096 to 16 384-world chunks. |
| 2 | Relief gate was an identity | Resolved in design: KTS port with T in {1, 2, 5, 10, 20}, `GradedKinesis` in the union. KTS(T=1) does reduce to one-tick memory (`wormwars/e03a/probe.py:113-116`), provided the port keeps `fall_threshold`. |
| 3 | Units | Resolved. Score defined (§2), criteria restated in it (§4). |
| 4 | B's baseline | Resolved. |
| 5 | Circular order | Resolved (§7 steps 3 to 5). Estimator specified; two small gaps, finding 7 below. |
| 6 | Bit's reading | Resolved. After the clamp, which is what `ScriptedBrain` reads (`scripted.py:43`). |
| 7 | Cut order | Resolved. |
| 8 | Rule 7 check | Resolved. |
| 9 | Bank provenance | Resolved. |
| 10 | Use the T1 distribution | Resolved, but the derived numbers are not in a committed file, finding 4. |
| 11 | `ScriptedBrain` extension | Resolved. |
| 12 | Bit's magnitude | Resolved as a registered value with a reason. Still untested in a random brain, finding 3. |
| 13 | Composition and padding | Resolved. |
| 14 | Registration leftovers | Partly. Aggregation, degenerate graphs, effect margin, ASK cap value and calibration genomes are fixed. World-id ranges are not listed anywhere; acceptable if §7.7 names them as pending. |

**Astra, round 2**

| # | Finding | Status |
|---|---|---|
| 2 | Outcome and unit | Resolved. Score, swarm as the evaluation unit, per-wey bit, worlds as the resampling unit. |
| 3 | Bank provenance, frozen probe parameters | Resolved. Matches `measures.py:92-93` defaults. |
| 4 | Gate validity | Resolved. Zero-threshold claim narrowed, graded policies in the union, longer memory added, bit after the clamp. |
| 5 | Order and sham overstatement | Resolved. Initial state, estimator, dead weys, realised occupancy and the narrower claim are all in §3. |
| 6 | A's conclusion wording | Resolved, including "meaningful" and "no improvement was detected". |
| 7 | Statistical contract | Resolved except world-id ranges and the seed-disjointness statement, which covers graphs only. |
| 8 | Six hours as a ceiling | Resolved. |

## Checks of the new parts

- **pilot.json.** The T1-M0 block holds 256 rows of 16 (lines 126 to 4736), for 16 pilot graphs. No value in the file is a literal zero. The fitness seconds are 64.5 to 67.5 per graph, calibration 7.4 to 12.4. Rate and budget arithmetic all reproduce: 17 280 episodes per graph, 1.82 h for 65 graphs, 0.21 h calibration.
- **The reliability.** From the stated SDs, 0.26² minus 0.25²/16 over 0.26² gives 0.94 at 16 worlds and 0.89 at 8. The SDs themselves I could not recompute without running code. The rows I sampled are consistent with them.
- **Step 0's regeneration.** The pilot was rerun after D053's seed fix, so the committed file was produced with the current `genome_seed` (whole-name hash, empty salt for the 03 instance). The genomes come from a CUDA generator seeded by the graph name (`scripts/exp03.py:448-449`), and the pilot graphs are rebuilt by the untouched SH sampler. So regeneration is possible on CUDA. But pilot.json carries no provenance and no genome hashes, and the engine has changed since (T0, T1). See finding 2.

## Findings

1. **§1, §6 B, medium. B's one-sided direction is not written.** U_g = T_sham − T_relief, and 03's formula counts references either at-or-above or at-or-below N2 (`wormwars/exp03/mc.py:19-30`). Under the hypothesis, the nulls gain more from the relief than N2 does, so U_N2 should rank high: r counts nulls with U at or above N2's. §1's "does N2's upper tail lose more to the relief" reads as the opposite, since nothing loses score under relief. Rewrite as "does N2's advantage shrink more under the relief than the nulls' expected gain", and state the counting direction in §6.

2. **§7.2, medium. Step 0's "committed seeds" are derived, and the regeneration needs a check.** The seeds are not in pilot.json. They are `genome_seed("pilotSH1xx", "")` on CUDA with 03's brain config. Register step 0 as: rebuild the graph, regenerate the 256 genomes, replay T1-M0 for at least one pilot graph on the current engine, compare with pilot.json at T1's declared equivalence tolerance, and only then relate H and S to the committed fitness. If the replay fails, step 0 is dropped; it is exploratory. This costs about one minute of GPU and is the only possible provenance for a file with none.

3. **§3, §7.6, medium. The pilot has no reading of the manipulation itself.** The amplitude 0.25 is a reasoned guess, and if the bit does not reach the motors in random brains then A2, B and the check are all uninformative nulls. The pilot's registration should include the decile shift relief against sham on the pilot graphs, and ideally the bit's input response at the turn read-out, with a pre-stated consequence (proceed with the amplitude, or raise it by a registered rule, or stop). This is for the pilot's registration, not the code.

4. **§2, low, rule 5. The derived numbers have no committed source.** The mean range, the two SDs and the reliabilities appear only in the design. Add them to step 0's output or a small committed script. Also define the reliability estimator: the per-world SD of 0.25 is mostly a world main effect shared by every genome (world 2 is high and world 6 low in every row I looked at), so the ranking reliability is above 0.94. The crossed decomposition already in `exp03.py:580-595` is the right tool, and §7.6's "reliability falls below 0.85" rule needs to say which estimator it uses.

5. **§7.6, low. "Undetectable at 64 graphs" is not numeric.** Fix it as a rule, for example: stop if the pilot's SD of graph-level D over 8 exceeds some fraction of δ_A, or if the power at D = 2δ_A falls below 0.8.

6. **§7, low. The pilot's registration has no step.** Insert it before step 2, covering steps 2 to 6, since step 0 and the gate are GPU work and carry decisions.

7. **§3, low. Two sham-estimator details.** Say that transitions are counted only between consecutive ticks on which the wey is alive on both, and whether the keyed stream includes the strain. Keying by world and wey only gives every genome and graph the same sham sequence, which is fine and reduces variance for the paired contrasts, but it must be stated.

8. **§4, low.** The sham sanity criterion says "within ±0.3" without saying point estimate or interval. Match the relief criterion's 90% interval. Also report the recovered share, (memoryless with bit − memoryless) / (memory − memoryless), which is the quantity "relief" implies and which neither criterion measures.

9. **§4, low.** If the relief part fails because slow memory beats the bit by more than 0.3, the natural response is a bit defined against the tuned average, not abandoning 03h. Say "stops for redesign", as §7.6 does.

10. **§6 B, low.** "The expected best of 32 by order statistics" is unexplained in the text. One clause: it is 01b's and 02's head-start statistic, Fable's round-1 secondary.

11. **§9, low.** "N2 must exceed nearly every null graph" is loose. For B to pass Holm's first threshold alone, N2 must rank first of 65 (2/65 = 0.031 fails 0.025). After A passes, up to two nulls may sit above N2 (3/65 = 0.046).

12. **§8, low.** Two cost notes. The 171/s predates the T1 throughput work, so the budget is probably conservative; the pilot will show. The SH-mirror-ASK sampler and the 10 000-resample crossed bootstrap with repeated selection are CPU costs and are not mentioned; the bootstrap can be hours if written naively.

## What blocks

Nothing blocks writing the code. Before the pilot's registration is bound: findings 1, 2 and 3 should be in the text, and 5 and 6 make the registration itself well-formed. The rest can be folded into the formal pre-registration.