# E3b-1 pre-registration: the E3 gate in mazes

Status: **draft 1, 2026-10-03, for both reviewers.** Nothing of E3b-1 has run.
- **Its design:** `docs/E3/E3b-1-DESIGN.md` v2, confirmed by both reviewers (D183). The pins listed in its
  "v2, as confirmed" are carried here. §12 lists the departures.
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
| `experiments/E3-ab-organism/E3b-0/report.json` (criterion 4's levels, the replay rule's precedent) | `af82e1c9573b0f2b73d228d065c277f9bb46310f2fd8d395439a557e359d7df8` |
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
- the maze run seed is 1 180 000 throughout.

**The seed:** E3a's engineered E plus W2, on the silent carrier: `maze_organisms.maze_organism(seed("E"),
"W2")`, with the carrier's resting turn set so that the resting turn command is +0.4 (D176).

**The degraded start (arm R):** E's no-latch variant plus W2, on E's mask: the gate weights and the
comparator biases at 0.

**The GA** is `evolve_batch`, as in E3a's Stage 3:
- population 32, elites 3, truncation 8, unshaped fitness (confirmed visits), `p_mutate` 1;
- 02's sigmas (w 0.08, log-τ 0.15, bias 0.05), × 0.25 on the mutable parameters and × 0 on the frozen
  ones.

**The statistics:** `scipy.stats` for the t-tests; the exact sign-flip test over 2^16 patterns, as in
`scripts/e3b1_power.py`; Holm's correction.

## 3. The arms, masks and seeds

| Arm | Runs | Generations (index 0 to G − 1) | Mazes per genome per generation | Access | Start | Run seeds |
|---|---|---|---|---|---|---|
| T-A | 8 | 125 | 16 | shared | the seed | 1 190 000 + i |
| T-F | 8 | 300, with a read at index 124 | 8 | shared | the seed | 1 190 100 + i |
| N | 6 | 125 | 16 | none | the seed | 1 190 200 + i |
| R | 2 | 125 | 16 | shared | the degraded start | 1 190 300 + i |

**The mutable set:** every chemical edge with a grafted end, and every grafted neuron's τ and bias, except:
- the relays E3_RA and E3_RB: their τ and bias are frozen, as in E3a's Stage 3;
- W2's two neurons (E3B_WL, E3B_WR): their τ and bias are frozen, and so are their 16 output edges;
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

1. **`project`:** the benchmark. On smoke ids, with projection seed 1 190 900, it times:
   - 2 complete generations of each training composition: T-A at 8 × 32 × 16, T-F at 8 × 32 × 8, N at
     6 × 32 × 16, R at 2 × 32 × 16;
   - one validation of 32 genomes on 128 mazes;
   - one chunk of the evaluation at its composition, with replay donors.

   It records the projection and any cuts (§9). Timings only.
2. **`g-e`, the engine check** (rule 7):
   - **on the GPU:** E2's formal GA batch, generations 0-25, with every generation's best-genome hash equal
     to `train-ga.json` (`scripts/e4s_equivalence.py`'s check, rerun). This leg was owed since E3b-0;
   - **on the CPU:** `scripts/e3_equivalence.py` against its 84ff98a reference: every case identical;
   - **`evolve_batch`'s new snapshot hook,** off by default, leaves E2's batch bit-identical.
3. **`train-ta`:** T-A's 8 runs.
4. **`train-tf`:** T-F's 8 runs, with the population at generation index 124 saved.
5. **`train-n`:** N's 6 runs.
6. **`train-r`:** R's 2 runs.
7. **`champions`:** every read point validated, the champions chosen and frozen (§6).
8. **`evaluate`:** the replay pre-passes, then the test block (§6, §7).

**Training's checkpoints:** every 25 generations and at the last index, the generation's best genome is
scored on the 128 learning-curve mazes (`evolve_batch`'s checkpoints). That is the learning curve. It is
descriptive, and selects nothing.

**Reruns:** a stage that stopped (a crash, a kill, a non-finite score) may be rerun once, with unchanged
seeds and inputs; a stopped rerun is final. A stage stopped by the cap is not rerun.

**A run that is non-finite twice** is reported as failed. The readings use the remaining runs, and say so.

## 6. Champions and the evaluation

**The read points:**
- T-A, N and R: the final population, the 32 genomes evaluated at index 124;
- T-F: the population evaluated at index 124, before that generation's selection and mutation, and the
  final population at index 299.

The read at 124 is read-only. Its validation scores do not affect T-F's continuation, and no compute moves
between arms.

**The champion** of a read point is its best genome by mean visits per wey on the 128 validation mazes,
with ties going to the lower population index. `evolve_batch`'s checkpoint champion is not used.

**The evaluation, on the test block,** at episode 0:

| Organism | Conditions |
|---|---|
| The 16 final T champions (T-A, and T-F at index 299) | shared, none, own, peers, scramble, replay |
| T-F's 8 champions at index 124 | shared, none |
| The 6 N champions | shared, none |
| The 2 R champions | shared, none |
| The seed E + W2 | shared, none, own, peers, scramble, replay |
| R's degraded start | shared, none |
| W2 alone, on the carrier | shared, none |
| The scripted follower | shared, none |
| The oracle and the random walk | none |

- **Replay** follows E3b-0's rule: a lockstep donor colony of the same organism at episode + 1 000,
  advanced until A or B differs, playing with shared trails.
- **Its coefficient** is the organism's own: the ratio of its mean nose exposure to live peers (shared)
  to its exposure to the donor at coefficient 1, from one pre-pass on the replay-calibration block. It is
  frozen, with no iteration.

**The measures,** per maze and colony:
- visits per wey (the colony mean), as the primary measure;
- legs per wey;
- the later-leg rate;
- the first-B time of later discoverers (the mean of order statistics 2-8, nonarrivals at H);
- raw entries;
- the share of weys completing at least one round trip (2 legs);
- the unvisited share, the occluded share, and the exposure.

## 7. The readings

**d per run.** For a champion c and the seed s, both on the test block with shared trails:
d = (the mean over the 256 mazes of c's visits per wey − the same for s) / s's mean.

**The gate G (registered):**
- **The estimand:** Δ = (mean d over T-A's 8 + mean d over T-F's 8 at index 299) / 2.
- **The test:** one-sided Welch.
  - The standard error is √(s_A² / 8 + s_F² / 8) / 2, with s the within-schedule SD of d.
  - The degrees of freedom are Satterthwaite's.
  - The test is at 5%.
- **The labels:**
  - **"better"** if p ≤ 0.05 for Δ > 0;
  - **"worse"** if p ≤ 0.05 for Δ < 0;
  - **"unclear"** otherwise.

  Together they allow about 10% under a symmetric null, as intended.
- **The descriptors,** fixed in advance:
  - the one-sided 95% lower bound of Δ;
  - "and at least 10%", if that lower bound is ≥ 0.10;
  - Δ × the seed's mean, in visits per wey, and as a multiple of (seed − W2 alone) and of (follower − seed),
    all measured on the test block.
- **The repeated-journey condition.** Per champion, the median over the 256 test mazes of the colony's mean
  legs per wey. If fewer than 8 of the 16 reach 2, "better" is reported as "better, but concentrated".
- **The sensitivity checks** (reported, not deciding):
  - the pooled one-sided t-test on the 16;
  - the exact sign-flip test over 2^16 patterns;
  - each schedule's mean d, with its own t interval.
- **The run-level spread:** the pooled within-schedule SD of d, √((s_A² + s_F²) / 2). It is reported
  against the assumed 0.282 with the uncertainty of Δ against the 10% reference. It is not read
  automatically as "underpowered".
- **Inference is conditional on the 256 test mazes.** If a T run failed, the gate uses the remaining runs
  per schedule and says so.

**The secondary tests (registered; Holm across the three at 5%):**
- **S-gen:**
  - the measure: T-F's champion at 299 against its own champion at 124, as the paired difference in test
    visits per wey over the 8 runs;
  - the test: a one-sided paired t-test, with the alternative "299 higher".
- **S-trail:**
  - the measure, per T run: e = [(T shared − T none) − (seed shared − seed none)] / the seed's shared mean,
    in visits per wey;
  - the test: the gate's stratified Welch estimator on e, with the alternative "greater".
  - **Reported:** the four means, and the decomposition (T shared − seed shared) = (T none − seed none) +
    e × the seed's mean.
  - **The wording:** a positive result is "increased trail dependence". It can come from a worse "none".
- **S-peer:**
  - the measure, per T run: [(T shared − T own) on the first-B time of later discoverers] / the seed's
    own value;
  - the test: the stratified Welch estimator, with the alternative "less than 0" (shorter is better).
  - The seed's own shared − own on the test block is reported beside it.

**Descriptive** (no test):
- S-worlds: T-A against T-F's champions at index 124, 8 against 8;
- N against T-A, with trails on and off;
- R's champions against R's degraded start and the seed;
- replay − own and scramble − own for the T champions and the seed, with exposure and route overlap;
- the learning curves;
- every champion's component tests at the levels E3b-0's report met, with E3b-0's thresholds (K_D ≥ 30 up
  to 0.35, K_D × level ≥ 10.5 up to 1.0, the one-nose checks);
- each champion's share of qualified nose inputs above 1.0, on the test block with shared trails;
- E3a's latch classification for each champion, and the memory assays at D = 141 where its latch has two
  stable roots;
- the training curves' best and mean fitness, and each run's zero share.

## 8. Missing outcomes

- **A run whose training stopped finally,** or whose champion's measures did not complete, is "not read";
  the outcome says "k of n read".
- **The gate needs at least 4 runs in each schedule.** Below that it is "not read", and each schedule's d is
  reported.
- **A secondary test with fewer than 4 runs per schedule** (S-gen: 4 pairs) is "not read". The Holm family
  shrinks accordingly, and this is stated.

## 9. The cap, admission and cuts

**The cap:** 24 GPU-hours for E3b-1, counted through `wormwars.accounting`, every stage included.

**After `project`,** the planned total is the projection of every stage, with the training stages
× 1.25.
- **If it exceeds 24,** the cuts are applied in this order until it fits:
  1. N to runs 0-3;
  2. R dropped;
  3. T-F to 250 generations, with the read at index 124 kept;
  4. E3b-1 does not start, and the owner is asked.
- This order departs from E3b-0's plan (generations, then worlds, then horizon) because N and R are
  secondary. The gate's arms are cut last.
- The cuts are recorded before any training.

**Admission:**
- Each training stage is admitted, in order, if the hours spent, plus its projected time, plus the
  projected time of every remaining non-training stage × 1.25, are within 22 hours (a 2-hour general
  reserve).
- Once one is refused, no later training stage starts, and the readings that need it are "not read".
- `champions` and `evaluate` are admitted if the hours spent plus their projected time are within 24.

## 10. Budget

From E3b-0's timing (0.057 s per tick at 4 096 worlds), assumed linear; the benchmark replaces it.

| Part | GPU-hours |
|---|---|
| T-A, T-F, N, R training | 4.71, 5.65, 3.53, 1.18 = 15.07 |
| The learning-curve checkpoints | 0.21 |
| `project`, `g-e` | 0.4 |
| Champion validation (32 read points × 32 × 128) | 1.21 |
| The replay pre-passes | 0.1 |
| The evaluation | 0.5 |
| **Total** | **about 17.5** |

That is 21.3 with the training × 1.25.

## 11. Tests before the formal run (each seen failing first; sabotage where a check could not fail)

1. **The mutation mask:**
   - every grafted parameter outside the frozen set has factor 0.25;
   - every frozen one has 0: W2's τ, bias and 16 edges; the relays' τ and bias; the worm block;
   - the end-of-run assertion catches a W2 edge changed by hand.
2. **"None" equals deposit-off:** with mutated genomes (not only the seed), trajectories under "none"
   equal those with d₀ = 0, bitwise on the CPU.
3. **The snapshot hook:**
   - it saves the population evaluated at index 124, before breeding;
   - off by default, it leaves `evolve_batch` bit-identical on E2's CPU smoke.
4. **The champion rule:** all 32 validated, with ties to the lower index; the checkpoint champion unused.
5. **The degraded start:** the gate weights and comparator biases at 0, on E's mask, with W2 as in the
   seed.
6. **The maze blocks:** disjoint from each other and from E3b-0's, at the same maze run seed.
7. **The test block is refused** before the evaluation stage.
8. **The gate's statistic:**
   - against hand computations, on synthetic d with unequal schedule spreads;
   - every label reached;
   - "better, but concentrated" reached;
   - "not read" below 4 runs per schedule.
9. **The secondary tests:** each statistic and direction on synthetic inputs; Holm's ordering; the shrunken
   family.
10. **The replay coefficient per organism,** and the replay donors' endpoint rule.
11. **Admission, refusal and the cuts,** on synthetic projections.
12. **The fixed inputs' hashes** are refused when changed.
13. **A smoke of every stage.**

## 12. Departures from design v2

- **The cap is 24 GPU-hours**, the plan's limit. The design gave only a projection.
- **The run seeds, the projection seed and the training span** are new.
- **The evaluation includes the oracle and the random walk** as context, in the access mode "none".
- **The gate needs at least 4 runs per schedule** to be read.

## 13. Amendments

None.
