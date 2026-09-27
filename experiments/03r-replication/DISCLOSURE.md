# 03r: public disclosure notice

**Dated 2026-09-27.** This notice sits beside the bound pre-registration
([`PREREGISTRATION.md`](PREREGISTRATION.md)) and does not change it.

**Binding:**
- The pre-registration was bound locally at commit `7c146fc`.
- Every measurement of the formal run records that commit in its provenance, with `code_dirty:
  false`.
- **The pre-registration, code and configs are unchanged since.** `git diff 7c146fc -- experiments/03r-replication/PREREGISTRATION.md wormwars scripts configs`
  shows only one comment edit, to a docstring in `wormwars/exp02/structure.py` that 03r does not
  execute.
- **One registered commitment is amended:** the README sentence that §10 binds ("a full
  replication was run before publishing"). D063 records the new wording. It will be reported as
  a deviation in 03r's results.

**Public disclosure came after measurement began:**
- The run started from `7c146fc`, committed 2026-09-26 23:43 +02:00. Its first measurement
  was saved 2026-09-26 23:45 +02:00.
- This branch, with the pre-registration, was first pushed to GitHub on 2026-09-27, while the run
  was in progress. GitHub's receipt time shows only when the text became public. It is not proof
  of registration before the run.

**State shortly before disclosure** (checked 2026-09-27 16:16 +02:00; GitHub records the push
time itself):
- 528 of 773 graphs measured;
- **N2 and its variants not measured.** They run last.

**What had been inspected:**
- **Before binding:** one preflight measurement of SH-1010000, not saved, as disclosed in §1 of
  the pre-registration.
- **During the run:** only operational information:
  - the provenance fields of the first saved measurement;
  - the number of files saved;
  - the per-graph run times;
  - the name of the latest file.
- The reviewers, reviewing the push, sampled provenance lines and counted files.
- **No signal value from the formal run has been inspected since binding.** The only 03r signal
  value seen is the preflight's P4 (0.756) for SH-1010000, before binding and disclosed in the
  pre-registration (Astra).

**What else is public on this branch, and why.** 03's first-run results are readable on this
branch before 03r finishes (D063). The owner's earlier decision (D059) was a replication before
anything from 03 was published. D063 records that the owner knowingly relaxed it, to get the
public timestamp. 03 and 03r reach main together, reported by the pre-registered rule whatever
the outcome.
