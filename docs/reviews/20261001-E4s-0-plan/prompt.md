You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing an exploratory experiment plan in WormWars, an open-science project that evolves
brains on the C. elegans connectome. The repository is your working directory; read `AGENTS.md`.

**What to review:** `docs/E4s/E4s-0-PLAN.md` (v1, on the `roadmap` branch). It pins the script details
of E4s-0, the diagnostics stage of the adopted plan `docs/E4s/ROADMAP-PROPOSAL.md` v2.1 (D144; its
reviews are in `docs/reviews/20261001-roadmap-proposal*/`). Nothing has run.

Relevant code: `wormwars/world.py` (`tick`, `_read_motors`, `_build_current`), `wormwars/graft.py`,
`wormwars/brain.py`, `wormwars/e04a/evolve.py`, `scripts/e2d.py` (`world_ci`, `classify`, the stage
frame), `scripts/e4s_gain_probe.py`, `configs/interface.yaml`.

**Please answer:**
1. A verdict: "run as planned", "revise" or "rethink".
2. Must-fix items (numbered; each with the section and the change). In particular check:
   - the residual wrapper and its k = 0 check;
   - the ladder's wiring and sign, the carrier's bias arithmetic, the stopping rule;
   - the simulated-population statistic against E4s-1's outcome table;
   - the world-id ranges, the budget, and the shrink order;
   - whether the tests would catch the likely bugs.
3. Suggestions (brief).

Be concrete and brief. You are read-only: do not edit files.
