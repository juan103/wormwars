You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# E4 design v1: please review

You are reviewing, read-only, the WormWars repository in the current directory, at cf201da (branch `roadmap`).

**The design:** `docs/E4/E4-DESIGN.md` (v1). E4's question is in `ROADMAP.md`, "E4 / 04c: do the two minds share?".
The task is E3f's validated maze family (`experiments/E3-ab-organism/E3f/RESULTS.md`, D237-D241, including the
requirements for E4 recorded there). The organism is in `wormwars/e3/organism.py` and `maze_organisms.py`; the
training machinery is E3c's (`scripts/e3c.py`, `wormwars/e3/assembly.py`, `tuning.py`, `e3c_stats.py`).

**Note:** the owner has said no GPU is to be used yet. This review is of the design only.

**Please answer, citing sections and files:**
1. **Does the design answer the roadmap's E4 question,** useful transfer above all, so that a positive or a null
   result is interpretable?
2. **The open decisions in §8:**
   - the mode clamp;
   - the cross-link set and its initialisation;
   - T2's matched control;
   - the diagnostic task;
   - trail-mediated transfer;
   - the arms' start;
   - anything missing.
3. **Is anything wrong** about the organism, the gating or the machinery as described?
4. **What should the pilot measure** to size the formal run, and what power analysis is needed?
5. **Your verdict:**
   - "proceed to a pre-registration";
   - or "revise", with a numbered list.
