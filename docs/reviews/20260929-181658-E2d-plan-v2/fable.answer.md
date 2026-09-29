**Verdict: revise.** The changes are small and none is structural. The pairing is sound, and reusing E2's training and validation worlds confounds nothing. Two other things do: the GA's run 2, and controls that are never replayed. I could not run code or git; everything below is from reading files and recomputing by hand.

## Must-fix

1. **Part C, readings: run 2 can carry a GA arm's reading by itself.** E2's GA run 2 scored 0.75, and all 32 of its generation-0 genomes scored 0 on its 8 worlds (E2 `RESULTS.md`, corrections).
   - If an arm's run 2 reaches 2.1, that one pair adds 0.17 to the mean. "Supports" then needs only +0.15 from the other seven.
   - In C1 and C4, 32 worlds change that zero start. That is a start effect, which E3 (starting from a module) does not have.
   - State each GA arm's reading over all 8 runs and over the 7 without run 2. Draw "supports" only if both hold; otherwise label it "supports, carried by run 2".

2. **Part C, pairing and guards: the controls are never replayed.** "No control arm" holds only if today's code and environment reproduce E2's runs.
   - Before C1, replay E2's GA and ES for generations 0-25 with E2's seeds, ids and composition, and require the generation-0 and generation-25 hashes to match the committed ones (about 5 GPU-minutes).
   - Record a pairing check per arm: for C2 and C3, the generation-0 candidate's hash; for C1 and C4, the first 8 training ids.

3. **Part B, the reading has gaps.**
   - "Non-stereo plateau" counts only "uses", so eight "unclear" champions would read as non-stereo. Require most to be "no detectable use".
   - "Most champions" does not say whether it is pooled or per set. Random sampling's eight are 1.36-1.87, none in the 1.90-2.50 band. Name the sets the reading covers.
   - Name the third outcome, when neither reading applies.

4. **Part B, the budget reading is already decided by committed data.** On E2's hold-out the seven distinct pairs differ by 0.38, 0.11, 0.05, 0.69, 0.24, 0.08 and 0.42.
   - Four of 7 reach 0.2, and the other three are far below it, so "6 of 7" will not fire. Yet the mean gain is 0.28 and all seven are positive.
   - Disclose these figures, and use Part C's form (mean paired gain with an interval) beside the count.
   - Say that the extension's champion is chosen over 42 checkpoints that include the formal one.
   - The episode figures are totals over 8 runs with the pilot; per run they are 166 144 and 100 608 more.

5. **Decision guidance, "only together".** "C4 supports, C1 and C2 do not" does not show an interaction; C1 at +0.25 and C4 at +0.35 would produce it.
   - Add the paired contrasts C4 − C1 and C4 − C2. C4 − C1 is the cleanest in the plan: only mutation differs.
   - Claim an interaction only from those contrasts.

6. **Guards: reruns bypass the reserve.** E2's admission test skips reruns (`scripts/e2.py:905`). Two late crashes could reach the cap before the hold-out pass, and then no arm has a result. Apply the reserve to reruns too, and say what the pass does when arms are missing.

7. **Part C0: the parents are not evaluated.** "Under half the parent's" needs each parent's score on the 256 probe worlds. Add the GA champions and ES means to the batch, and set a minimum pair count below which the reading is not drawn.

8. **Part A: three table cells differ from `part-a.json`.**

   | Cell | Plan | `part-a.json` |
   |---|---|---|
   | Gap 0.05-0.15, k = 32, tied | 0.07 | 0.06 (0.0648) |
   | Gap 0.05-0.15, k = 128, correct | 0.87 | 0.86 (0.8648) |
   | Gap 0.30-0.60, k = 32, tied | 0.01 | 0.00 (0.0049) |

   The Budget bullet's 2.02 and 2.31 are not produced by the script. Cite E2's `RESULTS.md` §5 or add them.

## Suggestions

- **Pairing wording:** "no unpaired seed luck" overclaims. Trajectories diverge within a generation or two, and E2's ES − GA differences show little shared seed effect apart from run 2. Report the arm-reference correlation across runs.
- **The 32-world prefix:** it follows from numpy drawing in sequence, which is not an API guarantee. Pin it in a test.
- **Matched checkpoints:** the fractions are about equal, not equal; they differ by 768 episodes.
- **Part B classes:** "no detectable use" is one-sided, so a champion that gains under `swapped` would land there. Make it two-sided.
- **The k = 4 reference:** name its speed and turn. E1's freeze holds the grid of means, not a frozen k = 4 winner.
- **C0 analysis:**
  - Take the reference from the 248 worlds not resampled, and sample without replacement.
  - Use the same noise across scales.
  - Say that pair signs are a proxy for the ES's rank-based update.
- **Intervals:** a percentile bootstrap over 8 runs is too narrow. Add a sign-flip test.
- **Budget table:** the parts sum to about 5.8 hours, not 5.7.
- **Part A wording:** say the resampling is with replacement. ES run 0 is within 0.25 of M-avg by 0.001.

## Checked and found correct

- **Pairing in code:** the start population, the training schedule, the breeding stream and the ES's noise all depend on the run seed only (`wormwars/e04a/evolve.py:63-80`, `wormwars/e2/loops.py:135`).
- **Reused worlds:** arm and reference are chosen on the same validation worlds and scored on a fresh hold-out. I see no leak.
- **v1 must-fixes:**

  | v1 item | Status |
  |---|---|
  | C3 changes only σ (0.15 is the pilot's rate; Adam normalises the gradient's scale) | resolved |
  | C1's matched checkpoints | resolved |
  | `swapped` for Part C's champions | resolved |
  | "Not the bottleneck" removed; harmful and inconclusive outcomes defined | resolved |
  | Part B's classes and reading | partly (item 3) |
  | The budget reading | partly (item 4) |

- **Arithmetic:**
  - 258 816, 266 496 and 166 144 episodes per run; 11, 41 and 26 checkpoints.
  - 2 131 712 and 804 864 total episodes.
  - C0 is 655 360 episodes, about 0.43 hours at E2's GA rate.
- **Part A:** every other figure matches `part-a.json`. The pair counts 74, 113 and 106 follow from v1's counts, which I recomputed then, less extension run 6's pairs (6, 9 and 4).
- **Probes:** `mean` and `swapped` are as described (`wormwars/world.py:693`).
- **Ids and seeds:** the 991-992 million block and the C0, smoke and projection seeds are unused in the code I searched.
- **Genome files:** E2's candidate files and 04a's 16 modules exist locally.

## Not checked

- Whether `wormwars/` changed since `69f4163`.
- M-avg's controller code, for the `swapped` identity.
- The script and tests were read, not run.