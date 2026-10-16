You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Confirmation pass, read-only, on design v2.1 of a confirmatory experiment in this repository (commit b8ed3ae, branch
roadmap).

You reviewed design v2 of `experiments/03mc-p4-confirm/DESIGN.md` at 1673ad5 (run 20261016-001758): Fable answered
"ready for the pre-registration" with three things to do first; Astra answered "revise". Design v2.1 is in the same
file; §11 "From v2" lists the changes and DECISIONS.md D287 records each finding and two corrections to D286. The diff
is `git diff 1673ad5 b8ed3ae`. New or changed:
- `scripts/p4mc_equivalence.py` (the pre-run check, tolerances in code) and its run `equivalence-check.json`;
- `experiments/03mc-p4-confirm/power.py` and `power.json` (joint draws of N2's quantities, Q-A posterior, Q-C
  modelled, a Student-t sensitivity, Q-D by tick);
- `tests/test_exp03_twin.py` (a pre-tanh reference test);
- `wormwars/exp03/mc.py` and `tests/test_exp03_mc.py` (statistics, matched controls, the freshness audit), and two
  new instances in `scripts/exp03.py` (code begun for the pre-registration; it will get its own code review).

Please check:
1. Is each of your v2 findings fixed, correctly and without a new error?
2. Do `equivalence-check.json` and `power.json` support every number the design quotes from them?
3. Anything that still blocks writing the pre-registration from this design.

Answer "ready for the pre-registration" or "revise", then numbered findings with file:line, evidence and a proposed
fix. Keep to what you verified; say what you could not check. Please do not run GPU work.
