**Verdict: bind it.** Every required change from both draft-3 reviews is taken correctly, and I found no error in draft 4 that changes a reading. Four optional notes follow.

I had no shell, so I could not run `git diff`, the tests, or a byte check of `power.json`. Instead I read the current pre-registration, `e3c_stats.py`, both test files, `e3c_power.py` and D209 against the line citations in both draft-3 reviews, and pulled every Q2 equal-means rejection rate out of `power.json` by pattern.

**1. The required changes**

- **Q2's disclosure (mine).** Taken at §7.1 lines 257-263 and §8 lines 439-443. The ranges are right. Over the 24 scenarios with no failures in either S arm and a true Q2 of 0, the exact rejection rate is 0.021 to 0.0548. Over the 58 scenarios where S-mod's failure rate is 1/8 or 1/4, it is 0.0532 to 0.1806, the maximum at P-joint's spread × 0.75. The base case is 0.042. The note to D208 is at DECISIONS.md lines 6806-6807.
- **The exact label (both).** "distributions differ (exact test); observed mean higher for X" is identical in `e3c_stats.py:156`, `e3c_power.py:149-150`, the test at lines 179-183 and §7.1 line 253.
- **The 6-run figures (mine).** §8 line 461 now gives 0.33-0.34 for 8 runs and 0.44-0.45 for 6.
- **The coverage components (Astra).** `coverage_rule` computes the S-arm part from the S arms alone, returns the P-joint comparison as None when any champion is undefined, and takes shares over defined champions. Astra's counterexample now yields "mixed", "high", None, and a None share. The new test at `tests/test_e3c_stats.py:201` would fail on draft 3's code, so rule 9 holds. The precedence in §7.3 lines 383-387 matches the code's branch order.
- **§8's Q1 qualification (Astra).** Lines 483-492 restrict the margin label to no failures at spread 0.06 and separate it from the exact test. The 0.82 and 0.15 figures match `power.json` lines 22520-22521.
- **The optional items** listed in §17 are all present, including the non-positive P-fixed mean as a registered outcome with its test, the bootstrap recomputing P-fixed's mean, and the split counts, which are the correct binomial coefficients.

**2. Optional notes, none blocking**

- **"When S-mod has failed runs"** (§7.1 line 261, §8 line 441, D209) describes scenarios where S-mod's failure probability is positive, averaged over trials that often show no failure. The text elsewhere insists observed failures are not the failure model. "Under the failure models" would be exact.
- **The 24-scenario count** omits the 10 base scenarios where only S-dense fails. Their Q2 rates are 0.021 to 0.051, inside the stated range, so nothing is false.
- **A latent crash:** `coverage_rule` raises a TypeError if an arm's list is empty, since its share is None but its undefined count is 0. The report function should never pass an empty list, or the function should guard it. Also its undefined check spans every arm passed, so the report function must pass exactly the three arms.
- **Line 262** says "the arms' outcomes differ" where the label says "distributions differ". Worth aligning.