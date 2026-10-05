**Verdict: run it.** Every required change from my two reviews is in the code with a test, Astra's five items from the last recheck are fixed correctly, and I found no path by which a completed run's registered reading would be computed other than as registered. What remains is one narrow gap in the stopped-stage route and three process conditions the guards enforce.

I read the code and records only. I could not run the suite, git, or the smoke; the smoke folder's state (a `train-smod` rerun ending in `reuse_refused: BadZipFile`, no `evaluate.json`) is what the test file leaves behind when run in order, which is consistent with the slow tests having run.

## D212-D214 against my earlier findings

All of my second-review required changes hold at 2e40827:

- **Stopped evaluate reportable.** Metadata is in the Progress state before any play at `scripts/e3c.py:1247-1251`; references play first at line 1258; a missing reference is a registered "not read" at lines 1403-1408; a champions record without W2-turn is skipped at line 1254. Tested by the salvage-shaped record test.
- **Consistency bypass closed.** In-loop checkpoints are written into each run's entry before the plays at line 1037 and checked in every attempt at lines 1054-1056. The test makes the mismatch refuse in attempt 1 and again after reuse.
- **Hash mismatch retrains** at lines 1003-1006, and the annotation says so.
- **Holm p = 1** for an unread contrast through the bound `contrasts` at `wormwars/e3/e3c_stats.py:95`, with the test comparing the partial reading to the full one.
- **Smoke cleanup** in `use_smoke` at lines 1609-1618.

Astra's five items, checked: the path-shape contract is now the same on both sides (lines 1234 and 1320) and tested on real files; W2-turn, each P-joint point, each learning reference and each `g-e` leg persist at once (lines 1166-1194, 909-914); champion saves go through a temporary file (lines 818-824); the no-evaluate report runs the full reading function with an empty evaluate record (lines 1577-1581); a corrupt archive falls into the retrain branch (line 1003); the bootstrap uses the scalar registered seed (line 1427) with an oracle test.

**The false-mismatch risk on the GPU is low.** The in-loop checkpoint and the post-hoc play use the same world class, the same strain-major layout and the same composition [R, 128, 8]. The pilot gives empirical evidence: all nine runs' generation-99 in-loop validation means equal their post-hoc play means to every printed digit, including the S-mod and P-sel runs that were trained in a 6-run batch and played in 3-run chunks.

## What could still cost hours or work

1. **A crash or kill whose rerun the cap refuses leaves the stage unreadable.** `run_stage` checks the cap at `scripts/e2.py:594-598` before `apply_rerun` writes anything, so the stage stays "stopped" (or marker-only) and `require_record` at `scripts/e3c.py:728-745` accepts only cap-outcome or final-stopped records. The report then refuses for good. This needs the cap to be crossed inside the very rollout that crashed, so it is narrow. A three-line fix is to let `require_record` treat a stopped or killed stage as final when the cap clock is exhausted. If you skip it, say in Amendment 2 how such a record would be read by hand. Fixing it after `project` starts is blocked by the code guard, so decide now.

2. **Nothing guarded may change between `project` and `report`.** `require_same_code` runs against every earlier record's commit over `scripts/`, `wormwars/`, `configs/`, `requirements.txt`, the design doc and the pre-registration. Amendment 2 must be committed and pushed before `project`, and any later annotation, even a dated note of a cap stop, must wait until after `report`.

3. **Each stage's record must be committed and pushed before the next stage**, including a cap-stopped record. The frame refuses otherwise.

Smaller notes, none blocking:

- The smoke test asserts the report completed but not that the real path validator passed; one assertion on `eligibility[arm]["paths_ok"]` and zero undefined nose classes would catch a recurrence of the D213 regression. Tests are not guarded, so this can be added any time.
- `check_pinned` runs after the start marker, so a pinned-file mismatch consumes a stage's one rerun at no GPU cost. This is the established pattern.
- The train record stores each run twice, under `training.runs` and `runs`. Cosmetic.