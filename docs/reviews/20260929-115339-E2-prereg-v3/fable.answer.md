## Verdict: revise

One must-fix remains, and it can be fixed in the text alone. If option (a) below is taken as written, my verdict is "ready to bind" without another round. All five of my v2 must-fixes are resolved, in the text and the code, and each has a test.

I could not run the suite or `git diff` (no shell), so test and sabotage results are taken as reported.

## Must-fix

1. **§6's "the extension never takes the evaluation's budget" is false for the rerun** (`PREREGISTRATION.md:263-266`; `scripts/e2.py:905`).
   - The skip check is `if not a.rerun and need > left`, so an obligatory rerun of a stopped or killed extension starts whatever is left of the cap.
   - Example at the planning figures: a GA rerun earlier leaves about 1.22 h, so the extension starts (it needs 1.04 h). Killed near its end, it is charged about 0.79 h, leaving 0.43 h. Its rerun needs 0.54 h and reaches the cap.
   - E2 then ends "not completed (the registered cap was reached)" because of a descriptive stage. This takes two failures and is unlikely, but the registered sentence says "never".
   - **Change, one of:**
     - **(a) text only (recommended):** say that the extension's first attempt starts only if the remainder covers its projected time plus the reserve, and that its obligatory rerun is exempt, so the reserve is not guaranteed after a stopped or killed first attempt. Add a test pinning the exemption.
     - **(b) code:** apply the check to the rerun too, and finalise the extension without running it, with champions over what the first attempt completed. This is stronger, but it adds a state to the rerun logic and would need its own tests and review.

## Suggestions

- **The skip record escapes the guards** (`scripts/e2.py:426-427`, `:906-907`). It carries no provenance, and `require_earlier` returns before `require_committed`, so the evaluation can start with `extension.json` uncommitted. Write `provenance_at_start` in it and let the normal checks run.
- **§10's definition of "final"** (`PREREGISTRATION.md:352`) does not include "skipped", which the code treats as final.
- **§11 should hold the third smoke run itself:** 09:52:26-09:52:50 UTC, HEAD `99f06a9` with a dirty tree, projection seeds 1 128 900. D121 is not guarded. The second run's HEAD (`12725de`, dirty) is also missing from §11.
- **Test gap:** no test takes a killed extension rerun with a real partial record, whose champion has source "extension", through `evaluate`. `_kill` still writes `{}`. I traced the path by reading and found it correct.
- **A flat ES run changes hash after generation 0:** in the smoke run, `train-es.json:397` has `b6767851…` and `:409` has `7a9bafed…`, though the mean never moved. Selection is unaffected, since ties go to generation 0; say so in the results so it is not read as movement.
- **Nits:**
  - `README.md:25` says D117-D120.
  - The budget rows sum to 17 870 s, not 17 850 (`PREREGISTRATION.md:390`).
  - The `unlink` at `scripts/e2.py:624` is not retried; this is harmless, because the record is already written.

## Checked and found correct

- **Rerun setup:** the note is written "archiving" before the first move and "applied" after the last. `rerun_state` returns "used" only with an applied note and the rerun's own record or an attempt-2 marker.
  - I traced interruptions before any move, between moves, after the moves but before the marker, and after the marker. Each is continued or finalised correctly.
  - `reconcile_kill` charges once per marker, so a resumed setup is not charged again.
  - `require_earlier` refuses with the right message in each state, and a plain run refuses during a setup.
- **Retried moves:** `apply_rerun`, `reconcile_kill`, `save_genomes` and `save_state` all use the retrying `replace`, which has its own test.
- **The extension's champions:**
  - `train_batch` writes the first partial record before `run_method`, with the fallback champions.
  - `final_killed_record` rebuilds them from `train-es.json` when no partial record exists.
  - `analyse` builds the summary from `champions_over_both`, with each champion's source.
  - The stopped case (before and after the first checkpoint) and the killed case without a partial are tested through `evaluate`.
- **Generation 0:** `es_batch` validates the start genome itself. The GA, random sampling and the ES all break ties with the first maximum, so the pairing holds under ties. The third smoke run shows `b6767851…` for all three methods and `generation0_candidates_match: true`.
- **The skip rule, first attempt:** it uses the projection's ES rates and the accounting's total. The skipped record blocks both a plain run and a rerun, and the evaluation runs without extension arms. The 0.5-hour reserve is about seven times the evaluation's estimate (260 s) and covers a killed evaluation plus its rerun.
- **§11 and D121:** `runs/e2-smoke/compute.json` lists three chains, at 08:54 (`8966e5b`), 09:29 (`12725de`) and 09:52 (`99f06a9`), matching the text.
- **Counts and arithmetic:** 75, 17 and 14 tests by my count; the allowance table, the extension's 804 864 episodes and the pilot's stage-2 time (3.56 s) are right.
- **My other v2 suggestions:** `final` is set on a stopped rerun, §8.5 explains stage records' `outcome`, and the pilot test is renamed.

## Not checked

- Whether the tests pass, and whether the sabotage checks were run.
- The ENOMAD citations.