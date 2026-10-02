You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing an exploratory experiment plan in WormWars, an open-science project that evolves brains on
the C. elegans connectome. The repository is your working directory; read `AGENTS.md`.

- **What to review:** `docs/E3/E3b-0-PLAN.md` v1 (`roadmap` branch, commit f6d3532).
- **Its agreed design:** `docs/E3/E3b-DESIGN.md` v2. Your reviews and pins are in
  `docs/reviews/20261002-E3b-design-v2/` and D173.
- **The engine:** `wormwars/world.py`, `fields.py`, `config.py`, `wormwars/e3/`, `wormwars/e1/controllers.py`.

**Please answer:**
1. A verdict: "run", "fix then run" (list the fixes), or "revise".
2. Is every pin from D173, and from your design-v2 review, carried in? Name any that are not.
3. Check the numbers and rules that could make E3b-0 uninformative or misleading:
   - the update order;
   - occlusion;
   - the deposit rule and the polarity guide;
   - the "maze-ready" variants and their selection;
   - the search grids and selection rules;
   - the exit criteria and their thresholds;
   - the power criterion;
   - the failure branches.
4. Is it feasible in the engine and within 3 GPU-hours?

Be concrete and brief. You are read-only: do not edit files.
