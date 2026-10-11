# E3f: results (draft, for review)

**The verdict, in the bound wording (E3d §4, labelled for E3f): "E3f: passed".**
- **Calibration** (128 mazes) and **confirmation** (256 fresh mazes) met every criterion, at k_r = 0 and
  H = 1 800, on their point estimates: G1a-G3b, the oracle's precondition and the feasible floor.
- **G2a,** the follower against the oracle, is the narrowest criterion: 0.337 on calibration and 0.361 on
  confirmation, against ⅓. Its confirmation interval crosses ⅓ (0.318-0.404).

**Where the numbers come from:**
- the gate and its intervals: `report.json` and `confirm.json`;
- calibration: `calibrate.json`;
- every summary figure: `scripts/e3d_summary.py --exp E3f` (`summary.json`, with its confirmation section);
- the projection: `project.json`;
- the equivalence legs: `g-e.json`;
- compute: `compute-record.json`;
- E3d's and E3e's figures: their folders' `summary.json` and `RESULTS.md`.

## What was run

- **The design:** `docs/E3/E3f-DESIGN.md` v1.1, bound at ef7609b (D239). It is E3d's design, pinned by hash,
  unchanged except H = 1 800, k_r = 0 only, a fresh maze run seed (1 192 000) and fresh blocks (ids
  32 000-32 455).
  - **Its review:** Astra said "bind"; Fable said "revise" with one wording item, taken (§1a).
  - **How H was chosen:** from an exploratory truncation of E3d's saved trajectories (D237). A test shows that
    truncation is exact for the follower and the walk on CPU mazes.
- **The stages:**
  - `project`: admitted with no reduction (1.56 h projected, plus 0.25 h reserved). The whole blind family
    played, including all nine random-walk settings;
  - `g-e`: passed; the full rollout against 40bd50f was identical on the CPU and the GPU;
  - `calibrate`: 12 minutes;
  - `confirm`: the confirmation block, the 6 × 6 tree reference at H = 1 800, and the tangent diagnostic;
  - `report`.
- **Compute:** 1.06 GPU-hours in the formal attempts' accounting, of 3. The full-rollout compare's worlds and
  ticks are not counted; its wall time is.
- **Rule 6:** the formal plays ran outside `replay_mode()` in their recorded compositions. The equivalence leg
  covers trees at c = 5 and c = 6 at 2 400 ticks, not exact replay of these plays. The per-wey records are kept
  locally (`runs/e3f/records/`), hashed in `calibrate.json` and `confirm.json`.

## The gate

Mean visits per wey, with 95% bootstrap intervals over the paired mazes (2 000 resamples, seed 20 261 011, B_max
recomputed in each):

| Block | shared follower | oracle | seed | B_max (member) | G1a: B_max ÷ follower ≤ 0.25 | G1b: B_max ≤ 2.0 | G2a: follower ÷ oracle ≥ ⅓ | G2b: follower ≥ 4 | G3a: seed − B_max | G3b: seed's median legs ≥ 2 |
|---|---|---|---|---|---|---|---|---|---|---|
| Calibration (128) | 10.41 | 30.91 | 6.75 | 1.71 (walk, persistence 0.5, rate 1) | 0.165 ✓ | 1.71 ✓ | 0.337 ✓ | ✓ | 5.04 ≥ 0.68 ✓ | 4.69 ✓ |
| **Confirmation (256)** | **11.61 [10.11, 13.07]** | **32.11 [31.31, 32.92]** | **6.74 [6.29, 7.19]** | **1.74 [1.68, 1.82]** (walk, 0.5, rate 2) | **0.150 [0.134, 0.174] ✓** | **1.74 ✓** | **0.361 [0.318, 0.404] ✓** | **✓** | **5.00 [4.56, 5.43] ≥ 0.67 ✓** | **5.19 [4.50, 5.63] ✓** |

- **The oracle's precondition held** on both blocks: every oracle wey made a visit.
- **First-draw feasible share:** 0.77 (calibration) and 0.73 (confirmation).
- **Calibration's intervals** are in `report.json`'s calibration summary.

**What a pass means here** (E3f §1a, stated before play):
- **The absolute criteria are counts within 1 800 ticks.** G1b's cap corresponds to about 2.67 visits per
  2 400 ticks, so G1b's pass reflects the shorter window, not a lower blind throughput.
- **The horizon-robust test is carried by G1a and G2a.** G1a passed with its interval wholly below 0.25. G2a passed
  on its point estimate, with an interval crossing ⅓, so the follower's efficiency against the oracle is
  established on this block, not beyond it.
- **The task E4 inherits is this one:** 6 × 6, k_r = 0, H = 1 800.
- **The blind family played** (the whole family, all nine walk settings) does not bound every possible blind
  strategy.

## The blind family on the confirmation block

| Member | Mean visits per wey |
|---|---|
| Random walk, persistence 0.25 / 0.5 / 0.8 at rate 0.5 | 0.98 / 1.33 / 1.50 |
| the same at rate 1 | 1.59 / 1.70 / 1.71 |
| the same at rate 2 | 1.62 / **1.74** / 1.57 |
| W2; W2-turn's best point (r = 0.4) | 1.24; 1.24 |
| W2+M40, W2+M80 | 1.22, 1.20 |
| The seed, noses removed | 1.28 |
| Scripted wall-follower, left and right | 0.01, 0.01 (16 and 14 visits in 2 048 weys) |
| E3c's S-mod and S-dense champions, noses removed (16) | 0.00 (S-mod 3 visits in total, S-dense 2) |
| E3c's P-sel champions, noses removed (4) | 0.00-0.18 (374 visits in total) |
| E3c's P-joint champions, noses removed (8) | 0.00-0.43 (the best 880 visits) |

- **The random walk's best member** covers 83% of the maze cells within the horizon, and 26% of its weys
  complete a round trip.
- **The tangent diagnostic** (every blind member started beside a wall, the confirmation's first 64 mazes, reported
  only): the best blind member made 1.60.

## The navigators (confirmation; `summary.json`)

| | shared follower | seed | oracle |
|---|---|---|---|
| Later-leg rate (per 1 000 ticks after the first visit) | 6.83 | 4.13 | 17.89 |
| Median first-entry tick, A (mazes not reached) | 175 (14) | 264 (6) | 60 (0) |
| Median first-entry tick, B (mazes not reached) | 313 (104) | 492 (7) | 113 (0) |
| Share of weys reaching A, B | 0.93, 0.65 | 0.96, 0.93 | 1.00, 1.00 |
| Round trips; no first visit | 0.54; 0.07 | 0.82; 0.04 | — |

- **The scent-reach flag:** 509 of 512 goals reach the perimeter track, too few unflagged to split.
- **With trails off, the follower makes 3.05:** 1.3 visits above the walk's best, against 11.61 with shared
  trails. The shared trails still carry most of the navigators' advantage.

## E3c's champions and the 6 × 6 tree reference (descriptive; the predictions stated in advance)

On the tree reference (128 mazes, ids 32 200-32 327, H = 1 800, E3b-1's tree placements):

| | tree reference | islands (confirmation) |
|---|---|---|
| E3c's S-mod champions, intact (8) | 3.26 (3 302-3 366 visits each) | 0.00 (1 visit in total) |
| E3c's S-dense champions, intact (8) | 3.28 (3 309-3 425 each) | 0.00 (1 visit in total) |
| E3c's P-sel champions, intact (4) | 2.56 | 0.06 (456 visits, all one champion) |
| E3c's P-joint champions, intact (8) | 3.51 | 0.51 (0 to 2 466 visits) |
| Scripted wall-follower, left and right | 3.70, 3.74 | 0.01, 0.01 |
| The seed | 2.34 | 6.74 |
| The shared follower | 7.07 | 11.61 |
| The oracle | 22.03 | 32.11 |

- **The S prediction holds:** each S arm on the islands keeps at most 0.5 × its tree-reference mean. Both arms make
  one visit in total; their ratios are below 0.0001.
- **The P-joint prediction fails:** its arm keeps 0.14 ×, against the predicted at least 0.5 ×. Per champion it
  ranges from 0.00 to 0.41.
- **The tree reference shows the contrast the islands were built for:**
  - on 6 × 6 trees at this horizon, a scripted wall-follower (3.74) beats the engineered seed (2.34), and E3c's
    scent-free S champions match it;
  - on the islands, the wall-follower and the S champions make nothing, and the seed makes 6.74.

  The two blocks differ in their placement rules (trees put the goals at dead ends), so this is a comparison of
  whole families, not of the carving alone.

## What this does and does not show

- **It shows** that this maze family, 6 × 6 with carved island goals, k_r = 0 and H = 1 800, meets E3d's gate on a
  fresh confirmation block. Scent-free coverage, including E3c's evolved coverers, scores nearly nothing, while the
  scripted and engineered navigators shuttle.
- **It does not show** that no blind strategy can solve the family: the gate covers the declared blind family
  only. Nor does it show that the follower's efficiency against the oracle exceeds ⅓ beyond this block: G2a's
  interval crosses ⅓.
- **The horizon was chosen from E3d's records,** then tested here on fresh mazes. The pass is on those fresh
  mazes.

## For E4 (from D237's consultation; not part of the registered result)

E4 can use this family: 6 × 6, k_r = 0, H = 1 800. Its design should:
- **re-play the blind family and the navigators on E4's own mazes,** as a precondition of each arm's navigation,
  not as a threshold for the effect;
- **separate navigation competence from transfer between the modules;**
- **control for trails and other environmental information paths.** On this family the trails carry most of the
  navigators' advantage;
- **implement real module isolation:** the seed's inactive module is suppressed by saturation, not disconnected.
