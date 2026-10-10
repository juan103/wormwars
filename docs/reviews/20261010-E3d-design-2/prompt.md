You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# E3d design v2: please review

You are reviewing, read-only, the WormWars repository in the current directory, at 292508f (branch `roadmap`).

**The design:** `docs/E3/E3d-DESIGN.md` (v2). Its §9 lists what changed from v1 (40bd50f).

**The context:**
- **D221 and D222** in `DECISIONS.md`: the owner's direction, and the v1 review.
- **Both v1 reviews,** yours among them: `docs/reviews/20261010-E3d-design/`.
- **The owner chose a 6 × 6 maze,** on the recomputed sizing: `scripts/e3d_sizing.py` and
  `docs/E3/e3d-sizing.json`.

**Why E3d exists:** E3c (`experiments/E3-ab-organism/E3c/RESULTS.md`) found that organisms trained from random
weights solve E3b-1's spanning-tree mazes as scent-free wall-followers. E4 needs a task where that fails and
navigating pays.

**The code it builds on:**
- `wormwars/e3/maze.py`;
- `wormwars/e3/maze_world.py`;
- `wormwars/e3/maze_controls.py`;
- `wormwars/e3/maze_organisms.py`;
- `scripts/e3c.py`, its W2-turn reference and noses-removed probe;
- E3b-0's and E3b-1's folders.

**Please answer, citing sections and files:**
1. **Were your v1 required changes taken correctly?** Name any that were not, or were taken wrongly.
2. **The carved construction** (§2):
   - Is it correct as specified? Check the post and segment geometry against `maze.py`.
   - Does it keep enough maze?
   - Is the sizing script measuring what the design says?
3. **The blind family and the scripted wall-follower** (§3): is any credible scent-free strategy missing? Is
   the wall-follower well specified?
4. **The gate** (§4):
   - the thresholds and the tree column;
   - the smallest-k_r rule;
   - the confirmation benchmark;
   - the readings of each G1 failure;
   - the champions' predictions.
5. **The records, tests and rule 7** (§5-6): anything missing or untestable?
6. **Your verdict:**
   - "proceed to code";
   - or "revise", with a numbered list of required changes.
