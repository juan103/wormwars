# E3e: results

**The verdict, in the bound wording (E3d §4, labelled for E3e): "E3e: failed at calibration".**
- **The failed criteria:** at every k_r (0, 2 and 4), **G2a** and **G1a**.
  - **G2a:** the shared follower made 0.13-0.16 of the oracle's visits, against the required ⅓.
  - **G1a:** the best scent-free control, a random walk, made 0.27-0.32 of the follower's visits, against 0.25.
- **What passed:** **G1b**, the criterion that failed E3d. The walk made 1.50-1.64 visits per wey against the
  limit of 2.0. G2b, G3a, G3b and the oracle's precondition passed too, on the point estimates.
- **What was not played:** by the bound procedure, no k_r was chosen, so the confirmation block, the 7 × 7 tree
  reference and the tangent diagnostic were not played.

**Where the numbers come from:**
- E3e's calibration block: `calibrate.json` and `report.json` in this folder, through
  `scripts/e3d_summary.py --exp E3e` (`summary.json`);
- the projection: `project.json`;
- the equivalence legs: `g-e.json`;
- compute: `compute-record.json`;
- E3d's figures: `experiments/E3-ab-organism/E3d/summary.json` and its `RESULTS.md`.

The report carries each calibration k_r's bootstrap intervals and scent-reach split (E3e §1a, D231's correction
built in).

## What was run

- **The design:** `docs/E3/E3e-DESIGN.md` v2, bound at 79de3a1 (D234). It is E3d's design, pinned by hash,
  unchanged except for c = 7, a fresh seed (1 191 000) and fresh blocks (ids 31 000-31 455).
  - **Its review:** both reviewers reviewed v1 ("revise"). On v2, Fable said "bind". Astra said "revise" with one
    wording change, taken verbatim, without a further check.
- **The stages:**
  - `project`: admitted after the second registered reduction. The random walk's grid was cut to persistence
    0.5, and the W2-turn grid to {−0.8, 0, 0.4, 0.8, 1.2, 1.4, 1.95}; the cut kept W2-turn's best point,
    r = 0.4. The projection was 3.15 h unreduced, 2.75 h after the first reduction and 2.37 h after the second,
    plus 0.25 h reserved, against 3.
  - `g-e`: passed. E3d's legs passed, and the full rollout against 40bd50f was identical on the CPU and the GPU.
    The full-rollout comparisons cover trees at c = 5 and c = 6, the GPU one inside `replay_mode()`. They do not
    establish exact replay of the formal c = 7 plays.
  - `calibrate`: 128 island mazes at each k_r, 34.5 minutes.
  - `report`.
- **Compute:** 0.71 GPU-hours (2 545 s) in the formal attempts' accounting, of 3. The full-rollout compare's
  worlds and ticks are not counted; its wall time is.
- **Rule 6:** the formal plays ran outside `replay_mode()` in their recorded compositions. Their per-wey records
  are kept locally (`runs/e3e/records/`), hashed in `calibrate.json`.
- **The wall-follower's 7 × 7 qualification:** each hand toured all 49 cells of 7 × 7 trees in at least 9 of 10
  (`tests/test_e3d_wall_follower.py`).

## The gate on the calibration block

Mean visits per wey, with 95% bootstrap intervals over the paired mazes (2 000 resamples, seed 20 261 011, B_max
recomputed in each):

| k_r | shared follower | oracle | seed | B_max (member) | G1a: B_max ÷ follower ≤ 0.25 | G1b: B_max ≤ 2.0 | G2a: follower ÷ oracle ≥ ⅓ | G2b: follower ≥ 4 | G3a: seed − B_max | G3b: seed's median legs ≥ 2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 5.52 [4.09, 7.03] | 35.03 | 3.95 [3.46, 4.46] | 1.50 [1.41, 1.59] (walk, rate 2) | 0.271 [0.211, 0.367] ✗ | 1.50 ✓ | 0.158 [0.118, 0.197] ✗ | ✓ | 2.45 [1.98, 2.96] ≥ 0.50 ✓ | 2.31 [1.94, 2.63] ✓ |
| 2 | 4.72 [3.33, 6.22] | 35.27 | 4.21 | 1.51 (walk, rate 2) | 0.320 [0.244, 0.461] ✗ | 1.51 ✓ | 0.134 [0.095, 0.174] ✗ | ✓ | 2.70 ✓ | 2.75 [2.38, 3.13] ✓ |
| 4 | 5.61 [4.06, 7.28] | 35.55 | 4.41 | 1.64 (walk, rate 1) | 0.292 [0.224, 0.401] ✗ | 1.64 ✓ | 0.158 [0.116, 0.202] ✗ | ✓ | 2.78 ✓ | 2.63 [2.25, 3.00] ✓ |

`summary.json` holds every quantity's interval at every k_r.
- **G2a's intervals lie wholly below ⅓** at every k_r.
- **G1a's point estimates fail the registered gate,** which alone would disqualify a k_r. Its intervals cross
  0.25, which limits inference beyond this block.
- **G2b and G3b passed on point estimates,** but their intervals reach below the thresholds in places:
  - the follower's interval at k_r = 2 crosses G2b's floor of 4;
  - the seed's median legs at k_r = 0 reach 1.94.
- **The oracle's precondition held:** every oracle wey made a visit.
- **First-draw feasible share:** 0.71, 0.70 and 0.69.

## How the G2a failure reads (E3e §1a's pre-stated reading)

The reading, as bound: "A G2a failure means the shared scripted follower falls below the required one-third of
oracle throughput on this block. Increased discovery cost associated with fixed scent reach and trail decay is a
possible explanation, to check against discovery, scent-reach, no-first-visit and later-leg records—not an
identified cause. Blind-control performance is assessed separately by G1."

The four records it names (`summary.json`; E3d's beside them, k_r = 0 / 2 / 4):

| Record (the shared follower) | E3d, c = 6 | E3e, c = 7 |
|---|---|---|
| Discovery: median over mazes of the censored median first-entry tick, A | 169 / 150 / 133 (6, 16, 9 mazes not reached) | 249 / 201 / 208 (19, 14, 14 not reached) |
| Discovery: the same for B | 324 / 354 / 333 (51, 50, 46 not reached) | 605 / 738 / 600 (71, 82, 68 not reached) |
| Share of weys reaching A, and B | 0.95, 0.65 / 0.90, 0.64 / 0.93, 0.67 | 0.84, 0.47 / 0.87, 0.41 / 0.85, 0.48 |
| No first visit | 0.05 / 0.10 / 0.08 | 0.16 / 0.13 / 0.15 |
| Later-leg rate (legs per 1 000 ticks after the first visit, over weys with one) | 7.15 / 7.04 / 7.37 | 2.33 / 1.92 / 2.31 |

- **"Not reached" mazes** are those where E3c's censored median touches a censored wey; the medians are over the
  others.
- **The scent-reach split:**
  - **too few unflagged goals to read:** only 5, 9 and 11 of 256 goals are unflagged;
  - **arrival on flagged goals against unflagged:** 0.65 against 0.58 (k_r = 0), 0.64 against 0.74 (2), 0.66
    against 0.72 (4). Arrival is the mean share of weys reaching a goal;
  - **visits per maze:** in mazes with an unflagged goal, the follower made 4.8, 14.1 and 12.3, against 5.5, 4.0
    and 5.0 in mazes with both flagged;
  - **so** the split shows no consistent direction, and it does not identify scent reach as the cause. The flag
    is a geometric proxy (E3d §2).
- **So:** the follower takes longer to find the goals and completes fewer later legs within the horizon than at
  6 × 6. These records are consistent with the pre-stated possible explanation; they do not identify the cause.

**G1a** fails arithmetically because the follower's score fell. B_max itself fell, from 2.34-2.53 to 1.50-1.64.
That describes the change; it is not a causal account.

## The blind family (k_r = 0; the other k_r alike, `summary.json`)

| Member | Mean visits per wey |
|---|---|
| Random walk, persistence 0.5, rate 0.5 / 1 / 2 | 1.11 / 1.44 / **1.50** |
| W2; W2-turn's best point (r = 0.4) | 1.07; 1.07 |
| W2+M40, W2+M80 | 1.10, 1.00 |
| The seed, noses removed | 1.05 |
| Scripted wall-follower, left and right | 0.01, 0.00 (8 and 2 visits in 1 024 weys) |
| E3c's S-mod and S-dense champions, noses removed (16) | 0.00 (S-mod 1 visit in total, S-dense none) |
| E3c's P-sel champions, noses removed (4) | 0.00-0.19 (194 visits in total) |
| E3c's P-joint champions, noses removed (8) | 0.00-0.38 (the best champion 394 visits) |

- **This is the blind family E3e actually played,** at its projected reductions. Its maximum does not bound every
  possible blind strategy (E3e §1a).
- **The random walk covers 77-83% of the maze cells** within the horizon (E3d: 90-95%). 19-22% of its weys
  complete a round trip (E3d: 41-45%).
- **The mazes:** 65-70% of internal segments are open; goal-to-goal paths are 1.59-1.61 × their Manhattan
  distance; 6-7% of spawn-goal pairs are in direct line of sight.
- **Where the rest is:** §6's other records (discovery, occupancy, contact, switches) are in `calibrate.json` per
  strain and maze. The per-wey arrays are in `runs/e3e/records/`.

## Against E3d at 6 × 6 (exploratory; separate blocks)

This comparison is descriptive. The two calibrations used different seeds and mazes, size-dependent placement
and acceptance rules, and different W2-turn grids (E3d its first reduction, E3e its second). It does not isolate
a mechanism. B_max is each block's own maximum; E3d's winner at k_r = 0 was the walk at rate 1, and E3e's the
walk at rate 2. Both settings were played in both.

| | E3d, c = 6 (k_r 0 / 2 / 4) | E3e, c = 7 (k_r 0 / 2 / 4) |
|---|---|---|
| Shared follower | 16.53 / 15.83 / 16.49 | 5.52 / 4.72 / 5.61 |
| Oracle | 42.45 / 42.63 / 43.02 | 35.03 / 35.27 / 35.55 |
| Seed | 9.01 / 9.48 / 10.57 | 3.95 / 4.21 / 4.41 |
| B_max (a random walk) | 2.34 / 2.35 / 2.53 | 1.50 / 1.51 / 1.64 |
| The follower with trails off | 2.93 / 2.39 / 2.37 | 1.55 / 1.52 / 1.48 |

From 6 × 6 to 7 × 7, scores fell by:
- the oracle, 17%, to 0.83 ×;
- the random walk, 35-36%, to 0.64-0.65 ×;
- the seed, 56-58%;
- the shared follower, 66-70%.

E3e §1a's lap arithmetic predicted about 0.73 × for a lap-coverer from size alone.

**With trails off, the follower now sits at or below the random walk:** 1.55, 1.52 and 1.48, against B_max's
1.50, 1.51 and 1.64. At 6 × 6, scent alone barely beat the walk; at 7 × 7 it does not. What separates the
navigators from the blind family here is the shared trails.

## What this does and does not show

- **It shows:** at 7 × 7 and a horizon of 2 400 ticks, this family fails E3d's gate in the other direction from
  6 × 6. The blind walk is under the absolute limit, but the scent navigators fall below a third of the oracle,
  and the walk exceeds a quarter of the follower.
- **It does not show** why the follower slows. The pre-stated reading names a possible explanation; the records
  are consistent with it and do not identify it.
- **Nothing was tuned on these results.**

## For the owner (not part of the registered result)

**E3d and E3e together:** at 6 × 6 a random walk scores too well, and at 7 × 7 the scent follower scores too
little, both within 2 400 ticks. Possible next directions, all untested; none is a demonstrated remedy:
- **7 × 7 with a longer horizon:** the follower's discovery and shuttling get more time, but so does the walk's
  coverage. G2b and G3b were within their intervals of failing too, so this is not merely a G2a fix. It changes
  the task E4 inherits.
- **6 × 6 with a shorter horizon:** the converse.
- **Strengthen the navigators' signal at 7 × 7:** the scent's reach or the trails' persistence. With trails off
  the follower no longer beats the walk, so the trails carry the separation. Either change alters the task.
- **Use one of the two families for E4 as it is,** with its blind and navigator references reported. Neither
  passed E3d's gate; choosing one would be a new task-design decision, not a rehabilitation of either verdict.
- **Stop maze validation here** and decide E4's direction otherwise.

Any revised validation needs its criteria fixed in advance and fresh blocks.

## Corrections before publication (the results review, D236)

Both reviewers ("fix then publish"; `docs/reviews/20261011-E3e-results/`) found the following in the draft at
bd9c869. Each was corrected here:
- **The follower's k_r = 0 interval:** "7.04" should read 7.03.
- **"Not decisive on its own" for G1a** was ambiguous: a G1a failure alone disqualifies a k_r.
- **The scent-reach split:**
  - it was reported at k_r = 0 only, the one k_r whose direction suited the sentence;
  - "does not separate arrival" was too strong;
  - "reached 65% of flagged goals" misdescribed a mean share of weys.

  All three k_r are now given, with no consistent direction.
- **The G2a discussion** used the no-visit and round-trip shares in place of the records the bound reading names.
  The discovery medians and the later-leg rates are now given, beside E3d's.
- **G2b's and G3b's intervals** reaching below their thresholds were not stated.
- **The trail-free follower** at or below the walk was not reported.
- **P-sel's and P-joint's noses-removed champions** were missing from the blind family, and so was the caveat
  that the family does not bound every blind strategy.
- **The E3d comparison** is now labelled descriptive across separate blocks, with its unpaired features named.
- **E3d's files** were missing from the sources. Rule 6's scope and the equivalence leg's c = 5 and c = 6 scope
  were not stated.
- **"Both reviewers agreed it"** overstated D234.

## Correction (2026-10-11, after publication; D237; Astra)

"With trails off, the follower now sits **at or below** the random walk: 1.55, 1.52 and 1.48, against B_max's
1.50, 1.51 and 1.64" is literally wrong at k_r = 0 and 2: 1.554 > 1.495 and 1.520 > 1.513. It should read: **the
trail-free follower is at about the random walk's level** (slightly above it at k_r = 0 and 2, below at 4). Astra's
paired bootstrap intervals for those differences cross zero, so there is no demonstrated reliable advantage. The
conclusion that the shared trails carry the separation at 7 × 7 stands.

## Correction (2026-10-11, after publication; D241; Astra's review of E3f)

**The discovery table's parenthetical counts** ("6, 16, 9 mazes not reached" for E3d, "19, 14, 14 not reached" for
E3e, and the same for B) are **mazes whose colony median first-entry tick is censored**: at most half the colony's
weys reached the goal (E3c's censored median). They are not mazes that no wey reached.

**The mazes with no arrival at all** for the shared follower (`summary.json`, `mazes_with_no_arrival`):

| | E3d | E3e |
|---|---|---|
| A, at k_r = 0 / 2 / 4 | 0 / 1 / 2 | 3 / 3 / 3 |
| B, at k_r = 0 / 2 / 4 | 30 / 23 / 19 | 30 / 41 / 35 |

The medians shown are over the mazes whose colony median is not censored. The reading (longer discovery at 7 × 7)
is unchanged.
