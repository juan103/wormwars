**Verdict: revise.** The main blockers are a miscentred power simulation, intervals that are not simultaneous confidence intervals, and incomplete rules for cuts and mechanistic readings.

I checked commit `54f6f5f`, ran the 12 statistics tests successfully, verified both pinned file hashes, and verified all 256 P-joint final-genome hashes plus its 256 index-124 snapshot hashes. I also ran statistical diagnostics entirely in memory. No files were changed.

**1. Faithfulness**

The core comparison follows the design and D205/D206: unchanged task, training schedules and mutation factors; reused P-joint with fresh champion selection; nose removal as a secondary reading; and narrower interpretation. The dual margin follows the owner’s instruction. See [§1](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:15), [§3](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:70), and [D205’s consequences](/D:/Claude/random/wormWars/DECISIONS.md:6630).

There are omissions:

- **The design’s cost ledger is missing.** The registration’s GPU budget does not replace the required historical first-use ledger, common inherited costs, incremental costs and reuse scenarios. Restore [design §7, lines 240–261](/D:/Claude/random/wormWars/docs/E3/E3c-DESIGN.md:240).
- **§13 is not a complete account of additions.** Explicitly include the descriptive correlations/resting-turn readings and the newly chosen arm-level coverage decision rule. Conversely, publication of champion parameters was already required by [design §3, lines 94–98](/D:/Claude/random/wormWars/docs/E3/E3c-DESIGN.md:94), so §13 item 9 should distinguish reaffirmation from departure.
- My requested paired-loss reading is included, but its interval and supplemental resampling procedure remain unspecified. The original request also included absolute intact/removed performance and maze-level differences; make their publication explicit. See [pilot review, lines 43–55](/D:/Claude/random/wormWars/docs/reviews/20261005-E3c-pilot/astra.answer.md:43).

Fable’s proposed analytic coverage ceiling is absent. I would treat that as optional until its derivation is checked, rather than importing the estimate as established fact.

**2. Statistics**

**The basic Welch calculation, Holm rejection algorithm, floor handling and dual-margin label implementation are correct as algorithms for the supplied inputs.** The tests support that limited conclusion. See [statistics code, lines 32–104](/D:/Claude/random/wormWars/wormwars/e3/e3c_stats.py:32).

**The “Holm-level intervals” are not valid simultaneous 95% confidence intervals.** Matching Holm’s decisions about zero does not establish coverage for nonzero parameter values or practical-margin assertions. Ranking tests against zero and choosing ordinary intervals at those ranks does not invert Holm for arbitrary hypothesized differences. Genuine corresponding confidence regions require additional construction; see [Guilbaud’s paper](https://pubmed.ncbi.nlm.nih.gov/18932131/).

I checked this numerically under the script’s Gaussian model: eight runs, S-arm SD 0.06, seed mean 5, true differences Q1 = 0.5 and Q2 = 1 visit. Across 100,000 simulations, **joint interval coverage was 92.62%**. The vectorized calculation agreed with the registered functions on 200 checked cases. This concerns [§7.1, lines 182–206](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:182) and [code lines 65–83](/D:/Claude/random/wormWars/wormwars/e3/e3c_stats.py:65).

My simple recommendation is **fixed 97.5% intervals for both contrasts, with all primary labels derived from those intervals**. Holm results can be reported separately. Alternatively, implement a justified simultaneous confidence procedure. Bonferroni addresses multiplicity; it does **not** repair small-sample Welch calibration under mixtures.

The dual-margin rule itself is sound and clear. Add explicit boundary conventions—currently the code requires strict containment/clearance—and require a finite, positive seed mean. Rewrite [line 210](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:209) as “**When Q1 is not read**, it enters Holm with p = 1”; “If so” is ambiguous.

**The reported 0.06 failure-mixture rate is not a false-positive rate**, for the reason in answer 3. Correctly centred nulls are more concerning. My separate 100,000-trial checks, using the script’s component distributions and registered Welch/Holm decisions, produced:

| S-arm failure probability | S runs / P-joint runs | True Q1 difference | Q2 false-positive rate at true Q2 = 0 |
|---|---:|---:|---:|
| 1/8 | 8 / 8 | 0 | 7.60% |
| 1/8 | 8 / 8 | 1 visit | 11.38% |
| 1/4 | 8 / 8 | 0 | 7.84% |
| 1/4 | 6 / 8 | 0 | 13.57% |

These are reviewer diagnostics, not committed experiment results. I checked the vectorized decisions against `readings()` on 1,000 mixture cases.

**Disclosure alone is insufficient for an unqualified 5% confirmatory claim.** Keep the estimands and practical margins. Fix a scientifically motivated stress family before comparing alternative procedures, then validate one fixed procedure for unequal-distribution means, including familywise and margin-claim errors. If useful calibration cannot be achieved at the fixed budget, report Welch results as approximate evidence and downgrade the confirmatory labels. A conservative bounded-mean confidence procedure is a principled fallback, though likely uninformative at these sample sizes. Neither Mann–Whitney nor an ordinary permutation test automatically repairs inference about equal means under unequal distributions.

**3. Power analysis**

It correctly uses the same S-mod sample in both contrasts and calls the registered reading function. However, its generating distributions do not have the advertised effects.

From [script lines 48–66](/D:/Claude/random/wormWars/scripts/e3c_power.py:48), with failure probability \(p\),

\[
E[S_{\rm mod}]=6.7-4.4p,\qquad
\Delta_1=(1-p)\,\texttt{delta1},\qquad
\Delta_2=\texttt{delta2}+4.4p.
\]

Thus, at \(p=1/4\), a scenario labelled `delta2=0` has a **true P-joint advantage of 1.1 visits**. At \(p=1/8\), the table’s “Q1 at 1 visit” actually means 0.875 visits.

For the current equal-failure-probability model, generate:

- S-dense’s successful component at \(6.7-\Delta_1/(1-p)\);
- P-joint at \(6.7-4.4p+\Delta_2\).

Store the analytically derived population means and actual contrasts in every scenario, and test those identities.

**The six-run scenario is also wrong.** [Script lines 64–66](/D:/Claude/random/wormWars/scripts/e3c_power.py:64) give every arm `n` runs. [§10, lines 363–366](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:363) cuts only S-mod and S-dense; P-joint stays at eight. The quoted reduction to approximately 0.45 power therefore does not describe the registered cut.

The scenarios also need:

- unequal failure probabilities between S arms, varied failure levels/spreads, and properly centred global and partial nulls;
- P-joint variance sensitivity beyond one fixed historical SD, reflecting reselection and the changed block;
- both directions of Q1 effects;
- joint false-rejection counters, simultaneous coverage and false margin classifications;
- Monte Carlo uncertainty, with more than 2,000 trials for close error-rate decisions.

The empirical P-joint shape is a useful sensitivity case, not strong evidence about its population distribution. Its construction is internally coherent, but [lines 40–43 and 55–58](/D:/Claude/random/wormWars/scripts/e3c_power.py:40) fix its spread to the historical estimate.

**§8 is only partly accurate against `power.json`:**

- The no-failure, other-contrast-zero base figures broadly match.
- “Q1’s false-positive rate stays at or below 0.03 in every scenario” is false: one genuine Q1-null scenario gives **0.0465**. See [power.json, lines 3925–3945](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/power.json:3925).
- Q2 “otherwise … at most 0.03” is false: a no-failure empirical-shape partial null gives **0.0625**. See [lines 713–731](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/power.json:713).
- Empirical-shape Q2 power is **0.609 for +1 visit and 0.644 for −1**, so “0.61 at ±1” suppresses the asymmetry.
- The failure-mixture table and the six-run interpretation require regeneration, not merely wording changes.

**4. Coverage hypothesis and nose removal**

The retained-fraction classes and per-champion coverer criterion are acceptable **operational descriptive definitions**, carried forward from D205. The definition of the intervention and intact-path measurements is faithful. See [§7.3, lines 242–254](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:242).

The arm-level rule needs revision:

- **Fewer coverers does not establish greater nose dependence.** P-joint could retain 100% of visits yet fail the tour criterion. The rule would support the stated hypothesis without supporting its “P-joint depends more on noses” component. Either narrow that hypothesis to lower coverer prevalence or give nose dependence its own direct criterion.
- **“6 of 8” does not handle the six-run cut.** Fix proportion-based thresholds beforehand—for example, at least 75% and at most 25%, with explicit rounding—and compare P-joint with **both S-arm proportions**, not raw counts.
- Define zero intact visits, no eligible tour paths and incomplete records. Undefined measurements should not silently become “partial.”
- Specify the loss interval: its method, whether 95% is one- or two-sided, and what is reported for singleton P-fixed.

These issues affect [lines 247–260](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:247). The supported/mixed/not-supported result should be called a registered descriptive classification, not a calibrated hypothesis test.

Appending qualifiers is fair, provided they never override Q1/Q2. But [lines 262–263](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:262) conflate **nose-class counts** with **coverer counts**. Report both separately.

**5. Blocks, seeds, stages, champions, cap and cuts**

The proposed validation, learning and test ranges are mutually disjoint and outside the listed earlier ranges. Training ranges and new seed bases are consistent with the intended separation. The final-population champion rule is clear. The existing P-joint populations and snapshots match their recorded hashes.

The execution specification is not yet complete:

- **The formal runner does not exist at this commit.** Its stages and commands contain only `pilot` and `replay`: [lines 68–81](/D:/Claude/random/wormWars/scripts/e3c.py:68), [line 622](/D:/Claude/random/wormWars/scripts/e3c.py:622). Given [§2 line 66](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:65), complete and check the formal implementation before binding its code, or explicitly distinguish registration and later implementation commits.
- Register benchmark IDs/seeds outside formal outcome blocks. Specify checkpoint, validation, evaluation and intervention batch compositions, including padding and the reduced-run plans. Training compositions alone do not determine reproducibility.
- Fix which run IDs survive each cut, and what happens if the projection still exceeds the remainder after all cuts.
- Specify eligibility after interruption: minimum completed runs, complete-maze requirements, whether shorter training runs are excluded, and explicit “not read” outcomes. Salvaging records does not define valid inference.
- Define P-joint’s learning-curve candidate selection at indices 124 and 299; “its populations” is not a selection rule.
- Give W2-turn a final tie-break when both score and absolute turn tie.
- Specify the bootstrap algorithm/seed and the censored-median convention. “Fewer than half” does not settle the exactly-half case.

See [§§4–6](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:107), [§7.2](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:221), and [§10](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:345).

**The diagnostic charge must enter executable accounting.** The committed aggregate contains **3.9156 hours**, excluding the approximately 0.03-hour seed diagnostic; the inherited cap clock reads that aggregate directly. The stated 3.95 is reasonable after adding the diagnostic, but prose does not charge the clock. See [compute record line 67](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/compute-record.json:67) and [CapClock lines 130–136](/D:/Claude/random/wormWars/wormwars/registration.py:130).

**6. Wording**

Several claims need tightening:

- [§1 lines 18–19](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:18) should identify **the three replayed S-dense champions**. S-mod’s corresponding mechanism remains a hypothesis.
- “Nose-independent” is a better operational class name than “scent-independent.” Preserved performance shows removal is tolerable under this intervention; it does not prove intact controllers ignore nose inputs. Occupancy inputs remain available.
- Q2’s short label should include **initialization plus tuning recipe**. The prose acknowledges the mutation-factor difference, but the emitted label only names initialization.
- A P-sel champion above the floor is a successful selector-only training outcome, not necessarily a “working selector” mechanistically.
- “No relevant difference” is a practical-equivalence assertion about this score and block. Reconcile it with [§1 line 46](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:44), rather than claiming no equivalence assertion is made.
- Equal historical normalized gains on different blocks do not establish an expected zero contrast. Keep “direction uncertain”; make predictions about “unclear” conditional on the assumed effect scenarios.

**7. Required changes before binding**

1. **Correct and regenerate the power analysis:** actual mixture means, eight retained P-joint runs after cuts, joint errors, uncertainty and corrected §8.
2. **Replace or properly justify the interval procedure**, and resolve the demonstrated mixture calibration problem before claiming confirmatory error control.
3. **Repair the coverage rule:** match its stated hypothesis, support reduced sample sizes, distinguish nose classes from coverers, and define missing/undefined cases.
4. **Fully specify secondary statistics:** loss intervals, paired bootstrap, censored medians and P-joint learning-curve selection.
5. **Complete the execution contract and implementation checks:** benchmark blocks, compositions, cut IDs, admission, interruption rules and cap accounting.
6. **Restore the design’s cost ledger and complete §13’s change inventory.**
7. **Narrow the mechanistic and Q2 wording** as described above.

Optional suggestions: derive and check the analytic coverage ceiling; show each champion’s intact and removed scores alongside the class counts; add uncertainty to descriptive coverer proportions.