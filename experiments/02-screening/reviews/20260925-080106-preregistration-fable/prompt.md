You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Adversarial review of experiment 02's pre-registration, in the WormWars repository (branch
exp02-screening, commit 225e8f8). You reviewed its design v1, v2 and the implementation plan earlier
tonight; much changed since. The evolution runs started at 06:25 from commit 225e8f8 and take about
7 hours. No probes or analysis have run, and no N2 result has been read. Changes to probes and
analysis are still cheap. A change to evolution would mean rerunning.

Read `experiments/02-screening/PREREGISTRATION.md` first (binding), then `DECISIONS.md` D034-D040,
`experiments/02-screening/exploration/README.md`, and the reviews already given in
`experiments/02-screening/reviews/` (Astra 6's go/no-go, pre-registration review, and recheck; do not
repeat its points unless you think a fix is wrong). Code: `wormwars/exp02/report.py`,
`wormwars/exp02/analysis.py`, `wormwars/exp02/probes.py`, `wormwars/world.py` (`_sensor_signals`),
`scripts/exp02.py` (`cmd_probes`, `cmd_report`, `cmd_validate_probes`), and
`experiments/02-screening/probe_validation.json`.

Questions:
1. Is the primary outcome (the N2 - SH contrast in bilateral-mean dependence, T0-M0, generation 39)
   the right one, given the disclosed N2 measurement and the failed feasibility gate? Is its verdict
   rule sound? What would you change before any probe runs?
2. Anything in the probes or analysis that would mislead: estimands, the bilateral-mean probe as
   implemented, normalisation, the bootstrap, tripwires?
3. Anything about the running evolution that makes the results uninterpretable, so that it should
   be stopped?
4. What have we still not seen: a failure mode nobody has named yet?

Numbered points, MAJOR or MINOR, concrete, with file:line where you can. Be brief about what is fine.
