Checked `f8506d1`.

1. **Reliability — accept.** The implementation correctly resamples worlds and refits and uses the monotonic lower-bound gate. SD ≤ p is acceptable for this explicitly provisional feasibility screen; it does not establish population reliability or satisfy pilot-check’s separate resolution requirement.

2. **Five original-partner refits — accept.** This improves the screen within the budget, with individual comparisons retained for interpretation.

3. **Drop V2; fund random-partner refits — accept.** Measuring the original-partner advantage under each retained search is a reasonable budget tradeoff. Bonferroni at 0.05/3 matches the three fixed variants.

No blocking code or v3.3 wording changes. One nonblocking documentation correction: [D315](/D:/Claude/random/wormWars/DECISIONS.md:9689) claims SD exactly at p is tested, but the [committed test](/D:/Claude/random/wormWars/tests/test_e03a_script.py:246) omits that equality case. I ran its existing assertions and additional SD=p and enrichment-p=α/3 checks in memory; all passed. The CUDA smoke record also reports completion.

**run it**