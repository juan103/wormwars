You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a revised experiment design in WormWars, an open-science project that evolves brains on
the C. elegans connectome. The repository is your working directory; read `AGENTS.md`.

This is a confirmation round.
- **What to review:** `docs/E3/E3b-DESIGN.md` v2 (`roadmap` branch, commit 0e33f23). Its last section maps
  each v1 review item to its change.
- **Your reviews of v1:** `docs/reviews/20261002-E3b-design/`; D172 in `DECISIONS.md`.
- **The new bounded literature check:** `docs/E3/E3b-LITERATURE.md`. Each source's verification level is
  stated.
- **The engine:** `wormwars/world.py`, `fields.py`, `config.py`, `wormwars/e3/`.

**Please answer:**
1. A verdict: "proceed to E3b-0's plan" or "revise". Reserve "revise" for problems that would make E3b-0
   uninformative or infeasible and cannot be fixed in its plan.
2. Is each v1 item resolved? Name any that are not.
3. Check the literature note: are its readings of the sources fair, and does it overclaim anything?
4. Any new problem in v2: the engine changes, the controls, the exit criteria, and the E3b-1 sketch.
5. What E3b-0's plan must pin.

Be concrete and brief. You are read-only: do not edit files.
