# E3b-1 results: the E3 gate in mazes (2026-10-04)

**Reviewed by both reviewers** (Astra 6, Fable 5.1: "fix then publish"); fixed (D192;
`docs/reviews/20261004-E3b-1-results/`). Both reviewers recomputed the registered readings from the
committed records, and every one matched.

**E3b-1 is confirmatory.**
- **The pre-registration** (`PREREGISTRATION.md`) was bound at 1c65e4e before any stage ran (D186).
- **Amendment 1** (infeasible mazes redraw their walls) was added after formal work had started and before
  any score was read (§14; D190, D191). See "Deviations and disclosures" below.
- **The code** was reviewed by both reviewers before the formal run (D188, D189).
- **Every number here** comes from the committed records in this folder: `evaluate.json` (`readings`,
  `probes`), the per-maze arrays `eval-*.npz`, and the training and champions records.
- **The test set:** inference is conditional on the 256 prespecified test mazes (6000-6255). Test maze 6073
  was redrawn under Amendment 1, and test maze 6000 had been played by the frozen seed in an audit trace (see
  the disclosures).

**Compute:** 18.73 of the 24 hours capped, over 9 attempts (`compute-record.json`). The accounting unit is
synchronised wall-clock time per category, CPU work included, not GPU kernel time.

| Stage | Hours (the stage record's wall time) | Projected |
|---|---|---|
| `project` | 1.04, on its rerun after Amendment 1 (attempt 1: 1.13 s) | |
| `g-e` | 0.07 | 0.3 |
| T-A | 5.12 | 5.05 |
| T-F | 6.44 | 6.32 |
| N | 2.62 | 2.54 |
| R | 1.55 | 1.53 |
| `champions` | 1.19 | 1.18 |
| `evaluate` | 0.69 | 1.03 |

- **Cuts:** cut 1 applied (N to runs 0-3); no other cut.
- **Training:** every run completed on its first attempt. The frozen-parameter assertion passed in every run.
- **No kill occurred.** D189's bound on undercharging a kill (up to about 40 minutes for T-A) was not
  exercised.

## In brief

- **G, the gate: "better".** Joint tuning of the seed E + W2 improved the colony's shuttling in 5 × 5 tree
  mazes with shared trails, against the frozen seed, on the 256 prespecified test mazes.
  - **The estimand** (the mean of the two schedules' mean d): Δ = +0.225 of the seed's mean, one-sided Welch
    p = 7.2 × 10⁻⁵.
  - **Its one-sided 95% lower bound is +0.166,** "and at least 10%".
  - **In visits per wey:** +1.32 (the seed makes 5.84).
  - **What the gate was built for:** §8 sized it to detect a gain of about 1.1 visits per wey, E's whole
    contribution over the blind W2 in E3b-0, not a modest refinement. The observed gain is of that size.
- **The two schedules differ about 5.5-fold.**

  | Schedule | Runs | Mean d | 95% interval |
  |---|---|---|---|
  | T-A (125 generations, 16 mazes per generation) | 8 | +0.069 | [+0.043, +0.096] |
  | T-F (300 generations, 8 mazes per generation) | 8 | +0.381 | [+0.233, +0.529] |

  - G is an average over the two schedules run.
  - **T-A's interval tops out at +0.096,** so T-A alone would not reach the 10% descriptor. The gate's
    "at least 10%" rests on T-F.
- **The secondary tests:** all three are significant after Holm's correction.
  - **S-gen:** T-F's champions at index 299 are above their own at index 124, by +0.315 of the seed's mean;
    Holm p = 0.002.
  - **S-trail:** "increased trail dependence", +0.127; Holm p = 0.005.
    - **As a descriptive split, the increase comes from T-F:** its e is positive in all 8 runs, mean +0.31.
    - **T-A's e** has mean −0.06 and is negative in 7 of 8 runs.
    - **T-A still benefits from trails:** shared − none is +1.00 visits per wey for its champions, against
      +1.34 for the seed. What T-A lacks is an increase in dependence, not a trail benefit.
  - **S-peer:** peers' trails still shorten later discoverers' first-B times. The tuned champions'
    shared − own is −0.060 in units of the seed's own first-B time; Holm p = 8 × 10⁻⁵.
    - Beside it, the seed's own shared − own is −0.118.
- **The probes** (descriptive, §6).
  - **No champion meets the registered active-comparator criteria** under the probe protocol: none reaches
    K_D 30 at any level, on either goal. The seed reaches 31-35 on both goals at every level up to 0.35.
  - **What this shows:** the tuned organisms depart from the seed's measured component performance.
  - **What it does not show:** whether, or how much, the maze gain depends on the engineered A/B selector.
    The probes do not partition the gain by mechanism.

## G: the registered gate (§7)

**Read on block 1** (shared trails, the 256 test mazes, episode 0) for the seed and the 16 final T champions.

**The estimand and its test:**
- Δ = (mean d over T-A + mean d over T-F at index 299) / 2 = **+0.2253**;
- SE 0.0318, Welch ν = 7.46, one-sided p = 7.2 × 10⁻⁵; **label "better"**;
- the one-sided 95% lower bound is +0.1657, so "and at least 10%" holds.

**Per run, d:**

| Schedule | d, runs 0-7 |
|---|---|
| T-A | +0.132, +0.048, +0.060, +0.099, +0.054, +0.073, +0.059, +0.031 |
| T-F | +0.385, +0.298, +0.430, +0.492, +0.113, +0.549, +0.611, +0.171 |

**The descriptors:**
- **Δ in visits per wey:** +1.32.
- **As a multiple of (seed − W2 alone on the carrier):** 0.32. The seed makes 5.84 and W2 alone 1.72.
  - **Not comparable with E3b-0's "+1.09 above W2 alone".** That figure used E3b-0's scripted W2 controller
    under "none". This one is the W2 module grafted on the silent carrier (§6; D188).
- **As a multiple of (follower − seed):** 0.12. The scripted follower makes 16.98.

**The repeated-journey condition:** every champion's median legs per wey is at least 2 (4.25 to 5.50), so
"better" is not "concentrated".

**The sensitivity checks:**
- the pooled one-sided t-test gives p = 2.3 × 10⁻⁴;
- the exact sign-flip test on the estimand gives p = 1.5 × 10⁻⁵ (1 of 65 536 patterns);
- every one of the 16 runs has d > 0.

**The run-level spread:** √((s_A² + s_F²)/2) = 0.127 of the seed's mean, against the 0.282 assumed in §8, at
which the prospective minimum detectable effect was 0.19.
- The observed variation within the schedules was smaller than assumed: the schedule SDs are 0.032 (T-A) and
  0.177 (T-F).
- The uncertainty of Δ is SE 0.032, with a lower bound of +0.166, above the 10% reference.

## The secondary tests (§7; Holm over three at 5%)

| Test | Measure | Estimate | Raw p | Holm p | Conclusion |
|---|---|---|---|---|---|
| S-gen | paired, T-F at index 299 − its own at index 124 | +0.315 (one-sided 95% lower bound +0.190; 8 pairs) | 0.0010 | 0.0020 | T-F's champions at index 299 above their own at index 124 |
| S-trail | e = [(T shared − T none) − (seed shared − seed none)] / seed shared | +0.127 (lower bound +0.054) | 0.0050 | 0.0050 | increased trail dependence |
| S-peer | [T shared − T own] in the later discoverers' first-B time / the seed's own | −0.060 (upper bound −0.042) | 2.8 × 10⁻⁵ | 8.4 × 10⁻⁵ | shorter first-B times of later discoverers with peers' trails |

### S-trail

**Per run, e:**

| Schedule | e, runs 0-7 | Mean |
|---|---|---|
| T-A | +0.066, −0.006, −0.021, −0.003, −0.059, −0.130, −0.060, −0.257 | −0.059 |
| T-F | +0.287, +0.209, +0.164, +0.404, +0.089, +0.573, +0.634, +0.141 | +0.313 |

The split by schedule is descriptive. The registered test is the stratified one above.

**The four means and the decomposition:**
- **The means** (both schedules, weighted equally, on complete pairs): T shared 7.16, T none 5.07, seed
  shared 5.84, seed none 4.50.
- **The decomposition:** (T shared − seed shared) = +1.32 visits splits into (T none − seed none) = +0.57 and
  e × the seed's shared mean = +0.74.

**The same contrast in the later-leg rate** (shared − none, legs per 1 000 ticks; descriptive, registered in
§7):

| | Shared − none, runs 0-7 | Mean |
|---|---|---|
| The seed | 0.61 | |
| T-A | 0.79, 0.59, 0.53, 0.67, 0.46, 0.30, 0.48, −0.10 | 0.46 |
| T-F | 1.44, 1.25, 1.10, 1.82, 0.89, 2.32, 2.50, 1.05 | 1.55 |

Every T-F champion is above the seed; 6 of 8 T-A champions are below it.

**The "worse none" rule** (§7: a positive result can come from a worse "none"):
- **At the schedule level, it does not:** both schedules' "none" means are above the seed's.
- **For two champions, part of e does come from a worse "none":** T-F runs 5 and 6 make 4.36 and 4.37 visits
  under "none", against the seed's 4.50. They are also the two best scorers with trails (d +0.549, +0.611).

### S-peer

- **The tuned champions:** their shared − own is −0.060 in units of the seed's own first-B time (1 526 ticks).
  Their own first-B times average about 1 060 ticks, so relative to their own times the benefit is about −9%.
- **The seed's own:** −11.8% (shared 1 347, own 1 526).
- **The comparison** between these two benefits is descriptive. No reduction in peer benefit was tested.

## Descriptive readings (§7; no tests)

**S-worlds** (T-A against T-F at index 124): the observed means were similar, +0.069 for T-A and +0.066 for
T-F's champions at index 124. That establishes neither equivalence nor the absence of an effect.

**N against T-A.** Differences from the seed's mean in the same condition, in units of the seed's *shared*
mean:

| | N's 4 champions | T-A's 8 champions |
|---|---|---|
| Shared trails | −0.13 | +0.07 |
| Trails off | +0.36 (+0.32 to +0.40) | +0.13 |

Relative to the seed's "none" mean instead, the trails-off row is +0.46 for N and +0.17 for T-A. Tuning
without sensing trails found colonies better than the seed without trails and worse than it with them.

**R** (from the degraded start: the latch's gate weights and the comparator biases at 0):
- the degraded start makes 0.48 visits per wey, −0.92 of the seed's mean;
- R's 2 champions recover +0.36 of the seed's mean and end at −0.56.

**Peer conditions** (§6's block 5; later-leg rate, condition − own, legs per 1 000 ticks):

| Condition | The seed | The T champions' mean | Mean exposure, seed / T mean |
|---|---|---|---|
| shared | | | 0.113 / 0.116 |
| replay (a donor colony's field, added to the wey's own trail) | −1.06 | −1.23 | 0.089 / 0.101 |
| scramble (the live peers' field, spatially permuted, added to the wey's own) | −1.36 | −1.35 | 0.019 / 0.019 |
| peers only (live peers' trails, without the wey's own) | −0.05 | +0.47 | 0.103 / 0.102 |

- **Replay and scrambled peer fields reduced the later-leg rate** relative to own-only trails, under these
  conditions.
- **Their exposure was not matched.** Replay's coefficient came from the calibration block (seed 0.61; T
  champions 0.54-0.87), and on the test block replay's exposure fell short of shared's. Scramble's is about
  a sixth of it.
- **With live peers' trails alone,** T-F's champions do better than with their own: +0.63 to +1.70.
- **The donors' geometric A-B route overlap** with the recipient's (the routes, not travelled
  trajectories) is 0.41 on average (median 0.37).

**The nose recorder** (the share of qualified inputs above 1.0; shared trails; test block; per champion in
`readings.nose_share_above_1`):
- the seed 5.5%;
- the 16 final T champions 2.9%-9.9%; T-F's champions at index 124 2.3%-3.6%;
- N 1.7%-2.3%; R 0.4%-0.5%;
- W2 alone 0.2%; the follower 19.0%.

Above 1.0 the comparator's response is reported, not required (§6).

**The probes** (block 7, on the CPU, under the registered protocol). The protocol imposes each champion's two
stable latch states, taking the upper as goal A, at E3b-0's fixed levels.
- **Every champion's latch is bistable** at its own q self-weight and bias. Static bistability does not show
  switching in the maze, and E3a's memory assays were not run (§6).
- **Active criterion:** none of the 30 reaches K_D 30 at any level, so none passes.
- **The other saved flags** (E3a's component tests):
  - inactive criterion: 29 of 30;
  - startup: 0 of 30;
  - offset: 2 of 30;
  - switching: 30 of 30. Its check compares against 90% of the settled response, so a zero settled response
    passes trivially. It is not evidence of working goal switching.
- **One-nose checks:** 4 pass: T-A runs 3 and 6; T-F run 5's final champion and run 4's at index 124.
- **An exploratory presentation of the active K_D.** The grouping is not registered. A response here means
  K_D > 10 (the maximum over the levels in each range):

  | Read points | Goal A, levels ≤ 0.04 | Goal A, 0.23-0.35 | Goal B, ≤ 0.04 | Goal B, 0.23-0.35 | Zero measured K_D at every level ≤ 1.0 |
  |---|---|---|---|---|---|
  | T (24: T-A's 8, T-F's 8 finals and 8 at index 124) | 21 (K_D 20-28) | 3 | 4 | 2 | 3 (T-F finals 2, 3 and 7) |
  | N (4) | 0 | 4 (K_D 22-27) | 0 | 0 | 0 |
  | R (2) | 0 | 0 | 0 | 0 | 2 |

  - **N's goal B** responds only at 0.89-1.0 (K_D 11.9-16.5).
  - **T-F finals 3 and 2 are the third and fourth best of the 16 by d** (+0.492, +0.430). With T-F final 7,
    they do respond to one-sided inputs: at level 0.23, on both goals, their one-nose turn goes from +1 with
    no input to −1 with the right nose alone. The baseline is saturated, so the check's "left above none"
    cannot pass. Zero K_D is measured around equal inputs only.
  - **The caveat:** a champion whose latch flipped its coding would read as having lost goal B. The probes do
    not say how the champions shuttle.

**Training** (each training record holds the full logs and learning curves):

| Arm | Runs | Generation-0 best (= mean) fitness | Last generation's best / mean fitness | Zero share at the last generation | Learning curve (128 mazes, generation-best): index 0 → last, mean [range] |
|---|---|---|---|---|---|
| T-A | 8 | 5.27 | 6.79 / 5.29 | 0 | 4.50 → 5.70 [5.38, 6.13] |
| T-F | 8 | 5.20 | 8.91 / 6.46 | 0 | 4.50 → 6.75 [5.78, 7.28] |
| N | 4 | 3.28 | 6.16 / 4.72 | 0 | 3.31 → 6.00 [5.42, 6.38] |
| R | 2 | 0.52 | 2.64 / 2.42 | 0 | 0.47 → 2.48 [2.24, 2.71] |

Fitness is the training mazes' mean visits per wey under the arm's access. The learning curve is descriptive
and selects nothing.

## What this does and does not show

**Shown, as registered:**
- **The gate:** the tuned colonies outperform the frozen seed E + W2 on the 256 prespecified test mazes with
  shared trails.
  - The claim is an average over the two schedules run, from this seed, with this GA.
  - The gain is mostly T-F's (300 generations).
- **The secondary readings:**
  - more generations helped (S-gen);
  - trail dependence increased (S-trail), through T-F as a descriptive split;
  - peers' trails still help later discoverers (S-peer).

**Not shown:**
- **Whether, or how much, the gain depends on the engineered A/B selector.** No champion meets the registered
  active-comparator criteria under this probe protocol, and three T-F champions have zero measured active K_D
  at every tested level. That establishes departure from the seed's measured component performance, not the
  route of the maze gain.
- **That weys follow a trail's direction** (§1; polarity was not shown in E3b-0).
- **Anything about worm behaviour.** The organism is a hand-built circuit on a silent worm, outside the N2
  mask.

**The frame:** stereo sensing and the maze-ready additions are game-design choices.

## Deviations and disclosures

- **Amendment 1 (D190), with its correction (D191).**
  - **The problem:** the registered schedules contained infeasible mazes: test id 6073, and 37 training ids
    (36 in the stages run after cut 1).
  - **The rule:** they now redraw their walls, keyed by the id. Every previously feasible maze in the audited
    corpus was bitwise unchanged.
  - **What the audit exposed:**
    - it read the walls of every block, the test block included;
    - its equivalence trace played the frozen seed for 300 CPU ticks on test maze 6000 (with validation
      mazes 4000 and 4001), twice;
    - this happened during the amendment audit, before `project`'s rerun and the evaluation. Only a hash of
      positions and events was computed; no score or behaviour was read.

    It breached §4's rule that the test block opens only in the evaluation stage, and it is reported as
    such. The trace now plays mazes outside every block.
  - **In the records:** each stage lists its redrawn mazes. `evaluate` played test maze 6073 redrawn
    (k = 1).
- **`project` ran twice.** Attempt 1 stopped after about 1 second on an infeasible maze. Its record is kept
  (`project-attempt1.json`).
- **Cut 1** (N to runs 0-3) was applied by `project`'s plan, before any training.

## Reproduce it

See `README.md` in this folder.
