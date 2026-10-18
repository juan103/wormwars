**Revise.** Fix the CUDA search path before any pilot-dev run. Also strengthen implementation controls, correct the timing projection, preserve partial results, and improve the longer-search diagnostic before spending the six-hour budget.

I verified HEAD is `a4956e5e9df9fe5e01bf0f9acf8eb2c56acf895d` on `roadmap`. This was a static review; I did not execute tests, scripts, or experiments.

1. **Blocking — the search passes CPU genomes into CUDA rollouts.**

   [`scripts/e03a.py:384`](D:/Claude/random/wormWars/scripts/e03a.py:384) constructs `Reinsertion` without a device argument, so its genomes are on CPU. [`search.py:325`](D:/Claude/random/wormWars/wormwars/e03a/search.py:325) concatenates those genomes and passes them directly to `rollout(..., device="cuda")`.

   `rollout` constructs `Brain(sub)` without moving the genome (`wormwars/evo/rollout.py:168–175`). The world constructs CUDA inputs; `Brain.step` then combines them with CPU parameters. The first tuning rollout will fail with a device mismatch.

   Move the genome and its spec to the requested device before rollout, as `arms.counts` already does. Add a device-contract regression check and put a tiny CUDA integration check before the expensive evolution stages. The existing CPU smoke test cannot detect this.

2. **High — failed implementation controls do not prevent further spending, and the CUDA replay control checks too little.**

   [`scripts/e03a.py:360`](D:/Claude/random/wormWars/scripts/e03a.py:360) and line 365 merely record restoration/deletion equality. A failed check still produces a completed baseline record, which `full` accepts.

   Likewise, [`scripts/e03a.py:650`](D:/Claude/random/wormWars/scripts/e03a.py:650) calls the full replay successful whenever the **integer target counts** agree. Different actions and trajectories can produce identical counts. The CPU unit test is stronger: it compares actions, final positions, and counts.

   Furthermore, these exactness checks do not enter `replay_mode()`, despite the repository’s explicit condition for CUDA exactness.

   Required changes:

   - Make restoration, NIP deletion equivalence, and replay-control failures stop dependent stages.
   - Run exact CUDA comparisons under the documented deterministic settings and matched composition.
   - Compare trajectory/action or state evidence, not counts alone.
   - Assert KT/KTM invariance in the driver; currently it only records their counts.

   The replay wrapper’s timing itself looks correct: rebuilding before step `t+1` implements the specified intervention, with the first potentially affected action at `2L+1`.

3. **High — the report does not yet provide a defensible measured budget projection.**

   [`scripts/e03a.py:662`](D:/Claude/random/wormWars/scripts/e03a.py:662) computes rates as **worlds built per second**, but the projection uses incompatible workloads:

   - Evolution’s 266,496 episodes include checkpoint validation, yet all are priced using the `selection` rate. Validation has its own `holdout` timing and different composition.
   - Scans are measured under `measure`, but projected using `final`.
   - Formal probe counts are **episode-equivalents**, including replay work; the measured probe rate counts actual worlds and mixes scripted, ordinary, bounded-replay, and full-replay episodes.
   - Pilot-dev evolves two runs together; it does not measure the five-NIP/eight-intact compositions specified in DESIGN §3.
   - Missing rates silently become 420/s. `report` does not even require a completed `probe` record before making its projection.

   There is also a concrete arithmetic error at line 682: pilot-check evolution is priced as **16 evolutions**, whereas DESIGN §10 specifies **14**: two graphs × six evolutions, plus two possible re-evolutions.

   Record timing by workload **and composition**, separate validation from selection, and use consistent units for probes. Any extrapolation should be identified explicitly. The 32-world permission must follow a corrected projection; its current `allowed` flag is not sufficient evidence.

4. **High for diagnostic usefulness — the longer search does not adequately resolve D308’s concern.**

   [`scripts/e03a.py:540`](D:/Claude/random/wormWars/scripts/e03a.py:540) gives the 200-generation searches different seeds from the ordinary searches. Line 597 reports the difference between two long-search means and five unrelated short-search means. That is a noisy comparison of two restart samples, not a direct measurement of improvement from generations 100 to 200.

   More seriously, Q trajectories, AUCs, turnover, and acceptance diagnostics are exported only for labels beginning with `free` (lines 573–583). **The longer searches receive none of these anatomical diagnostics.** Their final counts alone cannot establish whether anatomical recovery is still improving after functional performance plateaus.

   Save the 100-generation state of each long search and evaluate it alongside its 200-generation state. Export both anatomical and functional changes, with the relevant final rankings/states retained locally. This costs little additional simulation compared with the current long-search allocation.

   Also correct the Q timestamps: `cold_masks[::10]` currently samples generations **1, 11, …, 91**, followed by 100—not 10, 20, …, 100. Include initial Q and a chance reference.

   **Is 100 generations plausible?** For some functional improvement or partial enrichment, possibly. For dependable partner recovery, there is no supporting evidence yet. With one move per offspring, the four replicas collectively propose about 1,067 partner moves at `p_move=1/3`, or 1,920 at `0.6`. These are proposed moves across separate lineages, not accumulated discoveries in the returned state. The 16-candidate test supplies a noiseless, directly anatomical fitness oracle; the real task is much less informative. I would retain 100 as a development starting point, not treat it as an established adequate budget.

5. **High budget risk — reaching the cap can discard the measurements already purchased.**

   [`scripts/e03a.py:271`](D:/Claude/random/wormWars/scripts/e03a.py:271) calls evolution without its available `on_checkpoint` persistence hook; candidates are saved only after evolution finishes. Tuning rounds and full-search states likewise remain in memory until their stages finish.

   If `CapReached` occurs, the exception handler records the error and accounting, but not the partial scientific results. A failed `full` record then prevents `report` from extracting resolution or diagnostics. With a nominal 5.4-hour plan inside a six-hour cap, this is a practical risk.

   Persist evolution checkpoints, completed tuning rounds, and periodic search checkpoints. Allow a partial report that clearly identifies incomplete workloads. Check the cap before setup’s GPU work as well; setup currently does not call `ck.check()`.

6. **Medium — the pilot driver violates the shared-permutation rule across arms.**

   [`scripts/e03a.py:565`](D:/Claude/random/wormWars/scripts/e03a.py:565) seeds the anatomical null with `null_seed + bi`. MIP and NIP for the same target have different `bi`, so they receive different permutations.

   DESIGN §6 explicitly requires each target’s draw to apply jointly across connection types, brains, searches, **and arms**. The library correctly shares a permutation across types and brains within one call; the driver breaks sharing across arms.

   Key the permutation bank by target, not target-brain. This does not invalidate each marginal p-value, but it is a clear implementation mismatch that the tests miss.

7. **Medium — family 2 should reject or withhold non-finite brain values.**

   [`stats.py:72`](D:/Claude/random/wormWars/wormwars/e03a/stats.py:72) checks missing collections and their lengths, but not their values. A five-element collection containing `NaN` reaches `exact_p`; every comparison against the resulting `NaN` is false, producing **p = 0**.

   Its own effect-floor check will fail, but that artificial zero enters Holm and can make another target easier to reject.

   Validate finite, valid AUCs before testing; incomplete targets must retain p = 1. Add a test for an individual missing/non-finite brain, not only an entire collection set to `None`.

   For finite inputs, the exact 252-split test, one-sided tail, Holm implementation, observed-effect floor, and explicit withholding behave as designed. The committed validation records rates of **0.0408, 0.03765, and 0.03805** for the three null scenarios, all below 0.0531. The unequal-variance rates are correctly labelled robustness results. The relevant code is unchanged from the validation’s recorded commit.

8. **Medium documentation issue; acceptable implementation choice — NIP pinning works, but it changes initialization.**

   [`arms.py:36`](D:/Claude/random/wormWars/wormwars/e03a/arms.py:36) zeros every edge touching X, and the mutation scales keep those edges zero. For eligible, unmapped targets, the isolated neuron cannot affect the rest of the network. I accept this batching approach for pilot-dev.

   However, equivalence of the resulting dynamics does **not** make it the same initialization experiment as constructing a deleted mask. `Genome.random` normalizes chemical and gap magnitudes using the intact mask’s anatomical means (`wormwars/brain.py:214`, 228). Those means include X’s edges.

   The plan discloses this, appropriately. Add a dated design annotation accepting the shared intact normalization and state its information content precisely: NIP has no functional exposure to X during evolution, but its initialization scale is derived from the intact graph. Do not describe the change as purely computational.

9. **Medium — the tuning plan is usable development, but its uncertainty needs to remain visible.**

   The two highest-relevance representatives are a reasonable choice for obtaining a detectable search signal with two targets. They do not establish transferable diagnostic thresholds for low-relevance targets, and their relevance comes from a different, single selector brain. Report their actual MIP deletion deficits before interpreting search performance.

   Rounds A/B/C implement the stated sequential rules, including reusing the previous winner and keeping truth out of the selection criterion. Two searches per setting and target-brain make the B/C decisions noisy; the 0.02 rule is an operational preference, not evidence of a reliable improvement.

   Round A currently aggregates all neighbour swaps into one rate (`scripts/e03a.py:419`). An acceptable average can conceal a nearly closed cold/hot boundary. Retain per-neighbour rates for choosing and assessing the ladder.

   The `full` calculations of δ_eval and δ_search match the stated **pilot-dev** definitions. They will provide useful preliminary measurements after the driver fixes. The formal δ_search fraction must still come from **pilot-check**, as DESIGN specifies. Freeze the extraction rule beforehand.

10. **Implementation assessment — most core mathematics and graph handling match v7.1.**

   I found no substantive discrepancy in:

   - Union-mask construction, candidate inclusion, edge-identity background copying, self-loop handling, and saved restoration.
   - Partner-independent search initialization and proposals; fixed partner counts; symmetric gaps; random refits’ within-stratum counts.
   - Replica replacement and swap signs, alternating swap schedule, and returning the coldest replica’s final state.
   - Kind precedence, degrees with X removed, tertile boundaries, unsplit ties, and small-bin merging.
   - Joint truth-pattern support, tied-rank ROC AUC, equal weighting of scoreable types and brains, and the finite-sample enrichment p.
   - Three-state boundaries and per-brain reliability/outcome helpers.
   - Panel selection and the implemented structural ranking formulas.
   - Replay rebuilding and KT/KTM/KTS state handling.

   This is not yet the complete formal analysis pipeline. For example, `full` does not export the mirror-zero subset analysis, interface/non-interface recovery, precision-at-k null results, or the composite structural contrast. Five-brain target-arm aggregation and the final registered readings are also not exercised end to end. Those need completion before the formal protocol is frozen.

11. **Test audit — meaningful coverage, with several claims stronger than their assertions.**

   I read all eight test files. The following covers the implementation-test mapping and the additional tests.

   | Tests | Assessment |
   |---|---|
   | [`test_e03a_reinsert.py:75`](D:/Claude/random/wormWars/tests/test_e03a_reinsert.py:75): union/exact partner network, deletion/re-indexing, background, restoration, self-loop, direction, gap symmetry, wrong-source refusal | Substantial checks of the stated properties. The union reference copies parameters from the materialized union, so direction/background/restoration tests are necessary complementary checks. Coverage is CPU and selected targets. |
   | Reinsertion-file NIP initialization/mutation test, line 178 | Tests a **deleted mask**, where missing edges cannot regrow. It does not test the actual intact-mask pinning implementation. The arms tests supply that coverage. |
   | [`test_e03a_arms.py:41`](D:/Claude/random/wormWars/tests/test_e03a_arms.py:41): real evolution pinning and sabotage | Checks pinning through the tested generations. The claim that intact runs are “unchanged” is stronger than the assertion: it checks initial weights and nonzero final X edges, not equality with an ordinary intact evolution. |
   | Arms deletion/scoring tests, lines 62–90 | Exercise integration, but equality of counts over 12 ticks can pass despite dynamical differences. The neural-state tests provide stronger supporting evidence. |
   | [`test_e03a_search.py:121`](D:/Claude/random/wormWars/tests/test_e03a_search.py:121): information boundary and two sabotage cases | Useful checks of initialization and proposals under changed truth and fixed allowed background. They do not exercise the actual CUDA scoring path. |
   | Search counts/refits, random-refit composition, ranking | Check their claimed invariants meaningfully. |
   | Planted optimum and no-move sabotage | Establish that topology search can work on the small oracle problem. They do not establish scalability. The sabotage uses a different problem size and generation budget from the positive test. |
   | Search acceptance/swaps, line 246 | Checks improving replacement, effectively impossible worsening acceptance, and favourable swaps. It does **not** verify intermediate Metropolis probabilities, adverse swaps, both swap parities, or explicitly assert the coldest-result contract. Wrong temperature scaling could pass. |
   | Search common-world and identical-state tests | The fake rollout checks world scheduling well. The real test compares only counts from a short CPU episode; it does not cover CUDA device placement or trajectory equality. |
   | [`test_e03a_null.py:30`](D:/Claude/random/wormWars/tests/test_e03a_null.py:30): kinds, bins, degree, permutations, AUC, aggregation, ties, support, precision/AP | Generally meaningful small-case checks. None checks shared permutation draws across arms in the driver. |
   | No-task statistical check and sabotage, lines 157–186 | Useful smoke checks against gross bias. Twenty-four replications with broad acceptance bounds do not establish calibration or exclude modest bias. |
   | [`test_e03a_stats.py:13`](D:/Claude/random/wormWars/tests/test_e03a_stats.py:13): Holm, exact/scalar/batched tests, floor/withholding, simulation, verdicts, outcomes, reliability | Meaningful for the supplied finite examples. Missing-value coverage is incomplete, as finding 7 shows. The validation simulation measures Holm rejection without the floor, which is conservative for the additional floor filter. |
   | Stats paired-bootstrap test, line 91 | Constant paired differences verify pairing, but cannot establish correct brain resampling or shared resampling across brains/targets. Calling `world_resamples` twice with identical arguments only establishes reproducibility. |
   | [`test_e03a_panel.py:26`](D:/Claude/random/wormWars/tests/test_e03a_panel.py:26): eligibility, representatives, tiers/fallbacks | Useful coverage. The reachability sabotage tests loss of an outgoing path; it does not independently establish the incoming-path requirement. |
   | Panel relevance interval, line 60 | **Too weak for its name.** Every brain/world has the same target-specific drop. Incorrect resampling—or no bootstrap—can return the asserted result. Add heterogeneous brain and world effects with an independent expected calculation. |
   | Structural tests, lines 95–124 | Mirror direction/fallback examples are useful. The class-model test checks range and truth exclusion, not probabilities against hand-counted opportunities; an all-zero predictor could pass that portion. |
   | [`test_e03a_probe.py:47`](D:/Claude/random/wormWars/tests/test_e03a_probe.py:47): full replay, rebuild, prescribed sequence, calibrators | Stronger than the driver’s controls. The timing test proves equality through `2L` and some later effect; a delayed intervention could still pass. Use a prescribed sequence that forces a difference exactly at `2L+1`. |
   | [`test_e03a_script.py:27`](D:/Claude/random/wormWars/tests/test_e03a_script.py:27): end-to-end smoke, accounting, rerun protection, hash sabotage | Checks CPU plumbing, record shape, and the stated rerun/hash protections. It does not validate projection arithmetic, device transfer, cap recovery, or rejection of failed implementation controls. |

12. **Low — the mutation record supports less than “each core check was seen failing” suggests.**

   [`mutation_check.py:56`](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/mutation_check.py:56) counts **any nonzero pytest exit** as a killed mutation and preserves no failure details. Collection errors and unrelated failures would also count. The selected mutations also do not cover every core property.

   The surviving `>` mutation is indeed equivalent under the existing probabilistic branch; that explanation is correct.

   Preserve the failing assertion/output and distinguish assertion failures from test infrastructure errors. Describe this as selected mutation evidence, not comprehensive validation or a replacement for the disclosed tests-after-code exception.