# M6 step 2: design note (round 1)

The owner ordered (D379): step 1 (done, D381), then a test of whether the evolved champions' fading history effect
matters for their foraging, designed and costed first, then stop. The design note is
`docs/memory/M6-STEP2-DESIGN.md` (draft 1, also `draft1.md` here). Context: `docs/memory/M6-0-RESULTS.md` (the
champions' history effect: a fading transient, about six times drift's), `experiments/02b-champion-analysis/`
(analyse.py: `rollout` on `CRIT_WORLDS`, `stage_criticality`, `drifted`), `wormwars/brain.py` (tau's role),
`scripts/memory_m6/m6_0.py` (genomes, drift seeds, persistence measures), `docs/memory/M6-OPTIONS.md` (option 5,
Astra's causal-study idea). A disclosed one-champion timing run is in the note.

Read-only; proportionate (the owner was told about 1 to 5 CPU hours for this step):
1. Is the time-scale intervention (tau x k for every neuron; fixed points unchanged), with its controls, an honest
   test of whether the history effect matters for foraging? What would you change or add?
2. Controls: g00 and drift under the same k, a dose-response over the champions' history-effect size, k = 2 for
   symmetry, validation on the probe. Right ones? Missing ones?
3. The primary contrast and its wording: right? What should be fixed in the plan?
4. Anything not worth its cost, or a better intervention at similar cost?
5. Verdict: proceed to a plan (with fixes), or revise the design.
