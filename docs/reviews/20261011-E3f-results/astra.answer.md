**Verdict: fix then publish. “E3f: passed” is correct under the bound procedure.** The necessary fixes concern reporting and interpretation; none changes the gate outcome.

I checked `5648c44` on `roadmap`, verified both bound design hashes, independently recomputed both gates and all 18 bootstrap intervals, and reproduced the entire `summary.json` in memory. All seven supporting JSON files match HEAD. All 148 local record files match their committed hashes; their visit, leg, arrival and censored-discovery records agree with the JSON summaries. I changed no files and ran no simulations.

The recomputed gate quantities are:

| Block | B_max | B_max / follower | Follower / oracle | Seed − B_max | Seed median legs |
|---|---:|---:|---:|---:|---:|
| Calibration | 1.713867 | 0.164634 | 0.336777 | 5.038086 | 4.6875 |
| Confirmation | 1.744141 | 0.150286 | 0.361392 | 4.994141 | 5.1875 |

All six criteria pass. The oracle precondition holds, and first-draw feasibility is 0.765625 and 0.730469. Calibration therefore admits confirmation, and confirmation produces the registered pass.

G2a’s intervals are **[0.270923, 0.402873]** on calibration and **[0.318005, 0.403696]** on confirmation. Both cross one-third. That limits generalisation but does **not** overturn a procedure explicitly based on point estimates.

Required fixes:

1. **Correct the discovery table’s meaning.**  
   [RESULTS.md:88](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3f/RESULTS.md:88) labels the parenthetical counts “mazes not reached.” They actually count **mazes whose colony median is censored**: at most four of eight weys reached the goal.

   On confirmation, the follower has 14 censored A medians and 104 censored B medians, but only **6 A mazes and 42 B mazes with no arrivals**. The seed has six and seven censored medians, but **zero mazes with no arrivals** for either goal.

   Furthermore, 175/313 and the other displayed times are **medians over the finite per-maze colony medians**, excluding censored medians. State that explicitly. The summary keys `mazes_not_reached` and `median_over_mazes_reached` are themselves misleading; rename them or document their precise meaning.

2. **Fix two rounding errors.**  
   At [RESULTS.md:47](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3f/RESULTS.md:47), confirmation’s seed-minus-B_max is **4.99**, not 5.00: the unrounded value is `4.994140625`. Subtract before rounding.

   At [RESULTS.md:90](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3f/RESULTS.md:90), the seed’s share reaching B is **0.94**, not 0.93: the value is `0.93505859375`.

   The remaining quoted numerical results check out at their stated precision, including champion counts, tree means, prediction ratios, projection and compute: **3,799.333197 timed seconds = 1.055370 hours**.

3. **Correct the champion/tree interpretation and the claim about blind coverage.**  
   [RESULTS.md:117](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3f/RESULTS.md:117) says the S champions “match” the scripted wall-follower. Their tree means are **3.26 and 3.28**, versus **3.74** for the right-handed follower. Say that **both S arms and the scripted wall-followers outperform the seed’s 2.34**. No equivalence claim is needed.

   “The wall-follower and the S champions make nothing” is literally false: the wall-followers make **16 and 14 visits**, and the intact S arms make **one visit each**. Use “almost no visits.”

   More substantively, [RESULTS.md:127](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3f/RESULTS.md:127), “Scent-free coverage … scores nearly nothing,” overgeneralises. The blind walk scores **1.74**, covers **83%** of cells and completes round trips for **26%** of weys. Narrow the claim to the **tested scripted wall-followers and S champions**, while stating that the broader blind family remains below the gate’s limits.

   The registered champion predictions are reported correctly: the S arm ratios are approximately **0.0000187**, and P-joint retains **0.14429**. Keep the descriptive, whole-family comparison caveat; the tree reference does not isolate carving from placement and spawn differences.

4. **Restore explicit pointers to the required reporting already present.**  
   [RESULTS.md:93](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3f/RESULTS.md:93) says there are “too few unflagged to split.” The split **was computed**. Say “too few for reliable inference,” and point to `summary.json.k_r["0"].scent_split` and `summary.json.confirmation.scent_split`. There are four unflagged calibration goals and three confirmation goals. Small groups justify cautious interpretation, not withholding the prescribed split.

   Carry forward the reporting index required by the E3d/E3e reviews: identify `calibrate.json.blocks` and `confirm.json.blocks` as the locations of per-strain throughput, discovery, occupancy, contact, acquisition, switching and coverage records. Point to `report.json.predictions` for per-champion ratios and `report.json.round_trip_share_blind` for every blind member’s confirmation round-trip share. The tree wall-followers’ recorded switch rates are both zero.

   Also qualify the tangent diagnostic: all blind members received the same procedure, but **510/512 starts per strain were moved tangent to a wall**. The remaining starts stayed unchanged because their spawn cells lacked a closed side. This does not affect the gate.

5. **Correct the source map.**  
   [RESULTS.md:12](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3f/RESULTS.md:12) promises that “every summary figure” comes through `e3d_summary.py`. It does not produce the intact-champion/tree table or the tangent maximum. Those derive from **`confirm.json.blocks` and `report.json.predictions` / `tangent_blind_means`**. Name those sources explicitly.

   The figures are traceable to committed files; the draft’s account of that traceability is too broad. Also add **neural updates** to the full-rollout subprocess’s uncounted quantities alongside worlds and ticks.

6. **Narrow the trails claim and retain the limits of the pass.**  
   At [RESULTS.md:94](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3f/RESULTS.md:94) and in “For E4,” change “the navigators’ advantage” to **“the scripted follower’s advantage.”** E3f measured its trails-off score, **3.053711**, against **11.605469** with shared trails. It did not perform the corresponding trails-off intervention on the seed or champions. Removing noses removes scent and trail together and cannot establish that decomposition.

   The G1b explanation is appropriate: the shorter window changes the absolute acceptance claim, not demonstrated blind throughput. I would also qualify the inherited phrase **“horizon-robust”**: G1a/G2a are relative-throughput criteria measured at H = 1,800, not demonstrated invariants across horizons.

The **“For E4” section is otherwise sound**. It correctly separates navigation eligibility from the transfer effect, requires fresh references, and identifies environmental information paths. The saturation-versus-disconnection statement matches `organism.py`. Carry trails-off measurements for the seed and champions into E4’s controls; E3f’s pass itself establishes neither module transfer nor the adequacy of a transfer experiment.

I found no missing required experimental stage or missing category of recorded measurements. These fixes require reporting changes, not another formal run. Record them openly under the repository’s correction rule.