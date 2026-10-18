**Ready for step 0, with small fixes to the equivalence checker.** I found no error in the core T1 manipulation or step-0 reconstruction that warrants another design revision.

I checked `7b8edbf` on `roadmap`, including the diff against `6facc3d`. I only inspected files and Git metadata; I did not execute project code or tests. The numbering below follows Astra’s round-1 findings.

1. **Rule 7: addressed for the recorded cases, but the new checker has a medium-severity false-pass bug.**

   [e03h_equivalence.py:101](D:/Claude/random/wormWars/scripts/e03h_equivalence.py:101) defines inequality as `abs(got − ref) > 0`. A NaN difference makes that expression false, so a nonfinite endpoint can receive `bit_equal: true`. Subtraction also permits broadcasting instead of requiring identical shapes. For example, a mistakenly collapsed `food_start` array can match because starting food repeats across strains.

   Require identical shapes and finite inputs, then compare values directly. Add sabotage tests for a finite mismatch, NaN, and a broadcastable shape mismatch. **The existing records report finite maximum differences of zero, so the NaN bug does not invalidate those recorded comparisons.**

   The new check does cover all six class-E endpoints, against a separately saved reference, for N2 at CPU `(64,16,20)` and CUDA `(256,16,20)`, with CUDA rollouts inside `replay_mode()`. It covers those cases—not all compositions, graphs, or T1.md’s wider mode/shape matrix.

   **Remaining provenance weakness:** [line 79](D:/Claude/random/wormWars/scripts/e03h_equivalence.py:79) defaults reference generation to the current checkout. Neither the NPZ nor comparison JSON records the reference commit, dirty status, reference hash, or environment. An accidental current-engine reference would therefore be accepted. The old worktree exists at `6facc3d`, consistent with D327, but that alone cannot authenticate the saved NPZ. Require the intended reference revision and record its provenance.

2. **Round-1 #2, step-0 execution mode: resolved.**

   [e03h_step0.py:84](D:/Claude/random/wormWars/scripts/e03h_step0.py:84) now encloses CUDA genome construction, verification, and history measurement in `replay_mode()`, and records the mode.

   The historical qualification remains correctly stated: 03 ran in default mode. Deterministic execution now does not guarantee equality with `pilot.json`. The zero-tolerance rejection remains appropriate; do not relax it after seeing a mismatch.

3. **Round-1 #3, step-0 input provenance: resolved.**

   [e03h_step0.py:48](D:/Claude/random/wormWars/scripts/e03h_step0.py:48) guards both `pilot.json` and `remaps.json`; [line 81](D:/Claude/random/wormWars/scripts/e03h_step0.py:81) records their content hashes. The earlier altered-bank/clean-provenance failure is closed. Shared provenance also records the connectome hashes.

4. **Round-1 #4, reconstruction and verification branches: resolved, with a small remaining integration-test gap.**

   [e03h_step0.py:60](D:/Claude/random/wormWars/scripts/e03h_step0.py:60) matches §7.2 and `scripts/exp03.py`:

   - The committed pilot contains exactly `pilotSH101`–`pilotSH116`; reconstruction uses their integer seeds and 20 SH passes.
   - Each reconstruction draws 256 genomes in one device-local call, using `genome_seed(name, "")`, without `+1`.
   - Stored motor gains are reused; calibration is not rerun.
   - Verification uses the original world IDs, run seed, T1 configuration, and 4,096-world chunk.
   - H and S use the correct absolute raw-turn differences; fitness is averaged over worlds; between-graph spread uses sample SD.

   [test_e03h_step0.py:48](D:/Claude/random/wormWars/tests/test_e03h_step0.py:48) now tests both rejection before history and continuation after equality. Unlike the equivalence checker, step 0 uses `(diff == 0).all()`, so NaNs reject.

   The remaining gap is that these tests call `run()`, not `main()`: they do not exercise dirty-input rejection, environment checks, or writing the final provenance-bearing record.

5. **Round-1 #5, live bit and transition conventions: resolved for T1.**

   [world.py:906](D:/Claude/random/wormWars/wormwars/world.py:906) matches §3: gain and clamp precede the strict comparison; the first relief bit is zero; state is per wey; dead weys receive zero; hidden events do not reset history. With this interface, the reconstructed food current equals the current at the food sensor neuron.

   Counts encode `2 × previous + current`, yielding `N00,N01,N10,N11`. They start at tick index 2, exclude the forced-zero tick as a transition’s start, require both sensing-time endpoints alive, and cannot cross newly constructed worlds. Cloning the previous alive mask is correct.

   The added crafted test covers clamp binding, falls, separate weys, and death. **Residual coverage limitation:** [test_e03h_food_fell.py:224](D:/Claude/random/wormWars/tests/test_e03h_food_fell.py:224) calls `_food_fell` directly; it still does not compare the crafted sequence against actual `_build_current` output. An integration assertion would close that part of the original request.

   The injected-bit counts also exclude the first transition under sham, although sham starts stationary. That common counting convention should remain explicit in reporting.

6. **Round-1 #6, sham initialization and transitions: resolved. One seed-contract detail remains before the pilot.**

   [world.py:913](D:/Claude/random/wormWars/wormwars/world.py:913) correctly implements stationary occupancy `p01/(p01+p10)`, transitions `0→1` with probability `p01`, and `1→0` with probability `p10`. The latent sequence is food-blind and keyed by run seed, world, tick, swarm, and wey—not strain, graph, or batch position. Death masks injection without altering the latent sequence.

   `(0,0)` is now rejected, and the first-tick occupancy test addresses the previous weak test. The future estimator must still separately reject either zero transition-count denominator.

   **Low severity, before pilot registration:** §5 promises disjoint sham and world seeds, while [_keyed_uniform:815](D:/Claude/random/wormWars/wormwars/world.py:815) derives sham randomness from the same `run_seed` used for maps, with a separate stream tag. Domain-separated streams may satisfy the statistical intent, but there is no independently selectable sham seed. Either implement separate root seeds or explicitly reconcile the registration with this derivation. This does not affect level-only step 0.

7. **Round-1 #7, scripted equations and identities: resolved within the stated T1 scope.**

   [e03h/scripted.py:47](D:/Claude/random/wormWars/wormwars/e03h/scripted.py:47) compares against the previous memory before updating it. The `T == 1` branch stores the current level directly, preserving exact `MemoryKinesis` behavior with memory enabled and bit disabled, including nonzero thresholds. Longer-timescale recurrence and the OR combination are correct.

   `BitKinesis` equals zero-threshold `MemoryKinesis` **for live T1 weys and resulting world behavior**: mono food currents coincide, and ASK’s pheromone contribution is zero. Newly dead weys can produce different internal commands because memory sees the food current become zero while the bit is masked. Actions are masked, so this does not break the meaningful identity.

   Prescribed-sequence tests now cover commands, conflicting sources, source switches, and the slow recurrence. The eventual gate must still construct the required unions with `GradedKinesis` and include bit-ignoring settings.

8. **Round-1 #8, interface and ASK caps: still correct.**

   [interface-03h.yaml:61](D:/Claude/random/wormWars/configs/interface-03h.yaml:61) adds only the ASK channel at gain 0.25; existing mappings and motor settings remain unchanged.

   [samplers.py:292](D:/Claude/random/wormWars/wormwars/exp03/samplers.py:292) propagates ASK additions through chemical and gap count constraints and weight caps. Both new ensemble names are separate from `KINDS`.

   Tests cover both matrices and an uncapped counterexample. The previous limitation remains: ASK’s zero direct-edge cap makes its weight bound automatic; these tests do not independently exercise a positive ASK weight cap.

9. **Round-1 #9, history and partial Spearman: resolved at the primitive level.**

   [measures.py:92](D:/Claude/random/wormWars/wormwars/exp03/measures.py:92) preserves the frozen schedule and original default outputs. Per-history readouts support the specified falling-minus-rising absolute motor-turn measure. The frozen bank supplies no `food_fell`, so its contribution is zero.

   [stats.py:11](D:/Claude/random/wormWars/wormwars/e03h/stats.py:11) implements average ranks, intercept regression, residual correlation, and flagged-zero degeneracy correctly. Ties, constant covariate, and nonfinite-input tests were added.

   Crossed inference, flagged-graph sensitivity, sham-rate fitting, occupancy reporting, and gate orchestration remain future work. That is consistent with step 1; this review does not certify the later pipeline.

10. **Round-1 #10, earlier experiments: no scientific behavior change found.**

    The diff preserves the pinned interface, legacy sampler RNG paths, `KINDS`, history’s default keys/formulas, and existing scripted-policy arguments. Unset config fields are omitted from serialization. The legacy sampler test’s expected hash matches the committed 03a setup record.

    There are additional inert world attributes and small allocation overhead, but I found no changed earlier-experiment scores, hashes, or default scientific outputs attributable to this patch.

    One factual correction to the question: **GPU work beyond the test suite has occurred.** [D327](D:/Claude/random/wormWars/DECISIONS.md:10129) explicitly records the separate CUDA equivalence run. The accurate statement is that step 0, the gate, pilot, and formal experiment have not run.