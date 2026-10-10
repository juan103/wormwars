# E3d: a maze that wall-following cannot solve (design v2.2)

**Status:** v2.2, **bound** (§8; D225). v1 (40bd50f), v2 (292508f), v2.1 (44b81c0) and v2.2 (432fca6) were
each reviewed by both (D222-D225; `docs/reviews/20261010-E3d-design*/`); both said "bind" on v2.2, and the three
wording points they left are taken here. §10 lists what changed. E3d is
exploratory: it validates a task, and it trains nothing. Its gate and verdict wording are nevertheless fixed
here before any play, because they decide E4's task.

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
- **The working form:** each goal inside a free-standing wall ring (an "island") that the outer wall's circuit
  never passes.
- **The maze size** is the owner's choice (2026-10-10): **6 × 6**. At 5 × 5, only 9 interior cells can hold an
  island goal, and every feasible pair sits on opposite sides of that 3 × 3 interior (16 placements, the
  centre never a goal; §2's sizing).

## 1. The question, and what a pass does and does not mean

**Can a 6 × 6 maze family be built in which:**
- (a) every declared scent-free control scores well below a scent navigator, with a low average throughput;
- (b) a scripted scent navigator still shuttles, and the engineered seed beats every declared scent-free
  control by a practical margin;
- (c) the rest of the task is E3b-1's: the colony, the trails, the scent, the horizon and the visit rule?

**The geometric guarantee and the behavioural claim are separate:**
- **Geometric, by construction and tested:** no perimeter-connected wall cell lies in either goal's closed
  5 × 5 block, and no wall component touches both goal blocks. A creature that stays beside the perimeter
  component cannot score a visit.
- **Behavioural, measured:** whether real scent-free controllers stay beside the perimeter component, switch to
  another component, or reach the goals through free space. G1 is over a family of blind controls (§3), and
  every control's component contacts are recorded (§6).

**A pass means:** on this confirmation block, the declared blind family stayed below the declared limits and
the declared navigators above theirs. It does not mean that no scent-free strategy can solve the family; an
evolved one might find what the family misses. E4 will report its own blind references.

## 2. The maze family: carved island goals on a 6 × 6 tree

**The construction** (`maze.islands_for`, new; the tree generator is unchanged). Its draws are keyed by
(run seed, maze id, redraw index k):
- **the tree** from `walls_for`'s own streams, [run seed, id, 0x3A11] at k = 0 and [run seed, id, 0x3A11, k]
  after, so an island maze is carved from the same tree as the tree family's draw at the same id and index;
- **the goals, the swap and the k_r order** from a second stream, [run seed, id, 0x15A7, k].

1. **The tree:** E3b-1's Wilson spanning tree on the 6 × 6 grid of maze cells (3-wide corridors, 1-cell walls;
   a 25 × 25 grid).
2. **The goals:** a pair proposed uniformly among the 78 unordered pairs of interior cells (rows and columns
   1-4, 16 cells) whose rings share no corner post (Chebyshev distance at least 2); A and B swapped with
   probability ½, as `place` does.
3. **The islands:** for each goal, every closed wall segment that leaves one of its four corner posts outward
   is opened. Each goal's remaining sides and its four posts are then free-standing (one ring, or several
   pieces if a side was already open).
   - **A consequence:** all eight segments between consecutive neighbours of the goal touch a goal post, so
     every goal sits at the centre of a fully open 3 × 3 "roundabout" (Fable). The goals' neighbourhoods are
     therefore stereotyped; the openings in step 4 do not change that.
   - **A goal of tree degree 4** has no ring at all, only four isolated posts in an open plaza (Fable).
   - **Other islands:** carving also detaches wall sub-trees hanging off the roundabout's outer posts. They are
     islands too, but not goal rings.
4. **k_r further openings:** the first k_r of one random order of the remaining closed internal segments,
   **the goals' own sides excluded**, so each goal keeps the entrances the tree gave it. The openings at k_r = 2
   are a subset of those at k_r = 4 for the same maze id and redraw index.
5. **Every opening is appended to `Maze.edges`,** so the oracle, the distances and the dead ends see it.
6. **The checks on the final maze:**
   - A and B are island-safe: no perimeter-component wall cell (4-connected labelling of the wall grid; the
     perimeter component is every component touching the grid's border) in either goal's closed 5 × 5 block;
   - no wall component touches both goal blocks (automatic for carved goals; checked anyway);
   - the graph distance between A and B is in [⌈c/2⌉ + 1, 2c] = [4, 12], as for E3b-1 but over the final graph;
   - at least one spawn cell exists (below).
7. **The redraw:** a maze failing a check is redrawn from step 1 with the next redraw index, at most 64 times.
   A maze id still infeasible after 64 is an error. Accepted mazes at different k_r may sit at different
   redraw indices, and are then not nested.

**The spawns:** up to 4 cells, drawn per episode from E3b-1's episode stream [run seed, id, episode, 0x9ACE],
among the cells whose closed 5 × 5
block holds no island wall cell (the mirror of island-safe), at graph distance at least 2 from A and B. Weys
start at a spawn cell's centre with a random heading (`maze_world.py:215`), so a spawn is beside the perimeter
component, not on its circuit. This is a declared task condition. It favours the perimeter circuit as a blind
strategy, not the hardest case for every blind strategy. **One episode per maze, episode 0.**

**Why carved islands, not random openings** (both reviewers; the sizing below): island-safety is guaranteed
for the nominated goals without conditioning the walls on a rare event, and the tree is kept everywhere except
the two roundabouts and the k_r openings.

**Sizing** (`scripts/e3d_sizing.py`, seed 20 261 010, 400 mazes per row; `docs/E3/e3d-sizing.json`, with the
carved rows' placement histograms; it sizes the design, and no reading depends on it):

| c | construction | k | first-draw feasible (bound 4) | placements seen (of 78 at c = 6, 16 at c = 5) | effective placements | open share, all draws; accepted |
|---|---|---|---|---|---|---|
| 5 | random openings | 6 / 8 / 10 | 0.18 / 0.33 / 0.40 | 16 / 16 / 16 | 13.9 / 13.1 / 9.9 | 0.75 / 0.80 / 0.85; the same |
| 5 | carved, k_r | 0 / 2 / 4 | 0.60 / 0.53 / 0.36 | 16 / 16 / 16 | 14.8 / 15.1 / 15.0 | 0.75 / 0.80 / 0.85; 0.74 / 0.79 / 0.83 |
| 6 | random openings | 6 / 8 / 10 | 0.34 / 0.59 / 0.78 | 77 / 78 / 78 | 64.6 / 66.7 / 66.1 | 0.68 / 0.72 / 0.75; the same |
| 6 | carved, k_r | 0 / 2 / 4 | 0.73 / 0.72 / 0.70 | 73 / 73 / 71 | 62.8 / 62.8 / 61.4 | 0.69 / 0.73 / 0.76; 0.69 / 0.72 / 0.76 |

- **"Seen" is the observed support,** not a proof that the other pairs are impossible.
- **The effective number** is the exponential of the entropy of the accepted placements. The proposal is
  uniform; acceptance is not (pairs that are close on the grid fail the distance's lower bound more often).
- A tree opens 35 of 60 internal segments at c = 6 (0.58).
- At c = 6, the infeasible carved draws almost all fail only the distance's lower bound: 322 of 337 across k_r.
- **The sizing's sampler matches §2** (the nesting, the excluded goal sides), but draws its own stream. It
  validates neither the production keying nor the redraw; the tests do (§7).

**The scent's reach** (both reviewers): the scent is a Gaussian of the free-path distance d from the goal's
centre, zero beyond d = 9 (`maze_world.py:234-240`). At d = 9 it is below the scripted follower's threshold of
0.005, so for that follower a goal is detectable only within d ≤ 8. Below threshold it explores as W2.
- **The perimeter track:** the free grid cells 8-adjacent to a perimeter-component wall cell.
- **The flag,** per goal: whether some track cell lies at d ≤ 8. It is a grid-field proxy. Actual nose readings
  use offsets, bilinear interpolation and occlusion, and the neural seed has no hard threshold, so it is not an
  exact detectability class for every navigator (Astra).
- **Reported, not constrained:** the flag's share, and the follower's and the seed's visits and zero-visit
  shares split by it. Zeros on unflagged goals are read as a discovery cost that the task imposes on
  scent-guided controllers. The gate is computed on all mazes.

**Scramble mode** (the scrambled-cells probe) asserts equal open-cell counts across a batch
(`maze_world.py:263-266`); carved mazes differ in their counts. It is refused for the island family.

## 3. The controls and organisms

All play E3b-1's world except for the maze: c = 6, H = 2 400, colonies of 8, shared trails (μ 0.01, λ 0.02,
δ 0.05, d₀ 1.142), the scent's σ and reach, and the visit rule (the head inside the goal's 3 × 3 block).
Scores are the colony mean of visits per wey, averaged over mazes, paired across conditions.

**The blind family.** None senses scent or trail; "noses removed" is E3c's probe (`AT.without_scent`: the four
A/B nose channels at gain 0, which carry trail and scent together). Its best member on a block is B_max:

| Control | What it is | Settings |
|---|---|---|
| Wall-follower | new, scripted, privileged wall sensing (below) | left-handed and right-handed |
| W2 | the neural W2 carrier (E3b-1's organism, not E3b-0's scripted steady state) | one |
| W2-turn | neural W2 with its carrier's turn bias set for a resting turn r (E3c's reference) | E3c's grid {−0.8, −0.4, 0, 0.2, …, 1.4} plus {1.6, 1.8, 1.95} |
| W2+M40, W2+M80 | the carrier with E3b-0's oscillator, which flips the hugged side on a timer | two |
| Random walk | E1's persistent random walk plus W1's reflex (scripted) | persistence {0.25, 0.5, 0.8} × rate {0.5, 1, 2}, speed 1 |
| Noses removed | the frozen seed and all 28 of E3c's champions (S-mod 8, S-dense 8, P-sel 4, P-joint 8) with their noses removed | twenty-nine |

- **The noses-removed row includes the P arms and the seed** (Astra): E3c found P-sel's four champions
  nose-independent and P-joint's scoring 2.85-5.96 with their noses removed on its test block
  (`experiments/E3-ab-organism/E3c/evaluate.json`), so they are known scent-free adversaries.
- **W2-turn's bound:** |r| < 2, from `carrier_turn`'s atanh(r/2) (`maze_organisms.py:140`). Any r ≥ 1.0 already
  saturates the resting turn at the world's clamp, so the points from 1.0 up differ only in how much left
  collision it takes to unsaturate the reflex (Fable). W2 is played right-handed only: the maze distribution
  is mirror-symmetric, so a mirrored W2's expected score is the same.
- **A trail-using, scent-free controller is absent by construction:** the noses read trail and scent as one
  field (`maze_world.py:341`).

**The scripted wall-follower** (`maze_controls.WallFollower`, new):
- **Senses:** the world's wall raster, read as a Boolean lookup of the grid cell containing each probe point;
  a point outside the grid counts as wall. Three probes from the head: ahead at 1.5 grid cells; the hugged side
  at 1.0 cell, 90° from the heading; and ahead on the hugged side at 1.4 cells, 45°. It never reads scent or
  trail. It is privileged, as the oracle is; whether it hugs better than W2 is measured, not assumed.
- **The convention:** heading θ in the world's (x, y) frame; a positive turn command increases θ
  (`world.py:955`). Left-handed: the hugged side is θ + 90°, and "toward the side" is a positive turn.
  Right-handed: θ − 90°, a negative turn.
- **The policy:** wall ahead → full turn away from the hugged side; no wall at the side probe and none at the
  ahead-side probe → full turn toward it; otherwise straight. Forward drive 1.
- **The turning radius** at full turn is 0.35 / 0.30 ≈ 1.17 cells (`config.py:90,92`), which is why the ahead
  probe sits at 1.5 cells. At a tight concave corner it may still meet the wall and rely on the world's refusal
  and sliding (`maze_world.py:321-328`); the qualification tests record whether it does.
- **Its qualification** (§7), required before its island results are read: on hand-built layouts, it acquires
  a wall from a cell centre, rounds convex corners and isolated posts, stays on its component when another
  component lies across a corridor, and makes a full tour of a tree maze. Its switch rate on 6 × 6 trees is
  reported.
- **Declared asymmetry:** it starts like every other control, at a spawn centre with a random heading. A
  separate diagnostic starts every blind control alike tangent to a known wall; it is reported only.

**The navigators:**
- **The oracle** (E3b-0's), the reference ceiling. It is privileged and steers at the next hop of a shortest
  graph path over `Maze.edges`, so it uses loops. Its continuous trajectory is not exactly shortest, and it is
  not a proven optimum.
- **The scripted scent follower** (E3b-0's), under shared trails and under none.

**The organisms,** intact: the frozen seed E + W2 (P-fixed) and E3c's 28 champions, frozen from their saved
genomes and checked by hash. Their noses-removed plays are the blind family's last row.

**Who plays where:**

| Block | Blind family | Navigators | Seed intact | Champions intact |
|---|---|---|---|---|
| Calibration (islands, k_r = 0, 2, 4) | all | all | yes | no |
| Confirmation (islands, the chosen k_r) | all | all | yes | yes |
| Tree reference (6 × 6 trees) | all | all | yes | yes |

## 4. The blocks and the choice of k_r

**The blocks** (maze run seed 1 190 000; E3b-1's was 1 180 000):
- **calibration:** ids 30 000-30 127, islands, at each k_r ∈ {0, 2, 4};
- **confirmation:** ids 30 200-30 455, islands, at the chosen k_r only, played once;
- **the tree reference:** ids 30 200-30 327, the default tree family at c = 6. It separates the island effect
  from the size effect (Fable): a coverer's visits scale with the lap, and the perimeter lap grows from 48
  directed moves at c = 5 to 70 at c = 6, so size alone predicts about 0.69 × for a coverer.
  - It compares whole maze families, placement rules included, not the carving alone (Astra).
  - Paired tree-island comparisons use the common ids 30 200-30 327. The predictions' arm-mean ratios over the
    full blocks are descriptive.

**Choosing k_r** on the calibration block: **the smallest k_r** whose point estimates meet G1-G3 (§5) and the
oracle's precondition, and whose first-draw feasible share is at least 0.5. The smallest, not the largest gap,
because each opening removes maze structure (Astra).
- If none qualifies, the verdict is **"E3d: failed at calibration"**, naming each k_r's failed criteria.
  Neither the confirmation nor the tree reference is played.
- A revised construction needs a fresh calibration block and a fresh confirmation block.

**The benchmark:** B_max on a block is the maximum, over every blind member and setting played on that block,
of its mean visits per wey. Nothing is selected on calibration and frozen; taking the maximum of all of them on
confirmation is conservative, and it is declared now.

## 5. The gate (on the confirmation block)

**Definitions** (`maze_measures`; Astra): a wey's legs are its visits minus one (at least 0); a round trip is
legs ≥ 2, three visits (A → B → A).

| | Criterion | Why | On E3b-1's 5 × 5 trees |
|---|---|---|---|
| G1a | B_max ≤ 0.25 × the follower (shared) | the circuit no longer competes | 5.77 / 16.98 = 0.34: fails |
| G1b | B_max ≤ 2.0 mean visits per wey (one leg) | low blind throughput | 5.77: fails |
| G2a | the follower (shared) ≥ ⅓ of the oracle | navigation remains efficient | 16.98 / 34.5 = 0.49: passes |
| G2b | the follower (shared) ≥ 4.0 mean visits per wey | navigation is absolutely possible | 16.98: passes |
| G3a | the seed − B_max ≥ max(0.5, 0.10 × the seed) (E3c's dual margin) | the engineered navigator beats the blind family by a practical margin | 5.12 − 5.77 < 0: fails |
| G3b | the seed's median, over mazes, of the colony-mean legs per wey ≥ 2 (E3b-1's form, `scripts/e3b1.py:1348`) | it shuttles, not only arrives | (not computed) |

- **The tree column** shows the gate is informative: the task E3c measured fails G1 and G3 and passes G2. Its
  values come from different blocks (the oracle from E3b-0, the follower from E3b-1, W2-turn and the seed from
  E3c), and B_max there is W2-turn's alone, a lower bound on the tree family's. It illustrates; the 6 × 6 tree
  reference block gives the paired comparison.
- **Round trips are reported, not gated:** each blind member's share of weys completing a round trip. §1(a)
  claims a low average throughput, not that every blind wey rarely succeeds (Astra).
- **The oracle's precondition,** on calibration and confirmation alike: the oracle scores at least the shared
  follower's mean, and at least 95% of its weys make a visit. Otherwise the verdict is **"E3d: not
  evaluable"**: the oracle reference failed to qualify on this family, a fault or a limit of the oracle, to be
  found before anything else is read.
- **Uncertainty:** each gate quantity is reported with a 95% bootstrap interval, resampling the paired mazes
  (colonies intact; 2 000 resamples; seed 20 261 011) and recomputing B_max as the maximum over all blind
  settings inside each resample. The gate itself is acceptance on this fixed block's point estimates, and it is
  described that way.

**The verdict:** **"E3d: passed"** if G1-G3 all hold and the precondition is met; **"E3d: failed"** otherwise,
naming the failed criteria.

**How a G1 failure is read** (§6's records; possible explanations to check against the trajectories, not
identified causes):
- **a blind member whose visits follow goal-ring contact after contact with another component:** component
  switching (the island might also be the first component it acquired, which the acquisition record shows);
- **a random walk:** the walk reaches the goals; an open or small maze is one possible explanation;
- **a member with noses removed:** a controller evolved on another family solves this one without scent, the
  case E4 cares most about;
- **visits with little wall contact:** free-space excursions; the trajectories are inspected.

**A G3a failure while G1 passes** can only mean the seed itself scores below about 2.5 visits per wey on the
family. That is read as a failure of the engineered navigator or of the scent's reach on this family, not of
the blind family or the construction (Fable).

**The E3c champions** (descriptive; the predictions stated now, against the 6 × 6 tree reference):
- **The S arms:** each S arm's mean intact visits on the island confirmation block is at most 0.5 × its mean
  on the tree reference. Per-champion ratios are reported.
- **P-joint:** the arm's mean keeps at least 0.5 × its tree-reference mean. Tentative: E3c found four partial
  and four nose-dependent champions, with a large nose-free component. Keeping half the score is not keeping
  navigation, so the noses-removed scores are reported beside.
- **Readings:** S champions that keep shuttling intact but fall with their noses removed are using scent here,
  which defeats the collapse prediction but not the anti-blind aim. If they keep shuttling with their noses
  removed, G1 already reflects it.

## 6. What is recorded and reported

The records are observers computed from the rollout's positions and events; they cannot alter it.

**For every control and organism, on every block:**
- **throughput:** visits per wey (colony mean), legs, round trips and the zero-visit share; the later-leg rate
  as `maze_measures.later_leg_rate` defines it (legs per 1 000 ticks after the first visit, over weys with a
  first visit, and the share without one);
- **discovery:** the first tick the head enters each goal's 3 × 3 block, whatever the goal order (a raw entry
  record, new; the world's `first_b_tick` counts only a B visit after A). Nonarrivals are censored at H; the
  share arriving and the censored median are reported;
- **goal-block occupancy,** a flag separate from contact (Astra): the head inside a goal's closed 5 × 5 block;
  its share of ticks;
- **physical component contact** (both reviewers), from the raster's component labels (4-connected):
  - **contact:** each tick, the components with a wall cell in the head's 3 × 3 neighbourhood;
  - **classes:** perimeter (touches the grid's border); goal ring (not perimeter, with a cell in a goal's closed
    5 × 5 block); other island. On a tree every wall is in the perimeter component;
  - **the remembered component:** unchanged on a tick with no contact; on a tick with contact, kept if it is
    among the contacted components, otherwise the one with the most cells in the neighbourhood, ties to the
    smallest label;
  - **reported:** each class's share of ticks; the first component acquired and its class; the switch rate
    (changes of the remembered component after the first acquisition, per 1 000 ticks; zero on a tree), in
    total and by class pair, since a wey circling a roundabout changes between pieces of one goal's ring
    (Fable); and,
    at each visit's tick, the remembered component's class and the class of the last remembered component
    that is not one of the visited goal's ring components (or none);
- **coverage:** the share of maze cells whose open block the head entered.

E3c's tour match assumed the tree's 48-move circuit, so it is not used; contact and coverage replace it.

**Per maze:** the placement, the redraw index, each goal's entrance count (its tree degree), the number of spawn
cells available, the scent-reach flags, and
the maze-ness measures: the open share, the junction (degree ≥ 3) and dead-end counts, the A-B detour (graph
distance over Manhattan distance), and the share of spawn-goal pairs in direct line of sight. All of these are
reported over the accepted mazes.

## 7. Code, tests and equivalence

**Code:**
- `maze.islands_for(run_seed, maze_id, c, k_r)` and its checks; `maze_for` takes a family argument;
- a `maze_family` field in the maze world's config: "tree" (the default, E3b-1's generator) or "islands", with
  `maze_extra_openings` k_r;
- `maze_controls.WallFollower`;
- the entry, contact and coverage records and the maze-ness measures in `maze_measures`;
- `scripts/e3d.py` on E2's frame, with stages `project`, `g-e`, `calibrate`, `confirm` (the confirmation and
  the tree reference) and `report`, inside `wormwars.accounting`.

**The random streams,** fixed: the walls, the goals, the swap and the k_r order by (run seed, maze id, redraw
index; the carving itself is deterministic); the spawns by E3b-1's episode stream (episode 0); the random walk's noise from `ReflexWalk`'s
seed 0. The walk's draws depend on the batch's shape, so each block's composition (worlds per chunk, colony 8)
is fixed in the runner and recorded.

**Tests first** (each seen failing):
- **the labelling and island-safety** on hand-built grids, with a sabotage case where a ring touches the
  perimeter;
- **the construction:** raster and `Maze.edges` agree; the roundabout (all eight ring-road segments open);
  exactly k_r openings beyond the carving, none on a goal's side; nesting across k_r at a shared redraw index;
  connectivity; island-safety; no shared component; the distance bound on the final graph;
- **the keying:** deterministic per (seed, id, redraw); independent of the episode; the A/B swap; the error
  after 64 redraws;
- **the spawns:** no island wall cell in a spawn's block; their distance from the goals;
- **the oracle on loops:** on hand-built loop mazes, its waypoints follow a shortest graph path, and it reaches
  both goals;
- **the wall-follower:** acquisition, convex corners, isolated posts, retention across a corridor from another
  component, both handednesses, a full tree tour; and a sabotage test that its commands are unchanged when the
  scent field is scaled up;
- **the records:** on scripted paths, hand-computed legs, round trips, later-leg rates, raw entries with
  censoring, goal-block occupancy, contact classes, the tie rule, switches, the components at each visit, and
  coverage. Hand-computed cases include a centre-line goal entry with no wall nearby, a fragmented ring, and a
  tree goal (all contacts perimeter, no switches) (Astra);
- **the maze-ness measures and the scent-reach flag** on hand-built mazes;
- **W2-turn's bound:** 1.95 accepted, 2.0 refused;
- **the bootstrap:** B_max recomputed inside each resample;
- **scramble refused** for the island family.

**Rule 7** (`g-e`), with `maze_family` = "tree":
- E3b-1's `maze-reference.json` is reproduced bitwise;
- E3c's g-e legs pass again: the CPU equivalence reference and E2's GPU batch;
- **a new full-rollout leg:** tree-family maze rollouts from 40bd50f against the new code, at zero tolerance,
  comparing positions, headings, goals, visits and events per tick.
  - **Pinned:** the scripted follower and the seed; maze run seed 1 190 000; maze ids 30 000-30 007;
    episode 0; c = 5 and c = 6; H = 2 400; colonies of 8; 8 worlds per chunk; shared trails; float32.
  - **Run on** the CPU, and on the GPU inside `replay_mode()` in that composition.
  - **One driver for both engines:** the new driver, run with `--root` at a worktree of 40bd50f for the
    reference, as `scripts/e3_equivalence.py` does. The reference is committed with its hash.

**Compute:**
- no evolution: plays only;
- a ceiling of 3 GPU-hours. `project` measures the cost first;
- if the projection exceeds the ceiling, the reductions apply in order:
  1. the random walk's grid to persistence 0.5 at three rates;
  2. the W2-turn grid to {−0.8, 0, 0.4, 0.8, 1.2, 1.4, 1.95};
  3. the tree reference to ids 30 200-30 263.
- If it still exceeds the ceiling, nothing is played and the owner is asked.

## 8. Binding

After the last check by both reviewers, this design is committed and pushed, and its commit and the file's
sha256 are written into `scripts/e3d.py`. `calibrate` refuses unless the design is unchanged and the engine
matches the commit after `g-e`. Any change after binding is an amendment, added beside the text and dated,
and re-binds at its own commit, as E1's `require_same_code` guard does (`wormwars/registration.py`).

## 9. What E3d is for

If it passes, E4 uses this family at the chosen k_r, with its own blind references. If it fails, the failed
criteria say what the next construction must change, and the roadmap stays paused before E4 until the owner
decides.

## 10. Changes

**From v1** (both reviews, D222):
- the maze size, 6 × 6, the owner's choice on the recomputed sizing;
- carved islands plus k_r openings replace random openings;
- full feasible placements in the sizing, a committed script and seed;
- no wall component touching both goals; spawns that mirror island-safety; the spawn claim corrected;
- the blind family, its maximum the benchmark; neural and scripted W2 kept distinct;
- absolute limits beside the ratios; G2 recalibrated, with the tree values shown; a practical margin and
  repeated shuttling for G3; the smallest qualifying k_r; the confirmation benchmark declared; bootstrap
  intervals; the oracle's precondition;
- component contact, discovery, round trips, maze-ness and scent reach recorded; tour match dropped;
- the champions: a contradiction reported as one, noses-removed plays, P-joint's prediction tentative;
- code points and a full-rollout rule-7 leg.

**From v2** (both reviews, D223):
- **the k_r openings exclude the goals' own sides;** the roundabout stated; the "soften the neighbourhood"
  claim dropped (Fable);
- **the sizing rerun** with the production sampler's nesting and exclusions; "seen", "accepted", the
  histograms, the open share over accepted mazes (both);
- **the blind family** takes the seed and every E3c champion with noses removed (Astra);
- **G1b's and G2b's wording** follows the codebase's legs; "rarely completes a round trip" narrowed to a low
  average throughput, with round trips reported (both);
- **contact in three classes,** goal-ring contact on the closed 5 × 5 block, acquisition and the component
  before each visit; the false "impossible" reading removed and every G1 reading qualified (both);
- **a 6 × 6 tree reference block,** and the champions' predictions stated per arm against it (Fable);
- **the keying** of A, B and the openings, the swap, episode 0, the random walk's stream (both);
- **the wall-follower:** the probe rule, the convention, the ahead probe at 1.5 cells, a qualification with
  corners, posts and separated components (both);
- **the measures:** the later-leg rate and G3b's median defined; raw entries for discovery; the scent flag a
  proxy (Astra);
- **the bootstrap** recomputes B_max per resample; the oracle's precondition on both blocks and its reading
  (both);
- **who plays where;** the reductions and a stop rule (Astra);
- **the rule-7 leg pinned;** binding before `calibrate` (both).

**From v2.1** (both reviews, D224):
- **contact:** physical contact by raster component, with goal-block occupancy a separate flag; the remembered
  component, the tie rule and the components at each visit defined (both);
- **P-joint's noses-removed range** cited correctly (Fable);
- **the shared follower** named in G2 and the oracle's precondition; the oracle's "a visit" defined (Fable);
- **the G3a-only reading;** the goals' entrance counts; the streams shared with the tree family; the tree
  reference's scope (both);
- **the rule-7 pins** (run seed, episode, dtype, one driver) and re-binding after an amendment (Fable).

**At binding** (both said "bind" on v2.2, D225): the remembered component on any tick with contact; switches by
class pair; "the carving order" dropped from the random draws (Fable's non-blocking points). The reference leg
at 40bd50f calls that commit's own signatures, as `scripts/e3_equivalence.py`'s "only APIs both have" rule says.

## 11. Amendments (after binding; each re-binds at its own commit)

### Amendment 1 (2026-10-10, before any play): the wall-follower's search state and probe rays

**Found by** §3's qualification tests (`tests/test_e3d_wall_follower.py`), which the bound text requires before
the wall-follower's island results are read. The policy as bound failed them in two ways:
- **It circled forever** in open space and in a corridor's centre. With both side probes clear it turns
  toward the hugged side at full turn, and on that circle the side probe always points at the circle's centre,
  so it never meets a wall. From an open box's centre it never reached a wall in 800 ticks.
- **It stalled against a wall it never sensed.** A single probe point 1.5 cells ahead jumps over a 1-cell wall
  and lands in free space beyond, so the policy went straight into a wall that refused the move. Three of ten
  6 × 6 tree mazes stalled at the spawn.

**The amended policy** (`wormwars/e3/e3d_controls.py`):
- **Probes read along their rays:** each probe reads the grid cells at every half cell out to its range (ahead:
  0.5, 1.0, 1.5; side: 0.5, 1.0; ahead-side: 0.5, 1.0, 1.4), any wall counting.
- **A search state:** "both clear → full turn toward the hugged side" applies only for 12 ticks (3.6 rad at the
  full turn) after either side probe last sensed a wall; after that, and before the first wall, it goes
  straight. The counter resets whenever a side probe senses a wall.
- **Everything else as bound:** the probes' ranges and angles, "wall ahead → full turn away", forward 1, the
  convention, no scent or trail.

**The qualification after the amendment,** both hands: from an open box's centre at 8 headings it reaches a
wall within 120 ticks and keeps one within its head's 3 × 3 neighbourhood on at least 90% of later ticks. It
orbits a 3 × 3 pillar and a single post for 2 400 ticks, touching nothing else. Beside a corridor it never
contacts the island bar across it. It tours all 36 cells of each of ten 6 × 6 tree mazes in about 700-850
ticks. The tree mazes are ids 40 000-40 009, not the trees under E3d's blocks. The post test's thresholds were
set after its first run (§7's tests record this).

**What the bound text leaves open, fixed here:** §3's tangent-start diagnostic plays every blind member on the
confirmation block's first 64 mazes (ids 30 200-30 263), at the chosen k_r, reported only
(`e3d_controls.tangent_start`).

**Placement, not policy:** the wall-follower lives in `wormwars/e3/e3d_controls.py` and the records in
`wormwars/e3/e3d_records.py`, not in `maze_controls` and `maze_measures` as §3, §6 and §7 name them. E3b's
modules stay untouched. The records' contact is computed by `contact_batch`, which a test holds equal to the
readable `contact`.

**Correction to Amendment 1** (2026-10-10, after both reviewers' code review, D227; Astra): "before any play"
should read **before any formal block play**. CPU smoke runs of the stages had played toy mazes (ids 8 000-8 004,
H = 60, and timing mazes 40 100-40 115) before the amendment's commit. So had the qualification and equivalence
rollouts. None used a calibration, confirmation or tree-reference id at the formal horizon. The amended policy is
a declared strong wall-following control, not a proven strongest hugger. Its qualification thresholds are
engineering criteria, not evidence.

**Erratum to that correction** (2026-10-10, D228; Fable): "none used a calibration, confirmation or tree-reference id
at the formal horizon" is not quite right. The equivalence leg plays trees with ids 30 000-30 007 at H = 2 400.
The accurate statement: none played a formal block's maze, that is, an island maze at a formal id or the 6 × 6
tree reference.
