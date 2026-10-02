You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing an experiment design in WormWars, an open-science project that evolves brains on the
C. elegans connectome. The repository is your working directory; read `AGENTS.md`.

**What to review:** `docs/E3/DESIGN.md` (v1, `roadmap` branch).
- It designs E3, the minimal A/B organism of `ROADMAP.md` (the "E3 / 04b" section).
- It builds on E4s's published results: `experiments/E4s-stereo-module/README.md`, `E4s-0/RESULTS.md`
  and `E4s-1/RESULTS.md`.
- The literature review is in `docs/reviews/20261001-literature-review/` (the latch, selector and
  modular-organism sections).
- Code to check against: `wormwars/world.py` (Task N's targets, sensing, events), `wormwars/graft.py`,
  `wormwars/e4s/`, `configs/interface.yaml`, `wormwars/e1/`.

**Please answer:**
1. A verdict: "proceed to pre-registration", "revise" or "rethink".
2. Must-fix items (numbered; section and change).
3. Your answers to the design's seven questions.
4. Anything in the literature or in the repository's earlier results that the design should reuse or
   would contradict.

Be concrete and brief. You are read-only: do not edit files.
