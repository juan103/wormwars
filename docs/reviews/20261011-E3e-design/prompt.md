You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# E3e design v1: please review

You are reviewing, read-only, the WormWars repository in the current directory, at 5b76470 (branch `roadmap`).

**The design:** `docs/E3/E3e-DESIGN.md` (v1). D232 in `DECISIONS.md` gives the owner's choice.

**The context:**
- **E3d,** published: `experiments/E3-ab-organism/E3d/RESULTS.md`, with `docs/E3/E3d-DESIGN.md` bound and amended.
  Its decisions are D221-D231. It failed at calibration on G1b alone: a random walk at 2.34-2.53 against 2.0.
- **The owner chose** a 7 × 7 maze with the same island construction.

**What E3e proposes:** E3d's bound design, unchanged except for the size, the interior, the distance bound, a fresh
seed and fresh blocks, and the wall-follower's tree-tour qualification at c = 7. It uses a thin runner over
`scripts/e3d.py`.

**Please answer, citing sections and files:**
1. **Is "E3d unchanged except §1" sound?** Does the size change need anything else? Consider:
   - the horizon;
   - the scent's reach against longer routes;
   - the gate's absolute limits, G1b and G2b, at a new size;
   - the blind family's grids;
   - the projection.
2. **Is anything in E3d's text size-specific** and now wrong at c = 7 (for example the interior, the spawns, the
   hygiene exemption's limit of 8, the records)?
3. **The qualification at c = 7, and the thin runner:** adequate?
4. **Your verdict:**
   - "bind";
   - or "revise", with a numbered list limited to what would make the result wrong or uninterpretable.
