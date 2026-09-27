The three targeted island fixes are correct. **14 tests passed**, and each new bug regression fails against `54ad0a9`’s parent. A short parent-versus-current single-island run matched exactly in scores, champion tensors and all snapshot tensors, including Dale signs. The inspected recorded configurations use one island.

The corrected test in [test_evolve.py:90](D:/Claude/random/wormWars/tests/test_evolve.py:90) now checks the actual interleaved slots. All three bugs plausibly match what a careful reader would discover; there is no evidence establishing that they were the original unnamed three.

1. **Must fix — Neural accounting omits most actual updates.** [T0.md:20](D:/Claude/random/wormWars/docs/foundations/T0.md:20), [brain.py:336](D:/Claude/random/wormWars/wormwars/brain.py:336), [world.py:306](D:/Claude/random/wormWars/wormwars/world.py:306).

   `Brain.step` receives `[S, B, N]`; in normal rollouts, `B = worlds_per_strain × weys_per_swarm`. Counting `S × substeps` undercounts by that entire batch dimension. Count `S × B × effective_substeps` network updates, or additionally multiply by `N` if the unit is individual neuron updates. Include padding and dead slots that are still computed, and respect the `substeps` override.

   This hook correctly covers exp02 input-response probes and exp03 history probes. Their batch dimension is one, unlike world simulations.

2. **Must fix — Complete accounting needs coverage and output outside `evolve`.** [T0.md:16](D:/Claude/random/wormWars/docs/foundations/T0.md:16), [T0.md:26](D:/Claude/random/wormWars/docs/foundations/T0.md:26).

   `_play` is a useful rollout hook, but several production paths bypass it:

   | Path | Direct construction or stepping |
   |---|---|
   | Calibration, including repeated fitting and validation | [calibration.py:103](D:/Claude/random/wormWars/wormwars/calibration.py:103), [calibration.py:198](D:/Claude/random/wormWars/wormwars/calibration.py:198) |
   | Exp02 behaviour probes | [probes.py:155](D:/Claude/random/wormWars/wormwars/exp02/probes.py:155) |
   | Exp03 coverage | [measures.py:49](D:/Claude/random/wormWars/wormwars/exp03/measures.py:49) |
   | Exp03 stimulus-bank generation | [exp03.py:392](D:/Claude/random/wormWars/scripts/exp03.py:392) |
   | Exp02b replay and stimulus bank | [analyse.py:132](D:/Claude/random/wormWars/experiments/02b-champion-analysis/analyse.py:132), [analyse.py:207](D:/Claude/random/wormWars/experiments/02b-champion-analysis/analyse.py:207) |
   | Coevolution matches | [coevolve.py:168](D:/Claude/random/wormWars/wormwars/evo/coevolve.py:168) |

   The proposed explicit exceptions can work, but require counting tests for these paths—not just a construction-site allowlist. Instrumenting `World` construction/ticks would reduce omissions. Count actual simulated world-ticks, including early termination.

   Exp03 never calls `evolve`, so a `RunResult.compute` field alone cannot publish its accounting. Specify experiment-level collection and persistence, including unsuccessful calibration attempts and retries. Also inventory viewers, benchmarks and geometry probes; [SparseBrain.step:81](D:/Claude/random/wormWars/scripts/bench_brain.py:81) bypasses `Brain.step`.

3. **Must fix — Pairing tests must cover serialized scores; an existing mismatch is already present.** [evolve.py:171](D:/Claude/random/wormWars/wormwars/evo/evolve.py:171), [evolve.py:187](D:/Claude/random/wormWars/wormwars/evo/evolve.py:187), [T0.md:38](D:/Claude/random/wormWars/docs/foundations/T0.md:38).

   `fit_final` contains **one best score per generation**, but is saved as `fitness` alongside the **final population**. With six strains and three generations, that is three historical scores accompanying six genomes. Those are not paired population fitness values.

   Save final per-strain scores separately and give generation history an explicit name. Test the saved metadata, returned champion, snapshots and holdout association. A logged nickname alone is insufficient evidence of genome identity.

   Compare complete `[strain, world]` score arrays when testing permutations and chunking: comparing only means can miss a world-axis permutation.

4. **Must fix — Include stochastic probes in pairing/chunk tests: jitter currently violates the contract.** [world.py:302](D:/Claude/random/wormWars/wormwars/world.py:302), [world.py:485](D:/Claude/random/wormWars/wormwars/world.py:485), [T0.md:34](D:/Claude/random/wormWars/docs/foundations/T0.md:34).

   Jitter uses one generator seeded by `run_seed`, then draws according to the whole batch shape. Noise follows batch position, rather than world identity. Reordering strains or changing chunks changes their sensory noise.

   I reproduced this on CPU with two strains, worlds `[101, 102]`, run seed `3`, radius `1`, and 20 ticks: changing `chunk_worlds` from `4` to `2` changed a per-world score by **0.005271196**. Identical initial worlds in different batch slots also received different food samples.

   Add a failing regression and make probe noise reproducible by world/tick/individual identity, with an explicit common-random-number policy.

5. **Must fix — Separate deterministic round-trip tests from historical and nondeterministic replay.** [T0.md:50](D:/Claude/random/wormWars/docs/foundations/T0.md:50), [REPRODUCIBILITY.md:33](D:/Claude/random/wormWars/docs/REPRODUCIBILITY.md:33), [test_direction.py:161](D:/Claude/random/wormWars/tests/test_direction.py:161).

   Saving and loading should preserve every tensor exactly. Re-simulation should be exact under the same deterministic execution conditions. Switching an old CUDA result to CPU does **not** make its historical score exactly reproducible; the existing legacy-score test explicitly requires CUDA because that is where the original was scored.

   **`1e-4` absolute is a reasonable provisional diagnostic threshold, but not an established universal CUDA guarantee.** The repository documents long-horizon divergence from CUDA accumulation order. Specify hardware/software, episode length, genomes, repeat count and whether the bound applies per-world or to per-strain means. Test evolved champions as well as initialization. I have not established a CUDA bound in this review.

   Also qualify “identical for any chunk size” at line 36 by execution mode. Preserve the commitment to record failures rather than silently widening tolerance.

6. **Must fix — Declare the energy bound now.** [T0.md:61](D:/Claude/random/wormWars/docs/foundations/T0.md:61), [test_world.py:45](D:/Claude/random/wormWars/tests/test_world.py:45), [rollout.py:74](D:/Claude/random/wormWars/wormwars/evo/rollout.py:74).

   The existing documented acceptance bound is **relative error below `1e-5`**, checked every tick, normalized by starting total energy. It is not an absolute `ledger_error < 1e-5` requirement.

   Declare the normalization and full-episode coverage now; preferably check each world against its own starting energy. `_play` currently returns only the final residual, so testing that scalar can miss transient violations. Assert finite residuals before aggregation: `max(worst_err, NaN)` can retain the previous finite value at [rollout.py:128](D:/Claude/random/wormWars/wormwars/evo/rollout.py:128).

7. **Should fix — Island configuration boundaries remain unchecked.** [evolve.py:231](D:/Claude/random/wormWars/wormwars/evo/evolve.py:231), [evolve.py:167](D:/Claude/random/wormWars/wormwars/evo/evolve.py:167).

   Unequal island sizes can produce different source and destination slice lengths. I reproduced a shape-mismatch exception with `population=5`, `islands=2`, `migrants=3`. Empty islands and `migrate_every=0` also need defined handling.

   Validate supported configurations up front, or cap migration consistently to both island sizes. Test uneven populations, zero migrants and capacity boundaries. This does not invalidate the three targeted fixes.

8. **Should fix — Strengthen inheritance and migration integration tests.** [T0.md:43](D:/Claude/random/wormWars/docs/foundations/T0.md:43), [test_evo_islands.py:48](D:/Claude/random/wormWars/tests/test_evo_islands.py:48), [brain.py:229](D:/Claude/random/wormWars/wormwars/brain.py:229).

   Add `clone` to the operation list. Use distinguishable values in every field—initial gap weights are identical across strains—and exercise Dale both enabled and disabled. Check that outputs do not alias and mutate their parents.

   The migrant-fitness test verifies the returned number, but never breeds the migrated population. Add a controlled case proving the migrant survives selection with all fields intact. Check all ring edges simultaneously, untouched slots, multiple generations and pre-migration log/snapshot pairing. The current end-to-end test checks only completion and finite best scores.

9. **Should fix — Define timing and category aggregation precisely.** [T0.md:22](D:/Claude/random/wormWars/docs/foundations/T0.md:22).

   Synchronizing around wall-clock timing measures synchronized elapsed time, including CPU work; it is not GPU kernel execution time. Label the metric accordingly. Define nested categories so totals do not double-count, and count a holdout triggered by a snapshot only once—the current implementation performs one evaluation at [evolve.py:134](D:/Claude/random/wormWars/wormwars/evo/evolve.py:134). Test CPU-only operation and exception cleanup.

10. **Minor — D064 slightly overstates the immediate Dale effect.** [DECISIONS.md:1639](D:/Claude/random/wormWars/DECISIONS.md:1639), [brain.py:207](D:/Claude/random/wormWars/wormwars/brain.py:207).

    Migration already copied signed weights, so the immediate forward calculation remained the donor’s. The stale Dale vector corrupts subsequent mutation/clamping. Likewise, stale migrant fitness causes culling when truncation excludes the replaced slots, not invariably. Both bugs and their fixes are real.

island fixes: accept  
T0 plan: revise