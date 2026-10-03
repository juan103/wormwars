# E3b-1 pre-registration: the E3 gate in mazes

Status: **draft 2, 2026-10-03, for both reviewers.** Nothing of E3b-1 has run.
- **Draft 1** (95800aa): Fable said "bind after fixes"; Astra said "revise"
  (`docs/reviews/20261003-E3b-1-prereg/`; D184). Draft 2 takes every fix; §14 maps them.
- **Its design:** `docs/E3/E3b-1-DESIGN.md` v2, confirmed by both reviewers (D183). The pins in its "v2, as
  confirmed" are carried here. §12 lists the departures.
- **Binding:** it binds when committed and pushed after both reviewers agree, before any stage of E3b-1 runs
  (rule 2). From then on the text is never changed; amendments go in §13, dated.
- **The cap:** 24 GPU-hours (§9), within the owner's ceiling of about 30 for all of E3b, of which E3b-0 used
  2.62 (D159, D181).
- **The numbers below that come from a run** are E3b-0's (published, D180) and the gate's power simulation
  (CPU; `power.json`).

## 1. The question and its frame

**The gate:** does joint tuning of the maze-ready seed E + W2 improve the colony's shuttling in 5 × 5 tree
mazes with shared trails, against the frozen seed, on untouched mazes, under identical mechanics?

**The secondary questions:** does more training help (300 against 125 generations)? Does tuning raise trail
dependence? Do the tuned colonies' peers still speed later discoverers?

**The frame, stated in every claim:**
- Stereo sensing and the maze-ready additions are game-design choices.
- The organism is a hand-built circuit on a silent worm, outside the N2 mask. Nothing here is about worm
  behaviour.
- The claim is about tuning under the two schedules run, as an average, from this seed, with this GA, at
  this affordable effort. A null result is not a claim about evolution in general.
- No claim is made that weys follow a trail's direction: behavioural polarity was not shown in E3b-0.

## 2. Fixed inputs

Each is checked by sha256 at load (LF line endings, as committed):

| File | sha256 |
|---|---|
| `experiments/E4s-stereo-module/E4s-0/module.json` (L1) | `9613cd155a20ed2cfb891c1bd10fed16814f24a04f912a1940524f2378e877d4` |
| `experiments/E3-ab-organism/E3b-0/stage-b3.json` (the trail constants) | `a54003cfbdf4a00e4e4ff72203258211877d62d96c2f431e458ab14401e600e9` |
| `experiments/E3-ab-organism/E3b-0/stage-c.json` (the seed and variant) | `c3861dec78d8015902aff233f63cac331dd4594fe651c79c15f04d64dd6a082b` |
| `experiments/E3-ab-organism/E3b-0/report.json` (criterion 4's levels) | `af82e1c9573b0f2b73d228d065c277f9bb46310f2fd8d395439a557e359d7df8` |
| `experiments/E3-ab-organism/E3b-0/timing.json` | `c4cb4df44a6bdcf81b6f506103d2fe40f4d8991a1d97cb8dc8df9849921c7afd` |
| `experiments/E3-ab-organism/E3b-1/power.json` | `2b4e618e884dc678170e5d7ac8f569c0907609638e5086cd3b6e82df45129145` |
| `experiments/E1-navigation/freeze.json` | `c5c48f83079a6bd0dd48bdeb13d02ab211a08eb64433fdc8372cbd6e74bcaae9` |
| `experiments/E1-navigation/gate.json` | `a18b5a53845360107448527b2af038b9c613e4bf11fdfe843c328b7c2a01afa0` |
| `experiments/E2-optimizer-screen/train-ga.json` (G-E's reference) | `88a3ed88de2f89042970c11fc8e4de49b8432e533a2e9e802de3e1333e538d7c` |

**The task:** E1's Task N configuration, checked against E1's gate, turned into the maze shuttle by
`maze_config`:
- c = 5 (a 21 × 21 grid), H = 2 400 ticks, a colony of 8 weys on up to 4 spawns;
- shared trails with μ 0.01, λ 0.02, δ 0.05, d₀ 1.142;
- scents with σ 3 path cells, zero beyond 9;
- sliding on, crowding off, and the 5-tick start cue;
- 32 substeps, `pad_single_strain` on;
- the maze run seed is 1 180 000 throughout;
- every evaluation is at episode 0, except the replay donors (§6).

**The seed:** E3a's engineered E plus W2, on the silent carrier: `maze_organisms.maze_organism(seed("E"),
"W2")`, with the carrier's resting turn set so that the resting turn command is +0.4 (D176).

**The degraded start (arm R):** E's no-latch variant (`organism.no_latch`: the gate weights and the
comparator biases at 0, on E's mask) plus W2, built the same way.

**The GA** is `evolve_batch`, as in E3a's Stage 3:
- population 32, elites 3, truncation 8, unshaped fitness (confirmed visits), `p_mutate` 1;
- 02's sigmas (w 0.08, log-τ 0.15, bias 0.05), × 0.25 on the mutable parameters and × 0 on the frozen
  ones.

**The statistics:** `scipy.stats` for the t-tests; the exact sign-flip test over 2^n patterns; Holm's
correction.

## 3. The arms, masks and seeds

G_X is arm X's number of generations, run as indices 0 to G_X − 1.

| Arm | Runs | G | Mazes per genome per generation | Access, in training and in validation | Start | Run seeds |
|---|---|---|---|---|---|---|
| T-A | 8 | 125 | 16 | shared | the seed | 1 190 000 + i |
| T-F | 8 | 300, with a read at index 124 | 8 | shared | the seed | 1 190 100 + i |
| N | 6 | 125 | 16 | none | the seed | 1 190 200 + i |
| R | 2 | 125 | 16 | shared | the degraded start | 1 190 300 + i |

**The mutable set:** every chemical edge with a grafted end, and every grafted neuron's τ and bias, except:
- the relays E3_RA and E3_RB: their τ and bias are frozen, as in E3a's Stage 3;
- W2's two neurons (E3B_WL, E3B_WR): their τ and bias are frozen, and so are their 16 output edges. Their
  inputs come through the interface, not through graft edges;
- the carrier, so the worm block stays silent.

An end-of-run assertion checks that every frozen parameter is bitwise equal to the start organism's.

**The initial population** is 32 copies of the start organism.

**Training mazes:** `train_ids(run seed, generation, n, base 10 000 000, span 10 000 000)`. Every genome of
a generation plays the same mazes, at episode 0.

**"None" access** is the tested equivalent of deposit-off (§11): every wey senses no trail, while trails are
still laid.

## 4. The maze blocks

All are at maze run seed 1 180 000, disjoint from each other and from E3b-0's blocks (0-255, 1 000-1 255,
2 000-2 255, and the smoke block 9 000 and up). A test checks this.

| Use | Maze ids |
|---|---|
| Training | 10 000 000 to 19 999 999 |
| Champion validation | 4 000-4 127 (128) |
| The learning curve | 4 500-4 627 (128) |
| Replay calibration | 5 000-5 255 (256) |
| Test | 6 000-6 255 (256), opened only in the evaluation stage |

## 5. The stages, in order

Each writes a record that is committed and pushed before the next starts.

1. **`project`:** the benchmark (§9).
2. **`g-e`, the engine check** (rule 7). It must pass before any training stage starts (§10).
   - **On the GPU:** E2's formal GA batch, generations 0-25, with every generation's best-genome hash
     equal to `train-ga.json` (E4s's check, rerun). The stage fails on any mismatch. This leg was owed
     since E3b-0.
   - **On the CPU:** `scripts/e3_equivalence.py` against its 84ff98a reference, with every case identical.
   - **The snapshot hook:** `evolve_batch` with the new snapshot hook switched off leaves E2's CPU smoke
     batch bit-identical.
3. **`train-ta`:** T-A's 8 runs, as one lockstep batch.
4. **`train-tf`:** T-F's 8 runs, as one batch, with each run's population at index 124 saved.
5. **`train-n`:** N's runs.
6. **`train-r`:** R's runs.
7. **`champions`:** every read point validated, the champions chosen and frozen (§6).
8. **`evaluate`:** the replay pre-passes, the test block in a fixed order of blocks, and the probes (§6).

**Training's checkpoints:** at index 0, every 25 generations, and at the last index, each run's
generation-best genome is scored on the 128 learning-curve mazes, with the arm's training access. That is
the learning curve. It is descriptive, and selects nothing.

**Failures:**
- **A stage stopped by a crash or a kill** is rerun once, unchanged. A second stop is final, and its runs
  are "failed".
- **A training stage stopped by a non-finite score,** which `evolve_batch` raises for the whole lockstep
  batch:
  1. it is rerun once, unchanged;
  2. if that fails again, it is rerun once more without the runs the record names as non-finite, and
     those runs are "failed". The record states the batch's new composition;
  3. if that fails again, the stage is final, and all its runs are "failed".

  No population from a stopped attempt is used.
- **A stage stopped by the cap** is not rerun. Its runs are "not run".
- **Every rerun is admitted under §10 like any stage.**

## 6. Champions and the evaluation

**The read points** (all with index G_X − 1 = the last evaluated generation):
- T-A, N and R: the final population, the 32 genomes evaluated at index 124;
- T-F: the population evaluated at index 124, before that generation's selection and mutation, and the
  final population at index G_F − 1 (299, or 249 under cut 3).

The read at 124 is read-only. Its validation scores do not affect T-F's continuation, and no compute moves
between arms.

**The champion** of a read point is its best genome by mean visits per wey on the 128 validation mazes,
played with the arm's own access (shared for T-A, T-F and R; none for N), at episode 0. Ties go to the lower
population index. `evolve_batch`'s checkpoint champion is not used.

**The evaluation** runs on the test block at episode 0, in this order of blocks. Each block's per-maze
arrays are saved when it completes.

| Block | Organisms and conditions | For |
|---|---|---|
| 1 | the seed, and the final T champions (T-A, and T-F at G_F − 1): shared | G |
| 2 | the same: none | S-trail |
| 3 | the same: own | S-peer |
| 4 | T-F's champions at index 124: shared | S-gen |
| 5 | the same organisms as block 1: peers and scramble; the replay pre-passes on the replay-calibration block; replay | descriptive |
| 6 | the N and R champions, R's degraded start, W2 alone on the carrier, and the scripted follower: shared and none; the oracle and the random walk: none | descriptive and the descriptors |
| 7 | the probes (component tests and latch structure, CPU) | descriptive |

- **The composition:** chunks of 16 organisms × 256 mazes (4 096 worlds), or 8 × 256 with replay donors
  (8 192 worlds). Every record states it.
- **Replay** follows E3b-0's rule: a lockstep donor colony of the same organism at episode + 1 000,
  advanced until A or B differs, playing with shared trails.
  - **Its coefficient** is the organism's own: the ratio of its mean nose exposure to live peers (shared)
    to its exposure to the donor at coefficient 1, from one pre-pass on the replay-calibration block,
    frozen, with no iteration.
  - **If the donor exposure is 0,** replay is "not read" for that organism.

**The measures,** per maze and colony:
- visits per wey (the colony mean), as the primary measure;
- legs per wey;
- the later-leg rate;
- the first-B time of later discoverers (the mean of order statistics 2-8, nonarrivals at H);
- raw entries;
- the share of weys completing at least one round trip (2 legs);
- the unvisited share, the occluded share, and the exposure.

**The probes (block 7, descriptive):**
- **Each champion's latch structure** comes from its own q self-weight and bias (`latch.structure`).
- **If it is bistable:**
  - the component tests at its two stable states, the upper for goal A, at E3b-0's levels (0.001, 0.003,
    0.0398, 0.229, 0.35, 0.891, 1.0, 1.82), against E3b-0's thresholds (K_D ≥ 30 up to 0.35; K_D × level
    ≥ 10.5 up to 1.0);
  - the one-nose checks up to 1.0.
- **If it is monostable:** the structure is reported, and the component tests are not run.
- **E3a's memory assays are not run.** They need a stimulus calibration that maze runs do not record
  (Astra).

## 7. The readings

**d per run.** For a champion c and the seed s, both on the test block with shared trails:
d = (the mean over the 256 mazes of c's visits per wey − the same for s) / s's mean.

**The gate G (registered), on the n_A and n_F read runs of T-A and T-F:**
- **The estimand:** Δ = (mean d over T-A + mean d over T-F at index G_F − 1) / 2.
- **The test:** one-sided Welch.
  - With v_j = s_j² / n_j for each schedule j (s_j the sample SD of its d), the standard error is
    SE = √(v_A + v_F) / 2.
  - The degrees of freedom are ν = (v_A + v_F)² / (v_A² / (n_A − 1) + v_F² / (n_F − 1)).
  - The test is at 5%.
- **The labels:**
  - **"better"** if p ≤ 0.05 for Δ > 0;
  - **"worse"** if p ≤ 0.05 for Δ < 0;
  - **"unclear"** otherwise.
  - **If SE = 0:** "better" if Δ > 0, "worse" if Δ < 0, otherwise "unclear".

  Together the labels allow about 10% under a symmetric null, as intended.
- **The descriptors,** fixed in advance, all under shared trails on the test block:
  - the one-sided 95% lower bound of Δ, Δ − t₀.₉₅,ν × SE;
  - "and at least 10%", if that lower bound is ≥ 0.10;
  - Δ × the seed's mean, in visits per wey, and as a multiple of (seed − W2 alone) and of (follower −
    seed). A multiple whose denominator is ≤ 0 is "not read".
- **The repeated-journey condition.** Per champion, the median over the 256 test mazes of the colony's mean
  legs per wey. If fewer than half of the read champions (rounded up) reach 2, "better" is reported as
  "better, but concentrated".
- **The sensitivity checks** (reported, not deciding):
  - the pooled one-sided t-test on the n_A + n_F differences;
  - the exact sign-flip test over 2^(n_A + n_F) patterns;
  - each schedule's mean d, with its own two-sided 95% t interval.
- **The run-level spread:** √((s_A² + s_F²) / 2), the pooled within-schedule SD of d in units of the
  seed's mean. It is reported against the assumed 0.282 with the uncertainty of Δ against the 10%
  reference (§8). It is not read automatically as "underpowered".
- **Inference is conditional on the 256 test mazes.**

**The secondary tests (registered; Holm's correction over the three at 5%; a test that is not read enters
Holm with p = 1):**
- **S-gen:**
  - the measure, per T-F run: its champion at G_F − 1 against its own champion at index 124, as the paired
    difference in test visits per wey under shared trails, divided by the seed's shared mean;
  - the test: a one-sided paired t-test, with the alternative "G_F − 1 higher".
- **S-trail:**
  - the measure, per T run: e = [(T shared − T none) − (seed shared − seed none)] / the seed's shared mean,
    in visits per wey;
  - the test: G's stratified Welch estimator and test on e, with the alternative "greater".
  - **Reported:** the four means; the decomposition (T shared − seed shared) = (T none − seed none) +
    e × the seed's shared mean; and the same contrast in the later-leg rate, descriptively.
  - **The wording:** a positive result is "increased trail dependence". It can come from a worse "none".
- **S-peer:**
  - the measure, per T run: [T shared − T own, in the first-B time of later discoverers, as means over
    the test block] / the seed's mean first-B time of later discoverers under own;
  - the test: G's stratified estimator and test, with the alternative "less than 0" (shorter is better).
  - The seed's own shared − own on the test block is reported beside it.

**What each reading needs** (otherwise "not read", without affecting the others):

| Reading | Needs |
|---|---|
| G | block 1, with at least 4 read runs in each schedule |
| S-gen | block 4, plus block 1's T-F champions, with at least 4 complete pairs |
| S-trail | blocks 1-2, with at least 4 runs per schedule |
| S-peer | blocks 1 and 3, with at least 4 runs per schedule |
| The descriptive readings | their own blocks |

- A run counts as read for a reading only if its every needed condition covers all 256 mazes.
- The descriptors that need block 6 are "not read" if block 6 is missing.

**Descriptive** (no test):
- S-worlds: T-A against T-F's champions at index 124;
- N against T-A, with trails on and off;
- R's champions against R's degraded start and the seed;
- replay − own and scramble − own for the T champions and the seed, with exposure and route overlap;
- the learning curves;
- the probes (§6);
- each champion's share of qualified nose inputs above 1.0, on the test block with shared trails;
- the training curves' best and mean fitness, and each run's zero share.

## 8. Power (from `power.json`, simulated as G is computed: `scripts/e3b1_power.py`)

4 000 trials per point, with the normal shape and E3a's two-cluster empirical shape (fixed at ddof 0, D183).
Effects are shares of the seed's mean, with 8 runs per schedule.

| Scenario | False positives | Minimum detectable effect at 80% |
|---|---|---|
| Equal effects, CV 0.282 | 4.9-5.2% | 0.19 |
| Equal effects, CV 0.40 | 4.6-4.8% | 0.27 |
| Unequal spreads (0.15 and 0.40) | 4.8-5.3% | 0.21 |
| Schedule means ± 0.10 | 4.5-5.1% | 0.19 |
| Opposite effects averaging zero | 4.4-5.0% | — |

- **The scope of the CV:** the simulation treats 0.282 as the SD of d, in units of the seed's mean, at every
  effect. If instead the CV holds at the tuned mean, the SD of d at Δ 0.19 is about 0.34, and the minimum
  detectable effect is nearer 0.22-0.23. The CV-0.40 row brackets this.
- **The sensitivity checks,** at CV 0.282 with equal effects: the pooled t-test and the sign-flip test keep
  5.0-5.5% false positives. With opposite effects averaging zero they reject 2.9-3.6%.
- **A shifted null at 10%** would need an effect of 0.28-0.31 at CV 0.282 or with unequal spreads, and
  0.36-0.37 at CV 0.40. The 10% is therefore a descriptor, not the test.
- **In visits:** 0.19 of E3b-0's seed mean (5.78) is about 1.1 visits per wey, about E's whole
  contribution over the blind W2 in E3b-0. The gate detects a gain of that size, not a modest refinement,
  and the results will say so.

## 9. The benchmark (`project`)

On smoke ids, with projection seed 1 190 900, it times the second of two repeats of each of these:
- **training:** 2 complete generations of each composition, checkpoint included:
  - T-A at 8 × 32 × 16 (4 096 worlds);
  - T-F at 8 × 32 × 8 (2 048);
  - N at 6 × 32 × 16 (3 072), and at 4 × 32 × 16 under cut 1;
  - R at 2 × 32 × 16 (1 024);
- **validation:** 32 genomes on 128 mazes;
- **the evaluation:** one chunk of 16 × 256 and one of 8 × 256 with replay donors;
- **the probes,** on one organism.

**The projection** is computed from those times, without reserve:
- a training stage: its generations × its time per generation, plus its checkpoints;
- `champions`: the read points × one validation;
- `evaluate`: its chunks, plus its pre-passes, plus the probes.

**The planned total** is the hours spent, plus every training stage's projection × 1.25, plus every other
stage's projection.

## 10. The cap, admission and cuts

**The cap:** 24 GPU-hours for E3b-1, counted through `wormwars.accounting`, every stage included.

**If the planned total after `project` exceeds 24,** the cuts are applied in this order until it fits:
1. N to runs 0-3;
2. R dropped;
3. T-F to G_F = 250, with the read at index 124 kept. Its final read is then index 249, and every
   reading's wording says "250 generations";
4. if it still does not fit, E3b-1 does not start, and the owner is asked.

- This order departs from E3b-0's plan (generations, then worlds, then horizon) because N and R are
  secondary. The gate's arms are cut last.
- The cuts are recorded before any training.

**Admission:**
- No training stage starts unless `g-e` completed and passed.
- **Each training stage is admitted,** in order, if: the hours spent + its projection × 1.25 + the
  projection of every remaining non-training stage ≤ 22 (a 2-hour general reserve).
- Once one is refused, no later training stage starts, and its runs are "not run".
- **`champions` and `evaluate`** are admitted if the hours spent + their projection ≤ 24.
- **A rerun** is admitted by the same formula as its stage.

## 11. Budget

From E3b-0's timing (0.057 s per tick at 4 096 worlds), assumed linear; the benchmark replaces it.

| Part | GPU-hours |
|---|---|
| T-A, T-F, N, R training | 4.71, 5.65, 3.53, 1.18 = 15.07 |
| The learning-curve checkpoints (200 points × 128 mazes) | 0.24 |
| `project`, `g-e` | 0.4 |
| Champion validation (32 read points × 32 × 128) | 1.21 |
| The replay pre-passes | 0.1 |
| The evaluation | 0.5 |
| The probes | under 0.1 |
| **Total** | **about 17.6** |

That is 21.4 with the training × 1.25.

## 12. Tests before the formal run (each seen failing first; sabotage where a check could not fail)

1. **The mutation mask:**
   - every grafted parameter outside the frozen set has factor 0.25;
   - every frozen one has 0: W2's τ, bias and 16 edges; the relays' τ and bias; the worm block;
   - the end-of-run assertion catches a W2 edge changed by hand.
2. **"None" equals deposit-off:** with mutated genomes (not only the seed), trajectories under "none" equal
   those with d₀ = 0, bitwise on the CPU.
3. **The snapshot hook:**
   - it saves the population evaluated at index 124, before breeding;
   - off, it leaves `evolve_batch` bit-identical on E2's CPU smoke.
4. **The failure rules:**
   - a non-finite score in one run stops the batch;
   - the second rerun excludes the named runs;
   - no population from a stopped attempt is used.
5. **The champion rule:** all 32 validated under the arm's access, with ties to the lower index; the
   checkpoint champion unused.
6. **The degraded start:** the gate weights and comparator biases at 0, on E's mask, with W2 as in the
   seed.
7. **The maze blocks:** disjoint from each other and from E3b-0's, at the same maze run seed.
8. **The test block is refused** before the evaluation stage.
9. **The gate's statistic:**
   - against hand computations on synthetic d with unequal schedule spreads and unequal n;
   - every label reached, including at SE = 0;
   - "better, but concentrated" reached;
   - "not read" below 4 runs per schedule.
10. **The secondary tests:** each statistic, denominator and direction on synthetic inputs; Holm with an
    unread test at p = 1.
11. **The readings' needs:** a missing block 5 or 6 leaves G, S-gen, S-trail and S-peer read.
12. **The replay coefficient per organism,** the donors' endpoint rule, and zero donor exposure.
13. **Admission, refusal and the cuts,** on synthetic projections, with cut 3's index 249 carried into
    every reading.
14. **The fixed inputs' hashes** are refused when changed.
15. **A smoke of every stage.**

## 13. Departures from design v2

- **The cap is 24 GPU-hours**, the plan's limit. The design gave only a projection.
- **The run seeds, the projection seed and the training span** are new.
- **The gate and the secondary tests need at least 4 runs per schedule** to be read. A test that is not read
  enters Holm with p = 1, so the family stays three.
- **The replay coefficient** comes from a pre-pass on the replay-calibration block, not on E3b-0's
  selection block, which is spent.
- **E3a's memory assays are replaced** by each champion's latch structure, with the component tests at its
  stable states. The assays need a stimulus calibration that maze runs do not record.

## 14. Amendments

None.

## 15. Changes from draft 1 (the reviews, D184)

| Point (who) | Draft 2 |
|---|---|
| No power section; pin 1 not carried (Fable, Astra) | §8, with the CV's scope and the shifted null's scope |
| The SE hardcoded 8 runs (Astra) | n_A and n_F throughout; ν in full; SE = 0 handled; the repeated-journey threshold as half of the read champions |
| Run against stage failure (Astra) | §5's deterministic rules for crashes and non-finite scores; no population from a stopped attempt |
| "Not read" per reading (Astra) | §7's table of needs; the fixed block order (§6); Holm stays three, with p = 1 for an unread test |
| Cut 3's read point (both) | G_F − 1 throughout; index 249 under cut 3 |
| The admission formula against pin 11 (both) | One formula, with × 1.25 on training only; `g-e` must pass |
| Validation's access (both) | Each arm's own: N under none |
| Implicit denominators (Fable, Astra) | S-gen under shared; S-peer over the seed's first-B under own; the descriptors under shared; zero donor exposure; a denominator ≤ 0 |
| The memory assays were unspecified (Astra) | Latch structure, and component tests at the stable states; the assays are not run |
| The learning curve's count (both) | 200 points, 0.24 GPU-hours |
| Each schedule's interval (Fable) | Two-sided 95% |
| §12's oracle departure was wrong (Astra) | Removed; the replay calibration block added (Fable) |
| The later-leg rate beside S-trail (Fable) | Reported descriptively |
| The benchmark's composition and arithmetic (Astra) | §9 |
