**Verdict: run it.** Every finding of mine is resolved, and resolved correctly; Astra's too, as far as I can check from the files. Amendment 1 is adequate. Only notes remain; none changes a registered quantity, rule or stage.

## 1. My findings

1. **Local replay required on the tested machine.** Resolved. `scripts/e4d_evo_formal.py:277-278` refuses `check` before the marker when any `gen010` file is absent; `:423-435` hashes the loaded arrays through `load_population`, not the metadata. Tests `:131-135` and `:230-238`.
2. **Amendment branches unreachable.** Resolved as I recommended. `GUARDED` (`:103`) no longer holds the pre-registration; `prereg_append_only` (`:213-216`) requires the bound blob at c3fe432, CRLF→LF, to be a prefix of the current file; `requires` (`:273`) compares predecessors on `CODE + PINNED` only, so a dated amendment after `check` no longer refuses later stages. Test `:138-143` passes an appended file and refuses an edited line.
3. **Tests that passed with a broken implementation.** Resolved. The balance test now sabotages through `play` and shows the assertion is load-bearing (`tests/test_e4d_evo_formal_stages.py:314-336`); the timing rule is asserted exactly with the boundary (`:81-85`); the champion's last-selection input (`:361-369`, `[0]` would give 0); a mismatched final (`:372-384`); frozen set and lineage (`:347-358`, at the helper level, which `cmd_train` calls unconditionally at `:572`, `:596`, `:598`).
4. **Rerun overwrote the first attempt.** Resolved. `local_files=train_files(arm)` (`:612`, `:539-544`). I checked `evolve_batch`: snapshot and `on_checkpoint` both fire at generation 99 (`wormwars/e04a/evolve.py:194-216`), so `gen099` exists; `reconcile_kill` now sees the population files' mtimes.
5. **S₀ and E-G unchecked.** Resolved (`:556`, `:642`, `:653`).
6. **Lineage mutations unrecorded.** Resolved (`:668`); `FM.lineage_mutations` is `lineage.mutations` on the saved arrays, line for line.

## 2. Amendment 1

Adequate. The spent ranges in `SPENT` cover the amendment's list; the new layout clears them and the pilot's; the smoke record confirms isolation (seed 1 429 000, run seeds from 1 449 000, blocks 40 000–43 101, training 200 M+). Keeping the run seeds is right: a seed fixes offsets into a range and a tie stream, neither of which observed a formal maze. The one registered rule it relaxes, §0.3's "this text … refuses if it differs", is stated openly, and it is the fix I asked for. Note: §4's bullet at line 134 repeats the old training range in prose; "replacing §4's ids" covers it, but one clause saying so would remove the ambiguity.

## 3. What the fixes introduced

Nothing wrong. Checked: the provenance order (pinned, committed, append-only, bound files at c3fe432, `CODE` at the amendment's last commit line, then the marker's commit and environment; the marker is still under its original name when `requires` runs, since `apply_rerun` comes after); the timing recompute (the L folder's clock, with `reconcile_kill` applied before `requires`); `validate_runs` (order, seeds, 32 validation shares, every condition with `[64, 2]` arrays summing to the totals and 128 trials; S's start); `tie_shares` equals the pilot's formula; `turnover`'s indices are consistent (`child[g-1]` indexes generation g, which `source[g]` draws from); persistence before each assertion, selections atomic.

Notes, no change required before running:

- **Low.** `use_smoke` (`:715-732`) does not update `REGISTERED["blocks"]`, so the smoke records say 64 000+ while the preflight played 43 000 (`runs/e4d-evo-formal-smoke/records/check.json:39-61`). Misleading to a reader of smoke records only.
- **Low.** `validate_runs` raises `KeyError`, not `IntegrityError`, if a condition dict lacks a count key (`wormwars/e4/evo_formal.py:164,166`). Only reachable from a corrupt record; still a stop.
- **Low.** If a rerun's archiving was interrupted after the marker was renamed, `check_provenance` finds no marker and skips the first-attempt comparison. Reading `attempt1(marker)` as a fallback would close it.
- **Unverified, no shell:** that `git diff c3fe432..HEAD --stat -- wormwars scripts configs requirements.txt` touches only `evo_trial.py` and the new files (the frame's `local_files` and `sha256_bytes` predate D276, so no E2 change was needed), and that `prereg_append_only` passes on the actual file. `check` exercises the latter before its marker, so a failure costs nothing.

## 4. Recording the commit and running `check`

Yes. Commit the confirmation reviews; append a line matching the regex exactly, `**The formal code's commit:** \`<hash>\``, naming fb30301 or the review commit if it touches no code path; push; then `check` with the owner's word. The placeholder sentence does not match the regex, so `check` correctly refuses until then. The GPU smoke's record shows e5e928f dirty; optionally rerun it once at the recorded commit so the smoke matches the code reviewed.