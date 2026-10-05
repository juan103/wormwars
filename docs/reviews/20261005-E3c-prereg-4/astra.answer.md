**Verdict: revise — one new regression.**

The draft-3 requirements are correctly taken for nonempty arm lists: coverage components and precedence, Q2’s disclosure and D208 qualification, the observed-mean label, and §8’s narrow-spread Q1 qualification. All **32 statistics/power tests pass**. The revised coverage, label and non-positive-seed tests fail against draft 3 and pass against draft 4.

Your numerical correction is right: Q2’s equal-means rejection ranges are **0.021–0.0548** across the 24 no-failure scenarios and **0.0532–0.1806** when S-mod has failures. `power.json` is unchanged.

Required change:

1. **Handle empty arms in `coverage_rule`, with regression tests and explicit §7.3 wording.** Draft 4 introduces a crash:
   ```python
   coverage_rule({
       "s_mod": [True] * 8,
       "s_dense": [True] * 8,
       "p_joint": [],
   })
   ```
   This raises `TypeError` at [e3c_stats.py:203](/D:/Claude/random/wormWars/wormwars/e3/e3c_stats.py:203); an empty S arm crashes at line 196. Draft 3 returned `"mixed"` for both. Empty lists produce `share=None` but an undefined count of zero, bypassing the guards. Zero eligible champions can arise under §5’s interruption rules. Treat unavailable shares explicitly: overall `"mixed"`, P-joint comparison `None`, and S component `"undefined"` if an S arm is empty; preserve `"high"` for fully measured high S arms when only P-joint is empty. Test each empty arm.

I found no other error introduced by draft 4.