**Revise.** The core mechanisms largely match v3.2. The blockers are the equivalence evidence and step-0 verification/provenance, not a demonstrated error in the live bit or controller equations.

I checked `436a73c` on `roadmap` and compared its changes with its parent. I did not execute project code or tests.

1. **Medium — rule 7’s test does not establish equivalence against the previous engine.**  
   [test_e03h_food_fell.py:157](D:/Claude/random/wormWars/tests/test_e03h_food_fell.py:157) compares pinned-interface and level-interface rollouts **using the changed engine on both sides**. This satisfies the narrower interface comparison in design §3, for the tested compositions. It does not satisfy [T1.md:118](D:/Claude/random/wormWars/docs/foundations/T1.md:118), which explicitly requires an independent pre-change reference.

   It also checks only score; the class-E contract names energy, alive count, eaten, pellets and starting food. CUDA coverage is `(64 strains, 16 worlds, 20 weys)`, not the planned selection composition `(256, 16, 20)`. Add a pre-change reference comparison at the claimed composition and endpoints. The present tests should retain their narrower description.

2. **Medium — step 0’s zero-tolerance CUDA verification runs outside `replay_mode()`.**  
   [e03h_step0.py:81](D:/Claude/random/wormWars/scripts/e03h_step0.py:81) calls `rollout` without a deterministic context, then drops step 0 on any difference. The repository explicitly limits guaranteed CUDA exactness to replay mode. Default-mode nondeterminism could therefore cause a false rejection of an otherwise correct reconstruction.

   Establish and record the verification’s execution mode, with deterministic setup before CUDA work. There is a qualification: 03’s original driver also used default mode, so wrapping the new run does **not** guarantee equality with the historical file. That equality still has to be observed; keep the registered zero tolerance and drop rule.

3. **Medium — step 0 can report clean provenance while using modified reference data.**  
   [e03h_step0.py:44](D:/Claude/random/wormWars/scripts/e03h_step0.py:44) omits `experiments/03-generation0/pilot.json` from `GUARDED`, although that file supplies the bank, gains and fitness. Its content hash is also absent from the output provenance.

   A concrete failure: change only the bank in `pilot.json`. The fitness verification can still pass, while history is measured against an altered bank and the record says `dirty: false`. Guard and hash the input file. Include other consumed experiment inputs in the provenance inventory.

4. **The step-0 regeneration recipe itself matches §7.2. Its negative path is untested.**  
   [e03h_step0.py:48](D:/Claude/random/wormWars/scripts/e03h_step0.py:48) correctly reuses stored gains, rebuilds `pilotSH101`–`pilotSH116` through SH with 20 passes, uses `genome_seed(name, "")` without `+1`, and draws all 256 genomes in one device-local call. Verification uses the original worlds, run seed and 4,096-world chunk. It avoids recalibration. H, S and the between-graph sample SD are calculated as specified.

   [test_e03h_step0.py:17](D:/Claude/random/wormWars/tests/test_e03h_step0.py:17) exercises only `run(smoke=True)`, which deliberately bypasses the verification stop. It does not test that a mismatch prevents history measurement, that equality permits it, or that `main` writes and guards the record. Add controlled tests of those branches before spending GPU time.

5. **The live bit and transition-count conventions match §3 for the declared T1 interface.**  
   [world.py:903](D:/Claude/random/wormWars/wormwars/world.py:903) applies sensor gain and input gain, clamps, then compares strictly with the previous reading. The first relief bit is zero; each wey has its own state; dead weys are masked at sensing time; hidden events do not reset history.

   Counts use `2 * previous + current`, correctly yielding `N00, N01, N10, N11`. Counting starts at tick index 2, excluding the forced-zero tick as a transition’s start. Both endpoints must be alive when sensing; cloning the previous alive mask correctly protects it from `_reap`’s in-place mutation. A new `World` starts a new history.

   **Test gap:** [test_e03h_food_fell.py:66](D:/Claude/random/wormWars/tests/test_e03h_food_fell.py:66) does not deliberately force clamp binding or death, nor assert those events occurred. Add explicit sequences covering two unequal readings that clamp equal, a fall below the clamp, distinct weys, and death between transition endpoints. Compare against actual constructed current, not solely another copy of the gain/clamp expression.

6. **The sham is correctly keyed and updated, with one unregistered edge case.**  
   [world.py:910](D:/Claude/random/wormWars/wormwars/world.py:910) uses a separate stream keyed by run seed, world ID, tick, swarm and wey—not genome, graph or batch position. Its latent state continues independently of food and death; only injection is masked. For positive `p01 + p10`, stationary initialization and both transition probabilities are correct.

   **Medium, before the pilot:** validation accepts `(0, 0)`, and line 914 silently chooses an all-zero start. The design’s stationary formula is undefined there. Although zero is one stationary distribution of that chain, this particular choice was not specified. Reject the case or explicitly resolve it in the design.

   The stationary-start test is weak: [test_e03h_food_fell.py:130](D:/Claude/random/wormWars/tests/test_e03h_food_fell.py:130) checks occupancy averaged over 200 ticks. An incorrectly all-zero start can mix rapidly and pass. Test the **first tick** directly. The future rate estimator must separately enforce the registered zero-denominator stop.

7. **The scripted equations and claimed identities are correct within T1.**  
   [scripted.py:47](D:/Claude/random/wormWars/wormwars/e03h/scripted.py:47) compares against the previous memory before updating it. The explicit `T == 1` branch stores the current level directly, avoiding cancellation error. With memory enabled and bit disabled, it reproduces `MemoryKinesis`, including its threshold. The two enabled sources combine by OR.

   `BitKinesis` reproduces zero-threshold `MemoryKinesis` on live T1 weys: mono left/right currents coincide, ASK’s pheromone current is zero, and both policies use the same speed and turn rules. Their commands can differ for newly dead weys because `MemoryKinesis` sees its food current fall to zero; those commands are masked from world actions. Thus the meaningful identity is live policy/world behavior, not every dead-we y internal command.

   Tests should compare commands and memory states on prescribed sequences, including conflicting bit/memory indications and the longer-timescale recurrence. Equal final scores alone are weaker evidence. The eventual gate must explicitly include `GradedKinesis` in the required unions and retain settings that ignore the bit; the two new classes alone do not establish family nesting.

8. **The interface and ASK cap match §3.**  
   [interface-03h.yaml:60](D:/Claude/random/wormWars/configs/interface-03h.yaml:60) adds only ASK injection at 0.25; existing mappings, gains, sampling and motors are unchanged. [samplers.py:292](D:/Claude/random/wormWars/wormwars/exp03/samplers.py:292) passes the ASK additions through both chemical/gap count constraints and weight capping, while preserving the old paths.

   Tests check both matrices’ counts and weights and include a useful uncapped counterexample. ASK’s zero count cap makes its weight bound automatic; these tests do not independently exercise a positive ASK weight cap. That is a coverage limitation, not a defect for this connectome.

9. **History and partial Spearman match their specified primitives; later reporting remains to be implemented.**  
   [measures.py:92](D:/Claude/random/wormWars/wormwars/exp03/measures.py:92) preserves the original probe schedule and default calculations. The added values support the specified H_dir as `abs(falling motor turn) − abs(rising motor turn)`. Missing `food_fell` in the frozen bank contributes zero through `_current`.

   [stats.py:11](D:/Claude/random/wormWars/wormwars/e03h/stats.py:11) implements average ranks, intercept regression and residual correlation, with numerically zero residuals flagged as zero. Add explicit tied-rank and constant-S tests. Nonfinite inputs currently can produce an unflagged NaN or a linear-algebra error; reject them explicitly.

   Crossed inference, flagged-graph sensitivity, sham-rate fitting, occupancy reporting and gate orchestration are not implemented here. That is consistent with reviewing step 1, but these primitives do not yet establish compliance with all of §§4–7.

10. **I found no change to earlier experiments’ scientific behavior in this diff.**  
    Unset fields are omitted by `Config.to_dict`; the pinned interface is unchanged; `KINDS` is unchanged; legacy sampler paths retain their RNG operations; history’s default output retains its formulas and keys; existing scripted policies receive the same arguments.

    The sampler regression hash matches the committed 03a setup record. However, the hash test covers one legacy graph, and the history test compares two calls to the current implementation. These support compatibility but do not replace the missing pre-change engine comparison in finding 1.