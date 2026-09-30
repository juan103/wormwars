You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a design in WormWars, an open-science project that evolves brains on the C.
elegans connectome. The repository is your working directory; read `AGENTS.md` for its rules.

**Context:**
- E2 and its diagnosis E2d (both published; `experiments/E2-optimizer-screen/`,
  `experiments/E2d-taskn-diagnosis/`, D117-D138) found a "non-stereo plateau". No evolved champion
  steers by the left-right scent difference, and no tested optimizer change leaves the plateau.
- The owner decided (D139) to build the stereo capability by hand, ahead of the roadmap's plan: two
  noses, a ring attractor borrowed from the fly, a left/right turning readout, then evolution. The
  owner set a 96 GPU-hour ceiling.
- A deep literature research by Claude Sonnet 5.5 is archived in `docs/E4s/literature-report.md`.
- An exploratory open-loop gain probe of the champions is in
  `experiments/E4s-stereo-module/development-records/gain-probe.json` (`scripts/e4s_gain_probe.py`).

**What to review:** `docs/E4s/DESIGN.md` (v1). Nothing has run on its worlds or seeds. Please check
the code it relies on (`wormwars/brain.py`, `wormwars/interface.py`, `configs/interface.yaml`,
`wormwars/world.py` sensing and motor readout, `wormwars/exp02/scripted.py`) and the report's
derivations it uses.

**Please answer:**
1. **Is E4s well posed?** Does it test the owner's idea fairly? Is anything likely to make the graft
   win or fail for a trivial reason, for example:
   - the silent background in Stage A;
   - the random-N2 background's own drive on the turn neurons;
   - saturation or the common level of the scent;
   - the module-only probes built as interface variants;
   - the inert-module control.
2. **The gain probe:** is it sound as a design-informing measurement? What would you change in it?
   Does it support the "gain problem" reading?
3. **Stage A** (tuning and gate): the right positive control? The right thresholds (5.0 targets, the
   "uses" criterion, gain ≥ 32)? What must the tuning grid contain?
4. **Stage B:**
   - the arms (B1-B4);
   - the mutation scales;
   - 8 or 16 runs;
   - the proposed registered outcomes (useful and kept; eroded).

   What is missing, and what should be cut?
5. **The engine claim:** that the graft is new code, not a change, with the equivalence checks
   described. Is that right, given the code?
6. **The design's own questions** at its end (M1, backgrounds, mutation, `hold` as an arm).
7. **Budget and framing:** is the proposed 24-hour cap within the 96-hour ceiling sensible? Is the
   biology stated honestly?

**Answer format:** a verdict first, one of "proceed to pre-registration", "revise" or "rethink";
then must-fix items (numbered, each with the section and the change), then suggestions, then what you
checked and found correct. Be concrete and brief. You are read-only: do not edit files.
