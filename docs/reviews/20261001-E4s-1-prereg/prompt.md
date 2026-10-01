You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a pre-registration draft in WormWars, an open-science project that evolves brains on the
C. elegans connectome. The repository is your working directory; read `AGENTS.md`, especially rule 2.

**What to review:** `experiments/E4s-stereo-module/E4s-1/PREREGISTRATION.md` (draft, `roadmap` branch,
latest commit).
- It turns `docs/E4s/E4s-1-DESIGN.md` v2 into binding text, with every pin listed by the confirmation
  reviews (`docs/reviews/20261001-E4s-1-design-v2/`; D148-D149).
- Power and gate-1 numbers: `experiments/E4s-stereo-module/E4s-1/development-records/power.json`
  (`scripts/e4s1_power.py`).
- Code it will build on: `wormwars/graft.py`, `wormwars/e4s/`, `wormwars/e04a/evolve.py`,
  `scripts/e4s0.py`, `scripts/e2d.py`, `scripts/e2.py`.

**Please answer:**
1. A verdict: "bind as is", "bind after fixes" (list them) or "revise".
2. Must-fix items (numbered; section and change). In particular check:
   - that every outcome rule is exclusive, complete and implementable from the stated measures;
   - that the gates, seeds, worlds, masks and failure rules are unambiguous;
   - that nothing contradicts the design, E4s-0's records or the code.
3. Anything that would let the result be read two ways after the data are in.

Be concrete and brief. You are read-only: do not edit files.
