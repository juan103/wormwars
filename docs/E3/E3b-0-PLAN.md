# E3b-0's plan: the engine, the controls and the task's feasibility (v1, 2026-10-02)

Status: v1, for review by Astra 6 and Fable 5.1. Nothing has run.
- **Its design:** `docs/E3/E3b-DESIGN.md` v2, agreed (D173). This plan pins what both reviewers listed.
- **E3b-0 is exploratory.** Its job is to show that E3b-1 can detect an advantage and that a null would be
  interpretable. It does not test evolution.
- **The budget:** at most 3 GPU-hours. CPU work is not capped.
- **Its records** are committed. Failed settings are reported, not only the chosen ones (Astra).

## 1. The engine changes (test-first; rule 7)

**The reference commit is 84ff98a,** the last before any E3b change.
- **Equivalence, with every new flag off:**
  - on the CPU, bitwise for Task N, foraging, E3a's shuttle and E4s-1's graft, by
    `scripts/e3_equivalence.py`, extended with E3a's shuttle;
  - on the GPU, E2's GA generations 0-25 hashes.
- **Every new behaviour** has a test seen failing first, and a sabotage check where a check could not
  fail.

### 1a. The maze (`task = "maze_shuttle"`)
- **The generator:** a random spanning tree (randomised depth-first search) on a c × c grid of maze cells.
  - Corridors are 3 cells wide and walls 1 cell thick, so the side is 4c + 1.
  - It is drawn from a maze stream keyed by (run seed, maze id), separate from the episode stream keyed by
    (run seed, world id). So the same walls can carry different episodes.
- **The free-cell graph** is 4-connected. Path distances are by breadth-first search over free cells.
- **Placements,** at dead ends:
  - A and B at two distinct dead ends, with their tree distance (in maze cells) in [⌈c/2⌉ + 1, 2c];
  - the spawns at up to 4 other dead ends, each at least 2 maze cells from A and from B;
  - the colony's weys spread over them round-robin.
- **Visit regions:** a source's region is its dead-end cell's 3 × 3 open block. inside(X) is "the head is
  in X's region".

### 1b. Movement
- **Per-axis sliding** (a flag):
  1. try the full step;
  2. if the head's proposed cell is a wall, try the x-step alone, then the y-step alone;
  3. otherwise stay.
- **Corners:** a diagonal step that would pass between two wall cells sharing only a corner is refused. A
  test covers it.
- **Movement limits:** 0.35 cells per tick at full forward drive, and 0.30 rad per tick at full turn
  (unchanged).

### 1c. The trails (exact per-wey fields, linear)
- **Storage:** per world, a field of shape [weys, 2 (A, B), side, side], float32.
- **Per tick, in this order:**
  1. **sense:** each wey's noses read their channel. Shared is the sum over weys, own is the wey's slice,
     peers is shared minus own;
  2. think;
  3. move;
  4. **events:** entries and confirmed visits per wey, with the goal switching at a confirmed visit;
  5. **timers:** a wey's t (ticks since its last confirmed visit) resets to 0 at a visit, else grows by 1;
  6. **deposit:** a wey with a visit behind it adds d₀·exp(−λ·t) at its head cell to the trail of the
     source it came from. While its goal is A, that is the B trail, and the other way round. Because the
     timer resets in step 5, a visit's first deposit is d₀ at the source just visited;
  7. **diffuse and evaporate:** for each field, each open cell sends a fraction δ of its mass equally to
     its open 4-neighbours (no flux into walls, mass conserving), then every cell is multiplied by
     (1 − μ).
- **No clamp anywhere on the fields,** so shared stays the exact sum. A test checks linearity:
  shared = Σ own, bitwise on the CPU.
- **Rate conventions:** μ and δ are per-tick fractions, and λ a per-tick rate.
  - **The polarity condition** from the simplified single-pass model (no revisits, no diffusion) is
    λ > −ln(1 − μ) (Astra).
  - It is a guide only. Revisits, stationary deposition, diffusion and superposition can break it, so
    polarity is measured (§3b).

### 1d. Sensing and occlusion
- **The noses read bilinearly,** as now: head + 0.6·forward ± 0.5·left.
- **Occlusion (Astra):** a nose point that lies in a wall cell, or whose segment from the head crosses a
  wall cell, reads 0 on every trail and scent channel. A test puts a head 0.01 from a wall with signal
  only on the far side, and checks that every reading is 0.
- **The local scents:** each source's scent is A·exp(−p²/2σₚ²), with p the path distance from the source
  (in cells, by breadth-first search) and σₚ = 3. It is zero beyond p = 9 and zero in wall cells.
- **The nose input** is (trail + scent) × 0.35, the food scaling, clamped to ±5 by the interface as now.
- **The seed's noses:** module A reads the A trail plus A's scent, and module B the B trail plus B's
  scent. The relays read the visit levels, with E3a's cue for ticks 0-4 for every wey. Every wey's goal
  starts at A.

### 1e. Removed peer channels
- crowding is off (`crowd_resist` and `crowd_push` at 0);
- the collision inputs read the WALL channel only;
- no body or BODY field reaches any sensor.

## 2. "Maze-ready": the permitted additions (engineered, labelled, frozen for every arm)

Fable expects the bare seed to oscillate in place: the carrier circles within about ±6 cells. So these
additions are permitted. Each is a hand-built part, named and reported as a baseline on the carrier:
- **W0, sliding only.**
- **W1, a wall reflex:**
  - two neurons reading the wall-only collision sensors (front-left and front-right);
  - they drive the turn neurons away from the nearer wall, at a fixed gain;
  - symmetric.
- **W2, a hand-biased wall reflex:** W1 plus a constant turn toward one side when no wall is sensed.
  - On a tree, this is a wall follower made of neurons.
  - **Known in advance:** it explores every dead end, and trails can only add shortcuts.
- **M, a meander oscillator:** two mutually inhibiting neurons with adaptation give a slow, alternating
  turn bias. Its period P is in {40, 80} ticks.

**The variants are W0, W1, W2, W1+M and W2+M,** each as the carrier alone (a baseline) and as the seed.

**The seed's maze-ready variant** is the one with the highest seed score with shared trails and colony 8,
on the selection mazes. Ties go to the earlier variant in the list. It is then frozen.

**The carrier with the chosen variant** is reported as the blind baseline for that variant.

## 3. The controls and measurements

### 3a. Scripted controls (no neural network; the organism's movement limits)
- **The path oracle:** it follows the breadth-first-search route to the current goal, at the turn limit
  (0.30 rad per tick) and full speed.
- **The scripted trail follower:** the organism's sensory access only, with no temporal comparison
  (Fable).
  - **Its memory** is a goal bit, with no route knowledge.
  - **Its readings:** the bilateral trail-plus-scent readings for its goal's channel, the visit levels and
    the wall-only collision sensors.
  - **Its policy:**
    - if either nose reads above 0.005, it steers by k·(L − R) with k = 32;
    - otherwise it explores as W2 does (a wall follower);
    - W1's wall reflex is always on.
  - **Its trail access:** shared, own only, peers only, or none.
- **Blind baselines:** a random walk (E1's tuned settings), the W2 wall follower, and the carrier's
  circle.

### 3b. The trails' measurements
- **Gradient direction:** for each candidate setting, the share of on-trail cells along routes whose trail
  value rises toward the trail's source. Measured with 1 and 8 contributors, at trail ages up to the
  horizon.
- **The behavioural polarity test** (Fable): the scripted follower is placed mid-trail facing away from the
  source. It passes if it turns round and enters the source within 2 × the oracle's leg time. The pass
  share is measured over 256 placements.
- **The nose range:** the share of on-trail ticks whose nose input lies in L1's qualified range (0.005 to
  0.35), and the share above 0.35 (saturation).
- **Below 0.005:** with empty fields, readings below 0.005 are expected. L1's component tests are rerun at
  0.001 and 0.003 to see its gain there (Astra).

### 3c. The measures (the colony is the unit)
- **Raw entries** into A and B, with wrong and repeated ones.
- **Confirmed visits per wey.**
- **Completed round trips per wey:** an A visit then a B visit, or the other way round. Reported as the
  share of weys with at least k = 2.
- **First-A and first-B times by discovery order,** censored at the horizon. Compared paired, on the same
  colony and maze assignments across interventions (Astra).
- **Later trips:** visits after each wey's first round trip. **Own only cannot help a goal's first
  discovery,** because that trail does not yet exist (Astra). So the peer contrast shared > own > none is
  read on later trips.

## 4. The search (bounded; selection rules fixed here)

**Maze size and horizon:** c ∈ {5, 6, 7, 8} × H ∈ {1 200, 2 400}, on scripted controls only.
- **The rule:** choose the cheapest (c, H), smallest c·H first, then smaller c, satisfying all of:
  1. the oracle makes at least 8 confirmed visits per wey;
  2. the scripted follower, shared, colony 8, completes at least 2 round trips per wey at the median;
  3. the W2 wall follower makes at most 0.5 of the oracle's visits per wey. It is a ceiling for blind
     exploration, not a bar for the seed (Fable);
  4. the random walk makes at most 0.25 of the follower's;
  5. the median first discovery of A by any wey in the colony is at most H/4 for the scripted follower
     (Fable).

**Trail constants,** for the chosen (c, H), with the scripted follower:
- **The grid:**
  - μ ∈ {0.002, 0.005, 0.01};
  - λ = f·(−ln(1 − μ)) with f ∈ {1.5, 3};
  - δ ∈ {0.05, 0.15};
  - d₀ scaled so the first deposit at a source reads 0.2 after scaling, × {0.5, 1}.

  That is 24 settings.
- **The rule:** among the settings that meet all three conditions below, choose the one maximising the
  follower's later-trip visits per wey with shared trails. Ties go to the smaller μ.
  - the polarity test passes in at least 80% of placements;
  - the gradient points to its source on at least 80% of route cells, with 1 and 8 contributors;
  - the nose input lies in L1's range on at least 90% of on-trail ticks, with saturation on at most 5%.
- **The fallback** (Panait-Luke-style) is tried only if no setting passes. It is nonlinear, so if adopted
  the peer controls are redesigned and reviewed before E3b-1 (Fable).

**The seed's variant:** by §2's rule, on the chosen (c, H) and constants.

**Mazes and worlds:**
- **Selection mazes:** maze ids 0-255 of a smoke block.
- **Report mazes:** ids 1 000-1 255, with every reported number taken on them.
- E3b-1's blocks are separate and untouched (a test checks).

## 5. The exit criteria, with numbers (from the design; the colony is the unit)

1. **Mechanics:** every test and the equivalence pass.
2. **A usable task:** on the report mazes,
   - the seed's colony visits per wey exceed the random walk's (`world_ci` lower bound > 0, paired by
     maze);
   - there is headroom: the seed reaches at most 0.8 of the oracle;
   - the seed completes at least 1 round trip per wey at the median.

   The seed against the W2 wall follower is reported, not required. A seed at or above the scripted
   follower is a finding, not a failure (Fable).
3. **A usable signal:** on the report mazes, for the scripted follower,
   - shared − none, and own − none, each with a lower bound above 0.5 later-trip visits per wey;
   - shared − own reported with its interval;
   - for the seed, shared − none is reported.
   - **Each peer control** removes information in a scripted example: own only, peers only, replay and
     scramble, with the size of each loss.
4. **Frozen settings,** recorded with their search tables:
   - (c, H), the colony size (8), the trail constants, the scents and the variant;
   - L1's component tests at trail levels;
   - the memory assays' delay D recalibrated as the seed's median later-trip leg.
5. **A feasible E3b-1:**
   - timings and peak memory at the real composition (4 096 worlds × 8 weys), including the diffusion
     buffers and lockstep donor episodes for replay;
   - a projected E3b-1 of at most 24 hours, with a 25% reserve.
6. **Power for the gate:**
   - the seed's between-maze standard deviation on the report mazes;
   - an assumed run-to-run standard deviation of the tuned colonies' means, stated: from E3a's Stage 3
     champions' test means, scaled to E3b's units;
   - the minimum detectable effect for 8 runs (paired run-level bootstrap, 90%), which must be at most
     0.25 of the seed's mean.
   - The scripted peer effect shows measurement sensitivity only, not power over evolved runs (Astra).

## 6. If a criterion fails

| Criterion | What happens |
|---|---|
| 1 | Fixed and retested; the run waits |
| 2 | **Nothing passes:** the next (c, H) in the search, if one is left; then a report and a redesign, with the owner informed. **The seed fails "above the random walk" or "round trips":** the variant search widens once (P ∈ {20, 160}), then a report and a redesign |
| 3 | The fallback (§4); if it also fails, a report and a redesign |
| 4 | Not a failure: recorded |
| 5 | E3b-1's scope is cut: fewer generations, worlds or weys, then the no-trails arm made descriptive. If even the gate alone exceeds 24 hours, the owner is asked |
| 6 | E3b-1 is resized (more runs, or longer tuning) or redesigned before registration |

**The iteration limit:** each search above runs once on its grid. One widening is allowed, for criterion 2
only. Everything runs inside 3 GPU-hours, with CPU for the scripted searches where possible.

## 7. Records and review

- **The stage frame** is E2's: `scripts/e3b0.py`, with stages for the maze search, the trail search, the
  variant search, the report, and the timing and projection.
- **Each record** is committed and pushed before the next stage.
- **The results report** (`experiments/E3-ab-organism/E3b-0/RESULTS.md`) is reviewed by both before E3b-1's
  design.
