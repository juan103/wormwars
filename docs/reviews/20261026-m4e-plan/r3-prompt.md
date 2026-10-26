# M4e plan and code, round 3

Your round-2 answers are in `docs/reviews/20261026-m4e-plan/r2-{fable,astra}.md` (Fable "agree" with text fixes,
Astra "revise"). Draft 3 is `docs/memory/M4E-PLAN.md`. Every finding was taken:
- the dose slope's existence rule corrected: no slope only with no switch, or every switch at the largest or every one
  at the smallest S2 (Astra's interior-singleton counterexample is now a test, β ≈ 0.4646);
- the tables read the panels through the reader's validated counting and use its global audit choice
  (`m4e_read.classes`, tested under a failed audit); the per-genome predictor is saved per host, draw, arm and genome
  with the class the reading uses;
- the audit rationale softened to an expectation; each arm's actual audited fading count reported
  (`audited_fading_per_arm`); the 0.0037 bound stated as enough at 0.004, not at 0.001;
- the stale sign and bootstrap seeds in the plan's fixed sections corrected; the block range ends at 20261499;
- `check_skips` tested (with a sabotage); the batched replay test now uses 128 genomes, the production chunk, checking
  two rows; exactness claimed for those compositions;
- the two dose sabotages now fail by the tests' own checks; one more wrong-reason failure found and fixed (the
  interior-singleton test asserts before unpacking): 25 tests pass, 30 of 30 sabotages fail, none through an
  exception other than the tests' own;
- the audit's extra cost restated as 4 to 5 hours (about 33 to 34 in all).
The tables script ran again on the 16-genome smoke (`runs/m4e-smoke16-tables-log.txt`).

Read-only. Check the fixes and anything new. Verdict: agree / revise.
