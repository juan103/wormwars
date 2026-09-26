You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Confirmation pass: WormWars 03r pre-registration v2

You reviewed v1 of `experiments/03r-replication/PREREGISTRATION.md`. Your review is in
`docs/reviews/20260926-22590*-03r-prereg/`. The draft has been revised: see §12 of the file and
`DECISIONS.md` D060. The repository is at commit 0d2e7fe or later, on branch `roadmap`, and you
are read-only.

**The code changes since your review:**
- `wormwars/exp03/report.py`: `single_signal` gates, `replication_primary`, and the
  per-ensemble `min_graphs`;
- `scripts/exp03.py`: the `INSTANCES` fields `max_hours`, `min_graphs`,
  `fresh_secondary_permutation` and `pin_connectome`; `cap_hours`,
  `secondary_permutation_seed`, `accounting` and `side_by_side`; `cmd_run` and `cmd_report`;
- `experiments/03-generation0/supplement.py`, rewritten;
- `experiments/03r-replication/power.py`, with prior and noise sensitivity;
- `tests/test_exp03r_replication.py`, with 18 tests.

**Please check:**
1. Is each of your must-fix and should-fix findings resolved in both the text and the code?
2. Did the revision introduce any new error or inconsistency?
3. Is there anything that must still change before this becomes binding and the run starts?

Be brief: list any remaining must-fix items first (or "none"), then should-fix and minor ones,
then a one-line verdict: ready to bind, or not.
