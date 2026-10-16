You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Design review, read-only, of a confirmatory experiment in this repository (commit 6e948d7, branch roadmap).

The file is `experiments/03mc-p4-confirm/DESIGN.md` (design v1, nothing run). It proposes a confirmatory test of the
leads from the exploratory study 03m (`experiments/03m-p4-mechanism/`: PLAN.md, RESULTS.md with its Corrections, and
the committed JSON outputs). You reviewed 03m's results on 2026-09-29 and each proposed what a confirmatory follow-up
should register (`docs/reviews/20260929-061029-03m-results/`); the design says how it takes those up. The code it
would reuse is `scripts/p4m.py`, `scripts/exp03.py` (instances "03" and "03r"), `wormwars/exp03/measures.py`
(`history`), `wormwars/deletion.py` and `wormwars/brain.py`. 03r's pre-registration
(`experiments/03r-replication/PREREGISTRATION.md`) is the model for the rank tests and the single-signal rule.
DECISIONS.md D285 records the owner's go and the one timing measured.

Please check, against the files:
1. Is each primary question (Q-A to Q-D) a fair, well-posed confirmatory test of what 03m found? Are the
   predictions, tests and outcome wordings right, and is anything claimed that the test cannot show?
2. The numbers the design quotes from 03m (gap-junction changes, deletion cuts, permutation counts, decay ranks,
   the 94 of 95 pairs within 0.02). Are they right?
3. The statistics: Holm over Q-A to Q-D; intersection-union rank tests at 128 graphs per ensemble; Q-B's bootstrap
   conjunction (cut > 40% and |dP4| < 0.02, TOST); the pass-probability sketch. Is anything wrong or underpowered?
4. The procedure: the two-row probe (rising and falling histories as two rows sharing each strain's matrices) and
   its equivalence check at a relative 1e-5; fresh seeds and collision checks; order under the cap; the 10 GPU-hour
   cap.
5. The five questions in §9.
6. Anything missing that a reader would need to trust either outcome.

Answer "ready for the pre-registration" or "revise", then numbered findings with file:line, evidence and a proposed
fix. Keep to what you verified; say what you could not check.
