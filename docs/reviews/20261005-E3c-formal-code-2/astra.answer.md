**Fix first.** At `9d76251`, several fixes are correct, but interruption handling remains incomplete, and Amendment 1 introduces a checkpoint-check bypass.

I ran **57 read-only tests successfully**, inspected the existing smoke artifacts and path hashes, and reproduced additional failures in memory. I did not rerun the writing stages or the full suite. No files were modified.

For my previous required changes:

| Requirement | Recheck |
|---|---|
| Save populations before post-hoc checkpoint plays | Fixed. Broader durability remains incomplete. |
| Continue/report after interrupted stages and the cap | Partly fixed; still blocked or crashes in cases below. |
| Enforce eligibility and undefined cases | Minimum counts, missing checkpoint generations and missing nose rows are fixed; path/block completeness is not. |
| Preserve every path in both conditions | Fixed on completed evaluation. Existing smoke files have matching hashes and complete dimensions. |
| Add missing §7 outputs; fix one-run interval and nonfinite denominator | Those additions and numerical guards are present. Partial-record reporting still fails. |
| Compare checkpoint hashes and per-maze results; refuse mismatch | Works on the first attempt; reuse bypasses it. |
| Stage order, benchmark preflight, 23 checkpoint plays | Fixed. |
| Complete §12 tests | Improved, still incomplete. |
| Guard and pin the registered text | Fixed. The prefix is byte-identical after newline normalization and matches the stated SHA-256. |

The required remaining changes are:

1. **Make reporting work with the records that interrupted stages actually produce.**

   Raising the report’s cap to infinity does not complete the route. If `train-smod` hits the cap, later stages cannot start, and `report` refuses because `train-sdense` has no record. I reproduced that prerequisite refusal. See [the prerequisites](D:/Claude/random/wormWars/scripts/e3c.py:650) and [the frame’s pre-start cap check](D:/Claude/random/wormWars/scripts/e2.py:594).

   Even when all prerequisite records exist, actual salvage is insufficient. Evaluation puts `ab_distance` and `test_ids` only in its successful return, outside its salvage. Removing `ab_distance` from an otherwise complete evaluation reproduces `KeyError: 'ab_distance'`. Earlier stops reproduce `KeyError: 'seed'` or `KeyError: 'learning_curve_references'`. A stopped `champions` record can also lack the W2-turn choice that evaluation accesses unconditionally. See [evaluation](D:/Claude/random/wormWars/scripts/e3c.py:1238) and [reporting](D:/Claude/random/wormWars/scripts/e3c.py:1274).

   Persist the required metadata, handle unavailable references per reading, and permit reporting of stages never started because the cap was exhausted. This must produce explicit unavailable outcomes without running additional simulations.

2. **Retain and enforce checkpoint consistency across training reuse.**

   Amendment 1’s exemption is unsound. The original training **did** produce in-loop checkpoints; the runner simply does not persist them for reuse.

   I reproduced this using the real `train_arm` control flow with in-memory dependencies: the first attempt rejected differing per-maze counts; the rerun reused that training, received the same differing counts, and returned successfully with `"not checked: the training was reused (Amendment 1)"`. See [reuse](D:/Claude/random/wormWars/scripts/e3c.py:957), [the exemption](D:/Claude/random/wormWars/scripts/e3c.py:1018), and [Amendment 1](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:680).

   Save the original endpoint hashes and vectors alongside the training and compare them on reuse. A detected mismatch must not become an ordinary recoverable stop whose rerun disables the check. Correct the exemption through a dated amendment.

3. **Finish durability at the level of completed chunks.**

   `champions` publishes progress only after an entire arm. I injected a stop before its second validation chunk: the first run’s validation had completed, but salvage was still `{"arms": {}}`. See [the accumulation and save](D:/Claude/random/wormWars/scripts/e3c.py:1115).

   Evaluation similarly attaches each reference to salvage only after all its conditions finish. A stop during P-fixed’s noses-removed play loses its already completed intact result from the record. See [the reference loop](D:/Claude/random/wormWars/scripts/e3c.py:1240).

   Persist each completed validation chunk and reference condition immediately. Also complete the promised stage-wide partial/salvage handling: [`g-e`](D:/Claude/random/wormWars/scripts/e3c.py:876) still installs none. The current rollout-boundary `Progress.check()` calls do not establish the promised maximum one-minute write interval during longer operations.

4. **Enforce path and registered-block completeness.**

   The report never inspects `paths_files`. With no path manifests at all, I reproduced `"supported"` with zero undefined champions. That violates §5’s requirement that missing paths make §7.3 undefined. Stored coverage numbers do not establish that the required path records survived.

   Separately, the default expected maze count comes from P-fixed’s observed vector, rather than the registered block. Truncating every synthetic test vector from 16 mazes to 15 left all eight runs eligible and Q1 readable. See [the inferred count](D:/Claude/random/wormWars/scripts/e3c.py:1274).

   Validate against the registered maze IDs/count and validate path availability, integrity and dimensions. Missing paths must leave primary eligibility intact while making the affected secondary readings undefined.

5. **Remove fictitious observations from partial-contrast calculations.**

   The new partial-eligibility branch substitutes `np.zeros(2)` for insufficient arms, computes both contrasts, then discards the unavailable one. Its fictitious p-value still affects the surviving contrast’s Holm adjustment. See [that branch](D:/Claude/random/wormWars/scripts/e3c.py:1313).

   With Q1 unavailable, I obtained Q2’s raw and adjusted p-values both equal to `0.276072`; applying the existing unread-contrast rule of p = 1 gives `0.552144`. This is a **new defect introduced by the fix**.

   Represent unavailable contrasts explicitly and retain the registered testing family and interval levels. Compute each eligible contrast’s bootstrap independently too: currently an unrelated arm with fewer than two runs suppresses both bootstrap outputs.

6. **Test these interruption paths, not just complete synthetic records.**

   Add regression/sabotage tests for the cases above, including cap exhaustion before downstream stages start, the final frame cap check after a body returns, and mismatch followed by reuse.

   Remaining previously requested coverage also includes actual preflight-ID coverage, complete order/once-only and rerun-membership checks, actual cut compositions, an interior post-hoc checkpoint, and a numerical bootstrap oracle. The six-generation smoke still exercises only endpoint checkpoints 0 and 5.

The split stages, hash-verified reuse, post-hoc evaluation, full-path storage and CPU reporting are sound choices in principle. **Amendment 1 is not sound unchanged because its reuse exemption weakens the consistency protection**, and its durability/reporting promises are not fully implemented. There is also a textual mismatch in point 3: it promises retraining when saved training cannot be verified, whereas load/hash failures currently terminate the rerun. Resolve that behavior explicitly in the dated amendment.