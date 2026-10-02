# E3b: trails, branching mazes and the colony (design v1, 2026-10-02)

Status: v1, for review by Astra 6 and Fable 5.1. Nothing has run. A pre-registration follows only if
both agree.
- **Its basis:**
  - the roadmap's E3 section (the trail table, the gate, the peer-signal controls) and D144's additions;
  - E3's staging (`docs/E3/DESIGN.md`: E3a the shuttle, E3b this, E3c the assembly comparison);
  - E3a's published results (D169).
- **The owner's ceiling:** about 30 GPU-hours for E3b (D159).
- **The frame, as in E3a:** stereo sensing is a game-design choice. The organisms are circuits on a
  silent worm, outside the N2 mask. Nothing here is about worm or ant behaviour.

## What E3b must answer (the roadmap's gate)

"Repeated alternating journeys, counted with an event ledger, on unseen branching mazes, and better than
the seed design." Plus the peer-signal controls:
- shared trails;
- own trails only;
- scrambled or replayed peer trails;
- a colony evolved without trails from the start.

**The seed design** is E3a's engineered organism, carried into the maze. E3a's results suggest
three things:
- composition works (E at 97% of a module fed the goal's scent);
- joint tuning helps (+2.36);
- evolving a selector from scratch rarely works.

E3b therefore evolves *from* the seed. It does not build a selector from nothing.

## What the engine lacks (found by survey; `wormwars/world.py`, `fields.py`)

- **No interior walls or mazes.** The WALL channel is only the boundary ring, and a blocked head stays
  in place, with no sliding.
- **One pheromone channel per swarm,** deposited automatically at a constant rate. It diffuses through
  walls (the 3×3 kernel ignores WALL), so there is no A trail and no B trail.
- **The shuttle task allows one wey per world.** Its goal, visits and ledger are per world, not per
  wey.
- **No per-wey timer** (for "time since the last confirmed visit").

## The staging (proposed)

**E3b-0 (exploratory; engine, controls and the seed's feasibility; at most 3 GPU-hours).**
- **The engine changes:**
  - a maze generator;
  - two trail channels per swarm, masked by walls;
  - per-wey goals, ledgers and deposit timers;
  - wall sliding (proposed).

  Each is test-first, with an equivalence check against the current engine with the new task off
  (rule 7).
- **The controls, scripted:**
  - a path oracle (BFS on the maze);
  - a scripted trail follower with a perfect memory;
  - blind baselines (a random walk and a wall follower).
- **The seed in the maze,** alone and as a colony, with trails on and off.
- **It ends with a plan for E3b-1:** whether the seed does the task, how its score depends on colony
  size and trails, and the cost per rollout.

**E3b-1 (confirmatory; pre-registered; the gate and the peer-signal controls; about 25 GPU-hours).**
- **Joint tuning of the seed,** as E3a's Stage 3, in colonies, on training mazes.
- **The registered readings:** the tuned colony against the seed on unseen mazes (the gate), and the
  peer-signal controls.

## The task: the maze shuttle (proposed)

- **The maze:** a branching tree maze per world, drawn from the world's own stream.
  - Corridors 3 cells wide, walls 1 cell thick, on an arena of about 33 × 33 (a 5 × 5 grid of cells).
  - Generated as a random spanning tree, so there is exactly one route between any two places, and
    dead ends.
  - **A and B** are at two dead ends, with a path distance between them in a declared range.
  - **The spawn** is at a third dead end.
- **The scents are local only:** each source's scent follows path distance (BFS) with a short range (about
  3 corridor cells). It guides the last approach, not the route.
- **The trails** (the roadmap's table):

  | The wey's goal | It follows | It deposits |
  |---|---|---|
  | find A | the A trail | the B trail (it came from B) |
  | find B | the B trail | the A trail |

  - **Deposit is engineered,** not a brain output (labelled so):
    - a wey deposits only after its first confirmed visit;
    - the strength falls with time since its last confirmed visit (an engineered per-wey timer, as the
      roadmap says).
  - **The trails** evaporate and diffuse only through open cells.
- **The visit events:** E3a's contract, per wey. Each wey has its own goal (the scorer's state), starting
  at A, and its own ledger. A colony's score is its confirmed visits per wey per episode.
- **The signals to the brain:**
  - each module's noses read its trail plus its source's local scent, bilaterally. Module A reads the A
    trail and A's scent; module B reads the B trail and B's scent;
  - the visit levels and start cue are E3a's;
  - **the collision sensors (proposed):** routed to the turn neurons through a small engineered wall
    reflex, labelled hybrid. Otherwise a carrier with a fixed turn bias jams in corridors.
- **The colony:** a declared number of weys per world (for example 8), one genome per colony, sharing the
  trails.
- **The horizon:** long enough for several journeys after the trails form (for example 1 200 ticks).
  Set in E3b-0.

## The peer-signal controls (E3b-1)

- **Shared trails** (the default): every wey senses the colony's trails.
- **Own trails only:** each wey senses only what it deposited itself. This needs per-wey trail fields or
  masks; their cost is measured in E3b-0.
- **Replayed peer trails:** each wey senses a colony's trails recorded in another episode of the same
  maze (peer signals present but not coupled to its colony), or scrambled ones (the same total,
  displaced).
- **No trails from the start:** a colony evolved with deposit off, the same budget.

## Measures (sketch; fixed in E3b-1's pre-registration)

- **Confirmed visits per wey,** and alternation: the share of visits that alternate correctly, from the
  ledger.
- **The first-journey time,** and the time per later journey (does the colony speed up as trails form?).
- **Which wey found what first:** the trails' contribution as later weys' speed-up.
- **The memory assays,** carried over from E3a for the tuned organisms.

## Open questions for the reviewers

1. **The staging:** E3b-0 exploratory, then E3b-1 pre-registered. Is E3b-1 too large for about 25
   GPU-hours, with colonies of 8 weys × 313 neurons?
2. **"Better than the seed design":** is joint tuning of the seed, judged against the seed on unseen
   mazes, the right reading of the gate? Or should a selector or trail use also be evolved?
3. **The wall reflex:** engineered and labelled, or evolved, or left out (with wall sliding only)?
4. **The local scents:** path-distance scents with a short range, or none (trails and visit levels
   only)?
5. **Tree mazes only,** or loops as well (several routes)?
6. **Prior art,** from memory and not verified:
   - the classic two-pheromone ant-foraging model ("home" and "food" pheromones; Resnick's StarLogo ants;
     Panait & Luke, "Ant foraging revisited", 2004);
   - Deneubourg's double-bridge experiments.

   Should a literature check come before E3b-0, under the project's standard (D143)?
7. **The own-trails control** needs per-wey fields. Is a mask-based approximation acceptable?
