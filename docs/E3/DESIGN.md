# E3: the minimal A/B organism (design v2, 2026-10-02)

Status: v2, for a confirmation round by Astra 6 and Fable 5.1. Nothing has run. A pre-registration
follows only if both agree.
- **v1** (the previous commit of this file): both said "revise"
  (`docs/reviews/20261002-E3-design/`). Both agreed with the staging and with starting from L1. v2
  takes every must-fix; the map is the last section (D156).
- **Its basis:**
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

- **The arena:** Task N's 24 × 24 arena (centres within the 16 × 16 box that the wall clearance
  leaves), with one wey.
- **The sources:** A and B are fixed per world, drawn from the world's seed by rejection sampling, as
  Task N's targets are. 8 ≤ |A − B| ≤ 14, and both are at least 6 from the spawn.
  - A check found this feasible for every spawn.
  - At 14 cells the far scent is still 6.6% of its peak, inside the truncation at 3σ = 18. v1's 12-18
    put it at the truncation edge (Fable).
- **The scents:** separate channels, each A·exp(−d²/2σ²) with σ = 6 and amplitude 1, sensed bilaterally
  as `a_left`/`a_right` and `b_left`/`b_right`, scaled as food is.
- **The goal (the scorer's state, never given to the brain):** it is fixed at **A** at tick 0. A visit
  to the goal switches it. A visit to the other source counts nothing and switches nothing.
- **The event contract** (Astra):
  - **inside(X)** at tick t means the head, after the tick's movement, is within R = 1.5 of X.
  - **An entry** into X is inside(X) at t and not at t − 1. Re-arming is automatic: the head must
    leave and come back.
  - **A confirmed visit** is an entry into the current goal; the goal switches on the next tick. A
    and B are at least 8 apart, so the head can never be inside both.
  - **The ledger** (extending Task N's `_advance_targets` and `target_events`, not new machinery;
    Astra) records the tick of every entry into A and into B, every confirmed visit, the leg's path
    length, and the goal at every tick.
- **The score:** confirmed visits per episode, over a horizon of 600 ticks. That is a pilot
  assumption: at L1's pace (about 58 ticks per leg on Task N), about 10 legs.
- **The signals to the brain:**
  - **`at_a` and `at_b` are levels**, equal to 1 while inside(A) or inside(B), and 0 otherwise. Fable
    and Astra: a one-tick pulse cannot switch the latch.
  - **The latch's start cue:** at ticks 0-4 the world emits `at_b` = 1 as a level, as if the wey had
    just visited B, so the latch starts in "go to A" (Fable, Astra). The latch never starts on its
    unstable point.
- **No N2 interface in E3a** (both).
  - The organisms live on the silent carrier: the 302 worm neurons with zero weights, conductances
    and biases, except the carrier's forward and turn biases.
  - The new signals reach only the grafted modules. ALM and AVM, which carry collision signals, are
    untouched.
- **The engine change, with its check (rule 7, narrowed as Astra asks):**
  - **The new code:** the `shuttle` task in the world; `graft.py` generalised to several modules per
    graft, nose signals other than food, and probes per nose pair.
  - **The check, with the task off,** is against the previous engine at fixed compositions: Task N's
    and foraging's per-world states, events and scores are identical on declared worlds. That includes
    E2's GA generation 0-25 hashes on the GPU (as E4s did), and per-tick states and events on the CPU.
  - No broader claim is made.

## E3a: the organism's parts

**L1-A and L1-B.** Two copies of E4s-0's L1 comparator, with new neuron names (`E3_A_NL`, `E3_A_CL`,
and so on).
- L1-A's noses read A's scent and L1-B's read B's. Both drive the same 8 turn neurons, push-pull, as L1
  does.
- **The organism carries L1's parameters,** copied from `module.json` (sha256 checked), not the hashed
  file itself.

**The latch, one neuron q:** τ_q dq/dt = −q + 2·tanh q + w_s·(at_b − at_a), with bias 0 and τ_q = 1.
- **Settled states:** q* = ±1.915, so tanh q* = ±0.957. "Go to A" is q > 0.
- **Switching drive:** w_s = 3, through the levels.
  - From the opposite settled state, a level of 1 crosses zero in about 0.7 τ_q (Fable's estimate), so
    a pass of 1-2 ticks inside a radius switches it.
  - Measured in the real integrator (32 substeps), from both states, for passes of 1, 2 and 4 ticks.
- **Hold:** with no input, q holds its sign indefinitely. The test is 600 ticks with the levels
  withheld; a leaky trace would decay.

**The gate, by saturation, with the bias shift** (Fable's numbers, Astra's candidate):
- **L1-A's comparators** get +g·tanh(q), and **L1-B's** get −g·tanh(q), with g = 2. Every comparator's
  bias is −g·0.957 = −1.914 (within `b_max` = 2).
- **Going to A:** L1-A's comparators sit at 0 offset, linear and active. L1-B's sit at −3.83, saturated,
  with a slope near 0.002. The reverse holds when going to B.
- **This changes the comparators' operating points,** not only their outputs. It is declared as part
  of the selector interface (Astra).
- **Registered component tests** (open loop, on the carrier, at both latch states):

  | Test | Requirement |
  |---|---|
  | the active module's K_D | at least 30 (L1 alone: about 36) |
  | the inactive module's K_D | at most 1% of the active one's |
  | the turn offset added by the inactive module | below 0.02 |
  | switching and recovery | the active module reaches 90% of its gain within 10 ticks of the latch crossing |

**The inactive module keeps updating:** its comparators are driven into saturation, never frozen or
reset (the roadmap's addition). Both modules' proposed turn contributions are logged every tick
(Astra).

## E3a: stages, controls and gates

**Stage 0, positive controls (scripted; minutes).**
- **S-shuttle:** E1's S-const on the current goal's scent, with a perfect scripted memory. Two gains:
  k = 32, matched to L1's gain, and k = 256 (E1's best).
- **S-oracle:** straight to the current goal.
- **L1-switch, the artefact's own positive control** (both): one L1 on the carrier, whose noses the
  world feeds the current goal's scent. It is Stage 1's ceiling, and it separates a module failure from
  a latch or gate failure.
- **Blind baselines:** constant motion, a persistent random walk, and **the carrier's own circle**
  (forward 1.0, turn 0.2, no module).
- **The gate:**
  - L1-switch's lower bound must exceed a registered fraction of S-shuttle at k = 32;
  - every blind baseline must stay below a registered level.
  - If L1-switch fails, E3a stops for redesign; L1 does not travel this geometry.

**Stage 1, frozen modules with the fixed latch and gate (engineered; hybrid).**
- **The gate:**
  - its score's lower bound is at least a registered fraction of L1-switch's;
  - it beats the no-latch control (both modules always on) and the one-module control (L1-A only);
  - the component tests above pass.
- **Memory, tested causally** (Astra):
  - **paired assays:** the same world, the same body state and the same observations, with q clamped
    to each sign. The organism must head to the clamped goal;
  - **a hold test:** the levels withheld for a whole leg; the latch keeps its state;
  - **a reset test:** q set to the wrong state mid-leg; the organism turns to the wrong source, and
    recovers at the next visit.

  Without these, alternation could come from body dynamics.
- **The mean-nose probe for each module** (E4s's lesson): the score with one module's noses fed the
  mean, to measure how much of the score is stereo use.

**Stage 2, an evolved selector** (the roadmap's step 2).
- **The modules are frozen.** The selector evolves: q's τ, bias and self-weight, w_s, the two gate
  weights and the comparator biases. That is 7 parameters (Astra: ownership stated).
- **The initial distribution:** each parameter uniform over its bound's full range. A random census of
  1 024 selectors runs first (as E4s-0 did), with each one's score and whether it is bistable.
- **The mutation:** the selector's parameters at 1× 02's sigmas, which can cross zero (Fable: E4s-1
  showed 0.25× cannot). Everything else is frozen.
- **The comparators:**
  - **random sampling** at the same budget (E2's floor fired before);
  - **the engineered latch** (Stage 1).
- **Selection** uses 16 worlds per genome, not 8 (E2d: 8 worlds rank close genomes poorly).
- **The question:** does evolution find a working selector? Is it a clean, bistable latch, or a leaky
  trace or transient modes (Agmon and Beer, via the literature review)? The hold and paired tests above
  classify each champion.

**Stage 3, joint fine-tuning: descriptive** (Fable).
- **What evolves:** the modules' and the selector's parameters, at 0.25×, as in E4s-1. **The silent
  worm's 302 neurons and the carrier's biases stay fixed** (Fable, Astra: otherwise it becomes N2-host
  evolution).
- **A share of evaluations** goes to each module's own skill: single-source navigation with the latch
  clamped.
- **What it measures:** whether joint tuning improves the shuttle, and whether the modules keep their
  component skills.

**The baselines:**
- **B-shared:** one L1 whose two nose pairs (A's and B's) are gated by the latch, with the same
  saturation trick on the noses. 7 neurons against 9; its memory is its own latch (Astra). Descriptive:
  Fable expects a tie, and it cannot speak to modularity.
- **B-task:** a controller of the same neurons (9), receiving the same signals, fully connected among
  them, with the same output edges. It is evolved from the same initial distribution at the same
  budget as Stage 2 plus Stage 3.

## Budget (itemised; Fable, Astra)

**The carrier steps about 311 neurons,** so a rollout costs what an N2 rollout costs. E4s-1 took
about 0.2 GPU-hours per run of 1 000 generations at 300 ticks, so about 0.4 h at 600 ticks.

| Part | Runs | Estimate |
|---|---|---|
| Engine check, smoke, projection | — | 0.5 h |
| Stage 0 and Stage 1 (tuning, gates, assays) | — | 0.5 h |
| The Stage 2 census | 1 024 genomes × 16 worlds | 0.2 h |
| Stage 2 | 8 runs | 3.2 h |
| Random sampling | 8 runs | 3.2 h |
| Stage 3 | 8 runs | 3.2 h |
| B-task | 8 runs | 3.2 h |
| Evaluation | — | 1.5 h |
| **Total** | | **about 15.5 h** |

- **Proposed cap: 20 GPU-hours for E3a.** The owner has not yet set a ceiling for E3; this asks for one.
- **The projection measures the 600-tick shapes before training.** The run counts shrink, in a
  pre-stated order, if it exceeds the cap.

## What E3a cannot show

- Anything about worm behaviour or its circuits.
- Trails, mazes or colonies: that is E3b, which holds the roadmap's gate.
- Whether modularity pays: that is E3c.
- Gluing two whole N2 brains: that is E4.

## Changes from v1

| v1 review item | v2 |
|---|---|
| A one-tick pulse cannot switch the latch (both; and the literature review said so) | Levels while inside a radius; w_s = 3; switching tested for passes of 1, 2 and 4 ticks |
| The latch starts on its unstable point (both) | A start cue: `at_b` for ticks 0-4; the goal fixed at A |
| An event contract (Astra) | Entry, re-arming, the confirmed visit and the ledger defined; Task N's ledger extended |
| The gate: the bias shift and its bound (both) | g = 2, bias −1.914; the numbers stated; component tests registered |
| A positive control for the artefact (both) | L1-switch, as Stage 1's ceiling; S-shuttle at k = 32 and 256; the carrier's circle |
| Memory tested causally (Astra) | Clamped-latch paired assays; hold and reset tests |
| No N2 interface in E3a (both) | Dropped; the carrier only |
| Stage 2 cannot start from random at 0.25× (Fable); ownership (Astra) | 7 selector parameters, a full-range start, 1× mutation, a census, random sampling, 16 worlds |
| Stage 3 under-specified; the host must not evolve (both) | The modules and selector only, at 0.25×; the host and carrier fixed; descriptive |
| B-shared and B-task (both) | B-shared's memory its own, descriptive; B-task's mask, signals and budget stated |
| The budget (both) | Itemised from E4s-1's measured cost; a 20-hour cap proposed; projected first |
| The engine claim narrowed (Astra) | Specific identity checks at fixed compositions |
| Geometry (Fable) | 8-14 apart, spawn at least 6 from both; checked feasible |
| `graft.py`'s limits; L1's parameters copied; dtypes (Fable) | Generalised; L1 carried by its parameters; every per-world array's dtype declared |
