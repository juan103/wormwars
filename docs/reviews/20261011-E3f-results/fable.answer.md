**Verdict: fix then publish.** The registered verdict is the one the bound procedure gives, and the gate numbers all trace to `report.json` and `summary.json`. The fixes are one misrounded margin, several traceability and reporting gaps, and two sentences that reach beyond what was measured. None changes the verdict.

## 1. The verdict, recomputed

From `report.json`'s gate quantities, using the thresholds in `e3d_gate.py`:

| Block | G1a ≤ 0.25 | G1b ≤ 2.0 | G2a ≥ 0.3333 | G2b ≥ 4 | G3a ≥ max(0.5, 0.1 × seed) | G3b ≥ 2 | precondition | feasible ≥ 0.5 |
|---|---|---|---|---|---|---|---|---|
| Calibration | 0.1646 | 1.714 | **0.3368** | 10.41 | 5.038 ≥ 0.675 | 4.69 | 1.00, 30.9 ≥ 10.4 | 0.766 |
| Confirmation | 0.1503 | 1.744 | 0.3614 | 11.61 | 4.994 ≥ 0.674 | 5.19 | 1.00, 32.1 ≥ 11.6 | 0.730 |

With one k_r, `choose_k` returns "chosen" at calibration, confirmation is played, and `report_from` recomputes the gate on the confirmation block. "E3f: passed" follows. The B_max member is a random walk on both blocks, and it was in E3d's played reduction (persistence 0.5), so Astra's named risk, extra walk settings raising B_max, did not materialise: the best of the six added settings made 1.71 against 1.74.

Note the calibration G2a margin: 0.0035 above ⅓, with interval [0.271, 0.403]. The draft states the point but not the interval (item 2 below).

## 2. Numbers

Verified against committed files: both gate rows and every confirmation interval; the blind-family table (all nine walk settings, W2, W2-turn's best, M40/M80, the seed noses-removed, wall-follower counts 16 and 14, S-mod 3 and S-dense 2 visits, P-sel 374, P-joint 880); coverage 83% and round trips 26%; the tangent's best 1.60; the navigators' table; 509 of 512 flagged; the trail-free follower 3.05; the arm means and ratios in the champions table; the wall-follower, seed, follower and oracle on the tree reference; the projection (1.559 h, 0.254 h reserved, no reduction, full grids); g-e identical on both devices; calibrate 720 s = 12 minutes; 3 799 s timed = 1.055 GPU-hours; the binding commit and both design hashes as `e3f.py` pins them; the tangent block's feasible share (0.5625) agrees with the first 64 confirmation mazes' redraw counts.

Wrong or untraceable:

1. **G3a on confirmation is 4.994, which rounds to 4.99, not 5.00** (`RESULTS.md:47`).
2. **The per-champion counts in the champions table are in no committed summary.** "3 302-3 366 visits each", "3 309-3 425", P-sel's 2.56, 0.06 and 456 visits, and P-joint's "0 to 2 466" come from neither `report.json` (predictions omit P-sel; the tree quantities list only blind members) nor `summary.json` (`block_summary` skips conditions with role "organism", and there is no tree-reference section). They are consistent with the arm means, but I could not sum the per-maze arrays without a shell. Either extend `e3d_summary.py` with a tree-reference section and exact counts for the intact arms on both blocks, or name `confirm.json`'s per-maze arrays as the source. The opening line "every summary figure: `scripts/e3d_summary.py`" is wider than what that script emits.
3. **5.63** for the median-legs upper bound is 5.625 rounded up at a tie. The E3e review flagged the same thing. A nit.

## 3. Overclaims

On **what a pass means**, the draft is careful: it carries §1a's window caveat for G1b, states that G1a's interval is wholly below 0.25, and that G2a's confirmation interval crosses ⅓. Two gaps:

4. **Calibration's intervals are missing from the table.** E3d's and E3e's tables carried them, and §1a makes calibration a sequential screen that a pass needs. Add them, and say that *both* blocks' G2a intervals cross ⅓, not only confirmation's.
5. **The pre-stated prediction is never compared with the outcome.** Design §2 predicted B_max 1.761, follower 11.63, oracle 31.70, seed 6.46, G2a 0.367. Confirmation gave 1.744, 11.61, 32.11, 6.74, 0.361. That is a close hit on fresh mazes and the draft should say so in one line, with the walk-settings risk above and the fact that calibration's follower (10.41) came in below the prediction.

On **the champions and the tree reference**: the arm-level claims are right and properly descriptive, and the P-joint failure is reported plainly. Two wording points:

6. **"E3c's scent-free S champions match it"** (`RESULTS.md:117`): 3.26-3.28 against 3.70-3.74 is 12% below. "Approach it" or give both numbers.
7. An optional clause worth adding: on the 6 × 6 tree reference at this horizon, follower ÷ oracle is 0.32 and the seed's median legs 0.75, so the tree family at the same size and horizon would fail G2a and G3b as well as G1. The islands are more open (69% against 58% of segments), and that helps the follower as well as the walk. It is the honest context for "the contrast the islands were built for".

On **"For E4"**: fine as labelled, and the bullets match design §4. One sentence reaches too far:

8. **"The shared trails still carry most of the navigators' advantage"** (`RESULTS.md:95`, repeated at line 142). Only the scripted follower was played with trails off. There is no seed trails-off condition; the seed's noses-removed play removes trail and scent together. Narrow to "the scripted follower's advantage"; the seed's split is unmeasured.

## 4. Missing against the design and the earlier reviews

9. **The §6 records pointer** that E3d's and E3e's results carried (Fable's E3e review item 8) is absent. `confirm.json` holds, per strain and maze, for all three blocks: visits, legs, round trips, later-leg rate, no-first-visit, arrival, censored first-entry medians, coverage, occupancy, contact by class, switch rate, first class, switches by pair and at-visit classes. One sentence.
10. **Design §3: "Its switch rate on 6 × 6 trees is reported."** This is the first run where the tree reference was played. The entries I read of the wall-follower's tree-reference switch rate are zero, as the construction implies. Report it.
11. **The scent split's numbers**, as E3e's correction did: the follower made 11.46 in the 253 both-flagged mazes and 23.79 in the 3 others, the seed 6.69 and 10.83, too few to read. One clause.
12. **Round-trip shares** are in `report.json` for every blind member (§5 says each is reported); W2's is 0.14. A pointer suffices.

Not the draft, but for publication: E3f is not yet in `experiments/E3-ab-organism/README.md`, `ROADMAP.md`'s progress list, or the main README's "Newest" section, where E3e is in all three. `REVIEW_TRAIL.md` will need its row.

## What I could not check

No shell: I did not recompute either design's sha256, confirm from the git log that ef7609b records D239, hash the local `.npz` records, rerun the summary, or sum the per-maze arrays behind item 2. The guard enforced the hashes at each formal stage (every record shows "dirty": false and "completed"), so I take those as held.