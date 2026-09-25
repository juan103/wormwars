You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Adversarial review of a pre-registration, before any N2 run. You gave the go/no-go review an hour
ago (conditional GO, 11 points). The branch `exp02-screening` (local, commit af58faf and the
uncommitted `experiments/02-screening/PREREGISTRATION.md`) now claims to implement all of it.

Read `experiments/02-screening/PREREGISTRATION.md` first, then check it against the code and data:
`wormwars/exp02/report.py`, `wormwars/exp02/analysis.py`, `wormwars/exp02/probes.py`,
`wormwars/world.py` (`_sensor_signals`: the "mean" and "swapped" probes), `scripts/exp02.py`
(`cmd_probes`, `cmd_validate_probes`, `cmd_extend`, `cmd_run`), `wormwars/exp02/grid.py`,
`experiments/02-screening/probe_validation.json`, `DECISIONS.md` D038-D039, and
`experiments/02-screening/exploration/`.

Questions:
1. Does the pre-registration faithfully implement each of your 11 points? Name any it misses or
   gets wrong.
2. Does the code compute exactly what section 4 says (estimand, SH weighting, bootstrap nesting,
   verdict rule)? Any bug that would change the primary verdict?
3. Forking paths or loopholes: anything a motivated analyst could still choose after seeing the
   data? Is the verdict rule sound (e.g. the "challenged" branches, the 0.10 threshold)?
4. Anything that should stop the run from starting now?

Numbered points, MAJOR or MINOR, concrete, with file:line where you can. Be brief about what is fine.
