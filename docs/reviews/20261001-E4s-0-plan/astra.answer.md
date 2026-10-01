**Verdict: revise.** I checked `roadmap` at `21d84b2`, including the existing comparator implementation and tests. No files changed or experiments run.

The 20-edge wiring, left-turn sign, carrier bias arithmetic, and first-qualifying-step stopping rule are correct. The proposed formal world ranges are disjoint from the earlier experiments’ ranges.

Must-fix items:

1. **§1 and Tests — strengthen the residual check.** The existing wrapper correctly uses same-tick signals and adds before clamping. However, the [current test](/D:/Claude/random/wormWars/tests/test_e4s_comparator.py:103) would also pass an implementation that clamps the original turn first. Add an opposing-residual case: raw turn **1.5**, residual **−0.75**, expected **0.75**, whereas premature clamping gives **0.25**. Check forward and pump remain unchanged. Require identical batch composition for wrapped/unwrapped comparisons and across k; recording different compositions does not remove that confound.

2. **§3, open-loop dynamics — do not call the last ten of forty ticks “settled.”** At zero bias, τ = 2 and recurrence 0.95 give a near-rest effective time constant of approximately **40 ticks**, before the other stages’ delays. Your t90 can therefore substantially understate response time. Pin the preconditioning duration, measure change against the unchanged control, and either extend until a declared convergence criterion or label the response unsettled. Handle negative reversals and negligible response explicitly.

3. **§3, simulated populations — distinguish the correct selection unit from the classification protocol.** Selecting each population’s fitness-best G0 genome matches `evolve_batch`, including lowest-index ties. But **256-world D classification differs from E4s-1’s 1,024-world classification**. Use 1,024 worlds for this design-changing diagnostic, or explicitly call the smaller measurement a conservative proxy. Preserve “unclear” separately. Also correct the roadmap’s “out of reach by construction”: that statement applies to the *same sixteen runs’* G0 classifications, not sixteen independent pilot populations predicting future runs. Twelve pilot successes are neither necessary nor sufficient for twelve future retained outcomes.

4. **Common settings — resolve the bootstrap seed mismatch.** [`world_ci`](/D:/Claude/random/wormWars/scripts/e2d.py:118) reads E2d’s global configuration, whose seed is **0**, not **20,261,001**. Importing it unchanged does not implement the stated seed. Explicitly configure the imported analysis settings or expose the seed through a helper, and test the actual path.

5. **Budget, smoke and projection — measure the intended compositions.** Four toy candidates do not establish throughput for the production strain/world batches. Pin chunk compositions and benchmark those shapes on smoke worlds, including instrumentation and analysis overhead. The present workload is approximately **780,864 episodes**, including the extra **24,064 unwrapped baseline episodes** omitted from the 0.76 M estimate. Admission should compare **already-spent time plus projected remaining work** against the limit. Freeze the selected shrink configuration before formal measurements.

6. **§4 and Tests — cover parameter ownership and selection errors.** Add sabotage-sensitive checks that robustness mutations leave every host parameter exactly unchanged while allowing graft-to-host weights to mutate. Define `j` and whether mutation draws are paired across scales. Add a constructed G0-selection test covering population boundaries, fitness ties, and selection-world versus diagnostic-world mix-ups; checking embedded initial parameters alone cannot catch those bugs.

Brief suggestions:

- Make selection IDs explicit, e.g. `990500000 + 8*i + arange(8)`. Exempt deliberately reused smoke IDs from historical disjointness assertions.
- Pin L4 base-selection ties and state explicitly which winning recurrent coefficient stays fixed during retuning.
- Keep isolated k = 256 significance descriptive rather than letting it bypass the adjacency rule for class assignment.
- The shrink order preserves qualification and G0 measurements; I would shrink descriptive background worlds first. Commit per-world counts alongside summaries.