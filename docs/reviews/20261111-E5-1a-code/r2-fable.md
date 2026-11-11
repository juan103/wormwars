**Verdict: fix first, but the list is small (four edits and one decision, about half an hour) and needs no third round.** The round-1 fixes are done correctly, and I found nothing that makes equivalence, graphs or cuda compute a wrong result. Fix now rather than later because `guard` calls `require_same_code` on `wormwars`, `scripts` and `configs`. Any code commit after equivalence starts blocks every later stage, and start markers block reruns.

## Round-1 fixes

I read the code and the smoke records; I ran nothing.

- **Old against new:** real. `equivalence.json` records the worktree at 7d25460, clean, with 1 045 identical arrays; the captures sum to 530, 309 of them under the bite rule.
- **`compare` and its helpers:** correct.
  - Every hunter plays every id, and padding rows are dropped.
  - Each world keeps its setting on both sides, including the validation shape against the 1 × 512 reference.
  - The SD comes from separate worlds, and the largest required count is used.
  - The Welch–Satterthwaite formula and the weighted sizing SD, sqrt(8 Σ w²s²), are right.
- **Finiteness:** `play` raises on the final state. That is enough, because a NaN survives the clamp, the modulo and the brain step.
- **State level:** all 16 genomes at every shape; a NaN fails.
- **Respawns:** `_reap` runs after the move, so the distance measured after the tick is the placement, for moving prey too.
- **Cap and prerequisites:** the cap is bound to the bench's hash, and `fits` and explicit pass or complete are required. The refusal shows in the smoke's `compute.json` (cap 1 h, signal failed, cap 100 h, signal completed).
- **Projection:** I recomputed all five cut levels by hand; they match the smoke's episode counts.
- **Sabotage log:** 28 cases, all failed as required, clean run rc 0.

## Fix before running

1. **The bench's `e5_1a_remainder_upper` is not an upper bound.**
   - It omits the CPU side of the null champions' CPU-against-CUDA checks in the composition stage: up to 8 × 5 × 8 704 episodes, about 1.6 h at E5-0's 0.0165 s per episode.
   - Nothing compares spent plus remainder with the 6 hours. Add the term and a recorded `fits` flag.
   - Decide now, in §14.1, what happens if E5-1a's own cap stops a stage midway. Its start marker blocks a rerun, and the design is silent.
2. **§14.1's "plays hold at most 1 024 worlds" is false.** The code plays 4 × 512 = 2 048 in the CUDA stage and 8 × 512 = 4 096 in the bench, composition and sensitivity. I think 4 096 is fine, since it is the suite shape, but correct the sentence.
3. **The "scoring" equivalence rows can pass on zeros.** Both training-shape rows had `captures_mean: 0.0` in the smoke. At 300 ticks the champions should score, but nothing requires it. Add `captures_mean > 0` to `passed` for the champion rows.
4. **The null champions' CUDA check omits the mixed training shape.** §7.7 says "as in step 3", which includes it. Add `"mixed": (128, 8)` or state the omission in §14.1.

## Before the formal run, by hand

- **Worktree:** check that `git -C ../wormWars-e5-1ref status --porcelain` is empty. The stage writes its start marker before `reference_worktree()` checks this, and the smoke only checked it before any child had run there.
- **Whole suite:** `full-suite-guards.txt` stops at 45%. Wait for its exit code before committing.

## Not blocking

- **"High" is B's rate, not a ceiling.** It comes from generations 1 to 4 (3 elites and 29 mutants of Task N champions). Hunters evolved on Task H may capture more, and `stage_cap` judges the fit on it mechanically. Give the owner the capture rate behind it (`mean_fitness_by_generation`) beside E5-0's pursuit reference.
- **`smoke-cap.txt` is stale.** It still shows the first smoke ("cap 50.0 -> (1) B moves later"), and the second smoke's refusal output was not saved.
- **The pilot's null signal uses other batch shapes.** It plays 32 × 8 and 1 × 256, where N2's plays 128 × 8 and 4 × 256. It is never a stop, but say so in the record.
- **The ghost check does double work.** Each side computes both worlds.

After the fixes: run equivalence, graphs, cuda and bench, then stop for the owner's cap.