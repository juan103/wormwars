# E3d: a maze that wall-following cannot solve (design v2, for review)

**Status:** draft v2, for review by both reviewers. v1 (40bd50f) was reviewed by both ("revise", D222;
`docs/reviews/20261010-E3d-design/`). §9 lists what changed. E3d is exploratory: it validates a task, and it
trains nothing.

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
- **The working form:** loops, with each goal inside a free-standing wall ring (an "island") that the outer
  wall's circuit never passes.
- **The maze size** is the owner's choice (2026-10-10): **6 × 6**. At 5 × 5, only 9 interior cells can hold an
  island goal, and every feasible pair sits on opposite sides of that 3 × 3 interior (16 placements, the
  centre never a goal; §2's sizing).

## 1. The question, and what a pass does and does not mean

**Can a 6 × 6 maze family be built in which:**
- (a) every declared scent-free control, the strongest included, scores well below a scent navigator, and
  rarely completes a round trip;
- (b) a scripted scent navigator still shuttles, and the engineered seed beats every scent-free control by a
  practical margin;
- (c) the rest of the task is E3b-1's: the colony, the trails, the scent, the horizon and the visit rule?

**The geometric guarantee and the behavioural claim are separate:**
- **Geometric, by construction and tested:** no perimeter-connected wall cell lies in either goal's closed
  5 × 5 block, and no wall component touches both goal blocks. A creature that stays on the perimeter
  component cannot score a visit.
- **Behavioural, measured:** whether real scent-free controllers stay on the perimeter component, switch to an
  island, or cover the maze by bouncing. The gate's G1 is over a family of blind controls (§3), and every
  control's component contacts are recorded (§5).

**A pass means:** on this confirmation block, the declared blind family scored below the declared limits, and
the declared navigators above theirs. It does not mean that no scent-free strategy can solve the family; an
evolved one might find what the family misses. E4 will report its own blind references.

## 2. The maze family: carved island goals on a 6 × 6 tree

**The construction** (`maze.islands_for`, new; the tree generator is unchanged):
1. **The tree:** E3b-1's Wilson spanning tree on the 6 × 6 grid of maze cells (3-wide corridors, 1-cell walls;
   a 25 × 25 grid).
2. **The goals:** A and B drawn uniformly from the pairs of interior cells (rows and columns 1-4, 16 cells)
   whose rings share no corner post (Chebyshev distance at least 2).
3. **The islands:** for each goal, every closed wall segment that leaves one of its four corner posts outward
   is opened. Each goal's ring (its own closed sides and its four posts) is then free-standing.
4. **k_r further openings,** among the remaining closed internal segments: the first k_r of a random order of
   them, so the openings at k_r = 2 are a subset of those at k_r = 4 for the same maze id.
5. **Every opening is appended to `Maze.edges`,** so the oracle, the distances and the dead ends see it.
6. **The checks on the final maze:**
   - A and B are island-safe: no perimeter-component wall cell (4-connected labelling of the wall grid; the
     perimeter component is every component touching the grid's border) in either goal's closed 5 × 5 block;
   - no wall component touches both goal blocks;
   - the graph distance between A and B is in [⌈c/2⌉ + 1, 2c] = [4, 12], as for E3b-1 but over the final graph;
   - at least one spawn cell exists (below).
7. **The redraw:** a maze failing a check is redrawn from the start, keyed by (run seed, maze id, redraw index)
   as `walls_for` keys the tree, at most 64 times. A maze id still infeasible after 64 is an error.

**The spawns:** up to 4 cells, drawn per episode as in E3b-1, among the cells whose closed 5 × 5 block holds no
island wall cell (the mirror of island-safe), at graph distance at least 2 from A and B. Weys start at a spawn
cell's centre with a random heading (`maze_world.py:215`), so a spawn is beside the perimeter component, not on
its circuit. This is a declared task condition. It favours the perimeter circuit as a blind strategy, not the
hardest case for every blind strategy.

**Why carved islands, not random openings** (both reviewers; the sizing below):
- island-safety is guaranteed for the chosen goals, without conditioning the walls on a rare event;
- the tree is kept away from the goals, so less of the maze is opened;
- placements are drawn uniformly, with random orientations, and the k_r random openings soften the
  stereotyped goal neighbourhood.

**Sizing** (`scripts/e3d_sizing.py`, seed 20 261 010, 400 mazes per setting, `docs/E3/e3d-sizing.json`; it
sizes the design, and no reading depends on it). The share of mazes with a full feasible placement, and the
effective number of distinct placements (the exponential of the placement entropy):

| c | construction | k | feasible (lower bound 4) | effective placements | open share of internal segments |
|---|---|---|---|---|---|
| 5 | random openings | 6 / 8 / 10 | 0.18 / 0.33 / 0.40 | 13.9 / 13.1 / 9.9 (of 16) | 0.75 / 0.80 / 0.85 |
| 5 | carved, k_r | 0 / 2 / 4 | 0.63 / 0.43 / 0.33 | 14.6 / 14.7 / 12.2 (of 16) | 0.75 / 0.80 / 0.85 |
| 6 | random openings | 6 / 8 / 10 | 0.40 / 0.61 / 0.75 | 66.8 / 68.7 / 68.3 (of 78) | 0.68 / 0.72 / 0.75 |
| 6 | carved, k_r | 0 / 2 / 4 | 0.73 / 0.70 / 0.65 | 63.6 / 63.4 / 64.1 (of 73) | 0.69 / 0.72 / 0.76 |

- A tree opens 35 of 60 internal segments at c = 6 (0.58).
- v1's table counted mazes with two island-safe cells, not feasible placements (Fable); this one counts full
  placements.
- Infeasible carved draws at c = 6 almost all fail only the distance's lower bound: 362 of 368 across k_r.

**The scent's reach** (both reviewers): the scent is a Gaussian of the free-path distance d from the goal's
centre, zero beyond d = 9 (`maze_world.py:234-240`). At d = 9 it is below the follower's threshold of 0.005, so
a goal is detectable within d ≤ 8. A scent-guided controller below threshold explores as W2, so an island goal
whose scent never reaches the perimeter track is found only by exploring, by navigators and blind controls
alike.
- **The perimeter track:** the free grid cells 8-adjacent to a perimeter-component wall cell.
- **Reported, not constrained:** the share of goals whose scent reaches the perimeter track (some track cell
  at d ≤ 8). The follower's and the seed's visits and zero-visit shares are reported split by it.
- **Read as:** zeros on unreached goals are a discovery cost the task imposes on every scent-guided
  controller. The gate is computed on all mazes.

**Scramble mode** (the scrambled-cells probe) asserts equal open-cell counts across a batch
(`maze_world.py:263-266`); carved mazes differ in their counts. It is refused for the island family.

## 3. The controls and organisms

All play E3b-1's world except for the maze: c = 6, H = 2 400, colonies of 8, shared trails (μ 0.01, λ 0.02,
δ 0.05, d₀ 1.142), the scent's σ and reach, and the visit rule (the head inside the goal's 3 × 3 block). One
episode per maze. Scores are the colony mean of visits per wey, averaged over mazes, paired across conditions.

**The blind family** (no scent, no trail; its best member is the benchmark B_max of G1 and G3):

| Control | What it is | Settings |
|---|---|---|
| Wall-follower | new, scripted, privileged wall sensing (below) | left-handed and right-handed |
| W2 | the neural W2 carrier (E3b-1's organism, not E3b-0's scripted steady state) | one |
| W2-turn | neural W2 with its carrier's turn bias set for a resting turn r (E3c's reference) | r ∈ E3c's grid {−0.8, −0.4, 0, 0.2, …, 1.4} plus {1.6, 1.8, 1.95}; \|r\| < 2 is the bound |
| W2+M40, W2+M80 | the carrier with E3b-0's oscillator, which flips the hugged side on a timer | two |
| Random walk | E1's persistent random walk plus W1's reflex (scripted) | persistence {0.25, 0.5, 0.8} × rate {0.5, 1, 2}, speed 1 |
| S champions, noses removed | E3c's 16 S champions with the nose inputs zeroed (E3c's probe) | sixteen |

**The scripted wall-follower** (`maze_controls.WallFollower`, new):
- **Senses:** the world's wall raster at three probe points from the head: ahead (1.0 grid cell), the
  hugged side (1.0 cell at 90°), and ahead on the hugged side (1.4 cells at 45°). It never reads scent or
  trail. The probes are privileged, as the oracle's positions are, so it is a stronger hugger than W2.
- **Policy,** with handedness h: wall ahead → turn away from h at full turn; no wall on the side and none
  ahead-side → turn toward h at full turn; otherwise straight. Forward drive 1, the world's turn limit.
- **Its qualification** (tests, §6): on hand-built layouts it acquires a wall from a cell centre, keeps one
  component for 2 400 ticks, and on a tree maze visits every cell. Its component-switch rate on trees is
  reported.
- **Declared asymmetry:** it starts like every other control, at a spawn centre with a random heading. A
  separate diagnostic starts it tangent to a known wall and is reported only, for every blind control alike.

**The navigators:**
- **The oracle** (E3b-0's), the reference ceiling. It is privileged and steers along BFS next hops over
  `Maze.edges`, so it follows loops. It is not a proven optimum.
- **The scripted scent follower** (E3b-0's), under shared trails and under none.

**The organisms:**
- **the frozen seed E + W2** (P-fixed), intact and with its noses removed;
- **E3c's 28 champions** (S-mod 8, S-dense 8, P-sel 4, P-joint 8), frozen from their saved genomes, checked
  by hash, intact and with their noses removed. The S champions' noses-removed plays are the blind family's
  last row.

## 4. The procedure and the gate (fixed before any play on 6 × 6 island mazes)

**The blocks** (run seed 1 190 000; E3b-1's maze run seed was 1 180 000):
- **calibration:** maze ids 30 000-30 127, played at each k_r ∈ {0, 2, 4}. The same ids at each k_r, so each
  maze differs only by its nested openings, unless a redraw intervenes;
- **confirmation:** ids 30 200-30 455, at the chosen k_r only, played once.

**Choosing k_r** on the calibration block: **the smallest k_r** whose point estimates meet G1-G3 below and
whose first-draw feasible share is at least 0.5. The smallest, not the largest gap, because each opening
removes maze structure (Astra).
- If none qualifies, the verdict is **"E3d: failed at calibration"**, naming each k_r's failed criteria.
  Confirmation is not played.
- A revised construction needs a fresh calibration block and a fresh confirmation block.

**The benchmark on confirmation:** B_max is the maximum over every blind-family member and setting played on
the confirmation block. Nothing is selected on calibration and then frozen; the maximum of all of them is the
conservative choice, and it is declared now.

**The gate,** on the confirmation block:

| | Criterion | Why | On E3b-1's 5 × 5 trees |
|---|---|---|---|
| G1a | B_max ≤ 0.25 × the follower (shared) | the circuit no longer competes | 5.77 / 16.98 = 0.34: fails |
| G1b | B_max ≤ 2.0 visits per wey: at most one round trip on average in 2 400 ticks | blind success is rare | 5.77: fails |
| G2a | the follower ≥ ⅓ of the oracle | navigation remains efficient | 16.98 / 34.5 = 0.49: passes |
| G2b | the follower ≥ 4.0 visits per wey: two round trips | navigation is absolutely possible | 16.98: passes |
| G3a | the seed − B_max ≥ max(0.5, 0.10 × the seed) (E3c's dual margin) | the engineered navigator beats the circuit by a practical margin | 5.12 − 5.77 < 0: fails |
| G3b | the seed's median legs per wey ≥ 2 (E3b-1's repeated-journey condition) | it shuttles, not only arrives | (not computed on trees) |

- **The tree column** shows the gate is informative: the task E3c measured fails G1 and G3 and passes G2. Its
  values come from different blocks (the oracle from E3b-0, the follower from E3b-1, W2-turn and the seed from
  E3c), and B_max there is only W2-turn's, so a lower bound on the tree family's.
- **The oracle's precondition:** the oracle must score at least the follower's mean and make a visit in at
  least 95% of colonies. Otherwise the verdict is **"E3d: not evaluable"** (an oracle or construction fault).
- **Uncertainty:** each gate quantity is reported with a 95% bootstrap interval over mazes (2 000 resamples,
  colonies intact, seed 20 261 011). The gate itself is acceptance on this fixed block's point estimates, and
  it is described that way.

**The verdict:**
- **"E3d: passed"** if G1-G3 all hold;
- **"E3d: failed"** otherwise, naming the failed criteria.

**How each G1 failure is read** (stated now, from §5's contact records):
- **a wall-follower or W2 variant with a high island-contact share:** component switching defeats the
  construction;
- **the random walk:** random coverage reaches islands; the maze is too open or too small;
- **an S champion with its noses removed:** an evolved blind strategy beats it, the case E4 cares most about;
- **any blind control with no island contact:** impossible by construction; a fault to find before anything
  is reported.

**The E3c champions** (descriptive; the predictions stated now):
- **The S champions'** intact mean visits fall to at most 0.5 × their E3c test-block means.
- **P-joint's champions** keep at least 0.5 × theirs. This is tentative: E3c found four partial and four
  nose-dependent champions, with a large nose-free component. Keeping half the score is not keeping navigation,
  so their noses-removed scores are reported beside.
- **If the S champions intact still shuttle** (median legs ≥ 2 and above 0.5 × their E3c means), E3d reports
  that the task does not defeat E3c's coverers, whatever the gate says. If their noses-removed scores are low,
  they are using scent here, which is not a contradiction.

## 5. What is recorded and reported

**For every control and organism, on both blocks:**
- visits per wey (colony mean), legs, the later-leg rate (legs per 1 000 ticks after the first two),
  completed round trips (legs ≥ 2) and the zero-visit share;
- discovery: the share of weys reaching A, and B, within H, and the median first-visit tick of each;
- **component contact:** each tick, the wall components with a cell in the head's 3 × 3 neighbourhood,
  classed as perimeter or island. Reported as the island-contact share of ticks and the switch rate (changes
  of the last-contacted component, per 1 000 ticks);
- coverage: the share of maze cells whose open block the head entered.

E3c's tour match assumed the tree's 48-move circuit, so it is not used here; component contact and coverage
replace it (Astra).

**Per maze:** the placements, redraws, the scent-reach flags, and the maze-ness measures: the open share, the
junction (degree ≥ 3) and dead-end counts, the A-B detour (graph distance over Manhattan distance), and the
share of spawn-goal pairs in direct line of sight.

## 6. Code, tests and equivalence

**Code:**
- `maze.islands_for(run_seed, maze_id, c, k_r)` and its checks; `maze_for` takes a family argument;
- a `maze_family` field in the maze world's config: "tree" (the default, E3b-1's generator) or "islands", with
  `maze_extra_openings` k_r;
- `maze_controls.WallFollower`;
- the contact and coverage records in `maze_measures`;
- `scripts/e3d.py` on E2's frame, with stages `project`, `g-e`, `calibrate`, `confirm`, `champions` and
  `report`, inside `wormwars.accounting`.

**Tests first** (each seen failing):
- **the labelling and island-safety** on hand-built grids, with a sabotage case where a ring touches the
  perimeter;
- **the construction:** raster and `Maze.edges` agree; exactly k_r extra openings beyond the carving; nesting
  across k_r; connectivity; both goals island-safe; no shared component; the distance bound on the final
  graph;
- **the spawns:** no island wall cell in a spawn's block; distance from the goals;
- **the redraw:** deterministic per (seed, id, redraw); independent of the episode; the error after 64;
- **the oracle on loops:** on hand-built loop mazes, it reaches both goals along a shortest path;
- **the wall-follower:** wall acquisition, retention of one component, both handednesses, a full tree tour;
- **the contact record:** on a scripted path, the counted switches and island share;
- **scramble refused** for the island family.

**Rule 7** (`g-e`), with `maze_family` = "tree":
- E3b-1's `maze-reference.json` is reproduced bitwise;
- E3c's g-e legs pass again: the CPU equivalence reference and E2's GPU batch;
- **a new full-rollout leg:** tree-family maze rollouts (positions, headings, goals, visits and events per
  tick) from 40bd50f against the new code, at zero tolerance, on the CPU and on the GPU in E3d's composition.
  The 40bd50f reference is generated in a worktree at that commit and committed with its hash.

**Compute:**
- no evolution: plays only;
- calibration: the blind family, the navigators and the seed, on 128 mazes at three k_r;
- confirmation: everything, the champions intact and with their noses removed included, on 256 mazes;
- a ceiling of 3 GPU-hours. `project` measures the cost first. If its projection exceeds the ceiling, the
  random walk's grid shrinks to persistence 0.5 at three rates first, then the W2-turn grid to every other
  point plus 1.95.

## 7. Decisions open for the reviewers

1. **The gate's thresholds:** G1b's 2.0 visits, G2a's one third, G2b's 4.0, G3's dual margin.
2. **The blind family:** is any credible scent-free strategy missing? Is the privileged wall-follower the
   right extra, or should it use only the two front collision sensors?
3. **The carved construction:** acceptable as "less designed" enough, with k_r ≤ 4?
4. **The smallest-k_r rule,** with the feasible share floor of 0.5.
5. **Scent reach reported rather than constrained.**

## 8. What E3d is for

If it passes, E4 uses this family at the chosen k_r, with its own blind references. If it fails, the failed
criteria say what the next construction must change, and the roadmap stays paused before E4 until the owner
decides.

## 9. Changes from v1 (both reviews, D222)

- **The maze size:** 6 × 6, the owner's choice on the recomputed sizing (Fable: the 5 × 5 placements are
  stereotyped).
- **The construction:** carved islands plus k_r ∈ {0, 2, 4} replace random openings (Fable, Astra).
- **The sizing:** full feasible placements, a committed script and seed (both).
- **Placement checks:** no wall component touches both goals (Astra); spawns mirror island-safety (Fable); the
  spawn claim corrected (Astra).
- **The blind family:** the maximum over every member, the random walk with a grid, W2+M40 and W2+M80, W2-turn
  past 1.4, both wall-following hands, the S champions with noses removed; neural and scripted W2 kept
  distinct (both).
- **The gate:** absolute limits beside the ratios; G2 recalibrated with the tree values shown; a practical
  margin and repeated shuttling for G3; the smallest qualifying k_r; the confirmation benchmark declared;
  bootstrap intervals; the oracle's precondition (both).
- **The records:** component contact and switch rate, discovery and round trips, maze-ness, scent reach;
  tour match dropped (both).
- **The champions:** a contradiction is reported as one; noses-removed plays; P-joint's prediction tentative;
  E3c's test-block means as the reference (both).
- **Code and rule 7:** edges, scramble, the redraw stream, named legs, a full-rollout leg against 40bd50f on
  the CPU and the GPU (both).
