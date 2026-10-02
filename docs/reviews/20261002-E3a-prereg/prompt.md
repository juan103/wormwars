You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a pre-registration draft in WormWars, an open-science project that evolves brains on the
C. elegans connectome. The repository is your working directory; read `AGENTS.md` (rule 2 on
pre-registration).

- **What to review:** `experiments/E3-ab-organism/E3a/PREREGISTRATION.md`, first draft (`roadmap` branch,
  commit a7177e7). Once bound, its text is never changed.
- **Its design:** `docs/E3/DESIGN.md` v2.4, agreed by both of you in the last round
  (`docs/reviews/20261002-E3-design-v2.4/`; D163). D163 lists the pins you asked to be carried in.
- **The precedent it follows:** `experiments/E4s-stereo-module/E4s-1/PREREGISTRATION.md`.
- **Code it relies on:** `wormwars/world.py`, `wormwars/graft.py`, `wormwars/e4s/`, `wormwars/e1/`,
  `wormwars/e04a/evolve.py`, `scripts/e2d.py`, `experiments/E1-navigation/freeze.json`.

**Please answer:**
1. A verdict: "bind as is", "bind after fixes" (list them), or "revise".
2. Is every pin from D163 carried in? Name any that are not.
3. Check the departures in §12, in particular the S-shuttle gain (8192, from `freeze.json`) and S-oracle's
   geometric maximum and 0.6 threshold.
4. Anything that would change an outcome, or that the implementation cannot do as written:
   - the gates;
   - the assays and their tolerances;
   - the samplers and ties;
   - the seeds and world blocks;
   - the readings and their wording;
   - admission and reductions;
   - the tests.

Be concrete and brief. You are read-only: do not edit files.
