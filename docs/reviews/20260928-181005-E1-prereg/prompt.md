You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a pre-registration in the WormWars repository (your working directory, branch `roadmap`, HEAD). You reviewed and agreed E1's design earlier (docs/E1/DESIGN.md v2.1; your reviews under docs/reviews/*-E1/ and *-E1b/, DECISIONS D077, D078). T1 since found batch-composition effects on CUDA (docs/foundations/T1.md §7, D092).

Read:
- experiments/E1-navigation/PREREGISTRATION.md (the draft to review);
- scripts/e1.py (the runner; REGISTERED holds every number; pilot writes the freeze by rule; gate runs once);
- the Task N implementation: wormwars/world.py (task "navigate": _build_targets, target_field, _advance_targets, target_events, the sensing changes), wormwars/evo/rollout.py (score selector, events), wormwars/exp02/scripted.py (collision inputs, command), wormwars/e1/task.py, wormwars/e1/controllers.py;
- tests: tests/test_e1_task.py, tests/test_e1_script.py.

Please answer:
1. Does the implementation match the agreed design (Task N mechanics, sensing-only target, energy off, pairing, score, event table, controls, oracle privilege)? Any defect, with file:line?
2. Are the registered numbers sensible and fixed before data (σ rule, floor 5%, share 90%, fallback; grids; the navigator choice; the gate's reliability 80%/≥2, baseline margin 0.5, cue drop ≥50% of the real mean, bootstrap bound; 1 024 gate worlds; cap 8 GPU-hours)? Is anything left to the pilot that should be fixed now, or fixed now that the design left to the pilot for good reason?
3. §7 discloses that a debug run computed the σ measure on 32 pilot worlds before registration (σ=6 gives 0.875 < 0.90, so the fallback σ=6 "flagged" will likely apply). Is the handling honest and sufficient? Should the rule be kept as is (my position), or is there a principled change that is not data-driven?
4. Can the pilot or gate be gamed or silently fail (freeze checks, gate-once, provenance, cap, smoke isolation)?
5. Does T1's composition finding matter here (scripted controllers have no neural batch; generation-0 brains run as 256 strains in one chunk)?

Finish with one line: "E1 pre-registration: ready to bind", or "E1 pre-registration: revise" (list must-fix items).
