You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing an experiment design in WormWars, an open-science project that evolves brains on the
C. elegans connectome. The repository is your working directory; read `AGENTS.md`.

- **What to review:** `docs/E3/E3b-DESIGN.md` v1 (`roadmap` branch, commit ea06ce4).
- **Its basis:**
  - `ROADMAP.md`, the "E3 / 04b" section (the trail table, the gate, the peer-signal controls);
  - `docs/E3/DESIGN.md` (E3's staging);
  - E3a's published results (`experiments/E3-ab-organism/E3a/RESULTS.md`, `summary.json`);
  - D156-D171 in `DECISIONS.md`.
- **The engine:** `wormwars/world.py`, `wormwars/fields.py`, `wormwars/config.py`, `wormwars/e3/`,
  `configs/interface.yaml`.

**Please answer:**
1. A verdict: "proceed" (to E3b-0's plan), "revise", or "rethink".
2. The design's seven open questions: give your answer to each, with reasons.
3. Anything that would make E3b-0 or E3b-1 uninformative, unfair to a control, infeasible in the engine,
   or too costly for about 30 GPU-hours. Check the engine where you can.
4. What E3b-0 must establish before E3b-1 is pre-registered.

Be concrete and brief. You are read-only: do not edit files.
