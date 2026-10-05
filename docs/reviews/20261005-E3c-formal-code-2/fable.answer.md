**Verdict: fix first.** Defect 2 is fixed correctly and Amendment 1 is sound on paper. But the stopped-stage reading that Amendment 1 promises still crashes for the stop that the budget makes most likely, and the reuse path lets a consistency mismatch through on the rerun. Both are small fixes. I read the code and records; I ran nothing, so I cannot confirm the suite result or recompute the pinned hash myself.

## 1. My required defects

**Defect 2 (populations saved before the plays): fixed.** Finals and candidates are written at `scripts/e3c.py:991`, before any checkpoint play, and the training entry is marked complete at line 1002. The archived attempt in `runs/e3c-smoke/train-smod-attempt1.json` shows exactly that state after the injected failure, and the rerun test at `tests/test_e3c_stages.py:303` makes retraining fail and completes anyway.

**Defect 1 (eligibility and stopped records): partly fixed.** The eligibility rule is implemented at `scripts/e3c.py:1283` and every synthetic case Astra listed has a passing test. A stopped training stage is read correctly through `trained_runs`. The gap is the other two salvage paths:

- A stopped `evaluate` record cannot be reported. `ab_distance` exists only in the completed record at `scripts/e3c.py:1254`, not in the Progress state at line 1210, and the report indexes it unconditionally at line 1464. If the stop came during the arms, the references are also absent and line 1274 raises before that. Every evaluate stop therefore crashes the report, whose own rerun crashes the same way.
- A final-stopped `champions` without a W2-turn choice crashes `evaluate` at `scripts/e3c.py:1239`, and the report at line 1343 if the learning-curve references are missing.

The cap is the realistic stop here. Remaining budget is about 26 hours against a projection of about 25.5 with the training margin, so a training overrun near 20 percent lands the cap in `evaluate`. No test builds a salvage-shaped evaluate or champions record for the report.

**My recommended items 3 to 7: all taken.** Partial records in `project`, `champions` and `evaluate`; the undefined checkpoint at line 1349; the generation assertion for P-joint at line 1141; P-fixed's class, coverer and loss at line 1422, maze differences, P-sel against both references, W2-turn's coverage and tour match through the references, turn offsets and K_D, the curves; the consistency result surfaced at line 1378.

## 2. Amendment 1 and its implementation

The amendment changes no composition, seed, id, block or reading, and it is dated before any formal stage. Points 1, 2, 7 and 9 are implemented as written: separate stages at `scripts/e3c.py:646`, the save before the plays, every wey's path at line 456 with the smoke asserting the shapes, the guarded pre-registration at line 67 and the pin checked at line 713, with the smoke markers carrying the hash. Three points are implemented weaker than the text:

- **Point 4 is bypassed by point 3.** The in-loop checkpoints live only in the local `inloop` at `scripts/e3c.py:958` and are never written to the record. A mismatch raises at line 911, the stage stops, and the rerun reuses the training and writes "not checked" at line 1023. So "a mismatch stops the stage" means it stops attempt 1 only. The archived record confirms no in-loop data survives.
- **Point 3 says a hash mismatch trains again.** The code refuses at line 968 instead. That refusal happens inside the body, after the marker, so it consumes the one rerun and the arm is lost. Refusing is the safer instinct, but then the text should say so.
- **Point 6 holds only when `evaluate` has a record.** The report's prerequisites at line 655 require all five records to exist, so a cap stop in a training stage or in `champions` leaves no report record. That is defensible, since there is nothing to read, but it should be said.

## 3. Defects the fixes introduced

- **The too-few path couples Holm to the unread contrast.** At `scripts/e3c.py:1316` the unreadable arm is padded or passed short, so the readable contrast's adjusted p depends on a contrast that is not read. The bound module's own rule at `wormwars/e3/e3c_stats.py:85` is p = 1 for an unread contrast. Never a label, but a published number that an outsider would recompute differently.
- **The slow tests are not repeatable on this machine.** The rerun test leaves `train-smod-rerun.json` and the `-attempt1` files in `runs/e3c-smoke`. `use_smoke` at `scripts/e3c.py:1496` deletes only the record, marker and partial, so on the next run `rerun_state` returns "setup" and the frame refuses at `scripts/e2.py:589`. The smoke of every stage and the rerun test both fail from the second run onward. This does not touch the formal run, but it will make the suite red.

## 4. Required changes

1. **Make a stopped `evaluate` reportable.** Put `ab_distance`, `test_ids` and `trails_off_run` into the Progress state before any play. Play the four references before the arms; the order is not registered and each play seeds its own world, so nothing changes. Have the report return a registered "not read" when a reference is missing rather than raise, and let `evaluate` skip the W2-turn reference when the champions record lacks it. Add a test that feeds a salvage-shaped evaluate record and gets a completed report.
2. **Close the consistency bypass.** Write the in-loop checkpoints at generations 0 and 299 into each run's record entry before the plays, and run `check_consistency` against them on reuse. Sabotage it. This makes the amendment's "not checked after reuse" clause unnecessary, which an annotation can note.
3. **Resolve the hash-mismatch behaviour.** Either train again and record the mismatch, as point 3 says, or annotate point 3 to say the rerun refuses.
4. **Holm with p = 1 for an unread contrast** in the too-few branch. One line.
5. **Clean the smoke folder's rerun files** in `use_smoke` or in the rerun test's teardown.

Two notes that need no code: Amendment 2 must be committed and pushed before `project` runs, because the pre-registration is now guarded and `require_same_code` refuses every later stage after any edit. And §15 to §17 sit outside the pin, which is fine since they are changelogs.