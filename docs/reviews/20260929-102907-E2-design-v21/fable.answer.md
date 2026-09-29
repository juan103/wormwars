# E2 design v2.1: confirmation

My v2 points are met and nothing new blocks the pre-registration, but five details need fixing in it, one of them the allowance figure. I read the design, both v2 reviews, D117, the roadmap, `optimizers.py`, its tests and `evolve_batch`. I ran nothing.

## My v2 points

| Point | Status |
|---|---|
| Run length and formula | **Met, with one ambiguity** (item 1). (2 048 000 − 768 000 − 3 840 − 2 048) / 8 = 159 264, which is 622.125 generations, so 622. 256 episodes go unused. |
| One charging rule; σ and rate constant | Met (`docs/E2/DESIGN.md:93`, `:129`). |
| "Keep the GA" wording | Met. |
| Decision rule | Met: only the ES can be chosen, the trigger is one-sided, an incomplete GA batch blocks the decision, and diagnosis takes precedence over E3. |
| Roadmap amendment | Met (`ROADMAP.md:167`), dated and added beside the original text. |
| GA test on the CPU, sabotage-checked | Declared. It is not written yet, because there is no E2 driver. |
| ES update | Met. The code matches the design: the estimator and its sign, Adam's constants and bias correction, joint average ranks (`wormwars/e2/optimizers.py:85-96`). |
| Flat batch after real updates | Met. The test would fail if the early return were removed. I cannot confirm the sabotage check was run. D117's "13 tests" is correct. |
| Schedule alignment | Met. At checkpoint g both methods have spent (g + 1) × 256 training episodes. The GA gets 41 checkpoints and the ES 26. |
| Extension arm | Present, excluded from the decision. Under-specified (item 3). |

## To fix in the pre-registration

1. **The pilot's start screens are not in the formula.** It charges the pilot's validations (15 × 256) and the formal starts (8 × 256). My v2 figure charged 23 starts and no validations, so the two agree at 622 by coincidence.
   - If a pilot run is a start screen plus 200 updates, 3 840 more episodes are owed and the answer is **620**.
   - If the start is generation 0 of the 200, 622 stands, but selection is then at generation 199, not 200.
2. **The allowance's definition contradicts its exclusion.** Checkpoint validations choose the champion, so they are "episodes whose scores drive selection", yet they are not charged. Define the allowance as training episodes plus the pilot's setting-selection validations. The exclusion costs the ES about 1.5% of work, which is conservative.
3. **The extension needs four things stated.**
   - It should end at generation 999, not 1 000, to match the GA's 0-999.
   - It resumes from the saved state at 622: mean, Adam's moments and counter, and the noise generator.
   - Say how it is scored. I recommend its champions join the single hold-out pass, with hashes committed beforehand.
   - Its training world ids need a range.
4. **The flat-batch rule holds in the class, not yet in the loop.**
   - `tell` does not project; the driver must. `project` round-trips through the genome's dtype, and its own test allows 1e-4.
   - If the driver projects after a flat generation, the mean changes. Project only after a real update, and repeat the flat-batch test on the loop.
   - A non-finite score passes through `utilities` to the mean, and `BestSinceCheckpoint` ignores it silently. The driver needs `evolve_batch`'s finiteness check.
5. **Three small gaps in the rules.**
   - Nothing says what happens if random sampling's batch is incomplete, so the floor check would be undefined.
   - The start screen has no tie rule. At 04a's 97% zero share, all 32 genomes tie at zero with probability about 0.38 (my arithmetic), and the ES then waits on the plateau. Report each run's start score and first non-flat generation.
   - If every pair ties within itself but the batch is not flat, the gradient is zero and Adam still moves on momentum. Say whether that is intended.

## Minor

- From E1's throughput curve, the pilot is nearer 0.5 GPU-hours than 0.4 (my estimate). The total still fits under a cap of 7.

## Not checked

- The ENOMAD summary: I have no access to the paper.

**E2 design: proceed to pre-registration**