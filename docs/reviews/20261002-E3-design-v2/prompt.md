You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a revised experiment design in WormWars, an open-science project that evolves brains on
the C. elegans connectome. The repository is your working directory; read `AGENTS.md`.

- **What to review:** `docs/E3/DESIGN.md` v2 (`roadmap` branch, latest commit). Its last section maps each
  v1 must-fix to its change.
- **The v1 reviews** (Astra 6 and Fable 5.1, both "revise"): `docs/reviews/20261002-E3-design/`; D156 in
  `DECISIONS.md`.
- **Code:** `wormwars/world.py`, `wormwars/graft.py`, `wormwars/e4s/`, `wormwars/brain.py`; E4s's results in
  `experiments/E4s-stereo-module/`.

**Please answer:**
1. A verdict: "proceed to pre-registration" or "revise".
2. Is each v1 must-fix resolved? Name any that are not.
3. Did v2 introduce new problems? In particular check the latch's numbers (levels, w_s = 3, the start cue),
   the gate's arithmetic and component thresholds, the stage gates, and the budget.
4. What the pre-registration must pin that v2 leaves open.

Be concrete and brief. You are read-only: do not edit files.
