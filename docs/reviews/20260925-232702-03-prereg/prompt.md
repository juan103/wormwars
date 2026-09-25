You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Adversarial review of experiment 03's pre-registration before any N2 measurement, WormWars
repository (branch roadmap, HEAD; local). Read `experiments/03-generation0/PREREGISTRATION.md`
(binding), then check it against the code that will run: `scripts/exp03.py` (measure_graph,
run_order, cmd_run, cmd_report), `wormwars/exp03/report.py`, `verdict.py`, `measures.py`,
`samplers.py`, and the committed inputs (`ensembles.json`, `pilot.json`, `graphs_manifest.json`,
`configs/mirror_pairs.yaml`). History: `DESIGN.md` (v3.1) and `DECISIONS.md` D050-D053; your earlier
reviews are in `docs/reviews/`.

Questions:
1. Does the code compute exactly what sections 4-6 say (signals, SEs, latent SD and margins,
   rank tests, intersection-union then Holm, effect interval, verdicts, completeness)? Any bug
   that would change a verdict?
2. Is exchangeability of N2 with each ensemble actually delivered by the procedure (seeds,
   calibration, sample sizes, worlds, order)? Any residual asymmetry?
3. Loopholes or forking paths left open; anything a motivated analyst could still choose.
4. Is the power section honest, and is the run worth its about 20 GPU-hours as registered?
5. Anything that must change before the run starts.

Numbered points, MAJOR or MINOR, concrete, with file:line. Be brief about what is fine.
