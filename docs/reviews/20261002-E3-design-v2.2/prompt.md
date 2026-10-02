You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a revised experiment design in WormWars, an open-science project that evolves brains on
the C. elegans connectome. The repository is your working directory; read `AGENTS.md`.

- **What to review:** `docs/E3/DESIGN.md` v2.2 (`roadmap` branch, commit 0794db6). Its "Changes from v2.1" section maps
  each v2.1 review item to its change.
- **The v2.1 reviews** (both "revise", text only):
  `docs/reviews/20261002-E3-design-v2.1/`; D160 in `DECISIONS.md`.
- **New checks:** `scripts/e3_geometry_check.py` and its output, `docs/E3/geometry-check.json`.
- **E4s-1's measured training batches:** `experiments/E4s-stereo-module/E4s-1/train-*.json` (`seconds`,
  `composition`, `registered`).
- **Code:** `wormwars/world.py`, `wormwars/graft.py`, `wormwars/e4s/`, `wormwars/brain.py`.

**Please answer:**
1. A verdict: "proceed to pre-registration" or "revise".
2. Is each v2.1 item resolved? Name any that are not.
3. Did v2.2 introduce new problems? In particular check:
   - the no-latch control and the q-zero ablation;
   - the dynamical and memory classes, the hold, release and clamp tests on a champion's own states;
   - the selector's initial distribution near the ungated pair;
   - B-task's free parameters and reading;
   - the Euclidean spawn cap and the geometry script;
   - the reduction order.
4. What the pre-registration must pin that v2.2 leaves open. Keep this list to what changes outcomes.

Be concrete and brief. You are read-only: do not edit files.
