You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a revised experiment design in WormWars, an open-science project that evolves brains on
the C. elegans connectome. The repository is your working directory; read `AGENTS.md`.

- **What to review:** `docs/E3/DESIGN.md` v2.3 (`roadmap` branch, commit 9dc604e). Its "Changes from v2.2" section maps
  each v2.2 review item to its change.
- **The v2.2 reviews** (Fable: "proceed" with four fixes; Astra: "revise"):
  `docs/reviews/20261002-E3-design-v2.2/`; D161 in `DECISIONS.md`.
- **New checks:** `scripts/e3_geometry_check.py` and its output, `docs/E3/geometry-check.json`.
- **E4s-1's measured training batches:** `experiments/E4s-stereo-module/E4s-1/train-*.json` (`seconds`,
  `composition`, `registered`).
- **Code:** `wormwars/world.py`, `wormwars/graft.py`, `wormwars/e4s/`, `wormwars/brain.py`.

**Please answer:**
1. A verdict: "proceed to pre-registration" or "revise".
2. Is each v2.2 item resolved? Name any that are not.
3. Did v2.3 introduce new problems? In particular check:
   - the open-loop hold, settable and release assays, and whether q's retention really is exactly
     testable open loop;
   - the memory classes;
   - the initial draw balanced per module, and the claim of zero turn offset at generation 0;
   - both spawn caps and the acceptance rates;
   - the component tests down to m = 0.005.
4. What the pre-registration must pin that v2.3 leaves open. Keep this list to what changes outcomes.

Be concrete and brief. You are read-only: do not edit files.
