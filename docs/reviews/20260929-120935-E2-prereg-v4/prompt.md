You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing, for the fourth time, a pre-registration for WormWars, an open-science project
that evolves brains on the C. elegans connectome. The repository is your working directory; read
`AGENTS.md` for its rules.

**What to review:** `experiments/E2-optimizer-screen/PREREGISTRATION.md`, now **v4**, for E2, "a
short optimizer screen" (02's GA against OpenAI-ES, random sampling as a floor, equal additional
simulator work, Task N, 8 runs per method), with the code it binds: `scripts/e2.py`,
`wormwars/e2/optimizers.py`, `wormwars/e2/loops.py`, and the tests `tests/test_e2_commands.py`,
`tests/test_e2_loops.py`, `tests/test_e2_optimizers.py`.

**Your v1, v2 and v3 reviews** are archived verbatim in `docs/reviews/20260929-105911-E2-prereg/`, `docs/reviews/20260929-113044-E2-prereg-v2/` and `docs/reviews/20260929-115339-E2-prereg-v3/`: each time, both of you
said "revise". **D120-D122** in `DECISIONS.md` and **§14-§16** of the pre-registration list how each point was
taken. The v3 commit was `31beeda`; v4 is the current HEAD (`1e4b7f5`), so `git diff 31beeda` (read-only, if
you can) or a direct reading shows the changes.

**Please check:**
1. Is each of your v3 points resolved, in the text and the code, and tested? In particular §6's
   admission check (Fable's option (a)), the skip record through the guards (`require_earlier`,
   `cmd_extend`), the plain-run refusal when a start marker exists (`run_stage`), §10's "final",
   and §11.
2. Did any v4 change introduce a new problem?
3. Is anything still missing before binding? If not, say "ready to bind".

**Answer format:** a verdict first, one of "ready to bind", "revise" or "redesign"; then must-fix
items (numbered, each with file and line or section, and what to change), then suggestions, then
what you checked and found correct. Be concrete and brief. You are read-only: do not edit files or
run commands that change anything.
