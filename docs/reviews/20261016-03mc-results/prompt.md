You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing the results of a pre-registered, confirmatory computational study in the repository you can read
(read-only). Please review `experiments/03mc-p4-confirm/RESULTS.md` (commit 3e65ef6 on branch `roadmap`) before it is
published on the main branch. It will be published whatever the outcome; the question is whether it reports the
outcome correctly.

Context:
- 03mc tests four exploratory leads from 03m (`experiments/03m-p4-mechanism/`) on fresh draws. Its rules are
  `experiments/03mc-p4-confirm/PREREGISTRATION.md`, bound at 4dff311 (`bound.json`); you reviewed it in four rounds.
- The build, pre-run check and run are recorded in `DECISIONS.md` D295-D297; the report D298, the draft D299.
- Every number in RESULTS.md should come from `experiments/03mc-p4-confirm/report.json`, written by
  `scripts/p4mc.py report` (statistics in `wormwars/exp03/mc.py` and `wormwars/exp03/mc_report.py`) from the committed
  `measurements.json`. The per-genome arrays are local and not available to you; the hashes are in measurements.json.
- Compute: `runs/p4mc/compute.json` is local and gitignored; RESULTS cites 7.73 of 10 hours from it.

Please check, and say what you checked and what you could not:
1. **Fidelity to the pre-registration:** are the registered sentences quoted exactly and used where §6-§7 say they
   apply (including Q-A's conditional second sentence, the Holm reporting, the secondaries' verdict wording)? Is
   anything registered missing from RESULTS (§6's "reported for every question", §7's descriptive list)?
2. **Every number against report.json:** p values, counts, estimates, intervals and which interval level (90% or
   95%) each is. Flag any rounding that changes meaning.
3. **Overclaiming or underclaiming:** the "What this is and is not" and "What follows" sections, the descriptive
   readings labelled as such (AIY's ΔP4 interval excluding zero, the double deletion's ΔP4, the comparison of 0.875
   with the ensembles' means), and anything that reads as a mechanism or a claim §7 lists as "not claimed".
4. **The statistics as computed:** anything in mc.py / mc_report.py that makes a reported value not what the
   pre-registration defines (for example the lead used in Q-A's second sentence, Q-D's "other ticks", the share kept by
   the permutations, the retention eligibility).
5. Anything else a careful outside reader would trip on.

Answer with a verdict first: "publish", "fix then publish" (list the fixes), or "do not publish" (why). Then numbered
findings, each with the file and line, and how severe it is. Do not run GPU work; do not edit files.
