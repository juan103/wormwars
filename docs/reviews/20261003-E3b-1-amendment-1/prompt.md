You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# E3b-1: a gap in the bound pre-registration (infeasible mazes); a proposed Amendment 1

You are reviewing a proposed amendment in the WormWars repository (your working directory). You may read any
file.

## The facts (each can be checked)

- **E3b-1's pre-registration is bound** (`experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md`). Its §4
  fixes the maze blocks at maze run seed 1 180 000. Its §3 fixes the training mazes as
  `train_ids(run seed, generation, n, base 10 000 000, span 10 000 000)`.
- **The mazes:** `wormwars/e3/maze.py` `maze_for` draws a maze's walls from (run seed, maze id) only. The A/B
  placement comes from (run seed, maze id, episode), "drawn only among eligible pairs". A maze with no eligible
  pair raises `ValueError`. E3b-0's plan (`docs/E3/E3b-0-PLAN.md` line 39) said "0 of 2 000 mazes at c = 5-8
  did". The plan also made walls "never redrawn" (`maze_for` docstring; D-entries around 60d0de9): walls must
  not depend on the episode.
- **What happened:** E3b-1's first formal stage, `project` (the benchmark, which reads no scores), stopped
  after about 1 second. Maze 9585, at the projection seed 1 190 900, has no eligible placement.
- **A full check** (deterministic, since feasibility depends on (run seed, id) only):
  - the validation block (4000-4127), the learning-curve block (4500-4627) and the replay-calibration
    block (5000-5255) have no infeasible maze;
  - **the test block has one: id 6073**;
  - about 0.08% of ids in the training range are infeasible (4 of 5 000 sampled);
  - **training would crash in 36 generations** across the arms' registered (run, generation) id sets. The
    first is T-A run 1, generation 97;
  - E3b-0's own blocks: 0-255 and 1000-1255 have none; 2000-2255 has two (2067, 2183). Because a maze
    without a placement raises, no infeasible maze can be in any published result.
- **No score of E3b-1 has been read.** Only the 1-second stopped `project` attempt has run, and it is
  recorded. `project` may be rerun once (§5).

## The proposed Amendment 1 (dated 2026-10-03, before any stage completed)

> **Infeasible mazes.** A maze id whose walls admit no eligible A/B placement has its walls redrawn from
> (run seed, maze id, k) for k = 1, 2, … until they do. The redraw is keyed by the id, never by the episode,
> so walls stay fixed across episodes. Every block keeps its registered ids and size; feasible mazes are
> unchanged bitwise. Implemented in `maze_for`, and so it applies to every use: training, validation, the
> learning curve, the replay calibration and donors, the test block, and the smoke and projection ids. Each
> stage's record lists the redrawn ids it played. Reason: §3 and §4 did not say what an infeasible id does;
> found by the first formal stage, before any data.

The alternative I considered: skip an infeasible id and take the next feasible one not already in the set.
For the test block that means 6073 → 6256; in training, id + 1. It is statistically equivalent (both sample
from the feasible-maze distribution), but needs an id hook in `evolve_batch` and changes the registered id
lists.

Other consequences I see:
- **It is an engine change** (rule 7). The equivalence check is that every feasible maze's walls and
  placements are bitwise unchanged; E3b-0's CPU equivalence cases are re-run by `g-e`.
- **The `project` stage's rerun** runs on the new code (its one rerun under §5).

## The questions

1. Is an amendment the right instrument here, and is it admissible under rule 2 (before any data, dated,
   beside the registered text)?
2. The redraw or the skip, or something else? Attack my choice.
3. What should the amendment's text say that it does not? For example: the reporting of redrawn ids, the
   effect on E3b-0's published records, or the equivalence check.
4. Anything else this exposes. For example, other ways a training stage could crash on a maze, or other
   unregistered failure modes.

Please answer briefly, and end with: "adopt as written", "adopt with changes" (list them), or "do not adopt"
(and what instead).
