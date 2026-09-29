# Verdict: **run**

All eight must-fixes are resolved in the runner, and I found no new defect from the fixes. Two of the strengthened tests still cannot fail when their rule breaks. Both are test-only, so the guarded smoke can start now; close them before the formal projection. I need no further round unless one of them fails on the current code.

I could not execute anything. Every finding is from reading, and D133's thirteen sabotage checks are unverified by me.

## Must-fix (tests only, before the formal stages)

1. **`pairing_check` has still never been seen failing** (`tests/test_e2d_commands.py:327-342`).
   - The test at line 327 replaces the check's result, so it tests the consequence, not the detection.
   - The test at line 338 asserts only the shape of `last_generation_ids`. It passes if the check ignores their content.
   - Change: call `pairing_check` directly and assert `passed` is false for a tampered `last_ids` row, a changed generation-0 hash, and a changed roster.

2. **The Part B fallback is pinned by its label, not its behaviour** (`tests/test_e2d_commands.py:306-315`; rule at `scripts/e2d.py:966`).
   - The fakes score the same under every probe, so no champion is ever "uses". Dropping the `if b_ok` would pass.
   - Change: call `analyse_c` directly with champions that lose under `mean` and `swapped` and score below 2.5. Assert `leaves_plateau` is false with failed checks and true with passed ones. This is the case Astra reproduced.

## Suggestions

- **`boot_se` has no test** (`scripts/e2d.py:692`). The known-batches test uses constant rows, where any estimator gives 0. Pin it against an independent recomputation on varied rows.
- **The budget reading under a failed check** (`e2d.py:633-637`; plan lines 105-106). It is still drawn. That is defensible, since it uses only the `real` probe, but the plan's wording can be read either way. Record the choice in `DECISIONS.md` before Part B.
- **Formal-only checks sit after the start marker** (`e2d.py:558-567`). A hash or denominator failure would spend Part B's one rerun. Load the 48 champions on the CPU once beforehand.
- **C0's reading:** only the "not material" branch is tested (`tests/test_e2d_analysis.py:207`). The 0.8 threshold, the 30-pair minimum and `+ 10 * r` (`e2d.py:675`, `681`) are unpinned.
- **A test writes to the formal folder** (`tests/test_e2d_analysis.py:248`). `training_clock()` rewrites `runs/e2d/compute.json` once that folder exists. Point `OUT` at a scratch folder.
- **Untested outputs:** the added fields and the interval/sign-flip disagreement note have no assertions.
- **Minor:**
  - `e2d.py:870` checks only each run's first strain row; compare all `P` rows.
  - `e2d.py:367` records backslash paths on Windows.
- **Reading the smoke:** at 40 ticks Part B's reference check fails by design (D132), so the guarded smoke exercises only the scores-only path.

## Checked and found correct

| Fix | Finding |
|---|---|
| Cap as final | `require()` (`e2d.py:417`) accepts it under `final_ok`, and `rerun_plan` refuses to rerun it. The test fails if reverted. |
| Incomplete and unpaired arms | Champions are not loaded (`e2d.py:916`) and readings need `usable` (`e2d.py:957-963`). C2′ needs every matched generation. The stopped-after-checkpoint test does leave champions in the record. |
| Part B propagation | Set readings and the plateau are "not drawn"; Part C ignores classes and records the rule. |
| Arm configuration | `ctx.doc` is the record's own dict and is updated before the first partial write. The loops and `breed` never read `cfg.evo.generations`. |
| Ids actually played | `run_method` resolves `rollout_mod.rollout` at call time, so `capture` is what the loops call. Training ids are 2-D and validation ids 1-D, so the last capture is the last generation's training. |
| C3's pairing | The ES's generation-0 checkpoint is the start genome, which does not depend on σ, so the hash check can pass. |
| Bootstrap SE | Resamples 248 of the 256 worlds with replacement; settings recorded. |
| Projection total | `spent_hours()` reads earlier attempts only, so adding the elapsed time does not double count. Attempt files are written at exit, so `training_clock()` does not either. |
| Added outputs | All present. `budget_context` matches E2's records: 166 144 and 100 608 episodes per run. |
| Smoke sources | `runs/e2-smoke` and `runs/e04a-smoke` were made on CUDA at `06d2121`, the current HEAD, with sizes matching E2d's smoke. |
| Local genomes | All 32 E2 and 16 04a candidate files are present. `runs/e2d/` does not exist, so nothing is charged yet. |