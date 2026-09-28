You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Confirmation request: 04a's pre-registration, draft v4 (commit 1653809)

You reviewed v3 (`082210e`; `docs/reviews/20260928-224400-04a-prereg-v3/`) and said "revise",
narrowly. This is the confirmation of the diff you asked for, not a full round.

The diff since your review: `git diff 082210e 1653809` (ignoring D106's unrelated files). Key places:
- `scripts/e04a.py`: `rerun_plan`, `reconcile_kill`, `apply_rerun` (replacing `archive_attempt`), and
  where the three commands call them; `REGISTERED["rerun_kill_tail_seconds"]`;
- `tests/test_e04a_commands.py`: the kill-accounting tests (`_killed_batch_a`, charged once, refusal
  at the cap without using the rerun), the over-limit test requiring fewer generations, and the
  stopped-projection and stopped-evaluation rerun tests;
- `experiments/04a-navigation-primitive/PREREGISTRATION.md`: §6's expectation paragraph, §8's rerun
  rule, §9's compute line, and §13 (changes from v3);
- `DECISIONS.md` D107.

Please check that each of your v3 must-fixes is fixed in the code, and that the diff introduces no new
problem. You may read any file; you cannot run anything.

End with one line: **"04a pre-registration: ready to bind"** or **"04a pre-registration: revise"**.
