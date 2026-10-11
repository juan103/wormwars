# E3e: results (draft, for review)

**The verdict, in the bound wording (E3d §4, labelled for E3e): "E3e: failed at calibration".**
- **The failed criteria:** at every k_r (0, 2 and 4), **G2a** and **G1a**.
  - **G2a:** the shared follower made 0.13-0.16 of the oracle's visits, against the required ⅓.
  - **G1a:** the best scent-free control, a random walk, made 0.27-0.32 of the follower's visits, against 0.25.
- **What passed:** **G1b**, the criterion that failed E3d. The walk made 1.50-1.64 visits per wey against the
  limit of 2.0. G2b, G3a, G3b and the oracle's precondition passed too.
- **What was not played:** by the bound procedure, no k_r was chosen, so the confirmation block, the 7 × 7 tree
  reference and the tangent diagnostic were not played.

**Where the numbers come from:**
- the calibration block's numbers: `calibrate.json` and `report.json`, through
  `scripts/e3d_summary.py --exp E3e` (`summary.json`);
- the projection: `project.json`;
- the equivalence legs: `g-e.json`;
- compute: `compute-record.json`.

The report now carries each calibration k_r's bootstrap intervals and scent-reach split, D231's correction built
in (E3e §1a).

## What was run

- **The design:** `docs/E3/E3e-DESIGN.md` v2, bound at 79de3a1 (D234). It is E3d's design, pinned by hash,
  unchanged except for c = 7, a fresh seed (1 191 000) and fresh blocks (ids 31 000-31 455). Both reviewers
  agreed it, after two rounds.
- **The stages:**
  - `project`: admitted after the second registered reduction: the random walk's grid to persistence 0.5; the
    W2-turn grid to {−0.8, 0, 0.4, 0.8, 1.2, 1.4, 1.95}. The projection was 3.15 h unreduced and 2.37 h reduced,
    plus 0.25 h reserved, against 3.
  - `g-e`: passed. E3d's legs, and the full rollout against 40bd50f on the CPU and the GPU, were identical.
  - `calibrate`: 128 island mazes at each k_r, 34 minutes.
  - `report`.
- **Compute:** 0.71 GPU-hours in the formal attempts' accounting, of 3. The full-rollout compare's worlds and
  ticks are not counted; its wall time is.
- **The wall-follower's 7 × 7 qualification:** each hand toured all 49 cells of 7 × 7 trees in at least 9 of 10
  (`tests/test_e3d_wall_follower.py`).

## The gate on the calibration block

Mean visits per wey, with 95% bootstrap intervals over the paired mazes (2 000 resamples, seed 20 261 011, B_max
recomputed in each):

| k_r | shared follower | oracle | seed | B_max (member) | G1a: B_max ÷ follower ≤ 0.25 | G1b: B_max ≤ 2.0 | G2a: follower ÷ oracle ≥ ⅓ | G2b: follower ≥ 4 | G3a: seed − B_max | G3b: seed's median legs ≥ 2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 5.52 [4.09, 7.04] | 35.03 | 3.95 [3.46, 4.46] | 1.50 [1.41, 1.59] (walk, rate 2) | 0.271 [0.211, 0.367] ✗ | 1.50 ✓ | 0.158 [0.118, 0.197] ✗ | ✓ | 2.45 [1.98, 2.96] ≥ 0.50 ✓ | 2.31 [1.94, 2.63] ✓ |
| 2 | 4.72 | 35.27 | 4.21 | 1.51 (walk, rate 2) | 0.320 [0.244, 0.461] ✗ | 1.51 ✓ | 0.134 [0.095, 0.174] ✗ | ✓ | 2.70 ✓ | 2.75 ✓ |
| 4 | 5.61 | 35.55 | 4.41 | 1.64 (walk, rate 1) | 0.292 [0.224, 0.401] ✗ | 1.64 ✓ | 0.158 [0.116, 0.202] ✗ | ✓ | 2.78 ✓ | 2.63 ✓ |

`summary.json` holds every quantity's interval at every k_r.
- **G2a's intervals lie wholly below ⅓** at every k_r.
- **G1a's intervals cross 0.25** at every k_r. Its failure is on the point estimates, the gate's rule, and is
  not decisive on its own.
- **The oracle's precondition held:** every oracle wey made a visit.
- **First-draw feasible share:** 0.71, 0.70 and 0.69.
- **G2b and G3b pass narrowly:**
  - the follower's 4.72 at k_r = 2 is close to G2b's floor of 4;
  - G3b's interval at k_r = 0 reaches below 2.

## Against E3d at 6 × 6

E3d played its first reduction, E3e its second. The rows below are members both played.

| | E3d, c = 6 (k_r 0 / 2 / 4) | E3e, c = 7 (k_r 0 / 2 / 4) |
|---|---|---|
| Shared follower | 16.53 / 15.83 / 16.49 | 5.52 / 4.72 / 5.61 |
| Oracle | 42.45 / 42.63 / 43.02 | 35.03 / 35.27 / 35.55 |
| Seed | 9.01 / 9.48 / 10.57 | 3.95 / 4.21 / 4.41 |
| B_max (a random walk) | 2.34 / 2.35 / 2.53 | 1.50 / 1.51 / 1.64 |
| The follower with trails off | 2.93 / 2.39 / 2.37 | 1.55 / 1.52 / 1.48 |

From 6 × 6 to 7 × 7:
- the oracle lost 17%;
- the random walk lost about 36%;
- the shared follower lost 66-70%, and the seed 56-58%.

The scent navigators lost far more than the blind walk.

## How the G2a failure reads (E3e §1a's pre-stated reading)

The reading, as bound: "A G2a failure means the shared scripted follower falls below the required one-third of
oracle throughput on this block. Increased discovery cost associated with fixed scent reach and trail decay is a
possible explanation, to check against discovery, scent-reach, no-first-visit and later-leg records—not an
identified cause. Blind-control performance is assessed separately by G1."

The records to check it against (`summary.json`):
- **Discovery:** 13-16% of the follower's weys made no visit at all, against 5-10% at 6 × 6.
- **The scent-reach flag does not separate arrival:** 96-98% of goals are flagged as reaching the perimeter
  track. At k_r = 0 the follower reached 65% of flagged goals, and 58% of the 2.0% unflagged.
- **Round trips:** 23-27% of the follower's weys completed one, against 53-58% at 6 × 6. Its weys that do find
  the goals shuttle less within the horizon.

So the records are consistent with longer discovery and slower shuttling within the fixed horizon. They do not
identify the cause.

**G1a** fails because the follower's score fell, not because the blind controls rose. B_max fell from 2.34-2.53
to 1.50-1.64.

## The blind family, and what else the calibration shows (exploratory)

- **The blind family** (k_r = 0):
  - **the random walk:** 1.11 / 1.44 / 1.50 at rates 0.5 / 1 / 2;
  - **W2, and W2-turn's best point (r = 0.4):** 1.07;
  - **W2+M40 and W2+M80:** 1.10 and 1.00;
  - **the seed, noses removed:** 1.05;
  - **the wall-followers:** 0.01 and 0.00, that is 8 and 2 visits in 1 024 weys;
  - **E3c's S champions, noses removed:** S-mod's 8 made 1 visit in total, S-dense's 8 none.

  The other k_r are alike (`summary.json`).
- **The random walk covers 77-83% of the maze cells,** against 90-95% at 6 × 6. 19-22% of its weys complete a
  round trip, against 41-45%.
- **The mazes:** 65-70% of internal segments are open; goal-to-goal paths are 1.59-1.61 × their Manhattan
  distance; 6-7% of spawn-goal pairs are in direct line of sight.

## What this does and does not show

- **It shows:** at 7 × 7 and a horizon of 2 400 ticks, this family fails E3d's gate in the other direction from
  6 × 6. The blind walk is now under the absolute limit. But the scent navigators fall below a third of the
  oracle, and the walk exceeds a quarter of the follower.
- **It does not show** why the follower slows. The pre-stated reading names a possible explanation only.
- **Nothing was tuned on these results.**

## For the owner (not part of the registered result)

**E3d and E3e together:** at 6 × 6 a random walk scores too well, and at 7 × 7 the scent follower scores too
little, both within 2 400 ticks. No construction or threshold was tested beyond these two. Possible next
directions, all untested:
- **7 × 7 with a longer horizon:** the follower's discovery and shuttling get more time, but so does the walk's
  coverage. It changes the task E4 inherits.
- **6 × 6 with a shorter horizon:** the converse.
- **Strengthen the navigators' signal** at 7 × 7 (the scent's reach or the trails' persistence). That changes the
  task.
- **Use one of the two families for E4 as it is,** with its blind and navigator references reported. Neither
  passed E3d's gate.
- **Stop maze validation here** and decide E4's direction otherwise.
