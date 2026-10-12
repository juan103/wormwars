You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Design review request: E4-D v2 (WormWars), after your reviews of v1

You are reviewing a design in the WormWars repository (your working directory), read-only.

E4-D is E4's diagnostic task, where information must cross from module A to module B, with a hand-configured
positive control (E4 design v3 §7, `docs/E4/E4-DESIGN.md`). You reviewed v1 (`docs/reviews/20261012-E4-D-design/`,
your own answers are there). **v2 is `docs/E4/E4-D-DESIGN.md`;** D249 in `DECISIONS.md` lists what changed. In short:
fresh single-choice trials of one wey, in mode B from the first substep, scored at the first candidate entered, both
assignments played from identical starts, relays silent, a widened scent (declared), a start-cell rule, two control
wirings and four weights chosen on a calibration block, and declared pass criteria.

Code to check claims against: `wormwars/e3/maze_world.py`, `wormwars/e3/islands.py`, `wormwars/e3/organism.py`,
`wormwars/brain.py` (`gate_outputs`, `substep_hook`), `wormwars/e4/`.

**What I want:**
1. Does the single-choice trial close every path by which X0 could beat one half of entries? Is §3's exactness
   argument right in this engine (including anything in the world that reads the assignment)?
2. The widened scent and the start-cell rule (§2): acceptable, and right as specified? Will qualifying start cells
   exist on most of E4's island mazes?
3. The control and its selection, the blocks, the pass criteria and the failure rule (§4): tight enough to run
   before E4's formal run without fishing?
4. The engine work and tests (§6): anything missing?
5. Anything else before the feasibility code is written.

**The answer I want:** a verdict ("write the code", "revise", or "reject"), then numbered findings with severity
(critical / important / minor) and the fix. Terse; do not restate the design.
