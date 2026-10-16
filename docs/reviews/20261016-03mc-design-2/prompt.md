You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Second design review, read-only, of a confirmatory experiment in this repository (commit 1673ad5, branch roadmap).

You reviewed design v1 of `experiments/03mc-p4-confirm/DESIGN.md` (commit 6e948d7) and answered "revise" (run
20261015-232952). Design v2 is in the same file; its §11 lists the changes, and DECISIONS.md D286 records what was
taken and measured. New since v1, all committed:
- `experiments/03mc-p4-confirm/power.py` and `power.json`: a simulation of the whole Holm procedure from 03m's data
  (it reads 03m's local per-genome arrays in `runs/p4m/`, which you can read; their hashes are in power.json);
- `wormwars/exp03/twin.py` (the two-row history probe) and `tests/test_exp03_twin.py`;
- `scripts/p4mc_equivalence.py` and `equivalence.json`: the two-row probe against 03m's one-row outputs on old
  inputs (03's genomes, 03m's 80-graph panel, three N2 conditions).

Please check:
1. Is each of your v1 findings fixed, correctly and without a new error?
2. power.py: is the model right, and are the reported probabilities what the code computes? In particular Q-A's
   regression and extrapolation, Q-D's posterior draws, Q-B's two-stage draw, and the Holm loop.
3. twin.py and its tests: is the probe equivalent to `measures.history` plus 03m's `history_full` (p4m.py), and
   are the declared tolerances in §5 justified by equivalence.json?
4. The questions in §10.
5. Anything that still blocks writing the pre-registration from this design.

Answer "ready for the pre-registration" or "revise", then numbered findings with file:line, evidence and a proposed
fix. Keep to what you verified; say what you could not check.
