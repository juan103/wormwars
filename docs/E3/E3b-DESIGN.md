# E3b: trails, branching mazes and the colony (design v2, 2026-10-02)

Status: v2, for a confirmation round by Astra 6 and Fable 5.1. Nothing has run.
- **v1** (ea06ce4) was reviewed (`docs/reviews/20261002-E3b-design/`; D172):
  - **Fable:** "proceed to E3b-0's plan", with fixes.
  - **Astra:** "revise". Keep the staging, but tighten the controls, the measures and the feasibility
    gates.
  - v2 takes every point, and its last section maps them.
- **A bounded literature check** followed, as both asked (`docs/E3/E3b-LITERATURE.md`). Its findings are
  used below.
- **The owner's ceiling:** about 30 GPU-hours for E3b (D159).
- **The frame:** stereo sensing and the trails are game-design choices. The organisms are circuits on a
  silent worm, outside the N2 mask. Nothing here is about worm or ant behaviour.

## The question and the gate

- **The roadmap's gate:** "Repeated alternating journeys, counted with an event ledger, on unseen
  branching mazes, and better than the seed design", with peer-signal controls.
- **The seed design** is E3a's engineered organism E, made maze-ready and then frozen.
- **"Better"** means the jointly tuned seed against the frozen seed, on untouched mazes, under identical
  mechanics: reflexes, trail rules, scents and movement (Astra).
- **A tuned seed can win without using trails** (Fable), since tuning can just improve locomotion. So
  E3b-1 adds a 2 × 2 at evaluation: colonies evolved with trails and without, each tested with trails on
  and off.
- **No selector is evolved from scratch.** E3a found one working selector in 8 runs, but under one
  initialisation and mutation scheme, so that finding is not general (Astra).
- **Correction to v1 (2026-10-02, rule 4):** v1 wrote "joint tuning helps (+2.36)" as if against E. The
  +2.36 was against E3a's Stage 2 champions, not against E (Astra).

## The staging

**E3b-0 (exploratory; the engine, the controls and the task's feasibility; at most 3 GPU-hours).**
- **It does not test evolution.** It must establish that E3b-1 can detect an advantage, and that a null
  result would be interpretable (Astra).
- **It ends in a report and E3b-1's design,** and only then a pre-registration.

**E3b-1 (confirmatory; pre-registered; the gate, the 2 × 2 and the peer-signal controls).**
- **Its budget is not credible yet.** Scaling E3a's measured rate gives about 23.5 hours per tuned arm
  with 8 weys and 1 200 ticks, so 47 hours for the two training arms (both reviewers).
- **The scaling may be better on the GPU,** so E3b-0 measures it. Cuts then come from generations,
  worlds per genome or the horizon, before independent runs or the no-trails arm.

## E3b-0's engine changes (test-first; rule 7)

Each has a test seen failing first. Each is checked for equivalence with its task off, against the
current engine: Task N, foraging, E3a's shuttle, and E4s-1's graft.

1. **The maze.**
   - **The shape:** a tree maze, with one route between any two places and dead ends, drawn from its own
     stream, separate from the episode's.
   - **The geometry:** a c × c grid of cells, 3-wide corridors and 1-cell walls, so the side is
     4c + 1. The v1 figure of 33 × 33 for a 5 × 5 grid was wrong (Fable): a 5 × 5 grid is 21 × 21, and
     33 × 33 is 8 × 8.
   - **Its size is chosen by leg length** at the movement limit (0.35 cells per tick). An oracle should
     make at least 4 to 6 journeys in the horizon. The maze's side is set independently of colony size
     (`arena_side` would give 24).
   - **The free-cell graph** is 4-connected, and distances are by breadth-first search.
   - **A, B and the spawns** are at distinct dead ends, with a declared range of path distance between A
     and B.
2. **Movement against walls: per-axis sliding, as a flag.**
   - The boundary already slides per axis: `proposed.clamp` keeps heads off the ring, so `blocked` never
     fires there (Fable).
   - Interior walls get the same rule. Other tasks keep theirs.
3. **The trails: exact per-wey fields.**
   - **Storage:** two channels (the A trail and the B trail) per wey.
   - **What a wey senses:** the shared trail is the sum over weys; "own only" is its own field; "peers
     only" is the sum minus its own (Fable).
   - **The cost:** about 280 MB at 4 096 worlds × 8 weys × 2 channels × 33² (both). It is benchmarked.
   - **Diffusion** runs only between open neighbours, with no flux into walls, so it conserves mass.
   - **Evaporation** is μ per tick.
   - **Bilinear noses beside walls** read lower values, an implicit wall repulsion. Declared.
4. **Deposit (engineered and labelled).**
   - **The rule:** a wey whose goal is A deposits on the B trail at its head, and the other way round.
   - **The strength:** d₀·exp(−λ·t), with t the ticks since its last confirmed visit. Nothing is
     deposited before its first.
   - **The trail points toward its source only if λ exceeds μ.** Otherwise it is flat or reversed (both
     reviewers derived this).
   - E3b-0 measures the gradient's direction along routes, across delays and junctions. A trail alone
     carries no polarity in real ants (Jackson et al. 2004), so it is not assumed here.
   - **The fallback:** a Panait-Luke-style adjustment that gives a gradient by construction, labelled as
     more engineered (`E3b-LITERATURE.md`).
5. **The colony on the shuttle.**
   - **Per wey:** a goal, a ledger and a deposit timer.
   - **The score** is per wey, and the colony's score is its mean.
   - **The spawns** are spread over several dead ends: 8 weys in one 3 × 3 dead end start over the
     crowding threshold (Fable).
6. **Peer channels other than trails are switched off** (both):
   - crowding is off (`crowd_resist` and `crowd_push` at 0);
   - the collision inputs read walls only, without BODY.

   So "no trails" means no peer signal.
7. **Local scents:**
   - by path distance, with a short range;
   - the summed trail and scent reaching the noses stays inside L1's qualified range (0.005 to 0.35);
   - L1's component tests are rerun at trail levels (Fable).
8. **A wall reflex (engineered, labelled, wall-only inputs)** is built and tested beside sliding alone.
   - **The disagreement:** Fable wants sliding, and a reflex only if E3b-0 shows a jam; Astra wants an
     engineered reflex.
   - **The decision:** E3b-0 decides on evidence (corners, junctions, dead-end exits).
   - **The choice is frozen** for the seed and every arm, and the carrier-plus-reflex baseline is
     reported.

## E3b-0's controls and measures

**The controls:**
- **A path oracle:** breadth-first search, at the organism's movement limits.
- **A scripted trail follower** with the organism's sensory access: bilateral trail and scent readings
  and the visit levels.
  - Its only memory is a goal bit, no route knowledge (Astra). It explores when it senses no trail.
  - It is run with shared trails, own only, peers only, and none.
- **Blind baselines:**
  - a random walk;
  - a wall follower. In a tree maze it visits every dead end, so its ceiling is measured (Astra);
  - the carrier's circle, and the carrier with the reflex.
- **The seed:** E with its noses reading trail plus scent, alone and as a colony, with trails on and off,
  and with sliding alone and with the reflex.

**The measures:** the colony is the unit of inference, since weys in a colony are not independent
replicates (Astra).
- **Raw entries,** including wrong and repeated ones. Confirmed visits alternate by construction, since
  the scorer counts only entries into the current goal (Astra).
- **Completed round trips per wey,** and the share of weys completing at least k.
- **First-A and first-B times by discovery order,** with censoring. This is the primary peer measure:
  after one round trip a wey has laid both trails itself, so the peer benefit sits in the first legs
  (Fable).
- **The trails' gradient direction and persistence,** and the noses' saturation.
- **The cost per rollout and peak memory** at the intended compositions.

## E3b-0's exit criteria (before E3b-1 is designed and pre-registered)

1. **Correct mechanics:** every engine change passes its tests and its task-off equivalence, E3a's
   shuttle included.
2. **A usable task:** the oracle succeeds under the movement limits. The seed explores and makes repeated
   journeys from empty fields: above the blind baselines (the wall follower included), below the scripted
   follower. So there is headroom and a gradient, without universal failure or a trivial ceiling.
3. **A usable signal:**
   - the trails point toward their sources across the delays and junctions that matter;
   - the scripted follower orders shared > own only > none, with the gaps measured;
   - each peer control removes information in a scripted example.
4. **Frozen settings:**
   - the maze size, horizon, colony size, trail constants (d₀, λ, μ, diffusion), scents and wall
     mechanics;
   - L1's gains verified at trail levels;
   - the memory assays' durations recalibrated to maze journeys.
5. **A feasible E3b-1:**
   - timings and peak memory at the real compositions, for both training arms, validation, the donor
     episodes for replay, the assays and a reserve;
   - a projection of at most about 24 hours, with reserve.
6. **Power:** the peer effect in the scripted follower is large enough for E3b-1's planned runs to
   detect. If not, it is said so, and E3b-1 is redesigned before registration.

## E3b-1 (sketch; designed after E3b-0)

- **The gate:** the tuned colony against the frozen maze-adapted seed on untouched mazes, under a
  minimum repeated-journey criterion, a margin and a run-level paired inference.
- **The 2 × 2:** colonies evolved with trails and without, each evaluated with trails on and off.
- **The peer-signal controls:**
  - shared;
  - own only;
  - peers only;
  - **replayed:**
    - the recipient keeps its own live trail;
    - only the peers' part is replaced, from independent donor episodes on the same walls, with
      different A and B placements;
    - replay on the same placements would still mark the one true route of a tree (both);
  - scrambled within open cells, with the amount of signal matched.
- **No trails from the start:** a colony evolved with deposit off.
- **Trees only.** Loops add route choice, which is a different question.

## Changes from v1

| v1 review item | v2 |
|---|---|
| E3b-1's budget not credible, about 47 h for two arms (both) | Measured in E3b-0; cuts by generations, worlds or horizon first; exit criterion 5 |
| "Better than the seed" could be locomotion (Fable); identical mechanics; the +2.36 misattributed (Astra) | The 2 × 2 at evaluation; frozen identical mechanics; a dated correction |
| Alternation guaranteed by the scorer (Astra) | Raw entries, round trips per wey, shares of weys; the colony as the unit |
| The trail's direction needs λ > μ; default decay useless (both) | Measured in E3b-0; constants frozen; a Panait-Luke-style fallback |
| Replay on the same maze keeps route information (both) | Other A and B placements on the same walls; only the peers' part replaced; own live trail kept |
| Bodies are a second peer channel; the spawn crowding (Fable, Astra) | Crowding off; collision inputs read walls only; spawns spread |
| Own trails make peers redundant after a round trip (Fable) | First-leg times by discovery order as the primary peer measure |
| The seed has no exploration (both) | Exit criterion 2 |
| The geometry was inconsistent (Fable) | Side = 4c + 1; size chosen by leg length; independent of colony size |
| Wall sliding against a reflex (they disagreed) | Both built; E3b-0 decides on evidence; frozen across arms; the reflex baseline reported |
| Local scents in L1's range (Fable); scents' support (Astra) | Pinned to L1's qualified range; component tests at trail levels |
| Per-wey fields, not a mask (both); peers only (Fable) | Exact per-wey fields; shared, own and peers derived |
| Literature before fixing the trail rule (both) | Done, bounded and verified (`E3b-LITERATURE.md`) |
| Masked diffusion, wall reading, scorer aggregation, Task N disables pheromones (Astra) | Mass-conserving, declared; per-wey scoring; the shuttle colony configuration sets its own trails |
| Trees or loops (both: trees) | Trees |
