**Revise D312.** Most numerical summaries and the fixed budget reading stand, but several corrections and two material omissions are needed.

**Recommendation: (b)—use a tightly specified check within the remaining 1.42 pilot-dev hours to diagnose and amend the search; proceed to pilot-check only if it demonstrates useful improvement, otherwise choose (c).**

I checked `roadmap` at `374f88c` against the records and metric definitions. I made no changes and ran no experiments or tests.

1. **High — the missing headroom results materially change the interpretation.**

   Sources: [baseline.json](/D:/Claude/random/wormWars/experiments/03a-self-consistency/pilot-dev/baseline.json), `target_brains[].deletion_deficit`; [panel.json](/D:/Claude/random/wormWars/experiments/03a-self-consistency/pilot-dev/panel.json), `relevance`; [full.json](/D:/Claude/random/wormWars/experiments/03a-self-consistency/pilot-dev/full.json), `target_brains[].comparisons.headroom` and `attributes`.

   | Target-brain | MIP deletion deficit | Reference minus deleted | Headroom present? | Reliable reference? |
   |---|---:|---:|---|---|
   | MIP/URXL | 1.7832 | 1.6512 | Yes | No |
   | MIP/PLNL | 0.0127 | −0.0104 | No | Yes |
   | NIP/URXL | — | 0.0521 | No | Yes |
   | NIP/PLNL | — | 0.0065 | No | Yes |

   Both targets had selector deficits of **2.0586**. PLNL therefore illustrates a substantial failure of relevance to transfer between brains: its MIP deficit is only **0.13p**.

   The reported outcome labels follow the rules. But **all three included “functional success” outcomes lack demonstrated headroom above p**. They do not establish successful reconstruction of an important missing contribution. The only target-brain with substantial headroom is excluded.

   D312 should state this explicitly. Also, the concern for pilot-check is **criterion 4 as well as criteria 5 and 6**: neither pilot-dev target has NIP headroom. Under the analogous criterion-5 eligibility calculation, there are no qualifying targets.

2. **Low — the main arithmetic and outcome classifications are correct.**

   Sources: [tune.json](/D:/Claude/random/wormWars/experiments/03a-self-consistency/pilot-dev/tune.json), `rounds`; `full.json`, resolution fields, `comparisons`, `enrichment`, `attributes`, and `longer`.

   - Round A’s mean swap rates are **0.79167, 0.87500, 0.94583**. Its choice is correct under the fallback rule: the worst pair is **0.9000** for the selected ladder, versus **0.9125** for the colder ladder. Selection was not by the lowest mean.
   - Round B’s largest departure from the retained setting is **0.010376**; round C’s alternative improves the observed mean by **0.006348**. Both retain setting zero correctly.
   - **p = 0.0983154**, **δ_eval = 0.0211096**, **δ_search = 0.0422352 = 0.429588p**.
   - The four enrichment p-values are **0.68993, 0.12199, 0.62084, 1.00000**. The no-task p-values and outcome table also match.
   - MIP/URXL’s restoration comparison is **−0.131999 [−0.164388, −0.099772]**, correctly classified below −p. Its functional comparison against the weaker refit reference is equivalent, correctly producing “reached” before exclusion.
   - The longer-search AUC numbers match. One URXL extension gains **0.00671**, the other loses **0.00909**; PLNL’s are unchanged. **“No consistent improvement detected; retain the budget” is the correct fixed reading.** “Neither search gains” would be false.

   Those extensions concern **free searches**, not longer original-partner refits. They do not establish that extending refits could not repair the reference failure.

3. **Medium — several statements in D312 need correction or narrower wording.**

   Sources: [D312](/D:/Claude/random/wormWars/DECISIONS.md:9429), `full.json` fields named below, and [compute.json](/D:/Claude/random/wormWars/experiments/03a-self-consistency/pilot-dev/compute.json), `attempts`.

   - **“All ten stages completed on f27d4c4” is wrong as provenance.** `setup` and `evolve-intact` ran on **a5760c4**; `panel`, `evolve-nip`, `baseline`, and `probe` on **1b0531a**; `tune`, `full`, and `report` on **f27d4c4**. The aggregate also contains `family2` on **bb42654**. The question’s two-commit description likewise omits a5760c4.
   - **“Weights from zero” is wrong literally.** [DESIGN §6](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:220) specifies chemical weights initialized at ±`init_w_scale`, positive initial gap scale, and fresh τ/bias. Say “from fresh initial parameters.”
   - **URXL’s stated Q range misses observations.** Across ordinary free searches, `per_search[].q_every_10_from_0` spans **0–0.1778**, including NIP/URXL `free-4`’s final zero and `free-1`’s 0.1778. MIP alone spans 0.0444–0.1556.
   - **“Inside the chance range throughout” overstates what is recorded.** `chance_q` supplies an expectation, not a calibrated simultaneous trajectory envelope. Use “no sustained enrichment trajectory was apparent; the final primary enrichment tests did not reject.”
   - **The paired-difference ranges mix search classes.** Ordinary MIP/URXL free searches have means **−0.202 to −0.151**, and mean within-generation SDs **0.357–0.422**. The −0.140 and 0.322 endpoints come from `refit-2`. The broad figures are defensible only if labeled accordingly.
   - **“Jaccard near independent random” needs an exception.** MIP/PLNL’s incoming mean Jaccard is **0.04286**, versus expectation **0.007632**; NIP/URXL’s is **0.04744**, versus **0.03165**. These are not established significant departures, but the blanket wording hides them. The ten pairwise comparisons are dependent.

   There is also one exploratory anatomical result worth retaining without promoting it: MIP/PLNL’s gap `descriptive.precision_at_k` is **1/3**, nominal **p = 0.03670**. It does not overturn the primary null result or survive an unspecified multiplicity adjustment.

4. **High — the search has not demonstrated useful partner identification, but these records do not establish that identity is uninformative.**

   Sources: `full.json`, MIP/URXL `comparisons.advantage`, `refit_means`, `per_search`, and `enrichment`; [DESIGN §1](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:33).

   MIP/URXL’s original-partner advantage is **0.12171 [0.10410, 0.13929]**, above p. That is evidence that **the complete original partner set helps these refits**, against the sampled, stratum-matched random sets.

   It is not evidence that individual true partners have detectable marginal benefits during search. A useful combination can require coordinated partners and weights, with little or misleading benefit from individual substitutions. Nor does the result establish uniqueness: other wiring may perform similarly.

   The failed original-partner reference is especially informative. **Even after supplying the correct topology, the optimizer fails the restoration criterion.** This directly identifies parameter optimization or endpoint selection as a feasibility problem before topology discovery is considered.

   At the present settings, therefore:

   - Functional optimization is substantial on MIP/URXL.
   - Useful anatomical ranking has not been demonstrated.
   - Failure to recover anatomy cannot distinguish inadequate optimization, noisy selection, weak local identifiability, or alternative functional solutions.

   One shuffled graph, two selector-selected targets, and one shared MIP brain cannot establish typical recovery rates or falsify the N2 hypothesis. On this shuffled graph, task-specific compatibility with the original partners can arise through the fitted MIP background; the design also correctly notes that background initialization carries anatomical information. This is not a clean test of learning alone.

5. **High — turnover and paired spreads do not identify the failure mechanism, and the proposed turnover gate is unsound.**

   Sources: `full.json`, `per_search[].turnover_per_10_from_0`, `paired_diff_mean`, `paired_diff_sd_mean`; metric definitions in [e03a.py](/D:/Claude/random/wormWars/scripts/e03a.py:605) and [search.py](/D:/Claude/random/wormWars/wormwars/e03a/search.py:255).

   **Turnover follows the cold replica slot across swaps.** It does not follow one continuing state.

   This distinction is decisive for URXL. With 45 partners and at most one partner replacement per accepted offspring, a continuing state can replace at most **10/45 = 0.222** of its partners in ten generations. The observed roughly 0.9 turnover therefore necessarily involves changing which state occupies the cold slot.

   Consequently:

   - High slot turnover can coexist with fairly stable individual states.
   - Lowering slot turnover can merely suppress exchanges.
   - Applying the proposed 0.5 cutoff to a corrected, continuing-state metric would be automatically satisfied for URXL under these move limits.

   Frequent swaps, warm replicas, and sparse integer-valued scores are consistent with weak separation between replicas. They do **not** prove evaluation noise is the cause. Narrowing temperature spacing generally makes exchanges easier; it is not a remedy for excessively high swap acceptance.

   Likewise, the paired SD is the spread across **offspring–current score differences**, averaged over generations. It mixes mutation effects, replica differences, and evaluation noise. The negative mean says average proposals are harmful; it does not say the selected best of eight is harmful. These records cannot supply an evaluation-noise estimate by dividing that SD by √16.

6. **High — replace the proposed criterion 6 with a defensible repeatability check; do not invent a convergence cutoff from these traces.**

   Sources: [DESIGN §8](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:404), [PILOT-DEV “After pilot-dev”](/D:/Claude/random/wormWars/experiments/03a-self-consistency/PILOT-DEV.md:129).

   **I reject Claude’s draft as written.** Pilot-dev does fail its turnover clause—only **1/20** ordinary free searches has final-window turnover ≤0.5—but that does not validate the clause. Its Jaccard clause is too permissive: merely exceeding an expectation is not evidence against that null, especially when choosing any of three types. Three of the four target-brains already satisfy that weak clause.

   My preferred amendment is:

   - **Turnover becomes descriptive**, reporting slot turnover and, if retained as an optimization diagnostic, movement of continuing states through swaps. No universal 0.5 cutoff.
   - **Agreement is tested against a complete five-search random-set ensemble**, preserving each type’s set size. Compare the observed mean pairwise Jaccard with that ensemble, rather than treating ten pairs as independent. Use **p < 0.05 after correction across the tested high-target/type comparisons**, not “above expectation.” Require agreement on the same high-MIP target credited with anatomical recovery; explicitly disallow an empty-set pass. Agreement alone remains insufficient because repeated wrong partners can agree.
   - **Longer-search gain remains descriptive**, with the existing “no improvement detected” wording. I agree that requiring a gain would perversely penalize successful early convergence, while requiring no gain would reward uniformly unsuccessful searches. Criterion 5 supplies the substantive recovery gate.

   Removing turnover and extension gains as acceptance requirements **requires an explicit amendment** to the present promise in §8. These are proposed feasibility choices after pilot-dev, not thresholds statistically validated by its sample.

   **Low target:** report its diagnostics separately; do not require stabilization or repeatable anatomy where deletion and reinsertion offer no meaningful functional contrast. Likewise, do not impose an anatomical-agreement gate on NIP targets lacking headroom. Define this scope before pilot-check.

7. **Medium — freeze δ_search extraction explicitly, and do not confuse the pooled pass with precise search decisions.**

   Sources: `full.json`, `refit_sd`; [DESIGN §6](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:273).

   The pooled resolution pass is correct under the current rule. However, the MIP refit SDs are **0.05763 and 0.05187**, both above **p/2 = 0.04916**. Pooling MIP alone gives **0.05482 = 0.558p**; the smaller NIP spreads bring the combined quantity below the threshold.

   This is not a retroactive criterion-3 failure. It is a warning that the pooled number conceals the harder reconstruction cases. Also, δ_eval describes final **2,048-world comparisons**, not the reliability of decisions made using 16 worlds.

   A concrete extraction rule consistent with the design is:

   - For each pilot-check graph \(g\), calculate the sample SD \(s_{gta}\) of the three refit final scores for every target and arm.
   - Include all **eight target-brains**, including the low target and unreliable references:
     \[
     r_g=\frac{\sqrt{\frac18\sum_{t,a}s_{gta}^{2}}}{p_g}.
     \]
   - Require each graph’s \(r_g\le0.5\), alongside its δ_eval requirement.
   - Freeze \(r=\sqrt{(r_1^2+r_2^2)/2}\), and use **δ_search = r × p_N2** for formal reliability.
   - Missing refits make extraction incomplete; do not omit inconvenient cases. Report MIP/NIP and relevance-tier spreads separately.

   Do not carry pilot-dev’s 0.43 forward as the frozen value or choose the extraction subset after pilot-check.

8. **High for the spending decision — 43.8 hours already includes pilot-check.**

   Source: [report.json](/D:/Claude/random/wormWars/experiments/03a-self-consistency/pilot-dev/report.json:3277), `plan.hours`, `plan.total`, `remaining_hours`, and `search_worlds_32`.

   | Remaining workload | Projected hours |
   |---|---:|
   | Pilot-check | 10.338 |
   | N2 workloads | 33.366 |
   | Scripted remeasurement/calibration | 0.057 |
   | **Total** | **43.761** |

   Thus the question’s “10 hours and then about 44” double-counts pilot-check. D312’s “formal design” wording should be made explicit.

   Pilot-dev’s **4.577 hours**, remaining **66.893 hours**, no-cut choice, and **67.375-hour** 32-world projection all check out. Unchanged 32-world searches are disallowed by the existing rule.

   These remain projections, not guarantees. Once criterion 6 specifies pilot-check’s longer searches or additional validation, price those explicitly: the present projection’s ordinary-search calculation does not include an explicit extension allowance.

9. **High — choose a bounded search diagnostic before buying another feasibility run.**

   **(a) Proceed unchanged:** scientifically legitimate if the owner values an independently registered feasibility failure. It is not my preferred expenditure. Current evidence points to missing NIP headroom, failed MIP reference restoration, and undemonstrated identity recovery. Fresh graphs could change that, but “the pilot can fail honestly” does not by itself make it the best use of compute.

   **(b) Amend first:** my recommendation. Use MIP/URXL, the one consequential deletion, and keep PLNL as a low-effect comparison. Specify the check and stopping rule before further GPU work:

   - **Isolate evaluation instability:** hold candidate states fixed and reevaluate current/proposal comparisons on independent 16-, 32-, and possibly 64-world batches. Check whether apparent improvements and selected winners survive fresh evaluation.
   - **Trade offspring for worlds:** test **three offspring at 32 worlds** against eight at 16. Per replica, that is **4 × 32 = 128** state-world evaluations versus **9 × 16 = 144**, before throughput differences. This tests a plausible precision–breadth tradeoff without assuming doubled cost.
   - **Test a colder ladder**, for example `(0.01, 0.02, 0.04, 0.08)`, against the current ladder. This is an exploratory candidate, not an inferred optimum. Do not select it merely because turnover falls.
   - First establish whether original-partner refits can become reliable. If fixed-state reevaluation reveals winner instability, a fresh-world confirmation step for the selected challenger is a more targeted acceptance-rule change than blindly suppressing moves.

   Fewer offspring, changed acceptance rules, and the revised 32-world allocation exceed the existing tuning choices and require a documented amendment. Select settings using fresh functional validation; report anatomical diagnostics openly.

   **What would change my mind:** reliable restoration plus repeatable improvement in held-out anatomical ranking would justify fresh pilot-check. Merely colder traces or improved function with continued chance anatomy would not. If the bounded check fails, stop rather than repeatedly enlarging development.

   **(c) Stop now:** defensible, and preferable to unchanged pilot-check if no targeted diagnostic is undertaken. Publish this as an exploratory failure of the tested reconstruction procedure, not evidence against self-consistency.

   If option (a) is chosen and fresh pilot-check actually passes the substantive headroom, reference, and recovery gates, I would support the formal run under the frozen protocol.

10. **Medium — report the history probe, and preserve the distinction between development and confirmation.**

   Source: [probe.json](/D:/Claude/random/wormWars/experiments/03a-self-consistency/pilot-dev/probe.json), `evolved.MIP.plain`, `evolved.MIP["L=50"]`, and control fields.

   On the probe worlds, MIP falls from **1.9482 to 1.5664** under L=50 rebuilding, a **0.3818** loss. Full replay reproduces plain behavior; KT and KTM are unaffected. This belongs in the pilot-dev results and prevents an unsupported explanation that the anatomical null simply reflects no measured neural-history dependence. The design’s caveat still applies: this intervention does not uniquely identify useful sensory memory.

   All search changes, diagnostic thresholds, and scope changes chosen now are **informed by pilot-dev**. Label them accordingly, retain the original records and readings, and freeze the amended protocol before fresh pilot-check. A future failed pilot-check must not become another tuning round under the same registration.