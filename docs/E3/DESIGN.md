# E3: the minimal A/B organism (design v2.2, 2026-10-02)

Status: v2.2, for a third confirmation round by Astra 6 and Fable 5.1. Nothing has run. A
pre-registration follows only if both agree.
- **v2.1** (af9b768): both said "revise", with text fixes only (`docs/reviews/20261002-E3-design-v2.1/`;
  D160). They found that the budget, the relays and the geometry hold. They also found problems, all
  taken here and mapped in the last section:
  - the no-latch control was mis-built;
  - the memory classes misfiled real latches;
  - the champions' clamp values were undefined;
  - B-task had no reading;
  - the selector's initial distribution made a null near-certain;
  - the latch's quoted number came from the wrong update rule.
- **The owner set E3a's cap at 30 GPU-hours** (D158, corrected by D159).
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
- **The sources:** A and B are fixed per world, drawn from the world's own stream, as Task N's targets
  are (`_build_targets`), uniformly within the centre box 4-20.
  - **They are drawn jointly,** and both are redrawn on rejection.
  - **The rule:**
    - 8 ≤ |A − B| ≤ 14;
    - both are at least 6 from the spawn;
    - **|A − spawn| ≤ 16, Euclidean** (Fable).
  - **The Euclidean cap** bounds the scent of A at the spawn head from below: exp(−16²/72) = 0.0285,
    above the lowest level the component tests qualify (m = 0.02). v2.1's "16 along both axes" allowed
    about 22.6 cells, where the scent is about 0.0008.
- **The check:** `scripts/e3_geometry_check.py`, writing `docs/E3/geometry-check.json`.
  - Over the 2 000 sampled spawns, every one accepts at least 11.8% of draws; the median is 20%.
  - The lowest scent of A at a spawn head is 0.0286.
  - **Without the cap,** 16 373 of 8.8 million accepted draws (0.19%) put the head outside A's square
    support.
    - **Correction to v2.1 (2026-10-02):** v2.1 called these worlds ones that "would start blind". They
      are not a measure of sensory blindness, which also depends on the noses, the heading and the
      grid (Astra).
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
- **Checked in the engine's update rule** (semi-implicit, all neurons updated together, 32 substeps;
  Astra in `Brain.step`, then rechecked):
  - a one-tick level switches it from either state. q is ∓0.2197 at the end of the tick, and settles
    at ∓1.915;
  - two-tick and four-tick levels switch it too;
  - with no input it holds for 600 ticks.
  - The start cue drives q to 4.937 at tick 4, 1.963 at tick 10, and 1.915 by tick 20.
  - **Correction to v2.1 (2026-10-02):** v2.1 quoted "about ∓0.43", from explicit Euler with the relay
    updated first.
  - The implementation commits a test of these numbers against `Brain.step`.

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
- **The startup test** (Astra: preconditioning hides the start): K_D measured at ticks 5-15 after the
  cue.
- **The limits** are absolute (Astra):

  | Test | Requirement |
  |---|---|
  | the active module's K_D | at least 30 at every m |
  | the inactive module's | \|K_D\| at most 0.3 at every m |
  | the turn offset added by the inactive module | below 0.02 |
  | switching and recovery | after a two-tick level, the newly active module's K_D reaches 90% of its settled value within 10 ticks |
  | startup | the active module's K_D is at least 30 from tick 10 |

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
  reference for the module without a latch, **not a demonstrated upper bound**.
- **Blind baselines:** constant motion, a persistent random walk, and the carrier's own circle
  (forward 1.0, turn 0.2).
  - The circle's radius is about 5.8, so it can pass through both sources in some worlds. The gate
    therefore reads the 90th-percentile world as well as the mean.
- **The proposed gate:**
  - S-oracle's mean is at least 0.8 of its per-world geometric maximum;
  - S-shuttle at k = 256 reaches at least 0.5 of S-oracle;
  - L1-switch's lower bound is at least 0.5 of S-shuttle's mean at k = 32;
  - every blind baseline's mean is at most 0.25 of L1-switch's, and its 90th-percentile world at most
    0.5.
  - The pre-registration gives the formula for the geometric maximum and the blind policies' settings.
  - **If it fails,** E3a stops for redesign.

**Stage 1, the engineered organism (frozen; hybrid).**
- **The proposed gate:**
  - its lower bound is at least 0.8 of L1-switch's mean;
  - it beats the no-latch control and the one-module control (L1-A only), each by E2d's "uses" rule:
    both lower bounds above 0.5 visits;
  - the component tests pass, the startup test included.
- **The no-latch control is "both modules always on":** the four comparator biases at 0 and the four
  gate edges at 0, so both modules run as L1 alone.
  - **Correction to v2.1 (2026-10-02, rule 4).** v2.1 defined it as "both modules always on, q clamped
    to 0". With the biases left at −1.914, that leaves both modules mostly off: K_D 2.63-2.97 against
    31.6-35.6 (Astra, in `Brain.step`; Fable by hand).
  - That construction is kept as a separately named, descriptive **q-zero ablation**.
- **Memory, tested causally:**
  - **Paired clamp assays:** the same worlds and starts, with q clamped to each of the organism's two
    states. The first entry must be into the clamped goal in at least 90% of worlds for each state.
  - **The hold test:**
    - **Timing:** the levels are withheld from the first tick after the head leaves the source of the
      first confirmed visit, to the end of the episode. Worlds without a confirmed visit are excluded,
      and the test is not read if fewer than half of the worlds qualify.
    - **What passes:** q stays within 10% of its value at the start of the hold, and the organism's own
      active and inactive K_D at tick 600 are within 20% of their values at the start.
  - **The release test:**
    - the state is set by a two-tick level, not a clamp, and the levels are then withheld for D ticks;
    - D is the engineered organism's median leg duration on Stage 1's test worlds, fixed when Stage 1
      ends;
    - it passes if the correct module dominates afterwards, with the inactive |K_D| at most 0.1 of the
      active one, for both states.
  - **The reset test:** q set to the wrong state mid-leg. The organism turns to the wrong source, and
    resumes alternating after its next confirmed visit.
- **The mean-nose probe for each module:** the score with one module's noses fed their mean.
- **If the gate fails,** E3a stops for redesign: the parts do not compose.

**Stage 2, an evolved selector.**
- **The modules are frozen.** **The selector's 13 untied parameters evolve.** There is no tying, so no
  new machinery:

  | Parameter | Count |
  |---|---|
  | τ_q, w_qq, b_q | 3 |
  | w_aq, w_bq | 2 |
  | the four gate edges | 4 |
  | the four comparator biases | 4 |

  That is 7 weights, 5 biases and 1 time constant. The relays and the interface gain stay fixed.
- **The initial distribution, chosen to start near the ungated pair** (Fable: drawing uniformly over
  the bounds makes a working selector about 10⁻⁶-10⁻⁵ likely):
  - weights U[−0.5, 0.5];
  - biases N(0, 0.5²), clipped to ±2 (the brain's `init_bias_std`);
  - τ_q log-uniform over [0.5, 20].
  - A run starts close to the no-latch control, and selection has to build the gate and the latch.
  - This is drawn by E3's own sampler (`Genome.random` draws differently), changing only the selector.
  - **A 0-of-8 outcome reads:** "no working selector was found within this budget from this initial
    distribution", never "cannot evolve".
  - The engineered w_aq and w_bq sit on the bound (±3), so no evolved drive can exceed the engineered
    one.
- **The census:** 1 024 selectors from this distribution, and 1 024 drawn uniformly over the bounds
  (descriptive).
  - A selector qualifies if its 16-world score is at least 0.8 of the engineered organism's on the same
    worlds.
  - Qualifiers get the full check below on the test worlds.
- **The mutation:** 02's sigmas at 1× on these 13 parameters and 0 elsewhere. E4s-1 observed no sign
  change at 0.25×; 1× makes crossing zero routine.
- **The GA:** 02's (population 32, 3 elites, truncation 8), 16 worlds per genome, 300 generations, and
  validation every 25 generations on 256 worlds.
- **The champion:** the genome with the best validation mean at the final checkpoint. The test worlds
  are untouched until every champion is chosen.
- **The comparators:**
  - **random sampling,** from the same distribution: 9 600 genomes (32 × 300) scored on selection
    worlds. The top 32 are validated on the same 256 worlds, and the best is its champion;
  - **the engineered organism.**
- **Each champion's dynamical class:**
  - **bistable:** its q equation, with the relays at rest, has three fixed points, and a hysteresis
    sweep shows the levels reach both stable states;
  - **monostable:** otherwise.
- **Its memory class:**

  | Class | Requires |
  |---|---|
  | latch | bistable, and passes the hold test |
  | bistable, fails hold | bistable, and fails the hold test |
  | slow trace | monostable, and passes the release test |
  | no memory | monostable, and fails the release test |

  - Every test uses the champion's own states, not the engineered organism's:
    - its stable fixed points if it is bistable;
    - otherwise its median q in each goal phase on the test worlds.
  - A champion with the polarity mirrored (q < 0 meaning "go to A") counts as working.
- **A working selector:** a champion whose test lower bound is at least 0.8 of the engineered
  organism's mean, and which passes the clamp assays at its own states.
- **The proposed readings:**
  - **S2-a:** how many of the 8 runs reach a working selector, and each one's class.
  - **S2-b:** evolution against random sampling, by a run-level paired bootstrap of the champions' test
    scores, paired by seed index. The outcomes are ordered:
    1. "evolution better": the lower bound is above 0.5 visits;
    2. "random sampling better": the upper bound is below −0.5;
    3. "as good": the interval lies within ±0.5;
    4. "unclear".
  - **S2-c:** the census's count of working selectors from each distribution. If at least 10 of 1 024
    (about 1%) come from the GA's distribution, Stage 2 is answered at generation 0, and the wording
    says so.

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
  descriptive only. Its wiring and thresholds are pinned in the pre-registration.
- **B-task:** the same 11 neurons, signals, cue, input routing and output positions.
  - **What is free:**
    - all 121 edges among the 11 neurons;
    - the 9 non-relay neurons' τ and biases;
    - the 32 output edges, from the 4 comparator positions to the 8 turn neurons.
  - It starts from Stage 2's initial distribution, applied to all of these. It evolves at 1×, with the
    evaluations of Stage 2 and Stage 3 together.
  - **The reading (descriptive):** B-task's champions against Stage 3's, by the run-level paired
    bootstrap with S2-b's ordered outcomes.
  - **It matches neurons and inputs and outputs, not trainable capacity,** and is labelled so.

**Worlds, seeds and statistics** (all pinned in the pre-registration):
- **World ids:** new blocks, checked against every block in use by a collision test, as E4s's were:
  - selection 944M;
  - validation 945M;
  - test 946M (256 worlds);
  - assays and census 947M.
- **Run seeds:** 1 170 000 + i.
- **The statistics:**
  - within-organism comparisons on the same worlds use E2d's `world_ci`, two-sided 95%;
  - arm comparisons use the run-level bootstrap (E2d's `_boot_means`), 90% as in E4s-1;
  - there are 8 runs per evolved arm.

## Budget

**The rate,** measured from E4s-1's ten training batches: each took 1.35-1.43 hours for 8 runs ×
32 genomes × 8 worlds × 300 ticks × 1 000 generations, including validation.
- **Correction to v2.1 (2026-10-02):** E4s-1's carrier stepped 306 neurons, not 313; E3's steps 313.
- The estimate scales the rate linearly. The projection measures the real 600-tick, 16-world shapes
  before any training.

| Part | Shape | Estimate |
|---|---|---|
| Engine check, smoke, projection, Stages 0-1, assays | — | 1.0 h |
| The two censuses | 2 × 1 024 × 16 worlds | 0.2 h |
| Stage 2 | 8 runs, 16 worlds, 600 ticks, 300 generations | 1.7 h |
| Random sampling | the same evaluations | 1.7 h |
| Stage 3 | 8 runs, 16 worlds, 600 ticks, 500 generations | 2.8 h |
| B-task | Stage 2 + Stage 3's evaluations | 4.5 h |
| Evaluation, including B-shared | — | 1.5 h |
| **Total** | | **about 13.4 h** |

- **The cap is 30 GPU-hours for E3a, set by the owner** (D159).
- **If the projection exceeds the cap,** reductions are decided once, from the projection, before any
  training, in this order:
  1. B-task, to Stage 2's evaluations;
  2. B-task, dropped;
  3. Stage 3, to 4 runs;
  4. Stage 3, dropped;
  5. random sampling, to 4 runs, paired with GA runs 0-3.
- **The minimum viable E3a** is Stage 2's 8 runs and 4 runs of random sampling.
- A stage stopped by the cap is reported as stopped, and is rerun only under the E2 stage frame's rule.

## What E3a cannot show

- Anything about worm behaviour or its circuits.
- Trails, mazes or colonies: that is E3b, which holds the roadmap's gate.
- Whether modularity pays: that is E3c.
- Gluing two whole N2 brains: that is E4.

## Changes from v2.1

| v2.1 review item | v2.2 |
|---|---|
| The no-latch control was mostly off (both) | Both on: comparator biases and gate edges at 0; the q = 0 clamp kept as a named ablation; a dated correction |
| The classification misfiled real latches (both) | Dynamical class (bistable, with both states reachable) separate from memory class; four classes; tests on the champion's own states |
| Clamp values undefined for champions (Fable) | The champion's fixed points, or its median q per goal phase; mirrored polarity counts |
| Clamp assays do not show retention (Astra) | The release test: set by a level, withheld for D ticks, then read |
| When withholding begins; legless episodes (Astra) | Timed from leaving the first confirmed visit's source; worlds without one excluded; a minimum share |
| The initial distribution made a null near-certain (Fable); uniform not what `Genome.random` does (Astra) | A start near the ungated pair, by E3's own sampler; a uniform census as description; 0-of-8 wording; drive on the bound noted |
| Census qualification; "not small" (Astra) | A qualifier rule, then the full check; at least 10 of 1 024 |
| S2-b needs ordered outcomes, including "random better" (Astra) | Four ordered outcomes |
| B-task had no reading; its free parameters (both) | Free parameters listed; a descriptive reading against Stage 3; Stage 2's distribution |
| The latch's number was from the wrong update rule (Astra) | Rechecked: −0.2197; a dated correction; a test against `Brain.step` |
| Startup not tested (Astra) | A startup test at ticks 5-15 |
| A Euclidean spawn cap; the scent at the spawn; joint sampling; "start blind" mislabelled (both) | A Euclidean cap of 16; minimum scent 0.0286; joint sampling stated; relabelled with a dated correction |
| 306 neurons in E4s-1, not 313 (Astra) | Corrected |
| The reductions did not reach the minimum (Astra) | Five steps that reach it, decided once from the projection |
| Champion selection, random sampling's validation (both) | Pinned |
| The cap | 30 GPU-hours for E3a (D159) |

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
