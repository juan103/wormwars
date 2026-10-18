**Run it.** All three merged points accepted, and nothing in v3.3's code or wording must change before the check runs.

**1. Reliability: accept.** The merge is better than either of our proposals. With five refits (4 degrees of freedom), the SD ≤ p gate passes pilot-dev's own dispersion of 0.59 p about 98% of the time, a true SD of p about 59%, and 1.5 p about 22%, so it screens only dispersions well above the registered bound. Astra's p/2 would have passed 0.59 p only 42% of the time, a coin flip again. I checked `stats.compare` with `over_brains=True`: it resamples worlds (one shared draw) and refits jointly, and `np.tile(restored, (5, 1))` matches `fin[ri]`'s shape, so the lower bound does carry the refit spread as §7 claims.

**2. Five refits: accept.** It costs about 0.2 GPU-hours and the brain-resampled bound uses them.

**3. V2 dropped: accept.** That was my proposal, and the three random-partner refits per variant restore the advantage reading that v3.2 lacked.

**What I verified at f8506d1:**
- The config matches §7: order V4, V3, V1; 416, 576, 512 episodes per search-generation; plan 5/3/5; alpha 0.05; SD fraction 1.0; safety 1.15.
- `_check_outcome` implements the written rule, and the test's Bonferroni values (0.0166 passes, 0.0167 fails) straddle 0.05/3 correctly.
- Episodes sum to 2,442,624. At the slower measured rate (587.6 per second) plus finals at 971.9 per second, that is 1.12 hours, 1.29 with the factor. The cap leaves 6.0 − 4.56 − 0.03 (preflight) = 1.42. My own batch-size estimate puts the actual nearer 1.0 to 1.1 hours.
- The CUDA preflight of the new stage ran at f8506d1, clean, completed.
- The tell-split record shows 0 of 15 differ.

**Two non-blocking notes:**
- `scripts/e03a.py:1270` divides alpha by the number of variants passed in. If the cap stops the check before V1 and the rule is later applied to two completed variants, the divisor becomes 2. §7 (around line 401) also does not say how the rule reads after a cap stop. One sentence and a fixed divisor of 3 would close it. Not needed if the check completes, which the projection says it will.
- Rule 5: D315's "9 of 15 differ" for the planted swap-timing shift is in no committed file. `tell-split-check.txt` records only the identical runs and the script has no planted mode. Note it as a transient check in D315, or commit the planted run's output.