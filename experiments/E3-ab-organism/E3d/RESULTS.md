# E3d: results (draft, for review)

**The verdict, in the bound wording (design §4): "E3d: failed at calibration".** At every k_r (0, 2 and 4), one
criterion failed: **G1b**, the absolute limit on the best scent-free control. The best scent-free control is a
random walk, at 2.34, 2.35 and 2.53 mean visits per wey against the limit of 2.0. Every other criterion and the
oracle's precondition passed at every k_r. By the bound procedure, no k_r was chosen, so the confirmation block,
the 6 × 6 tree reference and the tangent-start diagnostic were not played.

Every number here comes from `calibrate.json`, `report.json` and `compute-record.json` in this folder, through
`scripts/e3d_summary.py` (`summary.json`).

## What was run

- **The design:** `docs/E3/E3d-DESIGN.md` v2.2, bound at 65b77fb (D225). Amendment 1 (the scripted wall-follower's
  search state and probe rays, D226), its correction and erratum (D227, D228) and the code were re-bound at
  202666e. Both reviewers said "run" on the code (`docs/reviews/20261010-E3d-code-3/`).
- **The stages:**
  - `project`: admitted after the first registered reduction, the random walk's grid cut to persistence 0.5 at
    rates 0.5, 1 and 2. The projection was 2.76 h unreduced and 2.38 h reduced, plus 0.25 h reserved, against a
    ceiling of 3.
  - `g-e`: passed (below).
  - `calibrate`: 128 island mazes (ids 30 000-30 127) at each k_r, 41 minutes.
  - `report`.
- **Compute:** 0.81 of 3 GPU-hours (2 905 s timed, 79 747 worlds, 6.7 × 10⁷ world ticks). One `g-e` attempt
  refused in 3 s, before playing anything, because HEAD was not yet pushed. It is in the compute record.

## Rule 7 (g-e)

`g-e` passed (`g-e.json`):
- E3c's legs: the CPU equivalence reference, E2's GPU batch, the snapshot hook and E3b-1's maze reference;
- **the new full-rollout leg:** tree-family maze rollouts of the scripted follower and the seed, at c = 5 and
  c = 6, compared tick by tick with the engine before E3d's code (40bd50f). Identical on the CPU and on the GPU
  (in `replay_mode()`, composition 1 strain × 8 worlds × 8 weys).

Rule 6's scope: the formal plays ran outside `replay_mode()` in their own recorded compositions. The
equivalence leg does not establish exact replay of them. Their per-wey trajectories are kept locally,
`runs/e3d/records/`, hashed in `calibrate.json`.

## The gate on the calibration block

Mean visits per wey (colony means over 128 mazes):

| k_r | shared follower | oracle | seed | B_max (member) | G1a: B_max ÷ follower ≤ 0.25 | G1b: B_max ≤ 2.0 | G2a: follower ÷ oracle ≥ ⅓ | G2b: follower ≥ 4 | G3a: seed − B_max | G3b: seed's median legs ≥ 2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 16.53 | 42.45 | 9.02 | 2.34 (walk, rate 1) | 0.141 ✓ | 2.34 ✗ | 0.389 ✓ | ✓ | 6.68 ≥ 0.90 ✓ | 6.81 ✓ |
| 2 | 15.83 | 42.63 | 9.48 | 2.35 (walk, rate 2) | 0.148 ✓ | 2.35 ✗ | 0.371 ✓ | ✓ | 7.13 ≥ 0.95 ✓ | 7.88 ✓ |
| 4 | 16.49 | 43.02 | 10.57 | 2.53 (walk, rate 1) | 0.154 ✓ | 2.53 ✗ | 0.383 ✓ | ✓ | 8.03 ≥ 1.06 ✓ | 8.69 ✓ |

- **The oracle's precondition held:** every oracle wey made a visit, and the oracle outscored the follower.
- **First-draw feasible share:** 0.80, 0.80 and 0.79, above the floor of 0.5.

## The blind family

Mean visits per wey, k_r = 0 / 2 / 4:

| Member | k_r 0 | k_r 2 | k_r 4 |
|---|---|---|---|
| Random walk, persistence 0.5, rate 0.5 / 1 / 2 | 1.80 / **2.34** / 2.29 | 1.92 / 2.31 / **2.35** | 2.01 / **2.53** / 2.44 |
| W2 (neural) | 1.76 | 1.91 | 1.88 |
| W2-turn, best point (r = 0.4, W2's own resting turn) | 1.76 | 1.91 | 1.88 |
| W2-turn, r ≥ 1.0 (all six points) | 0.00 | 0.00 | 0.00 |
| W2+M40, W2+M80 | 1.70, 1.81 | 1.77, 1.69 | 1.90, 1.79 |
| The seed, noses removed | 1.75 | 1.78 | 1.88 |
| Scripted wall-follower, left and right | 0.01, 0.01 | 0.01, 0.01 | 0.01, 0.01 |
| E3c's S-mod and S-dense champions, noses removed (16) | 0.00 (all 16) | 0.00 (all 16) | 0.00 (all 16) |
| E3c's P-sel champions, noses removed (4) | 0.00-0.26 | 0.00-0.28 | 0.00-0.30 |
| E3c's P-joint champions, noses removed (8) | 0.00-0.55 | 0.00-0.56 | 0.00-0.55 |

Beside them, the follower with trails off makes 2.93, 2.39 and 2.37. It still senses scent, so it is not a
blind control.

**Round trips** (three visits or more; reported, not gated): the random walk's best member completes one for
41%, 42% and 45% of its weys. W2 and W2-turn at r = 0.4 complete one for 27-31%. The shared follower completes
one for 53-58%, and the seed for 90-96%.

## How the G1 failure reads (the design's pre-stated readings)

The failing member is **a random walk**. The design's reading is "the walk reaches the goals; an open or small
maze is one possible explanation", a possibility to check against the records, not an identified cause. The
records show:
- **The walk covers the maze:** its head enters 90%, 92% and 95% of the 36 maze cells' open blocks within the
  horizon, and 89-91% of its weys make at least one visit.
- **It reaches the goals from the perimeter side and from fragments, not by following a ring:**
  - at the moment of a visit, its remembered component is a goal ring in most cases (k_r = 0: 2 230 of
    2 393 visits), as entering the roundabout makes likely;
  - the last component it touched before that ring is most often the perimeter (k_r = 0: 942 + 585 of 2 393
    visits), then a detached fragment (241 + 313);
  - it changes component 36-52 times per 1 000 ticks.
- **The mazes are open:**
  - 69%, 73% and 76% of internal segments are open, against 58% for a tree;
  - goal-to-goal paths are 1.64-1.66 × their Manhattan distance;
  - 8% of spawn-goal pairs are in direct line of sight;
  - each goal has 2.1 entrances on average.

**Not read here:** whether a smaller horizon, a larger maze or fewer openings around the goals would bring the
walk under 2.0. E3d's design does not test it.

## What else the calibration shows (exploratory; not part of the verdict)

- **The construction defeats perimeter-following as designed:** both scripted wall-followers make 0.01 visits
  per wey at every k_r.
- **E3c's 16 from-scratch champions with their noses removed make no visit at all** (0.00 for every one, at every
  k_r). On E3c's 5 × 5 tree mazes, noses removed, they made 6.59-6.79.
  - That is not E3d's prediction: the prediction concerned intact champions against a 6 × 6 tree reference,
    and neither was played.
  - It does not separate the islands from the change of size. The tree reference that would separate them was
    not played.
- **The scent navigators separate from the blind family by large factors:**
  - the shared follower makes 6.5-7.1 × B_max;
  - the seed makes 3.9-4.2 × B_max, with a median of 6.8-8.7 legs;
  - the seed with its noses removed falls to 1.75-1.88, near W2's own score.
- **The scent reach:** 99.6%, 98.4% and 95.7% of goals are flagged as reaching the perimeter track. The per-goal
  split is therefore almost entirely one group.

## What this does and does not show

- **It shows** that this maze family, at the registered thresholds, does not meet E3d's gate. A random walk with
  W1's reflex exceeds the absolute blind limit of 2.0 visits per wey by 0.34-0.53, while staying under a quarter
  of the scent follower's score.
- **It does not show** that the family is unusable for E4. The design states that if E3d fails, "the failed
  criteria say what the next construction must change, and the roadmap stays paused before E4 until the owner
  decides" (§9). G1b is the one that failed.
- **Nothing was tuned on these results.** The verdict follows the bound procedure. Any change to the construction
  or the thresholds needs fresh calibration and confirmation blocks (§4).

## For the owner (not part of the registered result)

The failed criterion points to three directions, none tested here:
- **Reduce random coverage:** a larger maze (c = 7), or a shorter horizon. The horizon change was set aside
  before: it changes the task, and it would apply to E4 too.
- **Keep the goals harder to reach blindly:** fewer openings around each goal. The carved roundabout opens all
  eight ring-road segments.
- **Revisit G1b's absolute level:** with every other criterion passed by wide margins, it is a choice about the
  claim, not a measurement. It cannot rescue E3d's verdict; a future validation would need it fixed in advance.
