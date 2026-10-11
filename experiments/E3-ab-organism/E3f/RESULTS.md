# E3f: results

**The verdict, in the bound wording (E3d §4, labelled for E3f): "E3f: passed".**
- **Calibration** (128 mazes) and **confirmation** (256 fresh mazes) met every criterion, at k_r = 0 and
  H = 1 800, on their point estimates: G1a-G3b, the oracle's precondition and the feasible floor.
- **G2a,** the follower against the oracle, is the narrowest criterion: 0.337 on calibration and 0.361 on
  confirmation, against ⅓. Both blocks' intervals cross ⅓ (calibration 0.271-0.403, confirmation 0.318-0.404).
- **E3f §2's prediction was close on fresh mazes.**
  - **Predicted from E3d's truncated block:** B_max 1.761, the follower 11.63, the oracle 31.70, the seed 6.46,
    G2a 0.367.
  - **Confirmation gave:** 1.744, 11.61, 32.11, 6.74 and 0.361.
  - **Calibration's follower came in lower,** at 10.41.
  - **The risk Astra named,** extra walk settings raising B_max, did not materialise. The best of the six walk
    settings E3d had not played made 1.71, against 1.74 for one E3d played (Fable).

**Where the numbers come from:**
- **the gate and its intervals:** `report.json` (confirmation) and `report.json`'s calibration summary;
- **the per-strain records:** `calibrate.json.blocks` and `confirm.json.blocks`. They hold throughput, discovery,
  occupancy, contact, acquisition, switching and coverage, per maze;
- **the summary figures:** `scripts/e3d_summary.py --exp E3f` (`summary.json`):
  - per block: the gate, the intervals, the scent split, the navigators' later-leg rates and censored discovery
    medians, the B_max member's detail, the champions' blind counts;
  - since D241, also the intact champions on both blocks, the tree reference's means and the tangent coverage;
- **the champions' predictions:** `report.json.predictions` (per-champion ratios);
- **every blind member's round-trip share:** `report.json.round_trip_share_blind`;
- **the tangent diagnostic:** `report.json.tangent_blind_means`;
- **the projection:** `project.json`; **the equivalence legs:** `g-e.json`; **compute:** `compute-record.json`;
- **E3d's and E3e's figures:** their folders' `summary.json` and `RESULTS.md`.

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
- **Compute:** 1.06 GPU-hours (3 799 s) in the formal attempts' accounting, of 3. The full-rollout compare's
  worlds, ticks and neural updates are not counted; its wall time is.
- **Rule 6:** the formal plays ran outside `replay_mode()` in their recorded compositions. The equivalence leg
  covers trees at c = 5 and c = 6 at 2 400 ticks, not exact replay of these plays. The per-wey records are kept
  locally (`runs/e3f/records/`), hashed in `calibrate.json` and `confirm.json`.

## The gate

Mean visits per wey, with 95% bootstrap intervals over the paired mazes (2 000 resamples, seed 20 261 011, B_max
recomputed in each):

| Block | shared follower | oracle | seed | B_max (member) | G1a: B_max ÷ follower ≤ 0.25 | G1b: B_max ≤ 2.0 | G2a: follower ÷ oracle ≥ ⅓ | G2b: follower ≥ 4 | G3a: seed − B_max | G3b: seed's median legs ≥ 2 |
|---|---|---|---|---|---|---|---|---|---|---|
| Calibration (128) | 10.41 | 30.91 | 6.75 | 1.71 (walk, persistence 0.5, rate 1) | 0.165 ✓ | 1.71 ✓ | 0.337 [0.271, 0.403] ✓ | ✓ | 5.04 ≥ 0.68 ✓ | 4.69 ✓ |
| **Confirmation (256)** | **11.61 [10.11, 13.07]** | **32.11 [31.31, 32.92]** | **6.74 [6.29, 7.19]** | **1.74 [1.68, 1.82]** (walk, 0.5, rate 2) | **0.150 [0.134, 0.174] ✓** | **1.74 ✓** | **0.361 [0.318, 0.404] ✓** | **✓** | **4.99 [4.56, 5.43] ≥ 0.67 ✓** | **5.19 [4.50, 5.625] ✓** |

- **The oracle's precondition held** on both blocks: every oracle wey made a visit.
- **First-draw feasible share:** 0.77 (calibration) and 0.73 (confirmation).
- **Calibration's other intervals** are in `report.json`'s calibration summary and `summary.json`.

**What a pass means here** (E3f §1a, stated before play):
- **The absolute criteria are counts within 1 800 ticks.** G1b's cap corresponds to about 2.67 visits per
  2 400 ticks, so G1b's pass reflects the shorter window, not a lower blind throughput.
- **The relative-throughput test is carried by G1a and G2a.** They are measured at H = 1 800; they are not
  demonstrated invariants across horizons (Astra). G1a passed with its interval wholly below 0.25. G2a passed on its
  point estimate on both blocks, with intervals crossing ⅓, so the follower's efficiency against the oracle is
  established on these blocks, not beyond them.
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
  complete a round trip. Every member's round-trip share is in `report.json` (W2's is 0.14).
- **The tangent diagnostic** (every blind member started beside a wall, the confirmation's first 64 mazes, reported
  only): the best blind member made 1.60. 510 of 512 starts per member were moved tangent to a wall; the other two
  stayed at a spawn cell with no closed side.

## The navigators (confirmation; `summary.json`)

| | shared follower | seed | oracle |
|---|---|---|---|
| Later-leg rate (per 1 000 ticks after the first visit) | 6.83 | 4.13 | 17.89 |
| First entry at A: median tick over the mazes with an uncensored colony median (mazes censored; mazes with no arrival) | 175 (14; 6) | 264 (6; 0) | 60 (0; 0) |
| The same for B | 313 (104; 42) | 492 (7; 0) | 113 (0; 0) |
| Share of weys reaching A, B | 0.93, 0.65 | 0.96, 0.94 | 1.00, 1.00 |
| Round trips; no first visit | 0.54; 0.07 | 0.82; 0.04 | — |

- **How to read the discovery rows:**
  - a maze's colony median is censored when at most half its weys reached the goal (E3c's censored median);
  - the medians shown are over the mazes whose colony median is not censored;
  - "no arrival" counts the mazes where no wey reached the goal (Astra).
- **The scent-reach split** was computed: `summary.json`, `k_r["0"].scent_split` and `confirmation.scent_split`.
  - **The groups:** 509 of 512 goals are flagged; only 4 (calibration) and 3 (confirmation) are not, too few for
    reliable inference.
  - **On confirmation:** the follower made 11.46 in the 253 mazes with both goals flagged and 23.79 in the other 3;
    the seed made 6.69 and 10.83.
- **With trails off, the scripted follower makes 3.05:** 1.3 visits above the walk's best, against 11.61 with
  shared trails. The shared trails carry most of the scripted follower's advantage. The seed's and the champions'
  split between scent and trails was not measured: removing the noses removes both together.

## E3c's champions and the 6 × 6 tree reference (descriptive; the predictions stated in advance)

On the tree reference (128 mazes, ids 32 200-32 327, H = 1 800, E3b-1's tree placements):

| | tree reference | islands (confirmation) |
|---|---|---|
| E3c's S-mod champions, intact (8) | 3.26 (3 302-3 366 visits each) | 0.00 (1 visit in total) |
| E3c's S-dense champions, intact (8) | 3.28 (3 309-3 425 each) | 0.00 (1 visit in total) |
| E3c's P-sel champions, intact (4) | 2.56 (1 395-3 095 each) | 0.06 (456 visits, all one champion) |
| E3c's P-joint champions, intact (8) | 3.51 (3 026-4 052 each) | 0.51 (0 to 2 466 visits each) |
| Scripted wall-follower, left and right | 3.70, 3.74 | 0.01, 0.01 |
| The seed | 2.34 | 6.74 |
| The shared follower | 7.07 | 11.61 |
| The oracle | 22.03 | 32.11 |

- **The S prediction holds:** each S arm on the islands keeps at most 0.5 × its tree-reference mean. Both arms make
  one visit in total; their ratios are below 0.0001.
- **The P-joint prediction fails:** its arm keeps 0.14 ×, against the predicted at least 0.5 ×. Per champion it
  ranges from 0.00 to 0.41.
- **The tree reference shows the contrast the islands were built for:**
  - on 6 × 6 trees at this horizon, both scripted wall-followers (3.70, 3.74) and both S arms (3.26, 3.28) outscore
    the engineered seed (2.34);
  - on the islands, the wall-followers and the S champions make almost no visits (16 and 14 visits, and one visit
    per S arm), and the seed makes 6.74.
- **The tree family at this size and horizon would fail E3d's gate on more than G1:** on the tree reference the
  follower makes 0.32 of the oracle, and the seed's median legs are 0.75. So it would fail G2a and G3b as well
  (Fable). The islands are more open (69% of segments, against 58%), which helps the follower as well as the walk.
- **Both comparisons are of whole families,** not of the carving alone: the blocks differ in their placement and
  spawn rules (trees put the goals at dead ends).
- **The scripted wall-followers' switch rate** on the tree reference is 0, as the construction implies (E3d §3).

## What this does and does not show

- **It shows** that this maze family, 6 × 6 with carved island goals, k_r = 0 and H = 1 800, meets E3d's gate on a
  fresh confirmation block.
  - **The tested scripted wall-followers and E3c's S champions** make almost no visits.
  - **The broader blind family stays below the gate's limits:** a random walk still makes 1.74, covers 83% of the
    cells, and completes round trips for 26% of its weys.
  - **The scripted and engineered navigators shuttle.**
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
  scripted follower's advantage. E4 should measure the trails-off split for the seed and its champions, which E3f
  did not;
- **implement real module isolation:** the seed's inactive module is suppressed by saturation, not disconnected.

## Corrections before publication (the results review, D241)

Both reviewers ("fix then publish"; `docs/reviews/20261011-E3f-results/`) found the following in the draft at
5648c44. Each was corrected here:
- **Rounding:** G3a on confirmation should read 4.99, not 5.00; the seed's share reaching B 0.94, not 0.93; the
  median-legs bound 5.625.
- **The discovery table** mislabelled censored colony medians as "mazes not reached". It now gives both counts.
- **"Every summary figure" from one script** was too broad; the sources are now listed by figure. The intact
  champions and the tree reference were added to the summary.
- **Calibration's G2a interval** was missing, and so was the comparison of §2's prediction with the outcome.
- **The S champions "match" the wall-follower, and the wall-followers "make nothing":** both were wrong, and are
  now given with their numbers. "Scent-free coverage scores nearly nothing" is narrowed to the tested controllers.
- **"The navigators' advantage" from trails** is narrowed to the scripted follower.
- **"Horizon-robust"** is qualified.
- **The scent split, the round-trip pointer, the §6 records and the tangent coverage** are given, with the tree
  reference's G2a and G3b context and the wall-follower's switch rate.
