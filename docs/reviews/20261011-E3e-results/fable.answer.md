**Verdict: fix then publish.** The registered verdict is the one the bound procedure gives, and every number I checked traces to a committed file. The draft does not overclaim on the verdict, the G2a reading or the E3d comparison, but it under-reports in several places the design, D231's correction and E3d's own results set as the standard. Nothing below changes the verdict.

## 1. The verdict, recomputed

From `summary.json` (which matches `report.json` and `calibrate.json` wherever I cross-read them):

| k_r | G1a B_max÷follower (≤0.25) | G1b B_max (≤2.0) | G2a follower÷oracle (≥⅓) | G2b follower (≥4) | G3a seed−B_max (≥0.5) | G3b median legs (≥2) | precond. | feasible (≥0.5) |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.271 ✗ | 1.495 ✓ | 0.158 ✗ | 5.52 ✓ | 2.45 ✓ | 2.31 ✓ | ✓ | 0.71 ✓ |
| 2 | 0.320 ✗ | 1.513 ✓ | 0.134 ✗ | 4.72 ✓ | 2.70 ✓ | 2.75 ✓ | ✓ | 0.70 ✓ |
| 4 | 0.292 ✗ | 1.637 ✓ | 0.158 ✗ | 5.61 ✓ | 2.78 ✓ | 2.63 ✓ | ✓ | 0.69 ✓ |

No k_r qualifies, so E3d §4 gives "failed at calibration", naming G1a and G2a at each k_r, with confirmation, the tree reference and the tangent diagnostic unplayed. That is what the draft says. The G3a threshold is 0.50 at every k_r because 0.1 × seed is 0.39 to 0.44. G2a's upper interval bounds are 0.197, 0.174 and 0.202, so "wholly below ⅓" holds. G1a's intervals all contain 0.25.

Other numbers verified: the gate table and intervals; the blind family at k_r = 0; the walk's coverage and round trips; the maze measures; the feasible shares; the projection (3.15, 2.75, 2.37 h plus 0.255 reserved); g-e identical on both devices; 2 545 s timed = 0.707 GPU-hours; E3d's figures against E3d's `RESULTS.md` and `summary.json`; the percentage losses (oracle 17.3 to 17.5%, walk 35.3 to 36.1%, follower 66.0 to 70.2%, seed 55.6 to 58.3%); the G2a reading quoted verbatim from E3e §1a; the 7 × 7 tour test exists with the stated threshold; origin/roadmap is at bd9c869.

## 2. Fix before publishing

1. **G2b's interval at k_r = 2 crosses 4.** The follower's interval there is [3.33, 6.22]; at k_r = 0 and 4 the lower bounds are 4.09 and 4.06. The draft says only "4.72 is close to G2b's floor". E3d's review removed "passed by wide margins" for the same reason on G2a. Say the interval crosses the floor; the gate is on point estimates, so the pass stands.
2. **The scent-reach split is reported for k_r = 0 only, and that choice is the one that supports the sentence.** At k_r = 2 and 4 the unflagged goals had higher arrival (0.74 vs 0.64; 0.72 vs 0.66), and the follower's visits in mazes with an unflagged goal were 14.1 and 12.3 against 4.0 and 5.0 in both-flagged mazes, on 9 and 11 mazes. That direction runs against the "fixed scent reach" explanation. Report all three k_r for the follower and the seed as E3d did (design §2: "the follower's and the seed's visits and zero-visit shares split by it"), and say the unflagged set is too small to read.
3. **Two of the four records the bound G2a reading names are not reported.** The reading says to check "discovery, scent-reach, no-first-visit and later-leg records". The draft gives the no-visit share, the flag and round trips. The later-leg rate (`later_leg_rate`) and the censored median first-entry ticks (`first_entry_median_a/b`) are in `calibrate.json` per maze but summarised nowhere. "Slower shuttling" and "longer discovery" are inferred from round trips and zeros; add the later-leg rate and the censored medians for the follower at each k_r, with E3d's beside them. A glance at k_r = 0's later-leg rates shows a strongly bimodal distribution (many zeros, a cluster at 5 to 17 legs per 1 000 ticks), which is worth a sentence.
4. **The trail-free follower now sits at or below the random walk, and the draft says nothing.** Follower with trails off: 1.55, 1.52, 1.48; B_max: 1.50, 1.51, 1.64. E3d's review required this observation to have its own paragraph ("scent alone barely beats a random walk"). At 7 × 7 scent alone does not beat it. This bears directly on the owner's "strengthen the navigators' signal" option and on E4.
5. **P-sel and P-joint with noses removed are missing from the blind family list,** and the exact counts cover S only, though §1a promises "exact counts for the champions' blind plays". P-joint's best champion makes 0.38 to 0.43 (394 to 440 visits), a quarter of the walk and above every W2 variant. Add the row as E3d's table has it.
6. **The §1a caveat is missing:** "the result names the blind family actually played; its maximum does not bound every possible blind strategy". It matters now that G1b passed. E3d's results carried the equivalent sentence.
7. **D235 says "the guard caught the first attempt", but the compute record lists four completed attempts and no failed one.** E3d's refused g-e attempt was recorded as failed and reported in its results. Either say in the draft that the refused attempt left no compute record and why (refused before accounting began?), or correct D235.
8. **Rule 5 and rule 6 housekeeping:** the source list does not name E3d's files, though the comparison section quotes them; add "E3d's figures: `experiments/E3-ab-organism/E3d/summary.json` and `RESULTS.md`". The draft also drops E3d's rule-6 scope sentence (formal plays ran outside `replay_mode()`; the equivalence leg does not establish their exact replay; records local, hashed in `calibrate.json`) and the pointer to where §6's records live. Carry both.
9. **"Both reviewers agreed it, after two rounds"** overstates D234: Fable said "bind"; Astra said "revise" with one wording change, taken verbatim, and no further check. Say that.

Nits: "34 minutes" is 2 068.6 s, 34.5 minutes; "2.63" is 2.625 rounded up at a tie; "58%" is 0.575; "reached 65% of flagged goals" is the mean share of weys arriving per flagged goal, as E3d phrased it; "E3d played its first reduction, E3e its second" should add that the W2-turn cut kept the best point (r = 0.4) at every k_r, so B_max is comparable across the two.

## 3. On the three specific questions

**The G2a reading** does not overclaim. It quotes the bound text and ends with "they do not identify the cause". Its defect is incompleteness (items 2 and 3), and the k_r = 0-only split reads as selective even if it was not meant to.

**The E3d comparison** is descriptive and the arithmetic is right. It should be labelled as unpaired (different seeds, different blocks, different maze sizes) and placed under the exploratory heading rather than before it. One useful addition: §1a predicted about 0.73 × for a lap-coverer from size alone; the walk fell to 0.64 to 0.65 ×, the oracle to 0.83 ×.

**"For the owner"** is appropriately hedged. Two things it should carry from the records: item 4 (scent alone no longer beats the walk, which changes what "strengthen the signal" means) and the fact that G2b and G3b were within their intervals of failing, so a longer-horizon 7 × 7 is not merely a G2a fix.

**What I could not check without a shell:** I did not rerun `e3d_summary.py`, hash the local `.npz` records against `calibrate.json`, or confirm from GitHub's push log that 7bc9c27 was on the remote before the project stage started at 08:35:55Z. The remote is at bd9c869 now.