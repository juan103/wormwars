**Revise.** Most v2 fixes are implemented. The remaining substantive blocker is that the newly permitted hard-kill retry loses the killed attempt’s compute from the cap. §6 also needs a factual correction.

I inspected the working files, with the HEAD reference pointing to `dff52b3`. I did not execute project code, tests, simulations or hash checks.

Two changes are required before binding:

1. **Charge hard-killed attempts against the cap before permitting a retry.**

   [`archive_attempt()`](/D:/Claude/random/wormWars/scripts/e04a.py:228) now accepts a marker without a result. That fixes the deadlock, but the accounting does not survive the corresponding hard kill:

   - [`accounting.attempt()`](/D:/Claude/random/wormWars/wormwars/accounting.py:250) writes its ledger only in `finally`.
   - `recorded()` likewise updates the aggregate in `finally`.
   - [`CapClock`](/D:/Claude/random/wormWars/wormwars/registration.py:123) reads that aggregate and adds only the current process’s elapsed time.
   - Neither `archive_attempt()` nor the three commands reconcile the killed process’s missing runtime.

   Consequently, an attempt can consume hours, be forcibly terminated, and then be retried with those hours absent from the six-hour budget. This contradicts §8’s cap “across all attempts.” Catchable exceptions and ordinary interrupts do not have this particular problem.

   **Fix:** require durable accounting or an explicitly recorded conservative reconciliation of the killed attempt’s time before another rollout; include it exactly once in the cap. Refuse a marker-only retry when its budget cannot be reconciled. A durable checkpoint alone needs a policy for the unrecorded tail.

   Add a regression test covering a marker-only attempt **with previously consumed time**, including refusal when reconciliation exhausts the cap. The current kill test merely creates a marker and calls `cmd_train()` directly; it bypasses `run_script()` and cannot detect this failure.

2. **Correct the minimum-mean explanation in §6.**

   [The expectation paragraph](/D:/Claude/random/wormWars/experiments/04a-navigation-primitive/PREREGISTRATION.md:261) says a mean near 1.60 could pass only if “nearly every episode reached exactly 2.” That is wrong.

   The minimum passing empirical mean is
   `820 × 2 / 1024 = 1.6015625`, attained by **820 episodes reaching two targets and 204 reaching zero**. That is about 80% reaching two, with about 20% failing completely.

   Suggested replacement:

   > Rule 1 requires at least 820 of 1,024 episodes to reach two targets. Its minimum possible passing mean is 1.6015625, attained by 820 episodes reaching exactly two and the remaining 204 reaching zero. A higher mean alone does not establish passage.

   The Poisson comparison is acceptable as an explicitly hypothetical illustration, not evidence about the pilot’s distribution. Keep 1,000 generations, the optimizer and the thresholds.

The requested v2 fixes check out as follows:

| Item | Code-level finding |
|---|---|
| **Separate seeds** | Fixed. Formal runs use `1_105_000 + run`; projection explicitly supplies `1_109_000`; `use_smoke()` sets `1_108_000`; the pilot explicitly retains `1_104_000`. The saved pilot record agrees with the latter. |
| **Effective brain configuration** | Fixed. [`check_genomes()`](/D:/Claude/random/wormWars/scripts/e04a.py:567) compares the loaded candidates’ complete effective configuration with `cfg.brain`, before the evaluation marker. This catches the padding override in `load_genome()`. |
| **Marker-only kill** | The retry is now reachable, and the old marker is archived. The accounting problem above remains. |
| **Projection retry** | `cmd_project()` now handles `--rerun`, accepting a stopped projection or a completed over-limit projection, and rejecting a completed passing projection. |
| **Over-limit amendment** | The former same-code deadlock is removed: projection can run on the amended commit, and batch A subsequently checks against that new projection. `AMENDMENTS.md` exists and is outside `GUARDED`. Recording the amendment and restricting the change remain procedural requirements; the runner does not validate them. |
| **Local training genomes** | `cmd_train()` includes each batch’s candidate files and final populations in the archive list. The retry note records the filename mapping. |
| **Reason and second stop** | A nonblank reason is required and written before the new stage starts. Existing archived record/marker files prevent a second retry. The test now genuinely stops both attempts. |
| **Failure record before genome saving** | Fixed. [`_train_not_completed()`](/D:/Claude/random/wormWars/scripts/e04a.py:444) writes the stopped record before retrying genome persistence, then records an ordinary persistence exception separately. |
| **Decoy error record** | Fixed. Each decoy calculation has its own exception handler; replay and module processing can continue. |
| **Exposure qualification and ledgers** | Fixed. Both preserved ledgers contain 48 selection worlds and 1,920 selection ticks, and both flag dirty code. The revised account correctly distinguishes reconstructed IDs from directly verified historical IDs. |

**The projection-plan change is correct for the registered two batches.** [`training_plan()`](/D:/Claude/random/wormWars/scripts/e04a.py:164) uses the same checkpoint condition as `evolve_batch()`: generation zero, multiples of the interval, and the final generation without duplication. It yields 2,000 batch-generations and 82 checkpoint rollouts; reducing to 500 generations yields 1,000 and 42.

`projection_verdict()` uses that plan, the median of generations 1–4, and the nonnegative final-generation excess. The genome-writing callback executes before the generation timer is recorded, so those writes are included. The text now appropriately calls this an estimate and acknowledges omitted final-generation breeding and growing checkpoint files.

The tests provide meaningful coverage, but some names and claims exceed what they exercise:

- The padding-metadata, persistent genome-save failure, decoy failure, stopped-training retry, second-stop refusal and validation-only NaN tests target the intended paths.
- `test_the_projection_is_rerun_after_a_stop_or_over_its_limit_only` exercises **over-limit**, not an actual stopped projection. It changes `within_limit` manually; it does not reduce generations or exercise an amended binding commit.
- There is still no evaluation-retry test.
- The guarded comparison test verifies calls to the code/environment guards, not rejection of mismatches through the stage commands.
- The archive test checks one candidate file’s stored hash list. It does not cover final-population preservation, the archive mapping, or recomputed parameter hashes.
- The genome-save failure test establishes that a stopped record survives. It does not test failure after an earlier durable checkpoint.

I have not established that these tests pass or verified their fail-before-pass history.

Suggestions, separate from the must-fixes:

- **Clarify projection-genome retention.** The new callback writes `OUT/projection-genomes`, but projection retry archives only its JSON and marker, so those genomes are overwritten. The comment says “then discarded,” but no cleanup performs that discard. Either archive them or explicitly exempt these timing scratch files from §8’s general genome-preservation promise.
- Add the missing stopped-projection and evaluation-retry cases, and a real amended-generation projection test.
- Strengthen persistence tests with a successful checkpoint followed by a failing save, then verify the surviving files and archived mapping.

I read `scripts/e04a.py`, `wormwars/e04a/evolve.py`, both requested test files, the pilot runner, relevant genome loading/hashing, registration and accounting paths, `AMENDMENTS.md`, D105, the archived v2 reviews and the supporting exposure records. I also checked the equivalence comparison’s new failing exit status. D106 is outside this verdict.

**04a pre-registration: revise**