You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Adversarial review of an experiment design before implementation, WormWars repository (branch
roadmap, HEAD; local, not public). Read `experiments/03-generation0/DESIGN.md` (experiment 03,
generation-0 structure and task specificity) and its measured `timing.json`. Context: `ROADMAP.md`
(v2.2, item 2), `DECISIONS.md` D041-D049, experiment 02's results
(`experiments/02-screening/RESULTS.md`) and 02b's (`experiments/02b-champion-analysis/RESULTS.md`).
Code: `wormwars/connectome/graphs.py` (the current shuffle sampler), `wormwars/exp02/remaps.py`
(D036's matching), `wormwars/exp02/structure.py`, `wormwars/exp02/probes.py`.

No N2 brain has been run for 03; nothing about N2 is measured before its pre-registration.

Questions:
1. Are the four ensembles the right controls, and are their samplers sound (degree preservation,
   the routing constraint, mirror-pair swaps with partial symmetry, class preservation, mixing and
   diversity checks)? Anything that would make an ensemble fail silently or be unsampleable?
2. The control task C (food-free locomotion, coverage score) and the argument against food
   avoidance: sound? Is there a better matched non-worm-like control?
3. Signals (a)-(e), the gate (percentile and mean claims, "stands out" / "compatible" /
   inconclusive) and the unit of analysis: flaws, overlaps, missing signals, multiplicity?
4. The budget and the 03a consequence (measured wide-batch throughput is about 1.8x, not 5x).
5. What must the pre-registration fix that this design leaves open?

Numbered points, MAJOR or MINOR, concrete, with file:line. Be brief about what is fine.
