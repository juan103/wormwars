**Fix then publish.** The exploratory conclusion is supported. The documents overstate several interpretations and omit important qualifications.

1. **Four rounding errors in [RESULTS.md](/D:/Claude/random/wormWars/experiments/E4-two-minds/RESULTS.md).** Correct:
   - §1, late-generation best-strain range: **6.2–6.9**, not 6.3–6.9; minimum 6.2453127.
   - §2, module B: **2.81**, not 2.80; value 2.8053610.
   - §3, bias factor 0.05: **6.72**, not 6.73; value 6.7248116.
   - §3, nose-origin cut at factor 0.25: **6.25**, not 6.26; value 6.2548490.

2. **§1’s population range is misleading.** Individual run-generation means span **1.49–5.16** after generation 0; averaging the four runs gives **2.16–3.71**. Replace “sits near 2.4–3.4 for 100 generations” with: “Across runs, the population averaged 2.90 in generations 1–10 and 3.22 in generations 90–99.” These follow from the committed summary.

3. **Two numerical claims lack the cited record support.** The children/elites ranges are correct—I recomputed them from the local selection file and verified its recorded SHA256—but are absent from `pilot-attempt1-summary.json`, and its generator does not emit them. Add those aggregates to the generator and committed summary. The **SD ≈3.7** comes from Fable’s E3f/E3c comparison, not an E4 measurement. Supply its underlying source and qualification, or remove it. Replace “mostly noise” with “affected by maze variation and selection of the maximum.”

4. **Both openings and §5 turn a forecast into a finding.** Replace “showed that it would most likely spend about 20 GPU-hours on an inconclusive null” with: “Both reviewers judged the proposed formal run poor value and recommended against spending its estimated 20 GPU-hours.” Delete “equivalent by construction”: no passing smaller factor or subsequent evolution was tested. Label the drift argument explicitly as Fable’s extrapolation. “Every registered size” should be **“every tested factor, 0.25–4.0, on calibration block A.”**

5. **§2 and README overstate causal exclusion.** Replace “the whole loss came from … biases” with **“bias-only mutation reproduced nearly all the loss on this block.”** Replace “no defect in the breeding or evaluation path” with **“the zero-mutation control matched E-G’s reported scores.”** Replace “not a property of E4’s gate or arena” with **“the load also occurred without the gate and on tree mazes.”** The ungated loss was 1.66 visits versus E-G’s 2.06; “lost as much” is inaccurate.

6. **The stage-A composition caveat is missing.** Add: “E-G was evaluated alone; children were evaluated as 116 strains × 16 mazes × 8 weys. Their exact comparison across compositions was not validated. ‘All links cut = E-G’ describes the genome, not a separately measured matched-composition control.” The final X0 validation *did* batch E-G and candidates together; distinguish it.

7. **Block dependence needs an explicit sentence.** Cross-link results use only block A. Block B tested frozen-bias offspring, not cross-links or bias factor 0.02. Four mutation seeds do not provide independent maze-block replication. Also replace the pilot’s categorical “floor … understate” explanation with: “The smaller pilot increment was measured on already impaired populations; stage A used different masks, seeds and mazes.”

8. **§3 misreports Fable’s prediction.** He predicted nose-bias losses about **three times** comparator-bias losses, from gains 18 versus 6. The observed ratio is **4.14**. Write: “Nose biases cost more, in the predicted direction; the observed loss ratio was about four, versus the predicted three.” In the mechanism paragraph, **0.01–0.02 denotes link weights**, not a measured comparator-input threshold.

9. **Stage-A reporting is incomplete.** Add the recorded share-at-least-five beside each mean, as D257 requested; presently only 42% appears. Define it as the share of children whose **maze-average** reaches five. Include 28% for nose biases and 100% for bias factors ≤0.02. Avoid presenting this threshold alone as proof that children “break.” State both bias criteria and write the cross-link bound dimensionally: **min(0.25 visits, 0.05 × X0 mean)**.

10. **The intervention table needs its operational caveat.** Source means were estimated on separate block C, eight mazes. These interventions do not yield an additive decomposition of the intact loss. Replace “removing the nose-origin links rescues most” with **“produces the largest rescue among the tested interventions.”** It restores approximately 49% and 29% of the intact deficit at the two factors.

11. **Narrow the evolutionary conclusion in §5 and README.** Use: “After 100 scored generations, none of the four final X0 populations contained a strain with a higher mean than E-G on these 64 validation mazes.” Retain the best-of-32 selection caveat and add that no independent post-selection test or completed X+ comparison is available. This supports neither “no evolutionary movement” nor failure of longer training.

12. **E4-D’s half-chance statement needs its denominator.** The design establishes exactly half **among entries under paired assignments**, provided entries occur. Over all trials, non-entry can lower success below half. Also amend README’s next steps to preserve D258: **code review → CPU feasibility → only if it passes, evolutionary design, review, pre-registration and pilot**. E4-D addresses necessary transfer in an engineered task, not ordinary-shuttling benefit.

13. **Corrections and attribution need completing.** Replace “Everything … was decided after seeing data” with “Exploratory follow-ups were chosen after earlier results; calibration rules were fixed before stage A.” Add the D253–D254 correction that **6.23 and 1.94 were different blocks**, not a paired loss. Credit Astra’s paired controls/composition warning and Fable’s distribution reporting/headroom request. The compute totals **3.01 + 1.19 = 4.20 hours** are correct; add a dated correction to D258’s approximate **4.4 spent / 25.6 remaining**, now **4.20 / 25.80**, and identify these as synchronised wall-clock hours.

14. **README reproduction claims need fixing.** The scripts do not invoke `replay_mode()`, so “are exact” is unsupported; state the same-device, environment, composition and deterministic-mode requirements without promising a verified replay. Diagnostics also need the local final populations to reproduce validation; otherwise that section is silently omitted. The pytest wildcard command is unsuitable for PowerShell—expand filenames explicitly. Convert key record/design/review paths to links and put a blank line before RESULTS’ first bullet list.

Other quoted means, headroom figures, setup values and approximate runtimes match the records.