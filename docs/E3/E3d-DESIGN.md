# E3d: a maze that wall-following cannot solve (design v1, for review)

**Status:** draft v1, for review by both reviewers. E3d is exploratory: it validates a task. It trains
nothing.

**Why it exists** (the owner, 2026-10-06/10; D221):
- **E3c found the problem:** organisms trained from random weights solve E3b-1's tree mazes as scent-free
  wall-followers (`experiments/E3-ab-organism/E3c/RESULTS.md`).
- **The cause:** in a spanning-tree maze, every wall is connected to the outer wall. So following any wall
  traces the whole tree and passes both sources.
- **The consequence:** a question about navigators, E4's above all, needs a maze where that circuit fails and
  navigating pays.
- **The owner's direction:** "a maze where no goal touches the perimeter". In a tree maze that alone does not
  help: E3c's wall-followers scored the same on its 11 test mazes with both goals in the interior (6.59-6.67)
  as on the others.
- **The working form:** loops, with the goals beside free-standing walls ("islands") that the outer wall's
  circuit never passes.

## 1. The question

**Can a maze family be built in which:**
- (a) a creature that follows the perimeter-connected walls rarely reaches the goals;
- (b) a navigator that follows the goals' scent still reaches them often;
- (c) the rest of the task (colony, trails, scent, horizon) is E3b-1's, unchanged?

**And, on such mazes, do E3c's evolved organisms separate as the coverage finding predicts?**
- the 16 scent-free coverers should collapse;
- the 8 tuned engineered navigators should keep much of their score.

## 2. The maze family: loops with island goals

**The walls** (`maze.generate_loops`, new; the tree generator is unchanged):
1. **Start from** E3b-1's Wilson spanning tree on the 5 × 5 grid of maze cells, with 3-wide corridors and 1-cell
   walls.
2. **Open k of the closed internal wall segments,** chosen uniformly at random. A 5 × 5 tree has 40 internal
   segments, 24 open and 16 closed.
   - Opening walls only adds connections, so every cell stays reachable.
   - Some wall pieces become disconnected from the outer wall: islands.

**The island-safe cells:**
- **Label** the wall cells' connected components (4-connectivity on the 21 × 21 grid). The *perimeter
  component* is every component that touches the grid's border.
- **A maze cell is island-safe** if no wall cell in its closed 5 × 5 block (its 3 × 3 open block, its four
  border segments and its four corner posts) belongs to the perimeter component.
- **What that means:** a creature hugging the perimeter-connected walls never passes within one grid cell of
  the goal's block. A visit, the head inside the 3 × 3 block, is then out of its reach.

**The placements** (`maze.place_islands`, new):
- **A and B:** two distinct island-safe cells, with a shortest-path distance over the maze graph in
  [⌈c/2⌉ + 1, 2c], as for E3b-1 but over the graph.
- **The spawns:** up to 4 cells adjacent to the perimeter component, each at least 2 maze cells from A and B, so
  that a wall-follower starts on the outer circuit, the hard case for the maze.
- **The redraw:** walls with no eligible placement are redrawn, keyed by the maze id only (E3b-1's Amendment 1
  rule), at most 64 times.

**Sizing** (a CPU sketch, 400 random mazes per k; it sizes the design, and no reading depends on it): the share
of mazes with at least two island-safe cells is

| k | 2 | 4 | 6 | 8 | 10 | 12 |
|---|---|---|---|---|---|---|
| Share | 0.21 | 0.49 | 0.75 | 0.93 | 0.98 | 1.00 |

So k between 6 and 10, with the redraw rule.

**The cost of loops:** a maze with half its closed walls opened is more open. "Maze-ness" falls, and with it
some of the navigation problem. This is why §4 also requires the scent follower to stay well above the
scent-free controls, not merely above the floor.

## 3. The controls and organisms

All are played on new maze blocks, never used before, with E3b-1's world otherwise unchanged: c = 5,
H = 2 400, colonies of 8, shared trails (μ 0.01, λ 0.02, δ 0.05, d₀ 1.142).

**Scripted:**
- **The oracle** (E3b-0's), the ceiling;
- **the scripted scent follower** (E3b-0's), the navigator;
- **a scripted wall-follower** (new). It keeps one wall on its left using the two front collision sensors, at
  W2's speed, and never uses scent. It is the circuit, written by hand;
- **W2 alone,** the floor;
- **W2-turn:** W2 with a constant resting turn, swept over E3c's grid. This was E3c's blind circuit, 5.77 there;
- **the random walk with W1's reflex** (E3b-0's).

**Organisms:**
- **the frozen seed E + W2** (P-fixed);
- **E3c's 28 champions,** frozen, from their saved genomes, checked by hash: S-mod 8, S-dense 8, P-sel 4,
  P-joint 8.

## 4. The procedure and the gate (fixed before any play on the new mazes)

**Two new blocks:**
- **calibration:** 128 mazes per k, for choosing k;
- **confirmation:** 256 mazes at the chosen k, played once.

**Choosing k,** on the calibration block, among {6, 8, 10}: the k with the largest gap between the scripted
scent follower and the best scent-free control (the wall-follower, or W2-turn at its best grid point). Ties
go to the smaller k.

**The gate,** on the confirmation block (each criterion fixed now):

| | Criterion | Why |
|---|---|---|
| G1 | the best scent-free control (the scripted wall-follower, or W2-turn's best point) makes at most 0.25 × the scent follower's visits | the circuit no longer solves the task |
| G2 | the scent follower makes at least 50% of the oracle | navigation is still possible within the horizon |
| G3 | the frozen seed makes more than the best scent-free control | the engineered navigator beats the circuit |

**The verdict:**
- **"E3d: passed"** if G1-G3 all hold;
- **"failed"** otherwise, naming the failed criteria.

**The E3c champions** (descriptive, the prediction stated now): the S champions' mean visits fall to at most
0.5 × their E3b-1-maze level, and P-joint's champions keep at least 0.5 × theirs. They are reported either way.
They are not part of the gate, so that the gate does not depend on organisms selected on another maze family.

**Also reported** (descriptive):
- each control's coverage and tour match;
- the visits per maze;
- the share of feasible mazes and the redraws;
- the island-safe cell counts.

## 5. Code, tests and equivalence

- **Code:** `maze.generate_loops`, `maze.place_islands` and a `maze_family` switch in the maze world's config.
  The default is "tree", E3b-1's generator.
- **The scripted wall-follower** in `maze_controls`.
- **A runner:** `scripts/e3d.py`, on E2's frame, with stages `calibrate`, `confirm` and `champions`.
- **Tests first:**
  - the components and the island-safe rule on hand-built grids;
  - the placements' constraints;
  - the redraw;
  - the switch.
- **Rule 7:** with the switch at "tree", E3b-1's `maze-reference.json` is reproduced bitwise, and an E3b-1 play
  is unchanged.
- **The scripted wall-follower** is checked on a tree maze: it must score like E3c's coverers.
- **Compute:** a few GPU-hours at most. No evolution: plays of scripted controls and 29 frozen organisms on
  128 × 3 + 256 mazes. The ceiling is 3 GPU-hours. `project` measures it first.

## 6. Decisions open for the reviewers

1. **The island-safe rule:** the 5 × 5 closed block, one grid cell of margin. Is it strict enough, or too
   strict? A wall-follower could switch to an island after a collision; the scripted one will not, but
   evolved ones might.
2. **Random openings against targeted openings,** which carve islands around chosen cells: random openings
   are simpler and less designed; targeted ones control "maze-ness".
3. **The spawns on the outer circuit:** the hard case. Or anywhere?
4. **The gate's thresholds:** 0.25 × the follower, 50% of the oracle, and the seed above the circuit.
5. **Whether the E3c champions' prediction** should be part of the gate.
6. **The horizon:** H = 2 400 unchanged. Loops shorten some paths; is 2 400 still right?
7. **Any scent-free strategy this misses.** For example, random bouncing in an open maze may now reach islands
   that a strict circuit misses.
