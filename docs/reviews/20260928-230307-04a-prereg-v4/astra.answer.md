**Revise, narrowly.** I checked `1653809` against `082210e` and the archived v3 reviews. I executed no project code or tests and made no changes.

The following fixes check out:

- **§6:** the minimum passing mean is correctly stated as `1.6015625`, from 820 episodes reaching two targets and 204 reaching none.
- **Over-limit projection:** `rerun_plan()` requires fewer projected generations before permitting the rerun.
- **§9:** 33.8 seconds agrees with the committed record’s `33.79282220010646`.
- **Rerun sequencing:** all three commands reconcile a marker-only kill before checking the cap and defer archiving until their prerequisite checks pass. Projection candidate files are included in the archive.
- **Tests:** the added cases cover elapsed kill time, cap refusal without consuming the rerun, repeated refusal without double charging, and stopped projection/evaluation retries. I have not verified that they pass.

**One blocking defect remains in kill accounting:** [scripts/e04a.py:274](/D:/Claude/random/wormWars/scripts/e04a.py:274) rebuilds `compute.json` **only when the reconciliation file does not already exist**.

The failure sequence is concrete:

1. Reconciliation writes `compute/killed-….json`.
2. The process is hard-killed before `acct.write_aggregate()` completes, leaving the previous valid `compute.json`.
3. The next rerun finds the reconciliation file and skips both writing and aggregation.
4. `CapClock` reads the stale aggregate, allowing another rollout despite the killed attempt potentially having exhausted the cap.

The outer accounting wrapper aggregates at process exit, which is too late: the rerun and its final cap check can already have completed against the stale budget. This is an interruption hole in the newly added recovery path.

**Required fix:** create the reconciliation record atomically; validate and reuse an existing record; and rebuild the aggregate unconditionally before allowing the cap check. Return the stored charge when reusing the record.

Add a regression case with an existing reconciliation record and a stale or missing aggregate. Its charge should exhaust the cap; assert refusal before any rollout or archiving, and exactly one charge after repeated retries. The current tests always complete the first aggregation, so they miss this state.

One nonblocking wording correction: §8 and D107 say accounting records are written only when a process “ends normally.” The `finally` paths also record catchable failures and interrupts. Say “when its cleanup handlers execute.”

I found no other blocking problem in the scoped diff.

**04a pre-registration: revise**