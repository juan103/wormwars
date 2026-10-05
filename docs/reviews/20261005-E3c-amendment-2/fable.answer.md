**Verdict: fix first, text only.** The D216 code is correct and needs no change. Amendment 2 has one sentence that will be false for seven of the eight stages, and because the pre-registration is a guarded path it can only be annotated before `project` runs.

**1. D216: correct and complete.** I traced the sequences against the frame; I could not run the suite or `git diff` from this session.

- **Killed first attempt.** A kill leaves recorded compute below the cap, since the running attempt is not in the aggregate. So `cap_exhausted()` at `scripts/e3c.py:748` cannot be true until the owner's `--rerun` charges the kill through `reconcile_kill` at `scripts/e2.py:491`. The cap check at `scripts/e2.py:596` then refuses before `apply_rerun`, so the rerun state stays "none" and the marker and partial keep their names. The route reads them under the same three guards as the stopped route. Rule 8 is satisfied by construction, though the amendment does not say so.
- **Killed rerun.** `rerun_state == "used"` sends it to the frame, which charges and writes a final record at `scripts/e2.py:479`. That record then passes `require_earlier` as final-stopped.
- **Kill before any partial.** The empty record flows through `report_from` correctly: `trained_runs` gives no runs, the primary readings become "not read: P-fixed's play is unavailable", and the inputs list shows the killed outcome.
- **`save_atomic`** removes its temporary file on any failure and keeps the earlier file.
- **The tests** exercise the real control flow and cover both reviewers' required cases, including the rerun exclusion and the empty case.

**2. Amendment 2: the reading rule is accurate; one claim is not.**

- `PREREGISTRATION.md:845` says every formal stage runs at the commit of this amendment and that commit is recorded in every start marker. The process condition at line 863 requires each stage's record to be committed and pushed before the next stage. Records live in the experiment folder, so HEAD advances after every stage and each marker will record a different commit. Only `project` will match. The code allows this, since `require_same_code` checks guarded paths only, but the sentence invites a literal check that will fail.
- The same paragraph's claim that 3385a8b differs from a8627ac only in the amendment text and the decision log is plausible but I could not verify it without git.
- Line 850 says no stage can start after the ceiling. Amendment 1 point 6 exempts `report`. A small inconsistency.

**Required change (one):** add a dated annotation to Amendment 2, committed and pushed before `project`, saying that "the commit of this amendment" means its guarded content, that HEAD advances between stages as records are committed, and that each marker records its own commit while the guards check the guarded paths against the earlier stage's commit. The amendment is already on `origin/roadmap` at 3385a8b, so editing it is not an option under rule 2, and adding the annotation after `project` would make every later stage refuse.

**Not required, your call:**
- Fold into the same annotation that the killed attempt's compute is charged by the refused rerun attempt, and that `report` is exempt from "no stage can start".
- `save_atomic` uses bare `os.replace`; the frame's `E.replace` retries the transient Windows refusal the suite has seen.
- Tightening `!= "used"` to `== "none"` at `scripts/e3c.py:748` sends an interrupted rerun setup to the frame's message instead of possibly reading a renamed partial as "killed before its first partial record". Nearly unreachable, one token.