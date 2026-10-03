# E3b-1's design: the E3 gate in mazes (v2, 2026-10-03, for confirmation)

**Status: v2, confirmed by both reviewers ("proceed to the pre-registration, with fixes; no further design
round"; `docs/reviews/20261003-E3b-1-design-v2/`; D183).** The fixes are in "v2, as confirmed" at the end; the
pre-registration carries them.
- **v1** (12289a7): Fable said "proceed to the pre-registration, with fixes"; Astra said "revise"
  (`docs/reviews/20261003-E3b-1-design/`; D182). v2 takes every point; §8 maps them.
- **E3b-1 is confirmatory.** A pre-registration follows this design, is reviewed, bound and pushed before
  any run (rule 2).
- **It builds on** E3b-0's published results (D180) and the E3b design v2 (D173).
- **The owner's schedule decision** is recorded in D181.

## 1. The question and the claim

Does joint tuning of the maze-ready seed improve the colony's shuttling in branching mazes with shared trails?
"Better" means the tuned colony against the frozen seed, on untouched mazes, under identical mechanics.

**The registered claim covers tuning under the two schedules run, as an average.** A pooled "better"
establishes neither schedule on its own, and each schedule's effect is reported beside it (both).

**Not claimed:**
- directional trail use: behavioural polarity was not shown in E3b-0;
- that the null holds for every optimiser. A null is about this initialisation, this GA and this affordable
  effort (Astra).

## 2. Fixed by E3b-0 (not reopened)

- **The task:**
  - 5 × 5 tree mazes (Wilson's algorithm), a colony of 8 weys on up to 4 spawns, H = 2 400 ticks;
  - per-wey goals; supercover movement with sliding, occlusion, and crowding off.
- **Trails:** linear; μ 0.01, λ 0.02, δ 0.05, d₀ 1.142.
- **Scents:** σ 3 path cells, zero beyond 9. The nose scale is 0.35.
- **The seed:** E3a's engineered E with W2 (resting turn +0.4, D176), on the silent carrier.
- **The peer controls and the peer measure:** as in E3b-0, with each champion's replay coefficient
  re-derived on its own pre-pass (§4).

## 3. The arms

| Arm | Runs | Generations | Mazes per genome per generation | Role |
|---|---|---|---|---|
| T-A | 8 | 125 | 16 | gate (Astra's proposal) |
| T-F | 8 | 300, with a read at 125 | 8 | gate (Fable's proposal) |
| N | 6 | 125 | 16 | without trails; secondary |
| R | 2 | 125 | 16 | the recovery control; descriptive |

- **T-A and T-F** are tuned with shared trails.
- **N** is tuned with the access mode "none".
  - Trails are laid but not sensed, so every wey behaves exactly as with deposit off. A test with mutated
    genomes confirms this.
  - Under N, E's trail-sensing edges drift without selection, which is what makes N a control (Fable).
  - **N is read against T-A,** whose schedule it matches (Astra).
- **R, the optimiser's recovery control** (Astra). It starts from a deliberately degraded seed: E's
  no-latch variant plus W2, with the gate weights and comparator biases at 0 on E's own mask.
  - It asks whether this GA, in these mazes, recovers performance it was given the means to recover.
  - Descriptive.
- **The read at generation 125 in T-F is read-only.** T-F runs to 300 whatever it shows, and no compute is
  moved between arms (both).

**The GA** is E3a's Stage 3: population 32, elites 3, truncation 8, mutation at 0.25 × the base sigmas.
- **The initial population** is 32 copies of the start organism (the seed, or for R the degraded seed).
- **Mutated:** every grafted edge, τ and bias of E's modules and selector, except the relays' τ and bias.
- **Frozen by a new mask** (`stage3_scales` would otherwise mutate them; both):
  - W2's two neurons and their 16 output edges;
  - the carrier.

  An end-of-run assertion checks that the frozen parameters are bitwise unchanged.
- **The fitness:** the colony's mean of visits per wey, over its training mazes. Every genome of a
  generation plays the same mazes (common random numbers).
- **Each run has its own training stream,** keyed by its run seed.

**The maze blocks,** all disjoint, and disjoint from E3b-0's (0-255, 1000-1255, 2000-2255, and the smoke
block 9000+):

| Use | Maze ids |
|---|---|
| Training | 10 000 000 to 19 999 999, drawn per run and generation |
| Validation | 4 000-4 127 |
| The learning curve | 4 500-4 627 |
| Replay calibration | 5 000-5 255 |
| Test | 6 000-6 255, opened once, after every champion is frozen |

The seed is re-evaluated on the test block. E3b-0's numbers are not carried over.

**Champions** (Astra's rule, as in E3a):
- at each read point (generation 125 in every run, and 300 in T-F), all 32 genomes of the population are
  scored on the 128 validation mazes;
- the champion is the best validation mean, with ties going to the lower population index.

**The learning curve** (Fable): every 25 generations, the generation's best genome is scored on the 128
learning-curve mazes. It is descriptive.

## 4. The readings

**The gate (G), registered.**
- **The estimand:** Δ = (mean d_A + mean d_F) / 2. Here d is a final champion's mean visits per wey on the
  test mazes, with shared trails, minus the seed's on the same mazes, as a share of the seed's mean.
- **The test:** a one-sided Welch t-test with variance from within each schedule (Satterthwaite degrees of
  freedom), at 5%.
- **The labels:**
  - "better" if p ≤ 0.05;
  - "worse" if the mirror test has p ≤ 0.05;
  - otherwise "unclear".

  The two directions together allow about 10% under a symmetric null, as intended.
- **The interpretation scale, fixed in advance, with no shifted null** (Fable, Astra):
  - reported: the one-sided 95% lower bound of Δ;
  - "and at least 10%" is added if that lower bound is ≥ 0.10;
  - Δ is also reported in units of E's contribution over W2 (1.09 visits per wey in E3b-0, re-measured on
    the test block) and of the seed-follower gap.
- **The sensitivity checks, reported:**
  - the pooled one-sided t-test;
  - the exact sign-flip test over 2^16 patterns.

  They do not decide the label.
- **A repeated-journey condition** (the E3b design's "minimum repeated-journey criterion"; both). If fewer
  than half of the 16 champions reach a median of at least 2 legs per wey on the test mazes, "better" is
  reported as "better, but concentrated".
  - **Reported:** raw entries, and the share of weys completing at least one round trip (2 legs).
- **Inference is conditional on the fixed test panel of 256 mazes.** Uncertainty over mazes is not part of
  the run-level test (Astra).
- **If the observed run-level CV exceeds 0.282,** "unclear" is read as underpowered (Fable).

**Secondary readings, registered, with Holm's correction across the three tests at 5%** (Astra):
- **S-gen, the effect of generations at 8 mazes:** T-F's 300 champion against its own 125 champion,
  paired, one-sided.
- **S-trail, trail dependence:**
  - **The test:** whether tuning raises trail dependence, (T on − T off) − (seed on − seed off), in visits
    per wey, over the 16 champions, one-sided.
  - **Reported:** all four means (T and the seed, with trails on and off), and the exact decomposition
    (T on − seed on) = (T off − seed off) + [(T on − T off) − (seed on − seed off)], locomotion plus trail
    dependence (Fable).
  - **The wording:** a larger on − off can arise from a worse off, so it is called "increased trail
    dependence", not better trail use (Astra).
  - **Secondary measure:** the later-leg rate.
- **S-peer, the peer measure:** shared − own on the 16 T champions, one-sided, beside the seed's on the
  same test mazes.

**Descriptive:**
- S-worlds: T-A against T-F's 125 champions, 8 against 8;
- N against T-A, with trails on and off;
- R's recovery;
- replay − own and scramble − own on the champions, with exposure reported;
- the learning curves;
- the champions' component tests at the levels E3b-0 met;
- the memory assays at D = 141, where a champion's latch has two stable roots, with E3a's latch
  classification;
- each champion's share of inputs above 1.0;
- the observed run-level CV.

## 5. Power (simulated as the gate is computed: `scripts/e3b1_power.py`, `E3b-1/power.json`)

4 000 trials per point. Effects are shares of the seed's mean.

| Scenario | False positives, Welch | Minimum detectable effect at 80% |
|---|---|---|
| Equal effects, CV 0.282 | 4.9-5.2% | 0.19 |
| Equal effects, CV 0.40 | 4.6-4.8% | 0.27 |
| Unequal spreads (0.15 and 0.40) | 4.8-5.3% | 0.21 |
| Schedule means ± 0.10 | 4.5-5.1% | 0.19 |
| Opposite effects averaging zero | 4.4-5.0% (calibrated for the estimand) | — |

*Correction, 2026-10-03 (Astra, D183):* this table first gave 0.18-0.19, 0.25-0.27, 0.20-0.21 and 0.18-0.19.
The empirical-shape rows were simulated with variance 7/8 of the nominal (a ddof error). After the fix
(ddof 0, `power.json` regenerated), both shapes give the values above. The normal-shape rows did not change.

- **The pooled t-test and the sign-flip test** keep 5.0-5.5% false positives with equal effects at CV
  0.282. They reject only 2.9-3.6% in the opposite-effects case: they are conservative there.
- **Against a shifted null at 10%,** the minimum detectable effect would be 0.28-0.31 at CV 0.282 and with
  unequal spreads, and 0.36-0.37 at CV 0.40. That is why the 10% is a descriptor, not the test.
- **In visits:** 0.18-0.19 of E3b-0's seed mean (5.78) is about 1.0-1.1 visits per wey, the size of E's
  whole contribution over the blind W2 (Fable). The gate detects a gain of that size, not a modest
  refinement, and the results will say so.

## 6. The compute

From E3b-0's timing: 0.057 s per tick at 4 096 worlds, assumed linear, H = 2 400.

| Item | GPU-hours |
|---|---|
| Training: T-A 4.71, T-F 5.65, N 3.53, R 1.18 | 15.1 |
| Training with the 25% reserve | 18.8 |
| Champion validation (32 read points × 32 genomes × 128 mazes) | 1.2 |
| The learning curves | 0.2 |
| Replay-coefficient pre-passes (16 champions and the seed) | 0.1 |
| The test evaluation (about 33 organisms, on and off, peer controls with replay donors, chunked) | 0.5 |
| The GPU equivalence leg, the benchmark, assays | 0.4 |
| **Total** | **about 21.2** |

That is within the plan's 24 and the roughly 27.4 left of the owner's E3b ceiling.

- **Before any training, a benchmark** times complete generations at each arm's real composition (T-A 4 096
  worlds, T-F 2 048, N 3 072, R 1 024), validation and the chunked evaluation. The projection is registered
  from that benchmark (both).
- **If it exceeds 24 hours, the cuts are, in order:**
  1. N to 4 runs;
  2. R dropped;
  3. T-F's generations to 250;
  4. the owner asked.

  This departs openly from E3b-0's plan order (generations, worlds, horizon), because N and R are
  secondary.

## 7. Before the pre-registration

- **The GPU equivalence leg** (E2's GA generations 0-25, hashed), owed since E3b-0.
- **The new freezing mask,** test-first, with the end-of-run assertion.
- **"None" equals deposit-off** with mutated genomes, test-first.
- **The runner's read points,** the population snapshot at 125, and the learning-curve hook.

## 8. Changes from v1 (the reviews)

| Point (who) | v2 |
|---|---|
| The pooled gate (both) | The estimand is the equal-weight mean of two schedules, tested by a Welch t-test within schedules (Astra). The pooled t and the sign-flip are sensitivity checks, not a conjunction (Astra). Each schedule is reported (both) |
| The power claims (both) | 0.18-0.19 at CV 0.282, not 0.17-0.19. The gate is now simulated as computed, including unequal spreads, different means and opposite effects (Astra), and the 16-run sign-flip (Fable) |
| A margin (both) | None in the test. The lower bound and a 10% descriptor, with units of E's contribution (Fable, Astra) |
| The champion rule was undefined (both) | All 32 genomes validated at each read point, as E3a did (Astra). v1's claim that E3a validated whole populations was wrong (Astra) |
| The learning curve (Fable) | Every 25 generations, on its own block |
| "None" access (both) | Kept, and tested with mutated genomes. Read against T-A (Astra) |
| S-trail (both) | Visits per wey, with the decomposition (Fable), the four means and "trail dependence" (Astra) |
| Multiplicity (Astra) | Holm across three secondary tests |
| The repeated-journey criterion (both) | A condition on "better", with round trips reported |
| The maze blocks (both) | Named and disjoint. The test block is not E3b-0's report block. The seed is re-evaluated |
| The read at 125 (both) | Read-only |
| The W2 freeze (both) | A new mask and an assertion |
| The recovery control (Astra) and the memory assays (Astra) | R arm (2 runs); assays descriptive |
| Inference scope (Astra) | Conditional on the test panel |
| The budget (both) | A benchmark of complete generations at the real compositions first; every item listed; the cut order with its departure stated |

## v2, as confirmed (2026-10-03; D183)

Both reviewers said "proceed to the pre-registration, with fixes; no further design round". The
pre-registration pins these.

1. **The power.** The empirical-shape scaling is fixed (Astra), and §5 is corrected. Fable adds that the
   simulation treats 0.282 as the SD of d at every effect. If instead the CV holds at the tuned mean, the
   SD of d at Δ 0.19 is about 0.34, and the minimum detectable effect is nearer 0.22-0.23. The CV-0.40
   rows bracket this.
2. **The maze run seed is 1 180 000, E3b-0's,** so disjoint ids are disjoint mazes (`maze_for` keys the
   walls by (run seed, maze id); Fable).
3. **W2's freeze covers** its two neurons' τ and bias and their 16 output edges. Its inputs come through the
   interface, not through graft edges (Fable).
4. **Every secondary test is pinned:**
   - **S-gen:** a one-sided paired t-test on T-F's 8 pairs (generation 300 against generation 125), the
     alternative being "300 is higher";
   - **S-trail:** the gate's stratified Welch estimator on the per-run differences
     [(T on − T off) − (seed on − seed off)], the alternative being "greater";
   - **S-peer:** the same estimator on shared − own, the alternative being "less than 0", since a shorter
     first-B time is better;
   - Holm's correction is applied across the three.
5. **The evaluation roster on the test block:**
   - the 16 final T champions and T-F's 8 champions at generation 125;
   - the 6 N champions and the 2 R champions;
   - the seed E + W2, and R's degraded start;
   - W2 alone on the carrier, the scripted follower, the oracle and the random walk.
6. **The read at generation 125** is the population of 32 genomes evaluated at generation index 124 (the
   125th generation), before that generation's selection and mutation. Its validation scores do not feed
   back into T-F's continuation. The end of T-F is generation index 299.
7. **The run-level spread** is the pooled within-schedule SD of d, in units of the seed's mean, matching
   the Welch variance. An observed value above 0.282 is reported with the uncertainty of Δ against the
   10% reference. It is not read automatically as "underpowered" (Astra).
8. **"Trails off" means the access mode "none" throughout,** the tested equivalent of deposit-off.
9. **The repeated-journey median,** as E3b-0 computed it: per champion, the median over the 256 test mazes
   of the colony's mean legs per wey (Astra). "Better, but concentrated" applies if fewer than 8 of the
   16 champions reach 2.
10. **A crashed or non-finite run** is rerun once on the same seed. If it fails again, it is reported as
    failed, and the gate is computed on the remaining runs with that stated (Fable).
11. **The 25% reserve covers training only.** The benchmark sizes the rest.
