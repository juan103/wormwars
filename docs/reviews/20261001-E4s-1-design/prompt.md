You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing an experiment design in WormWars, an open-science project that evolves brains on the
C. elegans connectome. The repository is your working directory; read `AGENTS.md`.

**What to review:** `docs/E4s/E4s-1-DESIGN.md` (v1, on the `roadmap` branch).
- It implements E4s-1 of the adopted plan (`docs/E4s/ROADMAP-PROPOSAL.md` v2.1, D144) after E4s-0's
  results (`experiments/E4s-stereo-module/E4s-0/RESULTS.md`, corrected per both reviewers, D147;
  numbers in `summary.json` and the stage records).
- Code to check against: `wormwars/graft.py`, `wormwars/e4s/`, `wormwars/e04a/evolve.py`,
  `scripts/e4s0.py`, `scripts/e2d.py`.

**Please answer:**
1. A verdict: "proceed to pre-registration", "revise" or "rethink".
2. Must-fix items (numbered; section and change). In particular check:
   - whether the design's comparisons answer its questions given E4s-0's findings: the turn offset,
     the ceiling near 5, generation-0 bests at the plateau's level, the mutational load, and R
     varying only signs;
   - the class table and its reading;
   - the gates;
   - the budget.
3. Answers to the design's four questions.

Be concrete and brief. You are read-only: do not edit files.
