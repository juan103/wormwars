# E3a pre-registration: the shuttle, a two-module organism with a latch

Status: **final**, 2026-10-02.
- **Its reviews:**
  - **The first draft** (a7177e7): both "bind after fixes" (`docs/reviews/20261002-E3a-prereg/`; D164).
  - **The second draft** (3a513e6): both "bind after fixes" again
    (`docs/reviews/20261002-E3a-prereg-2/`; D165).
  - This text takes every fix from both rounds.
- **Its design:** `docs/E3/DESIGN.md` v2.4, agreed by Astra 6 and Fable 5.1 (D163). The departures
  from it are listed in §12.
- **Binding:** it binds when committed and pushed after both reviewers agree, before any stage of E3a
  runs (rule 2). From then on the text is never changed; amendments go in §13, dated.
- **The cap:** 30 GPU-hours, set by the owner (D159).
- **Nothing has run.** The only numbers below that come from a run are the geometry check's
  (`docs/E3/geometry-check.json`, CPU) and E4s-1's measured batch times.

## 1. The question and its frame

Two copies of E4s-0's comparator L1 sit on the silent carrier, one smelling source A and one smelling
source B. A one-neuron latch q, driven by "I am at A" and "I am at B" signals through two relays,
gates which module steers. The task is to shuttle: A, then B, then A, and so on.
- **Stage 1:** does the engineered organism shuttle, and does its memory work causally?
- **Stage 2 (S2-a, S2-b, S2-c):** with the modules frozen, does evolution find a working selector
  from a start near the ungated pair? Does it beat a blind search over the whole range, and how
  often does a random draw already work?
- **Stage 3 and the baselines** (descriptive): does joint tuning help? How does a task-optimised
  controller of the same neurons compare?

**Frame, stated in every claim:**
- Stereo sensing is a game-design choice (the owner's option (a)).
- The organism is a hand-built circuit on a silent worm, outside the N2 mask. Nothing here is about
  worm behaviour or its circuits.
- E3a does not meet the roadmap's E3 gate (unseen branching mazes); that belongs to E3b.

## 2. Fixed inputs

**The module:** `experiments/E4s-stereo-module/E4s-0/module.json`, sha256
`9613cd155a20ed2cfb891c1bd10fed16814f24a04f912a1940524f2378e877d4` (LF line endings), checked at load.
- **Its parameters are copied,** under new names, into each module:
  - noses τ 0.5, bias 0;
  - comparators τ 0.5, bias 0, before the gate's shift;
  - its 20 edges: nose to comparator ±3, and comparator to SMDD, RMDD, SMDV and RMDV ±3.
- **The carrier:** the silent N2 worm (all 302 neurons' weights, conductances and biases at 0) with
  forward command 1.0 and turn command 0.2, as `carrier_genome` builds it.

**The task's base:** E1's frozen Task N configuration (`experiments/E1-navigation/freeze.json`,
sha256 `c5c48f83079a6bd0dd48bdeb13d02ab211a08eb64433fdc8372cbd6e74bcaae9`, checked at load), changed
only as §3 says:
- σ 6, amplitude 1, R = 1.5;
- the 24 × 24 arena with wall clearance 3;
- `max_speed` 0.35, `max_turn` 0.30, `forward_gain` 4, `turn_gain` 2;
- 32 substeps, and `pad_single_strain` on;
- `sense_scale_food` 0.35 for the scents.

**The GA:** 02's GA as E2 and E4s-1 kept it (`evolve_batch`):
- population 32, 3 elites, truncation 8;
- unshaped fitness (confirmed visits);
- 02's sigmas (w 0.08, log-τ 0.15, bias 0.05), multiplied per parameter by the arm's factor (§4);
- `p_mutate` 1.

**E2d's rules, imported unchanged** from `scripts/e2d.py`:
- `world_ci`: a paired percentile bootstrap over worlds, two-sided 95%, 10 000 resamples, seed 0. An
  organism's own interval is `world_ci` of its scores against zeros.
- `classify`: "uses" if both lower bounds > 0.5; "no material benefit" if both intervals lie inside
  (−0.25, 0.25); else "unclear".
- `_boot_means`, for the run-level bootstrap: 10 000 resamples, seed 20 261 002, with the 5th and
  95th percentiles (90%), as in E4s-1.

**The turn command u** is the world's: 0.5 × `turn_gain` × (the mean tanh of the 4 dorsal turn
neurons minus that of the 4 ventral ones), clamped to [−1, 1].

## 3. The task ("shuttle")

**Geometry,** drawn per world from the world's own stream, as `_build_targets` draws Task N's targets:
- the spawn is Task N's (one wey);
- A and B are drawn jointly, uniformly in the box [4, 20]², and both are redrawn until:
  - 8 ≤ |A − B| ≤ 14;
  - |A − spawn| and |B − spawn| are both at least 6 and at most 16;
- up to 10 000 tries, as Task N's sampler. A world that exhausts them raises an error; the geometry
  check found every sampled spawn accepting at least 11.8% of draws.

**The scents:** two sensing-only channels, A's and B's, each with amplitude 1, σ 6 and Task N's square
support (zero beyond 18 cells along either axis).
- They are sampled at the two noses as `food_left` and `food_right` are, and scaled by 0.35.
- They are named `a_left`, `a_right`, `b_left` and `b_right`.
- They are never written into the food field.

**Events** (after each tick's movement, in the world's order: sense, think, move, then events):
- **inside(X)** at tick t: the head is within R of X after tick t's movement.
- **An entry** into X: inside(X) at t and not at t − 1. Inside at tick 0 is not an entry (the spawn
  is at least 6 away).
- **The goal** is A at tick 0. **A confirmed visit** is an entry into the current goal, and the goal
  switches before tick t + 1's events. An entry into the other source changes nothing.
- **The score** is the number of confirmed visits in 600 ticks.
- **The ledger** extends Task N's (`target_events`), per world:
  - the tick of every entry into A and into B;
  - the tick of every confirmed visit;
  - each leg's path length;
  - the goal at every tick.

**The signals to the brain:**
- `at_a` = 1 while inside(A), and `at_b` = 1 while inside(B), else 0. They are sensed at tick t + 1
  for the position after tick t.
- **The start cue:** at ticks 0-4, `at_b` = 1, so the latch starts in "go to A". The cue is not an
  event and never enters the ledger.
- **For L1-switch alone:** `goal_left` and `goal_right`, the current goal's scent, scaled as the
  others.

**Routing** (the injection formula as for food: gain × `input_gain`, clamped to ±`input_max` = 5):

| Signal | Neuron | Gain |
|---|---|---|
| `a_left`, `a_right` | E3_A_NL, E3_A_NR | 1 (L1's `nose_gain`) |
| `b_left`, `b_right` | E3_B_NL, E3_B_NR | 1 |
| `at_a` | E3_RA | 3 |
| `at_b` | E3_RB | 3 |

For B-shared: `a_left` → E3_S_AL, `a_right` → E3_S_AR, `b_left` → E3_S_BL and `b_right` → E3_S_BR,
each at gain 1. For L1-switch: `goal_left` → E4S_NL and `goal_right` → E4S_NR, each at gain 1.

None of these signals reaches a worm neuron. ALM, AVM and every N2 sensor are untouched.

**Dtypes:**

| Quantity | Dtype |
|---|---|
| positions, scents, signals, neuron states | the world's float32 |
| ledger ticks and counts | int64 |
| path lengths | float64 |
| the goal | int8 |
| per-tick logs | float32 |

The per-tick logs are q, RA, RB, u, and each module's turn contribution. A module's turn contribution
is its summed signed input current into the 4 dorsal turn neurons minus that into the 4 ventral ones,
before their nonlinearity.

## 4. The organisms

**The engineered organism (E):** 11 grafted neurons.

| Neuron | τ | Bias |
|---|---|---|
| E3_A_NL, E3_A_NR, E3_B_NL, E3_B_NR | 0.5 | 0 |
| E3_A_CL, E3_A_CR, E3_B_CL, E3_B_CR | 0.5 | −1.914 |
| E3_RA, E3_RB | 0.5 | 0 |
| E3_Q | 1 | 0 |

- **Edges:** each module's 20 L1 edges (40 in all), plus:

  | Edge | Weight |
  |---|---|
  | E3_Q → E3_Q | 2 |
  | E3_RA → E3_Q | −3 |
  | E3_RB → E3_Q | +3 |
  | E3_Q → E3_A_CL, E3_Q → E3_A_CR | +2 |
  | E3_Q → E3_B_CL, E3_Q → E3_B_CR | −2 |

  That is 47 edges.
- **Its stable states:** q* = ±1.91501, so tanh q* = ±0.957504. "Go to A" is q > 0.

**The controls** (frozen; each a stated change to E):
- **No-latch ("both on"):** the four comparator biases at 0 and the four gate edges at 0.
- **q-zero ablation** (descriptive): E with q clamped to 0.
- **One-module:** E with module B's 16 output edges at 0, A's comparator biases at 0 and A's gate
  edges at 0.
- **L1-switch:** one L1 (module.json's names) on the carrier, its noses fed `goal_left` and
  `goal_right`.

**Scripted controls,** E1's controllers with E1's frozen parameters (`freeze.json`, "tuned") unless
stated:
- **S-oracle:** E1's oracle (k 2, speed 1), steering to the current goal.
- **S-shuttle:** E1's S-const on the current goal's bilateral scent, reading the scorer's goal (a
  perfect scripted memory, privileged as the oracle is). Two settings:
  - k 32, speed 1, turn 0.2 (E1's best with k ≤ 32);
  - k 8192, speed 1, turn 0 (E1's best overall).
- **Blind:**
  - constant motion (speed 0.8, turn 0.1);
  - a persistent random walk (speed 1, rate 1, persistence 0.5, seed 0);
  - the carrier's circle (the carrier, no graft).

**B-shared** (engineered, descriptive; 9 grafted neurons):
- **Neurons:**
  - noses E3_S_AL, E3_S_AR, E3_S_BL and E3_S_BR (τ 0.5, bias −1.914);
  - comparators E3_S_CL and E3_S_CR (τ 0.5, bias 0);
  - E3_RA, E3_RB and E3_Q as in E.
- **Edges:**
  - each nose pair onto the comparators in L1's pattern (left nose → CL +3, → CR −3; right nose → CR
    +3, → CL −3);
  - the comparators' 16 L1 output edges;
  - q's own three edges as in E;
  - the gate: q → A's noses +2, q → B's noses −2.
- **Why it works:** an inactive nose pair sits near tanh(−3.83) ≈ −0.999, and equal values on its two
  noses cancel in the push-pull.
- It passes the component tests of §6 with "module" read as "nose pair". To ablate a nose pair, its
  4 nose-to-comparator edges are set to 0.

## 5. The stages, in order (each writes a record committed and pushed before the next starts)

1. **Projection** (timings only; smoke ids 0-9 999, seed base 1 179 000);
2. **G-E, the engine check;**
3. **G0, Stage 0's gate;**
4. **G1, Stage 1's gate;**
5. **E's calibration** (D, and E's measured stimulus duration);
6. **the censuses' screening scores,** with E's mean on the same 16 census worlds (Fable);
7. **training batch 1:** Stage 2 GA, runs 0-7;
8. **training batch 2:** random sampling, runs 0-7;
9. **Stage 2's champions:** the GA's final populations and random sampling's top 32 validated, and the
   champions frozen;
10. **training batch 3:** Stage 3, runs 0-7, from the frozen Stage 2 champions;
11. **training batch 4:** B-task, runs 0-7;
12. **Stage 3's and B-task's champions:** validated and frozen;
13. **calibration** of every champion and census qualifier;
14. **evaluation on the test worlds,** in this order:
    1. the registered parts: E, Stage 2's and random sampling's champions, and the census qualifiers;
    2. then the descriptive parts: Stage 3, B-task and B-shared.

    Scores, assays, classes, and the qualifiers' full check.

Every stage writes a record that is committed and pushed before the next starts.

**The projection** times each shape twice, using the second timing:
- training: a 4-generation `evolve_batch` of 8 runs at 256 × 16;
- validation: 32 × 256, one run's final population;
- census screening: 256 × 16;
- a single organism: 1 padded × 1 024;
- assays: 1 padded × 256;
- the probe: open loop.

It records only timings.

**The workload the projection prices:**
- every stage at the shapes above, with these counts:
  - E, the controls and B-shared once each;
  - 8 champions per arm;
  - **64 census qualifiers per census;**
- the qualifiers' full check: calibration (256 worlds), the test worlds (256) and the clamp assays
  (2 × 256), plus the open-loop assays;
- **the cap on qualifiers:** if more than 64 qualify in a census, the 64 with the highest screening
  score (ties to the lower index) get the full check. S2-c then reads "at least k", and names the
  number left unchecked;
- after stage 6, the evaluation's projection is recomputed with the actual count.

**The compositions:**

| Use | Strains per chunk × worlds |
|---|---|
| test-world and calibration scoring | 32 × 256 |
| validation | 32 × 256 per run |
| census screening | 256 × 16 |
| gates | 1 padded × 1 024 |
| assays | 1 padded × 256 |

Every record states its composition (rule 6).

**G-E, the engine check** (rule 7). The previous engine is the commit before E3a's code.
- **On the GPU:** E2's formal GA batch for generations 0-25, with every generation's best-genome hash
  equal to `experiments/E2-optimizer-screen/train-ga.json`. This is `scripts/e4s_equivalence.py`'s
  check, rerun.
- **On the CPU,** every per-tick state, event and score identical between the two engines:
  - **Task N:** 300 ticks on smoke ids 0-15 (world seed 1 179 500), for 4 random N2 genomes
    (`initial_population`, run seed 1 179 500) and for E4s-1's M run 0 generation-0 genome (L1 on
    random N2, `embedded_population` with run seed 1 160 000, strain 0);
  - **foraging:** 300 ticks on the same ids, under the default configuration, for the same 4 random
    genomes.
- **The graft:** E4s-1's grafted genome rebuilt by the generalised `graft.py`, bit-identical to the
  old build, with its `MODULES` registration unchanged.
- **The test:** all identical. A failure stops E3a until the code is fixed, and G-E is rerun.

**G0, Stage 0's gate** (gate worlds, 1 024; one padded strain per controller):
- S-oracle's mean is at least 0.6 of the mean **straight-run reference.**
  - **Per world:** with t₁ = (|A − spawn| − R) / 0.35 and t_leg = (|A − B| − 2R) / 0.35 + π / 0.30,
    unrounded, the reference is 0 if t₁ > 600, else 1 + ⌊(600 − t₁) / t_leg⌋.
  - **It models** a straight run at full speed plus a stationary half-turn at the full turn rate per
    reversal. It is not a strict bound: the engine turns and moves in the same tick, and reversal
    angles vary (Astra).
  - **The threshold of 0.6** is a new choice, made before any run. It is a loose sanity check; Fable
    estimates the oracle near 0.8-0.9 of it.
- S-shuttle at k 8192 reaches at least 0.5 of S-oracle's mean.
- L1-switch's lower bound is at least 0.5 of S-shuttle's mean at k 32.
- Every blind control's mean is at most 0.25 of L1-switch's mean, and its 90th-percentile world at
  most 0.5 of it.

**G1, Stage 1's gate** (the same gate worlds, except where an assay names its own):
- E's lower bound is at least 0.8 of L1-switch's mean;
- `classify`(E against no-latch, E against one-module) gives "uses";
- E passes every component test (§6);
- **E passes these memory assays,** at its stable states q* = ±1.91501 (q > 0 is A), with a stimulus
  of 2 ticks and W = 20:
  - the clamp assays;
  - settable;
  - the hold;
  - the reset.

  E's release test needs D, so it is reported after calibration and does not gate.

**E's calibration** (after G1 passes; calibration worlds):
- **D:** E's median leg duration over completed legs after the first confirmed visit, rounded half up.
  Legs cut off by the episode's end are excluded.
- **E's measured stimulus duration,** reported. E's assays use 2 ticks by design; the real level is
  probably longer (Fable estimates 6-10 ticks).

**Champions' and qualifiers' calibration** (stage 13; calibration worlds):
- **The stimulus duration:** the median, pooled over A and B, of the number of consecutive ticks of
  the visited source's level, starting at each confirmed entry.
  - Rounded half up, at least 1.
  - Levels cut off by the episode's end are excluded.
  - If the pool is empty, it is 2.
- **For a monostable champion:** its median q in each goal phase.

**Gate failures and reruns** (E4s-1's rules):
- **A gate that completes and fails its test is final.** E3a stops for redesign, and the failure is
  reported. A re-gate needs a dated, reviewed amendment, on fresh worlds.
- **A stage that stopped** (a crash, a kill, a non-finite score) may be rerun once, with unchanged
  seeds and inputs; a stopped rerun is final.
- **A stage stopped by the cap is not rerun.**

## 6. Measures

**The probe** (every K_D):
- **The setup:**
  - open loop on the carrier, from a copy of the state under test;
  - q, RA and RB held at their saved values;
  - both modules' noses at m, with the probed module's L = m + d/2 and R = m − d/2, and d = ±0.001;
  - 50 ticks, then the mean of u over 10 more ticks.
- **The result:** K_D = (u(+d) − u(−d)) / 0.002, signed in L1's convention, so a module steering
  toward its source has K_D > 0.
- m = 0.05 unless a test names others.

**The component tests** (E and B-shared):

| Test | Requirement |
|---|---|
| the active module's K_D, at m in {0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.35}, from each stable state | at least 30 |
| the inactive module's | \|K_D\| at most 0.3 at every m |
| the inactive module's offset: \|u_with − u_without\|, where u_without has the inactive module's 16 output edges at 0 (B-shared: its 4 nose-to-comparator edges), at d = 0 | below 0.02 at every m |
| switching and recovery: after a two-tick level for the other goal, the newly active module's K_D, probed each tick | reaches 90% of its settled value within 10 ticks of the level's end |
| startup: from tick 0 with the cue, A's K_D probed at ticks 5-15 | at least 30 from tick 10 |

**The memory assays.**
- **Where they apply:**
  - E (G1);
  - every Stage 2, random-sampling and Stage 3 champion;
  - every census qualifier (stage 14).
- **Where they do not:**
  - B-task, whose recurrent inputs into q break the scalar q equation;
  - the scripted controls and L1-switch, which have no q.
- **The states:**
  - **for a bistable q,** its two stable fixed points;
  - **for a monostable q,** its calibration medians per goal phase.
  - **The release test's start for a monostable q** is the root with the most negative f′, with ties
    going to the lower q. This is defined whether or not any root meets the stability threshold
    (Astra: w_qq 1.0001, b_q 0 has stable roots at ±0.0173, too close to count as bistable).
  - "The separation" s is the distance between the two states. A tolerance of 10% means within
    0.1·s.
- **Which state is which goal:**
  - For E, q > 0 is A.
  - For a champion or a census qualifier, it is the one-to-one assignment of its two states to A and
    B under which both clamp assays pass (Fable). If neither assignment passes, it is the one with the larger summed first-entry
    share, and if they tie, the one with the higher state as A.
  - The assignment is reported. It fixes the "active module" in the hold, so mirrored champions are
    tested correctly.
- **The stimulus for goal X:** the level of the other source (`at_b` for goal A, `at_a` for goal B),
  for the organism's stimulus duration.
- **The window:** W = max(20, ⌈10·τ_q⌉) ticks, starting at the stimulus's last tick and read at its
  end.
- **The clamp assays:**
  - assay worlds, 600 ticks, with q clamped to each state in turn;
  - each passes if the first entry is into that state's goal in at least 90% of the worlds;
  - a world with no entry is a failure;
  - **They are not applicable** if s < 0.1, or, for an organism whose states come from calibration (a
    monostable champion or qualifier), if a goal phase never occurs on the calibration worlds. E's
    states are fixed, so its G1 assays never depend on calibration (Astra).
  - **"Not applicable" counts as not passed,** so such an organism is not working (Fable).
- **Settable** (bistable only): starting from each stable state, settled, with the relays at rest,
  the stimulus for the other goal leaves q within 10% of the other state at the end of W.
- **The hold** (bistable only): starting from each stable state, settled, with the relays at rest,
  apply its own goal's stimulus, wait W, then run 580 ticks with no levels. It passes, for both
  states, if:
  - q at the end is within 10% of its fixed point;
  - the active module's K_D is at least 15, and at least 0.8 of its value at the fixed point;
  - the inactive |K_D| is at most 0.1 of the active one.
- **The release test:** from q's computed equilibrium (each stable one, for a bistable q), with the
  relays at rest, the stimulus for goal X, then D ticks with no levels. It passes, for both goals,
  if X's module has a K_D of at least 15, and the other's |K_D| is at most 0.1 of it.
- **The reset** (E, in G1):
  - **The setup:** on the assay worlds, a one-time write of q to E's "go to A" state, 10 ticks after
    `at_a` returns to 0 following the first confirmed visit (Fable: 10 ticks after the visit itself
    often finds the head still inside A).
  - **What passes:** in at least 70% of the worlds with a first confirmed visit by tick 500, the next
    entry is into A, and a confirmed visit to B follows.
  - **A world where the write never happens stays in the denominator and fails** (Fable). That
    covers `at_a` never returning to 0, or returning within 10 ticks of the episode's end.
- **The fixed points** of f(q) = −q + w_qq·tanh q + b_q, with the relays at rest:
  - **If w_qq > 1,** f's stationary points ±acosh(√w_qq) split the line into three monotone
    intervals. Otherwise the line is one interval.
  - Each interval, bounded by |q| ≤ |w_qq| + |b_q| + 1, holds at most one root. It is found by
    bisection to 1e-12 when the interval's ends differ in sign or one is exactly 0.
  - A stationary point where |f| < 1e-12 is a tangent root, and is not stable.
  - **A root is stable** if f′(q) = −1 + w_qq·sech²q < −1e-6.
  - **Bistable** means two stable roots at least 0.1 apart; otherwise the structure is monostable.
  - **Correction of the design (D164):** the design's grid of 100 001 points can miss a pair of roots
    inside one cell. Astra's example, rechecked: w_qq 1.0119999647, b_q 0.0008732175 has a missed
    stable root at −0.10934, with f′ −2.7e−6.

**The memory class** (Stage 2 and Stage 3 champions; operational, so "no memory" means these assays
failed):

| Class | Requires |
|---|---|
| latch | bistable, settable both ways, and passes the hold |
| bistable, not a latch | bistable, otherwise; this includes slow settling within W |
| slow trace | monostable, and passes the release test |
| no memory | monostable, and fails the release test |

- The release test is also run, descriptively, on every "bistable, not a latch" champion.
- A two-tick version of settable and of the release test is reported beside each champion's own.
- The hysteresis sweep (the relay drive ramped from 0 to 3 and back over 200 ticks each way) is
  descriptive.

**A working selector:** a Stage 2, random-sampling or Stage 3 champion, or a census qualifier, is
working if both hold:
- its test-world lower bound is at least 0.8 of E's test-world mean;
- both of its clamp assays pass.

A champion with mirrored polarity can be working.

**Also measured, on the test worlds** (descriptive):
- each module's mean-nose probe: the score with that module's two noses fed their mean;
- per-tick turn contributions;
- generation 0's turn offsets and K_D, and each logged generation's offsets;
- **each module's skill,** for Stage 2's and Stage 3's champions (not the checkpoint candidates, which
  are not calibrated; Astra): the clamp assays' first-entry share for that module's state on the
  assay worlds, and its K_D at that state.

## 7. Arms, masks, seeds, worlds

| Arm | Start | Mutable, factor | Runs | Generations | Role |
|---|---|---|---|---|---|
| **Stage 2 GA** | 32 selectors from the GA distribution | the 13 selector parameters, 1× | 8 (0-7) | 300 | registered |
| **Random sampling** | — | — | 8, paired with the GA's | 9 600 draws | registered |
| Stage 3 | 32 copies of run i's Stage 2 champion | the 11 neurons' existing edges, τ and biases, except the relays' τ and bias, 0.25× | 8 | 500 | descriptive |
| B-task | 32 draws from B-task's distribution | its 171 parameters, 1× | 8 | 800 | descriptive |

**Checkpoints:** every arm runs `evolve_batch` with selection and validation at the world seed
1 171 000.
- Validation runs every 25 generations (`checkpoint_every` 25), from generation 0 to the last.
- Checkpoints describe the trajectory. They never choose a champion: `RunRecord.champion_index` is not
  used.

**The selector's 13 parameters:**
- τ_q, w_qq and b_q;
- w_aq (RA → Q) and w_bq (RB → Q);
- the four gate edges;
- the four comparator biases.

**The GA distribution:**
- for each module, one gate weight from U[−0.5, 0.5], given to both of its comparators, and one bias
  from N(0, 0.5²) clipped to ±2, given to both;
- w_qq, w_aq and w_bq from U[−0.5, 0.5];
- b_q from N(0, 0.5²), clipped;
- τ_q log-uniform over [0.5, 20].

The tie is in the draw only: mutation is untied.

**Random sampling's distribution:** the same tie, with:
- the gate weights, w_qq, w_aq and w_bq from U[−3, 3];
- the comparator biases and b_q from U[−2, 2];
- τ_q log-uniform over [0.5, 20].

That is 9 independent coordinates.

**Random sampling's search:**
- Draw j (0-9 599) of run i is scored on the GA run i's selection worlds of generation ⌊j / 32⌋:
  `train_ids(1 170 000 + i, ⌊j / 32⌋, 16, 944 000 000, 500 000)` at the world seed 1 171 000.
- The top 32 by that score (ties to the lower j) go to validation; the champion's ties also go to the
  lower j.

**B-task's 11 neurons** keep E's names and routing; its genome has all 121 edges among them plus 32
output edges.
- **What mutates:** all 153 edges, and the τ and bias of the 9 non-relay neurons. There are no gap
  junctions.
- **Its draws:**
  - **each nose pair:**
    - one τ, log-uniform over [0.5, 20], and one bias, N(0, 0.5²) clipped to ±2;
    - each edge into it from another neuron, one value given to both noses;
    - NL → NL = NR → NR, and NL → NR = NR → NL;
  - **each comparator pair:** one τ and one bias, drawn as for the noses;
    - its own module's nose edges in L1's pattern, with one magnitude a ~ U[−0.5, 0.5] (left nose →
      CL +a, → CR −a; right nose → CR +a, → CL −a);
    - from every other neuron, one value for both comparators;
    - CL → CL = CR → CR, and CL → CR = CR → CL;
  - **each comparator pair's outputs:** one value per turn neuron, from U[−0.5, 0.5], with opposite
    signs for CL and CR;
  - **E3_Q:** its τ log-uniform over [0.5, 20], its bias N(0, 0.5²) clipped to ±2;
  - **every other edge:** U[−0.5, 0.5].
- **The result:** generation 0 adds no turn at zero nose difference, and each module senses with gain
  a.

**Generation 0's limits** (from the design):
- The balance holds at generation 0 only: untied 1× mutation unbalances most children from generation
  1.
- The GA distribution is not expected to contain a working selector. Its q is monostable (|w_qq| ≤
  0.5), and its gate moves a comparator by about 1 at most. That is an expectation, not a claim; S2-c
  measures it.

**Seeds** (numpy `default_rng`; torch generators as `evolve_batch` takes them):

| Use | Seed |
|---|---|
| Stage 2 GA run i | run seed 1 170 000 + i |
| its initial draws | 1 172 000 + i |
| random sampling run i's draws | 1 173 000 + i |
| the GA-distribution census | 1 174 000 |
| the random-sampling-distribution census | 1 174 001 |
| B-task run i | run seed 1 177 000 + i; initial draws 1 175 000 + i |
| Stage 3 run i | run seed 1 176 000 + i |
| every evaluation | world seed 1 171 000 |

**World ids,** new blocks, disjoint from every earlier range (a test checks):

| Use | Ids |
|---|---|
| selection | base 944 000 000, span 500 000 (`train_ids`); 16 worlds per genome per generation |
| validation | 945 000 000-945 000 255 |
| test | 946 000 000-946 000 255 |
| the censuses' scoring | 947 000 000-947 000 015 |
| assays | 947 100 000-947 100 255 |
| G0 and G1 | 947 200 000-947 201 023 |
| calibration | 948 000 000-948 000 255 |

**The test worlds are read only in stage 14,** after every champion is frozen.

**End-of-run assertions:**
- in Stage 2, every non-selector parameter is bit-identical to E's;
- in Stage 3, the relays' τ and bias, the 302 worm neurons and the carrier's biases are unchanged;
- in every arm, the mask is unchanged.

A failure makes that batch "not read".

## 8. Outcomes

**The champions:** in each arm, every final-population member (for random sampling, its top 32) is
validated on the 256 validation worlds. The best validation mean is the champion, ties to the lower
index (for random sampling, the lower j).
- The runner implements this rule itself; `evolve_batch`'s checkpoint champion is not used.
- Stage 2's and random sampling's champions are frozen before Stage 3 starts. Stage 3 run i starts
  from run i's Stage 2 champion, working or not.

**Incomplete runs:**
- a run whose batch stopped finally, or whose measures did not complete, is "not read";
- S2-a then reads "k of n read";
- S2-b uses the complete pairs, and is descriptive below 8;
- if batch 1 or 2 stopped finally, S2-b is not read.

**S2-a (registered):** the number of Stage 2 runs, of 8, whose champion is a working selector, with
each champion's memory class.
- **8 or 7:** "evolution found a working selector in k of 8 runs".
- **1-6:** "evolution found a working selector in k of 8 runs, not reliably".
- **0:** "no working selector was found in 300 generations at 02's sigmas, with untied mutation at
  1×, from this initial distribution". Never "cannot evolve".

**S2-b (registered):** the GA's champions against random sampling's.
- **The estimand:** the mean over the 8 pairs (by i) of the difference in test-world means.
- **The interval:** `_boot_means`, 90%.
- **The rules, in order:**
  1. **"Neither found a working selector,"** if no champion in either arm is working;
  2. **"Evolution better,"** if the lower bound exceeds 0.5 visits;
  3. **"Random sampling better,"** if the upper bound is below −0.5;
  4. **"As good,"** if the interval lies within ±0.5;
  5. **"Unclear."**
- **The fixed wording** of rules 2-4 names what is compared: "evolution from a start near the ungated
  pair, with untied mutation, against a blind search over the whole range with the comparator pairs
  permanently tied". It does not isolate the search algorithm.
- **With 4 pairs** (reduction step 5), S2-b is descriptive.

**S2-c (registered, descriptive in force):** each census's count of working selectors, of 1 024, with
its Clopper-Pearson 95% interval, or "at least k" under the cap on qualifiers (§5).
- **The screen:** the qualifiers are the selectors scoring at least 0.8 of E's mean on the 16 census
  worlds.
- **The full check:** only the qualifiers get it (calibration, then the test worlds, after the
  champions are frozen).
- **The estimand is the probability of passing the screen and the full check,** not of being a
  working selector. The screen's false negatives are not checked (Astra).
- **If the GA distribution's count is at least 10,** the wording adds: "Stage 2 is answered at
  generation 0".
- **A zero** reads "none of 1 024 draws passed the screen and the full check; that rate is below [the
  upper bound]", never "the distribution holds none".

**Stage 3 (descriptive):**
- each run's champion against its Stage 2 champion, with S2-b's estimand, interval and ordered
  outcomes, and the wording "joint tuning";
- each module's skill (single-source navigation with q clamped) at the checkpoints and endpoints;
- each champion's memory class.

**B-task (descriptive):** its champions against Stage 3's, by S2-b's estimand and interval and its
rules 2-5. There is no "working" branch: B-task has no memory assays, so this is a comparison of
performance only.
- Under reduction step 1, they are compared against Stage 2's instead.
- **The wording** names the match: "the same neurons, inputs and outputs, not the same trainable
  capacity".
- B-task starts with weak sensing (gain a) and no latch structure.

**The engineered organism, reported:**
- its test-world mean;
- its no-latch and one-module contrasts;
- its mean-nose probes;
- its component and memory results;
- B-shared's, beside it.

**Missing measures:** a measurement that did not complete makes every outcome that needs it "not
read" for that run, and the run is named.

## 9. The cap, admission and reductions

**The cap:** 30 GPU-hours for E3a, counted through `wormwars.accounting`, every stage included.

**After the projection,** the planned total is the projection's estimate of every stage, × 1.25.
- **If it exceeds 30,** reductions are applied in this order until it fits:
  1. B-task, to 300 generations;
  2. B-task, dropped;
  3. Stage 3, to runs 0-3;
  4. Stage 3, dropped;
  5. random sampling, to runs 0-3.
- **If the minimum still exceeds 30,** E3a does not start, and the owner is asked. The minimum is the
  gates, calibration, the censuses, Stage 2's 8 runs, random sampling's 4, their validation, and
  their evaluation.
- The reductions are recorded before any training.

**Admission:**
- Each training batch is admitted, in order, if the hours spent, plus its projected time, plus the
  projected time of every remaining non-training stage × 1.25, are within 28 h (a 2 h general
  reserve). The × 1.25 applies to the remaining non-training stages alone.
- Once one is refused, no later batch starts.
- Evaluation is admitted if the hours spent plus its projected time are within 30.

## 10. Budget

The rate is E4s-1's measured batches: 1.35-1.43 h for 8 runs × 32 × 8 worlds × 300 ticks × 1 000
generations. It is scaled linearly; the projection replaces it.

| Part | Estimate |
|---|---|
| Projection, G-E, G0, G1, calibration | 1.0 h |
| Censuses (2 × 1 024 × 16 worlds × 600 ticks) | 0.2 h |
| Stage 2 (8 × 32 × 16 worlds × 600 ticks × 300 generations) | 1.7 h |
| Random sampling (the same evaluations) | 1.7 h |
| Stage 3 (500 generations) | 2.8 h |
| B-task (800 generations) | 4.5 h |
| Final-population validation and test-world evaluation | 1.5 h |
| **Total** | **about 13.4 h** |

## 11. Tests before the formal run (each seen failing first; sabotage where a check could not fail)

1. The shuttle's events:
   - entries, re-arming and confirmed visits;
   - the goal switching before tick t + 1;
   - the cue kept out of the ledger;
   - levels sensed at t + 1.
2. The geometry rule, with joint redraws, against the script's acceptance.
3. Routing: the six signals reach only their neurons, at their gains.
4. Dtypes: known non-zero values written through every saved array and read back.
5. The generalised graft: several modules, non-food noses, and E4s-1's L1 genome rebuilt
   bit-identical.
6. The clamp of a named neuron to a value, and the one-time write.
7. **The latch in `Brain.step`:**
   - a one-tick level leaves q at ∓0.2197 (±0.001) and it settles at ∓1.91501;
   - the cue gives 4.937 at tick 4;
   - with no input it holds for 600 ticks.
8. **The probe:** q, RA and RB held, and the state under test unchanged by the probe.
9. **E's component tests,** each with a sabotage: the gate edge at 0 must fail the inactive limit.
10. **The fixed-point finder:**
    - E's two stable roots;
    - Astra's near-fold case (w_qq 2, b_q 0.5328398943);
    - an exact grid zero;
    - a tangency.
11. **The memory assays on constructed organisms:** a latch, a bistable q that the stimulus cannot
    switch, a slow monostable trace, and a q with no memory, each landing in its class.
12. **The samplers:**
    - the GA, random-sampling and B-task distributions;
    - the ties at generation 0, with zero added turn at zero nose difference;
    - the seeds.
13. **The mutation factors and the end-of-run assertions,** for every arm.
14. **On synthetic inputs:** S2-a's, S2-b's and S2-c's rules, with every outcome reached.
15. The world ranges, against every earlier block.
16. **The stage dependencies:**
    - Stage 3 refuses to start without frozen Stage 2 champions;
    - calibration refuses champions not yet frozen;
    - the test worlds are refused before stage 14.
17. **Admission, refusal and the reductions,** on synthetic projections.
18. **Missing outcomes:** "not read" runs, "k of n read", and S2-b below 8 pairs.
19. **The census screen:** the estimand's bookkeeping, with a false negative constructed.
20. **The fixed-point finder on Astra's missed-root case** (w_qq 1.0119999647, b_q 0.0008732175),
    which the grid misses.
21. **B-task's draws:** the nose pairs' and comparator pairs' full within-pair blocks, with zero added
    turn at zero nose difference.
22. **The champion rule:** final-population validation, the tie-breaks, and `champion_index` unused.
23. A smoke of every stage.

## 12. Departures from design v2.4

- **S-shuttle's second gain is 8192, not 256.** The design said "k = 256 (E1's best)", which was
  wrong: E1's best S-const was k 8192, speed 1, turn 0, and its best with k ≤ 32 was k 32, speed 1,
  turn 0.2 (`freeze.json`, "tuned").
- **S-oracle's gate is 0.6 of a geometric maximum** that includes a half-turn per reversal. The design
  had 0.8 of a maximum it did not define. A maximum without turning would put the oracle below 0.8
  for kinematic reasons alone.
- **B-task's nose edges are drawn in L1's pattern** with one magnitude per module, so it starts with
  weak sensing rather than blind (both reviewers noted the blind start).
- **D is taken over legs after the first confirmed visit,** the legs that need memory.
- **The reset is timed from the level's end:** 10 ticks after `at_a` returns to 0, not 10 ticks after
  the visit (Fable).
- **The fixed points are bracketed by f's stationary points.** The design's grid could miss a pair of
  roots (Astra).
- **E's release test reports and does not gate:** it needs D, which comes after G1.
- **The blind controls use E1's tuned parameters.**
- **The world seed for evaluation (1 171 000) and the per-use seeds** are new, as are the block spans.

## 13. Amendments

None.
