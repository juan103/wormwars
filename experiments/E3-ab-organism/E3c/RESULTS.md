# E3c results: the assembly comparison in the maze shuttle (2026-10-06)

**Status:** reviewed by both reviewers ("fix then publish") and corrected (D220).

**The registration:**
- the pre-registration is bound at 69d7cd5, with Amendment 1 and Amendment 2 (§14);
- the formal code is at 3cb35fb;
- the run used 22.65 of E3c's 30 GPU-hours.

**Every number below** is from the committed records in this folder: `report.json`, `evaluate.json`,
`champions.json`, the training records and `compute-record.json`. Astra reproduced `report.json` from the records
exactly, and both reviewers recomputed the figures they could.

**The labels:**
- **registered:** labels that come from the pre-registration's rules, and also the supplements and descriptive
  classifications it names. Labels are quoted as the code emits them;
- **exploratory:** everything else, marked as such.

## In brief

**Q1, modular against dense, both trained from random weights:**
- **The margin reading:** **"approximate (model-based): no relevant difference"**.
  - S-mod − S-dense is −0.048 visits per wey. Its 97.5% interval, [−0.120, +0.023], lies inside the smaller
    registered margin of about 0.5 visits.
- **The exact test:** **"no difference detected (exact)"** (p = 0.099).
- **The registered qualifier:**
  - S-mod: 8 nose-independent, 8 coverers of 8;
  - S-dense: 8 nose-independent, 8 coverers of 8.

**Q2, the engineered start plus its tuning recipe (P-joint) against E's mask from scratch (S-mod):**
- **The margin reading:** **"approximate (model-based): unclear"**.
  - These eight P-joint champions averaged 0.66 visits per wey more than the eight S-mod champions (+0.13 of the
    seed's mean).
  - The 97.5% interval, [−0.24, +1.57], allows anything from a small deficit to a large advantage.
- **The exact test:** **"no difference detected (exact)"** (p = 0.052, against 0.025).
- **The registered qualifier:**
  - P-joint: 4 partial, 4 nose-dependent, 0 coverers of 8;
  - S-mod: 8 nose-independent, 8 coverers of 8.
- **The registered expectation** ("engineered initialization better") is neither confirmed nor refuted.

**The coverage hypothesis** (a registered descriptive classification): **"supported"**, with the S arms' part
"high".
- **All 16 selected champions trained from random weights met the coverer criterion.** They keep 99.5-100.1% of
  their visits with the noses removed, cover 99-100% of the maze, and repeat a circuit of the tree.
- **None of P-joint's 8 met it.** Their scores fall by 3.3 visits per wey without their noses, and follow the
  maze's geometry.

**What E3c can and cannot say:** in this task a scent-free circuit is a strong solution. So E3c compares training
routes on such a task, not assemblies of stereo navigators (§1).

## The setting

**The task:** E3b-1's maze shuttle (c = 5, H = 2 400, colonies of 8, shared trails), on 256 new test mazes
(10 400-10 655).

**The arms** (§3), every one trained for 300 generations × 8 mazes per genome:

| Arm | What it is | Runs |
|---|---|---|
| S-mod | E's mask (65 scalars), from a random draw, factor 1.0 | 8 |
| S-dense | B-task's full mask (171 scalars), from a random draw, factor 1.0 | 8 |
| P-sel | E's modules frozen; the 13 selector parameters from a random draw, factor 1.0 | 4 |
| P-joint | the engineered seed E + W2, tuned at factor 0.25: E3b-1's T-F cohort, reused and reselected | 8 |

**Champions:** each run's best genome of its final 32 on 128 validation mazes (§6).

**The unit:** d = (the champion's mean visits per wey on the test block − P-fixed's) / P-fixed's mean.

**The references** (test block, visits per wey):

| Reference | Intact | Noses removed | Trails off |
|---|---|---|---|
| P-fixed (the seed E + W2) | 5.118 | 1.473 | 3.602 |
| W2 alone | 1.478 | — | 1.478 |
| W2-turn (resting turn 1.4, chosen on validation) | 5.766 | — | — |
| R-shared (one engineered navigator) | 3.201 | — | — |

**About two of the references:**
- **R-shared** scores 1.92 visits below P-fixed.
- **W2-turn's chosen 1.4 is the grid's upper edge.** Its validation means were still rising (1.2: 5.82; 1.4:
  5.95), so 5.77 may understate what a constant turn bias can do (Fable).

**The run, and its checks:**
- **Every stage completed.**
- **All 28 champions were eligible:** complete training, complete test plays, verified path files. No run failed
  (all above W2 alone + 1).
- **`g-e` passed all its legs:** E3b-1's three registered legs (the CPU equivalence, the maze reference, the GPU
  hashes of E2's batch) and the snapshot hook.
- **Every training run's in-loop checkpoints at generations 0 and 299 equal the post-hoc plays,** in hashes and
  per-maze counts: 40 of 40 checks.

## The primary contrasts (§7.1)

**The champions' mean test visits per wey,** by arm:

| Arm | Range over runs | Mean | SD over runs | Mean d |
|---|---|---|---|---|
| S-mod | 6.62-6.71 | 6.666 | 0.031 | +0.302 |
| S-dense | 6.59-6.80 | 6.714 | 0.070 | +0.312 |
| P-joint | 6.06-8.75 | 7.329 | 0.902 | +0.432 |
| P-sel | 2.67-6.14 | 5.132 | 1.665 | +0.003 |

**The margins:** m_lo = 0.0977 and m_hi = 0.100 in d, about 0.5 visits per wey on P-fixed's 5.118.

**The contrasts:**

| | Q1: S-mod − S-dense | Q2: P-joint − S-mod |
|---|---|---|
| Estimate (d) | −0.0094 | +0.1297 |
| In visits per wey | −0.048 | +0.664 |
| 97.5% Welch interval (d) | [−0.0234, +0.0046] | [−0.0474, +0.3068] |
| In visits per wey | [−0.120, +0.023] | [−0.243, +1.570] |
| **Margin label** | **approximate (model-based): no relevant difference** | **approximate (model-based): unclear** |
| Welch p | 0.106 | 0.076 |
| Holm-adjusted Welch p (beside) | 0.152 | 0.152 |
| Exact permutation test, p | 0.099 | 0.052 |
| **Exact label** (at 0.025) | **no difference detected (exact)** | **no difference detected (exact)** |
| Mann-Whitney p (supplement) | 0.130 | 0.105 |
| Failed runs, and Fisher's p (decomposition) | 0 and 0; 1.0 | 0 and 0; 1.0 |
| Welch 95% among runs that did not fail (decomposition; d) | [−0.0213, +0.0024] | [−0.0177, +0.2771] |
| Maze-paired bootstrap, 95% (supplement; d) | [−0.0130, −0.0062] | [+0.046, +0.214] |
| **Qualifier** (nose classes; coverers) | S-mod 8 nose-independent, 8 of 8; S-dense the same | P-joint 4 partial and 4 nose-dependent, 0 of 8; S-mod 8 nose-independent, 8 of 8 |

**How to read them:**
- **Q1's interval lies inside ±m_lo,** so the registered margin label is "no relevant difference".
  - **Like every margin label, it is approximate.** Its calibration in `power.json` assumes the no-failure model,
    and observing no failed run does not establish that model (§7.1).
  - **One simulated assumption does not hold:** the power analysis gave the S arms a common spread, but S-mod's
    runs spread 0.031 visits and S-dense's 0.070. Separate spreads are a named, unsimulated limit (§8).
- **Q2's interval straddles both 0 and m_hi.**
  - P-joint's runs spread 13 to 29 times more than the S arms' (SD 0.90 against 0.03-0.07 visits).
  - The registered power analysis expected "unclear" unless the true difference was near a visit.
  - "Unclear" is not read as equivalence: the interval allows up to +1.57 visits.
- **The exact test for Q2:** its null, one distribution, was expected to be false on spread alone (§7.1). So its
  p of 0.052 carries no claim about means either way. "No difference detected" does not establish identical
  distributions; the spreads plainly differ.
- **The maze-paired bootstrap** resamples the test mazes for these particular champions. It does not resample
  evolutionary runs, so it cannot resolve the run-to-run uncertainty Q2's label reflects.
  - **For these 16 champions,** P-joint's average lead over S-mod's does not reverse under maze resampling.
  - **Q1's bootstrap interval,** −0.067 to −0.032 in visits, lies on the S-dense side and far inside the margin.

## Nose dependence and the coverage hypothesis (§7.3)

**Per arm**, on the test block. "No material loss" is a bounded-equivalence statement, approximate like every
margin label:

| Arm | Nose classes | Coverers | Paired loss L (visits per wey), 95% t-interval | "No material loss" (approximate) |
|---|---|---|---|---|
| S-mod | 8 nose-independent | 8 of 8 | 0.012 [0.000, 0.024] | yes |
| S-dense | 8 nose-independent | 8 of 8 | 0.002 [−0.005, 0.009] | yes |
| P-sel | 4 nose-independent | 0 of 4 | −0.228 [−0.595, 0.139] | yes |
| P-joint | 4 partial, 4 nose-dependent | 0 of 8 | 3.277 [2.122, 4.431] | no |
| P-fixed | nose-dependent (retained 0.288) | not a coverer | 3.645, bootstrap [3.185, 4.125] | no |

**The details behind the table:**
- **The S champions:**
  - retained fractions 0.995-1.001;
  - coverage 0.990-0.999;
  - tour match 0.988-0.993.
- **P-joint's champions:**
  - retained fractions 0.378-0.842, with runs 2 and 3 keeping 76-84%;
  - coverage 0.872-0.948;
  - tour match 0.148-0.625, with runs 2 and 3 above the coverer threshold of 0.5;
  - noses removed, they score 2.85-5.96 (mean 4.05), against P-fixed's 1.47.
- **The coverage hypothesis** (registered rule, `e3c_stats.coverage_rule`): **"supported"**, with the S arms'
  part "high". Both S arms' coverer shares are 1.0 (≥ 0.75), and P-joint's is 0.0, below both.
- **Nose dependence, directly** (registered, descriptive): P-joint's mean retained fraction minus S-mod's is
  −0.441 [−0.575, −0.307], and minus S-dense's −0.442 [−0.576, −0.308].

**What "noses removed" shows,** as registered:
- **The intervention:** the four A/B nose channels at gain 0, with the relays' occupancy inputs and W2's
  collision left on.
- **A small loss** means the intervention is tolerable, not that the intact controller ignores its noses.

**An exploratory reading** (Fable; not registered): tuning gave P-joint's champions a large nose-free component as
well as their nose use.
- **Noses removed,** they exceed P-fixed by 2.58 visits on average; intact, by 2.21.
- **So "navigation with the noses"** is part of their level, not all of it.

## The cost curve (§7.2; secondary)

**The thresholds,** on the learning-curve block: W2 alone + 1 (2.507) and P-fixed's level (5.313).

| Arm | Reach W2 alone + 1 | Median generation | Reach P-fixed's level | Median generation |
|---|---|---|---|---|
| S-mod | 8 of 8 | 5 | 8 of 8 | 15 |
| S-dense | 8 of 8 | 5 | 8 of 8 | 10 |
| P-sel | 4 of 4 | 87.5 | 3 of 4 | 137.5 |

**Fisher's exact test,** S-mod against S-dense: p = 1.0 for both thresholds (Holm 1.0). No run's curve was
undefined.

**P-joint's curve,** on the same block:
- at index 124: 4.91-6.88;
- at index 299: 6.20-8.36.

The cost curve measures the score, not the strategy: coverer status was assessed on the final champions only.

## Descriptive (§7.4)

**P-sel** (selector-only training):
- **All 4 runs ended above the floor** (W2 alone + 1 = 2.48), at 6.14, 6.14, 5.58 and 2.67.
- **Against P-fixed:** +1.02, +1.03, +0.46 and −2.45 visits. So three of four exceeded P-fixed.
- **Against the S arms:** all four stayed below the lowest S champion (6.59).
- **Against P-joint's mean:** −1.19, −1.19, −1.75 and −4.66 visits.
- **E3a's open arena** saw 1 of 8; the pilot, at 100 generations, saw 1 of 3.
- **The classifications:** all 4 are nose-independent, and none is a registered coverer.
  - **Three are near-perfect circuits** (tour match 0.997-0.998) of 84.5-91.9% of the maze, near W2-turn's
    circuit (tour 1.00, coverage 0.87).
  - **The fourth** (run 23) is neither.
  - **All four score higher with the noses removed,** run 23 by 0.57 visits. Runs 20 and 21 have module A's K_D
    of 12.6 and 7.5. As registered, a small loss with the noses removed does not show that the intact controller
    ignores them.

**The per-maze pattern** (Spearman, per champion):

| Arm | With P-fixed's per-maze visits | With the A-B tree distance |
|---|---|---|
| S arms | −0.05 to 0.11 | −0.02 to 0.04 |
| P-sel | −0.11 to 0.17 | −0.21 to 0.11 |
| P-joint | 0.24 to 0.47 | −0.47 to −0.27 |

P-joint's champions score less where the sources are far apart, as navigators do. The S champions do not.

**Trails off** (visits per wey):
- **the S champions** are unchanged: S-mod 6.59-6.70, S-dense 6.59-6.79;
- **P-sel's** runs 20-22 gain 0.10 each, and run 23 gains 0.52 (2.67 to 3.18, +19%);
- **P-joint's champions** fall to 3.65-5.92 (intact 6.06-8.75), and P-fixed to 3.60 (intact 5.12).

**The secondary outcomes** (means over champions):

| Arm | Legs per wey | Later-leg rate | Unvisited share | Round-trip share |
|---|---|---|---|---|
| S-mod | 5.67 | 2.78 | 0.007 | 0.991 |
| S-dense | 5.72 | 2.79 | 0.004 | 0.994 |
| P-sel | 4.24 | 2.31 | 0.106 | 0.799 |
| P-joint | 6.38 | 3.33 | 0.051 | 0.873 |

**Genomes:**
- **The resting turn offsets:**
  - S arms +0.44 to +0.60;
  - P-sel +0.43 to +0.60;
  - P-joint +0.34 to +0.60.
  - Every arm turned its carrier, and 9 of the 28 champions sit at 0.60, apparently a limit (Fable).
- **Module A's K_D at q = 0:**
  - S arms −0.38 to 0.05, about flat;
  - P-joint 1.7 to 3.8;
  - P-sel 0.0 to 12.6.

## The cost ledger (§11; descriptive)

| Line | GPU-hours | What it bought |
|---|---|---|
| E4s-0 | 0.23 | L1's calibration and diagnostics |
| E4s-1 | 16.6 | L1's confirmatory validation |
| E3a | 5.97 | the selector, E and its gates |
| E3b-0 | 2.62 | W2, the maze-ready additions and the task |
| E3b-1's T-F | 6.44 | P-joint's tuning |
| E3c's pilot, replay and diagnostic | 3.95 | the branch, and the coverage finding |
| E3c's formal stages | 18.70 | the three new arms, the evaluation, the readings |
| — `project` and `g-e` | 0.41 | |
| — S-mod, S-dense, P-sel training | 6.46, 6.53, 3.86 | |
| — `champions`, `evaluate` | 1.15, 0.29 | |

**As §11 registers it:**
- **The categories, kept apart:**
  - **artifact production and selection:** E4s-1, E3a, E3b-0, T-F and E3c's three training stages;
  - **shared infrastructure:** E4s-0, E3c's `project` and `g-e`;
  - **downstream adaptation and validation:** E3c's `champions` and `evaluate`;
  - **unmeasured design and review effort:** the many review rounds, which are not counted in hours, and for
    which no hours are invented.
- **Common costs:** every arm inherits W2, the carrier and the interface, and S-mod inherits E's mask. These are
  common, and not charged to any arm.
- **P-joint's first-use cost** is a range: from 6.7 hours (T-F plus E4s-0) to 31.9 hours (the full lineage, T-F
  included).
- **E3c's incremental cost:** 22.65 hours, apart from that historical cost. The new arms trained at the same
  evaluations per run as T-F, 300 × 32 × 8 maze episodes.
- **The reuse cost, as scenarios only:**
  - **P-sel** reused E's modules for 3.86 hours of training and ended below the from-scratch arms here;
  - **from scratch,** S-mod reached P-fixed's level at a median of 15 generations.
  - Neither is a measured saving from reuse.

## What this does and does not show

**Shown, for this task, these recipes and this test block:**
- **Under one recipe, E's modular mask and a dense controller of the same neurons reach the same level:**
  "approximate (model-based): no relevant difference". All 16 selected champions met the coverer criterion.
- **These eight tuned engineered champions averaged 0.66 visits more than the eight S-mod champions,** with a
  wide spread. The registered reading is "unclear".
  - They use the noses and the trails.
  - They also carry a large nose-free component (exploratory).
- **The coverage hypothesis is supported,** as a registered descriptive classification:
  - every selected champion trained from random weights met the coverer criterion;
  - no tuned engineered champion did.
- **Selector-only training on frozen modules** ended above the floor in 4 of 4 runs, and above P-fixed in 3. It
  stayed below the from-scratch arms, by routes that tolerate the noses' removal but are not full coverers.

**Not shown:**
- **Anything about assembling stereo navigators.** The selected from-scratch champions met the scent-free coverer
  criterion. Whether intact S controllers make any use of their noses is not measured.
- **That the engineered prior is better, or worse.** Q2 is unclear.
- **That a modular mask helps when the task needs navigation.** Q1 compared two training routes that ended in
  circuits.
- **Cumulative reuse savings.**

**For the roadmap** (exploratory; not a registered reading):
- **A question about assembled navigators needs a task where coverage cannot win.**
- **A shorter horizon is one untested idea, and possibly a poor one** (Fable). On E3c's numbers a lap takes
  about 700 ticks, and P-fixed needs about 470 ticks per visit, so a horizon shorter than a lap would leave a
  navigator about one visit. Any such task needs its own validation.
- **E4 would be affected** if it used this task and this score. Its roadmap entry proposes interventions and a
  diagnostic task of its own. The owner has paused before E4.

## Deviations

**None from the bound text, as amended before any formal stage ran:**
- Amendment 1 split the training stage and set out durability and eligibility;
- Amendment 2 recorded the formal code and how a stage stopped by the cap is read.

**Each stage's commit was pushed before its start marker** (Fable checked: 3-191 seconds before).

**Process notes:**
- **The formal code review** took five rounds (D211-D217).
- **Fable was unavailable** for one recheck (session limit, D213). It checked those changes in the next round.
- **GitHub's CPU suite was red from 9d76251 to 265ed2c,** because tests needed `g-e` to pass on Linux. Fixed
  (D218). No formal stage was affected.

## Corrections

The draft of 4b40e43 was corrected before publication, after both reviewers (D220):
- **P-sel.** It said selector-only training "can also reach the from-scratch level here, 3 of 4 runs, by a
  scent-free route". Three of four exceeded P-fixed but stayed below every S champion, and "scent-free" was more
  than the noses-removed reading shows.
- **Q1's bound.** It said "within 0.1 visit per wey"; the interval reaches −0.120.
- **The calibration.** It said that with no failed run the Q1 label "is calibrated under the no-failure model".
  Observing no failure does not establish that model.
- **Similar scores, and P-joint's advantage.** "Similar scores", and "P-joint's advantage does not depend on a few
  mazes", read the unclear Q2 as more than it is.
- **Smaller fixes:**
  - "85-92%" should read 84.5-91.9%;
  - the Holm row was not labelled as Welch-based;
  - the registered qualifier and decomposition were missing;
  - P-sel against P-joint, R-shared against P-fixed and §11's categories were missing;
  - the roadmap note stated the E4 implication too strongly.
