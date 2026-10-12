You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Design review request: E4-D v1, a task where transfer is necessary (WormWars)

You are reviewing a design in the WormWars repository (your working directory), read-only.

**Context:** E4 (`docs/E4/E4-DESIGN.md`, design v3, agreed by both reviewers) asks whether two grafted navigation
modules, A and B, come to use information crossing between them through 32 optional cross-links. Its §7 asks for a
separate diagnostic task, E4-D, where transfer is necessary, with a hand-configured positive control, so that a null
in E4 can be read. Astra's "randomised B-mode choice" was preferred in v3.

**The design under review:** `docs/E4/E4-D-DESIGN.md` (v1). It proposes a decoy B: three marked dead ends (A, the
real B, a decoy B′); per episode a random draw makes one B candidate real; in mode B, B's noses read the sum of both
candidates' scents (uninformative), while A's noses read the real B's scent alone (the cue). A's motors are gated off
in mode B, so the cue reaches the body only through the cross-links. No trails.

**Useful code to check claims against:** `wormwars/e3/maze_world.py` (`_extra_signals`, the visit rule, scent),
`wormwars/e3/islands.py` (E4's maze family and placements), `wormwars/e3/organism.py` (`engineered_gated`,
`motor_edges`, `gate_spec`), `wormwars/brain.py` (`gate_outputs`), `wormwars/e4/` (E4's code), and D245-D248 in
`DECISIONS.md`.

**What I want:**
1. Is the decoy-B task a fair "transfer necessary" task? Name every path by which X0 (cross-links at 0) could
   still beat chance: B's own senses, history and memory in B's or the carrier's state, the latch, the walls'
   geometry, the decoy's placement, peers, anything in the engine.
2. Is switching A's nose channel by mode an acceptable engineered cue (declared as such), or should the cue be a
   separate input only A receives? What does each choice cost in what E4-D can conclude?
3. The placement constraints (§2) and the chance level: are they enough? What would you fix?
4. The feasibility check's criteria (§3): thresholds, block size, controls (cue reversal, shuffling, removal). Are
   they declared tightly enough to be run before E4's formal run without fishing?
5. The engine work and its tests (§4): anything missing for rule 7 and rule 9?
6. Anything that should change before this becomes E4-D's design v2 and then its feasibility code.

**The answer I want:** a verdict ("go to v2 with these changes", "revise", or "reject the task"), then numbered
findings with severity (critical / important / minor) and the fix. Terse; do not restate the design.
