**Verdict: revise, text only.** All eight v2 must-fixes are resolved. v3 introduced two small contradictions in C0 that the runner's tests would pin, so they need settling first. If both are taken as written below, I need no further round. I read files and recomputed by hand; I ran no code, tests or git.

## Must-fix

1. **C0 against "Seeds": the seed mapping contradicts itself.**
   - Part C0 seeds the children per champion (1 131 000 + 10 × champion), so that every scale gets the same noise.
   - "Seeds" says 1 131 000 + 10 × champion + scale index, which gives different noise at each scale.
   - Keep the per-champion seed and drop "+ scale index". `Genome.mutate` draws `randn × sigma` with `p_mutate = 1.0`, so reseeding per scale gives the same directions.

2. **C0, measures: the bins are not defined once the reference is per draw.**
   - The reference is now the other 248 worlds, which change with each of the 400 draws. A pair's bin, and the pair count behind the 30-pair minimum, then vary by draw.
   - Bin each pair once, by its 256-world difference. Score each draw against its 248-world complement.
   - Say what a sibling draw counts as when the complement's difference is 0 or reversed. In the 0.05-0.15 bin this can happen.
   - For the ES's pairs, say that the zero-difference exclusion is per draw.

## Suggestions

- **Budget reading:** say plainly that the new rule already fires on E2's hold-out (mean 0.25 over 8 runs, none negative). With about 0.01 of world-sampling error on that mean, "budget-limited" is the expected result.
- **The controls' replay:**
  - E2 trained in default CUDA mode; `scripts/e2.py` never enters `replay_mode`. State that the replay and the arms run in that same mode.
  - `docs/REPRODUCIBILITY.md` does not guarantee default-mode determinism, so a generation-25 mismatch is ambiguous. Add a second replay: if the two replays disagree with each other, it is nondeterminism; if they agree but differ from E2, it is drift.
- **Pairing check for C1 and C4:** E2 recorded training ids for generation 0 only. At generation 249, "equal E2's" means equal to `train_ids` regenerated at 8 worlds; say so.
- **Incomplete arms:** C4's contrasts need C1 and C2. Say that a contrast with an incomplete arm is not drawn.
- **Which test governs:** "supports" uses the bootstrap interval, and the sign-flip test sits beside it. Say which decides when they disagree.
- **Run 2:** say whether the two-way rule also covers "harmful", the C4 contrasts and the interaction.
- **C0 pooling:** about 16 000 sibling pairs come from 8 parents, so 30 pairs is a weak guard. Report per-champion rates, and use the same 400 draws for every measure.
- **Plateau band:** pin 1.90-2.50 as fixed numbers, not as the re-measured M-avg ± 0.3.
- **Nits:**
  - The budget's parts sum to 5.95 hours, not 5.9.
  - "The last differs by 768 episodes" holds only if work is counted before the checkpointed generation; counted through it, the first ten differ and the last is equal.
  - "Changes from v1" still says "no unpaired seed luck".

## Checked and found correct

| v2 must-fix | Status |
|---|---|
| Run 2 | resolved; applied to every arm |
| The controls' replay | resolved; E2's generation-0 and generation-25 hashes are committed |
| Part B's reading | resolved; "non-stereo" and "stereo use present" cannot both hold, for sets of 4, 8 or 12 |
| The budget reading | resolved |
| The C4 contrasts | resolved; all at 11 matched checkpoints |
| The reserve for reruns | resolved; admission and the 6.5-hour stop are consistent with the cap |
| C0's parents and minimum | resolved |
| Part A's cells | resolved; all 27 match `part-a.json` |

- **Budget figures:** the seven differences, and the means 0.28 and 0.25, follow from `part-a.json`. Run 2's is 0.0449, so the plan's 0.04 is right and my v2 figure of 0.05 was wrong.
- **Episodes and checkpoints:** 258 816, 266 496, 166 144 and 100 608 per run, the pilot's 802 560, and 11, 41, 26 and 42 checkpoints.
- **Time estimates:** these match E2's ledger. The GA took 4 863 s (1.35 h) and the formal ES 3 084 s (0.86 h). C0 is 665 600 episodes, about 0.42 h, and the replay about 4.4 minutes.
- **C3's pairing check works:** the ES's generation-0 checkpoint is the start genome, which does not depend on σ (`wormwars/e2/loops.py:180`).
- **Part B's references:**
  - The k = 4 reference is speed 1.0, turn 0.1, mean 2.18 (04a's `evaluation.json`, `gain_curve`).
  - Under `mean`, S-const becomes constant motion, and blind baselines score 0.44 or less, so its check should pass with room.
  - M-avg reads `(left + right) / 2`, so `swapped` should leave it identical.
- **Probes:** `mean` and `swapped` act on Task N's readings; the task sets stereo sensing (`wormwars/world.py:693`, `wormwars/e1/task.py:35`).
- **Ids and seeds:** 991-993 million is free of every earlier range (`tests/test_e2_commands.py:335`), and no code uses the 1 131 000-1 139 999 seeds.

## Not checked

- Whether the local genome files still match their hashes.
- Whether (65, 256, 1), at 16 640 worlds per rollout, fits in memory; the projection will show.
- The Part A script and tests were read, not run.