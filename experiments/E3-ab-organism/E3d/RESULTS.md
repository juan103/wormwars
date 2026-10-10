# E3d: results

**The verdict, in the bound wording (design §4): "E3d: failed at calibration".**
- **The failed criterion:** at every k_r (0, 2 and 4), one criterion failed, **G1b**, the absolute limit on the
  best scent-free control. The best scent-free control was a random walk, at 2.34, 2.35 and 2.53 mean visits per
  wey against the limit of 2.0.
- **Everything else passed** at every k_r, on this calibration block's point estimates: the other criteria and
  the oracle's precondition.
- **What was not played:** by the bound procedure, no k_r was chosen, so the confirmation block, the 6 × 6 tree
  reference and the tangent-start diagnostic were not played. They are not missing work.

**Where the numbers come from:**
- the calibration block's numbers: `calibrate.json` and `report.json`, through `scripts/e3d_summary.py`
  (`summary.json`);
- the projection: `project.json`;
- the equivalence legs: `g-e.json`;
- compute: `compute-record.json`;
- E3c's earlier figures: E3c's committed records, cited where used.

`summary.json` also holds three analyses the report stage does not compute when calibration fails, added after
the results review (D231): the bootstrap intervals, the scent-reach split and the exact counts.

## What was run

- **The design:** `docs/E3/E3d-DESIGN.md` v2.2, bound at 65b77fb (D225). Amendment 1 (the scripted wall-follower's
  search state and probe rays, D226), its correction and erratum (D227, D228) and the code were re-bound at
  202666e. Both reviewers said "run" on the code (`docs/reviews/20261010-E3d-code-3/`).
- **The stages:**
  - `project`: admitted after the first registered reduction, the random walk's grid cut to persistence 0.5 at
    rates 0.5, 1 and 2. The projection was 2.76 h unreduced and 2.38 h reduced, plus 0.25 h reserved, against a
    ceiling of 3.
  - `g-e`: passed (below).
  - `calibrate`: 128 island mazes (ids 30 000-30 127) at each k_r.
  - `report`.
- **Compute:** 0.81 GPU-hours in the formal attempts' accounting, of 3 (2 905 s timed; 79 747 worlds;
  6.7 × 10⁷ world ticks).
  - One `g-e` attempt was refused before playing anything, because HEAD was not yet pushed. It is listed in the
    compute record.
  - The full-rollout compare ran as a subprocess. Its wall time counts in `g-e`'s seconds; its worlds, ticks and
    neural updates are not counted (`g-e.json`).

## Rule 7 (g-e)

`g-e` passed (`g-e.json`):
- E3c's legs: the CPU equivalence reference, E2's GPU batch, the snapshot hook and E3b-1's maze reference;
- **the new full-rollout leg:** tree-family maze rollouts of the scripted follower and the seed, at c = 5 and
  c = 6, compared tick by tick with the engine before E3d's code (40bd50f). Identical on the CPU and on the GPU
  (in `replay_mode()`, composition 1 strain × 8 worlds × 8 weys).

Rule 6's scope: the formal plays ran outside `replay_mode()` in their own recorded compositions. The
equivalence leg does not establish exact replay of them. Their per-wey trajectories are kept locally in
`runs/e3d/records/`, hashed in `calibrate.json`.

## The gate on the calibration block

Mean visits per wey (colony means over 128 mazes), with 95% bootstrap intervals over the paired mazes (2 000
resamples, seed 20 261 011, B_max recomputed in each resample; `summary.json`):

| k_r | shared follower | oracle | seed | B_max (member) | G1a: B_max ÷ follower ≤ 0.25 | G1b: B_max ≤ 2.0 | G2a: follower ÷ oracle ≥ ⅓ | G2b: follower ≥ 4 | G3a: seed − B_max | G3b: seed's median legs ≥ 2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 16.53 [13.54, 19.64] | 42.45 | 9.01 [8.09, 9.88] | 2.34 [2.21, 2.47] (walk, rate 1) | 0.141 [0.121, 0.171] ✓ | 2.34 ✗ | 0.389 [0.327, 0.452] ✓ | ✓ | 6.68 [5.79, 7.48] ≥ 0.90 ✓ | 6.81 [5.50, 7.88] ✓ |
| 2 | 15.83 [12.82, 18.98] | 42.63 | 9.48 [8.63, 10.31] | 2.35 [2.22, 2.50] (walk, rate 2) | 0.148 [0.125, 0.181] ✓ | 2.35 ✗ | 0.371 [0.307, 0.437] ✓ | ✓ | 7.13 [6.33, 7.90] ≥ 0.95 ✓ | 7.88 [6.88, 8.69] ✓ |
| 4 | 16.49 [13.41, 19.56] | 43.02 | 10.57 [9.68, 11.44] | 2.53 [2.39, 2.69] (walk, rate 1) | 0.154 [0.131, 0.185] ✓ | 2.53 ✗ | 0.383 [0.319, 0.446] ✓ | ✓ | 8.03 [7.21, 8.86] ≥ 1.06 ✓ | 8.69 [7.69, 9.81] ✓ |

- **The gate is acceptance on the block's point estimates** (design §5); the intervals are reported, not gated.
  - **B_max's intervals lie wholly above 2.0** at every k_r. The G1b failure is not a rounding accident.
  - **Every G2a interval crosses ⅓.** That does not change its registered pass, but G2a passed narrowly.
- **The oracle's precondition held:** every oracle wey made a visit (the interval is [1.00, 1.00]), and the
  oracle outscored the follower.
- **First-draw feasible share:** 0.80, 0.80 and 0.79, above the floor of 0.5.

## The blind family

Mean visits per wey, k_r = 0 / 2 / 4 (rounded to two decimals; exact counts below):

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

**Exact counts** (visits over 1 024 weys per member; `summary.json`):
- **S-mod's 8 champions, noses removed:** 5, 2 and 0 visits in total at k_r = 0, 2 and 4. Four champions
  contributed the 5, one the 2. Every one was a single visit: no leg was completed.
- **S-dense's 8 champions:** 0 visits.
- **The scripted wall-followers:** 8 to 15 visits each, and no round trip.

**Round trips** (three visits or more; reported, not gated):
- the random walk's best member completes one for 41%, 42% and 45% of its weys;
- W2 and W2-turn at r = 0.4: 28-31%;
- the shared follower: 53-58%;
- the seed: 90-96%.

## How the G1 failure reads (the design's pre-stated readings)

The failing member is **a random walk**. The design's reading is "the walk reaches the goals; an open or small
maze is one possible explanation", a possibility to check against the records, not an identified cause. The
records show:
- **The walk covers the maze:** its head enters 90%, 92% and 95% of the 36 maze cells' open blocks within the
  horizon, and 89-91% of its weys make at least one visit.
- **Its visits commonly follow remembered contact with another component, consistent with component
  switching:**
  - at the moment of a visit, its remembered component is a goal ring in most cases (k_r = 0: 2 230 of 2 393
    visits), as entering the roundabout makes likely;
  - the last remembered component outside the visited goal's ring is most often the perimeter (k_r = 0: 942 +
    585 visits), then a detached fragment (241 + 313);
  - it changes remembered component 36-52 times per 1 000 ticks.

  These summaries do not exclude local ring-following before a visit; a remembered component persists through
  free space.
- **The mazes are open:**
  - 69%, 73% and 76% of internal segments are open, against 58% for a tree;
  - goal-to-goal paths are 1.64-1.66 × their Manhattan distance;
  - 8% of spawn-goal pairs are in direct line of sight;
  - each goal has 2.1 entrances on average.

**Not read here:** whether a smaller horizon, a larger maze or fewer openings around the goals would bring the
walk under 2.0. E3d's design does not test it.

## The scent reach (design §2)

- **Most goals are flagged:** 255, 252 and 245 of 256 goals reach the perimeter track within the scripted
  follower's detectable distance. Only 1, 4 and 11 are not, too few to read a split.
- **Arrival, the share of weys whose head reached a goal,** flagged goals then unflagged:
  - **the shared follower:** 0.80 and 1.00 (k_r = 0), 0.77 and 0.75 (2), 0.80 and 0.81 (4);
  - **the seed:** 0.97 and 1.00, 0.99 and 1.00, 0.99 and 1.00.

  A and B separately, and the whole-maze split, are in `summary.json`.

## Where the rest of §6's records are

For every member at every k_r, `calibrate.json` holds, per strain and maze:
- visits, legs, round-trip share, the later-leg rate and the no-first-visit share;
- discovery (arrival at A and at B, and their censored median first-entry ticks);
- coverage and goal-block occupancy;
- the contact shares by class;
- the switch rate;
- the counts of the first component class, switches by class pair, and the at-visit class pairs.

Each condition's per-wey and per-visit arrays are in `runs/e3d/records/` (local, hashed).

## What else the calibration shows (exploratory; not part of the verdict)

- **Wall-following is defeated, for the tested controllers and starts.** Both qualified scripted
  wall-followers make 8-15 visits in 1 024 weys at every k_r, and no round trip. That is the behavioural side;
  the geometric guarantee is separate.
- **E3c's 16 from-scratch champions with their noses removed score below 0.002 visits per wey at every k_r, and
  none completes a leg.** With their noses removed they made 6.59-6.79 on E3c's 5 × 5 tree mazes (E3c's
  `evaluate.json`).
  - **Not E3d's prediction:** that concerned intact champions against a 6 × 6 tree reference, and neither was
    played.
  - **It does not separate the islands from the other changes:** the maze size (5 → 6), the family, and the
    spawn rule (E3b-1's dead ends against E3d's spawn cells).
  - **It does not establish nose dependence on islands:** their intact counterparts were not played.
- **Navigation here means following trails as well as scent.** With trails off, the scripted follower makes
  2.93, 2.39 and 2.37: within 0.6 of B_max, against 15.8-16.5 with shared trails. On this family scent alone
  barely beats a random walk, which matters for E4's navigators.
- **The scent navigators separate from the blind family by large factors:**
  - the shared follower makes 6.5-7.1 × B_max;
  - the seed makes 3.9-4.2 × B_max, with a median of 6.8-8.7 legs;
  - the seed with its noses removed falls to 1.75-1.88, near W2's own score.

## What this does and does not show

- **It shows** that this maze family, at the registered thresholds, does not meet E3d's gate. A random walk with
  W1's reflex exceeds the absolute blind limit of 2.0 visits per wey by 0.34-0.53, with intervals wholly above
  it, while staying under a quarter of the shared follower's score.
- **It does not show** that the family is unusable for E4. The design states that if E3d fails, "the failed
  criteria say what the next construction must change, and the roadmap stays paused before E4 until the owner
  decides" (§9). G1b is the one that failed.
- **Nothing was tuned on these results.** The verdict follows the bound procedure. Any change to the construction
  or the thresholds needs fresh calibration and confirmation blocks (§4).

## For the owner (not part of the registered result)

The failed criterion points to three directions, none tested here:
- **Reduce random coverage:** a larger maze (c = 7), or a shorter horizon. E3c's results note a shorter horizon
  as an untested idea (D220). It changes the task, and it would apply to E4 too.
- **Make the goals harder to reach blindly:** fewer openings around each goal. The carved roundabout opens all
  eight ring-road segments, and those openings make the goals island-safe. Fewer openings need a redesigned
  construction that keeps island safety.
- **Revisit G1b's absolute level:** a choice about the claim, not a measurement.
  - It cannot rehabilitate this run; a future validation would need it fixed in advance.
  - A limit that admits this random walk admits a blind control that completes a round trip for over 40% of its
    weys.

## Corrections before publication (the results review, D231)

Both reviewers ("fix then publish"; `docs/reviews/20261010-E3d-results/`) found the following in the draft at
d29fb3a. Each was corrected here:
- "make no visit at all (0.00 for every one)": S-mod made 5 and 2 visits at k_r = 0 and 2. They now read below
  0.002 per wey, with no leg.
- The seed at k_r = 0: 9.02 should read 9.01.
- W2's round trips: 27-31% should read 28-31%.
- The refused attempt's duration ("3 s") is not in a committed file. It was dropped.
- "Every number comes through `e3d_summary.py`" was false. The sources are now listed.
- The compute total is the formal attempts' accounting. The compare subprocess's worlds and ticks are not
  counted.
- "Not by following a ring" goes beyond the records. It is narrowed to "consistent with component switching".
- "Passed by wide margins" was removed: every G2a interval crosses ⅓.
- The bootstrap intervals (§5) and the scent-reach split (§2), which the report stage skips on a calibration
  failure, were added from `summary.json`.
- The trail-free follower now has its own observation. The S champions' observation names the spawn-rule
  change and the absent intact play.
- The owner section: G1b's bullet carries the walk's round-trip share; the horizon bullet cites D220; the
  roundabout bullet says a redesign must keep island safety.
