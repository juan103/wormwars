# E3c results: the assembly comparison in the maze shuttle (2026-10-06)

**Status:** draft, for review by both reviewers.

**The registration:**
- the pre-registration is bound at 69d7cd5, with Amendment 1 and Amendment 2 (§14);
- the formal code is at 3cb35fb;
- the run used 22.65 of E3c's 30 GPU-hours.

**Every number below** is from the committed records in this folder: `report.json`, `evaluate.json`,
`champions.json`, the training records and `compute-record.json`.

**The labels:**
- **registered:** labels that come from the pre-registration's rules. They are quoted as the code emits them;
- **descriptive:** everything else.

## In brief

**Q1, modular against dense, both trained from random weights:**
- **The margin reading** (approximate, model-based): **"no relevant difference"**.
- **The exact test:** **"no difference detected"** (p = 0.099).
- **What it means:** E's modular mask and the dense controller of the same 11 neurons end at the same level,
  within 0.1 visit per wey.

**Q2, the engineered start plus its tuning recipe (P-joint) against E's mask from scratch (S-mod):**
- **The margin reading:** **"unclear"**. P-joint is ahead by 0.66 visits per wey (+0.13 of the seed's mean), but
  its 97.5% interval runs from −0.24 to +1.57 visits.
- **The exact test:** **"no difference detected"** (p = 0.052, against 0.025).
- **The registered expectation** ("engineered initialization better") is neither confirmed nor refuted.

**The coverage hypothesis** (a registered descriptive classification): **"supported"**.
- **The from-scratch champions** are scent-free coverers, all 16 of them. They keep 99.5-100.1% of their visits
  with the noses removed, and repeat a circuit of the whole tree.
- **P-joint's champions** are none: 0 of 8. They lose 3.3 visits per wey without their noses, and their scores
  follow the maze's geometry.
- **The two routes reach similar scores by different strategies.**

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

**The run, and its checks:**
- **Every stage completed.**
- **All 28 champions were eligible:** complete training, complete test plays, verified path files. No run failed
  (all above W2 alone + 1).
- **`g-e` passed all four legs.**
- **Every training run's in-loop checkpoints at generations 0 and 299 equal the post-hoc plays,** in hashes and
  per-maze counts: 40 of 40 checks.

## The primary contrasts (§7.1)

**The champions' mean test visits per wey,** by arm:

| Arm | Runs | Mean | SD over runs | Mean d |
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
| Exact permutation test, p | 0.099 | 0.052 |
| **Exact label** (at 0.025) | **no difference detected (exact)** | **no difference detected (exact)** |
| Holm-adjusted p (beside) | 0.152 | 0.152 |
| Mann-Whitney p (supplement) | 0.130 | 0.105 |
| Failed runs | 0 and 0 | 0 and 0 |
| Maze-paired bootstrap, 95% (supplement) | [−0.0130, −0.0062] | [+0.046, +0.214] |

**How to read them:**
- **Q1's interval lies inside ±m_lo,** so the registered margin label is "no relevant difference". With no
  failed run, that label is calibrated under the no-failure model of `power.json`.
- **Q2's interval straddles both 0 and m_hi.** P-joint's runs spread 13 to 29 times more than the S arms' (SD
  0.90 against 0.03-0.07 visits), and the registered power analysis expected "unclear" unless the true
  difference was near a visit.
- **The exact test for Q2:** its null, one distribution, was expected to be false on spread alone (§7.1), so its
  p of 0.052 carries no claim about means either way.
- **The maze-paired bootstrap** varies only the mazes, not the runs, so its intervals are narrower than the
  registered ones. It is a supplement and gives no label.
  - **For Q2,** its interval excludes 0: P-joint's advantage does not depend on a few mazes.
  - **For Q1,** it excludes 0 on the S-dense side by about 0.05 visits. That is far inside the margin.

## Nose dependence and the coverage hypothesis (§7.3)

**Per arm**, on the test block:

| Arm | Nose classes | Coverers | Paired loss L (visits per wey), 95% t-interval | "No material loss" |
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
  - retained fractions 0.378-0.842;
  - coverage 0.872-0.948;
  - tour match 0.148-0.625.
- **The coverage hypothesis** (registered rule, `e3c_stats.coverage_rule`): **"supported"**. Both S arms' coverer
  shares are 1.0 (≥ 0.75), and P-joint's is 0.0, below both.
- **Nose dependence, directly** (descriptive): P-joint's mean retained fraction minus S-mod's is −0.441
  [−0.575, −0.307], and minus S-dense's −0.442 [−0.576, −0.308].

**What "noses removed" shows,** as registered:
- **The intervention:** the four A/B nose channels at gain 0, with the relays' occupancy inputs and W2's
  collision left on.
- **A small loss** means the intervention is tolerable, not that the intact controller ignores its noses.

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

## Descriptive (§7.4)

**P-sel** (selector-only training):
- **All 4 runs ended above the floor:** 6.14, 6.14, 5.58 and 2.67 against W2 alone + 1 = 2.48. Against P-fixed
  they are +1.02, +1.03, +0.46 and −2.45 visits.
- **E3a's open arena** saw 1 of 8; the pilot, at 100 generations, saw 1 of 3.
- **All 4 are nose-independent.** None is a registered coverer:
  - three are near-perfect circuits (tour match 0.997-0.998) of 85-92% of the maze, like W2-turn's circuit
    (tour 1.00, coverage 0.87);
  - the fourth (run 23) is neither.

**The per-maze pattern** (Spearman, per champion):

| Arm | With P-fixed's per-maze visits | With the A-B tree distance |
|---|---|---|
| S arms | −0.05 to 0.11 | −0.02 to 0.04 |
| P-sel | −0.11 to 0.17 | −0.21 to 0.11 |
| P-joint | 0.24 to 0.47 | −0.47 to −0.27 |

P-joint's champions score less where the sources are far apart, as navigators do. The S champions do not.

**Trails off** (visits per wey):
- the S champions are unchanged: S-mod 6.59-6.70, S-dense 6.59-6.79;
- P-sel is about unchanged: 3.18-6.25;
- P-joint's champions fall to 3.65-5.92 (intact 6.06-8.75), and P-fixed to 3.60 (intact 5.12).

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

  Every arm turned its carrier.
- **Module A's K_D at q = 0:**
  - S arms −0.38 to 0.05, about flat;
  - P-joint 1.7 to 3.8;
  - P-sel 0.0 to 12.6.

## The cost ledger (§11; descriptive)

| Line | GPU-hours |
|---|---|
| E3c's pilot, replay and diagnostic | 3.95 |
| E3c's formal stages | 18.70 |
| — `project` and `g-e` | 0.41 |
| — S-mod, S-dense, P-sel training | 6.46, 6.53, 3.86 |
| — `champions`, `evaluate` | 1.15, 0.29 |
| **E3c in all** | **22.65 of 30** |
| P-joint's first-use cost (reused, not run here) | 6.7 (T-F plus E4s-0) to 31.9 (the full lineage) |

**Equal training:** each new arm trained at the same evaluations per run as T-F, 300 × 32 × 8 maze episodes.

**Reaching P-fixed's level:**
- from scratch, median generation 10-15;
- with P-sel's selector only, 137.5.

## What this does and does not show

**Shown, for this task, these recipes and this test block:**
- **Under one recipe, E's modular mask and a dense controller of the same neurons reach the same level** ("no
  relevant difference"). Both reach it as scent-free coverers.
- **The tuned engineered organisms reach a level about 0.66 visits higher on average,** with a wide spread, by
  navigating with their noses and the trails. The registered reading is "unclear".
- **The coverage hypothesis holds:** evolution from random weights found a scent-free circuit every time, and
  quickly. The engineered and tuned organisms never did.
- **Selector-only training on frozen modules can also reach the from-scratch level here,** 3 of 4 runs, by a
  scent-free route.

**Not shown:**
- **Anything about assembling stereo navigators.** The from-scratch arms did not navigate.
- **That the engineered prior is better, or worse.** Q2 is unclear.
- **That a modular mask helps when the task needs navigation.** Q1 compared two routes to a circuit.
- **Cumulative reuse savings.**

**For the roadmap** (not a registered reading): a question about assembled navigators needs a task where
coverage cannot win, for example a horizon too short for a lap of the tree. E4, which asks whether two navigation
modules share information, is affected the same way. The owner has paused before E4.

## Deviations

**None from the bound text, as amended before any formal stage ran:**
- Amendment 1 split the training stage and set out durability and eligibility;
- Amendment 2 recorded the formal code and how a stage stopped by the cap is read.

**Process notes:**
- **The formal code review** took five rounds (D211-D217).
- **Fable was unavailable** for one recheck (session limit, D213). It checked those changes in the next round.
- **GitHub's CPU suite was red from 9d76251 to 265ed2c,** because tests needed `g-e` to pass on Linux. Fixed
  (D218). No formal stage was affected.
