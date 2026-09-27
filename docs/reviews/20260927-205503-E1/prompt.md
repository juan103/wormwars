You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Review: E1 navigation primitive, design v1

Roadmap v3 (`ROADMAP.md`, Track E, "E1 / 04a: navigation primitive") is delegated. Decisions
where Claude and both of you agree go ahead; disagreements go to the owner. Please review
`docs/E1/DESIGN.md` (branch `roadmap`, read-only). Nothing has been run.

**Useful context:**
- `experiments/02-screening/RESULTS.md` and `experiments/02b-champion-analysis/RESULTS.md`:
  why 02's champions circled;
- `wormwars/exp02/grid.py` (`task_config`), `wormwars/exp02/scripted.py` (K, M, S and tuning),
  `wormwars/world.py` and `wormwars/config.py` (food, odour, sensing);
- `configs/interface.yaml`;
- `docs/foundations/T0.md` (the declared tolerances).

**Please check:**
1. Does Task N test navigation, going somewhere specific, and not something circling or foraging
   can solve?
2. Are the positive controls (S, M) and the movement baselines right and sufficient?
3. Are the gate thresholds sensible, or should they come from a pilot?
4. Answer the design's open questions (1-6).
5. Does anything make E1 uninformative for E3, the A/B shuttle with trails?
6. What is missing, or over-built given the roadmap's tripwire (no new infrastructure beyond T0,
   T1 and minimal module save/load until 04b runs)?

Findings ranked **must change**, **should change**, **minor**. End with: "E1 design: proceed to
v2" or "rethink".
