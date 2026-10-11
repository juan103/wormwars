**Verdict: fix first.** All nine requested test files passed on CPU. I found no gate-wiring, mutation-pairing, or lineage-replay bug. The main problems are lost pilot data, missing measurements, and interpretation rules.

1. **Important — Completed pilot work can disappear.** [scripts/e4.py:236](D:/Claude/random/wormWars/scripts/e4.py:236), [scripts/e4.py:279](D:/Claude/random/wormWars/scripts/e4.py:279). Checkpoints save only generation counts; champion genomes, final populations, and captured selections are never saved. `ctx.salvage` remains empty. A cap exception—including the final check after `body` returns—therefore discards the substantive results. Even successful runs retain only champion hashes and cross-link weights. **Fix:** save populations/champions locally, persist results after each run and assessment, install salvage hooks, and check the cap before each expensive rollout.

2. **Important — Killed-run recovery raises `KeyError`.** [scripts/e4.py:90](D:/Claude/random/wormWars/scripts/e4.py:90), [scripts/e2.py:529](D:/Claude/random/wormWars/scripts/e2.py:529). E4 replaces E2’s `REGISTERED` dictionary without supplying `rerun_kill_tail_seconds`, which inherited kill reconciliation requires. **Fix:** supply an explicit E4 policy and test recovery from a start marker without a completed record.

3. **Important — The pilot cannot supply all requested power-analysis inputs.** [scripts/e4.py:179](D:/Claude/random/wormWars/scripts/e4.py:179), [scripts/e4.py:279](D:/Claude/random/wormWars/scripts/e4.py:279). Finalist validation results are reduced to one mean per strain; selection matrices are discarded; no blind references are played. Consequently, validation-size selection instability and competence failure rates cannot be calibrated from the saved data. **Fix:** retain candidate-by-maze scores and validation legs, measure selection noise across proposed W/block sizes, and replay the blind references. Between-run SD, paired correlation, and P1 maze SD **are** recoverable from the existing test arrays; those need analysis, not extra simulation.

4. **Important — Directional and censored-duration readings are not implemented.** [wormwars/e4/evaluate.py:90](D:/Claude/random/wormWars/wormwars/e4/evaluate.py:90), [scripts/e4.py:144](D:/Claude/random/wormWars/scripts/e4.py:144). `legs` means completed-leg **count**, not duration. Visit timestamps are discarded, so the recorded bundle/directional conditions cannot support §4’s mode-specific comparisons or censored leg durations. The latch summary also proves only equal total counts: misplaced switches can cancel, and a last-tick visit may legitimately precede its switch. **Fix:** retain visit events, censored durations, and switch timing/alignment with a declared latency tolerance. Measure inactive motor current separately; switch counts do not establish its absence.

5. **Important — Claim (a) is correct, but the proposed interpretation is not sound throughout.** [wormwars/e4/stats.py:93](D:/Claude/random/wormWars/wormwars/e4/stats.py:93), [wormwars/e4/stats.py:115](D:/Claude/random/wormWars/wormwars/e4/stats.py:115).
   - D2 cannot infer “constant drive at least in part” when P1-info is **inconclusive**. Separate equivalence from inconclusiveness.
   - Proposed P1 does not identify dependence on a natural tonic component. Say: cutting hurts; this constant replacement improves performance.
   - P6’s “not of the links” overstates what equivalent cutting establishes. Report the positive/negative mean-substitution contrast without resolving its mechanism.
   - `(equivalent, positive, not evaluable)` becomes D8, suppressing evaluable positive P1-info. `(inconclusive, inconclusive, beyond X+ higher)` becomes globally “unresolved” despite positive P2.

   **Fix:** return the three contrast readings independently, then append a joint qualification. Acute evidence should survive P2 incompetence when its own assay is evaluable—including P1-info, not just P1-cut. Preserve valid P2 evidence too. The extra state coverage is useful; nonempty coverage alone does not validate precedence or wording.

6. **Important — Revise the scale rule; qualify claim (b).** [wormwars/e4/scale_rule.py:39](D:/Claude/random/wormWars/wormwars/e4/scale_rule.py:39), [scripts/e4.py:294](D:/Claude/random/wormWars/scripts/e4.py:294). I reproduced factor-1 reach of **0.20855 at 100 mutations** and **0.46875 at 300**; factor 0.25 gives **0** and **0.00375** respectively (20,000 simulations, seed 0). The fallback indeed selects the least exploratory passing candidate.

   However, “X+ is nearly X0 by construction” does **not** follow: 32 smaller weights can affect dynamics collectively, and selection is not neutral drift. Nor is reach impossible at arbitrary longer horizons.

   **Fix:** include 2 and 4 in load screening, retain the smallest candidate meeting both criteria, and explicitly specify what happens if none qualifies. A largest-load-passing fallback is preferable to the current one, but must be labelled reach-deficient. Compute reach for the planned **formal horizon**, with explicit assumptions about lineage mutation counts; a 100-generation pilot’s counts cannot silently represent longer training.

7. **Important — Several tests accept relevant broken implementations.**
   - [test_e4_means.py:55](D:/Claude/random/wormWars/tests/test_e4_means.py:55): I verified that `test_source_means_on_the_validation_play` passes with **all-zero returned means**, and separately with the gate removed.
   - [test_e4_evaluate.py:73](D:/Claude/random/wormWars/tests/test_e4_evaluate.py:73): I verified that both the output-shape test and `test_a_known_cross_link_effect_is_seen` pass with evaluation gating removed.
   - [test_e4_gate.py:101](D:/Claude/random/wormWars/tests/test_e4_gate.py:101): comparing two paths through the current engine cannot detect a regression shared by both.
   - [test_e4_stats.py:87](D:/Claude/random/wormWars/tests/test_e4_stats.py:87): the coverage test accepts any nonempty interpretation, including wrong proposed rows.

   **Fix:** add independently accumulated gated trajectory means, gate-removal sabotage for both evaluation wrappers, a within-tick latch-crossing test, and expected outcomes for proposed table combinations. Retain previous-engine equivalence checks. Historical “seen failing first” cannot be established from these passing tests alone.

8. **Important — Re-evaluation changes batch composition; recorded training composition is wrong.** [scripts/e4.py:207](D:/Claude/random/wormWars/scripts/e4.py:207), [scripts/e4.py:299](D:/Claude/random/wormWars/scripts/e4.py:299). X+ intact is tested among 15 conditions but re-evaluated alone. Under the repository’s exactness limits, that mixes maze resampling with an unvalidated composition change. Training records 256 strains, although each arm’s actual batch has 128. **Fix:** hold composition constant for the noise-band comparison, or establish the relevant equivalence; record actual compositions for every phase. Trail-group timings also do not provide individual-condition costs.

9. **Minor — Avoid unnecessary pilot cost.** [scripts/e4.py:191](D:/Claude/random/wormWars/scripts/e4.py:191), [wormwars/e4/means.py:24](D:/Claude/random/wormWars/wormwars/e4/means.py:24). X0 and E-G receive full source-mean rollouts although their cross-link substitution contributes zero. Every neuron receives float64 tanh processing although only eight sources are needed. **Fix:** skip unused X0/reference means and accumulate the required sources. Keep the X0 sham—it is a useful check.

The checked implementation details are sound: gating reaches training, checkpoint validation, evaluation, and source-mean play; substitution sums by target and remains unclamped; replay peeks the exact parent draw used by `breed`; separate arm batches preserve maze schedules and shared mutation-noise draws. Divergent selection naturally means divergent parents.

The end-state/start-state mean discrepancy is a boundary term:
\[
\bar a_{\rm end}-\bar a_{\rm start}=(a_K-a_0)/K.
\]
With zero initial state, H=1800 and the runner’s 32 substeps, its bias contribution is bounded by approximately **0.000208 per target** at the weight bounds. It is not an accumulating integration error. I would retain the declared end-state definition.

**D246 rulings:** accept requiring an explicit X+ factor; accept practical equivalence despite rejection of exact zero/sign symmetry; accept two separate arm batches; accept factor 0.5 **for exploratory training**, but not as sufficient calibration for a materially different formal factor without sensitivity analysis or a bridging pilot. No GPU was used in this review.