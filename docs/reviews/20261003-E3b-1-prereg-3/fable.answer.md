I have what I need; writing the verdict now.

**Verdict: bind**, with the three text fixes below applied as written. No further round.

**1. My draft 2 points.** All resolved, checked in the file, not in §16:
- SE = 0 now covers every registered test with a numeric p and a point interval (§7).
- `champions` is admitted only if `evaluate` also fits (§10).
- `evaluate` saves per chunk, resumes at the first incomplete chunk, first completed attempt wins; training stages have at most three attempts with every path defined (§5).
- The record must name non-finite runs before the abort, tested in §12 item 4; `g-e` has a sabotage test (item 15).
- Cross-references fixed; the shifted null reads 0.29-0.31; the stage-level failure rule is in §13.

**2. Specified, computable, no post-hoc choices.** Yes. What I checked against files:
- Every §8 number matches `power.json`: the five false-positive ranges, the MDEs, the shifted null (0.29/0.29 at CV 0.282, 0.31/0.31 unequal, 0.36/0.37 at CV 0.40), the sensitivity checks' 5.0-5.5% and 2.9-3.6%.
- The probe rule matches `scripts/e3b0.py:297-308` exactly: K_D ≥ 30 at m ≤ 0.35, K_D × m ≥ 10.5 at 0.35 < m ≤ 1.0. The seed's values pass (15.2 and 14.5 at 0.891 and 1.0). `report.json`'s general `active.passed: false` comes from the 1.82 level, which §6 reports only, so test 16's claim holds. (That function's docstring says 11.06; the code uses the registered 10.5. Stale comment, not a problem for E3b-1.)
- `evolve_batch` does not breed at the last generation (`wormwars/e04a/evolve.py:181`), so `final` is the population evaluated at G − 1. The read points are right. Checkpoint counts give 200 points.
- `latch.structure`, `organism.no_latch`, `maze_runs.replay_donors`, `NoseRange` and `train_ids` exist with the semantics the text assumes.

**3. Last fixes (text only):**
- **The replay pre-pass has two legs.** E3b-0's `coefficient` (`scripts/e3b0.py:846-856`) plays a shared pass on the calibration block *and* the donor pass at coefficient 1. §6 says "one pre-pass" and §9 projects only "one chunk with donors per 8 organisms". State both legs in §6 and add the shared leg's chunks to §9's projection. Cost is trivial (about two 16-organism chunks), but the projection should match what runs.
- **Projections after a refusal or failed runs.** §10 says `champions`' projection is "the read points × one validation", without saying whether planned or existing read points enter. Say the projections for `champions` and `evaluate` are recomputed over the runs that completed. Otherwise the admission arithmetic has an undefined input in exactly the case it exists for.
- **The sign-flip in the power script** uses the pooled mean of all 16 (`scripts/e3b1_power.py:66`), which equals the registered stratified statistic only when n_A = n_F. Add that clause to §8; the simulation never had unequal n.

**One thing to know, not a fix.** After a non-finite score, attempt 2 is "unchanged". If the stage is exact on this GPU at that composition, it reproduces the same non-finite score at the same generation, so a non-finite T-A run costs up to a second full stage against the cap before attempt 3 drops it. The rule is specified and deterministic, so it binds as written; the owner should expect the cost.

**Not verified:** the nine hashes. I had no shell this session. Astra confirmed them at 6d251fd and the only commit since, 1c86190, is the pre-registration text by its message.