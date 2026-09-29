Checks finished: I read the v2 text, the bound code, the tests, both v1 reviews and the local smoke records. Review follows.

## Verdict: revise

Five small fixes, no redesign. All of my v1 must-fixes are resolved, but the fixes left two gaps in the new failure paths, one unguarded file move, one misleading report field and one stale exposure statement. I could not run the tests or `git diff` (no shell), so test and sabotage results are taken as reported.

## Must-fix

1. **§11 is inaccurate again: there were two smoke chains, not one.**
   - `runs/e2-smoke/compute.json:6-231` lists two full chains: 08:54:33-08:54:58 UTC at `8966e5b`, and 09:29:48-09:30:12 UTC at `12725de` with a dirty tree (the v2 code before its commit).
   - The second overwrote the first's records. `runs/e2-smoke/projection.json:330` now shows `seeds_base` 1128900, so D120's "Verified in `runs/e2-smoke/`" can no longer be checked from the folder.
   - **Change:** state both runs in §11, with each one's commit and seeds, and that the evidence for 1 129 000-1 129 002 is Astra's v1 review.

2. **`analyse` drops a stopped extension's champions from the summary** (`scripts/e2.py:986-987`).
   - It lists runs from `ext["records"]`, which is `[]` when the extension stops before generation 625 (`train_batch` fills `records` only at a checkpoint, `:663`, `:668`).
   - The formal-source champions are evaluated, but `extension.runs` is `{}` and `mean` is `None`.
   - **Change:** iterate `champions_over_both` and carry `source`. Add a test that runs through `evaluate`; the current one stops at `extension.json`.

3. **A killed extension rerun with no partial record loses its champions, against §6** (`final_killed_record`, `scripts/e2.py:453-464`; `champions`, `:890-896`).
   - The final record then has no `champions_over_both`, so no extension arm is evaluated.
   - **Change:** write the partial record once in `train_batch` before `run_method`, with `summary([])`; or narrow §6.
   - **Test gap:** `_kill` writes `{}` as the partial (`tests/test_e2_commands.py:364`). No test builds a final record from a real partial and evaluates it.

4. **`apply_rerun` and `reconcile_kill` still use a bare `os.replace`** (`scripts/e2.py:503`, `:490`).
   - If the transient refusal hits after the record is archived, `rerun_used` is true (`:285`) while the marker remains.
   - The next `--rerun` takes the killed-rerun branch (`:434-439`): it charges attempt 1 again and writes a final record from attempt 1's marker and partial.
   - The stage becomes final without its rerun ever running; for the GA that is "no decision". This is unlikely but irreversible.
   - **Change:** use the retrying `replace` in both places, with a flaky-replace test.

5. **The pairing report says the generation-0 candidates match when the ES's does not** (`scripts/e2.py:991-998`; §3, §9).
   - In the smoke run every champion is a generation-0 checkpoint. The GA and random sampling have `b6767851…`, the ES `7a9bafed…` (`runs/e2-smoke/evaluation.json:324-329`; `train-es.json:395` against `:445`).
   - The ES validates `decode(encode(start))`, which is not bit-identical. Its generation-0 validation counts need not equal the GA's.
   - **Change, one of:**
     - validate the start genome itself at generation 0 (`wormwars/e2/loops.py:180`) and say so in §3;
     - or disclose the round trip in §3 and §9, rename `generation0_candidates_match`, and report the ES's generation-0 checkpoint hash.

## Suggestions

- **Protect the evaluation's budget:** the descriptive extension runs first, and if it reaches the cap E2 ends "not completed". Let it refuse to start unless the remaining cap covers it plus the evaluation.
- **Stage records carry E2-level wording:** a stopped `train-ga.json` says "E2: not completed (the run stopped)", even on a first stop. Say in §8 that a stage record's `outcome` is the stage's status.
- **`final: true`** appears only on killed-and-finalised records; crash-then-crash finals lack it.
- **Rename** `test_the_pilot_selection_breaks_ties_by_the_smaller_value` (`tests/test_e2_commands.py:291`); its assertions are right, its name is not.
- **`replace()` has no test of its own;** §14's "(tested)" covers `write_atomic` only.
- **Budget table:** pilot stage 2 uses 3.8 s per generation, where scaling by strain count gives 3.56 s. It is harmless, but it is not "scaled by strain count".

## Checked and found correct

- **"Final":** all four crash/kill sequences end final by reading `require_earlier`, `rerun_plan`, `final_killed_record` and `rerun_used`, and each has a test. A repeated `--rerun` and a plain rerun are both refused after finalisation.
- **Killed-and-finalised record:** `provenance_at_start` comes from the rerun's own partial or marker, since `apply_rerun` archives attempt 1's. Genomes are saved before the partial, so champion hashes always resolve.
- **`decide`:** the incomplete-ES outcome, "no decision", the floor branches and `provisional` match §8; empty champion lists are handled.
- **Stopped extension:** `champions_over_both` is in the partial and the stopped record, with ties to the formal checkpoint.
- **Per-arm partial record:** written after every arm and tested.
- **Pilot tie order:** matches §4, and I found no new problem in it; `uninformative` is correct for both stages.
- **Seeds:** the projection uses 1 129 100-1 129 108 and smoke projections 1 128 900+; no other file uses them.
- **Budget:** the rows sum to about 17 900 s, there are 142 checkpoints, and the 4.7 h and 5.1 h figures follow. The labels are fixed.
- **Test counts:** 62, 16 and 14 match; the ES constants are pinned.

## Not checked

- Whether the tests pass and the sabotage checks were run.
- The ENOMAD citations.