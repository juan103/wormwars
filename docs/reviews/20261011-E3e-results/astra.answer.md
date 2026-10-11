**Fix then publish.** The registered verdict is correct. I found one numerical error and several reporting statements that need tightening; none changes the outcome.

I checked HEAD at `bd9c869`, verified both bound design hashes, independently recomputed the gates and all 27 E3e bootstrap intervals, and regenerated the entire summary in memory without writing files. It matches committed `summary.json`. All six supporting JSON files match their committed contents.

The recomputed gate is:

| k_r | B_max / follower | follower / oracle | Seed − B_max | Seed median legs | Failed criteria |
|---|---:|---:|---:|---:|---|
| 0 | 0.270830 | 0.157601 | 2.451172 | 2.3125 | G1a, G2a |
| 2 | 0.320372 | 0.133878 | 2.695313 | 2.7500 | G1a, G2a |
| 4 | 0.291884 | 0.157739 | 2.777344 | 2.6250 | G1a, G2a |

The oracle precondition and feasibility floor hold throughout. Consequently, no k_r qualifies, and **“E3e: failed at calibration”** follows from the bound procedure. Skipping confirmation, the tree reference and the tangent diagnostic is correct.

Required corrections:

1. **Correct one interval endpoint.** In [RESULTS.md:46](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3e/RESULTS.md:46), the follower’s k_r = 0 interval should be **[4.09, 7.03]**, not [4.09, 7.04]. The committed upper endpoint is `7.034741210937497`. The other quoted numerical results check out at their stated precision, including the comparison percentages, exact visit counts, projection and compute total: 2,545.138 seconds = 0.706983 hours.

2. **Remove the ambiguity in “not decisive on its own.”** [RESULTS.md:52](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3e/RESULTS.md:52) correctly says G1a uses point estimates, then undermines that statement. Under the bound procedure, **G1a alone would disqualify a k_r**. Replace the ending with something like: “Its point estimate fails the registered gate; its interval crosses the threshold, limiting inference beyond this block.”

3. **Fix the scent-reach interpretation and its denominator.** At [RESULTS.md:88](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3e/RESULTS.md:88), “does not separate arrival” is stronger than these records establish. There are only **5, 9 and 11 unflagged goals**, and the direction of the arrival difference changes across k_r.

   Also, “reached 65% of flagged goals” misdescribes the statistic. It is the **mean share of weys reaching each goal**, averaged over flagged goals. At k_r = 0, that share is 65.49% versus 57.5%; the number of goals reached by *any* wey is instead 219/251 versus 4/5. Suggested wording: “The split shows no consistent directional pattern, with very few unflagged goals; it does not identify scent reach as the cause.” Retain the qualification that the flag is a geometric proxy.

4. **Actually use the discovery and later-leg records in the G2a discussion.** The bound quotation is accurate and appropriately noncausal. But [RESULTS.md:86](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3e/RESULTS.md:86) substitutes no-first-visit and unconditional round-trip shares for the distinct discovery and later-leg measures named in §1a. A lower round-trip share alone does not establish slower shuttling among those that arrive.

   The recorded later-leg measure supports the intended observation: averaging the per-maze `later_leg_rate`, the shared follower scores **2.33 / 1.92 / 2.31**, against E3d’s **7.15 / 7.04 / 7.37** legs per 1,000 post-first-visit ticks. Add those figures and explicitly address the recorded discovery measures. Cite `calibrate.json`, or extend the summary to include them. Preserve censoring when summarising first-entry times; do not silently discard the null medians.

5. **Label the E3d comparison as descriptive across separate calibration blocks.** The numbers and percentage decreases at [RESULTS.md:60](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3e/RESULTS.md:60) are correct. However, the comparison uses fresh seeds and mazes, size-dependent placement and acceptance rules, and different W2-turn grids. It does not isolate a mechanism behind the decrease.

   Also clarify that B_max is each block’s maximum, not necessarily the same walk setting: at k_r = 0, E3d’s winner has rate 1 and E3e’s rate 2. Both settings were played in both experiments, so this does **not** invalidate the comparison. “G1a fails because the follower’s score fell” is defensible as an arithmetic description, provided it is not presented as a causal explanation.

6. **Complete the reporting scope.** The prose’s blind-family list omits **P-sel’s four and P-joint’s eight noses-removed champions**, although they were played and entered B_max. Name them, or label the list as selected examples and point explicitly to the full family. Their k_r = 0 ranges are 0–0.18945 and 0–0.38477 visits per wey.

   Add a short pointer to the remaining §6 records in `calibrate.json`. Also scope [the equivalence statement](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3e/RESULTS.md:31): the full-rollout comparisons cover **c = 5 and c = 6 trees**, with the GPU comparison inside `replay_mode()`. They do not establish exact replay of the formal c = 7 calibration.

I found no missing required experimental stage or missing category of committed calibration measurements. The reporting additions required by E3e §1a—intervals, scent split and exact champion counts—are present.

**The owner section is acceptable.** It labels the options untested and states that neither family passed. Choosing a failed family for E4 would be a new task-design decision, not rehabilitation of either verdict. I would add that any revised validation needs its criteria fixed beforehand and fresh blocks; the proposed horizon or signal changes are not demonstrated remedies.

This review recomputed analyses from the records; it did not rerun GPU rollouts or the wall-follower qualification tests.