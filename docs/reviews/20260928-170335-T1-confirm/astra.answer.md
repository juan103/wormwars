**Most original points are resolved, but I would not close T1 yet.** The remaining issues concern checker completeness, failed-child accounting, unsupported diagnostic wording, and the audit trail.

I reviewed `roadmap` at `f939ad2`, without modifying files. I could not run Python tests here: `py -0p` reports no installed Python.

The committed results confirm these counts, separately in both modes:

| Comparison | CUDA | CPU |
|---|---:|---:|
| Off equals reference | 268/268 | 250/250 |
| On, multi-strain equals reference | 158/158 | 146/146 |
| On, single-strain equals batch | 102/110 | 104/104 |

The CPU run used `--quick`, including shorter rollouts—not merely fewer strains. All **388 hold-outs and 468 supported probe evaluations** reproduce with padding off and remain unchanged with it on. The mean-change statistics are now zero. All four local reference NPZ hashes match the committed summaries.

My earlier requests concerning strict equality, inferred remainders, starting food, supplied-config loading, published probes, CPU coverage, cross-composition comparisons, profiling qualifications, and explicit post hoc acceptance have been addressed. The legacy-layout fix also looks correct. The following remain.

1. **The checker can silently accept incomplete evidence.**  
   [scripts/t1_equivalence.py:265](D:/Claude/random/wormWars/scripts/t1_equivalence.py:265) iterates only over reference keys. If an older reference omits newly added cases or fields, those current outputs are never checked. An empty reference even produces three passing legs through `all([])`. Require matching, nonempty output inventories and valid case descriptions before comparison.

   The pairing guard at [line 236](D:/Claude/random/wormWars/scripts/t1_equivalence.py:236) repeats the same classification used to construct the pairs, so it cannot detect the missing metadata it should protect against. [tests/test_t1_equivalence_script.py:61](D:/Claude/random/wormWars/tests/test_t1_equivalence_script.py:61), despite its name, asserts that an absent batch reference is returned; it tests no refusal. Add sabotage tests through `compare()` itself. **This does not invalidate the inspected v2 counts**, whose inventories are complete.

2. **Child accounting is fixed for successful children, but still loses failed-child work.**  
   The count-only merge in `accounting.py` is sensible: adding child seconds would double-count waiting time. However, [scripts/t1_equivalence.py:338](D:/Claude/random/wormWars/scripts/t1_equivalence.py:338) writes the ledger only after successful completion, and [line 305](D:/Claude/random/wormWars/scripts/t1_equivalence.py:305) raises before merging if the child fails. A child that completes several rollouts and then raises loses those counts. The profile worker has the same issue at [scripts/t1_profile.py:178](D:/Claude/random/wormWars/scripts/t1_profile.py:178). Persist and merge partial counts on failure, preserving the original error.

3. **“All explained” still exceeds the diagnostics.**  
   [T1.md:462](D:/Claude/random/wormWars/docs/foundations/T1.md:462) attributes both one-world and eight-world `eaten` differences to reporting. But `eaten_cause` tests **eight worlds only**, against 2,048; see [scripts/t1_diagnostics.py:114](D:/Claude/random/wormWars/scripts/t1_diagnostics.py:114). Its 32 identical final-field comparisons and 22 differing sums support that case. They do not establish the one-world explanation. Add that comparison or explicitly label its cause unconfirmed.

   Likewise, [T1.md:461](D:/Claude/random/wormWars/docs/foundations/T1.md:461) says the one-row brain failures have “the same reason.” Showing that two- and four-strain multiplications each differ from 32 does **not** establish that two differs from four—the actual brain-test comparison. This remains consistent with the proposed cause, rather than a demonstrated explanation.

   [T0.md:248](D:/Claude/random/wormWars/docs/foundations/T0.md:248) incorrectly describes **final food sums over 2–15 worlds** as tested. The range sweep uses random fields; the final-food diagnostic uses eight worlds. Name the discrete tested counts rather than ranges: raw `bmm` uses `{1,2,3,4,8,16}`, and differing random-field reductions were observed at `{2,4,8,12,15}`. Apply this precision to the corresponding reproducibility block.

4. **The closure amendment misdescribes the eight failures.**  
   [T1.md:543](D:/Claude/random/wormWars/docs/foundations/T1.md:543) associates all eight with 16 and one row. The actual partition is:

   - Two outputs: proxy score and energy at 16 rows.
   - Four outputs: one-row brain states.
   - Two outputs: `eaten` at **160 and 20 rows**, corresponding to eight and one world.

   Say “eight failures: six score/energy/brain-state outputs and two `eaten` outputs,” then describe their respective status. The amendment’s acceptance logic is otherwise correct.

5. **Some explicit earlier cleanup remains undone, and compute is still untraceable.**  
   Unconditional guarantees remain in [wormwars/brain.py:394](D:/Claude/random/wormWars/wormwars/brain.py:394), [wormwars/config.py:63](D:/Claude/random/wormWars/wormwars/config.py:63), and [wormwars/evo/rollout.py:8](D:/Claude/random/wormWars/wormwars/evo/rollout.py:8). These contradict the amended contract. Update the implementation comments; preserve historical plan text.

   The **6.9-hour** claim at [T1.md:538](D:/Claude/random/wormWars/docs/foundations/T1.md:538) still lacks committed accounting records and an explicit aggregation. Disclosing the deleted first reference ledger does not resolve this. Commit the surviving small summaries and calculation, distinguishing CPU runs and incomplete historical counts. I am calling the total **untraceable**, not proving it wrong.

   Also replace “costs nothing measurable” with “little measured overhead in these four workloads”: the proxy checkpoint’s recorded ratio is **1.014**, approximately a 1.4% slowdown.

**The reference engine is honest.** I verified that `ffeb541` differs from `1598d56` only in the three disclosed files, and those files match `790ce32`. Returning already-computed starting food and extending accounting do not alter the simulation arithmetic. The engine files listed in §7 are unchanged. `2f423dd` has no tree difference against its first parent. This is a legitimate, transparently instrumented pre-change reference.

**I confirm the proposed engineering decisions:** keep padding as a default-on mitigation; accept composition-specific results; match paired arms’ compositions; test actual E1 configurations; require E1’s own config builder and composition records. The tuple in AGENTS rule 6 is appropriate. Prefer “tested pairs and endpoints that passed” when describing cross-composition guarantees. Closure by dated amendment is appropriate after the corrections above; it should authorize the bounded pilot while leaving the measured budget gate with E1.

For the **signals text**, the stimulus schedules, sample sizes, formulas’ basic structure, reported values, ranks, and verdicts agree with the registration and results. Two explanations need correction:

- **P4 does not measure the fraction of the brain’s state retained.** [03 README:71](D:/Claude/random/wormWars/experiments/03-generation0/README.md:71) and [main README:62](D:/Claude/random/wormWars/README.md:62) overinterpret both zero and 0.93. Zero means no difference **in this readout, for these histories, at this tick**; hidden state or other history dependence can remain. The ratio of mean absolute contrasts does not establish that individual brains are mostly in their previous states. Replace that interpretation with: “The mean absolute final turn-output difference is about 93% of the mean absolute contrast after holding the two starting levels for 100 ticks.” Those 100 ticks do not establish equilibrium, as RESULTS already acknowledges.
- **Specify P1’s averaging.** At [03 README:96](D:/Claude/random/wormWars/experiments/03-generation0/README.md:96), say the signed directional response is **half the difference between mirrored conditions, averaged over genomes and all 40 ticks**, divided by the corresponding mean absolute common-mode response. This prevents interpreting it as a final-tick measurement.

T1: not yet — fix checker completeness and failed-child accounting; narrow diagnostic claims; correct failure wording and stale guarantees; commit the compute calculation.  
Signals text: fix — narrow P4’s interpretation and specify P1’s averaging.