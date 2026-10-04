# E3b-1 results: the E3 gate in mazes (2026-10-04)

**Draft, under review by both reviewers. Not yet published on main.**

**E3b-1 is confirmatory.**
- **The pre-registration** (`PREREGISTRATION.md`) was bound at 1c65e4e before any stage ran (D186).
- **Amendment 1** (infeasible mazes redraw their walls) was added before any score was read, after formal
  work had started. Its dated correction discloses that an audit trace had played the frozen seed on one test
  maze, with only a hash computed (§14; D190, D191).
- **The code** was reviewed by both reviewers before the formal run (D188, D189).
- **Every number here** comes from the committed records in this folder: `evaluate.json` (`readings`,
  `probes`), the per-maze arrays `eval-*.npz`, and the training and champions records. Inference is
  conditional on the 256 test mazes.

**Compute:** 18.73 of the 24 GPU-hours capped, over 9 attempts (`compute-record.json`).

| Stage | Hours (the stage record's wall time) | Projected |
|---|---|---|
| `project` | 1.04, on its rerun after Amendment 1 | |
| `g-e` | 0.07 | 0.3 |
| T-A | 5.12 | 5.05 |
| T-F | 6.44 | 6.32 |
| N | 2.62 | 2.54 |
| R | 1.55 | 1.53 |
| `champions` | 1.19 | 1.18 |
| `evaluate` | 0.69 | 1.03 |

- **Cut 1 applied** (N to runs 0-3); no other cut.
- **Every training run completed on its first attempt.** The frozen-parameter assertion passed in every run.

## In brief

- **G, the gate: "better".** Joint tuning of the seed E + W2 improved the colony's shuttling in 5 × 5 tree
  mazes with shared trails, against the frozen seed, on 256 untouched mazes.
  - **The estimand** (the mean of the two schedules' mean d): Δ = +0.225 of the seed's mean, one-sided Welch
    p = 7.2 × 10⁻⁵.
  - **Its 95% lower bound is +0.166,** "and at least 10%".
  - **In visits per wey:** +1.32 (the seed makes 5.84).
- **The two schedules differ by a factor of five.**

  | Schedule | Runs | Mean d | 95% interval |
  |---|---|---|---|
  | T-A (125 generations, 16 mazes per generation) | 8 | +0.069 | [+0.043, +0.096] |
  | T-F (300 generations, 8 mazes per generation) | 8 | +0.381 | [+0.233, +0.529] |

  G is an average over the two schedules run. T-A's gain alone is small.
- **The secondary tests:** all three are significant after Holm's correction.
  - **S-gen:** T-F's champions at index 299 are above their own at index 124, by +0.315 of the seed's mean;
    Holm p = 0.002.
  - **S-trail:** "increased trail dependence", +0.127; Holm p = 0.005.
    - **It comes from T-F:** its e is positive in all 8 runs, mean +0.31.
    - **T-A's e** averages −0.05 and is negative in 6 of 8 runs.
  - **S-peer:** peers' trails still shorten later discoverers' first-B times. The tuned champions'
    shared − own is −0.060 of the seed's own; Holm p = 8 × 10⁻⁵.
    - Beside it, the seed's own shared − own is −0.118.
    - The tuned colonies keep the peer benefit, at about half the seed's size relative to the seed's own
      time.
- **The tuned champions no longer pass the seed's component tests** (descriptive, §6). The registered gate
  says tuning improved shuttling. It does not show that the improvement runs through the engineered A/B
  selector; the probes suggest it largely does not.
  - **All 30 read points' champions are bistable.**
  - **None reaches K_D 30** at any level, on either goal, so none passes E3b-0's thresholds for the active
    comparator.
  - **Only 4 pass the one-nose checks.**
  - **The seed** responds at K_D 31-35 on both goals at every level up to 0.35 (E3b-0's `report.json`).
  - **Three of T-F's final champions respond to neither goal** at any level up to 1.0, among them two of the
    best scorers (d +0.43 and +0.49).

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

**The run-level spread:** √((s_A² + s_F²)/2) = 0.127 of the seed's mean, against the 0.282 assumed in §8.
At that assumption the minimum detectable effect was 0.19. Δ = 0.225 exceeds it, and the realised spread is
less than half the assumed one, so the test had more power than planned. Most of the spread is between T-F's
runs.

## The secondary tests (§7; Holm over three at 5%)

| Test | Measure | Estimate | Raw p | Holm p | Conclusion |
|---|---|---|---|---|---|
| S-gen | paired, T-F at index 299 − its own at index 124 | +0.315 (one-sided 95% lower bound +0.190; 8 pairs) | 0.0010 | 0.0020 | T-F's champions at index 299 above their own at index 124 |
| S-trail | e = [(T shared − T none) − (seed shared − seed none)] / seed shared | +0.127 (lower bound +0.054) | 0.0050 | 0.0050 | increased trail dependence |
| S-peer | [T shared − T own] in the later discoverers' first-B time / the seed's own | −0.060 (upper bound −0.042) | 2.8 × 10⁻⁵ | 8.4 × 10⁻⁵ | shorter first-B times of later discoverers with peers' trails |

**S-trail's four means and decomposition:**
- **The means** (both schedules, weighted equally): T shared 7.16, T none 5.07, seed shared 5.84, seed none
  4.50.
- **The decomposition:** (T shared − seed shared) = +1.32 visits splits into (T none − seed none) = +0.57 and
  e × the seed's shared mean = +0.74.
- **The two schedules differ in kind** (above). T-F's gain depends more on trails; T-A's does not.
- **As registered,** a positive result can come from a worse "none". Here both schedules' "none" means are
  above the seed's, so it does not.

**S-peer:**
- the tuned champions' peer benefit is −6% of the seed's own first-B time (1 526 ticks);
- the seed's own peer benefit is −11.8% (shared 1 347, own 1 526).

## Descriptive readings (§7; no tests)

- **S-worlds** (T-A against T-F at index 124): T-A's mean d is +0.069, and T-F's champions at index 124 make
  +0.066. At 125 generations, 16 mazes per generation did no better than 8. T-F's large gain comes after
  index 124.
- **N against T-A:**
  - **With shared trails:** N's 4 champions are −0.13 of the seed's mean, below the seed; T-A's are +0.07.
  - **With trails off**, d against the seed's "none" mean: N's are +0.36 (+0.32 to +0.40), T-A's +0.13.
  - So tuning without sensing trails found colonies better without trails and worse with them.
- **R** (from the degraded start, the latch's gate weights and the comparator biases at 0):
  - the degraded start makes 0.48 visits per wey, −0.92 of the seed's mean;
  - R's 2 champions recover +0.36 of the seed's mean and end at −0.56.
- **Peer conditions** (later-leg rate, condition − own, per 1 000 ticks):
  - **replay:** the seed −1.06, the T champions' mean −1.23;
  - **scramble:** the seed −1.36, the T champions' mean −1.35;
  - **peers only:** the seed −0.05, the T champions' mean +0.47.
  - As in E3b-0, peer fields not laid by the colony itself hurt.
  - **The replay coefficients:** the seed 0.61; the T champions 0.54-0.87.
  - **The donor routes** overlap the recipient's by 0.41 on average (median 0.37).
- **The nose recorder** (the share of qualified inputs above 1.0, shared trails, test block):
  - the seed 5.5%; the T champions 2.9%-9.9%; N 1.7%-2.3%; R 0.4%-0.5%;
  - W2 alone 0.2%; the follower 19.0%.
  - Above 1.0 the comparator's response is reported, not required (§6).
- **The probes** (block 7, on the CPU):
  - every champion's latch is bistable, at its own q self-weight and bias;
  - **component tests at its two states** (the upper for goal A): none of the 30 reaches K_D 30 at any level,
    so none passes the active thresholds;
  - **one-nose checks:** 4 pass (T-A runs 3 and 6; T-F run 5's final champion and run 4's at index 124);
  - **the pattern,** counting a response as K_D > 10 at a level (the maximum over the levels in each range):

    | Read points | Goal A, levels ≤ 0.04 | Goal A, 0.23-0.35 | Goal B, ≤ 0.04 | Goal B, 0.23-0.35 | Neither goal at any level ≤ 1.0 |
    |---|---|---|---|---|---|
    | T (24: T-A's 8, T-F's 8 finals and 8 at index 124) | 21 (K_D 20-28) | 3 | 4 | 2 | 3 (T-F finals 2, 3 and 7) |
    | N (4) | 0 | 4 (K_D 22-27) | 0 | 0 | 0 |
    | R (2) | 0 | 0 | 0 | 0 | 2 |

    N's goal B responds only at 0.89-1.0 (K_D 12-17);
  - **the caveat:** the probe takes the upper stable state as goal A, as E3a's did. A champion whose latch
    flipped its coding would read as having lost goal B. The probes do not say how the champions shuttle.
- **The training and learning curves** are in each training record: generation-best and mean fitness,
  zero share, and the learning-curve block at the checkpoints. The learning curve is descriptive and selects
  nothing.

## What this does and does not show

**Shown, as registered:**
- **The gate:** the tuned colonies outperform the frozen seed E + W2 on untouched mazes with shared trails.
  - The claim is an average over the two schedules run, from this seed, with this GA.
  - The gain is mostly T-F's (300 generations).
- **The secondary readings:** more generations helped (S-gen); trail dependence increased, through T-F
  (S-trail); peers' trails still help later discoverers (S-peer).

**Not shown:**
- **That the gain comes through the engineered A/B selector.** The probes suggest the tuned comparators no
  longer meet E's design criteria. The gain may come from the reflexes, the turn biases or other routes that
  this experiment did not probe.
- **That weys follow a trail's direction** (§1; polarity was not shown in E3b-0).
- **Anything about worm behaviour.** The organism is a hand-built circuit on a silent worm, outside the N2
  mask.

**The frame:** stereo sensing and the maze-ready additions are game-design choices.

## Deviations and disclosures

- **Amendment 1 (D190), with its correction (D191).**
  - **The problem:** the registered schedules contained infeasible mazes (test id 6073, and 37 training ids).
    They now redraw their walls, keyed by the id; every feasible maze is bitwise unchanged.
  - **The disclosure:** an audit trace played the frozen seed for 300 CPU ticks on test maze 6000, twice,
    before the amendment. Only a hash was computed.
  - **In the records:** each stage lists its redrawn mazes. `evaluate` played test maze 6073 redrawn (k = 1).
- **`project` ran twice:** attempt 1 stopped after about 1 second on an infeasible maze, and its record is
  kept (`project-attempt1.json`).
- **Kill accounting:** no kill occurred, so the bound on undercharging a kill (D189) did not apply.

## Reproduce it

See `README.md` in this folder.
