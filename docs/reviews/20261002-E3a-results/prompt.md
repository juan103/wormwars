You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing experiment results in WormWars, an open-science project that evolves brains on the
C. elegans connectome. The repository is your working directory; read `AGENTS.md` (rules 3-5).

- **What to review:** `experiments/E3-ab-organism/E3a/RESULTS.md`, first draft (`roadmap` branch, commit
  f70c949).
- **Its pre-registration:** `experiments/E3-ab-organism/E3a/PREREGISTRATION.md` (bound at 989da99; its §13
  holds Amendment 1, added before any stage ran).
- **The records** are in the same folder: `evaluate.json`, `g0.json`, `g1.json`, `calibrate-e.json`,
  `census.json`, `train-*.json`, `champions-*.json`, the `.npz` counts and traces, and `summary.json`
  (from `scripts/e3a_summary.py`).
- **The runner:** `scripts/e3a.py`. The decisions are D165-D168 in `DECISIONS.md`.

**Please answer:**
1. A verdict: "publish as is", "fix" (list the fixes), or "revise".
2. Does every registered reading use the pre-registered rule and its fixed wording? Check each against
   the records: S2-a, S2-b, S2-c, Stage 3 and B-task.
3. Is every number in RESULTS.md traceable to a committed record, and correct? Name any that are not.
4. Does any descriptive claim go beyond the data? In particular:
   - "bistable, not a latch" read as a leaky gate rather than lost memory;
   - the memory-less high scorers;
   - the mean-nose results;
   - the comparison of the GA with random sampling.
5. Are the deviations complete and honestly stated? This includes running without a confirmation round
   after the code review's fixes.

Be concrete and brief. You are read-only: do not edit files.
