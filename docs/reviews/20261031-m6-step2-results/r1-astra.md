**Verdict: fix then publish.** The calculations hold up. The main fixes concern claims of an optimum, T0–T1 equivalence, and a preference for a response-speed explanation. No further simulation is needed for publication.

I reproduced `reading.json` exactly in memory and independently re-derived 31 aggregate statistics from the records, including the block bootstraps. I also checked completeness, genome hashes against M6-0, per-world scores, validation exceptions, and the failure gates. Nothing was written.

1. **Numbers: the reported estimates, intervals and counts match at their stated precision.**

   Some key independent results:

   | Quantity | Re-derived estimate and 95% interval |
   |---|---|
   | T1 primary | −24.4813% [−26.4390, −22.5346] |
   | Without the switch champion | −24.4787% [−26.4390, −22.5333] |
   | Interior arm | −5.9882% [−7.0027, −5.0284] |
   | Interior minus full scaling | +18.4931 points [16.7122, 20.3629] |
   | Matched T1 minus T0 | −2.8362 points [−6.0622, +0.3654] |

   Both relative-change tables, the controls’ table, absolute changes, baselines, correlations, tau summaries and validation table check out. The probe exceptions and switch champion’s integrals also match.

   The matched comparison correctly uses 72 pairs in 24 blocks. Its T1 subset averages **−26.0985%**, explaining why the matched difference is not simply the difference between the two headline means.

   Two small corrections in the [results draft](D:/Claude/random/wormWars/docs/memory/M6-STEP2-RESULTS.md):
   - Line 30 introduces the combined table as “Over the 30 blocks.” Specify **30 T1 blocks and 24 T0 blocks**.
   - Line 175: 3.64 hours is **below**, not “inside,” the forecast of 4–4.3 hours. The recorded duration is 3.63666 hours.

2. **The fixed readings and gates were applied correctly to this run.**

   The primary interval is below zero; both control contrasts at 0.25 are below zero, so both “exceeded” sentences are correct. The sensitivity result is the same **at the displayed precision**, rather than literally identical.

   Completeness, consistency and validation pass. I also forced missing data, consistency failure and validation failure in memory: the reader suppressed affirmative wording as intended.

   **The k = 2 explanation is honest.** Its `not_below_1` list contains the 101 champions whose integrals increased. T1-MS-N2 run 3 is the sole decrease at both 2 and 4. The draft identifies it, and k = 2 does not enter the pass criterion. Preserve that explanation.

3. **Fix three substantive interpretation claims.**

   **“Tuned optimum” is too strong and contradicts the final plan.** Lines 45–47 revive the earlier design note’s claim, although the [final plan, line 61](D:/Claude/random/wormWars/docs/memory/M6-STEP2-PLAN.md:61) explicitly says losses in both directions neither establish a tuned optimum nor count against memory.

   Replace it with something like:

   > Mean performance was highest at the intact time scale among the five scalings tested. Losses in both directions are compatible with a preferred time scale.

   Apply this correction to the roadmap paragraph too. The coarse sweep does not locate an optimum, and individual champions do not all peak at k = 1.

   **T0 looks similar; equivalence is not established.** “Nothing here singles out T1” is fair as a statement about detected evidence. “The same profile within about 3 points” and “the dependence is as large” overstate the result. The matched interval permits a T1 loss approximately **6.1 points larger** than T0’s. Use:

   > The profiles were descriptively similar, and no matched difference was detected at k = 0.25.

   **The interior comparison does not favor response speed over memory.** The reduction from 24.5% to 6.0% supports the concrete observation that sparing sensory and motor time constants greatly reduced the performance cost. But the probe effect was also reduced less: 0.57 versus 0.23 of intact. These interventions do not separate the proposed explanations.

   Delete “This fits a response-speed account better than a memory account.” Replace “Most of the cost goes with…” with the direct intervention result. Keep the existing caveats about changed recurrent inputs and unequal probe effects.

4. **The other interpretations mostly hold, with qualifications.**

   - **Warm-up:** the hazard is stated clearly enough. Adding “all brains start from zero state” would make it more concrete. Keep the 200-tick horizon and the statement that startup costs were not separated. The caveat must constrain the optimum interpretation.
   - **Controls:** lower baselines and less room for absolute losses are legitimate cautions. They do not demonstrate that baseline differences explain the contrast.
   - **Drift:** change line 127 to “The drift genomes’ **mean score** changed little.” Individual responses are substantial: my check found absolute relative changes exceeding 10% in 28/102 genomes at 0.25 and 42/102 at 4. Small net means should not become a claim of individual insensitivity.
   - **Association with a:** handled appropriately. The reported correlations reproduce, and “not a dose-response” is correct. Do not strengthen this into a claim that intact score explains away the association; that was not established.

5. **Stopping and synthesizing follows the owner’s order.**

   [D379](D:/Claude/random/wormWars/DECISIONS.md:12216) explicitly orders the quick check, the champions’ test, then stopping with results folded into the write-up.

   The synthesis should retain the distinction between step 1’s census switches and step 2’s evolved champions. It must not turn state persistence into demonstrated behavioral utility, time-scale dependence into memory mediation, a nonsignificant contrast into task equivalence, or the literature check into biological validation of this model.

   The defensible conclusion is: **foraging depends on neural time scale; the tested interventions do not establish whether the probe-defined fading history effect benefits foraging.**