**Revise.** The principal blocker is family 2: independent permutations across targets disregard the five shared MIP brains and can produce false imprinting evidence. Before registration, also resolve reliability-based exclusions, close the pilot’s empty-denominator case, and finish the replay and resampling specifications. The owner’s “measure, don’t gate” decision is accurately recorded and does not need reopening.

I checked branch `roadmap`, HEAD `0cdd3a25a5bd80efd79ce3e6683d846aebd8cb9f`, the archived reviews, development records and relevant code. No files were changed and no GPU work was run.

1. **Disposition of my round-2 findings.**

   Numbers below refer to the archived [Astra round-2 review](D:/Claude/random/wormWars/docs/reviews/20261016-03a-design-v5/astra.answer.md).

   | Round-2 finding | Status | Assessment |
   |---|---|---|
   | 2. Memory claim and roadmap requirement | **Resolved** | §2 limits the scripted result appropriately; D305 and the dated roadmap annotation explicitly narrow the requirement. |
   | 3. History intervention | **Partly resolved** | Canonical-start replay removes the undefined steady-state operation. Calibration and interpretation still need qualifications; see finding 4 below. |
   | 4. Family-2 inference and four-brain fallback | **Partly resolved** | The four-brain cut is removed, and the effect floor is described correctly. The new pooled permutation scheme is invalid for the shared-brain design; see finding 2. |
   | 5. Stratified null and structural claims | **Resolved in substance** | Conditioning, shared identity permutations, finite Monte Carlo correction and narrow claim wording are supplied. A few implementation details remain; see finding 6. |
   | 6. Tier uniqueness and independent interneuron confirmation | **Resolved** | Sequential selection without replacement and fresh MIP confirmation with Bonferroni address both objections. |
   | 7. Resolution and reference reliability | **Partly resolved** | The 64-world definition and “not below” ambiguity are fixed. Shared-world resampling and the formal reliability rule remain insufficiently explicit. |
   | 8. Frozen pilot and diagnostics | **Partly resolved** | Frozen acceptance thresholds and the authentic zero-fitness search path address the main issues. Criterion 5 still has a logical hole. |
   | 9. Numerical reporting and qualifications | **Resolved in substance** | Means reproduce, performance wording is narrowed, and estimated smoke time is identified. Minor numerical wording remains below. |
   | 10. Budget and fallback | **Partly resolved** | Validation and replay costs are included, and the 32-world option is constrained. The episode total and final descriptive fallback need correction. |

   Round-2 item 1 was an inventory of round-1 findings, rather than an additional finding. The previously resolved points—conditional NIP, compensation/headroom limitations, removal of the formal null arm, implementation contracts at design level, and outcome definitions—remain addressed.

2. **[Major; must change] Family 2 treats dependent target contrasts as independently permutable.**

   [DESIGN.md:124](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:124) reuses the same five intact MIP brains across all targets. [DESIGN.md:275](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:275) nevertheless permutes arm labels independently across targets. A favorable MIP brain can improve several target AUCs together; those permutations destroy that dependence.

   This is consequential even when each target separately satisfies identical MIP/NIP distributions. I checked an exact finite counterexample:

   - Each brain’s AUC is independently 0.4 or 0.6 with equal probability.
   - Each MIP brain has its same AUC across five targets; NIP brains are independent across targets.
   - All references are reliable.
   - Apply the proposed independent target permutations, using exact enumeration instead of Monte Carlo.

   The nominal 5% pooled test rejects **14.81%** of these null datasets; imposing the observed 0.05-AUC floor still gives **14.79%**. This is a mathematical counterexample, not an experiment result. Using 10,000 Monte Carlo draws does not repair the underlying null distribution.

   **Required:** use inference justified for shared MIP brains and target-specific NIP brains. Simply synchronizing permutations is not automatically sufficient because the two arms have different dependence structures. A straightforward defensible fallback is the original per-target tests with Holm, retaining five brains, and a descriptive pooled contrast.

   Also, [line 282](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:282) calls unequal arm variances “under the null.” They are outside the stated distributional exchangeability null. Separate genuine-null calibration from equal-mean, unequal-variance robustness checks. Include shared-brain dependence and a predefined validation acceptance rule.

3. **[Major; must change] Reliability-based target selection is not accounted for in family 2.**

   [DESIGN.md:272](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:272) selects the common reliable set before testing. Reliability is data-dependent and arm-specific: MIP must match exact restoration, whereas NIP has no corresponding condition ([line 247](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:247)). Reliability can correlate with reconstruction AUC.

   Keeping the selected set fixed while permuting only AUC labels does not establish a valid conditional test. Simulating AUCs alone cannot validate this selection step.

   **Required:** either test a fixed target set and use reliability only to qualify or withhold interpretation, or provide a justified selection-aware procedure and validate the joint reliability/AUC process.

   There is also a smaller alignment issue: the anatomically enriched, functionally successful target witnessing “imprinting” at [line 289](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:289) need not belong to family 2’s common set. Require that membership if the reading is intended to join the pooled contrast to demonstrated recovery.

4. **[Moderate; probe specification] Bounded replay is an improvement, but the calibration requirement overstates what follows.**

   [DESIGN.md:312](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:312) defines a useful intervention on dependence on older neural state. It avoids the previous attractor-convergence problem. The body-memory limitation is correctly acknowledged.

   Three details remain:

   - Specify reset timing relative to sensing, integration and action, including the first window and whether the current input is already included. Full replay must retain the original numerical batch composition.
   - **KTM should be unaffected** for every proposed \(L\), since each replay contains more than its one-tick memory. State this expected negative-control result explicitly.
   - KTS does **not necessarily lose task score whenever \(L<T\)**. Its stored average changes, but its threshold decisions can remain unchanged or even improve. The update at [slow_memory_check.py:59](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/slow_memory_check.py:59) provides no performance-loss guarantee.

   Validate state reconstruction on prescribed input sequences, including sequences where discarded history provably changes the scripted action. Then measure closed-loop performance effects without requiring an unsupported universal sign.

   The earlier request for a neural control exposing nonspecific disruption also remains unanswered. Replay can reset autonomous phase or developmental transients, even under constant input. A score loss therefore supports **dependence on older neural state under this intervention**, not uniquely useful sensory memory. Conversely, no loss does not establish memorylessness.

5. **[Major for criterion 5; moderate for uncertainty specifications] The pilot can pass its recovery criterion with no eligible MIP target.**

   At [DESIGN.md:359](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:359), criterion 4 can pass on three NIP targets while all corresponding MIP references are unreliable. Criterion 5 then asks for half of an empty set: rounded up, zero. Its explicit failure clause only handles *no targets passing criterion 4*, not this case.

   **Required:** define the intersection explicitly, require a nonzero minimum denominator, and fail if it is empty. State the minimum number of successful recoveries.

   Additional specifications needed before freezing:

   - At [line 239](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:239), “worlds … within brains” must not mean independently resampling world IDs for each brain. The evaluation bank is crossed with brains. Use a shared world resample across compared brains/states, and preserve shared MIP identities across targets.
   - State whether the pilot’s pooled \(\delta_{\rm search}\) is frozen for formal reference-reliability decisions, and precisely how target-brain reliability becomes target-arm reliability.
   - The allowed replacement MIP brain must undergo all subsequent criteria; results from different MIP brains must not be combined to manufacture a pass.

   The independent interneuron confirmation itself is now appropriate. The pilot’s limited size and omission of medium targets are also openly described.

6. **[Minor] The stratified null and tier order are acceptable, with small specifications outstanding.**

   [DESIGN.md:219](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:219) now supplies the essential null contract. Computing degree after deleting X avoids using X’s hidden edges in the conditioning variables. Shared permutations preserve associations between connection types. The conclusion correctly allows residual within-bin structural predictability.

   Before coding, make deterministic:

   - Whether tied degrees may be split across tertiles, and the exact boundary rule.
   - Which neighbor receives an undersized middle bin.
   - Handling of unscoreable restricted subsets, including the mirror-zero subset.
   - Effective support in terms of **distinct truth-label arrangements**, not merely candidate-identity permutations. Many identity permutations yield identical labels.

   The high → medium → low order at [line 153](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:153) resolves duplication. Its flagged fallbacks are acceptable operational tiers; they do not guarantee three biologically distinct relevance bands, and the text now makes that limitation clear.

7. **[Checked numbers; minor corrections] Every mean in §2’s table reproduces.**

   I independently reduced the stored episode counts in [memoryless-check.json](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/memoryless-check.json), [jitter-check.json](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/jitter-check.json), [slow-memory-check.json](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/slow-memory-check.json), and [mono-check.json](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/mono-check.json).

   | Controller | Real | Jitter 1 | Jitter 2 |
   |---|---:|---:|---:|
   | KT | 1.199219 | 0.947266 | 0.816406 |
   | KTM | 2.841797 | 0.513672 | 0.041016 |
   | KTS, T=2 | 2.619141 | 1.761719 | 0.628906 |
   | KTS, T=5 | 2.687500 | 2.462891 | 1.556641 |
   | KTS, T=10 | 2.177734 | 2.128906 | 1.626953 |
   | KTS, T=20 | 1.578125 | 1.687500 | 1.591797 |
   | Champions, median | 2.262695 | 2.253906 | 2.250977 |

   Also verified: 1,920 KT grid points; 162 KTS points per T; 256 tuning and 512 check worlds; the **1.642578** KT–KTM gap; stereo median **2.319336**; paired mono-minus-stereo range **−0.162109 to +0.017578**; constant-scent range **0.082031–0.339844**.

   Two small qualifications:

   - “SEs 0.02–0.05” at [line 83](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:83) does not cover all table cells: KTM at jitter 2 has SE **0.00877**.
   - The historical KTM tuning loop still excludes the no-memory setting ([memoryless_check.py:75](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/memoryless_check.py:75)). This does not change the reported winner. Since v6 only remeasures frozen winners, it is no longer an outstanding optimization requirement; distinguish theoretical nesting from the grids actually searched.

8. **[Moderate] Budget hours check; the episode total and last fallback do not fully match their descriptions.**

   From [compute.json](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/compute.json), recorded exploration is **2,330,112 worlds**, **1,668.523 seconds = 0.463479 hours**. Adding the explicitly estimated smoke time gives approximately **0.533479 hours**. The missing smoke records cannot be independently verified.

   I recomputed [§10](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:383):

   | Component | Episodes | Hours at 420/s |
   |---|---:|---:|
   | One search | 57,600 | 0.03810 |
   | One target-brain | 748,800 | 0.49524 |
   | Formal searches | 44,928,000 | 29.71429 |
   | 38 evolutions, including validation | 10,126,848 | 6.69765 |
   | Final evaluations, including 30 restorations and five intact scores | 1,792,000 | 1.18519 |
   | Relevance scan and selection check | 395,776 | 0.26176 |
   | Probes at the stated 12-equivalent allowance | 933,888 | 0.61765 |

   The checkpoint count agrees with [evolve.py:198](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:198). The rounded workload rows total **84.19 million**, yielding **56.21 hours including exploration**. Thus “about 56.2” is correct.

   However:

   - The **84.2-million total excludes the 2.33 million recorded exploratory worlds**. Including those gives about **86.52 million**, plus unknown smoke worlds. Also distinguish actual episodes from replay episode-equivalents.
   - Pilot-check evolution/search work, including two re-evolutions, is **15,711,744 episodes**. The 16.73-million row therefore leaves about **1.02 million** for evaluations, scans and probes. That allowance is plausible but not independently itemized.
   - Four doubled replay probes already cost eight equivalents; constant, two jitters and hold bring the count to twelve **before the P4 ramp**. Price the ramp explicitly.
   - The historical throughput records support the approximate rates; they do not establish throughput for the new union-mask searches or five-run batches. Pilot-dev measurement remains essential.

   The cut order—random refits before free searches, preserving brains and evaluation precision—is reasonable. **Dropping family 2 alone saves essentially no simulator work.** At [line 406](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:406), the descriptive fallback must specify an actual reduced workload and how feasibility is checked, or simply stop when the preceding cuts still do not fit.