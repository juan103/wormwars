You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Review of an implementation plan, before it is built.

The working directory is the WormWars repository. Read:
- `experiments/02-screening/DESIGN.md` (v2): the design this plan implements. You reviewed v1.
- `docs/superpowers/plans/2026-09-25-exp02-screening.md`: the plan, with the code for each task.

Check the plan's code against the real code it modifies: `wormwars/world.py`, `wormwars/brain.py`,
`wormwars/config.py`, `wormwars/interface.py`, `wormwars/evo/rollout.py`, `wormwars/evo/evolve.py`,
`wormwars/evo/genomes.py`, `wormwars/calibration.py`.

What I want:
1. **Bugs in the plan's code** that tests would not catch, or would catch only late. For example:
   wrong tensor shapes or axes, off-by-one generation indices, seeds that are not crossed as
   claimed, defaults that are not bit-identical, statistics that do not compute what the design
   says (in particular the paired bootstrap, the interaction, the tripwires and the integrator
   comparison), and resume or budget logic that can lose or duplicate runs.
2. **Places where the plan does not implement the design,** or implements it differently without
   saying so.
3. **Anything that would invalidate the screening's results** and is cheap to fix now.

Numbered points, each marked MAJOR or MINOR, with the file and task. Check the code rather than
assume. If a task is fine, say so in one line.
