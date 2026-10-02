# E3a pre-registration: the shuttle, a two-module organism with a latch

Status: **first draft, for review**, 2026-10-02.
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
  - a persistent random walk (speed 1, rate 1, persistence 0.5);
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
- It passes the component tests of §6 with "module" read as "nose pair".

## 5. The stages, in order (each writes a record committed and pushed before the next starts)

1. **Projection** (timings only; smoke ids 0-9 999, seed base 1 179 000);
2. **G-E, the engine check;**
3. **G0, Stage 0's gate;**
4. **G1, Stage 1's gate** with the memory assays, then calibration;
5. **The censuses;**
6. **Training batches,** each its own stage:
   1. Stage 2 GA, runs 0-7;
   2. random sampling, runs 0-7;
   3. Stage 3, runs 0-7;
   4. B-task, runs 0-7;
7. **Final-population validation and champion choice;**
8. **Evaluation on the test worlds,** with the classes and the census qualifiers' full check.

**G-E, the engine check** (rule 7). The previous engine is the commit before E3a's code.
- **On the GPU:** E2's formal GA batch for generations 0-25, with every generation's best-genome hash
  equal to `experiments/E2-optimizer-screen/train-ga.json`. This is `scripts/e4s_equivalence.py`'s
  check, rerun.
- **On the CPU:** Task N and foraging, 300 ticks on smoke ids 0-15 (run seed 1 179 500):
  - every per-tick state, event and score identical between the two engines;
  - E4s-1's grafted L1 genome rebuilt by the generalised `graft.py` bit-identical to the old build.
- **The test:** all identical. A failure stops E3a until the code is fixed, and G-E is rerun.

**G0, Stage 0's gate** (gate worlds, 1 024; one padded strain per controller):
- S-oracle's mean is at least 0.6 of the mean geometric maximum. Per world, that maximum is the number
  of legs an ideal mover completes in 600 ticks:
  - the first leg takes (|A − spawn| − R) / 0.35 ticks;
  - each later leg takes (|A − B| − 2R) / 0.35 + π / 0.30 ticks: a straight run at full speed, plus a
    half-turn at the full turn rate.
- S-shuttle at k 8192 reaches at least 0.5 of S-oracle's mean.
- L1-switch's lower bound is at least 0.5 of S-shuttle's mean at k 32.
- Every blind control's mean is at most 0.25 of L1-switch's mean, and its 90th-percentile world at
  most 0.5 of it.

**G1, Stage 1's gate** (the same gate worlds):
- E's lower bound is at least 0.8 of L1-switch's mean;
- `classify`(E against no-latch, E against one-module) gives "uses";
- E passes every component test (§6);
- E passes every memory assay (§6): the clamp assays, settable, the hold and the reset.

**Calibration** (after G1 passes; calibration worlds), for each organism the assays need:
- **D:** E's median leg duration over completed legs after the first confirmed visit, rounded to the
  nearest tick (half up). Legs cut off by the episode's end are excluded.
- **Each champion's stimulus duration:** the median, pooled over A and B, of the number of
  consecutive ticks of its visited source's level starting at each confirmed entry.
  - Rounded half up, at least 1.
  - Levels cut off by the episode's end are excluded.
  - It is 2 for E and every control; 2 is also the fallback for a champion without a confirmed
    visit.
- **Each monostable champion's median q** in each goal phase.

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

**The component tests** (E, B-shared, the controls where stated):

| Test | Requirement |
|---|---|
| the active module's K_D, at m in {0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.35}, from each stable state | at least 30 |
| the inactive module's | \|K_D\| at most 0.3 at every m |
| the inactive module's offset: \|u\| with it, minus \|u\| with its 16 output edges at 0, at d = 0 | below 0.02 at every m |
| switching and recovery: after a two-tick level for the other goal, the newly active module's K_D, probed each tick | reaches 90% of its settled value within 10 ticks of the level's end |
| startup: from tick 0 with the cue, A's K_D probed at ticks 5-15 | at least 30 from tick 10 |

**The memory assays** (§1-§4's organisms, and every Stage 2 and Stage 3 champion):
- **The states:**
  - for a bistable q, its two stable fixed points;
  - for a monostable q, its calibration medians per goal phase.
  - "The separation" s is the distance between the two states. A tolerance of 10% means within
    0.1·s.
- **The stimulus for goal X:** the level of the other source (`at_b` for goal A, `at_a` for goal B),
  for the organism's stimulus duration.
- **The window:** W = max(20, 10·τ_q) ticks, read at its end.
- **The clamp assays:**
  - assay worlds, 600 ticks, with q clamped to each state in turn;
  - each passes if the first entry is into that state's goal in at least 90% of the worlds;
  - a world with no entry is a failure;
  - they are not applicable if s < 0.1, or if a goal phase never occurs on the calibration worlds.
- **Settable** (bistable only): from each stable state, the stimulus for the other goal leaves q
  within 10% of the other state at the end of W.
- **The hold** (bistable only): from each stable state, set by its stimulus, wait W, then run 580
  ticks with no levels. It passes, for both states, if:
  - q at the end is within 10% of its fixed point;
  - the active module's K_D is at least 15, and at least 0.8 of its value at the fixed point;
  - the inactive |K_D| is at most 0.1 of the active one.
- **The release test:** from q's computed equilibrium (each stable one, for a bistable q), the
  stimulus for goal X, then D ticks with no levels. It passes, for both goals, if X's module has a
  K_D of at least 15, and the other's |K_D| is at most 0.1 of it.
- **The reset** (E, in G1): a one-time write of q to E's "go to A" state, 10 ticks after the first
  confirmed visit. It passes if, in at least 70% of the assay worlds with a first confirmed visit by
  tick 500, the next entry is into A and a confirmed visit to B follows.
- **The fixed points** of f(q) = −q + w_qq·tanh q + b_q, with the relays at rest:
  - found on a grid of 100 001 points over |q| ≤ |w_qq| + |b_q| + 1, counting exact zeros and sign
    changes, each refined by bisection to 1e-9;
  - a root is stable if f′(q) = −1 + w_qq·sech²q < −1e-6;
  - **bistable** means two stable roots at least 0.1 apart; otherwise the structure is monostable.

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

**A working selector:** a champion is working if both hold:
- its test-world lower bound is at least 0.8 of E's test-world mean;
- both of its clamp assays pass.

A champion with mirrored polarity can be working.

**Also measured, on the test worlds** (descriptive):
- each module's mean-nose probe: the score with that module's two noses fed their mean;
- per-tick turn contributions;
- generation 0's turn offsets and K_D, and each logged generation's offsets.

## 7. Arms, masks, seeds, worlds

| Arm | Start | Mutable, factor | Runs | Generations | Role |
|---|---|---|---|---|---|
| **Stage 2 GA** | 32 selectors from the GA distribution | the 13 selector parameters, 1× | 8 (0-7) | 300 | registered |
| **Random sampling** | — | — | 8, paired with the GA's | 9 600 draws | registered |
| Stage 3 | 32 copies of run i's Stage 2 champion | the 11 neurons' existing edges, τ and biases, except the relays' τ and bias, 0.25× | 8 | 500 | descriptive |
| B-task | 32 draws from B-task's distribution | its 171 parameters, 1× | 8 | 800 | descriptive |

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
- Draw j (0-9 599) of run i is scored on the GA run i's selection worlds of generation ⌊j / 32⌋.
- The top 32 by that score (ties to the lower j) go to final-population validation.

**B-task's 11 neurons** keep E's names and routing; its genome has all 121 edges among them plus 32
output edges.
- **What mutates:** all 153 edges, and the τ and bias of the 9 non-relay neurons. There are no gap
  junctions.
- **Its draws:**
  - **each nose pair:** one τ (log-uniform) and one bias (N(0, 0.5²), clipped), and each edge into
    it from another neuron one value given to both noses;
  - **each comparator pair:** one τ and one bias as for the noses;
    - its own module's nose edges in L1's pattern, with one magnitude a ~ U[−0.5, 0.5] (left nose →
      CL +a, → CR −a; right nose → CR +a, → CL −a);
    - from every other neuron, one value for both comparators;
    - CL → CL = CR → CR, and CL → CR = CR → CL;
  - **each comparator pair's outputs:** one value per turn neuron, from U[−0.5, 0.5], with opposite
    signs for CL and CR;
  - **E3_Q:** its τ log-uniform, its bias N(0, 0.5²), clipped;
  - **every other edge:** U[−0.5, 0.5].
- **The result:** generation 0 adds no turn at zero nose difference, and each module senses with gain
  a.

**Generation 0's limits** (from the design):
- The balance holds at generation 0 only: untied 1× mutation unbalances most children from generation
  1.
- The GA distribution contains no working selector: q is monostable, and the gate moves a comparator
  by about 1 at most.

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

**The test worlds are read only in stage 8,** after every champion is frozen.

**End-of-run assertions:**
- in Stage 2, every non-selector parameter is bit-identical to E's;
- in Stage 3, the relays' τ and bias, the 302 worm neurons and the carrier's biases are unchanged;
- in every arm, the mask is unchanged.

A failure makes that batch "not read".

## 8. Outcomes

**The champions:** in each arm, every final population member (for random sampling, its top 32) is
validated on the 256 validation worlds. The best validation mean is the champion, ties to the lower
index.

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
its Clopper-Pearson 95% interval.
- The qualifiers are the selectors scoring at least 0.8 of E's mean on the census worlds. Only they
  get the full check on the test worlds, after the champions are frozen.
- **If the GA distribution's count is at least 10,** the wording adds: "Stage 2 is answered at
  generation 0".
- **A zero** reads "none found in 1 024 draws; the hit rate is below [the upper bound]", never "the
  distribution holds none".

**Stage 3 (descriptive):**
- each run's champion against its Stage 2 champion, with S2-b's estimand, interval and ordered
  outcomes, and the wording "joint tuning";
- each module's skill (single-source navigation with q clamped) at the checkpoints and endpoints;
- each champion's memory class.

**B-task (descriptive):** its champions against Stage 3's, by S2-b's procedure.
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
- **If the minimum** (the gates, the censuses, Stage 2's 8 runs and random sampling's 4) still
  exceeds 30, E3a does not start, and the owner is asked.
- The reductions are recorded before any training.

**Admission:**
- Each training batch is admitted, in order, if the hours spent, plus its projected time, plus the
  projected evaluation × 1.25, are within 28 h (a 2 h general reserve).
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
16. A smoke of every stage.

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
- **The blind controls use E1's tuned parameters.**
- **The world seed for evaluation (1 171 000) and the per-use seeds** are new, as are the block spans.

## 13. Amendments

None.
