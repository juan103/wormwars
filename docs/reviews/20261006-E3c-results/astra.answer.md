**Verdict: fix then publish.** The saved analysis is reproducible. The main problems are claims in the prose and omitted registered reporting, particularly the P-sel conclusion.

I checked HEAD `4b40e43`, read-only. Executing the analysis functions against the saved records reproduced the entire `report_readings` output exactly, including path-file verification. I also independently enumerated the permutation tests, recalculated the bootstrap intervals, checked all 28 champion selections, and compared all 40 checkpoint hashes and count arrays.

**1. Do the numbers match?**

The principal numerical results do:

| Recomputed quantity | Q1 | Q2 |
|---|---:|---:|
| Mean difference, visits/wey | −0.04827881 | +0.66381836 |
| 97.5% Welch interval, visits/wey | [−0.11995645, +0.02339883] | [−0.24260416, +1.57024088] |
| Exact permutation p | 1276/12870 = 0.09914530 | 674/12870 = 0.05236985 |
| Maze-bootstrap 95% interval, d | [−0.01300932, −0.00615904] | [+0.04596769, +0.21390829] |

These agree with [report.json:376](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/report.json:376), [report.json:441](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/report.json:441), and [report.json:508](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/report.json:508).

The arm means and SDs, reference scores, nose-loss intervals, descriptive summaries, and cost-curve medians also agree. The accounting totals reconcile to **3.94573559 hours before the formal stages + 18.69935641 formal hours = 22.64509200 hours**, correctly printed as 22.65. [compute-record.json:183](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/compute-record.json:183)

“Every number matches” nevertheless needs qualification: the P-sel coverage lower endpoint is slightly misrounded, the “Runs” column actually contains score ranges, and the prose contains unsupported quantitative comparisons, detailed below.

**2. Are the registered labels exact?**

The main contrast table correctly reproduces both full margin labels and both exact labels. The coverage classification **“supported”** is also correct: shares are 1, 1, and 0, with no undefined champions. [RESULTS.md:97](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:97), [report.json:10401](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/report.json:10401)

Reporting is not fully compliant, however:

- Summary passages abbreviate the labels, particularly Q2’s missing **“approximate (model-based)”** qualification.
- The nose-class and coverer qualifiers appear later, but are not appended to the Q1/Q2 labels as §7.3 explicitly requires.
- “No material loss” is presented without its registered model-based qualification.

The applicable requirements are explicit in [PREREGISTRATION.md:64](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:64), [line 265](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:265), and [line 398](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:398).

**3. Does the interpretation exceed the evidence?**

**Q2’s central reading is correct.** “Unclear,” and “neither confirmed nor refuted,” fit the registered interval. The exact p is 0.05237 against **0.025**. Its non-rejection establishes neither equal means nor identical distributions. The explanation concerning the exchangeability null and unequal spreads is consistent with the registration. [PREREGISTRATION.md:249](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:249)

The positive bootstrap interval is conditional on the particular trained champions: it resamples mazes, not evolutionary runs. It cannot resolve Q2’s run-level uncertainty. The stronger sentence about not depending on “a few mazes” should be replaced with that precise conditional statement. [RESULTS.md:113](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:113)

**Coverage is supported as the registered descriptive classification.** It establishes the observed separation in coverer status. It does not establish that intact S controllers never use nose information, or prove a general population claim about all outcomes of these training routes. The registration expressly distinguishes tolerating nose removal from ignoring noses intact. [PREREGISTRATION.md:351](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:351)

**P-sel’s concluding description is wrong.** Its three higher scores are 6.139, 6.144, and 5.578, whereas every S champion scores at least 6.591. They exceeded P-fixed; they did not reach the observed from-scratch range. [report.json:10482](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/report.json:10482), [RESULTS.md:82](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:82)

**The roadmap note is a reasonable design concern, not an established consequence for E4.** E4 already proposes interventions and a diagnostic task requiring information transfer. E3c did not test those. A shorter horizon is a proposed remedy requiring validation, not a demonstrated solution. [ROADMAP.md:379](D:/Claude/random/wormWars/ROADMAP.md:379)

**4. Is registered reporting missing or mislabelled?**

Yes, some is missing from the prose, although much is present in the JSON:

- The failed-run Fisher tests and successful-run 95% Welch decomposition, explicitly required beside each contrast.
- P-sel’s per-run comparison against P-joint.
- The explicit coverage component label **“high.”**
- Parts of §11’s cost ledger: separate cost categories, common inherited infrastructure, unmeasured design/review effort, and reuse scenarios.

The bootstrap and coverage classification are correctly described as supplements/descriptive readings. They were nevertheless pre-registered; “descriptive” must not be interpreted as “unregistered.” I found no numerical analysis defect requiring a new formal run.

**Required corrections before publication:**

1. **Correct P-sel’s conclusion and its repeated decision-log claim.** Replace “reach the from-scratch level … 3 of 4” with “three of four exceeded P-fixed, while remaining below the observed S-arm range.” Correct [RESULTS.md:240](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:240) and record the corresponding correction to [DECISIONS.md:7101](D:/Claude/random/wormWars/DECISIONS.md:7101). Also qualify “about unchanged” with trails off: run 23 increases from 2.6655 to 3.1826, **+0.5171 visits, approximately 19.4%**. [RESULTS.md:189](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:189), [report.json:10746](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/report.json:10746)

2. **Correct Q1’s bound and calibration wording.** “Within 0.1 visit” is not the demonstrated interval bound: the interval extends to −0.120. State the observed difference of −0.048 and the registered smaller margin of **0.5 visits**. Rewrite “With no failed run, that label is calibrated…” to make clear that calibration assumes the no-failure model; observing zero failures does not establish that model. [RESULTS.md:22](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:22), [RESULTS.md:106](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:106), [PREREGISTRATION.md:483](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:483)

3. **Complete the label presentation.** Preserve the full approximate/model-based qualification in the summary and README; qualify “no material loss”; append the registered counts to the primary readings: Q1 has 8 nose-independent coverers in each arm; Q2 has P-joint’s 4 partial, 4 nose-dependent, 0 coverers against S-mod’s 8 nose-independent coverers. Explicitly report the coverage component as **“high.”** Rename the Holm row **“Holm-adjusted Welch p”**: 0.152 is correct, but it is not an adjustment of the adjacent exact p-values. [report.json:418](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/report.json:418), [report.json:483](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/report.json:483)

4. **Narrow the mechanistic and bootstrap claims.** Replace “advantage does not depend on a few mazes” with the conditional bootstrap finding. Replace “The from-scratch arms did not navigate” with the measured result: all 16 selected S champions met the nose-independent coverer criterion. Apply the same scope to the README’s “every organism” wording. [RESULTS.md:115](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:115), [RESULTS.md:244](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:244), [README.md:9](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/README.md:9)

5. **Restore the omitted registered comparisons.** Both failed-run Fisher p-values are **1.0**. Successful-run 95% intervals in d are **Q1 [−0.021266, +0.002400]** and **Q2 [−0.017712, +0.277109]**. P-sel’s differences from P-joint’s mean are **−1.1903, −1.1859, −1.7513, −4.6639 visits**. These are already computed. [PREREGISTRATION.md:295](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:295), [report.json:400](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/report.json:400), [report.json:465](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/report.json:465), [report.json:10482](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/report.json:10482)

6. **Complete the registered cost accounting narrative.** Retain the correct hours, but add §11’s categories, shared inherited costs, unmeasured effort, and explicitly hypothetical reuse scenarios. The first-use range alone does not fulfil those commitments. [PREREGISTRATION.md:553](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:553)

7. **Make the E4 implication conditional and fix two presentation details.** Say coverage is a risk for an E4 design relying on the same score, rather than asserting E4 is affected identically. Rename the primary table’s “Runs” column to “Range over runs.” Change P-sel’s circuit coverage from “85–92%” to **84.5–91.9%**; the lower endpoint is 84.484375%. [RESULTS.md:249](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:249), [RESULTS.md:80](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:80), [report.json:7399](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/report.json:7399)