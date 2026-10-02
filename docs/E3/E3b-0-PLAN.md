# E3b-0's plan: the engine, the controls and the task's feasibility (v2, 2026-10-02)

Status: v2, for a confirmation round by Astra 6 and Fable 5.1. Nothing has run.
- **v1** (f6d3532): both said "fix then run" (`docs/reviews/20261002-E3b-0-plan/`; D174). v2 takes every
  fix; §9 maps them.
- **The owner, 2026-10-02:** add E3a's best tuned organism, Stage 3 run 3 (15.98 on E3a's test worlds), as a
  second candidate seed beside E (§2c).
- **The design:** `docs/E3/E3b-DESIGN.md` v2, agreed (D173).
- **E3b-0 is exploratory.** It shows whether E3b-1 can detect an advantage and whether a null would be
  interpretable. It does not test evolution.
- **The budget:** at most 3 GPU-hours, counted through `wormwars.accounting` (rule 8). CPU work is
  uncapped.
- **Its records** are committed, failed settings included.

## 1. The engine changes (test-first; rule 7; every change behind a flag)

**The reference commit is 84ff98a,** the last before any E3b change.
- `scripts/e3_equivalence.py` is extended with an E3a-shuttle case, and its reference is produced by
  running the extended script against a worktree at 84ff98a.
- **Equivalence, with every new flag off:**
  - on the CPU, bitwise, for Task N, foraging, E3a's shuttle and E4s-1's graft;
  - on the GPU, E2's GA generations 0-25 hashes.
- **Each new behaviour** has a test seen failing first, and a sabotage check where a check could not fail.

### 1a. The maze (`task = "maze_shuttle"`)
- **The generator:** a uniform random spanning tree by Wilson's algorithm on a c × c grid of maze cells,
  with 3-wide corridors and 1-cell walls, so the side is 4c + 1.
  - It is already built and tested (00fa5d5).
  - **The measured dead-end share** is 0.29 to 0.32 for c = 5-8, over 200 mazes each. Depth-first search
    gave far fewer, as both reviewers expected.
- **Two streams,** so placement never moves the walls (Astra):
  - the walls from (run seed, maze id, "walls");
  - the placements from (run seed, maze id, episode index, "place").

  Placement uses only the placement stream and never redraws the walls. At c = 5-8 it was feasible for
  all 200 mazes per size. An infeasible maze raises an error.
- **Placements** (at dead ends):
  - A and B, with their tree distance in [⌈c/2⌉ + 1, 2c];
  - the spawns at up to 4 other dead ends, each at least 2 maze cells from A and from B;
  - the colony's weys placed round-robin at the spawn cells' centres, with headings drawn from the
    episode stream.
- **inside(X):** the head is in X's dead-end cell's 3 × 3 open block.
- **Free distances** are by breadth-first search over 4-connected free cells.

### 1b. Movement
- **Wall crossing is refused:** a step whose segment from head to proposed head crosses any wall cell,
  by an exact supercover grid traversal, is refused. That covers single corners (Astra) and diagonal gaps.
- **Then per-axis sliding** (a flag):
  1. try the full step;
  2. then the x-component alone;
  3. then the y-component alone, each under the same rule;
  4. else stay.
- **The limits are unchanged:** 0.35 cells per tick and 0.30 rad per tick.

### 1c. The trails (exact per-wey fields, linear, no clamp)
- **Storage:** per world, [weys, 2 (A, B), side, side], float32. A wey senses shared (the sum over
  weys), own (its slice), or peers (shared minus own).
- **Per tick, in this order:**
  1. sense;
  2. think;
  3. move;
  4. **events:** entries and confirmed visits per wey; the goal switches at a confirmed visit;
  5. **timers:** a wey's t resets to 0 at its confirmed visit, else grows by 1;
  6. **deposit:** a wey with a visit behind it adds d₀·exp(−λ·t) at its head cell, to the trail of the
     source it last visited. While its goal is A, that is the B trail, and the other way round. A
     visit's first deposit is d₀ at the source just visited;
  7. **diffuse (flux form, symmetric and mass-conserving):** x_i ← x_i + (δ/4)·Σ_{open 4-neighbours j}
     (x_j − x_i). Its equilibrium is flat, unlike v1's equal-split rule, which ridged a 3-wide corridor
     at about 3:4:3 (Fable);
  8. **evaporate:** × (1 − μ).
- **Linearity is checked** against a separately evolved single field fed every wey's deposits: equal to
  the per-wey sum within 10⁻⁵ relative, on the CPU. It is not "bitwise", which would be tautological
  (Fable).
- **The polarity guide:** in the single-pass model, λ > m with m = −ln(1 − μ). It is a guide only, and
  polarity is measured (§3b).

### 1d. Sensing and occlusion
- **The noses read bilinearly,** at head + 0.6·forward ± 0.5·left.
- **Occlusion:** a nose reads 0 on every trail and scent channel if its segment from the head crosses a
  wall cell (supercover traversal). Each of its four bilinear support cells contributes only if the
  segment from the nose to that cell's centre crosses no wall cell, and the weights are not
  renormalised. That covers the corner footprint (Astra).
- **Its tests:**
  - with signal only behind a wall or a corner, every reading is 0;
  - an unoccluded nose in open space reads bitwise as before (Fable).
- **Reported:** the share of ticks with at least one occluded nose. A nose at 0 beside a nose on a trail
  is a strong wall-avoidance signal, declared.
- **The local scents:** A·exp(−p²/2σₚ²), with A = 1, σₚ = 3 path cells, and zero beyond p = 9 and in
  walls.
- **The nose input:** (trail + scent) × 0.35, then the interface's ±5 clamp, as now.
- **The seeds' wiring:**
  - module A reads the A trail plus A's scent, and module B the B trail plus B's scent;
  - the relays read the visit levels;
  - every wey's goal starts at A, with E3a's cue for ticks 0-4.

### 1e. Removed peer channels
- crowding is off;
- the collision inputs read WALL only;
- no BODY reaches a sensor.

## 2. The candidate organisms

### 2a. The maze-ready additions (engineered, labelled, frozen for every arm)
- **W0:** sliding only.
- **W1, a symmetric wall reflex:**
  - two grafted neurons, each reading one front collision sensor (wall-only) at gain 1, with bias −0.5,
    so they fire near walls;
  - each drives the 4 dorsal and 4 ventral turn neurons away from its side at weight ±3;
  - the carrier's +0.2 turn bias remains.
- **W2, a one-sided reflex (a wall follower made of neurons):** W1 with the right-side gain at 1.5 and
  the left at 3, plus a constant extra turn of +0.2 when neither neuron fires (+0.4 in total).
  - Its coverage and dead-end escape are measured, not assumed (Astra).
  - Trails can help it, but can also misdirect or trap it.
- **M, an oscillator:** a CTRNN oscillator within the genome's bounds (|w| ≤ 3, τ ∈ [0.5, 20], |b| ≤ 2),
  producing a turn bias of period about 40 or 80 ticks.
  - The engine has no adaptation state (Astra), so M must be found and verified on the CPU before
    E3b-0's searches: a 2- or 3-neuron circuit with a measured period and amplitude.
  - **If none is found within the bounds,** M is dropped and the variants below lose it. That is recorded
    as a result.
- **The variants,** in order of how engineered they are (§2b): W0, W1, W1+M40, W1+M80, W2, W2+M40,
  W2+M80. That is 7 (Astra, Fable).

### 2b. The variant rule (least engineered that passes; Fable)

For each candidate seed, its variant is the first in that order that meets all of these on the
selection mazes, with shared trails and colony 8:
- criterion 2's thresholds (§5);
- the seed's shared − none trail effect has a `world_ci` lower bound above 0.

The carrier with each variant is reported as a blind baseline.

### 2c. The candidate seeds (the owner's addition)
- **E,** E3a's engineered organism.
- **S3r3,** E3a's Stage 3 run 3 champion, with its parameters as published in `champions-3.json`. Its
  local genome is verified against the record's sha256.
  - **Known risks, stated in advance:**
    - its gate is partial (inactive module at 30-48% of the active one's gain), so the A and B trails may
      both pull at once;
    - it was tuned to E3a's open arena;
    - its 15.98 is the best of 8, so a winner's curse applies.
- **Both get the same wiring (§1d),** and each its own variant under §2b. Their variants may differ: E3b-1
  keeps the chosen seed's.
- **The seed rule** (on the selection mazes):
  - the candidate passing §2b with the higher later-leg rate per wey (§3c) with shared trails;
  - ties within 0.25 legs per 1 000 remaining ticks go to E.
  - If only one passes, it is the seed. If neither passes, criterion 2 fails (§6).
- **The choice is labelled exploratory:** S3r3 was added after E3a's results were seen.

## 3. The controls and the measurements

### 3a. Scripted controls (the organism's movement limits)
- **The path oracle:** breadth-first-search waypoints, at full speed, turning at most 0.30 rad per tick.
- **The scripted trail follower:**
  - **Senses:** instantaneous bilateral readings of its goal's channel (trail + scent), the visit levels
    and the wall-only collision sensors. No temporal comparison.
  - **Remembers:** its goal bit only.
  - **Policy:**
    - if max(L, R) ≥ 0.005, it steers by k·(L − R), with k = 32, plus W1's reflex;
    - otherwise it explores as W2;
    - forward is always 1.
  - **Trail access:** shared, own, peers, or none.
- **Blind baselines:**
  - a random walk (E1's tuned: speed 1, rate 1, persistence 0.5, seed 0), with W1's reflex;
  - W2 alone, a ceiling for blind exploration, not a bar for the seed;
  - the carrier's circle.

### 3b. The trails' measurements
- **On-trail is geometric:** the free cells on the A-B route by breadth-first search. It is not a
  threshold on intensity (Fable, Astra).
- **Deposition trajectories:** oracle colonies of 1 and 8 weys, shuttling for H ticks.
- **Gradient direction:** the share of route cells whose value rises toward the trail's source.
  - Measured at trail ages of 1, 2 and 4 oracle legs after the last deposit on that route segment, each
    reported separately, not pooled (Astra).
  - With 1 and 8 contributors.
- **The polarity test** (with its nulls; Fable, Astra):
  - **The setup:** the scripted follower is placed on a route cell mid-way along a trail of age 1 oracle
    leg, built by 1 contributor, facing away from the source, with a heading jitter uniform in ±0.3 rad.
    256 placements.
  - **A pass:** it enters the source within 2 × the oracle's leg time from that point.
  - **The conditions:** the real trail; the same with no trail; and a no-polarity trail (λ = m, a flat
    single-pass profile).
  - **The reading:** pass(real) − max(pass(none), pass(flat)).
- **The nose range:**
  - the share of on-trail ticks whose nose input lies in [0.005, 0.35], and the share above 0.35;
  - L1's component tests rerun at m = 0.001 and 0.003, and at the trail levels met.

### 3c. The measures (the colony is the unit; colony summaries are per-wey means)
- **A leg** is a confirmed visit after the previous one (A→B or B→A). **A round trip** is two consecutive
  legs. The v1 wording "round trip" for a single leg was wrong (Astra).
- **Raw entries,** including wrong and repeated ones.
- **Confirmed visits per wey.**
- **The later-leg rate:** legs per 1 000 ticks after each wey's first confirmed visit, so the time left is
  accounted for (Fable).
- **The first-B time of later discoverers:**
  - weys that confirm B after the first wey in the colony has, censored at H;
  - compared paired across interventions on the same mazes and placements (Astra);
  - this is the primary peer measure (§5, criterion 3). On a goal's first discovery, own ≡ none.
- **Peer controls** (scripted follower and seed):
  - **Own:** the wey's own field only.
  - **Peers:** shared minus own.
  - **Replay:**
    - **the donor:** a lockstep donor colony of the same controller, on the same walls (maze id), with
      placements from episode index + 1000;
    - **what the recipient senses:** its own live field, plus the donor's total field scaled by a single
      factor. The factor makes the recipient's mean nose exposure to it equal its exposure to live peers
      in the shared condition;
    - **reported:** the route overlap (the share of the recipient's A-B route cells on the donor's) and
      the scaling factor.
  - **Scramble:** the live peers' field (shared − own), with its open-cell values permuted by a fixed
    random permutation per episode. The recipient's own field stays live. Exposure is matched as in
    replay.
  - **Read beside own:** replay below own means misleading peers, not helpful live ones (Fable, Astra).
- **The sabotage test (free; Fable):** for the scripted follower, own and none give bitwise identical
  trajectories on the CPU until each wey's first confirmed B visit. For a seed, any difference is reported
  as leakage through its gated module.

## 4. The searches (bounded; nested; selection rules fixed)

**Pilot constants** for the (c, H) stage: μ = 0.01, λ = 0.03, δ = 0.15, d₀ such that the first deposit
reads 0.2 at the noses after scaling. These are inside the feasible region by Fable's arithmetic (§9).

**Stage A, maze size and horizon** (scripted controls only). The candidates are c ∈ {5, 6, 7, 8} ×
H ∈ {1 200, 2 400}, in order of c·H, then c. The first that meets all of these is chosen:
1. the oracle's mean visits per wey is at least 8;
2. the follower (shared, colony 8, pilot constants) reaches a median of at least 4 legs per wey;
3. W2's mean visits per wey are at most 0.5 of the oracle's;
4. the random walk's are at most 0.25 of the follower's;
5. the follower's median first discovery of A by any wey is at most H/4.

The colony mean is over its weys. Conditions use the mean, or the median where stated, over the 256
selection mazes. Each candidate has one episode per maze.

**Stage B, trail constants,** on the chosen (c, H), with the scripted follower:
- **The grid:**
  - μ ∈ {0.005, 0.01, 0.02} × λ ∈ {0.01, 0.02, 0.04}, decoupled (Fable);
  - δ ∈ {0.05, 0.15};
  - d₀ at {0.5, 1} × the pilot scale.

  That is 36 settings.
- **The rule:** the setting maximising the follower's later-leg rate with shared trails, among those
  meeting all of these. Ties go to smaller μ, then smaller λ.
  - λ > m;
  - polarity: pass(real) − max(pass(none), pass(flat)) ≥ 0.3;
  - the gradient points to its source on at least 80% of route cells at age 1 leg, with 1 and 8
    contributors;
  - the nose input is in range on at least 90% of on-trail ticks, saturated on at most 5%.
- **If the winner sits on the grid's edge,** in μ or λ: one widening by a factor of 2 beyond it, then the
  rule again (Fable).
- **If no setting passes:** the fallback (§6).

**Stage C, the variants and the seed:** §2b for each candidate, then §2c.

**The mazes:**

| Use | Maze ids |
|---|---|
| selection | 0-255 |
| the report | 1 000-1 255 |
| fresh report, after any retry | 2 000-2 255 |
| E3b-1's blocks | separate, and untouched (a test checks) |

## 5. The exit criteria (the colony is the unit; on the report mazes)

1. **Mechanics:** every test and the equivalence pass.
2. **A usable task.** For the chosen seed:
   - its colony visits per wey exceed the random walk's (`world_ci` lower bound > 0, paired by maze);
   - it reaches a median of at least 2 legs per wey;
   - **headroom:** oracle − seed ≥ 2 × the gate's minimum detectable effect (criterion 6; Fable).
   - The seed against W2 and against the follower is reported. A seed at or above the follower is a
     finding.
3. **A usable signal.** For the scripted follower:
   - shared − none and own − none in later-leg rate each have a lower bound above 0.5 legs per 1 000
     ticks;
   - **the peer effect:** shared − own in the first-B time of later discoverers has a `world_ci` interval
     wholly below 0, so shared is faster.
   - **If shared = own,** peer feasibility fails (§6), even with shared > none (Astra).
   - For each seed, shared − none, own − none and shared − own are reported. Replay and scramble against
     own are reported with route overlap and scaling.
4. **Frozen settings:**
   - (c, H), the colony size, the trail constants, the scents, the variant and the seed;
   - L1's component tests at trail levels and below 0.005. **These can fail:** an active K_D below 30 at a
     level actually met on trails is a failure, with its branch in §6 (Astra);
   - the memory assays' delay D, recalibrated to the seed's median later leg.
5. **A feasible E3b-1:**
   - timings and peak memory at E3b-1's composition (256 strains × 16 worlds per strain × 8 weys),
     including the diffusion buffers and the lockstep replay donors;
   - a projected E3b-1 of at most 24 hours with a 25% reserve, for every arm planned.
6. **Power for the gate:**
   - **The test:** a paired run-level bootstrap at 90% (one-sided 5%) with 8 runs, for a true effect δ,
     at 80% power, simulated.
   - **The variance assumption:** the run-to-run coefficient of variation of tuned colonies' means is
     taken as E3a's Stage 3 champions' 0.267 (3.41 / 12.79). It comes from 8 single-wey, open-arena runs,
     so it is weak (Fable).
   - **Sensitivity** at 0.15 and 0.40 is reported.
   - **The pass:** the minimum detectable effect at a CV of 0.267 is at most 0.25 of the seed's mean.
     Astra's normal approximation gives 23.4% at 80% power, so this is close and is simulated. The
     scripted peer effect shows measurement sensitivity only.

## 6. If a criterion fails

| Failure | What happens |
|---|---|
| 1, mechanics | fixed and retested |
| Stage A, nothing passes | a report and a redesign; the owner informed |
| Stage B, no setting passes | the fallback (Panait-Luke-style, nonlinear); the peer controls redesigned and reviewed before E3b-1. If the fallback fails too, a report and a redesign. Stage B only: controller failures never change the trail rule (Astra) |
| Stage B, winner on the grid's edge | one widening (§4) |
| 2, the seed fails "above" or "legs" | the variant search widens once (M at periods 20 and 160, if M exists), with every later number from the fresh report mazes; then a report and a redesign |
| 2, headroom | E3b-1's gate and its power re-examined; the reading set out before any registration |
| 3, the trail effect null for the follower | Stage B's widening, then the fallback |
| 3, the trail effect null for the seed | it is the variant rule's input (§2b); if no variant passes, as row 2 |
| 3, the peer effect null (shared = own) | the peer claims leave E3b-1, with the 2 × 2 and the gate kept; the owner informed |
| 4, component qualification | the trail levels are rescaled (d₀ down) within Stage B's rule, or a report |
| 5, over budget | the agreed cut order: generations, then worlds per genome, then horizon; the no-trails arm made descriptive. Fewer weys changes the peer task and needs E3b-0 requalified. If the gate alone exceeds 24 h, the owner is asked |
| 6, power | E3b-1 is redesigned (more runs, or a narrower gate) before registration. Longer tuning alone is not a remedy (Astra) |
| GPU budget exhausted | E3b-0 stops and reports what it has |

**After any retry,** reported numbers come from the fresh report mazes. If those are exhausted, the
intervals are labelled adaptively selected.

## 7. Workload and budget
- **The scripted searches** run on the CPU: Stage A has 8 candidates × 256 mazes × the controls; Stage B
  has 36 settings × 256 mazes.
- **On the GPU:**
  - Stage C: 7 variants × 2 seeds × 256 mazes × 8 weys, and the trail conditions;
  - the report's seed runs;
  - the timing at E3b-1's composition.
- **Fable's estimate** is well under 1 GPU-hour, against the cap of 3.
- **The projection** is recorded before Stage C, and the stage frame's cap clock enforces the cap.

## 8. Records and review
- **The runner** is `scripts/e3b0.py`, in E2's stage frame, with the compute accounting, its stages in
  §4's order plus the report and the timing. Each record is committed and pushed before the next.
- **The report** (`experiments/E3-ab-organism/E3b-0/RESULTS.md`) is reviewed by both before E3b-1's
  design.

## 9. Changes from v1

| v1 review item | v2 |
|---|---|
| λ tied to μ missed the feasible region (Fable) | Decoupled grid around μ 0.01-0.02, λ 0.02-0.04; a widening at the edge |
| Diffusion ridged corridors (Fable) | The flux form, symmetric and mass-conserving |
| (c, H) chosen before the trail constants (both) | Pilot constants for Stage A; nested stages |
| shared − own had no threshold (Fable); shared = own could pass (Astra) | The first-B time of later discoverers is primary, with an interval; a null is a failure with its branch |
| The polarity test had no null (both) | The no-trail and flat-trail nulls; heading jitter; the age and contributors pinned |
| "Highest score" picks W2 (Fable) | The least engineered variant that passes |
| The oscillator cannot exist without adaptation (Astra) | M must be found within bounds on the CPU, or it is dropped |
| Few dead ends from depth-first search (both) | Wilson's algorithm, measured at 0.29-0.32 dead ends |
| Corners leak in sensing and movement (Astra) | A supercover traversal for both; support-cell occlusion; tests both ways |
| Unpinned numbers (both) | A, W1, W2, the colony summaries, the aggregation and the tie-breaks pinned |
| "Round trip" mislabelled (Astra) | Legs and round trips defined |
| The later-leg confound (Fable) | A rate per remaining time |
| Power was not a power calculation (both) | A simulated 80% power at one-sided 5%, a CV of 0.267 with sensitivity; headroom ≥ 2 × the minimum detectable effect |
| Replay and scramble unpinned (both) | Donor, timing, overlap, exposure-matched scaling; scramble of peers only; read against own |
| The free sabotage test (Fable) | Added |
| The seed under own (both) | Added for each seed |
| Failure handling (Astra) | A full table; fresh report mazes; separate fallback triggers; criterion 4 can fail; the budget cut order restored |
| The full composition (Astra) | 256 × 16 × 8 |
| The equivalence reference for the shuttle (Fable) | Produced at 84ff98a by the extended script |
| Linearity "bitwise" was tautological (Fable) | Against a separately evolved field, 10⁻⁵ relative |
| — (the owner) | S3r3 as a second candidate seed, with its risks stated and a fixed rule |
