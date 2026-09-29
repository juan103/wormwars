You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing, for the second time, a pre-registration for WormWars, an open-science project
that evolves brains on the C. elegans connectome. The repository is your working directory; read
`AGENTS.md` for its rules.

**What to review:** `experiments/E2-optimizer-screen/PREREGISTRATION.md`, now **v2**, for E2, "a
short optimizer screen" (02's GA against OpenAI-ES, random sampling as a floor, equal additional
simulator work, Task N, 8 runs per method), with the code it binds: `scripts/e2.py`,
`wormwars/e2/optimizers.py`, `wormwars/e2/loops.py`, and the tests `tests/test_e2_commands.py`,
`tests/test_e2_loops.py`, `tests/test_e2_optimizers.py`.

**Your v1 reviews** are archived verbatim in `docs/reviews/20260929-105911-E2-prereg/`: both of you
said "revise". **D120** in `DECISIONS.md` and **§14** of the pre-registration list how each point was
taken. The v1 commit was `12725de`; v2 is the current HEAD, so `git diff 12725de` (read-only, if
you can) or a direct reading shows the changes.

**Please check:**
1. Is each of your v1 must-fixes resolved, in the text and in the code, and tested? In particular:
   - "final" under every crash/kill combination (`require_earlier`, `rerun_plan`,
     `final_killed_record`, `rerun_used`);
   - the incomplete-ES outcome and the other terminal outcomes in §8;
   - the stopped extension's champions (`champion_over_both`, the `summary` passed to `train_batch`);
   - the per-arm partial record in the evaluation;
   - the exposure corrections in §11 and the moved projection seeds;
   - the budget labels.
2. Did any fix introduce a new problem? Check in particular:
   - the pilot's new tie order (middle setting first);
   - the retried atomic writes (`write_atomic`, `replace`);
   - the pairing check and per-run differences in `analyse`;
   - whether a killed-and-finalised record (built from a partial record) can mislead the evaluation or
     the guards (its `provenance_at_start` comes from the partial record or the marker).
3. Anything still missing before binding.

**Answer format:** a verdict first, one of "ready to bind", "revise" or "redesign"; then must-fix
items (numbered, each with file and line or section, and what to change), then suggestions, then
what you checked and found correct. Be concrete and brief. You are read-only: do not edit files or
run commands that change anything.
