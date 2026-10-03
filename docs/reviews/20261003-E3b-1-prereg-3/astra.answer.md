**Verdict: bind, with these last fixes; no further review round.**

Draft 3 resolves the substance of my previous objections: statistical edge cases, unequal-n sign flips, checkpoint accounting, evaluation retry precedence, component thresholds and recording requirements. All nine hashes match committed files at `1c86190`. The power figures match `power.json`, and the corrected thresholds pass the published seed.

**“Every rule fully specified and computable” is still slightly too strong:**

1. **Replay calibration is undercounted.** [§9](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md:356) budgets only replay recipients plus donors. The numerator also requires separate episode-0 **shared** calibration rollouts, as [the existing coefficient function](/D:/Claude/random/wormWars/scripts/e3b0.py:846) demonstrates. For K organisms, add `ceil(K/16) × t_plain` alongside `ceil(K/8) × t_donor`. Donors at different endpoints cannot supply the stipulated episode-0 numerator.

2. **Terminal failure of `champions` remains unspecified.** [§5](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md:151) defines evaluation resumption but does not say whether partial champion validation survives or permits evaluation. The simplest complete rule: `champions` restarts atomically on its permitted retry; `evaluate` requires a successfully completed `champions` stage. A terminal stop leaves readings “not read”, without relabelling completed training runs as failed.

3. **Recorder coverage does not match the promised summary.** [§7](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md:311) promises the nose-input share for **each champion**, but [§6](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md:196) requires recording only block 1. Require the counts also for T-F’s index-124 champions in block 4 and N/R champions under shared access in block 6. Define an empty qualified-input denominator as “not read”; extend test 17 accordingly.

These are concrete specification fixes, with no need to reopen the scientific design. The E3b-1 runner and §12 checks still require implementation and validation before formal execution.