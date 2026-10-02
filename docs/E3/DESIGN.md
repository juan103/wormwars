# E3: the minimal A/B organism (design v2.1, 2026-10-02)

Status: v2.1, for a second confirmation round by Astra 6 and Fable 5.1. Nothing has run. A
pre-registration follows only if both agree.
- **v1** (1c68b6b): both said "revise" (`docs/reviews/20261002-E3-design/`).
- **v2** (5aaa314):
  - **Fable:** "proceed to pre-registration", provided the budget is corrected first.
  - **Astra:** "revise".
  - Their reviews are archived in `docs/reviews/20261002-E3-design-v2/`. Both checked the latch and gate
    numbers and found them right, Astra in the real `Brain.step` on the CPU.
  - Both found the budget wrong, w_s not a genome parameter, the parameter count resting on unstated
    tying, and the hold test unable to tell a latch from a leaky trace. Both found the maximum spawn
    distance, the dtypes and the sensing latency still missing.
  - v2.1 takes all of these. Its last section maps them.
- **Correction to v2 (2026-10-02, rule 4).** v2 said: "E4s-1 took about 0.2 GPU-hours per run of 1 000
  generations at 300 ticks, so about 0.4 h at 600 ticks", and estimated "about 15.5 h" in total.
  - That figure was at 8 worlds per genome, and v2 uses 16. v2 also gave B-task one stage's budget,
    where its text gave it two.
  - The table below is recomputed from E4s-1's measured batches.
- **The basis:**
  - the roadmap's E3 section and its additions (D144);
  - E4s's published results (D147, D154);
  - the literature review's latch and selector sections.
- **The frame, as in E4s:** stereo sensing is a game-design choice, and the computation lives in
  hand-built modules on a silent carrier. Nothing here is about worm behaviour.

## The staging

- **E3a (this design): the shuttle.** One wey, the open arena, two fixed sources A and B. It tests the
  two-module organism and its latch.
- **E3b: trails, branching mazes and the colony,** with the roadmap's peer-signal controls. **The
  roadmap's gate ("repeated alternating journeys on unseen branching mazes, better than the seed
  design") belongs to E3b and is not met by E3a.**
- **E3c: the assembly comparison.**

The roadmap gets a dated amendment saying so.

## E3a: the task ("shuttle")

- **The arena:** Task N's 24 × 24 arena with one wey. Task N's spawn: radius 7.38 from the centre at a
  uniform angle, with ±3.36 of jitter per axis.
- **The sources:** A and B are fixed per world, drawn by rejection sampling from the world's own stream,
  as Task N's targets are (`_build_targets`), uniformly within the centre box 4-20. Accepted when all of
  these hold:
  - 8 ≤ |A − B| ≤ 14;
  - both are at least 6 from the spawn;
  - **A is within 16 of the spawn along both axes,** so the first leg never starts outside the scent's
    support (`target_field` is zero beyond 18 along either axis).
- **The check:** `scripts/e3_geometry_check.py`, writing `docs/E3/geometry-check.json`.
  - Over 2 000 spawns, every spawn accepts at least 11.8% of draws; the median is 21%.
  - Without the axis limit, 16 373 of 8.8 million accepted draws (0.19%) would start blind.
  - At 14 cells the far source's scent is 6.6% of its peak.
- **The scents:** separate channels, each A·exp(−d²/2σ²) with σ = 6, amplitude 1, and Task N's square
  support. They are sensed bilaterally as `a_left`/`a_right` and `b_left`/`b_right`, scaled as Task N's
  scent is.
- **The goal (the scorer's state, never given to the brain):** **A** at tick 0. A confirmed visit
  switches it. An entry into the other source counts nothing and switches nothing.
- **The event contract:**
  - **The tick's order** is the world's: sense, think, move, then events.
  - **inside(X)** at tick t means the head, after tick t's movement, is within R = 1.5 of X.
  - **An entry** into X is inside(X) at t and not at t − 1. The head must leave and come back to
    re-arm.
  - **A confirmed visit** is an entry into the current goal. The goal switches before tick t + 1's
    events. A and B are at least 8 apart, so the head is never inside both.
  - **The ledger** extends Task N's (`_advance_targets`, `target_events`). It records:
    - every entry into A and into B, with its tick;
    - every confirmed visit;
    - each leg's path length;
    - the goal at every tick.
  - **The cue below is not an event** and never enters the ledger.
- **The score:** confirmed visits per episode over 600 ticks.
- **The signals to the brain:**
  - **`at_a` and `at_b` are levels:** 1 while inside(A) or inside(B), 0 otherwise. They are sensed
    with the scents, so inside(X) after tick t's movement first reaches the brain at tick t + 1.
  - **The start cue:** for ticks 0-4 the world sets `at_b` = 1, as if the wey had just visited B, so
    the latch starts in "go to A".
  - Every organism and baseline below receives the same signals and the same cue. Those without a
    latch ignore them.
- **No N2 interface in E3a.**
  - The organisms live on the silent carrier: the 302 worm neurons with zero weights, conductances
    and biases, except the carrier's forward and turn biases.
  - The new signals reach only the grafted neurons; ALM and AVM are untouched.
  - Substeps are 32, as in Task N (`task_n_config`; the config default is 8).
- **Dtypes** (declared after E4s-1's int16 defect, D154):

  | Quantity | Dtype |
  |---|---|
  | positions, scents, signals, neuron states | the world's float32 |
  | ledger ticks and counts | int64, as Task N's |
  | path lengths | float64 |
  | the goal | int8 |
  | per-tick logs (latch state, each module's turn contribution, the turn command) | float32 |

  A test writes known non-zero values through every saved array and reads them back.
- **The engine change, with its check (rule 7):**
  - **The new code:**
    - the `shuttle` task in the world;
    - `graft.py` generalised to several modules per graft, nose signals other than food, and probes
      per nose pair;
    - **a clamp of a named neuron to a value** (only `silence`, which clamps to 0, exists today).
  - **The check, with the task off,** is against the previous engine at fixed compositions. Task N's
    and foraging's per-world states, events and scores must be identical on declared worlds:
    - on the GPU, E2's GA generation 0-25 hashes, as E4s did;
    - on the CPU, per-tick states and events.
  - The worlds and compositions are named in the pre-registration. No broader claim is made.

## E3a: the organism (11 grafted neurons)

**L1-A and L1-B.** Two copies of E4s-0's L1 comparator, each with noses NL and NR (τ 0.5) and
comparators CL and CR (τ 0.5, bias 0), under new names (`E3_A_NL`, …, `E3_B_CR`).
- L1-A's noses read A's scent and L1-B's read B's. Both drive the same 8 turn neurons, push-pull, with
  L1's 20 edges each.
- The parameters are copied from `module.json` after its sha256 is checked.

**The relays RA and RB** (τ 0.5, bias 0, fixed). `at_a` enters RA and `at_b` enters RB at an
interface gain of 3, which is within `input_max` = 5.
- **Every evolvable quantity of the selector is then a genome parameter** (Fable, Astra). The
  interface gain is fixed, like the scents' scaling.

**The latch q:** τ_q dq/dt = −q + w_qq·tanh q + b_q + w_aq·tanh(RA) + w_bq·tanh(RB).
- **The engineered values:** τ_q 1, w_qq 2, b_q 0, w_aq −3, w_bq +3.
- **Its settled states:** q* = ±1.915, so tanh q* = ±0.9575. "Go to A" is q > 0.
- **Checked by simulation at 32 substeps,** with the relay's lag included:
  - a one-tick level switches it from either state (q is about ∓0.43 at the end of the tick and settles
    at ∓1.915);
  - two-tick and four-tick levels switch it too;
  - with no input it holds for 600 ticks.
  - The start cue drives q to about +4.9, and it relaxes to 1.915 within a few ticks. The component
    tests therefore include the start (Astra).

**The gate, by saturation:**
- **The edges:** q → L1-A's CL and CR at +2; q → L1-B's CL and CR at −2.
- **The comparator biases:** all four at −1.914, which is −2 × 0.957 and within `b_max` = 2.
- **Going to A,** L1-A's comparators sit at an offset of +0.001 and are active. L1-B's sit at −3.829,
  saturated. The reverse holds going to B.
- This shifts the comparators' operating points, and is declared as part of the selector interface.
  L1's own comparator bias is 0, so the active module matches L1 alone (Fable, checked against
  `module.json`).

**The registered component tests** (open loop on the carrier):
- **The measurement:**
  - carrier turn 0.2, the qualifying condition for L1;
  - noses fed L = m + d/2 and R = m − d/2, with d = ±0.001 and m in {0.02, 0.05, 0.1, 0.2, 0.35};
  - the other module's noses at the same m with d = 0;
  - 50 ticks of preconditioning in the latch state, measured after the start cue;
  - K_D = Δu / (2d) at each m.
- **The limits** are absolute (Astra):

  | Test | Requirement |
  |---|---|
  | the active module's K_D | at least 30 at every m |
  | the inactive module's | \|K_D\| at most 0.3 at every m |
  | the turn offset added by the inactive module | below 0.02 |
  | switching and recovery | after a two-tick level, the newly active module's K_D reaches 90% of its settled value within 10 ticks |

- **Astra's CPU check of the arithmetic:** active K_D 31.6-35.6, inactive 0.059-0.068.

**The inactive module keeps updating.** Its comparators are driven into saturation, never frozen or
reset.
- **Logged every tick:** the latch state, the turn command, and each module's turn contribution.
- **The contribution** is the module's summed signed current into the 4 dorsal turn neurons, minus its
  current into the 4 ventral turn neurons, before their nonlinearity. Defined this way because the
  turn neurons are shared and nonlinear (Astra).

## E3a: stages, controls and gates

Every proposed threshold below is fixed in the pre-registration before Stage 0 runs.

**Stage 0, the controls (scripted; minutes).**
- **S-oracle:** straight to the current goal.
- **S-shuttle:** E1's S-const on the current goal's scent, with a perfect scripted memory, at
  k = 32 (L1's gain) and k = 256 (E1's best).
- **L1-switch:** one L1 on the carrier, whose noses the world feeds the current goal's scent. It is a
  reference for the module without a latch, **not a demonstrated upper bound** (Astra).
- **Blind baselines:** constant motion, a persistent random walk, and the carrier's own circle
  (forward 1.0, turn 0.2).
  - The circle's radius is about 5.8, so it can pass through both sources in some worlds (Fable). The
    gate therefore reads the 90th-percentile world as well as the mean.
- **The proposed gate:**
  - S-oracle's mean is at least 0.8 of its per-world geometric maximum;
  - S-shuttle at k = 256 reaches at least 0.5 of S-oracle;
  - L1-switch's lower bound is at least 0.5 of S-shuttle's mean at k = 32;
  - every blind baseline's mean is at most 0.25 of L1-switch's, and its 90th-percentile world at most
    0.5.
  - **If it fails,** E3a stops for redesign.

**Stage 1, the engineered organism (frozen; hybrid).**
- **The proposed gate:**
  - its lower bound is at least 0.8 of L1-switch's mean;
  - it beats the no-latch control (both modules always on, q clamped to 0) and the one-module control
    (L1-A only), each by E2d's "uses" rule: both lower bounds above 0.5 visits;
  - the component tests pass.
- **Memory, tested causally:**
  - **Paired clamp assays:** the same worlds and starts, with q clamped to +1.915 and to −1.915. The
    first entry must be into the clamped goal in at least 90% of worlds for each sign.
  - **The hold test:** the levels withheld for a whole episode after the first visit. It passes if
    |tanh q| stays at least 0.9 and the component tests still pass at tick 600. **A sign is not
    enough** (Fable, Astra).
  - **The reset test:** q set to the wrong state mid-leg. The organism turns to the wrong source, and
    resumes alternating after its next confirmed visit.
- **The mean-nose probe for each module:** the score with one module's noses fed their mean.
- **If the gate fails,** E3a stops for redesign: the parts do not compose.

**Stage 2, an evolved selector.**
- **The modules are frozen.** **The selector's 13 untied parameters evolve** (no tying, so no new
  machinery):

  | Parameter | Count |
  |---|---|
  | τ_q, w_qq, b_q | 3 |
  | w_aq, w_bq | 2 |
  | the four gate edges | 4 |
  | the four comparator biases | 4 |

  The relays and the interface gain stay fixed.
- **The initial distribution:** weights and biases uniform over their bounds; τ log-uniform over
  [0.5, 20], as the brain's default initialisation.
- **The census:** 1 024 random selectors, each with its score and its bistability (below).
- **The mutation:** 02's sigmas at 1× on these 13 parameters and 0 elsewhere. That can cross zero, which
  0.25× could not in E4s-1.
- **The GA:** 02's (population 32, 3 elites, truncation 8), 16 worlds per genome, 300 generations, and
  validation every 25 generations on 256 worlds.
- **The comparators:** random sampling at the same number of evaluations; the engineered organism.
- **The classification of each champion** (Fable, Astra):
  - **latch:** its q equation (relays at rest) has three fixed points, so it is analytically bistable,
    and it passes the hold test above;
  - **slow trace:** it is monostable, but the clamp assays pass and the gate still meets the component
    tests after the episode's median leg duration;
  - **no memory:** neither.

  A hysteresis sweep (the relay drive ramped up, then down) is reported for each champion.
- **A working selector** is a champion whose test lower bound is at least 0.8 of the engineered
  organism's mean, and which passes the clamp assays.
- **The proposed readings:**
  - **S2-a:** how many of the 8 runs reach a working selector, and each one's class;
  - **S2-b:** evolution against random sampling, by a run-level paired bootstrap of the champions' test
    scores. The outcomes are "evolution better", "random sampling as good" (the interval within ±0.5
    visits), or "unclear";
  - **S2-c:** the census's fraction of working selectors. If it is not small, Stage 2 is answered at
    generation 0, and the wording says so (Fable).

**Stage 3, joint fine-tuning: descriptive.**
- **The start:** each Stage 2 run's champion.
- **What evolves:** the modules' and the selector's parameters, at 0.25×. **The silent worm's 302
  neurons, the relays and the carrier's biases stay fixed.**
- **Fitness** is the shuttle score only, with 16 worlds and 500 generations.
- **Each module's own skill** (single-source navigation with q clamped) is measured at the checkpoints
  and endpoints. It is not part of fitness.
- **What it measures:** whether joint tuning improves the shuttle, and whether the modules keep their
  component skills.

**The baselines.**
- **B-shared,** engineered: one L1 whose two nose pairs, A's and B's, are gated by a latch with relays,
  saturating the noses by the same bias-shift method. It passes its own component tests and is
  descriptive only.
- **B-task:** the same 11 neurons, signals, cue and output edges, with all 121 edges among the 11
  neurons free.
  - It starts from the same initial distribution and evolves at 1×, with the evaluations of Stage 2 and
    Stage 3 together.
  - **It matches neurons and inputs and outputs, not trainable capacity** (Astra), and is labelled so.

**Worlds, seeds and statistics** (all pinned in the pre-registration):
- **World ids:** new blocks, checked against every block in use by a collision test, as E4s's were:
  - selection 944M;
  - validation 945M;
  - test 946M (256 worlds);
  - assays and census 947M.
- **Run seeds:** 1 170 000 + i.
- **The statistics:**
  - within-organism comparisons on the same worlds use E2d's `world_ci`;
  - arm comparisons use the run-level bootstrap (E2d's `_boot_means`, as E4s-1);
  - there are 8 runs per evolved arm.

## Budget

**The rate,** measured from E4s-1's ten training batches: each took 1.35-1.43 hours for 8 runs ×
32 genomes × 8 worlds × 300 ticks × 1 000 generations, including validation. The carrier steps about
313 neurons, as E4s-1's did. The estimate scales that rate linearly. The projection measures the
real 600-tick, 16-world shapes before any training, and the scaling may be better than linear.

| Part | Shape | Estimate |
|---|---|---|
| Engine check, smoke, projection, Stages 0-1, assays | — | 1.0 h |
| The Stage 2 census | 1 024 × 16 worlds | 0.1 h |
| Stage 2 | 8 runs, 16 worlds, 600 ticks, 300 generations | 1.7 h |
| Random sampling | the same evaluations | 1.7 h |
| Stage 3 | 8 runs, 16 worlds, 600 ticks, 500 generations | 2.8 h |
| B-task | Stage 2 + Stage 3's evaluations | 4.5 h |
| Evaluation, including B-shared | — | 1.5 h |
| **Total** | | **about 13.3 h** |

- **Proposed cap: 20 GPU-hours for E3a.** That leaves a margin of about 1.5× for the linear scaling.
  The owner has not set a ceiling for E3; this asks for one.
- **If the projection exceeds the cap,** reductions are made in this order:
  1. B-task's evaluations, to Stage 2's alone;
  2. Stage 3, to 4 runs;
  3. random sampling, to 4 runs.
- **The minimum viable E3a** is Stage 2's 8 runs and 4 runs of random sampling.

## What E3a cannot show

- Anything about worm behaviour or its circuits.
- Trails, mazes or colonies: that is E3b, which holds the roadmap's gate.
- Whether modularity pays: that is E3c.
- Gluing two whole N2 brains: that is E4.

## Changes from v2

| v2 review item | v2.1 |
|---|---|
| The budget wrong by about 2× (both); B-task's line (both) | Corrected (dated above); recomputed from E4s-1's measured batches; Stage 2 at 300 generations; B-task given two stages; cap 20 h; shrink order and minimum |
| w_s is not a genome parameter (Fable); `mutate` cannot reach it (Astra) | Relays RA and RB at a fixed interface gain; w_aq and w_bq are genome edges; one-tick switching rechecked with the relay's lag |
| The parameter count rests on tying (both) | 13 untied parameters, listed |
| A leaky trace keeps its sign (both) | An analytic bistability test, a hold test on magnitude and function, a hysteresis sweep, three classes |
| The maximum spawn distance (Fable) | A within 16 along both axes; checked by a committed script |
| Dtypes promised, not declared (both) | Declared, with a round-trip test |
| The latency from movement to sensing (both) | Inside after tick t's movement reaches the brain at t + 1 |
| The measurement protocol for the component tests; absolute limits (Astra) | Given, with absolute limits |
| Each module's turn contribution (Astra) | Defined, before the turn neurons' nonlinearity |
| The start's overdrive (Astra) | Component tests measured after the cue |
| The carrier's circle can visit (Fable) | The gate reads the 90th-percentile world |
| Stage 2 may be answered at generation 0 (Fable) | S2-c, with its wording |
| Stage 3's component share (Fable); its start (Astra) | Measurement only; it starts from Stage 2's champions |
| B-task's mutation and capacity (both) | 1×; labelled as matching neurons, not capacity |
| Clamping q is new engine code (Fable) | Listed in the engine change |
| Stage gates as numbers; failure consequences (both) | Proposed numbers, fixed before Stage 0; a failure at either stage stops E3a |
| L1-switch is not an upper bound (Astra) | Reworded as a reference |
| Worlds, seeds, statistics (Astra) | New blocks with a collision test; the statistics named |
