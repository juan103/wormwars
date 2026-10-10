You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# E3d design v1: please review

You are reviewing, read-only, the WormWars repository in the current directory, at 40bd50f (branch `roadmap`).

**The design:** `docs/E3/E3d-DESIGN.md` (v1). D221 in `DECISIONS.md` gives the owner's direction.

**Why it exists:** E3c (`experiments/E3-ab-organism/E3c/RESULTS.md`, published) found that organisms trained
from random weights solve E3b-1's spanning-tree mazes as scent-free wall-followers. The owner wants better
mazes before E4: "a maze where no goal touches the perimeter".

**What E3d proposes:**
- **The mazes:** loop mazes (k extra openings in the tree), with the goals on island-safe cells, which no
  perimeter-connected wall touches;
- **the validation:** scripted controls, including a new wall-follower, and E3c's 28 frozen champions;
- **k chosen** on a calibration block, then a fixed gate on a confirmation block;
- **no evolution;** a few GPU-hours.

**Read the code it builds on:**
- `wormwars/e3/maze.py`, the generator and placements;
- `wormwars/e3/maze_world.py`, the world, scent and trails;
- `wormwars/e3/maze_controls.py`, the scripted controls;
- E3b-0's and E3b-1's folders, the earlier task validation.

**Please answer, citing sections and files:**
1. **Does the island-safe construction actually defeat wall-following?** Consider:
   - W2's reflex;
   - collisions that move a follower onto an island;
   - random bouncing in a more open maze;
   - the spawn rule.

   Is the 5 × 5 closed-block margin right?
2. **Does it keep navigation possible and meaningful?** Consider:
   - the scent field (free distance) in loop mazes;
   - "maze-ness" lost to the openings;
   - the horizon.
3. **Is the procedure sound?** Consider the choice of k on calibration, the gate G1-G3 and its thresholds, and
   the E3c champions as a descriptive prediction rather than part of the gate.
4. **Anything missing:**
   - controls;
   - equivalence (rule 7);
   - a better construction, such as targeted islands or another topology;
   - a simpler route to the owner's goal.
5. **Your verdict:**
   - "proceed to code";
   - or "revise", with a numbered list of required changes.
