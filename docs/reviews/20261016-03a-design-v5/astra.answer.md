**Revise.** Before pre-registration, resolve the memory claim and history intervention, repair the resolution and interneuron gates, define the permutation tests precisely, and remove the four-brain fallback from the confirmatory design. The descriptive results are mostly reported accurately; the remaining problems concern what would count as evidence.

I checked branch `roadmap`, HEAD `9a11651f7ceae6040f59900fdb8d6f42567b7790`, the archived reviews, D094/D303, the development records and scripts, and relevant implementation code. No files were modified and no GPU work was run.

1. **Round-1 findings: disposition of all twelve Astra findings.**

   These numbers refer to the archived [Astra review](D:/Claude/random/wormWars/docs/reviews/20261016-03a-design-v4/astra.answer.md).

   | Round-1 finding | Status | Reason |
   |---|---|---|
   | 1. Memory gate | **Partly resolved** | Stronger controls and useful exploratory results, but the scripted gap still does not establish memory necessity. The new intervention is not yet a valid selective history ablation. |
   | 2. Selection favoring MIP; tiers | **Partly resolved** | Separate selector brains resolve the direct selection bias. Tier uniqueness and pilot confirmation remain incomplete. |
   | 3. Compensation, headroom, conditional NIP | **Resolved at design level** | §1 states the limits plainly and requires the relevant accompanying scores. |
   | 4. Recovery beyond structural predictability | **Partly resolved** | Structural rankings and restricted-candidate readings are restored. Degree tertiles control only coarse degree categories, and structural superiority is not required for the primary reading. |
   | 5. Imprinting multiplicity and aggregation | **Partly resolved** | Holm, five brains, an effect floor, shared anatomical permutations and per-search reporting address much of it. Exchangeability and calibration remain unspecified; the four-brain cut defeats the test. |
   | 6. Formal null arm | **Resolved** | Cutting it and retaining SH-mirror for feasibility is appropriate. |
   | 7. Implementation contracts | **Resolved at design level** | The required contracts are now present. Their implementation and failing/sabotage tests still need review. |
   | 8. Search feasibility and interneuron use | **Partly resolved** | Diagnostics and a direct deletion gate are added. Resolution definitions, diagnostic acceptance rules and scan multiplicity remain unresolved. |
   | 9. Outcome classification | **Resolved at design level** | Units are explicit; “inconclusive” no longer qualifies as a substantive outcome; substitution is not claimed. Outcome diversity remains descriptive, as §7 now acknowledges. |
   | 10. Budget and batching | **Partly resolved** | Arithmetic is sound at the stated settings; actual configurations, extra probe work and the 32-world option remain uncosted adequately. |
   | 11. Factual corrections | **Resolved for the original corrections** | The 02b, sampling-location and earlier-history wording is corrected. New overstatements are identified below. |
   | 12. Self-contained protocol and held-out pilot | **Partly resolved** | The development/check split is correct. Several inherited definitions and gate details still need replacement with explicit specifications. |

2. **[Major; §11 question 1] Keep Task N-mono provisionally, but do not call the scripted gap proof that the task requires memory.**

   [DESIGN.md:81](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:81) says that “a task that requires memory” holds at the task level. That conclusion does not follow.

   The experiment demonstrates that a particular memory-enabled family outperforms a particular memoryless family. The latter remains restricted: one concentration threshold, limited speed/turn grids, and collision avoidance that collapses the front collision signals to their maximum and turns in one direction. See [memoryless_check.py:29](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/memoryless_check.py:29). It is not a bound on memoryless policies using the available observations.

   Likewise, jitter tolerance does not establish that the champions “ignore fast history” or operate “without depending on tick-to-tick change” ([DESIGN.md:72](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:72)). It establishes robustness to these particular spatial perturbations. A fast temporal computation could be robust to them.

   **My answer:** retain mono for development. Under the current [roadmap requirement](D:/Claude/random/wormWars/ROADMAP.md:567), useful neural history should be a feasibility requirement, with the validated diagnostic also applied to formal N2 brains. Pilot failure is an acceptable result. Alternatively, explicitly amend the requirement and describe the experiment as task-conditioned reconstruction without demonstrated memory use. Reporting history descriptively is defensible under that narrower objective, but does not satisfy the existing requirement.

3. **[Major; §11 question 2] The proposed steady-state reset is not yet a sound matched-current-input history ablation.**

   [DESIGN.md:258](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:258) assumes a well-defined “brain’s steady state” and says periodic replacement erases history older than \(k\) ticks. There are three problems.

   - **Which steady state?** These recurrent dynamics are not guaranteed to converge to one unique attractor. Settling from the current state can preserve history through attractor selection. Settling from a fixed initial state removes that dependence, but needs a convergence rule and treatment of nonconvergence. The update in [brain.py:434](D:/Claude/random/wormWars/wormwars/brain.py:434) supplies no uniqueness guarantee.
   - **What is erased?** A reset every \(k\) ticks erases recent neural history too, at each reset. It does not selectively remove history older than \(k\). History retained in body position and motion remains.
   - **What else changes?** Replacing the complete neural state can alter motor output, autonomous phase and normal sensory-response transients. Matching the instantaneous input does not make the intervention specific to useful sensory memory.

   Calibration on KT and KTM alone is insufficient. A one-tick-memory controller quickly reacquires its memory between resets at \(k=10,20,50\); weak effects on it would not validate an older-history ablation.

   **Required:** specify initialization, stopping tolerance, maximum settling work, reset timing relative to sensing/action, and nonconvergence handling. Calibrate against known memoryless, short-memory and longer-memory controllers, including neural implementations or controls that expose nonspecific neural-state disruption.

   I would prefer developing a **finite-history replay intervention**: reconstruct state from a canonical start using a specified recent input suffix, with full-history replay as an implementation control. It still needs validation, but its information boundary is clearer. Until then, call the proposed operation a *periodic state-reset probe*, not a selective history erase.

4. **[Major; §11 question 3] Family 2 is substantially better, but “exact” needs a stated null—and the four-brain fallback is incompatible with it.**

   The arithmetic at [DESIGN.md:226](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:226) is correct: \(\binom{10}{5}=252\), giving minimum one-sided \(p=1/252\).

   However, enumerating all splits does not itself establish validity. Arm-label permutation requires exchangeability under the null. Equality of mean AUC alone does not imply exchangeability when MIP and NIP can have different variances or distribution shapes.

   **My answer:** I still prefer descriptive imprinting contrasts for this proof of concept. Keeping the test is defensible if the registration specifies the distributional null, independent run/seed allocation, treatment of shared evaluation worlds, exclusions, ties, and the exact permutation statistic. Validate the complete decision procedure under simulated nulls, including heterogeneous brain outcomes. State that the observed 0.05 floor is an effect-size filter; it does not establish that the population difference exceeds 0.05.

   The decisive new problem is [DESIGN.md:329](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:329):

   \[
   \binom{8}{4}=70,\qquad p_{\min}=1/70=0.01429>0.05/5=0.01.
   \]

   With four brains per arm, **Holm cannot reject even its first hypothesis**. No imprinting result can pass, however completely the arms separate.

   Preserve five brains, stop if they do not fit, or predeclare a descriptive fallback. Do not retain the same confirmatory reading after this cut.

5. **[Major for claim wording; moderate for implementation; §11 question 4] Shared stratified permutations are appropriate, but the degree claim is too broad.**

   The shared permutation at [DESIGN.md:185](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:185) is the right dependence treatment: apply the same within-stratum candidate permutation jointly across arms, brains, searches and connection types. This preserves the multitype label associations and avoids manufacturing independent anatomical evidence.

   Kind × degree tertiles are a reasonable coarse null. They do **not** establish recovery beyond everything degree explains. A ranking favoring the highest-degree candidates *within* each tertile can pass while remaining entirely degree-driven. Total degree also does not distinguish incoming chemical, outgoing chemical and gap degree.

   **Required before registration:**

   - Define “kind”: mapped interface membership versus anatomical class, including overlapping labels and inactive mapped sensors.
   - Define total degree, tertile construction, ties, and whether bins are global or within kind.
   - Report stratum sizes, partner counts and effective permutation support; specify unscoreable connection types/subsets.
   - Use the finite Monte Carlo correction, including ties.
   - Narrow the conclusion to enrichment beyond the **specified kind/degree-bin null**, or strengthen the conditioning and check its calibration.

   The restored structural comparisons are useful. But a primary pass can still occur while the task ranking is worse than the mirror or class ranking. Report that combination explicitly; do not describe it as improvement over structural prediction. The current separation of these readings is acceptable if the wording stays narrow.

6. **[Major for the pilot gate; moderate for tier rules; §11 question 5] Separate selectors fix the original bias, but selection and confirmation remain conflated in the pilot.**

   The three independent selector brains at [DESIGN.md:94](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:94) resolve my original objection. They select targets for dependence in a separate sample, not for unusually large damage in the evaluated MIP brains.

   Two remaining problems:

   **First, the tier algorithm does not explicitly guarantee six distinct targets.** At [DESIGN.md:125](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:125), medium fallback must exclude already selected medium targets. The low rule must exclude all five previously selected targets. Otherwise, when high targets are only “relatively high,” a target can satisfy both a previously selected tier and the low rule. Specify sequential selection without replacement and every shortage fallback.

   Also, an interval containing \(p\) identifies an uncertain boundary case, not necessarily medium biological relevance. That is acceptable as an operational tier, provided the interpretation is explicit.

   **Second, criterion 3 appears to count nominal lower bounds from a large deletion scan** ([DESIGN.md:290](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:290)). Selecting three favorable intervals from many neurons does not give a calibrated demonstration that three neurons matter. The gate also does not clearly identify whether the effects belong to the selector or the MIP brain.

   Use the independent MIP remeasurement already promised in §4 as the gate: confirm the three preselected high targets on fresh worlds, with simultaneous lower bounds or multiplicity control over those three. State which brain and intact score define \(p\).

   **Pilot size answer:** two graphs with one MIP/NIP replicate are enough for a limited operational feasibility check, not for validating five-brain inference or estimating success rates reliably. The pilot additionally uses one selector instead of three and omits medium targets. Either make it more representative or state these limitations and test the missing aggregation logic separately.

7. **[Major] The resolution and reference-reliability gates are not self-contained and contain a consequential ambiguity.**

   [DESIGN.md:197](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:197) inherits the draft’s noise measures. But [DRAFT.md:138](D:/Claude/random/wormWars/experiments/03a-self-consistency/DRAFT.md:138) defines \(\delta_{\rm eval}\) using **64-world** means. Criterion 4 still requires it to be at most \(p/2\), despite final evaluation increasing to 2,048 worlds.

   This is consequential. From the committed mono counts:

   - Run 00: episode SD ≈ 0.772, implying SE at 64 worlds ≈ 0.0965; \(p/2≈0.0528\).
   - Run 12: episode SD ≈ 0.779, implying SE at 64 worlds ≈ 0.0974; \(p/2≈0.0660\).

   These are illustrative estimates, not pilot results. They show that the inherited gate could fail because it measures the wrong evaluation size.

   Define resolution for the actual **paired comparisons and replication structure** used in the decisions. Specify how \(\delta_{\rm search}\) is estimated and pooled, and preserve world pairing across states and any shared world bank across brains.

   A second ambiguity is “reference not below exact restoration” at [DESIGN.md:203](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:203). Under the four-way comparison scheme, *undetermined* is also “not below.” The inherited draft required **equivalent or above**. Restore that explicit requirement; otherwise uncertainty can qualify a reference as reliable.

8. **[Moderate; §11 question 5] The two-stage pilot is the right structure, but its frozen protocol needs more than a list of diagnostics.**

   [DESIGN.md:276](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:276) correctly separates development from an untouched check. Keep that.

   Before pilot-check, freeze:

   - The selected two development targets and brain counts.
   - What turnover, ranking reliability and the doubled-search comparison would make the search unacceptable.
   - How criterion 6 handles “at least half” and unreliable MIP references.
   - Whether NIP reference failures exclude corresponding imprinting tests, and how multiplicity is retained.
   - The complete formal-N2 diagnostic and failure-reporting policy.

   Do not turn diagnostics into pass/fail thresholds after observing pilot-check.

   The no-task control should execute the **same zero-fitness search path**, including best-of-eight tie handling and replica swaps. “Every offspring is accepted” ([DESIGN.md:252](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:252)) does not literally describe the stated optimizer, which selects one offspring before replacement. A separately implemented random walk is a weaker pipeline test.

9. **[Checked numerical findings] The new §2 numerical summaries reproduce; several interpretations need narrowing.**

   I independently recomputed means and, where quoted, standard errors from the stored episode counts.

   | Committed record | Recomputed result |
   |---|---|
   | [memoryless-check.json](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/memoryless-check.json) | 1,920 grid points. KT: **1.19921875**, SE **0.05059273**. KTM: **2.841796875**, SE **0.03552496**. Each uses 512 check worlds. Gap: **1.642578125**. |
   | [mono-check.json](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/mono-check.json) | Sixteen champions. Mono median **2.2626953125**, range **2.03125–2.67578125**; stereo median **2.3193359375**. Constant-scent range **0.08203125–0.33984375**. |
   | Same record | K-mono **0.947265625**; M-avg-mono **2.220703125**. Champion median at hold-20: **1.7255859375**. |
   | [jitter-check.json](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/jitter-check.json) | KTM at radii 0.5/1/2: **1.52734375 / 0.513671875 / 0.041015625**. KT: **1.12890625 / 0.947265625 / 0.81640625**. |
   | Same record | Champion medians at radii 0/0.5/1/2: **2.2626953125 / 2.2646484375 / 2.25390625 / 2.2509765625**. |
   | [compute.json](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/compute.json) | **1,194.654 seconds = 0.331848 hours**, 2,072,064 worlds. |

   Thus the rounded reported values are correct. Champion advantages over KT are **0.8320–1.4766** targets.

   Three qualifications:

   - “Score the same” is stronger than these summaries establish. Individual mono-minus-stereo differences range from **−0.1621 to +0.0176**. Say “similar typical performance” unless equivalence is tested.
   - The **0.40-hour charge is not fully verified by compute.json**. [D303](D:/Claude/random/wormWars/DECISIONS.md:9181) documents approximately 0.07 additional hours from two smoke attempts whose records were deleted. Retain the charge, but identify the estimated component.
   - KT is nested in the controller implementation through `fall_turn=None`, but the KTM tuning loop searches only three non-None settings ([memoryless_check.py:76](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/memoryless_check.py:76)). Include KT explicitly in the registered nested-family optimization. This does not change the observed winning score here.

10. **[Major for the fallback plan; §11 question 6] The base budget arithmetic checks, but it is not yet a complete projection.**

   I recomputed [§10](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:309):

   | Component | Episodes | Hours at 420/s |
   |---|---:|---:|
   | One search | 57,600 | 0.03810 |
   | One target-brain | 748,800 | 0.49524 |
   | N2 searches | 44,928,000 | 29.7143 |
   | N2 evolutionary selection | 9,728,000 | 6.4339 |
   | Pilot-check evolution and searches, before evaluations | 15,052,800 | 9.9556 |

   The stated projected rows total approximately **84.156 million episodes**, excluding already-run exploratory episodes. Including the separately charged 0.40 hours gives **56.06 hours**, consistent with “about 56.”

   What remains missing or conditional:

   - The 256,000 episodes per evolution omit checkpoint validation. Retaining 04a’s 256-world validation every 25 generations gives 41 checkpoints, or **398,848 additional episodes across 38 formal runs**, unless explicitly included elsewhere. See [evolve.py:198](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:198).
   - Steady-state resetting entails extra neural integration inside episodes. Ordinary episode throughput does not price it. Its cost depends on the unresolved convergence procedure.
   - The 2.5-million miscellaneous allowance needs an itemized ledger, including selection confirmation, calibration, probes and resolution measurements.
   - Five-run NIP batches and the actual union-mask search need measured timing.

   Most importantly, the allowed **32-search-world** option doubles the dominant workload. Holding the other allowances fixed, doubling formal and pilot-check search episodes raises the projection to approximately **93.7 hours**. Even reducing random refits to three and free searches to four leaves approximately **76.3 hours** under those same assumptions. The next proposed cut then makes Family 2 incapable of passing.

   **My answer on cut order:** reducing random refits before free searches is reasonable, conditional on feasibility checks. Preserve five brains and evaluation precision. Freeze a configuration that fits after pilot-dev; otherwise stop or explicitly switch to a descriptive proof of concept. The current sequence cannot promise both the confirmatory imprinting test and a workable fallback across its advertised search settings.