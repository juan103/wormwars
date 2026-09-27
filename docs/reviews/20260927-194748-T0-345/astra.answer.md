The ledger implementation and specified island validation look correct. The CPU gate is **not complete**: several required tests are ineffective or missing.

I verified `roadmap` at `b966a93`. Seventeen targeted CPU tests passed; the save/load/re-simulation test also passed with filesystem storage redirected to memory. No files were changed.

1. **Must fix — The owed jitter test is vacuous.**  
   [test_t0_items345.py:175](D:/Claude/random/wormWars/tests/test_t0_items345.py:175) enables `"jitter"` but leaves `food_probe_radius=0.0`. Both compared offsets are therefore zero. I replaced `_jittered` with an identity function in memory: the test still passed.

   Set a positive radius and assert that jitter actually moves points. Account for subtraction rounding: with radius 1, corresponding keys were identical, but `(jittered_points - points)` differed by up to `9.54e-7` because the starting positions differed. Compare using identical corresponding input points, or a justified rounding tolerance. The repaired test should fail both with jitter disabled and with the old padded-flat-index keys.

2. **Must fix — The multi-generation isolation test does not test isolation; other promised island coverage remains missing.**  
   [test_t0_items345.py:153](D:/Claude/random/wormWars/tests/test_t0_items345.py:153) constructs per-island ancestry sets, then unions them and checks only global winners. I replaced `_breed_islands` with global `breed` in memory: the test still passed.

   Capture populations through `evolve` and check **every slot against its own island’s initial members** across generations. The agreed plan also requires all ring edges, untouched slots, and log/snapshot pairing with migration active. Existing tests provide partial coverage, but the pairing test uses one island and the new test requests no snapshots. The new migrant-survives-breeding test is useful.

3. **Must fix — Numerical coverage falls short of section 5.**  
   [test_t0_items345.py:60](D:/Claude/random/wormWars/tests/test_t0_items345.py:60) covers the ledger matrix correctly: N2/SH/RD, eight worlds, T0/T1. Its genomes use ordinary initialization, however, and it never checks brain states.

   The separate numerical tests cover only positive/negative extreme N2 genomes at T0 on four worlds, plus one 01b N2 champion under its restored/default settings. They inspect final states only. Missing are random genomes at mutation bounds, the mixed-sign extreme from `test_brain.py`, and the declared graph/task/world coverage for numerical checks. Check scores, individual energies, and brain states throughout the episodes.

4. **Should fix — Add adversarial tests for the ledger contract.**  
   The implementation is correct by inspection and my targeted probes: an early relative-error peak survives a zero final residual, and an early NaN survives later finite ticks. Commit tests for those cases, unequal starting energies, Inf, and finite/NaN chunks in both orders. The current NaN test leaves per-tick tracking disabled and injects NaN everywhere, so it does not protect the new temporal maximum.

5. **Should fix — Broaden D073’s layout diagnosis and qualify its NaN claim.**  
   The mixed-headcount diagnosis is correct and pre-existing, but it affects **maps as well as placement**. In [world.py:412](D:/Claude/random/wormWars/wormwars/world.py:412), spawn draws consume `self.n_weys` values from the same RNG later used for food and hazards. Changing padding changes positions, headings, food, and hazards. I reproduced all four differences and a non-jitter coevolution score change across chunkings. Git blame places this RNG structure before the T0 work.

   Fixed-headcount single-swarm experiments are unaffected. Keeping this defect deferred is consistent with D067, but D073 should describe its full scope.

   Separately, [coevolve.py:197](D:/Claude/random/wormWars/wormwars/evo/coevolve.py:197) still uses `max(worst_err, residual)`. Injecting NaN there returned `ledger_error=0.0`. This is pre-existing; either fix it or explicitly limit “NaN is no longer swallowed” to `rollout`.

6. **Minor — Two documentation details remain.**  
   `_breed_islands`’ elite/parent counts are also capped by island size inside `breed`; mention that. D067’s promised jitter-docstring note about discarding run-seed bits above 32 is still absent.

The ledger divides each world’s absolute residual by **its own starting total energy**, then preserves the maximum across ticks, worlds, and chunks. NaN propagates and Inf remains detectable. The `1e-12` denominator floor defines behavior near zero starting energy. Tracking defaults off and consumes no RNG. Its enabled cost includes several float64 conversions/reductions over world state plus the elementwise maximum—not literally one reduction. Final relative-error reporting still adds work when tracking is off.

The island validation correctly rejects empty multi-island partitions, migration intervals below one, negative migrant counts, and counts above `floor(smallest_island / 2)`, before constructing genomes. The CPU round-trip/re-simulation check is valid. Beyond the acknowledged GPU work, the must-fix test gaps above remain before the gate.

not yet