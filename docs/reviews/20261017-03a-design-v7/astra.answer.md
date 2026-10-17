**Ready for the pre-registration, with small fixes.** V7 resolves the round-3 blockers. I found no new issue requiring another redesign, but the specifications and wording identified below should be settled before registration.

I checked branch `roadmap`, HEAD `9ded3776be19253adb95234d4012b03aae655748`. The reviewed files match that commit. I changed nothing and ran no GPU work.

1. **Round-3 findings: disposition.**

   These refer to the numbered findings in the archived [Astra round-3 review](/D:/Claude/random/wormWars/docs/reviews/20261017-03a-design-v6/astra.answer.md). Its item 1 was a retrospective inventory.

   | Round-3 finding | Status | Reason |
   |---|---|---|
   | 2. Invalid pooled family-2 permutation | **Resolved** | V7 uses separate exact tests per target and Holm across targets. Sharing MIP brains across targets no longer invalidates the correction. |
   | 3. Reliability-based selection and mismatched recovery witness | **Resolved** | The tested set is fixed independently of reliability. The target witnessing imprinting must itself satisfy the recovery and reliability conditions. |
   | 4. Replay timing, calibration and interpretation | **Resolved at design level** | Timing and numerical composition are specified; KTM must be unaffected; KTS has no unsupported performance-loss requirement; prescribed-input validation is required. Nonspecific neural disruption is explicitly acknowledged rather than experimentally excluded. |
   | 5. Empty pilot denominator, resampling and reliability | **Resolved** | Criterion 5 requires \(n\ge2\); world resampling is shared; MIP identities persist across targets; pilot δ_search is frozen; target-arm reliability and replacement-brain handling are defined. |
   | 6. Stratified-null and tier details | **Resolved** | Degree ties, boundaries, merge direction, unscoreable subsets and distinct-label support are specified. Selection remains sequential without replacement. |
   | 7. Numerical reporting | **Resolved** | The table reproduces, T = 50 is included, SE wording is corrected to rounded values, and theoretical nesting is distinguished from the searched grids. |
   | 8. Budget and ineffective fallback | **Resolved in substance** | Ramp cost and pilot workloads are itemised; exploratory worlds are distinguished; the ineffective “drop family 2” fallback is replaced by stopping. The budget remains a projection requiring measured throughput. |

2. **Family 2 is now defensible; it is no longer a pooled permutation test. Severity: minor remaining specifications; substantial acknowledged power limitation.**

   [DESIGN.md:291](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:291) specifies five per-target tests, with only the panel mean descriptive. That directly fixes the main round-3 objection.

   The resolution claim is correct: at Holm’s first threshold of 0.01, **2/252 = 0.00794 passes; 3/252 = 0.01190 does not**. Five brains per arm can detect unusually strong separation, but many meaningful differences will remain undetected. The design says this plainly; a negative result must retain that qualification.

   Three details should be explicit in the registration:

   - At lines 308–311, **shared MIP effects across targets are not inherently outside the per-target null**. If each target retains exchangeable MIP/NIP marginal distributions, cross-target dependence is precisely what Holm accommodates. Include that case in null calibration. Unequal arm variances are outside the stated exchangeability null.
   - Specify the simulation count and numerical acceptance rule replacing “beyond Monte Carlo error.”
   - If a target is withheld because a brain is missing, retain the registered five-member family—for example, assign that test \(p=1\)—rather than silently shrinking it.

   The test rejects the stated exchangeability null. It does not establish a population mean advantage of at least 0.05; the observed-effect filter is correctly described as weaker than that.

3. **The replay probe supports the narrowed claim, with one timing consequence worth adding. Severity: minor specification; moderate interpretive limitation.**

   [DESIGN.md:340](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:340) is now a coherent intervention. I checked the zero initial state and deterministic state update in [brain.py:431](/D:/Claude/random/wormWars/wormwars/brain.py:431), and the KTS update in [slow_memory_check.py:59](/D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/slow_memory_check.py:59).

   **The first reset also changes nothing:** at \(t=L\), replaying ticks 1 through L reconstructs the complete history. Under the stated convention, the first potentially affected action is at **\(2L+1\)**. For L = 50, the first 100 of 300 actions are therefore unperturbed.

   State this explicitly. Comparisons across L change both retained history and intervention frequency/exposure; they are not direct estimates of a brain’s memory horizon. The stated L-to-2L history range is otherwise correct.

   The implementation should replay the actual input-current sequence received by the ongoing perturbed trajectory, with identical integration settings. Body-mediated history remains available, as acknowledged. A loss can reflect disrupted filtering or autonomous dynamics; no loss cannot establish memorylessness. Those limitations are sufficient for the owner’s settled “measure, don’t gate” decision.

4. **The stratified null and tier order are acceptable for their stated purpose. Severity: no blocking finding.**

   [DESIGN.md:231](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:231) now defines a reproducible conditional comparison: degree after deleting X, role precedence, unsplit degree ties, shared identity permutations and finite Monte Carlo p-values. The MCL/MCR correction agrees with [interface.yaml:63](/D:/Claude/random/wormWars/configs/interface.yaml:63).

   Report support using **joint connection-type truth patterns**, consistent with the shared permutation—not a product of independently permutable incoming, outgoing and gap labels.

   The principal limitation remains correctly stated: enrichment beyond these strata is not evidence of superiority to structural prediction. The comparator results must remain beside the task result.

   The high → medium → low order at [DESIGN.md:164](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:164) prevents duplication. The operational “medium” tier and flagged fallbacks do not guarantee three distinct biological relevance bands; v7 does not claim otherwise.

5. **Pilot criteria and cut order now have coherent failure paths. Severity: no blocker; limited strength of a pilot pass.**

   At [DESIGN.md:403](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:403), criterion 5 cannot pass vacuously. However, its weakest passing case is **two eligible targets and one successful MIP recovery**, potentially on only one of the two graphs. That is a feasibility threshold, not replication of recovery across shuffled graphs. Keep that distinction when reporting a pass.

   Independent interneuron confirmation, shared-world uncertainty, the replacement-brain rule and frozen diagnostic thresholds address the previous concerns. A one-brain-per-arm pilot still cannot establish the performance of five-brain aggregation or the power of family 2; simulated-null calibration establishes error control, not power.

   The cuts at [DESIGN.md:450](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:450) are sensible: random refits first, free searches second, then stop. Restating the ranking and no-task control after the second cut is necessary and now required.

6. **§2: all 24 table entries checked and reproduced. Severity: no numerical discrepancy.**

   I independently reduced the stored episode counts in the committed [development records](/D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records), rather than relying on their stored means or the previous review.

   | Controller | Real scent | Jitter 1 | Jitter 2 |
   |---|---:|---:|---:|
   | KT | 1.199219 | 0.947266 | 0.816406 |
   | KTM | 2.841797 | 0.513672 | 0.041016 |
   | KTS, T = 2 | 2.619141 | 1.761719 | 0.628906 |
   | KTS, T = 5 | 2.687500 | 2.462891 | 1.556641 |
   | KTS, T = 10 | 2.177734 | 2.128906 | 1.626953 |
   | KTS, T = 20 | 1.578125 | 1.687500 | 1.591797 |
   | KTS, T = 50 | 1.173828 | 1.173828 | 1.181641 |
   | Champions, median | 2.262695 | 2.253906 | 2.250977 |

   Sources: `memoryless-check.json`, `jitter-check.json`, `slow-memory-check.json`, and `mono-check.json`.

   Also checked: **1,920** KT grid points; **162** KTS points per T; 256 tuning and 512 check worlds; the **1.642578** KT–KTM gap; stereo median **2.319336**; mono-minus-stereo range **−0.162109 to +0.017578**; constant-scent range **0.082031–0.339844**. The scripted SE range is approximately **0.00877–0.05059**, consistent with the rounded wording.

7. **§10: the revised budget arithmetic checks. Severity: no arithmetic blocker; throughput remains provisional.**

   From [compute.json](/D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/compute.json), exploration recorded **2,330,112 worlds** and **1,668.523 seconds = 0.463479 hours**. Adding the estimated smoke time gives **0.533479 hours**. The deleted smoke records cannot be independently verified.

   I recomputed every workload row at [DESIGN.md:434](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:434):

   | Workload | Episodes or episode-equivalents | Hours at 420/s |
   |---|---:|---:|
   | One search | 57,600 | 0.03810 |
   | One target-brain | 748,800 | 0.49524 |
   | Formal searches | 44,928,000 | 29.71429 |
   | 38 evolutions | 10,126,848 | 6.69765 |
   | Final evaluations¹ | 1,798,144 | 1.18925 |
   | Relevance and selection checks | 395,776 | 0.26176 |
   | Formal probes | 1,089,536 | 0.72059 |
   | Pilot-dev allowance | 9,072,000 | 6.00000 |
   | Itemised pilot-check | 16,782,848 | 11.09977 |
   | Scripted allowance | 200,000 | 0.13228 |

   ¹Counting 30 restorations and eight intact brains.

   Total: **84,393,152 planned episode-equivalents; 56.349 hours including charged exploration; 15.651 hours reserve.** Thus “about 84.4 M,” “about 56.3,” and “about 15.7” are consistent. Including recorded exploratory worlds gives approximately **86.72 M**, plus unknown smoke worlds; this mixes episodes and replay equivalents.

   The 41 validation checkpoints agree with [evolve.py:198](/D:/Claude/random/wormWars/wormwars/e04a/evolve.py:198). Historical records support the approximate throughput assumptions: about **426/s** for E2d C3 selection and **1,035/s** for C1. They do not establish throughput for the new search implementation. Pilot-dev measurement remains essential, including implementation controls and diagnostic work not separately itemised here.

8. **Two small wording corrections remain. Severity: minor.**

   - [DESIGN.md:106](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:106): “the champions lose nothing” is too absolute. At jitter 2, individual changes range from **−0.056641 to +0.031250** targets; the median changes by −0.011719. Say “show little measured loss.”
   - [DESIGN.md:414](/D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:414): the scripted gap on fresh worlds is not something that “cannot fail” merely because the exploratory estimates were 2.84 and 1.20. Keeping it descriptive is reasonable; that justification is not.

   D305 and its consequences are otherwise accurately represented in §1, §2 and the [roadmap annotation](/D:/Claude/random/wormWars/ROADMAP.md:568). I am not reopening that decision.