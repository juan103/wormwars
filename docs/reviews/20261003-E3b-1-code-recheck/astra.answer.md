**No. At `78f78a5`, three issues remain in failure recovery and recording.** Most of the fixes are correct, but D188’s “every blocking finding fixed” claim is premature.

I checked both archived reviews against the code. **100 tests passed**, with five tests that write files excluded. I also exercised the actual stage/recovery functions with persistence replaced by in-memory dictionaries. I did not run formal stages or modify files.

1. **Terminal recovery still depends on admitting another training batch.**

   [cmd_train’s `requires`](/D:/Claude/random/wormWars/scripts/e3b1.py:706) no longer rejects exhausted attempts explicitly, but it still applies the full training admission formula before `train_attempts` can settle them.

   I reproduced both sequences:

   - Attempt 1 non-finite → attempt 2 killed.
   - Attempts 1–2 non-finite → attempt 3 killed.

   With admission satisfied, both now produce a final record without running another batch. With admission unsatisfied, both instead write a refusal, produce **no final training record**, and classify the stage as `refused`. That changes an already-final failure into “not run” and unnecessarily prohibits later training.

   **Fix:** distinguish bookkeeping-only settlement from a new attempt. Reconcile and finalize exhausted attempts before training admission and the frame’s execution guards. Preserve the registered failed-run classification. Also correct the terminal error at [line 759](/D:/Claude/random/wormWars/scripts/e3b1.py:759): these paths did not all end with non-finite scores.

2. **An in-stage refusal still records every run as failed.**

   The durable refusal and refusal-first `stage_state` correctly prevent later training. However, [the refusal branch](/D:/Claude/random/wormWars/scripts/e3b1.py:753) raises `RuntimeError`, while [`unmade_label`](/D:/Claude/random/wormWars/scripts/e3b1.py:387) recognizes only `CapReached` as “not run.”

   Through `cmd_train → E.run_stage → _not_completed`, I obtained:

   ```text
   stage_state: refused
   refusal record: runs are not run
   stage record: failed_runs = [0,1,2,3,4,5,6,7]
   stage record: no not_run_runs
   ```

   This leaves Astra’s finding 4 partially unfixed.

   **Fix:** make salvage distinguish admission refusal from execution failure, and test the resulting stage record—not just the refusal file. The cap exception path itself works correctly.

3. **A killed outer rerun produces an incomplete final training record.**

   When the outer rerun is killed, [`rerun_plan`](/D:/Claude/random/wormWars/scripts/e2.py:478) calls [`final_killed_record`](/D:/Claude/random/wormWars/scripts/e2.py:505) directly, bypassing `cmd_train`’s salvage.

   The new [training progress record](/D:/Claude/random/wormWars/scripts/e3b1.py:405) contains only generation, batch run numbers and timestamps. Consequently, the final training record has **neither `attempts` nor `failed_runs`**. Before the first checkpoint, it has no run identification at all. I reproduced both cases. Provenance fallback and compute reconciliation work, but the registered failure classification and attempt history are absent.

   **Fix:** reconstruct the final training record from the durable attempt journal and the registered run set, including previously excluded runs. Cover kills both before and after a checkpoint.

The other blocking findings check out:

| Archived finding | Confirmation |
|---|---|
| Astra 1: kill accounting | The 900-second tail is configured. Checkpoint, champion-read and evaluation/calibration-chunk progress reaches the frame’s reconciliation file list. Final training records still need fix 3 above. |
| Astra 2 / Fable B1: internal-attempt kills | Works when admission passes; fix 1 remains. |
| Astra 3 / Fable B2: elapsed-time admission | Fixed: the callback receives `ctx.cap.t_start`. |
| Astra 4 / Fable B3: refusal and cap handling | Durable refusal precedence and subsequent-training prohibition work. Cap salvage works. Refusal classification still needs fix 2. |
| Astra 5: non-finite validation runs | Fixed: the exception identifies the actual run numbers in its message and `.runs`. |
| Fable B4: validation composition | Fixed in both champion validation and benchmarking: one chunk of 32 × 128. |
| Astra 6: independent denominators | Fixed for all four registered readings. S-peer remains readable when shared seed visits are zero. |
| Astra 7: secondary conclusions | Fixed: correct alternatives, upper bound for S-peer, lower bounds for the other secondaries, and conclusions controlled by Holm. |
| Astra 8: terminal champion failure | Fixed: `readings_from` returns “not read” without accessing missing champions. |
| Astra 9: S-trail summaries | Fixed: complete pairs, equal schedule weights, and a numerically consistent decomposition. |

I also checked the additional findings: `_counts` preserves fractional observations and integer records; route overlap and S-gen’s bound are implemented; admission projections account for completed runs in earlier stages; publication/provenance checks cover stopped training records; evaluation lists actual chunk compositions; the hook comparison describes its scope accurately; and the W2-alone note explicitly disclaims comparability with E3b-0. The distinct-organism batching test passed.

**Archiving the new progress records does not introduce the suspected chunk-loss problem:** the frame archives the partial JSON, leaves completed evaluation arrays in place, and permits a fresh progress record on recovery.

**Verdict: fix terminal kill settlement, refusal classification, and killed-rerun training records before starting the formal stages.**