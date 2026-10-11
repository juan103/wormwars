**Verdict: revise.** I checked HEAD: it is `cf201da71e13797830ef422b9d4daeb13e3108d4`. This was a read-only review; I used no GPU.

The design addresses the roadmap’s topics, but it does **not yet distinguish useful information transfer from additional circuit capacity, altered motor drive, or environmental mediation**. Its null interpretation is also incomplete. The main blockers are the state clamp, an infeasible matched-cut control, and a diagnostic that does not make cross-module transfer necessary.

Deferring consolidation is consistent with [ROADMAP.md, E4](D:/Claude/random/wormWars/ROADMAP.md:417). Using E3f’s family and replaying the references is also appropriate. However, E3f explicitly requires real module isolation and separation of navigation competence from transfer; v1 has not yet satisfied those requirements. See [E3f RESULTS, “For E4”](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3f/RESULTS.md:165).

The revisions I would require are:

1. **Replace the state clamp with an output-path intervention.**

   The proposal in [design §1](D:/Claude/random/wormWars/docs/E4/E4-DESIGN.md:37) is unsound for §3’s inference.

   Holding all inactive-module neurons at their no-input states removes the changing activity that could carry information through cross-links. Meanwhile, a nonzero clamped state still drives its motor edges. Deleting that neuron can therefore change motor drive directly, including by breaking cancellation between comparator outputs.

   There is also an implementation trap: existing `Brain.step` applies silencing **before** the nonzero clamp. Combining these APIs would restore a silenced neuron to its clamped value. The existing clamp is per strain, whereas maze inhabitants switch modes independently. See [brain.py](D:/Claude/random/wormWars/wormwars/brain.py:334) and [the update order](D:/Claude/random/wormWars/wormwars/brain.py:443).

   **My choice:** gate the inactive module’s motor-output edges while leaving its neural dynamics, sensory inputs and cross-link outputs live. Specify the mode signal, switching threshold, initial state and transition handling. Using `world.goal` would introduce an engineered mode signal; it must be declared, not silently substituted for Q.

   For the cleanest experiment, use the same output gate during training and evaluation in both arms, and recheck the seed’s competence. If training remains ungated, §3 becomes a separate, gate-conditioned assay whose baseline competence must be established.

   Apply lesions at matched saved states entering the tested leg. Whole-episode lesions can damage an earlier A leg and consequently reduce later B visits without any direct neural transfer. Positions, trails, timers and motor states must initially match.

   An engine implementation requires the declared equivalence check with the intervention disabled. “Evaluation only” does not itself exempt changed engine code from rule 7.

2. **Fix the cross-link specification and acknowledge what the mutation mask permits.**

   The edge count is exactly **32**, not “32–50”: each L1 copy has four neurons, giving \(2\times4\times4\) directed cross-links. The existing circuit has eight links wholly inside A/B, 32 comparator-to-motor links, and seven selector links. With the specified frozen parameters, X0 has 65 mutable scalars and X+ would have 97. These counts follow from [the committed L1 module](D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-0/module.json), [organism.py](D:/Claude/random/wormWars/wormwars/e3/organism.py:49), and [tuning.py](D:/Claude/random/wormWars/wormwars/e3/tuning.py:49).

   **My choice:** all 32 cross-links, initially zero. Comparator-only connections are a narrower question and particularly vulnerable to the saturation bottleneck. Zero initialization gives an interpretable common starting phenotype; small random cross-links would introduce an initial-performance difference.

   Distinguish nose-origin from comparator-origin effects descriptively. Nose-to-other-module links can provide direct sensory routing; that is information sharing, but it does not establish transfer of a learned comparator computation.

   Prefer a common union mask, with cross-link weights fixed at zero in X0 and mutable in X+. This also permits matching random draws for common parameters. The existing graft machinery supports zero-valued anatomical slots. See [graft.py](D:/Claude/random/wormWars/wormwars/graft.py:94).

   **A factual correction:** “the relays stay frozen” is too broad. Their τ and biases are frozen; RA→Q and RB→Q weights are mutable. Q’s self-weight, τ and bias, its gate weights, and comparator biases are also mutable. Consequently, the engineered latch and its saturation gating need not survive evolution. “Both arms share the same gating” means the same initial architecture and mutation permissions, not the same evolved gating.

3. **Redesign T2; the proposed matched cut is impossible and its decision rule is wrong.**

   [Design §2](D:/Claude/random/wormWars/docs/E4/E4-DESIGN.md:73) proposes cutting 32 cross-links against the same number of within-module links. **There are only eight existing within-module links.** Counting motor-output edges as “within-module” would change the control’s meaning substantially.

   More fundamentally, useful cross-links need not be more important than equally numerous internal links. Cutting essential internal sensory paths could be more damaging even when cross-links carry useful information. That inequality should not be a necessary condition for transfer.

   Conversely, the proposed inequality does not explicitly require cutting cross-links to hurt relative to intact: two beneficial cuts could satisfy it.

   I recommend:

   - Intact/sham versus all-cross-links-cut as the primary acute dependence contrast.
   - A separate test disrupting the task alignment of transmitted signals while preserving their baseline contribution as closely as possible.
   - Small-cut dose responses, with equal-count internal cuts where feasible, as contextual robustness controls.

   For the latter, match count first, then prespecified source/target classes and weight magnitude within a declared tolerance. Exact equality of summed absolute weights will generally be unavailable. Report mismatch rather than selecting controls by their behavioral damage.

   Weight-slot scrambling alone establishes sensitivity to wiring. It can disrupt recurrent dynamics or tonic bias without showing that task-relevant information was transferred. Add a mean-input replacement or suitably matched source-signal replay/shuffle, and state its limitations.

   Average lesion/permutation draws within each champion. They are not additional independent evolutionary runs.

4. **Replace the hazard sketch with a validated information-necessity diagnostic, and do it before interpreting the main null.**

   The assertion in [design §5](D:/Claude/random/wormWars/docs/E4/E4-DESIGN.md:119) that X0 cannot avoid B-mode hazards is unsupported. A’s motor edges remain live, and evolution can remove its saturation. A can influence B-mode behavior directly. Earlier movement, trails and goal encounters create additional routes.

   Hazard-contact rate alone is also inadequate: a controller can reduce contacts by failing to undertake B journeys. Resetting the goal or ending the leg changes the task and needs a precise scoring rule.

   My preferred diagnostic is a short, controlled B-mode choice:

   - A fresh, randomized cue identifies which of two feasible routes is safe.
   - Only A receives it, after matched initial conditions have been established.
   - A’s motor output is disabled; environmental and peer-mediated communication are excluded.
   - Success requires timely completion of the safe choice. Failure to progress is failure.
   - Cue reversal/shuffling and cross-link removal are prespecified controls.

   Demonstrate that a hand-configured X+ solution using the **actual allowed interface and topology** succeeds, and that X0’s decision is invariant to the hidden cue under matched conditions. This separates architectural feasibility from evolutionary discoverability.

   Run this feasibility check early. If evolution subsequently fails despite a working positive control, the result concerns search under the tested budget. If the positive control fails, a main-task null cannot diagnose evolution.

   The draft is correct that hazards are currently zeroed in the maze world: [maze_world.py](D:/Claude/random/wormWars/wormwars/e3/maze_world.py:236). The sensor mapping and any added neurons must also be specified; “a third nose channel” is not yet an implementation.

5. **Cross the trail conditions with the neural interventions.**

   Evaluating intact champions under shared/own/no trails, as [§4](D:/Claude/random/wormWars/docs/E4/E4-DESIGN.md:104) proposes, measures trail dependence. It does not establish how trails interact with the cross-link effect.

   At minimum, measure intact-minus-cross-cut performance separately under shared, own and no trails. Use matched states or controlled trail replay for the mechanism probes.

   Own trails retain communication across an individual’s earlier and later modes. No trails removes that channel but not information carried by position, heading or prior trajectory. Those matter especially for §3.

   Existing replay and scramble facilities can help, but both retain own trails; neither is complete environmental isolation. See [maze_world.py’s access definitions](D:/Claude/random/wormWars/wormwars/e3/maze_world.py:19).

   A cross-link benefit that occurs only with shared trails can still be useful transfer. Report that dependence. Do not present differences between trail conditions as an additive decomposition of neural versus environmental causation.

6. **Keep the engineered starts; specify the training recipe and competence rules completely.**

   **My choice:** start both arms from E+W2. Defer the from-scratch pair. It asks an additional acquisition question and would consume replication needed for the primary comparison.

   “Mutation σ as E3c” is ambiguous. E3c’s new random-start arms use factor **1.0**, whereas T-F and the reused P-joint cohort use **0.25**. I would retain 0.25 for this engineered-start comparison unless the exploratory pilot motivates a declared change. See [assembly.py](D:/Claude/random/wormWars/wormwars/e3/assembly.py:13), [tuning.py](D:/Claude/random/wormWars/wormwars/e3/tuning.py:49), and [E3c’s configured σ](D:/Claude/random/wormWars/scripts/e3c.py:73).

   Reusing the GA framework is reasonable, but it is not a ready-made E4 runner:

   - E3c’s configuration defaults to the tree family; explicitly select islands everywhere, including training and validation. See [scripts/e3c.py](D:/Claude/random/wormWars/scripts/e3c.py:136).
   - Training maze IDs depend on each run seed. Different arm seeds do not automatically give matched mazes. See [train_ids](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:63).
   - Freeze champion selection, tie handling, checkpoint use and seed namespaces. E3c selects from the final population on validation; it does not simply choose the best learning-curve checkpoint.

   Keep every run in the reported arm comparison. Competence is a qualification of the navigation/transfer claim, not permission to remove unsuccessful runs.

   Finally, nose dependence and “coverer” are different classifications. E3c’s coverer criterion additionally requires coverage and tour matching; [its implementation](D:/Claude/random/wormWars/scripts/e3c.py:1522) is specific enough that it should not be inherited casually on islands. Define mixed and undefined outcomes and the aggregation from champions to arms.

7. **Write an E4 statistical decision system, rather than referring generally to E3c’s.**

   Three corrections are needed.

   First, E3c’s dual margin is **not just the maximum**. “Beyond the margin” uses the larger threshold; “no relevant difference” requires the interval strictly inside the smaller threshold. See [e3c_stats.py](D:/Claude/random/wormWars/wormwars/e3/e3c_stats.py:62). Define the reference mean for E4 and account for its uncertainty.

   Second, pooled exact permutation tests and Welch intervals do not implement a paired-run analysis. If runs are paired through matched training schedules, use an analysis respecting those pairs. For T2, average over mazes within champions and base replication on evolutionary runs. Colony members, mazes and perturbation draws do not replace runs.

   Third, specify the joint decision across T1, T2 and the diagnostic, including multiplicity and practical thresholds. The inherited 0.025 came from E3c’s two contrasts; it is not automatically the right allocation here.

   The intended interpretations should distinguish:

   | Outcome | Supported interpretation |
   |---|---|
   | Relevant T1 advantage plus validated information-disruption effect | Cross-link availability improves performance, with evidence of useful transfer |
   | T1 advantage alone | Benefit of the enlarged architecture under this training recipe; mechanism unresolved |
   | Acute transfer dependence without T1 advantage | Evolved organisms use transfer, without a demonstrated advantage over X0 |
   | Narrow T1 equivalence interval, competent arms, working diagnostic | No material availability advantage under the tested task and training budget |
   | Broad intervals, failed competence or failed diagnostic | Unresolved comparison or failed assay |

   A nonsignificant T1 result does not establish that transfer did not evolve. E3c correctly limits its exact test to exchangeability of distributions, not a mean-benefit claim; retain that distinction.

8. **Complete the pruning, selector-control and budget specifications.**

   [ROADMAP.md](D:/Claude/random/wormWars/ROADMAP.md:439) requires preserved stereo or latch function during pruning, and separate acute/retrained readings. The design omits the preserved-function requirement. If there is no retraining, say so. Specify functional tolerances and keep circuit selection separate from its final evaluation.

   Define `no_latch` for an evolved champion. [The existing constructor](D:/Claude/random/wormWars/wormwars/e3/organism.py:89) builds the seed variant and changes comparator biases as well as gate weights. It is not automatically a selector-only ablation of a trained genome.

   Gene-duplication fate needs functional measurements—cue responses, mode-specific contribution and directional dependence—not just A/B weight divergence.

   The compute estimate also misstates its precedent: E3c trained 8 S-mod, 8 S-dense and **4** P-sel runs; its 8 P-joint runs were reused. See [E3c RESULTS](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:56). Repeated pruning, pair lesions and trail-by-intervention evaluations need their own projection. Their cost cannot be inferred from training time.

**The pilot should measure quantities that resolve these decisions and size the experiment.** Three runs per arm can reveal gross failures, but provide a weak estimate of run variance or failure probability.

Measure:

- **Search behavior:** held-out learning curves, competence/failure frequency, nose dependence, latch behavior, cross-link activation and whether improvement continues near the proposed generation limit.
- **Selection noise:** rank stability among parents and nearby mutants as training mazes per genome increase; champion-selection stability versus validation-block size.
- **Variance:** between-run spread, covariance of paired arms, paired acute-effect spread, and run-by-maze variation. Preserve per-maze outcomes.
- **Assay validity:** inactive motor isolation, X0’s absence of cross-module neural influence, diagnostic positive-control success, sham equivalence, and whether information-disruption controls preserve the intended baseline.
- **Actual cost:** training, validation, state recording, all intervention conditions and bounded pruning at the intended batch compositions. GPU timing waits for authorization.

**Power analysis should simulate the complete E4 decision procedure**, including competence gates, failures, paired structure, reference uncertainty, margins and joint claims. E3c’s [power script](D:/Claude/random/wormWars/scripts/e3c_power.py:1) provides a useful pattern—especially checking simulation labels against the real analysis—but its tree-task variance assumptions cannot size E4.

Require sensitivity analyses for unequal failure rates, skewed/mixed run outcomes and larger variance than the small pilot estimates. Report power for both meaningful benefit and informative equivalence, plus false-positive, wrong-direction and “not evaluable” rates. Choose \(R\), training \(W\), validation/test sizes and \(G\) jointly under the ceiling.

There is also a discrete-test constraint: a two-sided paired label-swap test with six pairs has minimum p-value \(2/2^6=0.03125\), so it cannot reject at 0.025. Larger run counts may also require replacing E3c’s implementation, which materializes every pooled permutation.

Reserve the diagnostic and essential mechanism controls before allocating the remaining budget. Freeze the final sizing rule or publish the pilot-informed specification before the formal run, leaving formal test data untouched.