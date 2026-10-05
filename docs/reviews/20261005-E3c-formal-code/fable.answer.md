I have everything I need. Writing up the review now.

**Verdict: fix first.** Two real defects, both small to fix and neither affecting a run that completes cleanly. Nothing I found would make a completed run's readings wrong. The exposure is to what happens when a stage stops.

## The defects

1. **The eligibility rule's "below the minimum" path is not implemented, and a twice-stopped training stage blocks everything after it.** `require_formal_stage` at `scripts/e3c.py:714` calls `require_earlier` without `final_ok`, so a final-stopped `train-psel` refuses `champions`, `evaluate` and `report`. Even with that flag, `cmd_champions` reads `ctx.earlier["train-s"]["arms"]` at `scripts/e3c.py:964`, while a stopped record carries `arms_completed` from `scripts/e3c.py:831`. The report at `scripts/e3c.py:1113` has no "not read: too few runs" branch and no "P-sel described with whatever runs count" branch. §5 registers these and §12 lists their test. A double stop of the 3.6-hour P-sel stage would leave the 20 hours of primary readings unreadable without hand intervention, against rule 3.

2. **Trained populations live only in memory until after the post-hoc checkpoint plays.** In `train_arms`, the genome files are written at `scripts/e3c.py:889` after the frozen assertions, 21 hash lookups and 21 plays at lines 860 to 882. Any failure there loses the arm's 6.4 hours with nothing on disk; the salvage at line 830 keeps hash lists only. Save the final and snapshot populations the moment `evolve_batch` returns, then play. This changes no registered procedure.

Recommended, not blocking:

3. **No partial record or salvage for `project`, `champions`, `evaluate`.** §5's frame promises both for every stage. Those bodies never set `ctx.salvage` or write partials. Low cost: each is rerunnable and about an hour.
4. **The missing-checkpoint rule** of §5 and §7.2 is not implemented at `scripts/e3c.py:1155`. A short curve reads as censored, not undefined. Unreachable today, since a completed run always has 21 points.
5. **P-joint's log is indexed by position** at `scripts/e3c.py:1013`. The real record has 300 entries so this is correct, but assert the entry's `generation` field equals 124 or 299.
6. **Report omissions against §7.3 and §7.4.** The qualifier is stored beside the labels at `scripts/e3c.py:1226`, not appended. W2-turn's coverage and tour match, P-sel per run against P-fixed and P-joint, and each champion's turn offset and K_D are in the evaluate record but not in the report. The learning curves are only in the champions and train records.
7. **`checkpoint_consistency`** at `scripts/e3c.py:896` is recorded, not surfaced. Have the report print it.

## Answers to the six questions

**1. Does each stage do what §5 registers?** Yes, on every point I could check.

- `project`: benchmark ids only, first 128 for the checkpoint and champion chunks at `scripts/e3c.py:733`, all 256 for evaluation at line 767. Timings of [256,8,8], [192,8,8], [128,8,8], [64,8,8] at line 753. Admission with ×1.25 in `wormwars/e3/e3c_formal.py:68`, cuts in §10's order at line 28. The remaining budget includes the 3.946 hours already in `runs/e3c/compute.json`.
- `g-e`: E3b-1's CPU, GPU and maze legs plus the hook leg via `scripts/e3b1.py:676`. The gate at `scripts/e3c.py:717` guards both training stages and `champions`.
- `train-s`, `train-psel`: runs, seeds and ids match §3 and §4 in `wormwars/e3/e3c_formal.py:11-17`. Draws use the registered stream at `scripts/e3c.py:853`. Every training id is pre-flighted at line 827. The frozen sets are checked on the final population and every snapshot at line 861. Final populations and candidates are saved with hashes at line 889.
- `champions`: P-joint's 256 + 256 hashes are checked before any play at `scripts/e3c.py:962`. The validation chunk is [32,128,8] per run. Ties go to the lower index via `np.argmax`. W2-turn's grid and tie rule match §3. P-joint's two points are found by the logged hash at line 1013. The two references use [1,128,8].
- `evaluate`: champions are hash-checked against the champions record at line 1073. Chunks are [runs,256,8]. Noses removed covers every champion and P-fixed. Trails off covers champions, P-fixed and W2 alone, intact only, and is skipped when cut.
- One interpretation to note: §5 says "each wey's cell path recorded in both conditions". The code keeps every wey's path in memory for the measures but stores only eight sample paths per strain at `scripts/e3c.py:446`, as the replay did.

**2. Is the checkpoint approach equivalent, and is the check sound?** Yes. In `wormwars/e04a/evolve.py:182` the snapshot is taken before breeding, and `best_sha256` at line 177 is computed on that same population. No breed follows the last generation, so `final` at line 211 is the population evaluated at 299. The post-hoc play uses the registered [R,128,8] composition. The in-loop checkpoint and `play_batch` build the same strain-major world layout through the same class, compare `wormwars/evo/rollout.py:69` with `wormwars/e3/maze_runs.py:356`, so equality at 0 and 299 is meaningful. One limit: the check cannot tell a pre-breeding snapshot from a post-breeding one, because the best genome survives as an elite. The code is right by inspection.

**3. Does `report_readings` compute §7?** The unit d, the exact test at 0.025, the 97.5% Welch intervals, Holm beside, the dual margin with strict bounds, the floor guard, the failed-run counts, the Fisher test and the decomposition, Mann-Whitney, the maze-paired bootstrap with its seed and 10 000 resamples, the cost curve with censoring and Holm over thresholds, the nose classes, coverers, the paired loss t-interval, P-fixed's bootstrap with its seed, the coverage rule and the nose-dependence Welch all match. Gaps are items 4 to 7 above. A non-positive P-fixed mean does not crash, but the bootstrap at line 1143 then divides by zero with warnings.

**4. What can make the hours worthless?** Organisms and masks are right: P-sel uses the seed with `stage2_scales` at factor 1.0, the S arms use the registered contexts. P-joint's ext matches E3c's seed because both come from `start_organism("seed")`. Hashes are device-independent in `wormwars/evo/genomes.py:42`. Missing records are refused by the frame. The real risks are defects 1 and 2, plus one design fact the owner should weigh before starting: `train-s` is a single 12.9-hour stage with a whole-stage rerun rule. A stop during S-dense's training costs S-mod's completed 6.4 hours, and a full rerun does not fit under the 30-hour cap. Splitting the two arms into separate stages would be an amendment to §5.

**5. Is §12 covered?** Missing or partial:

- the salvage and the eligibility rule: no test, and no implementation;
- the pre-flight of every id: exercised by the smoke, not asserted;
- the once-only rule and the rerun: covered only by E2's frame tests in `tests/test_e2_commands.py`, none for E3c;
- the W2-turn choice "on the validation block only": ties are tested, the block is not;
- P-joint's logged-hash lookup on the real files: only the slow smoke exercises it, and that test skips without the local genomes;
- the report "for every label": the report-level tests cover three Q1 labels, two nose outcomes and one coverage outcome. Within, unresolved, unclear, every Q2 label, supported, no material loss, not reached and a non-positive P-fixed mean are tested only at the statistics level in `tests/test_e3c_stats.py`.

**6. Verdict:** fix first. Items 1 and 2 are the required fixes, each under an hour with its test. After them, run it.